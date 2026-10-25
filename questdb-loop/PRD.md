# PRD — Harlequin QuestDB adapter (PGWire)

## Summary

Deliver a **`harlequin_questdb`** adapter that connects via **PostgreSQL wire protocol** (default port **8812**, see [PGWire overview](https://questdb.com/docs/query/pgwire/overview/) and [Dialect notes — not PostgreSQL](https://questdb.com/docs/query/pgwire/overview/#sql-dialect-differences)).

Users get: query execution, cancel where supported, catalog tree aligned with QuestDB semantics, autocomplete for **QuestDB SQL** (not generic Postgres catalogs).

Out of scope (initial slice): parity with Harlequin **Export / copy** pipelines unless trivial; **multi-database** UX (QuestDB ignores `dbname` logically — treat one logical catalog root).

---

## Connectivity

| Aspect | Requirement |
|--------|-------------|
| Driver | **psycopg3** + pool (reuse patterns from [`harlequin-postgres`](https://pypi.org/project/harlequin-postgres/), but **fork catalog/SQL**, do not subclass that package.) |
| Auth | Plain user/password (`admin`/`quest` defaults per server docs). |
| SSL | Typically **unsupported** server-side via PGWire; document and default `sslmode=disable`. |
| Timezone | Prefer client **UTC** (timestamps over wire as TS without TZ). |

---

## `pg_catalog` / `information_schema` audit (reuse from Postgres adapter → QuestDB replacements)

Evidence is from the **`harlequin-postgres`** package (vendor copy under `.venv`; upstream source **not in this repo**). Every SQL touchpoint below assumes **real PostgreSQL catalogs** — **replace for QuestDB**.

### Core catalog loaders (`adapter.py`)

| Symbol / query | PostgreSQL reliance | QuestDB replacement |
|----------------|---------------------|----------------------|
| `_get_databases()` | `pg_database` (`datname`, templates, allowconn). | **`SELECT current_database()`** or fixed label from conninfo (**`qdb`**). Single logical database in tree; optionally show `SELECT build();` as init message metadata (not catalog parent). |
| `_get_schemas(dbname)` | `information_schema.schemata` + `catalog_name` filter. | **Single schema node** **`public`** unless `SELECT current_schema();` proves otherwise. Do not filter via `catalog_name`. |
| `_get_relations(db, schema)` | `information_schema.tables` (`TABLE`, `VIEW`, etc.). | **`SELECT ... FROM tables()`** — map `table_type` / `matView` to Harlequin relation kinds (see below). |
| `_get_columns(db, schema, rel)` | `information_schema.columns` + `ordinal_position`. | **`SELECT column, type FROM table_columns('rel')`** (order as returned; extend with index/designated flags in UI later). |
| `_get_mvs(schema)` | `pg_matviews`. | Fold into **`tables()`** where `matView = true` or `table_type = 'M'`. |
| `_get_mv_cols(schema, mv)` | `pg_attribute` + `pg_class` + `pg_namespace` + `format_type`. | **`table_columns('mv')`** (same as tables). |
| `get_completions()` | `information_schema.routines` + **`pg_settings`**. | **`SELECT name, ... FROM functions()`** (see [Meta: `functions()`](https://questdb.io/docs/query/functions/meta/#functions)). Drop `pg_settings`; optional **`SHOW PARAMETERS`** or static config keywords stub. |

### Catalog interactions (`interactions.py` — heavy `pg_catalog` SQL)

Strings inserted into buffers use PostgreSQL internals. **Either** ship QuestDB equivalents **or** degrade gracefully (`notify` “not supported for QuestDB”).

| Interaction | PostgreSQL reliance | Replacement / stub |
|-------------|---------------------|---------------------|
| `show_list_objects` | `pg_class`, `pg_namespace`, `pg_am`, `pg_get_userbyid`, `pg_table_size`, `obj_description`. | Generate query using **`tables()`**, **`materialized_views()`**, or **`SELECT * FROM table_storage()`** (storage-oriented). Omit owner/size until meta covers it. |
| `show_list_indexes` | `pg_index`, `pg_class`, `pg_am`, etc. | **Stub**: `SHOW INDEX FROM relation` pattern if QuestDB exposes it — **verify**. Else suggest user run **`SHOW COLUMNS FROM tbl`** (index flags) or document gap. |
| `show_describe_relation` | Large CTE on `pg_attribute`, `pg_constraint`, `pg_index`, `col_description`, etc. | **`SHOW COLUMNS FROM "schema"."table"`** or **`SELECT * FROM table_columns('table')`** as buffer template. |
| `show_describe_table_indexes` | `pg_index`, `pg_attribute`. | Stub or metadata-only template from `table_columns` (`indexed` column). |
| `show_describe_table_constraints` | `pg_constraint`, `pg_class`. | **Stub / not supported** initially (QuestDB constraints differ; confirm docs). |
| `show_view_definition` | `pg_get_viewdef`, `pg_class`. | For native views, check **`tables()`** / view metadata; may need **`SELECT view_sql FROM materialized_views()`** for mat views only; regular views TBD — verify `table_type = 'V'`. |
| DDL context | `set search_path` | **Verify** QuestDB `SET` compatibility; may no-op with user message. |
| `drop database` / `drop schema` | PG DDL | **Disable or guard** — QuestDB multi-tenant model differs; avoid destructive stubs. |

---

## QuestDB capabilities to surface (product + autocomplete)

Reference: [QuestDB docs index](https://questdb.com/docs/), [Query / SQL overview](https://questdb.io/docs/query/overview/).

### Time-series & analytics SQL (keyword / function stubs)

- **Partitioning & timestamps**: `TIMESTAMP` / `timestamp(col)` in `CREATE TABLE`, **`PARTITION BY`**, **designated timestamp**, **TTL**, **WAL**, **deduplication** / `UPSERT` keys.
- **Time bucketing / aggregation**: **`SAMPLE BY`**, **`ALIGN TO`**, **`FROM-TO`**, **`FILL`**, **`LATEST ON`** ([SQL reference](https://questdb.io/docs/query/sql/)).
- **Joins**: **`ASOF JOIN`**, **`SPLICE JOIN`**, **`WINDOW JOIN`** (and standard joins where supported).
- **Windows**: `ROWS` / `RANGE` framing where documented.
- **Vectors / analytics**: Geospatial, `approx_*`, `kahan_sum`, etc. — low priority unless common.
- **Operational meta**: `tables()`, `table_columns()`, `table_partitions()`, `table_storage()`, `materialized_views()`, `query_activity()`, **`cancel query`**, `reload_config()`.

### PGWire limitations to document in adapter details

From official PGWire page: e.g. **no `DELETE`**, no **`COPY FROM stdin`**, **forward-only cursors**, **no SSL** (typical deployment), **`database` name ignored**, dialect **≠** Postgres.

---

## Acceptance criteria (initial)

1. `harlequin --adapter questdb` connects with psycopg and runs `SELECT 1`-class queries.
2. Catalog lists **relations** derived from **`tables()`** with sensible **table / view / mat view** labels.
3. Columns load via **`table_columns('...')`**.
4. **`get_completions()`** merges static Quest dialect tokens with **`functions()`**-derived labels (bounded row count acceptable).
5. No runtime dependency on `information_schema.*` or `pg_catalog.*` for the above paths.
6. `ruff check`, `ruff format`, `mypy` clean for new code.

---

## Open questions (track in PROGRESS)

- Exact QuestDB support for **views** (`table_type = 'V'`) and fetching view text.
- **Index introspection** statement (`SHOW INDEX` variants).
- **Cancel**: confirm PGWire cancellation behavior matches `Connection.cancel_*`.
- **`SET search_path`** / multi-schema UX.
