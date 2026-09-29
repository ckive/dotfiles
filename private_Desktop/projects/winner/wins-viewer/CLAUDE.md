# wins-viewer

Keyboard-first local media browser (C++23, SDL3/ImGui, libmpv). See
README.md for build/run/config and ARCHITECTURE.md for the layered design.

## Comment style

See `AGENTS.md`. Short version: ≤2 lines per function and usually 0; anything
longer is a `/** */` block on an interface or subsystem entry point, with ` * `
continuation lines. The rule lives in AGENTS.md because this file is gitignored
and invisible inside worktrees.

## All work happens in a worktree

Every feature or fix, however small, and every pile of batched asks: use
`scripts/new-worktree.sh` / `scripts/rm-worktree.sh` and follow
`.claude/skills/worktree/SKILL.md` rather than improvising `git worktree`
commands — build dir and config/db/logs isolation is already handled by that
flow.

**One worktree per task, worked by the main agent, one commit per phase.**
Not a worktree per feature and not a subagent per group: a task of any size
is one branch whose history reads as the plan. When several unrelated asks
arrive in one message, the skill's "When the ask is a pile" section covers
turning them into ordered phases — answer the embedded questions inline
first, order the rest by which files they touch, one batched clarifier round,
then build.

Don't spawn subagents unless asked for one by name.

## UI changes

`just check` doesn't see layout or interaction. For any UI phase, launch
`./build/wins_viewer` and exercise it where you can; in the summary give Dan a
≤5-step manual script (keys → expected result) and list what you couldn't verify.
