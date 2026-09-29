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

**Undecided as of 2026-08-25.** Dan wants to research the options first — do not assume a
package manager, linter, or test framework. Ask.

## Testing style — BDD, no Gherkin

Describe behavior, not internals. The scenario lives in the test name and docstring; the
body is structured Given / When / Then.

- **No Gherkin, no Cucumber, no `.feature` files, no step definitions.**
- Name tests after behavior: `test_resolves_exe_link_when_captcha_absent`, not `test_resolve`.
- Test at workflow boundaries over internal functions.
- When Dan describes a feature as a scenario, write the behavior test **first** and
  confirm the scenario list before implementing.
- C++: scenario-shaped GoogleTest names, e.g. `TEST(ResolveExeLink, WhenNoCaptcha_RecordsDestination)`.

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

## Project-specific

- `~/Desktop/projects/winner/wins-ingestion` is deliberately **not** a git repo. Don't `git init` it,
  don't offer to commit, don't propose CI or commit conventions there.
