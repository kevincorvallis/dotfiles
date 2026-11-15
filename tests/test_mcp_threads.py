"""Behavioral tests for thread memory in the gemini and codex MCP servers.

No network, login or third-party package is needed: Codex is a fake CLI and
the Gemini SDK is a stand-in at its client boundary.

Run from the repository root with:
    python3 -m unittest discover -s tests -p 'test_mcp_threads.py' -v
"""

from __future__ import annotations

import asyncio
import copy
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import textwrap
import threading
import time
import types
import unittest
from unittest import mock


REPO = Path(__file__).resolve().parents[1]
MCP_DIR = REPO / ".config" / "mcp"


# This executable implements the `codex exec` command boundary as codex-cli
# 0.153.4 behaves (probed 2026-11-14), not wrapper internals:
#   - `--json` prints events on stdout, `thread.started` first, and reports a
#     failure as `error` + `turn.failed` events with exit code 1;
#   - without `--json` a failure is an `ERROR: {json}` line on stderr;
#   - `--ephemeral` keeps no session; `resume <id>` needs a kept session;
#   - a prompt that starts with a dash is read as a flag (exit code 2) unless
#     it follows `--`.
# A session answers with every prompt it has heard, so a reply shows its memory.
FAKE_CODEX = r'''
import json
import os
from pathlib import Path
import sys
import time
import uuid

state = Path(os.environ["FAKE_CODEX_STATE"])
scenario = json.loads((state / "scenario.json").read_text())
arguments = sys.argv[1:]

def value(flag):
    return arguments[arguments.index(flag) + 1] if flag in arguments else None

with (state / "calls.jsonl").open("a") as log:
    log.write(json.dumps(arguments) + "\n")
call_number = len((state / "calls.jsonl").read_text().splitlines())

resuming = arguments[:2] == ["exec", "resume"]
as_json = "--json" in arguments
model = value("-m")
if "--" in arguments:
    prompt = arguments[arguments.index("--") + 1]
else:
    prompt = arguments[-1]
    if prompt.startswith("-"):
        print("error: unexpected argument '%s' found" % prompt, file=sys.stderr)
        sys.exit(2)
sessions = state / "sessions"
session = arguments[2] if resuming else str(uuid.uuid4())

def emit(event):
    if as_json:
        print(json.dumps(event), flush=True)

def refuse(status, message):
    body = json.dumps({"type": "error", "status": status, "error": {"message": message}})
    if as_json:
        emit({"type": "error", "message": body})
        emit({"type": "turn.failed", "error": {"message": body}})
    else:
        print("ERROR: " + body, file=sys.stderr)
    sys.exit(1)

if resuming and not (sessions / session).exists():
    print("Error: thread/resume: thread/resume failed: no rollout found for thread id "
          + session + " (code -32600)", file=sys.stderr)
    sys.exit(1)

if not scenario.get("hide_session_id"):
    emit({"type": "thread.started", "thread_id": session})
emit({"type": "turn.started"})

if call_number == 1 and scenario.get("hold_first_call_until"):
    deadline = time.monotonic() + 10
    while not Path(scenario["hold_first_call_until"]).exists() and time.monotonic() < deadline:
        time.sleep(0.02)

if model in scenario.get("refused_models", []):
    refuse(400, "The '%s' model is not supported when using Codex with a ChatGPT account." % model)
if call_number <= scenario.get("failing_calls", 0):
    refuse(503, "The server is overloaded.")

heard = json.loads((sessions / session).read_text()) if resuming else []
heard.append(prompt)
if "--ephemeral" not in arguments:
    sessions.mkdir(exist_ok=True)
    (sessions / session).write_text(json.dumps(heard))
reply = "heard: " + " | ".join(heard)
emit({"type": "item.completed", "item": {"id": "item_0", "type": "agent_message", "text": reply}})
emit({"type": "turn.completed", "usage": {"input_tokens": 1, "output_tokens": 1}})
Path(value("-o")).write_text(reply)
'''


