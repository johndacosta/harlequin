# PRD-19: Fix Thread-Safety in `Harlequin.commit()` / `rollback()` and Unhashable/Duplicate Cursor ID in `_execute_query()`

- **Slice ID**: `PRD-19`
- **Category**: Bug Fix (`Bug`)
- **Priority / Severity**: `P1` (High — Worker Thread UI Calls & Unhashable/Colliding Cursor IDs)
- **Target Branch / PR Scope**: Single atomic commit / PR (`fix(app): use call_from_thread in commit/rollback and sequential table IDs in _execute_query`)

## 1. Problem Statement & Root Cause
In `src/harlequin/app.py`:

1. **Cross-Thread UI Mutation in `commit()` and `rollback()` (`app.py:1246-1297`)**:
   `commit()` and `rollback()` are decorated with `@work(thread=True, ...)`, executing on a background OS thread. However, when `self.connection.transaction_mode.commit()` or `.rollback()` raises `HarlequinTransactionError`, they call `self._push_error_modal(...)` (which invokes `self.push_screen(ErrorModal(...))`) **directly from the background thread** instead of via `self.call_from_thread(self._push_error_modal, ...)`. Similarly, on success they call `self.update_schema_data()` directly from the background thread instead of `self.call_from_thread(self.update_schema_data)`.
2. **Fragile `f"t{hash(cur)}"` Table Widget ID in `_execute_query()` (`app.py:1086-1097`)**:
   ```python
   table_id = f"t{hash(cur)}"
   cursors[table_id] = (cur, q)
   ```
   - If a third-party or in-tree adapter defines its `HarlequinCursor` subclass as a `@dataclass` (which sets `__hash__ = None` by default), `hash(cur)` raises `TypeError: unhashable type`!
   - If `hash(cur)` is negative (e.g., `-12345`), `f"t{hash(cur)}"` produces `"t-12345"`, or if an adapter reuses the same cursor instance across multiple queries in a single batch, `cursors[table_id]` overwrites earlier query results. Using a monotonically increasing or enumerated identifier `f"t{i}_{id(cur)}"` avoids both `hash()` failures and collisions.

## 2. Goals & Non-Goals
### Goals
- Wrap `self._push_error_modal(...)` and `self.update_schema_data()` in `self.call_from_thread(...)` inside `Harlequin.commit()` and `Harlequin.rollback()`.
- Replace `f"t{hash(cur)}"` in `Harlequin._execute_query()` with `f"t{i}_{id(cur)}"` (using `enumerate(queries)`).
- Add unit/functional tests verifying `commit()`/`rollback()` error handling and `@dataclass` cursor execution.

### Non-Goals
- Changing `HarlequinCursor` ABC methods.

## 3. Technical Design & Affected Files
- `src/harlequin/app.py`
- `tests/functional_tests/test_app.py`

## 4. Verification & Acceptance Criteria
```bash
uv run pytest tests/functional_tests/test_app.py
uv run ruff check src/harlequin/app.py
uv run mypy src/harlequin/app.py
```
