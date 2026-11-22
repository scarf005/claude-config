#!/usr/bin/env python3
"""PreToolUse hook: deny commit, PR and issue text with Markdown tables that are hard to read.

`git log` shows commit bodies raw, so table columns must be padded (`deno fmt --ext md -` does it).
A table with Before and After columns must also show the speedup (`3.08x (-68%)`).
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
SPEEDUP = re.compile(r"speedup|faster|ratio|change")


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


def table_problem(text):
    """Why the first hard-to-read table block in `text` is hard to read, or None."""
    block = []
    for line in text.splitlines() + [""]:
        if ROW.match(line):
            block.append(line)
            continue
        if len(block) >= 2:
            first = pipe_columns(block[0])
            for row in block[1:]:
                if pipe_columns(row) != first:
                    return f"Table columns do not line up; pad them with `deno fmt --ext md -`. Row: {row.strip()[:200]}"
            header = {c.strip().lower() for c in block[0].strip().strip("|").split("|")}
            if {"before", "after"} <= header and not any(SPEEDUP.search(c) for c in header):
                return f"Before/After table has no speedup column; add one such as `3.08x (-68%)`. Header: {block[0].strip()[:200]}"
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
            return f"Cannot read message file {path!r}; pass a literal absolute path so its tables can be checked."
    for text in texts:
        problem = table_problem(text)
        if problem is not None:
            return problem
    return None


def main():
    data = json.load(sys.stdin)
    if data.get("tool_name") != "Bash":
        return
    reason = violation(data.get("tool_input", {}).get("command", ""))
    if reason is None:
        return
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }))


if __name__ == "__main__":
    main()
