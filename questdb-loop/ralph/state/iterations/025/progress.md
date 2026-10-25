### 2026-10-25 — PRD-16: fix(core): anchor option name regex, copy BUILTIN_THEMES, and specify utf-8 in HelpScreen

- **Author**: John DaCosta (`@johndacosta`)
- **State transition**: `SELECT` -> `GRILL` -> `BUILD` -> `VERIFY` -> `PROGRESS`
- **PRD**: [`questdb-loop/prds/PRD-16-option-name-regex-and-core-hygiene.md`](../questdb-loop/prds/PRD-16-option-name-regex-and-core-hygiene.md)
- **Changes**:
  - Anchor HarlequinOption name validation regex with re.fullmatch to reject trailing invalid characters.
  - Copy BUILTIN_THEMES in colors.py to prevent mutating Textual's global theme registry.
  - Specify utf-8 encoding when reading HelpScreen markdown documentation.
- **Deterministic commands run**: `uv run python -m compileall -q src/harlequin/options.py src/harlequin/colors.py src/harlequin/components/help_screen.py tests/unit_tests/test_options.py; uv run ruff check src/harlequin/options.py src/harlequin/colors.py src/harlequin/components/help_screen.py tests/unit_tests/test_options.py; uv run ruff format --check src/harlequin/options.py src/harlequin/colors.py src/harlequin/components/help_screen.py tests/unit_tests/test_options.py; uv run mypy src/harlequin/options.py src/harlequin/colors.py src/harlequin/components/help_screen.py tests/unit_tests/test_options.py; uv run pytest -m not online tests/unit_tests/test_options.py`
- **Outcome**: PASS (all compileall, ruff, mypy, and pytest checks exited 0).

---
