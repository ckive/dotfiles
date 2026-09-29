---
name: refine
description: Turn a Plane work item into the standard spec and stop for Dan's approval, planning larger asks first. Use for "/refine <ITEM-ID>"; /build also follows its spec steps when an item has none. Never writes code or opens a PR.
---

# Refine a work item

Aim: a spec a build agent can follow without guessing: one screen for a small ask, a planned spec for a large one. Keep it succinct and make the objective unmistakable.

1. `get_item <ID>` (pfi MCP). Read the description, comments and links.
2. Investigate in this worktree without committing:
   - Find the code involved.
   - For a bug, reproduce it. A failing test is the best repro. Record the cause as `file:line`.
3. Triage the item, then `comment_item` your verdict and a one-line reason (`**Track: spec**, one module, one decision`) before anything else:
   - **spec**: one area, few product decisions, fits on one screen. Follow the steps as written.
   - **plan**: several modules or repos, a new component or service, several product decisions, or it won't fit on one screen. Follow **Plan track** as well.
   - If Dan comments `plan it` or `just spec`, switch to that track, `comment_item` one line saying so, and rewrite the spec for it.
4. Product decisions are Dan's. Don't guess them; ask (see **Asking Dan**).
5. Check for collisions. Call `list_items` for items in Refining, In Progress and Review, and read their **Touched areas**. If one overlaps yours, add `Overlaps <ID>` under Context.
6. Replace the description with `update_item description=…` in exactly this format:

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
7. `comment_item`: three lines covering what you found, the spec's gist and any open questions.
8. `update_item remove_labels=["agent-refine"]`. Leave the item in Refining. Then stop and wait: Dan reads the spec and adds `agent-build` (in **Yolo mode**, pfi does).

## Plan track

A large ask gets planned before it is specced, in normal mode. Don't use Claude Code's plan mode (EnterPlanMode/ExitPlanMode): its approval menu can't be answered from Plane or Slack.
- Don't edit code on this track. Investigate only, as plan mode would.
- The result is still one spec, which /build does in one PR. Add these sections just before `## Acceptance criteria`:

```markdown
## Approach
The design in a few bullets: components, data flow, the key choices and why.

## Slices
1. <slice>: what it delivers (AC 1, 2). Each slice builds on the ones before it.

## Risks
- <risk>: how the build checks for it or limits it.
```

- Number the acceptance criteria, so each slice can name the ones it satisfies. Every criterion belongs to one slice.
- Ask every product decision through **Asking Dan**, as early as you can, and keep going until **Open questions** is `none`. Dan approves the spec by adding `agent-build`, as on the spec track.

## Yolo mode

If the item has `yolo` or `yolo-merge`, Dan has handed it over: take it all the way yourself. We believe you can.
- Never wait on Dan. For each question you would ask, pick your recommended option, `comment_item "**Assumed:** …"` with a one-line reason, and carry on. Leave **Open questions** as `none`, and never add `needs-dan`.
- Dan's comments still arrive and still adjust the work, as in **Dan's comments**.
- Step 8 still just removes `agent-refine`. pfi then adds `agent-build` and the build starts in this session; don't add it yourself.

## Asking Dan

- Post the question with `comment_item` as `**Question for Dan:** …`, then `update_item add_labels=["needs-dan"]`.
- Ask the same question here as well, as plain text, because Dan may answer through Remote Control. Then end your turn and wait. Never use AskUserQuestion: answers from Plane arrive as a pasted message, which its menu can't take.
- If the answer arrives here and not as "Dan commented on Plane: …", copy it to Plane with `comment_item "**Dan's answer:** …"` and `update_item remove_labels=["needs-dan"]`. Plane is the record.

## Dan's comments

"Dan commented on Plane: …" that isn't an answer adjusts the item. Don't start over:
- Spec written: change only the affected sections with `update_item description=…`; keep the rest and **Original notes** as they are.
- Spec not written yet: fold it into the spec you are writing.
- `plan it` or `just spec`: switch tracks (step 3).
- `comment_item` one line on what changed. If the comment is unclear, ask (see **Asking Dan**).
