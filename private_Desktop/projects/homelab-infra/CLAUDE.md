# CLAUDE.md — rules for AI agents working in this repo

Read this first. These rules override convenience.

## Where and as whom you run
- Started by pfi on dev01? Read `AGENTS.md`; it replaces this section.
- You run on the admin workstation. Never as `root@pam`, never on the Proxmox host.
- Proxmox access is via API tokens only (see `docs/access.md`):
  - `~/.config/homelab/pve-readonly.secret` — default for all inspection.
  - `~/.config/homelab/pve-provision.secret` — only for changes the human approved.
- Always verify TLS with `--cacert proxmox/pve-root-ca.pem`. Never use `-k`.
- Anything needing host root: write the exact commands, explain them and their
  risk, and have the human run them. Record them in the repo (script + docs).

## Protected — do not touch without explicit, specific approval
- VM 100 `ubuntu25` (SMB; both 20 TB disks `ata-ST20000NM007D-3DJ103_ZVT16XVX`, `_ZVTG83FH`)
- CT 101 `immich`, VM 102 `immich-vm`, VM 104 `family-photos` (WD 2 TB `WD-WXD2A5076KPD`)
- Any physical disk, filesystem, partition table, or LVM outside pool guests.

## Never run automatically
`rm -rf` on important paths, `mkfs`, `wipefs`, destructive `fdisk`/`parted`, LVM
removal, filesystem conversion, repartitioning, `qm destroy`, `pct destroy`,
guest delete via API (even inside pool `homelab`), storage deletion, Proxmox
network changes, firewall changes that could lock out, GPU/VFIO/IOMMU changes,
SSH daemon changes on any host.

## Before every substantial change
1. Show intended changes. 2. Show commands. 3. Identify risk.
4. Wait for approval if it can affect network connectivity, disks, Proxmox boot,
   GPU ownership, or existing services.
5. Tell the human whether they should do it via the UI (with step-by-step
   guidance) or whether you'll do it programmatically (and explain what it does).

## After every change
- Update Ansible/scripts and docs so the repo reflects reality.
- Small commit per successful step.

## Secrets
Never commit credentials, tokens, private keys, real `.env` files, Tailscale auth
keys, PATs, DNS API tokens or passwords. Commit `.env.example` only. See `secrets/README.md`.

## Architecture guardrails
No Kubernetes. No Terraform (for now). No application workloads on the Proxmox
host. Ansible for OS config, Docker Compose for apps, Git is the source of truth.
Deploy things because they solve a real problem, not because homelabs usually have them.
