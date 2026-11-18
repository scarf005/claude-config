#!/usr/bin/env python3
"""Stop hook: block once when this turn chained a PR onto an open PR's branch (`gh pr create|edit --base B`)
and ran no `gh stack link|submit` afterwards.

Base-chained PRs are not a GitHub stack: only `gh stack link|submit` makes one, at github.com/<repo>/stack/<N>.
"""
import json
import re
import subprocess
import sys

from stacked_merge import REPO

CREATE = re.compile(r"\bgh\s+pr\s+(?:create|edit)\b(.*)")
LINK = re.compile(r"\bgh\s+stack\s+(?:link|submit)\b(?!.*(?<!\S)(?:--help|-h)(?!\S))")
BASE = re.compile(r"(?<!\S)(?:--base|-B)[\s=](\S+)")
QUOTED = re.compile(r"'[^']*'|\"(?:\\.|[^\"\\])*\"")


def turn_commands(path):
    """Bash commands since the last prompt the user typed (tool results are user entries too)."""
    cmds = []
    try:
        lines = open(path).read().splitlines()
    except OSError:
        return cmds
    for line in lines:
        try:
            entry = json.loads(line)
        except ValueError:
            continue
        if not isinstance(entry, dict):
            continue
        message = entry.get("message")
        content = message.get("content") if isinstance(message, dict) else None
        blocks = [b for b in content if isinstance(b, dict)] if isinstance(content, list) else []
        if entry.get("type") == "user" and not any(b.get("type") == "tool_result" for b in blocks):
            cmds = []
        elif entry.get("type") == "assistant":
            cmds += [str(b.get("input", {}).get("command") or "") for b in blocks
                     if b.get("type") == "tool_use" and b.get("name") == "Bash"]
    return cmds


def is_pr_head(base, repo):
    flag = ["-R", repo] if repo else []
    try:
        out = subprocess.run(["gh", "pr", "list", *flag, "--head", base, "--state", "open", "--json", "number", "-q",
                              ".[].number"], capture_output=True, text=True, timeout=6).stdout
    except (subprocess.TimeoutExpired, OSError):
        return False
    return bool(out.strip())


def violation(cmds, lookup=is_pr_head):
    pending = []
    for command in cmds:
        flat = QUOTED.sub(lambda q: re.sub(r"[\s;&|]", "_", q.group(0)[1:-1]), command)
        for part in re.split(r"&&|\|\||;|\||\n", flat):
            if LINK.search(part):
                pending = []
            elif (m := CREATE.search(part)) and (base := BASE.search(m.group(1))):
                repo = REPO.search(m.group(1))
                pending.append((repo and repo.group(1), base.group(1)))
    return [hit for hit in list(dict.fromkeys(pending))[:3] if lookup(hit[1], hit[0])]


def main():
    data = json.load(sys.stdin)
    if data.get("stop_hook_active") or not data.get("transcript_path"):
        return
    hits = violation(turn_commands(data["transcript_path"]))
    if not hits:
        return
    bases = ", ".join(f"{repo or 'this repo'}:{base}" for repo, base in hits)
    print(json.dumps({"decision": "block", "reason":
        f"PRs chained with --base onto open PR branches ({bases}) are not a GitHub stack. "
        "Run `gh stack link <bottom> ... <top>`, check `gh stack view`, and report the github.com/<repo>/stack/<N> URL. "
        "Never call base-chained PRs a stack."}))


if __name__ == "__main__":
    main()
