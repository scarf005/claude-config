#!/usr/bin/env python3
"""Sticker hooks for the active persona (index: persona/stickers/<persona>.tsv, first line `dir<TAB>path`, then `file<TAB>moods<TAB>text`).

`inject` (UserPromptSubmit) lists one random sticker per mood of the session's persona as context; `check` (Stop) blocks once, pointing at the index file, when the reply does not end with a sticker path.
"""
import json
import random
import sys
from pathlib import Path

PERSONAS = Path.home() / ".config/persona"
SESSIONS = Path.home() / ".local/state/persona-sessions"
TAIL_LINES = 3


def parse(index):
    head, *rows = [line.split("\t") for line in index.read_text().splitlines() if line]
    return head[1], [(f, m.split(), t) for f, m, t in rows]


def load(persona_dir, sessions, session_id):
    """Pack of the persona this session started with (`sessions/<session_id>`, written by random_persona.py); the active link is shared by all running sessions, so it is only the fallback."""
    recorded = sessions / (session_id or "-")
    name = recorded.read_text().strip() if recorded.exists() else (persona_dir / "active.md").resolve().stem
    index = persona_dir / "stickers" / f"{name}.tsv"
    return {name: parse(index)} if index.exists() else None


def candidates(packs):
    out = []
    for persona, (directory, rows) in packs.items():
        moods = sorted({m for _, ms, _ in rows for m in ms})
        picks = {m: random.choice([r for r in rows if m in r[1]]) for m in moods}
        out += [f"{persona}:"] + [f"- {m}: {directory}/{f} ({t})" for m, (f, _, t) in picks.items()]
    return "\n".join(out)


def inject(persona_dir, sessions, data):
    loaded = load(persona_dir, sessions, data.get("session_id"))
    if not loaded:
        return ""
    return json.dumps({"hookSpecificOutput": {
        "hookEventName": "UserPromptSubmit",
        "additionalContext": "End the reply with 1-3 stickers on their own lines (absolute path, no code block), matched to the reply's mood. Pick from the candidates of the persona whose voice you use, one per mood:\n" + candidates(loaded),
    }}, ensure_ascii=False)


def check(persona_dir, sessions, data):
    loaded = load(persona_dir, sessions, data.get("session_id"))
    if not loaded or data.get("stop_hook_active"):
        return ""
    tail = [l for l in (data.get("last_assistant_message") or "").splitlines() if l.strip()][-TAIL_LINES:]
    if not tail or any(d in l for d, _ in loaded.values() for l in tail):
        return ""
    return json.dumps({
        "decision": "block",
        "reason": "Read the sticker index " + ", ".join(f"{persona_dir}/stickers/{n}.tsv" for n in loaded) + " (first line `dir<TAB>path`, then `file<TAB>moods<TAB>text`; sticker path = path/file), then reply with only 1-3 sticker paths, one per line, picked by mood. Write no other text, no acknowledgement and no mention of this check.",
    }, ensure_ascii=False)


if __name__ == "__main__":
    mode = sys.argv[1]
    out = (inject if mode == "inject" else check)(PERSONAS, SESSIONS, json.load(sys.stdin))
    if out:
        print(out)
