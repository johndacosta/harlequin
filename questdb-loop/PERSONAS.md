# Persona roster — what we need (and what we don’t)

## Verdict on CRO / CTO / CFO

| Title you named | Fit for this project? | Why |
|-----------------|----------------------|-----|
| **CRO** (Chief Revenue Officer) | **No as-named** | v1 is a free community Harlequin adapter, not a revenue product. “Revenue” thinking creates fake metrics (upsells, packaging SKUs) and blinds you to real success: *adoption, trust, time-to-first-query*. |
| **CTO** (Chief Technology Officer) | **Partial** | Architecture is already covered daily by **Architect**. What’s missing is *periodic* tech strategy: pin/extract/MCP reopen, debt vs ship—not another voter on every grill turn. |
| **CFO** (Chief Financial Officer) | **Partial** | No P&L, but there **is** real cost: Cursor API tokens, iteration thrash, your calendar. Needs a **Budget Steward**, not corporate finance theater. |

**Blind spots the core four don’t cover**

| Blind spot | Who closes it |
|------------|----------------|
| Building the wrong slice for users | **Product Lead** (adoption / JTBD—not CRO) |
| Burning budget on low-ROI grill/build loops | **Budget Steward** |
| Dialect lies / version fragility | **Dialect Specialist** |
| Shipping without a stranger-ready package story | **Release Steward** |
| Ignoring AI/MCP world until it’s an emergency | **Horizon Scout** (backlog only; never blocks v1) |
| Strategic tech bets vs daily slice mechanics | **Tech Strategy** (CTO-lite, infrequent) |

---

## Active loop personas (every slice)

Already in `ralph/agents/`:

| Persona | Job |
|---------|-----|
| **Architect** | Slice selection, grill lead, checklist gates |
| **Security** | Trust boundaries, escaping, destructive stubs |
| **Developer** | Ponytail implementation |
| **QA** | Prove acceptance; command evidence |

## Added personas (this write-up)

| Persona | C-suite analogue | Cadence | May block v1? |
|---------|------------------|---------|----------------|
| **Product Lead** | CRO → adoption | SELECT + grill (UX/priority) | Yes — wrong user value |
| **Budget Steward** | CFO → FinOps | Every N iterations + before long live runs | Yes — STOP / shrink slice |
| **Tech Strategy** | CTO → strategy | Every N iterations | Soft — reopen ADR only with Architect |
| **Dialect Specialist** | (none; domain expert) | Grill when slice touches SQL/meta/catalog | Yes — wrong QuestDB assumptions |
| **Horizon Scout** | Future / AI ecosystem | Every N iterations | **Never** — writes `HORIZON.md` only |
| **Release Steward** | COO / maintainer | When Must remaining ≤ 5 or docs/release slices | Yes — for release Musts only |

---

## Product Lead (not CRO)

**Mission:** Optimize for *time-series developers using Harlequin*, not for “monetization.”

**Asks every SELECT:**
- Whose job does this slice improve (query, explore catalog, learn SAMPLE BY)?
- Does it advance time-series facilitation or Postgres cosplay?
- What’s the stranger’s first 5 minutes after `pip install`?

**Explicitly ignores:** pricing, enterprise packaging, lead gen.

**Output:** priority amend / kill slice / accept — with user-visible rationale.

## Budget Steward (not CFO)

**Mission:** Keep the Ralph loop solvent and purposeful.

**Watches:**
- Iterations used vs `max_iterations`
- Repeated FAIL on same slice (thrash)
- Grill rounds > 5 without `ready_for_build`
- Slices that don’t move a Must checkbox

**Powers:** recommend `STOP`, force slice shrink, forbid new Horizon work in BUILD, prefer offline tests over expensive flaky online loops until pin exists.

## Tech Strategy (CTO-lite)

**Mission:** Protect hard-to-reverse bets already in ADRs; notice when evidence should *reopen* one.

**Topics:** pinned QuestDB version, extract-at-publish timing, when MCP becomes worth a new ADR, dependency risk (`psycopg`/pool), test pyramid.

**Does not:** redesign every slice or override Ponytail on implementation taste.

## Dialect Specialist

**Mission:** QuestDB truth over Postgres folklore.

**Topics:** `tables()` / `table_columns()` / `functions()` shapes on the **pin**, designated timestamp + partition strategy fields, PGWire limits, SAMPLE BY / ASOF semantics in completions/docs.

## Horizon Scout (AI-focused world)

**Mission:** Capture *future* requirements so v1 doesn’t paint us into a corner—**without** violating ADR 0001.

**Considers:**
- MCP tool surface over Harlequin adapters (connect / list relations / execute / cancel)
- Agent-safe defaults (read-only, row limits, secret handling)
- Whether catalog/completions APIs stay stable for non-TUI clients
- ILP / ingestion as *adjacent* docs pointers, not adapter scope
- Multi-adapter “AI data workbench” narrative for later marketing/docs

**Writes only to:** [`HORIZON.md`](./HORIZON.md)  
**Never:** adds v1 Must items, never sets `ready_for_build: false` for horizon reasons.

## Release Steward

**Mission:** Stranger can install, connect, and trust the README; extract/PyPI path is real.

**Topics:** entry point name, package metadata, guide-level docs completeness, known-limitations honesty, version pin recorded, no secrets in tree.

---

## Personas we deliberately skip

| Persona | Why skip |
|---------|----------|
| Literal CRO / sales | No revenue surface in ship milestone |
| Marketing copywriter | Product Lead + Release Steward cover adoption copy in docs |
| Legal counsel | Overkill for community adapter; Security covers secrets/destructive SQL |
| Separate SRE | Fold resilience checks into QA + Dialect + Budget (online flaky = budget) |
| Separate Docs-only | Guide-level docs are Product + Release; avoid another voter |

---

## How they sit in the Ralph loop

```
              ┌─ Budget Steward (every N) ── may STOP / shrink
              ├─ Tech Strategy (every N) ─── ADR hygiene
SELECT ───────┼─ Product Lead ────────────── kill/reorder slice
              └─ Horizon Scout (every N) ─── append HORIZON.md only

GRILL ──────── Architect + Security + QA + Dev
               + Dialect Specialist if SQL/catalog/completions

BUILD ──────── Developer + Ponytail only

VERIFY ─────── QA + Security
               + Release Steward if release/docs Must targeted

PROGRESS ───── Architect (+ Budget notes)
```

Default: advisory council every **3** iterations (`--advisory-every 3`). Horizon never blocks.

---

## Forward-looking product design (summary)

v1 stays: **TUI QuestDB adapter, time-series facilitation, credible public, community package.**

Horizon backlog should answer: *If an AI agent were the primary user tomorrow, what stable contracts must this adapter already respect?*  
Examples (non-blocking): stable catalog data shapes, deterministic error types, cancel best-effort semantics, no hidden side effects on connect, documented read-only recommendations for MCP wrappers.

See agent prompts in `ralph/agents/` and the living backlog in [`HORIZON.md`](./HORIZON.md).
