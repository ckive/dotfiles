---
name: build
description: Implement a refined Plane work item and open a PR for Dan's review. Use for "/build <ITEM-ID>", including resuming after Dan requests changes.
---

# Build a work item

If this session already refined or built the item, its spec and code are in your context: don't redo that work. Re-read only what `get_item` shows has changed (Dan may have edited the spec in Plane), and skip files and reading you've already done.

1. `get_item <ID>`.
   - If the description has no `## Acceptance criteria`, follow the **refine** skill instead, then `update_item remove_labels=["agent-build"]` and stop.
   - If Context says `Overlaps <X>` and X is not Done, `update_item add_labels=["blocked"]`, comment which item it waits for, and stop.
2. `update_item state="In Progress"`. Work in this worktree, on its branch, never on `main`.
3. Read the repo's `AGENTS.md` and follow it.
   - Write the spec's behaviour tests first and watch them fail. Then implement until the repo's checks pass (`just check` if there is a justfile).
   - If the spec is wrong or something is unclear, ask (see **Asking Dan** in the refine skill). Don't widen the scope.
4. Commit as Conventional Commits (`type(scope): what changed`), succinct, one commit per logical step. Never add a Claude trailer or any other attribution. Push with `git push -u origin HEAD`.
5. Open the PR with `open_pr_for_item <ID>`, unless a PR is already open, in which case pushing is enough. Only if another open PR touches the same files, pass `title_prefix="[<group> n/m] "` to state the review order.
6. **When Dan requests changes:**
   - Read every review comment (`get_pr`) and address each one, or say why not.
   - Push, then `comment_item` a short summary.
   - Set `update_item state="Review"`.
7. **When Dan comments on Plane** ("Dan commented on Plane: …"): apply it to the work in progress. If it changes scope or behaviour, update the spec's affected sections first (see **Dan's comments** in the refine skill). If a PR is open, push and `comment_item` what changed.
8. When done, run `update_item remove_labels=["agent-build"]`, post a two-line summary with `comment_item`, then stop and wait.

Never merge. Never push to `main`. Never force-push a branch that has a PR open unless Dan asked for it.
