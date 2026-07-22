# Execution Algorithm Simulator — Institutional-Quality Assessment

*2026-07-08. Page 1 (Execution Algorithm Simulator) assessed against what a
bank's electronic-trading stack actually provides, stage by stage of the order
lifecycle. Companion to `INSTITUTIONAL_GAP_REGISTER.md` (the feature inventory)
— this document is the QUALITY judgment and the productivity design on top of
it. Two gaps identified here were closed in the same session (see §4).*

---

## 1. Verdict up front

The simulator's analytical core is at or near institutional methodology on
free data: the algo suite (8 strategies, look-ahead-bias-free schedules,
Almgren-Chriss IS trajectory), the TCA stack (multi-benchmark, reversion,
permanent/temporary decomposition, now full Perold IS attribution), the
fitted cost model with robust SEs and A/B-with-controls, and the microstructure
estimators (Kyle's λ, VPIN/BVC, CS/AR/EDGE spreads, Amihud) are the same
methods a desk's quant group uses — with honest disclosure where free data
forces approximation. What separates it from institutional quality is not the
math but four things: **data fidelity** (5-min bars vs ticks — fills, queue
position and VPIN are approximations), **the counterfactual-tape problem**
(simulated fills don't move a real market; impact is modeled, and now clearly
labelled as a memo item in the IS attribution), **workflow packaging** (an
analyst's read, not yet a trader's blotter — Page 2 got this layer first),
and **feedback loops** (no persistent order history powering wheel
re-weighting or peer benchmarks). The first two are data-access facts to
disclose, not fix; the last two are design work this document specifies.

## 2. Stage-by-stage: current vs institutional quality

| Lifecycle stage | Institutional platform | This simulator today | Quality gap that matters |
|---|---|---|---|
| Order ticket & compliance | OMS: FIX-tagged ticket, restricted list, fat-finger, locate | I-1/I-9/I-11 shipped: full ticket incl. side/locate/window/cap/limit, compliance blocks, FIX panel | Small: window not yet enforced in live session; iceberg display qty deferred |
| Pre-trade analytics | Cost curves vs horizon, capacity, risk, event calendar — delivered as a one-page pre-trade report | Agent 6 + Almgren-2005 cross-check + capacity table + Agent 7 earnings + Agent 2 regime | Content parity; PACKAGING gap — numbers spread over sections vs the desk's single pre-trade card (see P-A below) |
| Strategy & venue selection | Algo wheel with randomized assignment + league table; SOR | Agent 5 rule-based + Agent 8 critic; Agent 13 statistical venue layer; Agent 10 pairwise A/B | The wheel (I-7): N-arm randomized comparison with significance is the industry's evidence engine — highest-value missing analytics |
| In-flight monitoring | EMS blotter: pace, participation, alerts, intervene | Agent 11 live session + I-4 alert blotter + interventions | Volume re-forecast missing (B4): desks re-plan on realized volume; ticket window not binding per leg |
| Post-trade TCA | Multi-benchmark, IS attribution (delay/trading/opportunity/explicit), venue TCA, peer percentiles | All present — IS attribution shipped THIS session (I-5), reconciling ±0.1 bp by construction; percentile is self-history | Peer universes are institution-only (disclosed); multi-day orders (I-10) still single-day |
| Feedback loop | Wheel re-weighting, cost-model refits on own fills | Cost model exists; no persistent order/run history to refit on | Same design as Page 2's event library — a RUN LIBRARY (P-C below) |

## 3. What actually produces trader productivity & insight (ranked designs)

**P-A ✅ (shipped 2026-07-08). Pre-trade desk card + verdict-first layout.**
One screen after the pipeline runs: side/size/urgency, recommended algo +
critic flags, expected cost ± the fitted model's CI, capacity ("days to
trade"), event-risk line, explicit-cost line — exportable as text/CSV like
Page 2's trade card. The institutional analog is the pre-trade report every
desk attaches to a parent order. *Productivity: minutes → seconds to a
decision; insight unchanged but reachable.*

**P-B ✅ (shipped 2026-07-08 in the quant-review pass — see QUANT_REVIEW_ADDITIONS.md). Algo wheel (I-7).** Generalize Agent 10 to N-arm: randomized strategy
assignment across historical days, Friedman/Nemenyi or bootstrap ranking,
league table with significance stars, fed by the cost model's
condition-controls so the ranking is net of size/vol/spread. *Insight: the
defensible answer to "which algo should be my default for this profile?" —
the exact question wheels exist to answer.*

**P-C ✅ (shipped 2026-07-08: `agents/desk_pack.py` run library — predicted-vs-realized bias/MAE displayed under the verdict). Run library.** Persist
every pipeline run (ticker, conditions, chosen algo, realized vs predicted
cost) → predicted-vs-realized tracking error over time, cost-model refits on
accumulated runs, percentile vs own history that survives restarts.
*Insight: the simulator starts learning; the GSET-consultant deliverable
("expected-cost benchmark per order") gets its data source.*

**P-D ✅ (shipped 2026-07-08: `agent11.live_volume_forecast` — run-rate vs curve, projected day volume, POV completion projection in the live session). Live volume re-forecast (B4).** Blend the historical curve with
realized volume-so-far; show "volume running 138% of expected — completion
projected 14:40 vs 15:55 plan"; re-plan the residual. *Productivity: the
single most-used number on a live blotter.*

**P-E. Multi-day parent orders (I-10)** — chain days with overnight-gap
opportunity cost and cumulative IS; unlocks realistic >1-day-capacity orders
and makes the IS attribution's delay component span days. *Insight: capacity
answers stop being single-day fictions.*

**P-F. Small polish with outsized credibility:** enforce the ticket window in
the live session per leg; fold EDGE into Agent 6's blended pre-trade spread
(will shift displayed numbers — document when done); side-aware captions;
split app.py into page modules (reduces the P-A edit-hazard permanently).

## 4. Closed this session (code shipped, tests green)

- **I-5 Full IS attribution** (`build_is_attribution` in agent6 + waterfall
  UI): canonical Perold decomposition — delay (decision→first fill), trading
  (first fill→avg px, share-weighted), opportunity (unfilled at close),
  explicit (per-market fees × fill fraction) — reconciling to the
  share-weighted shortfall within 0.1 bp BY CONSTRUCTION, asserted across all
  8 algos × both sides (`tests/test_is_attribution.py`, 5 tests). The
  dashboard's headline "total cost" (unweighted slippage + modeled impact) is
  a different convention on partial fills — the attribution note says so, and
  the modeled sqrt-law impact is displayed as a memo item because simulated
  fills don't embed it. That distinction is exactly the counterfactual-tape
  honesty the platform is built around.
- **I-8 Parent/child order detail** (EMS-style view): child slices per bar +
  cumulative completion overlay + schedule table, per executed algo.

Suite: 142 → 147 passed. PostTradeTCA gained `is_attribution` as a defaulted
trailing field (P-E backward-compat convention); no pinned anchor moved.

## 5. How to talk about the remaining boundary

Same stance as everywhere in this repo: the math is institutional; the tape
is not. Fills are simulated against historical bars that our own trading
could not have moved, so impact is a model, clearly labelled, cross-checked
three ways (η=0.3 sqrt-law, Almgren-2005 power law, Kyle's λ), and now kept
OUT of the reconciled IS attribution rather than blended into it. A desk
would swap the data layer and keep the methodology — which is the same
feasibility argument as `INSTITUTIONAL_PLATFORM_PROPOSAL.md` §2.
