---
name: fanout
description: Plan a batch of changes, split it into N file-disjoint work packages, run each on its own git worktree with an `implementer` subagent (Sonnet) in parallel, then merge them back into the local base branch and validate. Use when the user asks to fan out, parallelize, or "agentify" work across several agents or worktrees, e.g. `/fanout 3`.
argument-hint: "[agent count] [optional task list]"
---

# Fanout: plan here, implement in parallel worktrees, merge back

You (the main session) do the investigation, planning, splitting, merging and final report. The
`implementer` subagents do the edits. Speak to the user in their language.

## 1. Understand and plan
- Take the task list from the arguments or the recent conversation. The first argument, when a
  number, is the maximum agent count N (default: as many as there are independent packages, up to 3).
- Investigate each item yourself until the cause and the fix are concrete: files, functions,
  current values, the observed bug. Vague plans produce vague work.
- For each item write: goal, verified diagnosis, required behavior, constraints (what must not
  change), acceptance tests (with numbers where measurable), and commit subject(s).

## 2. Split into packages
- Group items so that packages touch disjoint files, or at least disjoint functions of a shared
  file. Name the ownership explicitly in each prompt ("in X touch only Y; another agent owns Z").
- Items that must edit the same function go in the same package, or run sequentially.
- If work already running (an earlier agent or uncommitted changes) touches the same code, hold
  that package until it lands and base it on the newer commit. Tell the user what waits and why.

## 3. Create worktrees from the LOCAL base
- Check the repository's worktree tool first. With git-gtr:
  `git gtr new agent/<slug> --from <base> --no-fetch --yes`, where `<base>` is the local branch
  (usually `main`). Without git-gtr: `git worktree add -b agent/<slug> <path> <base>`.
- Never rely on a default base: it may be a stale remote-tracking ref. Verify with
  `git worktree list` that every worktree sits on the current local base commit.
- Do not use the Agent tool's own `isolation: "worktree"` for this; it may branch from a stale ref.

## 4. Launch implementers
- Spawn one `implementer` agent per package (`subagent_type: "implementer"`), in parallel, in the
  background. Each prompt contains: the absolute worktree path and branch, "work only there",
  file/function ownership, the full plan for its items, the setup and test commands, the baseline
  expectation, commit subjects, and the report format.
- Tell the user in a short table which package runs where and what is waiting.

## 5. Merge back
- As each agent finishes, read its report critically: confirm commits exist
  (`git -C <worktree> log --oneline <base>..HEAD`), check deviations, and spot-check risky diffs.
- In the main checkout on `<base>`, bring the commits in with
  `git cherry-pick <base>..agent/<slug>` (or `git merge --no-ff agent/<slug>` if the user prefers
  merge commits). Resolve conflicts by keeping both sides' intent; never drop another package's
  change to make a conflict go away.
- After the last package, run the full test suite on `<base>` yourself and report the exact final
  line. If it fails, fix or send the failure back to the owning agent.
- Remove merged worktrees and branches (`git gtr rm agent/<slug>` or `git worktree remove` +
  `git branch -d`). Leave anything unmerged in place and say so.

## 6. Report
Per package: what changed (with the agents' measured numbers), commit hashes on `<base>`,
conflicts and how they were resolved, validation evidence, and what still needs the user's eyes
(visuals, audio, feel). Do not claim what was not verified.

## Pitfalls learned
- Worktrees created from a default/remote ref started on an old commit and conflicted on merge.
- Two agents running the full suite in the same checkout see each other's half-written edits;
  parallel work needs separate worktrees.
- Engines and generators create by-products (import caches, metadata files); decide per file
  whether the repository tracks that kind of file.
- A later user message can change a running package's scope; forward it with SendMessage instead
  of waiting for the agent to finish.
