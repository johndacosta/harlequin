"""Persisted Ralph loop state (JSON files are gitignored in this repo)."""

from __future__ import annotations

import json
import os
import tempfile
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from .checklist import prd_items

Phase = Literal[
    "IDLE",
    "SELECT",
    "GRILL",
    "BUILD",
    "VERIFY",
    "PROGRESS",
    "DONE",
    "FAILED",
]


def build_prd_queue(root: Path) -> list[dict[str, Any]]:
    checklist_path = root / "V1_SHIP_CHECKLIST.md"
    if not checklist_path.exists():
        return []
    return [
        {
            "id": p.prd_id,
            "category": p.category,
            "severity": p.severity,
            "path": p.prd_path,
            "summary": p.summary,
            "commit_title": p.commit_title,
            "status": "done" if p.done else "pending",
        }
        for p in prd_items(checklist_path)
    ]


@dataclass
class LoopState:
    phase: Phase = "IDLE"
    iteration: int = 0
    max_iterations: int = 50
    slice_id: str | None = None
    active_prd_path: str | None = None
    last_error: str | None = None
    deliverable: bool = False
    updated_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    history: list[dict[str, Any]] = field(default_factory=list)
    prd_queue: list[dict[str, Any]] = field(default_factory=list)

    def touch(self) -> None:
        self.updated_at = datetime.now(timezone.utc).isoformat()


def state_path(root: Path) -> Path:
    return root / "ralph" / "state" / "loop_state.json"


def sync_prd_queue(root: Path, state: LoopState) -> None:
    fresh = build_prd_queue(root)
    if fresh:
        state.prd_queue = fresh
        pending = [item for item in fresh if item["status"] == "pending"]
        if pending:
            state.deliverable = False
            if state.phase == "DONE":
                state.phase = "SELECT"
            if not state.active_prd_path or not any(
                item["path"] == state.active_prd_path and item["status"] == "pending"
                for item in fresh
            ):
                state.slice_id = pending[0]["id"]
                state.active_prd_path = pending[0]["path"]


def load_state(root: Path) -> LoopState:
    path = state_path(root)
    if not path.exists():
        st = LoopState()
        sync_prd_queue(root, st)
        return st
    data = json.loads(path.read_text(encoding="utf-8"))
    st = LoopState(
        phase=data.get("phase", "IDLE"),
        iteration=int(data.get("iteration", 0)),
        max_iterations=int(data.get("max_iterations", 50)),
        slice_id=data.get("slice_id"),
        active_prd_path=data.get("active_prd_path"),
        last_error=data.get("last_error"),
        deliverable=bool(data.get("deliverable", False)),
        updated_at=data.get("updated_at") or datetime.now(timezone.utc).isoformat(),
        history=list(data.get("history") or []),
        prd_queue=list(data.get("prd_queue") or []),
    )
    sync_prd_queue(root, st)
    return st


def save_state(root: Path, state: LoopState) -> None:
    path = state_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    sync_prd_queue(root, state)
    state.touch()
    payload = json.dumps(asdict(state), indent=2) + "\n"
    fd, tmp_name = tempfile.mkstemp(
        dir=str(path.parent), prefix=".loop_state.", suffix=".tmp"
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(payload)
        os.replace(tmp_name, path)
    except BaseException:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)
        raise


def iteration_dir(root: Path, iteration: int) -> Path:
    d = root / "ralph" / "state" / "iterations" / f"{iteration:03d}"
    d.mkdir(parents=True, exist_ok=True)
    (d / "grill").mkdir(exist_ok=True)
    (d / "build").mkdir(exist_ok=True)
    (d / "verify").mkdir(exist_ok=True)
    return d


def reset_runtime(root: Path, max_iterations: int = 50) -> LoopState:
    """Clear loop state and prior iteration artifacts."""
    import shutil

    from .interaction_log import mark_run_boundary

    iterations = root / "ralph" / "state" / "iterations"
    if iterations.exists():
        shutil.rmtree(iterations)
    iterations.mkdir(parents=True, exist_ok=True)
    stop = root / "ralph" / "state" / "STOP"
    if stop.exists():
        stop.unlink()
    mark_run_boundary(
        root, "reset_runtime — cleared iterations; interaction log continues"
    )
    state = LoopState(max_iterations=max_iterations)
    save_state(root, state)
    return state
