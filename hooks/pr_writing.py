#!/usr/bin/env python3
"""PreToolUse hook: deny commands that write a PR or issue title/body unless the `pr-writing` skill was loaded.

Covers `gh pr|issue create|edit` and `gh api` calls that touch pulls/issues, so the same text cannot reach
GitHub through a different command. The skill load is read from the session transcript.
"""
import json
import re
import sys

WRITE = re.compile(r"\bgh\s+(?:pr|issue)\s+(?:create|edit)\b|\bgh\s+api\b[^\n]*/(?:pulls|issues)\b")
LOADED = re.compile(r'"skill"\s*:\s*"pr-writing"')


def writes_body(command):
    return WRITE.search(command) is not None


def skill_loaded(transcript_path):
    try:
        with open(transcript_path, encoding="utf-8") as f:
            return LOADED.search(f.read()) is not None
    except OSError:
        return False


def main():
    data = json.load(sys.stdin)
    if data.get("tool_name") != "Bash":
        return
    if not writes_body(data.get("tool_input", {}).get("command", "")):
        return
    if skill_loaded(data.get("transcript_path", "")):
        return
    reason = (
        "Load the `pr-writing` skill before writing a PR or issue title or body, then retry. "
        "If a command is blocked, report the blocker; do not reach the same effect through another command."
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
