# Can the Taiwan pipeline be pointed at other markets?

Probed live 2026-08-08 from one machine, anonymous requests,
no keys. Status codes are what came back, not what the docs
promise. Re-run: the probe block is in the c-163 session note.

## What Taiwan actually uses — the four endpoints

| # | Endpoint | Gives us |
|---|---|---|
| 1 | `twse.com.tw/rwd/zh/afterTrading/MI_INDEX?type=ALL` | every TWSE name's daily close + volume |
| 2 | `twse.com.tw/rwd/zh/fund/MI_QFIIS` | shares issued + foreign holding (drives §2.2.8 foreign room) |
| 3 | `tpex.org.tw/www/zh-tw/afterTrading/otc?type=EW` | every TPEx name's daily close + volume |
| 4 | `opendata.tdcc.com.tw/getOD.ashx?id=1-5` | shareholder bracket distribution — the float PROXY |

**TPEx was not forgotten.** The 1,955-row universe at
2026-07-20 is 1,081 TWSE + 874 TPEx. Both boards are in, which
is why Sino-American Silicon (5483, TPEx) survives into the
MIEU.

Taiwan is unusually generous: one request returns the whole
board priced, and the day-files are archival, so they include
companies that have since delisted. That is what makes Taiwan
delisted-safe.

## What the other markets actually serve

**Tier A — full day-file, priced, one request.** The Taiwan
pattern works as-is.

| Market | Endpoint | Probe |
|---|---|---|
| India | `archives.nseindia.com/products/content/sec_bhavdata_full_DDMMYYYY.csv` | 200, 374 KB, all symbols priced |
| Taiwan | above | 200 |

**Tier B — listing master only, no prices.** You get the
universe free and delisted-safe, then must source price and
shares per name.

| Market | Endpoint | Probe |
|---|---|---|
| Japan | JPX `data_j.xls` | 200, 4,444 rows — code, name, segment, TOPIX size class. No price. |
| Hong Kong | HKEX `ListOfSecurities.xlsx` | 200, 1.4 MB |
| China (SSE) | `query.sse.com.cn/sseQuery/commonQuery.do` | 200 — includes `LIST_DATE`, `DELIST_DATE`, `FULL_NAME_IN_ENGLISH`. Delisted-safe universe AND an English name bridge. |

**Tier C — walled from an anonymous client.**

| Market | Barrier |
|---|---|
| Korea (KRX) | 400 `LOGOUT` — needs an OTP-issued session token |
| Shenzhen | SSL handshake refused from this host |
| Thailand, Indonesia, Malaysia | 403 — Akamai / Cloudflare bot wall |

## Does the size screen collapse the workload?

Partly — and the part it does not collapse is the part that
decides feasibility.

**Where the argument holds.** The expensive, per-name inputs —
free float, ATVR, foreign room — are only needed for names that
could plausibly sit near the cutoff. In Taiwan the size screen
took 1,955 down to ~425 before any of that was fetched, and we
only ever measured ATVR for 604 names. Downstream cost scales
with the BAND, not the market.

**Where it does not.** You cannot apply the size screen without
a market cap for every listed name, and market cap is
price x shares. That is precisely what Tier B and Tier C do not
give you. The cheap screen is only cheap where a priced
day-file exists.

So the binding constraint is not compute and not the number of
listed companies. It is whether the market publishes a priced
bulk file.

## Feasibility, market by market

| Market | Verdict | What it needs |
|---|---|---|
| Taiwan | DONE | — |
| India | Ready | bhavcopy already harvested for event windows; point the MIEU builder at it |
| Japan | Medium | JPX gives the 4,444-name universe; prices must come per-name. The TOPIX size class in the master is a usable pre-filter to cut the price fetch to a few hundred |
| Hong Kong | Medium | same shape as Japan |
| China | Medium-hard | SSE master is good and delisted-safe; SZSE blocked from here; universe is ~5,400 across both boards |
| Korea | Hard | KRX needs a session/OTP flow, or a paid feed |
| Thailand / Indonesia / Malaysia | Hard | bot walls; needs a browser-context fetch or a vendor |

