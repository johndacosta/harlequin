# Horizon backlog — future requirements (non-blocking)

Captured by the **Horizon Scout** persona. Items here must **not** be copied onto `V1_SHIP_CHECKLIST.md` Must without a new ADR that explicitly widens scope (see ADR 0001: MCP deferred).

## How to use

- Append dated entries (newest first).
- Tag: `mcp` | `agent-safety` | `api-stability` | `ecosystem` | `docs` | `perf`
- Status: `idea` | `research` | `candidate-v2` | `rejected`

---

## 2026-07-19 — iteration 1 SELECT advisory (Horizon Scout)

### Result grid types ≠ catalog types (OID gap)
- **Tag:** api-stability, mcp  
- **Status:** research  
- **Idea:** Catalog columns use `QUEST_TYPE_SHORT` from `table_columns('…').type`, but `HarlequinQuestDbCursor.columns()` maps PGWire `type_code` OIDs via a tiny Postgres-oriented dict (`_short_column_type_from_oid`)—most QuestDB-native types resolve to `"?"`. An MCP `execute_sql` tool that surfaces `columns()` metadata will mislead agents about `SYMBOL` / `GEOHASH` / etc.  
- **v1 implication:** Acceptable for TUI if grid matches peer adapters; when implementing ADR 0005 column labels, reuse the same native-type path for designated-timestamp flags. v2/MCP should prefer `table_columns` types (or a pin OID map) for result metadata, not uncached OID guesses.

### `functions()` discovery is intentionally bounded
- **Tag:** agent-safety, api-stability  
- **Status:** idea  
- **Idea:** `get_completions()` queries `functions()` with `length(name) < 48` and `LIMIT 4000`. Good guard against unbounded agent autocomplete, but **not a completeness contract**—MCP wrappers must not assume the list is exhaustive.  
- **v1 implication:** No change required; document the cap in guide-level “agent/MCP adjacency” prose so future tools expose `list_functions(max_rows=4000)` explicitly.

### Meta-function completions as agent lexicon
- **Tag:** ecosystem, docs  
- **Status:** candidate-v2  
- **Idea:** Static completions already advertise QuestDB meta entry points (`tables()`, `table_columns()`, `table_partitions()`, `table_storage()`, `materialized_views()`, `query_activity()`). These are the right **read-only discovery** verbs for an agent wrapper—mirror them in user docs as “safe introspection SQL,” not hidden adapter internals.  
- **v1 implication:** Keep completions list stable; avoid renaming or removing meta aliases without a version note.

### Buffer interactions = read-only MCP templates
- **Tag:** agent-safety, docs  
- **Status:** candidate-v2  
- **Idea:** Catalog interactions already encode safe patterns: `Preview Data` → `SELECT * … LIMIT 100`; `SHOW COLUMNS` / `SHOW PARTITIONS` → buffer-only exploration. A future MCP layer should default to these templates (row cap, no DDL) rather than raw `execute_sql` on user text.  
- **v1 implication:** Preserve `limit 100` on preview; do not add execute-side `LIMIT` injection in v1—document wrapper responsibility per ADR 0001.

### Connection meta returns tuples, not records
- **Tag:** api-stability, mcp  
- **Status:** research  
- **Idea:** `_list_relations()` → `list[tuple[str, str]]` and `_get_relation_columns()` → `list[tuple[str, str]]` have no room for ADR 0005 fields without signature growth or parallel methods. Pin fixture + offline tests (Tech Strategy / Budget alignment) should use **stable dict keys** even if v1 keeps tuples internally—eases a v2 `list_relations()` MCP tool without another meta-SQL rewrite.  
- **v1 implication:** Implement ADR 0005 at the connection query layer (extend SELECT from `tables()` / `table_columns()`); UI reads the same fields. Optional: internal `TypedDict` now, tuple compatibility for tree only.

### Reconnect-after-error semantics for long agent sessions
- **Tag:** api-stability  
- **Status:** idea  
- **Idea:** `execute()` retries once after recoverable connection loss (`_reconnect_main`); `cancel()` may also reconnect on `cancel_safe` failure. Agents holding implicit session state across tool calls need documented behavior: reconnect ≠ transaction boundary (already autocommit), but in-flight cancel may be lost.  
- **v1 implication:** No code change; note in adapter docs for MCP integrators alongside ADR 0008 cancel best-effort.

---

## 2026-07-18 — iteration 1 advisory (Horizon Scout)

### Pin meta probe as MCP catalog schema v0
- **Tag:** api-stability, mcp  
- **Status:** research  
- **Idea:** Tech Strategy’s pin-contract slice should emit a **versioned JSON fixture** (relations + columns + QuestDB-specific fields) alongside offline tests. Treat it as the proto-contract for a future `list_relations` / `list_columns` MCP tool—not a v1 deliverable.  
- **v1 implication:** When Dialect Specialist names `tables()` / `table_columns()` columns for designated timestamp and partition strategy, record them in the fixture with stable key names (`designated_timestamp`, `partition_strategy`, `relation_kind`) even if the TUI only shows abbreviated `type_label` chars.

