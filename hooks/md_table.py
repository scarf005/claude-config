#!/usr/bin/env python3
"""PreToolUse hook: deny commit, PR and issue text whose Markdown tables do not line up as plain text.

`git log` shows commit bodies raw, so table columns must be padded (`deno fmt --ext md -` does it).
Checks the command text (`-m`, heredocs) and files passed with `-F`/`--file`/`--body-file`.
"""
import json
import re
import shlex
import sys
import unicodedata

TARGET = re.compile(r"\bgit\b[^|;&\n]*\bcommit\b|\bgh\s+(?:pr|issue)\s+(?:create|edit|comment)\b")
FILE_FLAGS = {"-F", "--file", "--body-file"}
ROW = re.compile(r"^\s*\|.*\|\s*$")


def width(text):
    return sum(2 if unicodedata.east_asian_width(c) in "WF" else 1 for c in text)


def pipe_columns(line):
    line = line.strip()
    cols, col, escaped = [], 0, False
    for c in line:
        if c == "|" and not escaped:
            cols.append(col)
        escaped = c == "\\" and not escaped
        col += width(c)
    return cols


def unaligned_table(text):
    """First row of a table block whose pipes are not at the same columns as the block's first row."""
    block = []
    for line in text.splitlines() + [""]:
        if ROW.match(line):
            block.append(line)
            continue
        if len(block) >= 2:
            first = pipe_columns(block[0])
            for row in block[1:]:
                if pipe_columns(row) != first:
                    return row.strip()
        block = []
    return None


def message_files(command):
    try:
        words = shlex.split(command)
    except ValueError:
        return []
    files = []
    for i, word in enumerate(words):
        if word in FILE_FLAGS and i + 1 < len(words) and words[i + 1] != "-":
            files.append(words[i + 1])
        for flag in ("--file=", "--body-file="):
            if word.startswith(flag):
                files.append(word[len(flag):])
    return files


def violation(command, read=lambda p: open(p, encoding="utf-8").read()):
    if not TARGET.search(command):
        return None
    texts = [command.replace("\\n", "\n")]
    for path in message_files(command):
        try:
            texts.append(read(path))
        except OSError:
            pass
    for text in texts:
        row = unaligned_table(text)
        if row is not None:
            return row
    return None


def main():
    data = json.load(sys.stdin)
    if data.get("tool_name") != "Bash":
        return
    row = violation(data.get("tool_input", {}).get("command", ""))
    if row is None:
        return
    reason = (
        "Markdown table columns do not line up, so `git log` shows them unreadable. Pad every column "
        f"(pipe the message through `deno fmt --ext md -`). Unaligned row: {row[:200]}"
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