**The encouraging number:** MSCI Standard cutoffs are high
enough that the band stays small everywhere. MSCI Japan holds
~230 names and MSCI China ~700, so even in the largest markets
the population within striking distance of the cutoff is a few
hundred — the same order as Taiwan's 398-name MIEU. The work
does not scale with listed-company count.

## Honest caveats carried over from Taiwan

- Our liquidity screen dropped ZERO names, because ATVR was
  measured for 604 of 1,955 and the rest were carried as
  NOT_EVALUATED. It did not bind. Same risk in any new market.
- §2.2.9 financial reporting is NOT_EVALUATED for everything.
- The TDCC float is a proxy, calibrated on the Yahoo overlap.
  No other market has a TDCC equivalent, so each new market
  needs its own float source ranked into the tier stack.

---

# Addendum (c-164): Yahoo largely dissolves the Tier B/C wall

Bill asked whether Yahoo could fill the gap for the markets
with no priced bulk file, or whether it would be too many
requests. Measured, not assumed — all probed 2026-08-08.

## The batch endpoint, which changes the arithmetic

`query1.finance.yahoo.com/v7/finance/quote` returns **500
symbols per call** carrying `marketCap`, `sharesOutstanding`,
`regularMarketPrice` and `longName`. It needs a crumb, which
is two extra requests:

```
GET https://fc.yahoo.com                     -> sets the cookie
GET .../v1/test/getcrumb                     -> returns crumb
GET .../v7/finance/quote?symbols=...&crumb=  -> 500 at a time
```

Without the crumb it is a flat 401.

**So the whole of Japan is 9 requests, not 4,005.** The JPX
master gives 4,005 four-digit codes; at 500 per call that is
nine batches, a few seconds. The "too many requests" worry
does not survive contact with the batch endpoint.

Per-name history, where it is needed, is also cheap: the chart
endpoint ran 8.8 req/s on 8 threads, so 4,005 names of daily
history is about 8 minutes.

## Tier C: Yahoo covers the walled markets

Korea, Thailand, Malaysia and Indonesia all returned quotes
with `marketCap` AND `sharesOutstanding` through the same batch
call. The exchange bot-wall is irrelevant to the size screen.

Tier C's real gap was never prices — it was not knowing WHICH
symbols to ask for. That is closed too: the screener
enumerates by region, sorted by market cap descending, 100 per
page.

```
POST .../v1/finance/screener?crumb=...
  query: region == "kr" AND intradaymarketcap > 1e9
  sortField: intradaymarketcap, sortType: DESC
```

Returned 200 with a total and a cap-ranked list headed by
Samsung Electronics. Because it sorts by cap descending, you
paginate only until you drop below the market's cutoff — a
handful of pages per market, never the whole tail.

## Revised verdict

| Market | Was | Now |
|---|---|---|
| Japan, HK, China SSE | Tier B, needs prices | universe from the exchange master, prices from 9-20 batch calls |
| Korea, Thailand, Malaysia, Indonesia | Tier C, walled | universe from the screener, prices from the same batch call |

## What Yahoo does NOT fix — the limit that still binds

1. **Survivorship.** Yahoo carries live listings only. Fine for
   a FORWARD prediction; fatal for backtesting deletions,
   because the names that got deleted are exactly the ones
   missing. Taiwan and India keep their standing advantage:
   archival exchange day-files include the dead.
2. **Point-in-time.** `marketCap` and `sharesOutstanding` are
   TODAY's. Historical closes are available per name, but
   historical share counts are not. For a cutoff two to three
   weeks back that is usually harmless — but it is the same
   current-vintage assumption we already carry on Taiwan
   floats, and it must be labelled the same way, not quietly
   absorbed.
3. **Float.** Nothing here supplies FIF. Each new market still
   needs its own float source ranked into the tier stack.

So the honest framing: Yahoo makes the LIVE prediction feasible
in every APAC market. It does not make the BACKTEST feasible
outside Taiwan and India — and without a backtest we have no
measured hit rate, only a method.
