#!/usr/bin/env python3
"""PreToolUse hook: deny writing a prose file until this session loaded humanizer and read its patterns.md.

commit_gate.py checks only at commit time, after the text exists. Check earlier, at the first README, doc, issue form
or skill write.
"""
import json
import re
import sys

from commit_gate import tool_uses

PROSE = re.compile(r"(?i)(?:\.(?:md|mdx|rst|txt)|/\.github/(?:ISSUE_TEMPLATE/[^/]+|pull_request_template[^/]*))$")
NOTES = re.compile(r"/memory/|/\.claude/context/|^/tmp/")
PATTERNS = "humanizer/references/patterns.md"


def missing(lines):
    """Steps still missing before prose: loading the skill, reading its pattern reference."""
    loaded = read = False
    for name, args in tool_uses(lines):
        loaded = loaded or (name == "Skill" and args.get("skill") == "humanizer")
        read = read or (name == "Read" and str(args.get("file_path", "")).endswith(PATTERNS)) or (
            name == "Bash" and PATTERNS in str(args.get("command", "")))
    return [step for step, done in [("load the `humanizer` skill", loaded),
                                    (f"read ~/.config/claude/skills/{PATTERNS}", read)] if not done]


def main():
    try:
        data = json.load(sys.stdin)
        path = data["tool_input"].get("file_path") or ""
        if not PROSE.search(path) or NOTES.search(path):
            return
        with open(data["transcript_path"]) as f:
            steps = missing(f.readlines())
    except (ValueError, KeyError, TypeError, AttributeError, OSError):
        return
    if steps:
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "PreToolUse", "permissionDecision": "deny",
            "permissionDecisionReason": f"{path} is prose. First {' and '.join(steps)}, then write it by the "
                                        "skill's How to work steps."}}))


if __name__ == "__main__":
    main()
