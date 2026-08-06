# Variable Lab — Hypothesis Registry (LOCKED BEFORE EVALUATION)

*Session 9i (2026-08-04). This registry is written BEFORE the
evaluation harness runs — the acceptance criteria below cannot move
after results are seen (the Indonesia-watch-line discipline).
Framework: PRE_ANNOUNCEMENT follow-on, window = announcement ->
effective. Unit: name-event-day panel (WINDOW_STUDY §0 formulas),
PIT-gated via time_machine. Evaluation is event-clustered: a
variable's effective n is EVENTS, never name-days.*

## Acceptance criteria (fixed now, for all hypotheses)

- **ADOPT**: |effect| >= 50 bps AND direction holds in >= 65% of
  events AND sign survives leave-one-event-out AND n_events >= 6.
- **REJECT**: sign unstable across events (LOO flips) or direction
  holds in < 55% of events with n_events >= 6.
- **NULL-PIN**: |effect| < 25 bps with n_events >= 8 — pinned as a
  test like the violence-curve null.
- **DATA-GATED**: insufficient events to grade — stated, re-run as
  coverage grows. No verdict.
- Class-conditioning: each hypothesis is evaluated WITHIN
  provider-side cells first (FTSE/MSCI x Buy/Sell); pooling only if
  the within-cell signs agree.
- Effects are measured in bps of REMAINING favorable drift (day k ->
  T close, sign = with-flow) unless the hypothesis names another
  target. Split rule: above/below the event-side median of the
  variable at the stated decision day.

## The hypotheses

| ID | Variable (PIT at day k) | Decision moment | Target | Pre-declared direction |
|---|---|---|---|---|
| H1 | **Front-run completion**: cumulative excess volume since ann (Σ(vol-baseline)) / expected flow shares, at k=5 | D2 participation | remaining fav drift k=5 -> T | HIGH completion -> LESS remaining drift (obligation pre-traded; close part-spent) |
| H2 | **Crowding build**: short balance %-build since ann, at rk=-3 | D3/D4 envelope | remaining fav drift rk=-3 -> T | For DELETES: HIGH build -> remaining drift LESS favorable (covering bounce into print — the 6919 mechanism) |
| H3 | **A+3 momentum** (formal in-class re-test): fav drift over first 3 sessions | D1 pre-position | remaining fav drift k=3 -> T | POSITIVE momentum -> MORE remaining drift IN-CLASS (FTSE); expected to FAIL cross-class (MSCI) — the OOS lesson, now registered |
| H4 | **Foreign coverage**: cumulative foreign net flow (with-flow sign) / expected flow, at k=5 | D2 | remaining fav drift k=5 -> T | HIGH coverage -> LESS remaining drift (the tracked channel already moved) |
| H5 | **Cohort lag**: name's fav drift minus event-side median drift, at k=5 | D2 ordering | remaining fav drift k=5 -> T | LAGGARDS (below median) -> MORE remaining drift (convergence into the print) |
| H6 | **Early volume surge**: mean t_mult over k<=3 | D3 auction sizing | T-day print t_mult | HIGH early volume -> SMALLER T print multiple (flow pulled forward) |
| H7 | **EXITING tag** (crowding built then unwound >=15% off peak) by rk=-3 | D4 | remaining fav drift rk=-3 -> T | EXITING flips H2: exited crowd -> print behaves UNCROWDED |
| H8 | **Borrow utilization** (SBL bal/(bal+quota)) at rk=-5, deletes only | D3 | T print gap magnitude | HIGH utilization -> LARGER print dislocation (squeeze fuel) — DATA-GATED expected (quota coverage thin) |

## Known priors entering the lab (not re-litigated)

Crowding->print-character and A+3-in-class are ADOPTED with scope
restrictions from prior graded work; auction-share->gap is NULL
(pinned); ~45% of deletions carry no price signal (ladder stays
primary — this lab is about EXECUTION timing, not membership calls).

## Sample (at lock time)

