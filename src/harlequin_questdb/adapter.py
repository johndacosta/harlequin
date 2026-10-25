from __future__ import annotations

import logging
from typing import Any, Sequence

from psycopg import Connection, Cursor, InterfaceError, OperationalError, conninfo
from psycopg.errors import QueryCanceled
from psycopg_pool import ConnectionPool
from textual_fastdatatable.backend import AutoBackendType

from harlequin import (
    HarlequinAdapter,
    HarlequinCompletion,
    HarlequinConnection,
    HarlequinCursor,
)
from harlequin.catalog import Catalog
from harlequin.exception import HarlequinConnectionError, HarlequinQueryError
from harlequin_questdb.catalog import DatabaseCatalogItem
from harlequin_questdb.cli_options import QUESTDB_OPTIONS
from harlequin_questdb.completions import base_questdb_completions

logger = logging.getLogger(__name__)


def _configure_questdb_connection(conn: Connection[Any]) -> None:
    """Pool callback: predictable session settings for PGWire reads."""
    conn.autocommit = True


def _check_questdb_pool_connection(conn: Connection[Any]) -> None:
    """Pool callback before handing out a pooled connection."""
    if conn.closed != 0:
        raise OperationalError("pooled QuestDB connection is closed")
    with conn.cursor() as cur:
        cur.execute("select 1")


def _recoverable_connection_error(exc: BaseException) -> bool:
    if isinstance(
        exc,
        (
            BrokenPipeError,
            ConnectionResetError,
            OperationalError,
            InterfaceError,
        ),
    ):
        return True
    msg = str(exc).lower()
    return "closed" in msg or ("connection" in msg and "lost" in msg)


def _escape_quest_literal(ident: str) -> str:
    """Escape single quotes inside QuestDB string literals."""
    return ident.replace("'", "''")


class HarlequinQuestDbCursor(HarlequinCursor):
    def __init__(self, conn: HarlequinQuestDbConnection, cur: Cursor[Any]) -> None:
        self.conn = conn
        self.cur = cur
        assert cur.description is not None
        self.description = cur.description.copy()
        self._limit: int | None = None

    def columns(self) -> list[tuple[str, str]]:
        return [
            (col.name, self.conn._short_column_type_from_oid(col.type_code))
            for col in self.description
        ]

    def set_limit(self, limit: int) -> HarlequinQuestDbCursor:
        self._limit = limit
        return self

    def fetchall(self) -> AutoBackendType:
        try:
            if self._limit is None:
                return self.cur.fetchall()
            return self.cur.fetchmany(self._limit)
        except QueryCanceled:
            return []
        except Exception as e:
            raise HarlequinQueryError(
                msg=f"{e.__class__.__name__}: {e}",
                title="Harlequin encountered an error while executing your query.",
            ) from e
        finally:
            self.cur.close()


