import unittest

from md_table import violation

UNALIGNED = "| Renderer | Before | After |\n|---|---|---|\n| software | 0.797 s | 0.657 s |\n"
ALIGNED = (
    "| Renderer | Before  | After   | Speedup      |\n"
    "| -------- | ------- | ------- | ------------ |\n"
    "| software | 0.797 s | 0.657 s | 1.21x (-18%) |\n"
)
NO_SPEEDUP = (
    "| Renderer | Before  | After   |\n"
    "| -------- | ------- | ------- |\n"
    "| software | 0.797 s | 0.657 s |\n"
)


class MdTableTest(unittest.TestCase):
    def test_unaligned_table_in_heredoc_commit_is_denied(self):
        self.assertIsNotNone(violation(f"git commit -F - <<'EOF'\nperf: x\n\n{UNALIGNED}EOF"))

    def test_unaligned_table_in_message_file_is_denied(self):
        self.assertIsNotNone(violation("git commit --amend -F /tmp/m.txt", read=lambda _: UNALIGNED))
        self.assertIsNotNone(violation("gh pr edit 1 --body-file=b.md", read=lambda _: UNALIGNED))

    def test_unreadable_body_file_is_denied(self):
        """`--body-file $S/b.md` names a path the hook cannot open, so its tables would go unchecked."""
        def missing(_):
            raise FileNotFoundError
        self.assertIn("literal", violation("gh pr edit 1 -R o/r --body-file $S/b.md", read=missing))

    def test_aligned_table_is_allowed(self):
        self.assertIsNone(violation(f"git commit -F - <<'EOF'\nperf: x\n\n{ALIGNED}EOF"))
        self.assertIsNone(violation("git commit -F m.txt", read=lambda _: ALIGNED))

    def test_before_after_table_without_speedup_is_denied(self):
        self.assertIn("speedup", violation("git commit -F m.txt", read=lambda _: NO_SPEEDUP))

    def test_wide_characters_count_as_two_columns(self):
        table = "| 렌더러 | 값 |\n| ------ | -- |\n| sw     | 1  |\n"
        self.assertIsNone(violation("git commit -F m.txt", read=lambda _: table))

    def test_shell_pipes_and_other_commands_are_allowed(self):
        self.assertIsNone(violation('git commit -m "ci: x" | tail -1'))
        self.assertIsNone(violation(f"cat <<'EOF' > notes.md\n{UNALIGNED}EOF"))


if __name__ == "__main__":
    unittest.main()
