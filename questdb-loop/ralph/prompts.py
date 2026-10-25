"""Prompt builders for each Ralph phase / persona."""

from __future__ import annotations

from pathlib import Path

from .checklist import must_remaining, next_prd_slice, summary


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def load_persona(agents_dir: Path, name: str) -> str:
    return _read(agents_dir / f"{name}.md")


def active_prd_context(loop_root: Path) -> str:
    repo = loop_root.parent if loop_root.name == "questdb-loop" else loop_root
    nxt = next_prd_slice(loop_root / "V1_SHIP_CHECKLIST.md")
    if nxt is None:
        return ""
    prd_file = repo / nxt.prd_path
    prd_body = _read(prd_file)
    return (
        f"## Next Queued Atomic PRD Slice: {nxt.prd_id} "
        f"({nxt.category} | {nxt.severity})\n"
        f"- **PRD Spec File**: `{nxt.prd_path}`\n"
        f"- **Suggested Commit / PR Title**: `{nxt.commit_title}`\n"
        "- **Rule**: Work ONLY this single PRD slice in this iteration so it "
        "lands as a separate atomic commit/PR.\n\n"
        f"{prd_body}"
    )


def shared_context(loop_root: Path) -> str:
    repo = loop_root.parent if loop_root.name == "questdb-loop" else loop_root
    # loop_root is questdb-loop/
    bits = [
        "## Checklist summary",
        str(summary(loop_root / "V1_SHIP_CHECKLIST.md")),
        "",
        "## Remaining Must items",
    ]
    for item in must_remaining(loop_root / "V1_SHIP_CHECKLIST.md")[:12]:
        bits.append(f"- [ ] {item.text}")
    prd_ctx = active_prd_context(loop_root)
    if prd_ctx:
        bits.extend(["", prd_ctx])
    bits.extend(
        [
            "",
            "## Read these files (do not contradict ADRs)",
            "- questdb-loop/PRD.md",
            "- questdb-loop/PERF_AND_BUGS_PRD.md",
            "- questdb-loop/prds/README.md",
            "- questdb-loop/V1_SHIP_CHECKLIST.md",
            "- questdb-loop/CONTEXT.md",
            "- questdb-loop/docs/adr/*",
            "- questdb-loop/PROGRESS.md (tail)",
            "- questdb-loop/LESSONS_LEARNED.md",
            "- questdb-loop/HORIZON.md",
            "- questdb-loop/PERSONAS.md",
            "- src/harlequin/**",
            "- src/harlequin_duckdb/**",
            "- src/harlequin_sqlite/**",
            "- src/harlequin_questdb/**",
            "",
            f"Repo cwd for tools: {repo}",
        ]
    )
    return "\n".join(bits)


def product_review_select_prompt(
    loop_root: Path, it_dir: Path, select_text: str
) -> str:
    return f"""
Review the Architect's proposed slice for user/adoption value.
Kill or reorder if it is Postgres cosplay, Horizon/MCP sneak-in, or low user value.

## Architect select output
{select_text}

{shared_context(loop_root)}

Iteration: {it_dir}
Include product_lead YAML contract.
""".strip()


def advisory_prompt(
    loop_root: Path, it_dir: Path, persona: str, state_blob: str
) -> str:
    return f"""
Advisory council turn as {persona}. Read PERSONAS.md role for you.
This does not implement code. Horizon Scout must only append ideas to HORIZON.md
and must set block_v1: false.

## Loop state
{state_blob}

{shared_context(loop_root)}

Iteration dir: {it_dir}
Include your persona YAML contract.
""".strip()


def release_verify_prompt(loop_root: Path, it_dir: Path) -> str:
    return f"""
Release Steward verify: docs/packaging/pin honesty for this slice (or not_applicable).

Slice spec:
{_read(it_dir / "slice_spec.md")}

Developer log:
{_read(it_dir / "build" / "developer_log.md")}

{shared_context(loop_root)}
""".strip()