class FakeGemini:
    """google.genai.Client stand-in: records what each call sends, answers from a script."""

    def __init__(self):
        self.models = self
        self.answers = []
        self.sent = []
        self.failing = False
        self.hold = None  # an Event here blocks the next call until it is set
        self.entered = threading.Event()

    def generate_content(self, model, contents, config):
        self.sent.append({"model": model, "contents": copy.deepcopy(contents)})
        if self.failing:
            raise RuntimeError("service unavailable")
        answer = self.answers.pop(0)
        self.entered.set()
        if self.hold is not None:
            hold, self.hold = self.hold, None
            hold.wait(5)
        if isinstance(answer, Exception):
            raise answer
        return types.SimpleNamespace(text=answer)


def stub_packages(gemini_client=None):
    """Stand-ins for the servers' third-party imports: mcp, anyio and google-genai."""

    def module(name, **attributes):
        stub = types.ModuleType(name)
        for key, item in attributes.items():
            setattr(stub, key, item)
        return stub

    class FastMCP:
        def __init__(self, name):
            self.name = name

        def tool(self):
            return lambda function: function

    async def run_sync(function, *arguments):
        # Same contract as anyio.to_thread.run_sync: positional arguments only.
        return function(*arguments)

    to_thread = module("anyio.to_thread", run_sync=run_sync)
    genai_types = module(
        "google.genai.types",
        GenerateContentConfig=lambda **options: options,
        HttpOptions=lambda **options: options,
    )
    genai = module("google.genai", Client=lambda **options: gemini_client, types=genai_types)
    return {
        "mcp": module("mcp"),
        "mcp.server": module("mcp.server"),
        "mcp.server.fastmcp": module("mcp.server.fastmcp", FastMCP=FastMCP),
        "anyio": module("anyio", to_thread=to_thread),
        "anyio.to_thread": to_thread,
        "google": module("google", genai=genai),
        "google.genai": genai,
        "google.genai.types": genai_types,
    }


def load_server(filename):
    """Import a server file fresh, so each test starts with no threads."""
    spec = importlib.util.spec_from_file_location(filename[:-3].replace("-", "_"), MCP_DIR / filename)
    server = importlib.util.module_from_spec(spec)
    # Never leave a __pycache__ in .config/mcp: bootstrap deploys that directory.
    with mock.patch.object(sys, "dont_write_bytecode", True):
        spec.loader.exec_module(server)
    return server


def user(text):
    return {"role": "user", "parts": [{"text": text}]}


def model(text):
    return {"role": "model", "parts": [{"text": text}]}


class ServerTestCase(unittest.TestCase):
    def patch(self, patcher):
        patcher.start()
        self.addCleanup(patcher.stop)


