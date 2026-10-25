# PRD-10: Remove Leftover `print(parts)` in `S3Tree`, Fix Regional S3 URLs, and Guard Pre-Mount Cache Building

- **Slice ID**: `PRD-10`
- **Category**: Bug Fix (`Bug`)
- **Priority / Severity**: `P1` (High — Stdout Corruption, Broken Regional AWS S3 URLs, and `None/` Node Data Prefix)
- **Target Branch / PR Scope**: Single atomic commit / PR (`fix(catalog): fix S3Tree stdout print, regional S3 URL parsing, and root data initialization`)

## 1. Problem Statement & Root Cause
In `src/harlequin/components/data_catalog/s3_tree.py`:

1. **Leftover `print(parts)` Statement (`s3_tree.py:111`)**:
   `_is_prefixed_aws_url` contains a stray `print(parts)` debug statement that writes raw text to stdout inside a running Textual TUI or test session.
2. **Broken Regional Virtual-Hosted AWS S3 URL Detection (`s3_tree.py:112-114`)**:
   `".".join(parts[1:]) == "s3.amazonaws.com"` only matches global legacy virtual-hosted URLs (`https://my-bucket.s3.amazonaws.com/key`) and fails for standard regional virtual-hosted URLs (`https://my-bucket.s3.us-east-1.amazonaws.com/key`), misclassifying the bucket hostname as a custom S3 endpoint URL.
3. **`self.root.data` is `None` When `build_tree` Runs Before `on_mount` (`s3_tree.py:48-50, 58-63, 73-78`)**:
   `S3Tree.__init__` passes `data=None` to `super().__init__("Root", data, ...)` and only sets `self.root.data = self.endpoint_url or "s3:/"` inside `on_mount()`. If `build_tree` is called from cache before `on_mount`, `self.root.data` is `None`, giving every tree node `data="None/bucket/key"`.
4. **S3 Folder Marker Objects (`folder/`) Create Empty-Label Leaf Nodes (`s3_tree.py:177-180`)**:
   `key_parts = obj.key.split("/")` produces a trailing `""` element for zero-byte S3 directory marker objects whose key ends with `/`, inserting a bogus leaf node with label `""`.

## 2. Goals & Non-Goals
### Goals
- Remove `print(parts)` from `S3Tree._is_prefixed_aws_url`.
- Support both `my-bucket.s3.amazonaws.com` and regional `my-bucket.s3.<region>.amazonaws.com` / `s3-<region>.amazonaws.com` virtual-hosted URLs.
- Set `self.root.data` in `S3Tree.__init__` so `build_tree` works even before `on_mount`.
- Strip empty path segments (`[p for p in obj.key.split("/") if p]`) in `_reload_objects`.
- Add unit tests in `tests/unit_tests/test_s3_tree.py`.

### Non-Goals
- Modifying live `boto3` network calls.

## 3. Technical Design & Affected Files
- `src/harlequin/components/data_catalog/s3_tree.py`
- `tests/unit_tests/test_s3_tree.py`

## 4. Verification & Acceptance Criteria
```bash
uv run pytest tests/unit_tests/test_s3_tree.py
uv run ruff check src/harlequin/components/data_catalog/s3_tree.py tests/unit_tests/test_s3_tree.py
uv run mypy src/harlequin/components/data_catalog/s3_tree.py tests/unit_tests/test_s3_tree.py
```
