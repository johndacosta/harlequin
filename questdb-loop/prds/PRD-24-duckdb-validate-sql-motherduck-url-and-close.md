# PRD-24: Fix `DuckDbConnection.validate_sql()` Exception Handling, MotherDuck Query String Formatting, and Missing `close()` Method

- **Slice ID**: `PRD-24`
- **Category**: Bug Fix (`Bug`)
- **Priority / Severity**: `P1` (High — Uncaught `duckdb.Error` in `validate_sql` & `connect()`, Malformed MotherDuck URL, and Unclosed Connection)
- **Target Branch / PR Scope**: Single atomic commit / PR (`fix(duckdb): catch duckdb.Error in validate_sql/connect, fix MotherDuck URL params, and implement close()`)

## 1. Problem Statement & Root Cause
In `src/harlequin_duckdb/adapter.py`:

1. **`DuckDbConnection.validate_sql()` Catches `HarlequinQueryError` Instead of `duckdb.Error` (`adapter.py:166-181`)**:
   ```python
   def validate_sql(self, text: str) -> str:
       cur = self.conn.cursor()
       escaped = text.replace("'", "''")
       try:
           (parsed,) = cur.sql(  # type: ignore
               f"select json_serialize_sql('{escaped}')"
           ).fetchone()
       except HarlequinQueryError:
           return ""
   ```
   `cur` is a raw `duckdb.DuckDBPyConnection` cursor, not `DuckDbConnection`! `cur.sql(...)` raises `duckdb.Error`, never `HarlequinQueryError`. Because `Harlequin._validate_selection()` calls `validate_sql` synchronously on the main UI thread and only catches `NotImplementedError`, any `duckdb.Error` (or `TypeError` if `fetchone()` returns `None`) crashes the TUI.
2. **Malformed MotherDuck Connection URL When Both `md_token` and `md_saas` Are Used (`adapter.py:300-310`)**:
   ```python
   token = f"?token={self.md_token}" if self.md_token else ""
   saas = "?saas_mode=true" if self.md_saas else ""
   connection = duckdb.connect(database=f"{primary_db}{token}{saas}", config=config)
   ```
   When both `md_token` and `md_saas` are provided (or when `primary_db` already contains `?`), `database` is formatted with two `?` characters (`md:my_db?token=abc?saas_mode=true`) instead of joining query parameters with `&`.
3. **Uncaught `duckdb.Error` Subclasses in `DuckDbAdapter.connect()` (`adapter.py:318-346`)**:
   `connect()` only catches `(duckdb.CatalogException, duckdb.IOException)` on `duckdb.connect()` and `(duckdb.HTTPException, duckdb.IOException)` on `load_extension()`, allowing `duckdb.ConnectionException`, `duckdb.InvalidInputException`, `duckdb.PermissionException`, and `duckdb.BinderException` to escape uncaught instead of raising `HarlequinConnectionError`.
4. **Missing `DuckDbConnection.close()` Method (`adapter.py:77-247`)**:
   `DuckDbConnection` does not implement `close(self) -> None` to close `self.conn` when Harlequin exits, leaving DuckDB file locks and `.wal` files open until process termination.

## 2. Goals & Non-Goals
### Goals
- Catch `(duckdb.Error, TypeError, ValueError)` in `DuckDbConnection.validate_sql()`.
- Format MotherDuck query string parameters (`token=...`, `saas_mode=true`) using `?` for the first parameter and `&` for subsequent parameters.
- Catch `duckdb.Error` in `DuckDbAdapter.connect()` and `load_extension()` so all DuckDB connection/extension errors raise `HarlequinConnectionError`.
- Implement `DuckDbConnection.close(self) -> None` calling `self.conn.close()`.

### Non-Goals
- Changing DuckDB catalog introspection queries.

## 3. Technical Design & Affected Files
- `src/harlequin_duckdb/adapter.py`
- `tests/adapter_tests/test_duckdb.py`

## 4. Verification & Acceptance Criteria
```bash
uv run pytest tests/adapter_tests/test_duckdb.py
uv run ruff check src/harlequin_duckdb/adapter.py tests/adapter_tests/test_duckdb.py
uv run mypy src/harlequin_duckdb/adapter.py tests/adapter_tests/test_duckdb.py
```
