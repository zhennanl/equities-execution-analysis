# Execution Analytics Platform — Project Context
*Last updated: 2026-07-01 (institutional-grade analytics pass). Paste this file at the start of a new chat to resume work.*

---

## Purpose
A multi-agent Streamlit app built to demonstrate equity execution algorithm knowledge for Goldman Sachs GSET (Quantitative Execution Analyst) and CLSA job applications. Deployed at: https://equities-execution-analysis.streamlit.app (GitHub: https://github.com/zhennanl/equities-execution-analysis)

---

## Design Philosophy: Why "Agents", and What Genuine Multi-Agent Would Add

**Honest self-assessment first.** "Agent 1–6" as currently built is well-factored
component-wise programming, not architecturally multi-agent. Each module is a
pure function with a typed dataclass in, typed dataclass out; app.py calls them
in one fixed order every run (`data → regime → sim → comp → memo → pretrade/
posttrade`); Agent 5's "decision" is a static if/elif rule table, not autonomous
reasoning. Calling these "agents" is a naming/organizational convention — good
separation of concerns, same thing as five well-named functions. That's a
legitimate and defensible choice, not a shortcoming: this pipeline handles
money-adjacent numbers (cost estimates, market impact), so deterministic,
reproducible, cheaply-testable, git-diffable code is the *right* engineering
trade-off. A test suite can assert `total_cost_bps` to the cent; you cannot
assert that about an LLM's output.

**What makes a system genuinely multi-agent** (vs. this component pipeline):
- **Autonomy** — each agent decides its own action from goals + context, not a
  sequence the caller dictates. Valuable once the "decision function" is too
  open-ended for an enumerable if/elif tree (e.g. synthesizing conflicting
  signals across regimes never explicitly anticipated by the programmer).
- **Dynamic orchestration** — which agents run, in what order, is decided at
  runtime (typically by a planner/orchestrator), not hard-coded. Buys
  conditional/skippable steps and the ability to add new specialists without
  rewriting the pipeline.
- **Loose coupling via shared state** — agents read/write a shared context
  instead of every downstream function importing specific upstream dataclasses
  by name. Right now adding Agent 6 meant threading `pretrade`/`posttrade`
  explicitly through app.py and importing `PerformanceComparison`,
  `SimulationResult`, etc. by name — textbook tight coupling.
- **Negotiation / verification** — independent agents can evaluate the same
  question and reconcile disagreement (a risk agent that can veto a strategy
  agent), rather than one function producing one deterministic answer.
- **Concurrency** — agents without a real dependency chain can run in
  parallel (Market Regime and the spread estimator both only depend on Market
  Data, not on each other — currently sequential purely as an implementation
  artifact).
- **Memory / adaptation across runs** — agents that remember past outcomes
  (e.g. the Post-Trade TCA cost-percentile history) and adjust future
  estimates accordingly, rather than a fixed historical window recomputed
  from scratch every session.

**Where I would *not* introduce agentic/LLM behavior**: the core cost math
(square-root impact, Perold opportunity cost, Almgren-Chriss trajectory,
Corwin-Schultz spread) should stay deterministic Python. Knowing where
agentic reasoning adds value vs. where it just adds latency, cost, and
non-determinism to something that should be auditable is the substantive
point, not "replace everything with an LLM call."

**Modification directions considered, roughly low → high effort/complexity:**
1. Orchestrator that decides which specialist agents to invoke at runtime
   (e.g. skip the spread estimator when daily history is too short; only run
   an elevated-volatility deep-dive when Agent 2 flags Extremely Trending) —
   fully deterministic, no LLM needed.
2. Blackboard-style shared `ExecutionContext` object instead of explicit
   dataclass threading through app.py — decouples agents so new ones don't
   require touching every call site.
3. Verification/critic agent — a second pass that independently reviews
   Agent 5's pick against a risk policy and can flag disagreement, upgrading
   today's static risk-flag strings into an actual second opinion.
4. LLM-backed synthesis agent on top of the deterministic quant agents —
   Agents 1–4/6 stay exactly as-is (auditable math), but a reasoning layer
   reads their structured output and produces the narrative recommendation,
   handling edge cases the fixed rule tree can't enumerate, and can answer
   free-form follow-up questions about the analysis.
