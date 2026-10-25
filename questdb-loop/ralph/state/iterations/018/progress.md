### 2026-10-25 — PRD-10: fix(catalog): fix S3Tree stdout print, regional S3 URL parsing, and root data initialization

- **Author**: John DaCosta (`@johndacosta`)
- **State transition**: `SELECT` -> `GRILL` -> `BUILD` -> `VERIFY` -> `PROGRESS`
- **PRD**: [`questdb-loop/prds/PRD-10-s3-tree-stdout-and-regional-url-fix.md`](../questdb-loop/prds/PRD-10-s3-tree-stdout-and-regional-url-fix.md)
- **Changes**:
  - Remove leftover print(parts) debug statement in _parse_s3_uri.
  - Recognize regional virtual-hosted S3 URL patterns in _is_prefixed_aws_url.
  - Initialize self.root.data safely in S3Tree.__init__ before mount.
  - Filter zero-byte directory markers ('folder/') during S3 tree building.
- **Deterministic commands run**: `uv run python -m compileall -q src/harlequin/components/data_catalog/s3_tree.py tests/unit_tests/test_s3_tree.py; uv run ruff check src/harlequin/components/data_catalog/s3_tree.py tests/unit_tests/test_s3_tree.py; uv run ruff format --check src/harlequin/components/data_catalog/s3_tree.py tests/unit_tests/test_s3_tree.py; uv run mypy src/harlequin/components/data_catalog/s3_tree.py tests/unit_tests/test_s3_tree.py; uv run pytest -m not online tests/unit_tests/test_s3_tree.py`
- **Outcome**: PASS (all compileall, ruff, mypy, and pytest checks exited 0).

---
