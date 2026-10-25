# PRD-25: Fix QuestDB `conn_str` Parameter Precedence Over Defaults and `ConnectionPool` Lifecycle / Reconnect Leak

- **Slice ID**: `PRD-25`
- **Category**: Bug Fix & Resource Safety (`Bug`)
- **Priority / Severity**: `P0` (`conn_str` Parameters Overwritten by Defaults & Background Pool Thread Leak on Failed Connect)
- **Target Branch / PR Scope**: Single atomic commit / PR (`fix(questdb): preserve conn_str parameters over defaults and close pool on connect failure`)

## 1. Problem Statement & Root Cause
In `src/harlequin_questdb/adapter.py` and `questdb-loop/package/harlequin-questdb/src/harlequin_questdb/adapter.py`:

1. **Default `pool_kwargs.setdefault(...)` Values Overwrite `conn_str` Parameters (`adapter.py:175-205, 482-509, 525-530`)**:
   In `HarlequinQuestDbAdapter.__init__`, `pool_kwargs.setdefault(...)` unconditionally populates `"host": "127.0.0.1"`, `"port": "8812"`, `"user": "admin"`, `"password": "quest"`, `"dbname": "qdb"`, `"sslmode": "disable"` even when the user omitted CLI flags and passed a libpq `conn_str` (e.g., `harlequin -a questdb "host=prod.internal port=18812 user=reader password=secret dbname=metrics sslmode=require"`).
   Because `conninfo.conninfo_to_dict(conninfo=raw, **kwargs)` and `ConnectionPool(conninfo=raw, ..., kwargs=kwargs)` give **`kwargs` higher precedence than `conninfo` (`raw`)**, `pool_kwargs` defaults silently overwrite every parameter in `conn_str`!
2. **`ConnectionPool` Background Threads Leaked When `self.pool.getconn()` Fails in `__init__` (`adapter.py:192-210`)**:
   `ConnectionPool(..., open=True, reconnect_timeout=120.0)` starts background worker threads immediately. When `self._main_conn = self.pool.getconn()` raises (e.g. on an unreachable port), the `except Exception as e:` block raises `HarlequinConnectionError` **without calling `self.pool.close()`**, leaking background reconnect threads for up to 120 seconds.
3. **Unclosed `old` Connection in `_reconnect_main()`, Unprotected `close()`, and Permanent Legacy Downgrade on Transient Errors (`adapter.py:216-231, 352-411`)**:
   - `_reconnect_main()` returns `old` to the pool (`self.pool.putconn(old)`) without closing `old` first (`old.close()`), allowing `psycopg_pool` to hand back a broken connection, and does not guard `putconn` in `close()` with `try ... finally: self.pool.close()`.
   - In `_list_relations` and `_get_relation_columns`, catching a transient network error (`_recoverable_connection_error(e)`) permanently downgrades `self._quest_kind_sql = self._QUEST_KIND_SQL_LEGACY` and `self._relation_columns_include_designated = False` for the rest of the session.

## 2. Goals & Non-Goals
### Goals
- Parse `conn_str[0]` with `conninfo.conninfo_to_dict(raw)` first in `HarlequinQuestDbAdapter.__init__` so `setdefault` only fills in defaults not present in `conn_str`, while explicit CLI options override `conn_str`.
- Call `pool.close()` in `HarlequinQuestDbConnection.__init__` when `pool.getconn()` fails.
- Close `old` before `putconn(old)` in `_reconnect_main()`, ensure `self.pool.close()` always runs in `close()` via `try ... finally`, and only downgrade `_quest_kind_sql` / `_relation_columns_include_designated` when `not _recoverable_connection_error(e)`.
- Sync changes between `src/harlequin_questdb/` and `questdb-loop/package/harlequin-questdb/src/harlequin_questdb/`.

### Non-Goals
- Changing QuestDB CLI option names.

## 3. Technical Design & Affected Files
- `src/harlequin_questdb/adapter.py`
- `questdb-loop/package/harlequin-questdb/src/harlequin_questdb/adapter.py`
- `tests/adapter_tests/test_questdb.py`

## 4. Verification & Acceptance Criteria
```bash
./questdb-loop/scripts/sync-harlequin-questdb-package.sh
uv run pytest tests/adapter_tests/test_questdb.py tests/adapter_tests/test_questdb_packaging.py
uv run ruff check src/harlequin_questdb tests/adapter_tests/test_questdb*.py
uv run mypy src/harlequin_questdb tests/adapter_tests/test_questdb*.py
```
