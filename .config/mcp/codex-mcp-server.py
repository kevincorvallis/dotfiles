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
import threading
import time
from pathlib import Path

import anyio.to_thread

from mcp.server.fastmcp import FastMCP

# ChatGPT-account auth only accepts top-tier models; -codex and -mini
# variants return 400 "not supported" (verified 2026-07-03). gpt-5.6-sol
# needs codex-cli >= 0.144 (verified 2026-07-09). gpt-6-astra launched
# 2026-09-03 and ships in the codex-cli >= 0.153.1 catalog. A ChatGPT account
# gets 400 "not supported" for it until OpenAI enables it (still refused
# 2026-09-04, answered 2026-11-14) -- the FALLBACKS chain covers that gap.
ALLOWED = {"gpt-6-astra", "gpt-5.6-sol", "gpt-5.5"}
DEFAULT_MODEL = "gpt-6-astra"
CODEX_BIN = os.environ.get("CODEX_BIN") or shutil.which("codex") or "/opt/homebrew/bin/codex"
TIMEOUT_S = int(os.environ.get("CODEX_TIMEOUT_S", "300"))

# Network waits that an ask_gpt call does not need. Each costs seconds on a
# slow link (measured 2026-11-14, codex-cli 0.153.4):
# - analytics + metrics: `codex exec` uploads both before it exits, and this
#   wrapper waits for exit.
# - apps, plugins: catalog fetches with 5 s timeouts before the turn, which
#   also push the websocket warm-up past its 15 s limit.
LEAN = (
    "-c", "analytics.enabled=false",
    "-c", 'otel.metrics_exporter="none"',
    "--disable", "apps",
    "--disable", "plugins",
    "--disable", "remote_plugin",
)

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

# Thread memory: a caller-chosen thread_id maps to the Codex session that
# holds the conversation, plus the turns so far. Codex keeps the session
# itself, under $CODEX_HOME/sessions. This map lives in this process only, so
# a thread ends when Claude Code restarts the server. One lock per thread
# keeps parallel calls on the same thread in order.
_threads: dict[str, tuple[str, int]] = {}
_thread_locks: dict[str, threading.Lock] = {}
_registry_lock = threading.Lock()

mcp = FastMCP(name="codex")


def _thread_lock(thread_id: str) -> threading.Lock:
    with _registry_lock:
        return _thread_locks.setdefault(thread_id, threading.Lock())


class _AttemptFailed(Exception):
    """One `codex exec` attempt failed fast; `gated` = account/client refusal."""

    def __init__(self, detail: str, gated: bool = False):
        super().__init__(detail)
        self.gated = gated


@mcp.tool()
async def ask_gpt(
    prompt: str,
    model: str = DEFAULT_MODEL,
    thread_id: str = "",
) -> str:
    """Ask GPT a question via OpenAI Codex CLI (ChatGPT-account auth).

    Use this to get a second opinion from GPT, a differently-trained
    perspective, or to cross-check a Claude/Gemini answer. Without thread_id
    each call stands alone: pass a fully-formed prompt, because no chat
    history is kept. With thread_id, GPT sees the earlier turns of that
    thread, so a follow-up needs only the new message.

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
        thread_id: Optional name for a conversation; any string you choose.
            Calls that share it resume one Codex session, which Codex keeps
            on disk under ~/.codex/sessions. This server remembers the name
            until Claude Code restarts. The reply then starts with
            "[thread: <name>, turn N]". Turn 1 on a follow-up means the
            history was lost, so send the context again.

    Returns:
        GPT's text response (prefixed with a [fallback: ...] note when a
        fallback model answered), or an error message prefixed with "ERROR:".
    """
    # FastMCP runs sync tools on the event loop, so concurrent calls would
    # serialize behind one blocking subprocess.run; offload to a thread.
    return await anyio.to_thread.run_sync(_ask_gpt_sync, prompt, model, thread_id)


def _events(stdout: str) -> list[dict]:
    """The JSON events `codex exec --json` prints, one per stdout line."""
    events = []
    for line in stdout.splitlines():
        try:
            event = json.loads(line)
        except ValueError:
            continue
        if isinstance(event, dict):
            events.append(event)
    return events


