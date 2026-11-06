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


def parse(index):
    head, *rows = [line.split("\t") for line in index.read_text().splitlines() if line]
    return head[1], [(f, m.split(), t) for f, m, t in rows]


def load(persona_dir):
    """Packs of every persona with an index when the active persona has one, since the active link is shared by all running sessions."""
    if not (persona_dir / "stickers" / f"{(persona_dir / 'active.md').resolve().stem}.tsv").exists():
        return None
    return {i.stem: parse(i) for i in sorted((persona_dir / "stickers").glob("*.tsv"))}


def candidates(packs):
    out = []
    for persona, (directory, rows) in packs.items():
        moods = sorted({m for _, ms, _ in rows for m in ms})
        picks = {m: random.choice([r for r in rows if m in r[1]]) for m in moods}
        out += [f"{persona}:"] + [f"- {m}: {directory}/{f} ({t})" for m, (f, _, t) in picks.items()]
    return "\n".join(out)


def inject(persona_dir):
    loaded = load(persona_dir)
    if not loaded:
        return ""
    return json.dumps({"hookSpecificOutput": {
        "hookEventName": "UserPromptSubmit",
        "additionalContext": "End the reply with 1-3 stickers on their own lines (absolute path, no code block), matched to the reply's mood. Pick from the candidates of the persona whose voice you use, one per mood:\n" + candidates(loaded),
    }}, ensure_ascii=False)


def check(persona_dir, data):
    loaded = load(persona_dir)
    if not loaded or data.get("stop_hook_active"):
        return ""
    tail = [l for l in (data.get("last_assistant_message") or "").splitlines() if l.strip()][-TAIL_LINES:]
    if not tail or any(d in l for d, _ in loaded.values() for l in tail):
        return ""
    return json.dumps({
        "decision": "block",
        "reason": "Reply with only 1-3 sticker paths, one per line, picked by mood from the candidates of the persona whose voice you use. Write no other text, no acknowledgement and no mention of this check:\n" + candidates(loaded),
    }, ensure_ascii=False)


if __name__ == "__main__":
    mode = sys.argv[1]
    out = inject(PERSONAS) if mode == "inject" else check(PERSONAS, json.load(sys.stdin))
    if out:
        print(out)
