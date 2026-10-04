# Behavior scenarios

What this repo promises. Each scenario has an automated test in `tests/`. The tests build a
throwaway home folder and throwaway git remotes, so your real config and GitHub are never touched.
Test names match the headings below.

"Base" is the public repo `ckive/dotfiles`. "Overlay" is your private repo (`ckive/dotfiles-personal`,
or `dotfiles-work` on the work laptop). "Sync" is the background job that runs every 5 minutes and
whenever a shell starts.

## Syncing

### 1. Your edits reach GitHub in a single commit
`test_sync_commits_local_edits_in_one_conventional_commit`
- **Given** this machine is in sync
- **When** you change `~/.zshrc`, edit `~/.config/agents/standards.md`, and then the sync runs
- **Then** GitHub gets exactly one new commit containing both changes, titled like
  `chore(sync): macbook: .zshrc, standards.md`

### 1b. Editing the repo directly works too
`test_edit_made_in_the_repo_is_published_not_overwritten`
- **Given** you edit `home/dot_zshrc` in the repo instead of `~/.zshrc`
- **When** the sync runs
- **Then** your edit is pushed and copied to `~/.zshrc`. The old copy in `~` does not overwrite it.

### 1d. Stray files in the repo stay local
`test_stray_file_dropped_in_the_repo_is_not_published`
- **Given** a tool saved its report into the repo folder, e.g. `rmlint.json`
- **When** the sync runs
- **Then** it is not pushed. The sync only publishes config: `home/`, `packages/`, `claude/`,
  `macos/` and `drift-ignore`.

### 1e. Unfinished code edits are neither published nor lost
`test_unfinished_code_edit_in_the_repo_survives_incoming_changes`
- **Given** you are halfway through editing `bin/dotfiles`, and another machine pushed a change
- **When** the sync runs
- **Then** the other machine's change arrives, your edit is untouched, and it isn't pushed.
  Code changes are yours to commit.

### 2. Changes made on another machine arrive here
`test_sync_brings_in_changes_pushed_from_another_machine`
- **Given** the homelab box pushed a new alias in `~/.gitconfig`
- **When** the sync runs on your Mac
- **Then** your Mac's `~/.gitconfig` has the alias. The Mac makes no commit, because the change
  already has one (made on the homelab box). The Mac only downloads it.

### 3. Pull-only machines never push
`test_pull_only_machine_receives_changes_but_never_pushes`
- **Given** dev01 runs in pull-only mode, and an agent there edited `~/.claude/settings.json`
- **When** the sync runs
- **Then** nothing is pushed from dev01, and dev01 still receives new changes from `main`

### 4. A clash never loses work: you choose, then it fixes itself
`test_clash_keeps_local_file_and_waits_for_a_choice`
`test_resolve_keep_mine_publishes_local_version`
`test_resolve_take_theirs_applies_remote_and_saves_local_copy`
`test_resolve_merge_by_hand_opens_editor_then_finishes`
- **Given** you changed line 5 of `.zshrc` on the Mac, and the homelab box changed the same line and
  pushed first
- **When** the sync runs on the Mac
- **Then** your local file is untouched, nothing is force-overwritten, you get a notification, and
  every new shell prints `dotfiles: clash in .zshrc, run: dotfiles resolve`
- **When** you run `dotfiles resolve`, it shows both versions and asks:
  1. **Keep mine.** Your version is committed and pushed to every machine.
  2. **Take theirs.** The other version is applied here, and yours is saved to
     `~/.local/state/dotfiles/conflicts/<date>/.zshrc` in case you want it back.
  3. **Merge by hand.** Your `$EDITOR` opens with both versions marked. When you save, it commits,
     pushes and applies.
- **Then** in every case the sync is healthy again with no further steps

### 5. No internet is not an error
`test_sync_offline_exits_quietly_and_catches_up_later`
- **Given** GitHub is unreachable
- **When** the sync runs
- **Then** it exits silently with your files untouched, and the next sync with a network catches up

### 6. New things stay private until you publish them
`test_new_skill_is_saved_to_private_overlay_not_public_base`
- **Given** Claude or you create `~/.claude/skills/my-new-skill/SKILL.md`
- **When** the sync runs
- **Then** the skill is saved to your private repo, and the public repo is untouched

