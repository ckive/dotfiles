"""Test world: throwaway git remotes and machines with their own $HOME.

Every test drives the real `bin/dotfiles` CLI and real chezmoi/git against these, so nothing
touches the developer's own config or GitHub.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
DOTFILES = REPO / "bin" / "dotfiles"


def run(cmd: list[str], cwd: Path | None = None, env: dict | None = None, check: bool = True):
    return subprocess.run(
        cmd, cwd=cwd, env=env, check=check, capture_output=True, text=True, timeout=120
    )


@dataclass
class Remote:
    path: Path
    env: dict

    def git(self, *args: str) -> str:
        return run(["git", "--git-dir", str(self.path), *args], env=self.env).stdout

    def commits(self) -> list[str]:
        """Commit subjects on main, newest first."""
        return self.git("log", "--format=%s", "main").splitlines()

    def files(self) -> list[str]:
        return self.git("ls-tree", "-r", "--name-only", "main").splitlines()

    def show(self, path: str) -> str:
        return self.git("show", f"main:{path}")


@dataclass
class Machine:
    name: str
    home: Path
    env: dict
    base_src: Path
    overlay_src: Path
    notify_log: Path
    mode: str = "push"
    last: subprocess.CompletedProcess | None = field(default=None, repr=False)

    def path(self, rel: str) -> Path:
        return self.home / rel

    def read(self, rel: str) -> str:
        return self.path(rel).read_text()

    def write(self, rel: str, content: str) -> None:
        p = self.path(rel)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)

    def dotfiles(self, *args: str, input: str | None = None) -> subprocess.CompletedProcess:
        self.last = subprocess.run(
            [sys.executable, str(DOTFILES), *args],
            env=self.env,
            cwd=self.home,
            capture_output=True,
            text=True,
            input=input,
            timeout=120,
        )
        return self.last

    def sync(self) -> subprocess.CompletedProcess:
        result = self.dotfiles("sync")
        assert result.returncode == 0, result.stdout + result.stderr
        return result

    def notifications(self) -> str:
        return self.notify_log.read_text() if self.notify_log.exists() else ""


class World:
    def __init__(self, root: Path):
        self.root = root
        self.env = self._base_env()
        self.base = self._seed_remote("base", BASE_SEED)
        self.overlay = self._seed_remote("overlay", OVERLAY_SEED)

    def _base_env(self) -> dict:
        gitconfig = self.root / "gitconfig-global"
        gitconfig.write_text(
            "[user]\n\tname = Test\n\temail = test@example.com\n"
            "[init]\n\tdefaultBranch = main\n"
            "[commit]\n\tgpgsign = false\n"
            "[advice]\n\tdetachedHead = false\n"
        )
        env = {
            "PATH": os.environ["PATH"],
            "GIT_CONFIG_GLOBAL": str(gitconfig),
            "GIT_CONFIG_NOSYSTEM": "1",
            "LANG": "C.UTF-8",
            "TERM": "dumb",
        }
        return env

    def _seed_remote(self, name: str, files: dict[str, str]) -> Remote:
        bare = self.root / "remotes" / f"{name}.git"
        run(["git", "init", "--bare", "-q", "-b", "main", str(bare)], env=self.env)
        work = self.root / "seed" / name
        work.mkdir(parents=True)
        for rel, content in files.items():
            p = work / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content)
            if rel in EXECUTABLE:
                p.chmod(0o755)
        run(["git", "init", "-q", "-b", "main"], cwd=work, env=self.env)
        run(["git", "add", "--all"], cwd=work, env=self.env)
        run(["git", "commit", "-q", "-m", "seed"], cwd=work, env=self.env)
        run(["git", "push", "-q", str(bare), "main"], cwd=work, env=self.env)
        return Remote(bare, self.env)

    def machine(
        self, name: str, mode: str = "push", overlay: bool = True, first_sync: bool = True
    ) -> Machine:
        home = self.root / "machines" / name
        home.mkdir(parents=True)
        src = home / "src"
        base_src, overlay_src = src / "dotfiles", src / "dotfiles-personal"
        run(["git", "clone", "-q", str(self.base.path), str(base_src)], env=self.env)
        run(["git", "clone", "-q", str(self.overlay.path), str(overlay_src)], env=self.env)
        notify_log = home / "notifications.log"
        env = {
            **self.env,
            "HOME": str(home),
            "XDG_CONFIG_HOME": str(home / ".config"),
            "XDG_STATE_HOME": str(home / ".local" / "state"),
            "XDG_CACHE_HOME": str(home / ".cache"),
            "DOTFILES_HOST": name,
            "DOTFILES_NOTIFY_LOG": str(notify_log),
        }
        cfg = home / ".config" / "chezmoi"
        cfg.mkdir(parents=True)
        (cfg / "chezmoi.toml").write_text(
            f'sourceDir = "{base_src}"\n'
            f'[data]\n    overlaySource = "{overlay_src if overlay else ""}"\n'
        )
        dcfg = home / ".config" / "dotfiles"
        dcfg.mkdir(parents=True)
        lines = [f'mode = "{mode}"']
        if overlay:
            (cfg / "personal.toml").write_text(f'sourceDir = "{overlay_src}"\n')
            lines.append('overlay = "personal"')
        (dcfg / "config.toml").write_text("\n".join(lines) + "\n")
        m = Machine(name, home, env, base_src, overlay_src, notify_log, mode)
        if first_sync:
            m.sync()  # first apply, like a fresh install
        return m

    def offline(self, remote: Remote) -> Path:
        """Make a remote unreachable; returns a token to restore it."""
        hidden = remote.path.with_suffix(".offline")
        shutil.move(remote.path, hidden)
        return hidden

    def online(self, remote: Remote, hidden: Path) -> None:
        shutil.move(hidden, remote.path)


TEST_IGNORES = (
    "notifications.log\nsrc\nfake-editor.sh\n.cache\n.zsh_history\n.local/state\n"
    ".claude.json\n.claude/plugins\n.claude/projects\n"
)

BASE_SEED = {
    ".chezmoiroot": "home\n",
    "bin/dotfiles": DOTFILES.read_text(),
    "claude/settings.json": json.dumps(
        {
            "enabledPlugins": {"context7@claude-plugins-official": True},
            "permissions": {"allow": ["Bash(git status)"]},
        }
    ),
    "home/dot_claude/modify_settings.json.tmpl": (
        REPO / "home/dot_claude/modify_settings.json.tmpl"
    ).read_text(),
    "home/dot_zshrc": "export EDITOR=nano\nalias gs='git status'\n",
    "home/dot_gitconfig": "[alias]\n\tst = status\n",
    "home/dot_config/agents/standards.md": "# Standards\n\n- be concise\n",
    "home/.chezmoiignore": TEST_IGNORES,
    "drift-ignore": (REPO / "drift-ignore").read_text(),
}

OVERLAY_SEED = {
    ".chezmoiroot": "home\n",
    "home/dot_config/zsh/conf.d/personal.zsh": "export PERSONAL=1\n",
    "home/.chezmoiignore": TEST_IGNORES,
}

EXECUTABLE = {"bin/dotfiles"}


@pytest.fixture
def world(tmp_path: Path) -> World:
    return World(tmp_path)
