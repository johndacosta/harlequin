### 2026-10-25 — PRD-24: fix(duckdb): catch duckdb.Error in validate_sql/connect, fix MotherDuck URL params, and implement close()

- **Author**: John DaCosta (`@johndacosta`)
- **State transition**: `SELECT` -> `GRILL` -> `BUILD` -> `VERIFY` -> `PROGRESS`
- **PRD**: [`questdb-loop/prds/PRD-24-duckdb-validate-sql-motherduck-url-and-close.md`](../questdb-loop/prds/PRD-24-duckdb-validate-sql-motherduck-url-and-close.md)
- **Changes**:
  - Catch duckdb.Error, HarlequinQueryError, TypeError, ValueError in DuckDbConnection.validate_sql.
  - Implement DuckDbConnection.close() delegating to self.conn.close().
  - Correct MotherDuck URL parameter separator to check existing query parameters.
- **Deterministic commands run**: `uv run python -m compileall -q src/harlequin_duckdb/adapter.py tests/adapter_tests/test_duckdb.py; uv run ruff check src/harlequin_duckdb/adapter.py tests/adapter_tests/test_duckdb.py; uv run ruff format --check src/harlequin_duckdb/adapter.py tests/adapter_tests/test_duckdb.py; uv run mypy src/harlequin_duckdb/adapter.py tests/adapter_tests/test_duckdb.py; uv run pytest -m not online tests/adapter_tests/test_duckdb.py`
- **Outcome**: PASS (all compileall, ruff, mypy, and pytest checks exited 0).

---
