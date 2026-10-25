#!/usr/bin/env python3
"""Analyze Antigravity transcript logs to compute empirical token ROI across agents.

Attributed to: John DaCosta (@johndacosta)
Written in ASD-STE100 (Simplified Technical English).
"""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# Relative cost weights per 1M tokens (normalized to flash_lite = 1.0x base)
MODEL_WEIGHTS: dict[str, dict[str, float]] = {
    "flash_lite": {"input": 0.10, "cache": 0.025, "output": 0.40},
    "flash": {"input": 0.30, "cache": 0.075, "output": 1.20},
    "pro": {"input": 1.25, "cache": 0.3125, "output": 5.00},
    "inherit": {"input": 2.00, "cache": 0.50, "output": 8.00},
}


def _parse_iso(ts: str) -> datetime | None:
    if not ts:
        return None
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except ValueError:
        return None


def analyze_transcript(
    transcript_path: Path,
    model_tier: str = "inherit",
    slices_completed: int = 1,
) -> dict[str, Any]:
    if not transcript_path.exists():
        return {"error": f"Transcript not found: {transcript_path}"}

    input_tokens = 0
    cache_read_tokens = 0
    output_tokens = 0
    steps = 0
    planner_turns = 0
    first_ts: datetime | None = None
    last_ts: datetime | None = None

    for line in transcript_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        steps += 1
        ts = _parse_iso(str(record.get("created_at", "")))
        if ts is not None:
            if first_ts is None or ts < first_ts:
                first_ts = ts
            if last_ts is None or ts > last_ts:
                last_ts = ts
        usage = record.get("usage", {})
        in_tok = int(record.get("input_tokens", usage.get("input_tokens", 0)) or 0)
        cache_tok = int(
            record.get("cache_read_tokens", usage.get("cache_read_tokens", 0)) or 0
        )
        out_tok = int(record.get("output_tokens", usage.get("output_tokens", 0)) or 0)
        if in_tok or cache_tok or out_tok:
            planner_turns += 1
        input_tokens += in_tok
        cache_read_tokens += cache_tok
        output_tokens += out_tok

    weights = MODEL_WEIGHTS.get(model_tier, MODEL_WEIGHTS["inherit"])
    weighted_cost = (
        input_tokens * weights["input"]
        + cache_read_tokens * weights["cache"]
        + output_tokens * weights["output"]
    ) / 1_000_000.0

    duration_s = (
        round((last_ts - first_ts).total_seconds(), 2)
        if first_ts is not None and last_ts is not None
        else 0.0
    )
    total_tokens = input_tokens + cache_read_tokens + output_tokens
    cache_hit_ratio = (
        round(cache_read_tokens / (input_tokens + cache_read_tokens), 4)
        if (input_tokens + cache_read_tokens) > 0
        else 0.0
    )
    roi_slices_per_cost = (
        round(slices_completed / weighted_cost, 2) if weighted_cost > 0 else 0.0
    )

    return {
        "model_tier": model_tier,
        "steps": steps,
        "planner_turns": planner_turns,
        "duration_seconds": duration_s,
        "input_tokens": input_tokens,
        "cache_read_tokens": cache_read_tokens,
        "output_tokens": output_tokens,
        "total_tokens": total_tokens,
        "cache_hit_ratio": cache_hit_ratio,
        "slices_completed": slices_completed,
        "weighted_cost_units": round(weighted_cost, 6),
        "cost_per_slice": round(weighted_cost / max(1, slices_completed), 6),
        "roi_slices_per_cost_unit": roi_slices_per_cost,
    }


def main() -> None:
    if len(sys.argv) > 1:
        path = Path(sys.argv[1])
    else:
        path = Path("transcript.jsonl")
    tier = sys.argv[2] if len(sys.argv) > 2 else "inherit"
    slices = int(sys.argv[3]) if len(sys.argv) > 3 else 1
    results = analyze_transcript(path, model_tier=tier, slices_completed=slices)
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
