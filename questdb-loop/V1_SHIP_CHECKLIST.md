# V1 ship checklist — QuestDB adapter

Go/no-go for the first public community package. All **Must** items required unless waived in [`PROGRESS.md`](./PROGRESS.md) with rationale. Decisions: [`docs/adr/`](./docs/adr/), glossary: [`CONTEXT.md`](./CONTEXT.md), product: [`PRD.md`](./PRD.md).

**Pinned QuestDB version:** `questdb/questdb:8.2.2` — `Build Information: QuestDB 8.2.2, JDK 17.0.11, Commit Hash 73d82aa6ae15d9f08ce3e4221a78415233958586`

---

## Must — functional

- [x] Connect via PGWire (`psycopg` pool), default port **8812**, `SELECT 1` works on the pin
- [x] Catalog from `tables()` / `table_columns()` — no `information_schema` / `pg_catalog` on those paths
- [x] Relation kinds sensible (table / view / mat view per pin’s columns, e.g. `matView`)
- [x] **Designated timestamp** visible in catalog (tree and/or column labels)
- [x] **Partition strategy** visible in catalog for relations
- [x] Completions: static time-series tokens + `functions()` (bounded)
- [x] Types: `SYMBOL`, `GEOHASH`, `TIMESTAMP` (and peers) map sanely for the results grid
- [x] Failures → `HarlequinQueryError` / `HarlequinConnectionError` with readable messages
- [x] No destructive drop database/schema interactions
- [x] Cancel wired best-effort; if unreliable on pin → documented, not a blocker

## Must — quality

- [x] Offline tests in CI (`pytest -m "not online"`) covering catalog mapping / options / types as practical
- [x] Docker (or equivalent) online smoke on **pinned** image: connect, catalog hints, `SELECT 1`
- [x] `ruff check`, `ruff format`, `mypy` clean for adapter package
- [x] Security pass: escaping of dynamic identifiers; no secrets committed
- [x] Contract audit: no open P0 vs Harlequin adapter interface; P1 fixed or documented with visible degradation

## Must — docs & release

- [x] Guide-level docs: install/connect, auth defaults, PGWire limits, catalog hints, SAMPLE BY / ASOF / LATEST ON (etc.) examples, TTL/WAL/upsert/mat-view notes, **ILP is outside Harlequin**
- [x] Pinned QuestDB version recorded in docs + Compose
- [x] Known stubs/gaps listed (views, indexes, export, multi-version, lexer, cancel if limited)
- [x] Extract to community package repo + entry point `questdb`
- [x] PyPI publish (or release-candidate package ready with install instructions)

## Must — bug fixes (atomic PR slices)

