"""Pack repo context for local codegen prompts (token-budget aware)."""

from __future__ import annotations

import re
from pathlib import Path

DEFAULT_GLOBS = [
    "questdb-loop/prds/*.md",
    "src/harlequin_questdb/**/*.py",
    "src/harlequin/**/*.py",
    "src/harlequin_duckdb/**/*.py",
    "src/harlequin_sqlite/**/*.py",
    "tests/adapter_tests/test_questdb*.py",
]


def _iter_files(repo: Path, patterns: list[str]) -> list[Path]:
    found: list[Path] = []
    for pat in patterns:
        found.extend(sorted(repo.glob(pat)))
    seen: set[Path] = set()
    out: list[Path] = []
    for p in found:
        if p.is_file() and p not in seen:
            seen.add(p)
            out.append(p)
    return out


def paths_from_text(text: str, repo: Path) -> list[Path]:
    hits: list[Path] = []
    seen: set[Path] = set()
    for m in re.finditer(
        r"((?:src/harlequin(?:_[a-z0-9]+)?|questdb-loop/ralph|tests)/[^\s`\"':)]+\.py|questdb-loop/[^\s`\"':)]+\.md)",
        text,
    ):
        p = repo / m.group(1)
        if p.is_file() and p not in seen:
            seen.add(p)
            hits.append(p)
    return hits


def pack_context(
    repo: Path,
    *,
    hint_text: str = "",
    max_chars: int = 48_000,
) -> str:
    """Return a markdown bundle of relevant files for Ollama codegen."""
    preferred = paths_from_text(hint_text, repo)
    fallback = _iter_files(repo, DEFAULT_GLOBS)
    files = preferred + [p for p in fallback if p not in preferred]

    chunks: list[str] = ["# Repository context (truncated for local model)\n"]
    used = 0
    for path in files:
        try:
            body = path.read_text(encoding="utf-8")
        except OSError:
            continue
        rel = path.relative_to(repo).as_posix()
        lang = "markdown" if path.suffix == ".md" else "python"
        piece = f"\n## FILE: {rel}\n```{lang}\n{body}\n```\n"
        if used + len(piece) > max_chars:
            head = body[: max(500, max_chars - used - 80)]
            piece = f"\n## FILE: {rel} (truncated)\n```{lang}\n{head}\n```\n"
            if used + len(piece) > max_chars:
                break
        chunks.append(piece)
        used += len(piece)
        if used >= max_chars:
            break
    return "".join(chunks)
