# LESSONS LEARNED — QuestDB / Harlequin

Append succinct entries when something surprised you or wasted time — **avoid repeating the mistake**.

---

## Format

```markdown
### YYYY-MM-DD — headline

**Context:** adapter / autocomplete / PGWire / tests  
**Wrong assumption:** …  
**Truth:** …  
**Action:** docs updated / code changed / PROTOCOL tweak  
```

---

## Log

### 2026-05-05 — `tables()` column drift

**Context:** Catalog query on PGWire smoke test (.env-loaded connection).  
**Wrong assumption:** `tables()` exposes `table_type` like newer QuestDB doc examples (V/M/T).  
**Truth:** Local server returned only `matView`, `walEnabled`, `table_name`, etc. Must branch on **`matView`** for materialized vs base; cannot distinguish **`VIEW`** without another API.  
**Action:** `_QUEST_KIND_SQL` uses `when matView then 'MATERIALIZED VIEW'`; document version skew in PROGRESS.