- [x] **PRD-01** (`P0` | `questdb-loop/prds/PRD-01-questdb-source-sync.md`): Sync `src/harlequin_questdb` with hardened staged package & guard sync direction (`fix(questdb): sync in-tree questdb adapter with hardened staged package`)
- [x] **PRD-17** (`P0` | `questdb-loop/prds/PRD-17-export-screen-custom-filename-preservation.md`): Preserve custom filenames in `ExportScreen` when auto-switching format from extension & remove duplicate `Select.Changed` (`fix(export-screen): preserve custom filenames when auto-switching format from extension`)
- [x] **PRD-09** (`P0` | `questdb-loop/prds/PRD-09-debug-info-focus-crash-fix.md`): Fix `DebugInfoScreen.move_focus()` `NoMatches` crash and `pageup`/`pagedown` scroll target (`fix(debug-info): fix collapsible selector IDs in move_focus and scroll container in on_key`)
- [x] **PRD-11** (`P0` | `questdb-loop/prds/PRD-11-sqlite-identifier-escaping-and-null-type-fix.md`): Fix SQLite column type mapping (`None`, `""`, `bytes`), `show_describe_relation` pragma syntax, `show_relation_ddl` attached-DB lookup, and identifier escaping (`fix(sqlite): fix column type mapping, pragma table_info syntax, and identifier escaping`)
- [x] **PRD-23** (`P0` | `questdb-loop/prds/PRD-23-sqlite-cursor-limit-one-and-empty-fetchone-bug.md`): Fix `HarlequinSqliteCursor.set_limit(1).fetchall()` returning all rows (`fetchmany(0)`) and empty `fetchone()` returning `(None,)` (`fix(sqlite): handle set_limit(1) in fetchall and return None from fetchone when empty`)
- [x] **PRD-25** (`P0` | `questdb-loop/prds/PRD-25-questdb-conn-str-precedence-and-pool-lifecycle.md`): Preserve QuestDB `conn_str` parameters over defaults and close `ConnectionPool` on connect failure (`fix(questdb): preserve conn_str parameters over defaults and close pool on connect failure`)
- [x] **PRD-02** (`P1` | `questdb-loop/prds/PRD-02-member-completer-case-sensitivity-bug.md`): Normalize `HarlequinCompletion.context` to lowercase so `MemberCompleter` works for uppercase/mixed-case identifiers (`fix(autocomplete): normalize completion context to lowercase for member autocomplete`)
- [x] **PRD-06** (`P1` | `questdb-loop/prds/PRD-06-export-duckdb-resource-safety-and-options.md`): Preserve falsy export options, normalize Excel timezone datetimes, escape CR in Markdown export, and close DuckDB/openpyxl handles safely (`fix(export): preserve falsy options, handle excel timezones, and close duckdb/openpyxl resources`)
- [x] **PRD-07** (`P1` | `questdb-loop/prds/PRD-07-select-option-flat-choices-bug.md`): Return option value (`choice[1]`) instead of label (`choice[0]`) in `SelectOption._flat_choices()` (`fix(options): return option value instead of label in SelectOption._flat_choices`)
- [x] **PRD-08** (`P1` | `questdb-loop/prds/PRD-08-keymap-mutation-and-action-validation.md`): Avoid mutating `HarlequinKeyBinding.__dict__` in `to_dict()` and validate keymap action names (`fix(keymap): avoid mutating HarlequinKeyBinding.__dict__ and validate action names`)
- [x] **PRD-10** (`P1` | `questdb-loop/prds/PRD-10-s3-tree-stdout-and-regional-url-fix.md`): Remove stray `print(parts)` in `S3Tree`, support regional virtual-hosted S3 URLs, and initialize `root.data` before `on_mount` (`fix(catalog): fix S3Tree stdout print, regional S3 URL parsing, and root data initialization`)
- [x] **PRD-12** (`P1` | `questdb-loop/prds/PRD-12-duckdb-identifier-escaping-in-catalog-and-ddl.md`): Escape quotes in DuckDB catalog identifiers, `show_relation_ddl`, and `.open` script rewriting (`fix(duckdb): escape quotes in catalog identifiers, show_relation_ddl, and .open script rewriting`)
- [x] **PRD-24** (`P1` | `questdb-loop/prds/PRD-24-duckdb-validate-sql-motherduck-url-and-close.md`): Catch `duckdb.Error` in `DuckDbConnection.validate_sql()` & `connect()`, fix MotherDuck URL parameters, and implement `close()` (`fix(duckdb): catch duckdb.Error in validate_sql/connect, fix MotherDuck URL params, and implement close()`)
- [x] **PRD-15** (`P1` | `questdb-loop/prds/PRD-15-atomic-cache-writes-and-eof-resilience.md`): Use atomic temp-file writes for editor/catalog caches, catch `EOFError` on truncated pickles, and guard empty editor buffer lists (`fix(cache): atomic cache writes, handle truncated pickles, and guard empty editor buffers`)
- [x] **PRD-18** (`P1` | `questdb-loop/prds/PRD-18-code-editor-selected-queries-semicolon-boundary.md`): Stop `CodeEditor.selected_queries()` at semicolon boundary when cursor or selection ends at separator (`fix(editor): stop selected_queries at semicolon boundary when selection ends at separator`)
- [x] **PRD-19** (`P1` | `questdb-loop/prds/PRD-19-app-thread-safety-and-cursor-table-id.md`): Use `call_from_thread` in `Harlequin.commit()` / `rollback()` and sequential table IDs in `_execute_query()` (`fix(app): use call_from_thread in commit/rollback and sequential table IDs in _execute_query`)
- [x] **PRD-20** (`P1` | `questdb-loop/prds/PRD-20-config-missing-profiles-and-windows-tz-leak.md`): Guard missing `profiles` key in `config._raise_on_bad_schema` and close `TarFile`/`urlopen` handles in `windows_timezone.py` (`fix(config): guard missing profiles key in schema check and close tarfile/urlopen in windows_timezone`)
- [x] **PRD-26** (`P1` | `questdb-loop/prds/PRD-26-ralph-state-machine-verify-and-router-hardening.md`): Harden Ralph state machine `phase_verify` verdict gate, multi-agent issue board escalation, and atomic state persistence (`fix(ralph): harden phase_verify verdict gate, issue board escalation, and atomic state persistence`)
- [x] **PRD-16** (`P2` | `questdb-loop/prds/PRD-16-option-name-regex-and-core-hygiene.md`): Anchor `HarlequinOption` name regex with `re.fullmatch`, copy `BUILTIN_THEMES` in `colors.py`, and use UTF-8 in `HelpScreen` (`fix(core): anchor option name regex, copy BUILTIN_THEMES, and specify utf-8 in HelpScreen`)
- [x] **PRD-21** (`P2` | `questdb-loop/prds/PRD-21-database-tree-sorting-and-file-tree-dedup.md`): Sort preloaded children in `DatabaseTree._on_tree_node_expanded`, preserve dot-identifier highlight on reload, and deduplicate `FileTree` (`fix(catalog): sort preloaded children, preserve dot-identifier highlight, and deduplicate FileTree`)