5. Concurrent execution of independent agents (asyncio/threading) where
   there's no real sequential dependency.
6. Persistent memory agent — store realized-vs-expected cost outcomes across
   sessions and let future pre-trade estimates be informed by this name's own
   track record, not just a bigger static lookback window.

---

## File Structure
```
C:\Users\Bill\Downloads\execution_analytics\
├── app.py                              # Streamlit UI — 2 pages
├── requirements.txt
├── agents/
│   ├── __init__.py
│   ├── context.py                      # ExecutionContext blackboard (shared agent state)
│   ├── orchestrator.py                 # run_pipeline() — dynamic/conditional agent invocation
│   ├── agent1_market_data.py           # Fetches OHLCV (+ best-effort shares outstanding) from yfinance
│   ├── agent2_market_regime.py         # Regime classification (vol/volume/trend via variance ratio test)
│   ├── agent3_algo_simulation.py       # VWAP/TWAP/POV/IS/MOC/MOO/LIQ/STEALTH simulation
│   ├── agent4_performance_comparison.py # Multi-day comparison + sensitivity
│   ├── agent5_recommendation.py        # Rule-based memo generator
│   ├── agent6_pretrade_posttrade.py    # Pre-trade cost estimate + post-trade TCA
│   ├── agent7_earnings_calendar.py     # Earnings-date overnight-gap risk flag
│   ├── agent8_critic.py                # Independent verification/critic pass
│   ├── agent9_microstructure.py        # Kyle's lambda, VPIN, Almgren (2005) impact cross-check
│   └── rebalancing_event_study.py      # Event study (CAR, abnormal vol) — Page 2
```

---

## Git State
- Remote: https://github.com/zhennanl/equities-execution-analysis.git
- Branch: main
- Last 3 commits:
  - `353910a` Fix dropdown menu bug (Singapore KeyError)
  - `700184f` Add agents 2-5, 9 new Asian markets
  - `938a862` Initial build: Agent 1 + Streamlit app
- Working tree is CLEAN (all changes committed as of 2026-07-01)

---

## Agent Architecture

### Agent 1 — Market Data (`agent1_market_data.py`)
- Fetches 5-min intraday (5d) + daily OHLCV (60d) from yfinance
- Computes: ADV (shares + USD), current price, realized vol (annualized), intraday volume profile
- Rate-limit protection: `time.sleep(0.3)` between calls; friendly 429 error message
- `@st.cache_data(ttl=300)` applied in app.py via `_cached_fetch()` wrapper

**MARKET_INFO — 14 markets supported:**
| Market | Suffix | Bars/day |
|--------|--------|----------|
| Taiwan (TWSE) | .TW | 54 |
| Hong Kong (HKEX) | .HK | 78 |
| Japan (TSE) | .T | 78 |
| Korea (KRX) | .KS | 78 |
| US | (none) | 78 |
| Singapore (SGX) | .SI | 85 |
| China-A Shanghai | .SS | 49 |
| China-A Shenzhen | .SZ | 49 |
| India (NSE) | .NS | 75 |
| Australia (ASX) | .AX | 73 |
| Thailand (SET) | .BK | 61 |
| Indonesia (IDX) | .JK | 67 |
| Malaysia (KLSE) | .KL | 71 |
| Vietnam (HOSE) | .VN | 46 |

**Philippines (.PS): NOT supported — Yahoo Finance carries no PSE data.**

### Agent 2 — Market Regime (`agent2_market_regime.py`)
Three independent dimensions:
1. **Volatility** (range-based): today_range / 20d_median_range
   - >1.50 → Extremely Trending | 1.20–1.50 → Trending | 0.80–1.20 → Normal | <0.80 → Tight
2. **Volume pattern**: avg(first 25% bars, last 25% bars) / middle 50% bars
   - >1.5 → U-Shaped | ≥0.80 → Uniform | <0.80 → Midday-Heavy
