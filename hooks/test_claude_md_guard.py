import unittest

from claude_md_guard import violation


class ClaudeMdGuardTest(unittest.TestCase):
    def test_denies_writes_to_claude_md_files(self):
        for path in ["/r/CLAUDE.md", "/r/CLAUDE.local.md", "/h/.config/claude/CLAUDE.md", "/r/claude.md"]:
            self.assertTrue(violation("Edit", {"file_path": path}), path)
            self.assertTrue(violation("Write", {"file_path": path}), path)
        for cmd in ["echo x >> CLAUDE.md", "sed -i s/a/b/ /r/CLAUDE.local.md", "gio trash /r/CLAUDE.local.md",
                    "mv CLAUDE.md x.md"]:
            self.assertTrue(violation("Bash", {"command": cmd}), cmd)

    def test_allows_reads_and_other_files(self):
        self.assertFalse(violation("Edit", {"file_path": "/h/.config/AGENTS.md"}))
        self.assertFalse(violation("Read", {"file_path": "/r/CLAUDE.md"}))
        for cmd in ["cat CLAUDE.md", "rg force CLAUDE.local.md", "echo x > notes.md"]:
            self.assertFalse(violation("Bash", {"command": cmd}), cmd)


if __name__ == "__main__":
    unittest.main()
