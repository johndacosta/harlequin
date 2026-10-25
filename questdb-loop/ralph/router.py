"""Issue-thread router: pairwise debate, opposition, escalate, ROI caps."""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Callable

from .contracts import (
    ROUTABLE,
    OpenIssue,
    RouterMessage,
    hint_agents_for_text,
    parse_router_message,
)
from .interaction_log import append_interaction, write_turn_transcript

RunFn = Callable[[str, str], str]  # (persona, prompt) -> response text


@dataclass
class Turn:
    turn_id: str
    persona: str
    text: str
    msg: RouterMessage


@dataclass
class Thread:
    issue_id: str
    participants: list[str]
    turns: list[Turn] = field(default_factory=list)
    max_turns: int = 4
    pending_opposition_from: str | None = None  # who must rebut

    @property
    def full(self) -> bool:
        return len(self.turns) >= self.max_turns


@dataclass
class Board:
    issues: dict[str, OpenIssue] = field(default_factory=dict)
    threads: dict[str, Thread] = field(default_factory=dict)
    turns: list[Turn] = field(default_factory=list)
    force_closed: list[OpenIssue] = field(default_factory=list)
    call_count: int = 0
    phase_cap: int = 12
    log_lines: list[str] = field(default_factory=list)

    def blocking_open(self) -> list[OpenIssue]:
        return [i for i in self.issues.values() if i.blocking]

    def log(self, line: str) -> None:
        self.log_lines.append(line)

    def _remaining_needs_agents(self, issue_id: str) -> list[str]:
        issue = self.issues.get(issue_id)
        if issue is None:
            return []
        thread = self.threads.get(issue_id)
        spoken = {t.persona for t in thread.turns} if thread else set()
        return [
            a
            for a in issue.needs_agents
            if a in ROUTABLE and a != issue.raised_by and a not in spoken
        ]

    def apply(self, msg: RouterMessage) -> None:
        for iid in msg.resolved_issues:
            if iid in self.issues:
                rem = self._remaining_needs_agents(iid)
                if rem and iid in self.threads:
                    nxt = rem[0]
                    th = self.threads[iid]
                    if nxt not in th.participants:
                        th.participants.append(nxt)
                    th.pending_opposition_from = nxt
                    th.max_turns = max(th.max_turns, len(th.turns) + 2)
                    self.log(f"rotated {iid} to next required reviewer {nxt}")
                else:
                    self.issues[iid].blocking = False
                    self.log(f"resolved {iid} by {msg.persona}")
                    del self.issues[iid]
        for issue in msg.open_issues:
            if issue.id not in self.issues and issue.blocking:
                # Horizon never blocks — belt and suspenders
                if "mcp" in issue.topic.lower() or "horizon" in issue.topic.lower():
                    issue.blocking = False
                if issue.blocking:
                    self.issues[issue.id] = issue
                    self.log(f"opened {issue.id} needs={issue.needs_agents}")
        if msg.needs_agents and self.blocking_open():
            # attach escalation agents to current top issue
            top = self.blocking_open()[0]
            for a in msg.needs_agents:
                if a not in top.needs_agents:
                    top.needs_agents.append(a)


def _partner(thread: Thread, speaker: str) -> str | None:
    others = [p for p in thread.participants if p != speaker]
    if not others:
        return None
    spoken = {t.persona for t in thread.turns}
    for p in others:
        if p not in spoken:
            return p
    return others[0]


def _pick_speaker(thread: Thread, last: RouterMessage | None) -> str:
    if last and last.addressed_to and last.addressed_to in thread.participants:
        return last.addressed_to
    if thread.pending_opposition_from:
        return thread.pending_opposition_from
    if not thread.turns:
        # Reviewer speaks first (proposal already exists outside the thread).
        return (
            thread.participants[1]
            if len(thread.participants) > 1
            else thread.participants[0]
        )
    # Alternate
    last_p = thread.turns[-1].persona
    partner = _partner(thread, last_p)
    return partner or thread.participants[0]


