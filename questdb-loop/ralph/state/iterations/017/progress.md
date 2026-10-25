### 2026-10-25 — PRD-08: fix(keymap): avoid mutating HarlequinKeyBinding.__dict__ and validate action names

- **Author**: John DaCosta (`@johndacosta`)
- **State transition**: `SELECT` -> `GRILL` -> `BUILD` -> `VERIFY` -> `PROGRESS`
- **PRD**: [`questdb-loop/prds/PRD-08-keymap-mutation-and-action-validation.md`](../questdb-loop/prds/PRD-08-keymap-mutation-and-action-validation.md)
- **Changes**:
  - Construct new dictionary in HarlequinKeyBinding.to_dict without modifying instance __dict__.
  - Correct error message typo key_profile to key_display in HarlequinKeyMap.from_config.
  - Validate actions exist in HARLEQUIN_ACTIONS in HarlequinKeyMap.from_config.
- **Deterministic commands run**: `uv run python -m compileall -q src/harlequin/keymap.py tests/unit_tests/test_keymap.py; uv run ruff check src/harlequin/keymap.py tests/unit_tests/test_keymap.py; uv run ruff format --check src/harlequin/keymap.py tests/unit_tests/test_keymap.py; uv run mypy src/harlequin/keymap.py tests/unit_tests/test_keymap.py; uv run pytest -m not online tests/unit_tests/test_keymap.py`
- **Outcome**: PASS (all compileall, ruff, mypy, and pytest checks exited 0).

---
