set shell := ["bash", "-euo", "pipefail", "-c"]

shell_scripts := "install.sh home/dot_bashrc tests/e2e-checks.sh home/dot_local/bin/executable_claude-hook-guard-bash home/dot_local/bin/executable_claude-hook-guard-edit home/dot_local/bin/executable_claude-notify home/dot_local/bin/executable_cc-v"

default: check

# Install the test and lint toolchain
setup:
    uv sync

# Behavior tests (docs/scenarios.md)
test *args:
    uv run pytest -n auto {{ args }}

lint:
    uv run ruff check . home/dot_local/bin/executable_cc-v-proxy
    uv run ruff format --check . home/dot_local/bin/executable_cc-v-proxy
    uv run ty check bin/dotfiles tests
    uv run shellcheck {{ shell_scripts }}
    uv run shfmt -d -i 2 -ci {{ shell_scripts }}

fmt:
    uv run ruff check --fix .
    uv run ruff format .
    uv run shfmt -w -i 2 -ci {{ shell_scripts }}

check: lint test

# Sync this machine now
run:
    bin/dotfiles sync

# Fresh Debian machine from install.sh (needs Docker / OrbStack)
e2e:
    docker run --rm -v "$PWD:/src:ro" debian:13 bash -c '\
      apt-get update -q && apt-get install -yq git ca-certificates curl >/dev/null && \
      git config --global --add safe.directory "*" && git clone -q /src /root/dotfiles && cd /root/dotfiles && \
      DOTFILES_MODE=pull DOTFILES_OVERLAY=none DOTFILES_SKIP_SCHEDULE=1 sh install.sh && \
      sh tests/e2e-checks.sh'
