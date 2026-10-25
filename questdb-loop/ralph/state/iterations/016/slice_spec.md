# PRD-07: Fix `SelectOption._flat_choices()` Returning Display Label Instead of Value for Tuple Choices

- **Slice ID**: `PRD-07`
- **Category**: Bug Fix (`Bug`)
- **Priority / Severity**: `P1` (High — Broken CLI & Wizard Choice Validation for Tuple `SelectOption`s)
- **Target Branch / PR Scope**: Single atomic commit / PR (`fix(options): return option value instead of label in SelectOption._flat_choices`)

## 1. Problem Statement & Root Cause
`SelectOption` in `src/harlequin/options.py` supports `choices: Sequence[str | tuple[str, str]]`, where a tuple represents `(display_label, underlying_value)`.

1. In `SelectOption.to_widgets()` (`src/harlequin/options.py:511-520`), tuple choices are handled as `(label, value)`:
   ```python
   options=[
       choice if isinstance(choice, tuple) else (choice, choice)
       for choice in self.choices
   ]
   ```
   (Textual's `Select` widget expects `(prompt_label, value)` tuples, and `copy_formats.py:58-63` passes `[("No compression", "none"), ("ZSTD", "zstd"), ...]`).
2. However, in `SelectOption._flat_choices()` (`src/harlequin/options.py:543-550`):
   ```python
   def _flat_choices(self) -> list[str]:
       flat = []
       for choice in self.choices:
           if isinstance(choice, str):
               flat.append(choice)
           else:
               flat.append(choice[0])
       return flat
   ```
   `_flat_choices()` appends `choice[0]` (the human display label, e.g. `"No compression"`) instead of `choice[1]` (the value, e.g. `"none"`), while `SelectOption.default` holds the value (`"none"` or `"zstd"`).
3. As a result, `to_click()` and `to_questionary()` validate against display labels instead of values, causing `default` lookup and CLI option parsing to fail whenever an adapter or copy format uses `(label, value)` tuples in `SelectOption`.

## 2. Goals & Non-Goals
### Goals
- Fix `SelectOption._flat_choices()` to append `choice[1]` for tuple choices.
- Add unit tests in `tests/unit_tests/test_options.py` verifying `SelectOption` with `(label, value)` tuples works in `to_widgets()`, `to_click()`, and `_flat_choices()`.

### Non-Goals
- Changing `Textual` `Select` widget behavior.

## 3. Technical Design & Affected Files
- `src/harlequin/options.py`
- `tests/unit_tests/test_options.py` (new or extended test file)

### Proposed Changes
In `src/harlequin/options.py:543-550`:
```python
def _flat_choices(self) -> list[str]:
    flat = []
    for choice in self.choices:
        if isinstance(choice, str):
            flat.append(choice)
        else:
            flat.append(choice[1])
    return flat
```

## 4. Verification & Acceptance Criteria
```bash
uv run pytest tests/unit_tests/
uv run ruff check src/harlequin/options.py tests/unit_tests/
uv run mypy src/harlequin/options.py tests/unit_tests/
```
