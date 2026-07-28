# Index-Event Flow Simulation & Optimal Strategy — Taiwan 50 June 2026

*Session 6z. Part 1: what the two backtests taught the framework.
Part 2: the full order-flow simulation (adds + deletes + weight
adjustments) with per-name optimal execution via the S1–S4 frontier.
New module: `agents/index_flow.py` (6 tests).*

---

## Part 1 — Framework improvements from the two backtests

**Implemented during the backtest cycle (6v–6y):** country-segment
migration rule with calibratable buffer (MSCI deletions 0/7→7/7);
Monte-Carlo `robustness_check`; universe validator with per-market
listing eligibility and boundary-density checks; engine-level suffix
screens; per-name boundary-confidence tags.

**Implemented now (this session):** the flow layer — the screener said
WHO changes; nothing said HOW MUCH trades or HOW to execute it. Fixed
below.

**Remaining roadmap (ordered):**
1. **As-of universe pipeline** (Fix-3 protocol → code): caps from price
   history at the reconstruction date; kills hand-built universes.
2. **Review-type awareness:** Agent 12's calendar drives SAIR-vs-QIR
   hurdles and country-rule activation automatically — today the caller
   chooses.
3. **Multi-cycle buffer calibration:** the 2% country-buffer sweet spot
   came from ONE Feb/May pair; a rolling grade-and-tune loop across
   review cycles makes it a fitted parameter with a confidence interval.
4. **Reserve list as a first-class output** (FTSE): we grade against it;
   we should emit it.
5. **Confidence-weighted flows:** flow × P(change) from the margin tags,
   so the WORK/pre-position decision reflects prediction uncertainty.
6. **Pre-registration on Aug 12** — the standing protocol.

## Part 2 — The flow simulation (Taiwan 50, June 2026, $70B AUM lower bound)

`simulate_index_flow` computes before/after weights for EVERY name —
adds buy in at their new weight, deletes sell out at their old weight,
and all continuing members trim or top up as the denominator moves.

**Checks (arithmetic, not assumptions):**

| Check | Value |
|---|---|
| Gross turnover | **$2.95B** (4.2% of AUM) |
| Buys vs sells | $1.474B = $1.474B — **self-financing gap 0.00%** |
| Reweight share of turnover | **27%** — the flow nobody talks about |

**The headline nobody prices:** TSMC's dilution trim is **−$440M — the
second-largest single flow of the whole event**, bigger than any
deletion. But at 0.08 ADV-days it's a trivial MOC print. Dollar size and
execution difficulty are different axes — the simulation separates them
(bucket = MOC / WORK+MOC / MULTI-DAY by ADV-days).

**Optimal strategy per name** (`recommend_execution`, tracking tolerance
60 bps, frontier path calibrated at 500 bps pressure / 5× T-volume,
η=0.3):

| Flow | Size | Optimal strategy | Why |
|---|---|---|---|
| 4 adds (GUC, ZhenDing, BizLink, NanYaPCB) | ~7.3 ADV-days each | **S3 post-effective 50/50** (541 bps, 42 bps tracking) | buys must NOT pay the pressure peak; S2 pre-position violates participation feasibility (91% of a day); S4 cheapest but 134 bps tracking breaches tolerance |
| 3 deletes (CSC, FormosaPlastics, Hotai) | ~7.4 ADV-days | **S1 100% MOC** (−258 bps, 0 tracking) | the seller RIDES the pressure — selling at the pressured T-close is favorable; the asymmetry emerges from the frontier, not a hand rule |
| 47 reweights | ≤0.08 ADV-days | **S1 100% MOC** | footprint immaterial; take the print |

**The Madhavan asymmetry, reproduced by machinery:** buys into index
pressure should wait or spread; sells into index pressure should take the
crowded print. Nobody coded that preference — it fell out of running the
same frontier on both sides of the same calibrated path. (Tested:
`test_recommendations_and_buy_sell_asymmetry`.)

**Feasibility flag worth quoting:** S2 pre-position for a 7.3-ADV-day add
implies 91% max-day participation — infeasible; even S3 runs 36%. The
real desk answer extends the horizon (multi-week creep) or splits across
the reserve-announcement window — the frontier's participation column is
the tell, and extending S3's `post_days` is the knob.

## Honest boundaries

AUM $70B = 0050 alone (disclosed lower bound; full tracking AUM higher →
scale flows linearly). ADV proxied at 0.4% of cap — real ADV for AI
runners is far higher, so their true ADV-days are LOWER than shown
(direction disclosed). Uniform 0.7 float; path calibration (500 bps/5×)
is literature-shaped, override from the event library as it accumulates
real events. Weight math is Taiwan-50-style FF-cap proportional without
capping rules (Taiwan 50 caps single-name weight in some variants —
TSMC's 54% weight flags exactly why cap rules exist; not modeled,
disclosed).

## Interview one-liner

"My flow simulation prices all three legs of a review — adds, deletes,
and the reweight flows everyone forgets, which were 27% of turnover and
included a $440M TSMC trim. Then the strategy frontier picks per-name
execution, and it reproduced the Madhavan asymmetry on its own: work the
buys, print the sells. Self-financing verified to zero, every assumption
disclosed, and the participation column caught an infeasible
pre-position before a client ever would."
