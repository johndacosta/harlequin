"""Unit tests for Ralph state machine modules (checklist, contracts, router, state)."""

from __future__ import annotations

import sys
from pathlib import Path

# Insert questdb-loop into sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "questdb-loop"))

from ralph.checklist import (  # type: ignore
    is_deliverable,
    mark_prd_done,
    next_prd_slice,
    prd_items,
)
from ralph.contracts import (  # type: ignore
    _flag,
    _parse_open_issues,
    extract_yaml_block,
)
from ralph.router import OpenIssue, run_issue_board  # type: ignore
from ralph.state import (  # type: ignore
    load_state,
    save_state,
)


def test_checklist_functions(tmp_path: Path) -> None:
    checklist_file = tmp_path / "V1_SHIP_CHECKLIST.md"
    checklist_file.write_text(
        """## Must - Performance
- [ ] **PRD-01** (`P0` | `path/to/prd1.md`): First prd slice (`commit message 1`)
- [ ] **PRD-02** (`P1` | `path/to/prd2.md`): Second prd slice (`commit message 2`)

## Should
- [ ] Optional item
""",
        encoding="utf-8",
    )

    items = prd_items(checklist_file)
    assert len(items) == 2
    assert items[0].prd_id == "PRD-01"
    assert items[0].severity == "P0"
    assert items[0].commit_title == "commit message 1"
    assert not items[0].done

    next_item = next_prd_slice(checklist_file)
    assert next_item is not None
    assert next_item.prd_id == "PRD-01"

    assert not is_deliverable(checklist_file)

    success = mark_prd_done(checklist_file, "PRD-01")
    assert success

    updated_items = prd_items(checklist_file)
    assert updated_items[0].done

    next_item_2 = next_prd_slice(checklist_file)
    assert next_item_2 is not None
    assert next_item_2.prd_id == "PRD-02"

    mark_prd_done(checklist_file, "PRD-02")
    assert is_deliverable(checklist_file)


def test_contracts_parsing() -> None:
    text = """
Some introductory text.
```yaml
ready_for_build: false
```
Middle text with an example fence:
```yaml
example: true
```
Last YAML block:
```yaml
ready_for_build: true  # inline comment
```
"""
    block = extract_yaml_block(text)
    assert "ready_for_build: true" in block

    flag_val = _flag(block, "ready_for_build", "false")
    assert flag_val.lower() == "true"

    issues_block = """
open_issues:
  - {id: i1, topic: "Double quoted topic value", needs_agents: [security]}
  - {id: i2, topic: 'Single quoted topic value', needs_agents: [qa]}
"""
    issues = _parse_open_issues(issues_block, "architect")
    assert len(issues) == 2
    assert issues[0].id == "i1"
    assert issues[0].topic == "Double quoted topic value"
    assert issues[1].id == "i2"
    assert issues[1].topic == "Single quoted topic value"


def test_router_issue_board() -> None:
    def mock_run(persona: str, prompt: str) -> str:
        if persona == "security":
            return """
```yaml
verdict: accept
resolved_issues: [sec_issue]
ready_to_pass: true
summary: security reviewed and resolved
```
"""
        elif persona == "qa":
            return """
```yaml
verdict: accept
resolved_issues: [sec_issue]
ready_to_pass: true
summary: qa reviewed and resolved
```
"""
        else:
            return """
```yaml
verdict: pass_turn
ready_to_pass: false
summary: passing turn
```
"""

    seed = [
        OpenIssue(
            id="sec_issue",
            topic="injection security flaw",
            needs_agents=["security", "qa"],
            blocking=True,
            raised_by="architect",
        )
    ]

    board, output = run_issue_board(
        run=mock_run,
        phase="GRILL",
        shared_context="Context for test",
        seed_issues=seed,
        phase_cap=5,
    )
    assert "sec_issue" not in board.issues or board.force_closed


def test_state_persistence(tmp_path: Path) -> None:
    loop_root = tmp_path
    checklist_file = loop_root / "V1_SHIP_CHECKLIST.md"
    checklist_file.write_text(
        """## Must - Bug Fixes
- [ ] **PRD-10** (`P0` | `path/to/bug.md`): Bug fix prd (`commit 10`)
""",
        encoding="utf-8",
    )

    state = load_state(loop_root)
    assert state.phase == "IDLE"
    assert len(state.prd_queue) == 1
    assert state.slice_id == "PRD-10"

    state.phase = "SELECT"
    save_state(loop_root, state)

    state_loaded = load_state(loop_root)
    assert state_loaded.phase == "SELECT"
    assert state_loaded.slice_id == "PRD-10"
