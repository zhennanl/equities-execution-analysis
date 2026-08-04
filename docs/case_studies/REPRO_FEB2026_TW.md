# Retro Reproduction — MSCI Feb-2026 QIR, Taiwan (official TWSE history layer)
*Session 8t. First retrospective run on the backfill layer: pre-announcement crowding (TWT93U history), event-day T-multiples (official all-stock quotes), and foreign-flow color (TWT38U) — no yfinance anywhere. Names from the official Feb change ledger (incl. Feng Tay, the name whose stale-membership lesson built the verification gate).*

|   name | side   | pre_ann_crowding   |   event_t_mult |   window_foreign_net_Mshares |
|-------:|:-------|:-------------------|---------------:|-----------------------------:|
|   2354 | ADD    | MED (+21%/22obs)   |            0.9 |                          5.4 |
|   2105 | DELETE | MED (+20%/22obs)   |           25.6 |                         41.9 |
|   1476 | DELETE | LOW (-1%/22obs)    |           24.8 |                         -0.4 |
|   9910 | DELETE | HIGH (+33%/22obs)  |           21.1 |                         -0.5 |
|   8464 | DELETE | LOW (-4%/22obs)    |           21.3 |                          1.9 |

**Reads:** (1) The implementation print was FEB 26 — Feb 27 was a holiday; the tape, not the calendar, identified the day (third time this pattern has caught a date: Jun 18, May 29 CN, now Feb 26). (2) The 'HONPRECISION' -> 2354 alias candidate is EMPIRICALLY REJECTED: no event print in 2354 — the add's ticker remains unmapped, honestly (alias verification by event-day volume is now a reusable technique). (3) The foreign-net column SURPRISED us — the hypothesis ('delete-side foreign net negative') is CONTRADICTED for 2105: +41.9M shares of foreign BUYING into the deletion print — the column reveals who takes the OTHER side (the arb/value bid absorbing tracker sells), not a mechanical sell signature; 1476/9910 mildly negative. Recorded as found. (4) T-multiples land inside the measured 7-38x band. The retrospective engine runs on official data alone — next: sweep 2015-2026 (~40 reviews) to grow every prior from n=8 to n=hundreds. Window note: TWSE's CNY break (Feb 12-22) compressed the trading window to ~9 sessions.

## Why the lookback starts at 2015

The framework's lookback is set by its SHALLOWEST required input,
not its deepest. The pillars have different depths — official
daily quotes reach back ~two decades, the 5-second market/auction
archive serves 2012+, outcome lists are public 10+ years — but the
CROWDING layer binds everything: the TWT93U short-balance file (and
TWT38U foreign flows) verify from 2015, reflecting Taiwan's
mid-2010s expansion of short-sale/SBL disclosure. Any analysis that
needs the positioning read — crowding bands, the discretion matrix,
CONSENSUS/UNPRICED grading — therefore starts at 2015.

Two qualifications, stated precisely: (1) 2015 is VERIFIED-AT, not
proven-first — we probed 2015-05-15 successfully and have not
binary-searched earlier; the true floor may be somewhat deeper.
(2) Partial stacks go further back: T-multiple and flow studies
(daily data only) reach ~2005+, market-wide auction studies 2012+ —
only the FULL five-layer replication is 2015-bound. ~40 review
cycles at full fidelity is the honest number.
