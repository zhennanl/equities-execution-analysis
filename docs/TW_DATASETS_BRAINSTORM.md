# Additional Taiwan datasets — why useful + how to extract (c-136)

Ranked by (value to our rebalance questions) ÷ (extraction cost).
Statuses: 🟢 = extractable today with code we mostly have;
🟡 = extractable, new endpoint work; 🔴 = paid/gated.

## Tier 1 — high value, low cost

### 1. Broker-branch chip data (分點進出) 🟡
- **What**: per-broker-branch daily buy/sell per stock (TWSE
  `/fund/T86` gives institution totals; branch detail is on
  `bsr.twse.com.tw` per-stock daily files).
- **Why**: our biggest attribution gap. t86 tells us *foreign
  bought 3×ADV* but not *who*. Branch data separates the
  foreign-broker cluster (UBS/GS/ML Taipei = mostly HF + index
  flow) from local retail branches. Directly upgrades the
  Q1/Q23 "is early strength accumulation or froth" test from
  inference to observation.
- **How**: bsr.twse.com.tw serves per-stock per-day CSVs
  (captcha-free JSON route exists via `bsr.twse.com.tw/bshtm/`
  — session + querystring; ~1 req/stock/day, so harvest ONLY
  the 12 shortlist names × the window = ~300 requests). Run on
  Bill's terminal (TWSE one-consumer rule).

### 2. TWSE odd-lot trading (盤中零股) 🟢
- **What**: daily intraday odd-lot volume/value per stock
  (`TWTASU`-family endpoints, 2020-10 onward).
- **Why**: the cleanest pure-retail gauge in Taiwan — odd lots
  are ~90% retail by construction. Sharpens the retail leg of
  the flow triad (margin data is levered-retail only; odd-lot
  captures the cash-account crowd). Tests: does retail chase
  adds late in the window (our froth bucket) and provide the
  E+1 exit liquidity?
- **How**: same TWSE openapi/report pattern as MI_INDEX —
  `https://www.twse.com.tw/exchangeReport/TWTASU?date=YYYYMMDD`
  day-file (all stocks, survivorship-safe). ~14 requests per
  window. Add to `tw_event_window.py` as an optional layer.

### 3. TAIFEX single-stock futures OI + basis 🟢
- **What**: TAIFEX daily per-contract OI, volume, settlement
  (`taifex.com.tw/enl/eDownload` daily CSVs, all history).
- **Why**: the *other* pre-positioning venue. HFs express index
  bets in SSFs to avoid borrow cost and t86 visibility. An OI
  spike in a deletion's SSF before announcement = the short
  crowd we currently infer from SBL, but earlier and cheaper.
  Basis (futures−spot) into E measures how much of the close
  auction is already arbitraged.
- **How**: daily ZIP day-files (every contract, delisted-safe),
  no throttle drama. New script `tw_ssf_harvest.py`, sandbox-ok
  (TAIFEX not bot-blocked historically).

### 4. TDCC shareholder-dispersion weekly continuation 🟢
- **What**: we snapshot TDCC getOD (holder-size brackets); the
  site keeps ~1 year of weekly files.
- **Why**: WEEKLY DELTAS across the window = which size-bracket
  is accumulating. Bracket-15 (>1M shares) rising into E while
  bracket-1..5 falls = institutions absorbing retail exits —
  the holder-level confirmation of the migration story (Q2).
- **How**: already have the getOD scraper; add a weekly cron
  note to the live loop so the series builds itself from now.

## Tier 2 — high value, medium cost

### 5. SBL fee rates / borrow cost 🟡
- **What**: TWSE SBL daily has balance (we have it) but the
  fixed-rate transaction feed carries FEES.
- **Why**: crowding INTENSITY, not just size. A deletion at 5%
  borrow fee is a much more painful short than at 0.5% — our
  C_del_borrow "crowded bounce +3.3%" conditional would
  sharpen materially with cost attached (squeeze risk ∝ fee).
- **How**: `twse.com.tw/en/trading/SBL/t13sa710.html` daily
  files; join on our SBL balance harvester.
- 4/8 asks in our NEEDS column point here.

### 6. MI_QFIIS full daily history (foreign holding %) 🟢
- **What**: we pull MI_QFIIS point-in-time for review dates;
  the day-file exists for EVERY day back to ~2004.
- **Why**: daily foreign-ownership % per stock = the stock
  (not flow) version of t86. Lets us measure the LEVEL shift
  across the whole window and verify our elasticity number
  (0.0418/ADV-day) against holdings, not just net buys. Also
  the foreign-room screen's history for backtests.
- **How**: extend `tw_universe_pit.py` date list; ~1 req/day of
  history; Bill's terminal, resumable, low priority backfill.

### 7. Local Taiwan index-tracker flows (0050/006208 etc.) 🟡
- **What**: TWSE ETF daily units-outstanding change.
- **Why**: separates the MSCI tracker flow (foreign) from
  FTSE-TW/local-cap tracker flow that sometimes hits the SAME
  stock in the SAME week. Our Nov-25 cluster ambiguity (was
  the E−1 surge MSCI or 0050 rebalance?) becomes resolvable.
- **How**: the etf_flows_harvest.py AJAX route (awaiting
  Bill's AJAX_ID paste) or TDCC units file.

## Tier 3 — situational / gated

### 8. News + earnings-calendar overlay 🟡
- **Why**: our "idiosyncratic contamination" flag (analog
  matcher hazard, Q22 attribution) is currently guesswork; a
  simple earnings-date join (TWSE `t187ap` announcements
  day-file) marks which windows carry an earnings print inside
  them — those analogs deserve an asterisk.
- **How**: openapi `t187ap` family, trivially harvestable.
- Sentiment scoring (CMoney/Anue scrape) is 🔴 — parked.

### 9. Intraday tick/5-min for the full universe 🔴
- **Why**: would extend our IB-based auction study (14 adds)
  to every window since 2010 — the p95 auction-jump tail with
  n=150 instead of n=14.
- **How**: TEJ subscription or TWSE historical tick service
  (paid). The IB route already covers the live shortlist free;
  paid backfill is the interview-week decision, not now.

### 10. MSCI index-level files (PAF/weight files) 🔴
- **Why**: exact tracker demand in shares (weight × AUM ÷
  price) instead of our $180B assumption.
- **How**: licensed product; CLSA desk will have it. Our
  workaround (factsheet weights inversion) already recovers
  60/77 FIFs — this dataset retires the assumption the day
  Bill has desk access.

## Recommendation
Build order: **2 (odd-lot) → 3 (SSF) → 1 (branch, shortlist
names only) → 4 (weekly TDCC cron)** — all four are day-file
or small-N harvests that attach directly to open questions
(retail leg, pre-positioning venue, who-is-buying, holder
migration) before the Aug-11 announcement makes them live.
