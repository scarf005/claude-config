#!/usr/bin/env python3
"""PreToolUse hook: deny benchmark runs on the local machine.

Other jobs share this machine, so local timings are skewed. Benchmarks run on GitHub CI. A local run
(GPU path that CI cannot measure) needs the user's approval first; then mark it with LOCAL_BENCH_OK=1.
Checks the command and any script file it names.
"""
import json
import re
import shlex
import sys

from private_profile import script_texts

BENCH = re.compile(
    r"\bhyperfine\b|\bperf\s+(?:stat|record)\b|\bprofile_(?:wait|walk)\b|\bPROFILE_WAIT\w*=|"
    r"--benchmark-samples|\[\.?benchmark\]|^\s*(?:export\s+|env\s+)?CCACHE_DISABLE=1\b|"
    r"(?:/usr/bin/time|^\s*time)\b.*\b(?:ninja|cmake\s+--build|make)\b"
)
READ = re.compile(r"^\s*(?:rg|cat|sed|git|gh|ls|fd|head|tail|wc|echo)\b")
APPROVED = re.compile(r"\bLOCAL_BENCH_OK=1\b")


def commands(line):
    """Split a shell line at ; && || | into commands, so `rg profile_walk` is checked as one search."""
    lexer = shlex.shlex(line, posix=True, punctuation_chars=";&|")
    lexer.whitespace_split = True
    try:
        tokens = list(lexer)
    except ValueError:
        return [line]
    parts = [[]]
    for token in tokens:
        if token and set(token) <= set(";&|"):
            parts.append([])
        else:
            parts[-1].append(token)
    return [" ".join(part) for part in parts if part]


def violation(command):
    texts = [command, *script_texts(command)]
    if any(APPROVED.search(text) for text in texts):
        return None
    for text in texts:
        for line in text.splitlines():
            if any(BENCH.search(part) and not READ.search(part) for part in commands(line)):
                return line
    return None


def main():
    data = json.load(sys.stdin)
    if data.get("tool_name") != "Bash":
        return
    line = violation(data.get("tool_input", {}).get("command", ""))
    if line is None:
        return
    reason = (
        "Benchmarks run on GitHub CI, not on this shared machine. For a GPU-path measurement that CI "
        "cannot do, ask the user first, then add LOCAL_BENCH_OK=1 to the command "
        f"(offending line: {line.strip()[:200]})."
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
