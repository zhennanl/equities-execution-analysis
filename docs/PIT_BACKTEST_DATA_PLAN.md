# PIT Backtest 2015-2026 — Required Data Inventory & Acquisition Plan

*Session 9i (2026-08-05). Goal: PIT-grade the engine on all 46 TW
reviews. Every item below was PROBED LIVE before being listed —
status reflects actual API responses, not documentation promises.*

## What a PIT vintage needs, item by item

| # | Ingredient | Why | Source | Status (probed 2026-08-05) |
|---|---|---|---|---|
| 1 | Shares outstanding per name, per vintage | cap = price x shares AS-OF; THE vintage gate | FinMind `TaiwanStockShareholding` field `NumberOfSharesIssued` (daily) | **VERIFIED**: 2015-01 depth; TWSE + TPEx (6223 in 2015); DELISTED names covered (3474 Inotera 2016) |
| 2 | Prices incl. DELISTED names | survivorship: deleted names often delisted later; yfinance drops them | FinMind `TaiwanStockPrice` (daily OHLCV) | **VERIFIED**: 3474 prices 2016 present |
| 3 | Foreign holding % + FOL | foreign-room screen (GIMI §3.1.2.6), float input | same `TaiwanStockShareholding` rows (ForeignInvestmentSharesRatio, UpperLimitRatio) | **VERIFIED**: in every row since 2015 |
| 4 | Free float per vintage | float-adjusted caps for the coverage walk | TDCC dispersion (`TaiwanStockHoldingSharesPer`) | **PAYWALLED** on free tier. v1 fallback: current ff held constant with a REPORTED sensitivity band (±10%); v2: MOPS insider-holdings monthly scrape (free, heavy) or FinMind sponsor tier |
| 5 | Membership list per vintage | who was IN before each review | roll the 46 official change lists backward from the verified current list (alias bridge, print-verified) | **HELD** — no new data needed |
| 6 | Constituent count anchor per vintage | count-anchored universe (the 55%->65% fix) | MSCI TW factsheet archives via Wayback Machine | PARTIAL — spot-check per year; fallback: count implied by rolled membership (#5) |
| 7 | FX TWD/USD per vintage | USD caps | FinMind `ExchangeRate` / held daily series | trivial |
| 8 | ADV / ATVR per vintage | liquidity screens | daily volumes from #2 | comes free with prices |
| 9 | Universe breadth per vintage | who EXISTED (incl. later-delisted) | FinMind `TaiwanStockInfo` (4,300 incl. TPEx) + delisted probes | VERIFIED reachable; scope note below |

## Scope decision (breadth without 4,300-name harvest)

The GMSR walk needs the TOP of the market, not all 4,300 names.
v1 harvest set (EXECUTED 2026-08-05): **109 names** — every name in
the 46-review key (all adds/deletes 2015-2026 incl. delisted, via
msci_tw_events + the TW alias bridge) plus the current boundary set.
Result: 109/109 share + price series cached (58MB,
data/tw_vintage_cache.json), 100 reaching 2015-H1 (the other 9
listed later); TSMC mid-2015 share count matches the known 25.93B
exactly; delisted names (e.g. Inotera 3474) verified with both
shares and prices — survivorship solved. Optional v2 extension:
top-300-by-cap sweep to cover never-member near-miss candidates
(add-side false-negative grading only); stated residual until then.

## The float caveat (item 4) — stated before any backtest runs

v1 backtests will label every result: "float vintage approximated
(current ff held constant); results reported as a band under ff
±10%." If the graded conclusion FLIPS inside that band, the review
is marked FLOAT-SENSITIVE and excluded from headline accuracy. This
is the same honesty rule as BLIND_SHARE — uncertainty carried
explicitly, never averaged away.

## Execution

`scripts/tw_vintage_harvest.py` (this session): probe / fetch /
sanity. Resumable atomic cache -> data/tw_vintage_cache.json.
FinMind free API verified token-less; registered free token raises
rate limits (env FINMIND_TOKEN honored). ~350 names x 2 datasets,
paced — roughly one evening of polite requests.

Then: scripts/pit_backtest_2015.py rebuilds each vintage (shares x
price x FX, screens from #3/#8, membership from #5) and replays the
engine per review with the SAME cadence/buffer rules graded in
May-2026 — no parameter may move per-review (that would be tuning
on the answer).

## What this unlocks (the training set)

46 PIT-graded reviews -> labels for the three learned layers
discussed: cutline retention classifier (~40-60 hazard-zone
episodes), proximity-to-probability calibration, and
regime-conditional count priors (registry v4 H13/H14) — all
trainable with event-clustered leave-one-review-out validation,
Aug-2026 held out as the standing OOS event.
