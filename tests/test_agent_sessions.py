"""Agent sessions survive claude dying and dev01 rebooting (HL-31).

agent-session runs claude in the item's tmux window and relaunches it with --continue when it is
killed; agent-dispatch starts sessions only on agent-sessions.service's tmux server, and marks
each live one so `agent-dispatch resume all` brings it back after a boot.
Run: uv run --with pytest pytest tests (harness: conftest.py).
"""

from conftest import ID, Dispatch, Session


def test_session_relaunches_with_continue_when_claude_is_killed(session: Session) -> None:
    # Given a session whose claude is OOM-killed, then exits cleanly after the restart
    session.claude_will("kill", "0")
    # When the session runs
    session.run()
    # Then claude was relaunched with --continue, told why, and asked to say so on the item
    first, second = session.claude_runs()
    assert "--continue" not in first
    assert "--continue" in second and f"--name {ID}: An item" in second
    assert "signal 9" in second and f"comment_item on {ID}" in second
    assert "restarting with --continue" in session.dispatch_log()


def test_session_does_not_relaunch_when_claude_exits_cleanly(session: Session) -> None:
    # Given a session whose claude exits normally (/exit)
    session.claude_will("0")
    # When the session runs
    result = session.run()
    # Then claude ran once, and the session is no longer marked live
    assert len(session.claude_runs()) == 1
    assert result.returncode == 0
    assert not (session.work / "live" / ID).exists()


def test_session_stops_relaunching_after_three_restarts_in_an_hour(session: Session) -> None:
    # Given a claude that crashes every time it starts
    session.claude_will("1", "1", "1", "1", "1")
    # When the session runs
    result = session.run()
    # Then it ran once plus three restarts, then stopped, saying so in the pane and the log
    assert len(session.claude_runs()) == 4
    assert "restart limit reached" in result.stdout
    assert "restart limit reached" in session.dispatch_log()
    # and the pane stays open with that message; the marker stays for the next boot
    assert "remain-on-exit on" in (session.stub / "options.log").read_text()
    assert (session.work / "live" / ID).exists()


def test_dispatch_refuses_to_start_a_tmux_server_of_its_own(dispatch: Dispatch) -> None:
    # Given the only tmux server runs in pfi's cgroup, not agent-sessions.service
    dispatch.server_under("0::/system.slice/pfi.service")
    # When pfi asks for a build
    result = dispatch.run("build", check=False)
    # Then no session starts, and the dispatcher fails with a logged error
    assert result.returncode != 0
    assert dispatch.started() == {}
    assert "agent-sessions.service" in dispatch.dispatch_log()


def test_dispatch_refuses_when_no_tmux_server_runs(dispatch: Dispatch) -> None:
    # Given no tmux server at all (agent-sessions.service is down)
    dispatch.server_under(None)
    # When pfi asks for a build
    result = dispatch.run("build", check=False)
    # Then it fails instead of letting `tmux new-session` start a server under pfi
    assert result.returncode != 0
    assert dispatch.started() == {}


def test_new_session_runs_claude_through_agent_session(dispatch: Dispatch) -> None:
    # Given the agent-sessions server
    # When a build starts a session
    dispatch.run("build")
    # Then claude runs inside the resume wrapper, named after the item
    cmd = dispatch.started()[ID]
    assert "agent-session" in cmd and f"{ID}: An item" in cmd


def test_resume_all_restarts_only_sessions_marked_live(dispatch: Dispatch) -> None:
    # Given two sessions started by dispatch, and a worktree whose session was never marked live
    dispatch.run("build", "HL-1")
    dispatch.run("refine", "HL-2")
    dispatch.worked_on("HL-3")
    # When dev01 reboots and agent-sessions.service runs `resume all`
    dispatch.server_restarted()
    (dispatch.stub / "new.log").unlink()
    dispatch.run("resume", "all")
    # Then exactly the marked sessions come back, with --continue and their names
    started = dispatch.started()
    assert sorted(started) == ["HL-1", "HL-2"]
    assert all("--continue" in cmd for cmd in started.values())
    assert "HL-1: An item" in started["HL-1"]


def test_stopped_session_is_not_resumed_after_boot(dispatch: Dispatch) -> None:
    # Given a session that Dan stopped, and another still live
    dispatch.run("build", "HL-1")
    dispatch.run("build", "HL-2")
    dispatch.run("stop", "HL-1")
    # When dev01 reboots
    dispatch.server_restarted()
    (dispatch.stub / "new.log").unlink()
    dispatch.run("resume", "all")
    # Then only the live one is back
    assert list(dispatch.started()) == ["HL-2"]


def test_pruned_session_is_not_resumed_after_boot(dispatch: Dispatch) -> None:
    # Given a merged item's session that was pruned
    dispatch.run("build", "HL-1")
    dispatch.run("done", "HL-1")
    dispatch.run("prune", "HL-1")
    # When dev01 reboots
    dispatch.server_restarted()
    dispatch.run("resume", "all")
    # Then it stays gone
    assert not (dispatch.work / "live" / "HL-1").exists()
    assert list(dispatch.started()) == ["HL-1"]  # only the original start


def test_resume_skips_a_session_that_is_still_running(dispatch: Dispatch) -> None:
    # Given a live session that is running
    dispatch.run("build")
    # When resume runs anyway
    dispatch.run("resume", "all")
    # Then it isn't started twice
    assert dispatch.received() == [f"start /build {ID}"]


def test_resume_by_hand_works_for_a_session_without_marker(dispatch: Dispatch) -> None:
    # Given an item's worktree whose session predates live markers
    dispatch.worked_on()
    # When Dan runs `agent-dispatch resume <ID>`
    dispatch.run("resume")
    # Then the session starts in that worktree with --continue
    assert "--continue" in dispatch.started()[ID]


def test_dead_pane_counts_as_no_session(dispatch: Dispatch) -> None:
    # Given a session whose wrapper hit the restart limit (pane kept, process dead)
    dispatch.session_running()
    (dispatch.stub / "sessions" / ID).write_text("1\n")
    # When Dan comments
    dispatch.run("comment", comment="carry on")
    # Then a session is started, rather than text pasted into a dead pane
    [msg] = dispatch.received()
    assert msg.startswith(f"start Resume {ID} ")
