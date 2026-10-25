### 2026-10-25 — PRD-25: fix(questdb): preserve conn_str parameters over defaults and close pool on connect failure

- **Author**: John DaCosta (`@johndacosta`)
- **State transition**: `SELECT` -> `GRILL` -> `BUILD` -> `VERIFY` -> `PROGRESS`
- **PRD**: [`questdb-loop/prds/PRD-25-questdb-conn-str-precedence-and-pool-lifecycle.md`](../questdb-loop/prds/PRD-25-questdb-conn-str-precedence-and-pool-lifecycle.md)
- **Changes**:
  - Parse conn_str in HarlequinQuestDbAdapter.__init__ before applying default values so conn_str parameters are preserved unless overridden by explicit CLI options.
  - Do not auto-supply a default password in HarlequinQuestDbAdapter.__init__ per user guide contract.
  - Close ConnectionPool if getconn() fails during HarlequinQuestDbConnection.__init__ and ensure close() always closes the pool in a finally block.
  - Prevent recoverable connection errors from permanently downgrading QuestDB catalog metadata queries.
- **Deterministic commands run**: `uv run python -m compileall -q src/harlequin_questdb/adapter.py tests/adapter_tests/test_questdb.py; uv run ruff check src/harlequin_questdb/adapter.py tests/adapter_tests/test_questdb.py; uv run ruff format --check src/harlequin_questdb/adapter.py tests/adapter_tests/test_questdb.py; uv run mypy src/harlequin_questdb/adapter.py tests/adapter_tests/test_questdb.py; uv run pytest -m not online tests/adapter_tests/test_questdb.py tests/adapter_tests/test_questdb_completions.py tests/adapter_tests/test_questdb_docs.py`
- **Outcome**: PASS (all compileall, ruff, mypy, and pytest checks exited 0).

---
