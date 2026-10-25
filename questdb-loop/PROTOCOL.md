# Ralph-loop state protocol (QuestDB adapter)

Structured loop for iterative agent work without losing intent or guardrails.

## States

```
┌──────────┐      scope locked       ┌──────────┐
│   IDLE   │ ──────────────────────► │ PRD_HOLD │
└──────────┘                         └──────────┘
                                         │
                     implement slice       │
                                         ▼
┌──────────◄─────┐ failures / unknowns ┌──────────┐
│ LESSON_LOG     │ ◄────────────────── │ BUILDING │
└──────────◘     │                     └──────────┘
       ▲                                  │
       │ retrospect                        │ tests + manual smoke
       │                                  ▼
       └────────────────────────────┌───────────┐
                                    │ VERIFYING │
                                    └───────────┘
                                           │
                                           │ merged slice
                                           ▼
                                    update PROGRESS ► optionally back to BUILDING
```

| State       | Mandatory update                          | Exit criteria                          |
|------------|--------------------------------------------|----------------------------------------|
| **PRD_HOLD** | Confirm PRD invariants; refine acceptance | PRD checklist has testable assertions |
| **BUILDING** | Append PROGRESS entry before/after edits  | Slice compiles; ruff/mypy clean       |
| **VERIFYING**| Record commands + outcomes in PROGRESS    | Slice passes agreed tests/smoke       |
| **LESSON_LOG** | New row in LESSONS_LEARNED.md           | Retro feeds next BUILDING iteration   |

## Rules

1. **Single source intent**: Requirements live in `PRD.md`; do not silently widen scope mid-loop.
2. **Progress ledger**: Each session adds a dated entry to `PROGRESS.md` (what ran, outcome, next).
3. **Close the loop**: After a frustrating failure or surprise API behavior, add a lesson **before** retrying blindly.
4. **QuestDB truths**: Prefer [QuestDB SQL docs](https://questdb.io/docs/query/overview/) and [PGWire notes](https://questdb.com/docs/query/pgwire/overview/) over Postgres assumptions (`pg_catalog` / `information_schema` are unreliable or absent).

## Handoff snippet (paste into agent context)

```
State: BUILDING → VERIFYING
Read: questdb-loop/PRD.md, PROGRESS.md tail, LESSONS_LEARNED.md
Constraint: PGWire/psycopg only; introspect via tables(), table_columns(), functions(), SHOW
```
