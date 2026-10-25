# Deterministic Verification Gate: PRD-15

- **Author**: John DaCosta (`@johndacosta`)
- **Timestamp**: `2026-10-25T03:05:51.612906+00:00`
- **Status**: `PASS`

| Check | Command | Exit Code | Status |
| :--- | :--- | :---: | :---: |
| `uv run python -m` | `uv run python -m compileall -q src/harlequin/editor_cache.py src/harlequin/catalog_cache.py src/harlequin/app.py src/harlequin/components/code_editor.py tests/functional_tests/test_cache.py` | `0` | **PASS** |
| `uv run ruff check` | `uv run ruff check src/harlequin/editor_cache.py src/harlequin/catalog_cache.py src/harlequin/app.py src/harlequin/components/code_editor.py tests/functional_tests/test_cache.py` | `0` | **PASS** |
| `uv run ruff format` | `uv run ruff format --check src/harlequin/editor_cache.py src/harlequin/catalog_cache.py src/harlequin/app.py src/harlequin/components/code_editor.py tests/functional_tests/test_cache.py` | `0` | **PASS** |
| `uv run mypy src/harlequin/editor_cache.py` | `uv run mypy src/harlequin/editor_cache.py src/harlequin/catalog_cache.py src/harlequin/app.py src/harlequin/components/code_editor.py tests/functional_tests/test_cache.py` | `0` | **PASS** |
| `uv run pytest -m` | `uv run pytest -m not online tests/functional_tests/test_cache.py` | `0` | **PASS** |

## Output: `uv run ruff check src/harlequin/editor_cache.py src/harlequin/catalog_cache.py src/harlequin/app.py src/harlequin/components/code_editor.py tests/functional_tests/test_cache.py`
```text
All checks passed!
```

## Output: `uv run ruff format --check src/harlequin/editor_cache.py src/harlequin/catalog_cache.py src/harlequin/app.py src/harlequin/components/code_editor.py tests/functional_tests/test_cache.py`
```text
5 files already formatted
```

## Output: `uv run mypy src/harlequin/editor_cache.py src/harlequin/catalog_cache.py src/harlequin/app.py src/harlequin/components/code_editor.py tests/functional_tests/test_cache.py`
```text
Success: no issues found in 5 source files
```

## Output: `uv run pytest -m not online tests/functional_tests/test_cache.py`
```text
============================= test session starts ==============================
platform linux -- Python 3.10.15, pytest-9.0.3, pluggy-1.6.0
rootdir: /home/jdacosta/code/harlequin
configfile: pyproject.toml
plugins: textual-snapshot-0.4.0, asyncio-1.3.0, flaky-3.8.1, syrupy-5.0.0
asyncio: mode=strict, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collected 5 items

tests/functional_tests/test_cache.py .....                               [100%]

============================== 5 passed in 2.70s ===============================
```

