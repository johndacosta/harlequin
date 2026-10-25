# PRD-26: Harden Ralph State Machine `phase_verify` Verdict Gate, Multi-Agent Issue Board Escalation, and YAML Contract Parsing

- **Slice ID**: `PRD-26`
- **Category**: Bug Fix (`Bug`)
- **Priority / Severity**: `P1` (High — State Machine Verification Bypass on Timeout & Broken Escalation Routing)
- **Target Branch / PR Scope**: Single atomic commit / PR (`fix(ralph): harden phase_verify verdict gate, issue board escalation, and atomic state persistence`)

## 1. Problem Statement & Root Cause
Auditing `questdb-loop/ralph/` uncovered five state-machine and multi-agent routing defects:

1. **`phase_verify` and `run_issue_board` Allow Timed-Out/Failed `VERIFY` Phases to Pass (`loop.py:547-561`, `router.py:200-214`, `backend.py:174-200`)**:
   - When `AgentCliBackend` or `OllamaBackend` times out or exits non-zero, it returns a fallback YAML block with `verdict: pass_turn`.
   - In `run_issue_board`, when a thread hits `max_turns` without resolution, `router.py:213` force-closes the issue by deleting it from `board.issues` (`del board.issues[issue.id]`), making `board.blocking_open()` return `[]`.
   - Then `loop.py:556` checks `if verdict == "fail" or board.blocking_open():` with default `verdict = yaml_flag(block, "verdict", "pass")`. Because `"pass_turn" != "fail"` and `board.blocking_open()` is empty, a timed-out or unresolved `VERIFY` phase passes and advances to `PROGRESS`!
2. **Escalated 3rd Participant in `run_issue_board` Is Never Selected to Speak (`router.py:82-103, 198-215`)**:
   When a 2-agent thread `[p0, p1]` reaches `max_turns`, `router.py` appends `p2` (`extra[0]`), but `_partner()` always returns `others[0]` (`p1` for `p0`, and `p0` for `p1`), never `p2`! Moreover, line 198 resets `thread.max_turns = max_turns_per_thread` on every loop iteration, immediately force-closing the thread on the next iteration.
3. **First Reviewer `accept` Closes Multi-Agent Issues Before Remaining `needs_agents` Speak (`router.py:59-80, 255-263`)**:
   When an issue has `needs_agents=["security", "dialect_specialist", "qa"]`, `needs[0]` accepting on turn 1 immediately deletes `issue.id` from `board.issues` before `needs[1:]` participate.
4. **Dead Code in `phase_grill` Soft-Heal (`loop.py:385`), Missing `ready_for_verify` Check in `phase_build` (`loop.py:461-466`), and `HybridBackend` Double-YAML Extraction (`contracts.py:72-74`)**:
   - `"ready for BUILD" in synth.lower()` compares uppercase `"BUILD"` against `.lower()` (always `False`).
   - `contracts.extract_yaml_block` uses `YAML_FENCE.search(text)` (matching the first YAML block instead of the final YAML block `YAML_FENCE.findall(text)[-1]`).
5. **Non-Atomic `save_state` (`state.py:61-65`) and Narrow `context_pack.py` Globs (`context_pack.py:8-11, 30-32`)**:
   - `save_state` writes directly to `loop_state.json` instead of atomic temp-file + `os.replace`.
   - `context_pack.py` only matches `src/harlequin_questdb/` instead of `src/harlequin*/`, `questdb-loop/prds/`, and `tests/`.

## 2. Goals & Non-Goals
### Goals
- Track `force_closed` issues on `Board` in `router.py`, rotate through all `needs_agents` before closing an issue, and select the escalated 3rd participant (`thread.pending_opposition_from = extra[0]`, `thread.max_turns += 2`).
- Require explicit `verdict == "pass"` and `not board.blocking_open() and not board.force_closed` in `phase_verify` (`loop.py`).
- Fix `"ready for build" in synth.lower()`, select the last YAML fence in `contracts.extract_yaml_block`, strip inline `#` comments in YAML flags, and use atomic file replacement in `save_state()`.
- Expand `context_pack.py` to pack `src/harlequin/`, `src/harlequin_duckdb/`, `src/harlequin_sqlite/`, `src/harlequin_questdb/`, and `questdb-loop/prds/`.

### Non-Goals
- Changing external CLI binary invocations.

## 3. Technical Design & Affected Files
- `questdb-loop/ralph/loop.py`
- `questdb-loop/ralph/router.py`
- `questdb-loop/ralph/contracts.py`
- `questdb-loop/ralph/state.py`
- `questdb-loop/ralph/checklist.py`
- `questdb-loop/ralph/context_pack.py`
- `questdb-loop/ralph/prompts.py`

## 4. Verification & Acceptance Criteria
```bash
./questdb-loop/scripts/run-ralph.sh --status
./questdb-loop/scripts/run-ralph.sh --backend dry-run --once
uv run ruff check questdb-loop/ralph/
```
