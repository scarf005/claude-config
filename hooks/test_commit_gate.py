import json
import unittest

from commit_gate import COMMIT, has, needs_review


def use(name, **args):
    return json.dumps({"type": "assistant", "message": {"content": [
        {"type": "tool_use", "name": name, "input": args}]}})


EDIT = use("Edit", file_path="a.ts")
STAT = use("Bash", command="git diff --shortstat upstream/main...")


class CommitGateTest(unittest.TestCase):
    def test_commit_commands_match_and_prose_does_not(self):
        for cmd in ["git commit -m x", "cd /r && git -c a=b -C /p commit -q", "git add a; git commit --amend"]:
            self.assertTrue(has(COMMIT, cmd), cmd)
        for cmd in ["git commit-tree HEAD^{tree}", 'gh pr create --body "run git commit"', "echo git commit"]:
            self.assertFalse(has(COMMIT, cmd), cmd)

    def test_edit_after_measurement_needs_review(self):
        self.assertTrue(needs_review([EDIT]))
        self.assertTrue(needs_review([EDIT, STAT, use("Bash", command="sed -i s/a/b/ f")]))
        self.assertTrue(needs_review([EDIT, use("Bash", command="git diff --shortstat && git commit -m x")]))

    def test_measurement_after_last_edit_allows_commit(self):
        self.assertFalse(needs_review([EDIT, STAT, use("Bash", command='rg "sed -i" docs')]))
        self.assertFalse(needs_review(["not json", "123", '{"type": "assistant", "message": "x"}',
                                       use("Bash", command=["not", "str"])]))


if __name__ == "__main__":
    unittest.main()
