# ADR 0006: Pin one QuestDB version for v1

## Decision

v1 supports and CI-tests **one pinned QuestDB version** (the current stable at ship time, recorded in docs and Docker Compose). Older/newer servers are best-effort.

Catalog features (designated timestamp, partition strategy) are verified against that pin. If a meta column is missing at runtime, degrade gracefully with a clear absence—not a crash—but “supported” means the pinned version shows both hints.

## Why

Meta function shapes already differ across QuestDB builds. A multi-version matrix fights the credible-public bar. One pin makes online smoke and ADR 0005 requirements testable and honest.
