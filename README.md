# Execution Analytics Platform

An agentic equity execution-analysis platform built with Python and Streamlit. Two modules: a pre/intra/post-trade execution algorithm simulator, and an index-rebalancing event study with execution-cost extensions. Runs entirely on free Yahoo Finance data (`yfinance`) — no API key, no paid feed.

## Module 1 — Execution Algorithm Simulator

Given a ticker and an order (size as % of ADV, urgency, benchmark target), a pipeline of specialist agents assesses market conditions, simulates 8 execution algorithms against real intraday data, and produces a recommendation with pre-trade, post-trade, and microstructure analytics.

**Algorithms simulated:** VWAP, TWAP, POV, Implementation Shortfall (Almgren-Chriss optimal trajectory), Market-on-Close, Market-on-Open, Liquidity-Seeking, Stealth.

**Agent pipeline** (orchestrated by `agents/orchestrator.py`, sharing state via the `ExecutionContext` blackboard in `agents/context.py` — each agent runs, skips, or fails independently rather than the whole request hard-stopping on one error):

| Agent | Role |
|---|---|
| 1 — Market Data | Fetches 5-min intraday + 60-day daily OHLCV, computes ADV, annualized realized vol, intraday volume profile |
| 2 — Market Regime | Classifies intraday volatility (vs 20d median), volume pattern (U-shaped/uniform/midday-heavy), and price trend via the Lo-MacKinlay (1988) variance ratio test |
| 3 — Algorithm Simulation | Runs all 8 algos for the current order on the most recent complete trading day; look-ahead-bias-free (VWAP/MOC/MOO schedule off a leave-one-out historical volume curve); reports slippage, square-root-law market impact, Perold (1988) opportunity cost on unfilled shares, and fill rate per algo |
| 4 — Performance Comparison | Re-simulates all algos across every available historical day (not just one) for a robust average, plus a full order-size sensitivity grid and the Almgren-Chriss cost/risk efficient frontier |
| 5 — Recommendation | Rule-based primary/secondary algo pick and risk flags, given regime + simulation + comparison outputs, urgency, and the client's stated benchmark target |
| 6 — Pre-Trade / Post-Trade | Pre-trade: Corwin-Schultz (2012) spread estimate, days-to-complete capacity table, P10/P50/P90 expected cost range, Almgren et al. (2005) calibrated impact cross-check. Post-trade: multi-benchmark TCA (Arrival/VWAP/TWAP/Close), cost percentile vs. history, impact-reversion check, permanent/temporary impact decomposition |
| 7 — Earnings Calendar | Flags overnight gap risk when a scheduled earnings print falls inside the order's execution horizon |
| 8 — Critic | Independent second pass over Agent 5's pick — checks fill-qualification and earnings-date risk without silently overriding the recommendation |
| 9 — Market Microstructure | Kyle's Lambda (price impact per unit signed order flow) and VPIN (order-flow toxicity), both estimated via Bulk Volume Classification on 5-min bars since no tick/order-book feed is free at this granularity |

**Mid-Session Adjustment (interactive intervention):** real buy-side desks monitor fills on a GSET/REDIPlus-style blotter and can intervene mid-session. This is modeled directly: pick the algo that ran before a checkpoint, drag to any bar mid-session, choose a new algo/urgency for the remainder, and apply. Everything before the checkpoint is sliced from the already-computed original schedule (not re-simulated); only the unfilled remainder is re-planned and blended into one result, shown against the "no intervention" baseline. Backtest-style — same historical bars replayed under a hypothetical intervention, not a live feed.

**Supported markets (14):** US, Taiwan (TWSE), Hong Kong (HKEX), Japan (TSE), Korea (KRX), Singapore (SGX), China-A (Shanghai & Shenzhen), India (NSE), Australia (ASX), Thailand (SET), Indonesia (IDX), Malaysia (KLSE), Vietnam (HOSE).

## Module 2 — Index Rebalancing Analysis

Event study of price and volume dynamics around an index constituent addition/removal, using the market-model (OLS) approach to compute Cumulative Abnormal Returns and abnormal volume over a user-specified window around the effective date. Extends into execution-specific insights:

- Closing-auction volume concentration
- Post-event reversal classification (transient / partial / permanent / momentum)
- Pre-announcement vs. pre-effective drift decomposition
- Flow-to-trade estimator (index weight change × tracked AUM)
- Event-day impact (eta) recalibration
- Basket/crowding disclosure note
- Objective-aware recommendation (Cost-Minimizing vs. Index-Tracker mandates)

## Design notes

- **Data is disclosed, not idealized.** A sidebar panel ("Data Sources & Limitations") and inline captions throughout the app state exactly what's measured vs. approximated — e.g. Kyle's Lambda/VPIN are bar-level approximations of tick-level concepts, MOC/MOO are volume-curve approximations of real auction mechanics, since no free order-book or trade-print feed exists at intraday granularity across these 14 markets.
- **Agents are independent and composable**, not a fixed monolithic script — see `PROJECT_CONTEXT.md` for the full multi-agent design write-up, including what a genuinely LLM-driven version of this pipeline would add on top of the current rule-based logic.
- **Look-ahead bias is actively guarded against**: VWAP/MOC/MOO schedules are built from a leave-one-out historical volume curve rather than the simulated day's own (unknowable, in real time) volume; Kyle's Lambda regresses next-bar returns on this-bar's classified flow rather than a contemporaneous (circular) regression.

## Roadmap

- **Hypothesis testing on execution parameters** — a planned feature to let users define two configurations (algo/urgency/order size) and run a formal paired significance test (paired t-test + Wilcoxon signed-rank + bootstrap CI) on whether one significantly beats the other, reusing the multi-day paired simulation data Agent 4 already computes. Design proposed; not yet implemented.

## Running locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Tech stack

- **Data:** [yfinance](https://github.com/ranaroussi/yfinance) (free Yahoo Finance data, no API key)
- **UI:** Streamlit
- **Charts:** Plotly
- **Analysis:** pandas, NumPy — statistical/rule-based agents (variance ratio test, Corwin-Schultz, Bulk Volume Classification, Almgren-Chriss), not LLM-backed

## Repository structure

```
app.py                              # Streamlit UI — Page 1 (simulator) + Page 2 (rebalancing)
agents/
  agent1_market_data.py             # Market data fetch, ADV, realized vol, volume profile
  agent2_market_regime.py           # Volatility / volume / trend regime classification
  agent3_algo_simulation.py         # 8-algorithm single-day simulation + mid-session switch
  agent4_performance_comparison.py  # Multi-day comparison, sensitivity grid, AC frontier
  agent5_recommendation.py          # Rule-based recommendation memo
  agent6_pretrade_posttrade.py      # Pre-trade estimate + post-trade TCA
  agent7_earnings_calendar.py       # Earnings-date gap-risk flag
  agent8_critic.py                  # Independent recommendation review
  agent9_microstructure.py          # Kyle's Lambda, VPIN, Almgren impact cross-check
  rebalancing_event_study.py        # CAR/abnormal-volume event study + execution insights
  orchestrator.py                   # Runs Agents 2-9, conditional skip/fail handling
  context.py                        # Shared ExecutionContext ("blackboard") state
PROJECT_CONTEXT.md                  # Full design philosophy, methodology, and sourcing notes
requirements.txt
```
