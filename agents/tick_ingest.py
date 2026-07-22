"""Tick-file ingester — turn free historical tick data into the platform's
MarketData contract, and optionally into a kdb+-loadable trade table.

Supported formats (all genuinely free sources):
    LOBSTER   message files (data.lobsterdata.com samples) — NASDAQ
              ITCH-derived; executions are message types 4 (visible) and
              5 (hidden). Prices are stored x10000.
    Binance   trades / aggTrades monthly CSVs (data.binance.vision) —
              epoch time in ms (pre-2025) or us (2025+), auto-detected.
    generic   any CSV of trades via an explicit column mapping.
    IEX HIST  pcap TOPS files — only if the optional IEXTools package is
              installed (raise with instructions otherwise).

Normalized trades frame (the pivot everything flows through — deliberately
identical to the canonical kdb+ trade-table shape):
    date  (datetime64[ns], midnight)   sym (str)
    time  (timedelta since midnight)   price (float)   size (float)

From there:
    trades_to_bars / trades_to_daily   client-side equivalent of the q
                                       `xbar` aggregation used on live kdb+
    market_data_from_trades            -> agent1.assemble_market_data,
                                       so the pipeline sees the identical
                                       MarketData object
    to_kdb_csv                         write a csv that loads into q with
                                       the 3-liner in the docstring — the
                                       "serve real ticks from my own kdb+"
                                       demo path.

Honest notes: one tick file usually covers ONE day, so the tick-derived
daily frame has one row — Yang-Zhang then falls back to intraday RV and
ADV is that single day's volume (both disclosed in vol_note). Pass a
longer `daily` frame (e.g. from yfinance) to get proper 60-day context
around a real tick tape.
"""
from __future__ import annotations

import io
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

TRADE_COLS = ["date", "sym", "time", "price", "size"]
LOBSTER_COLS = ["time_s", "type", "order_id", "size", "price", "direction"]
LOBSTER_EXEC_TYPES = (4, 5)          # visible / hidden executions
LOBSTER_PRICE_SCALE = 10_000.0


def _finish(df: pd.DataFrame) -> pd.DataFrame:
    df = df[TRADE_COLS].dropna(subset=["price", "size"])
    df = df[(df["price"] > 0) & (df["size"] > 0)]
    return df.sort_values(["date", "time"]).reset_index(drop=True)


def _read_maybe_zip(path, **kw) -> pd.DataFrame:
    """CSV or single-CSV zip (Binance ships zips)."""
    p = Path(path)
    if p.suffix.lower() == ".zip":
        with zipfile.ZipFile(p) as z:
            name = z.namelist()[0]
            with z.open(name) as f:
                return pd.read_csv(io.BytesIO(f.read()), **kw)
    return pd.read_csv(p, **kw)


# ── LOBSTER ────────────────────────────────────────────────────────────────

def load_lobster(message_file, sym: str, trade_date) -> pd.DataFrame:
    """LOBSTER `*_message_*.csv`: time(sec after midnight), type, order_id,
    size, price(x10000), direction — no header. Executions only."""
    df = pd.read_csv(message_file, header=None, usecols=range(6),
                     names=LOBSTER_COLS)
    df = df[df["type"].isin(LOBSTER_EXEC_TYPES)]
    d = pd.Timestamp(trade_date).normalize()
    out = pd.DataFrame({
        "date": d,
        "sym": sym,
        "time": pd.to_timedelta(df["time_s"], unit="s"),
        "price": df["price"].astype(float) / LOBSTER_PRICE_SCALE,
        "size": df["size"].astype(float),
    })
    return _finish(out)


# ── Binance ────────────────────────────────────────────────────────────────

_BINANCE_TRADES = ["trade_id", "price", "qty", "quote_qty", "ts",
                   "is_buyer_maker", "is_best_match"]
_BINANCE_AGG = ["agg_id", "price", "qty", "first_id", "last_id", "ts",
                "is_buyer_maker", "is_best_match"]


def _epoch_to_ts(series: pd.Series) -> pd.Series:
    """Binance switched epoch ms -> us in 2025 files; detect by magnitude."""
    v = series.astype(np.int64)
    unit = "us" if int(v.iloc[0]) > 10 ** 14 else "ms"
    return pd.to_datetime(v, unit=unit)


def load_binance_trades(path, sym: str = "") -> pd.DataFrame:
    """Binance trades OR aggTrades CSV/zip (7 vs 8 columns, auto-detected;
    header row optional — also auto-detected)."""
    raw = _read_maybe_zip(path, header=None, nrows=1)
    has_header = not str(raw.iloc[0, 1]).replace(".", "").isdigit()
    df = _read_maybe_zip(path, header=0 if has_header else None)
    names = _BINANCE_TRADES if df.shape[1] == 7 else _BINANCE_AGG
    df.columns = names[:df.shape[1]]
    ts = _epoch_to_ts(df["ts"])
    out = pd.DataFrame({
        "date": ts.dt.normalize(),
        "sym": sym or "BINANCE",
        "time": ts - ts.dt.normalize(),
        "price": df["price"].astype(float),
        "size": df["qty"].astype(float),
    })
    return _finish(out)


# ── generic CSV ────────────────────────────────────────────────────────────

