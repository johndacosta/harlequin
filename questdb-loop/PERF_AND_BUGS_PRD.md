# Master PRD: Codebase-Wide Performance Improvements & Bug Fixes (`PRD-01` .. `PRD-26`)

## 1. Overview & Engineering Philosophy
Following a full static and dynamic audit across the entire repository (`src/harlequin/`, `src/harlequin_duckdb/`, `src/harlequin_sqlite/`, `src/harlequin_questdb/`, `questdb-loop/package/harlequin-questdb/`, and `questdb-loop/ralph/`), **26 distinct bug fixes and performance improvements** have been specified as individual, self-contained PRDs under [`questdb-loop/prds/`](./prds/README.md).

In accordance with software engineering best practices:
- **1 PRD = 1 Atomic Slice = 1 Separate Commit / Pull Request**: Each PRD has a narrow, well-defined scope, explicit non-goals, exact file/line targets, and isolated verification commands (`pytest`, `ruff`, `mypy`) so it can be reviewed, tested, and reverted independently.
- **State Machine Driven**: Every PRD is registered in [`V1_SHIP_CHECKLIST.md`](./V1_SHIP_CHECKLIST.md) under `## Must` sections and queued in [`ralph/state/loop_state.json`](./ralph/state/loop_state.json). Running the Ralph state machine (`./questdb-loop/scripts/run-ralph.sh`) selects and works one PRD slice per iteration (`SELECT` → `GRILL` → `BUILD` → `VERIFY` → `PROGRESS`).

---

## 2. Summary by Subsystem

### A. Data Export & Copy Formats (`PRD-04`, `PRD-05`, `PRD-06`, `PRD-17`)
- **[PRD-17](./prds/PRD-17-export-screen-custom-filename-preservation.md)** (`P0` Bug): Prevent `ExportScreen` from overwriting user-entered custom filenames when auto-switching export formats from file extensions, and eliminate duplicate `Select.Changed` events.
- **[PRD-04](./prds/PRD-04-export-background-worker-ui-responsiveness.md)** (`P1` Perf): Run `copy()` inside a background thread worker so large exports do not freeze the Textual event loop.
- **[PRD-05](./prds/PRD-05-export-streaming-and-batch-perf.md)** (`P1` Perf): Stream HTML exports directly to disk instead of buffering millions of `<tr>`/`<td>` strings in RAM, use `_iter_row_tuples` (`zip` over column batches) to eliminate per-row dictionary allocations in Markdown/HTML/Excel exports, and deduplicate column names in $O(C)$ with a `set`.
- **[PRD-06](./prds/PRD-06-export-duckdb-resource-safety-and-options.md)** (`P1` Bug): Preserve falsy numeric (`0`/`0.0`) and boolean (`False`) export options, default `header=True` in `_export_csv`, normalize timezone-aware datetimes in `_export_excel`, escape `\r` in `_md_escape_cell`, and close DuckDB/openpyxl handles in `finally` blocks with `CREATE OR REPLACE TABLE results`.

### B. Autocomplete Engine (`PRD-02`, `PRD-03`)
- **[PRD-02](./prds/PRD-02-member-completer-case-sensitivity-bug.md)** (`P1` Bug): Normalize `HarlequinCompletion.context` to lowercase so dot-completion (`MyTable.` / `MySchema.`) works for uppercase and mixed-case catalog identifiers.
- **[PRD-03](./prds/PRD-03-autocomplete-indexing-and-fuzzy-perf.md)** (`P1` Perf): Index `MemberCompleter` by `context` ($O(1)$ lookup), deduplicate completions in `extend_catalog`, combine 3 linear passes into 1, and remove capturing groups in `_build_fuzzy_regex` to prevent backtracking stalls.

