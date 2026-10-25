### 2026-10-25 — PRD-20: fix(config): guard missing profiles key in schema check and close tarfile/urlopen in windows_timezone

- **Author**: John DaCosta (`@johndacosta`)
- **State transition**: `SELECT` -> `GRILL` -> `BUILD` -> `VERIFY` -> `PROGRESS`
- **PRD**: [`questdb-loop/prds/PRD-20-config-missing-profiles-and-windows-tz-leak.md`](../questdb-loop/prds/PRD-20-config-missing-profiles-and-windows-tz-leak.md)
- **Changes**:
  - Guard missing profiles key in Harlequin config schema validation to avoid unhandled KeyError.
  - Wrap urlopen and tarfile handles in context managers in windows_timezone.py.
- **Deterministic commands run**: `uv run python -m compileall -q src/harlequin/config.py src/harlequin/windows_timezone.py tests/unit_tests/test_config.py; uv run ruff check src/harlequin/config.py src/harlequin/windows_timezone.py tests/unit_tests/test_config.py; uv run ruff format --check src/harlequin/config.py src/harlequin/windows_timezone.py tests/unit_tests/test_config.py; uv run mypy src/harlequin/config.py src/harlequin/windows_timezone.py tests/unit_tests/test_config.py; uv run pytest -m not online tests/unit_tests/test_config.py`
- **Outcome**: PASS (all compileall, ruff, mypy, and pytest checks exited 0).

---
