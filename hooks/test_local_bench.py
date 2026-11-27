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
        self.assertIsNone(violation("cat >> notes.md <<'EOF'\n- hook denies CCACHE_DISABLE=1 runs\nEOF"))

    def test_hyperfine_and_perf_are_denied(self):
        self.assertIsNotNone(violation("hyperfine 'cmake --build build'"))
        self.assertIsNotNone(violation("perf record -g ./cata_test-tiles -w NoTests '[map]'"))

    def test_script_with_a_profile_run_is_denied(self):
        with tempfile.TemporaryDirectory() as tmp:
            script = Path(tmp) / "floor.sh"
            script.write_text("#!/bin/bash\n./head-bin -w NoTests profile_wait\n")
            self.assertIsNotNone(violation(f"systemd-run --user --wait {script}"))

    def test_gpu_path_run_is_allowed(self):
        self.assertIsNone(violation("CATA_TEST_COMPUTE_ACCELERATION=gpu ./cata_test-tiles -w NoTests profile_walk"))
        self.assertIsNone(violation("export CATA_TEST_COMPUTE_ACCELERATION=gpu\n./cata_test-tiles profile_walk"))
        self.assertIsNone(violation("perf record -g ./cataclysm-bn-tiles --userdir u/ --configdir u/config/"))

    def test_cpu_path_run_is_denied(self):
        self.assertIsNotNone(violation("CATA_TEST_COMPUTE_ACCELERATION=cpu ./cata_test-tiles profile_walk"))
        self.assertIsNotNone(violation("CATA_TEST_COMPUTE_ACCELERATION=$accel ./cata_test-tiles profile_walk"))
        self.assertIsNotNone(violation("LOCAL_BENCH_OK=1 ./head-bin -w NoTests profile_wait"))

    def test_reading_a_script_is_allowed(self):
        with tempfile.TemporaryDirectory() as tmp:
            script = Path(tmp) / "hook.py"
            script.write_text('"""Split commands, so `rg profile_walk` is one search."""\n')
            self.assertIsNone(violation(f"sed -n 1,40p {script}"))
            self.assertIsNotNone(violation(f"bash {script}"))

    def test_search_and_plain_tests_are_allowed(self):
        self.assertIsNone(violation("rg -n profile_wait tests/"))
        self.assertIsNone(violation("git commit -m 'test: add profile_wait harness'"))
        self.assertIsNone(violation("./cata_test-tiles -w NoTests '[map]'"))

    def test_allows_search_after_other_commands(self):
        self.assertIsNone(violation("cd repo && rg -l 'profile_walk' tests 2>/dev/null | head"))
        self.assertIsNone(violation("cd repo; git log --all --oneline -S profile_walk | head -5"))

    def test_denies_run_after_a_search(self):
        self.assertIsNotNone(violation("rg -l x tests && ./head-bin -w NoTests profile_walk"))
        self.assertIsNotNone(violation("cd out && time ninja cataclysm-bn"))
        self.assertIsNotNone(violation("bash -c './head-bin profile_walk'"))

    def test_allows_harness_names_in_heredoc_data(self):
        self.assertIsNone(violation("cat > wf.yml <<'EOF'\n  run: ./cata_test -w NoTests profile_walk\nEOF"))
        self.assertIsNotNone(violation("bash <<'EOF'\n./head-bin profile_walk\nEOF"))


if __name__ == "__main__":
    unittest.main()
