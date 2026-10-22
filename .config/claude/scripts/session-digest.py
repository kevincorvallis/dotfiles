#!/usr/bin/env python3
"""Render the current Claude Code session transcript as plain text for an
external model (Gemini / GPT). Used by the /advisor-x slash command.

Usage:
    session-digest.py [--cwd PATH] [--turns N] [--max-chars N] [--session FILE]

Finds this session's .jsonl in the project dir for --cwd (default: $PWD) via
CLAUDE_CODE_SESSION_ID, and prints a readable, secret-scrubbed digest to stdout.

Python 3.10 compatible. Read-only.
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

PROJECTS = Path.home() / ".claude" / "projects"

# Anything matching these is replaced before the text leaves the machine.
SECRET_PATTERNS = [
    (re.compile(r"\b(gh[pousr]_[A-Za-z0-9]{20,})"), "[REDACTED_GITHUB_TOKEN]"),
    (re.compile(r"\b(sk-[A-Za-z0-9_\-]{20,})"), "[REDACTED_API_KEY]"),
    (re.compile(r"\b(AIza[A-Za-z0-9_\-]{30,})"), "[REDACTED_GOOGLE_KEY]"),
    (re.compile(r"\b(xox[abposr]-[A-Za-z0-9\-]{10,})"), "[REDACTED_SLACK_TOKEN]"),
    (re.compile(r"\b(ya29\.[A-Za-z0-9_\-]{20,})"), "[REDACTED_OAUTH_TOKEN]"),
    (re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----", re.S),
     "[REDACTED_PRIVATE_KEY]"),
    (re.compile(r"(?i)\b(api[_-]?key|secret|password|passwd|token)\s*[=:]\s*['\"]?([^\s'\"]{12,})"),
     r"\1=[REDACTED]"),
]


def scrub(text: str) -> str:
    for pat, repl in SECRET_PATTERNS:
        text = pat.sub(repl, text)
    return text


def project_dir(cwd: str) -> Path:
    """Claude Code slugifies the cwd: non-alphanumerics -> '-'."""
    slug = re.sub(r"[^a-zA-Z0-9]", "-", os.path.abspath(cwd))
    return PROJECTS / slug


def find_session(cwd: str, allow_guess: bool) -> Path:
    """Locate THIS session's transcript.

    Claude Code exports CLAUDE_CODE_SESSION_ID into every Bash call, so the
    right file is knowable exactly. Do not fall back to newest-mtime silently:
    one project dir can have 6+ concurrent sessions whose mtimes tie to the
    second, and picking wrong means sending someone else's conversation to an
    external API. Verified 2026-08-11: three transcripts shared one mtime and
    newest-mtime selected an unrelated session.
    """
    d = project_dir(cwd)
    if not d.is_dir():
        sys.exit(f"ERROR: no transcript dir for cwd {cwd} (looked in {d})")

    sid = os.environ.get("CLAUDE_CODE_SESSION_ID") or os.environ.get(
        "CODEX_COMPANION_SESSION_ID"
    )
    if sid:
        candidate = d / f"{sid}.jsonl"
        if candidate.is_file():
            return candidate
        sys.exit(
            f"ERROR: CLAUDE_CODE_SESSION_ID={sid} but {candidate} does not exist.\n"
            f"       The cwd may not match the session's project dir."
        )

    files = sorted(d.glob("*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not files:
        sys.exit(f"ERROR: no .jsonl transcripts in {d}")
    if not allow_guess:
        sys.exit(
            "ERROR: CLAUDE_CODE_SESSION_ID is not set, so the current session\n"
            "       cannot be identified. Refusing to guess — newest-mtime picks\n"
            "       the wrong transcript when sessions run concurrently.\n"
            "       Pass --session <path> explicitly, or --allow-guess to accept\n"
            f"       the newest ({files[0].name}) and its risk."
        )
    print(f"WARNING: guessing session by mtime -> {files[0].name}", file=sys.stderr)
    return files[0]


def clip(text: str, limit: int) -> str:
    text = text.strip()
    if len(text) <= limit:
        return text
    return text[:limit] + f"\n... [clipped {len(text) - limit} chars]"


def block_text(block, tool_limit: int) -> str:
    """Render one content block. Returns '' for blocks we intentionally drop."""
    if isinstance(block, str):
        return block
    kind = block.get("type")
    if kind == "text":
        return block.get("text", "")
    if kind == "thinking":
        # Signatures are opaque blobs; the visible reasoning is what matters.
        return ""
    if kind == "tool_use":
        name = block.get("name", "?")
        args = json.dumps(block.get("input", {}), ensure_ascii=False)
        return f"[tool: {name}] {clip(args, tool_limit)}"
    if kind == "tool_result":
        content = block.get("content")
        if isinstance(content, list):
            content = "\n".join(
                b.get("text", "") for b in content if isinstance(b, dict) and b.get("type") == "text"
            )
        return f"[tool result] {clip(str(content or ''), tool_limit)}"
    if kind == "image":
        return "[image omitted]"
    return ""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cwd", default=os.getcwd())
    ap.add_argument("--session", help="explicit .jsonl path, skips cwd lookup")
    ap.add_argument("--turns", type=int, default=80, help="keep the last N messages")
    ap.add_argument("--max-chars", type=int, default=140000, help="hard cap on output")
    ap.add_argument("--tool-limit", type=int, default=1500, help="per tool call/result clip")
    ap.add_argument(
        "--allow-guess",
        action="store_true",
        help="accept the newest-mtime transcript when the session ID is unavailable",
    )
    args = ap.parse_args()

    path = Path(args.session) if args.session else find_session(args.cwd, args.allow_guess)

    entries = []
    with path.open() as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue  # partial trailing write on a live session

    rendered = []
    for e in entries:
        if e.get("type") not in ("user", "assistant"):
            continue
        msg = e.get("message") or {}
        role = msg.get("role", e.get("type"))
        content = msg.get("content")
        if isinstance(content, str):
            parts = [content]
        elif isinstance(content, list):
            parts = [block_text(b, args.tool_limit) for b in content]
        else:
            continue
        body = "\n".join(p for p in parts if p and p.strip())
        if not body.strip():
            continue
        if "<local-command-caveat>" in body:
            continue
        rendered.append(f"### {role.upper()}\n{body}")

    kept = rendered[-args.turns:]
    dropped = len(rendered) - len(kept)

    header = [
        f"# Claude Code session transcript",
        f"session: {path.name}",
        f"cwd: {args.cwd}",
        f"messages: {len(kept)} shown"
        + (f" ({dropped} earlier messages omitted)" if dropped else ""),
        "",
    ]
    out = "\n".join(header) + "\n\n".join(kept)
    out = scrub(out)

    if len(out) > args.max_chars:
        # Trim from the front — recent context matters most to an advisor.
        out = (
            "\n".join(header)
            + "[earlier transcript truncated to fit budget]\n\n"
            + out[-args.max_chars:]
        )

    sys.stdout.write(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
