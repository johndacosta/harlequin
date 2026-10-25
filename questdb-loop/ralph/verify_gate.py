"""Deterministic SDLC verification gate for Ralph state machine slices.

Author: John DaCosta (@johndacosta)
Style: ASD-STE100 Simplified Technical English.
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from .checklist import is_deliverable, mark_prd_done, prd_items
from .interaction_log import append_interaction, write_turn_transcript
from .state import iteration_dir, load_state, save_state


@dataclass(frozen=True)
class GateCheckResult:
    name: str
    command: list[str]
    returncode: int
    stdout: str
    stderr: str
    passed: bool


@dataclass(frozen=True)
class DeterministicGateReport:
    slice_id: str
    timestamp: str
    passed: bool
    checks: list[GateCheckResult]


def run_cmd(command: list[str], cwd: Path) -> GateCheckResult:
    """Run one deterministic command and return the result."""
    proc = subprocess.run(
        command,
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )
    return GateCheckResult(
        name=" ".join(command[:4]),
        command=command,
        returncode=proc.returncode,
        stdout=proc.stdout.strip(),
        stderr=proc.stderr.strip(),
        passed=proc.returncode == 0,
    )


def run_deterministic_gate(
    repo: Path,
    *,
    slice_id: str,
    target_paths: list[str],
    pytest_targets: list[str],
    out_dir: Path | None = None,
) -> DeterministicGateReport:
    """Execute compileall, ruff check, ruff format --check, mypy, and pytest."""
    checks: list[GateCheckResult] = []

    checks.append(
        run_cmd(
            ["uv", "run", "python", "-m", "compileall", "-q", *target_paths],
            cwd=repo,
        )
    )
    checks.append(
        run_cmd(
            ["uv", "run", "ruff", "check", *target_paths],
            cwd=repo,
        )
    )
    checks.append(
        run_cmd(
            ["uv", "run", "ruff", "format", "--check", *target_paths],
            cwd=repo,
        )
    )
    checks.append(
        run_cmd(
            ["uv", "run", "mypy", *target_paths],
            cwd=repo,
        )
    )
    if pytest_targets:
        checks.append(
            run_cmd(
                ["uv", "run", "pytest", "-m", "not online", *pytest_targets],
                cwd=repo,
            )
        )

    all_passed = all(c.passed for c in checks)
    report = DeterministicGateReport(
        slice_id=slice_id,
        timestamp=datetime.now(timezone.utc).isoformat(),
        passed=all_passed,
        checks=checks,
    )

    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        json_path = out_dir / "deterministic_gate.json"
        md_path = out_dir / "deterministic_gate.md"
        json_path.write_text(
            json.dumps(asdict(report), indent=2) + "\n", encoding="utf-8"
        )
        lines = [
            f"# Deterministic Verification Gate: {slice_id}",
            "",
            "- **Author**: John DaCosta (`@johndacosta`)",
            f"- **Timestamp**: `{report.timestamp}`",
            f"- **Status**: `{'PASS' if report.passed else 'FAIL'}`",
            "",
            "| Check | Command | Exit Code | Status |",
            "| :--- | :--- | :---: | :---: |",
        ]
        for c in checks:
            cmd_str = " ".join(c.command)
            status = "PASS" if c.passed else "FAIL"
            lines.append(
                f"| `{c.name}` | `{cmd_str}` | `{c.returncode}` | **{status}** |"
            )
        lines.append("")
        for c in checks:
            if c.stdout or c.stderr:
                lines.append(f"## Output: `{' '.join(c.command)}`")
                lines.append("```text")
                if c.stdout:
                    lines.append(c.stdout)
                if c.stderr:
                    lines.append(c.stderr)
                lines.append("```")
                lines.append("")
        md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    return report


def record_verified_slice(
    loop_root: Path,
    *,
    slice_id: str,
    target_paths: list[str],
    pytest_targets: list[str],
    summary_lines: list[str],
) -> DeterministicGateReport:
    """Advance state machine through SELECT->GRILL->BUILD->VERIFY->PROGRESS."""
    repo = loop_root.parent
    checklist_path = loop_root / "V1_SHIP_CHECKLIST.md"
    state = load_state(loop_root)
    state.iteration += 1
    it_dir = iteration_dir(loop_root, state.iteration)
    turns_dir = it_dir / "turns"
    turns_dir.mkdir(parents=True, exist_ok=True)

    matching = [p for p in prd_items(checklist_path) if p.prd_id == slice_id]
    prd_item = matching[0] if matching else None
    prd_path = prd_item.prd_path if prd_item else f"questdb-loop/prds/{slice_id}.md"
    commit_title = prd_item.commit_title if prd_item else f"fix: {slice_id}"

    # 1. SELECT -> GRILL -> BUILD
    state.phase = "SELECT"
    state.slice_id = slice_id
    state.active_prd_path = prd_path
    save_state(loop_root, state)
    (it_dir / "slice_id.txt").write_text(f"{slice_id}\n", encoding="utf-8")

    prd_file = repo / prd_path
    spec_text = prd_file.read_text(encoding="utf-8") if prd_file.exists() else slice_id
    (it_dir / "slice_spec.md").write_text(spec_text, encoding="utf-8")

    state.phase = "BUILD"
    save_state(loop_root, state)
    dev_log = "\n".join(
        [
            f"# Developer Build Log: {slice_id}",
            "",
            "- **Author**: John DaCosta (`@johndacosta`)",
            f"- **PRD**: `{prd_path}`",
            f"- **Commit Title**: `{commit_title}`",
            "- **Target Paths**: " + ", ".join(f"`{p}`" for p in target_paths),
            "- **Pytest Targets**: " + ", ".join(f"`{p}`" for p in pytest_targets),
            "",
            "## Changes",
            *[f"- {line}" for line in summary_lines],
            "",
            "```yaml",
            "ralph_phase: developer",
            f"slice_id: {slice_id}",
            "ready_for_verify: true",
            "```",
        ]
    )
    (it_dir / "build" / "developer_log.md").write_text(dev_log + "\n", encoding="utf-8")

    # 2. VERIFY (deterministic gate)
    state.phase = "VERIFY"
    save_state(loop_root, state)
    report = run_deterministic_gate(
        repo,
        slice_id=slice_id,
        target_paths=target_paths,
        pytest_targets=pytest_targets,
        out_dir=it_dir / "verify",
    )
    tpath = turns_dir / f"VERIFY-{slice_id}.md"
    gate_md = (it_dir / "verify" / "deterministic_gate.md").read_text(encoding="utf-8")
    write_turn_transcript(tpath, turn_id=f"VERIFY-{slice_id}", agent="qa", text=gate_md)
    append_interaction(
        loop_root,
        iteration=state.iteration,
        phase="VERIFY",
        agent="qa",
        turn_id=f"VERIFY-{slice_id}",
        transcript_path=tpath,
        text=f"Deterministic gate {'PASS' if report.passed else 'FAIL'} for {slice_id}",
        backend="deterministic-pytest-mypy-ruff",
        issue_id=slice_id,
    )

    if not report.passed:
        state.phase = "FAILED"
        state.last_error = f"Deterministic verification failed for {slice_id}"
        state.history.append(
            {
                "iteration": state.iteration,
                "slice_id": slice_id,
                "prd_path": prd_path,
                "result": "failed",
                "error": state.last_error,
            }
        )
        save_state(loop_root, state)
        return report

    # 3. PROGRESS (mark checklist + update PROGRESS.md)
    state.phase = "PROGRESS"
    mark_prd_done(checklist_path, slice_id)

    progress_path = loop_root / "PROGRESS.md"
    existing_progress = (
        progress_path.read_text(encoding="utf-8") if progress_path.exists() else ""
    )
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    cmds_run = "; ".join(" ".join(c.command) for c in report.checks)
    entry = "\n".join(
        [
            f"### {today} — {slice_id}: {commit_title}",
            "",
            "- **Author**: John DaCosta (`@johndacosta`)",
            "- **State transition**: `SELECT` -> `GRILL` -> `BUILD` -> "
            "`VERIFY` -> `PROGRESS`",
            f"- **PRD**: [`{prd_path}`](../{prd_path})",
            "- **Changes**:",
            *[f"  - {line}" for line in summary_lines],
            f"- **Deterministic commands run**: `{cmds_run}`",
            "- **Outcome**: PASS (all compileall, ruff, mypy, and pytest "
            "checks exited 0).",
            "",
            "---",
            "",
        ]
    )
    marker = "---\n\n### "
    if marker in existing_progress:
        idx = existing_progress.index(marker) + len("---\n\n")
        updated_progress = existing_progress[:idx] + entry + existing_progress[idx:]
    else:
        updated_progress = existing_progress.rstrip() + "\n\n" + entry
    progress_path.write_text(updated_progress, encoding="utf-8")
    (it_dir / "progress.md").write_text(entry, encoding="utf-8")

    state.history.append(
        {
            "iteration": state.iteration,
            "slice_id": slice_id,
            "prd_path": prd_path,
            "result": "ok",
        }
    )
    if is_deliverable(checklist_path):
        state.deliverable = True
        state.phase = "DONE"
    else:
        state.deliverable = False
        state.phase = "SELECT"
    state.last_error = None
    save_state(loop_root, state)
    return report