class GeminiThreadTests(ServerTestCase):
    def setUp(self):
        self.gemini = FakeGemini()
        self.patch(mock.patch.dict(sys.modules, stub_packages(self.gemini)))
        self.patch(mock.patch.dict(os.environ, {
            "GEMINI_API_KEY": "test-key",
            "GOOGLE_API_KEY": "",
            "GOOGLE_CLOUD_PROJECT": "",
        }))
        self.server = load_server("gemini-mcp-server.py")

    def ask(self, prompt, **options):
        return asyncio.run(self.server.ask_gemini(prompt, **options))

    def test_second_call_on_a_thread_sends_the_earlier_turns(self):
        self.gemini.answers = ["Paris", "About two million"]
        self.ask("Capital of France?", thread_id="geo")
        self.ask("How many people live there?", thread_id="geo")
        self.assertEqual(self.gemini.sent[1]["contents"], [
            user("Capital of France?"),
            model("Paris"),
            user("How many people live there?"),
        ])

    def test_call_without_thread_id_sends_only_its_own_prompt(self):
        self.gemini.answers = ["one", "two"]
        self.ask("first")
        reply = self.ask("second")
        self.assertEqual(self.gemini.sent[1]["contents"], "second")
        self.assertEqual(reply, "two")

    def test_thread_names_keep_separate_history(self):
        self.gemini.answers = ["one", "two"]
        self.ask("first", thread_id="geo")
        self.ask("second", thread_id="history")
        self.assertEqual(self.gemini.sent[1]["contents"], [user("second")])

    def test_reply_names_the_thread_and_counts_turns(self):
        self.gemini.answers = ["one", "two"]
        first = self.ask("first", thread_id="geo")
        second = self.ask("second", thread_id="geo")
        self.assertEqual(first, "[thread: geo, turn 1]\n\none")
        self.assertEqual(second, "[thread: geo, turn 2]\n\ntwo")

    def test_failed_turn_is_not_remembered(self):
        self.gemini.answers = ["one", "three"]
        self.ask("first", thread_id="geo")
        self.gemini.failing = True
        failed = self.ask("second", thread_id="geo")
        self.gemini.failing = False
        self.ask("third", thread_id="geo")
        self.assertTrue(failed.startswith("ERROR:"), failed)
        self.assertEqual(self.gemini.sent[-1]["contents"], [user("first"), model("one"), user("third")])

    def test_fallback_note_stays_out_of_the_history(self):
        self.gemini.answers = [RuntimeError("model unavailable"), "one", "two"]
        first = self.ask("first", thread_id="geo")
        self.ask("second", thread_id="geo")
        self.assertIn("[fallback:", first)
        self.assertEqual(self.gemini.sent[-1]["contents"], [user("first"), model("one"), user("second")])

    def test_parallel_calls_on_one_thread_run_in_order(self):
        self.gemini.answers = ["one", "two"]
        release = self.gemini.hold = threading.Event()
        first = threading.Thread(target=self.ask, args=("first",), kwargs={"thread_id": "geo"})
        first.start()
        self.assertTrue(self.gemini.entered.wait(5))
        second = threading.Thread(target=self.ask, args=("second",), kwargs={"thread_id": "geo"})
        second.start()
        second.join(0.3)  # a call that does not wait for the first one finishes here
        release.set()
        first.join(5)
        second.join(5)
        self.assertEqual(self.gemini.sent[1]["contents"], [user("first"), model("one"), user("second")])


