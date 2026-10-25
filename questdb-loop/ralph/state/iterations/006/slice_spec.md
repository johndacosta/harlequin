# PRD-09: Fix `DebugInfoScreen.move_focus()` Crash (`NoMatches`) and `pageup`/`pagedown` Scroll Target

- **Slice ID**: `PRD-09`
- **Category**: Bug Fix (`Bug`)
- **Priority / Severity**: `P0` (Crash on `move_focus` & Broken Keyboard Page Scrolling in Debug Info Screen)
- **Target Branch / PR Scope**: Single atomic commit / PR (`fix(debug-info): fix collapsible selector IDs in move_focus and scroll container in on_key`)

## 1. Problem Statement & Root Cause
In `src/harlequin/components/debug_info.py`:

1. **`NoMatches` Crash in `DebugInfoScreen.move_focus()` (`debug_info.py:279-286`)**:
   `AdapterDebugInfo.parse_info()` (line 185) creates the adapter details `Collapsible` with `id="collapsible-adapter-details-section"`, and `ActiveProfileConfig.compose()` (line 206) creates `id="collapsible-active-profile-config"`.
   However, `DebugInfoScreen.move_focus()` queries a nonexistent selector `#collapsible-client-adapter-details` and omits `#collapsible-active-profile-config`:
   ```python
   focusables = [
       self.query_one("#collapsible-harlequin-System-info").children[0],
       self.query_one("#collapsible-active-cli-flags").children[0],
       self.query_one("#collapsible-client-adapter-details").children[0],
       self.query_one("#collapsible-driver-adapter-details").children[0],
       self.query_one("#return-button"),
   ]
   ```
   Calling `move_focus()` immediately raises `textual.css.query.NoMatches`.
2. **Wrong Scroll Container in `on_mount()` and `on_key()` (`debug_info.py:274, 299-306`)**:
   `on_mount` sets `self.container = self.query_one("#modal_outer")` (a non-scrolling `Vertical`), and `on_key` calls `self.container.scroll_page_up()` / `self.container.scroll_page_down()` instead of scrolling `self.query_one("#debug_info_scroll")` (the `VerticalScroll` widget that actually holds the scrollable content).

## 2. Goals & Non-Goals
### Goals
- Replace `#collapsible-client-adapter-details` with `#collapsible-adapter-details-section` and include `#collapsible-active-profile-config` in `DebugInfoScreen.move_focus()`.
- Scroll `#debug_info_scroll` on `pageup` and `pagedown` in `DebugInfoScreen.on_key()`.
- Add a test verifying `DebugInfoScreen.move_focus()` and `pageup`/`pagedown` work without errors.

### Non-Goals
- Redesigning the visual layout of `DebugInfoScreen`.

## 3. Technical Design & Affected Files
- `src/harlequin/components/debug_info.py`
- `tests/functional_tests/` (or `tests/unit_tests/`)

## 4. Verification & Acceptance Criteria
```bash
uv run pytest tests/
uv run ruff check src/harlequin/components/debug_info.py
uv run mypy src/harlequin/components/debug_info.py
```
