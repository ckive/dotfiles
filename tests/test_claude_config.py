"""Scenarios 8-12 of docs/scenarios.md: Claude plugins, MCP servers, promote, drift, settings."""

from __future__ import annotations

import json

PLUGIN = "mattpocock-skills@mattpocock"
MARKETPLACE = "mattpocock"


def settings(machine) -> dict:
    return json.loads(machine.read(".claude/settings.json"))


def install_plugin_with_slash_plugin(machine) -> None:
    """What `/plugin marketplace add` + `/plugin install` write on disk."""
    s = settings(machine)
    s.setdefault("enabledPlugins", {})[PLUGIN] = True
    machine.write(".claude/settings.json", json.dumps(s, indent=2))
    machine.write(
        ".claude/plugins/known_marketplaces.json",
        json.dumps(
            {
                MARKETPLACE: {
                    "source": {"source": "github", "repo": "mattpocock/skills"},
                    "installLocation": str(machine.path(".claude/plugins/marketplaces/mattpocock")),
                },
                "claude-plugins-official": {
                    "source": {"source": "github", "repo": "anthropics/claude-plugins-official"},
                },
            }
        ),
    )


def test_plugin_installed_with_slash_plugin_reaches_other_machines(world):
    """8. Plugins and marketplaces you install follow you."""
    # Given both machines are in sync, and the Mac installs a plugin from a new marketplace
    mac, lab = world.machine("macbook"), world.machine("homelab")
    install_plugin_with_slash_plugin(mac)

    # When the Mac syncs, then the homelab box syncs
    mac.sync()
    lab.sync()

    # Then the homelab box has the marketplace and the plugin enabled, plus the base ones
    s = settings(lab)
    assert s["enabledPlugins"][PLUGIN] is True
    assert s["enabledPlugins"]["context7@claude-plugins-official"] is True
    assert s["extraKnownMarketplaces"][MARKETPLACE]["source"]["repo"] == "mattpocock/skills"
    # and the private choice did not leak into the public base
    assert PLUGIN not in world.base.show("claude/settings.json")


def test_plugin_uninstalled_is_removed_on_other_machines(world):
    """8b. Uninstalling a plugin on any machine removes it everywhere."""
    mac, lab = world.machine("macbook"), world.machine("homelab")
    install_plugin_with_slash_plugin(mac)
    mac.sync()
    lab.sync()
    assert PLUGIN in settings(lab)["enabledPlugins"]

    # When the homelab box uninstalls it, and both sync
    s = settings(lab)
    del s["enabledPlugins"][PLUGIN]
    lab.write(".claude/settings.json", json.dumps(s, indent=2))
    lab.sync()
    mac.sync()

    # Then the Mac no longer has it, and the base plugin is untouched
    assert PLUGIN not in settings(mac)["enabledPlugins"]
    assert settings(mac)["enabledPlugins"]["context7@claude-plugins-official"] is True


def test_runtime_settings_written_by_claude_are_kept(world):
    """8c. Keys Claude writes that no repo manages are left alone by apply."""
    mac = world.machine("macbook")
    s = settings(mac)
    s["feedbackSurveyState"] = {"lastShown": 1}
    mac.write(".claude/settings.json", json.dumps(s))

    mac.sync()

    assert settings(mac)["feedbackSurveyState"] == {"lastShown": 1}


def add_mcp_server(machine, name: str, server: dict) -> None:
    """What `claude mcp add -s user` writes into ~/.claude.json."""
    path = machine.path(".claude.json")
    data: dict = json.loads(path.read_text()) if path.exists() else {"numStartups": 3}
    data.setdefault("mcpServers", {})[name] = server
    path.write_text(json.dumps(data))


def mcp_servers(machine) -> dict:
    path = machine.path(".claude.json")
    return json.loads(path.read_text()).get("mcpServers", {}) if path.exists() else {}


def test_mcp_server_added_on_one_machine_appears_on_others(world):
    """9. User-level MCP servers follow you."""
    mac, lab = world.machine("macbook"), world.machine("homelab")
    server = {"type": "http", "url": "https://mcp.context7.com/mcp"}
    add_mcp_server(mac, "context7", server)

    mac.sync()
    lab.sync()

    assert mcp_servers(lab)["context7"] == server
    # other keys in ~/.claude.json are never touched
    assert json.loads(mac.read(".claude.json"))["numStartups"] == 3


