### 2026-10-25 — PRD-17: fix(export-screen): preserve custom filenames when auto-switching format from extension

- **Author**: John DaCosta (`@johndacosta`)
- **State transition**: `SELECT` -> `GRILL` -> `BUILD` -> `VERIFY` -> `PROGRESS`
- **PRD**: [`questdb-loop/prds/PRD-17-export-screen-custom-filename-preservation.md`](../questdb-loop/prds/PRD-17-export-screen-custom-filename-preservation.md)
- **Changes**:
  - Fix ExportScreen.on_input_changed and ExportScreen.on_select_changed to preserve custom filenames when auto-switching export formats from file extensions.
  - Remove duplicate Select.Changed message posting in ExportScreen.on_input_changed and clear validation errors on empty path inputs.
  - Normalize file extensions to lowercase in ExportScreen._get_format_from_file_extension and guard None screen_data in export_callback.
  - Add deterministic unit, async widget, and functional export tests in tests/unit_tests/test_export_filename.py and tests/functional_tests/test_export.py.
- **Deterministic commands run**: `uv run python -m compileall -q src/harlequin/components/export_screen.py src/harlequin/export.py tests/unit_tests/test_export_filename.py tests/functional_tests/test_export.py; uv run ruff check src/harlequin/components/export_screen.py src/harlequin/export.py tests/unit_tests/test_export_filename.py tests/functional_tests/test_export.py; uv run ruff format --check src/harlequin/components/export_screen.py src/harlequin/export.py tests/unit_tests/test_export_filename.py tests/functional_tests/test_export.py; uv run mypy src/harlequin/components/export_screen.py src/harlequin/export.py tests/unit_tests/test_export_filename.py tests/functional_tests/test_export.py; uv run pytest -m not online tests/unit_tests/test_export_filename.py`
- **Outcome**: PASS (all compileall, ruff, mypy, and pytest checks exited 0).

---
