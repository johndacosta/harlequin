# Deterministic Verification Gate: PRD-01

- **Author**: John DaCosta (`@johndacosta`)
- **Timestamp**: `2026-10-25T02:02:56.083165+00:00`
- **Status**: `FAIL`

| Check | Command | Exit Code | Status |
| :--- | :--- | :---: | :---: |
| `uv run python -m` | `uv run python -m compileall -q src/harlequin_questdb tests/adapter_tests/test_questdb.py tests/adapter_tests/test_questdb_completions.py tests/adapter_tests/test_questdb_docs.py tests/adapter_tests/test_questdb_packaging.py` | `0` | **PASS** |
| `uv run ruff check` | `uv run ruff check src/harlequin_questdb tests/adapter_tests/test_questdb.py tests/adapter_tests/test_questdb_completions.py tests/adapter_tests/test_questdb_docs.py tests/adapter_tests/test_questdb_packaging.py` | `1` | **FAIL** |
| `uv run ruff format` | `uv run ruff format --check src/harlequin_questdb tests/adapter_tests/test_questdb.py tests/adapter_tests/test_questdb_completions.py tests/adapter_tests/test_questdb_docs.py tests/adapter_tests/test_questdb_packaging.py` | `1` | **FAIL** |
| `uv run mypy src/harlequin_questdb` | `uv run mypy src/harlequin_questdb tests/adapter_tests/test_questdb.py tests/adapter_tests/test_questdb_completions.py tests/adapter_tests/test_questdb_docs.py tests/adapter_tests/test_questdb_packaging.py` | `1` | **FAIL** |
| `uv run pytest -m` | `uv run pytest -m not online tests/adapter_tests/test_questdb.py tests/adapter_tests/test_questdb_completions.py tests/adapter_tests/test_questdb_docs.py tests/adapter_tests/test_questdb_packaging.py` | `2` | **FAIL** |

## Output: `uv run ruff check src/harlequin_questdb tests/adapter_tests/test_questdb.py tests/adapter_tests/test_questdb_completions.py tests/adapter_tests/test_questdb_docs.py tests/adapter_tests/test_questdb_packaging.py`
```text
I001 [*] Import block is un-sorted or un-formatted
  --> src/harlequin_questdb/adapter.py:1:1
   |
 1 | / from __future__ import annotations
 2 | |
 3 | | from contextlib import contextmanager
 4 | | from typing import Any, Iterator, Sequence
 5 | |
 6 | | from harlequin import (
 7 | |     HarlequinAdapter,
 8 | |     HarlequinConnection,
 9 | |     HarlequinCursor,
10 | |     HarlequinTransactionMode,
11 | | )
12 | | from harlequin.autocomplete import HarlequinCompletion
13 | | from harlequin.catalog import Catalog, CatalogItem
14 | | from harlequin.exception import HarlequinConnectionError, HarlequinQueryError
15 | | from psycopg import ClientCursor, Connection, OperationalError, conninfo
16 | | from psycopg.errors import QueryCanceled
17 | | from psycopg_pool import ConnectionPool
18 | | from textual_fastdatatable.backend import AutoBackendType
19 | |
20 | | from harlequin_questdb.catalog import (
21 | |     ColumnCatalogItem,
22 | |     DatabaseCatalogItem,
23 | |     RelationCatalogItem,
24 | |     SchemaCatalogItem,
25 | |     TableCatalogItem,
26 | |     ViewCatalogItem,
27 | | )
28 | | from harlequin_questdb.cli_options import QUESTDB_OPTIONS
29 | | from harlequin_questdb.completions import base_questdb_completions
30 | | from harlequin_questdb.interactions import (
31 | |     COLUMN_INTERACTIONS,
32 | |     DATABASE_INTERACTIONS,
33 | |     SCHEMA_INTERACTIONS,
34 | |     TABLE_INTERACTIONS,
35 | |     VIEW_INTERACTIONS,
36 | | )
   | |_^
37 |
38 |   # Verified against QuestDB 8.2.2 PGWire (`RowDescription.type_code`) in
   |
help: Organize imports

Found 1 error.
[*] 1 fixable with the `--fix` option.
```

