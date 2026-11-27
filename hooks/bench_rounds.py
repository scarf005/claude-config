#!/usr/bin/env python3
"""PreToolUse hook: deny pushes of CI benchmark branches that run more than 5 rounds.

The user asked for 5 rounds; more only costs CI time. Reads the workflows of the commit a
`git push ... <src>:[refs/heads/]bench/...` sends and counts the items of `for <var> in 1 2 ...` loops.
"""
import json
import re
import shlex
import subprocess
import sys

from private_profile import program, shell_commands

MAX_ROUNDS = 5
LOOP = re.compile(r"\bfor\s+\w+\s+in\s+((?:\d+\s+)+\d+)\s*;")


def workflow_rounds(src, cwd):
    """Largest numeric loop length in the workflows of `src`, or None when `src` does not resolve."""
    tree = subprocess.run(["git", "ls-tree", "-r", "--name-only", src, ".github/workflows"], cwd=cwd,
                          capture_output=True, text=True)
    if tree.returncode != 0:
        return None
    rounds = 0
    for path in tree.stdout.split():
        text = subprocess.run(["git", "show", f"{src}:{path}"], cwd=cwd, capture_output=True, text=True).stdout
        rounds = max([rounds, *(len(m[1].split()) for m in LOOP.finditer(text))])
    return rounds


def violation(command, cwd):
    for part in shell_commands(command):
        try:
            words = shlex.split(part)
        except ValueError:
            continue
        if program(part) == "cd" and len(words) > 1:
            cwd = words[1]
            continue
        if program(part) != "git" or "push" not in words or {"-d", "--delete"} & set(words):
            continue
        for word in words[words.index("push") + 1:]:
            src, colon, dst = word.lstrip("+").partition(":")
            dst = dst if colon else src
            if not src or not re.match(r"(refs/heads/)?bench/", dst):
                continue
            if "$" in src or "`" in src:
                return f"`{word}` hides the pushed commit. Push a bench branch from a literal SHA or ref."
            rounds = workflow_rounds(src, cwd)
            if rounds is None:
                return f"`{src}` does not resolve in {cwd}. Push a bench branch from a literal SHA or ref."
            if rounds > MAX_ROUNDS:
                return (f"`{word}` pushes a benchmark with {rounds} rounds. The user asked for {MAX_ROUNDS}; "
                        f"change the workflow loop to {MAX_ROUNDS} rounds.")
    return None


def main():
    data = json.load(sys.stdin)
    if data.get("tool_name") != "Bash":
        return
    reason = violation(data.get("tool_input", {}).get("command", ""), data.get("cwd", "."))
    if reason:
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                                                 "permissionDecisionReason": reason}}))


if __name__ == "__main__":
    main()
