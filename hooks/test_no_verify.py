import unittest

from no_verify import violation


class NoVerifyTest(unittest.TestCase):
    def test_no_verify_commit_is_denied(self):
        self.assertIsNotNone(violation('git commit -q -am "test: x" --no-verify 2>/dev/null || git commit -am x'))

    def test_hooks_path_override_is_denied(self):
        self.assertIsNotNone(violation("git -c core.hooksPath=/dev/null commit -m x"))

    def test_message_only_rewrite_is_allowed(self):
        self.assertIsNone(violation("CLAUDE_MSG_ONLY_REWRITE=1 git rebase -x 'git commit --amend --no-verify'"))

    def test_plain_commit_and_other_tools_are_allowed(self):
        self.assertIsNone(violation('git commit -m "ci: x"'))
        self.assertIsNone(violation("npm publish --no-verify"))


if __name__ == "__main__":
    unittest.main()
