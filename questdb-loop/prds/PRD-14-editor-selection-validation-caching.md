# PRD-14: Cache and Fast-Path Editor Selection SQL Validation to Prevent Synchronous DB Queries on Every Cursor Event

- **Slice ID**: `PRD-14`
- **Category**: Performance Improvement (`Performance`)
- **Priority / Severity**: `P1` (High — Synchronous Main-Thread DB Calls on Cursor/Selection Movement)
- **Target Branch / PR Scope**: Single atomic commit / PR (`perf(editor): memoize _validate_selection to avoid synchronous DB calls on cursor events`)

## 1. Problem Statement & Root Cause
Every time the cursor moves or the selection changes in the Query Editor (`on_text_area_selection_changed` in `src/harlequin/app.py:507-508`), Harlequin synchronously calls:
```python
self._sync_run_button_text()
  -> self._validate_selection()
    -> self.connection.validate_sql(selection)
```
In `DuckDbConnection.validate_sql` (`src/harlequin_duckdb/adapter.py:166-180`), this creates a DuckDB cursor and executes `select json_serialize_sql(?)` synchronously on the main UI thread!
1. Even when there is **no selection** (`selection == ""`), `on_text_area_selection_changed` calls `_sync_run_button_text()` -> `_validate_selection()`, which returns `""`, and then `_get_query_bar_T()` calls `self._validate_selection()` **a second time in the same event handler** (`app.py:1036` and `1219`)!
2. When a user drags the mouse or holds `Shift+Arrow` to select text, `_validate_selection()` is invoked **twice per selection event** on the main thread!
3. Furthermore, `_sync_run_button_text()` only cares whether `_validate_selection()` is non-empty and whether `len(selected_queries) > 1` (which is only possible if `";" in selection.strip().rstrip(";")`).

## 2. Goals & Non-Goals
### Goals
- Avoid calling `self._validate_selection()` twice inside `_sync_run_button_text()` (pass the validated selection into `_get_query_bar_T` or cache `(raw_selection, validated_result)` on `Harlequin`).
- Memoize `(self._last_validated_selection_raw, self._last_validated_selection_sql)` on `Harlequin` so repeated calls with identical `editor.selected_text` return in $O(1)$ without hitting the database adapter.
- Fast-path empty/whitespace-only selections (`if not selection.strip(): return ""`) before calling `self.connection.validate_sql(selection)`.

### Non-Goals
- Changing the visual behavior of the "Run Selection" / "Run Queries" button or `Ctrl+Enter` execution semantics.

## 3. Technical Design & Affected Files
- `src/harlequin/app.py`
- `tests/functional_tests/test_app.py` (or `tests/unit_tests/`)

### Proposed Changes
In `src/harlequin/app.py`:
1. Initialize `self._selection_cache: tuple[str, str] = ("", "")` on `Harlequin.__init__`.
2. In `_validate_selection(self) -> str`:
   ```python
   selection = self.editor.selected_text
   if not selection or not selection.strip():
       return ""
   if self._selection_cache[0] == selection:
       return self._selection_cache[1]
   if self.connection is None:
       return selection
   try:
       validated = self.connection.validate_sql(selection)
   except NotImplementedError:
       validated = selection
   self._selection_cache = (selection, validated)
   return validated
   ```

## 4. Verification & Acceptance Criteria
```bash
uv run pytest tests/functional_tests/test_app.py tests/functional_tests/test_code_editor.py
uv run ruff check src/harlequin/app.py
uv run mypy src/harlequin/app.py
```
