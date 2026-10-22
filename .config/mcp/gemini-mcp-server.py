#!/usr/bin/env python3
"""Gemini-as-MCP wrapper.

Exposes Gemini as a single MCP tool so Claude Code can consult Gemini without
leaving the terminal.

Auth (first match wins, read from the environment):
  1. GEMINI_API_KEY (or GOOGLE_API_KEY) -> Gemini Developer API.
  2. GOOGLE_CLOUD_PROJECT -> Vertex AI on that project, using Application
     Default Credentials (gcloud auth application-default login).
  Neither set -> every call returns an ERROR explaining what to set.
SDK : google-genai (NOT the deprecated `vertexai` SDK -- it 404s on Gemini 3).

Run via Claude Code's MCP loader (stdio transport). See mcp.json.example in
the dotfiles repo (.config/mcp/).
"""

from __future__ import annotations

import os
import sys

import anyio.to_thread

from mcp.server.fastmcp import FastMCP

# The MCP config passes these per-server so we don't pollute the shell. Empty
# strings count as unset (the template expands missing vars to "").
API_KEY  = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY") or ""
PROJECT  = os.environ.get("GOOGLE_CLOUD_PROJECT") or ""
AUTH_ERROR = (
    "ERROR: gemini MCP server has no credentials. Set GEMINI_API_KEY (Gemini "
    "Developer API) or GOOGLE_CLOUD_PROJECT (Vertex AI with gcloud ADC) in the "
    "server's env, then restart Claude Code."
)
if not API_KEY and not PROJECT:
    print(AUTH_ERROR, file=sys.stderr)

# Allow-list keeps the surface honest; Gemini 3+ lives at location=global,
# Gemini 2.5 lives at us-central1. Caller picks; we route.
# Location only matters on Vertex; the Developer API ignores it.
# Verified available on Vertex 2026-06-09 (models.list + smoke test);
# gemini-3.7-flash added 2026-08-14 (global only -- 404s on us-central1).
# gemini-3.8-flash added 2026-09-02 (global; smoke-tested on Vertex).
GLOBAL_MODELS    = {
    "gemini-3.8-flash",
    "gemini-3.7-flash",
    "gemini-3.5-flash",
    "gemini-3.1-pro-preview",
    "gemini-3.1-flash-lite",
    "gemini-3-flash-preview",
}
US_CENTRAL_MODELS = {"gemini-2.5-pro", "gemini-2.5-flash"}
ALLOWED = GLOBAL_MODELS | US_CENTRAL_MODELS

mcp = FastMCP(name="gemini")

# Fallback chains, ordered; first success wins. Preview/newest tiers fall back
# to the GA workhorses (2.5-pro/flash are the only models with an SLA). An
# empty response counts as a failure -- Gemini 3's thinking budget can consume
# the entire output allowance (observed 2026-06-01 via ask_gemini).
FALLBACKS: dict[str, tuple[str, ...]] = {
    "gemini-3.8-flash":        ("gemini-3.7-flash", "gemini-3.5-flash", "gemini-2.5-flash"),
    "gemini-3.7-flash":        ("gemini-3.5-flash", "gemini-2.5-flash"),
    "gemini-3.5-flash":        ("gemini-2.5-flash",),
    "gemini-3.1-pro-preview":  ("gemini-2.5-pro", "gemini-2.5-flash"),
    "gemini-3.1-flash-lite":   ("gemini-2.5-flash",),
    "gemini-3-flash-preview":  ("gemini-2.5-flash",),
    "gemini-2.5-pro":          ("gemini-2.5-flash",),
    "gemini-2.5-flash":        ("gemini-2.5-pro",),
}

# Lazy client init: one client per location (or one for the API-key route),
# built on first use.
_clients: dict[str, object] = {}


def _client(location: str):
    from google import genai
    key = "api-key" if API_KEY else location
    if key not in _clients:
        if API_KEY:
            _clients[key] = genai.Client(vertexai=False, api_key=API_KEY)
        else:
            _clients[key] = genai.Client(
                vertexai=True, project=PROJECT, location=location
            )
    return _clients[key]


def _generate(
    model: str,
    prompt: str,
    max_output_tokens: int,
    temperature: float,
    timeout_s: float,
) -> str:
    """One attempt against one model. Returns text or raises."""
    from google.genai import types

    location = "global" if model in GLOBAL_MODELS else "us-central1"
    resp = _client(location).models.generate_content(
        model=model,
        contents=prompt,
        config=types.GenerateContentConfig(
            max_output_tokens=max_output_tokens,
            temperature=temperature,
            http_options=types.HttpOptions(timeout=int(timeout_s * 1000)),
        ),
    )
    if not resp.text:
        raise ValueError("empty response (thinking budget likely ate the output)")
    return resp.text


@mcp.tool()
async def ask_gemini(
    prompt: str,
    model: str = "gemini-3.8-flash",
    max_output_tokens: int = 8192,
    temperature: float = 0.7,
    timeout_s: float = 90.0,
) -> str:
    """Ask Gemini a question (Gemini Developer API key or Vertex AI).

    Use this to get a second opinion, a pedagogical explanation, or a
    differently-trained perspective on a problem. Pass a fully-formed prompt;
    no chat history is preserved between calls.

    If the requested model errors, times out, or returns an empty response,
    the call automatically falls back to the GA-tier models (2.5-pro/flash)
    and the response is prefixed with a [fallback: ...] note saying which
    model actually answered.

    Args:
        prompt: The full prompt text. Be specific; Gemini has no context from
            this conversation.
        model: One of gemini-3.8-flash (default, newest), gemini-3.7-flash,
            gemini-3.5-flash, gemini-3.1-pro-preview (heavy reasoning),
            gemini-3.1-flash-lite, gemini-3-flash-preview,
            gemini-2.5-pro (long prose), gemini-2.5-flash.
        max_output_tokens: Cap on response length. Raise for JSON output;
            Gemini 3 has been observed to truncate below 4096.
        temperature: 0.0 deterministic, 1.0 creative. Default 0.7.
        timeout_s: Per-attempt HTTP timeout in seconds. Each fallback attempt
            gets the same budget.

    Returns:
        The model's text response (prefixed with a [fallback: ...] note when a
        fallback model answered), or "ERROR: ..." if every model failed.
    """
    # FastMCP runs sync tools on the event loop, so concurrent calls would
    # serialize behind one blocking HTTP request; offload to a thread.
    return await anyio.to_thread.run_sync(
        _ask_gemini_sync, prompt, model, max_output_tokens, temperature, timeout_s
    )


def _ask_gemini_sync(
    prompt: str,
    model: str,
    max_output_tokens: int,
    temperature: float,
    timeout_s: float,
) -> str:
    if not API_KEY and not PROJECT:
        return AUTH_ERROR
    if model not in ALLOWED:
        return f"ERROR: model {model!r} not allowed. Choose from {sorted(ALLOWED)}."

    failures: list[str] = []
    for candidate in (model, *FALLBACKS.get(model, ())):
        try:
            text = _generate(candidate, prompt, max_output_tokens, temperature, timeout_s)
        except Exception as e:  # noqa: BLE001 -- surface, never crash the server
            failures.append(f"{candidate}: {type(e).__name__}: {e}")
            continue
        if candidate != model:
            return f"[fallback: {candidate} answered after {'; '.join(failures)}]\n\n{text}"
        return text
    return "ERROR: all models failed -- " + " | ".join(failures)


if __name__ == "__main__":
    mcp.run(transport="stdio")
