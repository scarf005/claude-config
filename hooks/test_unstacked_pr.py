import json
import tempfile
import unittest

from unstacked_pr import turn_commands, violation


def heads(*branches):
    return lambda base, repo: f"{repo}:{base}" in branches


def bash(command):
    return {"type": "assistant", "message": {"content": [{"type": "tool_use", "name": "Bash", "input": {"command": command}}]}}


class UnstackedPrTest(unittest.TestCase):
    def test_pr_chained_on_open_pr_branch_without_link_is_blocked(self):
        cmds = ["gh pr create -R o/r --draft --base fix/a --head fix/b --title t"]
        self.assertEqual(violation(cmds, heads("o/r:fix/a")), [("o/r", "fix/a")])
        self.assertEqual(violation(["gh pr edit 7 -R o/r -B fix/a"], heads("o/r:fix/a")), [("o/r", "fix/a")])

    def test_stack_link_after_chained_create_allows_stop(self):
        cmds = ["gh pr create -R o/r --base fix/a --head fix/b", "gh stack link fix/a-h fix/b"]
        self.assertEqual(violation(cmds, heads("o/r:fix/a")), [])

    def test_chained_create_after_link_is_blocked_again(self):
        cmds = ["gh stack link fix/a fix/b && gh pr create -R o/r --base=fix/b --head fix/c", "gh stack link --help"]
        self.assertEqual(violation(cmds, heads("o/r:fix/b")), [("o/r", "fix/b")])
        cmds = ["gh stack link fix/a fix/b\ngh pr create -R o/r --base fix/b --head fix/c"]
        self.assertEqual(violation(cmds, heads("o/r:fix/b")), [("o/r", "fix/b")])

    def test_base_that_is_not_an_open_pr_branch_is_allowed(self):
        cmds = ["gh pr create -R o/r --base main --head fix/a", "gh pr create --head fix/b --body 'see --base fix/a'"]
        self.assertEqual(violation(cmds, heads("o/r:fix/a", "None:fix/a")), [])

    def test_turn_commands_reads_only_the_last_prompt_and_skips_bad_lines(self):
        lines = [bash("gh pr create --base old"), {"type": "user", "message": {"content": "next"}},
                 bash("gh pr create --base new"), {"type": "user", "message": {"content": [{"type": "tool_result"}]}},
                 {"type": "assistant", "message": None}, {"type": "assistant", "message": {"content": ["x"]}}, []]
        with tempfile.NamedTemporaryFile("w", suffix=".jsonl") as f:
            f.write("\n".join(json.dumps(x) for x in lines) + "\n\n{broken\n")
            f.flush()
            self.assertEqual(turn_commands(f.name), ["gh pr create --base new"])
        self.assertEqual(turn_commands("/nonexistent/t.jsonl"), [])


if __name__ == "__main__":
    unittest.main()
