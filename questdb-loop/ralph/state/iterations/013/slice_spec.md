# PRD-06: Fix Export Option Filtering, Excel Timezone/Resource Safety, Markdown CR Escaping, and DuckDB File Export Safety

- **Slice ID**: `PRD-06`
- **Category**: Bug Fix (`Bug`)
- **Priority / Severity**: `P1` (High — Broken Export Options, Excel Tz Crash & Resource Leaks)
- **Target Branch / PR Scope**: Single atomic commit / PR (`fix(export): preserve falsy options, handle excel timezones, and close duckdb/openpyxl resources`)

## 1. Problem Statement & Root Cause
Auditing `src/harlequin/export.py` revealed four correctness and resource-safety bugs in the data export pipeline:

1. **Blanket Falsy Option Filtering & Missing Default `header=True` (`export.py:65, 100-101`)**:
   ```python
   kwargs = {k: v for k, v in options.items() if v}
   ```
   This comprehension strips `False`, `0`, and `0.0`, not just `None` and `""`. Because `header=False` was stripped by `if v`, `_export_csv` added a workaround (`if "header" not in kwargs: kwargs["header"] = False`), which causes `copy(..., format_name="csv", options={})` to omit headers even though `FlagOption(name="header", default=True)` defaults to `True`! Furthermore, numeric `0`/`0.0` (e.g., ORC `padding_tolerance=0.0`, `dictionary_key_size_threshold=0.0`, or JSON `indent=0`) are silently dropped.
2. **Unclosed DuckDB Connection & Table Collision in `_export_duckdb_file` (`export.py:400-424`)**:
   ```python
   con = duckdb.connect(database=str(path))
   con.register("_hq_export_arrow", data)
   con.execute("CREATE TABLE results AS SELECT * FROM _hq_export_arrow")
   con.close()
   ```
   If `con.register` or `con.execute` raises `duckdb.Error` (for instance, when exporting to an existing `.duckdb` file that already has a `results` table), `con.close()` is bypassed, leaking the open DuckDB connection and OS file lock. Using `CREATE OR REPLACE TABLE results` and a `try ... finally: con.close()` block matches the overwrite behavior of all other exporters.
3. **`_export_excel` Crashes on Timezone-Aware Datetimes/Times and Complex Types & Leaks Temp Files (`export.py:336-369`)**:
   `openpyxl` raises `ValueError: Excel does not support timezones in datetimes` whenever a PyArrow timestamp/time column with a timezone is exported, and raises `ValueError: Cannot convert ... to Excel` for `list`, `dict`, or `UUID` values. Moreover, `Workbook(write_only=True)` creates temporary files on disk that are leaked if `ws.append` or `wb.save` raises without `wb.close()` in a `finally` block.
4. **`_md_escape_cell` Does Not Escape `\r` (`export.py:271-272`)**:
   `_md_escape_cell` only replaces `|` and `\n`, leaving literal `\r` carriage returns that break Markdown table rows.

## 2. Goals & Non-Goals
### Goals
- Filter out only `None` and `""` (empty strings) when building `kwargs` in `copy()`, preserving explicit booleans (`True`/`False`) and numeric `0`/`0.0`, and default `header` to `True` in `_export_csv` (`kwargs.setdefault("header", True)`).
- Wrap `duckdb.connect` in `_export_duckdb_file` in `try ... finally: con.close()` and use `CREATE OR REPLACE TABLE results AS SELECT * FROM _hq_export_arrow`.
- Normalize Excel cell values (strip `tzinfo` on timezone-aware `datetime`/`time` objects and stringify `list`/`dict`/`UUID` values) and close `wb` in a `finally:` block.
- Escape `\r\n` and `\r` in `_md_escape_cell`.

### Non-Goals
- Streaming HTML and tuple-iteration performance refactoring (covered in `PRD-05`).

## 3. Technical Design & Affected Files
- `src/harlequin/export.py`
- `tests/functional_tests/test_export.py`

## 4. Verification & Acceptance Criteria
```bash
uv run pytest tests/functional_tests/test_export.py tests/unit_tests/test_export_filename.py
uv run ruff check src/harlequin/export.py tests/functional_tests/test_export.py
uv run mypy src/harlequin/export.py tests/functional_tests/test_export.py
```
