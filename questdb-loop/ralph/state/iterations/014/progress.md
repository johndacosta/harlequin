### 2026-10-25 — PRD-06: fix(export): preserve falsy options, handle excel timezones, and close duckdb/openpyxl resources

- **Author**: John DaCosta (`@johndacosta`)
- **State transition**: `SELECT` -> `GRILL` -> `BUILD` -> `VERIFY` -> `PROGRESS`
- **PRD**: [`questdb-loop/prds/PRD-06-export-duckdb-resource-safety-and-options.md`](../questdb-loop/prds/PRD-06-export-duckdb-resource-safety-and-options.md)
- **Changes**:
  - Filter export options with v is not None and v != "" so explicit False and 0 values are preserved.
  - Default CSV header option to True and strip quoting=False before calling DuckDB write_csv.
  - Escape CR and CRLF line breaks in Markdown export cells.
  - Sanitize timezone-aware datetime and time values in Excel export and close Workbook in a finally block.
  - Use CREATE OR REPLACE TABLE results and close DuckDB connection in a finally block in _export_duckdb_file.
- **Deterministic commands run**: `uv run python -m compileall -q src/harlequin/export.py tests/unit_tests/test_export_filename.py; uv run ruff check src/harlequin/export.py tests/unit_tests/test_export_filename.py; uv run ruff format --check src/harlequin/export.py tests/unit_tests/test_export_filename.py; uv run mypy src/harlequin/export.py tests/unit_tests/test_export_filename.py; uv run pytest -m not online tests/unit_tests/test_export_filename.py`
- **Outcome**: PASS (all compileall, ruff, mypy, and pytest checks exited 0).

---