class CodexThreadTests(ServerTestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.state = Path(temporary.name)
        fake = self.state / "codex"
        fake.write_text("#!" + sys.executable + "\n" + textwrap.dedent(FAKE_CODEX))
        fake.chmod(0o700)
        self.scenario({})
        self.patch(mock.patch.dict(sys.modules, stub_packages()))
        self.patch(mock.patch.dict(os.environ, {
            "CODEX_BIN": str(fake),
            "FAKE_CODEX_STATE": str(self.state),
        }))
        self.server = load_server("codex-mcp-server.py")

    def scenario(self, values):
        (self.state / "scenario.json").write_text(json.dumps(values))

    def ask(self, prompt, **options):
        return asyncio.run(self.server.ask_gpt(prompt, **options))

    def calls(self):
        log = self.state / "calls.jsonl"
        return [json.loads(line) for line in log.read_text().splitlines()] if log.exists() else []

    def test_second_call_on_a_thread_continues_the_first_session(self):
        self.ask("remember 41", model="gpt-5.5", thread_id="design")
        reply = self.ask("which number?", model="gpt-5.5", thread_id="design")
        self.assertEqual(reply.splitlines()[-1], "heard: remember 41 | which number?")

    def test_call_without_thread_id_keeps_no_session(self):
        self.ask("first", model="gpt-5.5")
        reply = self.ask("second", model="gpt-5.5")
        self.assertEqual(reply, "heard: second")
        self.assertFalse((self.state / "sessions").exists())

    def test_thread_names_keep_separate_memory(self):
        self.ask("a", model="gpt-5.5", thread_id="one")
        self.ask("b", model="gpt-5.5", thread_id="two")
        reply = self.ask("c", model="gpt-5.5", thread_id="one")
        self.assertEqual(reply.splitlines()[-1], "heard: a | c")

    def test_reply_names_the_thread_and_counts_turns(self):
        first = self.ask("a", model="gpt-5.5", thread_id="design")
        second = self.ask("b", model="gpt-5.5", thread_id="design")
        self.assertEqual(first, "[thread: design, turn 1]\n\nheard: a")
        self.assertEqual(second, "[thread: design, turn 2]\n\nheard: a | b")

    def test_later_turns_stay_read_only(self):
        self.ask("a", model="gpt-5.5", thread_id="design")
        self.ask("b", model="gpt-5.5", thread_id="design")
        resumed = self.calls()[1]
        self.assertEqual(resumed[:2], ["exec", "resume"])
        self.assertIn(("-c", 'sandbox_mode="read-only"'), list(zip(resumed, resumed[1:])))

    def test_every_call_skips_the_uploads_and_catalog_fetches(self):
        self.ask("a", model="gpt-5.5")
        self.ask("b", model="gpt-5.5", thread_id="design")
        self.ask("c", model="gpt-5.5", thread_id="design")
        calls = self.calls()
        self.assertEqual(len(calls), 3)  # one-shot, new thread, resumed thread
        for call in calls:
            pairs = list(zip(call, call[1:]))
            for flag in [
                ("-c", "analytics.enabled=false"),
                ("-c", 'otel.metrics_exporter="none"'),
                ("--disable", "apps"),
                ("--disable", "plugins"),
                ("--disable", "remote_plugin"),
            ]:
                self.assertIn(flag, pairs, call[:2])

    def test_prompt_that_starts_with_a_dash_is_still_the_prompt(self):
        one_shot = self.ask("- a", model="gpt-5.5")
        self.ask("- b", model="gpt-5.5", thread_id="design")
        resumed = self.ask("--help", model="gpt-5.5", thread_id="design")
        self.assertEqual(one_shot, "heard: - a")
        self.assertEqual(resumed.splitlines()[-1], "heard: - b | --help")

    def test_failed_first_turn_leaves_no_thread_behind(self):
        self.scenario({"failing_calls": 1})
        failed = self.ask("a", model="gpt-5.5", thread_id="design")
        reply = self.ask("b", model="gpt-5.5", thread_id="design")
        self.assertTrue(failed.startswith("ERROR:"), failed)
        self.assertEqual(reply, "[thread: design, turn 1]\n\nheard: b")

    def test_thread_continues_on_the_fallback_model(self):
        self.scenario({"refused_models": ["gpt-6-astra"]})
        self.ask("a", thread_id="design")
        reply = self.ask("b", thread_id="design")
        self.assertEqual(reply.splitlines()[-1], "heard: a | b")

    def test_refusal_in_a_thread_is_reported_and_remembered(self):
        self.scenario({"refused_models": ["gpt-6-astra"]})
        first = self.ask("a", thread_id="design")
        self.ask("b", thread_id="design")
        self.assertIn("HTTP 400: The 'gpt-6-astra' model is not supported", first)
        self.assertEqual(len([call for call in self.calls() if "gpt-6-astra" in call]), 1)

    def test_missing_session_id_is_reported(self):
        self.scenario({"hide_session_id": True})
        first = self.ask("a", model="gpt-5.5", thread_id="design")
        second = self.ask("b", model="gpt-5.5", thread_id="design")
        self.assertEqual(first, "[thread: design, turn 1, not saved: codex gave no session id]\n\nheard: a")
        self.assertEqual(second.splitlines()[-1], "heard: b")

    def test_parallel_calls_on_one_thread_run_in_order(self):
        release = self.state / "release"
        self.scenario({"hold_first_call_until": str(release)})
        replies = {}

        def ask(prompt):
            replies[prompt] = self.ask(prompt, model="gpt-5.5", thread_id="design")

        first = threading.Thread(target=ask, args=("first",))
        first.start()
        deadline = time.monotonic() + 10
        while not self.calls() and time.monotonic() < deadline:
            time.sleep(0.02)
        second = threading.Thread(target=ask, args=("second",))
        second.start()
        second.join(0.5)  # a call that does not wait for the first one finishes here
        release.write_text("")
        first.join(15)
        second.join(15)
        self.assertEqual(replies["second"].splitlines()[-1], "heard: first | second")


if __name__ == "__main__":
    unittest.main()
