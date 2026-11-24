import tempfile
import unittest
from pathlib import Path

from local_bench import violation


class LocalBenchTest(unittest.TestCase):
    def test_profile_run_is_denied(self):
        self.assertIsNotNone(violation("PROFILE_WAIT_MINUTES=600 ./head-bin -w NoTests profile_wait"))

    def test_timed_or_cold_build_is_denied(self):
        self.assertIsNotNone(violation('/usr/bin/time -o t -f "%U" ninja -C out -j 8 cataclysm-bn'))
        self.assertIsNotNone(violation("time cmake --build out/build/ci-curses"))
        self.assertIsNotNone(violation("export CCACHE_DISABLE=1\nninja -C out"))

    def test_hyperfine_and_perf_are_denied(self):
        self.assertIsNotNone(violation("hyperfine 'cmake --build build'"))
        self.assertIsNotNone(violation("perf record -g ./cata_test-tiles -w NoTests '[map]'"))

    def test_script_with_a_profile_run_is_denied(self):
        with tempfile.TemporaryDirectory() as tmp:
            script = Path(tmp) / "floor.sh"
            script.write_text("#!/bin/bash\n./head-bin -w NoTests profile_wait\n")
            self.assertIsNotNone(violation(f"systemd-run --user --wait {script}"))

    def test_approved_run_is_allowed(self):
        self.assertIsNone(violation("LOCAL_BENCH_OK=1 ./head-bin -w NoTests profile_wait"))

    def test_search_and_plain_tests_are_allowed(self):
        self.assertIsNone(violation("rg -n profile_wait tests/"))
        self.assertIsNone(violation("git commit -m 'test: add profile_wait harness'"))
        self.assertIsNone(violation("./cata_test-tiles -w NoTests '[map]'"))


if __name__ == "__main__":
    unittest.main()
