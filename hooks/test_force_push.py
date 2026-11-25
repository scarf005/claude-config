import os
import subprocess
import tempfile
import unittest
from unittest import mock

from force_push import approvers, reviewed, violation


def only(*repos):
    return lambda repo, remote: repo in repos


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

    def test_opt_in_for_one_remote_allows_only_that_remote(self):
        fork = lambda repo, remote: remote == "origin"
        self.assertIsNone(violation("git push -f origin main", "/r", fork))
        self.assertIsNotNone(violation("git push -f upstream main", "/r", fork))

    def test_one_remote_opt_in_denies_push_without_remote(self):
        """`claude.forcePushDefaultBranch o/r` with `git push --force-with-lease=main` (no remote): deny, not crash."""
        env = {"GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1"}
        with tempfile.TemporaryDirectory() as d, mock.patch.dict(os.environ, env):
            subprocess.run(["git", "init", "-q", d], check=True)
            subprocess.run(["git", "-C", d, "config", "claude.forcePushDefaultBranch", "o/r"], check=True)
            self.assertIsNotNone(violation("git push --force-with-lease=main", d))

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

    def test_only_approvals_on_a_mergeable_pr_count(self):
        """GitHub dismisses only approvals on a push. A conflicting PR cannot merge, so its approval is void."""
        review = lambda login, state: {"author": {"login": login}, "state": state}
        self.assertEqual(approvers([{"mergeable": "MERGEABLE", "reviews": [review("a", "APPROVED")]}]), ["a"])
        self.assertEqual(approvers([{"mergeable": "MERGEABLE", "reviews": [
            review("a", "CHANGES_REQUESTED"), review("b", "COMMENTED"), review("c", "DISMISSED")]}]), [])
        self.assertEqual(approvers([{"mergeable": "CONFLICTING", "reviews": [review("a", "APPROVED")]}]), [])


if __name__ == "__main__":
    unittest.main()
