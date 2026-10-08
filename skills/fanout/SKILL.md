---
name: fanout
description: Plan a batch of changes, split it into N file-disjoint work packages, run each on its own git worktree with an `implementer` subagent (Sonnet) in parallel, then merge them back into the local base branch and validate. Use when the user asks to fan out, parallelize, or "agentify" work across several agents or worktrees, e.g. `/fanout 3`.
argument-hint: "[agent count] [optional task list]"
---

# Fanout

You investigate, plan, split, merge and report; `implementer` subagents edit.

## 1. Plan
- Tasks come from the arguments or the conversation. A leading number is the maximum agent count N (default: one
  per independent package, up to 3).
- Investigate each item until files, functions, current values and the observed bug are concrete. Per item write:
  goal, verified diagnosis, required behavior, what must not change, acceptance tests (numbers where measurable),
  commit subject(s).

## 2. Split
- Packages own disjoint files, or disjoint functions of a shared file; name ownership in each prompt. Items editing
  the same function share a package or run sequentially.
- Hold a package whose code is touched by running work or uncommitted changes until that lands; tell the user.

## 3. Worktrees from the local base
- `git gtr new agent/<slug> --from <base> --no-fetch --yes` (without gtr:
  `git worktree add -b agent/<slug> <path> <base>`). `<base>` is the local branch; default refs may be stale remote
  refs, so verify each worktree's commit with `git worktree list`.
- Do not use the Agent tool's `isolation: "worktree"`; it may branch from a stale ref.

## 4. Launch
- One background `implementer` per package, in parallel. Each prompt: absolute worktree path and branch, "work only
  there", ownership, the full item plans, setup and targeted test commands, baseline, commit subjects, report format,
  and "the parent runs the full suite after merging" (parallel full suites contend for CPU and slow every agent).
- Show the user a short table of packages, worktrees and anything waiting.
- Forward later scope changes to a running agent with SendMessage.

## 5. Merge
- On each completion, check the report: commits exist (`git -C <worktree> log --oneline <base>..HEAD`), deviations,
  risky diffs.
- On `<base>` in the main checkout: `git cherry-pick <base>..agent/<slug>` (or `git merge --no-ff` if preferred).
  Resolve conflicts keeping both intents; never drop another package's change.
- After the last package, run the full suite once as a tracked background task and report the exact final line.
  Send failures back to the owning agent or fix them.
- Remove merged worktrees and branches (`git gtr rm agent/<slug>`); leave unmerged ones and say so.
- Engine/generator by-products (import caches, `.uid` files): commit only kinds the repository tracks.

## 6. Report
Per package: changes with measured numbers, commit hashes on `<base>`, conflicts and resolutions, validation
evidence, and what still needs the user's eyes (visuals, audio, feel). Claim nothing unverified.
