import tempfile
import unittest
from pathlib import Path

from null_sink import violation


class NullSinkTest(unittest.TestCase):
    def test_per_run_sink_is_denied(self):
        self.assertIsNotNone(violation("pactl load-module module-null-sink sink_name=bniso_3738226"))
        self.assertIsNotNone(violation("pactl load-module module-null-sink"))

    def test_script_with_a_per_run_sink_is_denied(self):
        with tempfile.TemporaryDirectory() as tmp:
            script = Path(tmp) / "capture.sh"
            script.write_text("#!/bin/bash\npactl load-module module-null-sink sink_name=probe_$$\n")
            self.assertIsNotNone(violation(f"systemd-run --user --wait {script}"))

    def test_shared_sink_is_allowed(self):
        self.assertIsNone(violation(
            "pactl list short sinks | rg -q '\\sagent_mute\\s' || pactl load-module module-null-sink sink_name=agent_mute"
        ))

    def test_search_is_allowed(self):
        self.assertIsNone(violation("rg -n 'load-module module-null-sink' tests/"))


if __name__ == "__main__":
    unittest.main()
