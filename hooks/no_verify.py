#!/usr/bin/env python3
"""PreToolUse hook: deny git commands that skip hooks (`--no-verify`, `-c core.hooksPath=...`).

A rewrite that changes only commit messages (trees unchanged) may skip hooks; mark it with
CLAUDE_MSG_ONLY_REWRITE=1.
"""
import json
import re
import sys

BYPASS = re.compile(r"\bgit\b[^|;&\n]*?(?:\s--no-verify\b|\s-c\s*core\.hooksPath\b)", re.IGNORECASE)
APPROVED = re.compile(r"\bCLAUDE_MSG_ONLY_REWRITE=1\b")


def violation(command):
    if APPROVED.search(command):
        return None
    m = BYPASS.search(command)
    return m.group(0) if m else None


def main():
    data = json.load(sys.stdin)
    if data.get("tool_name") != "Bash":
        return
    hit = violation(data.get("tool_input", {}).get("command", ""))
    if hit is None:
        return
    reason = (
        "Never bypass git hooks. Fix what the hook reports instead. For a rewrite that changes only commit "
        f"messages, add CLAUDE_MSG_ONLY_REWRITE=1 (offending part: {hit.strip()[:200]})."
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
