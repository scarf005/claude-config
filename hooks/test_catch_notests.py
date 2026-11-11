import unittest

from catch_notests import violation


class CatchNoTestsTest(unittest.TestCase):
    def test_filtered_run_without_notests_is_denied(self):
        self.assertIsNotNone(violation('out/build/linux-full/tests/cata_test-tiles --rng-seed 1 "$F"'))

    def test_run_with_notests_is_allowed(self):
        self.assertIsNone(violation('out/build/linux-full/tests/cata_test-tiles -w NoTests "[map]"'))

    def test_build_target_and_copy_are_allowed(self):
        self.assertIsNone(violation("cmake --build out/build/linux-full --target cata_test-tiles -j8"))
        self.assertIsNone(violation("cp out/build/linux-full/tests/cata_test-tiles /tmp/x"))

    def test_listing_is_allowed(self):
        self.assertIsNone(violation('out/build/linux-full/tests/cata_test-tiles --list-test-names-only "[map]"'))


if __name__ == "__main__":
    unittest.main()
