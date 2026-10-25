# Routing protocol (issue threads)

You are in a **token-efficient multi-agent board**, not a round-robin meeting.

## Rules

1. Speak only to resolve the **current issue** and thread you were given.
2. Prefer **pairwise** debate: set `addressed_to` to exactly one persona.
3. If you disagree, set `verdict: reject` or `amend`, set `opposition_to` to the turn id you oppose, and `addressed_to` to that speaker.
4. Do **not** invite the whole team. Escalate with `needs_agents: [one_persona]` only when the pair cannot resolve (missing expertise).
5. When the issue is settled, list it under `resolved_issues` and set `ready_to_pass: true`.
6. Horizon / MCP ideas never create **blocking** issues (ADR 0001). Use `blocking: false` or don’t open them.
7. Keep `summary` to one line. Put detail in prose above the YAML.

## Who to address

| Topic | Prefer |
|-------|--------|
| User value / priority / kill slice | product_lead |
| Escaping, secrets, destructive SQL | security |
| QuestDB SQL / meta / types / pin | dialect_specialist |
| Testability / commands | qa |
| Implementation cost / minimal diff | developer |
| Docs / PyPI / stranger install | release_steward |
| Loop spend / STOP | budget_steward |
| Synthesize / shrink slice / checklist | architect |

## Efficiency

- One question or one objection per turn.
- If you `accept`, set `ready_to_pass: true` and `addressed_to: null` (or `architect` for synthesize).
- Do not restate the whole PRD.
