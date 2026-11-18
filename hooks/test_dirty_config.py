import os
import subprocess
import tempfile
import unittest

from dirty_config import dirty_files, foreign_files, record_edit


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

    def edit(self, session, text):
        """Write `text` to a.txt as `session` did with Edit, and record it like the PostToolUse hook."""
        with open(self.file, "w") as f:
            f.write(text)
        record_edit(self.file, session, os.path.join(self.root, "state"))

    def foreign(self, session):
        return foreign_files(self.file, session, self.root, os.path.join(self.root, "state"))

    def test_session_may_edit_again_after_its_own_edit(self):
        """Session "s" changes a.txt to "2": its next edit of a.txt is allowed."""
        self.edit("s", "2\n")
        self.assertEqual(self.foreign("s"), [])

    def test_other_session_change_still_blocks(self):
        """Session "s" leaves a.txt changed: session "t" must commit a.txt first."""
        self.edit("s", "2\n")
        self.assertEqual(self.foreign("t"), ["a.txt"])

    def test_outside_change_after_own_edit_blocks(self):
        """Session "s" writes "2", then someone writes "3": "s" must commit a.txt first."""
        self.edit("s", "2\n")
        with open(self.file, "w") as f:
            f.write("3\n")
        self.assertEqual(self.foreign("s"), ["a.txt"])

    def test_deleted_file_blocks(self):
        """Someone deletes tracked a.txt: session "s" must commit the deletion first."""
        os.remove(self.file)
        self.assertEqual(self.foreign("s"), ["a.txt"])

    def test_quoted_path_blocks(self):
        """Someone changes tracked "b c.txt": the name comes back without porcelain quotes."""
        path = os.path.join(self.repo, "b c.txt")
        with open(path, "w") as f:
            f.write("1\n")
        run(self.repo, "add", "b c.txt")
        run(self.repo, "commit", "-q", "-m", "b")
        with open(path, "w") as f:
            f.write("2\n")
        self.assertEqual(self.foreign("s"), ["b c.txt"])


if __name__ == "__main__":
    unittest.main()
