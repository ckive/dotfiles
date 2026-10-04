"""Scenarios 13-16 of docs/scenarios.md, against this repo's real home/ source."""

from __future__ import annotations

import json
import os
import subprocess
import time
from pathlib import Path

import pytest
from conftest import REPO, run

BIN = REPO / "home" / "dot_local" / "bin"


@pytest.fixture
def fresh_home(tmp_path: Path):
    """A home where this repo's real source is applied (no packages, scripts or externals)."""
    home = tmp_path / "home"
    overlay = tmp_path / "overlay"
    (overlay / "codex").mkdir(parents=True)
    cfg = home / ".config" / "chezmoi"
    cfg.mkdir(parents=True)
    (cfg / "chezmoi.toml").write_text(
        f'sourceDir = "{REPO}"\n[data]\n    overlaySource = "{overlay}"\n'
    )
    env = {
        "PATH": os.environ["PATH"],
        "HOME": str(home),
        "XDG_CONFIG_HOME": str(home / ".config"),
        "XDG_STATE_HOME": str(home / ".local" / "state"),
        "XDG_CACHE_HOME": str(home / ".cache"),
    }

    def apply():
        out = run(
            ["chezmoi", "apply", "--force", "--no-tty", "--exclude", "scripts,externals"],
            env=env,
            check=False,
        )
        assert out.returncode == 0, out.stderr
        return out

    return home, overlay, apply


def test_codex_trusted_folders_survive_apply(fresh_home):
    """13. Codex's own folder trust survives syncing."""
    home, overlay, apply = fresh_home
    # Given Codex recorded a trusted project and a hook trust hash itself
    codex = home / ".codex" / "config.toml"
    codex.parent.mkdir(parents=True)
    codex.write_text(
        '[projects."/Users/dan/Desktop/projects/homelab-infra"]\ntrust_level = "trusted"\n'
    )
    # and the overlay adds a personal setting
    (overlay / "codex" / "config.toml").write_text('model = "gpt-5.5"\n')

    # When chezmoi applies
    apply()

    # Then the trust entry, the base setting and the overlay setting are all there
    text = codex.read_text()
    assert "homelab-infra" in text and 'trust_level = "trusted"' in text
    assert "followUpQueueMode" in text
    assert 'model = "gpt-5.5"' in text


def test_skill_stored_once_is_visible_to_claude_and_codex(fresh_home):
    """14. One skill, every tool."""
    home, _, apply = fresh_home

    apply()

    stored = home / ".config" / "agents" / "skills" / "rmsesh"
    assert (stored / "SKILL.md").is_file()
    for link in (home / ".claude" / "skills" / "rmsesh", home / ".agents" / "skills" / "rmsesh"):
        assert link.is_symlink() and link.resolve() == stored.resolve()


def test_every_agent_reads_the_shared_standards(fresh_home):
    """Instructions are written once and reach Claude, Codex and Gemini."""
    home, overlay, apply = fresh_home
    ov = home / ".config" / "agents" / "overlay.md"
    ov.parent.mkdir(parents=True, exist_ok=True)
    ov.write_text("## Personal\n- homelab rule\n")

    apply()

    standards = home / ".config" / "agents" / "standards.md"
    assert "Testing style" in standards.read_text()
    assert "@~/.config/agents/standards.md" in (home / ".claude" / "CLAUDE.md").read_text()
    assert "@~/.config/agents/overlay.md" in (home / ".claude" / "CLAUDE.md").read_text()
    codex = (home / ".codex" / "AGENTS.md").read_text()
    assert "Testing style" in codex and "homelab rule" in codex
    assert f"@{standards}" in (home / ".gemini" / "GEMINI.md").read_text()


