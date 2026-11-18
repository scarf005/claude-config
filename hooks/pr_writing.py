#!/usr/bin/env python3
"""PreToolUse hook for PR and issue text.

- Bash: a PR title or body write (`gh pr create`, `gh pr edit` with a title or body flag, `gh api` writes to
  pulls) runs only inside the `pr-writer` subagent, which starts without the session's context. Other PR or issue
  title/body writes need the `pr-writing` skill loaded (read from the session transcript).
- Agent: a `pr-writer` brief is capped at 600 characters, so the parent passes facts, not its session story.
"""
import json
import re
import shlex
import sys

REPO = r"(?:(?:-R|--repo)(?:\s+|=)?\S+\s+)?"
API_WRITE = (
    r"\bgh\s+api\b(?=[^\n]*/{kind}(?:/[^/\s'\"?]+)?(?=[\s?'\"]|$))(?![^\n]*\s(?:-X|--method)[\s=]*GET\b)"
    r"(?=[^\n]*(?:\s-[fF]|\s--(?:raw-)?field\b|\s--input\b|\s(?:-X|--method)[\s=]*(?:POST|PATCH|PUT)\b))"
    r"|\bgh\s+api\s+graphql\b[^\n]*\b(?:create|update){mutation}\b"
)
WRITE = re.compile(
    rf"\bgh\s+(?:pr|issue)\s+{REPO}(?:create|edit)\b|"
    + API_WRITE.format(kind="(?:pulls|issues)", mutation="(?:PullRequest|Issue)")
)
PR_WRITE = re.compile(
    rf"\bgh\s+pr\s+{REPO}create\b|\bgh\s+pr\s+{REPO}edit\b[^\n]*\s(?:--title\b|--body\b|--body-file\b|-[tbF])|"
    + API_WRITE.format(kind="pulls", mutation="PullRequest")
)
LOADED = re.compile(r'"skill"\s*:\s*"pr-writing"')
WRITER = "pr-writer"
BRIEF_LIMIT = 600


def segments(command):
    """Split a command into its simple commands at unquoted `;`, `&`, `|` and newlines; each comes back as one line."""
    lexer = shlex.shlex(command.replace("\\\n", " "), posix=True, punctuation_chars=";&|\n")
    lexer.whitespace = " \t\r"
    lexer.whitespace_split = True
    lexer.commenters = ""
    try:
        tokens = list(lexer)
    except ValueError:
        return [command.replace("\n", " ")]
    parts = [[]]
    for token in tokens:
        if set(token) <= set(";&|\n"):
            parts.append([])
        else:
            parts[-1].append(token.replace("\n", " "))
    return [" ".join(part) for part in parts]


def writes_body(command):
    return any(WRITE.search(s) for s in segments(command))


def writes_pr(command):
    return any(PR_WRITE.search(s) for s in segments(command))


def skill_loaded(transcript_path):
    try:
        with open(transcript_path, encoding="utf-8") as f:
            return LOADED.search(f.read()) is not None
    except OSError:
        return False


def brief_problem(tool_input):
    """Return a deny reason for an over-long `pr-writer` brief, else None."""
    if tool_input.get("subagent_type") != WRITER or len(tool_input.get("prompt", "")) <= BRIEF_LIMIT:
        return None
    return (
        f"A `{WRITER}` brief must stay within {BRIEF_LIMIT} characters: repo, PR number or branch and base, "
        "linked issues, capture URLs with what each shows, and the local test result. Leave out the session story."
    )


def deny_reason(data):
    tool_input = data.get("tool_input", {})
    if data.get("tool_name") == "Agent":
        return brief_problem(tool_input)
    if data.get("tool_name") != "Bash":
        return None
    command = tool_input.get("command", "")
    if writes_pr(command):
        if data.get("agent_type") == WRITER:
            return None
        return (
            f"Write PR titles and bodies only through the `{WRITER}` agent: Agent with subagent_type `{WRITER}` and a "
            f"brief within {BRIEF_LIMIT} characters. Do not reach the same effect through another command."
        )
    if writes_body(command) and not skill_loaded(data.get("transcript_path", "")):
        return (
            "Load the `pr-writing` skill before writing an issue title or body, then retry. "
            "If a command is blocked, report the blocker; do not reach the same effect through another command."
        )
    return None


def main():
    reason = deny_reason(json.load(sys.stdin))
    if reason:
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": reason,
            }
        }))


if __name__ == "__main__":
    main()
