### 2026-10-25 — PRD-19: fix(app): use call_from_thread in commit/rollback and sequential table IDs in _execute_query

- **Author**: John DaCosta (`@johndacosta`)
- **State transition**: `SELECT` -> `GRILL` -> `BUILD` -> `VERIFY` -> `PROGRESS`
- **PRD**: [`questdb-loop/prds/PRD-19-app-thread-safety-and-cursor-table-id.md`](../questdb-loop/prds/PRD-19-app-thread-safety-and-cursor-table-id.md)
- **Changes**:
  - Invoke UI modal and schema updates via call_from_thread in Harlequin commit and rollback workers.
  - Generate collision-free sequential table IDs f't{i}_{id(cur)}' in Harlequin._execute_query.
- **Deterministic commands run**: `uv run python -m compileall -q src/harlequin/app.py tests/functional_tests/test_app.py; uv run ruff check src/harlequin/app.py tests/functional_tests/test_app.py; uv run ruff format --check src/harlequin/app.py tests/functional_tests/test_app.py; uv run mypy src/harlequin/app.py tests/functional_tests/test_app.py; uv run pytest -m not online tests/functional_tests/test_app.py -k test_validate_selection_memoization`
- **Outcome**: PASS (all compileall, ruff, mypy, and pytest checks exited 0).

---
