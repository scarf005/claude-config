#!/usr/bin/env python3
"""PreToolUse hook: deny `gh stack link|init` with more than 3 PRs or branches.

A PR holds what a reviewer judges on its own. Work steps, lanes, issues and commits are not PR borders.
A larger stack needs the user's approval of the split first; then mark the command with STACK_SPLIT_OK=1.
"""
import json
import re
import shlex
import sys

STACK = re.compile(r"\bgh\s+stack\s+(?:link|init)\b(.*)")
VALUED = {"--base", "--remote"}
APPROVED = re.compile(r"\bSTACK_SPLIT_OK=1\b")
LIMIT = 3


def members(args):
    try:
        tokens = shlex.split(args)
    except ValueError:
        tokens = args.split()
    found, skip = [], False
    for token in tokens:
        if skip:
            skip = False
        elif token in VALUED:
            skip = True
        elif not token.startswith("-"):
            found.append(token)
    return found


def violation(command):
    if APPROVED.search(command):
        return None
    for part in re.split(r"&&|\|\||;|\||\n", command):
        m = STACK.search(part)
        if m and len(found := members(m.group(1))) > LIMIT:
            return found
    return None


def main():
    data = json.load(sys.stdin)
    if data.get("tool_name") != "Bash":
        return
    found = violation(data.get("tool_input", {}).get("command", ""))
    if found is None:
        return
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason": f"This stack has {len(found)} PRs; the limit without approval is {LIMIT}. "
                                    "Merge PRs that a reviewer would judge together (same defect, same kind of "
                                    "change), or show the user the split with additions per PR, then add "
                                    "STACK_SPLIT_OK=1 to the command.",
    }}))


if __name__ == "__main__":
    main()
