# TASK BRIEF — Collect FTSE TWSE Taiwan 50 Historical Review Lists (2015→now)

*Handoff instruction file. Paste or reference this in a NEW chat to
have Claude complete the collection. Written 2026-07-29 (session 8w)
after the sandbox-only evaluation concluded this needs a browser.*

## Context (read first)

This repo (`execution_analytics`) is an index-rebalance analytics
platform. The retrospective backtest program needs ANSWER KEYS =
official quarterly review change lists. **MSCI is already solved**:
all 44 Standard-index public lists 2015-2025 are downloaded and
parsed (`data/msci_archive/`, `scripts/fetch_msci_archive.py`).
**FTSE TW50 is the missing provider.** Why it resisted automation:
no uniform document archive (CMS news pages, unpredictable URLs);
TIP's news list is client-side JS (SSR payload carries only CSS);
the old research.ftserussell.com constituents page has zero Wayback
snapshots. Full evaluation: docs/TAIWAN_MARKET_ANALYSIS.md §5.

## The goal

A machine-readable file `data/ftse_tw50_changes.json` covering
**every FTSE TWSE Taiwan 50 quarterly review from 2015 to now**
(4/year: Mar, Jun, Sep, Dec — ~46 events), schema:

```json
{"2026-06": {"ann_date": "2026-06-05", "eff_print": "2026-06-18",
             "adds": [{"code": "3443", "name": "GUC"}],
             "dels": [{"code": "....", "name": "..."}],
             "source": "<url or citation>"},
 ...}
```

Empty adds/dels are VALID (quiet reviews happen) — record them as
empty lists with the source, never guess. Unknown quarters get
`"status": "NOT FOUND"` — a gap stated beats a gap filled in.

## Method (ranked — use the Chrome extension)

1. **TIP (taiwanindex.com.tw)** — the co-manager. Open the news/
   announcement archive in the browser (it renders client-side),
   filter/search for 臺灣50指數 + 審核 (review) announcements, walk
   back as far as the archive goes (TIP founded ~2016). Each
   quarterly announcement lists 納入 (additions) and 剔除
   (deletions) with codes.
2. **TWSE news archive (twse.com.tw)** — TWSE co-publishes the
   same review results; use its news search for 臺灣50指數成分股;
   this covers 2015-2016 before TIP existed.
3. **FTSE Russell (ftserussell.com)** — review announcements under
   index news; use for cross-checking, expect JS walls.
4. **Cross-validation (do for at least 4 quarters):** the repo's
   event-print detector — adds should show large effective-day
   auction prints (June-2026: 3443/3665/8046/4958 at 44-71%
   auction share, print day Jun 18). Effective print day = last
   trading day before the effective Monday (watch holidays: Jun-19
   Dragon Boat and Feb-27 examples are in the repo's case studies).

## Repo conventions that BIND this task

- **Honesty rules:** never fabricate a quarter; state NOT FOUND;
  keep a per-quarter `source`; record any ambiguity inline.
- **Ticker codes** are the join key (TWSE 4-digit); keep both code
  and Chinese/English name (alias maps matter — see the
  "HONPRECISION" alias-rejection story in
  docs/case_studies/REPRO_FEB2026_TW.md).
- Save the JSON to `data/` (gitignored caches live there); write a
  short case-study doc `docs/case_studies/FTSE_TW50_KEYS.md` with
  coverage stats (quarters found / NOT FOUND, source mix).
- Append a work-block entry to `docs/SESSION_SUMMARY_2026-07-08.md`
  (follow the existing format) and update
  `docs/TAIWAN_MARKET_ANALYSIS.md` §5 (change "queued" to the
  result).
- Do NOT git commit — the user commits personally.
- Suite must stay green: `python -m pytest -q` (407+ tests).

## Definition of done

- [ ] `data/ftse_tw50_changes.json` with >= 40 quarters keyed or
      explicitly NOT FOUND
- [ ] >= 4 quarters cross-validated against effective-day prints
- [ ] `docs/case_studies/FTSE_TW50_KEYS.md` coverage report
- [ ] TAIWAN_MARKET_ANALYSIS §5 + session summary updated
- [ ] pytest green

## Suggested opening prompt for the new chat

> Read docs/TASK_FTSE_LIST_COLLECTION.md in my execution_analytics
> folder and complete the task. Use the Chrome extension for the
> TIP/TWSE/FTSE archives — the sandbox evaluation already proved
> plain HTTP cannot do this. Work in autopilot mode; follow the
> repo's honesty conventions.
