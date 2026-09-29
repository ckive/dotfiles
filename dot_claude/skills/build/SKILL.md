---
name: build
description: Implement a refined Plane work item and open a PR for Dan's review. Use for "/build <ITEM-ID>", including resuming after Dan requests changes.
---

# Build a work item

If this session already refined or built the item, its spec and code are in your context: don't redo that work. Re-read only what `get_item` shows has changed (Dan may have edited the spec in Plane), and skip files and reading you've already done.

1. `get_item <ID>`.
   - If the description has no `## Acceptance criteria`, Dan's notes are the brief: write the spec yourself and keep going. Follow the **refine** skill's steps 2 and 4–6 (investigate, ask only a product decision the notes leave open, check collisions, write the spec keeping **Original notes**); skip its triage and closing steps. `comment_item "Spec written from your notes; building now."` and continue. Don't remove `agent-build` or wait for approval.
   - If Context says `Overlaps <X>` and X is not Done, `update_item add_labels=["blocked"]`, comment which item it waits for, and stop.
2. `update_item state="In Progress"`. Work in this worktree, on its branch, never on `main`.
3. Read the repo's `AGENTS.md` and follow it.
   - Write the spec's behaviour tests first and watch them fail. Then implement until the repo's checks pass (`just check` if there is a justfile).
   - If the spec has `## Slices`, build them in order, each one test-first and passing checks before the next, with at least one commit per slice. All slices go in one PR.
   - If the spec is wrong or something is unclear, ask (see **Asking Dan** in the refine skill). Don't widen the scope.
4. Update the docs in the same branch: the README (and its diagram) and every doc the change makes stale. If none apply, the PR body must say `Docs: none needed` (CI `check / docs` fails otherwise).
5. Commit as Conventional Commits (`type(scope): what changed`), succinct, one commit per logical step. Never add a Claude trailer or any other attribution. Push with `git push -u origin HEAD`.
6. Open the PR with `open_pr_for_item <ID>`, unless a PR is already open, in which case pushing is enough. Only if another open PR touches the same files, pass `title_prefix="[<group> n/m] "` to state the review order.
7. **When Dan requests changes:**
   - Read every review comment (`get_pr`) and address each one, or say why not.
   - Push, then `comment_item` a short summary.
   - Set `update_item state="Review"`.
8. **When Dan comments on Plane** ("Dan commented on Plane: …"): apply it to the work in progress. If it changes scope or behaviour, update the spec's affected sections first (see **Dan's comments** in the refine skill). If a PR is open, push and `comment_item` what changed.
9. When done, run `update_item remove_labels=["agent-build"]`, post a two-line summary with `comment_item`, then stop and wait.

## Yolo mode

If the item has `yolo` or `yolo-merge`, you own it end to end, and we believe you can get it there. Work through whatever gets in the way.
- Don't stop for questions: pick your recommended option, `comment_item "**Assumed:** …"`, and keep going (never `needs-dan`).
- Post a short progress note with `comment_item` at each phase: tests red, green, PR opened, each revision. When something fights you, post `**Roadblock:** <what> — trying <next>` and keep at it. Dan reads these in the item's Slack thread and may steer.
- `Overlaps <X>` doesn't block you: if X has an open PR, stack on its branch; otherwise build on `main` and say so in a comment.
- After the PR opens, a reviewer agent reviews every push. If it wants changes you get a revise prompt pointing at its `**Review:**` comment: address each finding (**When Dan requests changes** applies, reading that comment instead of `get_pr`), push, and set `state="Review"`. Keep iterating until it approves, with no round limit.
- With `yolo-merge`, pfi merges once the reviewer approves. Never merge yourself.

Never merge. Never push to `main`. Never force-push a branch that has a PR open unless Dan asked for it.
