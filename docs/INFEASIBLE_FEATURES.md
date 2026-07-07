# Why We Can't: Infeasible Features & Their Reasons

*The consolidated answer to "why doesn't this platform do X like the real
thing?" — one entry per institutional capability this project cannot deliver,
with the specific blocking reason, what the project does instead (the honest
mitigation), and what access would unlock it. Companion to
`INSTITUTIONAL_GAP_REGISTER.md` (which tracks status) — this document explains
the* reasons. *Updated 2026-07-08.*

Blocking reasons fall into five categories:

- **[DATA]** — the required data is licensed/paid or simply not distributed
  (tick, order book, auction imbalance, consolidated real-time feeds).
- **[ACCESS]** — requires memberships, connectivity, or relationships only
  institutions have (venue connectivity, dark pools, broker relationships).
- **[COUNTERFACTUAL]** — logically impossible with any historical data: the
  recorded tape did not contain our simulated order, so the market's reaction
  to it can never be replayed, only modeled.
- **[PROPRIETARY]** — the input is other firms' non-public information
  (peer fills, broker algo internals, internalization flow).
- **[SCOPE]** — feasible, but deliberately deferred with reasoning.

---

## 1. Market data limitations [DATA]

| Feature | Why we can't | Mitigation in this project | What would unlock it |
|---|---|---|---|
| **Tick / Level-2+ order-book simulation** (queue position, order-by-order fills, book depth) | Exchange market-data licenses cost $10³–10⁵/yr per venue; no free tick source covers even one of our 15 markets, let alone all | 5-min bars + Bulk Volume Classification for signed flow; fills at bar typical price; square-root impact at bar participation | Vendor feed (BMLL, Refinitiv, Databento) or exchange data agreements |
| **Real-time consolidated quotes** (SIP/proprietary feeds, sub-second) | Real-time redistribution is licensed; yfinance is delayed and rate-limited | The "Live Trading Session" replays *historical* bars on a timer — honest backtest-style playback, labelled as such | Real-time feed subscription + entitlements |
| **Auction imbalance feeds** (MOC/MOO imbalance, indicative price) | Distributed as premium real-time products (e.g. NYSE/Nasdaq imbalance feeds); no free historical archive | MOC/MOO fills print at the close/open with participation vs. an auction-share assumption; effective-day auction stress measured against observed total volume | Exchange premium data products |
| **Intraday history depth** (long intraday backtests) | Yahoo caps 5-min history at ~60 days | Cross-day comparison limited to the available window; daily-bar analytics (event studies, Agent 14) reach further back | Any paid intraday history vendor |
| **Odd-lot / block prints, trade conditions** | Requires trade-condition-coded tick data | Not modeled | Same as tick data |

## 2. Connectivity & venue access [ACCESS]

| Feature | Why we can't | Mitigation | What would unlock it |
|---|---|---|---|
| **Actual order routing** (FIX sessions to venues, co-location) | Exchange memberships, sponsored access agreements, capital, and 15c3-5 controls — institutional infrastructure by definition | Agent 13 simulates routing as expected-cost venue allocation; the FIX panel renders what *would* go on the wire | Broker sponsored access; never realistic for a demo |
| **Dark pools / SIs / conditional venues, IOIs** | Membership- and relationship-gated; fill data is not public | Stylized dark venue with literature-calibrated fill probability and adverse selection (Zhu 2014 direction) | Broker relationships |
| **Real SOR behavior** (live queue estimates, latency-aware, anti-gaming) | Tuned on proprietary fill data; sub-millisecond state | Deterministic expected-fill router — same objective function, no microsecond mechanics | Proprietary fill history + tick data |
| **Block / high-touch channel (RFQ, capital commitment)** | A negotiation workflow between counterparties, not a dataset | Out of scope; noted in capacity analysis when order size warrants it | Being a desk |

## 3. The counterfactual-tape problem [COUNTERFACTUAL]

The deepest limitation, worth stating precisely because no data purchase
fixes it: **the historical tape did not contain our order.** When the
simulator replays a day and "executes" against it:

