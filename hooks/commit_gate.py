#!/usr/bin/env python3
"""PreToolUse hook: deny `git commit` until the diff is measured and read after the last edit in this session.

The rule asks for a self-review and one LoC shrink pass over the whole diff before every commit.
A `git diff --shortstat` and a patch-showing `git diff`/`git show`, both after the last edit, start that pass.
Only shell segments that start with the command count, so quoted prose never matches.
"""
import json
import re
import sys

GIT = r"^\s*git\s+(?:-[Cc]\s+\S+\s+)*"
COMMIT = re.compile(GIT + r"commit(?![-\w])")
SHORTSTAT = re.compile(GIT + r"diff\b.*--shortstat\b")
PATCH = re.compile(GIT + r"(?:diff|show)\b(?!.*--(?:shortstat|stat|numstat|name-only|name-status|quiet|exit-code)\b)")
SHELL_EDIT = re.compile(r"^\s*sed\s+-i\b|" + GIT + r"apply\b")
SEPARATOR = re.compile(r"&&|\|\||;|\||\n")


def has(pattern, command):
    return isinstance(command, str) and any(pattern.search(part) for part in SEPARATOR.split(command))


def tool_uses(lines):
    for line in lines:
        try:
            entry = json.loads(line)
        except ValueError:
            continue
        message = entry.get("message") if isinstance(entry, dict) and entry.get("type") == "assistant" else None
        content = message.get("content") if isinstance(message, dict) else None
        for block in content if isinstance(content, list) else []:
            if isinstance(block, dict) and block.get("type") == "tool_use" and isinstance(block.get("input"), dict):
                yield block.get("name"), block["input"]


def needs_review(lines):
    """True when the last edit is not followed by both a shortstat and a patch, outside commit commands."""
    measured = read = True
    for name, args in tool_uses(lines):
        command = args.get("command") if name == "Bash" else None
        if name in ("Edit", "Write", "NotebookEdit") or has(SHELL_EDIT, command):
            measured = read = False
        elif not has(COMMIT, command):
            measured = measured or has(SHORTSTAT, command)
            read = read or has(PATCH, command)
    return not (measured and read)


def main():
    try:
        data = json.load(sys.stdin)
        if not has(COMMIT, data["tool_input"]["command"]):
            return
        with open(data["transcript_path"]) as f:
            dirty = needs_review(f)
    except (ValueError, KeyError, TypeError, OSError):
        return
    if dirty:
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": "Files changed after the last diff review. Run "
                                        "`git diff --shortstat <base>...` and read the whole patch "
                                        "(`git diff <base>...`), review it for correctness, make one LoC "
                                        "shrink pass, then commit.",
        }}))


if __name__ == "__main__":
    main()
