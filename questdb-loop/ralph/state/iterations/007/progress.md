### 2026-10-25 — PRD-11: fix(sqlite): fix column type mapping, pragma table_info syntax, and identifier escaping

- **Author**: John DaCosta (`@johndacosta`)
- **State transition**: `SELECT` -> `GRILL` -> `BUILD` -> `VERIFY` -> `PROGRESS`
- **PRD**: [`questdb-loop/prds/PRD-11-sqlite-identifier-escaping-and-null-type-fix.md`](../questdb-loop/prds/PRD-11-sqlite-identifier-escaping-and-null-type-fix.md)
- **Changes**:
  - Fix HarlequinSqliteConnection._short_column_type to handle None and empty strings without raising AttributeError or returning #.#.
  - Fix HarlequinSqliteConnection._short_column_type_from_python_object to map type(None) to empty string and bytes/bytearray/memoryview to b.
  - Fix show_describe_relation to emit valid pragma "db".table_info("rel") syntax and show_relation_ddl to filter table/view rows in the parent database.
  - Escape identifiers and literals in SQLite catalog queries and add deterministic tests in tests/adapter_tests/test_sqlite.py.
- **Deterministic commands run**: `uv run python -m compileall -q src/harlequin_sqlite/adapter.py src/harlequin_sqlite/interactions.py src/harlequin_sqlite/catalog.py tests/adapter_tests/test_sqlite.py; uv run ruff check src/harlequin_sqlite/adapter.py src/harlequin_sqlite/interactions.py src/harlequin_sqlite/catalog.py tests/adapter_tests/test_sqlite.py; uv run ruff format --check src/harlequin_sqlite/adapter.py src/harlequin_sqlite/interactions.py src/harlequin_sqlite/catalog.py tests/adapter_tests/test_sqlite.py; uv run mypy src/harlequin_sqlite/adapter.py src/harlequin_sqlite/interactions.py src/harlequin_sqlite/catalog.py tests/adapter_tests/test_sqlite.py; uv run pytest -m not online tests/adapter_tests/test_sqlite.py`
- **Outcome**: PASS (all compileall, ruff, mypy, and pytest checks exited 0).

---