def _run_once(
    prompt: str, model: str, keep: bool = False, session: str | None = None
) -> tuple[str, str | None]:
    """One `codex exec` attempt against one model. Returns (text, session id)
    or raises. `keep` starts a session that a later call can resume; `session`
    resumes one. With neither, the run is ephemeral and the id is None."""
    if session:
        # `resume` takes no -s flag, so the sandbox is set through config.
        mode = ["resume", session, "-m", model, "-c", 'sandbox_mode="read-only"', "--json"]
    elif keep:
        mode = ["-m", model, "-s", "read-only", "--color", "never", "--json"]
    else:
        mode = ["-m", model, "-s", "read-only", "--color", "never", "--ephemeral"]
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as tf:
        out_path = Path(tf.name)
    try:
        result = subprocess.run(
            [
                CODEX_BIN, "exec", *mode, *LEAN,
                "--skip-git-repo-check",
                "--ignore-user-config",
                "--ignore-rules",
                "-o", str(out_path),
                # Without `--`, codex reads a prompt that starts with a dash
                # as a flag and exits with rc=2.
                "--", prompt,
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
        events = _events(result.stdout or "") if keep or session else []
        if result.returncode == 0 and text:
            started = (e.get("thread_id") for e in events if e.get("type") == "thread.started")
            return text, session or next(started, None)
        # API errors arrive as `ERROR: {json}` lines on stderr with rc=1
        # (codex-cli 0.153.2, verified 2026-09-04). With --json they are
        # `error` events on stdout that carry the same JSON body as a string
        # (codex-cli 0.153.4, verified 2026-11-14).
        stderr = result.stderr or ""
        err_lines = [ln for ln in stderr.splitlines() if ln.startswith("ERROR:")]
        err_lines += [f"ERROR: {e.get('message')}" for e in events if e.get("type") == "error"]
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


def _ask_gpt_sync(prompt: str, model: str, thread_id: str) -> str:
    if model not in ALLOWED:
        return f"ERROR: model {model!r} not allowed. Choose from {sorted(ALLOWED)}."
    if not thread_id:
        return _answer(prompt, model)[1]

    with _thread_lock(thread_id):
        session, turns = _threads.get(thread_id, (None, 0))
        answered, reply, session = _answer(prompt, model, keep=True, session=session)
        if not answered:
            return reply  # a failed turn leaves the thread map as it was
        if not session:
            return f"[thread: {thread_id}, turn 1, not saved: codex gave no session id]\n\n{reply}"
        _threads[thread_id] = (session, turns + 1)
        return f"[thread: {thread_id}, turn {turns + 1}]\n\n{reply}"


def _answer(
    prompt: str, model: str, keep: bool = False, session: str | None = None
) -> tuple[bool, str, str | None]:
    """Walk the fallback chain. Returns (answered, the reply for the caller,
    the session id of a kept run)."""
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
            text, session_id = _run_once(prompt, candidate, keep, session)
        except _AttemptFailed as e:
            if e.gated:
                _gated_until[candidate] = time.monotonic() + GATED_TTL_S
            failures.append(f"{candidate}: {e}")
            continue
        except subprocess.TimeoutExpired:
            note = f" (earlier: {' | '.join(failures)})" if failures else ""
            return False, f"ERROR: codex exec timed out after {TIMEOUT_S}s on {candidate}.{note}", None
        except FileNotFoundError:
            return False, f"ERROR: codex binary not found at {CODEX_BIN}. Install with `npm i -g @openai/codex`.", None
        except Exception as e:  # noqa: BLE001 -- surface, never crash the server
            failures.append(f"{candidate}: {type(e).__name__}: {e}")
            continue
        if candidate != model:
            text = f"[fallback: {candidate} answered after {'; '.join(failures)}]\n\n{text}"
        return True, text, session_id
    return False, "ERROR: all models failed -- " + " | ".join(failures), None


if __name__ == "__main__":
    mcp.run(transport="stdio")
