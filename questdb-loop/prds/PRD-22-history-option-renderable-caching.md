# PRD-22: Cache `HistoryOption` Rich Renderable at Initialization Instead of Rebuilding on Every Property Access

- **Slice ID**: `PRD-22`
- **Category**: Performance Improvement (`Performance`)
- **Priority / Severity**: `P2` (Medium — Repeated Rich Layout Allocation During History Screen Measurement & Scrolling)
- **Target Branch / PR Scope**: Single atomic commit / PR (`perf(history): precompute HistoryOption prompt renderable on init`)

## 1. Problem Statement & Root Cause
In `src/harlequin/components/history_screen.py` (lines 28-77):
- `HistoryOption` defines `@property def prompt(self) -> Padding:` which calls `strftime`, `splitlines`, `Text.assemble`, `Columns`, `Group`, and `Padding` on **every access** to `option.prompt` (as well as in `__rich__` and `visualize`).
- Textual's `OptionList` accesses `.prompt` repeatedly across all options (up to 500 `QueryExecution` items) when mounting, measuring heights, and scrolling the History Screen, allocating thousands of transient Rich `Text`, `Columns`, `Group`, and `Padding` objects for immutable history entries.

## 2. Goals & Non-Goals
### Goals
- Precompute the `Padding` renderable once in `HistoryOption.__init__` (storing `self._prompt` or passing `prompt` to `super().__init__(prompt=...)`) so accessing `.prompt`, `__rich__()`, and `visualize()` returns the cached Rich renderable in $O(1)$ with zero allocations.

### Non-Goals
- Changing the visual appearance or snapshot output of `HistoryScreen`.

## 3. Technical Design & Affected Files
- `src/harlequin/components/history_screen.py`
- `tests/functional_tests/test_history_screen.py`

## 4. Verification & Acceptance Criteria
```bash
uv run pytest tests/functional_tests/test_history_screen.py
uv run ruff check src/harlequin/components/history_screen.py
uv run mypy src/harlequin/components/history_screen.py
```
