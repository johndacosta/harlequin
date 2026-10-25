from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, cast
from unittest.mock import MagicMock

import pytest
from psycopg.errors import QueryCanceled
from psycopg.errors import SyntaxError as PsycopgSyntaxError

import harlequin_questdb.interactions as questdb_interactions
from harlequin import HarlequinConnection, HarlequinCursor
from harlequin.catalog import Catalog
from harlequin.exception import HarlequinConnectionError, HarlequinQueryError
from harlequin_questdb.adapter import (
    HarlequinQuestDbAdapter,
    HarlequinQuestDbConnection,
    HarlequinQuestDbCursor,
    _escape_quest_literal,
    _quote_quest_identifier,
)
from harlequin_questdb.catalog import (
    DatabaseCatalogItem,
    MaterializedViewCatalogItem,
    SchemaCatalogItem,
    TableCatalogItem,
)
from harlequin_questdb.interactions import show_questdb_partitions

_DROP_DATABASE_OR_SCHEMA = re.compile(r"drop\s+(database|schema)", re.IGNORECASE)
_FORBIDDEN_SECRET = re.compile(
    r"""(?<![\w])password\s*=\s*["'][^"']{1,}["']""",
    re.IGNORECASE,
)


@pytest.fixture
def pin_meta(data_dir: Path) -> dict[str, Any]:
    path = data_dir / "adapter_tests" / "questdb" / "pin_meta.json"
    with open(path) as f:
        return cast(dict[str, Any], json.load(f))


@pytest.fixture
def pin_type_oids(data_dir: Path) -> dict[str, Any]:
    path = data_dir / "adapter_tests" / "questdb" / "pin_type_oids.json"
    with open(path) as f:
        return cast(dict[str, Any], json.load(f))


@pytest.fixture
def stubbed_connection(pin_meta: dict[str, Any]) -> HarlequinQuestDbConnection:
    conn = MagicMock(spec=HarlequinQuestDbConnection)
    type_short = HarlequinQuestDbConnection.QUEST_TYPE_SHORT

    def short_questdb_type(native: str) -> str:
        base = native.upper().split("(")[0].strip()
        return type_short.get(base, "?")

    conn.short_questdb_type = short_questdb_type

    def list_relations() -> list[tuple[str, str, str | None, str | None]]:
        rows: list[tuple[str, str, str | None, str | None]] = []
        for row in pin_meta["tables_rows"]:
            kind = "MATERIALIZED VIEW" if row["matView"] else "BASE TABLE"
            rows.append(
                (
                    row["table_name"],
                    kind,
                    row.get("partitionBy"),
                    row.get("designatedTimestamp"),
                )
            )
        return rows

    def get_relation_columns(
        relation: str,
    ) -> list[tuple[str, str, bool]]:
        cols = pin_meta["table_columns"].get(relation, [])
        return [
            (c["column"], c["type"], bool(c.get("designated", False))) for c in cols
        ]

    conn._list_relations = list_relations
    conn._get_relation_columns = get_relation_columns
    conn._list_schemas = lambda: ["public"]
    return conn


def test_contract_adapter_options_non_empty() -> None:
    assert HarlequinQuestDbAdapter.ADAPTER_OPTIONS
    assert len(HarlequinQuestDbAdapter.ADAPTER_OPTIONS) >= 1


def test_contract_no_copy_formats() -> None:
    assert HarlequinQuestDbAdapter.COPY_FORMATS is None
    adapter = HarlequinQuestDbAdapter([])
    assert not adapter.implements_copy


def test_contract_implements_cancel_matches_override() -> None:
    assert HarlequinQuestDbAdapter.IMPLEMENTS_CANCEL is True
    assert HarlequinQuestDbConnection.cancel is not HarlequinConnection.cancel


def test_contract_adapter_details_points_to_known_limitations() -> None:
    details = HarlequinQuestDbAdapter.ADAPTER_DETAILS or ""
    assert "KNOWN_LIMITATIONS" in details
    assert "tables()" in details
    assert "table_columns()" in details
    assert "functions()" in details
    assert "USER_GUIDE" in details


