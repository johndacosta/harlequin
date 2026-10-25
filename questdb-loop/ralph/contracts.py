"""Agent I/O contracts and YAML parsing for issue-thread routing."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

YAML_FENCE = re.compile(r"```ya?ml\s*(.*?)```", re.DOTALL | re.IGNORECASE)

# Who may participate in blocking issue threads (grill/select/verify).
ROUTABLE = frozenset(
    {
        "architect",
        "product_lead",
        "security",
        "dialect_specialist",
        "qa",
        "developer",
        "budget_steward",
        "release_steward",
    }
)

# Keyword → agents to seed when Architect forgets needs_agents
TOPIC_HINTS: list[tuple[re.Pattern[str], list[str]]] = [
    (
        re.compile(
            r"catalog|tables\(|table_columns|designated|partition|matView|functions\(",
            re.I,
        ),
        ["dialect_specialist", "qa"],
    ),
    (
        re.compile(r"escap|inject|password|secret|drop\s+database|destructive", re.I),
        ["security"],
    ),
    (re.compile(r"test|pytest|docker|smoke|online", re.I), ["qa"]),
    (re.compile(r"doc|readme|pypi|package|install|guide", re.I), ["release_steward"]),
    (
        re.compile(r"complet|sample by|asof|latest on|perf|export", re.I),
        ["dialect_specialist", "product_lead"],
    ),
]


@dataclass
class OpenIssue:
    id: str
    topic: str
    needs_agents: list[str] = field(default_factory=list)
    blocking: bool = True
    raised_by: str = "architect"


@dataclass
class RouterMessage:
    persona: str
    verdict: str = "accept"
    addressed_to: str | None = None
    opposition_to: str | None = None
    next_agent: str | None = None
    needs_agents: list[str] = field(default_factory=list)
    open_issues: list[OpenIssue] = field(default_factory=list)
    resolved_issues: list[str] = field(default_factory=list)
    ready_to_pass: bool = False
    blocking: bool = True
    summary: str = ""
    raw_yaml: str = ""
    turn_id: str = ""


def extract_yaml_block(text: str) -> str:
    blocks = YAML_FENCE.findall(text or "")
    return blocks[-1].strip() if blocks else ""


def _strip_inline_comment(val: str) -> str:
    val = val.strip()
    if not val:
        return val
    if val[0] in ('"', "'") and val[-1] == val[0] and len(val) >= 2:
        return val[1:-1]
    if " #" in val:
        val = val.split(" #", 1)[0].strip()
    return val.strip("\"'")


def _flag(block: str, key: str, default: str = "") -> str:
    m = re.search(rf"^{re.escape(key)}:\s*(.+)$", block, re.MULTILINE)
    if not m:
        return default
    return _strip_inline_comment(m.group(1))


def _parse_list(block: str, key: str) -> list[str]:
    # needs_agents: [a, b] or resolved_issues: [i1]
    m = re.search(rf"^{re.escape(key)}:\s*\[(.*?)\]", block, re.MULTILINE)
    if not m:
        return []
    inner = m.group(1).strip()
    if not inner:
        return []
    return [x.strip().strip("\"'") for x in inner.split(",") if x.strip()]


def _parse_open_issues(block: str, raised_by: str) -> list[OpenIssue]:
    issues: list[OpenIssue] = []
    # Simple line form: - {id: i1, topic: "...", needs_agents: [security]}
    for m in re.finditer(
        r"-\s*\{([^}]+)\}",
        block[block.find("open_issues:") :] if "open_issues:" in block else "",
    ):
        body = m.group(1)
        id_m = re.search(r"id:\s*([^,]+)", body)
        topic_m = re.search(
            r"topic:\s*\"([^\"]+)\"|topic:\s*'([^']+)'|topic:\s*([^,]+)", body
        )
        needs = re.search(r"needs_agents:\s*\[(.*?)\]", body)
        blocking_m = re.search(r"blocking:\s*(true|false)", body, re.I)
        if not id_m:
            continue
        topic = ""
        if topic_m:
            topic = (
                (topic_m.group(1) or topic_m.group(2) or topic_m.group(3) or "")
                .strip()
                .strip("\"'")
            )
        needs_list = []
        if needs and needs.group(1).strip():
            needs_list = [
                x.strip().strip("\"'") for x in needs.group(1).split(",") if x.strip()
            ]
        issues.append(
            OpenIssue(
                id=id_m.group(1).strip().strip("\"'"),
                topic=topic or "unspecified",
                needs_agents=[a for a in needs_list if a in ROUTABLE],
                blocking=(
                    blocking_m.group(1).lower() == "true" if blocking_m else True
                ),
                raised_by=raised_by,
            )
        )
    return issues


def parse_router_message(persona: str, text: str, turn_id: str) -> RouterMessage:
    block = extract_yaml_block(text)
    if not block:
        # Fail soft: treat as pass_turn so router can escalate
        return RouterMessage(
            persona=persona,
            verdict="pass_turn",
            ready_to_pass=True,
            turn_id=turn_id,
            summary="no yaml; treated as pass",
        )
    addressed = _flag(block, "addressed_to", "null")
    if addressed.lower() in ("null", "none", "~", ""):
        addressed_to = None
    else:
        addressed_to = addressed if addressed in ROUTABLE else None

    opp = _flag(block, "opposition_to", "null")
    if opp.lower() in ("null", "none", "~", ""):
        opposition_to = None
    else:
        opposition_to = opp

    nxt = _flag(block, "next_agent", "null")
    if nxt.lower() in ("null", "none", "~", ""):
        next_agent = None
    else:
        next_agent = nxt if nxt in ROUTABLE else None

    ready = _flag(block, "ready_to_pass", "false").lower() == "true"
    blocking = _flag(block, "blocking", "true").lower() != "false"

    return RouterMessage(
        persona=persona,
        verdict=_flag(block, "verdict", "accept").lower(),
        addressed_to=addressed_to,
        opposition_to=opposition_to,
        next_agent=next_agent,
        needs_agents=[a for a in _parse_list(block, "needs_agents") if a in ROUTABLE],
        open_issues=_parse_open_issues(block, persona),
        resolved_issues=_parse_list(block, "resolved_issues"),
        ready_to_pass=ready,
        blocking=blocking,
        summary=_flag(block, "summary", ""),
        raw_yaml=block,
        turn_id=turn_id,
    )


def hint_agents_for_text(text: str) -> list[str]:
    found: list[str] = []
    for pat, agents in TOPIC_HINTS:
        if pat.search(text):
            for a in agents:
                if a not in found:
                    found.append(a)
    return found or ["product_lead"]


def contract_blurb(persona: str) -> str:
    return (
        f"You are '{persona}'. Obey routing_protocol.md. "
        "Always end with the routing YAML contract "
        "(verdict, addressed_to, opposition_to, needs_agents, "
        "open_issues, resolved_issues, ready_to_pass, summary)."
    )
