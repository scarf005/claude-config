#!/usr/bin/env python3
"""PreToolUse hook: deny benchmark runs on the local machine.

Other jobs share this machine, so local timings are skewed. Run benchmarks on GitHub CI. CI runners
have no GPU, so allow a local run that sets CATA_TEST_COMPUTE_ACCELERATION=gpu or runs the game binary
(default COMPUTE_ACCELERATION=auto). Check the command and every script that a non-reading command in
it names.
"""
import json
import re
import sys

from private_profile import READERS, program, script_texts, shell_commands

BENCH = re.compile(
    r"\bhyperfine\b|\bperf\s+(?:stat|record)\b|\bprofile_(?:wait|walk)\b|\bPROFILE_WAIT\w*=|"
    r"--benchmark-samples|\[\.?benchmark\]|^\s*(?:export\s+|env\s+)?CCACHE_DISABLE=1\b|"
    r"(?:/usr/bin/time|^\s*time)\b.*\b(?:ninja|cmake\s+--build|make)\b"
)
GPU_PATH = re.compile(r"\bCATA_TEST_COMPUTE_ACCELERATION=['\"]?gpu\b|\bcataclysm-bn-tiles\b")
GPU_EXPORT = re.compile(r"^\s*export\s.*\bCATA_TEST_COMPUTE_ACCELERATION=['\"]?gpu\b", re.M)


def violation(command):
    scripts = [text for part in shell_commands(command) if program(part) not in READERS for text in script_texts(part)]
    return next(
        (
            part
            for text in [command, *scripts]
            if not GPU_EXPORT.search(text)
            for part in shell_commands(text)
            if BENCH.search(part) and program(part) not in READERS and not GPU_PATH.search(part)
        ),
        None,
    )


def main():
    data = json.load(sys.stdin)
    if data.get("tool_name") != "Bash":
        return
    line = violation(data.get("tool_input", {}).get("command", ""))
    if line is None:
        return
    reason = (
        "Run CPU-path benchmarks on GitHub CI, not on this shared machine. To measure the hardware "
        "GPU path locally, set CATA_TEST_COMPUTE_ACCELERATION=gpu on the command "
        f"(offending line: {line.strip()[:200]})."
    )
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }))


if __name__ == "__main__":
    main()
