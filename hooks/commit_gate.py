#!/usr/bin/env python3
"""PreToolUse hook: deny `git commit` until the diff is measured and read after the last edit in this session.

The rule asks for a self-review and one LoC shrink pass over the whole diff before every commit.
A `git diff --shortstat` and a patch-showing `git diff`/`git show`, both after the last edit, start that pass.
Deny it also when this session edited files and never loaded the humanizer skill: every commit message is prose,
and a commit in another repository (`cd x && git commit`) shows no diff in the session cwd.
Only shell segments that start with the command count, so quoted prose never matches.
"""
import json
import re
import sys

GIT = (r"^\s*(?:\(\s*|(?:env|command|exec)\s+|\w+=\S*\s+|(?:ba|z|fi)?sh\s+-c\s+['\"])*git\s+"
       r"(?:(?:-[Cc]\s+(?:'[^']*'|\"[^\"]*\"|[^\s'\"])+|--[\w-]+(?:=\S+)?)\s+)*")
COMMIT = re.compile(GIT + r"commit(?![-\w])")
# The whole branch against its base (`main...`); HEAD-relative and staged-only diffs hide the earlier commits.
SHORTSTAT = re.compile(GIT + r"diff\b(?=.*--shortstat\b)(?=.*\s(?!HEAD\b|@)[^\s-]\S*\.\.\.)")
SUMMARY_ONLY = r"--(?:shortstat|stat|numstat|name-only|name-status|quiet|exit-code|check|no-patch|summary|raw|compact-summary)\b|\s-s\b|\S:\S"
PATCH = re.compile(GIT + r"(?:(?:diff|show)\b(?!.*(?:" + SUMMARY_ONLY + r"))|log\b.*\s(?:-p|--patch)\b)")
SHELL_EDIT = re.compile(r"^\s*(?:sed\s+-i|perl\s+-\w*i|patch|tee|cp|mv)\b|(?<![-=>&])>>?\s*(?!/dev/|/tmp/|&)\S|" + GIT
                        + r"(?:apply|am|checkout|restore|merge|cherry-pick|rebase|revert|stash\s+(?:pop|apply)|mv|rm)\b")
SEPARATOR = re.compile(r"&&|\|\||;|\||\n")
EDITS = ("Edit", "MultiEdit", "Write", "NotebookEdit")
HEREDOC = re.compile(r"<<-?\s*['\"]?(\w+)['\"]?(.*?\n).*?^\s*\1\s*$", re.S | re.M)


def has(pattern, command):
    return isinstance(command, str) and any(
        pattern.search(part) for part in SEPARATOR.split(HEREDOC.sub(r"<<\2", command)))


def tool_uses(lines):
    for line in lines:
        try:
            entry = json.loads(line)
        except ValueError:
            continue
        message = entry.get("message") if isinstance(entry, dict) and entry.get("type") == "assistant" else None
        content = message.get("content") if isinstance(message, dict) else None
        for block in content if isinstance(content, list) else []:
            if isinstance(block, dict) and block.get("type") == "tool_use" and isinstance(block.get("input"), dict):
                yield block.get("name"), block["input"]


def needs_review(lines):
    """True when the last edit is not followed by both a shortstat and a patch, outside commit commands."""
    measured = read = True
    for name, args in tool_uses(lines):
        command = args.get("command") if name == "Bash" else None
        if name in EDITS or has(SHELL_EDIT, command):
            measured = read = False
        elif not has(COMMIT, command):
            measured = measured or has(SHORTSTAT, command)
            read = read or has(PATCH, command)
    return not (measured and read)


def needs_humanizer(lines):
    """True when the session edited files and never loaded the humanizer skill.

    A compaction keeps loaded skills in context, so one load covers the whole session.
    """
    uses = list(tool_uses(lines))
    loaded = any(name == "Skill" and args.get("skill") == "humanizer" for name, args in uses)
    return not loaded and any(
        name in EDITS or has(SHELL_EDIT, args.get("command") if name == "Bash" else None) for name, args in uses)


def deny(reason):
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse", "permissionDecision": "deny", "permissionDecisionReason": reason}}))


def main():
    try:
        data = json.load(sys.stdin)
        if not has(COMMIT, data["tool_input"]["command"]):
            return
        with open(data["transcript_path"]) as f:
            lines = f.readlines()
        dirty = needs_review(lines)
        unhumanized = needs_humanizer(lines)
    except (ValueError, KeyError, TypeError, OSError):
        return
    if dirty:
        deny("Files changed after the last diff review. Run `git diff --shortstat <base>...` and read the "
             "whole patch (`git diff <base>...`) in calls before the commit call, review it for correctness, "
             "make one LoC shrink pass, then commit.")
    elif unhumanized:
        deny("This session edited files without the humanizer skill. Load the `humanizer` skill, rewrite every "
             "added comment, doc, user-facing string and the commit message by its rules, then commit.")


if __name__ == "__main__":
    main()
