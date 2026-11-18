#!/usr/bin/env python3
"""PreToolUse hook: deny Android service dumps whose output goes into a pipe.

`dumpsys` and `cmd <service> dump` write from system_server while it holds service locks
(`cmd package dump` holds the ActivityManagerService lock). A slow or stalled pipe reader
(ssh, `head`, `rg -m`) blocks that write; after 60 s the watchdog kills system_server and
the phone soft-reboots. Redirect the dump to a file on the device, then read the file.
"""
import json
import re
import sys

PIPED_DUMP = re.compile(r"\b(?:dumpsys|cmd\s+\S+\s+dump)\b[^|>;&\n]*\|(?!\|)")


def violation(command):
    return PIPED_DUMP.search(re.sub(r"\d*>&\d+", "", command))


def main():
    data = json.load(sys.stdin)
    if data.get("tool_name") != "Bash" or violation(data.get("tool_input", {}).get("command", "")) is None:
        return
    reason = (
        "A piped Android service dump can block system_server on a service lock until the watchdog "
        "soft-reboots the phone. Write it to a device file first: "
        "`dumpsys package <pkg> > /data/local/tmp/d.txt` (or `$TMPDIR/d.txt` in Termux), then read that file."
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
