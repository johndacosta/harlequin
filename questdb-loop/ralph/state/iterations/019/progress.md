### 2026-10-25 — PRD-12: fix(duckdb): escape quotes in catalog identifiers, show_relation_ddl, and .open script rewriting

- **Author**: John DaCosta (`@johndacosta`)
- **State transition**: `SELECT` -> `GRILL` -> `BUILD` -> `VERIFY` -> `PROGRESS`
- **PRD**: [`questdb-loop/prds/PRD-12-duckdb-identifier-escaping-in-catalog-and-ddl.md`](../questdb-loop/prds/PRD-12-duckdb-identifier-escaping-in-catalog-and-ddl.md)
- **Changes**:
  - Escape double quotes in DuckDB catalog identifiers via _quote_ident helper.
  - Escape single quotes for db/schema/relation in show_relation_ddl and guard None cursor.
  - Quote table names safely in .open script rewriting.
- **Deterministic commands run**: `uv run python -m compileall -q src/harlequin_duckdb/catalog.py src/harlequin_duckdb/interactions.py src/harlequin_duckdb/adapter.py tests/adapter_tests/test_duckdb.py; uv run ruff check src/harlequin_duckdb/catalog.py src/harlequin_duckdb/interactions.py src/harlequin_duckdb/adapter.py tests/adapter_tests/test_duckdb.py; uv run ruff format --check src/harlequin_duckdb/catalog.py src/harlequin_duckdb/interactions.py src/harlequin_duckdb/adapter.py tests/adapter_tests/test_duckdb.py; uv run mypy src/harlequin_duckdb/catalog.py src/harlequin_duckdb/interactions.py src/harlequin_duckdb/adapter.py tests/adapter_tests/test_duckdb.py; uv run pytest -m not online tests/adapter_tests/test_duckdb.py`
- **Outcome**: PASS (all compileall, ruff, mypy, and pytest checks exited 0).

---
