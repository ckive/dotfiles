"""cc-v: launch Claude Code against another Anthropic-compatible provider, per session."""

from __future__ import annotations

import json
import os
import socket
import stat
import subprocess
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

import pytest

REPO = Path(__file__).resolve().parent.parent
CC_V = REPO / "home" / "dot_local" / "bin" / "executable_cc-v"
CC_V_PROXY = REPO / "home" / "dot_local" / "bin" / "executable_cc-v-proxy"
DEEPSEEK_ENV = REPO / "home" / "dot_config" / "cc-v" / "providers" / "deepseek.env"

FAKE_CLAUDE = """#!/usr/bin/env python3
import json, os, sys, urllib.request
dump = {"args": sys.argv[1:], "env": dict(os.environ)}
probe = os.environ.get("CC_V_PROBE")
if probe:
    url = os.environ["ANTHROPIC_BASE_URL"] + "/v1/messages?beta=true"
    headers = {"content-type": "application/json",
               "authorization": "Bearer " + os.environ["ANTHROPIC_AUTH_TOKEN"]}
    req = urllib.request.Request(url, open(probe, "rb").read(), headers)
    with urllib.request.urlopen(req, timeout=10) as resp:
        dump["status"] = resp.status
        dump["reply"] = resp.read().decode()
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
    proxy = bin_dir / "cc-v-proxy"  # repo files aren't +x; chezmoi sets that on install
    proxy.write_text(f'#!/bin/sh\nexec python3 "{CC_V_PROXY}" "$@"\n')
    proxy.chmod(0o755)
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


# --- providers that need a request-fixing proxy (CC_V_PROXY=1), e.g. xAI Grok ---

SSE = b'event: message_start\ndata: {"type":"message_start"}\n\nevent: message_stop\ndata: {}\n\n'

CLAUDE_REQUEST = {
    "model": "grok-4.7",
    "system": [{"type": "text", "text": "You are Claude Code."}],
    "messages": [
        {"role": "user", "content": [{"type": "text", "text": "say pong"}]},
        {"role": "system", "content": [{"type": "text", "text": "<reminder>"}]},
        {"role": "assistant", "content": "ok"},
        {"role": "system", "content": "late reminder"},
    ],
    "tools": [
        {"name": "TaskStop", "input_schema": {"type": "object", "properties": {}}},
        {
            "name": "Bash",
            "input_schema": {
                "type": "object",
                "properties": {"command": {"type": "string"}},
                "required": ["command"],
            },
        },
    ],
    "stream": True,
}


@pytest.fixture
def upstream():
    """A fake xAI that records what reached it and streams back a fixed SSE reply."""
    seen: dict = {}

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            seen["path"] = self.path
            seen["auth"] = self.headers.get("authorization")
            seen["body"] = json.loads(self.rfile.read(int(self.headers["content-length"])))
            self.send_response(200)
            self.send_header("content-type", "text/event-stream")
            self.send_header("content-length", str(len(SSE)))
            self.end_headers()
            self.wfile.write(SSE)

        def log_message(self, format, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    seen["url"] = f"http://127.0.0.1:{server.server_port}"
    yield seen
    server.shutdown()


def proxied_provider(home: Path, upstream: dict) -> None:
    (home / ".config" / "cc-v" / "providers" / "grok.env").write_text(
        f"ANTHROPIC_BASE_URL={upstream['url']}\nANTHROPIC_MODEL=grok-4.7\nCC_V_PROXY=1\n"
    )
    store_key(home, "grok", "xai-test")


def run_grok(home: Path) -> dict:
    probe = home.parent / "request.json"
    probe.write_text(json.dumps(CLAUDE_REQUEST))
    result = cc_v(home, "grok", extra_env={"CC_V_PROBE": str(probe)})
    assert result.returncode == 0, result.stderr
    return launched(home)


def test_proxied_provider_routes_claude_through_a_local_proxy(home, upstream):
    """Given a provider marked CC_V_PROXY=1, claude talks to localhost, not the provider."""
    proxied_provider(home, upstream)

    env = run_grok(home)["env"]

    assert urlparse(env["ANTHROPIC_BASE_URL"]).hostname == "127.0.0.1"
    assert env["ANTHROPIC_BASE_URL"] != upstream["url"]
    assert "CC_V_PROXY" not in env
    assert upstream["path"] == "/v1/messages?beta=true"
    assert upstream["auth"] == "Bearer xai-test"


def test_proxy_folds_system_role_messages_into_user_turns(home, upstream):
    """When claude sends role=system messages, the provider only sees user/assistant turns."""
    proxied_provider(home, upstream)

    run_grok(home)

    messages = upstream["body"]["messages"]
    assert [m["role"] for m in messages] == ["user", "assistant", "user"]
    assert [b["text"] for b in messages[0]["content"]] == ["say pong", "<reminder>"]
    assert messages[2]["content"] == [{"type": "text", "text": "late reminder"}]


def test_proxy_gives_every_tool_schema_a_required_list(home, upstream):
    """When a tool schema has no `required`, the provider sees an empty list; others are kept."""
    proxied_provider(home, upstream)

    run_grok(home)

    schemas = {t["name"]: t["input_schema"] for t in upstream["body"]["tools"]}
    assert schemas["TaskStop"]["required"] == []
    assert schemas["Bash"]["required"] == ["command"]


def test_proxy_streams_the_provider_reply_back_unchanged(home, upstream):
    """The SSE reply from the provider reaches claude byte for byte."""
    proxied_provider(home, upstream)

    dump = run_grok(home)

    assert dump["status"] == 200
    assert dump["reply"] == SSE.decode()


def test_proxy_stops_when_claude_exits(home, upstream):
    """After the session ends, nothing is left listening on the proxy port."""
    proxied_provider(home, upstream)

    port = urlparse(run_grok(home)["env"]["ANTHROPIC_BASE_URL"]).port

    with pytest.raises(ConnectionRefusedError):
        socket.create_connection(("127.0.0.1", port), timeout=2)
