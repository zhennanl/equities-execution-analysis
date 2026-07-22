# kdb+/q Market-Data Integration

*How the platform connects to an existing kdb+ time-series database and
uses it as the market-data source in place of yfinance. Session 6f.*

## Architecture — one contract, many sources

```
yfinance ──┐
           ├─> assemble_market_data(ticker, market, intraday, daily)
kdb+/q  ───┘        └─> MarketData (ADV, Yang-Zhang vol, volume profile, …)
                          └─> run_pipeline(...)   # never knows the source
```

`agents/agent1_market_data.fetch_market_data` was split: the yfinance fetch
stays, and everything derivable from the two raw OHLCV frames moved into
`assemble_market_data`. A source therefore only has to deliver (a) intraday
bars with a DatetimeIndex and (b) daily bars, both with
Open/High/Low/Close/Volume. `agents/kdb_source.py` is the kdb+ deliverer.

## What gets sent over IPC

Bars are aggregated **server-side** — the whole point of owning a kdb+ HDB
is that ticks never cross the wire:

```q
/ intraday: N-minute bars from the trade table
0!select Open:first price, High:max price, Low:min price, Close:last price,
  Volume:sum size
  by date, bar:5 xbar time.minute
  from trade where date>=.z.d-9, sym=`$"AAPL"

/ daily: EOD OHLCV renamed to the platform contract
0!select Date:date, Open:open, High:high, Low:low, Close:close, Volume:volume
  from daily where sym=`$"AAPL", date>=.z.d-92
```

Every table/column name is user-mappable via `KdbSchema` (UI: Page 1 →
"Market data source" expander) because every site names its trade table
differently. Lookbacks (92/9 calendar days) mirror the yfinance path
(60 trading days daily, 5 days intraday) so downstream statistics see the
same window regardless of source.

## Drivers & connection

`connect_kdb` tries **qpython** (pure Python, no license) then **PyKX**
(KX official; unlicensed mode supports IPC), wrapping both behind one
`KdbHandle.query(q) -> DataFrame`. Missing driver or unreachable server →
`KdbConnectionError` with the actionable next step. Neither driver ships
with the platform: `pip install qpython` on the user's machine.

Normalization handles the driver quirks: keyed-table results flattened,
qpython byte-symbols decoded, bar keys accepted as q minute (timedelta),
`datetime.time`, or int minutes.

## Testability without a server

`fetch_market_data_kdb(query_fn, ...)` takes ANY callable
`q_string -> DataFrame` — the live `KdbHandle`, a site gateway wrapper
(auth/entitlements/throttles), or a test stub. The test suite runs the full
path — query build, normalization, assembly, `run_pipeline` — against
q-shaped fake frames (`tests/test_kdb_source.py`, 8 tests).

## Honest boundaries (production notes)

- **HDB-style queries only.** No tickerplant subscription (`.u.sub`), no
  RDB/HDB unioned reads — the live-day bars are whatever the queried
  process can see. A production install points this at a gateway.
- **No sym enumeration handling.** ``sym=`$"..."`` assumes the sym column
  is a symbol; enumerated HDB syms resolve transparently server-side, but
  exotic partitioning (par.txt multi-disk) is untested.
- **No pagination.** Lookbacks are small by design; pointing the intraday
  query at years of ticks would need date-sliced batching.
- **Trust boundary.** The q strings interpolate table/column names from
  user config — fine for a user querying THEIR OWN database (same trust
  domain), but a multi-tenant deployment would whitelist identifiers.
- **Timezones.** Timestamps are used as stored; the yfinance path returns
  exchange-local times, so store bars exchange-local for like-for-like.


## Tick-file ingestion (free historical data, session 6g)

`agents/tick_ingest.py` turns free tick sources into the same MarketData
contract — and into kdb+ itself:

| Source | Loader | Notes |
|---|---|---|
| LOBSTER samples | `load_lobster(file, sym, date)` | ITCH-derived; exec types 4/5; price x10000 |
| Binance public data | `load_binance_trades(file)` | trades/aggTrades, zip OK, ms/us epoch auto |
| Any trades CSV | `load_csv_trades(...)` | explicit column mapping |
| IEX HIST pcap | `load_iex_tops(...)` | optional `pip install IEXTools` |

All parse to one normalized trades frame (date, sym, time, price, size — the
canonical kdb+ trade-table shape). `trades_to_bars` reproduces the q `xbar`
aggregation client-side so a tick file and a live kdb+ produce identical
bars. `market_data_from_trades` assembles MarketData (thin single-day
ADV/vol context is disclosed in vol_note; pass a longer `daily` frame for
production-grade context). `to_kdb_csv` writes a q-loadable csv:

```q
trade:("DSTFF";enlist",")0:`$":trades.csv"
\p 5000
```

…then connect Page 1's kdb+ form to localhost:5000 — real ITCH-derived
ticks served from your own kdb+ instance into the platform.

UI: Page 1 → Market data source → "Tick file". While a tick file is
pinned, the ticker/market inputs are ignored (shown loudly, unload to
release).
