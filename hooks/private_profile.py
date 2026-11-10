#!/usr/bin/env python3
"""PreToolUse hook: deny app launches that would read and write the user's real profile.

An automated launch under gamescope or xvfb-run, or a Cataclysm launch with `--userdir`/`--world`,
must isolate its config: `--configdir`, `XDG_CONFIG_HOME=` or `HOME=`. `--userdir` alone still
writes `~/.config/cataclysm-bn/options.json`. Checks the Bash command and the text of every script
file it names, since launches often live in a script (`cargo -Zscript live.rs`).
"""
import json
import re
import shlex
import sys
from pathlib import Path

LAUNCH = re.compile(r"\bgamescope\b(?!ctl)|\bxvfb-run\b|--userdir\b|--world\b")
ISOLATED = re.compile(r"--configdir\b|\bXDG_CONFIG_HOME=|(?<![\w$])HOME=")
SCRIPT_SUFFIXES = {".rs", ".sh", ".py", ".fish", ".ts", ".js"}


def script_texts(command):
    try:
        tokens = shlex.split(command, comments=True)
    except ValueError:
        tokens = command.split()
    for token in tokens:
        path = Path(token).expanduser()
        if path.suffix in SCRIPT_SUFFIXES and path.is_file() and path.stat().st_size < 1_000_000:
            yield path.read_text(errors="replace")


def violation(command):
    return next(
        (text for text in [command, *script_texts(command)] if LAUNCH.search(text) and not ISOLATED.search(text)),
        None,
    )


def main():
    data = json.load(sys.stdin)
    if data.get("tool_name") != "Bash":
        return
    if violation(data.get("tool_input", {}).get("command", "")) is None:
        return
    reason = (
        "This launch uses the user's real profile. Give the app a private config: "
        "Cataclysm `--userdir X/ --configdir X/config/`, other apps `XDG_CONFIG_HOME=X/config` "
        "(or `HOME=X`), in the command and in any script it runs."
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
