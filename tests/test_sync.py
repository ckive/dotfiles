"""Scenarios 1-7 of docs/scenarios.md: the background sync."""

from __future__ import annotations

import json


def test_sync_commits_local_edits_in_one_conventional_commit(world):
    """1. Your edits reach GitHub in a single commit."""
    # Given a machine that is in sync
    mac = world.machine("macbook")
    before = len(world.base.commits())

    # When two tracked files change and the sync runs
    mac.write(".zshrc", mac.read(".zshrc") + "alias ll='ls -l'\n")
    mac.write(".config/agents/standards.md", mac.read(".config/agents/standards.md") + "- test\n")
    mac.sync()

    # Then the remote has exactly one new commit holding both, with a conventional subject
    commits = world.base.commits()
    assert len(commits) == before + 1
    assert commits[0].startswith("chore(sync): macbook: ")
    assert ".zshrc" in commits[0] and "standards.md" in commits[0]
    assert "alias ll" in world.base.show("home/dot_zshrc")
    assert "- test" in world.base.show("home/dot_config/agents/standards.md")


def test_edit_made_in_the_repo_is_published_not_overwritten(world):
    """1b. Editing the repo directly works too: the sync publishes it and applies it."""
    # Given you edit the source file in the repo instead of the file in $HOME
    mac = world.machine("macbook")
    src = mac.base_src / "home" / "dot_zshrc"
    src.write_text(src.read_text() + "alias from_repo=1\n")

    # When the sync runs
    mac.sync()

    # Then the edit is on GitHub and in $HOME, not reverted to the old $HOME copy
    assert "alias from_repo=1" in world.base.show("home/dot_zshrc")
    assert "alias from_repo=1" in mac.read(".zshrc")


def test_sync_brings_in_changes_pushed_from_another_machine(world):
    """2. Changes made on another machine arrive here, without a commit from this one."""
    # Given the homelab box pushed a new git alias
    mac = world.machine("macbook")
    lab = world.machine("homelab")
    lab.write(".gitconfig", lab.read(".gitconfig") + "\tco = checkout\n")
    lab.sync()
    commits_after_lab = world.base.commits()

    # When the Mac syncs
    mac.sync()

    # Then the Mac has the alias and made no commit of its own
    assert "co = checkout" in mac.read(".gitconfig")
    assert world.base.commits() == commits_after_lab


def test_pull_only_machine_receives_changes_but_never_pushes(world):
    """3. Pull-only machines never push."""
    # Given dev01 is pull-only and an agent there edited a tracked file
    mac = world.machine("macbook")
    dev01 = world.machine("dev01", mode="pull")
    dev01.write(".gitconfig", "[alias]\n\tagent = edit\n")
    base_before, overlay_before = world.base.commits(), world.overlay.commits()

    # When dev01 syncs
    dev01.sync()

    # Then nothing was pushed from dev01
    assert world.base.commits() == base_before
    assert world.overlay.commits() == overlay_before

    # And when the Mac pushes a change, dev01 still receives it
    mac.write(".zshrc", mac.read(".zshrc") + "alias from_mac=1\n")
    mac.sync()
    dev01.sync()
    assert "alias from_mac=1" in dev01.read(".zshrc")


def _make_clash(world):
    """Mac and homelab edit the same line; homelab pushes first; Mac syncs into a clash."""
    mac = world.machine("macbook")
    lab = world.machine("homelab")
    lab.write(".zshrc", "export EDITOR=vim\nalias gs='git status'\n")
    lab.sync()
    mac.write(".zshrc", "export EDITOR=hx\nalias gs='git status'\n")
    mac.sync()
    return mac, lab


def test_clash_keeps_local_file_and_waits_for_a_choice(world):
    """4. A clash never loses work: local file untouched, user told what to run."""
    # Given/When the Mac syncs a change that clashes with one already pushed
    mac, _ = _make_clash(world)

    # Then the local file is untouched and nothing was force-pushed over the other change
    assert mac.read(".zshrc").startswith("export EDITOR=hx")
    assert "export EDITOR=vim" in world.base.show("home/dot_zshrc")

    # And the user is notified, and status explains what to run
    assert "dotfiles resolve" in mac.notifications()
    status = mac.dotfiles("status")
    assert status.returncode == 1
    assert ".zshrc" in status.stdout and "dotfiles resolve" in status.stdout

    # And the shell banner says so too
    banner = mac.dotfiles("status", "--banner")
    assert "clash in .zshrc" in banner.stdout


