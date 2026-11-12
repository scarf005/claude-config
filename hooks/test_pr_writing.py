import tempfile
import unittest

from pr_writing import skill_loaded, writes_body


class PrWritingTest(unittest.TestCase):
    def test_pr_create_and_edit_are_writes(self):
        self.assertTrue(writes_body("gh pr create --fill"))
        self.assertTrue(writes_body("gh pr edit 12 --body-file b.md"))
        self.assertTrue(writes_body("gh issue create -t x"))

    def test_api_pulls_is_a_write(self):
        self.assertTrue(writes_body("gh api repos/o/r/pulls -f title=x"))
        self.assertTrue(writes_body("gh api repos/o/r/issues/5 -X PATCH -F body=@b.md"))

    def test_reads_are_allowed(self):
        self.assertFalse(writes_body("gh pr list -L 1"))
        self.assertFalse(writes_body("gh pr checks --watch"))
        self.assertFalse(writes_body("gh api user -q .login"))

    def test_skill_load_is_read_from_transcript(self):
        with tempfile.NamedTemporaryFile("w", suffix=".jsonl") as f:
            f.write('{"name":"Skill","input":{"skill":"pr-writing"}}\n')
            f.flush()
            self.assertTrue(skill_loaded(f.name))
        with tempfile.NamedTemporaryFile("w", suffix=".jsonl") as f:
            f.write('{"name":"Skill","input":{"skill":"humanizer"}}\n')
            f.flush()
            self.assertFalse(skill_loaded(f.name))
        self.assertFalse(skill_loaded("/nonexistent"))


if __name__ == "__main__":
    unittest.main()
