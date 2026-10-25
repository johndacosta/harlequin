# PRD-03: Autocomplete Engine Indexing, Single-Pass Filtering, Deduplication & Bounded Fuzzy Matching

- **Slice ID**: `PRD-03`
- **Category**: Performance Improvement (`Performance`)
- **Priority / Severity**: `P1` (High — Keystroke Latency & Main-Thread Stalls on Large Schemas)
- **Target Branch / PR Scope**: Single atomic commit / PR (`perf(autocomplete): index member contexts, deduplicate catalog items, and optimize matching`)

## 1. Problem Statement & Root Cause
In databases with hundreds of tables and thousands of columns, typing in the Query Editor or expanding nodes in the Data Catalog causes noticeable latency spikes due to four compounding bottlenecks in `src/harlequin/autocomplete/completers.py` and `src/harlequin/autocomplete/completion.py`:

1. **Triple Full-Scan on Every Keystroke (`completers.py:39-48, 150-159`)**:
   `WordCompleter.__call__` and `MemberCompleter.__call__` iterate over the entire completion list **three separate times** per keystroke:
   - Pass 1: `[c for c in self.completions if c.match_val == match_prefix]`
   - Pass 2: `[c for c in self.completions if c.match_val != match_prefix and c.match_val.startswith(match_prefix)]`
   - Pass 3: `[c for c in self.completions if c.match_val != match_prefix and not c.match_val.startswith(match_prefix) and self._fuzzy_match(c.match_val, match_regex)]`
2. **Unbounded Regex Backtracking in `_fuzzy_match` (`completers.py:93-105`)**:
   `_fuzzy_match` builds `^.*(c1).{0,2}?(c2).{0,2}?...$` with capturing groups on every character and executes `match_regex.match(val)` across all completions. When a user types a 10–15 character identifier, the leading `^.*` combined with multiple `.{0,2}?` quantifiers triggers exponential/polynomial backtracking on non-matching strings.
3. **Linear Scan in `MemberCompleter` (`completers.py:146-148`)**:
   `MemberCompleter` linearly scans all completions (`[c for c in self.completions if c.context == match_context]`) on every keystroke instead of looking up `match_context` in a pre-built `dict[str, list[HarlequinCompletion]]` index.
4. **Unbounded Duplicate Accumulation in `extend_catalog` (`completers.py:74-84`)**:
   Every time a node is expanded or refreshed in `DatabaseTree`, `extend_catalog` runs `self._catalog_completions.extend(new_completions)` without deduplicating existing items and re-sorts the entire `itertools.chain` of completions.
5. **Tuple Allocation in `HarlequinCompletion.__lt__` (`completion.py:37-48`)**:
   `__lt__` allocates `(self.priority, self.label) < (other.priority, other.label)` on every comparison during `sorted()`.

## 2. Goals & Non-Goals
### Goals
- Index `MemberCompleter` completions in a `dict[str, list[HarlequinCompletion]]` keyed by normalized `context` for $O(1)$ context lookup.
- Deduplicate `_catalog_completions` in `extend_catalog` and `update_catalog`.
- Combine the 3 filtering passes (exact, prefix, fuzzy) into a clearer, faster single-pass partitioning loop (or skip fuzzy matching once exact + prefix matches already exceed a reasonable threshold, or fast-reject strings shorter than `len(match_prefix)`).
- Replace capturing groups in `_build_fuzzy_regex` with non-capturing characters (`re.escape(char)`) so regex matching does not allocate capture group tuples or backtrack unnecessarily.
- Optimize `HarlequinCompletion.__lt__` to compare `self.priority < other.priority` before `self.label < other.label` without tuple allocation.

### Non-Goals
- Changing the visual order or user-facing behavior of autocomplete results.

## 3. Technical Design & Affected Files
- `src/harlequin/autocomplete/completers.py`
- `src/harlequin/autocomplete/completion.py`
- `tests/unit_tests/test_completers.py`

### Proposed Changes
1. **`HarlequinCompletion.__lt__` (`src/harlequin/autocomplete/completion.py`)**:
   ```python
   def __lt__(self, other: object) -> bool:
       if not isinstance(other, HarlequinCompletion):
           return NotImplemented
       if self.priority != other.priority:
           return self.priority < other.priority
       if self.label != other.label:
           return self.label < other.label
       return self.type_label < other.type_label
   ```
2. **`_build_fuzzy_regex` (`src/harlequin/autocomplete/completers.py`)**:
   Use `r".{0,2}?".join(re.escape(char) for char in prefix)` with `re.search` instead of `^.*(c1).{0,2}?(c2).*$` with `re.match` and capturing groups, and skip running regex if `len(val) < len(prefix)` or `prefix[0] not in val`.
3. **Single-pass categorization**:
   Partition candidates into `exact_matches`, `prefix_matches`, and `fuzzy_candidates` in a single loop over the candidate list.
4. **Context Index in `MemberCompleter`**:
   Maintain `self._completions_by_context: dict[str, list[HarlequinCompletion]]` rebuilt when `_merge_completions()` runs, making `MemberCompleter.__call__` look up `self._completions_by_context.get(match_context, [])` in $O(1)$ time.
5. **Deduplication in `_merge_completions` / `extend_catalog`**:
   Track seen `(label, type_label, priority, context)` keys so expanding catalog nodes repeatedly never duplicates completions.

## 4. Verification & Acceptance Criteria
```bash
uv run pytest tests/unit_tests/test_completers.py tests/functional_tests/test_code_editor.py
uv run ruff check src/harlequin/autocomplete tests/
uv run mypy src/harlequin/autocomplete tests/
```
