#!/usr/bin/env python3
"""PreToolUse hook for PR and issue text.

- Bash: a PR title or body write (`gh pr create`, `gh pr edit` with a title or body flag, `gh api` writes to
  pulls) runs only inside the `pr-writer` subagent, which starts without the session's context. Other PR or issue
  title/body writes need the `pr-writing` skill loaded (read from the session transcript).
- Agent: a `pr-writer` brief is capped at 600 characters, so the parent passes facts, not its session story.
"""
import json
import os
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
TICKED_ISSUE_BOX = re.compile(r"^\s*- \[[xX]\] I linked any relevant issues.*$", re.M)
ISSUE_REF = re.compile(r"(?:^|[\s(])#\d+\b|/(?:issues|pull)/\d+")
# `mktemp` names: the default `tmp.XXXXXXXXXX`, or a template such as `pr-body.XXXXXX` (random suffix).
TEMP_NAME = re.compile(r"^tmp\.?[A-Za-z0-9_]{6,}(?:\.\w+)?$|\.(?=[a-z]*[A-Z0-9])[A-Za-z0-9]{6,}$")
GH_API = re.compile(r"\bgh\s+api\b")
BODY_HOW = (
    "Run `mktemp` alone, write the body to the path it prints with the Write tool, then pass that literal path "
    "to `--body-file` in a command of its own. If that is blocked too, report the blocker and stop."
)


def token_segments(command):
    """Split a command into its simple commands at unquoted `;`, `&`, `|` and newlines; each is a list of words."""
    lexer = shlex.shlex(command.replace("\\\n", " "), posix=True, punctuation_chars=";&|\n")
    lexer.whitespace = " \t\r"
    lexer.whitespace_split = True
    lexer.commenters = ""
    try:
        tokens = list(lexer)
    except ValueError:
        return [command.replace("\n", " ").split()]
    parts = [[]]
    for token in tokens:
        if set(token) <= set(";&|\n"):
            parts.append([])
        else:
            parts[-1].append(token.replace("\n", " "))
    return parts


def segments(command):
    """`token_segments`, each simple command joined into one line."""
    return [" ".join(part) for part in token_segments(command)]


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


def body_files(command):
    """Return the `--body-file`/`-F` paths of `gh pr` writes in a command; None for a body that is not in a file."""
    paths = []
    for tokens in token_segments(command):
        if not PR_WRITE.search(" ".join(tokens)):
            continue
        if GH_API.search(" ".join(tokens)):
            return None
        values = iter(tokens)
        for flag in values:
            if flag in ("--title", "-t"):
                next(values, None)
            elif flag in ("--body-file", "-F"):
                paths.append(next(values, ""))
            elif flag.startswith("--body-file="):
                paths.append(flag.split("=", 1)[1])
            elif flag.startswith("-F"):
                paths.append(flag[2:].removeprefix("="))
            elif flag == "--body" or flag.startswith(("--body=", "-b")):
                return None
    return paths


def ticked_issue_box_without_issue(body):
    """True when the body ticks the linked-issue checkbox but links no issue or PR."""
    without_box = TICKED_ISSUE_BOX.sub("", body)
    return TICKED_ISSUE_BOX.search(body) is not None and ISSUE_REF.search(without_box) is None


def body_problem(command):
    paths = body_files(command)
    if paths is None:
        return f"Write the PR body only with `gh pr create` or `gh pr edit` and `--body-file <path>`. {BODY_HOW}"
    for path in paths:
        if path == "-":
            return f"`--body-file -` reads the body from stdin, where it cannot be checked. {BODY_HOW}"
        if re.search(r"[$`]", path) or not os.path.isabs(path):
            return f"`--body-file {path}` is not a literal absolute path. {BODY_HOW}"
        if not TEMP_NAME.search(os.path.basename(path)):
            return f"{path} is a fixed name, and parallel agents share the scratchpad. {BODY_HOW}"
        try:
            with open(path, encoding="utf-8") as f:
                body = f.read()
        except OSError:
            return f"Cannot read {path}. {BODY_HOW}"
        if not body.strip():
            return f"{path} is empty. Write the body into it first, in its own command."
        if ticked_issue_box_without_issue(body):
            return (
                f"{path} ticks the linked-issue checkbox, but the body links no issue. Untick it or link the issue."
            )
    return None


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
            return body_problem(command)
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