## Must — performance improvements (atomic PR slices)

- [x] **PRD-03** (`P1` | `questdb-loop/prds/PRD-03-autocomplete-indexing-and-fuzzy-perf.md`): Index `MemberCompleter` by context, deduplicate catalog completions, and optimize single-pass/fuzzy matching (`perf(autocomplete): index member contexts, deduplicate catalog items, and optimize matching`)
- [x] **PRD-04** (`P1` | `questdb-loop/prds/PRD-04-export-background-worker-ui-responsiveness.md`): Run data export (`copy()`) in a background thread worker to keep TUI responsive (`perf(export): run file export in background thread worker`)
- [x] **PRD-05** (`P1` | `questdb-loop/prds/PRD-05-export-streaming-and-batch-perf.md`): Stream HTML export to disk and use tuple row iteration (`_iter_row_tuples`) for Markdown/HTML/Excel writers (`perf(export): stream html output and use tuple row iteration for tabular writers`)
- [x] **PRD-13** (`P1` | `questdb-loop/prds/PRD-13-questdb-pool-check-and-catalog-perf.md`): Reuse worker connection across QuestDB `get_catalog()` queries and avoid redundant `autocommit` resets (`perf(questdb): avoid redundant pool check round-trips and autocommit resets`)
- [x] **PRD-14** (`P1` | `questdb-loop/prds/PRD-14-editor-selection-validation-caching.md`): Memoize `Harlequin._validate_selection()` to prevent synchronous DB queries on every cursor/selection event (`perf(editor): memoize _validate_selection to avoid synchronous DB calls on cursor events`)
- [x] **PRD-22** (`P2` | `questdb-loop/prds/PRD-22-history-option-renderable-caching.md`): Precompute and cache `HistoryOption` Rich renderable on initialization (`perf(history): precompute HistoryOption prompt renderable on init`)

## Should (do not block if timeboxed)

- [x] Extra completion tokens (`INTERPOLATE`, `LT JOIN`, `LATEST BY`, `TTL`, …)
- [ ] Online cancel test (only if cancel proven on pin)
- [ ] Error stack scrubbing (only if pin leaks noise)
- [ ] Screenshots / asciinema
- [ ] Handshake `SET` stripping beyond what the pin requires

## Won’t (v1)

- [x] MCP / AI multi-DB surface
- [x] Custom QuestDB lexer
- [x] Subclass `harlequin-postgres`
- [x] ILP ingestion in Harlequin
- [x] Multi-version QuestDB CI matrix
- [x] Full Postgres-adapter interaction parity
- [x] Export/copy pipeline parity

---

## Sign-off

| Role | Name / date | Notes |
|------|-------------|-------|
| Dialect / catalog | | |
| Resilience / security | | |
| Tests / CI | | |
| Docs | | |
| Release gatekeeper | | **GO / NO-GO** |
