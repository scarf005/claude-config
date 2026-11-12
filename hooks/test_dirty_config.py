import os
import subprocess
import tempfile
import unittest

from dirty_config import dirty_files


def run(repo, *args):
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    subprocess.run(["git", "-C", repo, *args], check=True, capture_output=True, env=env)


class DirtyConfigTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.root = os.path.realpath(self.dir.name)
        self.repo = os.path.join(self.root, "repo")
        os.mkdir(self.repo)
        run(self.repo, "init", "-q")
        run(self.repo, "config", "user.email", "t@example.com")
        run(self.repo, "config", "user.name", "t")
        self.file = os.path.join(self.repo, "a.txt")
        with open(self.file, "w") as f:
            f.write("1\n")
        run(self.repo, "add", "a.txt")
        run(self.repo, "commit", "-q", "-m", "init")

    def tearDown(self):
        self.dir.cleanup()

    def test_clean_repo_is_allowed(self):
        self.assertEqual(dirty_files(self.file, self.root)[1], [])

    def test_modified_tracked_file_is_dirty(self):
        with open(self.file, "w") as f:
            f.write("2\n")
        self.assertEqual(len(dirty_files(os.path.join(self.repo, "new.txt"), self.root)[1]), 1)

    def test_unstaged_entry_keeps_full_path(self):
        with open(self.file, "w") as f:
            f.write("2\n")
        self.assertEqual(dirty_files(self.file, self.root)[1][0][3:], "a.txt")

    def test_untracked_file_is_ignored(self):
        with open(os.path.join(self.repo, "u.txt"), "w") as f:
            f.write("x\n")
        self.assertEqual(dirty_files(self.file, self.root)[1], [])

    def test_path_outside_root_is_ignored(self):
        self.assertIsNone(dirty_files("/etc/hostname", self.root))


if __name__ == "__main__":
    unittest.main()
