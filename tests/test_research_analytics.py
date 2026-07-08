"""Research-grounded microstructure + Asian-market + client analytics
(docs/MICROSTRUCTURE_RESEARCH_IMPROVEMENTS.md)."""
import numpy as np
import pandas as pd
import pytest

from agents.microstructure_analytics import (
    edge_spread, estimate_spread_edge, amihud_illiquidity, intraday_seasonality,
    acf, ljung_box,
)
from agents.asian_markets import (
    price_limit_pct, price_limit_flag, closing_auction_concentration,
)
from agents.client_analytics import benchmark_scorecard, client_report


# ── EDGE spread (Ardia-Guidotti-Kroencke 2024) ─────────────────────────────

def test_edge_recovers_injected_spread():
    rng = np.random.RandomState(0)
    n, s_true = 600, 0.01
    half = s_true / 2
    o = np.full(n, 100.0)
    h = np.full(n, 100.0 * (1 + half))
    l = np.full(n, 100.0 * (1 - half))
    c = 100.0 * (1 + half * rng.choice([-1.0, 1.0], n))
    est = edge_spread(o, h, l, c)
    assert est == pytest.approx(s_true, abs=0.002)


def test_edge_needs_three_obs():
    assert np.isnan(edge_spread([1, 2], [1, 2], [1, 2], [1, 2]))


def test_estimate_spread_edge_shape():
    rng = np.random.RandomState(1)
    px = 100 + np.cumsum(rng.randn(60))
    daily = pd.DataFrame({"Open": px, "High": px * 1.002, "Low": px * 0.998, "Close": px})
    out = estimate_spread_edge(daily)
    assert out["spread_bps"] is not None and out["half_spread_bps"] == pytest.approx(out["spread_bps"] / 2, abs=0.01)


# ── Amihud illiquidity ─────────────────────────────────────────────────────

def test_amihud_higher_when_less_volume():
    rng = np.random.RandomState(2)
    px = 100 + np.cumsum(rng.randn(60) * 0.5)
    liquid = pd.DataFrame({"Close": px, "Volume": np.full(60, 1e7)})
    illiquid = pd.DataFrame({"Close": px, "Volume": np.full(60, 1e5)})
    a_liq = amihud_illiquidity(liquid)["impact_bps_per_1m"]
    a_illiq = amihud_illiquidity(illiquid)["impact_bps_per_1m"]
    assert a_illiq > a_liq > 0


# ── Intraday seasonality ───────────────────────────────────────────────────

def _u_shaped_intraday(days=3, n=78):
    frames = []
    base = pd.Timestamp("2026-06-01 09:30")
    for d in range(days):
        i = np.arange(n)
        u = 1 + 2 * ((i - (n - 1) / 2) / ((n - 1) / 2)) ** 2
        idx = pd.date_range(base + pd.Timedelta(days=d), periods=n, freq="5min")
        frames.append(pd.DataFrame({"Volume": u * 1000}, index=idx))
    return pd.concat(frames)


def test_seasonality_detects_u_shape():
    out = intraday_seasonality(_u_shaped_intraday())
    assert out["u_shape_ratio"] > 1.3       # open+close heavier than midday
    assert out["buckets"]["open"] > out["buckets"]["midday"]


def test_seasonality_flat_is_near_one():
    idx = pd.date_range("2026-06-01 09:30", periods=78, freq="5min")
    flat = pd.DataFrame({"Volume": np.full(78, 1000.0)}, index=idx)
    out = intraday_seasonality(flat)
    assert out["u_shape_ratio"] == pytest.approx(1.0, abs=0.1)


# ── Time series (ACF + Ljung-Box) ──────────────────────────────────────────

def test_acf_recovers_ar1():
    rng = np.random.RandomState(3)
    e = np.zeros(2000)
    for t in range(1, 2000):
        e[t] = 0.6 * e[t - 1] + rng.randn()
    assert acf(e, 5)[1] == pytest.approx(0.6, abs=0.08)


