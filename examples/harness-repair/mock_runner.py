#!/usr/bin/env python3
"""Scripted stand-in for a model. It is not a language model.

It returns ANSWER: 0 while the harness does not say "use the calc tool".
After that phrase is present it calls calc or read_file, then copies the
tool result into an ANSWER line. When asked to edit the harness, it writes
that phrase once and then stops.

Stdout is one JSON object, which is the command-runner protocol.
"""

from __future__ import annotations

import json
import re
import sys


SYSTEM = (
    "Use the calc tool for arithmetic. "
    "Use the read_file tool to read a workspace file. "
    "After a tool result, reply with one line of the form ANSWER: value.\n"
)
DONE = "The last line must be ANSWER: followed by the tool value.\n"
EXPR = re.compile(r"-?\d+\s*[+*/-]\s*-?\d+")


def emit(obj):
    obj.setdefault("usage", {"input_tokens": 8, "output_tokens": 4, "cost_usd": 0})
    json.dump(obj, sys.stdout)
    sys.stdout.write("\n")


def main():
    req = json.load(sys.stdin)
    if req.get("role") == "optimizer":
        blob = json.dumps(req)
        if "Never use tools" in blob:
            emit({
                "content": json.dumps({
                    "hypothesis": "Tell the agent to call calc or read_file and then write ANSWER.",
                    "files": {"system.md": SYSTEM, "done.md": DONE},
                })
            })
        else:
            emit({"content": json.dumps({"hypothesis": "No further edit.", "files": {}})})
        return

    system = (req.get("system") or "").lower()
    if "calc tool" not in system:
        emit({"content": "ANSWER: 0"})
        return

    messages = req.get("messages") or []
    last = messages[-1] if messages else {}
    if last.get("role") == "tool":
        emit({"content": "ANSWER: " + (last.get("content") or "").strip()})
        return

    text = last.get("content") or ""
    match = EXPR.search(text)
    if match:
        emit({
            "content": "",
            "tool_calls": [{
                "id": "calc-1",
                "name": "calc",
                "arguments": {"expression": match.group(0)},
            }],
        })
        return
    if "note.txt" in text:
        emit({
            "content": "",
            "tool_calls": [{
                "id": "read-1",
                "name": "read_file",
                "arguments": {"path": "note.txt"},
            }],
        })
        return
    emit({"content": "ANSWER: unknown"})


if __name__ == "__main__":
    main()
