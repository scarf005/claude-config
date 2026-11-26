#!/usr/bin/env python3
"""PreToolUse hook: deny `cmake --preset` configures that let the preset pick a bare compiler.

The Cataclysm-BN presets name bare `clang`; PATH differences resolve it to another path than the
cached one, and CMake then wipes the cache to curses defaults (TILES OFF, no test target). A
configure must pass absolute compilers. Checks the command and any script file it names.
"""
import json
import re
import sys

from private_profile import READERS, program, script_texts, shell_commands

CONFIGURE = re.compile(r"cmake\s+(?:-S\s+\S+\s+)?--preset\b")
ABSOLUTE = re.compile(r"-DCMAKE_CXX_COMPILER=/")
# A Debug configure caches the source root as the runtime output dir; it outlives later build types.
UNSET_OUTPUT = re.compile(r"-U\s*CMAKE_RUNTIME_OUTPUT_DIRECTORY")


def violation(command):
    """First configure without absolute compilers; searches and heredoc file data pass."""
    return next(
        (part for text in [command, *script_texts(command)] for part in shell_commands(text)
         if program(part) not in READERS and CONFIGURE.search(part)
         and not (ABSOLUTE.search(part) and UNSET_OUTPUT.search(part))),
        None,
    )


def main():
    data = json.load(sys.stdin)
    if data.get("tool_name") != "Bash" or violation(data.get("tool_input", {}).get("command", "")) is None:
        return
    reason = (
        "A preset configure with a bare compiler can wipe the CMake cache to curses defaults. Use "
        "`PATH=/usr/bin:$PATH cmake --preset <p> -DCMAKE_C_COMPILER=/usr/bin/clang "
        "-DCMAKE_CXX_COMPILER=/usr/bin/clang++ -U CMAKE_RUNTIME_OUTPUT_DIRECTORY -DTILES=ON -DCURSES=OFF ...` and build with plain `cmake --build`."
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
