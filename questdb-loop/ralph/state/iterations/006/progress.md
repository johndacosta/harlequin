### 2026-10-25 — PRD-09: fix(debug-info): fix collapsible selector IDs in move_focus and scroll container in on_key

- **Author**: John DaCosta (`@johndacosta`)
- **State transition**: `SELECT` -> `GRILL` -> `BUILD` -> `VERIFY` -> `PROGRESS`
- **PRD**: [`questdb-loop/prds/PRD-09-debug-info-focus-crash-fix.md`](../questdb-loop/prds/PRD-09-debug-info-focus-crash-fix.md)
- **Changes**:
  - Fix DebugInfoScreen.move_focus to query existing collapsible IDs (#collapsible-active-profile-config and #collapsible-adapter-details-section) instead of nonexistent #collapsible-client-adapter-details.
  - Fix DebugInfoScreen.on_mount and DebugInfoScreen.on_key to scroll the VerticalScroll (#debug_info_scroll) container on pageup and pagedown.
  - Add deterministic async widget tests in tests/unit_tests/test_debug_info.py.
- **Deterministic commands run**: `uv run python -m compileall -q src/harlequin/components/debug_info.py tests/unit_tests/test_debug_info.py; uv run ruff check src/harlequin/components/debug_info.py tests/unit_tests/test_debug_info.py; uv run ruff format --check src/harlequin/components/debug_info.py tests/unit_tests/test_debug_info.py; uv run mypy src/harlequin/components/debug_info.py tests/unit_tests/test_debug_info.py; uv run pytest -m not online tests/unit_tests/test_debug_info.py`
- **Outcome**: PASS (all compileall, ruff, mypy, and pytest checks exited 0).

---