def test_contract_get_catalog_on_stub(
    stubbed_connection: HarlequinQuestDbConnection,
) -> None:
    stubbed_connection._logical_database_label = (  # type: ignore[method-assign]
        lambda worker=None: "qdb"
    )
    catalog = HarlequinQuestDbConnection.get_catalog(stubbed_connection)
    assert isinstance(catalog, Catalog)
    assert len(catalog.items) == 1
    assert isinstance(catalog.items[0], DatabaseCatalogItem)
    assert catalog.items[0].label == "qdb"


def test_contract_get_completions_on_stub() -> None:
    class FakeCursor:
        def __enter__(self) -> FakeCursor:
            return self

        def __exit__(self, *args: object) -> None:
            return None

        def execute(self, query: str) -> None:
            return None

        def fetchall(self) -> list[tuple[str]]:
            return [("avg",), ("sum",)]

    class FakeWorker:
        def cursor(self) -> FakeCursor:
            return FakeCursor()

    pool = MagicMock()
    pool.getconn.return_value = FakeWorker()

    conn = object.__new__(HarlequinQuestDbConnection)
    conn.pool = pool

    completions = conn.get_completions()
    labels = [c.label for c in completions]
    assert "SAMPLE BY" in labels
    assert "avg" in labels
    assert "sum" in labels
    assert completions == sorted(completions, key=lambda c: (c.priority, c.label))


def test_contract_cursor_columns_shape() -> None:
    conn = MagicMock(spec=HarlequinQuestDbConnection)
    conn._short_column_type_from_oid = (
        HarlequinQuestDbConnection._short_column_type_from_oid
    )

    class Col:
        def __init__(self, name: str, type_code: int) -> None:
            self.name = name
            self.type_code = type_code

    description = [Col("n", 23)]
    cur = MagicMock()
    cur.description = description
    cursor = HarlequinQuestDbCursor(conn, cur)
    assert isinstance(cursor, HarlequinCursor)
    columns = cursor.columns()
    assert columns == [("n", "#")]
    assert all(
        isinstance(name, str) and isinstance(short, str) for name, short in columns
    )
    assert all(len(short) <= 4 for _, short in columns)


def test_escape_quest_literal_doubles_single_quotes() -> None:
    assert _escape_quest_literal("tricky'name") == "tricky''name"


def test_quote_quest_identifier_doubles_embedded_double_quotes() -> None:
    assert _quote_quest_identifier("plain") == '"plain"'
    assert _quote_quest_identifier('foo"bar') == '"foo""bar"'


def test_catalog_qualified_identifier_quotes_special_chars(
    stubbed_connection: HarlequinQuestDbConnection,
) -> None:
    db = DatabaseCatalogItem.from_label(label='db"name', connection=stubbed_connection)
    assert db.qualified_identifier == '"db""name"'

    schema = SchemaCatalogItem.from_parent(parent=db, label="sch'ema")
    assert schema.qualified_identifier == '"sch\'ema"'

    table = TableCatalogItem.from_parent(parent=schema, label='tbl"id')
    assert table.qualified_identifier == f'{schema.qualified_identifier}."tbl""id"'
    assert table.query_name == f'{schema.query_name}."tbl""id"'


def test_show_questdb_partitions_uses_qualified_identifier() -> None:
    driver = MagicMock()
    conn = MagicMock(spec=HarlequinQuestDbConnection)
    db = DatabaseCatalogItem.from_label(label="qdb", connection=conn)
    schema = SchemaCatalogItem.from_parent(parent=db, label="public")
    table = TableCatalogItem.from_parent(parent=schema, label='tricky"name')

    show_questdb_partitions(table, driver)

    driver.insert_text_in_new_buffer.assert_called_once()
    buffer_text = driver.insert_text_in_new_buffer.call_args[0][0]
    assert table.qualified_identifier in buffer_text
    assert '"tricky""name"' in buffer_text


def test_no_secrets_in_questdb_fixtures(data_dir: Path) -> None:
    adapter_test_dir = Path(__file__).parent
    paths = sorted(adapter_test_dir.glob("test_questdb*.py"))
    paths.extend(sorted((data_dir / "adapter_tests" / "questdb").rglob("*")))
    skip_line_markers = ("FAKE_PASSWORD", '"password="', "'password='")
    for path in paths:
        if not path.is_file():
            continue
        for lineno, line in enumerate(path.read_text().splitlines(), start=1):
            if any(marker in line for marker in skip_line_markers):
                continue
            match = _FORBIDDEN_SECRET.search(line)
            assert match is None, (
                f"forbidden secret pattern in {path}:{lineno}: {match.group(0)!r}"
            )


