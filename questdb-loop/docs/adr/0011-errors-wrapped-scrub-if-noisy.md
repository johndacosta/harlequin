# ADR 0011: Errors are wrapped; scrub only if noisy

## Decision

v1 always surfaces query/connection failures via Harlequin’s error types (`HarlequinQueryError` / `HarlequinConnectionError`) with the underlying server/driver message. **Aggressive** QuestDB-specific stack-trace scrubbing is only required if the pinned QuestDB version actually leaks large Java/C++ traces through PGWire.

## Why

Credible public needs clear errors, not a bespoke error-parsing engine. Conditional scrubbing avoids fragile string matching until evidence from the pin demands it.
