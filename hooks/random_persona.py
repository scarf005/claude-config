#!/usr/bin/env python3
"""SessionStart hook: point persona/active.md at a random persona (never `off`) and inject its text.

The global instructions import active.md before this hook runs, so the injected text replaces the persona loaded from the previous session's link.
"""
import json
import random
from pathlib import Path

PERSONAS = Path.home() / ".config/persona"
SKIP = {"active", "off"}


def pick(persona_dir):
    choice = random.choice([p for p in sorted(persona_dir.glob("*.md")) if p.stem not in SKIP])
    link = persona_dir / "active.md"
    link.unlink(missing_ok=True)
    link.symlink_to(choice.name)
    return json.dumps({"hookSpecificOutput": {
        "hookEventName": "SessionStart",
        "additionalContext": f"This session's reply persona is {choice.stem}. It replaces any persona loaded earlier from active.md; follow it for all user-visible text.\n\n{choice.read_text()}",
    }}, ensure_ascii=False)


if __name__ == "__main__":
    print(pick(PERSONAS))
