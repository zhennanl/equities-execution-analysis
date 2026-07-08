"""
Shared pytest fixtures and synthetic-data builders for the execution-analytics
test suite.

Everything here is OFFLINE and DETERMINISTIC — no network, fixed RNG seeds — so
`pytest -m "not live"` runs anywhere (including CI) and reproduces the
hand-verified regression anchors documented in docs/HANDOFF_2026-07-08.md §6.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

# Deterministic bytecode location (mirrors the P-2 stale-.pyc protocol) and
# make the repo root importable so `import agents.*` works from tests/.
os.environ.setdefault("PYTHONPYCACHEPREFIX", "/tmp/pycache")
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures"


# ── Intraday / daily synthetic builders ────────────────────────────────────

def _one_day_bars(date: pd.Timestamp, n_bars: int, base: float,
                  drift_per_bar: float, wick_frac: float, seed: int,
                  vol_base: float = 10_000.0) -> pd.DataFrame:
    """Build one trading day of 5-minute OHLCV bars.

    Close follows a deterministic linear drift off `base`; High/Low carry a
    symmetric up/down wick of `wick_frac` around Close; Volume is a mild U-shape.
    """
    rng = np.random.RandomState(seed)
    idx = pd.date_range(date + pd.Timedelta("9h30min"), periods=n_bars, freq="5min")
    i = np.arange(n_bars)
    close = base + drift_per_bar * i
    open_ = np.concatenate([[close[0]], close[:-1]])
    high = close * (1 + wick_frac)
    low = close * (1 - wick_frac)
    # U-shaped intraday volume (heavier at open/close) + light noise
    u = 1.0 + 1.5 * ((i - (n_bars - 1) / 2) / ((n_bars - 1) / 2)) ** 2
    volume = vol_base * u * (1 + 0.02 * rng.randn(n_bars))
    return pd.DataFrame(
        {"Open": open_, "High": high, "Low": low, "Close": close,
         "Volume": np.clip(volume, 1.0, None)},
        index=idx,
    )


def make_intraday(n_days: int = 4, n_bars: int = 78, base: float = 100.0,
                  seed: int = 7) -> pd.DataFrame:
    """Several consecutive trading days of intraday bars (for hist-curve build)."""
    days = []
    d = pd.Timestamp("2026-06-01")
    made = 0
    off = 0
    while made < n_days:
        day = d + pd.Timedelta(days=off)
        off += 1
        if day.weekday() >= 5:            # skip weekends
            continue
        days.append(_one_day_bars(day, n_bars, base=base,
                                  drift_per_bar=0.0, wick_frac=0.001,
                                  seed=seed + made))
        made += 1
    return pd.concat(days)


def make_daily(n: int = 90, base: float = 100.0, ann_vol: float = 0.20,
               seed: int = 11) -> pd.DataFrame:
    """Daily OHLCV built from a per-day GBM path so Yang-Zhang can recover
    `ann_vol`. Each day = 64 intraday GBM steps; OHLC taken from that path."""
    rng = np.random.RandomState(seed)
    sig_d = ann_vol / np.sqrt(252)
    steps = 64
    idx = pd.bdate_range("2026-01-02", periods=n)
    rows = []
    prev_close = base
    for _ in range(n):
        incr = rng.randn(steps) * (sig_d / np.sqrt(steps))
        path = prev_close * np.exp(np.cumsum(incr))
        o, c = path[0], path[-1]
        h, l = path.max(), path.min()
        rows.append((o, h, l, c, 1_000_000.0))
        prev_close = c
    return pd.DataFrame(rows, columns=["Open", "High", "Low", "Close", "Volume"],
                        index=idx)


def make_market_data(ticker: str = "TEST", market: str = "US",
                     order_seed: int = 7):
    """A fully-formed MarketData object with no network access."""
    from agents.agent1_market_data import MarketData, yang_zhang_vol_ann
    intraday = make_intraday(seed=order_seed)
    daily = make_daily()
    adv_shares = float(daily["Volume"].mean())
    current_price = float(daily["Close"].iloc[-1])
    yz = yang_zhang_vol_ann(daily)
    vol_ann = float(yz) if np.isfinite(yz) else 0.20
    return MarketData(
        ticker=ticker, market=market, intraday=intraday, daily=daily,
        adv_shares=adv_shares, adv_usd=adv_shares * current_price,
        current_price=current_price, realized_vol_ann=vol_ann,
        vol_profile=pd.DataFrame(), shares_outstanding=None,
        rv_intraday_ann=None, vol_note="synthetic",
    )


def make_day(n_bars: int = 78, close_base: float = 100.0,
             drift_per_bar: float = 0.0, wick_frac: float = 0.0,
             vol: float = 1000.0) -> pd.DataFrame:
    """A single day of bars used to test the private _sim_* schedulers directly
    (bypasses MarketData / _sim_day). Open[0] == close_base so a caller can use
    close_base as the arrival price."""
    idx = pd.date_range("2026-06-15 09:30", periods=n_bars, freq="5min")
    i = np.arange(n_bars)
    close = close_base + drift_per_bar * i
    open_ = np.concatenate([[close_base], close[:-1]])
    high = close * (1 + wick_frac)
    low = close * (1 - wick_frac)
    return pd.DataFrame(
        {"Open": open_, "High": high, "Low": low, "Close": close,
         "Volume": np.full(n_bars, vol)},
        index=idx,
    )


@pytest.fixture
def market_data():
    return make_market_data()
