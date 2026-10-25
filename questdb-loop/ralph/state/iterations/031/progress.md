### 2026-10-25 — PRD-13: perf(questdb): avoid redundant pool check round-trips and autocommit resets

- **Author**: John DaCosta (`@johndacosta`)
- **State transition**: `SELECT` -> `GRILL` -> `BUILD` -> `VERIFY` -> `PROGRESS`
- **PRD**: [`questdb-loop/prds/PRD-13-questdb-pool-check-and-catalog-perf.md`](../questdb-loop/prds/PRD-13-questdb-pool-check-and-catalog-perf.md)
- **Changes**:
  - Avoid redundant autocommit = True assignments in QuestDb connection borrowing.
  - Accept optional worker connection in _logical_database_label, _list_schemas, and _list_relations.
  - Synchronize staged harlequin-questdb package.
- **Deterministic commands run**: `uv run python -m compileall -q src/harlequin_questdb/adapter.py tests/adapter_tests/test_questdb.py; uv run ruff check src/harlequin_questdb/adapter.py tests/adapter_tests/test_questdb.py; uv run ruff format --check src/harlequin_questdb/adapter.py tests/adapter_tests/test_questdb.py; uv run mypy src/harlequin_questdb/adapter.py tests/adapter_tests/test_questdb.py; uv run pytest -m not online tests/adapter_tests/test_questdb.py -k test_worker_connection_reuse_and_autocommit`
- **Outcome**: PASS (all compileall, ruff, mypy, and pytest checks exited 0).

---
