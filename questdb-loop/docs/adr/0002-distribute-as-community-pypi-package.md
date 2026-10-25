# ADR 0002: Distribute as a community PyPI package

## Decision

The ship milestone publishes the QuestDB adapter as a **community package** on PyPI (e.g. `harlequin-questdb`), not as an in-tree Harlequin core adapter.

## Why

Upstream keeps DuckDB/SQLite in core and Postgres-class adapters as separate packages. A community package matches that norm, avoids needing a maintainer decision to merge into core, and keeps release cadence independent of Harlequin core.
