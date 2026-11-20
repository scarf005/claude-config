import unittest

from amend_author import violation


def other_in(*repos):
    return lambda repo: repo in repos


class AmendAuthorTest(unittest.TestCase):
    def test_amend_of_other_authors_head_is_denied(self):
        for cmd in ["git commit --amend --no-edit", "git commit -q --amend -F - <<'EOF'",
                    "cd /r && git add a && git commit --amend", "git -C /r commit --amend"]:
            self.assertIsNotNone(violation(cmd, "/r", other_in("/r")), cmd)

    def test_own_head_and_plain_commit_are_allowed(self):
        self.assertIsNone(violation("git commit --amend", "/r", other_in()))
        self.assertIsNone(violation("git commit -m 'fix: x'", "/r", other_in("/r")))
        self.assertIsNone(violation("cd /mine && git commit --amend", "/r", other_in("/r")))


if __name__ == "__main__":
    unittest.main()
