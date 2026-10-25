from __future__ import annotations

from harlequin.options import AbstractOption, TextOption

host = TextOption(
    name="host",
    short_decls=["-h"],
    default="localhost",
    description="QuestDB hostname (PGWire defaults to localhost).",
)
port = TextOption(
    name="port",
    short_decls=["-p"],
    default="8812",
    description="PGWire TCP port (QuestDB defaults to 8812).",
)
user = TextOption(
    name="user",
    short_decls=["-U"],
    default="admin",
    description=(
        "User name configured in pg.user/pg.readonly.user in QuestDB "
        "`server.conf` (default admin)."
    ),
)
password = TextOption(
    name="password",
    description=(
        "PGWire password (`quest` unless changed in QuestDB configuration)."
    ),
)
dbname = TextOption(
    name="dbname",
    short_decls=["-d"],
    default="qdb",
    description=(
        "Libpq database field; QuestDB ignores logical database names "
        '(use `"qdb"` or any placeholder).'
    ),
)
connect_timeout = TextOption(
    name="connect-timeout",
    description="Seconds before connect fails.",
)
sslmode = TextOption(
    name="sslmode",
    description="PGWire docs: SSL typically unsupported until enabled server-side; "
    "prefer `disable` for local/dev.",
)


QUESTDB_OPTIONS: list[AbstractOption] = [
    host,
    port,
    user,
    password,
    dbname,
    connect_timeout,
    sslmode,
]
