# ADR 0008: Cancel is best-effort in v1

## Decision

Query cancel in v1 is **best-effort**: wire it if PGWire on the pinned QuestDB version supports it; cover with an online test when reliable. If cancel is flaky or unsupported, document that clearly and **do not** block the PyPI release gate.

## Why

Long analytical queries benefit from cancel, but unproven PGWire cancel semantics must not create a false “works” claim. Credible public prefers honest limits over a hard gate on uncertain protocol behavior.