## Output: `uv run ruff format --check src/harlequin_questdb tests/adapter_tests/test_questdb.py tests/adapter_tests/test_questdb_completions.py tests/adapter_tests/test_questdb_docs.py tests/adapter_tests/test_questdb_packaging.py`
```text
Would reformat: tests/adapter_tests/test_questdb_docs.py
1 file would be reformatted, 9 files already formatted
```

## Output: `uv run mypy src/harlequin_questdb tests/adapter_tests/test_questdb.py tests/adapter_tests/test_questdb_completions.py tests/adapter_tests/test_questdb_docs.py tests/adapter_tests/test_questdb_packaging.py`
```text
src/harlequin_questdb/cli_options.py:3:1: error: Module "harlequin.options" has no attribute "IntOption"  [attr-defined]
src/harlequin_questdb/cli_options.py:3:1: error: Module "harlequin.options" has no attribute "PasswordOption"  [attr-defined]
src/harlequin_questdb/catalog.py:14:50: error: Type argument "ColumnCatalogItem" of "InteractiveCatalogItem" must be a subtype of "HarlequinConnection"  [type-var]
src/harlequin_questdb/catalog.py:29:48: error: Type argument "RelationCatalogItem" of "InteractiveCatalogItem" must be a subtype of "HarlequinConnection"  [type-var]
src/harlequin_questdb/catalog.py:34:50: error: Type argument "SchemaCatalogItem" of "InteractiveCatalogItem" must be a subtype of "HarlequinConnection"  [type-var]
src/harlequin_questdb/interactions.py:49:9: error: Unexpected keyword argument "title" for "notify" of "HarlequinDriver"  [call-arg]
src/harlequin_questdb/interactions.py:49:9: note: "notify" defined in "harlequin.driver"
src/harlequin_questdb/interactions.py:65:9: error: Unexpected keyword argument "title" for "notify" of "HarlequinDriver"  [call-arg]
src/harlequin_questdb/interactions.py:65:9: note: "notify" defined in "harlequin.driver"
src/harlequin_questdb/interactions.py:82:13: error: Unexpected keyword argument "title" for "notify" of "HarlequinDriver"  [call-arg]
src/harlequin_questdb/interactions.py:82:13: note: "notify" defined in "harlequin.driver"
src/harlequin_questdb/interactions.py:99:13: error: Unexpected keyword argument "title" for "notify" of "HarlequinDriver"  [call-arg]
src/harlequin_questdb/interactions.py:99:13: note: "notify" defined in "harlequin.driver"
src/harlequin_questdb/adapter.py:216: error: Unused "type: ignore" comment  [unused-ignore]
src/harlequin_questdb/adapter.py:253:45: error: Argument 1 to "make_conninfo" has incompatible type "**dict[str, str | int | None]"; expected "str"  [arg-type]
src/harlequin_questdb/adapter.py:379:17: error: Unexpected keyword argument "interactions" for "SchemaCatalogItem"  [call-arg]
src/harlequin_questdb/adapter.py:384:30: error: Argument "children" to "SchemaCatalogItem" has incompatible type "list[RelationCatalogItem]"; expected "list[CatalogItem]"  [arg-type]
src/harlequin_questdb/adapter.py:384:30: note: "list" is invariant -- see https://mypy.readthedocs.io/en/stable/common_issues.html#variance
src/harlequin_questdb/adapter.py:384:30: note: Consider using "Sequence" instead, which is covariant
src/harlequin_questdb/adapter.py:386:32: error: Argument "connection" to "SchemaCatalogItem" has incompatible type "HarlequinQuestDbConnection"; expected "RelationCatalogItem | None"  [arg-type]
src/harlequin_questdb/adapter.py:387: error: Unused "type: ignore" comment  [unused-ignore]
src/harlequin_questdb/adapter.py:391:19: error: Unexpected keyword argument "interactions" for "DatabaseCatalogItem"  [call-arg]
src/harlequin_questdb/adapter.py:396:22: error: Argument "children" to "DatabaseCatalogItem" has incompatible type "list[SchemaCatalogItem]"; expected "list[CatalogItem]"  [arg-type]
src/harlequin_questdb/adapter.py:396:22: note: "list" is invariant -- see https://mypy.readthedocs.io/en/stable/common_issues.html#variance
src/harlequin_questdb/adapter.py:396:22: note: Consider using "Sequence" instead, which is covariant
src/harlequin_questdb/adapter.py:398:24: error: Argument "connection" to "DatabaseCatalogItem" has incompatible type "HarlequinQuestDbConnection"; expected "SchemaCatalogItem | None"  [arg-type]
src/harlequin_questdb/adapter.py:399: error: Unused "type: ignore" comment  [unused-ignore]
src/harlequin_questdb/adapter.py:521:20: error: Unexpected keyword argument "interactions" for "ViewCatalogItem"  [call-arg]
src/harlequin_questdb/adapter.py:521:20: error: Unexpected keyword argument "fetch_children" for "ViewCatalogItem"  [call-arg]
src/harlequin_questdb/adapter.py:528:28: error: Argument "connection" to "ViewCatalogItem" has incompatible type "HarlequinQuestDbConnection"; expected "ColumnCatalogItem | None"  [arg-type]
src/harlequin_questdb/adapter.py:529: error: Unused "type: ignore" comment  [unused-ignore]
src/harlequin_questdb/adapter.py:535:16: error: Unexpected keyword argument "interactions" for "TableCatalogItem"  [call-arg]
src/harlequin_questdb/adapter.py:535:16: error: Unexpected keyword argument "fetch_children" for "TableCatalogItem"  [call-arg]
src/harlequin_questdb/adapter.py:542:24: error: Argument "connection" to "TableCatalogItem" has incompatible type "HarlequinQuestDbConnection"; expected "ColumnCatalogItem | None"  [arg-type]
src/harlequin_questdb/adapter.py:543: error: Unused "type: ignore" comment  [unused-ignore]
src/harlequin_questdb/adapter.py:560:17: error: Unexpected keyword argument "interactions" for "ColumnCatalogItem"  [call-arg]
src/harlequin_questdb/adapter.py:568: error: Unused "type: ignore" comment  [unused-ignore]
tests/adapter_tests/test_questdb.py:24:1: error: Module "harlequin_questdb.catalog" has no attribute "MaterializedViewCatalogItem"  [attr-defined]
tests/adapter_tests/test_questdb.py:30:1: error: Module "harlequin_questdb.interactions" has no attribute "show_questdb_partitions"  [attr-defined]
tests/adapter_tests/test_questdb.py:43:9: error: Returning Any from function declared to return "dict[str, Any]"  [no-any-return]
tests/adapter_tests/test_questdb.py:50:9: error: Returning Any from function declared to return "dict[str, Any]"  [no-any-return]
tests/adapter_tests/test_questdb.py:56:18: error: "type[HarlequinQuestDbConnection]" has no attribute "QUEST_TYPE_SHORT"  [attr-defined]
tests/adapter_tests/test_questdb.py:60:9: error: Returning Any from function declared to return "str"  [no-any-return]
tests/adapter_tests/test_questdb.py:163:9: error: "type[HarlequinQuestDbConnection]" has no attribute "_short_column_type_from_oid"  [attr-defined]
tests/adapter_tests/test_questdb.py:196:10: error: "type[DatabaseCatalogItem]" has no attribute "from_label"  [attr-defined]
tests/adapter_tests/test_questdb.py:199:14: error: "type[SchemaCatalogItem]" has no attribute "from_parent"  [attr-defined]
tests/adapter_tests/test_questdb.py:202:13: error: "type[TableCatalogItem]" has no attribute "from_parent"  [attr-defined]
tests/adapter_tests/test_questdb.py:210:10: error: "type[DatabaseCatalogItem]" has no attribute "from_label"  [attr-defined]
tests/adapter_tests/test_questdb.py:211:14: error: "type[SchemaCatalogItem]" has no attribute "from_parent"  [attr-defined]
tests/adapter_tests/test_questdb.py:212:13: error: "type[TableCatalogItem]" has no attribute "from_parent"  [attr-defined]
tests/adapter_tests/test_questdb.py:277:10: error: "type[DatabaseCatalogItem]" has no attribute "from_label"  [attr-defined]
tests/adapter_tests/test_questdb.py:293:10: error: "type[DatabaseCatalogItem]" has no attribute "from_label"  [attr-defined]
tests/adapter_tests/test_questdb.py:304:10: error: "type[DatabaseCatalogItem]" has no attribute "from_label"  [attr-defined]
tests/adapter_tests/test_questdb.py:345:13: error: "type[HarlequinQuestDbConnection]" has no attribute "_short_column_type_from_oid"  [attr-defined]
tests/adapter_tests/test_questdb.py:351:18: error: "type[HarlequinQuestDbConnection]" has no attribute "QUEST_TYPE_SHORT"  [attr-defined]
tests/adapter_tests/test_questdb.py:354:17: error: "type[HarlequinQuestDbConnection]" has no attribute "_short_column_type_from_oid"  [attr-defined]
tests/adapter_tests/test_questdb.py:365:9: error: "type[HarlequinQuestDbConnection]" has no attribute "_short_column_type_from_oid"  [attr-defined]
tests/adapter_tests/test_questdb.py:396:14: error: Argument "port" to "HarlequinQuestDbAdapter" has incompatible type "int"; expected "str | None"  [arg-type]
tests/adapter_tests/test_questdb.py:450:5: error: "HarlequinQuestDbConnection" has no attribute "_short_column_type_from_oid"  [attr-defined]
tests/adapter_tests/test_questdb.py:451:9: error: "type[HarlequinQuestDbConnection]" has no attribute "_short_column_type_from_oid"  [attr-defined]
tests/adapter_tests/test_questdb.py:475:5: error: "HarlequinQuestDbConnection" has no attribute "_short_column_type_from_oid"  [attr-defined]
tests/adapter_tests/test_questdb.py:476:9: error: "type[HarlequinQuestDbConnection]" has no attribute "_short_column_type_from_oid"  [attr-defined]
Found 54 errors in 5 files (checked 10 source files)
```

