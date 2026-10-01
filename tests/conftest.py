"""Harness for agent-dispatch and agent-session: the scripts run for real against stubs on PATH.

Run: uv run --with pytest pytest tests
The tmux stub keeps one file per session in $STUB/sessions and records what a session receives
in $STUB/tmux.log: `paste <text>` for each pasted message and `start <prompt>` for a new one.
Each new session's name and full command also go to $STUB/new.log. The tmux server runs under
agent-sessions.service unless a test says otherwise (a fake /proc gives its cgroup).
"""

import json
import os
import shlex
import subprocess
import time
from pathlib import Path

import pytest

BIN = Path(__file__).parents[1] / "private_dot_local/bin"
DISPATCH = BIN / "executable_agent-dispatch"
SESSION = BIN / "executable_agent-session"
ID = "HL-99"
SERVER_PID = "4242"

TMUX = r"""#!/usr/bin/env bash
log=$STUB/tmux.log s=$STUB/sessions
mkdir -p "$s"
# The session a `-t =name[:]` target or `-s name` names.
arg() { while [ $# -gt 1 ]; do [ "$1" = "$flag" ] && { t=${2#=}; printf '%s' "${t%%:*}"; return; }; shift; done; }
target() { flag=-t arg "$@"; }
case $1 in
  has-session) [ -e "$s/$(target "$@")" ] ;;
  new-session) # the last arg is the shell command; its last word is claude's prompt
    n=$(flag=-s arg "$@"); touch "$s/$n"
    printf 'new %s %s\n' "$n" "${@: -1}" >>"$STUB/new.log"
    eval "set -- ${@: -1}"; printf 'start %s\n' "${@: -1}" >>"$log" ;;
  display-message)
    case ${@: -1} in
      '#{pid}') [ -e "$STUB/server" ] && echo "$SERVER_PID" ;;
      '#{pane_dead}') [ -e "$s/$(target "$@")" ] && cat "$s/$(target "$@")" ;;
    esac ;;
  capture-pane) [ -e "$s/$(target "$@")" ] && printf '\n❯ \n' ;;
  set-buffer) printf '%s' "${@: -1}" >"$STUB/buffer" ;;
  paste-buffer) printf 'paste %s\n' "$(cat "$STUB/buffer")" >>"$log" ;;
  set-option) printf 'set-option %s\n' "$*" >>"$STUB/options.log" ;;
  send-keys) : ;;
  kill-session) rm -f "$s/$(target "$@")" ;;
esac
"""

GIT = """#!/usr/bin/env bash
# `worktree add` creates the worktree's directory; everything else succeeds silently.
if [[ " $* " == *" worktree add "* ]]; then
  for a; do [[ $a == "$AGENT_WORK_DIR"/wt/* ]] && mkdir -p "$a"; done
fi
exit 0
"""

# Each run takes the next line of $STUB/claude.plan: an exit status, or `kill` (SIGKILL itself).
CLAUDE = r"""#!/usr/bin/env bash
printf '%s\n' "$*" >>"$STUB/claude.log"
step=$(head -n1 "$STUB/claude.plan"); sed -i 1d "$STUB/claude.plan"
[ "$step" = kill ] && kill -9 $$
exit "${step:-0}"
"""


