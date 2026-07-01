# Execution Analytics Platform — Project Context
*Last updated: 2026-07-01. Paste this file at the start of a new chat to resume work.*

---

## Purpose
A multi-agent Streamlit app built to demonstrate equity execution algorithm knowledge for Goldman Sachs GSET (Quantitative Execution Analyst) and CLSA job applications. Deployed at: https://equities-execution-analysis.streamlit.app (GitHub: https://github.com/zhennanl/equities-execution-analysis)

---

## File Structure
```
C:\Users\Bill\Downloads\execution_analytics\
├── app.py                              # Streamlit UI — 2 pages
├── requirements.txt
├── agents/
│   ├── __init__.py
│   ├── agent1_market_data.py           # Fetches OHLCV from yfinance
│   ├── agent2_market_regime.py         # Regime classification (vol/volume/trend)
│   ├── agent3_algo_simulation.py       # VWAP / TWAP / POV / IS simulation
│   ├── agent4_performance_comparison.py # Multi-day comparison + sensitivity
│   ├── agent5_recommendation.py        # Rule-based memo generator
│   └── rebalancing_event_study.py      # Event study (CAR, abnormal vol)
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
3. **Trend** (lag-1 autocorr of 5-min returns):
   - >+0.10 → Trending | <-0.10 → Mean-Reverting | else → Neutral

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
