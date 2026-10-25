# PRD-05: Stream HTML Export and Eliminate Per-Row Dict Allocations in Export Writers

- **Slice ID**: `PRD-05`
- **Category**: Performance Improvement (`Performance`)
- **Priority / Severity**: `P1` (High — O(N×M) Memory & Dict Allocation Bottleneck in Exports)
- **Target Branch / PR Scope**: Single atomic commit / PR (`perf(export): stream html output and use tuple row iteration for tabular writers`)

## 1. Problem Statement & Root Cause
`src/harlequin/export.py` contains three major CPU and memory bottlenecks when exporting query results to Markdown, HTML, Excel, and JSON:

1. **In-Memory HTML Accumulation (`export.py:302-329`)**:
   `_export_html` builds a single Python list `parts: list[str]` containing `<tr>` and `<td>` strings for every cell of every row in the result set, then calls `"\n".join(parts)` and `out.write_text(...)`. For a 100k-row × 20-column table, `parts` holds >2.2 million strings in RAM simultaneously before allocating another multi-hundred-MB joined string.
2. **Per-Row Dictionary Allocation & Redundant Key Lookups (`export.py:216-223, 275-363`)**:
   `_iter_row_dicts` converts each Arrow `RecordBatch` to `pyd = batch.to_pydict()` and then allocates a brand new `dict[str, Any]` for every row:
   ```python
   yield {c: pyd[c][i] for c in columns}
   ```
   Then `_export_markdown`, `_export_html`, and `_export_excel` immediately iterate over `columns` again and call `row.get(name)` for each cell! For 100k rows × 20 columns, this allocates 100,000 ephemeral dictionaries and performs 4,000,000 hash table operations when ordered tuple iteration (`zip(*(pyd[c] for c in columns))`) requires zero dicts and zero key lookups.
3. **Quadratic Column Name Deduplication (`export.py:51-58`)**:
   ```python
   export_names: list[str] = []
   for label, _ in columns:
       ...
       while export_label in export_names:
   ```
   `export_label in export_names` linearly scans `export_names` for each column ($O(C^2)$).

## 2. Goals & Non-Goals
### Goals
- Add `_iter_row_tuples(table: Table, columns: list[str]) -> Iterator[tuple[Any, ...]]` using `zip(*(pyd[c] for c in columns))` per `RecordBatch`.
- Refactor `_export_markdown`, `_export_html`, and `_export_excel` to consume `_iter_row_tuples` instead of `_iter_row_dicts`.
- Refactor `_export_html` to stream directly to a buffered file handle (`with out.open("w", encoding="utf-8") as f:`) instead of accumulating all HTML tags in memory.
- Use a `seen_names: set[str]` in `copy()` for $O(1)$ duplicate column name resolution.

### Non-Goals
- Changing the output format or formatting options of JSON, Markdown, HTML, or Excel exports.

## 3. Technical Design & Affected Files
- `src/harlequin/export.py`
- `tests/functional_tests/test_export.py`

### Proposed Changes
1. In `copy()` (`src/harlequin/export.py:51-58`), track `seen_names: set[str] = set()` alongside `export_names: list[str] = []`.
2. Implement `_iter_row_tuples(table: Table, columns: list[str]) -> Iterator[tuple[Any, ...]]`:
   ```python
   def _iter_row_tuples(table: Table, columns: list[str]) -> Iterator[tuple[Any, ...]]:
       if not columns:
           return
       for batch in table.to_batches():
           pyd = batch.to_pydict()
           yield from zip(*(pyd[c] for c in columns))
   ```
3. Update `_export_markdown`, `_export_html`, and `_export_excel` to iterate over `_iter_row_tuples(table, columns)`.
4. Stream `_export_html` directly to `out.open("w", encoding="utf-8")`.

## 4. Verification & Acceptance Criteria
```bash
uv run pytest tests/functional_tests/test_export.py tests/unit_tests/test_export_filename.py
uv run ruff check src/harlequin/export.py
uv run mypy src/harlequin/export.py
```