3. **Trend** — Lo-MacKinlay (1988) variance ratio test on the most recent day's
   5-min log returns (grid q=2,4,8; q=4 heteroskedasticity-robust z* is the
   headline stat): significant (|z*|≥1.96) + VR>1 → Trending | significant +
   VR<1 → Mean-Reverting | else → Neutral. Lag-1 autocorrelation is retained
   as a simpler supporting statistic alongside it (see "Institutional-Grade
   Analytics" section below for why the VR test replaced a raw autocorr
   threshold).

### Agent 3 — Algorithm Simulation (`agent3_algo_simulation.py`)
Simulates on most recent complete trading day (≥80% of expected bars).
- **VWAP**: volume-proportional schedule
- **TWAP**: equal shares per bar
- **POV**: participation rate × bar volume (Low=10%, Med=15%, High=20%); may not fill 100%
- **IS**: exponential front-loading (lambda Low=0.5, Med=1.2, High=2.5)

**Metrics:**
- `slippage_bps = (avg_exec - arrival) / arrival × 10,000`
- `market_impact_bps = η × σ_daily × √(Q/ADV) × speed_factor × 10,000` (η=0.3)
- Speed factors: TWAP=0.85, VWAP=0.90, POV=1.00, IS={Low:1.20, Med:1.55, High:2.00}

### Agent 4 — Performance Comparison (`agent4_performance_comparison.py`)
- Multi-day simulation: runs all 4 algos on every available intraday day (skips days <50% bars)
- Produces: daily_costs df, daily_slips df, summary (Mean/Std/Min/Max/Win Days), sensitivity matrix
- Sensitivity: algos × [1,5,10,15,20,25]% ADV using mean slip + sqrt market impact model
- Inlines simulation math (does NOT import private `_sim_*` functions from agent3)

### Agent 5 — Recommendation Memo (`agent5_recommendation.py`)
Rule-based (no API key needed). Selection logic priority:
1. Extremely Trending + Medium/High urgency → IS
2. High urgency → IS
3. Tight/Normal + U-Shaped + Low → VWAP
4. Uniform + Low/Medium → TWAP
5. Mean-Reverting + Low → TWAP
6. Default → comparison.best_algo

Risk flags: elevated vol, large order (≥15% ADV), POV fill <100%, trending+low urgency mismatch.

### Agent 6 — Pre-Trade / Post-Trade Analytics (`agent6_pretrade_posttrade.py`)
- **Pre-trade**: Corwin-Schultz spread estimate, capacity table, expected cost
  range (empirical P10/P50/P90 percentile bands when ≥5 simulated days are
  available, else falls back to Mean±Std), and the Almgren et al. (2005)
  calibrated impact cross-check (see below).
- **Post-trade**: multi-benchmark comparison (Arrival/VWAP/TWAP/Close), cost
  percentile vs. own history, impact-reversion check, and the Almgren et al.
  (2005) I/J/K permanent-temporary impact decomposition (see below).

### Agent 7 — Earnings Calendar (`agent7_earnings_calendar.py`)
Flags overnight-gap risk when a scheduled earnings print falls within
`NEAR_TERM_TRADING_DAYS` (5) of the order. Data: `yfinance.Ticker.get_earnings_dates()`.

### Agent 8 — Critic / Verification (`agent8_critic.py`)
Independent second pass over Agent 5's pick — checks fill-qualification
(defense in depth), earnings-date risk vs. urgency, degraded-spread/size
interaction, elevated VPIN (Agent 9), and statistically significant Kyle's
lambda (Agent 9) vs. the fixed square-root impact model. Raises findings;
never silently overrides `memo.primary_algo`.

### Agent 9 — Market Microstructure & Order-Flow Toxicity (`agent9_microstructure.py`)
The institutional-grade liquidity/impact layer added in the 2026-07-01 pass —
see "Institutional-Grade Analytics" section immediately below for full
methodology, formulas, and sources.

---

## Institutional-Grade Analytics — Methodology & Sources (2026-07-01 pass)

Added after reviewing published institutional/academic TCA and market-
microstructure literature, with the explicit goal of moving the platform's
analysis closer to how real execution desks and quant researchers evaluate
trading costs and liquidity — while being honest about what a free,
OHLCV-only data feed (no order book, no tick-level trade prints, no venue-
level data) can and can't support. Every new metric below documents its
approximation relative to the canonical (tick/order-book) version in its
own module docstring; this section is the consolidated summary.

