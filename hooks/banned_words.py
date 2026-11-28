#!/usr/bin/env python3
"""Hook: deny the words gate, gates, gated and gating in replies, file edits, and commit, PR or issue text.

The user calls the word AI slop. Name the action instead (compare, require, block, check before).
Identifiers such as `commit_gate.py` and `t_gate_metal` pass: `_` joins them into one word.
PreToolUse (Edit, MultiEdit, Write, Bash `git commit` and `gh pr|issue`): deny when the new text has more matches
than the text it replaces. Stop: block a final reply that has the word.
"""
import json
import re
import sys

from korean_reply import final_texts
from md_table import TARGET

BANNED = re.compile(r"(?i)\bgat(?:es?|ed|ing)\b")
HOW = "Name the action instead (compare, require, block, check before)."


def old_and_new(data):
    tool, args = data.get("tool_name"), data.get("tool_input") or {}
    if tool == "Edit":
        return args.get("old_string", ""), args.get("new_string", "")
    if tool == "MultiEdit":
        edits = args.get("edits") or []
        return "".join(e.get("old_string", "") for e in edits), "".join(e.get("new_string", "") for e in edits)
    if tool == "Write":
        try:
            with open(args.get("file_path", ""), encoding="utf-8") as f:
                return f.read(), args.get("content", "")
        except OSError:
            return "", args.get("content", "")
    if tool == "Bash" and TARGET.search(args.get("command", "")):
        return "", args["command"]
    return "", ""


def added(data):
    """Deny reason when the call adds a banned word, else None."""
    old, new = old_and_new(data)
    if len(BANNED.findall(new)) > len(BANNED.findall(old)):
        return f"The text adds {sorted(set(BANNED.findall(new)))}. {HOW}"
    return None


def final_reply_problem(texts):
    words = sorted({w for t in texts for w in BANNED.findall(t)})
    return f"Rewrite the reply without {words}. {HOW} Do not mention this hook." if words else None


def main():
    data = json.load(sys.stdin)
    if data.get("hook_event_name") == "Stop":
        if data.get("stop_hook_active") or not data.get("transcript_path"):
            return
        reason = final_reply_problem(final_texts(data))
        if reason:
            print(json.dumps({"decision": "block", "reason": reason}))
        return
    reason = added(data)
    if reason:
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "PreToolUse", "permissionDecision": "deny", "permissionDecisionReason": reason}}))


if __name__ == "__main__":
    main()
