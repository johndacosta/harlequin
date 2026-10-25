# QuestDB adapter — user guide

Harlequin connects to [QuestDB](https://questdb.io/) over **PGWire** (PostgreSQL wire protocol) on port **8812**. This guide targets the **pinned** QuestDB image **`questdb/questdb:8.2.2`** used in this repo's Compose file and online tests.

## Install and connect

From a Harlequin checkout (or install with the `questdb` extra):

```bash
uv sync --extra questdb
harlequin --adapter questdb
```

Common flags (long form is safest if short flags clash with other tools):

```bash
harlequin --adapter questdb \
  --host 127.0.0.1 \
  --port 8812 \
  --user admin \
  --password quest \
  --dbname qdb \
  --sslmode disable
```

Or pass a single libpq connection string:

```bash
harlequin --adapter questdb \
  "host=127.0.0.1 port=8812 user=admin password=quest dbname=qdb sslmode=disable"
```

- **Port:** PGWire defaults to **8812** (not PostgreSQL's 5432).
- **Pin:** Develop and test against QuestDB **8.2.2** (`questdb-loop/docker-compose.yml`).
- **Logical database:** The `dbname` field is accepted by libpq but **ignored** by QuestDB; `qdb` is a conventional placeholder.

## Quickstart server (local development)

```bash
docker compose -f questdb-loop/docker-compose.yml up -d
```

Wait for port **8812**, then launch Harlequin with an explicit password (see Auth below).

## Authentication (development only)

> **Development only — not for production.** The `admin` / `quest` credentials below are QuestDB's **upstream defaults** for local development and the Compose file in this repo on pin **8.2.2**. They are **not** production guidance. Configure proper credentials and network controls before exposing QuestDB beyond localhost.

Harlequin's QuestDB adapter defaults to **`--user admin`** and does **not** auto-supply a password. You must pass **`--password`** (or embed it in `CONN_STR`). The stock server password for the Compose quickstart is **`quest`**, matching `tests/adapter_tests/test_questdb_online.py`.

Prefer environment variables over shell history:

```bash
export QUESTDB_USER=admin
export QUESTDB_PASSWORD=quest
harlequin --adapter questdb --host 127.0.0.1 --port 8812
```

Do not commit `.env` files or real secrets to version control.

## PGWire limits and adapter stubs

QuestDB over PGWire is **not** full PostgreSQL. Expect differences in SQL dialect, metadata, cursors, and copy/export:

| Topic | What to expect |
|-------|----------------|
| **`DELETE`** | Not available on PGWire the way PostgreSQL clients expect. |
| **`COPY FROM stdin`** | Not supported for Harlequin's import/copy pipeline (`COPY_FORMATS` is unset on this adapter). |
| **Cursors** | Forward-only; no scrollable result sets. |
| **SSL** | Typically unsupported until enabled server-side; use `sslmode=disable` for local dev. |
| **`dbname`** | Logical database name is **ignored** by QuestDB. |
| **Dialect** | QuestDB SQL **≠** PostgreSQL — time-series syntax (`SAMPLE BY`, `LATEST ON`, etc.) is QuestDB-specific. |

For adapter limitations and v1 gaps (views, indexes, export, multi-version pin, lexer, cancel, results-grid OID collisions), see **[Known limitations](./KNOWN_LIMITATIONS.md)**. The in-app **ADAPTER_DETAILS** panel links to the same document.

Official PGWire overview: [QuestDB PGWire docs](https://questdb.com/docs/query/pgwire/overview/).

## Catalog sidebar hints

Run the smoke DDL first so the catalog tree has something to show:

```sql
CREATE TABLE IF NOT EXISTS _harlequin_smoke (
    ts TIMESTAMP,
    id INT,
    sensor SYMBOL,
    geo GEOHASH(8c)
) TIMESTAMP(ts) PARTITION BY DAY;

CREATE MATERIALIZED VIEW IF NOT EXISTS _harlequin_smoke_mv AS
SELECT ts, count() AS n
FROM _harlequin_smoke
SAMPLE BY 1d;
```

(These statements are copied from `SMOKE_DDL` / `SMOKE_MV_DDL` in `tests/adapter_tests/test_questdb_online.py`.)

### Decoding labels in the Harlequin catalog tree

| Sidebar label | Meaning |
|---------------|---------|
| **`t·DAY`** | Base **table** with `partitionBy` = `DAY` (from `tables()`). |
| **`mv·MONTH`** (etc.) | **Materialized view** with its partition strategy (from `tables()` / `matView` on pin 8.2.2). |
| **`ts★`** on a column | **Designated timestamp** column (`designated=true` in `table_columns()`). |

Regular SQL `VIEW`s without `table_type` in `tables()` may appear like base tables on this pin; materialized views are detected via the `matView` column. See **ADAPTER_DETAILS** in Harlequin for the P1 labeling note.

### Introspection SQL (QuestDB meta functions only)

Use QuestDB meta functions — **not** PostgreSQL-style system catalogs:

```sql
SELECT * FROM tables();

SELECT * FROM table_columns('_harlequin_smoke');
```

Meta function reference: [QuestDB meta functions](https://questdb.io/docs/query/functions/meta/).

## Time-series SQL recipes

The examples below use the smoke schema above. Seed data for `LATEST ON`:

```sql
INSERT INTO _harlequin_smoke VALUES
    (now(), 1, 'a', 'u4pruydq'),
    (dateadd('s', -10, now()), 1, 'a', 'u4pruydq');
```

### SAMPLE BY

Downsample by time buckets:

```sql
SELECT ts, sensor, count() AS n
FROM _harlequin_smoke
SAMPLE BY 1h;
```

Or query the materialized view:

```sql
SELECT * FROM _harlequin_smoke_mv;
```

Docs: [SAMPLE BY](https://questdb.io/docs/reference/sql/sample-by/).

### ASOF JOIN

Create a companion events table (same designated-timestamp pattern):

```sql
CREATE TABLE IF NOT EXISTS _harlequin_smoke_events (
    ts TIMESTAMP,
    id INT,
    event SYMBOL
) TIMESTAMP(ts) PARTITION BY DAY;

INSERT INTO _harlequin_smoke_events VALUES
    (now(), 1, 'start'),
    (dateadd('s', -5, now()), 1, 'warmup');
```

Join readings to the latest prior event per key:

```sql
SELECT s.ts, s.sensor, e.event
FROM _harlequin_smoke s
ASOF JOIN _harlequin_smoke_events e ON (id);
```

Docs: [ASOF JOIN](https://questdb.io/docs/reference/sql/asof-join/).

### LATEST ON

Pick the latest row per partition key:

```sql
SELECT *
FROM _harlequin_smoke
LATEST ON ts PARTITION BY sensor;
```

Docs: [LATEST ON](https://questdb.io/docs/reference/sql/latest-on/).

## Deeper QuestDB topics (pointers)

Harlequin does not implement these features in the TUI — run the SQL in the editor against your QuestDB server:

- **TTL (time-to-live):** [Designated timestamp & TTL](https://questdb.io/docs/concept/designated-timestamp/)
- **WAL (write-ahead log):** [WAL configuration](https://questdb.io/docs/guides/configure-wal/)
- **UPSERT KEYS:** [Upsert keys](https://questdb.io/docs/reference/sql/upsert-keys/)
- **Materialized views:** [Materialized views](https://questdb.io/docs/concepts/materialized-views/)

## ILP ingestion is outside Harlequin

**ILP (InfluxDB Line Protocol) ingestion is outside Harlequin.** This adapter speaks PGWire for interactive SQL only. For high-throughput ingestion, use QuestDB's ILP clients and HTTP/TCP receivers:

- [InfluxDB Line Protocol (ILP)](https://questdb.io/docs/reference/api/ilp/overview/)
- [Data ingestion overview](https://questdb.io/docs/guides/ingestion-overview/)
