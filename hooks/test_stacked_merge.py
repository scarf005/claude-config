import unittest

from stacked_merge import violation


def stack(**deps):
    return lambda pr, repo: deps.get(f"{repo}:{pr}", [])


class StackedMergeTest(unittest.TestCase):
    def test_merge_with_open_dependent_pr_is_denied(self):
        lookup = stack(**{"o/r:10905": ["10915"]})
        self.assertEqual(violation("gh pr merge 10905 -R o/r --rebase", lookup), ("10905", ["10915"]))
        self.assertIsNotNone(violation("gh pr merge -R o/r --rebase 10905 --match-head-commit abc", lookup))

    def test_merge_without_dependents_is_allowed(self):
        lookup = stack(**{"o/r:10905": ["10915"]})
        self.assertIsNone(violation("gh pr merge 10915 -R o/r --rebase", lookup))
        self.assertIsNone(violation("gh pr view 10905 -R o/r", lookup))
        self.assertIsNone(violation("gh stack merge", lookup))


if __name__ == "__main__":
    unittest.main()
