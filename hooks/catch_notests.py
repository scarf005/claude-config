#!/usr/bin/env python3
"""PreToolUse hook: deny Catch2 test runs (cata_test) that would exit 0 when the filter matches nothing.

A malformed test spec (e.g. a name wildcard followed by a tag exclusion) selects no tests, and Catch2
then exits 0, which reads as a pass. `-w NoTests` makes such a run fail. Checks the command and any
script file it names.
"""
import json
import re
import sys

from private_profile import script_texts

RUN = re.compile(r"\S*/cata_test[-\w]*(?=\s|$)")
SKIP = re.compile(r"--target|--list|\b(?:cp|ls|mv|stat|file|du|install)\s|systemctl|gio trash|tmp-rm")
NOTESTS = re.compile(r"(?:-w|--warn)\s+NoTests")


def violation(command):
    for text in [command, *script_texts(command)]:
        for line in text.splitlines():
            if RUN.search(line) and not SKIP.search(line) and not NOTESTS.search(line):
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
        "Catch2 exits 0 when a test filter matches nothing. Add `-w NoTests` to every cata_test run "
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
