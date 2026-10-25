# Ralph autonomy — multi-persona ship loop

Run Architect, Security, Developer, and QA together until the QuestDB adapter meets [`V1_SHIP_CHECKLIST.md`](./V1_SHIP_CHECKLIST.md).

## Honest answer: can this finish delivery alone?

**Mostly yes, with guardrails** — not magic:

| Need | Reality |
|------|---------|
| Cursor API | `--live` needs `CURSOR_API_KEY` + `cursor-sdk` |
| Done detection | All **Must** boxes on `V1_SHIP_CHECKLIST.md` must be `[x]` (agents should check them when evidence exists; humans can too) |
| Cost / runaway | `--max-iterations` (default 40) + `ralph/state/STOP` file |
| Online QuestDB | QA may `verdict: blocked` without Docker; offline Musts can still advance |
| Commits / PyPI | Loop does **not** auto-publish or force-push; extract-at-publish stays a human release step unless you extend it |

Dry-run proves the state machine without spending tokens. Live mode drives real Cursor local agents against this repo.

## Architecture

Default routing is **issue threads** (not round-robin). See [`ROUTING.md`](./ROUTING.md).

```
Advisory (every N): Budget | Tech Strategy | Horizon
SELECT: Architect proposes → issue thread Architect↔Product (only)
GRILL: seeded issues → pairwise debates (Security/Dialect/QA as needed) → Architect synthesizes
BUILD: Developer + Ponytail
VERIFY: issue threads QA / Security (/ Release) → Architect synthesizes
PROGRESS: Architect
```

See [`PERSONAS.md`](./PERSONAS.md) · [`ROUTING.md`](./ROUTING.md) · [`HORIZON.md`](./HORIZON.md)

Personas: `ralph/agents/*.md`  
Ponytail: `ralph/agents/ponytail.md`  
Routing protocol: `ralph/agents/routing_protocol.md`

## Hybrid (local Ollama)

Prefer **`--hybrid`**: Cursor orchestrates judgment/tools; Ollama drafts codegen. See [`OLLAMA_HYBRID.md`](./OLLAMA_HYBRID.md).

```bash
./questdb-loop/scripts/run-ralph.sh --hybrid --reset --max 2
```

# One dry-run iteration (no API)
./questdb-loop/scripts/run-ralph.sh --dry-run --once --reset

# Live until done (spends API budget)
export CURSOR_API_KEY=...
./questdb-loop/scripts/run-ralph.sh --live --reset

# Stop a running live loop
./questdb-loop/scripts/run-ralph.sh --stop
```

Or:

```bash
export PYTHONPATH=questdb-loop
python -m ralph.loop --backend dry-run --once --reset
python -m ralph.loop --backend cursor --model composer-2.5
```

## Artifacts

```
questdb-loop/ralph/state/
  loop_state.json          # phase, iteration, history
  STOP                     # create to halt
  interactions.md          # timestamped agent index (summaries + links; no code)
  interactions.jsonl       # same events as JSON lines
  iterations/00N/
    turns/*.md             # per-turn agent chat transcripts
    select.md
    slice_spec.md
    grill/...
    build/developer_log.md
    verify/qa_report.md
    verify/security_report.md
    progress.md
```

The interaction log (`interactions.md`) is an append-only index: UTC timestamp, iteration, phase, agent name, verdict, and a link to that turn’s markdown under `iterations/00N/turns/`. Chat text lives only in those turn files — not inlined in the index. `--reset` clears iteration folders but keeps the interaction log and writes a run-boundary marker.

## Configuring personas

Edit markdown under `ralph/agents/`. Full rationale: [`PERSONAS.md`](./PERSONAS.md).

| File | Role |
|------|------|
| `architect.md` | Slice pick, grill lead, checklist gates |
| `product_lead.md` | Adoption / JTBD priority (not CRO) |
| `budget_steward.md` | Loop FinOps / STOP (not CFO) |
| `tech_strategy.md` | ADR hygiene / CTO-lite |
| `dialect_specialist.md` | QuestDB truth vs Postgres folklore |
| `horizon_scout.md` | AI/MCP future → `HORIZON.md` only |
| `release_steward.md` | Docs/package stranger-readiness |
| `security.md` | Grill answers + verify P0/P1 |
| `developer.md` | Ponytail implementation |
| `qa.md` | Grill testability + verify commands |
| `ponytail.md` | Lazy-senior ladder for BUILD |
| `grill_protocol.md` | Peer interview rules |

## Extending for “true” delivery

1. Teach Architect to flip `[ ]` → `[x]` on `V1_SHIP_CHECKLIST.md` when QA evidence is attached (prompt already asks; enforce in live runs).
2. Add a final **release** persona that only runs when `check-done.sh` exits 0 (extract package, tag — keep human approval).
3. Point Docker Compose at the pinned QuestDB image so online Musts can pass.

## Relation to PROTOCOL.md

This automation **is** the Ralph loop for ship readiness. Manual sessions still append `PROGRESS.md`; the loop writes per-iteration logs under `ralph/state/iterations/`.
