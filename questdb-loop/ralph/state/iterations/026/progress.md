### 2026-10-25 — PRD-21: fix(catalog): sort preloaded children, preserve dot-identifier highlight, and deduplicate FileTree

- **Author**: John DaCosta (`@johndacosta`)
- **State transition**: `SELECT` -> `GRILL` -> `BUILD` -> `VERIFY` -> `PROGRESS`
- **PRD**: [`questdb-loop/prds/PRD-21-database-tree-sorting-and-file-tree-dedup.md`](../questdb-loop/prds/PRD-21-database-tree-sorting-and-file-tree-dedup.md)
- **Changes**:
  - Sort preloaded children alphabetically by label in DatabaseTree._on_tree_node_expanded.
  - Preserve tree node highlight candidates across catalog reload for identifiers with dots.
  - Deduplicate FileTree by importing from data_catalog.file_tree.
- **Deterministic commands run**: `uv run python -m compileall -q src/harlequin/components/data_catalog/database_tree.py src/harlequin/components/data_catalog/__init__.py tests/unit_tests/test_s3_tree.py; uv run ruff check src/harlequin/components/data_catalog/database_tree.py src/harlequin/components/data_catalog/__init__.py tests/unit_tests/test_s3_tree.py; uv run ruff format --check src/harlequin/components/data_catalog/database_tree.py src/harlequin/components/data_catalog/__init__.py tests/unit_tests/test_s3_tree.py; uv run mypy src/harlequin/components/data_catalog/database_tree.py src/harlequin/components/data_catalog/__init__.py tests/unit_tests/test_s3_tree.py; uv run pytest -m not online tests/unit_tests/test_s3_tree.py -k test_database_tree_preloaded_children_sorted`
- **Outcome**: PASS (all compileall, ruff, mypy, and pytest checks exited 0).

---
