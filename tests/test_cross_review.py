"""Behavioral tests for cross-review; all model calls use an isolated fake CLI.

Run from the repository root with:
    python3 -m unittest discover -s tests -p 'test_cross_review.py' -v
"""

from __future__ import annotations

import json
import hashlib
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import textwrap
import time
import unittest


REPO = Path(__file__).resolve().parents[1]
RUNNER = REPO / "bin" / "cross-review"
CLAUDE_MODEL = "claude-test"
GEMINI_MODEL = "gemini-test"


# This executable implements the documented Cursor command boundary, not runner
# internals. Every process writes one atomic event record so the parent test can
# distinguish catalogue requests from model calls and inspect literal arguments.
FAKE_CURSOR = r'''
import json
import os
from pathlib import Path
import sys
import time
import subprocess

scenario = json.loads(Path(os.environ["FAKE_CURSOR_SCENARIO"]).read_text())
state = Path(os.environ["FAKE_CURSOR_STATE"])
arguments = sys.argv[1:]

def record(**values):
    values["time"] = time.monotonic()
    values["workspace"] = str(Path.cwd())
    for field, variable, filename in (
            ("config_directory", "CURSOR_CONFIG_DIR", "selection.json"),
            ("data_directory", "CURSOR_DATA_DIR", "sessions.json")):
        location = os.environ.get(variable)
        values[field] = location
        values[field + "_mode"] = None
        if location:
            directory = Path(location)
            # Emulate CLI preference writes only inside this test's own tree.
            if directory.resolve().is_relative_to(state.parent.resolve()) and directory.is_dir():
                values[field + "_mode"] = directory.stat().st_mode & 0o777
                (directory / filename).write_text("Synthetic CLI preference write\n")
    data = (json.dumps(values) + "\n").encode()
    descriptor = os.open(os.environ["FAKE_CURSOR_LOG"],
                         os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
    try:
        os.write(descriptor, data)
    finally:
        os.close(descriptor)

def emit(value):
    print(json.dumps(value), flush=True)

if "--version" in arguments:
    record(kind="version", arguments=arguments)
    print(scenario.get("version", "fixture-cursor-1.0.0"))
    sys.exit(0)

if "models" in arguments or "--list-models" in arguments:
    record(kind="catalogue", arguments=arguments)
    if scenario.get("catalogue_error"):
        print("Synthetic catalogue failure", file=sys.stderr)
        sys.exit(9)
    for model in scenario.get("models", ["claude-test", "gemini-test"]):
        label = scenario.get("model_labels", {}).get(model, model + " fixture")
        print(model + " - " + label)
    sys.exit(0)

model = None
for index, argument in enumerate(arguments):
    if argument == "--model" and index + 1 < len(arguments):
        model = arguments[index + 1]
    elif argument.startswith("--model="):
        model = argument.split("=", 1)[1]
if model is None:
    record(kind="unexpected", arguments=arguments)
    print("Fake CLI requires an explicit model", file=sys.stderr)
    sys.exit(10)

if "--trust" not in arguments:
    record(kind="trust-required", model=model, arguments=arguments)
    print("Workspace Trust Required: synthetic workspace was not explicitly trusted",
          file=sys.stderr, flush=True)
    sys.exit(13)

first_call = state / (model + ".first")
try:
    first_call.mkdir()
    stage = "review"
except FileExistsError:
    stage = "reconcile"
configuration_file = Path.cwd() / ".cursor" / "cli.json"
configuration = (json.loads(configuration_file.read_text())
                 if configuration_file.exists() else {})
record(kind="model", model=model, stage=stage, arguments=arguments,
       workspace=str(Path.cwd()), configuration=configuration,
       direnv_disabled=os.environ.get("DIRENV_DISABLE"))

if stage == "review" and scenario.get("require_parallel"):
    (state / (model + ".ready")).touch()
    deadline = time.monotonic() + 3
    while not all((state / (name + ".ready")).exists()
                  for name in scenario.get("models", [])):
        if time.monotonic() >= deadline:
            print("Review peers did not start in parallel", file=sys.stderr)
            sys.exit(11)
        time.sleep(0.01)

behavior = scenario.get("behaviors", {}).get(
    stage + ":" + model, scenario.get("behaviors", {}).get(model, "success"))
reported_model = scenario.get("reported_models", {}).get(model, model)
if behavior == "wrong-model":
    reported_model = "unexpected-model"
if behavior == "display-model":
    reported_model = model + " fixture"
if behavior != "missing-init":
    emit({"type": "system", "subtype": "init", "model": reported_model,
          "session_id": "fixture-" + model + "-" + stage})

if behavior in ("timeout", "child-timeout"):
    if behavior == "child-timeout":
        child_program = ("import time; from pathlib import Path; time.sleep(1.5); "
                         "Path(" + repr(str(state / "orphan-ran")) + ").write_text('orphan')")
        child = subprocess.Popen([sys.executable, "-c", child_program])
        record(kind="child", pid=child.pid)
    print("Synthetic call started before timeout", file=sys.stderr, flush=True)
    time.sleep(60)
    sys.exit(12)
if behavior == "cli-error":
    print("Synthetic provider unavailable", file=sys.stderr, flush=True)
    emit({"type": "result", "subtype": "error", "is_error": True,
          "error": "Synthetic provider unavailable", "model": reported_model})
    sys.exit(7)
if behavior == "reported-error":
    emit({"type": "result", "subtype": "error", "is_error": True,
          "result": "Synthetic provider error", "model": reported_model})
    sys.exit(0)
if behavior == "malformed-events":
    print("not a JSON event", flush=True)
    sys.exit(0)
if behavior == "tool-call":
    emit({"type": "tool_call", "subtype": "started",
          "tool_call": {"name": "shell", "arguments": "never executed"}})

if stage == "reconcile":
    result = {"verdict": "Synthetic synthesis",
              "agreements": ["Both reviewers checked the fixture"],
              "disagreements": ["Reviewers differ on fixture priority"],
              "recommendations": ["Verify the fixture independently"],
              "tests": ["Run the fixture checks"],
              "limitations": ["These are synthetic reviews"]}
else:
    result = {"verdict": model + " fixture verdict",
              "assumptions": ["Only supplied fixture context is available"],
              "findings": [{"severity": "medium", "title": model + " finding",
                            "evidence": "Fixture line 1",
                            "recommendation": "Validate the fixture"}],
              "tests": ["Check the fixture"]}
if behavior == "invalid-schema":
    result = {"verdict": "Missing required review fields"}
answer = "not JSON review content" if behavior == "malformed-result" else json.dumps(result)
emit({"type": "assistant", "message": {"role": "assistant", "content": [
    {"type": "text", "text": answer}]}})
terminal = {"type": "result", "subtype": "success", "is_error": False,
            "result": answer, "model": reported_model,
            "session_id": "fixture-" + model + "-" + stage}
if behavior == "session-mismatch":
    terminal["session_id"] = "a-different-session"
if behavior == "wrong-result-model":
    terminal["model"] = "unexpected-result-model"
emit(terminal)
if behavior == "duplicate-terminal":
    emit(terminal)
record(kind="finished", model=model, stage=stage)
'''


