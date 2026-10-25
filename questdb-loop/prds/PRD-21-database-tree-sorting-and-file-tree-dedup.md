# PRD-21: Fix `DatabaseTree` Unsorted Expanded Children, Dot-Identifier Highlight Reload, and Duplicate `FileTree` Class

- **Slice ID**: `PRD-21`
- **Category**: Bug Fix (`Bug`)
- **Priority / Severity**: `P2` (Medium — Unsorted Catalog Nodes, Highlight Loss on Quoted Dot Identifiers, and Dead Duplicate Code)
- **Target Branch / PR Scope**: Single atomic commit / PR (`fix(catalog): sort preloaded children, preserve dot-identifier highlight, and deduplicate FileTree`)

## 1. Problem Statement & Root Cause
1. **Unsorted Pre-Loaded Children in `DatabaseTree._on_tree_node_expanded` (`src/harlequin/components/data_catalog/database_tree.py:303-306, 349-354`)**:
   `_load_children` sorts lazily fetched children by `catalog_item.label`, whereas `_on_tree_node_expanded` passes `content=node.data.children` to `_populate_node` **unsorted** when `node.data.children` was already populated during `get_catalog()`.
2. **Broken Highlight Restoration on Reload for Identifiers Containing Dots (`database_tree.py:214-235`)**:
   In `_reload`, `parents(qualified_identifier)` splits `highlighted_identifier` on `"."` (`parent.rpartition(".")[0]`). If a database, schema, or table name contains a literal dot inside quotes (e.g., `"my.db"."my.schema"`), `.rpartition(".")` splits inside the quoted identifier, failing to match ancestor nodes' `qualified_identifier` and losing the selection highlight on refresh. Walking the tree node's actual `.parent` chain before `reset_node` avoids string splitting altogether.
3. **Duplicate `FileTree` Definition (`src/harlequin/components/data_catalog/__init__.py:234-246` vs `file_tree.py:1-25`)**:
   `src/harlequin/components/data_catalog/file_tree.py` defines `FileTree`, but `src/harlequin/components/data_catalog/__init__.py` redefines `class FileTree` inline instead of importing it from `file_tree.py`.

## 2. Goals & Non-Goals
### Goals
- Sort `node.data.children` by `catalog_item.label` in `DatabaseTree._on_tree_node_expanded`.
- Collect ancestor `qualified_identifier`s in `DatabaseTree._reload` by walking `node.parent` when `highlighted_node` is available.
- Import `FileTree` from `harlequin.components.data_catalog.file_tree` in `src/harlequin/components/data_catalog/__init__.py` and remove the duplicate class definition.

### Non-Goals
- Changing `DirectoryTree` behavior in Textual.

## 3. Technical Design & Affected Files
- `src/harlequin/components/data_catalog/database_tree.py`
- `src/harlequin/components/data_catalog/__init__.py`
- `src/harlequin/components/data_catalog/file_tree.py`
- `tests/functional_tests/test_data_catalog.py`

## 4. Verification & Acceptance Criteria
```bash
uv run pytest tests/functional_tests/test_data_catalog.py
uv run ruff check src/harlequin/components/data_catalog/
uv run mypy src/harlequin/components/data_catalog/
```
