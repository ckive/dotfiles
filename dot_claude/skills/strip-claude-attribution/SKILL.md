---
name: strip-claude-attribution
description: Remove Claude/Anthropic attribution (Co-Authored-By trailers, "Generated with Claude Code" lines) from a repo's existing commit messages. Use when asked to scrub Claude authorship from git history, or to audit a repo for it.
---

# Strip Claude attribution from history

New commits never get attribution: `~/.claude/settings.json` sets `attribution.commit` and
`attribution.pr` to `""`. This skill cleans up history written before that.

## Steps

1. **Dry run** — lists affected commits, how many hashes will change, and whether any are
   already on a remote:
   `~/.claude/skills/strip-claude-attribution/strip.sh <repo>`
2. **Show Dan the dry-run output and get an explicit yes.** Rewriting changes the hash of
   every commit from the oldest affected one onward. Call out anything that references old
   hashes (memory files, docs, issue/PR links) and any pushed commits.
3. **Apply**: `strip.sh --apply <repo>`. It refuses on tracked changes or extra worktrees,
   writes a backup bundle to `~/.cache/strip-claude-attribution/`, rewrites all local
   branches and tags (message only — trees, authors and dates are untouched), and verifies
   zero matches remain.
4. If commits were pushed: `git push --force-with-lease` per branch, only with Dan's
   go-ahead. Protected branches (Forgejo `main`) refuse; that needs an admin to lift
   protection temporarily — Dan's call, not the agent's.

## Notes

- Rewritten commits lose any signature they had; re-signing is a separate step.
- Remote-tracking refs, stashes and other clones are not touched; other clones must re-clone
  or `git reset` onto the rewritten branch.
- Restore: `git clone <bundle>` or `git fetch <bundle> 'refs/heads/*:refs/heads/*' --force`.
