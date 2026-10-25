"""Parse V1_SHIP_CHECKLIST.md for Must progress, PRD queue, and delivery readiness."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

MUST_HEADER = re.compile(r"^## Must", re.MULTILINE)
SECTION_HEADER = re.compile(r"^## ", re.MULTILINE)
CHECKBOX = re.compile(r"^- \[([ xX])\] (.+)$", re.MULTILINE)
PRD_ITEM_RE = re.compile(
    r"\*\*(PRD-\d+)\*\*\s*\(\s*`?(P[012])`?\s*\|\s*`([^`]+)`\s*\):\s*(.+?)(?:\s*\(`([^`]+)`\))?$"
)


@dataclass(frozen=True)
class ChecklistItem:
    text: str
    done: bool
    section: str


@dataclass(frozen=True)
class PrdSliceItem:
    prd_id: str
    severity: str
    prd_path: str
    category: str
    summary: str
    commit_title: str
    done: bool
    section: str


def _sections(md: str) -> list[tuple[str, str]]:
    """Return (heading, body) for each ## section."""
    out: list[tuple[str, str]] = []
    matches = list(re.finditer(r"^## (.+)$", md, re.MULTILINE))
    for i, m in enumerate(matches):
        title = m.group(1).strip()
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(md)
        out.append((title, md[start:end]))
    return out


def parse_checklist(path: Path) -> list[ChecklistItem]:
    text = path.read_text(encoding="utf-8")
    items: list[ChecklistItem] = []
    for title, body in _sections(text):
        for m in CHECKBOX.finditer(body):
            items.append(
                ChecklistItem(
                    text=m.group(2).strip(),
                    done=m.group(1).lower() == "x",
                    section=title,
                )
            )
    return items


def must_items(path: Path) -> list[ChecklistItem]:
    return [i for i in parse_checklist(path) if i.section.lower().startswith("must")]


def must_remaining(path: Path) -> list[ChecklistItem]:
    return [i for i in must_items(path) if not i.done]


def prd_items(path: Path) -> list[PrdSliceItem]:
    """Return all structured PRD slice items declared in Must sections."""
    out: list[PrdSliceItem] = []
    for item in must_items(path):
        m = PRD_ITEM_RE.search(item.text)
        if not m:
            continue
        prd_id, severity, prd_path, desc, commit_title = m.groups()
        category = "Performance" if "performance" in item.section.lower() else "Bug"
        out.append(
            PrdSliceItem(
                prd_id=prd_id,
                severity=severity,
                prd_path=prd_path,
                category=category,
                summary=desc.strip(),
                commit_title=(commit_title or "").strip(),
                done=item.done,
                section=item.section,
            )
        )
    return out


def next_prd_slice(path: Path) -> PrdSliceItem | None:
    """Return the next unchecked PRD slice in checklist order."""
    for p in prd_items(path):
        if not p.done:
            return p
    return None


def mark_prd_done(path: Path, prd_id: str) -> bool:
    """Mark one PRD checkbox as [x] in V1_SHIP_CHECKLIST.md."""
    text = path.read_text(encoding="utf-8")
    pattern = re.compile(rf"^- \[ \] (\*\*{re.escape(prd_id)}\*\* .+)$", re.MULTILINE)
    new_text, count = pattern.subn(r"- [x] \1", text, count=1)
    if count > 0:
        path.write_text(new_text, encoding="utf-8")
        return True
    return False


def is_deliverable(path: Path) -> bool:
    must = must_items(path)
    if not must:
        return False
    remaining = [i for i in must if not i.done]
    return len(remaining) == 0


def summary(path: Path) -> dict[str, int | bool]:
    must = must_items(path)
    left = [i for i in must if not i.done]
    prds = prd_items(path)
    prds_left = [p for p in prds if not p.done]
    return {
        "must_total": len(must),
        "must_done": len(must) - len(left),
        "must_remaining": len(left),
        "prd_total": len(prds),
        "prd_done": len(prds) - len(prds_left),
        "prd_remaining": len(prds_left),
        "deliverable": bool(must) and len(left) == 0,
    }