class HarlequinQuestDbConnection(HarlequinConnection):
    """
    QuestDB via PGWire (see https://questdb.com/docs/query/pgwire/overview/).
    Avoid pg_catalog/information_schema; introspect with tables()/table_columns().
    """

    _QUEST_KIND_SQL = """
        select
            table_name,
            case
                when matView then 'MATERIALIZED VIEW'
                else 'BASE TABLE'
            end as harlequin_kind
        from tables()
        order by table_name asc
        ;
    """

    QUEST_TYPE_SHORT: dict[str, str] = {
        "SYMBOL": "sym",
        "STRING": "s",
        "VARCHAR": "s",
        "CHAR": "s",
        "TIMESTAMP": "ts",
        "DATE": "d",
        "DOUBLE": "#.#",
        "FLOAT": "#.#",
        "REAL": "#.#",
        "LONG": "##",
        "SHORT": "#",
        "INT": "#",
        "BOOLEAN": "t/f",
        "BYTE": "b",
        "GEOINT": "geo",
        "GEOHASH": "geo",
        "BINARY": "0b",
        "UUID": "uid",
        "LONG256": "h",
        "DECIMAL": "$",
        "IP": "ip",
        "INTERVAL": "|-|",
        "RECORD": "{}",
        "LONG128": "##",
        "CURSOR": "cur",
        "VARIANT": "?",
        "UNKNOWN": "?",
        "CHARACTER": "s",
        "NUMBER": "#.#",
    }

    def __init__(
        self,
        conn_str: Sequence[str],
        *,
        kwargs: dict[str, Any],
        logical_database: str | None = None,
        init_message: str = "",
    ) -> None:
        self.init_message = init_message
        self._logical_database = logical_database or "qdb"
        raw = conn_str[0] if conn_str else ""

        try:
            self.conn_info = conninfo.conninfo_to_dict(conninfo=raw, **kwargs)
        except Exception as e:
            raise HarlequinConnectionError(
                msg=str(e),
                title="Harlequin could not connect to QuestDB — invalid connection.",
            ) from e

        try:
            raw_timeout = self.conn_info.get("connect_timeout")
            timeout = float(raw_timeout) if raw_timeout is not None else 30.0
        except (TypeError, ValueError) as e:
            raise HarlequinConnectionError(
                msg=str(e),
                title="Harlequin could not connect to QuestDB — bad connect_timeout.",
            ) from e

        try:
            self.pool = ConnectionPool(
                conninfo=raw,
                min_size=1,
                max_size=5,
                kwargs=kwargs,
                configure=_configure_questdb_connection,
                check=_check_questdb_pool_connection,
                open=True,
                timeout=timeout,
                max_idle=float(86400),
                max_lifetime=float(86400 * 7),
                reconnect_timeout=float(120),
            )
            self._main_conn = self.pool.getconn()
        except Exception as e:
            raise HarlequinConnectionError(
                msg=str(e), title="Harlequin could not connect to QuestDB."
            ) from e

        self._main_conn.autocommit = True

    def _reconnect_main(self) -> None:
        """
        Swap the primary connection leased for editor queries/cancel. Call after
        the server closes the TCP session (NAT, PGWire idle policy, restart).
        """
        old = self._main_conn
        try:
            self.pool.putconn(old)
        except Exception as exc:
            logger.debug("Could not putconn main QuestDB handle: %s", exc)
            try:
                old.close()
            except Exception:
                pass
        self._main_conn = self.pool.getconn()

    def _borrow_worker(self) -> Connection[Any]:
        cn = self.pool.getconn()
        cn.autocommit = True
        return cn

    def execute(self, query: str) -> HarlequinCursor | None:
        cur: Cursor[Any] | None = None
        for attempt in range(2):
            try:
                cur = self._main_conn.cursor()
                cur.execute(query=query)
            except QueryCanceled:
                if cur is not None:
                    cur.close()
                return None
            except Exception as e:
                if cur is not None:
                    cur.close()
                    cur = None
                if attempt == 0 and _recoverable_connection_error(e):
                    self._reconnect_main()
                    continue
                raise HarlequinQueryError(
                    msg=str(e),
                    title="Harlequin encountered an error while executing your query.",
                ) from e
            else:
                if cur is not None and cur.description is not None:
                    return HarlequinQuestDbCursor(self, cur)
                if cur is not None:
                    cur.close()
                return None
        return None

    def cancel(self) -> None:
        try:
            self._main_conn.cancel_safe()
        except Exception as exc:
            logger.debug(
                "QuestDB cancel_safe failed (%s); will reconnect on next execute.",
                exc,
            )
            try:
                self._reconnect_main()
            except Exception:
                pass

    def get_catalog(self) -> Catalog:
        label = self._logical_database_label()
        db_item = DatabaseCatalogItem.from_label(label=label, connection=self)
        return Catalog(items=[db_item])

    def get_completions(self) -> list[HarlequinCompletion]:
        completions = base_questdb_completions()
        worker = self._borrow_worker()
        try:
            with worker.cursor() as cur:
                cur.execute(
                    """
                    select distinct name as routine_name
                    from functions()
                    where
                        name is not null
                        and length(name) < 48
                    order by 1 asc
                    limit 4000
                    ;"""
                )
                rows = cur.fetchall()
        except Exception:
            rows = []
        finally:
            self.pool.putconn(worker)

        completions.extend(
            HarlequinCompletion(
                label=row[0],
                type_label="fn",
                value=row[0],
                priority=1000,
                context=None,
            )
            for row in rows
            if row and row[0]
        )

        return sorted(completions)

    def close(self) -> None:
        self.pool.putconn(self._main_conn)
        self.pool.close()

    def _logical_database_label(self) -> str:
        worker = self._borrow_worker()
        try:
            with worker.cursor() as cur:
                cur.execute("select current_database();")
                row = cur.fetchone()
                if row and isinstance(row[0], str):
                    return row[0]
        except Exception:
            pass
        finally:
            self.pool.putconn(worker)
        return self._logical_database

    def _list_schemas(self) -> list[str]:
        worker = self._borrow_worker()
        try:
            with worker.cursor() as cur:
                cur.execute("select current_schema();")
                row = cur.fetchone()
                if row and isinstance(row[0], str):
                    return [row[0]]
        except Exception:
            pass
        finally:
            self.pool.putconn(worker)
        return ["public"]

    def _list_relations(self) -> list[tuple[str, str]]:
        worker = self._borrow_worker()
        try:
            with worker.cursor() as cur:
                cur.execute(self._QUEST_KIND_SQL)
                return [(str(r[0]), str(r[1])) for r in cur.fetchall()]
        finally:
            self.pool.putconn(worker)

    def _get_relation_columns(self, relation: str) -> list[tuple[str, str]]:
        lit = _escape_quest_literal(relation)
        worker = self._borrow_worker()
        try:
            with worker.cursor() as cur:
                cur.execute(
                    f"""
                    select "column", type
                    from table_columns('{lit}')
                    order by "column" asc
                    ;"""
                )
                return [(str(r[0]), str(r[1])) for r in cur.fetchall()]
        finally:
            self.pool.putconn(worker)

    def short_questdb_type(self, native: str) -> str:
        base = native.upper().split("(")[0].strip()
        return self.QUEST_TYPE_SHORT.get(base, "?")

    @staticmethod
    def _short_column_type_from_oid(oid: int) -> str:
        # Best-effort until dedicated QuestDB OID map exists.
        MAPPING: dict[int, str] = {
            16: "t/f",
            20: "##",
            21: "#",
            23: "#",
            25: "s",
            700: "#.#",
            701: "#.#",
            1082: "d",
            1114: "ts",
            1184: "ts",
        }
        return MAPPING.get(oid, "?")


