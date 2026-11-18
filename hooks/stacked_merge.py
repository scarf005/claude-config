#!/usr/bin/env python3
"""PreToolUse hook: deny `gh pr merge N` while other open PRs use PR N's head branch as their base.

Such PRs are a stack. Link them with `gh stack link` and merge with `gh stack merge`, so GitHub shows the stack
and moves the upper PRs to the new base.
"""
import json
import re
import subprocess
import sys

MERGE = re.compile(r"\bgh\s+pr\s+merge\b(.*)")
REPO = re.compile(r"(?:-R|--repo)[\s=](\S+)")
VALUED = re.compile(r"(?<!\S)(?:-R|--repo|--match-head-commit|-t|--subject|-b|--body|-A|--author-email)[\s=]\S+")
NUMBER = re.compile(r"(?:^|\s|/pull/)#?(\d+)(?=\s|$)")


def gh(*args):
    try:
        return subprocess.run(["gh", *args], capture_output=True, text=True, timeout=10).stdout.split()
    except (subprocess.TimeoutExpired, OSError):
        return []


def dependents(pr, repo):
    flag = ["-R", repo] if repo else []
    head = gh("pr", "view", pr, *flag, "--json", "headRefName", "-q", ".headRefName")
    if not head:
        return []
    return gh("pr", "list", *flag, "--base", head[0], "--state", "open", "--json", "number", "-q", ".[].number")


def violation(command, lookup=dependents):
    for part in re.split(r"&&|\|\||;|\|", command):
        m = MERGE.search(part)
        if not m:
            continue
        args = VALUED.sub(" ", m.group(1))
        pr = NUMBER.search(args)
        repo = REPO.search(m.group(1))
        if pr and (found := lookup(pr.group(1), repo and repo.group(1))):
            return pr.group(1), found
    return None


def main():
    data = json.load(sys.stdin)
    if data.get("tool_name") != "Bash":
        return
    hit = violation(data.get("tool_input", {}).get("command", ""))
    if hit is None:
        return
    pr, found = hit
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason": f"Open PRs {', '.join('#' + n for n in found)} use PR #{pr}'s branch as base. "
                                    "Link them with `gh stack link`, check `gh stack view`, "
                                    "then merge with `gh stack merge`.",
    }}))


if __name__ == "__main__":
    main()
