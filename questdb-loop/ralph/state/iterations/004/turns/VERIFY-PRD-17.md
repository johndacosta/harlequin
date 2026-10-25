# VERIFY-PRD-17

- agent: `qa`
- written: `2026-10-25T02:13:35.283873Z`

## Chat

# Deterministic Verification Gate: PRD-17

- **Author**: John DaCosta (`@johndacosta`)
- **Timestamp**: `2026-10-25T02:13:35.283078+00:00`
- **Status**: `FAIL`

| Check | Command | Exit Code | Status |
| :--- | :--- | :---: | :---: |
| `uv run python -m` | `uv run python -m compileall -q src/harlequin/components/export_screen.py src/harlequin/export.py tests/unit_tests/test_export_filename.py` | `0` | **PASS** |
| `uv run ruff check` | `uv run ruff check src/harlequin/components/export_screen.py src/harlequin/export.py tests/unit_tests/test_export_filename.py` | `1` | **FAIL** |
| `uv run ruff format` | `uv run ruff format --check src/harlequin/components/export_screen.py src/harlequin/export.py tests/unit_tests/test_export_filename.py` | `1` | **FAIL** |
| `uv run mypy src/harlequin/components/export_screen.py` | `uv run mypy src/harlequin/components/export_screen.py src/harlequin/export.py tests/unit_tests/test_export_filename.py` | `1` | **FAIL** |
| `uv run pytest -m` | `uv run pytest -m not online tests/unit_tests/test_export_filename.py` | `0` | **PASS** |

## Output: `uv run ruff check src/harlequin/components/export_screen.py src/harlequin/export.py tests/unit_tests/test_export_filename.py`
```text
F401 [*] `pathlib.Path` imported but unused
 --> tests/unit_tests/test_export_filename.py:4:21
  |
3 | import datetime as dt
4 | from pathlib import Path
  |                     ^^^^
5 | from unittest.mock import MagicMock, patch
  |
help: Remove unused import: `pathlib.Path`

E501 Line too long (90 > 88)
  --> tests/unit_tests/test_export_filename.py:94:89
   |
92 |         assert screen.format_select.value == "parquet"
93 |         assert screen.file_input.value == "/tmp/custom_dir/my_report.parquet"
94 |         # _mount_copy_options must be called once, not twice (no duplicate Select.Changed)
   |                                                                                         ^^
95 |         assert mount_spy.call_count == 1
   |

Found 2 errors.
[*] 1 fixable with the `--fix` option.
```

## Output: `uv run ruff format --check src/harlequin/components/export_screen.py src/harlequin/export.py tests/unit_tests/test_export_filename.py`
```text
Would reformat: src/harlequin/export.py
1 file would be reformatted, 2 files already formatted
```

## Output: `uv run mypy src/harlequin/components/export_screen.py src/harlequin/export.py tests/unit_tests/test_export_filename.py`
```text
src/harlequin/export.py:168:1: error: Cannot find implementation or library stub for module named "zstandard"  [import-not-found]
src/harlequin/export.py:184:1: error: Function is missing a return type annotation  [no-untyped-def]
src/harlequin/export.py:219:15: error: "RecordBatch" has no attribute "to_pydict"  [attr-defined]
src/harlequin/export.py:342:1: error: Library stubs not installed for "openpyxl"  [import-untyped]
src/harlequin/export.py:342:1: note: Hint: "python3 -m pip install types-openpyxl"
src/harlequin/export.py:342:1: note: (or run "mypy --install-types" to install all missing stub packages)
src/harlequin/export.py:359:19: error: "RecordBatch" has no attribute "to_pydict"  [attr-defined]
src/harlequin/export.py:386:1: error: Skipping analyzing "pyarrow.ipc": module is installed, but missing library stubs or py.typed marker  [import-untyped]
src/harlequin/export.py:386:1: note: See https://mypy.readthedocs.io/en/stable/running_mypy.html#missing-imports
src/harlequin/export.py:390:14: error: Module has no attribute "OSFile"  [attr-defined]
Found 7 errors in 1 file (checked 3 source files)
```

## Output: `uv run pytest -m not online tests/unit_tests/test_export_filename.py`
```text
============================= test session starts ==============================
platform linux -- Python 3.10.15, pytest-9.0.3, pluggy-1.6.0
rootdir: /home/jdacosta/code/harlequin
configfile: pyproject.toml
plugins: textual-snapshot-0.4.0, asyncio-1.3.0, flaky-3.8.1, syrupy-5.0.0
asyncio: mode=strict, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collected 6 items

tests/unit_tests/test_export_filename.py ......                          [100%]

============================== 6 passed in 0.64s ===============================
```