### 7. Two syncs at once don't collide
`test_second_sync_exits_while_first_is_running`
- **Given** a sync is running (the timer fired)
- **When** another one starts (a new shell)
- **Then** the second exits immediately and the first finishes normally

### 8. Plugins and marketplaces you install follow you
`test_plugin_installed_with_slash_plugin_reaches_other_machines`
`test_plugin_uninstalled_is_removed_on_other_machines`
- **Given** in Claude you run `/plugin marketplace add mattpocock/skills` and install `mattpocock-skills`
- **When** the sync runs on this machine, and later on the homelab box
- **Then** the homelab box's Claude has the marketplace and the plugin enabled (plugin code
  downloads itself)
- **And when** you uninstall it on any machine, it is removed everywhere after the next sync

### 9. User-level MCP servers follow you, but secrets don't
`test_mcp_server_added_on_one_machine_appears_on_others`
`test_mcp_server_with_literal_token_is_not_synced`
- **Given** you run `claude mcp add -s user context7 …`
- **When** the sync runs here and then on another machine
- **Then** the other machine has the same MCP server
- **But** a server whose config contains a literal token (not `${ENV_VAR}`) is never synced, and
  `dotfiles status` tells you which one was skipped and why

## Helper commands

### 10. Publishing something from private to public
`test_promote_moves_file_from_overlay_to_base`
- **Given** `my-new-skill` lives in your private repo (scenario 6)
- **When** you run `dotfiles promote ~/.claude/skills/my-new-skill`
- **Then** it is in the public repo, gone from the private one, and still works in Claude

### 11. Spotting config that isn't tracked
`test_drift_lists_untracked_config_and_skips_junk`
- **Given** a newly installed tool created `~/.config/newtool/config.toml`, next to `~/Music`,
  shell history, SSH keys, caches and empty folders
- **When** you run `dotfiles drift` (it also runs weekly and notifies you)
- **Then** only `.config/newtool` is listed

### 11b. Telling drift a path isn't worth tracking
`test_drift_ignore_hides_a_path_on_every_machine`
- **Given** drift lists `.config/newtool` and you don't want it tracked
- **When** you run `dotfiles drift --ignore .config/newtool`
- **Then** drift stops listing it, on every machine: the path is saved in the private repo's
  `drift-ignore`. Generic patterns (history, caches, keys) are in the public `drift-ignore`.

## Settings files built from public and private parts

### 12. Private settings add to public ones, never replace them
`test_overlay_settings_are_added_to_base_claude_settings`
- **Given** the public base's Claude `settings.json` enables `context7` and allows `Bash(git status)`,
  and your private repo adds the homelab plugins and `Bash(ansible *)`
- **When** chezmoi applies
- **Then** the real `~/.claude/settings.json` has all of them

### 13. Codex's own folder trust survives syncing
`test_codex_trusted_folders_survive_apply`
- **Given** Codex itself recorded "trust `~/Desktop/projects/homelab-infra`" in `~/.codex/config.toml`
- **When** chezmoi applies your synced Codex settings
- **Then** the trust entry is still there, alongside the synced settings

### 14. One skill, every tool
`test_skill_stored_once_is_visible_to_claude_and_codex`
- **Given** `rmsesh` is stored once in `~/.config/agents/skills/rmsesh/`
- **When** chezmoi applies
- **Then** `~/.claude/skills/rmsesh` and `~/.agents/skills/rmsesh` both point at it

## Safety guards (Claude Code hooks)

### 15. Destructive commands are blocked
`test_guard_blocks_destructive_commands_and_allows_safe_variants`
- **When** Claude tries `rm -rf build/`, `git add -A`, `git commit -a`, `git reset --hard`, or
  `git push --force`
- **Then** the command is refused with a reason
- **But** `git push --force-with-lease` and `git add src/main.py` run normally

### 16. Secrets can't be written into config
`test_guard_blocks_token_written_into_tracked_config`
- **When** Claude tries to write a token such as `ghp_…` into `~/.claude/settings.json`
- **Then** the write is blocked before the file changes

## New machine

### 17. A fresh machine becomes yours from one command
`test_fresh_linux_machine_bootstraps_from_install_script` (CI: Debian container, macOS runner)
- **Given** a machine with nothing installed except a shell and `curl`
- **When** you run the one-line install from the README
- **Then** the shell, prompt, git config, Claude/Codex config, skills and dev tools (mise) are all in
  place, and the sync job is scheduled
