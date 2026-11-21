#!/usr/bin/env python3
"""PreToolUse hook: deny per-run PulseAudio null sinks.

A killed run skips its unload step, so each per-run sink stays in the desktop's output device list.
Runs share one sink, agent_mute, created only when missing and never unloaded.
Checks the command and any script file it names.
"""
import json
import re
import sys

from private_profile import script_texts

LOAD = re.compile(r"\bload-module\s+module-null-sink\b")
SHARED = re.compile(r"\bsink_name=agent_mute\b")
READ = re.compile(r"^\s*(?:rg|cat|sed|git|gh|ls|fd|head|tail|wc|echo)\b")


def violation(command):
    for text in [command, *script_texts(command)]:
        for line in text.splitlines():
            if LOAD.search(line) and not SHARED.search(line) and not READ.search(line):
                return line
    return None


def main():
    data = json.load(sys.stdin)
    if data.get("tool_name") != "Bash":
        return
    line = violation(data.get("tool_input", {}).get("command", ""))
    if line is None:
        return
    reason = (
        "Do not load a per-run null sink: a killed run leaves it in the desktop's output list. Run with "
        "PULSE_SINK=agent_mute and create it only when missing: pactl list short sinks | rg -q '\\sagent_mute\\s' "
        "|| pactl load-module module-null-sink sink_name=agent_mute "
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
