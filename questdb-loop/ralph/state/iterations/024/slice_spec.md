# PRD-20: Fix `config._raise_on_bad_schema` `KeyError: 'profiles'` and `windows_timezone.py` Resource Leaks

- **Slice ID**: `PRD-20`
- **Category**: Bug Fix (`Bug`)
- **Priority / Severity**: `P1` (High — Unhandled `KeyError` on Config File Without `[profiles]` & Windows File Lock Leak)
- **Target Branch / PR Scope**: Single atomic commit / PR (`fix(config): guard missing profiles key in schema check and close tarfile/urlopen in windows_timezone`)

## 1. Problem Statement & Root Cause
1. **Unhandled `KeyError: 'profiles'` in `src/harlequin/config.py` (lines 212-214, 272-283)**:
   Line 212 permits a TOML config file where `config.get("profiles", None) is None`. However, lines 272-278 execute:
   ```python
   elif (
       default is not None
       and isinstance(default, str)
       and isinstance(config["profiles"], dict)
       and default != "None"
       and config["profiles"].get(default, None) is None
   ):
   ```
   If a user's config file sets `default_profile = "my_profile"` without defining a `[profiles]` table, `config["profiles"]` raises an uncaught `KeyError: 'profiles'` instead of raising `HarlequinConfigError`!
2. **Unclosed `TarFile` and `urlopen` Handles in `src/harlequin/windows_timezone.py` (lines 42-56)**:
   `tarfile.open(tar_path).extractall(HARLEQUIN_TZ_DATA_PATH)` opens `tar_path` inside `with TemporaryDirectory() as tmpdir:` without closing the `TarFile`. On Windows, leaving a file handle open inside `TemporaryDirectory` causes `TemporaryDirectory.__exit__` to fail with `PermissionError: [WinError 32]` when deleting `tmpdir`. `urlopen(...)` responses are also opened without `with` context managers.

## 2. Goals & Non-Goals
### Goals
- Use `config.get("profiles", None)` safely in `_raise_on_bad_schema` so setting `default_profile` without `[profiles]` raises `HarlequinConfigError`.
- Wrap `urlopen(...)` and `tarfile.open(tar_path)` in `with` context managers in `src/harlequin/windows_timezone.py`.
- Add a unit test in `tests/unit_tests/test_config.py` covering `default_profile = "foo"` with no `[profiles]` section.

### Non-Goals
- Changing the TOML configuration format.

## 3. Technical Design & Affected Files
- `src/harlequin/config.py`
- `src/harlequin/windows_timezone.py`
- `tests/unit_tests/test_config.py`

## 4. Verification & Acceptance Criteria
```bash
uv run pytest tests/unit_tests/test_config.py
uv run ruff check src/harlequin/config.py src/harlequin/windows_timezone.py tests/unit_tests/test_config.py
uv run mypy src/harlequin/config.py src/harlequin/windows_timezone.py tests/unit_tests/test_config.py
```
