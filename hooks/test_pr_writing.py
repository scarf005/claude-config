import tempfile
import unittest

from pr_writing import brief_problem, deny_reason, skill_loaded, writes_body, writes_pr


class PrWritingTest(unittest.TestCase):
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

    def test_brief_length_is_capped(self):
        """A `pr-writer` brief over 600 characters is denied, so the parent cannot pass its session story."""
        self.assertIsNone(brief_problem({"subagent_type": "pr-writer", "prompt": "Edit PR #5. fixes #4."}))
        self.assertIsNotNone(brief_problem({"subagent_type": "pr-writer", "prompt": "x" * 601}))
        self.assertIsNone(brief_problem({"subagent_type": "implementer", "prompt": "x" * 601}))

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
