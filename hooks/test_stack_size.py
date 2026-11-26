import unittest

from stack_size import violation


class StackSizeTest(unittest.TestCase):
    def test_four_prs_are_denied(self):
        self.assertEqual(violation("gh stack link 10961 10959 10957 10958"), ["10961", "10959", "10957", "10958"])
        self.assertIsNotNone(violation("gh stack init a b c d"))

    def test_three_prs_are_allowed(self):
        self.assertIsNone(violation("gh stack link 10961 10959 10957"))

    def test_flag_values_are_not_members(self):
        self.assertIsNone(violation("gh stack link --base main --remote upstream a b c --open"))

    def test_repo_flag_and_redirections_are_not_members(self):
        self.assertIsNone(violation("gh stack link -R o/r --base main 1 2 3 2>&1 | tail"))
        self.assertIsNone(violation("gh stack init -b main a b c > /tmp/out.log 2> err.log"))
        self.assertIsNotNone(violation("gh stack link --repo o/r 1 2 3 4 2>&1"))

    def test_approved_split_is_allowed(self):
        self.assertIsNone(violation("STACK_SPLIT_OK=1 gh stack link a b c d"))

    def test_other_commands_are_allowed(self):
        self.assertIsNone(violation("gh stack view && gh pr list --json number a b c d"))


if __name__ == "__main__":
    unittest.main()
