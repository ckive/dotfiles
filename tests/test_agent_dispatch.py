"""agent-dispatch delivers Dan's slash commands to an item's Claude Code session as typed.

Run: uv run --with pytest pytest tests (harness: conftest.py).
"""

from conftest import ID, Dispatch


def test_comment_starting_with_slash_is_pasted_verbatim(dispatch: Dispatch) -> None:
    # Given a running session
    dispatch.session_running()
    # When Dan comments a slash command on Plane
    dispatch.run("comment", comment="  /goal all behaviour tests pass\nand CI is green")
    # Then the session receives exactly that command, nothing else
    assert dispatch.received() == ["paste /goal all behaviour tests pass\nand CI is green"]


def test_slack_reply_with_slash_command_drops_author_prefix(dispatch: Dispatch) -> None:
    # Given a running session, and a Slack reply pfi relayed as "<author> (slack): <text>"
    dispatch.session_running()
    # When the reply had a leading space so Slack would post it
    dispatch.run("comment", comment="Dan Yang (slack):  /goal clear")
    # Then the session receives the bare command
    assert dispatch.received() == ["paste /goal clear"]


def test_backticked_command_is_unwrapped_and_pasted_verbatim(dispatch: Dispatch) -> None:
    # Given a running session
    dispatch.session_running()
    # When Dan wraps the command in backticks
    dispatch.run("comment", comment="Dan Yang (slack): `/compact`")
    # Then the session receives the command without them
    assert dispatch.received() == ["paste /compact"]


def test_comment_without_leading_slash_keeps_dan_commented_wrapper(dispatch: Dispatch) -> None:
    # Given a running session
    dispatch.session_running()
    # When Dan comments prose that merely mentions a command
    dispatch.run("comment", comment="Dan Yang (slack): use /goal later")
    # Then it arrives wrapped, as before
    [msg] = dispatch.received()
    assert msg.startswith("paste Dan commented on Plane: Dan Yang (slack): use /goal later\n")


def test_command_reaches_session_that_was_not_running_after_resume(dispatch: Dispatch) -> None:
    # Given an item an agent worked on, whose session has ended
    dispatch.worked_on()
    # When Dan comments a slash command
    dispatch.run("comment", comment="/goal the PR is open")
    # Then the session resumes first, then receives the command as typed
    start, paste = dispatch.received(expect=2)
    assert start.startswith(f"start Resume {ID} ")
    assert "Dan commented" not in start
    assert paste == "paste /goal the PR is open"


def test_command_for_item_without_agent_is_ignored(dispatch: Dispatch) -> None:
    # Given an item no agent has worked on
    # When Dan comments a slash command
    out = dispatch.run("comment", comment="/goal anything").stdout
    # Then nothing reaches a session
    assert dispatch.received() == []
    assert "comment ignored" in out


def test_description_goal_is_pasted_before_build(dispatch: Dispatch) -> None:
    # Given a running session (from refine) and a /goal line in the description
    dispatch.session_running()
    # When the build starts
    dispatch.run("build", description="Make it fast.\n  /goal p95 under 200 ms\nThanks")
    # Then the goal is set first, then /build runs
    assert dispatch.received() == ["paste /goal p95 under 200 ms", f"paste /build {ID}"]


def test_description_goal_reaches_new_build_session_once_ready(dispatch: Dispatch) -> None:
    # Given no session yet and a /goal line in the description
    dispatch.worked_on()
    # When the build starts
    dispatch.run("build", description="/goal all checks pass")
    # Then the session starts with /build and gets the goal as soon as it is ready
    assert dispatch.received(expect=2) == [f"start /build {ID}", "paste /goal all checks pass"]


def test_description_goal_is_not_applied_during_refine(dispatch: Dispatch) -> None:
    # Given a running session and a /goal line in the description
    dispatch.session_running()
    # When the item is refined
    dispatch.run("refine", description="/goal all checks pass")
    # Then only /refine arrives
    assert dispatch.received() == [f"paste /refine {ID}"]