**1. Kyle's Lambda** (Kyle, 1985) — price impact per unit of signed order
flow, the standard liquidity/depth metric on institutional microstructure
desks. Estimated via OLS of NEXT-bar returns on THIS-bar's Bulk-Volume-
Classified net order flow (deliberately lagged, not contemporaneous, to
avoid a near-tautological regression — see `agent9_microstructure.py`'s
docstring). In the spirit of the regression approach in Breen, Hodrick &
Korajczyk (2002), cited in Almgren et al. (2005).

**2. VPIN — Volume-Synchronized Probability of Informed Trading** (Easley,
López de Prado & O'Hara; bulk-volume classification from their 2012 paper
"Bulk Classification of Trading Activity"). Order-flow "toxicity" measure
that reached historically elevated levels in the hour before the May 6,
2010 Flash Crash; a Lawrence Berkeley National Laboratory study for the SEC
called it "the strongest early warning signal known to us at this time."
Implemented here as a TIME-BAR approximation of Bulk Volume Classification
(5-min OHLCV bars standing in for tick-level trade prints / true volume
buckets) — disclosed explicitly as an approximation, not a canonical
tick-data VPIN reading.

**3. Almgren et al. (2005) calibrated impact model** — "Direct Estimation
of Equity Market Impact" (Almgren, Thum, Hauptmann & Li, Citigroup Global
Quantitative Research), fit to ~29,500 real Citigroup institutional equity
orders (Dec 2001–Jun 2003). Splits impact into a linear permanent component
(γ=0.314, α=1) and a concave temporary component (η=0.142, β=0.60 — the
paper rejects the classical square-root law's β=0.5 at 95% confidence in
favor of a 3/5 power law) with an optional turnover liquidity factor
(shares outstanding / ADV)^0.25. Reported alongside — not in place of —
Agent 3's independent η=0.3 square-root model as a literature-anchored
cross-check; the two disagreeing is itself informative. Also used
post-trade for the I (permanent) / J (realized) / K (temporary = J − I/2)
impact decomposition, using arrival price, average execution price, and
day-end price already computed elsewhere in the pipeline.

**4. Lo-MacKinlay (1988) variance ratio test** — replaced Agent 2's raw
lag-1-autocorrelation-vs-±0.10-threshold trend classifier. Computes VR(q)
at q=2,4,8 with both the homoscedastic and heteroskedasticity-robust z*
statistics (the latter correcting for volatility clustering, well-documented
in intraday equity returns); q=4's robust z* drives the Trending/Mean-
Reverting/Neutral label at ~95% significance. A materially more standard
academic test than an arbitrary autocorrelation cutoff.

**5. Percentile-band pre-trade cost estimates** — Expected Cost Range
switched from Mean±Std to empirical P10/P50/P90 quantiles of Agent 4's
simulated daily-cost distribution (when ≥5 days are available), since
Almgren et al. (2005)'s own residual analysis found impact-cost residuals
"extremely fat-tailed" even though "a standard Gaussian is a reasonable fit
to the central part" — a symmetric Mean±Std band understates tail risk.

**Known data limitations (unchanged from before this pass, restated for
completeness):** no free order-book/NBBO feed, no tick-level trade prints,
no venue/dark-pool routing data, no cross-sectional peer universe for
percentile ranking (VPIN and cost percentiles are read against a name's own
history, not a peer set). Every metric above is built to degrade gracefully
and disclose its approximation rather than silently presenting a proxy as
the canonical figure.

**Sources consulted:**
- Almgren, Thum, Hauptmann & Li (2005), "Direct Estimation of Equity Market Impact" — https://www.cis.upenn.edu/~mkearns/finread/costestim.pdf
- Easley, López de Prado & O'Hara — VPIN overview and Bulk Volume Classification — https://www.quantresearch.org/VPIN.pdf
- Kyle (1985) lambda — estimation methodology survey — https://metricgate.com/docs/kyle-lambda-price-impact/
- Lo & MacKinlay (1988) variance ratio test — https://mingze-gao.com/posts/lomackinlay1988/
- Effective/realized spread & price-impact decomposition survey (Ødegaard) — https://ba-odegaard.no/teach/notes/liquidity_estimators/spread/spread_lectures.pdf
- 2024-2025 European buy-side TCA benchmark usage survey (Bloomberg Professional Services) — https://www.bloomberg.com/professional/insights/trading/european-institutional-equity-trading-study-technology/