def _ensure_thread(
    board: Board,
    issue: OpenIssue,
    default_raiser: str,
    max_turns_per_thread: int = 4,
) -> Thread:
    if issue.id in board.threads:
        return board.threads[issue.id]
    raiser = issue.raised_by if issue.raised_by in ROUTABLE else default_raiser
    needs = [a for a in issue.needs_agents if a in ROUTABLE and a != raiser]
    if not needs:
        needs = hint_agents_for_text(issue.topic)
        needs = [a for a in needs if a != raiser] or ["product_lead"]
    partner = needs[0]
    participants = [raiser, partner]
    thread = Thread(
        issue_id=issue.id,
        participants=participants,
        max_turns=max_turns_per_thread,
    )
    board.threads[issue.id] = thread
    board.log(f"thread {issue.id}: {participants}")
    return thread


def _transcript(thread: Thread) -> str:
    parts = []
    for t in thread.turns:
        parts.append(
            f"### {t.turn_id} ({t.persona})\n{t.text}\n"
            f"(verdict={t.msg.verdict} addressed_to={t.msg.addressed_to} "
            f"opposition_to={t.msg.opposition_to})\n"
        )
    return "\n".join(parts)


def _thread_prompt(
    *,
    persona: str,
    issue: OpenIssue,
    thread: Thread,
    phase: str,
    shared_context: str,
    extra: str = "",
) -> str:
    return f"""
PHASE={phase} — ISSUE THREAD (pairwise). Only resolve this issue.

## Current issue
- id: {issue.id}
- topic: {issue.topic}
- needs_agents: {issue.needs_agents}
- blocking: {issue.blocking}
- participants: {thread.participants}

## Thread transcript
{_transcript(thread) or "(no turns yet — open the debate or answer the raiser)"}

## Your role this turn
You are **{persona}**. If the last message addressed or opposed you, respond to that.
Set addressed_to to your pair partner when you need a rebuttal/answer.
When settled: resolved_issues: [{issue.id}] and ready_to_pass: true.

{shared_context}

{extra}
""".strip()


