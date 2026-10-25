# QuestDB ship effort

Bounded context for making the Harlequin QuestDB adapter publicly releasable. Not the whole Harlequin product domain.

## Language

**Ship milestone**:
The next releasable outcome of this effort: a public QuestDB adapter for the Harlequin TUI.
_Avoid_: MCP release, AI database layer, multi-track launch

**QuestDB adapter**:
A Harlequin adapter plugin that talks to QuestDB over PGWire (not a generic Postgres adapter).
_Avoid_: Postgres adapter, QuestDB MCP server

**Community package**:
The public distribution form of the QuestDB adapter: a separate installable package (e.g. `harlequin-questdb` on PyPI), not an in-tree Harlequin core adapter.
_Avoid_: core extra, upstream in-tree merge (as the ship target)

**Credible public bar**:
The v1 release standard: PRD acceptance + offline CI tests + Docker QuestDB online smoke + security pass on catalog SQL/destructive stubs + clear errors + documented gaps.
_Avoid_: “bug-free”, Postgres feature parity, “rock solid” without a checklist

**Time-series facilitation**:
The product aim of the QuestDB adapter: make QuestDB’s time-series SQL and metadata easy to discover and use in Harlequin (not emulate PostgreSQL).
_Avoid_: Postgres parity, generic SQL IDE sameness, implementing ILP/storage-engine features inside the adapter

**Adapter contract coverage**:
Implementing Harlequin’s adapter/connection/cursor responsibilities (connect, execute, catalog, completions, types, cancel where claimed) at a quality comparable to peer adapters—without copying Postgres-specific SQL or UI assumptions.
_Avoid_: “Postgres parity”, feature-checklist cloning of `harlequin-postgres`

**Designated timestamp**:
The QuestDB column marked as the table’s timestamp key for time-series operations (SAMPLE BY, ASOF JOIN, LATEST ON, etc.).
_Avoid_: “timestamp column” (any TIMESTAMP-typed column), Postgres `PRIMARY KEY` analogies

**Partition strategy**:
How a QuestDB table is time-partitioned (e.g. by hour/day/month/none), as exposed by server metadata.
_Avoid_: Postgres declarative partitioning, arbitrary “shard” language

**Pinned QuestDB version**:
The single QuestDB server release that v1 documents and CI online tests against.
_Avoid_: “all QuestDB versions”, informal “latest I have locally” without recording the pin

**Dialect discovery**:
How users learn QuestDB-specific SQL in Harlequin in v1: completions, catalog hints (designated timestamp, partition strategy), and documentation—not custom syntax highlighting.
_Avoid_: QuestDBLexer-as-v1-gate, “feels like Postgres highlighting”

**Best-effort cancel**:
v1 may attempt to cancel running queries via the driver/PGWire, but cancel is not a release gate if the pinned QuestDB build cannot do it reliably.
_Avoid_: “cancel always works”, treating cancel failure as an automatic v1 blocker

**Extract-at-publish**:
The release step that moves the hardened in-fork adapter into its own community package repository for PyPI.
_Avoid_: “must live in a separate repo before any quality work”, forever-monorepo as the public distribution form

**Guide-level docs**:
v1 user documentation that teaches install/connect, PGWire limits, catalog time-series hints, and practical QuestDB SQL recipes (including what Harlequin does not do, e.g. ILP). Prose and copy-pasteable SQL are enough; screenshots are optional.
_Avoid_: install-only README, treating marketing engine features as adapter features, blocking release on media production

**Wrapped errors**:
Driver/server failures presented through Harlequin error types with a readable message; deep QuestDB stack scrubbing only when the pinned server proves noisy.
_Avoid_: raw uncaught psycopg exceptions in the TUI, mandatory elaborate error parsers before evidence

**MCP surface**:
A possible later product that exposes Harlequin adapters to AI clients via Model Context Protocol. Out of scope for the ship milestone; tracked under Horizon backlog.
_Avoid_: treating MCP as part of QuestDB adapter “done”

**Horizon backlog**:
Non-blocking future requirements (MCP, agent safety, API stability) recorded in `HORIZON.md` by the Horizon Scout.
_Avoid_: promoting Horizon items to v1 Must without a new ADR

