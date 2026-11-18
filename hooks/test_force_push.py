import unittest

from force_push import violation


def only(*repos):
    return lambda repo: repo in repos


class ForcePushTest(unittest.TestCase):
    def test_force_push_to_main_is_denied_without_opt_in(self):
        for cmd in ["git push --force-with-lease=main:abc origin main", "git push -f origin main",
                    "git push origin +main", "git push origin --force master",
                    "git push -f origin refs/heads/main", "git push -f origin HEAD:refs/heads/main"]:
            self.assertIsNotNone(violation(cmd, "/r", only()), cmd)

    def test_opted_in_repo_may_force_push_main(self):
        self.assertIsNone(violation("git push --force origin main", "/r", only("/r")))
        self.assertIsNone(violation("cd /r && git push -f origin main", "/x", only("/r")))
        self.assertIsNone(violation("git -C /r push -f origin main", "/x", only("/r")))
        self.assertIsNotNone(violation("cd /x && git push -f origin main", "/r", only("/r")))

    def test_plain_push_and_feature_branch_force_are_allowed(self):
        self.assertIsNone(violation("git push origin main", "/r", only()))
        self.assertIsNone(violation("git push --force-with-lease origin feat/x", "/r", only()))
        self.assertIsNone(violation("git push -f origin feat/maintenance fix/main-menu", "/r", only()))


if __name__ == "__main__":
    unittest.main()
