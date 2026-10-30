"""Behavioral tests for agent-sessions; every run uses an isolated data dir.

Run from the repository root with:
    python3 -m unittest discover -s tests -p 'test_agent_sessions.py' -v
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


REPO = Path(__file__).resolve().parents[1]
RUNNER = REPO / "bin" / "agent-sessions"


def line(**fields) -> str:
    return json.dumps(fields, separators=(",", ":")) + "\n"


def user(text, ts, sid="s1", cwd="/repo/widgets", branch="me/fix", **extra) -> str:
    return line(type="user", sessionId=sid, cwd=cwd, gitBranch=branch, timestamp=ts,
                message={"role": "user", "content": text}, **extra)


def assistant(blocks, ts, sid="s1", cwd="/repo/widgets", branch="me/fix") -> str:
    return line(type="assistant", sessionId=sid, cwd=cwd, gitBranch=branch, timestamp=ts,
                message={"role": "assistant", "content": blocks})


class AgentSessionsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.data = self.root / "data"
        self.env = dict(os.environ, AGENT_SESSIONS_DIR=str(self.data), AGENT_SESSIONS_HOST="work-mbp")

    def tearDown(self):
        self.tmp.cleanup()

    def transcript(self, sid="s1", text="") -> Path:
        path = self.root / "projects" / f"{sid}.jsonl"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        return path

    def run_cli(self, *args, stdin="", env=None):
        return subprocess.run([sys.executable, str(RUNNER), *args], input=stdin, text=True,
                              capture_output=True, env=env or self.env, timeout=30)

    def hook(self, path: Path, event="Stop", sid="s1", **extra):
        payload = dict(session_id=sid, transcript_path=str(path), cwd="/repo/widgets",
                       hook_event_name=event, **extra)
        return self.run_cli("hook", stdin=json.dumps(payload))

    def events(self, host="work-mbp"):
        path = self.data / f"events-{host}.jsonl"
        return [json.loads(x) for x in path.read_text().splitlines()] if path.exists() else []

    def test_stop_extracts_links_from_conversation_not_tool_output_or_prompts(self):
        path = self.transcript(text="".join([
            line(type="custom-title", customTitle="Fix login 403", sessionId="s1"),
            user("Look at PROJ-15006", "2026-10-29T10:00:00.000Z"),
            assistant([
                {"type": "thinking", "thinking": "PROJ-77777"},
                {"type": "text", "text": "See widgets#2079 and [[Gotchas]]"},
                {"type": "tool_use", "name": "Bash", "input": {"command": "jira view PROJ-12345"}},
                {"type": "tool_use", "name": "Edit", "input": {"file_path": "/repo/widgets/app.py"}},
            ], "2026-10-29T10:01:00.000Z"),
            user([{"type": "tool_result", "content": "PROJ-99999"}], "2026-10-29T10:01:30.000Z",
                 toolUseResult={}),
            user("PROJ-66666 injected", "2026-10-29T10:01:40.000Z", isMeta=True),
            line(type="api-request-blob", message={"role": "user", "content": [
                {"type": "text", "text": "PROJ-88888"}]}),
            line(type="queue-operation", content="PROJ-55555"),
        ]))

        result = self.hook(path)

        self.assertEqual((result.returncode, result.stdout), (0, ""))
        [record] = self.events()
        self.assertEqual(record["event"], "Stop")
        self.assertEqual(record["host"], "work-mbp")
        self.assertEqual(record["session_id"], "s1")
        self.assertEqual(record["title"], "Fix login 403")
        self.assertEqual((record["cwd"], record["branch"]), ("/repo/widgets", "me/fix"))
        self.assertEqual(record["ts"], "2026-10-29T10:01:40.000Z")
        self.assertEqual(record["jira"], ["PROJ-12345", "PROJ-15006"])
        self.assertEqual(record["prs"], ["widgets#2079"])
        self.assertEqual(record["notes"], ["Gotchas"])
        self.assertEqual(record["files"], ["/repo/widgets/app.py"])

    def test_second_stop_reads_only_lines_appended_since_the_first(self):
        path = self.transcript(text=user("PROJ-1 first", "2026-10-29T10:00:00.000Z"))
        self.hook(path)
        with path.open("a") as f:
            f.write(user("PROJ-2 second", "2026-10-29T11:00:00.000Z"))

        self.hook(path)

        self.assertEqual([r["jira"] for r in self.events()], [["PROJ-1"], ["PROJ-2"]])

    def test_partial_trailing_line_is_left_for_the_next_stop(self):
        whole = user("PROJ-3 later", "2026-10-29T10:00:00.000Z")
        path = self.transcript(text=whole[:20])
        self.hook(path)
        self.assertEqual(self.events(), [])

        path.write_text(whole)
        self.hook(path)

        self.assertEqual([r["jira"] for r in self.events()], [["PROJ-3"]])

    def test_transcript_shorter_than_saved_offset_is_reread_from_start(self):
        path = self.transcript(text=user("PROJ-4 " + "x" * 500, "2026-10-29T10:00:00.000Z"))
        self.hook(path)
        path.write_text(user("PROJ-5", "2026-10-29T12:00:00.000Z"))

        self.hook(path)

        self.assertEqual([r["jira"] for r in self.events()], [["PROJ-4"], ["PROJ-5"]])

    def test_bad_input_exits_zero_silently_and_logs(self):
        result = self.run_cli("hook", stdin="not json")

        self.assertEqual((result.returncode, result.stdout, result.stderr), (0, "", ""))
        self.assertIn("Traceback", (self.data / "errors.log").read_text())

    def test_github_pull_urls_and_owner_refs_normalize_to_repo_ref(self):
        path = self.transcript(text=assistant([{"type": "text", "text":
            "https://github.com/acme/widgets/pull/2079 and acme/widgets#2079 "
            "and web-app#88 but not PR#5 or issue#3"}], "2026-10-29T10:00:00.000Z"))

        self.hook(path)

        self.assertEqual(self.events()[0]["prs"], ["web-app#88", "widgets#2079"])

    def test_table_escaped_wikilink_alias_keeps_only_the_note_name(self):
        path = self.transcript(text=user("| [[Jane Doe\\|Jane]] | [[Runbook#Step 2]] |",
                                         "2026-10-29T10:00:00.000Z"))

        self.hook(path)

        self.assertEqual(self.events()[0]["notes"], ["Jane Doe", "Runbook"])

    def test_wikilinks_in_tool_input_count_only_for_markdown_writes(self):
        path = self.transcript(text=assistant([
            {"type": "tool_use", "name": "Write",
             "input": {"file_path": "/repo/t.py", "content": 'assert x == [["PROJ-1"]]'}},
            {"type": "tool_use", "name": "Bash", "input": {"command": "echo [[Bash Note]]"}},
            {"type": "tool_use", "name": "Write",
             "input": {"file_path": "/vault/Daily.md", "content": "see [[Gotchas]]"}},
        ], "2026-10-29T10:00:00.000Z"))

        self.hook(path)

        [record] = self.events()
        self.assertEqual(record["notes"], ["Gotchas"])
        self.assertEqual(record["jira"], ["PROJ-1"])

    def test_default_jira_pattern_drops_common_lookalikes(self):
        path = self.transcript(text=user("SHA-256 UTF-8 UTF-16 ISO-8601 PROJ-12 OPS-7585",
                                         "2026-10-29T10:00:00.000Z"))

        self.hook(path)

        self.assertEqual(self.events()[0]["jira"], ["OPS-7585", "PROJ-12"])

    def test_configured_jira_prefixes_are_the_only_ones_kept(self):
        self.data.mkdir(parents=True)
        (self.data / "config.json").write_text(json.dumps({"jira_prefixes": ["PROJ"]}))
        path = self.transcript(text=user("PROJ-12 FOO-34 OPS-7585", "2026-10-29T10:00:00.000Z"))

        self.hook(path)

        self.assertEqual(self.events()[0]["jira"], ["PROJ-12"])

    def test_session_end_writes_an_end_record_even_with_no_new_lines(self):
        path = self.transcript(text=user("PROJ-1", "2026-10-29T10:00:00.000Z"))
        self.hook(path)

        self.hook(path, event="SessionEnd", reason="logout")

        end = self.events()[-1]
        self.assertEqual((end["event"], end["reason"], end["jira"]), ("SessionEnd", "logout", []))

    def test_find_folds_sessions_across_hosts_and_filters_by_link(self):
        a = self.transcript("a", line(type="custom-title", customTitle="Login 403", sessionId="a")
                            + user("PROJ-15006", "2026-10-29T09:00:00.000Z", sid="a"))
        b = self.transcript("b", line(type="custom-title", customTitle="Billing outage", sessionId="b")
                            + user("PROJ-14893", "2026-10-29T10:00:00.000Z", sid="b"))
        c = self.transcript("c", line(type="custom-title", customTitle="Studio follow-up", sessionId="c")
                            + user("PROJ-15006 again", "2026-10-29T11:00:00.000Z", sid="c",
                                   cwd="/srv/my repo"))
        self.hook(a, sid="a")
        self.hook(b, sid="b")
        studio = dict(self.env, AGENT_SESSIONS_HOST="mac-studio")
        self.run_cli("hook", stdin=json.dumps(dict(session_id="c", transcript_path=str(c),
                                                   hook_event_name="Stop")), env=studio)

        out = self.run_cli("find", "proj-15006").stdout

        self.assertNotIn("Billing outage", out)
        self.assertLess(out.index("Studio follow-up"), out.index("Login 403"))
        self.assertIn("mac-studio", out)
        self.assertIn("cd '/srv/my repo' && claude -r c", out)

    def test_find_ranks_title_matches_then_focused_sessions_above_broad_ones(self):
        many = " ".join("PROJ-%d" % n for n in range(100, 111))
        sessions = [("titled", "PROJ-1: fix login", "PROJ-1 " + many, "08"),
                    ("focused", "Small fix", "PROJ-1 PROJ-2", "10"),
                    ("broad", "Evening sweep", "PROJ-1 " + many, "12")]
        for sid, title, text, hour in sessions:
            path = self.transcript(sid, line(type="custom-title", customTitle=title, sessionId=sid)
                                   + user(text, "2026-10-29T%s:00:00.000Z" % hour, sid=sid))
            self.hook(path, sid=sid)

        ranked = self.run_cli("find", "PROJ-1").stdout
        recent = self.run_cli("find").stdout

        order = lambda out: sorted(("PROJ-1: fix login", "Small fix", "Evening sweep"), key=out.index)
        self.assertEqual(order(ranked), ["PROJ-1: fix login", "Small fix", "Evening sweep"])
        self.assertEqual(order(recent), ["Evening sweep", "Small fix", "PROJ-1: fix login"])

    def test_backfill_indexes_every_transcript_under_a_projects_dir(self):
        self.transcript("a", user("PROJ-1", "2026-10-29T09:00:00.000Z", sid="a"))
        self.transcript("b", user("PROJ-2", "2026-10-29T10:00:00.000Z", sid="b"))

        self.run_cli("backfill", str(self.root / "projects"))

        self.assertEqual(sorted(r["session_id"] for r in self.events()), ["a", "b"])
        self.assertEqual({r["event"] for r in self.events()}, {"Backfill"})

    def test_backfill_skips_plugin_logs_and_subagent_transcripts(self):
        projects = self.root / "projects"
        for rel in ("proj/c.jsonl", "proj/vercel-plugin/skill-injections.jsonl",
                    "proj/c/subagents/agent-x.jsonl"):
            path = projects / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(user("PROJ-1", "2026-10-29T09:00:00.000Z", sid=path.stem))

        self.run_cli("backfill", str(projects))

        self.assertEqual([r["session_id"] for r in self.events()], ["c"])


if __name__ == "__main__":
    unittest.main()
