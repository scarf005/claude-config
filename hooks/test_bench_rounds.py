import os
import subprocess
import tempfile
import unittest

from bench_rounds import violation


def repo_with_workflow(tmp, loop):
    """Creates a repo whose HEAD holds a bench workflow with the given round loop."""
    run = lambda *a: subprocess.run(["git", *a], cwd=tmp, check=True, capture_output=True, env=ENV)
    run("init", "-q")
    os.makedirs(f"{tmp}/.github/workflows")
    with open(f"{tmp}/.github/workflows/bench-walk.yml", "w") as f:
        f.write(f"on:\n  push:\n    branches: ['bench/walk-ab-*']\njobs:\n  run: |\n    {loop}\n")
    run("add", ".")
    run("commit", "-qm", "bench")


ENV = {"PATH": os.environ["PATH"], "HOME": "/nonexistent", "GIT_CONFIG_NOSYSTEM": "1",
       "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}


class BenchRoundsTest(unittest.TestCase):
    def test_push_of_a_bench_with_7_rounds_is_denied(self):
        """The 10958 bench ran `for r in 1 2 3 4 5 6 7`; the user asked for 5 rounds."""
        with tempfile.TemporaryDirectory() as tmp:
            repo_with_workflow(tmp, "for r in 1 2 3 4 5 6 7; do run; done")
            self.assertIn("7 rounds", violation("git push origin HEAD:refs/heads/bench/walk-ab-x", tmp))
            self.assertIn("7 rounds", violation(f"cd {tmp} && git push -q origin HEAD:bench/walk-ab-x", "/"))
            subprocess.run(["git", "branch", "bench/walk-ab-x"], cwd=tmp, check=True, env=ENV)
            self.assertIn("7 rounds", violation("git push origin bench/walk-ab-x", tmp))

    def test_push_of_a_bench_with_5_rounds_is_allowed(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo_with_workflow(tmp, "for r in 1 2 3 4 5; do run; done")
            self.assertIsNone(violation("git push origin HEAD:refs/heads/bench/walk-ab-x", tmp))

    def test_bench_push_from_an_unresolvable_source_is_denied(self):
        """A `$h:bench/...` refspec hides the pushed commit from the check."""
        with tempfile.TemporaryDirectory() as tmp:
            repo_with_workflow(tmp, "for r in 1 2 3 4 5; do run; done")
            self.assertIn("literal", violation("git push origin $h:refs/heads/bench/walk-ab-x", tmp))

    def test_other_pushes_are_ignored(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo_with_workflow(tmp, "for r in 1 2 3 4 5 6 7; do run; done")
            self.assertIsNone(violation("git push origin HEAD:refs/heads/perf/x", tmp))
            self.assertIsNone(violation("git log --format=%h bench/walk-ab-x", tmp))
            self.assertIsNone(violation("git push origin :refs/heads/bench/walk-ab-x", tmp))
            self.assertIsNone(violation("git push origin --delete bench/walk-ab-gone", tmp))


if __name__ == "__main__":
    unittest.main()
