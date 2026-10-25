### 2026-10-25 — PRD-22: perf(history): precompute HistoryOption prompt renderable on init

- **Author**: John DaCosta (`@johndacosta`)
- **State transition**: `SELECT` -> `GRILL` -> `BUILD` -> `VERIFY` -> `PROGRESS`
- **PRD**: [`questdb-loop/prds/PRD-22-history-option-renderable-caching.md`](../questdb-loop/prds/PRD-22-history-option-renderable-caching.md)
- **Changes**:
  - Precompute Rich renderable in HistoryOption.__init__.
  - Return cached renderable in prompt, __rich__, and visualize methods.
- **Deterministic commands run**: `uv run python -m compileall -q src/harlequin/components/history_screen.py tests/functional_tests/test_history_screen.py; uv run ruff check src/harlequin/components/history_screen.py tests/functional_tests/test_history_screen.py; uv run ruff format --check src/harlequin/components/history_screen.py tests/functional_tests/test_history_screen.py; uv run mypy src/harlequin/components/history_screen.py tests/functional_tests/test_history_screen.py; uv run pytest -m not online tests/functional_tests/test_history_screen.py -k test_history_option_prompt_cached`
- **Outcome**: PASS (all compileall, ruff, mypy, and pytest checks exited 0).

---
