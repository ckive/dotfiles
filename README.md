# dotfiles

Shell, git, editor, dev-tool and AI-agent (Claude, Codex, Gemini) config for macOS, Linux and WSL,
managed with [chezmoi](https://www.chezmoi.io/). It keeps itself in sync. You mostly just use your
machine.

## How it fits together

| Repo | Visibility | Holds |
|---|---|---|
| `ckive/dotfiles` (this one) | public | everything that's the same on every machine |
| `ckive/dotfiles-personal` | private | personal git identity, ssh hosts, homelab skills/plugins/MCP servers |
| `dotfiles-work` (company git) | private | work tools, MCP servers, instructions |

Every machine applies this repo plus one private overlay. A background **sync** runs every 5
minutes and at each new shell. It saves your local edits to GitHub, pulls changes from your other
machines, and applies them. Pull-only machines (dev01, devcontainers) only receive.

## Set up a machine

```bash
curl -fsSL https://raw.githubusercontent.com/ckive/dotfiles/main/install.sh | sh
```

It installs chezmoi, applies this repo, installs packages (Homebrew on macOS, apt on Linux, mise
for dev tools), and schedules the sync. It asks which overlay to use: `personal`, `work`, or none.
Then do the things that are deliberately **not** in git:

1. `gh auth login` (lets the sync reach your private overlay)
2. Create an ssh key for this machine and add it to GitHub/Forgejo (keys are per machine, never copied)
3. Restore secrets (`~/.config/homelab/*.secret`) yourself. This repo never manages them
4. Sign into apps; turn **off** VS Code/Cursor Settings Sync (this repo owns those settings)

Lost or stolen machine: everything above is already on GitHub (at most ~5 minutes of edits are
lost). Revoke that machine's ssh keys and `gh` token, then set up the new one.

## Day to day

Edit files where they live (`~/.zshrc`, `~/.claude/settings.json`, `/plugin install …`). The sync
picks them up. There's nothing to run.

| You want to… | Do this |
|---|---|
| Check that everything is healthy | `dotfiles status` |
| Sync right now | `dotfiles sync` |
| Fix a clash (you'll be told) | `dotfiles resolve` and pick: keep mine / take theirs / merge by hand |
| Share a private skill or file with every machine, publicly | `dotfiles promote <path>` |
| Find config that isn't tracked yet | `dotfiles drift` |
| Track a new file | `chezmoi add <path>` (public) or `dotfiles ov add <path>` (private) |
| Stop tracking a file | `chezmoi forget <path>` (or `dotfiles ov forget`) |
| Change a package list | edit `Brewfile` / `packages-apt.txt` / `~/.config/mise/config.toml`. Installs on next sync |

New files under `~/.claude/{skills,agents,commands,rules}` go to the **private** overlay
automatically. Nothing becomes public until you `promote` it.

## Where things go

| Thing | Public base | Private overlay |
|---|---|---|
| Shell | `.zshrc`, `common.sh`, prompt | `~/.config/zsh/conf.d/*.zsh` |
| Git | defaults, aliases, global ignore | identity, signing key |
| SSH | defaults | `~/.ssh/config.d/*.conf` hosts |
| Agent instructions | `~/.config/agents/standards.md` (Claude, Codex, Gemini all read it) | `~/.claude/rules/*.md`, overlay instructions |
| Skills | `~/.config/agents/skills/` (Claude + Codex) | same, in the overlay |
| Claude plugins, marketplaces, permissions | base `settings.json` | added on top, never replacing |
| MCP servers | (none) | `mcp-servers.json` |
| Packages | `Brewfile`, `packages-apt.txt`, mise config | `Brewfile.overlay` |

**Never tracked:** secrets, tokens, private keys, shell history, caches, Claude sessions
(`~/.claude/projects`). `chezmoi add` refuses anything shaped like an API key.

## Develop this repo

`just setup`, `just test`, `just lint`, `just fmt`, `just check`. What the repo promises is in
[docs/scenarios.md](docs/scenarios.md). Each scenario is a test. Windows/WSL setup:
[docs/windows.md](docs/windows.md).
