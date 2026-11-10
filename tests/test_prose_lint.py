"""Behavioral tests for prose-lint; each run uses an isolated phrases file.

Run from the repository root with:
    python3 -m unittest discover -s tests -p 'test_prose_lint.py' -v
"""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


REPO = Path(__file__).resolve().parents[1]
RUNNER = REPO / "bin" / "prose-lint"


def words(n: int, word: str = "and") -> str:
    """A sentence of exactly n words. The filler is not a noun, so it makes no noun stack."""
    return " ".join([word.capitalize()] + [word] * (n - 1)) + "."


class ProseLintTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.phrases = self.dir / "phrases.txt"  # absent unless a test writes it

    def tearDown(self):
        self.tmp.cleanup()

    def lint(self, text=None, *args, files=None):
        env = dict(os.environ, PROSE_LINT_PHRASES=str(self.phrases))
        cmd = [sys.executable, "-B", str(RUNNER), *args]
        if files is None:
            cmd.append("-")
        else:
            cmd.extend(str(f) for f in files)
        return subprocess.run(cmd, input=text, capture_output=True, text=True, env=env)

    def findings(self, text, *args):
        out = self.lint(text, *args).stdout.splitlines()
        return [line for line in out if line.strip()]

    # ---------- sentence length ----------

    def test_sentence_of_25_words_passes_and_26_fails(self):
        self.assertEqual(self.lint(words(25)).returncode, 0)
        result = self.lint(words(26))
        self.assertEqual(result.returncode, 1)
        self.assertIn("-:1: long-sentence: 26 words (limit 25)", result.stdout)

    def test_numbered_step_limit_is_20_words(self):
        self.assertEqual(self.lint("1. " + words(20)).returncode, 0)
        result = self.lint("1. " + words(21))
        self.assertEqual(result.returncode, 1)
        self.assertIn("long-sentence: 21 words (limit 20)", result.stdout)

    def test_bullet_item_uses_the_description_limit(self):
        self.assertEqual(self.lint("- " + words(25)).returncode, 0)

    def test_two_short_sentences_are_not_one_long_one(self):
        self.assertEqual(self.lint(words(15) + " " + words(15)).returncode, 0)

    def test_a_paragraph_wrapped_over_lines_is_split_into_sentences(self):
        text = "First line is short.\n" + words(26) + "\nLast line is short.\n"
        result = self.lint(text)
        self.assertIn("-:2: long-sentence: 26 words", result.stdout)

    def test_sentence_that_starts_mid_line_reports_the_line_it_starts_on(self):
        text = "Intro words here. " + " ".join(["Start"] + ["word"] * 12) + "\n" + " ".join(["word"] * 14) + ".\n"
        result = self.lint(text)
        self.assertIn("-:1: long-sentence: 27 words", result.stdout)

    # ---------- what ends a sentence ----------

    def test_file_names_and_paths_do_not_end_a_sentence(self):
        text = "The script bootstrap.sh reads ~/.extra and scripts/check.sh before it starts. " + words(5)
        self.assertEqual(self.lint(text).returncode, 0)
        long = "The script bootstrap.sh reads ~/.extra and " + " ".join(["word"] * 20) + "."
        self.assertIn("long-sentence: 26 words", self.lint(long).stdout)  # 6 + 20

    def test_abbreviations_and_numbers_do_not_end_a_sentence(self):
        long = "Use a tool, e.g. the linter, on version 3.14 or v2.0-beta.1 and " + " ".join(["word"] * 14) + "."
        self.assertIn("long-sentence: 26 words", self.lint(long).stdout)  # 12 + 14

    def test_inline_code_counts_as_one_word(self):
        text = "Run `git log --oneline origin/main..HEAD | head -5` and " + " ".join(["word"] * 22) + "."
        self.assertEqual(self.lint(text).returncode, 0)  # 3 + 22 = 25
        text = "Run `git log --oneline origin/main..HEAD | head -5` and " + " ".join(["word"] * 23) + "."
        self.assertIn("long-sentence: 26 words", self.lint(text).stdout)

    def test_link_counts_its_text_and_a_bare_url_counts_as_one_word(self):
        text = "See [the run page](https://example.com/a/b/c?d=e.f) and https://example.com/x.y.z and " + " ".join(["word"] * 18) + "."
        self.assertEqual(self.lint(text).returncode, 0)  # See the run page and URL and + 18 = 25

    def test_bold_label_that_opens_a_block_is_not_counted(self):
        for label in ("**Verified by:** ", "**Not verified**: ", "- **Verified by:** "):
            self.assertEqual(self.lint(label + words(25)).returncode, 0, label)

    def test_plain_clause_before_a_colon_is_counted(self):
        text = "The script is the scorecard: " + words(21)
        self.assertIn("long-sentence: 26 words", self.lint(text).stdout)

    def test_sentence_that_starts_with_a_lowercase_name_is_split(self):
        text = words(15) + " macOS " + " ".join(["and"] * 14) + "."
        self.assertEqual(self.lint(text).returncode, 0)
        # ...but an abbreviation or a dotted token before a lowercase word is not an end
        long = "Use the tool, i.e. the linter, or a.k.a. the checker and " + " ".join(["and"] * 15) + "."
        self.assertIn("long-sentence: 26 words", self.lint(long).stdout)  # 11 + 15

    def test_question_and_exclamation_marks_end_sentences(self):
        self.assertEqual(self.lint(words(15)[:-1] + "? " + words(15)[:-1] + "! " + words(15)).returncode, 0)

    # ---------- what is skipped ----------

    def test_fenced_code_tables_headings_and_html_are_skipped(self):
        long = " ".join(["word"] * 40)
        text = "\n".join([
            "# " + long,
            "",
            "```bash",
            long + ".",
            "```",
            "",
            "| " + long + " | in order to |",
            "|---|---|",
            "",
            "<details>",
            "<summary>" + "Full write-up" + "</summary>",
            "",
            "<!-- " + long + " -->",
            "",
            "Short sentence here.",
            "",
        ])
        result = self.lint(text)
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertEqual(result.stdout.strip(), "")

    def test_yaml_frontmatter_at_the_top_is_skipped(self):
        long = " ".join(["and"] * 40)
        text = "---\ntitle: Note\ndescription: " + long + " in order to\ntags:\n  - one\n---\n\n" + words(26) + "\n"
        result = self.lint(text)
        self.assertEqual(result.stdout.count("\n"), 1, result.stdout)
        self.assertIn("-:8: long-sentence: 26 words", result.stdout)
        # a rule line later in the file is not frontmatter
        later = "Short sentence here.\n\n---\n\n" + words(26) + "\n\n---\n"
        self.assertIn("-:5: long-sentence", self.lint(later).stdout)

    def test_line_numbers_count_skipped_lines(self):
        text = "```\ncode\n```\n\n" + words(26) + "\n"
        self.assertIn("-:5: long-sentence", self.lint(text).stdout)

    # ---------- stock phrases ----------

    def test_stock_phrase_is_a_finding_with_a_suggestion(self):
        result = self.lint("We do this in order to save time.")
        self.assertEqual(result.returncode, 1)
        self.assertIn('-:1: stock-phrase: "in order to"', result.stdout)
        self.assertIn('"to"', result.stdout)

    def test_stock_phrases_ignore_case_and_cover_verb_forms(self):
        out = "\n".join(self.findings("Leveraging the cache, we Utilized it. It's Worth Noting that it delves deep."))
        for phrase in ("Leveraging", "Utilized", "Worth Noting", "delves"):
            self.assertIn(phrase, out)

    def test_stock_phrase_needs_a_word_boundary(self):
        self.assertEqual(self.lint("The leverages table lists delvers and reorder tools.").stdout.count("stock-phrase"), 1)

    def test_stock_phrase_inside_code_is_ignored(self):
        text = "Run `utilize --now` here.\n\n```\nin order to\n```\n"
        self.assertEqual(self.lint(text).returncode, 0)

    def test_local_phrases_file_adds_private_phrases(self):
        self.assertEqual(self.lint("The widget is frobnicated daily.", "-q").returncode, 0)
        self.phrases.write_text("# private list\n\nfrobnicated => changed\nzork\n")
        result = self.lint("The widget is frobnicated daily. A zork ran.", "-q")
        self.assertEqual(result.returncode, 1)
        self.assertIn('stock-phrase: "frobnicated" -> use "changed"', result.stdout)
        self.assertIn('stock-phrase: "zork"', result.stdout)

    # ---------- warnings: passive voice ----------

    def test_passive_with_a_named_actor_is_a_warning_not_a_finding(self):
        result = self.lint("The decision was made by the team.")
        self.assertEqual(result.returncode, 0)
        self.assertIn("-:1: passive:", result.stdout)
        self.assertIn("was made by", result.stdout)

    def test_passive_without_an_actor_is_a_weaker_warning(self):
        result = self.lint("The file was not replaced.")
        self.assertEqual(result.returncode, 0)
        self.assertIn("passive?", result.stdout)

    def test_adjectives_and_active_verbs_are_not_passive(self):
        for text in ("The file is unchanged.", "The team decided to ship it.", "It is ready and it is small.",
                     "The check has passed.", "She was interested in the result."):
            self.assertNotIn("passive", self.lint(text).stdout, text)

    def test_quiet_hides_warnings_but_keeps_findings(self):
        text = "The decision was made by the team. We did it in order to win."
        out = self.lint(text, "-q").stdout
        self.assertNotIn("passive", out)
        self.assertIn("stock-phrase", out)

    # ---------- warnings: noun stacks ----------

    def test_noun_stack_over_three_words_is_a_warning(self):
        result = self.lint("We raised the prod batch job queue retry limit today.")
        self.assertEqual(result.returncode, 0)
        self.assertIn('noun-stack: "prod batch job queue retry limit"', result.stdout)

    def test_capitalized_names_do_not_count_toward_a_noun_stack(self):
        self.assertNotIn("noun-stack", self.lint("Read the Mac Studio GUI Setup note first.").stdout)
        self.assertIn("noun-stack", self.lint("Prod batch job queue limit rose.").stdout)

    def test_three_noun_stack_and_plain_sentences_are_fine(self):
        for text in ("We raised the job retry limit today.", "The repo check passes offline now.",
                     "Bootstrap replaces every drifted file after a backup.", "A new skip list keeps seven files."):
            self.assertNotIn("noun-stack", self.lint(text).stdout, text)

    # ---------- inputs, output, exit codes ----------

    def test_clean_text_prints_nothing_and_exits_0(self):
        result = self.lint("Run the script. Read the output.")
        self.assertEqual((result.returncode, result.stdout), (0, ""))

    def test_files_are_named_in_findings_and_missing_file_exits_2(self):
        good = self.dir / "good.md"
        bad = self.dir / "bad.md"
        good.write_text("Short sentence.\n")
        bad.write_text("\n" + words(30) + "\n")
        result = self.lint(files=[good, bad])
        self.assertEqual(result.returncode, 1)
        self.assertIn(f"{bad}:2: long-sentence: 30 words", result.stdout)
        self.assertNotIn(str(good), result.stdout)
        self.assertEqual(self.lint(files=[self.dir / "none.md"]).returncode, 2)

    def test_summary_goes_to_stderr(self):
        result = self.lint(words(26) + " The plan was made by us.")
        self.assertIn("1 finding", result.stderr)
        self.assertIn("1 warning", result.stderr)

    def test_unknown_option_exits_2(self):
        self.assertEqual(self.lint("x", "--bogus").returncode, 2)


if __name__ == "__main__":
    unittest.main()