def test_resolve_keep_mine_publishes_local_version(world):
    """4a. Keep mine: local version is pushed to every machine."""
    mac, lab = _make_clash(world)

    result = mac.dotfiles("resolve", "--choice", "mine")

    assert result.returncode == 0, result.stdout + result.stderr
    assert "export EDITOR=hx" in world.base.show("home/dot_zshrc")
    assert mac.dotfiles("status").returncode == 0
    lab.sync()
    assert lab.read(".zshrc").startswith("export EDITOR=hx")


def test_resolve_take_theirs_applies_remote_and_saves_local_copy(world):
    """4b. Take theirs: remote version applied here, local copy kept aside."""
    mac, _ = _make_clash(world)

    result = mac.dotfiles("resolve", "--choice", "theirs")

    assert result.returncode == 0, result.stdout + result.stderr
    assert mac.read(".zshrc").startswith("export EDITOR=vim")
    saved = list(mac.path(".local/state/dotfiles/conflicts").rglob(".zshrc"))
    assert len(saved) == 1 and saved[0].read_text().startswith("export EDITOR=hx")
    assert mac.dotfiles("status").returncode == 0


def test_resolve_merge_by_hand_opens_editor_then_finishes(world):
    """4c. Merge by hand: $EDITOR opens with both versions; saving finishes everything."""
    mac, lab = _make_clash(world)
    editor = mac.path("fake-editor.sh")
    editor.write_text(
        "#!/bin/sh\n"
        "grep -q '<<<<<<<' \"$1\" || exit 1\n"
        "printf \"export EDITOR=nvim\\nalias gs='git status'\\n\" > \"$1\"\n"
    )
    editor.chmod(0o755)
    mac.env["EDITOR"] = str(editor)

    result = mac.dotfiles("resolve", "--choice", "merge")

    assert result.returncode == 0, result.stdout + result.stderr
    assert mac.read(".zshrc").startswith("export EDITOR=nvim")
    assert "export EDITOR=nvim" in world.base.show("home/dot_zshrc")
    lab.sync()
    assert lab.read(".zshrc").startswith("export EDITOR=nvim")


def test_sync_offline_exits_quietly_and_catches_up_later(world):
    """5. No internet is not an error."""
    # Given GitHub is unreachable
    mac = world.machine("macbook")
    hidden = world.offline(world.base)

    # When the user edits a file and the sync runs
    mac.write(".zshrc", mac.read(".zshrc") + "alias offline=1\n")
    result = mac.sync()

    # Then it exits quietly with the file untouched and no clash recorded
    assert result.stderr == ""
    assert "alias offline=1" in mac.read(".zshrc")
    assert mac.dotfiles("status").returncode == 0

    # And the next sync with a network catches up
    world.online(world.base, hidden)
    mac.sync()
    assert "alias offline=1" in world.base.show("home/dot_zshrc")


def test_new_skill_is_saved_to_private_overlay_not_public_base(world):
    """6. New things stay private until you publish them."""
    # Given Claude creates a new skill
    mac = world.machine("macbook")
    base_before = world.base.commits()
    mac.write(".claude/skills/my-new-skill/SKILL.md", "---\nname: my-new-skill\n---\nhi\n")

    # When the sync runs
    mac.sync()

    # Then it is in the private overlay, the public base is untouched,
    # and Claude still reads it at the same path
    assert any("my-new-skill/SKILL.md" in f for f in world.overlay.files())
    assert world.base.commits() == base_before
    assert "hi" in mac.read(".claude/skills/my-new-skill/SKILL.md")

    # And another machine gets it
    lab = world.machine("homelab")
    assert "hi" in lab.read(".claude/skills/my-new-skill/SKILL.md")


def test_second_sync_exits_while_first_is_running(world):
    """7. Two syncs at once don't collide."""
    # Given a sync holds the lock
    mac = world.machine("macbook")
    lock = mac.path(".local/state/dotfiles/sync.lock")
    lock.mkdir(parents=True)
    (lock / "pid").write_text(json.dumps({"pid": 1}))
    before = world.base.commits()

    # When another sync starts with a pending edit
    mac.write(".zshrc", mac.read(".zshrc") + "alias locked=1\n")
    result = mac.sync()

    # Then it exits immediately without committing
    assert "already running" in result.stdout
    assert world.base.commits() == before
