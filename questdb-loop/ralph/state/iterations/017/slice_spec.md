# PRD-08: Fix `HarlequinKeyBinding.to_dict()` Instance Mutation and Validate Keymap Actions

- **Slice ID**: `PRD-08`
- **Category**: Bug Fix (`Bug`)
- **Priority / Severity**: `P1` (High — Destructive Object Mutation & Unhandled `KeyError` on Invalid Config Action)
- **Target Branch / PR Scope**: Single atomic commit / PR (`fix(keymap): avoid mutating HarlequinKeyBinding.__dict__ and validate action names`)

## 1. Problem Statement & Root Cause
Three bugs exist in `src/harlequin/keymap.py`:

1. **Destructive Mutation of `self.__dict__` in `HarlequinKeyBinding.to_dict()` (`keymap.py:41-45`)**:
   ```python
   def to_dict(self) -> RawKeyBinding:
       all_keys: RawKeyBinding = self.__dict__  # type: ignore[assignment]
       if not self.key_display:
           all_keys.pop("key_display")
       return all_keys
   ```
   Because `all_keys` is a direct reference to `self.__dict__` (not a copy), calling `all_keys.pop("key_display")` **deletes the `key_display` attribute from the `HarlequinKeyBinding` instance itself**! Any subsequent access to `binding.key_display` (or calling `to_dict()` a second time!) raises `AttributeError: 'HarlequinKeyBinding' object has no attribute 'key_display'`.
2. **Incorrect Property Name in Error Message (`keymap.py:64-68`)**:
   ```python
   raise HarlequinConfigError(
       f"Cannot load keymap from {repr(raw)}. Key bindings definitions "
       "may contain only three properties: `keys`, `action`, and `key_profile`.",
       title="Harlequin could not load the configured keymap.",
   )
   ```
   The third property is `key_display`, not `key_profile`.
3. **Missing Action Name Validation in `HarlequinKeyMap.from_config()` (`keymap.py:93-128`)**:
   If a user defines a custom keybinding in `.harlequin.toml` with a misspelled `action` (e.g. `action = "code_editor.run_qurey"`), `from_config()` accepts it without validation, and Harlequin later crashes with an unhandled `KeyError` in `src/harlequin/app.py:731` / `835` or `src/harlequin/keys_app.py:497` when indexing `HARLEQUIN_ACTIONS[b.action]`.

## 2. Goals & Non-Goals
### Goals
- Fix `HarlequinKeyBinding.to_dict()` to construct a new dictionary (or copy `self.__dict__`) so calling `to_dict()` is idempotent and never mutates the instance.
- Fix the typo in `HarlequinKeyBinding.from_config()` error message (`key_display` instead of `key_profile`).
- Validate `binding.action in HARLEQUIN_ACTIONS` inside `HarlequinKeyBinding.from_config()`, raising a clear `HarlequinConfigError` when an unknown action is configured.
- Add unit tests in `tests/unit_tests/test_keymap.py`.

### Non-Goals
- Adding new keymap actions or modifying built-in key bindings.

## 3. Technical Design & Affected Files
- `src/harlequin/keymap.py`
- `tests/unit_tests/test_keymap.py`

### Proposed Changes
1. In `HarlequinKeyBinding.to_dict()` (`src/harlequin/keymap.py:41-45`):
   ```python
   def to_dict(self) -> RawKeyBinding:
       result: RawKeyBinding = {
           "keys": self.keys,
           "action": self.action,
       }
       if self.key_display:
           result["key_display"] = self.key_display
       return result
   ```
2. In `HarlequinKeyBinding.from_config()` (`src/harlequin/keymap.py:64-72`), fix the error message to say `` `keys`, `action`, and `key_display` `` and validate `raw["action"] in HARLEQUIN_ACTIONS` (raising `HarlequinConfigError` with a helpful message if unknown).

## 4. Verification & Acceptance Criteria
```bash
uv run pytest tests/unit_tests/test_keymap.py
uv run ruff check src/harlequin/keymap.py tests/unit_tests/test_keymap.py
uv run mypy src/harlequin/keymap.py tests/unit_tests/test_keymap.py
```
