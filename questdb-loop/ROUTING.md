# Agent I/O contracts & efficient routing

Replaces round-robin “everyone speaks every round” with **issue threads**: only the agents needed to resolve an open issue talk, usually **pairwise**, until that issue is closed—then the router advances.

Full protocol for models: [`ralph/agents/routing_protocol.md`](./ralph/agents/routing_protocol.md)  
Machine contracts: [`ralph/contracts.py`](./ralph/contracts.py) + [`ralph/router.py`](./ralph/router.py)

## Why

Round-robin wastes tokens (Dialect weighs in on unrelated packaging debates). Productive tension needs **opposition → rebuttal → resolve** between the right two agents before involving a third.

## I/O contract (every agent turn)

Each reply **must** end with:

```yaml
ralph_phase: <persona>
verdict: accept|reject|amend|question|pass_turn
addressed_to: <persona>|null          # who must answer next (pair partner)
opposition_to: <turn_id>|null         # which message you rebut
next_agent: <persona>|null            # handoff when ready_to_pass
needs_agents: []                      # escalate: spawn/widen issue
open_issues:
  - {id: i1, topic: "...", needs_agents: [security], blocking: true}
resolved_issues: []
ready_to_pass: false                  # true = leave this thread
blocking: true|false
summary: "<one line>"
```

### Inputs by persona (what the router feeds you)

| Persona | Inputs |
|---------|--------|
| Architect | checklist remaining, ADRs, open/resolved issues, thread transcript |
| Product Lead | proposed slice, user-value question, opposition from Architect |
| Security | slice/spec, code paths named, opposition |
| Dialect | SQL/meta claims, pin assumptions, opposition |
| QA | acceptance claims, how to test, opposition |
| Developer | implementation shape questions only (grill); slice_spec (build) |
| Budget Steward | call counts, thrash signals, open issue count |
| Tech Strategy / Horizon | advisory only (not in issue threads by default) |
| Release Steward | docs/package claims near release |

### Outputs that change routing

| Field | Effect |
|-------|--------|
| `addressed_to` | Next speaker in this thread (pair debate) |
| `opposition_to` | Marks conflict; partner should rebut before others join |
| `needs_agents` | Escalation — router may add a participant or new issue |
| `resolved_issues` | Closes issues; thread ends when blocking set empty |
| `ready_to_pass: true` | Exit thread; router picks next open issue or synthesizes |
| `verdict: reject` + blocking | Keeps issue open; partner must respond |

## Router algorithm (ROI)

```
while blocking issues open AND calls < phase_cap:
  issue = highest-priority open blocking issue
  thread = existing pair thread for issue OR create (raiser + first needs_agent)
  if thread at max_turns:
    escalate once (add one needs_agent) OR Architect force-resolve/shrink
  else:
    speaker = addressed_to OR partner who hasn't answered opposition OR raiser
    call ONLY speaker
    apply YAML to board
Architect synthesizes slice_spec when no blocking issues (or cap hit → shrink)
```

**Caps (defaults):** max 4 turns/thread, max 12 agent calls/grill phase, max 6 turns/select debate, never pull Horizon into blocking threads.

## Phase mapping

| Phase | Threads |
|-------|---------|
| SELECT | `slice_priority`: Architect ↔ Product Lead only |
| GRILL | Architect opens issues; router runs pair debates (Security/Dialect/QA/Dev as needed) |
| BUILD | Developer alone (+ Ponytail) |
| VERIFY | QA then Security; Release only if remaining Must ≤ 5; pairwise if reject |
| ADVISORY | Budget / Tech / Horizon — no issue board (unchanged cadence) |

## Enable

Default in `loop.py` is **issue routing** (`--routing issue`).  
Legacy round-robin: `--routing round-robin` (debug only).
