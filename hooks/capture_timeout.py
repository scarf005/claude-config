#!/usr/bin/env python3
"""PreToolUse hook: deny `asciinema rec` runs without a `timeout`.

asciinema 3 keeps running after the tmux pane that started it closes, and the recorded program sits on
asciinema's pty waiting for input. Leftover tiles builds each hold about 90 MiB of VRAM.
Checks the Bash command and the text of every script file it names.
"""
import json
import re
import sys

from private_profile import script_texts

RECORD = re.compile(r"\basciinema\s+rec\b")
TIMEOUT = re.compile(r"\btimeout\s")


def violation(command):
    return next(
        (text for text in [command, *script_texts(command)] if RECORD.search(text) and not TIMEOUT.search(text)),
        None,
    )


def main():
    data = json.load(sys.stdin)
    if data.get("tool_name") != "Bash":
        return
    if violation(data.get("tool_input", {}).get("command", "")) is None:
        return
    reason = (
        "Bound the recording: `asciinema rec -c 'timeout -k 10s <limit> <cmd>' <file>`. A closed tmux pane "
        "leaves asciinema and the recorded program running, and each leftover game holds VRAM."
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