def test_mcp_server_removed_on_one_machine_is_removed_on_others(world):
    """9b. Removing a user MCP server removes it everywhere."""
    mac, lab = world.machine("macbook"), world.machine("homelab")
    add_mcp_server(mac, "context7", {"type": "http", "url": "https://mcp.context7.com/mcp"})
    mac.sync()
    lab.sync()

    data = json.loads(lab.read(".claude.json"))
    del data["mcpServers"]["context7"]
    lab.write(".claude.json", json.dumps(data))
    lab.sync()
    mac.sync()

    assert "context7" not in mcp_servers(mac)


def test_mcp_server_with_literal_token_is_not_synced(world):
    """9c. A server holding a literal token stays on this machine, and status says why."""
    mac = world.machine("macbook")
    add_mcp_server(mac, "github", {"command": "gh-mcp", "env": {"GITHUB_TOKEN": "abc123"}})
    add_mcp_server(mac, "safe", {"command": "x", "env": {"TOKEN": "${MY_TOKEN}"}})

    mac.sync()

    overlay_files = world.overlay.files()
    assert "claude/mcp-servers.json" in overlay_files
    synced = json.loads(world.overlay.show("claude/mcp-servers.json"))
    assert "github" not in synced and "safe" in synced
    status = mac.dotfiles("status")
    assert "github" in status.stdout and "literal" in status.stdout


def test_promote_moves_file_from_overlay_to_base(world):
    """10. Publishing something from private to public."""
    # Given a new skill was saved to the private overlay
    mac = world.machine("macbook")
    mac.write(".claude/skills/my-new-skill/SKILL.md", "---\nname: my-new-skill\n---\nhi\n")
    mac.sync()

    # When it is promoted
    result = mac.dotfiles("promote", str(mac.path(".claude/skills/my-new-skill")))

    # Then it lives in the public base only, and Claude still reads it
    assert result.returncode == 0, result.stdout + result.stderr
    assert any("my-new-skill/SKILL.md" in f for f in world.base.files())
    assert not any("my-new-skill" in f for f in world.overlay.files())
    assert "hi" in mac.read(".claude/skills/my-new-skill/SKILL.md")
    assert world.base.commits()[0].startswith("feat(promote): ")


def test_drift_lists_untracked_config_and_skips_junk(world):
    """11. Spotting config that isn't tracked: only config, not folders, history, keys or caches."""
    # Given a new tool wrote its config, next to the usual non-config clutter in $HOME
    mac = world.machine("macbook")
    mac.write(".config/newtool/config.toml", "x = 1\n")
    mac.write("Music/song.mp3", "x")
    mac.write(".zsh_history", "ls\n")
    mac.write(".ssh/id_ed25519", "key")
    mac.write(".cache/thing/blob", "x")
    mac.write(".claude/projects/abc/session.jsonl", "{}")
    mac.path(".claude/rules").mkdir(parents=True, exist_ok=True)

    # When you run drift
    result = mac.dotfiles("drift")

    # Then only the new tool's config is listed
    assert result.returncode == 0, result.stderr
    assert result.stdout.split() == [".config/newtool"]


def test_drift_ignore_hides_a_path_on_every_machine(world):
    """11b. Telling drift a path isn't worth tracking."""
    # Given drift lists a tool's config you don't want tracked
    mac = world.machine("macbook")
    mac.write(".config/newtool/config.toml", "x = 1\n")

    # When you ignore it and the sync runs
    result = mac.dotfiles("drift", "--ignore", ".config/newtool")
    mac.sync()

    # Then drift no longer lists it, and the choice is saved in the private repo
    assert result.returncode == 0, result.stderr
    assert ".config/newtool" not in mac.dotfiles("drift").stdout
    assert ".config/newtool" in world.overlay.show("drift-ignore")


def test_overlay_settings_are_added_to_base_claude_settings(world):
    """12. Private settings add to public ones, never replace them."""
    # Given the private overlay adds plugins and permissions on top of the base
    mac = world.machine("macbook")
    fragment = mac.overlay_src / "claude" / "settings.json"
    fragment.parent.mkdir(parents=True, exist_ok=True)
    fragment.write_text(
        json.dumps(
            {
                "enabledPlugins": {"ansible-docs@claude-ansible-skills": True},
                "permissions": {"allow": ["Bash(ansible *)"]},
            }
        )
    )

    # When chezmoi applies (via sync)
    mac.sync()

    # Then the live settings hold both sides
    s = settings(mac)
    assert s["enabledPlugins"] == {
        "context7@claude-plugins-official": True,
        "ansible-docs@claude-ansible-skills": True,
    }
    assert s["permissions"]["allow"] == ["Bash(git status)", "Bash(ansible *)"]
