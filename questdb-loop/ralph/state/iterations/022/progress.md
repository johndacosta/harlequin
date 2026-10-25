### 2026-10-25 — PRD-18: fix(editor): stop selected_queries at semicolon boundary when selection ends at separator

- **Author**: John DaCosta (`@johndacosta`)
- **State transition**: `SELECT` -> `GRILL` -> `BUILD` -> `VERIFY` -> `PROGRESS`
- **PRD**: [`questdb-loop/prds/PRD-18-code-editor-selected-queries-semicolon-boundary.md`](../questdb-loop/prds/PRD-18-code-editor-selected-queries-semicolon-boundary.md)
- **Changes**:
  - Halt query expansion at semicolon boundaries when selection ends at separator in selected_queries.
  - Add deterministic tests in test_code_editor.py verifying multi-query boundary selection.
- **Deterministic commands run**: `uv run python -m compileall -q src/harlequin/components/code_editor.py tests/functional_tests/test_code_editor.py; uv run ruff check src/harlequin/components/code_editor.py tests/functional_tests/test_code_editor.py; uv run ruff format --check src/harlequin/components/code_editor.py tests/functional_tests/test_code_editor.py; uv run mypy src/harlequin/components/code_editor.py tests/functional_tests/test_code_editor.py; uv run pytest -m not online tests/functional_tests/test_code_editor.py`
- **Outcome**: PASS (all compileall, ruff, mypy, and pytest checks exited 0).

---
