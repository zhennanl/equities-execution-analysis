# Market-Microstructure Research → Platform Improvements (Asia focus)

*A literature scan (with an Asian-equities emphasis) turned into concrete,
testable additions to this platform, each mapped to the GSET consultant
responsibilities. Every improvement cites its source and states the honesty
boundary (free OHLCV/bar data, not tick/order-book).*

---

## 1. Research scanned

**A. EDGE — Efficient Discrete Generalized Estimator of the effective spread.**
Ardia, Guidotti & Kroencke, *Journal of Financial Economics* 161 (2024) 103916.
Derives asymptotically-unbiased effective-spread estimators from Open/High/Low/
Close under *discretely observed* prices and combines them to minimise variance —
more efficient than Corwin-Schultz (2012) and Abdi-Ranaldo (2017), works at
daily *and* intraday frequency, needs ≥3 observations. Authors publish reference
code in 6 languages (MIT license). → *Add EDGE as the third, state-of-the-art
spread cross-check.*

**B. The "double" square-root law of market impact — Tokyo Stock Exchange.**
Maitrier, Loeper, Kanazawa & Bouchaud (2025), *Quantitative Finance* 26(4) /
arXiv:2502.16246, using TSE 2012–2018 data with trader IDs. Confirms the
square-root impact law is *mechanical* (not information-driven) and adds an
inverse-square-root **decay in time** after a metaorder. This is direct Asian-
market evidence for the platform's √-law impact model, and motivates modelling
impact **decay** (temporary vs permanent), which the post-trade reversion module
already gestures at. → *Validates our √-impact prefactor; motivates a decay-aware
temporary/permanent split and an empirical-prefactor readout (already delivered
by the regression cost model).*

**C. Closing auctions in Asia.** Closing auctions now reach ~20% of daily volume
in large developed markets; ETF/passive ownership is a primary driver (AEA 2021;
Global Trading). Hong Kong's Closing Auction Session (CAS, relaunched 2016) uses
a **reference-price band** (±5–7.5% around the reference) after the 2008–09 CAS
was withdrawn over manipulation concerns. China runs opening (09:15–09:25) and
closing call auctions on both exchanges. → *A closing-auction concentration
metric and Asia-aware MOC framing; auction volume is where a large Asian order
often should sit.*

**D. Price limits / circuit mechanics (Asia).** Daily price-limit bands: China
main-board ±10% (ST ±5%, STAR/ChiNext ±20%), Korea (KRX) ±30%, Taiwan (TWSE)
±10%, Vietnam (HOSE) ±7%, Thailand (SET) ±30%, Japan variable yen bands; US/UK/
HK/AU/SG have none (HK only at the CAS). Limits create genuine execution risk
(limit-up/down "locked" markets, incomplete fills) that a buy-side desk must
price. (SSE/exchange rulebooks; China circuit-breaker microstructure study,
APJFS 2019.) → *A per-market price-limit model + a pre-trade flag when a limit
order or the expected move sits near the band.*

**E. Amihud illiquidity.** Amihud (2002), *J. Financial Markets* 5, 31–56:
ILLIQ = average of |daily return| / daily dollar volume — "daily price response
per dollar traded", a price-impact proxy computable anywhere OHLCV exists,
especially valued in markets without good spread data (i.e. much of Asia). →
*Add ILLIQ as a liquidity metric and an independent cross-check on the impact
model.*

**F. Intraday seasonality (U-shape) with Asian sessions.** Volume and volatility
are U-shaped intraday; Asian markets (China, Japan, HK, TW, Vietnam, Thailand,
Indonesia) have **lunch breaks** producing a distinctive twin-U, morning/afternoon
profile. → *Explicit seasonality buckets (open / midday / close, session-aware)
so schedule advice is Asia-correct.*

## 2. Improvements implemented (this session)

| # | Improvement | Source | Module | Responsibility |
|---|---|---|---|---|
| 1 | **EDGE effective-spread estimator** (third cross-check alongside CS & AR) | A | `agents/microstructure_analytics.py::edge_spread` | R3 |
| 2 | **Amihud illiquidity** (ILLIQ, price-impact-per-$ proxy) | E | `…::amihud_illiquidity` | R3, R4 |
| 3 | **Intraday seasonality** buckets (open/midday/close; lunch-break aware) | F | `…::intraday_seasonality` | R3, R4 |
| 4 | **Time-series tools** — autocorrelation function + Ljung-Box test (cost/return serial dependence) | — (JD "time series") | `…::acf`, `…::ljung_box` | R7 |
| 5 | **Per-market price-limit bands + pre-trade flag** | D | `agents/asian_markets.py` | R4, compliance |
| 6 | **Closing-auction concentration** metric | C | `agents/asian_markets.py::closing_auction_concentration` | R4 |
| 7 | **Client benchmark scorecard** (realized vs model-expected vs history) | — (R2) | `agents/client_analytics.py::benchmark_scorecard` | R2 |
| 8 | **Client-ready TCA one-pager** generator (markdown) | — (R1) | `agents/client_analytics.py::client_report` | R1 |

Together with the prior session's regression cost model (R3/R6/R7) and the
existing venue/SOR sim (R4) and multi-day backtest (R5), this closes coverage of
all seven responsibility bullets — see the coverage map in
`docs/GSET_ROLE_AUTOMATION_ANALYSIS.md`.

## 3. Honesty boundary
All estimators run on free OHLCV/5-min bars. EDGE/CS/AR estimate the *effective*
spread from ranges, not a quoted book; Amihud is a daily price-impact proxy;
price-limit bands are the published statutory rates (stylised, not a live
exchange rule engine); auction concentration uses the historical volume curve as
the auction proxy. The methods and code transfer unchanged to real client fills
and vendor data.

## Sources
- Ardia, Guidotti, Kroencke (2024), *JFE* 161:103916 — EDGE. https://doi.org/10.1016/j.jfineco.2024.103916 ; reference code https://github.com/eguidotti/bidask
- Maitrier, Loeper, Kanazawa, Bouchaud (2025) — double square-root law, TSE. https://arxiv.org/abs/2502.16246
- Amihud (2002), *J. Financial Markets* 5:31–56. https://www.cis.upenn.edu/~mkearns/finread/amihud.pdf
- Closing auctions / Asia: AEA 2021 "Who Trades at the Close?"; Global Trading "Volumes Shifting Toward the Close"; HKEX CAS design (ScienceDirect S1386418121000732).
- China market microstructure / circuit breakers: APJFS 2019; Shanghai Stock Exchange trading mechanism rulebook.
