# ADR 0001: Ship milestone is QuestDB adapter only

## Decision

The ship milestone is a public QuestDB adapter for Harlequin’s TUI. An MCP / AI multi-database surface is deferred and must not gate this release.

## Why

Harlequin has no MCP today. Coupling MCP to QuestDB would make “rock solid” unachievable and blur packaging, tests, and acceptance. Postgres-class databases already ship as adapter plugins; that is the proven public path.
