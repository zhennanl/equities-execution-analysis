# Step-2 Window Study — China A / Japan / Hong Kong, May-2026 MSCI Cohorts
*Session 9d. 39 names; formulas identical to the Taiwan study (WINDOW_STUDY §0); announcement 2026-05-12 post-close, print 2026-05-29; PIT baselines pre-announcement only.*

> **REVISION (session 9h, decade study):** the one-event caveat below
> did its job. Extending the same framework to 367 print-validated
> name-events 2015-2025 (WINDOW_STUDY_DECADE_CNJPHK.md), the CLASS
> INVERSION found here does **not** generalize: decade CN adds grind
> up TW-style (working beats the print, LINEAR −234 median) and
> decade deletes show no press-to-print. The May-2026 pop-then-decay
> reads as late-regime or event-specific — hold the MSCI-add WAIT
> rule as a hypothesis until Aug-2026 grades it. Decade-scale
> additions: CN prints are material for only ~25% of names
> (10–20% IF vs a retail-heavy tape); the JP edge flipped sign after
> 2022 (the Greenwood-Sammon disappearance arriving in Asia).

## 1. Per-market data limitations (stated first)

| Market | Quotes | Crowding at vintage | Foreign flow |
|---|---|---|---|
| CN-A | baostock daily (official-grade, years) | ABSENT — margin data walled; northbound holdings = queued fetcher | ABSENT (same) |
| JP | yfinance daily | ABSENT at May vintage — JPX site retains ~1 month; our archive starts Jul-2026 | weekly aggregates only (structural) |
| HK | yfinance daily | **RECONSTRUCTED — the SFC page lists all 724 weekly files back to 2012** (the HK crowding pillar is historical!) | CCASS (future fetcher) |

## 2. Execution counterfactuals vs the T-close (median bps; negative = beat the close)

|                |   LINEAR |   LATE5 |   EARLY30_MOC70 |   ALL_DAY1 |
|:---------------|---------:|--------:|----------------:|-----------:|
| ('CN', 'Buy')  |      336 |     -80 |             271 |       1103 |
| ('CN', 'Sell') |     -192 |    -326 |            -136 |       -614 |
| ('HK', 'Buy')  |      765 |     379 |             395 |       1453 |
| ('HK', 'Sell') |     -306 |     -78 |            -286 |      -1097 |
| ('JP', 'Buy')  |     -402 |     132 |             -52 |        633 |
| ('JP', 'Sell') |      -50 |     -34 |              -7 |        -71 |

## 3. OUT-OF-SAMPLE test of the Taiwan A+3 rule (sign rule, no re-fit)

|                 |   LINEAR |   LATE5 |
|:----------------|---------:|--------:|
| ('Buy', False)  |      336 |      43 |
| ('Buy', True)   |      448 |     695 |
| ('Sell', False) |     -219 |     -45 |
| ('Sell', True)  |     -210 |     -79 |

*(A3_hot = favorable drift at session 3 > 0 — the rule as exported from Taiwan, applied unchanged to MSCI-class flows in three other markets.)*

## 4. HK vintage crowding (SFC weekly, base week 20260508)

| name    |   20260410 |   20260417 |   20260424 |   20260430 |   20260508 |   20260515 |   20260522 |   20260529 |
|:--------|-----------:|-----------:|-----------:|-----------:|-----------:|-----------:|-----------:|-----------:|
| 1138.HK |        1.8 |       -5.4 |       -1.5 |       -9.8 |          0 |       -1.9 |       -1.2 |       17.3 |
| 9995.HK |       -4.2 |       -3.9 |        6   |        2.3 |          0 |       -9.4 |      -10   |       -2.9 |
| 0177.HK |        0.6 |        0.5 |        2.2 |        1.6 |          0 |        0.5 |       -0.5 |      -45.1 |
| 0772.HK |       -7.3 |       -3.7 |        0.8 |        2.5 |          0 |       -4.2 |       -5.9 |      -33.6 |
| 1066.HK |        5.5 |        0.9 |        8.2 |       -1.5 |          0 |       -2.1 |        2.9 |      -55.2 |
| 1357.HK |       -8.6 |       -4.7 |       -2   |       -1.1 |          0 |       -0.5 |       -2.9 |      -27.1 |
| 2357.HK |       19.7 |       13.6 |        4.3 |        3.4 |          0 |       -3.5 |       -7.5 |      -41.7 |
| 2799.HK |        4.7 |       -0.3 |       -0.5 |        0.4 |          0 |        0.8 |        0.9 |      -45.1 |
| 9899.HK |        5.2 |        0.4 |       -0.2 |        2.1 |          0 |       -4.3 |      -15.9 |      -50.4 |
| 0004.HK |       -1.6 |       -3.4 |       -0.2 |        1.6 |          0 |       -5.1 |      -14.1 |      -71.2 |

*(% change in aggregated reportable short positions vs the last pre-announcement week — the weekly-cadence crowding read, at vintage.)*

## 5. Cross-market synthesis — the MSCI-class window INVERTS the Taiwan playbook

**The Taiwan (FTSE-class) lessons do NOT transfer — and the
inversion is systematic, which makes it a finding, not noise:**

| Lesson | Taiwan FTSE-class (6 events, 38 names) | MSCI-class May-2026 (CN/HK, this study) |
|---|---|---|
| Adds | drift builds ALL window; buy day-1 = **−630** (early wins) | announcement-day overshoot then DECAY; buy day-1 = **+1103 (CN) / +1453 (HK)** — day-1 buys the pop's top; WAIT/MOC wins |
| Deletes | fall early, RECOVER into print; MOC best | keep pressing to T; sell early = **−614 (CN) / −1097 (HK)**; working wins |
| A+3 momentum gate | separates ±500 bps, dominates | **FAILS OOS on adds** (hot +448 vs cold +336 — mean-reversion after the pop); no separation on deletes |

**Mechanism hypothesis (consistent with everything measured):**
MSCI events carry 16x flows and a professional arb ecosystem — the
add pop is priced WITHIN THE ANNOUNCEMENT SESSION and then decays
as arbs distribute; FTSE-class events (5x, more domestic) leak in
gradually, so momentum persists. Delete-side: MSCI's larger flow
presses prices to the print; FTSE deletes finish early and bounce.
**Execution playbooks must be EVENT-CLASS-CONDITIONAL**: provider x
tracked-AUM class is a first-order input to the discretion matrix,
ahead of the A+3 gate.

**Caveats, stated:** ONE MSCI event (the 66-deletion May-2026 SAIR,
one tape regime); JP's milder pattern (adds LINEAR −402, deletes
~flat) hints market-level variation within the class; close-fill
counterfactuals are impact-free upper bounds. Cross-event
replication (Aug-2026 + the archived future events + alias-bridged
history) is the designed confirmation path before any rule ships.

