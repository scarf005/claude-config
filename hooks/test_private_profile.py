import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from private_profile import violation

HOOK = Path(__file__).with_name("private_profile.py")


def run_hook(command, tool="Bash"):
    out = subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps({"tool_name": tool, "tool_input": {"command": command}}),
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    return json.loads(out)["hookSpecificOutput"]["permissionDecision"] if out else None


class PrivateProfileTest(unittest.TestCase):
    def test_gamescope_without_private_config_is_denied(self):
        self.assertEqual(run_hook("gamescope --backend headless -- ./cataclysm-bn-tiles --userdir ud/"), "deny")

    def test_userdir_without_configdir_is_denied(self):
        self.assertIsNotNone(violation("./cataclysm-bn-tiles --userdir ud/ --world test"))

    def test_configdir_or_xdg_config_home_passes(self):
        self.assertIsNone(violation("gamescope -- game --userdir ud/ --configdir ud/config/"))
        self.assertIsNone(violation("XDG_CONFIG_HOME=/tmp/x gamescope -- godot"))
        self.assertIsNone(violation("env HOME=/tmp/h xvfb-run app"))

    def test_launch_inside_a_named_script_is_checked(self):
        with tempfile.TemporaryDirectory() as tmp:
            script = Path(tmp, "live.rs")
            script.write_text('Command::new("gamescope").args(["--", "game", "--userdir", ud]);')
            self.assertEqual(run_hook(f"cargo +nightly -Zscript {script} game"), "deny")
            script.write_text('Command::new("gamescope").args(["--", "game", "--configdir", cfg]);')
            self.assertIsNone(run_hook(f"cargo +nightly -Zscript {script} game"))

    def test_unrelated_commands_pass(self):
        self.assertIsNone(violation("gamescopectl screenshot shot.png"))
        self.assertIsNone(violation("./cataclysm-bn-tiles --check-mods"))
        self.assertIsNone(run_hook("gamescope", tool="Read"))


class CmakePresetTest(unittest.TestCase):
    def test_preset_configure_needs_absolute_compiler(self):
        from cmake_preset import violation as preset_violation
        self.assertIsNotNone(preset_violation("cmake --preset linux-full -DTILES=ON"))
        self.assertIsNone(preset_violation(
            "PATH=/usr/bin:$PATH cmake --preset linux-full -DCMAKE_C_COMPILER=/usr/bin/clang "
            "-DCMAKE_CXX_COMPILER=/usr/bin/clang++ -U CMAKE_RUNTIME_OUTPUT_DIRECTORY"))
        self.assertIsNotNone(preset_violation(
            "cmake --preset linux-full -DCMAKE_CXX_COMPILER=/usr/bin/clang++"))
        self.assertIsNone(preset_violation("cmake --build --preset linux-full --target x"))


if __name__ == "__main__":
    unittest.main()
