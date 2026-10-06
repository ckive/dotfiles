# Dan's global engineering standards

Applies to every project unless a project's own CLAUDE.md overrides it.

## Python

| Slot | Tool |
|---|---|
| Env / interpreter versions / packages | `uv` — **never** pip, venv, pyenv, pipenv, poetry |
| Lint + format | `ruff` — never black, isort, flake8, pyflakes |
| Type check | `ty` (Astral) |
| Tests | `pytest` + `pytest-cov`, `pytest-xdist` |
| Build backend | `uv_build` |
| Docs | `mkdocs-material` |

- `uv add` / `uv remove` / `uv sync` / `uv run`. Dev tools go in `[dependency-groups]`.
- Commit `uv.lock`; gitignore `.venv/`. Pin the interpreter with `.python-version`.
- Set `[tool.uv] python-preference = "only-managed"`.
- Prefer `uv run <cmd>` over activating a venv.
- `ty` was 0.0.74 as of 2026-08-25 — pre-1.0. It has no Django/SQLAlchemy plugin support;
  raise it rather than silently using `ty` on projects that need those.
- Notebooks (marimo vs jupyter): **undecided**, don't pick one.

## C++

| Slot | Tool |
|---|---|
| Standard | **C++23** |
| Build | CMake ≥3.28 + `CMakePresets.json` |
| Dependencies | `vcpkg` manifest mode |
| Speed | Ninja + `ccache` |
| Format / static analysis | `clang-format`, `clang-tidy` |
| Tests | **GoogleTest** (chosen over Catch2) |
| Runtime checks | ASan + UBSan debug preset; TSan when threaded |
| Editor | `clangd` (`CMAKE_EXPORT_COMPILE_COMMANDS=ON`) |

## TypeScript

Principle: the most modern tool that has become the standard — one tool per slot, fast
native binaries over plugin stacks (the uv/ruff philosophy). **Decided** by Dan: Biome.
The other rows are Claude's 2026-10-05 proposal (first used in wins-viewer `web/`); Dan is
curating them, so follow them but flag any row that fights a project.

| Slot | Tool |
|---|---|
| Node version | `mise` (`mise.toml` per repo) — never nvm or Volta (unmaintained) |
| Package manager | `pnpm` — commit `pnpm-lock.yaml`; never npm/yarn |
| Build / dev server | Vite |
| Type check | `tsc --noEmit` (TypeScript 7 native), `strict` on |
| Lint + format | **Biome** — never ESLint, Prettier |
| Unit tests | Vitest |
| Browser / e2e | Playwright across Chromium, Firefox, WebKit |
| UI | SolidJS when a page needs components; plain DOM for a single page |
| Runtime validation | Valibot at trust boundaries (network, storage) |

- `pnpm add` / `pnpm add -D` / `pnpm install --frozen-lockfile` in CI.
- `just lint` → `biome ci`; `just fmt` → `biome check --write`.

## Testing style — BDD, no Gherkin

Describe behavior, not internals. The scenario lives in the test name and docstring; the
body is structured Given / When / Then.

- **No Gherkin, no Cucumber, no `.feature` files, no step definitions.**
- Name tests after behavior: `test_resolves_exe_link_when_captcha_absent`, not `test_resolve`.
- Test at workflow boundaries over internal functions.
- When Dan describes a feature as a scenario, write the behavior test **first** and
  confirm the scenario list before implementing.
- C++: scenario-shaped GoogleTest names, e.g. `TEST(ResolveExeLink, WhenNoCaptcha_RecordsDestination)`.
- Bug fixes start red: write a test that reproduces the bug, show it failing, then fix.
- UI changes: end with a short manual test script (keys to press, expected result) and
  say what wasn't verified in the running app. Green checks aren't proof a UI works.

## Intent — don't block, don't assume

- "Don't block on X" means proceed; note the risk once and never re-raise it.
- An unanswered question is not agreement. Ask again, or design the best option yourself
  if that's what was asked.
- "Delete" means delete — not rename to `.bak`.
- A UI request that references existing behavior ("like g-d"): restate your reading in one
  sentence before changing layout.
- Work in Q&A, one topic at a time. Run each decision by Dan before it goes into a plan —
  no big all-at-once plans. Once a topic is decided, hand it to an implementation subagent
  right away while the discussion moves on.

## Verification

- Never pipe build/test output through `tail`/`head` without `set -o pipefail`; check exit codes.
- Don't report measured numbers (sizes, counts, timings) without the command that produced them.
- Network-critical changes (DHCP, DNS, sshd, firewall): state the fallback and rollback
  command before applying.

## Data safety

- No backups (decided 2026-10-05). Git history is the safety net; revert, don't restore.
- Data that a change could alter or lose permanently (media, databases, user files): work on
  a copy, never the original.
- Don't propose backup tooling (vzdump, PBS, offsite, dumps) or raise backups as a risk.

## Every repo gets

- **`justfile`** — same verbs everywhere: `just setup`, `just test`, `just lint`, `just fmt`,
  `just check`, `just run`. Recipes wrap native tools; callers never learn the tool.
- **`.editorconfig`** — covers what the real formatters don't own (CMakeLists, YAML,
  Markdown, justfile, shell).
- **Conventional Commits** — `type(scope): description`; types `feat` `fix` `docs`
  `refactor` `test` `chore` `perf` `build` `ci`. Use this for every commit written for Dan.
- **Succinct commits**: subject ≤72 chars says what changed. Body only when the why isn't
  obvious from the diff, ≤3 lines. No narration, no file lists.
- **No Claude authorship anywhere** — no `Co-Authored-By: Claude`, no "Generated with Claude
  Code", in commits or PR bodies. Commits are Dan's. (`attribution` in settings.json enforces it.)
- **No `lefthook`, no `pre-commit`, no `prek`.** Correctness is enforced by `just check`
  and CI, not git hooks.
- **Stage by path.** Never `git add -A`/`.`/`commit -a`; never commit files you didn't create
  in this task (plan files, `*.db`, `.bak`). Check `git status` before committing.
  (`claude-hook-guard-bash` enforces the first and `*.db`.)