Full five-pillar TW panels cached for ~8 events; backfill queue
targets ~12-14 (FTSE 2021-06/09, 2023-09, 2024-03, 2025-12,
2026-03/06 + MSCI 2025-08/11, 2026-02/05 + best-effort 2024-25
FTSE). Anything below n_events=6 in a cell reports DATA-GATED.
Aug-2026 is the standing out-of-sample event for every verdict.

## Registry v2 (session 9i — LOCKED before evaluation, intraday hypotheses)

New data: full ann->eff 5m coverage incl. per-day auction bars for
24 events post the 2023-05 IB floor. Criteria for v2: same
event-clustering, LOO, and n>=6 rules; effect units per hypothesis.

| ID | Variable (PIT at day k) | Target | Pre-declared direction | ADOPT threshold |
|---|---|---|---|---|
| H9 | WINDOW-DAY auction share (per name, per day) | late-window (rk >= -3) minus early-window (k <= 3) mean share | For DELETES: share RISES toward T (the crowd migrates to the closes as the print nears) | abs diff >= 0.05 share, winrate >= 65%, LOO-stable |
| H10 | PM drift concentration: fraction of each day's favorable drift occurring after 13:00 | late minus early window, in bps of PM fav drift | PM-session drift GROWS toward T (positioning concentrates at day-ends) | >= 50 bps, winrate >= 65%, LOO-stable |

H6 (carried from v1, criteria gap fixed): early volume surge ->
print t_mult, threshold now in t_mult UNITS: ADOPT if abs diff >=
3.0x with winrate >= 65% and LOO-stable.

## Registry v3 (session 9i — LOCKED before evaluation): PRE-ANNOUNCEMENT ANTICIPATION

Question: does individual-stock tape behavior BEFORE the announcement
carry information about upcoming index changes — i.e., does the
market front-run the announcement itself?

CONFOUNDER STATED UP FRONT: for ADDS, price momentum mechanically
CAUSES the change (cap crosses the threshold), so pre-announcement
drift is NOT evidence of anticipation. The clean tests are
(a) abnormal VOLUME (drift-orthogonal) and (b) DELETES, where ~45%
are coverage-arithmetic with no mechanical tape cause — any
systematic pre-announcement signal there is genuine anticipation.
Control = each name's OWN earlier baseline (within-name design;
cross-name controls impossible without historical PIT universes —
stated limitation: this measures anticipation EXISTENCE, not
incremental predictive power over the cap ladder, except where
watch-zone cohorts exist (TW) for a conversion test).

| ID | Variable | Window | Target/test | ADOPT threshold |
|---|---|---|---|---|
| H11a | Abnormal volume: mean(day vol, ann-10..ann-1) / mean(day vol, ann-30..ann-11), DELETES only | pre-announcement | > 1 systematically (event-clustered vs 1.0) | ratio >= 1.25, winrate >= 65%, LOO, n_events >= 6 per market cell |
| H11b | Same, ADDS (reported w/ confounder caveat; volume may still be momentum-driven) | pre-announcement | same | same, interpretation guarded |
| H12 | Close-hour volume share shift, ann-10..ann-1 vs baseline (do anticipators use the closes?) | pre-announcement | share rises | +0.03 abs share, winrate >= 65%, LOO |

Cells: per market (HK, CN-A) x side; TW joins for 2023+ only (IB
floor). Aug-2026 announcement (Aug-11) is the standing OOS event.

### v3 pre-run refinement (2026-08-04, BEFORE any evaluation — data
### not yet fetched)

CN events May18 / May19 / Nov19 are INCLUSION-TRANCHE events: their
additions were pre-announced months-to-a-year ahead (the Jun-2017
inclusion plan and the 2019 factor step-ups), so the review
announcement was not the information event. These events are
FLAGGED: H11b (adds) is reported both with and without them, and
the without-tranche cell is the primary. H11a (deletes) is barely
affected (0-1 deletes in those events). Harvest keeps them — the
windows still serve execution studies.

## Registry v4 (session 9i c-56 — LOCKED before evaluation)

