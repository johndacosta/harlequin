# VERIFY-PRD-06

- agent: `qa`
- written: `2026-10-25T02:33:12.193122Z`

## Chat

# Deterministic Verification Gate: PRD-06

- **Author**: John DaCosta (`@johndacosta`)
- **Timestamp**: `2026-10-25T02:33:12.192776+00:00`
- **Status**: `FAIL`

| Check | Command | Exit Code | Status |
| :--- | :--- | :---: | :---: |
| `uv run python -m` | `uv run python -m compileall -q src/harlequin/export.py tests/unit_tests/test_export_filename.py` | `0` | **PASS** |
| `uv run ruff check` | `uv run ruff check src/harlequin/export.py tests/unit_tests/test_export_filename.py` | `0` | **PASS** |
| `uv run ruff format` | `uv run ruff format --check src/harlequin/export.py tests/unit_tests/test_export_filename.py` | `0` | **PASS** |
| `uv run mypy src/harlequin/export.py` | `uv run mypy src/harlequin/export.py tests/unit_tests/test_export_filename.py` | `0` | **PASS** |
| `uv run pytest -m` | `uv run pytest -m not online tests/unit_tests/test_export_filename.py` | `1` | **FAIL** |

## Output: `uv run ruff check src/harlequin/export.py tests/unit_tests/test_export_filename.py`
```text
All checks passed!
```

## Output: `uv run ruff format --check src/harlequin/export.py tests/unit_tests/test_export_filename.py`
```text
2 files already formatted
```

## Output: `uv run mypy src/harlequin/export.py tests/unit_tests/test_export_filename.py`
```text
Success: no issues found in 2 source files
```

## Output: `uv run pytest -m not online tests/unit_tests/test_export_filename.py`
```text
============================= test session starts ==============================
platform linux -- Python 3.10.15, pytest-9.0.3, pluggy-1.6.0
rootdir: /home/jdacosta/code/harlequin
configfile: pyproject.toml
plugins: textual-snapshot-0.4.0, asyncio-1.3.0, flaky-3.8.1, syrupy-5.0.0
asyncio: mode=strict, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collected 7 items

tests/unit_tests/test_export_filename.py ......F                         [100%]

=================================== FAILURES ===================================
_____________ test_export_falsy_options_markdown_excel_and_duckdb ______________

tmp_path = PosixPath('/tmp/pytest-of-jdacosta/pytest-11/test_export_falsy_options_mark0')

    def test_export_falsy_options_markdown_excel_and_duckdb(tmp_path: object) -> None:
        from pathlib import Path
    
        import duckdb
        import pyarrow as pa
        from textual_fastdatatable.backend import ArrowBackend
    
        from harlequin.export import _md_escape_cell, copy
    
        assert isinstance(tmp_path, Path)
        assert _md_escape_cell("a|b\r\nc\rd\ne") == "a\\|b c d e"
    
        data = pa.table(
            {
                "id": [1, 2],
                "note": ["line1\r\nline2", "pipe|val"],
                "ts": [
                    dt.datetime(2025, 5, 5, 12, 0, tzinfo=dt.timezone.utc),
                    dt.datetime(2025, 5, 6, 12, 0, tzinfo=dt.timezone.utc),
                ],
            }
        )
        table = MagicMock()
        table.row_count = 2
        table.plain_column_labels = ["id", "note", "ts"]
        backend = MagicMock(spec=ArrowBackend)
        backend.source_data = data
        table.backend = backend
    
        # 1. CSV export with explicit header=False must omit header row
        csv_no_hdr = tmp_path / "no_header.csv"
        copy(table=table, path=csv_no_hdr, format_name="csv", options={"header": False})
        lines_no_hdr = csv_no_hdr.read_text(encoding="utf-8").strip().splitlines()
>       assert len(lines_no_hdr) == 2
E       assert 3 == 2
E        +  where 3 = len(['1,"line1', 'line2",2025-05-05 08:00:00-04', '2,pipe|val,2025-05-06 08:00:00-04'])

tests/unit_tests/test_export_filename.py:137: AssertionError
=========================== short test summary info ============================
FAILED tests/unit_tests/test_export_filename.py::test_export_falsy_options_markdown_excel_and_duckdb
========================= 1 failed, 6 passed in 0.62s ==========================
```
