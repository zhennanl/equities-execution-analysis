# Taiwan Review Backtest — First Slice (2025-2026), Iteration Log

*Session 8u. The opening slice of the 2015->now program. Honest
scope up front: full-depth backtesting is gated by ANSWER KEYS
(historical MSCI/FTSE lists are not sandbox-fetchable; TIP is a
manual-collection path) and UNIVERSE BREADTH (16 real names with
share counts). This slice: 3 MSCI TW events (Aug-25 QIR, Nov-25
SAIR, Feb-26 QIR) + the known May-26 SAIR as out-of-sample check —
keys reconstructed by a VALIDATED event-print detector where
official lists don't exist.*

## The answer-key problem, and the detector

MSCI historical lists: only Feb/May-2026 held. Solution: reconstruct
keys from the official tape — true Standard-index changes print
unmistakably on the effective close. Detector iterations, each
graded against KNOWN keys:

| It | Rule | Result | Verdict |
|---|---|---|---|
| 1 | t-mult >=6, value >= NT$1B | recall 4/4 (Feb) + 7/7 (May), 6 false+ | recall solid, precision poor |
| 2 | t-mult >= 12 | Feb clean — but **REJECTED out-of-sample**: 3 true May deletions printed 8.4-11.9x | the tune failed exactly the way in-sample tunes fail |
| 3 | t>=6 AND value >= NT$4B (Standard names live near the GMSR -> big prints) AND limit-locked names tagged SUSPECT (a +-10% lock = news) + ETF codes excluded | **Feb: exactly the 4 true deletions; May recall 7/7 preserved** | adopted; precision bound measured |

Reconstructed 2025 keys: **Aug-25 QIR: {2395} (weak single, flat
print — quiet QIR); Nov-25 SAIR: {8033 delete; 7769 new listing =
fast-entry class; 2316 SUSPECT}.** Quiet reviews — consistent with
the May-26 SAIR being the batch cleanup.

## The prediction iterations

| It | Change | Aug-25 QIR | Nov-25 SAIR |
|---|---|---|---|
| (setup) | vintage caps = close(vintage) x shares(current)/FX; ff from cache; membership back-rolled through Feb changes; count anchor 86 | | |
| 3 | SAIR-style migration at all reviews | **10 false deletions** | 9 deletions flagged |
| 4 | **Review-cadence rule**: the deep coverage-migration sweep is SAIR business; QIRs execute only extreme breaches (0.5x floor + screens). Documented MSCI cadence — the Feb-26 QIR's real deletions were all sub-floor (Feng Tay 0.38x), consistent | **0 false deletions** | 9 flagged (SAIR — stands) |

## The finding that reframes deletion calls: flag-to-deletion hazard

The Nov-25 SAIR "over-flags" were not wrong — they were EARLY:
**6 of the 9 flagged members were deleted at the very next SAIR
(May-26), and the 3 survivors (1101/1326/2207) are precisely the
cutline residents every graded run has false-flagged.** MSCI batches
boundary cleanups (quiet reviews, then the 66-deletion May wave);
a coverage breach is therefore a HAZARD, not a date. Measured on
this cohort: ~2/3 conversion per SAIR, ~1/3 persistent residents.
Deletion output is hereby formally a hazard-ranked watch zone with
a measured conversion rate — the number the client conversation
has needed all along.

## Where iteration honestly stops (this slice)

Remaining misses are not tunable: 2395/8033 sit below the 16-name
universe floor (fix = universe breadth: more share counts, more
names); 7769 is the fast-entry class (different detector — the
CA/IPO radar); deeper history needs TIP/MSCI key collection (manual
path) and degrades on share-count drift past ~2-3y. The 2015 sweep
continues as data collection, not as rule iteration.

## Scorecard (this slice, all events)

| Event | Truth source | Engine result |
|---|---|---|
| Aug-25 QIR | reconstructed (weak) | 0 calls — matches quiet review; 2395 below universe floor, ungradable |
| Nov-25 SAIR | reconstructed | 9-flag watch zone -> 6 converted next SAIR (hazard measured); in-window hits 0 (keys below floor) |
| Feb-26 QIR | OFFICIAL | detector 4/4; prediction rule consistent (all true deletions sub-floor class) |
| May-26 SAIR | OFFICIAL | 7/7 deletions + 1/1 add at PIT (the graded run) |
