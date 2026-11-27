import unittest

from ci_watch import unwatched_push


def bash(command, background=False):
    return {"type": "assistant", "message": {"content": [
        {"type": "tool_use", "name": "Bash", "input": {"command": command, "run_in_background": background}}]}}


PUSH = bash("git push -q origin HEAD:refs/heads/bench/walk-ab-s-fire")
WATCH = bash("/home/x/gh run watch 45925433303 -R a/b --exit-status", background=True)


class CiWatchTest(unittest.TestCase):
    def test_push_without_watch_blocks(self):
        """The 2026-11-27 session pushed bench/walk-ab-s-fire and stopped with no watcher."""
        self.assertTrue(unwatched_push([PUSH]))
        self.assertTrue(unwatched_push([WATCH, PUSH]))

    def test_background_watch_after_push_passes(self):
        self.assertFalse(unwatched_push([PUSH, WATCH]))
        self.assertFalse(unwatched_push([PUSH, bash("gh pr checks 5 --watch --fail-fast", background=True)]))

    def test_foreground_watch_and_branch_delete_do_not_count(self):
        """A foreground watch ends with the call; `push --delete bench/x` starts no run."""
        self.assertTrue(unwatched_push([PUSH, bash("gh run watch 1 --exit-status")]))
        self.assertFalse(unwatched_push([bash("git push -q origin --delete bench/walk-ab-s-horde5")]))


if __name__ == "__main__":
    unittest.main()
