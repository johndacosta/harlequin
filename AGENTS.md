# Agent guide (Harlequin)

This file orients coding agents working in this repository. For human-oriented contribution policy, see [CONTRIBUTING.md](./CONTRIBUTING.md). End-user and adapter documentation live at [harlequin.sh](https://harlequin.sh/docs/getting-started/index); the website source is the separate [`harlequin-web`](https://github.com/tconbeer/harlequin-web) repo—do not expect full docs here.

## What this project is

[Harlequin](https://github.com/tconbeer/harlequin) is **the SQL IDE for your terminal**: a Python [Textual](https://textual.textualize.io/) TUI with pluggable database **adapters** (entry points under `harlequin.adapter`; core ships DuckDB and SQLite).

## Prerequisites

- **Python**: `>= 3.10` (see [pyproject.toml](./pyproject.toml)).
- **`uv`** for installs and runnable commands ([uv](https://docs.astral.sh/uv)).

## Repository layout

- **`src/harlequin/`**: core app (CLI in `cli.py`, main app in `app.py`, adapters base types in `adapter.py`, etc.).
- **`src/harlequin_duckdb/`**, **`src/harlequin_sqlite/`**, **`src/harlequin_vscode/`**: in-tree adapters and the VS Code-style keymap.
- **`tests/`**: `unit_tests/`, `functional_tests/` (Textual snapshots via `pytest-textual-snapshot`), `adapter_tests/`.
- **`stubs/`**: types for libraries that ship incomplete stubs (used by **mypy** via `mypy_path`).

## Everyday commands

From the repo root:

| Goal | Command |
|------|---------|
| Full local gate (what maintainers roughly expect before a PR) | `make check` |
| Lint / format / typecheck only | `make lint` |
| Run app in Textual dev mode (DuckDB profile) | `make serve` |
| Run app with SQLite adapter | `make sqlite` |
| Tests only (skip online tests, matches CI default) | `uv sync --group test` then `uv run pytest -m "not online"` |

CI runs **`ruff format` (diff), `ruff check`, `mypy`** on PRs and **`pytest -m "not online"`** across Python versions. Prefer **`uv run …`** so you use the project’s locked deps.

## Code expectations

- **Typing**: mypy is **strict** for `src/**/*.py` and `tests/**/*.py`; new code should type-check without loosening project settings.
- **Style**: **Ruff** with rules in [pyproject.toml](./pyproject.toml) (`A`, `B`, `E`, `F`, `I`); format with Ruff as in `make lint`.
- **Tests**: Extend existing patterns in `tests/`; functional UI tests use **snapshots**—update snapshots only when UI changes are intentional, per pytest snapshot workflow.
- **Scope**: Prefer **minimal, focused diffs**. Adapters that are maintained as separate PyPI packages should not be merged into core without an explicit repo decision—see the [adapter guide](https://harlequin.sh/docs/contributing/adapter-guide).

## Plugins and CLI

- Console script: **`harlequin`** → `harlequin.cli:harlequin`.
- Declare new in-tree adapters in **`[project.entry-points."harlequin.adapter"]`** and keymaps under **`harlequin.keymap`** in [pyproject.toml](./pyproject.toml); mirror package lists under **`[tool.hatch.build.targets.wheel]`**.

When unsure how a behavior is supposed to work, search call sites and tests before changing public CLI or adapter contracts.
