---
name: rmsesh
description: Delete a Claude Code session and optionally its backend artifacts
---

# Delete a Claude Code session (`/rmsesh`)

This skill deletes all local traces of a Claude Code session and provides options for backend cleanup.

## Usage

```
/rmsesh <session_id_or_name>
```

Or just `/rmsesh` to be prompted for the session ID.

## What it does

### Local cleanup (automatic)
- Deletes session metadata from `~/.claude/sessions/`
- Removes any local session state, artifacts, and transcripts
- **This is instant and reversible only via backups**

### Backend cleanup (prompted)
Three options:
1. **Manual deletion link** — Extracts the conversation ID and gives you a Claude.ai link to delete it yourself
2. **Auto-delete via undocumented API** — Uses Claude.ai's internal APIs (risky, may break, no guarantees)
3. **Keep backend** — Delete local only, leave the conversation in Claude.ai (safest if you want to keep records)

## Implementation steps

When invoked:

1. **Validate** the session ID exists in `~/.claude/sessions/`
2. **Warn** the user this is destructive
3. **Ask for confirmation** and backend deletion preference
4. **Extract** conversation ID from session metadata (if it exists)
5. **Delete** local files: `rm -rf ~/.claude/sessions/<session_id>`
6. **Handle backend** based on user choice:
   - **Manual**: Print the Claude.ai conversation URL
   - **Auto**: Attempt DELETE via internal Claude.ai API endpoint
   - **Skip**: Done

## Notes

- **Backend deletion is unofficial** — Uses reverse-engineered endpoints that may not exist, fail silently, or break in future updates
- **No recovery** — Local deletion is permanent; backups are your only safety net
- **Conversation ID** — Stored in session metadata; will be extracted automatically if available
