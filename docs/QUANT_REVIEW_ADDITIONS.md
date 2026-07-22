# Quant Review — Statistics & Microstructure Additions (2026-07-08)

*Critical review of both tools from two lenses — (1) statistics, (2) market
microstructure — identifying what an experienced institutional practitioner
would look for and not find, followed by what was implemented in this pass.
All five additions shipped with deterministic tests (suite 147 → 160 passed).*

---

## 1. The review

### Lens 1 — Statistics

**What was already strong.** The cost model is a properly-specified regression
(HC1/Newey-West robust SEs, F-test, BP/DW/JB diagnostics); A/B testing is
paired with a controls variant; the regime model uses a formal variance-ratio
test; the whole suite is pinned by regression tests.

**What a practitioner would notice missing:**

1. **The event study reported point estimates with NO inference.** A CAR of
   −6% is meaningless without knowing whether normal co-movement could produce
   it. Institutional/academic convention (Brown-Warner 1985; Patell; the BMP
   refinement) standardizes AR by the estimation-window residual variance with
   a forecast-error correction. → **Shipped:** `event_inference()` — per-day
   AR t-stats and a cumulative CAR σ; the CAR chart now carries a ±1.96σ null
   band and the key-day table a "CAR t" column. Honesty note displayed:
   event-induced variance (the BMP critique) makes the band anti-conservative
   ON event days — it is guidance, not a hard test; with one firm there is no
   cross-section to aggregate.

2. **Pairwise A/B answers the wrong daily question.** Desks don't ask "is A
   better than B"; they run 6–8 algos and ask which are *jointly*
   distinguishable and which are separable from the leader — the algo wheel
   (gap I-7/B6). → **Shipped:** `agents/algo_wheel.py` — Friedman χ² across
   the day-blocked cost matrix (all algos on the SAME days = fully blocked
   design, stronger pairing than a live randomized wheel), Nemenyi critical
   difference on average ranks, league table with "Separable from best?"
   verdicts, rank bar chart with the CD line. Small-n honesty: "not separable"
   is the correct reading, stated in the output notes.

3. Remaining (documented, not built): multiple-testing control if the wheel
   is re-run across many configs (BH correction), quantile cost regression
   (tail cost, not mean cost), and out-of-sample walk-forward validation of
   the fitted cost curve.

### Lens 2 — Market microstructure

**What was already strong.** Kyle's λ, VPIN via BVC, three spread estimators
(CS, AR, EDGE 2024), Amihud, intraday seasonality, permanent/temporary impact
decomposition, reversion diagnostics, Asia market mechanics (price limits,
lunch sessions, auction concentration).

**What a practitioner would notice missing:**

4. **No markout curve.** Post-fill markouts at multiple horizons are THE
   standard fill-quality/adverse-selection tool on every desk and at every
   market maker. → **Shipped:** `compute_markout_curve()` — share-weighted
   signed drift from each child fill to +5/10/15/30/60 minutes (bar-close mid
   proxy, disclosed), rendered as the classic decay curve in Post-Trade TCA
   with a rising-vs-reverting interpretation. Sell-side mirror pinned by test.

5. **Spread cross-check lacked the classic.** Roll (1984) is the estimator
   every practitioner knows; its failure mode (positive serial covariance on
   trending samples → undefined) is itself diagnostic. → **Shipped:**
   `roll_spread()` as the 4th row of the cross-check table, with the
   undefined case reported honestly (eps-guarded against numerical zeros).

6. **The rebalance tool measured the event but not the regime change.**
   Inclusion/deletion changes comovement (Barberis-Shleifer-Wurgler 2005) and
   liquidity (Hegde-McDermott 2003) — a desk updates hedge ratios and expects
   different completion costs post-event. → **Shipped:**
   `compute_liquidity_shift()` — pre (estimation window) vs post (T+1 onward,
   min 8 days) beta, EDGE spread, and Amihud, as an insights panel with the
   hedge-ratio/completion-cost reading and a short-window caveat.

7. Remaining (documented, not built): impact-decay propagator fit (Bouchaud
   "double sqrt" — backlog research direction), realized-vol signature plot,
   and venue-level markouts (needs the Agent-13 venue simulation joined to
   the markout engine — natural next step).

## 2. What shipped where

| Addition | Module | UI | Tests |
|---|---|---|---|
| Event-study inference (AR t, CAR σ band) | `rebalancing_event_study.event_inference` (+ trailing `EventStudyResult` fields, P-E convention) | Page 2: CAR chart band + "CAR t" summary column | anchors on the closed-form variance |
| Algo wheel league table | `agents/algo_wheel.py` | Page 1: new section before Cost Model | Friedman detection, Nemenyi CD formula, indistinguishable-arms note, guards |
| Markout curve | `microstructure_analytics.compute_markout_curve` | Page 1: Post-Trade TCA | drift anchor, sell mirror, fills-at-close guard; sparse-schedule alignment by `time` |
| Roll (1984) spread | `microstructure_analytics.roll_spread` | Page 1: cross-check table 4th row | iid-bounce recovery (±10%), trend-undefined |
| Post-event liquidity/beta shift | `rebalancing_event_study.compute_liquidity_shift` (+ trailing field) | Page 2: insights panel | beta-change detection, min-post-days guard |

Runtime verified beyond unit tests: `run_event_study` exercised end-to-end
with a monkeypatched data layer (summary carries CAR t; inference arrays and
liquidity shift populate; an ordering bug — inference computed after the
summary consumed it — was caught this way and fixed before shipping).

## 3. Sources

- Brown & Warner (1985); Patell (1976); Boehmer-Musumeci-Poulsen (1991) —
  event-study inference conventions: [eventstudytools significance tests](https://www.eventstudytools.com/significance-tests)
- Roll (1984) — implied spread from serial covariance of price changes.
- [Databento — markouts as the standard fill-quality/adverse-selection tool](https://databento.com/microstructure/markout) · [QuestDB markout cookbook](https://questdb.com/docs/cookbook/sql/finance/markout/)
- [Virtu — Algo Wheel: a systematic, quantifiable approach to best execution](https://www.virtu.com/wp-content/themes/virtu-2019/microsite/documents/virtu-algowheel-2019.pdf) · [Bloomberg — automation, TCA and broker wheels](https://www.bloomberg.com/professional/insights/trading/how-automation-tca-and-broker-wheels-work-together-in-modern-equity-ems/)
- Demšar (2006) — Friedman + Nemenyi for comparing algorithms over data sets
  (the CD formula used here).
- Barberis, Shleifer & Wurgler (2005) — comovement; Hegde & McDermott (2003)
  — liquidity after index inclusion.
