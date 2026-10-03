# Windows + WSL setup: brief for an agent

You are setting up Dan's work laptop (Windows with WSL) from this repo. Work through the steps in
order and stop to ask Dan wherever it says **ASK**. Finish by filling in the acceptance checklist
and reporting it.

## Ground rules
- **ASK first:** does company policy allow cloning a public GitHub repo onto this laptop? If not, stop.
- The work overlay lives on company git. **Never push anything from this laptop to `ckive/*` repos.**
  Run the base in `pull` mode here. The work overlay may run in `push` mode.
- Read `README.md` and `docs/scenarios.md` first. Changes to `bin/dotfiles` follow the repo's
  rules: behavior test first (shown failing), then code, then `just check` green.

## 1. WSL (Linux side)
1. Use WSL 2 with a Debian or Ubuntu distro. Turn on systemd if it's off: put `[boot]` and
   `systemd=true` in `/etc/wsl.conf`, then run `wsl --shutdown` from Windows. **ASK** before
   changing `/etc/wsl.conf`.
2. Create the work overlay:
   1. Copy `docs/overlay-template/` into a new private repo on company git.
   2. **ASK** Dan for the work git identity and work MCP servers, and fill in the template.
   3. Push it.
3. Run from inside WSL:
   ```bash
   DOTFILES_MODE=pull DOTFILES_OVERLAY=work DOTFILES_OVERLAY_URL=<company-git-url> \
     sh -c "$(curl -fsSL https://raw.githubusercontent.com/ckive/dotfiles/main/install.sh)"
   ```
   Note: `pull` mode applies to the base and the overlay alike today. If Dan wants the work
   overlay to push, that's step 3 below.
4. Check:
   - `dotfiles status` exits 0.
   - `systemctl --user list-timers` shows `dotfiles-sync.timer`. If systemd is off, the sync
     still runs at each zsh start.
   - `claude` shows the shared standards in `/memory`.

## 2. Windows side, applied from WSL
Dan wants one chezmoi install, in WSL. Add a **Windows instance** that writes into the Windows
home from WSL:

1. **Source:** a new `windows/` directory in this repo, used directly as that instance's
   `sourceDir`. Do not put it under `home/`, so the Linux instance never sees it. Contents:
   - AutoHotkey scripts →
     `windows/AppData/Roaming/Microsoft/Windows/Start Menu/Programs/Startup/*.ahk`
     (they run at login). **ASK** Dan for the scripts.
   - PowerShell profile → `windows/Documents/PowerShell/Microsoft.PowerShell_profile.ps1`
   - Windows Terminal → `windows/AppData/Local/Packages/Microsoft.WindowsTerminal_8wekyb3d8bbwe/LocalState/settings.json`
   - `winget export -o packages/winget.json` from the current machine, and a
     `run_onchange_` script in `windows/` that runs `winget.exe import` through `cmd.exe /c`
2. **Instance config** `~/.config/chezmoi/windows.toml`:
   - `sourceDir = "<base>/windows"`
   - `destDir` = the Windows home:
     `wslpath "$(cmd.exe /c 'echo %USERPROFILE%' | tr -d '\r')"`
   - `[data] target = "windows"`
3. **Template caveats:**
   - `.chezmoi.os` reports `linux` inside WSL, so branch on `.target`.
   - Use `.chezmoi.destDir`, never `.chezmoi.homeDir`, for Windows paths.
   - Put `# chezmoi:template:line-endings=crlf` in templates whose output Windows tools need as CRLF.
   - No `symlink_`, `private_` or `executable_` in `windows/`: drvfs ignores modes, and Windows
     apps can't follow WSL symlinks.
4. **Teach `bin/dotfiles` about it**, test first. Config key `windows = true` adds an instance
   with `--config ~/.config/chezmoi/windows.toml` plus its own `--persistent-state` and
   `--cache`. That instance shares the base git repo, so git operations must run **once per
   repo**, not once per instance. Scenarios to add to `docs/scenarios.md` and `tests/`:
   - `test_windows_instance_applies_into_windows_home`
   - `test_windows_instance_shares_base_repo_without_double_commits`
   - `test_edit_on_windows_side_is_captured` (e.g. an `.ahk` edited in Windows)
5. **If drvfs causes trouble** (slow, permission diffs that won't go away): stop and **ASK**.
   The fallback is a native `chezmoi.exe` on Windows using the same repo, scheduled with Task
   Scheduler.

## 3. Optional: push mode for the work overlay only
If Dan wants edits on this laptop saved to the **work** overlay (never the public base), add a
per-instance mode, for example `[modes] base = "pull"`, `work = "push"`. Add a test that proves
the base never receives a push from this machine.

## Acceptance checklist (report back)
- [ ] Policy check answered by Dan: ______
- [ ] WSL: `dotfiles status` = 0; timer or shell-start sync confirmed
- [ ] New zsh in WSL shows the p10k prompt; `gs`, `cz` and `lllm status` work
- [ ] Claude in WSL: `/memory` lists the standards and the work overlay; `/skills` lists `rmsesh`
- [ ] Work MCP servers present (`claude mcp list`)
- [ ] Windows: AutoHotkey scripts run after a reboot; PowerShell profile loads; Windows Terminal settings applied
- [ ] Editing an `.ahk` on Windows shows up as a commit in the right repo after one sync
- [ ] `just check` green with the new scenarios
- [ ] Nothing pushed to `ckive/*` from this laptop (`git log` of the base checkout shows no local commits)
