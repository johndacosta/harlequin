# ADR 0003: v1 quality bar is “credible public”

## Decision

The first public PyPI release must meet the **credible public** bar: PRD acceptance, offline CI tests, Docker QuestDB online smoke, security review of escaping/destructive stubs, and clear connection/query errors—with intentional gaps documented, not silent.

We aim for **wise** proximity to `harlequin-postgres` adapter *contract* coverage, not Postgres product parity. The product differentiator is QuestDB time-series SQL and metadata—not behaving like PostgreSQL.

## Why

A thinner bar ships fragile software. Full Postgres-adapter parity fights the dialect and delays forever. Credible public matches “safe for strangers” while leaving room for time-series depth as the real value.
