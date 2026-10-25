### 2026-10-25 — PRD-23: fix(sqlite): handle set_limit(1) in fetchall and return None from fetchone when empty

- **Author**: John DaCosta (`@johndacosta`)
- **State transition**: `SELECT` -> `GRILL` -> `BUILD` -> `VERIFY` -> `PROGRESS`
- **PRD**: [`questdb-loop/prds/PRD-23-sqlite-cursor-limit-one-and-empty-fetchone-bug.md`](../questdb-loop/prds/PRD-23-sqlite-cursor-limit-one-and-empty-fetchone-bug.md)
- **Changes**:
  - Fix HarlequinSqliteCursor.fetchall to return [self._first_row] when limit == 1 and None when limit <= 0.
  - Fix HarlequinSqliteCursor.fetchone to return None when has_records is False instead of a synthetic tuple of Nones.
  - Add deterministic unit tests in tests/adapter_tests/test_sqlite.py.
- **Deterministic commands run**: `uv run python -m compileall -q src/harlequin_sqlite/adapter.py tests/adapter_tests/test_sqlite.py; uv run ruff check src/harlequin_sqlite/adapter.py tests/adapter_tests/test_sqlite.py; uv run ruff format --check src/harlequin_sqlite/adapter.py tests/adapter_tests/test_sqlite.py; uv run mypy src/harlequin_sqlite/adapter.py tests/adapter_tests/test_sqlite.py; uv run pytest -m not online tests/adapter_tests/test_sqlite.py`
- **Outcome**: PASS (all compileall, ruff, mypy, and pytest checks exited 0).

---
