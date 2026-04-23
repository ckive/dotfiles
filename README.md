# dotfiles

Personal dotfiles for macOS (and Linux VMs). Managed via symlinks.

## Setup

```bash
git clone git@github.com:ckive/dotfiles.git ~/dotfiles
cd ~/dotfiles
./setup.sh
```

Then open a new shell.

## Structure

| Path | Purpose |
|------|---------|
| `macos/zshrc` | macOS zsh config (oh-my-zsh + p10k) |
| `linux/bashrc` | Linux / Docker stub |
| `shared/shell/common.sh` | Aliases + `dotfiles()` function, sourced by both shells |
| `shared/git/gitconfig` | Git aliases, included via `~/.gitconfig_shared` |
| `claude/settings.json` | Claude Code user settings |
| `claude/CLAUDE.md` | Claude Code global instructions |
| `claude/agents/` | Custom Claude agents |
| `hooks/post-commit` | Auto-pushes dotfiles to all remotes after each commit |

## dotfiles command

```bash
dotfiles cd      # jump to ~/dotfiles
dotfiles push    # git add -A + commit + push
dotfiles pull    # git pull
dotfiles status  # git status
```

## Prerequisites (macOS)

```bash
brew install oh-my-posh fzf zoxide bat ripgrep fd lazygit gh
brew install --cask font-jetbrains-mono-nerd-font
```
