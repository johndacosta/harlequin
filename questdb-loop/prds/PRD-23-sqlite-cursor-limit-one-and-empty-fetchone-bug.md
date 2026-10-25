# PRD-23: Fix `HarlequinSqliteCursor.set_limit(1).fetchall()` Returning All Rows (`fetchmany(0)`) and Empty `fetchone()` Returning `(None,)`

- **Slice ID**: `PRD-23`
- **Category**: Bug Fix (`Bug`)
- **Priority / Severity**: `P0` (Critical Data Bug — `LIMIT 1` in UI Returns Entire Table in SQLite)
- **Target Branch / PR Scope**: Single atomic commit / PR (`fix(sqlite): handle set_limit(1) in fetchall and return None from fetchone when empty`)

## 1. Problem Statement & Root Cause
In `src/harlequin_sqlite/adapter.py`:

1. **`set_limit(1).fetchall()` Returns All Rows in the Table (`adapter.py:55-62`)**:
   `HarlequinSqliteCursor.__init__` prefetches the first row (`self._first_row = self.cur.fetchone()`). Then `fetchall()` executes:
   ```python
   remaining_rows = (
       self.cur.fetchall()
       if self._limit is None
       else self.cur.fetchmany(self._limit - 1)
   )
   return [self._first_row, *remaining_rows]
   ```
   When the user sets the Harlequin limit input to `1` (`cur.set_limit(1)`), `self._limit - 1` is `0`.
   In Python's standard library `sqlite3`, **`cur.fetchmany(0)` returns ALL remaining rows in the cursor** instead of an empty list `[]`!
   Consequently, running a query with Limit = `1` against a 10,000,000-row SQLite table fetches all 10,000,000 rows into memory instead of 1 row!
2. **`fetchone()` Returns `(None, ...)` When Query Returns Zero Rows (`adapter.py:38-41, 76-77`)**:
   When a query returns 0 rows, `HarlequinSqliteCursor.__init__` sets `self.has_records = False` and initializes `self._first_row = tuple([None for _ in range(len(self.cur.description))])` so `columns()` can still inspect column count.
   However, `fetchone()` (lines 76-77) unconditionally returns `self._first_row` without checking `self.has_records`, returning `(None,)` instead of `None` on empty result sets!

## 2. Goals & Non-Goals
### Goals
- In `HarlequinSqliteCursor.fetchall()`:
  - If `not self.has_records` or `(self._limit is not None and self._limit <= 0)`, return `None`.
  - If `self._limit == 1`, return `[self._first_row]` without calling `self.cur.fetchmany(0)`.
- In `HarlequinSqliteCursor.fetchone()`:
  - Return `self._first_row if self.has_records else None`.
- Add regression tests in `tests/adapter_tests/test_sqlite.py` for `cur.set_limit(1).fetchall()`, `cur.set_limit(0).fetchall()`, and `cur.fetchone()` on an empty result set.

### Non-Goals
- Changing how `HarlequinSqliteCursor.columns()` infers column types.

## 3. Technical Design & Affected Files
- `src/harlequin_sqlite/adapter.py`
- `tests/adapter_tests/test_sqlite.py`

## 4. Verification & Acceptance Criteria
```bash
uv run pytest tests/adapter_tests/test_sqlite.py
uv run ruff check src/harlequin_sqlite/adapter.py tests/adapter_tests/test_sqlite.py
uv run mypy src/harlequin_sqlite/adapter.py tests/adapter_tests/test_sqlite.py
```
