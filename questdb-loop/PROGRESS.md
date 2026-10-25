# PROGRESS — QuestDB adapter

Ledger for Ralph-loop sessions. Append **newest first**.

---

## Template (copy for each entry)

```markdown
### YYYY-MM-DD — <short title>

**State entering:** PRD_HOLD | BUILDING | VERIFYING

**Goals this session:**
- 

**Commits / edits:**
- 

**Commands run:** (paths, adapters, `-m`)

**Outcome:** ✅ / ⚠️ / ❌

**Next:**
- 

**Pointers:** issues, gist, gist of errors
```

---

### 2026-05-05 — `.env` smoke test vs live QuestDB

**Goals:** Run adapter against `.env` (`QUESTDB_*` same as `.env-template`).

**Commands run:** psycopg probe of `tables()` columns; adapter smoke (catalog, schemas, relations, `table_columns`, completions, `SELECT 1`).

**Outcome:** ✅ Fixed catalog SQL: this server has **`matView`** but no **`table_type`**. Pooled workers now use **`autocommit=True`** via `_borrow_worker()` to avoid psycopg-pool rollback noise on return.

**Facts:** ~149 relations (`BASE TABLE` + `MATERIALIZED VIEW`); schema `public`; ~346 completions.

**Next:** Optional full TUI run (`harlequin --adapter questdb` with conn string); VIEW detection if server adds metadata.

---

### 2026-05-05 — Bootstrap loop + stubs

**State entering:** BUILDING  

**Goals this session:**
- Initialize loop docs (`PROTOCOL.md`, PRD audit, PROGRESS, LESSONS).
- Land `harlequin_questdb` package skeleton plus pyproject extras and entry-point.

**Commands run:**
- `uv lock`, `uv sync --extra questdb --group static --group test`
- `uv run ruff check/format src/harlequin_questdb`, `uv run mypy src/harlequin_questdb`
- `get_adapter_class(\"questdb\")` import probe

**Outcome:** ✅ stubs + lint/typecheck green for new package.

**Next:**
- Smoke `harlequin --adapter questdb` against live QuestDB; validate `tables()` / `functions()` shapes on installed version.
