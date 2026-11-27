import os
import tempfile
import unittest

from pr_writing import brief_problem, brief_warning, ticked_issue_box_without_issue, deny_reason, skill_loaded, writes_body, writes_pr


class PrWritingTest(unittest.TestCase):
    def test_brief_pointing_to_notes_file_is_denied(self):
        """A 300-character brief naming /tmp/s/facts.md passed the cap and the writer copied every fact (PR 11034)."""
        brief = lambda text: brief_problem({"subagent_type": "pr-writer", "prompt": text + " no player-visible change"})
        self.assertIn("notes file", brief("Repo o/r, branch b, base main. Facts: /tmp/s/facts.md"))
        self.assertIsNone(brief("Repo o/r, branch b, base main. Diff: git -C /w/b diff upstream/main..."))

    def test_body_over_120_prose_words_is_denied(self):
        """The user's own PR bodies have 42 words of prose at the median; the AI draft of PR 11034 had 199."""
        user = (
            "## Purpose of change (The Why)\n\n1. make loading screen submission easier\n"
            "2. prevent repo size bloat due to more graphic assets\n\n## Describe the solution (The How)\n\n"
            "1. moved all loading images (and submission) to https://github.com/cataclysmbn/loading-screen\n"
            "2. bundle it on release\n\n| a | b |\n| --- | --- |\n| ![](https://x/a.webp) | c |\n\n"
            "<!-- template prompt " + "word " * 200 + "-->\n## Checklist\n\n- [x] " + "word " * 200
        )
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "tmp.Ab3dE5gH7j")
            data = {"tool_name": "Bash", "agent_type": "pr-writer",
                    "tool_input": {"command": "gh pr create -R o/r --body-file " + path}}
            for body, expected in ((user, None), (user.replace("## Checklist", "word " * 100), "120 words")):
                with open(path, "w") as f:
                    f.write(body)
                reason = deny_reason(data)
                self.assertIsNone(reason) if expected is None else self.assertIn(expected, reason)

    def test_perf_title_without_speedup_is_denied(self):
        """PR 11049 got `perf: skip time while a fire burns`; the user wanted the player action and the speedup."""
        data = lambda title: {"tool_name": "Bash", "agent_type": "pr-writer",
                              "tool_input": {"command": f"gh pr edit 5 -R o/r --title '{title}'"}}
        self.assertIn("measured speedup", deny_reason(data("perf: skip time while a fire burns")))
        self.assertIsNone(deny_reason(data("perf: make waiting faster with fire nearby (up to 10x faster)")))
        self.assertIsNone(deny_reason(data("fix: stop fire from spreading")))

    def test_perf_body_without_provenance_label_bars_webp_and_with_median_of_5_or_more(self):
        """PR 11049 captioned its bars `(fork CI)` and used a bars-only animation (pr11046-bars.webp); the user
        asked for no label and only game recordings with bars. A median of 5 or more rounds passes, 3 is denied."""
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "tmp.Ab3dE5gH7j")
            data = {"tool_name": "Bash", "agent_type": "pr-writer",
                    "tool_input": {"command": "gh pr edit 5 -R o/r --body-file " + path}}
            for body, expected in (("ms/turn (fork CI)", "fork CI"), ("ms/turn, median of 3", "median of 3"),
                                   ("![](https://x/pr11046-bars.webp)", "bars-only"),
                                   ("![](https://x/pr11046-fire.webp) ms/turn, median of 5", None),
                                   ("ms/turn, median of 7", None)):
                with open(path, "w") as f:
                    f.write("fixes #1\n" + body)
                reason = deny_reason(data)
                self.assertIsNone(reason) if expected is None else self.assertIn(expected, reason)

    def test_ticked_issue_box_needs_an_issue_link(self):
        """A ticked "I linked any relevant issues" box is wrong without `#N` or an issue URL in the body."""
        box = "- [x] I linked any relevant issues using [syntax](https://x/#notes) like `closes #1234` in Summary.\n"
        self.assertTrue(ticked_issue_box_without_issue("Why: tests fail.\n" + box))
        self.assertFalse(ticked_issue_box_without_issue("fixes #10\n" + box))
        self.assertFalse(ticked_issue_box_without_issue("see https://github.com/o/r/issues/7\n" + box))
        self.assertFalse(ticked_issue_box_without_issue("Why: tests fail.\n" + box.replace("[x]", "[ ]")))

    def test_pr_writer_body_file_with_ticked_box_is_denied(self):
        """`pr-writer` running `gh pr edit 5 --body-file b.md` is denied when b.md ticks the box without an issue."""
        with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False) as f:
            f.write("Why: tests fail.\n- [x] I linked any relevant issues like `closes #1234`.\n")
        self.addCleanup(os.unlink, f.name)
        command = "gh pr edit 5 --body-file " + f.name
        data = {"tool_name": "Bash", "agent_type": "pr-writer", "tool_input": {"command": command}}
        self.assertIn("linked-issue checkbox", deny_reason(data))

    def test_pr_writer_body_file_needs_a_temp_name(self):
        """Parallel `pr-writer`s share the scratchpad: `--body-file pr-body.md` is denied, a `mktemp` name is not."""
        with tempfile.TemporaryDirectory() as d:
            fixed, temp = os.path.join(d, "pr-body.md"), os.path.join(d, "tmp.Ab3dE5gH7j")
            for path in (fixed, temp):
                with open(path, "w") as f:
                    f.write("Why: tests fail.\n")
            data = lambda path: {"tool_name": "Bash", "agent_type": "pr-writer",
                                 "tool_input": {"command": "gh pr edit 5 -R o/r --body-file " + path}}
            self.assertIn("mktemp", deny_reason(data(fixed)))
            self.assertIsNone(deny_reason(data(temp)))

    def test_pr_writer_body_comes_only_from_a_checked_file(self):
        """`pr-writer` cannot pass a body the hook cannot read: stdin, a shell variable, `--body`, `gh api`, or an
        empty file. `cat empty | gh pr create --body-file -` opened a PR with an empty body."""
        with tempfile.TemporaryDirectory() as d:
            empty, custom = os.path.join(d, "tmp.Ab3dE5gH7j"), os.path.join(d, "pr-body.jHuSUk")
            open(empty, "w").close()
            with open(custom, "w") as f:
                f.write("Why: tests fail.\n")
            reason = lambda command: deny_reason(
                {"tool_name": "Bash", "agent_type": "pr-writer", "tool_input": {"command": command}})
            self.assertIn("stdin", reason("cat b | gh pr create -R o/r --title x --body-file -"))
            self.assertIn("literal", reason("f=$(mktemp); gh pr create --title x --body-file $f"))
            self.assertIn("--body-file", reason("gh pr edit 5 --body 'Why: x'"))
            self.assertIn("--body-file", reason("gh api -X PATCH repos/o/r/pulls/5 -F body=@" + custom))
            self.assertIn("empty", reason("gh pr edit 5 --body-file " + empty))
            self.assertIn("read", reason("gh pr edit 5 --body-file " + os.path.join(d, "tmp.Zz9yX8wV7u")))
            self.assertIsNone(reason("gh pr edit 5 --body-file " + custom))
            self.assertIsNone(reason("gh pr edit 5 --body-file=" + custom))
            self.assertIsNone(reason("gh pr edit 5 --title 'fix: x'"))
            for attached in ("-F=-", "-F-", "-F=/tmp/fixed.md", "-F/tmp/fixed.md", "-bx", "--body=x"):
                self.assertIsNotNone(reason("gh pr edit 5 " + attached), attached)
            for title in ("'fix -bar thing'", "-b", '"don\'t"'):
                self.assertIsNone(reason(f"gh pr edit 5 --title {title} --body-file {custom}"), title)

    def test_pr_create_and_edit_are_writes(self):
        self.assertTrue(writes_body("gh pr create --fill"))
        self.assertTrue(writes_body("gh pr edit 12 --body-file b.md"))
        self.assertTrue(writes_body("gh issue create -t x"))

    def test_api_pulls_is_a_write(self):
        self.assertTrue(writes_body("gh api repos/o/r/pulls -f title=x"))
        self.assertTrue(writes_body("gh api repos/o/r/issues/5 -X PATCH -F body=@b.md"))

    def test_reads_are_allowed(self):
        self.assertFalse(writes_body("gh pr list -L 1"))
        self.assertFalse(writes_body("gh pr checks --watch"))
        self.assertFalse(writes_body("gh api user -q .login"))
        self.assertFalse(writes_body("gh api repos/o/r/pulls/5/files"))

    def test_pr_text_writes_need_pr_writer(self):
        """PR title or body writes go through `pr-writer`; issue writes and label edits do not."""
        self.assertTrue(writes_pr("gh pr create --fill"))
        self.assertTrue(writes_pr("gh pr edit 12 --body-file b.md"))
        self.assertTrue(writes_pr("gh pr edit 12 -t 'fix: x'"))
        self.assertTrue(writes_pr("gh api repos/o/r/pulls/5 -X PATCH -f body=x"))
        self.assertFalse(writes_pr("gh pr edit 12 --add-label bug"))
        self.assertFalse(writes_pr("gh issue edit 5 --body-file b.md"))
        self.assertFalse(writes_pr("gh api repos/o/r/pulls/5/files"))

    def test_pr_write_forms_that_reach_github(self):
        """Repo flag before the subcommand, continued lines, attached short values and GraphQL still count as writes."""
        self.assertTrue(writes_pr("gh pr -R o/r edit 5 --body x"))
        self.assertTrue(writes_pr("gh pr --repo o/r create --fill"))
        self.assertTrue(writes_pr("gh pr edit 5 \\\n  --body-file b.md"))
        self.assertTrue(writes_pr("gh api repos/o/r/pulls/5 \\\n  -X PATCH -f body=x"))
        self.assertTrue(writes_pr("gh api repos/o/r/pulls/5 -fbody=x"))
        self.assertTrue(writes_pr("gh pr edit 5 -bx"))
        self.assertTrue(writes_pr("gh api graphql -f query='mutation{updatePullRequest(input:{})}'"))
        self.assertTrue(writes_pr("gh pr -Ro/r edit 5 --body x"))
        self.assertTrue(writes_pr('gh api "repos/o/r/pulls/$PR" -X PATCH -f body=x'))
        self.assertTrue(writes_body("gh api repos/o/r/issues/${N} -F body=@b.md"))

    def test_chained_commands_are_checked_one_by_one(self):
        """`-X GET` or `-F` in a later command does not change the result for an earlier `gh` command."""
        self.assertTrue(writes_pr("gh api repos/o/r/pulls/5 -X PATCH -f body=x && gh api -X GET user"))
        self.assertFalse(writes_pr("gh pr edit 5 --add-label bug && tail -F log"))
        self.assertFalse(writes_pr("gh pr edit 5 --add-label bug\ntail -F log"))

    def test_quoted_separators_do_not_split(self):
        """`|`, `;` and newlines inside quotes stay in one command, so the path or mutation after them still matches."""
        self.assertTrue(writes_pr("gh api -X PATCH -f body='a | b' repos/o/r/pulls/5"))
        self.assertTrue(writes_pr("gh api -X PATCH -f body='a; b' repos/o/r/pulls/5"))
        self.assertTrue(writes_pr("gh pr edit 5 --add-label a#b --body x"))
        self.assertTrue(writes_pr("gh api -X PATCH -f body='line1\nline2' repos/o/r/pulls/5"))
        self.assertTrue(writes_pr("gh api graphql -f query='\n  mutation {\n    updatePullRequest(input: {}) { x }\n  }'"))

    def test_pr_reads_and_other_pull_writes_are_allowed(self):
        """An explicit GET, reviewer requests and merges do not change PR text."""
        self.assertFalse(writes_pr("gh api -X GET repos/o/r/pulls -F per_page=100"))
        self.assertFalse(writes_pr("gh api repos/o/r/pulls/5/requested_reviewers -f reviewers[]=a"))
        self.assertFalse(writes_pr("gh api repos/o/r/pulls/5/merge -X PUT"))

    def test_agent_brief_goes_through_deny_reason(self):
        """An Agent call with a long `pr-writer` brief is denied by the hook entry point."""
        call = {"tool_name": "Agent", "tool_input": {"subagent_type": "pr-writer", "prompt": "x" * 601}}
        self.assertIsNotNone(deny_reason(call))

    def test_only_pr_writer_may_write_pr_text(self):
        """`gh pr create` is denied in the main session and allowed when `agent_type` is `pr-writer`."""
        call = {"tool_name": "Bash", "tool_input": {"command": "gh pr create --fill"}}
        self.assertIsNotNone(deny_reason(call))
        self.assertIsNotNone(deny_reason(call | {"agent_type": "implementer"}))
        self.assertIsNone(deny_reason(call | {"agent_type": "pr-writer"}))

    def test_pr_writer_runs_on_opus(self):
        """A `pr-writer` call with `model: sonnet` is denied; no `model` or `model: opus` passes."""
        brief = {"subagent_type": "pr-writer", "prompt": "Edit PR #5. fixes #4."}
        self.assertIsNotNone(brief_problem(brief | {"model": "sonnet"}))
        self.assertIsNone(brief_problem(brief | {"model": "opus"}))
        self.assertIsNone(brief_problem(brief))

    def test_brief_length_is_capped(self):
        """A `pr-writer` brief over 600 characters is denied, so the parent cannot pass its session story."""
        self.assertIsNone(brief_problem({"subagent_type": "pr-writer", "prompt": "Edit PR #5. fixes #4."}))
        self.assertIsNotNone(brief_problem({"subagent_type": "pr-writer", "prompt": "x" * 601}))
        self.assertIsNone(brief_problem({"subagent_type": "implementer", "prompt": "x" * 601}))

    def test_brief_cannot_dictate_added_prose(self):
        """A brief like "Under the table add one line: measured with X" is denied; briefs give facts, not sentences."""
        for prompt in ["PR #5. Under the table add one line: measured with x.", "PR #5. Add a sentence saying y.",
                       "PR #5. add a note that z"]:
            self.assertIsNotNone(brief_problem({"subagent_type": "pr-writer", "prompt": prompt}), prompt)
        self.assertIsNone(brief_problem({"subagent_type": "pr-writer", "prompt": "PR #5. Delete the line x."}))

    def test_new_pr_brief_needs_captures(self):
        """A new-PR brief needs capture URLs, "no player-visible change", or "captures unavailable: <reason>"."""
        brief = {"subagent_type": "pr-writer", "prompt": "Repo a/b, base main, head x. No captures."}
        self.assertIsNotNone(brief_problem(brief))
        self.assertIsNone(brief_problem(brief | {"prompt": "base main. Before https://x/y/before.webp, https://asciinema.org/a/1"}))
        self.assertIsNone(brief_problem(brief | {"prompt": "base main. No player-visible change."}))
        self.assertIsNone(brief_problem(brief | {"prompt": "base main. Captures unavailable: the issue has no save."}))
        self.assertIsNotNone(brief_problem(brief | {"prompt": "base main. Captures unavailable."}))

    def test_webp_without_asciinema_needs_tiles(self):
        """A brief with only .webp URLs is denied unless it names a tiles capture, which has no terminal recording."""
        brief = {"subagent_type": "pr-writer", "prompt": "base main. Before https://x/before.webp popup."}
        self.assertIsNotNone(brief_problem(brief))
        self.assertIsNone(brief_problem(brief | {"prompt": brief["prompt"] + " Tiles build."}))

    def test_existing_pr_brief_without_captures_only_warns(self):
        """Editing PR #5 (base main) without captures is allowed with a warning; a new PR is still denied."""
        edit = {"subagent_type": "pr-writer", "prompt": "Repo a/b, PR #5 (base main). Drop one word."}
        self.assertIsNone(brief_problem(edit))
        self.assertIsNotNone(brief_warning(edit))
        self.assertIsNone(brief_warning(edit | {"prompt": "PR #5, base main. No player-visible change."}))
        self.assertIsNone(brief_warning({"subagent_type": "pr-writer", "prompt": "Repo a/b, base main, head x."}))

    def test_skill_load_is_read_from_transcript(self):
        with tempfile.NamedTemporaryFile("w", suffix=".jsonl") as f:
            f.write('{"name":"Skill","input":{"skill":"pr-writing"}}\n')
            f.flush()
            self.assertTrue(skill_loaded(f.name))
        with tempfile.NamedTemporaryFile("w", suffix=".jsonl") as f:
            f.write('{"name":"Skill","input":{"skill":"humanizer"}}\n')
            f.flush()
            self.assertFalse(skill_loaded(f.name))
        self.assertFalse(skill_loaded("/nonexistent"))


if __name__ == "__main__":
    unittest.main()