class Stubs:
    def __init__(self, tmp: Path) -> None:
        self.tmp = tmp
        self.work = tmp / "work"
        self.stub = tmp / "stub"
        (self.stub / "bin").mkdir(parents=True)
        (self.stub / "sessions").mkdir()
        for name, body in {"tmux": TMUX, "git": GIT, "claude": CLAUDE}.items():
            path = self.stub / "bin" / name
            path.write_text(body)
            path.chmod(0o755)
        (self.work / "homelab__repo" / ".git").mkdir(parents=True)
        self.env = os.environ | {
            "PATH": f"{self.stub / 'bin'}:{os.environ['PATH']}",
            "HOME": str(tmp),
            "STUB": str(self.stub),
            "SERVER_PID": SERVER_PID,
            "AGENT_WORK_DIR": str(self.work),
            "AGENT_READY_POLL": "0.1",
            "AGENT_PROC": str(tmp / "proc"),
            "AGENT_SESSION_BIN": str(SESSION),
            "AGENT_RESTART_DELAY": "0",
        }
        self.server_under("0::/agents.slice/agent-sessions.service")

    def server_under(self, cgroup: str | None) -> None:
        """The tmux server runs in `cgroup`; None: no server at all."""
        (self.stub / "server").unlink(missing_ok=True)
        if cgroup is None:
            return
        (self.stub / "server").touch()
        proc = self.tmp / "proc" / SERVER_PID
        proc.mkdir(parents=True, exist_ok=True)
        (proc / "cgroup").write_text(cgroup + "\n")

    def dispatch_log(self) -> str:
        path = self.work / "dispatch.log"
        return path.read_text() if path.exists() else ""


class Dispatch(Stubs):
    def session_running(self, sess: str = ID) -> None:
        (self.stub / "sessions" / sess).write_text("0\n")
        self.worked_on(sess)

    def worked_on(self, wt: str = ID) -> None:
        (self.work / "wt" / wt).mkdir(parents=True, exist_ok=True)

    def server_restarted(self) -> None:
        """Every session is gone, as after a reboot; live markers and worktrees stay."""
        for s in (self.stub / "sessions").iterdir():
            s.unlink()

    def run(
        self, job: str, item: str = ID, *, comment: str = "", description: str = "", check: bool = True
    ) -> subprocess.CompletedProcess[str]:
        payload = {
            "event": {"repo": "homelab/repo", "context": {"comment": {"text": comment}}},
            "items": [{"name": "An item", "description": description}],
        }
        return subprocess.run(
            ["bash", str(DISPATCH), job, item],
            input=json.dumps(payload),
            env=self.env,
            capture_output=True,
            text=True,
            check=check,
            timeout=30,
        )

    def received(self, expect: int = 0) -> list[str]:
        """Each message a session got, in order; waits for `expect` of them (background pastes)."""
        log = self.stub / "tmux.log"
        deadline = time.monotonic() + 10
        while True:
            text = log.read_text() if log.exists() else ""
            msgs = [m for m in text.split("\n") if m.startswith(("paste ", "start "))]
            if len(msgs) >= expect or time.monotonic() > deadline:
                return _messages(text)
            time.sleep(0.1)

    def started(self) -> dict[str, str]:
        """Each new tmux session: name → its shell command, unquoted."""
        log = self.stub / "new.log"
        lines = log.read_text().splitlines() if log.exists() else []
        return {n: " ".join(shlex.split(cmd)) for n, _, cmd in (line.removeprefix("new ").partition(" ") for line in lines)}


class Session(Stubs):
    def claude_will(self, *steps: str) -> None:
        (self.stub / "claude.plan").write_text("".join(f"{s}\n" for s in steps))

    def run(self, sess: str = ID) -> subprocess.CompletedProcess[str]:
        live = self.work / "live"
        live.mkdir(parents=True, exist_ok=True)
        (live / sess).write_text(f"{self.work}/wt/{sess}\n{sess}: An item\n")
        return subprocess.run(
            ["bash", str(SESSION), sess, ID, "--name", f"{sess}: An item", "/build " + ID],
            env=self.env,
            capture_output=True,
            text=True,
            timeout=30,
        )

    def claude_runs(self) -> list[str]:
        log = self.stub / "claude.log"
        return log.read_text().splitlines() if log.exists() else []


def _messages(text: str) -> list[str]:
    """Split the log into messages; a multi-line paste continues until the next record."""
    out: list[str] = []
    for line in text.splitlines():
        if line.startswith(("paste ", "start ")):
            out.append(line)
        elif out:
            out[-1] += "\n" + line
    return out


@pytest.fixture
def dispatch(tmp_path: Path) -> Dispatch:
    return Dispatch(tmp_path)


@pytest.fixture
def session(tmp_path: Path) -> Session:
    return Session(tmp_path)
