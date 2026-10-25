# PRD-01: Sync `src/harlequin_questdb` with Hardened Staged Package & Guard Sync Direction

- **Slice ID**: `PRD-01`
- **Category**: Bug Fix (`Bug`)
- **Priority / Severity**: `P0` (Test Suite Blocker)
- **Target Branch / PR Scope**: Single atomic commit / PR (`fix(questdb): sync in-tree questdb adapter with hardened staged package`)

## 1. Problem Statement & Root Cause
The in-tree QuestDB adapter under `src/harlequin_questdb/` is out of sync with the hardened staged package under `questdb-loop/package/harlequin-questdb/src/harlequin_questdb/` and the unit/adapter test suite in `tests/adapter_tests/test_questdb.py`:

1. `tests/adapter_tests/test_questdb.py` imports `_quote_quest_identifier` from `harlequin_questdb.adapter` and tests the 4-tuple `_list_relations` (`table_name, rel_kind, partition_by, designated_timestamp`), 3-tuple `_get_relation_columns` (`col_name, col_type, designated`), `QueryCanceled` handling, and `PGP_PUB_KEY` / `_PIN_OID_TO_SHORT` type mappings.
2. Those implementations exist in `questdb-loop/package/harlequin-questdb/src/harlequin_questdb/` (`adapter.py`, `catalog.py`, `completions.py`, `interactions.py`), whereas `src/harlequin_questdb/` still has an older snapshot lacking `_quote_quest_identifier`, partition-by badge formatting, and designated timestamp markers.
3. Consequently, running `uv run pytest -m "not online"` fails immediately during collection with:
   ```text
   ImportError: cannot import name '_quote_quest_identifier' from 'harlequin_questdb.adapter'
   ```
4. Furthermore, `questdb-loop/scripts/sync-harlequin-questdb-package.sh` unconditionally runs `rsync -a --delete "$ROOT/src/harlequin_questdb/" "$PKG/src/harlequin_questdb/"`, which overwrites the newer staged package with the stale root `src/harlequin_questdb/` if executed before syncing root.

## 2. Goals & Non-Goals
### Goals
- Synchronize `src/harlequin_questdb/{__init__.py,adapter.py,catalog.py,cli_options.py,completions.py,interactions.py}` with the hardened implementation in `questdb-loop/package/harlequin-questdb/src/harlequin_questdb/`.
- Ensure `ADAPTER_DETAILS` in `src/harlequin_questdb/adapter.py` references the canonical `questdb-loop/docs/questdb-Limitations.md` and `questdb-loop/docs/questdb-architecture.md` paths required by `tests/adapter_tests/test_questdb_packaging.py`.
- Ensure `questdb-loop/scripts/sync-harlequin-questdb-package.sh` keeps both trees identical and passes `tests/adapter_tests/test_questdb.py` and `tests/adapter_tests/test_questdb_packaging.py`.

### Non-Goals
- Changing QuestDB connection pooling strategy (covered separately in `PRD-13`).
- Modifying core Harlequin widgets or other adapters.

## 3. Technical Design & Affected Files
- `src/harlequin_questdb/__init__.py`
- `src/harlequin_questdb/adapter.py`
- `src/harlequin_questdb/catalog.py`
- `src/harlequin_questdb/cli_options.py`
- `src/harlequin_questdb/completions.py`
- `src/harlequin_questdb/interactions.py`
- `questdb-loop/package/harlequin-questdb/src/harlequin_questdb/adapter.py`

### Key Changes
1. Copy the updated `adapter.py`, `catalog.py`, `cli_options.py`, `completions.py`, `interactions.py`, and `__init__.py` from `questdb-loop/package/harlequin-questdb/src/harlequin_questdb/` into `src/harlequin_questdb/`.
2. Update `ADAPTER_DETAILS` in `src/harlequin_questdb/adapter.py` (and re-run `questdb-loop/scripts/sync-harlequin-questdb-package.sh`) so both trees contain identical source files with the canonical `questdb-loop/docs/...` references.

## 4. Verification & Acceptance Criteria
```bash
./questdb-loop/scripts/sync-harlequin-questdb-package.sh
uv run pytest tests/adapter_tests/test_questdb.py tests/adapter_tests/test_questdb_packaging.py
uv run ruff check src/harlequin_questdb tests/adapter_tests/test_questdb*.py
uv run mypy src/harlequin_questdb tests/adapter_tests/test_questdb*.py
```
- All tests in `tests/adapter_tests/test_questdb.py` and `tests/adapter_tests/test_questdb_packaging.py` pass with 0 errors.
- `diff -ru src/harlequin_questdb questdb-loop/package/harlequin-questdb/src/harlequin_questdb` reports no differences.
