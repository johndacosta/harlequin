#!/usr/bin/env bash
# Run the QuestDB Ralph autonomy loop until deliverable, STOP, or max iterations.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
LOOP_ROOT="$ROOT/questdb-loop"
cd "$ROOT"

BACKEND="${RALPH_BACKEND:-dry-run}"
MODEL="${RALPH_MODEL:-composer-2.5}"
MAX_ITERS="${RALPH_MAX_ITERATIONS:-40}"
ROUTING="${RALPH_ROUTING:-issue}"
EXTRA_ARGS=()

usage() {
  cat <<'EOF'
Usage: questdb-loop/scripts/run-ralph.sh [options]

Options:
  --live              Use Cursor agent CLI (--backend agent-cli)
  --hybrid            Cursor orchestrator + local Ollama codegen (recommended)
  --live-sdk          Use Cursor SDK (--backend cursor); needs CURSOR_API_KEY
  --ollama            Ollama-only (no Cursor tools; limited)
  --dry-run           No API calls (default)
  --once              Single iteration
  --reset             Reset loop state
  --status            Print status only
  --max N             Max iterations (default 40)
  --model ID          Cursor model id (default composer-2.5)
  --routing MODE      issue (default, pairwise) | round-robin
  --ollama-quality    Use larger local coder (qwen3-coder:30b)
  --stop              Create STOP file and exit
  -h, --help          Show help

Env:
  CURSOR_API_KEY      Required for --live-sdk
  RALPH_BACKEND       dry-run|agent-cli|cursor|ollama|hybrid
  RALPH_MODEL         Cursor model id
  RALPH_OLLAMA_CODE   default qwen2.5-coder:7b (or qwen3-coder:30b)
  RALPH_OLLAMA_CHAT   default qwen3:8b
  RALPH_OLLAMA_QUALITY 1 to prefer 30b coder
  RALPH_HYBRID_OLLAMA comma personas forced onto Ollama
  OLLAMA_HOST         default http://127.0.0.1:11434
  RALPH_MAX_ITERATIONS
  RALPH_ROUTING       issue|round-robin
  RALPH_AGENT_TIMEOUT seconds per Cursor agent call (default 600)
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --live) BACKEND=agent-cli; shift ;;
    --hybrid) BACKEND=hybrid; shift ;;
    --live-sdk) BACKEND=cursor; shift ;;
    --ollama) BACKEND=ollama; shift ;;
    --dry-run) BACKEND=dry-run; shift ;;
    --once) EXTRA_ARGS+=(--once); shift ;;
    --reset) EXTRA_ARGS+=(--reset); shift ;;
    --status) EXTRA_ARGS+=(--status); shift ;;
    --max) MAX_ITERS="$2"; shift 2 ;;
    --model) MODEL="$2"; shift 2 ;;
    --routing) ROUTING="$2"; shift 2 ;;
    --ollama-quality) export RALPH_OLLAMA_QUALITY=1; shift ;;
    --stop)
      mkdir -p "$LOOP_ROOT/ralph/state"
      touch "$LOOP_ROOT/ralph/state/STOP"
      echo "Wrote $LOOP_ROOT/ralph/state/STOP"
      exit 0
      ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1"; usage; exit 1 ;;
  esac
done

export PYTHONPATH="$LOOP_ROOT${PYTHONPATH:+:$PYTHONPATH}"
export PYTHONUNBUFFERED=1

PYTHON_BIN="${PYTHON_BIN:-python3}"
if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  PYTHON_BIN=python
fi

if [[ "$BACKEND" == "cursor" ]]; then
  if [[ -z "${CURSOR_API_KEY:-}" ]]; then
    echo "ERROR: CURSOR_API_KEY required for --live-sdk" >&2
    echo "Tip: use --live (agent-cli) if \`agent status\` shows logged in." >&2
    exit 1
  fi
  if ! "$PYTHON_BIN" -c "import cursor_sdk" 2>/dev/null; then
    echo "Installing cursor-sdk into current environment..."
    pip install -q cursor-sdk || uv pip install cursor-sdk
  fi
fi

if [[ "$BACKEND" == "agent-cli" || "$BACKEND" == "hybrid" ]]; then
  if ! command -v agent >/dev/null 2>&1; then
    echo "ERROR: Cursor \`agent\` CLI not on PATH" >&2
    exit 1
  fi
fi

if [[ "$BACKEND" == "ollama" || "$BACKEND" == "hybrid" ]]; then
  if ! curl -sf "${OLLAMA_HOST:-http://127.0.0.1:11434}/api/tags" >/dev/null; then
    echo "ERROR: Ollama not reachable at ${OLLAMA_HOST:-http://127.0.0.1:11434}" >&2
    echo "Start it with: ollama serve" >&2
    exit 1
  fi
fi

exec "$PYTHON_BIN" -m ralph \
  --backend "$BACKEND" \
  --model "$MODEL" \
  --max-iterations "$MAX_ITERS" \
  --routing "$ROUTING" \
  "${EXTRA_ARGS[@]}"
