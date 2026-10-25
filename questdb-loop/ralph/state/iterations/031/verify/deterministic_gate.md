# Deterministic Verification Gate: PRD-13

- **Author**: John DaCosta (`@johndacosta`)
- **Timestamp**: `2026-10-25T03:06:28.690913+00:00`
- **Status**: `PASS`

| Check | Command | Exit Code | Status |
| :--- | :--- | :---: | :---: |
| `uv run python -m` | `uv run python -m compileall -q src/harlequin_questdb/adapter.py tests/adapter_tests/test_questdb.py` | `0` | **PASS** |
| `uv run ruff check` | `uv run ruff check src/harlequin_questdb/adapter.py tests/adapter_tests/test_questdb.py` | `0` | **PASS** |
| `uv run ruff format` | `uv run ruff format --check src/harlequin_questdb/adapter.py tests/adapter_tests/test_questdb.py` | `0` | **PASS** |
| `uv run mypy src/harlequin_questdb/adapter.py` | `uv run mypy src/harlequin_questdb/adapter.py tests/adapter_tests/test_questdb.py` | `0` | **PASS** |
| `uv run pytest -m` | `uv run pytest -m not online tests/adapter_tests/test_questdb.py -k test_worker_connection_reuse_and_autocommit` | `0` | **PASS** |

## Output: `uv run ruff check src/harlequin_questdb/adapter.py tests/adapter_tests/test_questdb.py`
```text
All checks passed!
```

## Output: `uv run ruff format --check src/harlequin_questdb/adapter.py tests/adapter_tests/test_questdb.py`
```text
2 files already formatted
```

## Output: `uv run mypy src/harlequin_questdb/adapter.py tests/adapter_tests/test_questdb.py`
```text
Success: no issues found in 2 source files
```

## Output: `uv run pytest -m not online tests/adapter_tests/test_questdb.py -k test_worker_connection_reuse_and_autocommit`
```text
============================= test session starts ==============================
platform linux -- Python 3.10.15, pytest-9.0.3, pluggy-1.6.0
rootdir: /home/jdacosta/code/harlequin
configfile: pyproject.toml
plugins: textual-snapshot-0.4.0, asyncio-1.3.0, flaky-3.8.1, syrupy-5.0.0
asyncio: mode=strict, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collected 32 items / 31 deselected / 1 selected

tests/adapter_tests/test_questdb.py .                                    [100%]

======================= 1 passed, 31 deselected in 0.06s =======================
```

