# FTSE TWSE Taiwan 50 — Historical Answer Keys (2016-2026)

*Session 8x. The FTSE key-collection task (TASK_FTSE_LIST_COLLECTION
.md), completed same-day via the hybrid path: the Chrome extension
opened the door (TIP's client-side news archive, unreachable by
plain HTTP), revealed that DETAIL pages are numeric AND server-side
rendered — so the sandbox then enumerated all ~460 pages threaded,
kept the 41 TWSE-FTSE review announcements, and parsed them.*

## Coverage

- **data/ftse_tw50_changes.json**: 41 keyed events (quarterly
  reviews + ad-hoc corporate-action changes), 2016-11 → 2026-06;
  **100 TW50 additions+deletions** with codes, names, reserve
  lists, effective dates, and per-event source URLs.
- **NOT FOUND (7 quarters, stated): 2015-03 → 2016-09** — the
  pre-TIP era; path: TWSE-era announcements / 證交資料月刊
  (manual). The 2015 target is 7 quarters short; everything TIP
  ever published is captured.

## Parser iterations (each caught by a data check)

1. Preamble trap: announcements ENUMERATE index names before the
   sections — first regex captured "、"; fixed by selecting the
   occurrence whose section carries content.
2. Spaced variant: 2020-03 writes "臺灣 50 指數"; regex now allows
   whitespace. 41/41 parse.

## Validation (the keys validate against everything we measured)

- **2026-06 exact match:** adds 3665/3443/8046/4958 = the quartet
  whose 44-71% auction shares we derived from bars; official eff
  "自2026年6月18日交易結束後生效" = the print day the DATA identified
  (Dragon Boat holiday shift) — official text confirms it.
- **Deletion side we never had:** 6919/2002/1301/2207 — our
  cutline residents (2002, 2207!) were June FTSE deletions.
- **History reads true:** the 2021-06 shipping-boom cohort
  (2603/2615/2609 in) and its 2023-09 reversal; Feng Tay's TW50
  arc (in 2019-06, out 2024-03) rhyming with its MSCI story;
  2025-09's 康霈 6919 in → 2026-06 out (a one-review resident —
  churn is real at FTSE too); 7769's 2026-03 entry matching the
  new-listing print our detector flagged.
- Eff dates reproduce known holiday shifts (2018-09-24, 2026-06-18).

## What this unlocks

Both providers now have official answer keys on Taiwan: MSCI 44
quarters (2015-2025, all countries) + FTSE TW50 41 events
(2016-2026 w/ reserve lists — the rank-buffer game's watch zones,
finally gradable against official reserve lists). The rank-engine
backtest (promote-at-40 / relegate-at-61) can now be graded on ~38
quarterly outcomes, and the churn/hazard studies extend to the
FTSE side.
