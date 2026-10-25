# PRD-13: Eliminate Redundant QuestDB Pool `SELECT 1` Round-Trips and Redundant `autocommit` Writes

- **Slice ID**: `PRD-13`
- **Category**: Performance Improvement (`Performance`)
- **Priority / Severity**: `P1` (High — 2x Network Round-Trips on Every Catalog & Completion Query)
- **Target Branch / PR Scope**: Single atomic commit / PR (`perf(questdb): avoid redundant pool check round-trips and autocommit resets`)

## 1. Problem Statement & Root Cause
In `src/harlequin_questdb/adapter.py`:

1. **Redundant `autocommit` Reset on Every `_borrow_worker` (`adapter.py:293-303`)**:
   `_configure_questdb_connection` already sets `conn.autocommit = True` when the pool opens a connection, yet `_borrow_worker` sets `cn.autocommit = True` again on every single borrowunless `cn.autocommit` is already `True`.
2. **Multiple Separate Pool Borrows During `get_catalog()` (`adapter.py:372-395`)**:
   `get_catalog()` calls `self._logical_database_label()` (borrows & checks connection #1), `self._list_schemas()` (borrows & checks connection #2), and `self._list_relations()` (borrows & checks connection #3). Because `ConnectionPool` has `check=_check_questdb_pool_connection` (which executes `SELECT 1` over the network on every `pool.getconn()`), initial catalog loading performs **6 sequential network round-trips** instead of borrowing a single worker connection for the duration of `get_catalog()` (which takes 1 check + 3 queries = 4 round-trips, or 3 without redundant checks).

## 2. Goals & Non-Goals
### Goals
- Allow `_logical_database_label`, `_list_schemas`, and `_list_relations` to accept an optional `conn: Any | None = None` so `get_catalog()` borrows a single worker connection from the pool once and reuses it across all three metadata queries.
- Only set `cn.autocommit = True` in `_borrow_worker()` if `not getattr(cn, "autocommit", False)`.
- Preserve existing unit test behavior and monkeypatch points in `tests/adapter_tests/test_questdb.py`.

### Non-Goals
- Removing `_check_questdb_pool_connection` entirely (since `tests/adapter_tests/test_questdb.py` explicitly tests `_check_questdb_pool_connection`).

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
