#!/bin/sh
# Checks after install.sh on a fresh machine (scenario 17). Prints every result.
# shellcheck disable=SC2016 # each check is single-quoted on purpose; sh -c expands it
fail=0
check() {
  if sh -c "$2" >/dev/null 2>&1; then echo "ok   $1"; else
    echo "FAIL $1"
    fail=1
  fi
}
check "skill linked for Claude" 'test -L "$HOME/.claude/skills/rmsesh"'
check "skill linked for Codex" 'test -L "$HOME/.agents/skills/rmsesh"'
check "standards installed" 'grep -q "Testing style" "$HOME/.config/agents/standards.md"'
check "oh-my-zsh fetched" 'test -f "$HOME/.oh-my-zsh/oh-my-zsh.sh"'
check "p10k fetched" 'test -d "$HOME/.oh-my-zsh/custom/themes/powerlevel10k"'
check "dotfiles CLI linked" 'test -L "$HOME/.local/bin/dotfiles"'
check "mise installed" 'test -x "$HOME/.local/bin/mise"'
check "ripgrep via mise" '"$HOME/.local/bin/mise" which rg'
check "zsh installed by apt" 'command -v zsh'
check "status healthy" '"$HOME/.local/bin/dotfiles" status'
cat "$HOME/.local/state/dotfiles/last.json" 2>/dev/null
exit $fail
