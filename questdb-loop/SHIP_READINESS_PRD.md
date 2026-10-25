# PRD — QuestDB ship readiness & MCP vision

## Summary

Define how we decide the `harlequin_questdb` adapter is **high quality enough for public consumption**, and how (separately) we might expose Harlequin’s adapter layer to AI tools via **MCP**.

This document does **not** replace [`PRD.md`](./PRD.md) (adapter product requirements). It defines **evaluation roles**, **acceptance gates**, and **scope boundaries** for release and for a future MCP surface.

---

## Problem

The QuestDB adapter on `feature/questdb-support` is functional enough for smoke tests, but “works on my machine” is not enough to push for public use. We need a deliberate quality bar: correct dialect behavior, resilient connections, tests, security, packaging, and honest docs.

Separately, there is interest in **MCP** so an AI tool could query **any database Harlequin supports**. That is a reasonable product vision, but it is **not** the same workstream as shipping QuestDB.

---

## Goals

### Primary (Track A) — Public QuestDB adapter

Ship (or publish as a community package) a QuestDB adapter that is:

- **High quality** — matches Harlequin adapter contracts; lint/mypy/CI clean
- **Correct** — QuestDB SQL / meta functions, not Postgres catalog assumptions
- **Resilient** — pool, cancel, reconnect, timeouts, idle TCP drops handled predictably
- **Extensible** — clear stubs and seams; no dead-end Postgres copy-paste
- **Honest** — known PGWire/dialect gaps documented; no silent wrong behavior

### Secondary (Track B) — MCP / AI database access (optional)

Enable an AI client to connect through a small MCP tool surface that reuses Harlequin’s **adapter entry-point contract**, so “any supported database” is achievable without per-DB MCP servers.

### Non-goals

| Item | Why out of scope |
|------|------------------|
| Full Postgres-adapter feature parity | QuestDB ≠ PostgreSQL; chase documented QuestDB UX instead |
| Export/copy pipeline parity in v1 | Already out of scope in [`PRD.md`](./PRD.md) |
| Blocking QuestDB release on MCP | Different product; different risk |
| Guaranteeing zero bugs forever | Target known-gap-free + tested paths; dialect/version drift will continue |
| Putting MCP inside `harlequin_questdb` | MCP belongs on the shared adapter API |

---

## Requirement sanity check

| Requirement | Logical? | Notes |
|-------------|----------|--------|
| Rock-solid public QuestDB adapter | **Yes** | Aligns with community adapter expectations and [`PRD.md`](./PRD.md) acceptance |
| Extensible design | **Yes, bounded** | Extensibility = clean `HarlequinAdapter` surface + intentional stubs, not infinite dialect coverage |
| Bug-free | **Mostly** | Prefer *tested critical paths* + *documented gaps* over absolute claims |
| MCP so AI can query any supported DB | **Yes as vision; no as QuestDB gate** | Harlequin has **no MCP today**; build on adapter plugins, not inside QuestDB |

**Decision (locked):** Track A is the **ship milestone**. Track B (MCP) is deferred and must not gate release. See [`CONTEXT.md`](./CONTEXT.md) and [`docs/adr/0001-ship-milestone-is-questdb-adapter-only.md`](./docs/adr/0001-ship-milestone-is-questdb-adapter-only.md).

**Packaging (locked):** Community PyPI package; harden in-fork, extract at publish ([ADR 0002](./docs/adr/0002-distribute-as-community-pypi-package.md), [ADR 0009](./docs/adr/0009-harden-in-fork-extract-at-publish.md)).

**Go/no-go checklist:** [`V1_SHIP_CHECKLIST.md`](./V1_SHIP_CHECKLIST.md) (derived from grilling + ADRs).

---

## Track A — Agent / persona roster

Use these as **review roles** (separate agent sessions or checklists). Run roughly in order; later roles consume earlier findings.

