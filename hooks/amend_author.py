#!/usr/bin/env python3
"""PreToolUse hook: deny `git commit --amend` when HEAD was written by someone other than the git user.

Amending another author's commit hides your change inside their commit. Add a new commit on top instead.
The repository is the `git -C` path, else a leading `cd PATH`, else the session's working directory.
"""
import json
import re
import subprocess
import sys

AMEND = re.compile(r"\bgit\s+(?:-C\s+(\S+)\s+)?(?:-c\s+\S+\s+)*commit\b[^|;&]*--amend\b")
CD = re.compile(r"^\s*cd\s+(\S+)\s*$")


def git(repo, *args):
    return subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True).stdout.strip()


def head_author_is_other(repo):
    """True when HEAD's author email differs from `user.email`."""
    author, user = git(repo, "log", "-1", "--format=%ae"), git(repo, "config", "user.email")
    return bool(author and user and author != user)


def violation(command, cwd, other=head_author_is_other):
    repo = cwd
    for part in re.split(r"&&|\|\||;|\|", command):
        if m := CD.match(part):
            repo = m.group(1)
            continue
        if (m := AMEND.search(part)) and other(m.group(1) or repo):
            return part.strip()
    return None


def main():
    data = json.load(sys.stdin)
    if data.get("tool_name") != "Bash":
        return
    part = violation(data.get("tool_input", {}).get("command", ""), data.get("cwd", "."))
    if part is None:
        return
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason": f"HEAD was written by another author; do not amend it ({part[:200]}). "
                                    "Add your change as a new commit on top.",
    }}))


if __name__ == "__main__":
    main()