def test_ljung_box_detects_serial_dependence():
    rng = np.random.RandomState(4)
    ar = np.zeros(500)
    for t in range(1, 500):
        ar[t] = 0.7 * ar[t - 1] + rng.randn()
    assert ljung_box(ar, 10)["autocorrelated"] is True
    assert ljung_box(rng.randn(500), 10)["autocorrelated"] is False


# ── Asian markets: price limits + closing auction ──────────────────────────

def test_china_price_limit_band():
    assert price_limit_pct("China-A Shanghai") == 10.0
    assert price_limit_pct("Korea (KRX)") == 30.0
    assert price_limit_pct("US") is None


def test_buy_limit_above_band_blocks():
    f = price_limit_flag("China-A Shanghai", limit_price=120.0, last_price=100.0, side="Buy")
    assert f["severity"] == "BLOCK"          # +20% > +10% band => can never fill


def test_sell_limit_below_band_blocks():
    f = price_limit_flag("Taiwan (TWSE)", limit_price=85.0, last_price=100.0, side="Sell")
    assert f["severity"] == "BLOCK"          # -15% < -10% band


def test_limit_within_band_is_info_or_warn():
    f = price_limit_flag("China-A Shanghai", limit_price=103.0, last_price=100.0, side="Buy")
    assert f["severity"] in ("INFO", "WARN")


def test_no_limit_market_returns_none_severity():
    f = price_limit_flag("US", limit_price=200.0, last_price=100.0, side="Buy")
    assert f["severity"] is None


def test_closing_auction_concentration_flags_close_heavy_day():
    idx = pd.date_range("2026-06-01 09:30", periods=78, freq="5min")
    vol = np.full(78, 100.0)
    vol[-8:] = 5000.0                         # heavy close
    intr = pd.DataFrame({"Volume": vol}, index=idx)
    out = closing_auction_concentration(intr)
    assert out["close_share_pct"] > 15.0 and out["concentrated"] is True


# ── Client analytics: scorecard + report ───────────────────────────────────

def test_scorecard_grades_by_history_percentile():
    hist = list(range(0, 100))          # historical total costs 0..99
    sc = benchmark_scorecard(realized_cost_bps=10.0,
                             benchmark_slippages={"Arrival": -2.0, "VWAP": 1.5},
                             model_expected_bps=12.0, hist_total_costs=hist)
    assert sc["grade"] == "A"           # 10 is in the low percentile
    assert sc["percentile"] <= 25
    assert sc["improvement_bps"] > 0    # cheaper than the median (49.5)
    assert sc["model_delta_bps"] == pytest.approx(-2.0)


def test_scorecard_verdicts():
    sc = benchmark_scorecard(5.0, {"Arrival": -3.0, "VWAP": 0.0, "Close": 4.0})
    verdicts = dict(zip(sc["table"]["benchmark"], sc["table"]["verdict"]))
    assert verdicts["Arrival"] == "outperformed"
    assert verdicts["VWAP"] == "in line"
    assert verdicts["Close"] == "underperformed"


def test_client_report_contains_key_sections():
    sc = benchmark_scorecard(5.0, {"Arrival": -3.0}, hist_total_costs=list(range(50)))
    md = client_report({
        "ticker": "2330.TW", "market": "Taiwan (TWSE)", "side": "Buy",
        "order_pct_adv": 5, "algo": "VWAP", "realized_cost_bps": 5.0,
        "benchmarks": {"Arrival": -3.0, "VWAP": 1.2},
        "spreads": {"Corwin-Schultz": 8.0, "EDGE": 6.5},
        "amihud_impact_bps_per_1m": 0.4,
        "auction": {"close_share_pct": 22.0, "concentrated": True},
        "scorecard": sc,
        "price_limit": {"severity": "WARN", "message": "near the ±10% band"},
        "recommendation": "Shift more size into the closing auction.",
    })
    assert "# Execution Quality Review — 2330.TW" in md
    assert "Benchmark performance" in md
    assert "Closing-auction concentration" in md
    assert "WARN" in md
    assert "Recommendation" in md


def test_client_report_handles_missing_keys():
    md = client_report({"ticker": "AAPL"})
    assert "AAPL" in md and "Execution Quality Review" in md
