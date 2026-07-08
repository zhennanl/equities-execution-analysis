# Institutional Feature Gap Register — Execution Platform

*Living document. Tracks (a) what a production institutional execution platform
(e.g. what a bank's electronic trading desk offers clients) includes, (b) which
of those this project already models, (c) which it could realistically simulate
with free data, and (d) which are deliberately out of scope because they require
institutional access — kept here so the boundary is explicit and demonstrably
understood, not overlooked.*

*Last updated: 2026-07-08*

---

## 1. Reference model — the institutional order lifecycle

How a parent order actually flows through a bank's electronic trading stack:

1. **Order arrival (OMS → EMS).** The PM's order originates in an Order
   Management System (allocation, account, restrictions), then is staged to an
   Execution Management System where the trader works it. Orders carry FIX
   fields: side, quantity, order type (Tag 40), time-in-force (Tag 59), limit
   price, target strategy (Tag 847), strategy parameters (participation cap,
   start/end time, aggression).
2. **Pre-trade compliance & risk checks.** Restricted/watch list, position and
   fat-finger limits, short-sale locate requirement, market-abuse screens —
   all *before* anything is routed.
3. **Pre-trade analytics.** Expected cost/impact curves vs. execution horizon,
   liquidity profile (ADV, spread, depth), risk (volatility, event calendar),
   capacity ("days to trade"), strategy recommendation.
4. **Strategy & venue selection.** Choice of algo (VWAP/TWAP/POV/IS/Liquidity-
   seeking/Close), its parameterization (urgency, participation cap, dark/lit
   preference, display quantity, would-price), and routing constraints (venue
   include/exclude lists). Many desks randomize comparable orders across
   algos/brokers via an **algo wheel** to generate unbiased performance data.
5. **Smart order routing (SOR).** The parent is sliced into child orders routed
   across lit exchanges, MTFs/ECNs, dark pools, systematic internalisers, and
   periodic auctions — optimizing for fill probability, fees/rebates, queue
   position, and information leakage, with anti-gaming logic.
6. **In-flight monitoring (the EMS blotter).** Fill rate vs. schedule,
   slippage vs. arrival/interval VWAP/PWP, real-time participation, venue-level
   fill quality, alerts (behind schedule, limit breached, toxicity spike,
   unusual reversion), and trader intervention: pause, re-parameterize,
   switch strategy, cancel/replace, kill switch.
7. **Post-trade TCA & best execution.** Multi-benchmark TCA, implementation-
   shortfall attribution (delay / trading / opportunity / fees), venue analysis
   (effective spread, price improvement, markouts/adverse selection), peer-
   universe percentile comparison, regulatory best-ex reporting, and a feedback
   loop into future strategy selection (wheel re-weighting).

---

## 2. Covered by this project today

| Institutional function | Where it lives here |
|---|---|
| Pre-trade cost/impact estimates, capacity table, spread estimate | Agent 6 (pre-trade), Almgren-2005 cross-check, Corwin-Schultz |
| Market condition assessment / regime | Agent 2 (vol, volume shape, variance-ratio trend) |
| Strategy simulation across 8 algo types | Agent 3 (look-ahead-bias-free schedules) |
| Cross-day strategy comparison + size sensitivity + efficient frontier | Agent 4 |
| Rule-based strategy recommendation + independent review | Agents 5, 8 |
| Event risk (earnings in horizon) | Agent 7 |
| Microstructure toxicity/impact estimation | Agent 9 (Kyle's λ, VPIN via BVC) |
| In-flight monitor with interventions (algo/urgency/benchmark switches, re-plan of residual) | Live Trading Session (Agent 11 + `simulate_with_interventions`) |
| Live re-recommendation ("Reconsider" flag) | Agent 5 re-fire in live session |
| Post-trade multi-benchmark TCA, percentile vs. history, reversion, perm/temp decomposition | Agent 6 (post-trade) |
| A/B strategy testing (paired backtest = algo-wheel analog) | Agent 10 (hypothesis testing) |
| Venue selection & SOR (statistical simulation) + venue TCA | Agent 13 (`agent13_venue_router.py`) — stage 2 of the pre-trade workflow |
| Index-event execution analytics | Module 2 + Agent 12 (rebalance calendar/changes) |
| Rebalance best-execution strategy simulation (cost vs tracking-error frontier, S1-S4) | Agent 14 (`agent14_rebalance_strategist.py`) + `docs/INDEX_REBALANCE_RESEARCH.md` |
| **Research-grounded microstructure & client analytics**: EDGE effective-spread estimator (Ardia-Guidotti-Kroencke, JFE 2024) as a 3rd cross-check; Amihud (2002) illiquidity; intraday volume seasonality (U-shape); ACF + Ljung-Box time-series tests; Asia price-limit bands (China/Korea/Taiwan/Vietnam/Thailand/Indonesia) with pre-trade flag; closing-auction concentration; client benchmark scorecard + client-ready one-pager | `agents/microstructure_analytics.py`, `agents/asian_markets.py`, `agents/client_analytics.py` + Page-1 "Microstructure & Client Analytics" — shipped 2026-07-08 (see `docs/MICROSTRUCTURE_RESEARCH_IMPROVEMENTS.md`) |
| **Fitted transaction cost model** (regression TCA): OLS cost curve `cost~sqrt(size%ADV)+vol+participation+spread+duration` with White HC1 / Newey-West HAC robust SEs, F-test, Durbin-Watson / Breusch-Pagan / Jarque-Bera diagnostics, predicted-vs-realized benchmark, and **A/B-with-controls** (strategy dummy net of confounders) | `agents/cost_model.py` + `agents/cost_panel.py` + Page-1 "Cost Model — TCA Regression" — shipped 2026-07-08 (directly serves the GSET consultant role; see `docs/GSET_ROLE_AUTOMATION_ANALYSIS.md`) |
| Regression test suite + CI over the analytics kernels (pins the hand-verified anchors: cap→fill, limit→opp cost, wick convention, S1-S4 costs, YZ/CS/AR estimators, routing, explicit costs, alerts) | `tests/` (offline pytest, 64 tests + recorded AAPL integration fixture) + `.github/workflows/tests.yml` — shipped 2026-07-08 |

---

## 3. Implementable gaps (roadmap candidates — free data suffices)

| # | Feature | Institutional analog | How we'd simulate it |
|---|---|---|---|
| I-1 ✅ *(shipped 2026-07-07: limit/window/cap/auction-gating/must-complete; iceberg display qty deferred to venue layer. Live-session cap+limit binding shipped 2026-07-08 (B3); side-aware Buy/Sell shipped 2026-07-08 (B2))* | **Institutional order ticket**: limit price, start/end time window, max participation cap, min-fill / must-complete constraint, MOC/MOO auction participation flags, display quantity (iceberg), would-price | FIX strategy parameters on every algo order | Extend order inputs + Agent 3 schedule logic; constraints bind the simulated fills (e.g. no fills through limit; participation cap throttles POV) |
| I-2 ✅ *(shipped 2026-07-07: Agent 13 — per-market venue sets, 4 routing policies, deterministic expected-fill model, spread input capped at 15 bps with disclosure)* | **Simulated venue & SOR layer**: stylized venue set (primary exchange, 2 ECN/MTF-like lit venues, 1 dark pool, closing auction) with per-venue spread/fee/fill-probability/adverse-selection parameters; child orders allocated by a simple SOR policy | Smart order router + venue network | Parameterize venues from literature (fee tiers, dark midpoint fills, markout profiles); allocate each 5-min slice's shares across venues; report venue-level fills |
| I-3 ✅ *(shipped 2026-07-07: per-venue shares, spread cost, fees, adverse selection, price improvement, net cost + policy comparison)* | **Venue-level TCA**: fill rate, effective spread capture, price improvement, post-fill markouts by venue | Venue analysis page of any TCA suite | Direct extension of I-2's simulated fills |
| I-4 ✅ *(shipped 2026-07-08: EMS-style alert blotter in the live session — completion pace, participation breach, limit state, toxicity, benchmark slippage; pure-function rules, unit-tested)* | **Alerting engine** on the live monitor: behind-schedule, participation-breach, limit-breach, toxicity-spike, reversion alerts with severity levels | EMS alert blotter | Threshold rules over the existing live metrics (Agent 11 outputs); UI badge/log with acknowledge |
| I-5 | **Full IS attribution** in post-trade: delay cost / trading cost / opportunity cost / explicit fees, reconciling to total shortfall | Standard TCA decomposition (Perold framework) | Mostly re-arrangement of existing numbers + a fee model (I-6) |
| I-6 ◐ *(partial 2026-07-08: side-aware per-market commission/fee/stamp-tax table (`agents/explicit_costs.py`) reported in pre-trade per TCA convention; maker-taker per-venue lives in Agent 13. Remaining: fold into full IS attribution I-5)* | **Explicit costs model**: commissions, exchange fees/rebates (maker-taker), taxes/stamp duty per market | Commission schedules, fee engines | Static per-market fee table; feeds I-2 and I-5 |
| I-7 | **Algo wheel module**: randomized strategy assignment across historical days, league table with statistical significance | Broker algo wheels | Generalize Agent 10's paired framework to N-arm randomized comparison |
| I-8 | **Parent/child order visualization**: planned vs. actual execution schedule timeline, child slices with venue tags | EMS order detail view | Plotly timeline of Agent 3/11 slice data (+ I-2 venue tags) |
| I-9 ✅ *(shipped 2026-07-07)* | **Pre-trade compliance simulation**: restricted-list check, fat-finger (size vs. ADV cap), short-locate flag | OMS pre-trade checks | Small rule engine + demo restricted list; blocks the run with an override flow |
| I-10 | **Multi-day parent orders**: order > 1 day of capacity carried across days with per-day TCA and cumulative IS | Multi-day working orders | Extend Agent 3/4 to chain days; opportunity cost across overnight gaps (ties into Agent 7) |
| I-11 ✅ *(shipped 2026-07-07)* | **FIX-style order representation**: internal order object mirroring FIX tags (40, 59, 847, 848, 6062...) shown in an "order details" panel | FIX protocol messaging | Cosmetic-but-credible: render the order as its FIX field set; no network layer |

## 4. Institution-only capabilities (tracked, deliberately not implemented)

*These require data, connectivity, or entitlements that only institutions have.
Listed so the boundary is explicit — each entry notes what access it would take.*

**Market data**
- **Tick-by-tick / Level-2+ order book data** (full depth, order-by-order) — needed for real queue-position modeling, true VPIN/flow toxicity, realistic fill simulation. Requires exchange data agreements (or vendors: Refinitiv/Bloomberg/BMLL). *We approximate with 5-min bars + Bulk Volume Classification.*
- **Real-time consolidated feeds** (SIP + proprietary feeds) with sub-second latency. *Our "live" session replays historical bars.*
- **Auction imbalance feeds** (MOC/MOO imbalance, indicative price) — semi-public with delays but not free in real time. *Relevant to Module 2's closing-auction analytics.*

**Connectivity & routing**
- **Actual venue connectivity**: FIX sessions to exchanges/MTFs, co-location, exchange memberships. *Our venue layer (I-2) is a statistical simulation, not routing.*
- **Real SOR**: live queue estimates, latency-aware routing, rebate optimization, anti-gaming logic tuned on proprietary fill data. *(I-2 ships the statistical analog: expected-cost venue allocation with stylized parameters — the objective function is real, the microstructure mechanics are not.)*
- **Dark pools / systematic internalisers / conditional venues** (e.g. bank-run ATSs), IOIs, and conditional order types. Access is membership/relationship-gated; fill quality data is proprietary.
- **Block/high-touch channel**: RFQ, capital commitment, IOI negotiation — a workflow, not just data.
- **Internalization** against the bank's own flow (retail/market-making) — the economics that only a sell-side franchise has.

**Order & risk infrastructure**
- **OMS integration**: allocations, account hierarchies, compliance rules per mandate, locates inventory for shorts.
- **Pre-trade credit/risk checks** against real limits (15c3-5 market-access controls); firm-wide kill switch with regulatory obligations.
- **Clearing & settlement** (T+1 affirmation, fails management, CSDR penalties).
- **Audit trail & surveillance**: CAT/OATS-style reporting, market-abuse surveillance, order-record retention.

**Analytics & benchmarking**
- **TCA peer universes** (anonymized cross-client fills from vendors/brokers) — our "percentile vs. history" is self-history only, not peer-relative.
- **Broker algo suites** and their proprietary signals (short-term alpha, minute-ahead volume forecasts trained on tick data).
- **Real venue fill-quality stats** (Rule 605/606 filings are public but stale and aggregate; desks use their own fill data).
- **Best-execution regulatory reporting** (MiFID II RTS 28-style, FINRA 606 client disclosures) — meaningless without real routing.

**Scope**
- **Futures overlay for rebalance transitions** (gain index exposure via futures while legging into stock, per transition-management practice) — needs futures data/rolls; declared out of scope for Agent 14.
- **Basket-level rebalance execution** (whole add/delete basket with cross-name crowding interactions) — Agent 14 is single-name; the basket/crowding disclosure note in Module 2 covers the caveat.
- **Sell-side orders** — ✅ *shipped 2026-07-08 (B2): `side_sign` convention in `order_ticket.py`, signed slippage/opportunity/tracking and a side-aware limit gate across Agents 3/4/6/11, plus a short-locate compliance BLOCK; verified by a Buy/Sell mirror-property test (a Sell on path P equals a Buy on 2·P0−P) across all 8 algos and the Agent-4 fast path. Agent 14 was already side-aware. The UI now carries a Buy/Sell selector + short-locate checkbox (FIX Tag 54), and constraints bind both the static pipeline and the live session. Window-in-live-session binding is the only remaining refinement.*
- **Multi-asset support** (futures hedging overlays, options, FX legs for cross-border settlement).
- **Entitlements/permissioning, client onboarding, SLAs** — platform plumbing.

---

## 5. How to talk about this bounda