#!/usr/bin/env python3
"""Stop hook: block a turn whose visible assistant text is not Korean.

Checks every line of the text blocks of the final reply (the assistant entries after the last tool result; earlier mid-turn notes are already sent and a rewrite cannot undo them), plus the
input's last_assistant_message, since the hook can run before the transcript has the last entry. A line (code spans, blocks and path/URL tokens
removed; markdown table rows skipped, since their cells are names and labels) with 4+ Latin words and fewer than half as many Hangul syllables as Latin letters blocks the stop and asks for
a Korean rewrite that does not mention the violation; English with a Korean ending appended is caught too.
"""
import json
import re
import sys

HANGUL = re.compile(r"[가-힣]")
LATIN = re.compile(r"[A-Za-z]")
WORD = re.compile(r"[A-Za-z]{2,}")
CODE = re.compile(r"```.*?```|`[^`\n]*`|[^\s`]*/[^\s`]*", re.S)


def is_english(text):
    return any(
        len(WORD.findall(line)) >= 4 and len(HANGUL.findall(line)) * 2 < len(LATIN.findall(line))
        for line in CODE.sub("", text).splitlines()
        if not line.lstrip().startswith("|")
    )


def main():
    data = json.load(sys.stdin)
    if data.get("stop_hook_active"):
        return
    path = data.get("transcript_path")
    if not path:
        return
    with open(path, encoding="utf-8") as f:
        entries = [json.loads(line) for line in f if line.strip()]
    start = max((i for i, e in enumerate(entries) if e.get("type") == "user"), default=-1)
    texts = [
        c.get("text", "")
        for e in entries[start + 1:]
        if e.get("type") == "assistant"
        for c in e.get("message", {}).get("content") or []
        if isinstance(c, dict) and c.get("type") == "text"
    ] + [data.get("last_assistant_message") or ""]
    bad = [t for t in texts if is_english(t)]
    if bad:
        print(json.dumps({
            "decision": "block",
            "reason": "Reply to the user again in Korean, in the persona voice from the global instructions. "
                      "Give only the substantive answer; do not mention this hook, a language violation, or an "
                      "apology, and do not quote the earlier text (code, paths and commands may stay as is).",
        }, ensure_ascii=False))


if __name__ == "__main__":
    main()