def test_get_relation_columns_sql_escapes_quotes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    executed: list[str] = []

    class FakeCursor:
        def __enter__(self) -> FakeCursor:
            return self

        def __exit__(self, *args: object) -> None:
            return None

        def execute(self, query: str) -> None:
            executed.append(query)

        def fetchall(self) -> list[tuple[str, str, bool]]:
            return [("id", "INT", False)]

    class FakeWorker:
        def cursor(self) -> FakeCursor:
            return FakeCursor()

    pool = MagicMock()
    pool.getconn.return_value = FakeWorker()

    conn = object.__new__(HarlequinQuestDbConnection)
    conn.pool = pool
    conn._relation_columns_include_designated = True

    conn._get_relation_columns("tricky'name")

    assert len(executed) == 1
    assert "table_columns('tricky''name')" in executed[0]


def test_catalog_relation_type_labels(
    stubbed_connection: HarlequinQuestDbConnection,
) -> None:
    db = DatabaseCatalogItem.from_label(label="qdb", connection=stubbed_connection)
    schemas = db.fetch_children()
    assert len(schemas) == 1
    schema = schemas[0]
    assert isinstance(schema, SchemaCatalogItem)

    relations = {rel.label: rel.type_label for rel in schema.fetch_children()}
    assert relations["readings"] == "t·DAY"
    assert relations["plain_table"] == "t"
    assert relations["readings_mv"] == "mv·MONTH"
    assert relations["tricky'name"] == "t"


def test_catalog_column_designated_marker(
    stubbed_connection: HarlequinQuestDbConnection,
) -> None:
    db = DatabaseCatalogItem.from_label(label="qdb", connection=stubbed_connection)
    schema = db.fetch_children()[0]
    readings = next(rel for rel in schema.fetch_children() if rel.label == "readings")
    assert isinstance(readings, TableCatalogItem)
    column_labels = {col.label: col.type_label for col in readings.fetch_children()}
    assert column_labels["ts"] == "ts★"
    assert column_labels["sensor"] == "sym"
    assert column_labels["value"] == "#.#"


def test_catalog_mat_view_kind(stubbed_connection: HarlequinQuestDbConnection) -> None:
    db = DatabaseCatalogItem.from_label(label="qdb", connection=stubbed_connection)
    schema = db.fetch_children()[0]
    mv = next(rel for rel in schema.fetch_children() if rel.label == "readings_mv")
    assert isinstance(mv, MaterializedViewCatalogItem)
    assert mv.type_label == "mv·MONTH"


def test_pin_meta_fixture_shape(pin_meta: dict[str, Any]) -> None:
    assert pin_meta["pin"] == "questdb/questdb:8.2.2"
    assert pin_meta["build"]
    assert pin_meta["tables_rows"]
    assert pin_meta["table_columns"]
    forbidden = {"host", "port", "user", "password", "conn_str"}
    assert forbidden.isdisjoint(pin_meta.keys())
    for row in pin_meta["tables_rows"]:
        assert {
            "table_name",
            "matView",
            "partitionBy",
            "designatedTimestamp",
        } <= row.keys()


def test_pin_type_oids_fixture_shape(pin_type_oids: dict[str, Any]) -> None:
    assert pin_type_oids["pin"] == "questdb/questdb:8.2.2"
    assert pin_type_oids["oids"]
    assert pin_type_oids["probe"]
    forbidden = {"host", "port", "user", "password", "conn_str"}
    assert forbidden.isdisjoint(pin_type_oids.keys())
    for oid_str, short in pin_type_oids["oids"].items():
        assert oid_str.isdigit()
        assert isinstance(short, str)
    for row in pin_type_oids["probe"]:
        assert {"questdb_type", "oid"} <= row.keys()


def test_short_column_type_from_oid_matches_pin_fixture(
    pin_type_oids: dict[str, Any],
) -> None:
    for oid_str, expected in pin_type_oids["oids"].items():
        assert (
            HarlequinQuestDbConnection._short_column_type_from_oid(int(oid_str))
            == expected
        )


def test_must_type_oids_not_question_mark(pin_type_oids: dict[str, Any]) -> None:
    type_short = HarlequinQuestDbConnection.QUEST_TYPE_SHORT
    for row in pin_type_oids["probe"]:
        oid = int(row["oid"])
        short = HarlequinQuestDbConnection._short_column_type_from_oid(oid)
        assert short != "?"
        native = row["questdb_type"]
        if oid != 1043:
            assert short == type_short[native]