def test_mise_tools_are_on_path_when_shell_plugins_load(fresh_home):
    """The fzf and zoxide plugins find their tools when only mise provides them."""
    # Given a machine where fzf comes only from mise (in ~/.local/bin), not from brew
    home, _, apply = fresh_home
    apply()
    tools = home / "mise-tools"
    tools.mkdir()
    (tools / "fzf").write_text("#!/bin/sh\n")
    (tools / "fzf").chmod(0o755)
    mise = home / ".local" / "bin" / "mise"
    mise.write_text(f"#!/bin/sh\necho 'path=({tools} $path)'\n")
    mise.chmod(0o755)
    omz = home / ".oh-my-zsh" / "oh-my-zsh.sh"
    omz.parent.mkdir()
    omz.write_text("(( $+commands[fzf] )) || echo 'fzf plugin: Cannot find fzf'\n")

    # When a new shell starts
    out = run(
        ["zsh", "-c", "source ~/.zshrc"],
        env={"HOME": str(home), "PATH": "/usr/bin:/bin"},
        check=False,
    )

    # Then the plugins load without complaining
    assert "Cannot find fzf" not in out.stdout + out.stderr


def test_mise_tools_work_in_non_interactive_login_shells(fresh_home):
    """Scripts and agent shells (zsh -l, not interactive) can run tools that only mise provides."""
    # Given gh is installed only by mise, as a shim
    home, _, apply = fresh_home
    apply()
    shim = home / ".local" / "share" / "mise" / "shims" / "gh"
    shim.parent.mkdir(parents=True)
    shim.write_text("#!/bin/sh\necho gh-from-mise\n")
    shim.chmod(0o755)

    # When a non-interactive login shell runs gh
    out = run(
        ["zsh", "-lc", "gh"],
        env={"HOME": str(home), "PATH": "/usr/bin:/bin"},
        check=False,
    )

    # Then mise's gh runs
    assert out.stdout.strip() == "gh-from-mise", out.stderr


def bash_home(tmp_path: Path) -> Path:
    """A $HOME with this repo's .bashrc and common.sh, and a fake `dotfiles` that logs calls."""
    home = tmp_path / "home"
    (home / ".config" / "shell").mkdir(parents=True)
    (home / ".bashrc").write_text((REPO / "home" / "dot_bashrc").read_text())
    (home / ".config" / "shell" / "common.sh").write_text(
        (REPO / "home" / "dot_config" / "shell" / "common.sh").read_text()
    )
    bin_dir = home / ".local" / "bin"
    bin_dir.mkdir(parents=True)
    (bin_dir / "dotfiles").write_text('#!/bin/sh\necho "$@" >> "$HOME/dotfiles-calls"\n')
    (bin_dir / "dotfiles").chmod(0o755)
    return home


def bash(home: Path, script: str, interactive: bool = True) -> subprocess.CompletedProcess:
    flags = ["-i", "-c"] if interactive else ["-c"]
    return run(
        ["bash", *flags, script],
        env={"HOME": str(home), "PATH": "/usr/bin:/bin", "TERM": "dumb"},
        check=False,
    )


def test_bash_loads_common_aliases_and_overlay_shell_config(tmp_path):
    """WSL uses bash: it gets the shared aliases and the overlay's ~/.config/shell/conf.d files."""
    # Given the work overlay put a proxy setting in the shared shell slot
    home = bash_home(tmp_path)
    conf = home / ".config" / "shell" / "conf.d"
    conf.mkdir()
    (conf / "work.sh").write_text("export WORK_PROXY=http://proxy:8080\n")

    # When an interactive bash starts
    out = bash(home, 'echo "proxy=$WORK_PROXY"; alias gs')

    # Then the work setting and the shared aliases are there
    assert "proxy=http://proxy:8080" in out.stdout, out.stderr
    assert "git status" in out.stdout


def test_bash_starts_a_background_sync_at_most_every_five_minutes(tmp_path):
    """Without systemd (common on WSL), opening a terminal is what keeps config in sync."""
    # Given the last sync was long ago
    home = bash_home(tmp_path)
    calls = home / "dotfiles-calls"

    # When a terminal opens
    bash(home, "true")

    # Then a sync starts in the background
    for _ in range(50):
        if calls.exists():
            break
        time.sleep(0.1)
    assert calls.read_text().split() == ["sync"]

    # And when a sync ran a moment ago, the next terminal doesn't start another
    calls.unlink()
    state = home / ".local" / "state" / "dotfiles"
    state.mkdir(parents=True)
    (state / "last.json").write_text("{}")
    bash(home, "true")
    time.sleep(1)
    assert not calls.exists()


