### 2026-10-25 — PRD-15: fix(cache): atomic cache writes, handle truncated pickles, and guard empty editor buffers

- **Author**: John DaCosta (`@johndacosta`)
- **State transition**: `SELECT` -> `GRILL` -> `BUILD` -> `VERIFY` -> `PROGRESS`
- **PRD**: [`questdb-loop/prds/PRD-15-atomic-cache-writes-and-eof-resilience.md`](../questdb-loop/prds/PRD-15-atomic-cache-writes-and-eof-resilience.md)
- **Changes**:
  - Write editor and catalog caches atomically via temporary files and os.replace.
  - Catch EOFError, UnpicklingError, and corrupt file exceptions in load_cache.
  - Guard empty buffer lists in action_quit and EditorCollection.on_mount.
- **Deterministic commands run**: `uv run python -m compileall -q src/harlequin/editor_cache.py src/harlequin/catalog_cache.py src/harlequin/app.py src/harlequin/components/code_editor.py tests/functional_tests/test_cache.py; uv run ruff check src/harlequin/editor_cache.py src/harlequin/catalog_cache.py src/harlequin/app.py src/harlequin/components/code_editor.py tests/functional_tests/test_cache.py; uv run ruff format --check src/harlequin/editor_cache.py src/harlequin/catalog_cache.py src/harlequin/app.py src/harlequin/components/code_editor.py tests/functional_tests/test_cache.py; uv run mypy src/harlequin/editor_cache.py src/harlequin/catalog_cache.py src/harlequin/app.py src/harlequin/components/code_editor.py tests/functional_tests/test_cache.py; uv run pytest -m not online tests/functional_tests/test_cache.py`
- **Outcome**: PASS (all compileall, ruff, mypy, and pytest checks exited 0).

---
