# Work laptop (Windows + WSL): setup brief

For an agent running **inside WSL** on Dan's work laptop, with Dan at the keyboard. Do the steps
in order. Stop and ask Dan wherever it says **ASK**. Finish by filling in the checklist at the end
and reporting it. The [publishing](#publishing-to-the-public-repo-from-the-work-laptop) section
is for Dan only.

## What exists and what you build

| Part | State |
|---|---|
| WSL side: bash, git, mise tools, Claude/Codex config, background sync | **Done.** `install.sh`, tested in CI on a fresh Debian 13 |
| Work overlay (private repo on company git) | You create it from `docs/overlay-template/` (step 2) |
| Windows side: AutoHotkey, PowerShell, Windows Terminal, VS Code, winget | **You build it** (step 4) |

On Linux, WSL included, nothing macOS-only runs:

| macOS thing | On WSL |
|---|---|
| Homebrew, `packages/Brewfile` | not used. apt installs `packages/apt.txt`; mise installs dev tools |
| macOS defaults script, Rectangle | the script renders empty off macOS |
| launchd job, `~/Library/**` | `~/Library` is ignored off macOS; a systemd user timer runs the sync instead |
| VS Code extensions script | skips itself in WSL (VS Code runs on Windows; step 4 installs them) |
| zsh config (`.zshrc`, oh-my-zsh, p10k), `kitty.conf` | copied but unused: WSL stays on bash, its default shell |

## Rules

1. **ASK first:** does company policy allow cloning a public GitHub repo (`ckive/dotfiles`) onto
   this laptop? If not, stop.
2. **Never push to `ckive/*`.** Never run `git push` in `~/dotfiles`, and never run
   `dotfiles publish` (the guard hook blocks it; only Dan publishes).
3. **Work-specific content goes only into the work overlay** (`~/dotfiles-work`, company git):
   hostnames, proxies, identities, internal URLs, work MCP servers. Never into `~/dotfiles`.
4. **No secrets in any repo.** Tokens stay in env vars or files outside the repos; MCP configs
   reference them as `${VAR}`.
5. **Changes to `bin/dotfiles`** (step 4.4) follow this repo's rules: write the behavior test
   first and show it failing, then implement, then `just check` must pass. Work in a separate
   worktree (step 4.4), never on `~/dotfiles` itself, which the sync manages.

## 0. Save the laptop's existing config first

The first sync replaces existing files with the repo versions (scenario 1c). Company lines in
them must move to the work overlay **before** installing, or they're lost.

1. Back up:
   ```bash
   tar czf ~/pre-dotfiles-$(date +%F).tgz --ignore-failed-read -C ~ \
     .zshrc .zprofile .bashrc .profile .gitconfig .ssh/config .p10k.zsh \
     .claude/settings.json .claude/CLAUDE.md .codex/config.toml .codex/AGENTS.md
   ```
2. Read each of those files. List every company-specific line: proxies, internal hosts, PATHs
   for company tools, git identity / URL rewrites / credential helpers, Claude or Codex
   settings, MCP servers. **ASK** Dan about anything unclear.
3. Carry the list into step 2.3.

Later, if a company tool runs `git config --global …`, it writes to `~/.gitconfig`, which the
sync puts back within 5 minutes. Move such settings into the overlay's `overlay.gitconfig`.

## 1. WSL prerequisites

1. `wsl.exe -l -v` (from WSL or Windows) shows the distro with `VERSION 2`. Debian or Ubuntu.
2. systemd: `cat /etc/wsl.conf` should contain:
   ```ini
   [boot]
   systemd=true
   ```
   If it doesn't, **ASK**, then add it with `sudo`, and have Dan run `wsl --shutdown` in
   PowerShell and reopen the terminal. Without systemd the sync still runs each time a terminal opens
   (throttled to every 5 minutes), just not in the background.
3. WSL can reach company git: `git ls-remote <work-repo-url>` works (set up an ssh key or
   credential helper first if needed; **ASK** which).
4. Dan creates an empty private repo on company git for the overlay, e.g. `dotfiles-work`, and
   gives you its URL.

## 2. Create the work overlay

```bash
git clone https://github.com/ckive/dotfiles.git ~/dotfiles   # install.sh reuses this checkout
cp -r ~/dotfiles/docs/overlay-template ~/dotfiles-work         # install.sh expects this path
cd ~/dotfiles-work
rm packages/Brewfile                                            # macOS only
```

Fill it in from the step 0 list:

| File | Put here |
|---|---|
| `home/dot_config/shell/conf.d/work.sh` | proxies, PATHs, env vars, company shell setup (POSIX sh; bash and zsh both load it) |
| `home/dot_config/git/overlay.gitconfig` | work name/email, signing, `url.*.insteadOf`, credential helpers |
| `home/private_dot_ssh/private_config.d/work.conf` | work ssh hosts |
| `home/dot_config/agents/overlay.md` | work-only instructions for Claude, Codex and Gemini |
| `claude/settings.json` | work plugins, permissions, marketplaces (added on top of the base) |
| `claude/mcp-servers.json` | work MCP servers, tokens as `${VAR}` |
| `codex/config.toml` | work Codex settings (merged on top of the base) |

Delete any file you leave empty. Then:

```bash
git init -b main
git add .chezmoiroot home claude codex     # stage by path; add packages/ only if you used it
git commit -m "chore: start work overlay"
git remote add origin <work-repo-url>
git push -u origin main                    # -u matters: the sync needs an upstream
```

## 3. Install (WSL side)

```bash
cd ~/dotfiles
DOTFILES_MODE=pull DOTFILES_OVERLAY=work DOTFILES_OVERLAY_MODE=push sh install.sh
```

- `DOTFILES_MODE=pull`: the public base only ever receives here.
- `DOTFILES_OVERLAY_MODE=push`: edits on this laptop are saved to the work repo.
- It asks for the sudo password (apt packages from `packages/apt.txt`). The login shell stays
  bash.

Check, and report each result:

```bash
cat ~/.config/dotfiles/config.toml        # mode = "pull", overlay = "work", [modes] work = "push"
dotfiles status; echo $?                  # 0
systemctl --user list-timers dotfiles-sync.timer   # listed (if systemd is on)
ls ~/Library 2>&1                         # "No such file or directory"
command -v brew || echo "no brew"         # "no brew"
bash -lc 'command -v rg gh just'          # all three from ~/.local/share/mise/shims
```

Then open a **new** WSL tab: `gs`, `cz` and `lllm status` work, and `echo $WORK_PROXY` (or
whatever `work.sh` sets) prints the work value. In `claude`, `/memory` lists the shared standards
and the work `overlay.md`; `/skills` lists `rmsesh`; `claude mcp list` shows the work MCP servers.

Prove the work repo saves and the base doesn't: add a comment line to
`~/.config/shell/conf.d/work.sh`, run `dotfiles sync`, and check that `git -C ~/dotfiles-work log -1`
shows a `chore(sync)` commit that reached company git, while `git -C ~/dotfiles status -sb` shows
no `ahead`.

## 4. Windows side (build it)

### 4.1 Design (decided; don't change it without asking Dan)

- One chezmoi install, in WSL. A third chezmoi **instance** named `windows` writes into the
  Windows home (`/mnt/c/Users/<WindowsUser>`).
- Its source is `~/dotfiles-work/windows/`, in the **work overlay**. This laptop is Dan's only
  Windows machine, and the work repo pushes, so Windows-side edits get saved automatically.
  `windows/` sits next to `home/`, so the WSL instances never see it (`.chezmoiroot` is `home`).
- Shared content comes **read-only** from the base: VS Code `settings.json` and the extension
  list. Templates include them by absolute path via a `baseSource` data variable.

### 4.2 Instance config: `~/.config/chezmoi/windows.toml`

```toml
sourceDir = "/home/<wsl-user>/dotfiles-work/windows"
destDir = "/mnt/c/Users/<WindowsUser>"
[data]
    target = "windows"
    baseSource = "/home/<wsl-user>/dotfiles"
[git]
    autoCommit = false
    autoPush = false
```

Find the Windows home with `wslpath "$(cmd.exe /c 'echo %USERPROFILE%' 2>/dev/null | tr -d '\r')"`.

### 4.3 What goes in `~/dotfiles-work/windows/`

Find the Documents folder first: work laptops often redirect it to OneDrive:
`powershell.exe -NoProfile -Command '[Environment]::GetFolderPath("MyDocuments")'`. Use the
path under the Windows home that it prints (e.g. `OneDrive - Company/Documents`).

| Source path in `windows/` | Notes |
|---|---|
| `AppData/Roaming/Microsoft/Windows/Start Menu/Programs/Startup/<name>.ahk` | AutoHotkey scripts, run at login. **ASK** Dan for the scripts and whether they're AutoHotkey v1 or v2 |
| `<Documents>/PowerShell/Microsoft.PowerShell_profile.ps1` | PowerShell 7 profile. Windows PowerShell 5.1 uses `<Documents>/WindowsPowerShell/` instead; **ASK** which one Dan uses |
| `AppData/Local/Packages/Microsoft.WindowsTerminal_8wekyb3d8bbwe/LocalState/settings.json` | Windows Terminal. Terminal rewrites this file itself; the sync then commits its changes, which is expected |
| `AppData/Roaming/Code/User/settings.json.tmpl` | content: `{{ include (joinPath .baseSource "home/dot_config/editors/vscode/settings.json") }}` |
| `run_onchange_after_10-winget.sh.tmpl` | `winget.exe import`, see below |
| `run_onchange_after_20-vscode-extensions.sh.tmpl` | installs the base's `packages/vscode-extensions.txt` into Windows VS Code, see below |

Package list: run `winget.exe export -o "$(wslpath -w ~/dotfiles-work/packages/winget.json)"`
once. Dan reviews it and removes what he doesn't want. The winget script then embeds
`{{ include (joinPath .chezmoi.sourceDir "../packages/winget.json") | sha256sum }}` in a comment
(so it reruns when the list changes) and runs
`winget.exe import -i "$(wslpath -w <path>)" --accept-package-agreements --accept-source-agreements`.
Add `AutoHotkey.AutoHotkey` to the list.

VS Code extensions: the script embeds the sha256 of `{{ joinPath .baseSource "packages/vscode-extensions.txt" }}`,
lists installed ones with `cmd.exe /c code --list-extensions`, and installs each missing one with
`cmd.exe /c code --install-extension <id>`. Log failures and carry on, like the base script does.
Some entries are macOS-only and will fail; that's fine. Dan turns VS Code Settings Sync **off**.

Rules for files in `windows/`:
- No `symlink_`, `private_` or `executable_` prefixes. drvfs ignores Unix modes, and Windows apps
  can't follow WSL symlinks.
- `.chezmoi.os` is `linux` here. Branch on `.target` if a template needs to know.
- Use `.chezmoi.destDir` for Windows paths, never `.chezmoi.homeDir` (that's the WSL home).
- Run scripts execute in WSL bash. Call Windows programs as `cmd.exe /c …`, `powershell.exe …`
  or `winget.exe …`, and convert paths with `wslpath -w`.
- LF line endings work for all of the above. Use `# chezmoi:template:line-endings=crlf` only if
  a tool complains.

### 4.4 Teach `bin/dotfiles` about the instance (test first)

Work in a worktree, never in `~/dotfiles` itself:
`git -C ~/dotfiles worktree add ~/dotfiles-dev -b feat/windows-instance`, then `cd ~/dotfiles-dev && just setup`.

Behavior to add:
- Config key `windows = true` in `~/.config/dotfiles/config.toml` adds an instance named
  `windows`: `--config ~/.config/chezmoi/windows.toml --persistent-state
  ~/.config/chezmoi/windows-state.boltdb --cache ~/.cache/chezmoi-windows`.
- It has **no git of its own**: its source lives in the overlay repo. In a sync, run its
  `chezmoi re-add` (in push mode for the overlay) **before** the overlay's `sync_repo`, so
  Windows-side edits land in the overlay's one commit. Skip `sync_repo` for it. Apply it after
  the others.
- Every existing scenario keeps passing on machines without `windows = true`.

Scenarios. Add each to `docs/scenarios.md` and `tests/`, and show it failing first. Tests point
`destDir` at a temp dir, not `/mnt/c`:
- `test_windows_files_are_applied_into_the_windows_home`
- `test_edit_on_the_windows_side_is_saved_to_the_overlay_repo`
- `test_windows_instance_makes_no_commit_of_its_own`

When `just check` passes, commit in the worktree, Conventional Commits, staging by path, using the
personal identity from the [publishing setup](#publishing-to-the-public-repo-from-the-work-laptop).
Then **stop and hand over to Dan**. He pushes the branch and opens the PR:
`git -C ~/dotfiles-dev push -u origin feat/windows-instance`.

Until that PR is merged and synced, turn the instance on locally by running chezmoi by hand:
`chezmoi --config ~/.config/chezmoi/windows.toml --persistent-state ~/.config/chezmoi/windows-state.boltdb --cache ~/.cache/chezmoi-windows apply`.
After the merge, add `windows = true` to `config.toml`.

**If drvfs causes trouble** (very slow applies, permission diffs that won't go away): stop and
**ASK**. The fallback is a native `chezmoi.exe` on Windows using `~/dotfiles-work/windows` as its
source, scheduled with Task Scheduler.

## Publishing to the public repo from the work laptop

**Dan only.** Agents never do this. The base is pull-only here, so nothing reaches
`ckive/dotfiles` unless you publish it. `dotfiles publish` commits with the identity set **in the
repo** and refuses without one, so the company identity can't leak into the public history.

One-time setup, in WSL:

```bash
cd ~/dotfiles
git config --local user.name "ckive"
git config --local user.email "<the email your Mac commits use>"   # Mac: git -C ~/Desktop/projects/dotfiles log -1 --format=%ae
git config --local commit.gpgsign false        # the work overlay may turn signing on with a work key
ssh-keygen -t ed25519 -f ~/.ssh/id_ed25519_github_personal -C "ckive work-laptop"
# add ~/.ssh/id_ed25519_github_personal.pub at github.com/settings/keys (personal account)
git config --local core.sshCommand "ssh -i ~/.ssh/id_ed25519_github_personal -o IdentitiesOnly=yes"
git remote set-url --push origin git@github.com:ckive/dotfiles.git
ssh -i ~/.ssh/id_ed25519_github_personal -o IdentitiesOnly=yes -T git@github.com   # "Hi ckive!"
```

If the company network blocks ssh on port 22, use GitHub's port-443 endpoint for pushes:
`git remote set-url --push origin ssh://git@ssh.github.com:443/ckive/dotfiles.git`.

Each time:

```bash
chezmoi edit --apply ~/.config/shell/common.sh     # edits the repo copy; the sync keeps it
dotfiles publish -m "feat(shell): add foo alias"
```

`publish` shows the full diff and asks before pushing. **Read the diff.** If anything
work-specific is in it, answer `n` and move that part to the work overlay. If you edit
the file in `~` directly instead of using `chezmoi edit`, publish within 5 minutes, or the sync puts the
file back. Until you publish, `dotfiles status` reminds you that local edits aren't on GitHub.

## Acceptance checklist (report back)

- [ ] Policy answer from Dan: ______
- [ ] Backup tarball made; company lines moved into the work overlay (list them)
- [ ] `config.toml`: `mode = "pull"`, `overlay = "work"`, `[modes] work = "push"`
- [ ] `dotfiles status` exits 0; the sync timer is listed (or systemd is off and Dan knows)
- [ ] A new bash tab has `gs`, `cz`, `lllm status` and the `work.sh` settings
- [ ] No `~/Library`, no `brew`; `bash -lc 'command -v rg gh just'` finds all three
- [ ] Claude in WSL: `/memory` shows standards + work overlay; `/skills` lists `rmsesh`; `claude mcp list` shows work servers
- [ ] An edit to `work.sh` became a commit on company git; `~/dotfiles` shows no local commits
- [ ] Windows: AutoHotkey scripts run after a reboot; PowerShell profile loads; Windows Terminal settings applied; VS Code settings and extensions applied
- [ ] Editing an `.ahk` file on Windows shows up as a commit in the work repo after one sync
- [ ] `feat/windows-instance` branch: new scenarios shown failing first, `just check` passes, handed to Dan
- [ ] Nothing pushed to `ckive/*` by the agent
