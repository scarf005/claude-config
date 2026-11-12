#!/usr/bin/env python3
"""PreToolUse hook: deny Edit/Write under ~/.config while the target's git repo has uncommitted tracked changes.

Existing changes are user-owned and must be committed as their own checkpoint before new edits, so the new
change stays a separate commit. Untracked files and submodule state are ignored.
"""
import json
import os
import subprocess
import sys

CONFIG = os.path.expanduser("~/.config")
GIT_ENV = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}


def git(repo, *args):
    done = subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True, env=GIT_ENV)
    return done.stdout.strip() if done.returncode == 0 else ""


def dirty_files(path, root=CONFIG):
    """Return (repo, tracked changes) for the repo owning `path`, or None when `path` is outside `root`."""
    real = os.path.realpath(path)
    if not real.startswith(os.path.realpath(root) + os.sep):
        return None
    repo = git(os.path.dirname(real) if os.path.isdir(os.path.dirname(real)) else root, "rev-parse", "--show-toplevel")
    if not repo:
        return None
    status = git(repo, "status", "--porcelain", "--untracked-files=no", "--ignore-submodules=all")
    return repo, status.splitlines()


def main():
    data = json.load(sys.stdin)
    path = data.get("tool_input", {}).get("file_path") or data.get("tool_input", {}).get("notebook_path")
    if not path:
        return
    found = dirty_files(path)
    if found is None or not found[1]:
        return
    repo, files = found
    reason = (
        f"{repo} has uncommitted changes ({', '.join(f[3:] for f in files[:5])}). They are user-owned: "
        "commit them first as a separate checkpoint commit (`git add <those paths>`, then commit), then retry the edit."
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
