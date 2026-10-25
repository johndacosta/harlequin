from __future__ import annotations

from unittest.mock import MagicMock

from harlequin_questdb.adapter import HarlequinQuestDbConnection
from harlequin_questdb.completions import base_questdb_completions

PRD_TS_TOKENS = (
    "SAMPLE BY",
    "ALIGN TO",
    "ALIGN TO CALENDAR",
    "FILL",
    "LATEST ON",
    "ASOF JOIN",
    "SPLICE JOIN",
    "WINDOW JOIN",
)

SHOULD_TS_TOKENS = (
    "INTERPOLATE",
    "LT JOIN",
    "LATEST BY",
    "TTL",
)


def test_base_questdb_completions_includes_prd_tokens() -> None:
    completions = base_questdb_completions()
    by_label = {c.label: c for c in completions}

    for token in (*PRD_TS_TOKENS, *SHOULD_TS_TOKENS):
        assert token in by_label, f"missing completion token {token!r}"
        completion = by_label[token]
        assert completion.type_label == "kw"
        assert completion.context == "questdb-sql"


class _FunctionsCursor:
    def __init__(
        self,
        *,
        rows: list[tuple[str]] | None = None,
        fail: bool = False,
    ) -> None:
        self.rows = rows or []
        self.fail = fail
        self.executed: list[str] = []

    def __enter__(self) -> _FunctionsCursor:
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def execute(self, query: str) -> None:
        self.executed.append(query)
        if self.fail:
            raise RuntimeError("functions() unavailable")

    def fetchall(self) -> list[tuple[str]]:
        return self.rows


class _FunctionsWorker:
    def __init__(self, cursor: _FunctionsCursor) -> None:
        self._cursor = cursor

    def cursor(self) -> _FunctionsCursor:
        return self._cursor


def _connection_with_functions_cursor(
    cursor: _FunctionsCursor,
) -> HarlequinQuestDbConnection:
    worker = _FunctionsWorker(cursor)
    pool = MagicMock()
    pool.getconn.return_value = worker

    conn = object.__new__(HarlequinQuestDbConnection)
    conn.pool = pool
    return conn


def test_get_completions_merges_functions() -> None:
    cursor = _FunctionsCursor(rows=[("date_trunc",), ("first",)])
    conn = _connection_with_functions_cursor(cursor)

    completions = conn.get_completions()
    labels = {c.label for c in completions}

    assert "date_trunc" in labels
    assert "first" in labels
    assert "SAMPLE BY" in labels

    dynamic = [
        c
        for c in completions
        if c.label in {"date_trunc", "first"}
        and c.priority == 1000
        and c.context is None
    ]
    assert len(dynamic) == 2
    for completion in dynamic:
        assert completion.type_label == "fn"

    assert completions == sorted(completions)


def test_get_completions_degrades_on_functions_failure() -> None:
    cursor = _FunctionsCursor(fail=True)
    conn = _connection_with_functions_cursor(cursor)

    completions = conn.get_completions()
    labels = {c.label for c in completions}

    for token in PRD_TS_TOKENS:
        assert token in labels


def test_functions_query_is_bounded() -> None:
    cursor = _FunctionsCursor(rows=[])
    conn = _connection_with_functions_cursor(cursor)

    conn.get_completions()

    assert len(cursor.executed) == 1
    sql = cursor.executed[0].lower()
    assert "limit 4000" in sql
    assert "length(name) < 48" in sql
