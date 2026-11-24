import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from capture_timeout import violation

HOOK = Path(__file__).with_name("capture_timeout.py")


def run_hook(command):
    out = subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps({"tool_name": "Bash", "tool_input": {"command": command}}),
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    return json.loads(out)["hookSpecificOutput"]["permissionDecision"] if out else None


class CaptureTimeoutTest(unittest.TestCase):
    def test_recording_without_timeout_is_denied(self):
        self.assertEqual(
            run_hook("tmux new-session -d \"asciinema rec -q -c './cataclysm-bn --userdir u/' out.cast\""), "deny"
        )

    def test_timeout_inside_or_around_the_recording_passes(self):
        self.assertIsNone(violation("asciinema rec -c 'timeout -k 10s 20m ./cataclysm-bn' out.cast"))
        self.assertIsNone(violation("timeout -k 10s 20m asciinema rec -c ./cataclysm-bn out.cast"))

    def test_other_asciinema_commands_pass(self):
        self.assertIsNone(violation("asciinema play out.cast"))
        self.assertIsNone(violation("asciinema convert -f gif out.cast out.gif"))

    def test_recording_inside_a_named_script_is_checked(self):
        with tempfile.TemporaryDirectory() as tmp:
            script = Path(tmp, "cap.sh")
            script.write_text("asciinema rec -c ./cataclysm-bn out.cast\n")
            self.assertEqual(run_hook(f"bash {script}"), "deny")


if __name__ == "__main__":
    unittest.main()
