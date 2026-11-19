"""Behavioral tests for harness-repair. The model runner is always a local script.

Run from the repository root with:
    python3 -m unittest discover -s tests -p 'test_harness_repair.py' -v
"""

from __future__ import annotations

import importlib.machinery
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import textwrap
import unittest


REPO = Path(__file__).resolve().parents[1]
RUNNER = REPO / "bin" / "harness-repair"
EXAMPLE = REPO / "examples" / "harness-repair"
TOOLS = (EXAMPLE / "harness" / "tools.json").read_text(encoding="utf-8")


def load_module():
    # The script has no .py suffix, so the default suffix loader will not take it.
    loader = importlib.machinery.SourceFileLoader("harness_repair", str(RUNNER))
    spec = importlib.util.spec_from_file_location("harness_repair", str(RUNNER), loader=loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


MOD = load_module()


def rows(*items):
    return "".join(json.dumps(item) + "\n" for item in items)


class HarnessRepairTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def cli(self, *args, env=None):
        merged = dict(os.environ)
        merged.pop("HARNESS_REPAIR_EXAMPLES", None)
        if env:
            merged.update(env)
        return subprocess.run(
            [sys.executable, "-B", str(RUNNER), *args],
            cwd=str(self.root),
            capture_output=True,
            text=True,
            env=merged,
        )

    def write(self, name, text):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(textwrap.dedent(text).lstrip("\n"), encoding="utf-8")
        return path

    def harness(self, system="You are a hasty assistant. Never use tools.\n", done="Stop when you feel done.\n"):
        path = self.root / "harness"
        path.mkdir(exist_ok=True)
        (path / "system.md").write_text(system, encoding="utf-8")
        (path / "done.md").write_text(done, encoding="utf-8")
        (path / "tools.json").write_text(TOOLS, encoding="utf-8")
        return path

    def tasks(self, text, name="tasks.jsonl"):
        return self.write(name, text)

    def optimize(self, harness, tasks, runner, env=None, **extra):
        out = self.root / "out"
        cmd = [
            "optimize",
            "--harness", str(harness),
            "--tasks", str(tasks),
            "--runner", "command",
            "--runner-cmd", "%s -B %s" % (sys.executable, runner),
            "--out", str(out),
        ]
        for key, value in extra.items():
            flag = "--" + key.replace("_", "-")
            if value is True:
                cmd.append(flag)
            else:
                cmd.extend([flag, str(value)])
        result = self.cli(*cmd, env=env)
        report = {}
        report_path = out / "report.json"
        if report_path.is_file():
            report = json.loads(report_path.read_text(encoding="utf-8"))
        return result, report, out


class ExampleLoopTest(HarnessRepairTest):
    def test_mock_example_keeps_only_a_train_improvement_and_reports_heldout(self):
        source = (EXAMPLE / "harness" / "system.md").read_bytes()
        result, report, out = self.optimize(
            EXAMPLE / "harness",
            EXAMPLE / "tasks.jsonl",
            EXAMPLE / "mock_runner.py",
            max_iterations=1,
            max_calls=40,
        )
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertEqual(report["baseline_train_passed"], 0)
        self.assertEqual(report["baseline_train_total"], 3)
        self.assertEqual(report["best_train_passed"], 3)
        self.assertEqual(report["best"], "v001")
        self.assertEqual(report["accepted"], ["v001"])
        self.assertTrue(report["heldout_scored"])
        self.assertEqual(report["heldout_passed"], 2)
        self.assertEqual(report["heldout_total"], 2)
        self.assertEqual(report["calls"], 14)
        self.assertEqual(report["cost_usd"], 0)
        self.assertIn("not used to accept edits", result.stdout)
        best = (out / "best" / "system.md").read_text(encoding="utf-8")
        self.assertIn("calc tool", best)
        self.assertNotIn("Never use tools", best)
        self.assertIn("Never use tools", (out / "versions" / "v000" / "system.md").read_text(encoding="utf-8"))
        history = (out / "history.jsonl").read_text(encoding="utf-8")
        self.assertIn("calc tool", history)
        self.assertIn('"verdict": "accepted"', history)
        self.assertIn("system.md", (out / "versions" / "v001" / "diff.patch").read_text(encoding="utf-8"))
        self.assertEqual((EXAMPLE / "harness" / "system.md").read_bytes(), source)

    def test_optimizer_request_omits_heldout_prompts(self):
        capture = self.root / "capture.jsonl"
        wrapper = self.write("wrap.py", """
            import json, os, subprocess, sys
            req = json.load(sys.stdin)
            with open(os.environ["CAPTURE"], "a", encoding="utf-8") as handle:
                handle.write(json.dumps(req) + "\\n")
            proc = subprocess.run(
                [sys.executable, "-B", os.environ["MOCK"]],
                input=json.dumps(req),
                text=True,
                capture_output=True,
            )
            sys.stdout.write(proc.stdout)
            sys.stderr.write(proc.stderr)
            raise SystemExit(proc.returncode)
        """)
        result, report, _out = self.optimize(
            EXAMPLE / "harness",
            EXAMPLE / "tasks.jsonl",
            wrapper,
            env={"CAPTURE": str(capture), "MOCK": str(EXAMPLE / "mock_runner.py")},
            max_iterations=1,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(report["best_train_passed"], 3)
        text = capture.read_text(encoding="utf-8")
        optimizer = [json.loads(line) for line in text.splitlines() if '"optimizer"' in line]
        self.assertTrue(optimizer)
        blob = json.dumps(optimizer)
        self.assertIn("17 * 3", blob)
        self.assertIn("Lyon", blob)
        self.assertNotIn("84 / 4", blob)
        self.assertNotIn("HELD-CITY", blob)
        self.assertNotIn("Oslo", blob)

    def test_dry_run_writes_nothing_and_does_not_call_the_runner(self):
        out = self.root / "out"
        result = self.cli(
            "optimize",
            "--harness", str(EXAMPLE / "harness"),
            "--tasks", str(EXAMPLE / "tasks.jsonl"),
            "--runner", "command",
            "--runner-cmd", "%s -B %s" % (sys.executable, self.root / "missing.py"),
            "--dry-run",
            "--out", str(out),
            "--max-cost", "1",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("dry-run", result.stdout)
        self.assertIn("3 train, 2 heldout", result.stdout)
        self.assertFalse(out.exists())

    def test_init_copies_the_example_and_refuses_a_second_time(self):
        dest = self.root / "mine"
        result = self.cli("init", str(dest))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((dest / "harness" / "tools.json").is_file())
        self.assertTrue((dest / "mock_runner.py").is_file())
        again = self.cli("init", str(dest))
        self.assertEqual(again.returncode, 2)
        self.assertIn("not empty", again.stderr)

    def test_run_scores_both_splits_and_does_not_edit_the_harness(self):
        before = (EXAMPLE / "harness" / "system.md").read_bytes()
        out = self.root / "run"
        result = self.cli(
            "run",
            "--harness", str(EXAMPLE / "harness"),
            "--tasks", str(EXAMPLE / "tasks.jsonl"),
            "--runner", "command",
            "--runner-cmd", "%s -B %s" % (sys.executable, EXAMPLE / "mock_runner.py"),
            "--out", str(out),
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads((out / "report.json").read_text(encoding="utf-8"))
        self.assertEqual(report["train_passed"], 0)
        self.assertEqual(report["heldout_passed"], 0)
        self.assertEqual(report["calls"], 5)
        self.assertEqual((EXAMPLE / "harness" / "system.md").read_bytes(), before)


class SelectionTest(HarnessRepairTest):
    def test_tie_and_regression_are_rejected_and_the_diff_is_kept(self):
        harness = self.harness()
        tasks = self.tasks(rows(
            {"id": "only", "split": "train", "prompt": "Say one.", "expect": "1"},
        ))
        runner = self.write("runner.py", """
            import json, sys
            req = json.load(sys.stdin)
            if req.get("role") == "optimizer":
                content = json.dumps({
                    "hypothesis": "this wording is worse",
                    "files": {"system.md": "WORSE prompt.\\n"},
                })
            else:
                system = req.get("system") or ""
                content = "ANSWER: 0" if "WORSE" in system else "ANSWER: 1"
            json.dump({"content": content, "usage": {"cost_usd": 0}}, sys.stdout)
        """)
        result, report, out = self.optimize(harness, tasks, runner, max_iterations=1)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(report["baseline_train_passed"], 1)
        self.assertEqual(report["best"], "v000")
        self.assertEqual(report["accepted"], [])
        verdict = json.loads((out / "versions" / "v001" / "verdict.json").read_text(encoding="utf-8"))
        self.assertEqual(verdict["verdict"], "rejected")
        self.assertIn("did not improve", verdict["reason"])
        self.assertIn("WORSE", verdict["diff"])
        history = (out / "history.jsonl").read_text(encoding="utf-8")
        self.assertIn("WORSE", history)

    def test_heldout_loss_does_not_block_a_train_gain(self):
        harness = self.harness(system="Plain start.\\n")
        tasks = self.tasks(rows(
            {"id": "tr", "split": "train", "prompt": "TRAIN-TOKEN please", "expect": "alpha"},
            {"id": "he", "split": "heldout", "prompt": "HELD-TOKEN please", "expect": "beta"},
        ))
        runner = self.write("runner.py", """
            import json, sys
            req = json.load(sys.stdin)
            if req.get("role") == "optimizer":
                content = json.dumps({"hypothesis": "mark it", "files": {"system.md": "IMPROVED agent.\\n"}})
            else:
                system = req.get("system") or ""
                text = req["messages"][-1].get("content") or ""
                content = "ANSWER: alpha" if "IMPROVED" in system and "TRAIN-TOKEN" in text else "ANSWER: no"
            json.dump({"content": content, "usage": {"cost_usd": 0}}, sys.stdout)
        """)
        result, report, _out = self.optimize(harness, tasks, runner, max_iterations=1)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(report["best"], "v001")
        self.assertEqual(report["best_train_passed"], 1)
        self.assertEqual(report["heldout_passed"], 0)
        self.assertTrue(report["heldout_scored"])

    def test_pasted_train_answer_is_rejected_before_scoring(self):
        harness = self.harness(system="Start.\\n")
        tasks = self.tasks(rows(
            {"id": "city", "split": "train", "prompt": "Name the city.", "expect": "Lyon"},
        ))
        runner = self.write("runner.py", """
            import json, sys
            req = json.load(sys.stdin)
            if req.get("role") == "optimizer":
                content = json.dumps({
                    "hypothesis": "paste the city",
                    "files": {"system.md": "When asked, answer Lyon.\\n"},
                })
            else:
                system = req.get("system") or ""
                content = "ANSWER: Lyon" if "Lyon" in system else "ANSWER: 0"
            json.dump({"content": content, "usage": {"cost_usd": 0}}, sys.stdout)
        """)
        result, report, out = self.optimize(harness, tasks, runner, max_iterations=1)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(report["best"], "v000")
        self.assertEqual(report["calls"], 2)
        verdict = json.loads((out / "versions" / "v001" / "verdict.json").read_text(encoding="utf-8"))
        self.assertIn("pastes a train answer", verdict["reason"])
        self.assertIsNone(verdict["train_passed"])

    def test_illegal_path_and_bad_tools_are_rejected(self):
        harness = self.harness(system="Start.\\n")
        tasks = self.tasks(rows(
            {"id": "only", "split": "train", "prompt": "Say one.", "expect": "1"},
        ))
        runner = self.write("runner.py", """
            import json, os, sys
            req = json.load(sys.stdin)
            step = os.environ.get("STEP", "path")
            if req.get("role") == "optimizer" and step == "path":
                content = json.dumps({"hypothesis": "escape", "files": {"../tasks.jsonl": "nope"}})
            elif req.get("role") == "optimizer":
                content = json.dumps({"hypothesis": "break tools", "files": {"tools.json": "["}})
            else:
                content = "ANSWER: 0"
            json.dump({"content": content, "usage": {"cost_usd": 0}}, sys.stdout)
        """)
        path_run, path_report, path_out = self.optimize(harness, tasks, runner, max_iterations=1)
        self.assertEqual(path_run.returncode, 0, path_run.stderr)
        self.assertEqual(path_report["best"], "v000")
        reason = json.loads((path_out / "versions" / "v001" / "verdict.json").read_text(encoding="utf-8"))["reason"]
        self.assertIn("cannot edit", reason)

        out = self.root / "out-tools"
        result = self.cli(
            "optimize",
            "--harness", str(harness),
            "--tasks", str(tasks),
            "--runner", "command",
            "--runner-cmd", "%s -B %s" % (sys.executable, runner),
            "--out", str(out),
            "--max-iterations", "1",
            env={"STEP": "tools"},
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads((out / "report.json").read_text(encoding="utf-8"))
        self.assertEqual(report["best"], "v000")
        reason = json.loads((out / "versions" / "v001" / "verdict.json").read_text(encoding="utf-8"))["reason"]
        self.assertIn("tools.json", reason)


class BudgetTest(HarnessRepairTest):
    def test_call_budget_stops_before_an_unscored_candidate_is_kept(self):
        harness = self.harness(system="Start.\\n")
        tasks = self.tasks(rows(
            {"id": "only", "split": "train", "prompt": "Say one.", "expect": "1"},
            {"id": "held", "split": "heldout", "prompt": "Say two.", "expect": "2"},
        ))
        runner = self.write("runner.py", """
            import json, sys
            req = json.load(sys.stdin)
            if req.get("role") == "optimizer":
                content = json.dumps({"hypothesis": "improve", "files": {"system.md": "IMPROVED.\\n"}})
            else:
                system = req.get("system") or ""
                content = "ANSWER: 1" if "IMPROVED" in system else "ANSWER: 0"
            json.dump({"content": content, "usage": {"cost_usd": 0}}, sys.stdout)
        """)
        result, report, out = self.optimize(harness, tasks, runner, max_iterations=1, max_calls=2)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(report["calls"], 2)
        self.assertEqual(report["best"], "v000")
        self.assertEqual(report["stopped"], "call budget reached")
        self.assertFalse(report["heldout_scored"])
        verdict = json.loads((out / "versions" / "v001" / "verdict.json").read_text(encoding="utf-8"))
        self.assertEqual(verdict["verdict"], "incomplete")

    def test_baseline_call_budget_is_an_error(self):
        harness = self.harness(system="Start.\\n")
        tasks = self.tasks(rows(
            {"id": "a", "split": "train", "prompt": "A", "expect": "1"},
            {"id": "b", "split": "train", "prompt": "B", "expect": "1"},
        ))
        runner = self.write("runner.py", """
            import json, sys
            json.dump({"content": "ANSWER: 0", "usage": {"cost_usd": 0}}, sys.stdout)
        """)
        result, report, _out = self.optimize(harness, tasks, runner, max_iterations=1, max_calls=1)
        self.assertEqual(result.returncode, 1)
        self.assertEqual(report["stopped"], "call budget reached")
        self.assertFalse(report["baseline_complete"])

    def test_cost_budget_is_checked_before_the_next_call(self):
        harness = self.harness(system="Start.\\n")
        tasks = self.tasks(rows({"id": "only", "split": "train", "prompt": "Say one.", "expect": "1"}))
        runner = self.write("runner.py", """
            import json, sys
            req = json.load(sys.stdin)
            if req.get("role") == "optimizer":
                content = json.dumps({"hypothesis": "improve", "files": {"system.md": "IMPROVED.\\n"}})
            else:
                content = "ANSWER: 0"
            json.dump({"content": content, "usage": {"cost_usd": 0.4}}, sys.stdout)
        """)
        result, report, _out = self.optimize(harness, tasks, runner, max_iterations=1, max_cost=0.3)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(report["best"], "v000")
        self.assertEqual(report["calls"], 1)
        self.assertEqual(report["stopped"], "cost budget reached")
        self.assertGreater(report["cost_usd"], 0.3)

    def test_missing_cost_stops_when_a_cap_is_set(self):
        harness = self.harness(system="Start.\\n")
        tasks = self.tasks(rows({"id": "only", "split": "train", "prompt": "Say one.", "expect": "1"}))
        runner = self.write("runner.py", """
            import json, sys
            json.dump({"content": "ANSWER: 0"}, sys.stdout)
        """)
        result, report, _out = self.optimize(harness, tasks, runner, max_iterations=1, max_cost=1)
        self.assertEqual(result.returncode, 1)
        self.assertIn("cost_usd", report["stopped"])


class ToolAndProtocolTest(HarnessRepairTest):
    def test_calc_and_read_file_stay_inside_their_limits(self):
        self.assertEqual(MOD.eval_arith("17 * 3"), "51")
        self.assertEqual(MOD.eval_arith("84 / 4"), "21")
        self.assertEqual(MOD.eval_arith("(2+3)*4"), "20")
        for expr in ("__import__('os').system('echo hi')", "2**10", "nine", ""):
            with self.assertRaises(ValueError):
                MOD.eval_arith(expr)
        workspace = self.root / "ws"
        workspace.mkdir()
        (workspace / "note.txt").write_text("Lyon", encoding="utf-8")
        self.assertEqual(MOD.impl_read_file({"path": "note.txt"}, workspace), "Lyon")
        with self.assertRaises(Exception):
            MOD.impl_read_file({"path": "../secret"}, workspace)
        outside = self.root / "secret.txt"
        outside.write_text("nope", encoding="utf-8")
        (workspace / "link.txt").symlink_to(outside)
        with self.assertRaises(Exception):
            MOD.impl_read_file({"path": "link.txt"}, workspace)

    def test_answer_lines_and_proposal_fences(self):
        self.assertEqual(MOD.extract_answer("guess\nANSWER: 51\n"), "51")
        self.assertEqual(MOD.extract_answer("51"), "51")
        self.assertNotEqual(MOD.extract_answer("the answer is 51"), "51")
        parsed = MOD.parse_proposal('```json\n{"hypothesis":"h","files":{}}\n```')
        self.assertEqual(parsed["hypothesis"], "h")

    def test_claude_and_codex_invocations_do_not_skip_permissions(self):
        payload = {"system": "SYS", "messages": [{"role": "user", "content": "hi there"}]}
        cmd, stdin = MOD.claude_invocation(payload, "", "claude")
        self.assertEqual(cmd[0], "claude")
        self.assertIn("--append-system-prompt", cmd)
        self.assertIn("SYS", cmd)
        self.assertNotIn("hi there", cmd)
        self.assertIn("hi there", stdin)
        self.assertNotIn("--dangerously-skip-permissions", cmd)
        codex = MOD.codex_invocation(payload, "some-model", "codex", "read-only")
        self.assertIn("--sandbox", codex)
        self.assertIn("read-only", codex)
        self.assertIn("--skip-git-repo-check", codex)
        self.assertNotIn("danger-full-access", codex)

    def test_api_requests_keep_the_key_out_of_the_body(self):
        payload = {
            "system": "SYS",
            "messages": [
                {"role": "user", "content": "hi"},
                {"role": "assistant", "content": "", "tool_calls": [
                    {"id": "c1", "name": "calc", "arguments": {"expression": "1+1"}},
                ]},
                {"role": "tool", "name": "calc", "tool_call_id": "c1", "content": "2"},
            ],
            "tools": [{
                "name": "calc",
                "description": "add",
                "parameters": {"type": "object", "properties": {}},
            }],
        }
        _url, headers, body = MOD.openai_request(payload, "demo-model", "https://example.test/v1", "test-key", 128)
        blob = json.dumps(body)
        self.assertNotIn("test-key", blob)
        self.assertEqual(headers["Authorization"], "Bearer test-key")
        self.assertEqual(body["model"], "demo-model")
        self.assertEqual(body["messages"][-1]["role"], "tool")
        url, headers, body = MOD.anthropic_request(
            payload, "demo-model", "https://example.test", "test-key", 128
        )
        self.assertTrue(url.endswith("/v1/messages"))
        self.assertEqual(headers["x-api-key"], "test-key")
        self.assertNotIn("test-key", json.dumps(body))
        roles = [message["role"] for message in body["messages"]]
        self.assertEqual(roles, ["user", "assistant", "user"])
        self.assertEqual(body["messages"][-1]["content"][0]["type"], "tool_result")

    def test_command_check_scores_answer_txt(self):
        harness = self.harness(system="Reply with the word.\n")
        code = "import pathlib,sys; sys.exit(0 if pathlib.Path('answer.txt').read_text().strip()=='ok' else 1)"
        tasks = self.tasks(rows({
            "id": "word",
            "split": "train",
            "prompt": "Say ok.",
            "check": {"type": "command", "argv": [sys.executable, "-c", code]},
        }))
        runner = self.write("runner.py", """
            import json, sys
            json.dump({"content": "ok", "usage": {"cost_usd": 0}}, sys.stdout)
        """)
        out = self.root / "run"
        result = self.cli(
            "run",
            "--harness", str(harness),
            "--tasks", str(tasks),
            "--runner", "command",
            "--runner-cmd", "%s -B %s" % (sys.executable, runner),
            "--out", str(out),
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads((out / "report.json").read_text(encoding="utf-8"))
        self.assertEqual(report["train_passed"], 1)

    def test_help_and_a_missing_harness(self):
        help_result = self.cli("--help")
        self.assertEqual(help_result.returncode, 0)
        self.assertIn("optimize", help_result.stdout)
        missing = self.cli(
            "run",
            "--harness", str(self.root / "nope"),
            "--tasks", str(EXAMPLE / "tasks.jsonl"),
            "--runner", "command",
            "--runner-cmd", "python3 mock.py",
        )
        self.assertEqual(missing.returncode, 2)


if __name__ == "__main__":
    unittest.main()