### C. Core Harlequin TUI, Editor, Catalog, Config & Cache (`PRD-07`, `PRD-08`, `PRD-09`, `PRD-10`, `PRD-14`, `PRD-15`, `PRD-16`, `PRD-18`, `PRD-19`, `PRD-20`, `PRD-21`, `PRD-22`)
- **[PRD-09](./prds/PRD-09-debug-info-focus-crash-fix.md)** (`P0` Bug): Fix `DebugInfoScreen.move_focus()` `NoMatches` crash on `#collapsible-client-adapter-details` and scroll `#debug_info_scroll` on `pageup`/`pagedown`.
- **[PRD-07](./prds/PRD-07-select-option-flat-choices-bug.md)** (`P1` Bug): Return `choice[1]` (option value) instead of `choice[0]` (display label) in `SelectOption._flat_choices()`.
- **[PRD-08](./prds/PRD-08-keymap-mutation-and-action-validation.md)** (`P1` Bug): Stop mutating `self.__dict__` in `HarlequinKeyBinding.to_dict()`, fix `key_display` error message typo, and validate keymap action names against `HARLEQUIN_ACTIONS`.
- **[PRD-10](./prds/PRD-10-s3-tree-stdout-and-regional-url-fix.md)** (`P1` Bug): Remove stray `print(parts)` in `S3Tree`, support regional virtual-hosted S3 URLs (`bucket.s3.us-east-1.amazonaws.com`), initialize `self.root.data` before `on_mount`, and ignore empty S3 folder-marker segments.
- **[PRD-14](./prds/PRD-14-editor-selection-validation-caching.md)** (`P1` Perf): Memoize `Harlequin._validate_selection()` so cursor/selection movement does not execute redundant synchronous `connection.validate_sql()` queries on the main UI thread.
- **[PRD-15](./prds/PRD-15-atomic-cache-writes-and-eof-resilience.md)** (`P1` Bug): Use atomic temp-file + `os.replace` in `editor_cache` and `catalog_cache`, catch `EOFError` on truncated pickle files, and guard empty editor buffer lists in `action_quit` and `EditorCollection.on_mount`.
- **[PRD-18](./prds/PRD-18-code-editor-selected-queries-semicolon-boundary.md)** (`P1` Bug): Fix `CodeEditor.selected_queries()` executing the next statement when the cursor or selection ends immediately after a semicolon.
- **[PRD-19](./prds/PRD-19-app-thread-safety-and-cursor-table-id.md)** (`P1` Bug): Use `call_from_thread` in `Harlequin.commit()` and `rollback()`, and use `f"t{i}_{id(cur)}"` instead of `f"t{hash(cur)}"` in `_execute_query()`.
- **[PRD-20](./prds/PRD-20-config-missing-profiles-and-windows-tz-leak.md)** (`P1` Bug): Guard missing `profiles` key in `config._raise_on_bad_schema` and close `TarFile`/`urlopen` handles in `windows_timezone.py`.
- **[PRD-16](./prds/PRD-16-option-name-regex-and-core-hygiene.md)** (`P2` Bug): Anchor `AbstractOption._validate_name` with `re.fullmatch`, copy `BUILTIN_THEMES` in `colors.py`, and read `help_screen.md` with `encoding="utf-8"`.
- **[PRD-21](./prds/PRD-21-database-tree-sorting-and-file-tree-dedup.md)** (`P2` Bug): Sort preloaded children in `DatabaseTree._on_tree_node_expanded`, preserve highlight for dot-containing identifiers in `_reload`, and deduplicate `FileTree`.
- **[PRD-22](./prds/PRD-22-history-option-renderable-caching.md)** (`P2` Perf): Precompute and cache the `HistoryOption` Rich renderable at initialization.

### D. Database Adapters: QuestDB, SQLite, DuckDB (`PRD-01`, `PRD-11`, `PRD-12`, `PRD-13`, `PRD-23`, `PRD-24`, `PRD-25`)
- **[PRD-01](./prds/PRD-01-questdb-source-sync.md)** (`P0` Bug): Sync `src/harlequin_questdb/` with hardened staged package `questdb-loop/package/harlequin-questdb/src/harlequin_questdb/`.
- **[PRD-25](./prds/PRD-25-questdb-conn-str-precedence-and-pool-lifecycle.md)** (`P0` Bug): Preserve `conn_str` parameters over default `pool_kwargs`, close `ConnectionPool` when initial `getconn()` fails, and harden `_reconnect_main()` / `close()`.
- **[PRD-13](./prds/PRD-13-questdb-pool-check-and-catalog-perf.md)** (`P1` Perf): Reuse borrowed worker connection across `get_catalog()` and avoid redundant `autocommit` writes.
- **[PRD-11](./prds/PRD-11-sqlite-identifier-escaping-and-null-type-fix.md)** (`P0` Bug): Fix `HarlequinSqliteConnection._short_column_type` (`None` crash and `""` overwritten by `"NUMERIC"`), `_short_column_type_from_python_object` (`type(None)` and `bytes`), `show_describe_relation` pragma syntax, `show_relation_ddl` attached-DB lookup, and identifier quoting.
- **[PRD-23](./prds/PRD-23-sqlite-cursor-limit-one-and-empty-fetchone-bug.md)** (`P0` Bug): Fix `HarlequinSqliteCursor.set_limit(1).fetchall()` returning all rows (`fetchmany(0)`) and `fetchone()` returning `(None,)` on empty results.
- **[PRD-12](./prds/PRD-12-duckdb-identifier-escaping-in-catalog-and-ddl.md)** (`P1` Bug): Escape quotes in DuckDB catalog items, `show_relation_ddl`, and `_rewrite_dot_open`, and filter blank lines in `_split_script`.
- **[PRD-24](./prds/PRD-24-duckdb-validate-sql-motherduck-url-and-close.md)** (`P1` Bug): Catch `duckdb.Error` in `DuckDbConnection.validate_sql()` and `connect()`, fix MotherDuck query string joining (`?` vs `&`), and implement `DuckDbConnection.close()`.

### E. Ralph Autonomous State Machine (`PRD-26`)
- **[PRD-26](./prds/PRD-26-ralph-state-machine-verify-and-router-hardening.md)** (`P1` Bug): Prevent timed-out/force-closed `VERIFY` runs from passing, fix 3rd-agent escalation and multi-agent `needs_agents` rotation in `router.py`, use atomic `save_state()`, and expand `context_pack.py` globs across all packages and `questdb-loop/prds/`.
