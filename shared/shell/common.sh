# Shared shell config — sourced by both macOS zshrc and Linux bashrc
[[ $- != *i* ]] && return

export EDITOR=nano

alias ll='ls -alF'
alias la='ls -A'
alias l='ls -CF'

alias g='git'
alias gs='git status'
alias gd='git diff'
alias gl='git log --oneline -20'

command -v bat &>/dev/null && alias cat='bat --pager=never'

dotfiles() {
  local repo="$HOME/dotfiles"
  case "${1:-}" in
    cd)
      cd "$repo"
      ;;
    push)
      (
        cd "$repo"
        git add -A
        git commit -m "dotfiles: $(date '+%Y-%m-%d %H:%M')"
      )
      ;;
    pull)
      ( cd "$repo" && git pull )
      ;;
    status)
      ( cd "$repo" && git status )
      ;;
    *)
      echo "Usage: dotfiles {cd|push|pull|status}"
      ;;
  esac
}
