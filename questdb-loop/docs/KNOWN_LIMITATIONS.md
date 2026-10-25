# Known limitations — QuestDB adapter (v1)

Honest gaps and stubs for the Harlequin QuestDB adapter on pin **`questdb/questdb:8.2.2`**. For install, auth, and catalog hints (`t·DAY`, `ts★`, etc.), see the [user guide](./USER_GUIDE.md) — especially [Decoding labels in the Harlequin catalog tree](./USER_GUIDE.md#decoding-labels-in-the-harlequin-catalog-tree).

The catalog sidebar omits database- and schema-level drop actions; relation menus are read-oriented (introspection and copy-friendly labels, not destructive DDL).

| Topic | Limitation on pin 8.2.2 |
|-------|-------------------------|
| **Views** | Regular SQL VIEWs **will** appear as base tables when `tables()` lacks `table_type`. Materialized views are detected via the `matView` column. Harlequin does not open a view-definition buffer for QuestDB views. |
| **Indexes** | No index introspection catalog interaction (no `pg_index` / `information_schema` index paths). The `indexed` column from `table_columns()` is not read or surfaced in the UI in v1. |
| **Export / copy** | `COPY_FORMATS` is unset; Harlequin's export/copy pipeline is unavailable for this adapter. Use QuestDB's own export tools for bulk extracts. |
| **Multi-version** | Built and tested against **`questdb/questdb:8.2.2`** only; other QuestDB versions are best-effort. Meta function columns may drift across pins (see `LESSONS_LEARNED`); a future `table_type` column could change VIEW labeling. |
| **Lexer** | No QuestDB-specific syntax highlighting (ADR 0007). Dialect discovery uses completions, the catalog tree, and docs — not a custom lexer. |
| **Cancel** | Query cancel is wired **best-effort** via `cancel_safe()` (ADR 0008). It may not stop every long-running query on every pin build; there is no online cancel reliability gate in CI. |
| **Results grid types (P1)** | PGWire OID **1043** maps to `s` for STRING, SYMBOL, and GEOHASH alike in the **results grid**. Use catalog `table_columns()` type labels as authoritative. |

**ILP ingestion** is outside Harlequin — see [ILP ingestion is outside Harlequin](./USER_GUIDE.md#ilp-ingestion-is-outside-harlequin) in the user guide.