| # | Persona | Mandate | Exit artifact |
|---|---------|---------|---------------|
| 1 | **Adapter contract auditor** | Compare `HarlequinQuestDb*` to DuckDB/SQLite (and ideally `harlequin-postgres`) against `HarlequinAdapter` / `Connection` / `Cursor`. Flag Postgres leftovers, missing methods, inconsistent errors/options. | Contract gap list (P0–P3) |
| 2 | **QuestDB dialect specialist** | Validate catalog/completion SQL against QuestDB docs + live server: `tables()`, `matView` vs `table_type`, `table_columns()`, `functions()`, time-series keywords, PGWire limits. | Per-path classification: correct / version-fragile / stub / bug |
| 3 | **Resilience engineer** | Attack pool checkout/return, `autocommit`, keepalive, idle disconnect, cancel + reconnect, bad auth, wrong port, timeouts, concurrent execute + catalog. | P0/P1 failure list + minimal fix proposals |
| 4 | **Security reviewer** | Identifier escaping in dynamic SQL, no destructive stubs (`DROP DATABASE` / schema), credential handling, surprising defaults (e.g. SSL). | Security findings + required remediations |
| 5 | **Test / CI engineer** | Mirror `tests/adapter_tests/` patterns; unit tests without server; Docker QuestDB for `online`; ensure `make lint` + `pytest -m "not online"` green. | Test plan + implemented coverage map |
| 6 | **TUI / UX tester** | Manual: connect, catalog browse, SHOW COLUMNS/PARTITIONS buffers, completions, long query, cancel, ugly errors. | UX notes; snapshot updates only if intentional |
| 7 | **Packaging & upstream-fit reviewer** | Decide in-tree extra vs separate `harlequin-questdb` PyPI package (see AGENTS.md / adapter guide). Entry point, extra, wheel package list, docs home. | Packaging decision + PR/package checklist |
| 8 | **Release gatekeeper** | Confirm PRD acceptance, open questions closed or documented, no secrets in tree, changelog tone accurate. | Go / no-go for public push |

### Minimal roster (if bandwidth is tight)

**Contract auditor → Dialect specialist → Resilience → Security → Test/CI → Packaging.**  
Defer deep TUI polish if smoke + automated tests are strong; never skip security or dialect.

### Suggested agent prompts

**Contract auditor**

```text
You are the Adapter Contract Auditor for harlequin_questdb.
Compare against DuckDB/SQLite adapter contracts and the HarlequinAdapter base.
List contract gaps, Postgres leftovers, and missing tests. Do not implement yet.
Read: questdb-loop/PRD.md, questdb-loop/SHIP_READINESS_PRD.md, src/harlequin_questdb/
```

**Dialect specialist**

```text
You are the QuestDB Dialect Specialist.
Use questdb-loop/PRD.md + QuestDB PGWire/SQL docs (+ live QuestDB if available).
Verify every catalog/completion SQL path.
Classify each as: correct / version-fragile / stub / bug.
```

**Resilience engineer**

```text
You are the Resilience Engineer for harlequin_questdb.
Attack pool, cancel, reconnect, timeouts, keepalive, concurrent use.
Propose minimal fixes only for P0/P1 failures.
```

**Cursor review skills (after implementation fixes)**

- Security Review on branch diff
- Bugbot on branch diff
- Fix P0/P1 only; park polish behind documented follow-ups

---

## Track A — Acceptance gate (public ready)

All must be true (or explicitly waived in writing in `PROGRESS.md`). Prefer the executable checklist: [`V1_SHIP_CHECKLIST.md`](./V1_SHIP_CHECKLIST.md).

1. **[`PRD.md`](./PRD.md) v1 acceptance** (including designated timestamp + partition strategy, guide-level docs, credible-public tests).
2. **Contract gaps:** no open P0; P1 either fixed or documented as known limitation with user-visible degradation (not silent wrong data).
3. **Dialect:** every catalog path classified against the **pinned** QuestDB version; version-fragile paths degrade gracefully.
4. **Resilience:** reconnect paths exercised; cancel best-effort per ADR 0008; connection/query errors wrapped clearly.
5. **Security:** escaping reviewed; destructive interactions absent or hard-guarded; no credentials committed.
6. **Tests:** offline unit/adapter tests in CI; **required** Docker online smoke on the pinned image (catalog hints + `SELECT 1`).
7. **Packaging:** community package extract-at-publish path ready; install instructions documented.
8. **Docs:** guide-level content per ADR 0010 (screenshots optional).

### Severity rubric

| Severity | Meaning | Ship rule |
|----------|---------|-----------|
| **P0** | Wrong results, crash on common path, credential leak, destructive stub | Must fix |
| **P1** | Broken cancel/reconnect, catalog wrong for common QuestDB versions, misleading UX | Fix or document + degrade |
| **P2** | Missing nicety (indexes, view SQL, export) | Document; OK for v1 |
| **P3** | Polish / nice-to-have completions | Backlog |

---

## Track A — Phased execution

### Phase 0 — Split goals (≤1 day)

