### 2026-10-25 — PRD-04: perf(export): run file export in background thread worker

- **Author**: John DaCosta (`@johndacosta`)
- **State transition**: `SELECT` -> `GRILL` -> `BUILD` -> `VERIFY` -> `PROGRESS`
- **PRD**: [`questdb-loop/prds/PRD-04-export-background-worker-ui-responsiveness.md`](../questdb-loop/prds/PRD-04-export-background-worker-ui-responsiveness.md)
- **Changes**:
  - Support background worker execution for export copy pipeline.
  - Maintain responsive TUI event loop during lengthy data exports.
- **Deterministic commands run**: `uv run python -m compileall -q src/harlequin/copy_formats.py src/harlequin/export.py tests/unit_tests/test_export_filename.py; uv run ruff check src/harlequin/copy_formats.py src/harlequin/export.py tests/unit_tests/test_export_filename.py; uv run ruff format --check src/harlequin/copy_formats.py src/harlequin/export.py tests/unit_tests/test_export_filename.py; uv run mypy src/harlequin/copy_formats.py src/harlequin/export.py tests/unit_tests/test_export_filename.py; uv run pytest -m not online tests/unit_tests/test_export_filename.py`
- **Outcome**: PASS (all compileall, ruff, mypy, and pytest checks exited 0).

---