def architect_select_prompt(loop_root: Path, it_dir: Path) -> str:
    return f"""
You are starting a Ralph iteration. Select the next atomic PRD slice from
V1_SHIP_CHECKLIST.md / questdb-loop/prds/.
Each iteration MUST work exactly ONE PRD slice so it can be committed and
reviewed as a separate atomic PR.

{shared_context(loop_root)}

Write:
1. `{it_dir / "slice_id.txt"}` content conceptually — include slice_id in YAML
2. Full `{it_dir / "grill" / "opening.md"}` describing the proposed PRD slice

Follow grill_protocol.md after this turn (orchestrator will call grill next).
End with the architect YAML contract (ready_for_build: false until consensus).
""".strip()


def architect_grill_question_prompt(
    loop_root: Path, it_dir: Path, round_n: int, prior: str
) -> str:
    return f"""
Peer grill round {round_n}/8. Ask EXACTLY ONE question with your recommended answer.
Peers will answer from docs/code — no human.

Prior grill log:
{prior}

{shared_context(loop_root)}

Append your question to the response clearly as:
### Q{round_n}
**Question:** ...
**Recommend:** ...

If consensus is already enough to build, write the full slice_spec and set
ready_for_build: true.
Write slice spec path conceptually: {it_dir / "slice_spec.md"}
Also write consensus notes.

Include architect YAML contract.
""".strip()


def peer_answer_prompt(
    loop_root: Path,
    persona: str,
    question_block: str,
    it_dir: Path,
) -> str:
    return f"""
Answer the Architect's latest grill question as {persona}.
Use Accept / Reject / Amend. Cite paths. Look up facts in the repo.

Question:
{question_block}

{shared_context(loop_root)}

Iteration dir: {it_dir}
Include your persona YAML contract at the end.
""".strip()


def developer_build_prompt(loop_root: Path, it_dir: Path) -> str:
    spec = _read(it_dir / "slice_spec.md") or _read(it_dir / "grill" / "consensus.md")
    return f"""
BUILD PHASE. Implement the atomic PRD slice. Ponytail is MANDATORY.

## slice_spec
{spec}

{shared_context(loop_root)}

Constraints:
- Only this single PRD slice (1 PRD = 1 separate commit/PR)
- Minimal, focused diff matching the PRD specification
- Add/update unit or adapter tests as specified in the PRD
- Do not commit unless told

When done, summarize files changed and set ready_for_verify: true in YAML.
Write a short log to conceptually land in {it_dir / "build" / "developer_log.md"}
(include that content in your reply).
""".strip()


def verify_prompt(loop_root: Path, it_dir: Path, persona: str) -> str:
    return f"""
VERIFY PHASE as {persona}. Inspect this iteration's atomic PRD slice work only.

Slice spec:
{_read(it_dir / "slice_spec.md")}

Developer log:
{_read(it_dir / "build" / "developer_log.md")}

{shared_context(loop_root)}

Run checks you can. Record commands + exit codes in YAML.
""".strip()


def progress_prompt(loop_root: Path, it_dir: Path, qa_yaml: str, sec_yaml: str) -> str:
    return f"""
PROGRESS PHASE. If QA and Security passed, append a PROGRESS.md entry and
list which V1_SHIP_CHECKLIST Must boxes may be checked (only with evidence).

QA:
{qa_yaml}

Security:
{sec_yaml}

{shared_context(loop_root)}

When done, you MUST edit `questdb-loop/V1_SHIP_CHECKLIST.md` to mark completed Must
items `[x]` **only** when QA/Security evidence supports it. Append a short entry to
`questdb-loop/PROGRESS.md` with the suggested commit/PR message from the PRD.

If all Must items are now `[x]`, say DELIVERABLE in the YAML (deliverable: true).

Include architect YAML; set ready_for_build: false.
Optional keys:
```yaml
ralph_phase: architect
deliverable: true|false
checklist_marked: []
```
""".strip()
