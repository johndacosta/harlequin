"""Append-only interaction log: timestamps, agent, links to transcripts."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .contracts import parse_router_message


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def log_paths(loop_root: Path) -> tuple[Path, Path]:
    base = loop_root / "ralph" / "state"
    base.mkdir(parents=True, exist_ok=True)
    return base / "interactions.md", base / "interactions.jsonl"


def _ensure_md_header(md_path: Path) -> None:
    if md_path.exists() and md_path.stat().st_size > 0:
        return
    md_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text(
        "# Ralph interaction log\n\n"
        "Timestamped agent turns with links to transcript markdown. "
        "Full chat text lives in the linked files — not inlined here.\n\n",
        encoding="utf-8",
    )


def _summary_from_text(persona: str, text: str, turn_id: str) -> str:
    msg = parse_router_message(persona, text, turn_id)
    if msg.summary:
        return msg.summary.strip()[:240]
    # Fall back: first non-empty prose line, skip fences/code
    for line in (text or "").splitlines():
        s = line.strip()
        if not s or s.startswith("```") or s.startswith("#"):
            continue
        if s.startswith("ralph_phase:") or s.startswith("verdict:"):
            continue
        return s[:240]
    return "(no summary)"


def _rel(loop_root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(loop_root.resolve()).as_posix()
    except ValueError:
        return str(path)


def append_interaction(
    loop_root: Path,
    *,
    iteration: int | None,
    phase: str,
    agent: str,
    turn_id: str,
    transcript_path: Path,
    text: str = "",
    backend: str | None = None,
    issue_id: str | None = None,
    extra: dict[str, Any] | None = None,
) -> None:
    """
    Record one agent interaction.

    Stores metadata + link to the transcript markdown — not full code bodies.
    """
    md_path, jsonl_path = log_paths(loop_root)
    msg = parse_router_message(agent, text, turn_id) if text else None
    summary = _summary_from_text(agent, text, turn_id) if text else ""
    ts = _now()
    rel = _rel(loop_root, transcript_path)
    link = f"[{turn_id}]({rel})"

    record: dict[str, Any] = {
        "ts": ts,
        "iteration": iteration,
        "phase": phase,
        "agent": agent,
        "turn_id": turn_id,
        "transcript": rel,
        "verdict": msg.verdict if msg else None,
        "addressed_to": msg.addressed_to if msg else None,
        "opposition_to": msg.opposition_to if msg else None,
        "ready_to_pass": msg.ready_to_pass if msg else None,
        "summary": summary,
        "backend": backend,
        "issue_id": issue_id,
    }
    if extra:
        record.update(extra)

    # Markdown index (human-readable, no code)
    _ensure_md_header(md_path)
    line = (
        f"- **{ts}** · iter `{iteration}` · `{phase}` · **{agent}** · "
        f"verdict=`{record['verdict']}` · {link}"
    )
    if issue_id:
        line += f" · issue=`{issue_id}`"
    if record["addressed_to"]:
        line += f" · → `{record['addressed_to']}`"
    if summary:
        line += f"  \n  _{summary}_"
    with md_path.open("a", encoding="utf-8") as fh:
        fh.write(line + "\n")

    with jsonl_path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False) + "\n")


def write_turn_transcript(path: Path, *, turn_id: str, agent: str, text: str) -> None:
    """Write one turn's chat to its own markdown file (linked from the log)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    body = (
        f"# {turn_id}\n\n"
        f"- agent: `{agent}`\n"
        f"- written: `{_now()}`\n\n"
        f"## Chat\n\n{text.rstrip()}\n"
    )
    path.write_text(body, encoding="utf-8")


def mark_run_boundary(loop_root: Path, note: str) -> None:
    md_path, jsonl_path = log_paths(loop_root)
    _ensure_md_header(md_path)
    ts = _now()
    for path, content in (
        (
            md_path,
            f"\n---\n\n## Run boundary · {ts}\n\n{note}\n\n",
        ),
        (
            jsonl_path,
            json.dumps({"ts": ts, "event": "run_boundary", "note": note}) + "\n",
        ),
    ):
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as fh:
            fh.write(content)
