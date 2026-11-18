#!/usr/bin/env python3
"""Edit/Write hook: deny edits under ~/.config while the target's git repo has uncommitted tracked changes.

Existing changes are user-owned and must be committed as their own checkpoint before new edits, so the new
change stays a separate commit. Untracked files and submodule state are ignored.

PostToolUse records a hash of each file the session wrote. PreToolUse treats a changed file as the session's own
while its content still matches that hash, so a session can edit one file several times in a row.
"""
import hashlib
import json
import os
import subprocess
import sys

CONFIG = os.path.expanduser("~/.config")
STATE = os.path.join(os.environ.get("XDG_RUNTIME_DIR", "/tmp"), "claude-dirty-config")
GIT_ENV = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}


def git(repo, *args):
    done = subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True, env=GIT_ENV)
    return done.stdout.rstrip() if done.returncode == 0 else ""


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


def digest(path):
    try:
        with open(path, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()
    except OSError:
        return None


def load(session, state_dir):
    try:
        with open(os.path.join(state_dir, f"{session}.json")) as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def record_edit(path, session, state_dir=STATE):
    """Remember the content `session` left in `path`."""
    owned = load(session, state_dir) | {os.path.realpath(path): digest(path)}
    os.makedirs(state_dir, exist_ok=True)
    with open(os.path.join(state_dir, f"{session}.json"), "w") as f:
        json.dump(owned, f)


def foreign_files(path, session, root=CONFIG, state_dir=STATE):
    """Return changed files in the repo of `path` whose content `session` did not write."""
    found = dirty_files(path, root)
    if found is None:
        return []
    repo, files = found
    owned = load(session, state_dir)
    rels = [f[3:] for f in files]
    return [r for r in rels if owned.get(os.path.join(repo, r)) != digest(os.path.join(repo, r))]


def main():
    data = json.load(sys.stdin)
    path = data.get("tool_input", {}).get("file_path") or data.get("tool_input", {}).get("notebook_path")
    session = data.get("session_id", "")
    if not path or not session:
        return
    if data.get("hook_event_name") == "PostToolUse":
        if dirty_files(path) is not None:
            record_edit(path, session)
        return
    foreign = foreign_files(path, session)
    if not foreign:
        return
    reason = (
        f"{dirty_files(path)[0]} has uncommitted changes ({', '.join(foreign[:5])}). They are user-owned: "
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
