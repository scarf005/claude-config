#!/usr/bin/env python3
"""Sticker hooks for the active persona (index: persona/stickers/<persona>.tsv, first line `dir<TAB>path`, then `file<TAB>moods<TAB>text`).

`inject` (UserPromptSubmit) lists one random sticker per mood as context; `check` (Stop) blocks once when the reply does not end with a sticker path.
"""
import json
import random
import sys
from pathlib import Path

PERSONAS = Path.home() / ".config/persona"
TAIL_LINES = 3


def load(persona_dir):
    index = persona_dir / "stickers" / f"{(persona_dir / 'active.md').resolve().stem}.tsv"
    if not index.exists():
        return None
    head, *rows = [line.split("\t") for line in index.read_text().splitlines() if line]
    return head[1], [(f, m.split(), t) for f, m, t in rows]


def candidates(directory, rows):
    moods = sorted({m for _, ms, _ in rows for m in ms})
    picks = {m: random.choice([r for r in rows if m in r[1]]) for m in moods}
    return "\n".join(f"- {m}: {directory}/{f} ({t})" for m, (f, _, t) in picks.items())


def inject(persona_dir):
    loaded = load(persona_dir)
    if not loaded:
        return ""
    return json.dumps({"hookSpecificOutput": {
        "hookEventName": "UserPromptSubmit",
        "additionalContext": "End the reply with 1-3 stickers on their own lines (absolute path, no code block), matched to the reply's mood. Pick from these candidates, one per mood:\n" + candidates(*loaded),
    }}, ensure_ascii=False)


def check(persona_dir, data):
    loaded = load(persona_dir)
    if not loaded or data.get("stop_hook_active"):
        return ""
    tail = [l for l in (data.get("last_assistant_message") or "").splitlines() if l.strip()][-TAIL_LINES:]
    if not tail or any(loaded[0] in l for l in tail):
        return ""
    return json.dumps({
        "decision": "block",
        "reason": "Reply with only 1-3 sticker paths, one per line, picked by mood from the list below. Write no other text, no acknowledgement and no mention of this check:\n" + candidates(*loaded),
    }, ensure_ascii=False)


if __name__ == "__main__":
    mode = sys.argv[1]
    out = inject(PERSONAS) if mode == "inject" else check(PERSONAS, json.load(sys.stdin))
    if out:
        print(out)
