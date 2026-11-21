#!/usr/bin/env python3
"""PreToolUse hook: deny a force-push to a default branch (main, master), or to a branch whose open PR has reviews.

A repository allows default-branch force-push with `git config claude.forcePushDefaultBranch true`, or only to
one remote repository with `git config claude.forcePushDefaultBranch OWNER/REPO`.
A force-push that dismisses reviews needs the user's approval, then `CLAUDE_REVIEWED_PUSH_OK=1` in the command.
The repository is the `git -C` path, else a leading `cd PATH`, else the session's working directory.
"""
import json
import re
import subprocess
import sys

PUSH = re.compile(r"\bgit\s+(?:-C\s+(\S+)\s+)?push\b(.*)")
FORCE = re.compile(r"(?:^|\s)(?:-f|--force\S*|-\w*f\w*|\+\S+)(?=\s|$)")
DEFAULT = re.compile(r"(?<![\w/.-])(?:refs/heads/)?(?:main|master)(?![\w/.-])")
CD = re.compile(r"^\s*cd\s+(\S+)\s*$")


def allowed(repo, remote):
    out = subprocess.run(["git", "-C", repo, "config", "--get", "claude.forcePushDefaultBranch"],
                         capture_output=True, text=True).stdout.strip()
    return out.lower() in ("true", "yes", "on", "1") or (bool(out) and out == remote_slug(repo, remote))


def remote_slug(repo, remote):
    url = subprocess.run(["git", "-C", repo, "remote", "get-url", remote], capture_output=True, text=True).stdout
    m = re.search(r"github\.com[:/]([^/\s]+/[^/\s]+?)(?:\.git)?\s*$", url)
    return m.group(1) if m else None


def reviewers(repo, remote, branch):
    """Logins of reviews on the open PR with head `branch` in the remote's repository; None if unknown."""
    slug = remote_slug(repo, remote)
    if not slug:
        return []
    try:
        out = subprocess.run(["gh", "pr", "list", "-R", slug, "--head", branch, "--state", "open", "--json",
                              "reviews", "-q", "[.[].reviews[] | select(.state != \"DISMISSED\") | .author.login]"],
                             capture_output=True, text=True, timeout=4)
    except subprocess.TimeoutExpired:
        return None
    return json.loads(out.stdout) if out.returncode == 0 and out.stdout.strip() else None


def destinations(args):
    words = [w for w in args.split() if not w.startswith("-")]
    return words[0] if words else None, [w.lstrip("+").split(":")[-1].removeprefix("refs/heads/") for w in words[1:]]


def reviewed(command, cwd, lookup=reviewers):
    """(branch, logins) of the first force-pushed branch with reviews, or (branch, None) when unknown."""
    if "CLAUDE_REVIEWED_PUSH_OK=1" in command:
        return None
    repo = cwd
    for part in re.split(r"&&|\|\||;|\|", command):
        if m := CD.match(part):
            repo = m.group(1)
            continue
        m = PUSH.search(part)
        if not (m and FORCE.search(m.group(2))):
            continue
        remote, branches = destinations(m.group(2))
        for branch in branches:
            logins = lookup(m.group(1) or repo, remote, branch)
            if logins is None or logins:
                return branch, logins
    return None


def violation(command, cwd, allow=allowed):
    repo = cwd
    for part in re.split(r"&&|\|\||;|\|", command):
        if m := CD.match(part):
            repo = m.group(1)
            continue
        m = PUSH.search(part)
        if m and FORCE.search(m.group(2)) and DEFAULT.search(m.group(2)) and \
                not allow(m.group(1) or repo, destinations(m.group(2))[0]):
            return part.strip()
    return None


def main():
    data = json.load(sys.stdin)
    if data.get("tool_name") != "Bash":
        return
    command, cwd = data.get("tool_input", {}).get("command", ""), data.get("cwd", ".")
    if hit := reviewed(command, cwd):
        branch, logins = hit
        who = ", ".join(sorted(set(logins))) if logins else "unknown (PR lookup failed)"
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": f"Force-pushing {branch} dismisses reviews on its open PR by {who}. "
                                        "Ask the user first; after approval add CLAUDE_REVIEWED_PUSH_OK=1 to the command.",
        }}))
        return
    part = violation(command, cwd)
    if part is None:
        return
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason": f"Force-push to a default branch is denied here ({part[:200]}). "
                                    "A repository allows it with `git config claude.forcePushDefaultBranch true` (or OWNER/REPO for one remote).",
    }}))


if __name__ == "__main__":
    main()
