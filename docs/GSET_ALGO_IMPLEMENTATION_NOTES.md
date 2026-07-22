# GSET Algorithm Suite — Public Implementation Notes & Our Analogs

*2026-07-09. Everything below is compiled from PUBLIC sources — The TRADE's
GSET guide, Goldman's GSET pages, and press releases — which describe
behavior at the marketing/spec level, never internals. This doc summarizes
what each algorithm does per those sources, maps it to this platform's
analog, and records the two documented behavioral traits adopted into our
code this session. Where the public record is thin, that is stated rather
than embellished.*

**Sources:** [The TRADE — GSET guide](https://www.thetradenews.com/guide/goldman-sachs-electronic-trading-gset/) ·
[GS — GSET Equities](https://www.goldmansachs.com/what-we-do/ficc-and-equities/gset-equities) ·
[Business Wire — Sonar Dark X launch, Oct 2022](https://www.businesswire.com/news/home/20221004005155/en/Goldman-Sachs-Launches-Liquidity-Seeking-Algorithm-Sonar-Dark-X-on-Atlas-Trading-Platform)

## 1. The suite, by family

**Benchmark matching** — trade on a schedule over a period, tracking a
benchmark while minimizing market and impact risk.

- **VWAP** — slices proportional to the expected intraday volume curve;
  tracks the day's volume-weighted average price. *Our analog:* `_sim_vwap`,
  with the look-ahead-bias rule (curve from prior days only) as a hard
  invariant.
- **TWAP** — equal slices across time; used when curves are unreliable or a
  constant footprint is preferred. *Our analog:* `_sim_twap` (also the
  parity workhorse in the live-binding tests).
- **Implementation Shortfall** — targets the arrival price; front-loads per
  an impact-vs-timing-risk trade-off with an urgency dial (Almgren-Chriss
  lineage). *Our analog:* `_sim_is` with a true AC trajectory (κ·T scaling
  by urgency).
- **Scaling** — public record: price-conditional scaling in/out at levels.
  *Our analog:* none (price-triggered scaling is an order-type layer we
  haven't built; the ticket's limit gate is the nearest primitive).

**Participation-based** — track a percentage of composite market volume
**"while ignoring outsized prints"** (the one implementation detail the
public description volunteers).

- **Participate** — POV follower with the outsized-print filter and urgency
  → participation-rate mapping. *Our analog:* `_sim_pov` — and as of this
  session it implements the documented filter: each bar's participation
  base is capped at 3× the trailing-median bar volume (causal window), so a
  block print can't drag the follower into chasing inaccessible liquidity.
  **[TRAIT ADOPTED — tested: `test_pov_ignores_outsized_prints`]**

**Price & liquidity seeking** — access liquidity in public and dark venues
(or dark only) based on price, minimizing information leakage.

- **Sonar** — lit + dark opportunistic liquidity capture; supplements dark
  liquidity with lit per the user's urgency. *Our analog:*
  `_sim_liquidity_seeking` (price-conditioned participation tilt) with the
  venue dimension living in Agent 13's statistical SOR.
- **Sonar Dark / Sonar Dark X** — dark-only; the Atlas launch release is
  the richest public spec in the suite: a **liquidity scoring framework**
  over distinct ATS segments, plus **"Liquidity Shield" logic** that reduces
  parent-order information leakage by *"balancing the liquidity quality and
  capture objectives throughout the life of the order by dynamically
  adjusting among distinct combinations of venue segments, minimum execution
  quantities and spread allowances."* *Our analogs:* venue scoring ≈ Agent
  13's historical-fill-quality venue ranking (same objective, statistical
  simulation); and as of this session `_sim_liquidity_seeking` implements a
  Liquidity-Shield-style balance: selectivity on price early and on-pace,
  relaxing as the order falls behind pro-rata pace — quality first, capture
  when completion risk compounds. Side-symmetric, causal.
  **[TRAIT ADOPTED — tested: `test_liq_shield_relaxes_when_behind_schedule`]**
  Minimum-execution-quantity logic is NOT replicated (meaningless at 5-min
  bar granularity; requires fill-level simulation).
- **Stealth** — minimal-footprint execution designed to avoid signaling.
  *Our analog:* `_sim_stealth` already carries the anti-gaming essentials:
  hard per-bar participation cap plus seeded randomized child sizing with
  iceberg-style carry-forward. No change needed — the trait predated this
  review.

**Specialists & meta-strategies** (public record is thin; summaries only):

- **SmallCap** — tuned for illiquid names (wider spreads, lumpy volume).
  *Our analog:* none as a distinct algo; the regime/spread inputs condition
  parameters instead. Honest gap.
- **SpreadTrader** — pairs/spread execution with leg-risk management. *Our
  analog:* none (multi-leg execution is out of scope; noted in the
  infeasible-features register).
- **Port X** — portfolio/basket execution. *Our analog:* the program-desk
  blotter and wave plan cover the pre-trade layer; simultaneous basket
  *execution* with risk balancing is not simulated.
- **Navigator / 1CLICK** — per the public description, the "customized"
  family "leverages historical execution quality to select the most
  appropriate strategy based on order and security characteristics" — i.e.
  meta-selection. *Our analog is real:* Agent 5's rule-based recommendation
  + the condition-adjusted ranking + the wheel are exactly
  selection-from-measured-performance; ours recommends to a human rather
  than auto-routing (the critic-pattern stance).
- **Listed-options algos (Pegging, Volatility Limit, Strike)** — out of
  scope (equities-only platform).

**Infrastructure:** every algo's children route via the SOR (venue choice
from historical execution statistics; anti-gaming and dynamic price-limit
logic) with the Sigma X dark-pool family among venues, on the Atlas
platform. *Our analog:* Agent 13 (statistical venue layer, disclosed as a
simulation of the objective function, not the microstructure mechanics).

## 2. What was changed in our code (and what deliberately wasn't)

| Change | Where | Source trait | Guard |
|---|---|---|---|
| POV outsized-print filter (3× trailing-median cap, causal) | `_sim_pov` | Participate description | New test; no pinned anchor touched; mirror property unaffected (side-independent) |
| Progress-aware selectivity relaxation | `_sim_liquidity_seeking` | Sonar Dark X "Liquidity Shield" | New test; side-symmetric (mirror suite passes); causal |

Deliberately unchanged: IS (the AC trajectory is a pinned methodological
anchor; adaptivity would be speculation beyond the public record), Stealth
(trait already present), MOC/MOO (auction conventions are pinned), and
anything requiring fill-level granularity (minimum quantities, venue-segment
switching) or data we don't have (ATS segment scoring). Suite: 197 → 199
passed, all prior anchors intact.

## 3. The honest boundary, one paragraph

Public descriptions specify objectives and occasional behavioral details;
they never specify signals, parameters, or logic. Everything adopted here is
a documented *behavior* (ignore outsized prints; balance quality vs capture
over the order's life) implemented with our own disclosed mechanics — not a
claim of replicating GSET internals. Where a named GSET algorithm has no
analog here, the table says so instead of stretching one.


---

## SOR & dark pool incorporation (session 6d)

**What Agent 13 already covered.** A statistical SOR: per-market venue tables
(lit/dark, fee, addressable volume share, fill probability, spread capture,
adverse selection), expected-cost ranking, and a per-bar dark-first-then-lit
sweep under four policies (Cost-optimized / Lit-only / Dark-preferred /
Primary-only). Single-venue markets (China A, Taiwan) correctly degrade to
primary-only. This is routing *in expectation* — fill_prob scales allocations
rather than simulating fill-by-fill randomness.

**What was added — "Shield (dark-patient)" policy.** Inspired by the
publicly documented Sonar Dark X "Liquidity Shield" (quality vs. capture
balance): for the first 50% of the schedule (`SHIELD_PATIENT_FRAC`), the
residual after dark pings CARRIES FORWARD to the next bar instead of sweeping
lit. No spread crossed and nothing displayed early; completion risk is
deliberately pushed later, with a full lit sweep guaranteed from the patience
boundary onward (share conservation holds — tested). Effects visible in
`compare_policies`: higher % dark and lower blended cost on wide-spread
tapes, tested at half-spread 10 bps.

**Honest boundaries (fill-level realism we do NOT claim):**
- No minimum-quantity / min-acceptable-quantity logic — needs order-book data.
- No ATS segmentation or counterparty scoring (the real Liquidity Shield's
  core) — needs proprietary fill attribution; ours is a bar-level expected
  behavior analog only.
- Adverse selection is a static per-venue bps parameter, not measured from
  markouts on our own fills — the calibration path is the markout module,
  once real fills exist.
- No IOI handling, no conditional orders, no sweep vs. post decision.

**How the pieces now connect end-to-end:** flow forecast (L1–L6b) predicts
whether liquidity will be there → algo simulation schedules the parent →
Agent 13 routes each bar's child shares across venues under a chosen policy
→ TCA/markouts measure what it cost. The quantile head (L6b P10) is the
natural input to the Shield patience decision — thin expected tape argues
for less patience — wiring that in is a listed future step, not implemented.
