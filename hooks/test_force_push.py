import unittest

from force_push import reviewed, violation


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


    def test_force_push_to_reviewed_pr_branch_is_denied(self):
        lookup = lambda repo, remote, branch: {"feat/x": ["rev"], "feat/down": None}.get(branch, [])
        self.assertEqual(reviewed("git push -f upstream feat/x", "/r", lookup), ("feat/x", ["rev"]))
        self.assertEqual(reviewed("git push --force-with-lease=feat/x:abc upstream tmp:feat/x", "/r", lookup),
                         ("feat/x", ["rev"]))
        self.assertEqual(reviewed("git push -f upstream +feat/down", "/r", lookup), ("feat/down", None))

    def test_unreviewed_plain_or_approved_force_push_is_allowed(self):
        lookup = lambda repo, remote, branch: ["rev"] if branch == "feat/x" else []
        self.assertIsNone(reviewed("git push -f upstream feat/y", "/r", lookup))
        self.assertIsNone(reviewed("git push upstream feat/x", "/r", lookup))
        self.assertIsNone(reviewed("CLAUDE_REVIEWED_PUSH_OK=1 git push -f upstream feat/x", "/r", lookup))


if __name__ == "__main__":
    unittest.main()