---

## Free Order-Book / Tick Data — Feasibility Investigation (2026-07-06)

Investigated whether free order-book depth or tick-level trade data exists
anywhere (live or historical, any market) as a genuine upgrade path beyond
OHLCV bars for Agent 9's Kyle's lambda / VPIN / BVC approximations. Findings,
in order of practical usefulness:

**1. IEX Exchange HIST — the best standing (ongoing, free, live) option.**
https://iextrading.com/trading/market-data/#hist-download — IEX publishes
free, no-registration-required downloads of its own full order-book depth
(DEEP) and top-of-book (TOPS) feeds, in raw pcap format, for every symbol it
trades. Rolling trailing-12-months history plus new data added T+1 (over
17TB / ~5,000 files as of March 2026). This is genuine tick-by-tick
order-book data — real quote updates and trade prints — not a BVC-style
approximation. Caveat: IEX is one venue among ~16 in the fragmented US
equity market and carries roughly 3-6% of a given US stock's consolidated
volume (Q4 2025 IEX-reported figures) — a real, live, currently-updating
order book, but a single-venue view, not the full NBBO-consolidated book.
Needs a pcap parser; open-source Python libraries already exist (`IEXTools`,
`iex_parser` on PyPI/GitHub), so this is a real, buildable integration, not
just a data dump with no path to use it.

**2. LOBSTER free samples — the best one-time ground-truth benchmark.**
https://lobsterdata.com — fully reconstructed limit-order-book data (at
1/5/10/30/50 price-level depths), built from real NASDAQ TotalView-ITCH
data — genuinely research-grade. The free samples are frozen to a single
historical trading day (June 21, 2012) for exactly five tickers: AAPL,
AMZN, GOOG, INTC, MSFT. Not live and not extensible to other tickers/dates
without a paid subscription, but ideal as a fixed, one-time benchmark to
validate this project's BVC/VPIN approximation against a real, fully
reconstructed order book on that one day.

**3. Databento — $125 free credit, not a standing free source.** Full L3
market-by-order data across 15 US exchanges + 30 ATSs since 2018 — the best
coverage/quality of anything found — but it's a depleting credit rather
than an ongoing free tier. Usable for one focused validation pull, not a
permanent data source for this project.

