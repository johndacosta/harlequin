# PRD-12: Fix DuckDB Identifier Escaping in Catalog Items, `show_relation_ddl`, and `.open` Script Rewriting

- **Slice ID**: `PRD-12`
- **Category**: Bug Fix (`Bug`)
- **Priority / Severity**: `P1` (High — Broken DDL Inspection, Identifier Quoting, and `.open` Init Script Rewriting)
- **Target Branch / PR Scope**: Single atomic commit / PR (`fix(duckdb): escape quotes in catalog identifiers, show_relation_ddl, and .open script rewriting`)

## 1. Problem Statement & Root Cause
In `src/harlequin_duckdb/`:

1. **Unescaped Single Quotes & `None` Result Handling in `show_relation_ddl` (`src/harlequin_duckdb/interactions.py:118-140`)**:
   ```python
   select sql
   from duckdb_{relation_type}s()
   where
       database_name = '{item.parent.parent.label}'
       and schema_name = '{item.parent.label}'
       and {relation_type}_name = '{item.label}'
   ```
   - Single quotes in database, schema, or relation names are not escaped (`'` -> `''`), causing a DuckDB `ParserException` when viewing DDL.
   - If `result` is `(None,)` (when `sql` is `NULL`), `result is not None` is `True` and `result[0]` is `None`, crashing `driver.insert_text_in_new_buffer`.
2. **Unescaped Double Quotes in Catalog `qualified_identifier` & `query_name` (`src/harlequin_duckdb/catalog.py:36-37, 87-88, 111-112, 135-136, 161, 212`)**:
   All catalog items wrap `label` as `f'"{label}"'` without doubling embedded double quotes (`label.replace('"', '""')`).
3. **Unquoted Database Stem in `_rewrite_dot_open` & Whitespace-Only Segments in `_split_script` (`src/harlequin_duckdb/adapter.py:391-420`)**:
   - `_rewrite_dot_open` generates `f"attach '{db_path}'{option} as {db_path.stem}; use {db_path.stem};"`, which fails if `db_path.stem` contains hyphens or spaces (`my-db.duckdb`) or is a SQL keyword.
   - `_split_script` filters `[command.strip() for command in commands if command]`, which checks `if command` before `.strip()`, leaving `""` entries when whitespace-only lines precede a `.dot` command.

## 2. Goals & Non-Goals
### Goals
- Escape single quotes (`'` -> `''`) and guard `result[0] is not None` in `show_relation_ddl` in `src/harlequin_duckdb/interactions.py`.
- Escape double quotes (`"` -> `""`) via `_quote_ident(label: str) -> str` in `src/harlequin_duckdb/catalog.py`.
- Filter `if command.strip()` in `_split_script` and quote identifiers/literals safely in `_rewrite_dot_open`.

### Non-Goals
- Fixing `DuckDbConnection.validate_sql`, MotherDuck URL parameters, and `close()` (covered in `PRD-24`).

## 3. Technical Design & Affected Files
- `src/harlequin_duckdb/adapter.py`
- `src/harlequin_duckdb/catalog.py`
- `src/harlequin_duckdb/interactions.py`
- `tests/adapter_tests/test_duckdb.py`

## 4. Verification & Acceptance Criteria
```bash
uv run pytest tests/adapter_tests/test_duckdb.py
uv run ruff check src/harlequin_duckdb tests/adapter_tests/test_duckdb.py
uv run mypy src/harlequin_duckdb tests/adapter_tests/test_duckdb.py
```
