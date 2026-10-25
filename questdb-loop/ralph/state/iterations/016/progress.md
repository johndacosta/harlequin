### 2026-10-25 — PRD-07: fix(options): return option value instead of label in SelectOption._flat_choices

- **Author**: John DaCosta (`@johndacosta`)
- **State transition**: `SELECT` -> `GRILL` -> `BUILD` -> `VERIFY` -> `PROGRESS`
- **PRD**: [`questdb-loop/prds/PRD-07-select-option-flat-choices-bug.md`](../questdb-loop/prds/PRD-07-select-option-flat-choices-bug.md)
- **Changes**:
  - Yield choice[1] (underlying value) in SelectOption._flat_choices for tuple choices.
  - Add test_select_option_tuple_choices validating both options pass click parsing without error.
- **Deterministic commands run**: `uv run python -m compileall -q src/harlequin/options.py tests/unit_tests/test_options.py; uv run ruff check src/harlequin/options.py tests/unit_tests/test_options.py; uv run ruff format --check src/harlequin/options.py tests/unit_tests/test_options.py; uv run mypy src/harlequin/options.py tests/unit_tests/test_options.py; uv run pytest -m not online tests/unit_tests/test_options.py`
- **Outcome**: PASS (all compileall, ruff, mypy, and pytest checks exited 0).

---