**4. Asian markets: confirmed no free tick/order-book data exists
anywhere.** Directly checked HKEX and JPX (the two most relevant exchanges
for this project's Taiwan/Hong Kong/Japan coverage) — both offer only paid
real-time and historical tick/order-book products (JPX in fact just
launched a new *paid* 10-level order-book historical dataset in June 2026,
underscoring this is an active commercial product line, not one trending
toward free). This means any order-book upgrade to this project can only
ever cover the US-ticker subset of the 14 supported markets — the 13 Asian
markets remain OHLCV-only regardless of which option above is chosen.

**Implication for this project:** IEX HIST is the most promising path to a
genuine (not approximated) order-flow-toxicity/impact estimate — for US,
IEX-eligible tickers specifically — since it's free, real, and ongoing
rather than a frozen sample. LOBSTER's 2012 AAPL sample is a good
complementary one-time benchmark: reconstruct real Kyle's lambda/VPIN from
the actual order book on that one day, and compare against what the
BVC-approximation methodology currently in Agent 9 produces on the same
day, as a direct accuracy check of the approximation. **Not yet
implemented** — this is a feasibility finding pending a scope/priority
decision, not a completed integration.

---

### Index Rebalancing Event Study (`agents/rebalancing_event_study.py`)
- Estimation window: T-70 to T-11 trading days
- OLS market model: R_stock = α + β × R_index
- Outputs: CAR, per-day AR, abnormal volume, price indexed to 100 at T
- **Timezone fix**: yfinance returns tz-aware DatetimeIndex for Asian markets.
  Strip with: `pd.to_datetime([d.date() for d in index])`
  Also create `_close_tz` copy BEFORE reindexing (silent NaN bug otherwise)

**INDEX_PROXIES (19 options):**
- MSCI Taiwan / TAIEX → `^TWII`
- Hang Seng Index → `^HSI` | H-Shares → `^HSCE`
- Nikkei 225 → `^N225` | TOPIX → `^N300`
- KOSPI → `^KS11`
- STI Singapore → `^STI`
- Shanghai Composite → `000001.SS` | Shenzhen Component → `399001.SZ` | CSI 300 → `000300.SS`
- NIFTY 50 → `^NSEI` | BSE SENSEX → `^BSESN`
- S&P/ASX 200 → `^AXJO`
- SET Thailand → `^SET.BK`
- IDX Composite → `^JKSE`
- FTSE Bursa KLCI → `^KLSE`
- Vietnam proxy → `VNM` (US ETF, imperfect)
- S&P 500 → `^GSPC` | NASDAQ 100 → `^NDX`

---

## app.py — Key Structure
- **Page 1**: Execution Algorithm Simulator — 5-agent pipeline
  - Inputs: Market (14 options), Ticker, Order Size (% ADV), Urgency
  - Example tickers pre-filled per market (e.g. Singapore → D05, India → RELIANCE)
  - Agent 5 recommendation pinned at top; Agents 1–4 outputs below
  - `_cached_fetch()` wraps Agent 1 with `@st.cache_data(ttl=300)`
- **Page 2**: Index Rebalancing Analysis — event study
  - Index dropdown uses `INDEX_PROXIES` keys (19 options)
  - 3 chart tabs: CAR / Abnormal Volume / Price Performance
  - Summary table at key days (T-10, T-5, T-1, T+0, T+1, T+5, T+10)

---

## Known Bugs Fixed
- **Write tool truncation**: Always use bash heredoc (`cat > file << 'PYEOF'`) for file writes, NOT the Write tool — it truncates at original file size.
- **Timezone mismatch**: yfinance Asian data has tz-aware DatetimeIndex. Strip with `pd.to_datetime([d.date() for d in index])`.
- **Price index stuck at 100**: Must strip tz from Close series BEFORE `.reindex()`, not after.
- **Singapore KeyError**: `ex` dict in app.py line ~63 was missing new markets. Fixed by adding all 14 markets + `.get(market, "")` fallback.
- **`fillna(method='ffill')` deprecated**: Use `.ffill()` instead.

---

## Technical Details
- **yfinance version**: 1.5.1
- **Python**: 3.10 (in sandbox: `/sessions/.../mnt/`)
- **Streamlit**: `st.cache_data(ttl=300)`, `st.empty()` for status placeholders
- **File paths**:
  - Project: `C:\Users\Bill\Downloads\execution_analytics\`
  - Bash sandbox path: `/sessions/brave-awesome-lovelace/mnt/Downloads/execution_analytics/`

---

## Pending Items
1. **Streamlit Cloud deployment**: Connect GitHub repo at share.streamlit.io (user does this directly)
2. **Push to GitHub**: `git add . && git commit -m "msg" && git push origin main`
   - Auth: use Personal Access Token (GitHub → Settings → Developer Settings → PAT → repo scope)
3. **CV finalization**: Revised sections assembled into final Word document
4. **Cover letters**: GS version and CLSA version (not yet drafted in this session)

---

## Index Constituent Change Data Sources (for rebalancing event study)
- **MSCI**: msci.com/indexes/index-resources/index-announcements — changes announced free, 2 business days before effective. Quarterly schedule: effective 1st business day of Mar/Jun/Sep/Dec.
- **iShares ETF holdings**: ishares.com — free daily CSV. Best MSCI constituent proxy: EWT (TW), EWH (HK), EWJ (JP), EWY (KR), EWS (SG), MCHI (CN), INDA (IN), EWA (AU).
- **Exchange sites**: JPX.co.jp (Nikkei/TOPIX), KRX.co.kr (KOSPI200), SGX.com (STI), NSEIndia.com (NIFTY50), ASX.com.au (ASX200).
- **FTSE Russell**: lseg.com/en/ftse-russell — semi-annual for most Asian indices.
