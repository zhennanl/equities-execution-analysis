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
