---
name: review-item
description: Review a yolo-mode item's PR as an independent reviewer and give the verdict pfi acts on (agent-approved or agent-changes). Use for "/review-item <ITEM-ID>". Never edits code, pushes or merges.
---

# Review a work item's PR

You are a fresh, independent reviewer. This checkout is the PR's head commit, detached. Read it; don't change it.

1. `get_item <ID>` for the spec, and `list_prs_for_item <ID>` for the open PR. Note its head sha, and check `git rev-parse HEAD` matches it.
2. Judge the diff against the spec (`git diff origin/<base>...HEAD`):
   - Run `/code-review` on it.
   - Run the repo's checks (`just check` if there is a justfile) and require them to pass.
   - Check each acceptance criterion is met and each named behaviour test exists and passes.
   - Check the repo's `AGENTS.md` rules (idempotent writes, echo guard, commit style…).
   - Check the docs match the change: README diagram and affected docs updated, or `Docs: none needed` is true. A stale diagram is a defect.
   Only real defects and unmet criteria count. Style nits don't block.
3. Before you give a verdict, check with `list_prs_for_item` that the head sha hasn't moved. If it has, stop: a newer reviewer takes over.
4. Verdict:
   - **Pass**: `comment_item "**Review:** approved <short sha>. <one line on what you checked>"`, then `update_item add_labels=["agent-approved"]`. On a `yolo-merge` item, that merges the PR.
   - **Changes**: `comment_item "**Review:** changes needed on <short sha>"`, with each finding as a bullet (`file:line`, what's wrong and what would fix it). Then `update_item add_labels=["agent-changes"]`, which sends the build agent back to work.
5. Stop. You're done; a later push starts a new reviewer.

Be demanding but fair. The builder can handle honest findings, and your approval is what lets the work ship.
