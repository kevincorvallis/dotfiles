#!/usr/bin/env python3
"""Codex-as-MCP wrapper.

Exposes OpenAI's Codex CLI as an MCP tool so Claude Code can consult GPT
without leaving the terminal. Mirrors the shape of gemini-mcp-server.py,
including its ordered fallback chain and `[fallback: ...]` reply prefix.

Auth: handled by Codex itself (`codex login` -> ChatGPT account or API key).
      We just shell out to `codex exec`, which uses whatever auth Codex has.

Run via Claude Code's MCP loader (stdio transport). See mcp.json.example in
the dotfiles repo (.config/mcp/).
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

import anyio.to_thread

from mcp.server.fastmcp import FastMCP

# ChatGPT-account auth only accepts top-tier models; -codex and -mini
# variants return 400 "not supported" (verified 2026-07-03). gpt-5.6-sol
# needs codex-cli >= 0.144 (verified 2026-07-09). gpt-6-astra launched
# 2026-09-03 and ships in the codex-cli >= 0.153.1 catalog, but as of
# 2026-09-04 this ChatGPT account still gets 400 "not supported" for it --
# the FALLBACKS chain covers the gap and stops mattering the day it unlocks.
ALLOWED = {"gpt-6-astra", "gpt-5.6-sol", "gpt-5.5"}
DEFAULT_MODEL = "gpt-6-astra"
CODEX_BIN = os.environ.get("CODEX_BIN") or shutil.which("codex") or "/opt/homebrew/bin/codex"
TIMEOUT_S = int(os.environ.get("CODEX_TIMEOUT_S", "300"))

# Fallback chains, ordered; first success wins. Only fast failures fall
# through (API error, non-zero exit, empty final message) -- a timeout is
# returned as-is so a bad day never costs 2x TIMEOUT_S.
FALLBACKS: dict[str, tuple[str, ...]] = {
    "gpt-6-astra": ("gpt-5.6-sol",),
}

# A 400 that says the *account* or *client* can't use a model is not
# transient. Remember it for a while so a 4-seat gauntlet doesn't pay the
# ~5s probe on every call. Matched only against `ERROR:` lines on stderr
# (codex echoes the user prompt there too, so never scan the whole stream).
GATED_MARKERS = (
    "not supported when using codex with a chatgpt account",
    "requires a newer version of codex",
)
GATED_TTL_S = 3600
_gated_until: dict[str, float] = {}

mcp = FastMCP(name="codex")


class _AttemptFailed(Exception):
    """One `codex exec` attempt failed fast; `gated` = account/client refusal."""

    def __init__(self, detail: str, gated: bool = False):
        super().__init__(detail)
        self.gated = gated


@mcp.tool()
async def ask_gpt(
    prompt: str,
    model: str = DEFAULT_MODEL,
) -> str:
    """Ask GPT a question via OpenAI Codex CLI (ChatGPT-account auth).

    Use this to get a second opinion from GPT, a differently-trained
    perspective, or to cross-check a Claude/Gemini answer. Pass a fully-formed
    prompt; no chat history is preserved between calls.

    If the requested model is refused (e.g. not yet enabled for this account),
    the call falls back down the chain and the response is prefixed with a
    [fallback: ...] note saying which model actually answered.

    Args:
        prompt: The full prompt text. Be specific; GPT has no context from
            this conversation.
        model: gpt-6-astra (default, newest; falls back to gpt-5.6-sol while
            this ChatGPT account isn't enabled for it), gpt-5.6-sol, or
            gpt-5.5 (previous generation). Other variants are rejected by
            ChatGPT-account auth.

    Returns:
        GPT's text response (prefixed with a [fallback: ...] note when a
        fallback model answered), or an error message prefixed with "ERROR:".
    """
    # FastMCP runs sync tools on the event loop, so concurrent calls would
    # serialize behind one blocking subprocess.run; offload to a thread.
    return await anyio.to_thread.run_sync(_ask_gpt_sync, prompt, model)


def _run_once(prompt: str, model: str) -> str:
    """One `codex exec` attempt against one model. Returns text or raises."""
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as tf:
        out_path = Path(tf.name)
    try:
        result = subprocess.run(
            [
                CODEX_BIN, "exec",
                "-m", model,
                "-s", "read-only",
                "--ephemeral",
                "--skip-git-repo-check",
                "--ignore-user-config",
                "--ignore-rules",
                "--color", "never",
                "-o", str(out_path),
                prompt,
            ],
            capture_output=True,
            text=True,
            timeout=TIMEOUT_S,
            cwd="/tmp",
            # codex exec reads stdin to EOF when it's not a TTY; inheriting
            # the MCP stdio pipe (never closed) hangs every call until timeout.
            stdin=subprocess.DEVNULL,
        )
        text = out_path.read_text().strip() if out_path.exists() else ""
        if result.returncode == 0 and text:
            return text
        # API errors arrive as `ERROR: {json}` lines on stderr with rc=1
        # (codex-cli 0.153.2, verified 2026-09-04).
        stderr = result.stderr or ""
        err_lines = [ln for ln in stderr.splitlines() if ln.startswith("ERROR:")]
        gated = any(m in ln.lower() for ln in err_lines for m in GATED_MARKERS)
        detail = _error_detail(err_lines, stderr or result.stdout or "")
        raise _AttemptFailed(f"rc={result.returncode} {detail}", gated=gated)
    finally:
        try:
            out_path.unlink(missing_ok=True)
        except Exception:
            pass


def _error_detail(err_lines: list[str], raw: str) -> str:
    """Human-readable failure reason. Prefer the API error's `message` field so
    the [fallback: ...] prefix never carries a JSON object in front of a reply
    that callers may JSON-parse."""
    if not err_lines:
        return raw.strip()[-400:] or "no final message"
    body = err_lines[0][len("ERROR:"):].strip()
    try:
        err = json.loads(body)
        msg = (err.get("error") or {}).get("message") or err.get("message")
        status = err.get("status")
        if msg:
            return f"HTTP {status}: {msg}" if status else str(msg)
    except (ValueError, AttributeError):
        pass
    return err_lines[0][:300]


def _ask_gpt_sync(prompt: str, model: str) -> str:
    if model not in ALLOWED:
        return f"ERROR: model {model!r} not allowed. Choose from {sorted(ALLOWED)}."

    failures: list[str] = []
    for candidate in (model, *FALLBACKS.get(model, ())):
        gated_left = _gated_until.get(candidate, 0.0) - time.monotonic()
        if gated_left > 0:
            failures.append(
                f"{candidate}: skipped, refused for this account earlier "
                f"(rechecked in {int(gated_left // 60) + 1} min)"
            )
            continue
        try:
            text = _run_once(prompt, candidate)
        except _AttemptFailed as e:
            if e.gated:
                _gated_until[candidate] = time.monotonic() + GATED_TTL_S
            failures.append(f"{candidate}: {e}")
            continue
        except subprocess.TimeoutExpired:
            note = f" (earlier: {' | '.join(failures)})" if failures else ""
            return f"ERROR: codex exec timed out after {TIMEOUT_S}s on {candidate}.{note}"
        except FileNotFoundError:
            return f"ERROR: codex binary not found at {CODEX_BIN}. Install with `npm i -g @openai/codex`."
        except Exception as e:  # noqa: BLE001 -- surface, never crash the server
            failures.append(f"{candidate}: {type(e).__name__}: {e}")
            continue
        if candidate != model:
            return f"[fallback: {candidate} answered after {'; '.join(failures)}]\n\n{text}"
        return text
    return "ERROR: all models failed -- " + " | ".join(failures)


if __name__ == "__main__":
    mcp.run(transport="stdio")
