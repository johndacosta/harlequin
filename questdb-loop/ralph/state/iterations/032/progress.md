### 2026-10-25 — PRD-14: perf(editor): memoize _validate_selection to avoid synchronous DB calls on cursor events

- **Author**: John DaCosta (`@johndacosta`)
- **State transition**: `SELECT` -> `GRILL` -> `BUILD` -> `VERIFY` -> `PROGRESS`
- **PRD**: [`questdb-loop/prds/PRD-14-editor-selection-validation-caching.md`](../questdb-loop/prds/PRD-14-editor-selection-validation-caching.md)
- **Changes**:
  - Memoize _validate_selection with cached (selection, valid) tuple.
  - Avoid repetitive synchronous database validate_sql calls on cursor movements.
- **Deterministic commands run**: `uv run python -m compileall -q src/harlequin/app.py tests/functional_tests/test_app.py; uv run ruff check src/harlequin/app.py tests/functional_tests/test_app.py; uv run ruff format --check src/harlequin/app.py tests/functional_tests/test_app.py; uv run mypy src/harlequin/app.py tests/functional_tests/test_app.py; uv run pytest -m not online tests/functional_tests/test_app.py -k test_validate_selection_memoization`
- **Outcome**: PASS (all compileall, ruff, mypy, and pytest checks exited 0).

---
