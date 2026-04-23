#!/usr/bin/env bash
set -euo pipefail

DOTFILES_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

detect_os() {
  case "$(uname -s)" in
    Darwin) echo "macos" ;;
    Linux)
      if grep -qi microsoft /proc/version 2>/dev/null; then
        echo "wsl"
      else
        echo "linux"
      fi
      ;;
    *) echo "unknown" ;;
  esac
}

link_file() {
  local src="$1" dst="$2"
  if [ -L "$dst" ] && [ "$(readlink "$dst")" = "$src" ]; then
    echo "[ok]   $dst"
    return
  fi
  if [ -L "$dst" ]; then
    rm "$dst"
  elif [ -e "$dst" ]; then
    mv "$dst" "${dst}.bak"
    echo "[bak]  ${dst}.bak"
  fi
  mkdir -p "$(dirname "$dst")"
  ln -s "$src" "$dst"
  echo "[link] $dst -> $src"
}

link_dir() {
  local src="$1" dst="$2"
  if [ -L "$dst" ] && [ "$(readlink "$dst")" = "$src" ]; then
    echo "[ok]   $dst"
    return
  fi
  if [ -L "$dst" ]; then
    rm "$dst"
  elif [ -d "$dst" ]; then
    mv "$dst" "${dst}.bak"
    echo "[bak]  ${dst}.bak"
  fi
  mkdir -p "$(dirname "$dst")"
  ln -s "$src" "$dst"
  echo "[link] $dst -> $src"
}

OS=$(detect_os)
echo "==> Detected OS: $OS"
echo ""

# Shared links
echo "==> Shared"
link_file "$DOTFILES_DIR/shared/shell/common.sh" "$HOME/.config/shell/common.sh"
link_file "$DOTFILES_DIR/shared/git/gitconfig"   "$HOME/.gitconfig_shared"

if ! grep -q "gitconfig_shared" "$HOME/.gitconfig" 2>/dev/null; then
  printf '\n[include]\n    path = ~/.gitconfig_shared\n' >> "$HOME/.gitconfig"
  echo "[edit] Added [include] path to ~/.gitconfig"
fi

# Claude links
echo ""
echo "==> Claude"
link_file "$DOTFILES_DIR/claude/settings.json" "$HOME/.claude/settings.json"
link_file "$DOTFILES_DIR/claude/CLAUDE.md"     "$HOME/.claude/CLAUDE.md"
link_dir  "$DOTFILES_DIR/claude/skills"        "$HOME/.claude/skills"
link_dir  "$DOTFILES_DIR/claude/agents"        "$HOME/.claude/agents"
link_dir  "$DOTFILES_DIR/claude/output-styles" "$HOME/.claude/output-styles"

# OS-specific links
echo ""
echo "==> OS: $OS"
case "$OS" in
  macos)
    link_file "$DOTFILES_DIR/macos/zshrc" "$HOME/.zshrc"
    ;;
  wsl|linux)
    link_file "$DOTFILES_DIR/linux/bashrc" "$HOME/.bashrc"
    ;;
esac

# Git hook
echo ""
echo "==> Git hook"
HOOK_SRC="$DOTFILES_DIR/hooks/post-commit"
HOOK_DST="$DOTFILES_DIR/.git/hooks/post-commit"
chmod +x "$HOOK_SRC"
mkdir -p "$DOTFILES_DIR/.git/hooks"
if [ -L "$HOOK_DST" ] && [ "$(readlink "$HOOK_DST")" = "$HOOK_SRC" ]; then
  echo "[ok]   post-commit hook"
else
  ln -sf "$HOOK_SRC" "$HOOK_DST"
  echo "[link] post-commit hook"
fi

echo ""
echo "Done. Open a new shell to pick up changes."