## Output: `uv run pytest -m not online tests/adapter_tests/test_questdb.py tests/adapter_tests/test_questdb_completions.py tests/adapter_tests/test_questdb_docs.py tests/adapter_tests/test_questdb_packaging.py`
```text
============================= test session starts ==============================
platform linux -- Python 3.10.15, pytest-9.0.3, pluggy-1.6.0
rootdir: /home/jdacosta/code/harlequin
configfile: pyproject.toml
plugins: textual-snapshot-0.4.0, asyncio-1.3.0, flaky-3.8.1, syrupy-5.0.0
asyncio: mode=strict, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collected 26 items / 2 errors

==================================== ERRORS ====================================
_____________ ERROR collecting tests/adapter_tests/test_questdb.py _____________
ImportError while importing test module '/home/jdacosta/code/harlequin/tests/adapter_tests/test_questdb.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
../../.local/share/uv/python/cpython-3.10.15-linux-x86_64-gnu/lib/python3.10/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
tests/adapter_tests/test_questdb.py:13: in <module>
    import harlequin_questdb.interactions as questdb_interactions
src/harlequin_questdb/__init__.py:3: in <module>
    from harlequin_questdb.adapter import (
src/harlequin_questdb/adapter.py:28: in <module>
    from harlequin_questdb.cli_options import QUESTDB_OPTIONS
src/harlequin_questdb/cli_options.py:3: in <module>
    from harlequin.options import (
E   ImportError: cannot import name 'IntOption' from 'harlequin.options' (/home/jdacosta/code/harlequin/src/harlequin/options.py)
_______ ERROR collecting tests/adapter_tests/test_questdb_completions.py _______
ImportError while importing test module '/home/jdacosta/code/harlequin/tests/adapter_tests/test_questdb_completions.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
../../.local/share/uv/python/cpython-3.10.15-linux-x86_64-gnu/lib/python3.10/importlib/__init__.py:126: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
tests/adapter_tests/test_questdb_completions.py:5: in <module>
    from harlequin_questdb.adapter import HarlequinQuestDbConnection
src/harlequin_questdb/__init__.py:3: in <module>
    from harlequin_questdb.adapter import (
src/harlequin_questdb/adapter.py:28: in <module>
    from harlequin_questdb.cli_options import QUESTDB_OPTIONS
src/harlequin_questdb/cli_options.py:3: in <module>
    from harlequin.options import (
E   ImportError: cannot import name 'IntOption' from 'harlequin.options' (/home/jdacosta/code/harlequin/src/harlequin/options.py)
=========================== short test summary info ============================
ERROR tests/adapter_tests/test_questdb.py
ERROR tests/adapter_tests/test_questdb_completions.py
!!!!!!!!!!!!!!!!!!! Interrupted: 2 errors during collection !!!!!!!!!!!!!!!!!!!!
============================== 2 errors in 0.32s ===============================
```

