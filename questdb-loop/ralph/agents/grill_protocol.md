# Peer grill protocol (no human)

Used in Ralph phase **GRILL**. Personas interview each other; answers come from repo docs and code—not from a human operator.

## Rules (Matt Pocock grilling, adapted)

1. Ask **one question at a time** (Architect posts Q1, waits for answers, then Q2…).
2. Each question includes the asker’s **recommended answer**.
3. If a *fact* is in the filesystem, **look it up**—do not speculate.
4. *Decisions* still need an explicit Accept/Reject/Amend from Security and QA (and Developer when the question is about implementation shape).
5. Cap: **max 8 questions** per slice. If unresolved after 8, Architect must shrink the slice or mark `ready_for_build: false`.
6. Do not write application code in GRILL. Only docs under the iteration folder + optional ADR if a *new* hard-to-reverse decision appears (rare; prefer existing ADRs).

## Sequence

```
Architect → writes questions one-by-one into grill/architect_log.md
Security  → answers in grill/security_log.md (Accept|Reject|Amend)
QA        → answers in grill/qa_log.md
Developer → answers only when asked about implementation cost/risk
Architect → synthesizes grill/consensus.md + slice_spec.md
```

In the automated loop, each “one question” is one agent turn; the orchestrator feeds prior Q&A into the next turn.

## Consensus must include

- Slice goal (one sentence)
- Checklist Must targets
- In-scope files
- Acceptance commands / observables
- Non-goals
- `ponytail_level`: lite|full|ultra
- Security amendments folded in
