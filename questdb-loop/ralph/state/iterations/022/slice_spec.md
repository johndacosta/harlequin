# PRD-18: Fix `CodeEditor.selected_queries()` Executing Subsequent Query When Cursor or Selection Ends at Semicolon

- **Slice ID**: `PRD-18`
- **Category**: Bug Fix (`Bug`)
- **Priority / Severity**: `P1` (High — Unintended Execution of Next SQL Statement After Semicolon)
- **Target Branch / PR Scope**: Single atomic commit / PR (`fix(editor): stop selected_queries at semicolon boundary when selection ends at separator`)

## 1. Problem Statement & Root Cause
In `src/harlequin/components/code_editor.py` (lines 56-66):

```python
query_start = (0, 0)
for query_end in [*separators, self.text_input.document.end]:
    if query_start > self.selection.end:
        break
    q = self.text_input.get_text_range(start=query_start, end=query_end).strip()
    if q and query_end >= self.selection.start:
        queries.append(q)
    elif q:
        prev_query = q
    query_start = query_end
```

Each element of `separators` is the `(row, col)` position **immediately after** a `;` token (`n.end_point`).
Suppose the editor contains `select 1; select 2;` (where the first `;` ends at `(0, 9)`):
- When the user places their cursor right after the first semicolon (`select 1;| select 2;`, so `selection.start == selection.end == (0, 9)`), OR selects the first query including its trailing semicolon (`[select 1;] select 2;`, so `selection.start == (0, 0), selection.end == (0, 9)`):
  - Iteration 1 (`query_start = (0, 0)`, `query_end = (0, 9)`): appends `"select 1;"` and sets `query_start = (0, 9)`.
  - Iteration 2 (`query_start = (0, 9)`, `query_end = (0, 19)`): `if query_start > self.selection.end:` evaluates `(0, 9) > (0, 9)` -> `False`! And `query_end >= self.selection.start` evaluates `(0, 19) >= (0, 9)` -> `True`! So it **also** appends `"select 2;"`!
- Pressing `Ctrl+Enter` with the cursor at the end of `select 1;|` or with `select 1;` selected unexpectedly executes the second statement (`select 2;`, which could be a `DROP` or `DELETE` statement!).

## 2. Goals & Non-Goals
### Goals
- Break out of the separator loop in `CodeEditor.selected_queries()` when `query_start > self.selection.end or (queries and query_start == self.selection.end)`.
- Add regression tests in `tests/functional_tests/test_app.py` (or `test_code_editor.py`) covering cursor at `select 1;| select 2;` and selection `[select 1;] select 2;`.

### Non-Goals
- Changing Tree-sitter SQL grammar parsing.

## 3. Technical Design & Affected Files
- `src/harlequin/components/code_editor.py`
- `tests/functional_tests/test_app.py`

## 4. Verification & Acceptance Criteria
```bash
uv run pytest tests/functional_tests/test_app.py tests/functional_tests/test_code_editor.py
uv run ruff check src/harlequin/components/code_editor.py
uv run mypy src/harlequin/components/code_editor.py
```
