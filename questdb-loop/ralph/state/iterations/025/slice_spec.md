# PRD-16: Anchor `HarlequinOption` Name Regex Validation, Protect `BUILTIN_THEMES` Mutation, and Use UTF-8 in `HelpScreen`

- **Slice ID**: `PRD-16`
- **Category**: Bug Fix (`Bug`)
- **Priority / Severity**: `P2` (Medium — Broken Regex Validation, Global Dict Mutation, and Encoding Safety)
- **Target Branch / PR Scope**: Single atomic commit / PR (`fix(core): anchor option name regex, copy BUILTIN_THEMES, and specify utf-8 in HelpScreen`)

## 1. Problem Statement & Root Cause
Three small but distinct bugs exist in core Harlequin utilities:

1. **Unanchored Regex in `HarlequinAdapterOption._validate_name` (`src/harlequin/options.py:76-82`)**:
   ```python
   @staticmethod
   def _validate_name(name: str) -> None:
       match = re.match(r"[A-Za-z](\w|-)*", name)
       if match is None:
           raise HarlequinExitError(...)
   ```
   Because `re.match` only anchors at the beginning of the string and the pattern lacks a trailing `$` (or `re.fullmatch`), any string starting with an ASCII letter—such as `"port$invalid!@#"` or `"my option with spaces"`—passes validation!
2. **In-Place Mutation of Textual's Global `BUILTIN_THEMES` Dict (`src/harlequin/colors.py:33-35`)**:
   ```python
   VALID_THEMES = BUILTIN_THEMES
   VALID_THEMES.pop("textual-ansi")
   VALID_THEMES.update({"harlequin": HARLEQUIN_TEXTUAL_THEME})
   ```
   `VALID_THEMES` aliases `textual.theme.BUILTIN_THEMES` directly and pops `"textual-ansi"` without a default. Mutating a third-party library's global dictionary in-place causes side effects and raises `KeyError: 'textual-ansi'` if the module is ever reloaded.
3. **Missing `encoding="utf-8"` When Opening `help_screen.md` (`src/harlequin/components/help_screen.py:22-24`)**:
   ```python
   markdown_path = Path(__file__).parent / "help_screen.md"
   with open(markdown_path, "r") as f:
       markdown = f.read()
   ```
   Opening `help_screen.md` without `encoding="utf-8"` uses the platform locale encoding (such as `cp1252` on Windows), which can fail or corrupt non-ASCII punctuation.

## 2. Goals & Non-Goals
### Goals
- Use `re.fullmatch(r"[A-Za-z](\w|-)*", name)` in `HarlequinAdapterOption._validate_name`.
- Copy `BUILTIN_THEMES` (`VALID_THEMES = dict(BUILTIN_THEMES)`) and use `VALID_THEMES.pop("textual-ansi", None)` in `src/harlequin/colors.py`.
- Use `markdown_path.read_text(encoding="utf-8")` in `src/harlequin/components/help_screen.py`.
- Add unit tests in `tests/unit_tests/` verifying `_validate_name` rejects invalid trailing characters.

### Non-Goals
- Changing valid adapter option names or theme definitions.

## 3. Technical Design & Affected Files
- `src/harlequin/options.py`
- `src/harlequin/colors.py`
- `src/harlequin/components/help_screen.py`
- `tests/unit_tests/`

## 4. Verification & Acceptance Criteria
```bash
uv run pytest tests/unit_tests/
uv run ruff check src/harlequin/options.py src/harlequin/colors.py src/harlequin/components/help_screen.py
uv run mypy src/harlequin/options.py src/harlequin/colors.py src/harlequin/components/help_screen.py
```
