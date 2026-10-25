### 2026-10-25 — PRD-02: fix(autocomplete): normalize completion context to lowercase for member autocomplete

- **Author**: John DaCosta (`@johndacosta`)
- **State transition**: `SELECT` -> `GRILL` -> `BUILD` -> `VERIFY` -> `PROGRESS`
- **PRD**: [`questdb-loop/prds/PRD-02-member-completer-case-sensitivity-bug.md`](../questdb-loop/prds/PRD-02-member-completer-case-sensitivity-bug.md)
- **Changes**:
  - Add cached context_val property to HarlequinCompletion that normalizes context strings to lowercase.
  - Fix MemberCompleter.__call__ to compare c.context_val == match_context so dot-completion works on mixed-case and uppercase database, schema, table, and view names.
  - Add deterministic unit tests in tests/unit_tests/test_completers.py.
- **Deterministic commands run**: `uv run python -m compileall -q src/harlequin/autocomplete/completion.py src/harlequin/autocomplete/completers.py tests/unit_tests/test_completers.py; uv run ruff check src/harlequin/autocomplete/completion.py src/harlequin/autocomplete/completers.py tests/unit_tests/test_completers.py; uv run ruff format --check src/harlequin/autocomplete/completion.py src/harlequin/autocomplete/completers.py tests/unit_tests/test_completers.py; uv run mypy src/harlequin/autocomplete/completion.py src/harlequin/autocomplete/completers.py tests/unit_tests/test_completers.py; uv run pytest -m not online tests/unit_tests/test_completers.py`
- **Outcome**: PASS (all compileall, ruff, mypy, and pytest checks exited 0).

---
