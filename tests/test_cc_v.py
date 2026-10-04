"""cc-v: launch Claude Code against another Anthropic-compatible provider, per session."""

from __future__ import annotations

import json
import os
import stat
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
CC_V = REPO / "home" / "dot_local" / "bin" / "executable_cc-v"
DEEPSEEK_ENV = REPO / "home" / "dot_config" / "cc-v" / "providers" / "deepseek.env"

FAKE_CLAUDE = """#!/usr/bin/env python3
import json, os, sys
dump = {"args": sys.argv[1:], "env": dict(os.environ)}
json.dump(dump, open(os.environ["CC_V_DUMP"], "w"))
"""


@pytest.fixture
def home(tmp_path: Path) -> Path:
    """A $HOME with the repo's deepseek provider and a fake `claude` that records how it ran."""
    h = tmp_path / "home"
    providers = h / ".config" / "cc-v" / "providers"
    providers.mkdir(parents=True)
    (providers / "deepseek.env").write_text(DEEPSEEK_ENV.read_text())
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    fake = bin_dir / "claude"
    fake.write_text(FAKE_CLAUDE)
    fake.chmod(0o755)
    return h


def cc_v(home: Path, *args: str, stdin: str = "", extra_env: dict | None = None):
    env = {
        "HOME": str(home),
        "PATH": f"{home.parent / 'bin'}:/usr/bin:/bin",
        "CC_V_DUMP": str(home.parent / "dump.json"),
        **(extra_env or {}),
    }
    return subprocess.run(
        ["bash", str(CC_V), *args], env=env, input=stdin, capture_output=True, text=True
    )


def launched(home: Path) -> dict:
    return json.loads((home.parent / "dump.json").read_text())


def store_key(home: Path, provider: str, key: str) -> None:
    secret = home / ".config" / "cc-v" / f"{provider}.secret"
    secret.write_text(key + "\n")
    secret.chmod(0o600)


def test_launches_claude_with_provider_env_and_key(home):
    """Given a deepseek key is stored, `cc-v deepseek` runs claude pointed at DeepSeek."""
    store_key(home, "deepseek", "sk-test")

    result = cc_v(home, "deepseek")

    assert result.returncode == 0, result.stderr
    env = launched(home)["env"]
    assert env["ANTHROPIC_BASE_URL"] == "https://api.deepseek.com/anthropic"
    assert env["ANTHROPIC_AUTH_TOKEN"] == "sk-test"
    assert env["ANTHROPIC_MODEL"] == "deepseek-flash[1m]"
    assert env["CLAUDE_CODE_SUBAGENT_MODEL"] == "deepseek-flash"


def test_passes_extra_args_through_to_claude(home):
    """Given a stored key, args after the provider reach claude unchanged."""
    store_key(home, "deepseek", "sk-test")

    cc_v(home, "deepseek", "-p", "say hi; $(rm -rf /)")

    assert launched(home)["args"] == ["-p", "say hi; $(rm -rf /)"]


def test_drops_anthropic_api_key_when_switching_provider(home):
    """Given an Anthropic key in the shell, it never reaches the other provider."""
    store_key(home, "deepseek", "sk-test")

    cc_v(home, "deepseek", extra_env={"ANTHROPIC_API_KEY": "sk-ant-secret"})

    assert "ANTHROPIC_API_KEY" not in launched(home)["env"]


def test_refuses_to_launch_when_key_missing(home):
    """Given no stored key, cc-v exits non-zero and says how to add one."""
    result = cc_v(home, "deepseek")

    assert result.returncode != 0
    assert "cc-v set-key deepseek" in result.stderr
    assert not (home.parent / "dump.json").exists()


def test_refuses_unknown_provider(home):
    """Given no provider file named `nope`, cc-v exits non-zero and lists known providers."""
    result = cc_v(home, "nope")

    assert result.returncode != 0
    assert "deepseek" in result.stderr
    assert not (home.parent / "dump.json").exists()


def test_list_shows_which_providers_have_keys(home):
    """Given two providers with only one key stored, `list` marks which is ready."""
    (home / ".config" / "cc-v" / "providers" / "other.env").write_text("ANTHROPIC_BASE_URL=x\n")
    store_key(home, "deepseek", "sk-test")

    out = cc_v(home, "list").stdout

    assert "deepseek" in out and "key stored" in out
    assert "other" in out and "no key" in out


def test_set_key_writes_owner_only_secret(home):
    """When a key is entered at the prompt, it's stored readable by the owner only."""
    result = cc_v(home, "set-key", "deepseek", stdin="sk-new\n")

    assert result.returncode == 0, result.stderr
    secret = home / ".config" / "cc-v" / "deepseek.secret"
    assert secret.read_text().strip() == "sk-new"
    assert stat.S_IMODE(os.stat(secret).st_mode) == 0o600
