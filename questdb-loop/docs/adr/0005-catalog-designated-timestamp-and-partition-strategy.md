# ADR 0005: v1 catalog must show designated timestamp and partition strategy

## Decision

Before the first public PyPI release, the catalog (tree and/or column type labels) must surface:

1. The **designated timestamp** column for each relation (when QuestDB exposes it)
2. The relation’s **partition strategy** (e.g. `DAY` / `MONTH` / `NONE`, or the server’s equivalent)

SHOW PARTITIONS buffer actions alone are not sufficient for this requirement.

## Why

Under time-series facilitation, these two facts are how users know whether SAMPLE BY / ASOF / LATEST ON / TTL-style workflows apply. Shipping without them leaves the sidebar Postgres-shaped and under-sells QuestDB.
