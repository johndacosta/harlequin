"""Minimal Ollama HTTP client (no extra deps)."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any


def ollama_base() -> str:
    return os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434").rstrip("/")


def ollama_generate(
    *,
    model: str,
    prompt: str,
    system: str | None = None,
    options: dict[str, Any] | None = None,
    timeout: float = 600.0,
) -> str:
    payload: dict[str, Any] = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": options
        or {
            "temperature": 0.2,
            "num_ctx": int(os.environ.get("RALPH_OLLAMA_NUM_CTX", "16384")),
        },
    }
    if system:
        payload["system"] = system
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"{ollama_base()}/api/generate",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except urllib.error.URLError as e:
        raise RuntimeError(
            f"Ollama request failed ({ollama_base()}): {e}. Is `ollama serve` running?"
        ) from e
    return str(body.get("response") or "")


def ollama_tags() -> list[str]:
    req = urllib.request.Request(f"{ollama_base()}/api/tags", method="GET")
    with urllib.request.urlopen(req, timeout=30) as resp:
        body = json.loads(resp.read().decode("utf-8"))
    return [m.get("name", "") for m in body.get("models", []) if m.get("name")]
