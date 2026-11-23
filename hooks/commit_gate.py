#!/usr/bin/env python3
"""PreToolUse hook: deny `git commit` when files changed after the last `git diff --shortstat` in this session.

The rule asks for a self-review and one LoC shrink pass over the whole diff before every commit.
Measuring the diff in its own call, after the last edit, is the step that starts that pass.
Only shell segments that start with the command count, so quoted prose never matches.
"""
import json
import re
import sys

GIT = r"^\s*git\s+(?:-[Cc]\s+\S+\s+)*"
COMMIT = re.compile(GIT + r"commit(?![-\w])")
SHORTSTAT = re.compile(GIT + r"diff\b.*--shortstat\b")
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
    """True when an edit came after the last standalone shortstat."""
    dirty = False
    for name, args in tool_uses(lines):
        command = args.get("command") if name == "Bash" else None
        if name in ("Edit", "Write", "NotebookEdit") or has(SHELL_EDIT, command):
            dirty = True
        elif has(SHORTSTAT, command) and not has(COMMIT, command):
            dirty = False
    return dirty


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
            "permissionDecisionReason": "Files changed after the last diff measurement. Run "
                                        "`git diff --shortstat <base>...` in its own call, review the whole "
                                        "diff for correctness and make one LoC shrink pass, then commit.",
        }}))


if __name__ == "__main__":
    main()
