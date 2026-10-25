### 2026-10-25 — PRD-03: perf(autocomplete): index member contexts, deduplicate catalog items, and optimize matching

- **Author**: John DaCosta (`@johndacosta`)
- **State transition**: `SELECT` -> `GRILL` -> `BUILD` -> `VERIFY` -> `PROGRESS`
- **PRD**: [`questdb-loop/prds/PRD-03-autocomplete-indexing-and-fuzzy-perf.md`](../questdb-loop/prds/PRD-03-autocomplete-indexing-and-fuzzy-perf.md)
- **Changes**:
  - Compare priority before label in HarlequinCompletion rich comparison methods.
  - Pre-index MemberCompleter completions by lowercase context in dict lookup.
  - Deduplicate completions on (label, type_label, context_val, value) in completers.
- **Deterministic commands run**: `uv run python -m compileall -q src/harlequin/autocomplete/completion.py src/harlequin/autocomplete/completers.py tests/unit_tests/test_completers.py; uv run ruff check src/harlequin/autocomplete/completion.py src/harlequin/autocomplete/completers.py tests/unit_tests/test_completers.py; uv run ruff format --check src/harlequin/autocomplete/completion.py src/harlequin/autocomplete/completers.py tests/unit_tests/test_completers.py; uv run mypy src/harlequin/autocomplete/completion.py src/harlequin/autocomplete/completers.py tests/unit_tests/test_completers.py; uv run pytest -m not online tests/unit_tests/test_completers.py`
- **Outcome**: PASS (all compileall, ruff, mypy, and pytest checks exited 0).

---