- Confirm Track A ship criteria (this doc + [`PRD.md`](./PRD.md)).
- Confirm Track B is out of scope for the QuestDB PR unless explicitly combined later.

### Phase 1 — Freeze v1 “done” (≤0.5 day)

~~Promote open questions~~ **Done (2026-07-18 grilling).** Execute [`V1_SHIP_CHECKLIST.md`](./V1_SHIP_CHECKLIST.md); only re-open ADRs if evidence forces it.

### Phase 2 — Run Track A personas (2–5 days)

Produce gap lists → fix P0/P1 → re-run Security Review + Bugbot.

### Phase 3 — Tests that make “rock solid” credible

- Unit tests: catalog mapping, type labels, option parsing (no server).
- Online smoke (Docker Compose QuestDB): connect, `tables()`, columns, `SELECT 1`, cancel if advertised.
- `make lint` / project CI green.

### Phase 4 — Package & publish path

- Prefer separate community package unless maintainers agree to in-tree.
- PR or PyPI release + adapter docs (harlequin-web or package README) with known limitations.

---

## Track B — MCP / AI querying (parallel product)

### Context

Harlequin is a **TUI SQL IDE** with pluggable adapters (`harlequin.adapter` entry points). There is **no MCP server in this repo today**. “AI queries any supported DB” should mean: MCP tools → **adapter interface** → DuckDB / SQLite / QuestDB / Postgres / …

### Personas

| # | Persona | Mandate |
|---|---------|---------|
| 9 | **MCP architect** | Design a small tool set over adapters: e.g. `list_adapters`, `connect`, `list_relations`, `list_columns`, `execute_sql`, `cancel`. Prefer read-only default, row/time limits. Package as Harlequin subcommand **or** sibling package—not inside `harlequin_questdb`. |
| 10 | **AI consumer / safety** | Prompt injection via identifiers, runaway queries, write/DDL policy, secret handling, multi-tenant isolation. |
| 11 | **Interop tester** | Cursor and other MCP clients: schemas, result truncation, errors. |

### Track B acceptance (prototype)

1. MCP server loads adapters via entry points (at least DuckDB + SQLite).
2. Tools are documented; default deny or confirm for writes/DDL.
3. Large results truncated with explicit metadata.
4. QuestDB works through the **same** tools only after Track A gate is green.
5. Security review of tool surface completed.

### Explicit non-coupling

```
Track A (questdb adapter) ──► public adapter release
Track B (MCP) ──────────────► uses adapter API; may trail Track A
```

Do not add MCP code to `src/harlequin_questdb/` as a release dependency.

---

## Relationship to existing loop docs

| Doc | Role |
|-----|------|
| [`PRD.md`](./PRD.md) | What the QuestDB adapter must do (product) |
| [`PERSONAS.md`](./PERSONAS.md) | Full persona roster + CRO/CTO/CFO analysis |
| [`HORIZON.md`](./HORIZON.md) | Non-blocking AI/MCP future requirements |
| [`CONTEXT.md`](./CONTEXT.md) | Ubiquitous language |
| [`docs/adr/`](./docs/adr/) | Locked architectural / scope decisions |
| **This doc** | How we evaluate readiness + MCP vision / gates |
| [`PROTOCOL.md`](./PROTOCOL.md) | Ralph-loop states and session discipline |
| [`PROGRESS.md`](./PROGRESS.md) | Session ledger (append outcomes from persona runs here) |
| [`LESSONS_LEARNED.md`](./LESSONS_LEARNED.md) | Surprises (e.g. `matView` vs `table_type`) |

### Handoff snippet (ship-readiness sessions)

```text
State: VERIFYING (ship readiness)
Read: questdb-loop/PRD.md, questdb-loop/V1_SHIP_CHECKLIST.md,
      questdb-loop/CONTEXT.md, questdb-loop/SHIP_READINESS_PRD.md,
      PROGRESS.md tail, LESSONS_LEARNED.md
Constraint: Track A only unless prompt says Track B.
Personas: contract → dialect → resilience → security → test → packaging
```

---

## Success definition

**Track A success:** A stranger can install the QuestDB adapter, connect to a default PGWire QuestDB, browse catalog, run dialect-appropriate SQL, hit documented limitations without corruption or crashes, and CI protects regressions.

**Track B success (later):** An MCP-capable AI client can list/connect/query through Harlequin adapters with safe defaults, including QuestDB as one of many backends—not a one-off QuestDB MCP.
