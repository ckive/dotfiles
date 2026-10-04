# dotfiles overlay template

A private overlay adds machine-group config on top of the public base (`ckive/dotfiles`).
Copy this directory into a new **private** repo (company git for work), fill in the files,
then run the base `install.sh` and answer the overlay question with its URL.

| File | Lands at / used for |
|---|---|
| `home/dot_config/shell/conf.d/<name>.sh` | sourced by both bash and zsh (PATHs, env, proxies); keep it POSIX sh |
| `home/dot_config/zsh/conf.d/<name>.zsh` | zsh only (zsh syntax, plugins) |
| `home/dot_config/git/overlay.gitconfig` | identity, signing, URL rewrites |
| `home/private_dot_ssh/private_config.d/<name>.conf` | ssh hosts |
| `home/dot_config/agents/overlay.md` | extra agent instructions (Claude, Codex, Gemini) |
| `claude/settings.json` | added on top of the base Claude settings (plugins, permissions, marketplaces) |
| `claude/mcp-servers.json` | user-scope MCP servers (use `${VAR}` for tokens) |
| `codex/config.toml` | added on top of the base Codex config |
| `packages/Brewfile` | extra macOS packages |

Skills, agents and commands you create on the machine are saved here automatically.
Only the files above are needed; delete what you don't use.
