# High-Frequency Historical Data for TW Index Events — All Solutions, Assessed

*Session 9i (2026-08-04). Every row live-probed today or in this
project unless marked [doc-verified]. Goal: per-name intraday bars
(5m preferred, hourly acceptable) on historical MSCI/FTSE effective
dates for Taiwan.*

## The verdict table

| Source | Granularity x depth (VERIFIED) | Auction print? | Cost / effort | Verdict |
|---|---|---|---|---|
| **TradingView (tvdatafeed, anonymous)** | **5m -> 2026-03 (covers May-29 MSCI + Mar/Jun FTSE prints); 1h -> 2022-06 (~16 event T-days)**; more complete than Yahoo (first hour present) | NO (last bar 13:20) | free; UNOFFICIAL API — ToS grey zone, fine for research, not for a production desk | **Best free unlock. Adopt for research with the greyness stated** |
| yfinance 60m | 1h -> ~730d (8 event T-days) | NO (+ 09:00 bar volume = 0 — verified undercount) | free, stable API | in use; superseded by TV where TV reaches |
| yfinance 5m/15m/30m | 60-day wall (hard-verified) | — | — | forward-capture only |
| **Shioaji (SinoPac broker API)** | 1m kbars, community-documented to ~2020 [doc-verified] | YES (exchange feed) | free w/ brokerage account — **user signup required** | **Best real solution: minute bars + auction, years deep. Recommended action for Bill** |
| **Fugle MarketData API** | intraday candles, years [doc-verified]; 401 without key | YES | free tier w/ account signup — user action | Strong alternative to Shioaji |
| FinMind sponsor | minute + tick, years | YES | ~NT$ hundreds/month | cheapest PAID no-account-hassle route (free tier verified walled today) |
| TWSE Data E-Shop | official tick, full history | YES | per-file purchase | the official archive; budget item |
| Interactive Brokers API | 5m+, years (TWSE supported since 2023) | YES | account + market-data sub | viable; heavier setup |
| Twelve Data | TWSE symbols LISTED (verified) but intraday plan-gated | ? | paid plans | probe with a free key before paying |
| Stooq | bot-walled (verified) | — | — | dead |
| Eastmoney | 31-day wall (verified, earlier session) | — | — | forward-capture only |
| LSEG/BMLL/TEJ | full tick, decades | YES | institutional | the CLSA answer (documented upgrade path) |

## THE DERIVED METHOD (found during verification — worth more than any single source)

Official STOCK_DAY daily volume MINUS TV continuous-bar volume =
**the per-name closing-auction print**, computable for every
name-day TV covers. Exhibit (verified today): 1102 on its May-29
MSCI deletion — official 205.2M shares, TV continuous 17.6M ->
**auction = 91.4% of the day**. (Yahoo's continuous sum was 11.6M —
the missing first hour; TV is the usable continuous leg.)

This converts the auction-share dataset from 17 hand-measured
points to potentially HUNDREDS (every event name x T-day back to
2022 at hourly, plus 5m granularity from Mar-2026) — re-opening the
violence curve with real sample size, per-name auction shares for
the MSCI class (previously unmeasured), and auction-vs-continuous
splits for every counterfactual.

Caveats, stated: TV continuous completeness is verified on spot
checks, not proven universally (each harvest day should pass the
sanity check continuous_sum < official_daily); block/odd-lot
volumes may sit in the difference term (TWSE block trades print
off-auction — subtract BFIAUU block volume where material);
anonymous tvdatafeed is ToS-grey and rate-unguaranteed — cache
aggressively, never build production dependencies on it.

## Residency + account findings (session 9i, Bill-specific)

- **Shioaji AND Fugle both require a Taiwan brokerage account**
  (Fugle's API keys need an E.Sun Securities account; demo token
  only otherwise). Online opening is ROC-tax-resident-only; HK
  residents CAN open — permitted category, UI number obtainable
  online 4h after entering Taiwan — but it is an IN-PERSON branch
  errand (~half-day when next in Taipei). Not a remote option.
- **Bill HAS an Interactive Brokers account → scripts/ib_harvest.py
  built** (runs on his machine against TWS/Gateway): IB historical
  5m depth limits are lifted for bar sizes >= 1 min (TWS API docs);
  the script verifies TW entitlement on one name first (`verify`,
  incl. a delayed-data fallback), then fetches all event windows
  pacing-compliant (`fetch`, resumable, ~30 min), then decides
  auction-inclusion empirically (`sanity`: bar-sum vs official
  daily). If sanity ~1.0, IB supersedes TV for everything.
- No-travel fallbacks unchanged: FinMind sponsor month (harvest and
  cancel) or TradingView paid plan (deeper 5m via login).

## APAC expansion probes (session 9i, Bill's account, all live-tested)

- **TW floor is FINAL at ~2023-05**: deep-probe tested TRADES /
  ADJUSTED_LAST / MIDPOINT / BID_ASK at 2018 — all pre-coverage
  (three "no permissions", one farm-silent timeout). No data type
  reaches deeper; pre-2023 TW stays on official daily + TV hourly.
- **Every OTHER accessible APAC market reaches 2015+ at 5m**:
  HK (SEHK), China-A (SEHKNTL northbound), Singapore (SGX),
  Australia (ASX), India (NSE), Korea (KRX — the "KSE" NO-CONTRACT
  was a wrong exchange code; the fee-waived Korea Equities Bundle
  covers KRX+NXT). Probed at 2023/2021/2018/2015 print days: bars
  everywhere. Taiwan is the newcomer exception, not the rule.
- Caveats logged for the expansion sanity passes: probe bar counts
  were clipped by a fixed 06:00-UTC end time (probe artifact, not
  data); older bars carry ADJUSTED fractional volumes (per-market
  unit/adjustment calibration required, as TW's lots/shares switch
  was); Korea volume field thin pre-~2018; SGX returned Jun-14 for
  Jun-15-2018 (Hari Raya — calendar trap #7); India bars may lack
  volume (zero-vol observations).
- Japan: DEFERRED by user (TSE Equities L1 = JPY 3,000/mo);
  re-enable in APAC_PROBES when subscribed. Korea/India/SG/AU
  event-key bridges: KR (182 decade name-changes) and IN (195) are
  the high-value builds; SG/AU low event counts.

## Recommended plan

1. NOW (free): harvest TV hourly for all event T-days 2022-2026 +
   5m for the three 2026 prints; run the derived-auction-share
   method across them; sanity-check every day against official
   daily volume. This multiplies the auction dataset ~20x.
2. BILL ACTION (free, ~30 min): open a SinoPac account -> Shioaji
   API key -> minute bars WITH auction back to ~2020 — the clean,
   legal, deep solution; Fugle as backup.
3. STANDING: the Aug-11 indicative archiver still matters — nothing
   above captures the 13:25-13:30 indicative WALK, only the print.
4. CLSA: LSEG/BMLL tick history — the institutional endgame, already
   documented in the upgrade tables.
