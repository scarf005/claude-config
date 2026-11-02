---
description: Switch the reply persona (no argument lists them)
argument-hint: [eri|villainess|nagisa|off]
allowed-tools: Bash(just -f /home/scarf/.config/justfile persona *), Bash(ls /home/scarf/.config/persona), Bash(readlink /home/scarf/.config/persona/active.md), Read(/home/scarf/.config/persona/*)
---
Persona argument: `$ARGUMENTS`

- Empty: run `readlink /home/scarf/.config/persona/active.md` and `ls /home/scarf/.config/persona`, then reply with the current persona and the names (without `active` and `.md`). Stop there.
- A name: run `just -f /home/scarf/.config/justfile persona <name>`. On success, read `/home/scarf/.config/persona/active.md` and use that voice from this reply on, in place of the earlier persona. On failure, report the error.
