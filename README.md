# dotfiles

Personal dotfiles managed with [chezmoi](https://www.chezmoi.io/). The source of truth is
this repo, checked out at `~/Documents/dotfiles`.

Primary purpose: keep **agentic coding configs** (Claude Code, Kimi Code, Codex) in sync
across machines automatically. Adapted from
[rymiwe's gist](https://gist.github.com/rymiwe/2e5b940ae1ba981551450d318a2ee6c5).

> This repo is **private**. It holds agent settings and local permission lists. Keep it that way.

## How syncing works

| Direction | Mechanism |
|---|---|
| Push | chezmoi `autoCommit` + `autoPush` — every `chezmoi add` commits and pushes |
| Pull | `SessionStart` hook runs `~/.local/bin/chezmoi-session-sync` (chezmoi has **no** native autoPull) |
| Capture | `PostToolUse` hook auto-adds any edited `.claude/` file; `Stop` hook runs `chezmoi re-add` |

## Machine roles

One data var, `role`, set once at `chezmoi init`. It changes only the git flow and which
role-gated hooks act — every Claude config file is identical on every machine.

| Role | Source branch | Pushes to | Role-gated hooks |
|---|---|---|---|
| `workstation` (default) | `main` | `main` directly | none (they exit immediately) |
| `agent` (e.g. dev01) | `agent/<hostname>` | that branch; `claude-hook-agent-pr` keeps one PR open into `main` | `guard-bash` blocks any push to `main`/`master`; session sync rebases onto `main` and never blocks |

Agent-made config (new skills, agents, settings) reaches other machines only after Dan
merges the `agent config: <host>` PR. The main-push block is hook-enforced only: GitHub
Free cannot protect branches on private repos.

Claude config comes from three layers — keep each thing in exactly one:

| Layer | Holds | Managed by |
|---|---|---|
| `~/.claude/settings.json` etc. (this repo) | personal settings, hooks, skills, agents — all machines | chezmoi |
| `/etc/claude-code/managed-settings.json` | agent-host policy: permission mode, bridge/telemetry hooks, fleet plugins | Ansible (`homelab-infra`, role `agent_host`) |
| Plugin marketplace `homelab/claude-plugins` | shared homelab skills, hooks, MCP config | Forgejo repo, enabled by either layer above |

Portability rule: no OS templating inside Claude config. Hook scripts handle OS
differences themselves (e.g. `claude-notify` uses `osascript` on macOS, `notify-send` with a
display, else nothing).

## New machine

`sourceDir` lives in the config file, but on a fresh machine that config doesn't exist until
after `init` — so the non-default source path **must** be passed explicitly the first time:

```bash
brew install chezmoi flock jq
chezmoi init --apply --source ~/Documents/dotfiles git@github.com:ckive/dotfiles.git
```

Agent host (done by Ansible; needs `gh` authenticated with the dotfiles-scoped PAT and
`gh auth setup-git`, plus `flock`, `jq`):

```bash
chezmoi init --apply --promptString role=agent \
  --source ~/Documents/dotfiles https://github.com/ckive/dotfiles.git
```

Existing machine picking up the `role` var for the first time: `chezmoi init` (answer
`workstation`). Until then templates default to `workstation`.

`flock` and `jq` are genuine dependencies, not optional: the auto-add and Stop hooks call
`flock` for locking, and every hook parses its stdin JSON with `jq`. macOS ships neither
`flock` nor a new enough `jq` by default — without them the hooks fail **silently**.

## What gets backed up (two gates)

A file is auto-tracked only if it passes **both**:

**Gate 1 — WHAT.** It must be an agent config file:
`CLAUDE.md`, `CLAUDE.local.md`, `AGENTS.md`, `AGENTS.local.md`, or anything under
`.claude/`, `.codex/`, `.kimi-code/`. Source code, build output, and data are never
tracked, ever.

**Gate 2 — WHERE.** It must live under either:
- a global agent dir — `~/.claude`, `~/.codex`, `~/.kimi-code` (always included), or
- a prefix listed in `~/.config/claude-sync/backup-paths`

To back up a new project directory, add one line to that file:

```bash
echo '~/work/client-x/' >> ~/.config/claude-sync/backup-paths
chezmoi re-add   # picks up the allowlist change itself
```

The allowlist widens **where** we look, never **what** we take — adding a 20GB
project directory does not put 20GB in this repo.

> Upstream gist note: its setup section is opt-in per project, but its hook
> blanket-matches `.claude/` and sweeps in every project under `$HOME`. Gate 2
> restores the documented intent.

## Layout

| Source path | Target | Notes |
|---|---|---|
| `dot_zshrc` | `~/.zshrc` | oh-my-zsh + p10k |
| `dot_gitconfig` | `~/.gitconfig` | aliases folded in (no more `.gitconfig_shared`) |
| `private_dot_config/shell/common.sh` | `~/.config/shell/common.sh` | aliases, `lllm()` switcher, `claude()` wrapper |
| `dot_claude/` | `~/.claude/` | settings, hooks, agents, skills, commands, rules |
| `dot_kimi-code/tui.toml` | `~/.kimi-code/tui.toml` | client prefs only |
| `dot_codex/` | `~/.codex/` | Codex settings, `AGENTS.md` |
| `private_dot_local/bin/` | `~/.local/bin/` | hook scripts (`executable_` = mode 755, `.tmpl` = rendered with `role`) |

Naming: `dot_` → `.`, `private_` → chmod 600, `executable_` → chmod 755.

## Daily use

```bash
chezmoi edit ~/.zshrc     # edit the SOURCE, then apply
chezmoi apply             # source  -> home
chezmoi re-add            # home    -> source
chezmoi update            # remote  -> home
chezmoi cd                # jump to the source dir
chezmoi diff              # what would apply change?
chezmoi managed           # what is tracked?
```

Shell shortcuts in `common.sh`: `df` → `chezmoi`, `dfcd` → `chezmoi cd`.

### The one footgun

chezmoi **copies**; it does not symlink. Editing a file in `~` does not update the source,
and the next `chezmoi apply` will overwrite it. Either edit via `chezmoi edit`, or edit in
`~` and then run `chezmoi re-add`. A `PreToolUse` guard hook warns when Claude edits the
source dir directly.

## What is deliberately not tracked

Session data, caches, credentials, telemetry, and device IDs — see `.chezmoiignore`.
Notably excluded: `~/.claude/{sessions,projects,history.jsonl,.credentials.json,plugins}`,
`~/.kimi-code/{device_id,telemetry,sessions}`, and `~/.codex/auth.json`.

`.chezmoiignore` paths are **target**-relative (`.claude/...`), never source-relative
(`dot_claude/...`). Verify with `chezmoi ignored`.

## Secrets

`add.secrets = "error"` in the chezmoi config makes `chezmoi add` hard-fail on anything
API-key-shaped, rather than warning. This is deliberate — the auto-add hook runs unattended,
so a warning would scroll past unseen.
