#!/usr/bin/env python3
"""PreToolUse hook: deny every write to a CLAUDE.md-style file (CLAUDE.md, CLAUDE.local.md, ...).

The user keeps rules in AGENTS.md; CLAUDE*.md files are theirs alone. Covers Edit/Write/NotebookEdit by path and
Bash commands that name such a file and also edit, move or delete files.
"""
import json
import os
import re
import sys

from commit_gate import SHELL_EDIT, has

NAME = re.compile(r"(?i)\bCLAUDE[\w.-]*\.md\b")
REMOVE = re.compile(r"^\s*(?:gio\s+trash|tmp-rm|rm|trash|unlink|ln)\b")


def violation(tool, args):
    if tool in ("Edit", "MultiEdit", "Write", "NotebookEdit"):
        path = args.get("file_path") or args.get("notebook_path") or ""
        return bool(NAME.fullmatch(os.path.basename(path)))
    command = args.get("command") if tool == "Bash" else None
    return isinstance(command, str) and bool(NAME.search(command)) and (
        has(SHELL_EDIT, command) or has(REMOVE, command))


def main():
    data = json.load(sys.stdin)
    if violation(data.get("tool_name"), data.get("tool_input") or {}):
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "PreToolUse", "permissionDecision": "deny",
            "permissionDecisionReason": "Never write, modify or delete CLAUDE*.md files. Put rules in AGENTS.md."}}))


if __name__ == "__main__":
    main()
