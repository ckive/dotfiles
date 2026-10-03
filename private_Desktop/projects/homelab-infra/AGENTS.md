# AGENTS.md: agents on dev01 working in homelab-infra

For agents started by pfi on dev01 (HL items). `CLAUDE.md` still applies (protected guests, never-run
list, secrets, guardrails), except "Where and as whom you run": you are **not** on the admin workstation.

## What you have, what you don't
- You have: this repo on Forgejo (`dan/homelab-infra`) as `dan-bot`, Plane via pfi, `just check`.
- You don't have: `~/.config/homelab/*.secret`, Proxmox or Tailscale tokens, SSH to any host, Docker on
  svc01. So `just deploy`, `just run`, `just pve` and `just ts` won't work. Don't try to get around that.
- You change the homelab only through a PR that Dan merges. Nothing reaches a host before then.

## Layout
| Path | What |
|---|---|
| `ansible/` | `site.yml` and `playbooks/` per layer; `roles/*/README.md` per role; `host_vars/<host>.yml`; rules in `ansible/CLAUDE.md` |
| `docker/<host>/<stack>/` | Compose stacks; `*.j2` are templated by `roles/compose_stacks`, `.env` is rendered from secrets |
| `proxmox/`, `tailscale/`, `dns/` | Guest specs and API scripts; tailnet policy; DNS |
| `docs/` | `architecture.md`, `services.md`, `sdlc.md`; `plans/` (designs); `runbooks/` (human procedures) |

## Making a change
1. Branch `<ID>-<slug>` off `main`; Conventional Commits.
2. Change the Ansible/compose/docs together, so the repo describes reality after the deploy.
3. `just setup && just check` must pass (it's also the `check` CI on Forgejo).
4. PR `[<ID>] <summary>`. The body says **what to deploy** (e.g. `just deploy svc01 stacks`), what
   restarts, the risk, and how to verify it. Anything needing host root: exact commands for Dan.
5. Docs in the same PR: the README diagram and affected docs. If none apply, write `Docs: none needed`
   in the PR body; the `check / docs` CI fails otherwise.

## Deploy
After merge, svc01 redeploys changed `docker/svc01/<stack>/` for caddy, dockhand, homepage and plane
within minutes and sets commit status `deploy/svc01` ([`deploy_agent`](ansible/roles/deploy_agent/README.md)).
Everything else (roles, vars, the forgejo stack, other hosts) Dan deploys by hand with the command your
PR names; the status then says `manual deploy needed`. Don't add CI that deploys.

## Not allowed
- Adding secrets anywhere in the repo, or to CI; adding CI jobs that deploy or reach hosts.
- Changing branch protection, `forgejo_config_mergers`/`pushers`, the GitHub push mirror, or the
  bot/token setup to widen your own access.
- Pushing to GitHub (`ckive/homelab-infra` is a read-only mirror of Forgejo).
- Anything on CLAUDE.md's protected or never-run lists, even inside a PR, without Dan's explicit
  approval on the Plane item.
