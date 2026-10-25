# PRD-11: Fix SQLite Column Type Mapping (`None`, `""`, `bytes`), Identifier Escaping, and `show_describe_relation` / `show_relation_ddl` Syntax

- **Slice ID**: `PRD-11`
- **Category**: Bug Fix (`Bug`)
- **Priority / Severity**: `P0` (`AttributeError` & `sqlite3.OperationalError` on Standard SQLite Operations)
- **Target Branch / PR Scope**: Single atomic commit / PR (`fix(sqlite): fix column type mapping, pragma table_info syntax, and identifier escaping`)

## 1. Problem Statement & Root Cause
Auditing `src/harlequin_sqlite/` uncovered five bugs in column type mapping, catalog introspection, and context-menu interactions:

1. **`AttributeError` When `raw_type` is `None` and Overwritten `""` Affinity (`src/harlequin_sqlite/adapter.py:188-215`)**:
   ```python
   @staticmethod
   def _short_column_type(raw_type: str) -> str:
       if raw_type is None or raw_type == "":
           affinity = ""
       typ = raw_type.lower()
       if "int" in typ:
           affinity = "INTEGER"
       ...
       else:
           affinity = "NUMERIC"
   ```
   - When `raw_type is None`, line 191 sets `affinity = ""` and then falls through to line 193 `typ = raw_type.lower()`, raising `AttributeError: 'NoneType' object has no attribute 'lower'`.
   - When `raw_type == ""` (which SQLite `pragma table_info` returns for untyped columns `CREATE TABLE t (x)` and view expressions), line 191 sets `affinity = ""`, and then lines 194-203 fall through to the `else:` branch and **overwrite `affinity = "NUMERIC"`** (`"#.#"`)!
2. **`_short_column_type_from_python_object` Uses `None` Instead of `type(None)` and `object` Instead of `bytes` (`adapter.py:217-225`)**:
   ```python
   mapping: dict[type | None, str] = {
       None: "",
       str: "s",
       float: "#.#",
       int: "##",
       object: "b",
   }
   return mapping.get(type(obj), "?")
   ```
   `type(None)` is `NoneType` (not `None`), and SQLite `BLOB` values are `bytes` (not `object`), so `NULL` and `BLOB` values both return `"?"` instead of `""` and `"b"`.
3. **Invalid SQLite Syntax in `show_describe_relation` (`src/harlequin_sqlite/interactions.py:51-57`)**:
   `pragma table_info({item.qualified_identifier})` expands to `pragma table_info("main"."drivers")`, which fails in SQLite with `sqlite3.OperationalError: near ".": syntax error`. SQLite requires the schema name before the pragma: `pragma "main".table_info("drivers")`.
4. **Broken Attached-DB DDL Query & Unescaped `tbl_name` (`src/harlequin_sqlite/interactions.py:60-78`)**:
   `show_relation_ddl` queries `from sqlite_schema where tbl_name = '{item.label}'` instead of `{item.parent.qualified_identifier}.sqlite_schema where name = '{escaped}' and type in ('table', 'view') and sql is not null`, failing on attached databases, tables with single quotes, or tables with indexes/triggers.
5. **Unquoted `db_name` & Unescaped `rel_name` in `_get_columns` (`adapter.py:176-185`) and `catalog.py` (`catalog.py:55`)**:
   `f"pragma {db_name}.table_info('{rel_name}')"` and `attach database '{uri}' as {name}` do not quote `"{db_name}"` or escape single quotes in `rel_name`, and `catalog.py:55` has a redundant chained comparison `if self.parent is None is None`.

## 2. Goals & Non-Goals
### Goals
- Fix `_short_column_type` with an `else:` branch so `None` and `""` return `""` without raising `AttributeError` or falling through to `"NUMERIC"`.
- Fix `_short_column_type_from_python_object` to map `type(None): ""` and `bytes: "b"`.
- Fix `show_describe_relation` to emit `pragma "db".table_info("table")`.
- Fix `show_relation_ddl` to query `{db}.sqlite_schema` with `type in ('table', 'view') and name = '...' and sql is not null`.
- Quote `"{db_name}"` and escape quotes in `adapter.py` and `catalog.py`, and fix `self.parent is None is None`.

### Non-Goals
- Fixing `HarlequinSqliteCursor.set_limit(1)` and `fetchone()` (covered in `PRD-23`).

## 3. Technical Design & Affected Files
- `src/harlequin_sqlite/adapter.py`
- `src/harlequin_sqlite/catalog.py`
- `src/harlequin_sqlite/interactions.py`
- `tests/adapter_tests/test_sqlite.py`

## 4. Verification & Acceptance Criteria
```bash
uv run pytest tests/adapter_tests/test_sqlite.py
uv run ruff check src/harlequin_sqlite tests/adapter_tests/test_sqlite.py
uv run mypy src/harlequin_sqlite tests/adapter_tests/test_sqlite.py
```
