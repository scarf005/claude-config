#!/usr/bin/env python3
"""PreToolUse hook: deny `rm` anywhere it runs as a command, including heredocs, quoted remote shells and wrappers.

Claude Code matches `Bash(rm:*)` against local command segments only, so `ssh phone bash <<'EOF' ... rm ... EOF`,
`bash -c 'rm x'` and `xargs rm` pass it. Use `gio trash` (or `tmp-rm` under /tmp) instead.
"""
import json
import re
import sys

RM = re.compile(r"(?:^|[\n;&`'\"]|\$\(|\b(?:sudo|xargs|exec|command|nice|nohup|timeout\s+\S+|env(?:\s+\w+=\S*)*"
                r"|ssh\s+\S+)\s)\s*(?:\\|/(?:usr/)?bin/)?rm(?=[\s;&|)]|$)", re.M)


def violation(command):
    return RM.search(command) if isinstance(command, str) else None


def main():
    data = json.load(sys.stdin)
    if data.get("tool_name") == "Bash" and violation(data.get("tool_input", {}).get("command")):
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "PreToolUse", "permissionDecision": "deny",
            "permissionDecisionReason": "Never run rm, also not in heredocs, remote shells or wrappers. "
                                        "Use `gio trash` (`tmp-rm` under /tmp)."}}))


if __name__ == "__main__":
    main()
