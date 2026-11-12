---
name: fable-handoff
description: Fable (Mythos-class) sessions plan and hand off instead of implementing. Use in a Fable session once the plan is settled, or when the user asks a Fable session to write a handoff.
---

# Fable handoff

When the plan is settled, do not implement it; write a detailed handoff for an Opus or Sonnet session to
`.claude/context/working-notes.md` and stop. Implement in a Fable session only when the user asks.

The handoff holds:
- the goal in the user's words;
- branch and build state;
- how the current code works, with `file:line`;
- each step with its reason and LoC or perf expectation;
- open decisions with a default, and rejected options;
- validation and profiling commands, acceptance checks;
- the next command.