def load_csv_trades(path, sym: str, timestamp_col: str, price_col: str,
                    size_col: str, epoch_unit: str = "") -> pd.DataFrame:
    """Catch-all: any trades CSV. `epoch_unit` in {"s","ms","us","ns"} for
    numeric epochs; empty = parse as datetime strings."""
    df = _read_maybe_zip(path)
    ts = (pd.to_datetime(df[timestamp_col], unit=epoch_unit) if epoch_unit
          else pd.to_datetime(df[timestamp_col]))
    out = pd.DataFrame({
        "date": ts.dt.normalize(), "sym": sym,
        "time": ts - ts.dt.normalize(),
        "price": pd.to_numeric(df[price_col], errors="coerce"),
        "size": pd.to_numeric(df[size_col], errors="coerce"),
    })
    return _finish(out)


# ── IEX HIST (optional dependency) ─────────────────────────────────────────

def load_iex_tops(pcap_path, syms=None) -> pd.DataFrame:      # pragma: no cover
    """IEX HIST TOPS pcap -> trades, via the optional IEXTools package
    (`pip install IEXTools`). Not bundled: pcap decoding is heavy and the
    sandbox/test suite never exercises it."""
    try:
        from IEXTools import Parser, messages
    except ImportError as e:
        raise ImportError(
            "IEX HIST pcap parsing needs IEXTools: pip install IEXTools — "
            "then re-run. (LOBSTER/Binance/CSV paths work without it.)") from e
    p = Parser(str(pcap_path))
    rows = []
    while True:
        try:
            m = p.get_next_message([messages.TradeReport])
        except StopIteration:
            break
        s = m.symbol.decode() if isinstance(m.symbol, bytes) else str(m.symbol)
        if syms and s not in syms:
            continue
        ts = pd.to_datetime(m.timestamp, unit="ns")
        rows.append({"date": ts.normalize(), "sym": s,
                     "time": ts - ts.normalize(),
                     "price": m.price_int / 1e4, "size": float(m.size)})
    return _finish(pd.DataFrame(rows, columns=TRADE_COLS))


# ── trades -> bars (client-side equivalent of q's xbar) ────────────────────

def trades_to_bars(trades: pd.DataFrame, bar_minutes: int = 5) -> pd.DataFrame:
    """OHLCV bars: `by date, bar_minutes xbar time.minute` done in pandas.
    Identical semantics to the query agents/kdb_source.py sends to a live
    kdb+ — so a tick file and a kdb+ server produce the same bars."""
    t = trades.copy()
    bar = (t["time"].dt.total_seconds() // (bar_minutes * 60)).astype(int)
    t["bar_ts"] = t["date"] + pd.to_timedelta(bar * bar_minutes, unit="m")
    g = t.groupby("bar_ts")
    out = pd.DataFrame({"Open": g["price"].first(), "High": g["price"].max(),
                        "Low": g["price"].min(), "Close": g["price"].last(),
                        "Volume": g["size"].sum()})
    out.index = pd.DatetimeIndex(out.index)
    return out.sort_index()


def trades_to_daily(trades: pd.DataFrame) -> pd.DataFrame:
    g = trades.groupby("date")
    out = pd.DataFrame({"Open": g["price"].first(), "High": g["price"].max(),
                        "Low": g["price"].min(), "Close": g["price"].last(),
                        "Volume": g["size"].sum()})
    out.index = pd.DatetimeIndex(out.index)
    return out.sort_index()


# ── MarketData assembly ────────────────────────────────────────────────────

def market_data_from_trades(trades: pd.DataFrame, market: str,
                            bar_minutes: int = 5, daily: pd.DataFrame = None,
                            log=None):
    """Build the standard MarketData from a normalized trades frame.

    `daily`: optional longer daily OHLCV frame (e.g. yfinance) for proper
    60-day ADV / Yang-Zhang context around a short tick tape; default is
    daily bars derived from the ticks themselves (usually 1 row — the
    estimator fallback and thin ADV are disclosed in vol_note).
    """
    if trades.empty:
        raise ValueError("No trades to assemble — check the file/format/sym.")
    syms = trades["sym"].unique()
    if len(syms) > 1:
        raise ValueError(f"Trades frame has {len(syms)} syms {list(syms)[:5]} — "
                         "filter to one before assembling.")
    intraday = trades_to_bars(trades, bar_minutes)
    d = trades_to_daily(trades) if daily is None else daily
    from agents.agent1_market_data import assemble_market_data
    md = assemble_market_data(str(syms[0]), market, intraday, d,
                              shares_outstanding=None, log=log,
                              source=f"tick file ({len(trades):,} trades)")
    if daily is None and len(d) < 20:
        md.vol_note += (f" ⚠️ daily context is only {len(d)} day(s) of "
                        "tick-derived bars — ADV and vol are thin; supply a "
                        "longer daily history for production-grade context.")
    return md


# ── kdb+ export (the 'serve it from my own kdb+' demo path) ───────────────

def to_kdb_csv(trades: pd.DataFrame, path) -> str:
    """Write the canonical kdb+ trade-table csv. Load into q with:

        trade:("DSTFF";enlist",")0:`$":trades.csv"
        \p 5000

    …then connect the platform's Page-1 kdb+ form to localhost:5000 with
    the default schema. Returns the q load snippet."""
    out = trades.copy()
    out["date"] = pd.to_datetime(out["date"]).dt.strftime("%Y.%m.%d")
    td = out["time"].dt.components
    out["time"] = (td.hours.map("{:02d}".format) + ":"
                   + td.minutes.map("{:02d}".format) + ":"
                   + td.seconds.map("{:02d}".format) + "."
                   + td.milliseconds.map("{:03d}".format))
    out[TRADE_COLS].to_csv(path, index=False)
    return ("trade:(\"DSTFF\";enlist\",\")0:`$\":" + str(path) + "\"; "
            "\\p 5000")
