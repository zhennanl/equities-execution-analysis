"""kdb+/q market-data adapter (agents/kdb_source.py).

No kdb+ server in CI: the adapter takes any callable q->DataFrame, so a
stub returning q-shaped frames exercises the full path — query building,
normalization (bytes syms, keyed-table flattening, minute-typed bars), and
assembly into the standard MarketData contract, through to run_pipeline."""
import numpy as np
import pandas as pd
import pytest

from agents.kdb_source import (KdbSchema, KdbConnectionError, q_daily_query,
                               q_intraday_query, fetch_market_data_kdb,
                               connect_kdb, normalize_intraday)


# ── q-shaped fake result frames (what qpython pandas-mode returns) ─────────

def _q_daily_frame(n=60):
    rng = np.random.RandomState(5)
    dates = pd.bdate_range("2026-04-01", periods=n)
    close = 100 * np.exp(np.cumsum(rng.randn(n) * 0.01))
    return pd.DataFrame({
        "Date": dates.to_numpy().astype("datetime64[D]"),
        "Open": close * (1 + rng.randn(n) * 0.002),
        "High": close * 1.01, "Low": close * 0.99, "Close": close,
        "Volume": np.full(n, 2_000_000.0)})


def _q_intraday_frame(days=5, bars=66, bar_min=5):
    rng = np.random.RandomState(9)
    rows = []
    for d in pd.bdate_range("2026-06-22", periods=days):
        px = 100 * np.exp(np.cumsum(rng.randn(bars) * 0.001))
        for i in range(bars):
            rows.append({
                "date": d.to_numpy().astype("datetime64[D]"),
                # q minute type -> timedelta64 in pandas conversion
                "bar": pd.Timedelta(hours=9, minutes=30 + bar_min * i),
                "Open": px[i], "High": px[i] * 1.001, "Low": px[i] * 0.999,
                "Close": px[i], "Volume": 10_000.0 + rng.rand() * 5_000})
    return pd.DataFrame(rows)


def _fake_query(q: str) -> pd.DataFrame:
    return _q_intraday_frame() if "xbar" in q else _q_daily_frame()


# ── query builders ─────────────────────────────────────────────────────────

def test_query_builders_default_schema():
    qi = q_intraday_query(KdbSchema(), "AAPL")
    assert "5 xbar time.minute" in qi and 'sym=`$"AAPL"' in qi and "from trade" in qi
    qd = q_daily_query(KdbSchema(), "AAPL")
    assert "from daily" in qd and "Close:close" in qd and ".z.d-92" in qd


def test_query_builders_respect_custom_schema():
    sch = KdbSchema(trade_table="tick_eq", daily_table="eod_bars",
                    sym_col="ric", time_col="tstamp", price_col="px",
                    size_col="qty")
    qi = q_intraday_query(sch, "7203.T", bar_minutes=10)
    assert "from tick_eq" in qi and "10 xbar tstamp.minute" in qi
    assert "sum qty" in qi and "first px" in qi and 'ric=`$"7203.T"' in qi


# ── end-to-end on the stub ─────────────────────────────────────────────────

@pytest.fixture(scope="module")
def md():
    return fetch_market_data_kdb(_fake_query, "AAPL", "US")


def test_marketdata_contract(md):
    assert list(md.daily.columns[:5]) == ["Open", "High", "Low", "Close", "Volume"]
    assert isinstance(md.intraday.index, pd.DatetimeIndex)
    assert md.intraday.index.is_monotonic_increasing
    assert md.adv_shares == pytest.approx(2_000_000.0)
    assert md.current_price == pytest.approx(float(md.daily["Close"].iloc[-1]))
    assert np.isfinite(md.realized_vol_ann) and md.realized_vol_ann > 0
    assert md.vol_profile["volume_pct"].sum() == pytest.approx(1.0)
    assert "kdb+" in md.vol_note


def test_intraday_timestamps_assembled_from_date_plus_bar(md):
    first = md.intraday.index[0]
    assert (first.hour, first.minute) == (9, 30)
    assert md.intraday.index.normalize().nunique() == 5


def test_pipeline_runs_on_kdb_sourced_data(md):
    from agents.orchestrator import run_pipeline
    ctx = run_pipeline(md, order_pct_adv=5.0, urgency="Medium")
    assert ctx.market_data is md
    assert ctx.order_shares == pytest.approx(md.adv_shares * 0.05)


# ── normalization edges ────────────────────────────────────────────────────

def test_normalize_handles_int_minute_bars():
    df = _q_intraday_frame(days=1, bars=4)
    df["bar"] = [570, 575, 580, 585]              # int minutes-since-midnight
    out = normalize_intraday(df, KdbSchema())
    assert out.index[0].hour == 9 and out.index[0].minute == 30


def test_empty_result_raises_actionable_error():
    def empty_query(q):
        f = _fake_query(q)
        return f.iloc[0:0]
    with pytest.raises(ValueError, match="no intraday bars"):
        fetch_market_data_kdb(empty_query, "NOSUCH", "US")


def test_connect_without_driver_or_server_raises_kdb_error():
    # Sandbox has neither qpython/pykx installed nor a q process listening —
    # either way the user must get a KdbConnectionError with a next step.
    with pytest.raises(KdbConnectionError):
        connect_kdb("127.0.0.1", 4999, timeout=0.5)
