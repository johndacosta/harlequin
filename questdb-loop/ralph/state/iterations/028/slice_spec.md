# PRD-04: Run Data Export in Background Thread Worker to Eliminate TUI Freeze

- **Slice ID**: `PRD-04`
- **Category**: Performance & UX Responsiveness (`Performance`)
- **Priority / Severity**: `P1` (High — Main Event Loop Freeze on Large Exports)
- **Target Branch / PR Scope**: Single atomic commit / PR (`perf(export): run file export in background thread worker`)

## 1. Problem Statement & Root Cause
When a user exports query results via the Export modal (`Ctrl+E`), the actual file export executes **synchronously on the main Textual event loop thread**:

1. In `src/harlequin/app.py:424-439`, `action_export` creates `export_callback` using ` functools.partial` and pushes `ExportScreen`.
2. In `src/harlequin/components/export_screen.py:24-40`, `export_callback` directly calls `copy(data=data, columns=columns, path=..., format_name=..., options=...)` on the UI thread before calling `notify_success()` or `push_error_modal()`.
3. When exporting 50,000–1,000,000 rows to CSV, Parquet, JSON, HTML, Markdown, or Excel, the Textual event loop is completely blocked for seconds or minutes—freezing screen repaints, animations, and keyboard input.

## 2. Goals & Non-Goals
### Goals
- Offload `copy(...)` execution from the main Textual UI thread to an exclusive background thread worker (`@work(thread=True, exclusive=True, group="export")` or `app.run_worker(..., thread=True)`).
- Dispatch `notify_success` / `push_error_modal` safely back on the main thread when the worker completes.
- Preserve existing functional test compatibility (`tests/functional_tests/test_export.py` using `app.workers.wait_for_complete()`).

### Non-Goals
- Changing the internal implementation of individual format writers in `src/harlequin/export.py` (covered in `PRD-05` and `PRD-06`).

## 3. Technical Design & Affected Files
- `src/harlequin/app.py`
- `src/harlequin/components/export_screen.py`
- `tests/functional_tests/test_export.py`

### Proposed Changes
1. Add a `@work(thread=True, exclusive=True, group="export", exit_on_error=False)` method `_export_data(...)` on `Harlequin` in `src/harlequin/app.py` (or invoke `copy()` inside a thread worker and use `self.call_from_thread(...)` to show the toast notification or error modal).
2. In `tests/functional_tests/test_export.py`, ensure `await app.workers.wait_for_complete()` is awaited after pressing Enter on `ExportScreen` so tests deterministically wait for the background export worker to finish writing the file.

## 4. Verification & Acceptance Criteria
```bash
uv run pytest tests/functional_tests/test_export.py tests/unit_tests/test_export_filename.py
uv run ruff check src/harlequin/app.py src/harlequin/components/export_screen.py tests/functional_tests/test_export.py
uv run mypy src/harlequin/app.py src/harlequin/components/export_screen.py tests/functional_tests/test_export.py
```
