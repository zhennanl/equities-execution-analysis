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

**Live Trading Session (time-lapse playback with agents synced to the clock):** real buy-side desks watch fills and slippage-vs-benchmark intraday on a broker execution-management-system (EMS) blotter, and intervene — potentially more than once — if the algo is behaving suboptimally. This is modeled as an actual time-lapse rather than a static scrub bar: press **Play** and the session advances bar-by-bar on a timer (Slow/Normal/Fast), or step/scrub manually and pause at any point. As it plays, every panel recomputes using ONLY the bars observed so far — not the full, already-known day every other section on the page is based on:
- **Market Regime** and **Microstructure** (Kyle's Lambda, VPIN) re-run live, truncated to the elapsed session (prior historical days stay whole; only *today* is cut off at the playback position)
- **Pre-Trade** re-underwrites the Almgren (2005) impact estimate and capacity table for whatever's still unfilled, not the original full order
- **Agent 5's selection rule re-fires** against the live regime and flags "Reconsider" the moment it would no longer pick the original algo, with the specific regime shift that changed (e.g. volume pattern flipping from Uniform to U-Shaped)
- **Live TCA** shows benchmarks-to-date (Arrival / VWAP-to-date / TWAP-to-date) and a mark-to-market valuation of the unfilled remainder, converging into the full reversion/decomposition/percentile readout once the session completes

At any point the user can add an intervention — switch algo/urgency for the remainder — and stack multiple across the session (e.g. VWAP → POV → IS), each one re-planning only the shares still unfilled over the remaining bars; interventions auto-pause playback so the effect can be reviewed before resuming. Interventions can be undone individually or reset entirely, and the final blended outcome is shown against the "stayed on the original algo all day" baseline. Backtest-style — the same historical bars are replayed on a timer, not a live feed.

**Hypothesis Testing on execution parameters:** lets a user define two configurations (algo / urgency / order size) and click a button to get a formal statistical verdict on whether one significantly beats the other on a chosen metric (Total Cost, Slippage, Market Impact, Opportunity Cost, or Fill Rate). Since this platform can't route live orders through two algos at once, it uses the practical analog quant desks use: a **paired backtest** — replaying the exact same historical days under both configurations so market-condition noise is held constant and only the configuration differs. Reports a paired t-test, a Wilcoxon signed-rank robustness check, a 5,000-resample bootstrap confidence interval on the mean difference, and Cohen's d, plus a histogram of daily paired differences and disclosed caveats (small-sample warnings, fast-path vs. re-simulated data provenance). When a tested configuration exactly matches the current pipeline's settings it reuses Agent 4's already-computed daily data instead of re-simulating.

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

## Running locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Tech stack

- **Data:** [yfinance](https://github.com/ranaroussi/yfinance) (free Yahoo Finance data, no API key)
- **UI:** Streamlit
- **Charts:** Plotly
- **Analysis:** pandas, NumPy, SciPy — statistical/rule-based agents (variance ratio test, Corwin-Schultz, Bulk Volume Classification, Almgren-Chriss, paired t-test / Wilcoxon / bootstrap for hypothesis testing), not LLM-backed

## Repository structure

```
app.py                              # Streamlit UI — Page 1 (simulator) + Page 2 (rebalancing)
agents/
  agent1_market_data.py             # Market data fetch, ADV, realized vol, volume profile
  agent2_market_regime.py           # Volatility / volume / trend regime classification
  agent3_algo_simulation.py         # 8-algorithm single-day simulation + chained live-execution interventions
  agent4_performance_comparison.py  # Multi-day comparison, sensitivity grid, AC frontier
  agent5_recommendation.py          # Rule-based recommendation memo
  agent6_pretrade_posttrade.py      # Pre-trade estimate + post-trade TCA
  agent7_earnings_calendar.py       # Earnings-date gap-risk flag
  agent8_critic.py                  # Independent recommendation review
  agent9_microstructure.py          # Kyle's Lambda, VPIN, Almgren impact cross-check
  agent10_hypothesis_test.py        # Paired-backtest hypothesis testing (t-test/Wilcoxon/bootstrap)
  agent11_live_snapshot.py          # Point-in-time re-run of Agents 2/5/6/9 for the Live Trading Session
  rebalancing_event_study.py        # CAR/abnormal-volume event study + execution insights
  orchestrator.py                   # Runs Agents 2-9, conditional skip/fail handling
  context.py                        # Shared ExecutionContext ("blackboard") state
PROJECT_CONTEXT.md                  # Full design philosophy, methodology, and sourcing notes
requirements.txt
```
