# PRD-02: Fix `MemberCompleter` Case-Sensitivity Bug on Identifier Contexts

- **Slice ID**: `PRD-02`
- **Category**: Bug Fix (`Bug`)
- **Priority / Severity**: `P1` (High — Broken Autocomplete for Uppercase/Mixed-Case Identifiers)
- **Target Branch / PR Scope**: Single atomic commit / PR (`fix(autocomplete): normalize completion context to lowercase for member autocomplete`)

## 1. Problem Statement & Root Cause
Dot-qualified member autocomplete (e.g., typing `MySchema.` or `MyTable.` in the Query Editor) fails to suggest any child tables or columns whenever the parent catalog item's label contains uppercase characters:

1. In `src/harlequin/autocomplete/completers.py` lines 224, 241, and 265, `_build_children_completions` constructs `HarlequinCompletion` objects with `context=item.label` (preserving original case, such as `"MyTable"` or `"Information_Schema"`).
2. In `src/harlequin/autocomplete/completion.py` lines 20-35, `HarlequinCompletion.__init__` sets `self.match_val = label.lower()`, but stores `self.context = context` without lowercasing it.
3. In `src/harlequin/autocomplete/completers.py` lines 141-148, `MemberCompleter.__call__` normalizes the user's typed prefix via:
   ```python
   match_context = context.strip("'`\"").lower()
   context_matches = [
       c for c in self.completions if c.context == match_context
   ]
   ```
4. Because `match_context` is always lowercase while `c.context` retains uppercase characters from `item.label`, `c.context == match_context` evaluates to `False` for every database, schema, table, or view whose name is not strictly lowercase!

## 2. Goals & Non-Goals
### Goals
- Normalize `HarlequinCompletion.context` (or `c.context` comparison) to lowercase so dot-completion (`MySchema.`, `"MyTable".`, `MY_DB.`) works regardless of identifier casing.
- Add unit tests in `tests/unit_tests/` verifying `MemberCompleter` returns child completions for mixed-case and uppercase schema/table contexts (both quoted and unquoted).

### Non-Goals
- Algorithmic indexing and fuzzy-matching performance optimizations (tracked in `PRD-03`).

## 3. Technical Design & Affected Files
- `src/harlequin/autocomplete/completion.py`
- `src/harlequin/autocomplete/completers.py`
- `tests/unit_tests/test_completers.py` (new or extended test module)

### Proposed Changes
1. In `HarlequinCompletion.__init__` (`src/harlequin/autocomplete/completion.py:29-35`), normalize `self.context`:
   ```python
   self.context = context.lower() if context is not None else None
   ```
   (or normalize at comparison/indexing time in `MemberCompleter` while keeping `context.lower()` consistent).
2. Add regression tests in `tests/unit_tests/test_completers.py` constructing a `Catalog` with mixed-case labels (`"MyDatabase"`, `"MySchema"`, `"MyTable"`, `"MyColumn"`) and asserting `member_completer(context="MyTable", prefix="")` and `member_completer(context='"MyTable"', prefix="my")` return `"MyColumn"`.

## 4. Verification & Acceptance Criteria
```bash
uv run pytest tests/unit_tests/test_completers.py
uv run ruff check src/harlequin/autocomplete tests/unit_tests
uv run mypy src/harlequin/autocomplete tests/unit_tests
```
