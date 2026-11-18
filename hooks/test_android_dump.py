import unittest

from android_dump import violation


class AndroidDumpTest(unittest.TestCase):
    def test_piped_dump_is_denied(self):
        # The command that soft-rebooted the phone: rg -m3 stalls the pipe while AMS is locked.
        for cmd in ["ssh phone 'cmd package dump app.gamenative 2>&1 | rg -m3 -i sig'",
                    "adb shell dumpsys activity | head", "adb shell 'dumpsys package x|tail'"]:
            self.assertIsNotNone(violation(cmd), cmd)

    def test_dump_to_device_file_and_unrelated_pipes_are_allowed(self):
        for cmd in ["adb shell 'dumpsys package x > /data/local/tmp/d.txt'",
                    "adb shell dumpsys battery", "adb shell 'dumpsys x || true'",
                    "adb shell logcat -d | rg Watchdog", "cmd package list packages | head"]:
            self.assertIsNone(violation(cmd), cmd)


if __name__ == "__main__":
    unittest.main()
