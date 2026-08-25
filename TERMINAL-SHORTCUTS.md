# Terminal shortcuts (kitty + herdr)

Source-only doc (see `.chezmoiignore`) — not applied to `$HOME`. Covers only what we've
explicitly customized, plus the kitty defaults worth knowing. For anything not listed here,
kitty's defaults are documented at <https://sw.kovidgoyal.net/kitty/overview/#default-shortcuts>
and herdr's full default set is printed by `herdr --default-config`.

**Keep this in sync**: a Claude Code hook (`claude-hook-shortcuts-reminder`, wired into
`PostToolUse` in `dot_claude/settings.json`) fires a reminder whenever `kitty.conf` or
herdr's `config.toml` is edited via Claude Code. It only catches Claude-driven edits — if
you hand-edit either file yourself, update this doc manually.

## Cross-tool split mnemonic

Both tools use the same scheme: base key = vertical split (left/right), `+alt`/`+opt` =
horizontal split (top/bottom). Chosen to avoid every existing default collision in both
tools (notably `shift+cmd+d` = kitty's default `close_window`, and `prefix+shift+d` =
herdr's default `close_workspace` — neither is touched).

| Split | kitty | herdr |
|---|---|---|
| Vertical (left \| right) | `cmd+d` | `prefix+d` |
| Horizontal (top / bottom) | `opt+cmd+d` | `prefix+alt+d` |

Terminology note: "vertical split" here means the panes end up **side by side** (split by
a vertical line); "horizontal split" means panes end up **stacked** (split by a horizontal
line). This is kitty's own `vsplit`/`hsplit` naming, which herdr matches — it's the
opposite of tmux's `-h`/`-v` flags, so don't carry tmux muscle memory over.

## kitty — custom (`~/.config/kitty/kitty.conf`)

| Shortcut | Action |
|---|---|
| `cmd+d` | Split pane vertically → left/right (`launch --location=vsplit`) |
| `opt+cmd+d` | Split pane horizontally → top/bottom (`launch --location=hsplit`) |
| `cmd+f` | Search scrollback with fzf, Enter copies match to clipboard |

`enabled_layouts` is pinned to `splits,stack` so `--location=` is always honored (it's only
respected in the `splits` layout).

## kitty — defaults worth knowing (macOS, kitty 0.46.2, unmodified)

| Shortcut | Action |
|---|---|
| `cmd+enter` | New window (current layout) |
| `cmd+n` | New OS window |
| `cmd+t` | New tab |
| `cmd+w` | Close tab |
| `shift+cmd+d` | Close window |
| `cmd+right` / `cmd+left` (`kitty_mod+]`/`[`) | Next / previous window |
| `cmd+shift+right` / `left` (`kitty_mod+right`/`left`) | Next / previous tab |
| `cmd+1`..`cmd+9` | Jump to window N |
| `cmd+r` | Start resizing window |
| `kitty_mod+l` | Cycle to next layout |

`kitty_mod` = `cmd` on macOS by default (unchanged here).

## herdr — custom (`~/.config/herdr/config.toml`)

| Shortcut | Action |
|---|---|
| `prefix+d` | Split pane vertically → left/right |
| `prefix+alt+d` | Split pane horizontally → top/bottom |

Prefix key is the unchanged default: `ctrl+b` (tmux-style — press then release, then the
key, no simultaneous chord).

## herdr — defaults worth knowing (unmodified)

All require the `prefix` (`ctrl+b`) first, e.g. `prefix+s` = press `ctrl+b`, release, press `s`.

| Shortcut | Action |
|---|---|
| `prefix+c` | New tab |
| `prefix+shift+n` | New workspace |
| `prefix+shift+g` | New git-worktree workspace |
| `prefix+w` | Workspace picker |
| `prefix+g` | Goto |
| `prefix+h` / `j` / `k` / `l` | Focus pane left / down / up / right (vim-style) |
| `prefix+tab` / `shift+tab` | Cycle pane next / previous |
| `prefix+x` | Close pane |
| `prefix+shift+d` | Close workspace |
| `prefix+shift+x` | Close tab |
| `prefix+z` | Zoom (fullscreen) pane |
| `prefix+r` | Resize mode |
| `prefix+b` | Toggle sidebar |
| `prefix+q` | Detach |
| `prefix+s` | Settings |
| `prefix+?` | Help |

Full reference, including unbound optional actions (`focus_agent`, custom popup commands,
etc.): `herdr --default-config`.

## When to use which

- **Native kitty splits** — quick, disposable pane arrangement within a single sitting. No
  persistence: closing kitty or losing the SSH connection loses the layout.
- **herdr** — anything that should survive a detach/reattach, a remote/SSH session, work
  spread across git worktrees, or coordinating multiple AI agent panes you want to track
  and query (`herdr agent`, `herdr pane`). Run herdr sessions inside kitty; use kitty's own
  splits *within* a herdr pane only for throwaway local layout.
