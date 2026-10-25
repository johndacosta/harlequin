# ADR 0010: v1 includes guide-level user docs

## Decision

v1 ships **guide-level** documentation, not install-only notes. Required content:

1. Install / connect (`-a questdb`, port `8812`, auth, pinned QuestDB version)
2. PGWire limits and intentional stubs
3. Time-series facilitation: designated timestamp, partition strategy, SAMPLE BY / ASOF / LATEST ON (and related) with examples tied to catalog hints
4. Deeper QuestDB-oriented recipes (TTL, WAL, upsert keys, mat views) plus an explicit pointer that **ILP ingestion is outside Harlequin**

Exact medium (README-only vs README + docs site) can follow packaging extract; the **content bar** above is the release gate. Screenshots / asciinema are **nice-to-have**, not a v1 blocker—prose and copy-pasteable SQL satisfy the gate.

## Why

Thesis is time-series facilitation. Completions and catalog hints under-deliver if strangers lack a guided path. ILP remains out of the adapter; docs should send users to QuestDB’s ingestion docs instead of pretending the TUI covers it.
