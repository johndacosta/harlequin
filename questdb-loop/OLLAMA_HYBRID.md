# Hybrid compute: Cursor orchestrator + local Ollama

Your machine profile (measured): **~31 GiB RAM**, **RTX 5070 12 GiB VRAM**, **28 threads**. That is enough for a hybrid Ralph loop: Cursor does judgment + tool use; Ollama does codegen and cheap YAML roles.

## Why hybrid

| Work | Best place | Why |
|------|------------|-----|
| Slice pick, product kill/reorder, security veto | **Cursor** | Needs ADR/PRD judgment, low tolerance for wrong YAML |
| Dialect truth vs QuestDB docs | **Cursor** | Easy to hallucinate meta columns locally |
| QA (pytest/ruff/docker) | **Cursor** | Needs shell/tools |
| Developer implementation draft | **Ollama coder** | Highest token volume; local is “free” |
| Apply patch + run tests | **Cursor** | Tool use / edit / verify |
| Budget / Horizon / Release drafts | **Ollama chat** | Structured YAML; cheap |

## Recommended models (from your install)

| Role | Model | Notes |
|------|-------|--------|
| **Default codegen** | `qwen2.5-coder:14b` (Q4, ~9 GB) | Best fit for 12 GiB VRAM; auto-selected when installed |
| **Fast codegen** | `qwen2.5-coder:7b` | Fallback if 14b missing |
| **Higher-quality codegen** | `qwen3-coder:30b` (`--ollama-quality`) | Better code; GPU+RAM; slower |
| **Cheap YAML chat** | `qwen3:8b` | Budget / Horizon / Release drafts |

Do **not** pull another 20 GB+ model unless you accept CPU offload. Prefer one strong coder resident in VRAM.

### Optional pull

```bash
ollama pull qwen2.5-coder:14b
export RALPH_OLLAMA_CODE=qwen2.5-coder:14b
```

## How to run

```bash
# Cursor logged in (`agent status`) + ollama serve
./questdb-loop/scripts/run-ralph.sh --hybrid --reset --max 2

# Prefer larger local coder for BUILD drafts
./questdb-loop/scripts/run-ralph.sh --hybrid --ollama-quality --max 2

# Ollama-only (no shell tools — not recommended for full ship)
./questdb-loop/scripts/run-ralph.sh --ollama --max 1
```

### Env knobs

| Var | Default | Meaning |
|-----|---------|---------|
| `RALPH_OLLAMA_CODE` | `qwen2.5-coder:7b` | Developer draft model |
| `RALPH_OLLAMA_CHAT` | `qwen3:8b` | Cheap persona model |
| `RALPH_OLLAMA_QUALITY` | unset | `1` → use `qwen3-coder:30b` for code |
| `RALPH_HYBRID_OLLAMA` | `developer,horizon_scout,budget_steward,release_steward` | Personas on Ollama |
| `RALPH_OLLAMA_CTX_CHARS` | `48000` | Context pack budget for codegen |
| `OLLAMA_HOST` | `http://127.0.0.1:11434` | API |

## Routing (default hybrid)

```
Architect / Product / Security / Dialect / QA / Tech Strategy  →  Cursor agent-cli
Developer  →  Ollama draft  →  Cursor apply+test
Budget / Horizon / Release  →  Ollama YAML/docs draft
```

## Cost / ROI intuition

- Live Cursor-only: every grill turn + every build line burns cloud tokens.
- Hybrid: grill/verify still Cursor (quality), but **BUILD drafts** (largest prompts) stay local.
- Keep issue routing (`--routing issue`) so you don’t round-robin expensive Cursor calls.

## Limits

- Local models still hallucinate QuestDB APIs — Dialect/Security stay on Cursor.
- Ollama cannot run your pytest; Cursor apply step must.
- First Ollama call after idle pays model load time (seconds–tens of seconds).
