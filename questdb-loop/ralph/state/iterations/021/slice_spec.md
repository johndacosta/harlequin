# PRD-15: Atomic Cache File Writes, Corrupt/Truncated Pickle Resilience, and Empty Editor Buffer Guard

- **Slice ID**: `PRD-15`
- **Category**: Bug Fix & Reliability (`Bug`)
- **Priority / Severity**: `P1` (High — Startup Crash on Truncated/Empty Cache & UnboundLocalError on Early Quit)
- **Target Branch / PR Scope**: Single atomic commit / PR (`fix(cache): atomic cache writes, handle truncated pickles, and guard empty editor buffers`)

## 1. Problem Statement & Root Cause
Harlequin persists editor buffers (`src/harlequin/editor_cache.py`) and data catalog trees (`src/harlequin/catalog_cache.py`) to disk using `pickle`:

1. **Unhandled `EOFError` / `AttributeError` / `ImportError` on Truncated or Incompatible Pickle (`editor_cache.py:43-50`, `catalog_cache.py:127-134`)**:
   When a pickle file is 0 bytes or truncated (due to a crash or concurrent process exit), `pickle.load(f)` raises `EOFError` (not a subclass of `pickle.UnpicklingError`), crashing Harlequin on startup.
2. **Non-Atomic Direct Overwrites in `write_cache` (`editor_cache.py:58-64`, `catalog_cache.py:143-147`)**:
   `with open(cache_file, "wb") as f: pickle.dump(...)` truncates the live cache file in-place before serializing.
3. **`UnboundLocalError: focus_index` in `Harlequin.action_quit` & `NoMatches` on Empty Cached `buffers` (`app.py:953-959`, `code_editor.py:241-253`)**:
   - In `Harlequin.action_quit` (`app.py:954-959`), if `self.editor_collection.all_editors` is empty (e.g., quitting before `Lazy` mounts `EditorCollection`), `focus_index` is never assigned and raises `UnboundLocalError`!
   - If `Cache(focus_index=0, buffers=[])` is ever written, `EditorCollection.on_mount` (`code_editor.py:242`) checks `if self.startup_cache is not None:` without checking `and self.startup_cache.buffers:`, creating 0 tabs and crashing on `self.current_editor` with `NoMatches`.

## 2. Goals & Non-Goals
### Goals
- Catch `(pickle.UnpicklingError, EOFError, AttributeError, ImportError, ValueError, IndexError, TypeError, OSError)` in `editor_cache.load_cache()` and `catalog_cache.get_catalog_cache()`.
- Write pickle data to a temporary sibling file (`NamedTemporaryFile(dir=cache_file.parent, delete=False)`) and atomically replace `cache_file` via `Path(tmp_name).replace(cache_file)`.
- Initialize `focus_index = 0` in `Harlequin.action_quit` and only write the editor cache when `buffers` is non-empty; check `if self.startup_cache is not None and self.startup_cache.buffers:` in `EditorCollection.on_mount`.
- Add unit tests in `tests/unit_tests/` and `tests/functional_tests/test_cache.py`.

### Non-Goals
- Changing the cache schema version or migrating away from `pickle`.

## 3. Technical Design & Affected Files
- `src/harlequin/editor_cache.py`
- `src/harlequin/catalog_cache.py`
- `src/harlequin/app.py`
- `src/harlequin/components/code_editor.py`
- `tests/functional_tests/test_cache.py`

## 4. Verification & Acceptance Criteria
```bash
uv run pytest tests/functional_tests/test_cache.py tests/unit_tests/
uv run ruff check src/harlequin/editor_cache.py src/harlequin/catalog_cache.py src/harlequin/app.py src/harlequin/components/code_editor.py
uv run mypy src/harlequin/editor_cache.py src/harlequin/catalog_cache.py src/harlequin/app.py src/harlequin/components/code_editor.py
```
