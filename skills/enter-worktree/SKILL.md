---
name: enter-worktree
description: Switch the Claude Code main session into a git worktree. Use when the main session starts working in a worktree, one just created with `git gtr new` or one the user names.
---

# Enter a worktree

- First switch the session into it with `EnterWorktree` and `path: <worktree path>` (load it via ToolSearch), so the
  working directory, memory and relative paths follow the worktree. Do not `cd` or edit it by absolute path from the
  main checkout.
- Leave with `ExitWorktree` `action: "keep"` only when the user asks, or for a step that must run in the main
  checkout (the session's worktree guard refuses it there). Then re-enter with `EnterWorktree` `path:` so resume
  still finds the session in the worktree.
- Remove worktrees with `git gtr rm`.
