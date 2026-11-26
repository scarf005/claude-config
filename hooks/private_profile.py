#!/usr/bin/env python3
"""PreToolUse hook: deny app launches that would read and write the user's real profile.

An automated launch under gamescope or xvfb-run, or a Cataclysm launch with `--userdir`/`--world`,
must isolate its config: `--configdir`, `XDG_CONFIG_HOME=` or `HOME=`. `--userdir` alone still
writes `~/.config/cataclysm-bn/options.json`. Checks the Bash command and the text of every script
file it names, since launches often live in a script (`cargo -Zscript live.rs`).
"""
import json
import re
import shlex
import sys
from pathlib import Path

LAUNCH = re.compile(r"\bgamescope\b(?!ctl)|\bxvfb-run\b|--userdir\b|--world\b")
ISOLATED = re.compile(r"--configdir\b|\bXDG_CONFIG_HOME=|(?<![\w$])HOME=")
SCRIPT_SUFFIXES = {".rs", ".sh", ".py", ".fish", ".ts", ".js"}
SHELLS = {"bash", "sh", "dash", "zsh", "fish"}
READERS = {"rg", "cat", "sed", "git", "gh", "ls", "fd", "head", "tail", "wc", "echo", "printf"}
WRAPPERS = {"env", "exec", "time", "nice", "command", "sudo", "then", "do", "else", "{", "(", "!"}
ASSIGNMENT = re.compile(r"^[A-Za-z_]\w*=")
HEREDOC = re.compile(r"(?<!<)<<(?!<)-?\s*(['\"]?)([A-Za-z_]\w*)\1")


def split_commands(line):
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


def program(command):
    """Name of the program a command runs, past `VAR=value` and wrapper words: `PATH=x cmake ..` gives cmake."""
    for word in command.split():
        if not (ASSIGNMENT.match(word) or word in WRAPPERS):
            return Path(word).name
    return ""


def shell_commands(text):
    """Yield every command of a shell text. A heredoc body counts only when a shell reads it."""
    lines = text.replace("\\\n", " ").splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        parts = split_commands(line)
        yield from parts
        i += 1
        heredoc = HEREDOC.search(line)
        if not heredoc:
            continue
        shell_input = any("<<" in part and program(part) in SHELLS for part in parts)
        while i < len(lines) and lines[i].strip() != heredoc.group(2):
            if shell_input:
                yield from split_commands(lines[i])
            i += 1
        i += 1


def script_texts(command):
    try:
        tokens = shlex.split(command, comments=True)
    except ValueError:
        tokens = command.split()
    for token in tokens:
        try:
            path = Path(token).expanduser()
        except RuntimeError:
            path = Path(token)
        if path.suffix in SCRIPT_SUFFIXES and path.is_file() and path.stat().st_size < 1_000_000:
            yield path.read_text(errors="replace")


def violation(command):
    return next(
        (text for text in [command, *script_texts(command)] if LAUNCH.search(text) and not ISOLATED.search(text)),
        None,
    )


def main():
    data = json.load(sys.stdin)
    if data.get("tool_name") != "Bash":
        return
    if violation(data.get("tool_input", {}).get("command", "")) is None:
        return
    reason = (
        "This launch uses the user's real profile. Give the app a private config: "
        "Cataclysm `--userdir X/ --configdir X/config/`, other apps `XDG_CONFIG_HOME=X/config` "
        "(or `HOME=X`), in the command and in any script it runs."
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