def test_cursor_columns_returns_pin_shorts(pin_type_oids: dict[str, Any]) -> None:
    conn = MagicMock(spec=HarlequinQuestDbConnection)
    oid_map = {int(k): v for k, v in pin_type_oids["oids"].items()}
    conn._short_column_type_from_oid = (
        HarlequinQuestDbConnection._short_column_type_from_oid
    )

    class Col:
        def __init__(self, name: str, type_code: int) -> None:
            self.name = name
            self.type_code = type_code

    description = [
        Col("ts", 1114),
        Col("sensor", 1043),
        Col("value", 701),
        Col("id", 23),
    ]
    cur = MagicMock()
    cur.description = description
    cursor = HarlequinQuestDbCursor(conn, cur)
    columns = dict(cursor.columns())
    assert columns["ts"] == oid_map[1114]
    assert columns["sensor"] == oid_map[1043]
    assert columns["value"] == oid_map[701]
    assert columns["id"] == oid_map[23]


FAKE_PASSWORD = "not-a-real-secret"


def test_connection_error_unreachable_port() -> None:
    adapter = HarlequinQuestDbAdapter(
        [],
        host="127.0.0.1",
        port=1,
        connect_timeout=1,
        password=FAKE_PASSWORD,
    )
    with pytest.raises(HarlequinConnectionError) as exc_info:
        adapter.connect()
    exc = exc_info.value
    assert isinstance(exc.msg, str) and exc.msg
    assert exc.title
    assert "password=" not in exc.msg
    assert FAKE_PASSWORD not in exc.msg


def test_connection_error_multiple_conn_strings() -> None:
    adapter = HarlequinQuestDbAdapter(
        ["host=localhost dbname=qdb", "host=remote dbname=qdb"],
    )
    with pytest.raises(HarlequinConnectionError) as exc_info:
        adapter.connect()
    exc = exc_info.value
    assert isinstance(exc.msg, str) and exc.msg
    assert exc.title
    assert "received 2" in exc.msg
    assert "single connection string" in exc.msg.lower()


def test_query_error_on_execute() -> None:
    main_conn = MagicMock()
    mock_cur = MagicMock()
    mock_cur.execute.side_effect = PsycopgSyntaxError('syntax error at or near "FROM"')
    main_conn.cursor.return_value = mock_cur

    conn = object.__new__(HarlequinQuestDbConnection)
    conn._main_conn = main_conn

    with pytest.raises(HarlequinQueryError) as exc_info:
        conn.execute("SELECT * FROM")
    exc = exc_info.value
    assert "syntax error" in exc.msg
    assert exc.title == "Harlequin encountered an error while executing your query."


def test_query_error_on_fetchall() -> None:
    main_conn = MagicMock()
    mock_cur = MagicMock()
    col = MagicMock()
    col.name = "n"
    col.type_code = 23
    mock_cur.description = [col]
    mock_cur.fetchall.side_effect = Exception("fetch failed")
    main_conn.cursor.return_value = mock_cur

    conn = object.__new__(HarlequinQuestDbConnection)
    conn._main_conn = main_conn
    conn._short_column_type_from_oid = (  # type: ignore[method-assign]
        HarlequinQuestDbConnection._short_column_type_from_oid
    )

    cursor = conn.execute("SELECT 1")
    assert cursor is not None
    with pytest.raises(HarlequinQueryError) as exc_info:
        cursor.fetchall()
    exc = exc_info.value
    assert exc.msg == "fetch failed"
    assert exc.title == "Harlequin encountered an error while executing your query."


def test_fetchall_query_canceled_returns_none() -> None:
    main_conn = MagicMock()
    mock_cur = MagicMock()
    col = MagicMock()
    col.name = "n"
    col.type_code = 23
    mock_cur.description = [col]
    mock_cur.fetchall.side_effect = QueryCanceled()
    main_conn.cursor.return_value = mock_cur

    conn = object.__new__(HarlequinQuestDbConnection)
    conn._main_conn = main_conn
    conn._short_column_type_from_oid = (  # type: ignore[method-assign]
        HarlequinQuestDbConnection._short_column_type_from_oid
    )

    cursor = conn.execute("SELECT 1")
    assert cursor is not None
    assert cursor.fetchall() is None