| ID | Variable (PIT at T-1) | Target | Pre-declared direction | ADOPT threshold |
|---|---|---|---|---|
| H16 | COMPOUND: window flow-completion >= 1.5x expected AND foreign-flow direction INCONSISTENT with the side | abs(T+1..3 reversal) | compound cell reverses HARD (panel evidence n=2: mean 17.8% vs 4.6% base — registered, NOT adopted) | mean abs rev >= 10% with n_events >= 5, event-clustered, LOO-stable; graded on every future event starting Aug-2026 |

Panel basis: data/liquidity_panel_tw.json (133 name-events, 33
events, 2015-2026). Declared thresholds 0.3/0.7/1.2 EVALUATED
(first full-history grade): completion -> t_mult MONOTONE
(8.3/12.9/19.8/21.1x) = the effective-date volume forecaster;
mean reversals flat across buckets; event-level corr NEGATIVE
(-0.43) = well-supplied closes are orderly. Scenario table's
VOLUME semantics ADOPTED; its reversal semantics REVISED to the
compound cell (H16).

### v4 addendum (c-65 — registered from the pattern study, LOCKED)

| ID | Variable (PIT at T-1) | Target | Pre-declared direction | ADOPT threshold |
|---|---|---|---|---|
| H17 | Foreign net-outflow intensity over the window (deletions) | T+3 favorable bounce | harder foreign selling -> bigger bounce (study: rho -0.200, p 0.21 — REGISTERED not adopted) | abs(rho) >= 0.25 with clustered perm-p <= 0.05, n_events grows past 35; graded from Aug-2026 |

NULL PINNED (c-65): mean effective-day RETURNS are unpredictable
from daily window features (9 tests null; LOO-event ML 0.52-0.56
vs 0.66 base). Future return-prediction claims must beat this
study's clustered bar. Volume prediction (completion -> t_mult)
re-confirmed rho 0.347 p 0.002.

## Registry v5 (session 9i c-69, 2026-08-05 — LOCKED BEFORE the
## harvesters finish; NONE of the new datasets has been evaluated)

Written while margin/daytrade/blocks/SBL/T86 histories are still
downloading. Directions, mechanisms, and thresholds declared NOW
so the data cannot tune them. Targets reuse the panel's outcome
set (t_mult, close dislocation, T+1..3 reversal/bounce); all
variables PIT at T-1 unless noted.

| ID | Dataset | Variable (PIT T-1) | Target | Pre-declared direction & mechanism | ADOPT threshold |
|---|---|---|---|---|---|
| H18 | MI_MARGN | Margin-LONG balance / float (deletions) | T-day return + T+1..3 drift | High retail leverage into a delete = weak hands forced out -> worse T-day, more downside follow-through | abs(rho) >= 0.25, clustered perm-p <= 0.05, n >= 35 |
| H19 | MI_MARGN | Margin-SHORT balance BUILD over window / expected demand (deletions) | completion, squeeze incidence | Retail short build = borrow-supply channel parallel to SBL (CH1 complement) -> higher completion, fewer squeezes | direction holds in both halves of era split + clustered p <= 0.05 |
| H20 | TWTB4U | Baseline day-trade ratio (60d pre-announcement) | abs(close dislocation), T+1 reversal | High toll-collector capacity (CH3) = deeper intraday provision -> smaller dislocation, smaller reversal | abs(rho) >= 0.25, clustered perm-p <= 0.05 |
| H21 | TWTB4U | T-day day-trade ratio spike vs baseline | share of print absorbed intraday vs at close | Day-traders recycle inventory intraday -> spike names print relatively less at the close | descriptive first; ADOPT only if quartile contrast >= 10pp with n >= 35 |
| H22 | BFIAUU | Window block volume / expected passive demand | t_mult, completion | Pre-arranged crossing moves demand off-tape -> lower forced close print, higher measured completion | abs(rho) >= 0.25, clustered perm-p <= 0.05 |
| H23 | TAIFEX SSF | SSF OI build in window (event names) | completion residual, squeeze incidence | Synthetic pre-positioning (CH3.5) invisible to cash data -> high OI build lowers true squeeze risk | LOG-ONLY: capture-forward n=1 at Aug-2026; no test before n >= 5 events. Declared so the direction is on record |
| H24 | T86 | Dealer-prop net window flow (signed) / expected demand | completion, T+1..3 reversal | The direct arb footprint: dealer accumulation against the side = positioned for the bounce -> larger reversal when dealers lean in | abs(rho) >= 0.25, clustered perm-p <= 0.05 |
| H25 | T86 | H16's foreign leg REBUILT from signed daily flow (replacing holding-delta proxy) | abs(T+1..3 reversal) | Same compound direction as H16; signed flow should SHARPEN the cell, not create it — if the effect vanishes under better data, H16 is downgraded, not defended | H16's own threshold, regraded on signed flow |
| H26 | cross | CROWDING INDEX: standardized sum of SBL balance build + margin-short build + dealer-prop flow + (when n allows) SSF OI build, per expected demand | completion residual from the lambda model | The residual we named "crowding" becomes measured: index should explain >= 20% of residual variance | OOS R^2 >= 0.10 on 2023+ after fitting 2015-2022; else REGISTERED not adopted |

