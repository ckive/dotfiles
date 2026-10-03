#!/bin/sh
# Set up this machine from the dotfiles repo.
#
#   curl -fsSL https://raw.githubusercontent.com/ckive/dotfiles/main/install.sh | sh
#
# Also the entrypoint GitHub Codespaces / devcontainers run from a checkout (pull-only, no overlay).
# Optional env: DOTFILES_DIR, DOTFILES_MODE (push|pull), DOTFILES_OVERLAY (personal|work|none),
# DOTFILES_OVERLAY_URL, DOTFILES_SKIP_PACKAGES=1, DOTFILES_SKIP_SCHEDULE=1.
set -eu

BASE_URL="https://github.com/ckive/dotfiles.git"
PERSONAL_URL="https://github.com/ckive/dotfiles-personal.git"

say() { printf '\033[1mdotfiles:\033[0m %s\n' "$*"; }
# ask "question" default -> prints the answer (default when there is no terminal)
ask() {
  reply=""
  if [ -z "${CI:-}" ] && (: </dev/tty) 2>/dev/null; then
    printf '%s [%s]: ' "$1" "$2" >/dev/tty
    read -r reply </dev/tty || reply=""
  fi
  printf '%s' "${reply:-$2}"
}

os="$(uname -s)"
export PATH="$HOME/.local/bin:$PATH"

# ---- 1. Tools the setup itself needs: git, curl, Homebrew (macOS), uv, chezmoi ----
if [ "$os" = Darwin ]; then
  if ! command -v brew >/dev/null 2>&1 && [ ! -x /opt/homebrew/bin/brew ]; then
    say "installing Homebrew (asks for your password)"
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
  fi
  [ -x /opt/homebrew/bin/brew ] && eval "$(/opt/homebrew/bin/brew shellenv)"
elif command -v apt-get >/dev/null 2>&1; then
  need=""
  for p in git curl zsh jq ca-certificates; do
    dpkg-query -W -f='${Status}' "$p" 2>/dev/null | grep -q "ok installed" || need="$need $p"
  done
  if [ -n "$need" ]; then
    say "installing$need"
    sudo=""
    [ "$(id -u)" -eq 0 ] || sudo="sudo"
    # shellcheck disable=SC2086 # $need is a word list
    $sudo apt-get update -q && $sudo apt-get install -yq $need
  fi
fi
command -v uv >/dev/null 2>&1 || {
  say "installing uv"
  curl -LsSf https://astral.sh/uv/install.sh | sh
}
command -v chezmoi >/dev/null 2>&1 || {
  say "installing chezmoi"
  sh -c "$(curl -fsLS get.chezmoi.io)" -- -b "$HOME/.local/bin"
}

# ---- 2. The base repo ----
here="$(cd "$(dirname "$0")" 2>/dev/null && pwd || true)"
if [ -n "$here" ] && [ -f "$here/.chezmoiroot" ] && [ -f "$here/bin/dotfiles" ]; then
  base="$here" # run from a checkout (Codespaces, devcontainer, or by hand)
else
  if [ "$os" = Darwin ]; then default_dir="$HOME/Desktop/projects/dotfiles"; else default_dir="$HOME/dotfiles"; fi
  base="${DOTFILES_DIR:-$default_dir}"
  [ -d "$base/.git" ] || {
    mkdir -p "$(dirname "$base")"
    git clone -q "$BASE_URL" "$base"
  }
fi

# ---- 3. Mode and overlay ----
if [ -n "${CODESPACES:-}${REMOTE_CONTAINERS:-}" ]; then
  mode="${DOTFILES_MODE:-pull}"
  overlay="${DOTFILES_OVERLAY:-none}"
else
  mode="${DOTFILES_MODE:-$(ask "Sync mode: push (your machine) or pull (receive only)" push)}"
  overlay="${DOTFILES_OVERLAY:-$(ask "Private overlay: personal, work or none" none)}"
fi

overlay_src=""
if [ "$overlay" != none ]; then
  case "$overlay" in
    personal) url="${DOTFILES_OVERLAY_URL:-$PERSONAL_URL}" ;;
    *) url="${DOTFILES_OVERLAY_URL:-$(ask "Git URL of the $overlay overlay" "")}" ;;
  esac
  overlay_src="$(dirname "$base")/dotfiles-$overlay"
  if [ ! -d "$overlay_src/.git" ] && ! git clone -q "$url" "$overlay_src"; then
    say "could not clone $url (private repo: run 'gh auth login && gh auth setup-git' first)."
    say "continuing without an overlay; rerun install.sh to add it."
    overlay=none
    overlay_src=""
  fi
fi

mkdir -p "$HOME/.config/dotfiles" "$HOME/.config/chezmoi"
{
  printf 'mode = "%s"\n' "$mode"
  [ "$overlay" != none ] && printf 'overlay = "%s"\n' "$overlay"
} >"$HOME/.config/dotfiles/config.toml"
if [ "$overlay" != none ]; then
  cat >"$HOME/.config/chezmoi/$overlay.toml" <<TOML
sourceDir = "$overlay_src"
[git]
    autoCommit = false
    autoPush = false
[add]
    secrets = "error"
TOML
fi

# ---- 4. Apply: render the base config, then one sync applies overlay + base ----
DOTFILES_OVERLAY_SOURCE="$overlay_src" chezmoi init --source "$base"
say "applying (packages can take a while the first time)"
"$base/bin/dotfiles" sync
"$base/bin/dotfiles" status || true
say "done. Open a new terminal. Not in git, do these yourself: ssh key, gh auth login, secrets, app sign-ins."
