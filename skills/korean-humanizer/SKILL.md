---
name: korean-humanizer
description: "Remove machine-sounding Korean (AI 슬롭, 번역투, 어색한 문구) from game text, UI labels, log lines, hover text, docs and replies. Use before saving or sending Korean prose, when writing or reviewing player-facing Korean strings, or when the user calls Korean text 어색하다, 슬롭, 번역투 or 이상하다."
license: MIT
metadata:
  upstream: https://github.com/DaleSeo/korean-skills/tree/ae12ba27982ebeff03b46dc738365aaa34260d9a/skills/humanizer
allowed-tools: Read Write Edit Grep Glob
---

# Korean humanizer

The `references/` pattern files come from DaleSeo/korean-skills (MIT, see `LICENSE`). `references/user-corrections.md` holds this user's real corrections and overrides them. Read it first, every time.

Check each line in this order. Stop at the first step that settles it.

1. **Should it exist?** Delete a line only for one of these causes: another line or the thing's tag already says it, it is a hint or a guess at a secret, it is flavour text, it spoils a discovery, or it states what is absent or was not done. Keep a prompt the player must act on and a fact the player cannot get elsewhere: rewrite those. `R 키를 누르면 다시 시작한다` stays as `R키를 눌러 재시작`.
2. **Which surface is it?**
   - A rule on a thing (hover, sidebar, 도감): a bare tag or `이름: 값`. `가연성.`, `면역: 불`, `피해: 2`. No `N하면 M한다`.
   - An event (log, popup): a whole past-tense sentence with its subject and particles. `장승이 피해를 2 입었다`.
   - A refusal or a limit: a whole sentence ending in `-ㄹ 수 있다` or `-ㄹ 수 없다`.
   - A reply or a document: go to step 5.
3. **Is every word one a Korean player knows?** Use the plain word a Korean game prints. Never coin a word. One thing has one name on every screen.
4. **Say it aloud.** Rewrite it if a Korean speaker would not say it. Fragments that pass the format rules can still be wrong: `잠: 안 잠`, `미호 위치를 앎`. Translate the meaning, never the English comment or brief word by word.
5. **For prose longer than one sentence,** check the upstream patterns in `references/`: `translation-ese-patterns.md`, `vocabulary-patterns.md`, `structure-patterns.md`, `pos-patterns.md`, `punctuation-patterns.md`, `spacing-patterns.md`. Load a file when its category appears.

Overrides of the upstream patterns:

- Pattern 33 (`할 수 있다` 남발) does not apply to a single line, a label or game text.
- Rewriting most of a short line is normal. Skip the upstream change-rate guard for text under three sentences, and keep it for prose.
- Keep every number, name and negation. If the source does not say what a line means, read the code or ask; do not guess a meaning.

Report the changed text alone, unless the user asks why.
