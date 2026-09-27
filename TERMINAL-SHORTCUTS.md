# Terminal shortcuts (kitty)

Source-only doc (see `.chezmoiignore`) — not applied to `$HOME`. Covers only what we've
explicitly customized, plus the kitty defaults worth knowing. For anything not listed here,
kitty's defaults are documented at <https://sw.kovidgoyal.net/kitty/overview/#default-shortcuts>.

**Keep this in sync**: a Claude Code hook (`claude-hook-shortcuts-reminder`, wired into
`PostToolUse` in `dot_claude/settings.json`) fires a reminder whenever `kitty.conf` is
edited via Claude Code. It only catches Claude-driven edits — if you hand-edit it yourself,
update this doc manually.

Split naming: "vertical split" means panes end up **side by side** (split by a vertical
line); "horizontal split" means **stacked**. This is kitty's own `vsplit`/`hsplit` naming —
the opposite of tmux's `-h`/`-v` flags, so don't carry tmux muscle memory over.
`opt+cmd+d` was chosen to avoid kitty's default `shift+cmd+d` (`close_window`).

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

## When to use which

- **Native kitty splits** — quick, disposable pane arrangement within a single sitting. No
  persistence: closing kitty or losing the SSH connection loses the layout.
- **tmux** — anything that must survive a disconnect, e.g. attaching to agent sessions on
  dev01 over Tailscale SSH (`ssh agent@dev01 -t tmux attach`).
