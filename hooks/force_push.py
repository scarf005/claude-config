#!/usr/bin/env python3
"""PreToolUse hook: deny a force-push to a default branch (main, master).

A repository allows it with `git config claude.forcePushDefaultBranch true` (local config, not committed).
The repository is the `git -C` path, else a leading `cd PATH`, else the session's working directory.
"""
import json
import re
import subprocess
import sys

PUSH = re.compile(r"\bgit\s+(?:-C\s+(\S+)\s+)?push\b(.*)")
FORCE = re.compile(r"(?:^|\s)(?:-f|--force\S*|-\w*f\w*|\+\S+)(?=\s|$)")
DEFAULT = re.compile(r"main|master")
CD = re.compile(r"^\s*cd\s+(\S+)\s*$")


def allowed(repo):
    out = subprocess.run(["git", "-C", repo, "config", "--get", "--bool", "claude.forcePushDefaultBranch"],
                         capture_output=True, text=True)
    return out.stdout.strip() == "true"


def violation(command, cwd, allow=allowed):
    repo = cwd
    for part in re.split(r"&&|\|\||;|\|", command):
        if m := CD.match(part):
            repo = m.group(1)
            continue
        m = PUSH.search(part)
        if m and FORCE.search(m.group(2)) and DEFAULT.search(m.group(2)) and not allow(m.group(1) or repo):
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
        "permissionDecisionReason": f"Force-push to a default branch is denied here ({part[:200]}). "
                                    "A repository allows it with `git config claude.forcePushDefaultBranch true`.",
    }}))


if __name__ == "__main__":
    main()