@pytest.mark.parametrize(
    "catalog_item_cls",
    [DatabaseCatalogItem, SchemaCatalogItem],
)
def test_no_destructive_database_schema_interactions(
    catalog_item_cls: type[DatabaseCatalogItem] | type[SchemaCatalogItem],
) -> None:
    interactions = catalog_item_cls.INTERACTIONS
    if interactions is not None:
        labels = [label for label, _interaction in interactions]
        assert not any(_DROP_DATABASE_OR_SCHEMA.search(label) for label in labels)

    interactions_source = Path(questdb_interactions.__file__).read_text().lower()
    assert "drop database" not in interactions_source
    assert "drop schema" not in interactions_source


def test_conn_str_precedence_and_cli_override() -> None:
    adapter = HarlequinQuestDbAdapter(
        [
            "host=quest.example.com port=18812 user=reader "
            "dbname=telemetry sslmode=require"
        ]
    )
    assert adapter.pool_kwargs["host"] == "quest.example.com"
    assert str(adapter.pool_kwargs["port"]) == "18812"
    assert adapter.pool_kwargs["user"] == "reader"
    assert adapter.pool_kwargs["dbname"] == "telemetry"
    assert adapter.pool_kwargs["sslmode"] == "require"
    assert "password" not in adapter.pool_kwargs
    assert adapter.connection_id == "quest.example.com:18812/telemetry"

    # Explicit CLI options must override values in conn_str
    adapter_override = HarlequinQuestDbAdapter(
        ["host=quest.example.com port=18812 dbname=telemetry"],
        host="override.local",
        port=28812,
    )
    assert adapter_override.pool_kwargs["host"] == "override.local"
    assert adapter_override.pool_kwargs["port"] == "28812"
    assert adapter_override.pool_kwargs["dbname"] == "telemetry"


def test_pool_closed_when_getconn_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_pool = MagicMock()
    fake_pool.getconn.side_effect = RuntimeError("getconn timeout")
    monkeypatch.setattr(
        "harlequin_questdb.adapter.ConnectionPool",
        lambda *args, **kwargs: fake_pool,
    )
    adapter = HarlequinQuestDbAdapter([])
    with pytest.raises(HarlequinConnectionError):
        adapter.connect()
    fake_pool.close.assert_called_once()


def test_close_always_closes_pool_even_if_putconn_raises() -> None:
    conn = object.__new__(HarlequinQuestDbConnection)
    conn._main_conn = MagicMock()
    conn.pool = MagicMock()
    conn.pool.putconn.side_effect = RuntimeError("already returned")
    conn.close()
    conn.pool.close.assert_called_once()


def test_worker_connection_reuse_and_autocommit() -> None:
    conn = object.__new__(HarlequinQuestDbConnection)
    fake_pool = MagicMock()
    conn.pool = fake_pool
    conn._logical_database = "qdb"
    conn._quest_kind_sql = "SELECT 1"

    # 1. autocommit already True: cn.autocommit is not overwritten
    mock_cn = MagicMock()
    mock_cn.autocommit = True
    fake_pool.getconn.return_value = mock_cn
    borrowed = conn._borrow_worker()
    assert borrowed is mock_cn

    # 2. worker passed directly into metadata helpers
    worker = MagicMock()
    cursor = MagicMock()
    worker.cursor.return_value.__enter__.return_value = cursor

    cursor.fetchone.return_value = ("custom_db",)
    label = conn._logical_database_label(worker=worker)
    assert label == "custom_db"
    fake_pool.putconn.assert_not_called()

    cursor.fetchone.return_value = ("public",)
    schemas = conn._list_schemas(worker=worker)
    assert schemas == ["public"]
    fake_pool.putconn.assert_not_called()

    cursor.fetchall.return_value = [("t1", "TABLE", "NONE", None)]
    relations = conn._list_relations(worker=worker)
    assert relations == [("t1", "TABLE", "NONE", None)]
    fake_pool.putconn.assert_not_called()

    # 3. zero-arg calls borrow and putconn back to pool
    fake_pool.reset_mock()
    fake_pool.getconn.return_value = worker
    cursor.fetchone.return_value = ("custom_db",)
    label_zero = conn._logical_database_label()
    assert label_zero == "custom_db"
    fake_pool.putconn.assert_called_once_with(worker)