class CrossReviewTests(unittest.TestCase):
    """Each test has a fresh catalogue, CLI, workspace, and output location."""

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="cross-review-test-")
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name)
        self.state = self.directory / "fake state"
        self.state.mkdir()
        self.runner_temp = self.directory / "temporary workspaces"
        self.runner_temp.mkdir()
        self.log = self.directory / "calls.jsonl"
        self.scenario_file = self.directory / "scenario.json"
        self.fake = self.directory / "fake cursor"
        self.fake.write_text("#!" + sys.executable + "\n" + textwrap.dedent(FAKE_CURSOR))
        self.fake.chmod(0o700)
        self.brief = self.directory / "review brief.md"
        self.brief.write_text("Review this synthetic implementation for correctness.\n")
        self.output = self.directory / "review output"
        self.scenario = {"models": [CLAUDE_MODEL, GEMINI_MODEL], "behaviors": {}}
        # Do not forward the caller's credentials or model configuration.
        self.environment = {
            "PATH": os.defpath,
            "LANG": "en_US.UTF-8",
            "TMPDIR": str(self.runner_temp),
            "CROSS_REVIEW_CURSOR": str(self.fake),
            "FAKE_CURSOR_SCENARIO": str(self.scenario_file),
            "FAKE_CURSOR_LOG": str(self.log),
            "FAKE_CURSOR_STATE": str(self.state),
        }

    def run_cli(self, arguments, *, timeout=15):
        self.scenario_file.write_text(json.dumps(self.scenario))
        return subprocess.run(
            [sys.executable, str(RUNNER), *arguments],
            cwd=self.directory,
            env=self.environment,
            input="",
            capture_output=True,
            text=True,
            timeout=timeout,
        )

    def run_review(self, *arguments, timeout=15):
        return self.run_cli([
            "run", str(self.brief), "--output", str(self.output),
            "--claude-model", CLAUDE_MODEL, "--gemini-model", GEMINI_MODEL,
            "--timeout", "5", *arguments,
        ], timeout=timeout)

    def calls(self, kind=None):
        if not self.log.exists():
            return []
        values = [json.loads(line) for line in self.log.read_text().splitlines()]
        return [value for value in values if kind is None or value["kind"] == kind]

    def clear_fake_history(self):
        for marker in self.state.iterdir():
            if marker.is_dir():
                marker.rmdir()
            else:
                marker.unlink()
        if self.log.exists():
            self.log.unlink()

    def configure_observed_model_label(self, *, version="2026.10.22-27dcf5f",
                                       requested="claude-opus-5-5-medium",
                                       catalogue="Claude Opus 5.5 1M",
                                       reported="Claude Opus 5.5 300K Medium"):
        self.scenario.update(version=version, models=[requested, GEMINI_MODEL],
                             model_labels={requested: catalogue},
                             reported_models={requested: reported})
        return requested

    def json_output(self, relative):
        artifact = self.output / relative
        self.assertTrue(artifact.is_file(), str(artifact))
        return json.loads(artifact.read_text())

    def assert_success(self, result):
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def assert_failed(self, result):
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)

    def assert_temporary_client_storage(self, calls):
        self.assertTrue(calls)
        for call in calls:
            workspace = Path(call["workspace"]).resolve()
            self.assertTrue(workspace.is_relative_to(self.runner_temp.resolve()))
            for field in ("config_directory", "data_directory"):
                self.assertIsNotNone(call[field])
                storage = Path(call[field]).resolve()
                self.assertEqual(storage.parent, workspace)
                self.assertEqual(call[field + "_mode"], 0o700)
                self.assertFalse(storage.exists(), "Temporary CLI state was not removed")
            self.assertNotEqual(call["config_directory"], call["data_directory"])

    def test_models_lists_exact_catalogue_without_model_calls(self):
        result = self.run_cli(["models"])
        self.assert_success(result)
        self.assertIn(CLAUDE_MODEL, result.stdout)
        self.assertIn(GEMINI_MODEL, result.stdout)
        self.assertEqual(len(self.calls("catalogue")), 1)
        self.assertEqual(self.calls("model"), [])
        self.assert_temporary_client_storage(self.calls())

    def test_parallel_reviews_and_synthesis_keep_provenance(self):
        self.scenario["require_parallel"] = True
        result = self.run_review()
        self.assert_success(result)
        model_calls = self.calls("model")
        independent = [call for call in model_calls if call["stage"] == "review"]
        reconciliations = [call for call in model_calls if call["stage"] == "reconcile"]
        self.assertEqual({call["model"] for call in independent},
                         {CLAUDE_MODEL, GEMINI_MODEL})
        self.assertEqual(len(independent), 2)
        self.assertEqual(len(reconciliations), 1)
        first_finished = min(call["time"] for call in self.calls("finished")
                             if call["stage"] == "review")
        self.assertTrue(all(call["time"] < first_finished for call in independent))
        for stage, model in (("claude", CLAUDE_MODEL), ("gemini", GEMINI_MODEL)):
            self.assertEqual(self.json_output(stage + "/review.json")["verdict"],
                             model + " fixture verdict")
            metadata = self.json_output(stage + "/metadata.json")
            self.assertIn(model, json.dumps(metadata))
            self.assertTrue((self.output / stage / "events.jsonl").is_file())
            self.assertTrue((self.output / stage / "stderr.log").is_file())
            self.assertIn(model + " finding", (self.output / stage / "review.md").read_text())
        manifest = json.dumps(self.json_output("manifest.json"))
        self.assertIn(CLAUDE_MODEL, manifest)
        self.assertIn(GEMINI_MODEL, manifest)
        self.assertEqual(self.json_output("manifest.json")["mode"], "design")
        self.assertEqual((self.output / "brief.md").read_text(), self.brief.read_text())
        self.assertIn("Synthetic synthesis", (self.output / "report.md").read_text())
        synthesis_prompt = "\n".join(reconciliations[0]["arguments"])
        self.assertIn(CLAUDE_MODEL + " fixture verdict", synthesis_prompt)
        self.assertIn(GEMINI_MODEL + " fixture verdict", synthesis_prompt)

    def test_modes_reach_both_reviewers_and_reconciliation_with_frozen_evidence(self):
        prompt_hashes = set()
        for mode in ("design", "planning", "ui", "adversarial", "code"):
            with self.subTest(mode=mode):
                self.clear_fake_history()
                self.output = self.directory / ("mode-" + mode)
                result = self.run_review("--mode", mode)
                self.assert_success(result)
                manifest = self.json_output("manifest.json")
                self.assertEqual(manifest["mode"], mode)
                self.assertEqual(manifest["brief_sha256"], hashlib.sha256(self.brief.read_bytes()).hexdigest())
                self.assertEqual((self.output / "brief.md").read_bytes(), self.brief.read_bytes())
                prompt = (self.output / "prompt.txt").read_text()
                self.assertEqual(manifest["prompt_sha256"], hashlib.sha256(prompt.encode()).hexdigest())
                prompt_hashes.add(manifest["prompt_sha256"])
                calls = self.calls("model")
                self.assertEqual(len(calls), 3)
                for call in calls:
                    stage = "reconcile" if call["stage"] == "reconcile" else (
                        "claude" if call["model"] == CLAUDE_MODEL else "gemini")
                    dispatched_prompt = call["arguments"][-1]
                    self.assertEqual(dispatched_prompt, (self.output / stage / "prompt.txt").read_text())
                    self.assertIn("Review mode: " + mode + "\n", dispatched_prompt)
                    self.assertIn(self.brief.read_text(), dispatched_prompt)
                    if call["stage"] == "review":
                        self.assertEqual(dispatched_prompt, prompt)
                    else:
                        self.assertIn(CLAUDE_MODEL + " fixture verdict", dispatched_prompt)
                        self.assertIn(GEMINI_MODEL + " fixture verdict", dispatched_prompt)
                    metadata = self.json_output(stage + "/metadata.json")
                    self.assertEqual(metadata["mode"], mode)
                    self.assertEqual(metadata["prompt_sha256"], hashlib.sha256(dispatched_prompt.encode()).hexdigest())
                    self.assertIn("Review mode: `" + mode + "`", (self.output / stage / "review.md").read_text())
                    # Analysis modes never alter Cursor's read-only invocation.
                    self.assertIn("--mode=ask", call["arguments"])
                    self.assertEqual(call["arguments"][call["arguments"].index("--sandbox") + 1], "enabled")
                    self.assertEqual(call["configuration"]["permissions"]["allow"], [])
                    self.assertTrue({"Shell(*)", "Write(**)", "Read(**)", "WebFetch(*)", "Mcp(*:*)"}
                                    .issubset(set(call["configuration"]["permissions"]["deny"])))
                self.assertIn("Review mode: `" + mode + "`", (self.output / "report.md").read_text())
        self.assertEqual(len(prompt_hashes), 5, "The selected mode must change the actual model input")

    def test_planning_can_propose_a_plan_without_changing_the_review_schema(self):
        self.brief.write_text("Objective: sync profile settings across two Macs. Constraints: offline operation; no draft plan exists.\n")
        self.assert_success(self.run_review("--mode", "planning"))
        for stage in ("claude", "gemini"):
            prompt = (self.output / stage / "prompt.txt").read_text()
            self.assertIn("even if no draft plan is", prompt)
            self.assertIn("ordered steps, prerequisites, dependencies", prompt)
            self.assertIn("Compare at least one plausible alternative", prompt)
            self.assertIn("findings[].recommendation", prompt)
            self.assertIn("do not manufacture defects", prompt)
            self.assertEqual(set(self.json_output(stage + "/review.json")),
                             {"verdict", "assumptions", "findings", "tests"})
        synthesis = (self.output / "reconcile/prompt.txt").read_text()
        self.assertIn("preferred ordered plan and alternatives in recommendations", synthesis)
        self.assertNotIn("findings[].recommendation", synthesis)
        self.assertEqual(set(self.json_output("reconcile/review.json")),
                         {"verdict", "agreements", "disagreements", "recommendations", "tests", "limitations"})

    def test_ui_mode_uses_written_evidence_without_loading_screenshot_references(self):
        absent_screenshot = self.directory / "screenshot-not-supplied.png"
        self.brief.write_text("UI observation: the confirmation is missing. Screenshot reference: " + str(absent_screenshot) + "\n")
        self.assert_success(self.run_review("--mode", "ui"))
        self.assertFalse(absent_screenshot.exists())
        for call in self.calls("model"):
            prompt = call["arguments"][-1]
            self.assertIn("No images or attachments are sent", prompt)
            self.assertIn("screenshot paths and URLs are references, not pixels", prompt)
            self.assertIn("DOM/accessibility excerpts", prompt)
            self.assertNotIn(str(absent_screenshot), call["arguments"][:-1])
        report = (self.output / "report.md").read_text()
        self.assertIn("no screenshot pixels were inspected", report)

    def test_unknown_mode_is_rejected_before_catalogue_or_output_creation(self):
        result = self.run_review("--mode", "execute")
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn("invalid choice", result.stderr)
        self.assertEqual(self.calls(), [])
        self.assertFalse(self.output.exists())

    def test_each_model_gets_a_separate_workspace_with_tools_denied(self):
        original_config = self.directory / "original cursor configuration"
        original_data = self.directory / "original cursor data"
        for directory, filename in ((original_config, "selection.json"),
                                    (original_data, "sessions.json")):
            directory.mkdir()
            (directory / filename).write_text("Existing preference must remain unchanged\n")
        self.environment["CURSOR_CONFIG_DIR"] = str(original_config)
        self.environment["CURSOR_DATA_DIR"] = str(original_data)
        result = self.run_review()
        self.assert_success(result)
        calls = self.calls("model")
        self.assert_temporary_client_storage(self.calls())
        self.assertEqual(len({call["config_directory"] for call in calls}), 3)
        self.assertEqual(len({call["data_directory"] for call in calls}), 3)
        self.assertEqual((original_config / "selection.json").read_text(),
                         "Existing preference must remain unchanged\n")
        self.assertEqual((original_data / "sessions.json").read_text(),
                         "Existing preference must remain unchanged\n")
        workspaces = {call["workspace"] for call in calls}
        self.assertEqual(len(workspaces), 3)
        self.assertNotIn(str(self.directory), workspaces)
        for call in calls:
            arguments = call["arguments"]
            self.assertIn("--trust", arguments)
            workspace = Path(call["workspace"])
            workspace_index = arguments.index("--workspace")
            self.assertEqual(Path(arguments[workspace_index + 1]).resolve(), workspace.resolve())
            self.assertTrue(workspace.resolve().is_relative_to(self.runner_temp.resolve()))
            self.assertFalse(workspace.exists(), "Trusted temporary workspace was not removed")
            self.assertNotEqual(workspace.resolve(), self.directory.resolve())
            self.assertFalse(workspace.resolve().is_relative_to(self.output.resolve()))
            options = {argument.split("=", 1)[0] for argument in arguments}
            self.assertFalse(options & {"--force", "-f", "--yolo", "--approve-mcps"})
            self.assertEqual(call["direnv_disabled"], "1")
            permissions = call["configuration"].get("permissions", {})
            self.assertEqual(permissions.get("allow"), [])
            self.assertTrue({"Shell(*)", "Write(**)", "Read(**)", "WebFetch(*)", "Mcp(*:*)"}
                            .issubset(set(permissions.get("deny", []))))
            self.assertIn("--mode=ask", arguments)
            sandbox_index = arguments.index("--sandbox")
            self.assertEqual(arguments[sandbox_index + 1], "enabled")

    def test_unavailable_exact_model_stops_before_any_model_call(self):
        # A similarly named model must never satisfy the requested exact ID.
        self.scenario["models"] = [CLAUDE_MODEL + "-latest", GEMINI_MODEL]
        result = self.run_review()
        self.assert_failed(result)
        self.assertEqual(self.calls("model"), [])
        self.assertIn(CLAUDE_MODEL, result.stdout + result.stderr)

    def test_catalogue_failure_never_starts_a_model(self):
        self.scenario["catalogue_error"] = True
        result = self.run_review()
        self.assert_failed(result)
        self.assertEqual(self.calls("model"), [])

    def test_failed_review_preserves_successful_peer_and_raw_evidence(self):
        for behavior in ("wrong-model", "malformed-events", "malformed-result",
                         "invalid-schema", "cli-error", "reported-error",
                         "missing-init", "session-mismatch", "duplicate-terminal",
                         "tool-call", "wrong-result-model"):
            with self.subTest(behavior=behavior):
                self.output = self.directory / ("result-" + behavior)
                self.clear_fake_history()
                self.scenario["behaviors"] = {GEMINI_MODEL: behavior}
                result = self.run_review()
                self.assert_failed(result)
                self.assertEqual(self.json_output("claude/review.json")["verdict"],
                                 CLAUDE_MODEL + " fixture verdict")
                self.assertTrue((self.output / "gemini/events.jsonl").is_file())
                self.assertTrue((self.output / "gemini/stderr.log").is_file())
                self.assertTrue(self.json_output("gemini/metadata.json"))
                self.assertTrue(self.json_output("manifest.json"))
                self.assertFalse(any(call["stage"] == "reconcile"
                                     for call in self.calls("model")))

    def test_catalogue_display_name_is_retained_as_reported_model(self):
        self.scenario["behaviors"] = {GEMINI_MODEL: "display-model"}
        result = self.run_review("--no-reconcile")
        self.assert_success(result)
        metadata = self.json_output("gemini/metadata.json")
        self.assertEqual(metadata["requested_model"], GEMINI_MODEL)
        self.assertEqual(metadata["reported_model"], GEMINI_MODEL + " fixture")

    def test_observed_runtime_alias_is_version_scoped_and_discloses_context_difference(self):
        requested = self.configure_observed_model_label(catalogue="Claude Opus 5.5 1M (current)")
        result = self.run_review("--claude-model", requested, "--no-reconcile")
        self.assert_success(result)
        metadata = self.json_output("claude/metadata.json")
        self.assertEqual(metadata["requested_model"], requested)
        self.assertEqual(metadata["catalogue_label"], "Claude Opus 5.5 1M")
        self.assertEqual(metadata["reported_model"], "Claude Opus 5.5 300K Medium")
        self.assertEqual(metadata["cursor_version"], "2026.10.22-27dcf5f")
        self.assertEqual(metadata["model_verification"], "known_runtime_label")
        note = metadata["model_label_note"]
        self.assertIn("Claude Opus 5.5 1M", note)
        self.assertIn("Claude Opus 5.5 300K Medium", note)
        self.assertIn("not independent proof", note)
        self.assertIn(note, (self.output / "claude/review.md").read_text())

    def test_runtime_alias_rejects_changes_to_any_verified_component(self):
        variants = {
            "cli-version": {"version": "2026.10.23-27dcf5f"},
            "requested-model": {"requested": "claude-opus-5-5-high"},
            "catalogue-label": {"catalogue": "Claude Opus 5.5 300K"},
            "runtime-effort": {"reported": "Claude Opus 5.5 300K High"},
            "runtime-version": {"reported": "Claude Opus 5.4 300K Medium"},
            "runtime-context": {"reported": "Claude Opus 5.5 1M Medium"},
        }
        for name, changes in variants.items():
            with self.subTest(component=name):
                self.clear_fake_history()
                self.output = self.directory / ("alias-" + name)
                requested = self.configure_observed_model_label(**changes)
                result = self.run_review("--claude-model", requested, "--no-reconcile")
                self.assert_failed(result)
                metadata = self.json_output("claude/metadata.json")
                self.assertEqual(metadata["model_verification"], "unverified_runtime_label")
                self.assertEqual(metadata["reported_model"], self.scenario["reported_models"][requested])
                self.assertEqual(self.json_output("gemini/metadata.json")["status"], "success")

    def test_catalogue_current_and_default_suffixes_do_not_change_model_identity(self):
        for index, suffix in enumerate((" (current)", " (default)", " (current, default)",
                                        " (default, current)")):
            with self.subTest(suffix=suffix):
                self.clear_fake_history()
                self.output = self.directory / ("annotation-" + str(index))
                self.scenario["model_labels"] = {CLAUDE_MODEL: "Claude fixture label" + suffix}
                self.scenario["reported_models"] = {CLAUDE_MODEL: "Claude fixture label"}
                result = self.run_review("--no-reconcile")
                self.assert_success(result)
                metadata = self.json_output("claude/metadata.json")
                self.assertEqual(metadata["catalogue_label"], "Claude fixture label")
                self.assertEqual(metadata["reported_model"], "Claude fixture label")
                self.assertIn(suffix, (self.output / "models.txt").read_text())

    def test_catalogue_does_not_strip_arbitrary_or_nonterminal_label_text(self):
        for index, suffix in enumerate((" (current, experimental)", " (current) Extra")):
            with self.subTest(suffix=suffix):
                self.clear_fake_history()
                self.output = self.directory / ("unknown-annotation-" + str(index))
                self.scenario["model_labels"] = {CLAUDE_MODEL: "Claude fixture label" + suffix}
                self.scenario["reported_models"] = {CLAUDE_MODEL: "Claude fixture label"}
                result = self.run_review("--no-reconcile")
                self.assert_failed(result)
                metadata = self.json_output("claude/metadata.json")
                self.assertEqual(metadata["catalogue_label"], "Claude fixture label" + suffix)
                self.assertEqual(metadata["model_verification"], "unverified_runtime_label")

    def test_reconciliation_failure_preserves_both_independent_reviews(self):
        self.scenario["behaviors"] = {"reconcile:" + CLAUDE_MODEL: "cli-error"}
        result = self.run_review()
        self.assert_failed(result)
        for stage in ("claude", "gemini"):
            self.assertEqual(self.json_output(stage + "/metadata.json")["status"], "success")
            self.assertTrue(self.json_output(stage + "/review.json"))
        self.assertTrue((self.output / "reconcile/events.jsonl").is_file())
        self.assertIn("Synthetic provider unavailable",
                      (self.output / "reconcile/stderr.log").read_text())
        self.assertFalse((self.output / "report.md").exists())
        self.assertEqual(self.json_output("manifest.json")["status"], "failed")

    def test_timeout_preserves_completed_review_and_partial_output(self):
        self.scenario["behaviors"] = {GEMINI_MODEL: "timeout"}
        result = self.run_review("--timeout", "1", timeout=8)
        self.assert_failed(result)
        self.assertEqual(self.json_output("claude/review.json")["verdict"],
                         CLAUDE_MODEL + " fixture verdict")
        self.assertIn("Synthetic call started", (self.output / "gemini/stderr.log").read_text())
        self.assertIn("fixture-" + GEMINI_MODEL,
                      (self.output / "gemini/events.jsonl").read_text())
        self.assertIn("timeout", json.dumps(self.json_output("gemini/metadata.json")).lower())
        self.assertFalse(any(call["stage"] == "reconcile" for call in self.calls("model")))

    def test_timeout_also_stops_a_cli_child_process(self):
        self.scenario["behaviors"] = {GEMINI_MODEL: "child-timeout"}
        result = self.run_review("--timeout", "0.4", timeout=8)
        self.assert_failed(result)
        self.assertEqual(len(self.calls("child")), 1, "The fake child must actually have started")
        time.sleep(1.6)
        self.assertFalse((self.state / "orphan-ran").exists(), "Timed-out CLI left a child running")

    def test_nonfinite_timeout_is_rejected_before_model_calls(self):
        for value in ("nan", "inf", "-inf"):
            with self.subTest(value=value):
                self.output = self.directory / ("timeout-" + value)
                result = self.run_review("--timeout=" + value)
                self.assert_failed(result)
                self.assertEqual(self.calls("model"), [])

    def test_brief_shell_syntax_is_passed_literally(self):
        marker = self.directory / "must-not-exist"
        text = ("Untrusted quoted review input:\n"
                "$(touch '" + str(marker) + "')\n"
                "`touch '" + str(marker) + "'`\n"
                "'; touch '" + str(marker) + "'; #\n")
        self.brief.write_text(text)
        result = self.run_review("--no-reconcile")
        self.assert_success(result)
        self.assertFalse(marker.exists())
        self.assertEqual((self.output / "brief.md").read_text(), text)
        for call in self.calls("model"):
            self.assertIn(text, "\n".join(call["arguments"]))

    def test_existing_output_directory_is_never_overwritten(self):
        self.output.mkdir()
        sentinel = self.output / "manifest.json"
        sentinel.write_text("Existing results must be preserved\n")
        result = self.run_review()
        self.assert_failed(result)
        self.assertEqual(sentinel.read_text(), "Existing results must be preserved\n")
        self.assertEqual(sorted(item.name for item in self.output.iterdir()), ["manifest.json"])
        self.assertEqual(self.calls("model"), [])

    def test_completed_output_cannot_be_reused(self):
        self.assert_success(self.run_review("--no-reconcile"))
        before = {str(item.relative_to(self.output)): item.read_bytes()
                  for item in self.output.rglob("*") if item.is_file()}
        count = len(self.calls("model"))
        result = self.run_review("--no-reconcile")
        self.assert_failed(result)
        after = {str(item.relative_to(self.output)): item.read_bytes()
                 for item in self.output.rglob("*") if item.is_file()}
        self.assertEqual(after, before)
        self.assertEqual(len(self.calls("model")), count)

    def test_no_reconcile_runs_only_the_two_independent_reviews(self):
        result = self.run_review("--no-reconcile")
        self.assert_success(result)
        self.assertEqual(len(self.calls("model")), 2)
        self.assertFalse(any(call["stage"] == "reconcile" for call in self.calls("model")))
        self.assertFalse((self.output / "reconcile").exists())
        self.assertTrue(self.json_output("claude/review.json"))
        self.assertTrue(self.json_output("gemini/review.json"))

    def test_dry_run_never_starts_a_model(self):
        result = self.run_review("--dry-run")
        self.assert_success(result)
        self.assertEqual(self.calls("model"), [])
        manifest = self.json_output("manifest.json")
        self.assertEqual(manifest["status"], "dry_run")
        self.assertEqual(manifest["requested_models"],
                         {"claude": CLAUDE_MODEL, "gemini": GEMINI_MODEL})
        self.assertFalse((self.output / "claude").exists())
        self.assertFalse((self.output / "gemini").exists())
        self.assert_temporary_client_storage(self.calls())


if __name__ == "__main__":
    unittest.main()
