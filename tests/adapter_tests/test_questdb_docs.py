from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
USER_GUIDE = REPO_ROOT / "questdb-loop" / "docs" / "USER_GUIDE.md"
KNOWN_LIMITATIONS = REPO_ROOT / "questdb-loop" / "docs" / "KNOWN_LIMITATIONS.md"


@pytest.fixture
def user_guide_text() -> str:
    assert USER_GUIDE.is_file(), f"missing {USER_GUIDE}"
    return USER_GUIDE.read_text(encoding="utf-8")


def test_user_guide_exists() -> None:
    assert USER_GUIDE.is_file()


def test_user_guide_install_and_connect(user_guide_text: str) -> None:
    assert "8812" in user_guide_text
    assert "8.2.2" in user_guide_text
    assert "harlequin --adapter questdb" in user_guide_text
    assert "uv sync --extra questdb" in user_guide_text


def test_user_guide_auth_dev_only_not_production(user_guide_text: str) -> None:
    lowered = user_guide_text.lower()
    assert "not for production" in lowered or "development only" in lowered
    assert (
        "does not auto-supply" in lowered
        or "does **not** auto-supply" in user_guide_text
    )
    assert "--password quest" in user_guide_text


def test_user_guide_pgwire_limits(user_guide_text: str) -> None:
    lowered = user_guide_text.lower()
    for signal in ("delete", "copy from", "forward-only", "ssl", "dbname"):
        assert signal in lowered
    assert "≠" in user_guide_text or "not" in lowered and "postgresql" in lowered


def test_user_guide_catalog_hints(user_guide_text: str) -> None:
    lowered = user_guide_text.lower()
    assert "tables()" in user_guide_text
    assert "table_columns(" in user_guide_text
    assert "partitionby" in lowered or "partition by" in lowered
    assert "★" in user_guide_text or "designated" in lowered
    assert "t·day" in lowered or "t·DAY" in user_guide_text


def test_user_guide_time_series_recipes(user_guide_text: str) -> None:
    assert "SAMPLE BY" in user_guide_text
    assert "ASOF JOIN" in user_guide_text
    assert "LATEST ON" in user_guide_text
    assert "_harlequin_smoke" in user_guide_text


def test_user_guide_deeper_topics_and_ilp_out_of_scope(user_guide_text: str) -> None:
    lowered = user_guide_text.lower()
    for signal in ("ttl", "wal", "upsert", "materialized view"):
        assert signal in lowered
    assert "ilp" in lowered
    assert "outside harlequin" in lowered


def test_user_guide_no_postgres_system_catalogs(user_guide_text: str) -> None:
    lowered = user_guide_text.lower()
    assert "information_schema" not in lowered
    assert "pg_catalog" not in lowered


@pytest.fixture
def known_limitations_text() -> str:
    assert KNOWN_LIMITATIONS.is_file(), f"missing {KNOWN_LIMITATIONS}"
    return KNOWN_LIMITATIONS.read_text(encoding="utf-8")


def test_known_limitations_exists() -> None:
    assert KNOWN_LIMITATIONS.is_file()


def test_known_limitations_checklist_topics(known_limitations_text: str) -> None:
    lowered = known_limitations_text.lower()
    for signal in ("view", "matview", "table_type"):
        assert signal in lowered
    assert "index" in lowered
    for signal in ("export", "copy_formats", "copy"):
        assert signal in lowered
    for signal in ("8.2.2", "multi-version", "pin"):
        assert signal in lowered
    for signal in ("lexer", "highlight"):
        assert signal in lowered
    assert "cancel" in lowered
    assert "1043" in known_limitations_text


def test_user_guide_links_known_limitations(user_guide_text: str) -> None:
    assert (
        "KNOWN_LIMITATIONS" in user_guide_text or "Known limitations" in user_guide_text
    )


def test_known_limitations_no_destructive_stub_framing(
    known_limitations_text: str,
) -> None:
    lowered = known_limitations_text.lower()
    for forbidden in ("drop database", "drop schema", "destructive stub"):
        assert forbidden not in lowered
