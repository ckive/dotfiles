---
name: refine
description: Turn a Plane work item into the standard spec before any build. Use for "/refine <ITEM-ID>", and when /build finds an item without a spec. Never writes code or opens a PR.
---

# Refine a work item

Aim: a spec that fits on one screen, so a build agent can do the work without guessing. Keep it succinct and make the objective unmistakable.

1. `get_item <ID>` (pfi MCP). Read the description, comments and links.
2. Investigate in this worktree without committing:
   - Find the code involved.
   - For a bug, reproduce it. A failing test is the best repro. Record the cause as `file:line`.
3. Product decisions are Dan's. Don't guess them; ask (see **Asking Dan**).
4. Check for collisions. Call `list_items` for items in Refining, In Progress and Review, and read their **Touched areas**. If one overlaps yours, add `Overlaps <ID>` under Context.
5. Replace the description with `update_item description=…` in exactly this format:

```markdown
## Goal
The outcome, and who it is for (1–2 sentences).

## Context
What exists today; for bugs the cause (`file:line`). Overlaps <ID>, if any.

## Repro
(bugs only) Steps → actual vs expected.

## Acceptance criteria
- When <trigger>, the app shall <response>.

## Behaviour tests
- test_<behaviour_in_words>

## Touched areas
- path/or/module: why

## Out of scope
- …

## Open questions
- none

## Original notes
<the previous description, verbatim>
```

   - Write each acceptance criterion in EARS form, so it can be tested.
   - Name the behaviour tests the repo's BDD way: the scenario goes in the name, with no Gherkin.
6. `comment_item`: three lines covering what you found, the spec's gist and any open questions.
7. `update_item remove_labels=["agent-refine"]`. Leave the item in Refining. Then stop and wait: Dan reads the spec and adds `agent-build`.

## Asking Dan

- Post the question with `comment_item` as `**Question for Dan:** …`, then `update_item add_labels=["needs-dan"]`.
- Ask the same question here as well, as plain text, because Dan may answer through Remote Control. Then end your turn and wait. Never use AskUserQuestion: answers from Plane arrive as a pasted message, which its menu can't take.
- If the answer arrives here and not as "Dan commented on Plane: …", copy it to Plane with `comment_item "**Dan's answer:** …"` and `update_item remove_labels=["needs-dan"]`. Plane is the record.

## Dan's comments

"Dan commented on Plane: …" that isn't an answer adjusts the item. Don't start over:
- Spec written: change only the affected sections with `update_item description=…`; keep the rest and **Original notes** as they are.
- Spec not written yet: fold it into the spec you are writing.
- `comment_item` one line on what changed. If the comment is unclear, ask (see **Asking Dan**).