- Our fills' **impact does not move subsequent bars** — the real market would
  have reacted (permanent impact, opponents' responses, liquidity withdrawal).
  Adding a synthetic permanent-impact drift to the replayed path risks
  double-counting (the tape already contains the impact of whatever real
  orders happened) and creates untestable claims. We therefore charge impact
  as a **cost adjustment** (square-root model + Almgren-2005 cross-check) and
  disclose that the price path itself is exogenous.
- **Fill probability is certain** — in reality a passive slice may not fill;
  our POV/cap constraints model volume-share limits, not queue dynamics.
- **Other participants don't react** — no gaming of our footprint, no
  liquidity provision drawn by our presence.

This is the same limitation every institutional backtest has; desks accept it
and calibrate against *their own realized fills* — which is precisely the
feedback loop (post-trade → model recalibration) that requires being in
production with real orders.

## 4. Proprietary-information features [PROPRIETARY]

| Feature | Why we can't | Mitigation |
|---|---|---|
| **Peer-universe TCA percentiles** (your cost vs. anonymized peers) | Peer fill data is the crown jewel of TCA vendors (Virtu, BestEx, ISS LiquidMetrix) and brokers; never public | Percentile vs. the *stock's own* simulated history (self-relative, labelled as such) |
| **Broker algo internals** (minute-ahead volume/alpha signals, child-order logic) | Trade secrets trained on tick data | Literature-standard schedules (VWAP curve, AC trajectory, POV) — the *public* versions of these algos |
| **Internalization against franchise flow** | Requires being a market-making franchise | Not modeled; noted in the venue register |
| **Real venue fill-quality stats** (fresh, granular) | Rule 605/606 public filings are stale and aggregate; desks use their own fills | Stylized venue parameters, labelled as constants |
| **Algo-wheel league tables across brokers** | Requires routing real flow to multiple brokers | Agent 10's paired backtest + (roadmap) N-arm simulated wheel |

## 5. Deliberately deferred [SCOPE] — feasible, reasoned deferrals

| Feature | Reasoning |
|---|---|
| **Sell-side orders** | Feasible but touches ~25+ sign-sensitive arithmetic/language sites across Agents 3/4/6/10/11 and the UI. A half-migrated sign convention produces *subtly wrong* TCA — worse than a clearly-labelled buy-only tool. Scheduled as a dedicated, test-first migration. (Agent 14 on Page 2 already supports both sides — it was built side-aware from scratch.) |
| **Live-session ticket binding** | The intervention re-planner is the most delicate code in the app; constraints currently bind the static pipeline (Agents 3-6) with an in-app note. Next build. |
| **Multi-day parent orders** | Needs an order-state model across days + overnight gap handling (ties into Agent 7). Register I-10. |
| **Futures overlay for rebalance transitions** | Needs futures data/roll logic; declared out of Agent 14's scope. |
| **Basket-level rebalance execution** | Cross-name crowding interactions need basket data; Agent 14 is single-name with a disclosure. |
| **LLM synthesis layer** | Deliberate architecture stance: deterministic math stays deterministic; agentic reasoning belongs in orchestration/verification, not the P&L path (see PROJECT_CONTEXT.md). |

## 6. Regulatory/operational features with no meaning in a simulator

- **Best-execution regulatory reporting** (MiFID II RTS 28-style, FINRA 606):
  meaningless without real routed flow to report.
- **CAT/audit-trail, surveillance, kill-switch obligations**: obligations of
  registered entities, not simulations. The compliance module deliberately
  simulates the *pre-trade* checks (restricted list, fat-finger, overrides)
  because those change trader behavior, which a simulator can teach.
- **Clearing/settlement (T+1 affirmation, fails, locates inventory)**:
  post-trade operations requiring counterparties. The short-locate *check*
  will ship with sell-side support as a flag.

---

## The one-paragraph answer

Everything computable from free daily/5-minute public data is computed and
tested; everything requiring licensed data, institutional access, or
proprietary information is either simulated with a clearly-labelled
statistical model (venues, auctions, fills) or declared out of scope here.
The single limitation no budget fixes is the counterfactual tape: a
simulator's order never moves a market that already happened — which is why
this platform charges impact as a disclosed model cost rather than pretending
the tape reacts, and why real desks calibrate on their own fills instead of
backtests alone.
