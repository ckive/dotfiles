# Shared shell config — sourced by both macOS zshrc and Linux bashrc
[[ $- != *i* ]] && return

export EDITOR=nano

alias ll='ls -alF'
alias la='ls -A'
alias l='ls -CF'

alias lg='lazygit'
alias g='git'
alias gs='git status'
alias gd='git diff'
alias gl='git log --oneline -20'

command -v bat &>/dev/null && alias cat='bat --pager=never'

# Local LLM switcher for Claude Code (via ollama)
_LLLM_DEFAULT_FILE="$HOME/.lllm_default"

_lllm_help() {
  echo "lllm — toggle Claude Code between local (ollama) and Anthropic models"
  echo ""
  echo "  lllm on               activate local model (uses saved default)"
  echo "  lllm off              deactivate, revert to Anthropic"
  echo "  lllm list             show available ollama models"
  echo "  lllm status           show whether local mode is active"
  echo "  lllm default          show current default local model"
  echo "  lllm default <model>  set a new default local model"
  echo "  lllm help             show this message"
  echo ""
  echo "  Note: state is per terminal session. New sessions default to Anthropic."
}

lllm() {
  case "$1" in
    on)
      local model
      [[ -f "$_LLLM_DEFAULT_FILE" ]] && model=$(cat "$_LLLM_DEFAULT_FILE") || model="gemma4:e4b"
      export ANTHROPIC_AUTH_TOKEN=ollama
      export ANTHROPIC_BASE_URL=http://localhost:11434
      export _LLLM_ACTIVE_MODEL="$model"
      echo "local LLM ON → $model"
      ;;
    off)
      unset ANTHROPIC_AUTH_TOKEN
      unset ANTHROPIC_BASE_URL
      unset _LLLM_ACTIVE_MODEL
      echo "local LLM OFF → Anthropic"
      ;;
    list)
      ollama list
      ;;
    default)
      if [[ -z "$2" ]]; then
        echo "current default: ${$(cat "$_LLLM_DEFAULT_FILE" 2>/dev/null):-gemma4:e4b}"
      else
        echo "$2" > "$_LLLM_DEFAULT_FILE"
        echo "default set to: $2"
      fi
      ;;
    status)
      if [[ -n "$ANTHROPIC_BASE_URL" ]]; then
        echo "ON → model: ${_LLLM_ACTIVE_MODEL:-unknown} | base: $ANTHROPIC_BASE_URL"
      else
        echo "OFF → Anthropic"
      fi
      ;;
    help|"")
      _lllm_help
      ;;
    *)
      echo "unknown command: $1"
      _lllm_help
      ;;
  esac
}

# Wrap claude to auto-inject --model when local LLM mode is active
claude() {
  if [[ -n "$ANTHROPIC_BASE_URL" && -n "$_LLLM_ACTIVE_MODEL" ]]; then
    command claude --model "$_LLLM_ACTIVE_MODEL" "$@"
  else
    command claude "$@"
  fi
}

# Dotfiles are managed by chezmoi (source: ~/Desktop/projects/dotfiles).
#   chezmoi cd       jump to the source dir
#   chezmoi edit <f> edit a managed file
#   chezmoi apply    push source -> home
#   chezmoi re-add   pull home -> source
#   chezmoi update   pull from remote and apply
alias df='chezmoi'
alias dfcd='chezmoi cd'