def run_issue_board(
    *,
    run: RunFn,
    phase: str,
    shared_context: str,
    seed_issues: list[OpenIssue],
    synthesizer: str = "architect",
    phase_cap: int = 12,
    max_turns_per_thread: int = 4,
    synthesize_prompt: str | None = None,
    loop_root: Path | None = None,
    iteration: int | None = None,
    turns_dir: Path | None = None,
    backend_name: str | None = None,
) -> tuple[Board, str | None]:
    """
    Run issue threads to completion (or cap).
    Returns (board, synthesizer_output_or_None).
    """
    board = Board(phase_cap=phase_cap)
    for issue in seed_issues:
        board.issues[issue.id] = issue

    while board.blocking_open() and board.call_count < board.phase_cap:
        issue = board.blocking_open()[0]
        thread = _ensure_thread(
            board, issue, synthesizer, max_turns_per_thread=max_turns_per_thread
        )

        if thread.full:
            # One escalation seat if available
            extra = [
                a
                for a in issue.needs_agents
                if a not in thread.participants and a in ROUTABLE
            ]
            if extra and len(thread.participants) < 3:
                thread.participants.append(extra[0])
                thread.pending_opposition_from = extra[0]
                thread.max_turns += 2
                board.log(f"escalate {issue.id} +{extra[0]}")
            else:
                # Force-close as amend — synthesizer must shrink
                board.log(f"force-close {issue.id} at max turns")
                board.force_closed.append(issue)
                del board.issues[issue.id]
                continue

        last_msg = thread.turns[-1].msg if thread.turns else None
        speaker = _pick_speaker(thread, last_msg)
        board.call_count += 1
        turn_id = f"{phase}-{board.call_count:02d}-{speaker}"
        prompt = _thread_prompt(
            persona=speaker,
            issue=issue,
            thread=thread,
            phase=phase,
            shared_context=shared_context,
        )
        text = run(speaker, prompt)
        msg = parse_router_message(speaker, text, turn_id)
        turn = Turn(turn_id=turn_id, persona=speaker, text=text, msg=msg)
        thread.turns.append(turn)
        board.turns.append(turn)
        board.apply(msg)

        if turns_dir is not None and loop_root is not None:
            tpath = turns_dir / f"{turn_id}.md"
            write_turn_transcript(tpath, turn_id=turn_id, agent=speaker, text=text)
            append_interaction(
                loop_root,
                iteration=iteration,
                phase=phase,
                agent=speaker,
                turn_id=turn_id,
                transcript_path=tpath,
                text=text,
                backend=backend_name,
                issue_id=issue.id,
            )

        if msg.opposition_to or msg.verdict in ("reject", "amend", "question"):
            partner = _partner(thread, speaker)
            if partner and not msg.ready_to_pass:
                thread.pending_opposition_from = msg.addressed_to or partner
            else:
                thread.pending_opposition_from = None
        elif msg.ready_to_pass or msg.verdict == "accept":
            thread.pending_opposition_from = None
            if issue.id in msg.resolved_issues or msg.verdict == "accept":
                if issue.id in board.issues and msg.verdict == "accept":
                    rem = board._remaining_needs_agents(issue.id)
                    if rem:
                        nxt = rem[0]
                        if nxt not in thread.participants:
                            thread.participants.append(nxt)
                        thread.pending_opposition_from = nxt
                        thread.max_turns = max(thread.max_turns, len(thread.turns) + 2)
                        board.log(f"rotated {issue.id} to next required reviewer {nxt}")
                    elif msg.ready_to_pass and issue.id in board.issues:
                        del board.issues[issue.id]
                        board.log(f"accept-close {issue.id}")

        if (
            msg.ready_to_pass
            and issue.id in msg.resolved_issues
            and issue.id not in board.issues
        ):
            continue

    synth_out = None
    if synthesize_prompt:
        board.call_count += 1
        synth_out = run(
            synthesizer,
            synthesize_prompt
            + "\n\n## Board state\n"
            + json.dumps(
                {
                    "remaining_blocking": [asdict(i) for i in board.blocking_open()],
                    "force_closed": [asdict(i) for i in board.force_closed],
                    "log": board.log_lines,
                    "calls": board.call_count,
                    "turn_ids": [t.turn_id for t in board.turns],
                },
                indent=2,
            )
            + "\nSynthesize slice_spec. If unresolved blocking issues remain, "
            "shrink the slice. Set ready_for_build: true only if safe.\n",
        )
        if synth_out is not None and turns_dir is not None and loop_root is not None:
            turn_id = f"{phase}-{board.call_count:02d}-{synthesizer}-synth"
            tpath = turns_dir / f"{turn_id}.md"
            write_turn_transcript(
                tpath, turn_id=turn_id, agent=synthesizer, text=synth_out
            )
            append_interaction(
                loop_root,
                iteration=iteration,
                phase=phase,
                agent=synthesizer,
                turn_id=turn_id,
                transcript_path=tpath,
                text=text,
                backend=backend_name,
                issue_id="synthesis",
            )
    return board, synth_out


def dump_board(board: Board, path: Path, *, turns_dir: Path | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "call_count": board.call_count,
        "log": board.log_lines,
        "open_blocking": [asdict(i) for i in board.blocking_open()],
        "force_closed": [asdict(i) for i in board.force_closed],
        "threads": {
            tid: {
                "participants": th.participants,
                "turns": [
                    {
                        "turn_id": t.turn_id,
                        "persona": t.persona,
                        "verdict": t.msg.verdict,
                        "addressed_to": t.msg.addressed_to,
                        "opposition_to": t.msg.opposition_to,
                        "summary": t.msg.summary,
                    }
                    for t in th.turns
                ],
            }
            for tid, th in board.threads.items()
        },
    }
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    # Human index: summaries + links to per-turn transcripts (not full chat/code)
    log_path = path.with_suffix(".md")
    lines = [
        "# Issue board log",
        "",
        "Full agent chat lives in linked turn markdown files.",
        "",
    ]
    for t in board.turns:
        if turns_dir is not None:
            tpath = turns_dir / f"{t.turn_id}.md"
            rel = Path(os.path.relpath(tpath, start=log_path.parent)).as_posix()
            lines.append(
                f"- **{t.turn_id}** · `{t.persona}` · verdict=`{t.msg.verdict}` · "
                f"[{t.turn_id}]({rel})"
            )
            if t.msg.summary:
                lines.append(f"  _{t.msg.summary}_")
        else:
            lines.append(f"## {t.turn_id}")
            lines.append(t.text)
            lines.append("")
    log_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