Underpowered-by-design, stated: H23 (n=1 until events accrue);
H21 needs the 5-min legs (2023+ only, n~30 name-events). SBL fee
rates: no hypothesis registered — variable does not exist yet
(registering one would invite fishing once a source appears; the
original borrow-COST hypothesis enters as H27 only when a fee
series is in hand, BEFORE evaluating it).

### v5 quick reference (one line per hypothesis)

| ID | Dataset | Claim (direction declared) |
|---|---|---|
| H18 | Margin long | Leveraged retail = weak hands -> worse T-day + follow-through on deletes |
| H19 | Margin short | Retail short build = borrow supply parallel to SBL -> higher completion, fewer squeezes |
| H20 | Day-trade | High toll-collector capacity -> smaller close dislocation, smaller reversal |
| H21 | Day-trade | T-day spike shifts print from close into session |
| H22 | Blocks | Window block volume = demand crossed off-tape -> smaller forced close print |
| H23 | SSF OI | Synthetic pre-positioning lowers true squeeze risk — LOG-ONLY (n=1 until 5 events) |
| H24 | T86 dealer-prop | Arb desks leaning against the side -> bigger bounce |
| H25 | T86 foreign | H16 rebuilt on signed flow — if the effect vanishes under better data, H16 is downgraded |
| H26 | Composite | Crowding index should explain >= 20% of the lambda-model residual, OOS |

### v5 methods protocol (fixed now — how findings get graded)

1. FAMILY-WISE HONESTY: v5 is one family of 8 tests. Report raw
   AND Benjamini-Hochberg-adjusted p (q=0.10). A hypothesis
   ADOPTS only if it passes its own threshold AND survives BH.
2. INFERENCE: event-clustered block permutation (2,000 draws,
   the pattern-study machinery) — never naive iid p-values;
   Spearman primary (monotonic, outlier-robust).
3. EFFECT SIZE FIRST: every result reported as effect size +
   bootstrap CI (resampled BY EVENT); p alone never adopts.
4. TEMPORAL OOS: fit/threshold on 2015-2022, validate 2023-2026;
   LOO-event where n is small. Aug-2026 is the standing
   out-of-sample event for everything.
5. INCREMENTAL VALUE TEST: new variable enters a regression with
   the controls we already have (ln size, side, float-days, era)
   — it must improve on the lambda-model residual, not merely
   correlate with outcomes the old variables already explain.
6. POWER BEFORE TESTING: n~77 deletions -> 80% power at
   |rho|~0.31. Hypotheses below power are graded REGISTERED /
   INDETERMINATE, never "suggestive".
7. NULLS GET PINNED: any v5 miss is written into this registry
   and, where mechanical, pinned as a test — the c-65 return-
   prediction null remains the bar any return claim must beat.
8. NO POST-HOC PROMOTION: patterns noticed outside this table go
   into a v6 registry and wait for the NEXT data vintage.
