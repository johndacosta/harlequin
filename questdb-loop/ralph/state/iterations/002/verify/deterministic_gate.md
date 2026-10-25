# Deterministic Verification Gate: PRD-01

- **Author**: John DaCosta (`@johndacosta`)
- **Timestamp**: `2026-10-25T02:06:43.230660+00:00`
- **Status**: `FAIL`

| Check | Command | Exit Code | Status |
| :--- | :--- | :---: | :---: |
| `uv run python -m` | `uv run python -m compileall -q src/harlequin_questdb tests/adapter_tests/test_questdb.py tests/adapter_tests/test_questdb_completions.py tests/adapter_tests/test_questdb_docs.py tests/adapter_tests/test_questdb_packaging.py` | `0` | **PASS** |
| `uv run ruff check` | `uv run ruff check src/harlequin_questdb tests/adapter_tests/test_questdb.py tests/adapter_tests/test_questdb_completions.py tests/adapter_tests/test_questdb_docs.py tests/adapter_tests/test_questdb_packaging.py` | `0` | **PASS** |
| `uv run ruff format` | `uv run ruff format --check src/harlequin_questdb tests/adapter_tests/test_questdb.py tests/adapter_tests/test_questdb_completions.py tests/adapter_tests/test_questdb_docs.py tests/adapter_tests/test_questdb_packaging.py` | `0` | **PASS** |
| `uv run mypy src/harlequin_questdb` | `uv run mypy src/harlequin_questdb tests/adapter_tests/test_questdb.py tests/adapter_tests/test_questdb_completions.py tests/adapter_tests/test_questdb_docs.py tests/adapter_tests/test_questdb_packaging.py` | `1` | **FAIL** |
| `uv run pytest -m` | `uv run pytest -m not online tests/adapter_tests/test_questdb.py tests/adapter_tests/test_questdb_completions.py tests/adapter_tests/test_questdb_docs.py tests/adapter_tests/test_questdb_packaging.py` | `0` | **PASS** |

## Output: `uv run ruff check src/harlequin_questdb tests/adapter_tests/test_questdb.py tests/adapter_tests/test_questdb_completions.py tests/adapter_tests/test_questdb_docs.py tests/adapter_tests/test_questdb_packaging.py`
```text
All checks passed!
```

## Output: `uv run ruff format --check src/harlequin_questdb tests/adapter_tests/test_questdb.py tests/adapter_tests/test_questdb_completions.py tests/adapter_tests/test_questdb_docs.py tests/adapter_tests/test_questdb_packaging.py`
```text
10 files already formatted
```

## Output: `uv run mypy src/harlequin_questdb tests/adapter_tests/test_questdb.py tests/adapter_tests/test_questdb_completions.py tests/adapter_tests/test_questdb_docs.py tests/adapter_tests/test_questdb_packaging.py`
```text
tests/adapter_tests/test_questdb.py:43:9: error: Returning Any from function declared to return "dict[str, Any]"  [no-any-return]
tests/adapter_tests/test_questdb.py:50:9: error: Returning Any from function declared to return "dict[str, Any]"  [no-any-return]
tests/adapter_tests/test_questdb.py:450:5: error: Cannot assign to a method  [method-assign]
tests/adapter_tests/test_questdb.py:475:5: error: Cannot assign to a method  [method-assign]
Found 4 errors in 1 file (checked 10 source files)
```

## Output: `uv run pytest -m not online tests/adapter_tests/test_questdb.py tests/adapter_tests/test_questdb_completions.py tests/adapter_tests/test_questdb_docs.py tests/adapter_tests/test_questdb_packaging.py`
```text
============================= test session starts ==============================
platform linux -- Python 3.10.15, pytest-9.0.3, pluggy-1.6.0
rootdir: /home/jdacosta/code/harlequin
configfile: pyproject.toml
plugins: textual-snapshot-0.4.0, asyncio-1.3.0, flaky-3.8.1, syrupy-5.0.0
asyncio: mode=strict, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collected 58 items

tests/adapter_tests/test_questdb.py ............................         [ 48%]
tests/adapter_tests/test_questdb_completions.py ....                     [ 55%]
tests/adapter_tests/test_questdb_docs.py ............                    [ 75%]
tests/adapter_tests/test_questdb_packaging.py ..............             [100%]

======================== 58 passed in 137.76s (0:02:17) ========================
```

