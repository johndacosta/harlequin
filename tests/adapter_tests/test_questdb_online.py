from __future__ import annotations

import os
from typing import Any

import pytest

from harlequin.exception import HarlequinConnectionError, HarlequinQueryError
from harlequin_questdb.adapter import (
    HarlequinQuestDbAdapter,
    HarlequinQuestDbConnection,
)
from harlequin_questdb.catalog import (
    DatabaseCatalogItem,
    MaterializedViewCatalogItem,
    SchemaCatalogItem,
    TableCatalogItem,
)

SMOKE_TABLE = "_harlequin_smoke"
SMOKE_DDL = """
CREATE TABLE IF NOT EXISTS _harlequin_smoke (
    ts TIMESTAMP,
    id INT,
    sensor SYMBOL,
    geo GEOHASH(8c)
) TIMESTAMP(ts) PARTITION BY DAY;
"""
SMOKE_MV_TABLE = "_harlequin_smoke_mv"
SMOKE_MV_DDL = """
CREATE MATERIALIZED VIEW IF NOT EXISTS _harlequin_smoke_mv AS
SELECT ts, count() AS n
FROM _harlequin_smoke
SAMPLE BY 1d;
"""


def _questdb_connect_kwargs() -> dict[str, Any]:
    return {
        "host": os.environ.get("QUESTDB_HOST", "127.0.0.1"),
        "port": os.environ.get("QUESTDB_PG_PORT", "8812"),
        "user": os.environ.get("QUESTDB_USER", "admin"),
        "password": os.environ.get("QUESTDB_PASSWORD", "quest"),
        "sslmode": "disable",
    }


def _connect_or_skip(adapter: HarlequinQuestDbAdapter) -> HarlequinQuestDbConnection:
    try:
        return adapter.connect()
    except HarlequinConnectionError as exc:
        pytest.skip(f"QuestDB unreachable at {adapter.connection_id}: {exc}")
        raise AssertionError("unreachable") from exc


@pytest.fixture
def questdb_adapter() -> HarlequinQuestDbAdapter:
    return HarlequinQuestDbAdapter([], **_questdb_connect_kwargs())


@pytest.mark.online
def test_questdb_online_connect_and_select_one(
    questdb_adapter: HarlequinQuestDbAdapter,
) -> None:
    conn = _connect_or_skip(questdb_adapter)
    cursor = conn.execute("SELECT 1")
    assert cursor is not None
    assert cursor.fetchall() == [(1,)]


@pytest.mark.online
def test_questdb_online_catalog_hints(questdb_adapter: HarlequinQuestDbAdapter) -> None:
    conn = _connect_or_skip(questdb_adapter)
    try:
        conn.execute(SMOKE_DDL)
    except HarlequinQueryError as exc:
        pytest.skip(f"QuestDB smoke DDL failed: {exc}")

    db_item = conn.get_catalog().items[0]
    assert isinstance(db_item, DatabaseCatalogItem)
    schemas = db_item.fetch_children()
    assert len(schemas) >= 1
    schema = schemas[0]
    assert isinstance(schema, SchemaCatalogItem)

    relations = {rel.label: rel for rel in schema.fetch_children()}
    smoke = relations.get(SMOKE_TABLE)
    assert smoke is not None, f"{SMOKE_TABLE} missing from catalog"
    assert isinstance(smoke, TableCatalogItem)
    assert smoke.type_label == "t·DAY"

    column_labels = {col.label: col.type_label for col in smoke.fetch_children()}
    assert column_labels.get("ts") == "ts★"


@pytest.mark.online
def test_questdb_online_relation_mat_view_kind(
    questdb_adapter: HarlequinQuestDbAdapter,
) -> None:
    """VIEWs without table_type appear as BASE TABLE on this pin."""
    conn = _connect_or_skip(questdb_adapter)

    db_item = conn.get_catalog().items[0]
    assert isinstance(db_item, DatabaseCatalogItem)
    schemas = db_item.fetch_children()
    assert len(schemas) >= 1
    schema = schemas[0]
    assert isinstance(schema, SchemaCatalogItem)

    mat_views = [
        rel
        for rel in schema.fetch_children()
        if isinstance(rel, MaterializedViewCatalogItem)
    ]
    if mat_views:
        assert mat_views[0].type_label.startswith("mv")
        return

    try:
        conn.execute(SMOKE_DDL)
        conn.execute(SMOKE_MV_DDL)
    except HarlequinQueryError as exc:
        pytest.skip(f"QuestDB smoke MV DDL failed: {exc}")

    db_item = conn.get_catalog().items[0]
    assert isinstance(db_item, DatabaseCatalogItem)
    schemas = db_item.fetch_children()
    schema = schemas[0]
    assert isinstance(schema, SchemaCatalogItem)
    relations = {rel.label: rel for rel in schema.fetch_children()}
    mv = relations.get(SMOKE_MV_TABLE)
    assert mv is not None, f"{SMOKE_MV_TABLE} missing from catalog after CREATE"
    assert isinstance(mv, MaterializedViewCatalogItem)
    assert mv.type_label.startswith("mv")


@pytest.mark.online
def test_questdb_online_grid_column_types(
    questdb_adapter: HarlequinQuestDbAdapter,
) -> None:
    conn = _connect_or_skip(questdb_adapter)
    try:
        conn.execute(SMOKE_DDL)
    except HarlequinQueryError as exc:
        pytest.skip(f"QuestDB smoke DDL failed: {exc}")

    try:
        cursor = conn.execute(
            """
            SELECT
                cast(null as timestamp) as ts,
                cast(1 as int) as id,
                cast('a' as symbol) as sensor,
                cast(null as geohash(8c)) as geo
            FROM long_sequence(0)
            """
        )
    except HarlequinQueryError as exc:
        pytest.skip(f"QuestDB grid type probe failed: {exc}")
    assert cursor is not None
    column_types = dict(cursor.columns())
    assert column_types["ts"] == "ts"
    assert column_types["id"] == "#"
    assert column_types["sensor"] != "?"
    assert column_types["geo"] != "?"
    assert column_types["sensor"] == column_types["geo"] == "s"


@pytest.mark.online
def test_questdb_online_query_error_message(
    questdb_adapter: HarlequinQuestDbAdapter,
) -> None:
    conn = _connect_or_skip(questdb_adapter)
    with pytest.raises(HarlequinQueryError) as exc_info:
        cursor = conn.execute("SELECT * FROM definitely_not_a_table_xyz")
        if cursor is not None:
            cursor.fetchall()
    exc = exc_info.value
    assert exc.msg
    assert exc.title