class HarlequinQuestDbAdapter(HarlequinAdapter):
    """
    QuestDB via PGWire (psycopg). Use `--adapter questdb` after installing the
    `questdb` extra.
    """

    ADAPTER_OPTIONS = QUESTDB_OPTIONS
    IMPLEMENTS_CANCEL = True
    ADAPTER_DETAILS = (
        "## QuestDB (PGWire)\n\n"
        "- Connects with [psycopg](https://www.psycopg.org/) on port **8812** "
        "by default.\n"
        "- QuestDB's SQL dialect and catalogs differ from PostgreSQL; this "
        "adapter reads metadata via [`tables()`](https://questdb.io/docs/query/"
        "functions/meta/#tables), [`table_columns()`](https://questdb.io/docs/"
        "query/functions/meta/#table_columns), and [`functions()`](https://"
        "questdb.io/docs/query/functions/meta/#functions).\n"
        "- Prefer long flags if `-h`/`-p` are rejected: `--host`, `--port`, `--user`, "
        "`--password`, `--dbname`.\n"
        "- Or pass a single libpq `CONN_STR`: "
        '`"host=… port=… user=… password=… dbname=qdb sslmode=disable"`.\n'
        "- PGWire notes (SSL, dialect, timestamps, cursors) are summarized in "
        "[QuestDB docs](https://questdb.com/docs/query/pgwire/overview/).\n"
        "- Idle TCP drops (NAT/firewall/QuestDB) are mitigated with **TCP keepalive** "
        "libpq options on the socket and **automatic reconnect** of the editor "
        "connection after failures that look like a dead session.\n"
    )

    def __init__(
        self,
        conn_str: Sequence[str],
        host: str | None = None,
        port: str | int | None = None,
        user: str | None = None,
        password: str | None = None,
        dbname: str | None = None,
        connect_timeout: str | int | float | None = None,
        sslmode: str | None = None,
        **_ignored: Any,
    ) -> None:
        pool_kwargs: dict[str, Any] = {
            **({"host": host} if host is not None else {}),
            **({"port": str(port)} if port is not None else {}),
            **({"user": user} if user is not None else {}),
            **({"password": password} if password is not None else {}),
            **({"dbname": dbname} if dbname is not None else {}),
            **(
                {"connect_timeout": str(connect_timeout)}
                if connect_timeout is not None
                else {}
            ),
            **({"sslmode": sslmode} if sslmode is not None else {}),
        }
        pool_kwargs.setdefault("host", "127.0.0.1")
        pool_kwargs.setdefault("port", "8812")
        pool_kwargs.setdefault("user", "admin")
        pool_kwargs.setdefault("dbname", "qdb")
        pool_kwargs.setdefault("sslmode", "disable")
        # Reduce idle TCP teardown on long-running Harlequin sessions (NAT / PGWire).
        pool_kwargs.setdefault("keepalives", 1)
        pool_kwargs.setdefault("keepalives_idle", 30)
        pool_kwargs.setdefault("keepalives_interval", 10)
        pool_kwargs.setdefault("keepalives_count", 6)
        self.conn_str = conn_str
        self.pool_kwargs = pool_kwargs
        self.logical_database_label = str(pool_kwargs.get("dbname", "qdb"))

    def connect(self) -> HarlequinQuestDbConnection:
        if len(self.conn_str) > 1:
            raise HarlequinConnectionError(
                msg=(
                    "The QuestDB adapter accepts a single connection string; "
                    f"received {len(self.conn_str)}."
                ),
                title="Too many connection strings for QuestDB.",
            )
        return HarlequinQuestDbConnection(
            self.conn_str,
            logical_database=self.logical_database_label,
            kwargs=self.pool_kwargs,
        )

    @property
    def connection_id(self) -> str | None:
        host = str(self.pool_kwargs.get("host", "127.0.0.1"))
        port = str(self.pool_kwargs.get("port", "8812"))
        db = str(self.pool_kwargs.get("dbname", "qdb"))
        return f"{host}:{port}/{db}"
