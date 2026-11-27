#!/usr/bin/env python3
"""Stop hook: block a stop while a pushed CI benchmark or capture run has no background watcher.

On 2026-11-27 the session pushed 4 `bench/` branches, ended its turn, and sat idle for 2 h 50 min:
nothing re-invokes a session when a CI run ends unless a background `gh run watch` or
`gh pr checks --watch` call is running. Blocks when the last `git push` to a `bench/` ref comes after
the last background watch call.
"""
import json
import re
import sys

BENCH_PUSH = re.compile(r"\bgit\b[^|;&]*\bpush\b(?![^|;&]*(?:--delete|\s-d\b))[^|;&]*\bbench/")
WATCH = re.compile(r"\bgh\b[^|;&]*\b(?:run\s+watch|pr\s+checks\b[^|;&]*--watch)\b")


def unwatched_push(entries):
    """True when a `bench/` push has no background watch call after it."""
    last_push = last_watch = -1
    for i, e in enumerate(entries):
        for c in e.get("message", {}).get("content") or [] if e.get("type") == "assistant" else []:
            if not isinstance(c, dict) or c.get("type") != "tool_use" or c.get("name") != "Bash":
                continue
            command = c.get("input", {}).get("command", "")
            if BENCH_PUSH.search(command):
                last_push = i
            if WATCH.search(command) and c.get("input", {}).get("run_in_background"):
                last_watch = i
    return last_push > last_watch


def main():
    data = json.load(sys.stdin)
    if data.get("stop_hook_active") or not data.get("transcript_path"):
        return
    with open(data["transcript_path"], encoding="utf-8") as f:
        entries = [json.loads(line) for line in f if line.strip()]
    if unwatched_push(entries):
        print(json.dumps({"decision": "block", "reason": (
            "A pushed `bench/` CI run has no watcher, so nothing wakes this session when it ends. Start one "
            "background `gh run watch <run id> -R <repo> --exit-status` (run_in_background) before stopping.")}))


if __name__ == "__main__":
    main()
