#!/usr/bin/env bash
# Exit 0 if V1 Must checklist is complete (deliverable).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
export PYTHONPATH="$ROOT/questdb-loop${PYTHONPATH:+:$PYTHONPATH}"
cd "$ROOT"
PYTHON_BIN="${PYTHON_BIN:-python3}"
command -v "$PYTHON_BIN" >/dev/null 2>&1 || PYTHON_BIN=python
"$PYTHON_BIN" - <<'PY'
from pathlib import Path
from ralph.checklist import is_deliverable, summary
from ralph.state import load_state

loop = Path("questdb-loop")
s = summary(loop / "V1_SHIP_CHECKLIST.md")
print(s)
state = load_state(loop)
print("loop_phase:", state.phase, "iteration:", state.iteration)
raise SystemExit(0 if is_deliverable(loop / "V1_SHIP_CHECKLIST.md") else 1)
PY