def test_bash_warns_about_a_pending_clash(tmp_path):
    """The clash banner shows in bash too."""
    # Given a clash is waiting for a decision
    home = bash_home(tmp_path)
    state = home / ".local" / "state" / "dotfiles"
    state.mkdir(parents=True)
    (state / "conflict.json").write_text("{}")
    (state / "last.json").write_text("{}")

    # When a terminal opens
    out = bash(home, "true")

    # Then it says what to run
    assert "dotfiles: clash pending, run: dotfiles resolve" in out.stdout + out.stderr


def test_mise_tools_work_in_non_interactive_bash(tmp_path):
    """Scripts and agents in bash can run tools only mise provides."""
    # Given gh is installed only by mise, as a shim
    home = bash_home(tmp_path)
    shim = home / ".local" / "share" / "mise" / "shims" / "gh"
    shim.parent.mkdir(parents=True)
    shim.write_text("#!/bin/sh\necho gh-from-mise\n")
    shim.chmod(0o755)

    # When a non-interactive bash that reads .bashrc (ssh commands, ~/.profile) runs gh
    out = bash(home, "source ~/.bashrc; gh", interactive=False)

    # Then mise's gh runs
    assert out.stdout.strip() == "gh-from-mise", out.stderr


def test_zsh_loads_overlay_shell_config_from_the_shared_slot(fresh_home):
    """The shared ~/.config/shell/conf.d slot works in zsh too (Mac, Linux servers)."""
    # Given an overlay file in the shared slot
    home, _, apply = fresh_home
    apply()
    conf = home / ".config" / "shell" / "conf.d"
    conf.mkdir(parents=True)
    (conf / "work.sh").write_text("export WORK_PROXY=http://proxy:8080\n")

    # When zsh starts
    out = run(
        ["zsh", "-c", 'source ~/.zshrc; echo "proxy=$WORK_PROXY"'],
        env={"HOME": str(home), "PATH": "/usr/bin:/bin"},
        check=False,
    )

    # Then the setting is loaded
    assert "proxy=http://proxy:8080" in out.stdout, out.stderr


def guard(script: str, payload: dict) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["bash", str(BIN / script)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        timeout=30,
    )


@pytest.mark.parametrize(
    "command",
    [
        "rm -rf build/",
        "git add -A",
        "git add .",
        "git commit -a -m wip",
        "git reset --hard HEAD~1",
        "git push --force origin main",
        "git clean -fd",
        "dotfiles publish --yes",
    ],
)
def test_guard_blocks_destructive_commands(command, tmp_path):
    """15. Destructive commands are blocked."""
    result = guard(
        "executable_claude-hook-guard-bash",
        {"tool_input": {"command": command}, "cwd": str(tmp_path)},
    )
    assert result.returncode == 2
    assert "BLOCKED" in result.stderr


@pytest.mark.parametrize(
    "command",
    [
        "git push --force-with-lease origin feature",
        "git add src/main.py",
        'git commit -m "fix: handle git add -A in docs"',
        "rm notes.txt",
    ],
)
def test_guard_allows_safe_variants(command, tmp_path):
    """15b. ...but their safe variants run normally."""
    result = guard(
        "executable_claude-hook-guard-bash",
        {"tool_input": {"command": command}, "cwd": str(tmp_path)},
    )
    assert result.returncode == 0, result.stderr


def test_guard_blocks_token_written_into_tracked_config(tmp_path):
    """16. Secrets can't be written into config."""
    token = "ghp_" + "a" * 36
    result = guard(
        "executable_claude-hook-guard-edit",
        {
            "tool_input": {
                "file_path": "/Users/x/.claude/settings.json",
                "content": json.dumps({"env": {"GITHUB_TOKEN": token}}),
            },
        },
    )
    assert result.returncode == 2
    assert "credential" in result.stderr


def test_guard_allows_ordinary_config_edit():
    result = guard(
        "executable_claude-hook-guard-edit",
        {
            "tool_input": {"file_path": "/Users/x/.claude/settings.json", "content": '{"a": 1}'},
        },
    )
    assert result.returncode == 0
