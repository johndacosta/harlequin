# ADR 0004: v1 thesis is time-series facilitation

## Decision

v1 optimizes for **time-series facilitation**: QuestDB-native catalog metadata, rich time-series completions/docs, correct types and errors—not Postgres emulation or full `harlequin-postgres` interaction parity.

Engine differentiators (columnar storage, SIMD, ILP, WAL internals, Parquet tiering, Zero-GC) are **not** adapter features. Users get them by using QuestDB; the adapter helps them write and discover the SQL that exercises those capabilities.

Do **not** subclass `harlequin-postgres`; keep a dedicated adapter that speaks QuestDB meta (`tables()`, `table_columns()`, `functions()`, etc.).

## Why

QuestDB’s value is its dialect and operational model. A Postgres-shaped adapter would hide that. ILP and storage-engine mechanics are outside Harlequin’s SQL IDE role. Forking catalog SQL (already in the product PRD) avoids fighting PostgreSQL catalogs that QuestDB does not faithfully provide.
