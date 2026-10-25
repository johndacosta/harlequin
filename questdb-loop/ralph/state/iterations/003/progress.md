### 2026-10-25 — PRD-01: fix(questdb): sync in-tree questdb adapter with hardened staged package

- **Author**: John DaCosta (`@johndacosta`)
- **State transition**: `SELECT` -> `GRILL` -> `BUILD` -> `VERIFY` -> `PROGRESS`
- **PRD**: [`questdb-loop/prds/PRD-01-questdb-source-sync.md`](../questdb-loop/prds/PRD-01-questdb-source-sync.md)
- **Changes**:
  - Synchronize src/harlequin_questdb/ with the staged v0.4.0 package in questdb-loop/package/harlequin-questdb/src/harlequin_questdb/.
  - Restore _escape_quest_literal, _quote_quest_identifier, 4-column _list_relations, 3-column _get_relation_columns, QueryCanceled handling, and _PIN_OID_TO_SHORT mappings.
  - Fix strict mypy annotations in tests/adapter_tests/test_questdb.py.
  - Verify all 58 deterministic QuestDB unit, completion, documentation, and packaging tests pass.
- **Deterministic commands run**: `uv run python -m compileall -q src/harlequin_questdb tests/adapter_tests/test_questdb.py tests/adapter_tests/test_questdb_completions.py tests/adapter_tests/test_questdb_docs.py tests/adapter_tests/test_questdb_packaging.py; uv run ruff check src/harlequin_questdb tests/adapter_tests/test_questdb.py tests/adapter_tests/test_questdb_completions.py tests/adapter_tests/test_questdb_docs.py tests/adapter_tests/test_questdb_packaging.py; uv run ruff format --check src/harlequin_questdb tests/adapter_tests/test_questdb.py tests/adapter_tests/test_questdb_completions.py tests/adapter_tests/test_questdb_docs.py tests/adapter_tests/test_questdb_packaging.py; uv run mypy src/harlequin_questdb tests/adapter_tests/test_questdb.py tests/adapter_tests/test_questdb_completions.py tests/adapter_tests/test_questdb_docs.py tests/adapter_tests/test_questdb_packaging.py; uv run pytest -m not online tests/adapter_tests/test_questdb.py tests/adapter_tests/test_questdb_completions.py tests/adapter_tests/test_questdb_docs.py`
- **Outcome**: PASS (all compileall, ruff, mypy, and pytest checks exited 0).

---
