"""Autonomous Ralph loop: Architect/Security/QA grill -> Developer -> verify."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from . import prompts
from .backend import get_backend
from .checklist import is_deliverable, must_remaining, next_prd_slice, summary
from .interaction_log import (
    append_interaction,
    write_turn_transcript,
)
from .state import LoopState, iteration_dir, load_state, reset_runtime, save_state

ROOT_MARKER = "V1_SHIP_CHECKLIST.md"
YAML_FENCE = re.compile(r"```ya?ml\s*(.*?)```", re.DOTALL | re.IGNORECASE)


def find_loop_root(start: Path | None = None) -> Path:
    cur = (start or Path.cwd()).resolve()
    for p in [cur, *cur.parents]:
        if (p / "questdb-loop" / ROOT_MARKER).exists():
            return p / "questdb-loop"
        if (p / ROOT_MARKER).exists() and p.name == "questdb-loop":
            return p
    raise SystemExit(
        "Could not find questdb-loop/V1_SHIP_CHECKLIST.md from cwd. "
        "Run from the harlequin repo."
    )


def repo_root(loop_root: Path) -> Path:
    return loop_root.parent


def agents_dir(loop_root: Path) -> Path:
    return loop_root / "ralph" / "agents"


def extract_yaml_block(text: str) -> str:
    """Prefer the yaml fence that carries build/routing control keys."""
    blocks = YAML_FENCE.findall(text or "")
    if not blocks:
        return ""
    scored: list[tuple[int, int, str]] = []
    for i, raw in enumerate(blocks):
        b = raw.strip()
        score = 0
        if re.search(r"^ready_for_build:\s*true", b, re.M | re.I):
            score += 100
        if re.search(r"^ready_for_build:", b, re.M | re.I):
            score += 40
        if re.search(r"^ready_for_verify:\s*true", b, re.M | re.I):
            score += 80
        if re.search(r"^ready_for_verify:", b, re.M | re.I):
            score += 30
        if re.search(r"^slice_id:", b, re.M | re.I):
            score += 20
        if re.search(r"^verdict:", b, re.M | re.I):
            score += 5
        if re.search(r"^checklist_targets:", b, re.M | re.I):
            score += 10
        scored.append((score, i, b))
    scored.sort(key=lambda t: (t[0], t[1]), reverse=True)
    return scored[0][2]


def yaml_flag(block: str, key: str, default: str = "") -> str:
    m = re.search(rf"^{re.escape(key)}:\s*(.+)$", block, re.MULTILINE)
    if not m:
        return default
    val = m.group(1).strip()
    if " #" in val and not (val[:1] in ('"', "'") and val[-1:] == val[:1]):
        val = val.split(" #", 1)[0].strip()
    return val.strip("\"'")


def yaml_flag_in_text(text: str, key: str, default: str = "") -> str:
    """Search all yaml fences; prefer an explicit true if present."""
    blocks = [b.strip() for b in YAML_FENCE.findall(text or "")]
    if not blocks:
        return default
    values: list[str] = []
    for b in blocks:
        v = yaml_flag(b, key, "")
        if v:
            values.append(v)
    if not values:
        return default
    for v in values:
        if v.lower() == "true":
            return "true"
    return values[-1]


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def system_for(loop_root: Path, persona: str, *, ponytail: bool = False) -> str:
    ad = agents_dir(loop_root)
    parts = [
        prompts.load_persona(ad, persona),
        prompts.load_persona(ad, "routing_protocol"),
        prompts.load_persona(ad, "grill_protocol"),
    ]
    if ponytail or persona == "developer":
        parts.append(prompts.load_persona(ad, "ponytail"))
    return "\n\n---\n\n".join(p for p in parts if p.strip())


def run_persona(
    backend,
    *,
    loop_root: Path,
    persona: str,
    prompt: str,
    ponytail: bool = False,
    iteration: int | None = None,
    phase: str | None = None,
    turn_id: str | None = None,
    turns_dir: Path | None = None,
    issue_id: str | None = None,
    backend_name: str | None = None,
) -> str:
    text = backend.run(
        persona=persona,
        system=system_for(loop_root, persona, ponytail=ponytail),
        prompt=prompt,
        cwd=repo_root(loop_root),
    )
    if phase is not None and turns_dir is not None:
        tid = turn_id or f"{phase}-{persona}"
        tpath = turns_dir / f"{tid}.md"
        write_turn_transcript(tpath, turn_id=tid, agent=persona, text=text)
        append_interaction(
            loop_root,
            iteration=iteration,
            phase=phase,
            agent=persona,
            turn_id=tid,
            transcript_path=tpath,
            text=text,
            backend=backend_name or type(backend).__name__,
            issue_id=issue_id,
        )
    return text


def phase_select(
    backend,
    loop_root: Path,
    state: LoopState,
    it_dir: Path,
    *,
    routing: str = "issue",
) -> None:
    from .contracts import OpenIssue, hint_agents_for_text
    from .router import dump_board, run_issue_board

    turns_dir = it_dir / "turns"
    backend_name = type(backend).__name__
    next_prd = next_prd_slice(loop_root / "V1_SHIP_CHECKLIST.md")
    out = run_persona(
        backend,
        loop_root=loop_root,
        persona="architect",
        prompt=prompts.architect_select_prompt(loop_root, it_dir),
        iteration=state.iteration,
        phase="SELECT",
        turn_id="SELECT-00-architect",
        turns_dir=turns_dir,
        backend_name=backend_name,
    )
    write(it_dir / "select.md", out)

    if routing == "round-robin":
        prod = run_persona(
            backend,
            loop_root=loop_root,
            persona="product_lead",
            prompt=prompts.product_review_select_prompt(loop_root, it_dir, out),
            iteration=state.iteration,
            phase="SELECT",
            turn_id="SELECT-01-product_lead",
            turns_dir=turns_dir,
            backend_name=backend_name,
        )
        write(it_dir / "select_product_review.md", prod)
        if yaml_flag(extract_yaml_block(prod), "verdict") == "kill":
            out = run_persona(
                backend,
                loop_root=loop_root,
                persona="architect",
                prompt=prompts.architect_select_prompt(loop_root, it_dir)
                + f"\n\nProduct Lead KILLED prior slice.\n{prod}",
                iteration=state.iteration,
                phase="SELECT",
                turn_id="SELECT-02-architect-retry",
                turns_dir=turns_dir,
                backend_name=backend_name,
            )
            write(it_dir / "select.md", out)
    else:
        hints = hint_agents_for_text(out)
        seed = [
            OpenIssue(
                id="slice_priority",
                topic="Is this the highest-ROI Must-aligned slice for users?",
                needs_agents=["product_lead"]
                + [h for h in hints if h != "product_lead"][:1],
                blocking=True,
                raised_by="architect",
            )
        ]
        shared = prompts.shared_context(loop_root)

        def _run(persona: str, prompt: str) -> str:
            return run_persona(
                backend, loop_root=loop_root, persona=persona, prompt=prompt
            )

        board, synth = run_issue_board(
            run=_run,
            phase="SELECT",
            shared_context=shared + f"\n\n## Architect proposal\n{out}",
            seed_issues=seed,
            synthesizer="architect",
            phase_cap=6,
            max_turns_per_thread=4,
            synthesize_prompt=(
                "SELECT synthesis: confirm slice after Product debate.\n"
                "Emit EXACTLY ONE ```yaml fence with slice_id and "
                "ready_for_build: false.\n"
                "If killed, pick a different Must. Do not emit a second yaml block."
            ),
            loop_root=loop_root,
            iteration=state.iteration,
            turns_dir=turns_dir,
            backend_name=backend_name,
        )
        dump_board(board, it_dir / "select_board.json", turns_dir=turns_dir)
        if synth:
            write(it_dir / "select_synthesis.md", synth)
            out = synth

    block = extract_yaml_block(out)
    default_slice = (
        next_prd.prd_id if next_prd is not None else f"iter-{state.iteration:03d}"
    )
    parsed_slice = yaml_flag_in_text(out, "slice_id", "") or yaml_flag(
        block, "slice_id", ""
    )
    if (not parsed_slice or parsed_slice == "dry-run-slice") and next_prd is not None:
        state.slice_id = next_prd.prd_id
        state.active_prd_path = next_prd.prd_path
    else:
        state.slice_id = parsed_slice or default_slice
        if next_prd is not None and state.slice_id == next_prd.prd_id:
            state.active_prd_path = next_prd.prd_path
    write(it_dir / "slice_id.txt", state.slice_id or "")
    state.phase = "GRILL"


def phase_advisory(
    backend,
    loop_root: Path,
    state: LoopState,
    it_dir: Path,
) -> str | None:
    """Returns 'stop' if Budget Steward says stop, else None."""
    import json
    from dataclasses import asdict

    blob = json.dumps(asdict(state), indent=2)
    adv_dir = it_dir / "advisory"
    adv_dir.mkdir(exist_ok=True)
    turns_dir = it_dir / "turns"
    backend_name = type(backend).__name__
    stop = False
    for persona in ("budget_steward", "tech_strategy", "horizon_scout"):
        out = run_persona(
            backend,
            loop_root=loop_root,
            persona=persona,
            prompt=prompts.advisory_prompt(loop_root, it_dir, persona, blob),
            iteration=state.iteration,
            phase="ADVISORY",
            turn_id=f"ADVISORY-{persona}",
            turns_dir=turns_dir,
            backend_name=backend_name,
        )
        write(adv_dir / f"{persona}.md", out)
        if persona == "budget_steward":
            if yaml_flag(extract_yaml_block(out), "verdict") == "stop":
                stop = True
    if stop:
        stop_path = loop_root / "ralph" / "state" / "STOP"
        stop_path.parent.mkdir(parents=True, exist_ok=True)
        stop_path.write_text("budget_steward requested stop\n", encoding="utf-8")
        return "stop"
    return None


def phase_grill(
    backend,
    loop_root: Path,
    state: LoopState,
    it_dir: Path,
    *,
    routing: str = "issue",
) -> None:
    from .contracts import OpenIssue, hint_agents_for_text
    from .router import dump_board, run_issue_board

    if routing == "round-robin":
        _phase_grill_round_robin(backend, loop_root, state, it_dir)
        return

    select_txt = ""
    for name in ("select_synthesis.md", "select.md"):
        p = it_dir / name
        if p.exists():
            select_txt = p.read_text(encoding="utf-8")
            break

    hints = hint_agents_for_text(select_txt)
    needs: list[str] = []
    for a in ["security", *hints]:
        if a not in needs and a != "architect":
            needs.append(a)
    needs = needs[:3] or ["security", "product_lead"]

    seed = [
        OpenIssue(
            id="slice_validity",
            topic="Validate slice against ADRs/checklist; name risks before build",
            needs_agents=needs,
            blocking=True,
            raised_by="architect",
        )
    ]
    if any(x in select_txt.lower() for x in ("catalog", "designated", "partition")):
        seed.append(
            OpenIssue(
                id="catalog_truth",
                topic="QuestDB meta for designated timestamp / partition strategy",
                needs_agents=["dialect_specialist", "qa"],
                blocking=True,
                raised_by="architect",
            )
        )

    shared = prompts.shared_context(loop_root)
    turns_dir = it_dir / "turns"
    backend_name = type(backend).__name__

    def _run(persona: str, prompt: str) -> str:
        return run_persona(backend, loop_root=loop_root, persona=persona, prompt=prompt)

    board, synth = run_issue_board(
        run=_run,
        phase="GRILL",
        shared_context=shared + f"\n\n## Slice proposal\n{select_txt}",
        seed_issues=seed,
        synthesizer="architect",
        phase_cap=12,
        max_turns_per_thread=4,
        synthesize_prompt=(
            "GRILL synthesis: write slice_spec content.\n"
            "Emit EXACTLY ONE ```yaml fence that MUST include:\n"
            "  ready_for_build: true\n"
            "  slice_id: <id>\n"
            "  ponytail_level: full\n"
            "  checklist_targets: [...]\n"
            "Set ready_for_build: true only if blocking issues resolved "
            "or slice shrunk.\n"
            "Do not emit a second yaml block."
        ),
        loop_root=loop_root,
        iteration=state.iteration,
        turns_dir=turns_dir,
        backend_name=backend_name,
    )
    dump_board(board, it_dir / "grill" / "board.json", turns_dir=turns_dir)
    if not synth:
        state.phase = "FAILED"
        state.last_error = "Grill synthesis missing"
        return
    write(it_dir / "grill" / "consensus.md", synth)
    write(it_dir / "slice_spec.md", synth)
    ready = yaml_flag_in_text(synth, "ready_for_build", "false")
    if ready != "true":
        # Soft-heal: if board cleared and slice_id present, allow build.
        if (
            not board.blocking_open()
            and yaml_flag_in_text(synth, "slice_id", "")
            and "ready for build" in synth.lower()
        ):
            ready = "true"
    if ready != "true":
        state.phase = "FAILED"
        state.last_error = "Grill did not reach ready_for_build"
        return
    state.phase = "BUILD"


def _phase_grill_round_robin(
    backend, loop_root: Path, state: LoopState, it_dir: Path
) -> None:
    """Legacy everyone-speaks path (debug)."""
    grill_log = it_dir / "grill" / "architect_log.md"
    turns_dir = it_dir / "turns"
    backend_name = type(backend).__name__
    prior = ""
    ready = False
    for round_n in range(1, 9):
        arch = run_persona(
            backend,
            loop_root=loop_root,
            persona="architect",
            prompt=prompts.architect_grill_question_prompt(
                loop_root, it_dir, round_n, prior
            ),
            iteration=state.iteration,
            phase="GRILL",
            turn_id=f"GRILL-rr-{round_n:02d}-architect",
            turns_dir=turns_dir,
            backend_name=backend_name,
        )
        prior += f"\n\n# Architect round {round_n}\n{arch}\n"
        write(grill_log, prior)
        if yaml_flag(extract_yaml_block(arch), "ready_for_build") == "true":
            write(it_dir / "slice_spec.md", arch)
            write(it_dir / "grill" / "consensus.md", arch)
            ready = True
            break
        for peer in ("security", "qa", "dialect_specialist"):
            ans = run_persona(
                backend,
                loop_root=loop_root,
                persona=peer,
                prompt=prompts.peer_answer_prompt(loop_root, peer, arch, it_dir),
                iteration=state.iteration,
                phase="GRILL",
                turn_id=f"GRILL-rr-{round_n:02d}-{peer}",
                turns_dir=turns_dir,
                backend_name=backend_name,
            )
            write(it_dir / "grill" / f"{peer}_r{round_n}.md", ans)
            prior += f"\n\n# {peer} round {round_n}\n{ans}\n"
            write(grill_log, prior)
    if not ready:
        state.phase = "FAILED"
        state.last_error = "Grill did not reach ready_for_build"
        return
    state.phase = "BUILD"


def phase_build(backend, loop_root: Path, state: LoopState, it_dir: Path) -> None:
    out = run_persona(
        backend,
        loop_root=loop_root,
        persona="developer",
        prompt=prompts.developer_build_prompt(loop_root, it_dir),
        ponytail=True,
        iteration=state.iteration,
        phase="BUILD",
        turn_id="BUILD-developer",
        turns_dir=it_dir / "turns",
        backend_name=type(backend).__name__,
    )
    write(it_dir / "build" / "developer_log.md", out)
    block = extract_yaml_block(out)
    if yaml_flag(block, "ready_for_verify", "false").lower() != "true":
        state.phase = "FAILED"
        state.last_error = "Developer not ready_for_verify"
        return
    state.phase = "VERIFY"


def phase_verify(
    backend,
    loop_root: Path,
    state: LoopState,
    it_dir: Path,
    *,
    routing: str = "issue",
) -> None:
    from .contracts import OpenIssue
    from .router import dump_board, run_issue_board

    if routing == "round-robin":
        _phase_verify_linear(backend, loop_root, state, it_dir)
        return

    shared = prompts.shared_context(loop_root)
    seed = [
        OpenIssue(
            id="verify_qa",
            topic="Do acceptance checks pass for this slice?",
            needs_agents=["qa"],
            blocking=True,
            raised_by="architect",
        ),
        OpenIssue(
            id="verify_security",
            topic="Any P0/P1 security regressions in this slice?",
            needs_agents=["security"],
            blocking=True,
            raised_by="architect",
        ),
    ]
    remaining = len(must_remaining(loop_root / "V1_SHIP_CHECKLIST.md"))
    if remaining <= 5:
        seed.append(
            OpenIssue(
                id="verify_release",
                topic="Docs/package honesty for stranger install",
                needs_agents=["release_steward"],
                blocking=True,
                raised_by="architect",
            )
        )

    spec = ""
    if (it_dir / "slice_spec.md").exists():
        spec = (it_dir / "slice_spec.md").read_text(encoding="utf-8")
    dev = ""
    if (it_dir / "build" / "developer_log.md").exists():
        dev = (it_dir / "build" / "developer_log.md").read_text(encoding="utf-8")

    def _run(persona: str, prompt: str) -> str:
        return run_persona(backend, loop_root=loop_root, persona=persona, prompt=prompt)

    turns_dir = it_dir / "turns"
    backend_name = type(backend).__name__
    board, synth = run_issue_board(
        run=_run,
        phase="VERIFY",
        shared_context=shared + f"\n\n## slice_spec\n{spec}\n\n## developer_log\n{dev}",
        seed_issues=seed,
        synthesizer="architect",
        phase_cap=10,
        max_turns_per_thread=4,
        synthesize_prompt=(
            "VERIFY synthesis: overall pass/fail. "
            "If fail, list blockers. Emit YAML verdict: pass|fail and "
            "qa/security summaries for progress.md."
        ),
        loop_root=loop_root,
        iteration=state.iteration,
        turns_dir=turns_dir,
        backend_name=backend_name,
    )
    dump_board(board, it_dir / "verify" / "board.json", turns_dir=turns_dir)
    if synth:
        write(it_dir / "verify" / "summary.md", synth)
    block = extract_yaml_block(synth or "")
    verdict = yaml_flag(block, "verdict", "fail").lower()
    write(
        it_dir / "verify" / "qa_yaml.txt",
        block or f"verdict: {verdict}\n",
    )
    write(
        it_dir / "verify" / "sec_yaml.txt",
        block or f"verdict: {verdict}\n",
    )
    if verdict not in ("pass", "accept") or board.blocking_open() or board.force_closed:
        state.phase = "FAILED"
        state.last_error = f"Verify failed verdict={verdict}"
        return
    state.phase = "PROGRESS"


def _phase_verify_linear(
    backend, loop_root: Path, state: LoopState, it_dir: Path
) -> None:
    turns_dir = it_dir / "turns"
    backend_name = type(backend).__name__
    qa = run_persona(
        backend,
        loop_root=loop_root,
        persona="qa",
        prompt=prompts.verify_prompt(loop_root, it_dir, "qa"),
        iteration=state.iteration,
        phase="VERIFY",
        turn_id="VERIFY-qa",
        turns_dir=turns_dir,
        backend_name=backend_name,
    )
    write(it_dir / "verify" / "qa_report.md", qa)
    sec = run_persona(
        backend,
        loop_root=loop_root,
        persona="security",
        prompt=prompts.verify_prompt(loop_root, it_dir, "security"),
        iteration=state.iteration,
        phase="VERIFY",
        turn_id="VERIFY-security",
        turns_dir=turns_dir,
        backend_name=backend_name,
    )
    write(it_dir / "verify" / "security_report.md", sec)
    remaining = len(must_remaining(loop_root / "V1_SHIP_CHECKLIST.md"))
    rel_v = "not_applicable"
    if remaining <= 5:
        rel = run_persona(
            backend,
            loop_root=loop_root,
            persona="release_steward",
            prompt=prompts.release_verify_prompt(loop_root, it_dir),
            iteration=state.iteration,
            phase="VERIFY",
            turn_id="VERIFY-release_steward",
            turns_dir=turns_dir,
            backend_name=backend_name,
        )
        write(it_dir / "verify" / "release_report.md", rel)
        rel_v = yaml_flag(extract_yaml_block(rel), "verdict", "not_applicable")
    qa_v = yaml_flag(extract_yaml_block(qa), "verdict", "fail")
    sec_v = yaml_flag(extract_yaml_block(sec), "verdict", "fail")
    write(
        it_dir / "verify" / "summary.md",
        f"qa={qa_v}\nsecurity={sec_v}\nrelease={rel_v}\n",
    )
    if qa_v != "pass" or sec_v != "pass":
        state.phase = "FAILED"
        state.last_error = f"Verify failed qa={qa_v} security={sec_v}"
        return
    if rel_v == "fail":
        state.phase = "FAILED"
        state.last_error = "Release Steward failed verify"
        return
    state.phase = "PROGRESS"
    write(it_dir / "verify" / "qa_yaml.txt", extract_yaml_block(qa))
    write(it_dir / "verify" / "sec_yaml.txt", extract_yaml_block(sec))


def phase_progress(backend, loop_root: Path, state: LoopState, it_dir: Path) -> None:
    qa_yaml = (it_dir / "verify" / "qa_yaml.txt").read_text(encoding="utf-8")
    sec_yaml = (it_dir / "verify" / "sec_yaml.txt").read_text(encoding="utf-8")
    out = run_persona(
        backend,
        loop_root=loop_root,
        persona="architect",
        prompt=prompts.progress_prompt(loop_root, it_dir, qa_yaml, sec_yaml),
        iteration=state.iteration,
        phase="PROGRESS",
        turn_id="PROGRESS-architect",
        turns_dir=it_dir / "turns",
        backend_name=type(backend).__name__,
    )
    write(it_dir / "progress.md", out)
    state.history.append(
        {
            "iteration": state.iteration,
            "slice_id": state.slice_id,
            "prd_path": state.active_prd_path,
            "result": "ok",
        }
    )
    if is_deliverable(loop_root / "V1_SHIP_CHECKLIST.md"):
        state.deliverable = True
        state.phase = "DONE"
    else:
        state.deliverable = False
        state.phase = "SELECT"


def run_iteration(
    backend,
    loop_root: Path,
    state: LoopState,
    *,
    advisory_every: int = 3,
    routing: str = "issue",
) -> LoopState:
    state.iteration += 1
    it_dir = iteration_dir(loop_root, state.iteration)
    state.phase = "SELECT"
    save_state(loop_root, state)

    if advisory_every > 0 and state.iteration % advisory_every == 1:
        if phase_advisory(backend, loop_root, state, it_dir) == "stop":
            state.phase = "FAILED"
            state.last_error = "Budget Steward stop"
            return state

    phase_select(backend, loop_root, state, it_dir, routing=routing)
    save_state(loop_root, state)
    if state.phase == "FAILED":
        return state

    phase_grill(backend, loop_root, state, it_dir, routing=routing)
    save_state(loop_root, state)
    if state.phase == "FAILED":
        return state

    phase_build(backend, loop_root, state, it_dir)
    save_state(loop_root, state)
    if state.phase == "FAILED":
        return state

    phase_verify(backend, loop_root, state, it_dir, routing=routing)
    save_state(loop_root, state)
    if state.phase == "FAILED":
        return state

    phase_progress(backend, loop_root, state, it_dir)
    save_state(loop_root, state)
    return state


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Ralph autonomy loop for QuestDB adapter & codebase PRDs"
    )
    parser.add_argument(
        "--backend",
        choices=("dry-run", "cursor", "agent-cli", "ollama", "hybrid"),
        default="dry-run",
        help=(
            "dry-run | agent-cli | cursor | ollama | hybrid "
            "(Cursor judgment+tools, Ollama codegen)"
        ),
    )
    parser.add_argument("--model", default="composer-2.5")
    parser.add_argument(
        "--max-iterations",
        type=int,
        default=None,
        help="Override max iterations (default 50 or prior state)",
    )
    parser.add_argument(
        "--advisory-every",
        type=int,
        default=3,
        help="Budget/Tech/Horizon every N iters (1=always, 0=off)",
    )
    parser.add_argument(
        "--routing",
        choices=("issue", "round-robin"),
        default="issue",
        help="issue=pairwise ROI router (default); round-robin=legacy",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run a single iteration then exit",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Reset loop state before running",
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Print checklist + loop state and exit",
    )
    args = parser.parse_args(argv)

    loop_root = find_loop_root()
    checklist = loop_root / "V1_SHIP_CHECKLIST.md"

    if args.status:
        state = load_state(loop_root)
        save_state(loop_root, state)
        print("checklist:", summary(checklist))
        print(
            f"state: phase={state.phase} "
            f"iteration={state.iteration}/{state.max_iterations} "
            f"slice_id={state.slice_id} active_prd_path={state.active_prd_path} "
            f"deliverable={state.deliverable}"
        )
        rem = must_remaining(checklist)
        print(f"remaining Must ({len(rem)}):")
        for i in rem:
            print(f"  - [{i.section}] {i.text}")
        return 0

    if args.reset:
        state = reset_runtime(loop_root, max_iterations=args.max_iterations or 50)
    else:
        state = load_state(loop_root)
    if args.max_iterations is not None:
        state.max_iterations = args.max_iterations
        save_state(loop_root, state)

    if is_deliverable(checklist):
        state.deliverable = True
        state.phase = "DONE"
        save_state(loop_root, state)
        print("Already deliverable: all Must checklist items are checked.")
        return 0
    else:
        state.deliverable = False
        if state.phase == "DONE":
            state.phase = "SELECT"
        save_state(loop_root, state)

    # Stop file
    if (loop_root / "ralph" / "state" / "STOP").exists():
        print("STOP file present — exiting.")
        return 2

    backend = get_backend(args.backend, args.model)
    print(
        f"Ralph start backend={args.backend} model={args.model} "
        f"routing={args.routing} summary={summary(checklist)}"
    )

    while True:
        if (loop_root / "ralph" / "state" / "STOP").exists():
            print("STOP file detected — graceful exit.")
            return 2
        if state.iteration >= state.max_iterations:
            if state.history and all(
                h.get("result") == "ok" for h in state.history[-state.max_iterations :]
            ):
                state.phase = "DONE" if state.deliverable else "SELECT"
                state.last_error = None
                save_state(loop_root, state)
                print(
                    f"Stopped after {state.iteration}/{state.max_iterations} "
                    "iterations (cap). Not deliverable yet — re-run with higher --max "
                    "or --live to continue."
                )
                return 0
            state.phase = "FAILED"
            state.last_error = "max_iterations reached"
            save_state(loop_root, state)
            print(state.last_error)
            return 1
        if state.deliverable or is_deliverable(checklist):
            state.deliverable = True
            state.phase = "DONE"
            save_state(loop_root, state)
            print("DELIVERABLE: all Must items complete.")
            return 0

        print(f"\n=== Iteration {state.iteration + 1}/{state.max_iterations} ===")
        state = run_iteration(
            backend,
            loop_root,
            state,
            advisory_every=args.advisory_every,
            routing=args.routing,
        )
        save_state(loop_root, state)
        last = state.history[-1] if state.history else {}
        print(
            f"done_iteration={state.iteration} slice={state.slice_id} "
            f"result={last.get('result')} next_phase={state.phase} "
            f"err={state.last_error}"
        )

        if state.phase == "DONE":
            print("DELIVERABLE.")
            return 0
        if state.phase == "FAILED":
            print("Iteration failed — see ralph/state/iterations/ and fix/restart.")
            state.history.append(
                {
                    "iteration": state.iteration,
                    "slice_id": state.slice_id,
                    "prd_path": state.active_prd_path,
                    "result": "failed",
                    "error": state.last_error,
                }
            )
            state.phase = "SELECT"
            state.last_error = None
            save_state(loop_root, state)
            if args.once:
                return 1
            continue
        if args.once:
            return 0


if __name__ == "__main__":
    sys.exit(main())
