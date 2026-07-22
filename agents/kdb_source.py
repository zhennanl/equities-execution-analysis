"""kdb+/q market-data source — plug an existing tick database into the
platform as a drop-in replacement for the yfinance fetch.

Design:
    connect_kdb()  -> a thin handle wrapping qpython or PyKX IPC (whichever
                      is installed), exposing .query(q_string) -> DataFrame.
    KdbSchema      -> the user's table/column names (every site names their
                      trade table differently); defaults follow the canonical
                      kdb+ tick schema (trade: date/sym/time/price/size).
    q_daily_query / q_intraday_query
                   -> the exact q sent over IPC. Intraday bars are built
                      SERVER-side with `xbar` (that's the whole point of
                      having kdb+ — don't drag ticks over the wire).
    fetch_market_data_kdb(query_fn, ...)
                   -> runs both queries, normalizes the frames, and hands
                      them to agent1's assemble_market_data — so the
                      pipeline receives the IDENTICAL MarketData contract
                      and never knows the source.

`query_fn` is duck-typed (any callable q_string -> DataFrame), which keeps
the adapter fully testable without a live kdb+ server and lets a site swap
in their own gateway wrapper (auth, entitlements, query throttles).

Honest boundaries: this queries an EOD/intraday HDB-style store. It does not
subscribe to a tickerplant (.u.sub), handle sym enumeration domains, or
paginate huge date ranges — see docs/KDB_INTEGRATION.md for the production
notes.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

DEFAULT_PORT = 5000
DAILY_LOOKBACK_CAL_DAYS = 92     # ~60 trading days, matches the yfinance path
INTRADAY_LOOKBACK_CAL_DAYS = 9   # ~5 trading days, matches the yfinance path
DEFAULT_BAR_MINUTES = 5


class KdbConnectionError(RuntimeError):
    """Connection/driver failures, with an actionable message."""


@dataclass
class KdbSchema:
    """Table/column mapping for the user's database. Defaults = the
    canonical kdb+ tick schema. Every field is overridable from the UI."""
    daily_table: str = "daily"     # EOD bars: date, sym, open, high, low, close, volume
    trade_table: str = "trade"     # ticks: date, sym, time, price, size
    sym_col: str = "sym"
    date_col: str = "date"
    time_col: str = "time"         # time/timestamp type castable with .minute
    price_col: str = "price"
    size_col: str = "size"
    open_col: str = "open"
    high_col: str = "high"
    low_col: str = "low"
    close_col: str = "close"
    volume_col: str = "volume"


# ── q query builders ───────────────────────────────────────────────────────

def q_daily_query(schema: KdbSchema, sym: str,
                  lookback_days: int = DAILY_LOOKBACK_CAL_DAYS) -> str:
    """EOD OHLCV for one symbol, renamed server-side to the platform's
    column contract."""
    c = schema
    return (f"0!select Date:{c.date_col}, Open:{c.open_col}, High:{c.high_col}, "
            f"Low:{c.low_col}, Close:{c.close_col}, Volume:{c.volume_col} "
            f"from {c.daily_table} where {c.sym_col}=`$\"{sym}\", "
            f"{c.date_col}>=.z.d-{int(lookback_days)}")


def q_intraday_query(schema: KdbSchema, sym: str,
                     bar_minutes: int = DEFAULT_BAR_MINUTES,
                     lookback_days: int = INTRADAY_LOOKBACK_CAL_DAYS) -> str:
    """N-minute bars aggregated SERVER-side from the trade table with xbar —
    ticks never cross the wire."""
    c = schema
    return (f"0!select Open:first {c.price_col}, High:max {c.price_col}, "
            f"Low:min {c.price_col}, Close:last {c.price_col}, "
            f"Volume:sum {c.size_col} "
            f"by {c.date_col}, bar:{int(bar_minutes)} xbar {c.time_col}.minute "
            f"from {c.trade_table} where {c.date_col}>=.z.d-{int(lookback_days)}, "
            f"{c.sym_col}=`$\"{sym}\"")


# ── connection ─────────────────────────────────────────────────────────────

class KdbHandle:
    """Uniform wrapper over qpython QConnection / PyKX SyncQConnection."""

    def __init__(self, raw, kind: str):
        self._raw, self.kind = raw, kind

    def query(self, q: str) -> pd.DataFrame:
        if self.kind == "qpython":
            out = self._raw.sendSync(q)
        else:                                   # pykx
            out = self._raw(q).pd()
        df = pd.DataFrame(out)
        # keyed-table results arrive with the keys in the index — flatten
        if df.index.nlevels > 1 or df.index.name is not None:
            df = df.reset_index()
        # qpython returns symbols as bytes
        for col in df.columns:
            if df[col].dtype == object and len(df) and isinstance(df[col].iloc[0], bytes):
                df[col] = df[col].str.decode("utf-8")
        return df

    def close(self):
        try:
            self._raw.close()
        except Exception:
            pass


def connect_kdb(host: str, port: int = DEFAULT_PORT, username: str = "",
                password: str = "", timeout: float = 5.0) -> KdbHandle:
    """Open an IPC connection with whichever driver is installed
    (qpython preferred: pure Python, no license; PyKX unlicensed IPC as
    fallback). Raises KdbConnectionError with an actionable message."""
    try:
        from qpython.qconnection import QConnection
        try:
            raw = QConnection(host=host, port=int(port),
                              username=username or None,
                              password=password or None,
                              pandas=True, timeout=timeout)
            raw.open()
            return KdbHandle(raw, "qpython")
        except Exception as e:
            raise KdbConnectionError(
                f"qpython could not reach kdb+ at {host}:{port} — {e}. "
                "Check the process is listening (\\p in the q session), the "
                "port, and any -u/-U auth file.") from e
    except ImportError:
        pass
    try:
        import pykx as kx
        try:
            raw = kx.SyncQConnection(host=host, port=int(port),
                                     username=username or None,
                                     password=password or None,
                                     timeout=timeout)
            return KdbHandle(raw, "pykx")
        except Exception as e:
            raise KdbConnectionError(
                f"PyKX could not reach kdb+ at {host}:{port} — {e}.") from e
    except ImportError:
        pass
    raise KdbConnectionError(
        "No kdb+ driver installed. Install one of:  pip install qpython  "
        "(pure Python, no license)  or  pip install pykx  (KX official; "
        "unlicensed mode supports IPC). Then reconnect.")


# ── normalization + assembly ───────────────────────────────────────────────

def _col(df: pd.DataFrame, name: str) -> str:
    """Case-insensitive column lookup (q results are usually lowercase)."""
    for c in df.columns:
        if str(c).lower() == name.lower():
            return c
    raise KeyError(f"column '{name}' not in result columns {list(df.columns)}")


def _to_timedelta(series: pd.Series) -> pd.Series:
    """Bar keys arrive as q minute (timedelta64), datetime.time, or int
    minutes depending on driver/schema — normalize to timedelta."""
    if np.issubdtype(series.dtype, np.timedelta64):
        return pd.to_timedelta(series)
    first = series.iloc[0]
    if hasattr(first, "hour"):                          # datetime.time
        return series.map(lambda t: pd.Timedelta(hours=t.hour, minutes=t.minute))
    return pd.to_timedelta(series.astype(float), unit="m")


def normalize_daily(df: pd.DataFrame) -> pd.DataFrame:
    out = pd.DataFrame({
        k: pd.to_numeric(df[_col(df, k)], errors="coerce")
        for k in ("Open", "High", "Low", "Close", "Volume")})
    out.index = pd.DatetimeIndex(pd.to_datetime(df[_col(df, "Date")]))
    return out.sort_index().dropna(subset=["Close"])


def normalize_intraday(df: pd.DataFrame, schema: KdbSchema) -> pd.DataFrame:
    out = pd.DataFrame({
        k: pd.to_numeric(df[_col(df, k)], errors="coerce")
        for k in ("Open", "High", "Low", "Close", "Volume")})
    dates = pd.to_datetime(df[_col(df, schema.date_col)])
    bars = _to_timedelta(df[_col(df, "bar")])
    out.index = pd.DatetimeIndex(dates.to_numpy() + bars.to_numpy())
    return out.sort_index().dropna(subset=["Close"])


def fetch_market_data_kdb(query_fn, ticker: str, market: str,
                          schema: KdbSchema = None,
                          bar_minutes: int = DEFAULT_BAR_MINUTES, log=None):
    """Fetch from kdb+ and assemble the standard MarketData contract.

    `query_fn`: KdbHandle, or any callable q_string -> DataFrame (a site
    gateway, or a test stub). `ticker` is the sym AS STORED in the user's
    database — no Yahoo-style suffixing is applied.
    """
    def _log(msg):
        if log:
            log(msg)
    schema = schema or KdbSchema()
    q = query_fn.query if hasattr(query_fn, "query") else query_fn

    qi = q_intraday_query(schema, ticker, bar_minutes=bar_minutes)
    _log(f"kdb+ intraday query: `{qi}`")
    intraday = normalize_intraday(q(qi), schema)
    if intraday.empty:
        raise ValueError(f"kdb+ returned no intraday bars for sym '{ticker}' "
                         f"in {schema.trade_table} (last "
                         f"{INTRADAY_LOOKBACK_CAL_DAYS} days).")
    _log(f"Intraday: {len(intraday)} bars across "
         f"{intraday.index.normalize().nunique()} days")

    qd = q_daily_query(schema, ticker)
    _log(f"kdb+ daily query: `{qd}`")
    daily = normalize_daily(q(qd))
    if daily.empty:
        raise ValueError(f"kdb+ returned no daily bars for sym '{ticker}' "
                         f"in {schema.daily_table}.")
    _log(f"Daily: {len(daily)} trading days")

    from agents.agent1_market_data import assemble_market_data
    return assemble_market_data(ticker, market, intraday, daily,
                                shares_outstanding=None, log=log,
                                source=f"kdb+ ({schema.trade_table}/"
                                       f"{schema.daily_table})")
