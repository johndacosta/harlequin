### 2026-10-25 — PRD-05: perf(export): stream html output and use tuple row iteration for tabular writers

- **Author**: John DaCosta (`@johndacosta`)
- **State transition**: `SELECT` -> `GRILL` -> `BUILD` -> `VERIFY` -> `PROGRESS`
- **PRD**: [`questdb-loop/prds/PRD-05-export-streaming-and-batch-perf.md`](../questdb-loop/prds/PRD-05-export-streaming-and-batch-perf.md)
- **Changes**:
  - Stream HTML output row-by-row to file handle using _iter_row_tuples.
  - Use zero-copy tuple iteration for tabular writers to reduce memory pressure.
  - Use compact separators in JSON and JSONL exports.
- **Deterministic commands run**: `uv run python -m compileall -q src/harlequin/export.py tests/unit_tests/test_export_filename.py; uv run ruff check src/harlequin/export.py tests/unit_tests/test_export_filename.py; uv run ruff format --check src/harlequin/export.py tests/unit_tests/test_export_filename.py; uv run mypy src/harlequin/export.py tests/unit_tests/test_export_filename.py; uv run pytest -m not online tests/unit_tests/test_export_filename.py`
- **Outcome**: PASS (all compileall, ruff, mypy, and pytest checks exited 0).

---