### CatalogItem is TUI-native, not agent-serializable
- **Tag:** api-stability, mcp  
- **Status:** candidate-v2  
- **Idea:** `InteractiveCatalogItem` carries `connection` refs, lazy `fetch_children()`, and `INTERACTIONS` bound to `HarlequinDriver` (see `catalog.py`). An MCP wrapper cannot dump the live tree without re-querying meta SQL.  
- **v1 implication:** Keep meta reads in connection methods (`_list_relations`, `_get_relation_columns`) as the **single source of truth**; avoid QuestDB-only catalog logic buried only in UI labels. ADR 0005 hints should be computable from those queries, not only from tree rendering.

### Eager pool open on connect
- **Tag:** api-stability, agent-safety  
- **Status:** idea  
- **Idea:** `HarlequinQuestDbConnection.__init__` opens a psycopg pool, leases `_main_conn`, and pool `check` runs `select 1`—real side effects on connect. MCP agents may want `validate_config` vs `connect` separation.  
- **v1 implication:** Document that `adapter.connect()` is the intentional connect boundary; do not add hidden catalog prefetch or DDL on connect. Pin-first offline tests should mock at the connection/query layer, not require live TCP for unit fixtures.

### Execute has no default row cap
- **Tag:** agent-safety  
- **Status:** idea  
- **Idea:** `execute()` runs arbitrary SQL; `HarlequinQuestDbCursor.set_limit()` caps `fetchall()` only when the TUI sets it. An agent calling execute directly can issue unbounded `SELECT *`. Catalog “Preview Data” already uses `limit 100`—good pattern for wrappers.  
- **v1 implication:** No Harlequin-core change required; guide docs should warn that PGWire has no server-side `LIMIT` injection. Future MCP layer should default `max_rows` + deny DDL unless opted in.

### QuestDB time-series fields for tool surfaces
- **Tag:** api-stability, ecosystem  
- **Status:** research  
- **Idea:** Beyond generic relation kinds, tools need structured fields from `tables()` / `table_columns()` on the pin: **designated timestamp** column name, **partition strategy** (e.g. `DAY`/`MONTH`/`NONE`), optionally `walEnabled`, `matView`. LESSONS_LEARNED notes column drift (`matView` without `table_type`)—fixtures must encode per-pin shapes, not Postgres idioms.  
- **v1 implication:** Satisfy ADR 0005 in the tree and/or column labels, but **prefer fields** on relation/column catalog items (or parallel dict from the same SQL) so a later MCP tool does not re-parse UI abbreviations like `type_label="t"`.

### Cancel + error types are MCP-ready
- **Tag:** api-stability  
- **Status:** candidate-v2  
- **Idea:** `cancel_safe()` best-effort (ADR 0008), `HarlequinQueryError` / `HarlequinConnectionError` on failures, `connection_id` exposes `host:port/db` without secrets—these map cleanly to `execute_sql` / `cancel` / `connect` tools.  
- **v1 implication:** Preserve these contracts; avoid QuestDB-specific exception types that bypass Harlequin wrappers.

### ILP stays forever adjacent
- **Tag:** ecosystem, docs  
- **Status:** rejected (for Harlequin scope)  
- **Idea:** Ingestion agents should use QuestDB ILP/HTTP clients outside Harlequin. Reconfirm on every Horizon pass.  
- **v1 implication:** Guide docs must keep the ILP-out-of-scope note (ADR 0010); do not add ingestion hooks “for agents.”

---

## Seeds (from ship grilling + AI-world lens)

### 2026-07-18 — MCP over adapter entry points
- **Tag:** mcp, api-stability  
- **Status:** candidate-v2  
- **Idea:** Separate package or Harlequin subcommand exposing tools: `list_adapters`, `connect`, `list_relations`, `list_columns`, `execute_sql`, `cancel`. Reuse `harlequin.adapter` plugins (DuckDB/SQLite first, QuestDB after v1).  
- **v1 implication:** Keep connection/catalog/execute/cancel contracts clean; avoid QuestDB-only private APIs for catalog.

### 2026-07-18 — Agent-safe defaults
- **Tag:** agent-safety  
- **Status:** idea  
- **Idea:** Read-only mode, max rows, statement timeout, deny DDL/DML unless flagged.  
- **v1 implication:** Document dangerous operations; no destructive catalog interactions (already required).

### 2026-07-18 — Stable machine-readable catalog
- **Tag:** api-stability  
- **Status:** idea  
- **Idea:** Designated timestamp + partition strategy as explicit fields (not only UI labels) so MCP/tools can expose them.  
- **v1 implication:** Prefer structured catalog metadata while implementing ADR 0005.

### 2026-07-18 — ILP / ingestion adjacency
- **Tag:** ecosystem, docs  
- **Status:** idea  
- **Idea:** Docs link to QuestDB ILP; never build ILP into Harlequin. Future “agent ops” might call ILP outside this adapter.  
- **v1 implication:** Guide-level docs already require ILP-out-of-scope note (ADR 0010).

### 2026-07-18 — Multi-adapter AI workbench narrative
- **Tag:** ecosystem  
- **Status:** idea  
- **Idea:** Positioning: Harlequin adapters as the DB connectivity layer for both humans (TUI) and agents (MCP). QuestDB is the time-series specialty adapter in that set.  
- **v1 implication:** Community package naming/docs should say “Harlequin adapter,” not “QuestDB MCP server.”
