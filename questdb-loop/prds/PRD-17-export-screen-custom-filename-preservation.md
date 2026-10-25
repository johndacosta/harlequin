# PRD-17: Fix `ExportScreen` Overwriting Custom Filenames on Extension Change and Duplicate `Select.Changed` Events

- **Slice ID**: `PRD-17`
- **Category**: Bug Fix (`Bug`)
- **Priority / Severity**: `P0` (Active Functional Test Regression in `tests/functional_tests/test_export.py` & UX Bug)
- **Target Branch / PR Scope**: Single atomic commit / PR (`fix(export-screen): preserve custom filenames when auto-switching format from extension`)

## 1. Problem Statement & Root Cause
In `src/harlequin/components/export_screen.py` (lines 174-200) and `src/harlequin/export.py` (lines 529-544):

1. On mount (`export_screen.py:145-150`), `ExportScreen` initializes `file_input.value` to a generated timestamp path `{cwd}/{timestamp}.out.csv` and `format_select.value = "csv"`.
2. When the user types or sets a custom export path with a non-CSV extension (e.g., `/tmp/foo-bar-static/one.parquet`), `on_input_changed` (`export_screen.py:174-181`) detects `new_format = "parquet" != "csv"`.
3. It sets `self.format_select.value = new_format` (which causes Textual to emit `Select.Changed`) **and** manually posts a second duplicate `Select.Changed` message (`lines 179-181`).
4. `on_select_changed` (`export_screen.py:190-199`) then runs (twice!) and executes:
   ```python
   self.file_input.value = next_default_export_path(
       self.file_input.value, fmt.filename_suffix
   )
   ```
5. In `next_default_export_path` (`src/harlequin/export.py:529-544`), because `/tmp/foo-bar-static/one.parquet` does **not** match `_DEFAULT_FILENAME_STEM_RE` (`^[0-9]{8}T[0-9]{6}\.[0-9]{3}\.out\.(?P<suffix>[A-Za-z0-9_-]+)$`), it falls through to line 544:
   ```python
   return str(parent / default_export_filename(filename_suffix))
   ```
   This **overwrites** the user's custom filename `one.parquet` with a generated timestamp filename `20261024T213000.123.out.parquet`!
6. Additionally, `_get_format_from_file_extension` (`export_screen.py:245-253`) indexes `mapping[p.suffix]` without `.lower()`, failing on uppercase extensions like `.CSV` or `.PARQUET`, and `export_callback` (`lines 24-40`) does not guard `if screen_data is None: return`.

## 2. Goals & Non-Goals
### Goals
- Remove the duplicate manual `self.post_message(Select.Changed(...))` in `ExportScreen.on_input_changed`.
- When `format_select.value` is updated automatically in response to the user typing an extension in `path_input`, do not overwrite `file_input.value` in `on_select_changed`.
- When the user explicitly changes `format_select` in the UI while a custom filename is in `file_input` (e.g., `/tmp/my_report.csv` -> user selects `Parquet`), preserve their custom stem (`my_report`) and only update its suffix (`/tmp/my_report.parquet`), using `next_default_export_path` only when the path is empty or matches the default generated timestamp stem.
- Normalize `p.suffix.lower()` in `_get_format_from_file_extension` and guard `screen_data is None` in `export_callback`.

### Non-Goals
- Changing the format of `default_export_filename` for untouched default paths.

## 3. Technical Design & Affected Files
- `src/harlequin/components/export_screen.py`
- `src/harlequin/export.py`
- `tests/functional_tests/test_export.py`
- `tests/unit_tests/test_export_filename.py`

## 4. Verification & Acceptance Criteria
```bash
uv run pytest tests/functional_tests/test_export.py tests/unit_tests/test_export_filename.py
uv run ruff check src/harlequin/components/export_screen.py src/harlequin/export.py
uv run mypy src/harlequin/components/export_screen.py src/harlequin/export.py
```
