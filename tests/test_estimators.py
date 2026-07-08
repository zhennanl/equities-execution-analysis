"""Volatility & spread estimators recover known synthetic inputs.

Anchors (docs/HANDOFF_2026-07-08.md §6): Yang-Zhang on a 20%-sigma GBM recovers
~0.18-0.20; Corwin-Schultz recovers an injected constant spread on a
zero-drift series."""
import numpy as np
import pandas as pd
import pytest

from agents.agent1_market_data import yang_zhang_vol_ann
from agents.agent6_pretrade_posttrade import (
    estimate_spread_corwin_schultz, estimate_spread_abdi_ranaldo,
)
from conftest import make_daily


def test_yang_zhang_recovers_20pct_gbm():
    daily = make_daily(n=90, ann_vol=0.20, seed=11)
    yz = yang_zhang_vol_ann(daily)
    # statistical estimator on 64-step/day discretization; band is generous
    assert 0.13 < yz < 0.28


def test_yang_zhang_scales_with_input_vol():
    lo = yang_zhang_vol_ann(make_daily(ann_vol=0.15, seed=3))
    hi = yang_zhang_vol_ann(make_daily(ann_vol=0.45, seed=3))
    assert hi > lo


def test_yang_zhang_nan_on_insufficient_data():
    tiny = make_daily(n=3)
    assert np.isnan(yang_zhang_vol_ann(tiny))


def _constant_spread_daily(n: int, price: float, spread_frac: float,
                           seed: int = 5) -> pd.DataFrame:
    """Zero-drift true price; High=ask, Low=bid at a fixed proportional spread;
    Close bounces between bid and ask. Corwin-Schultz should recover ~spread."""
    rng = np.random.RandomState(seed)
    half = spread_frac / 2.0
    idx = pd.bdate_range("2026-01-02", periods=n)
    o = np.full(n, price)
    h = np.full(n, price * (1 + half))
    l = np.full(n, price * (1 - half))
    c = price * (1 + half * rng.choice([-1.0, 1.0], size=n))
    return pd.DataFrame({"Open": o, "High": h, "Low": l, "Close": c,
                         "Volume": np.full(n, 1e6)}, index=idx)


def test_corwin_schultz_recovers_injected_spread():
    injected_bps = 100.0                      # 1% quoted spread
    daily = _constant_spread_daily(60, price=100.0, spread_frac=0.01)
    est = estimate_spread_corwin_schultz(daily, window=20)
    assert est["spread_bps"] is not None
    # CS recovers the spread to within ~25% on a clean constant-spread series
    assert est["spread_bps"] == pytest.approx(injected_bps, rel=0.25)


def test_corwin_schultz_floors_negative_and_reports_n_obs():
    # Constant OHLC (zero range) => estimator floors at 0, still returns n_obs.
    idx = pd.bdate_range("2026-01-02", periods=40)
    flat = pd.DataFrame({"Open": 100.0, "High": 100.0, "Low": 100.0,
                         "Close": 100.0, "Volume": 1e6}, index=idx)
    est = estimate_spread_corwin_schultz(flat, window=20)
    assert est["spread_bps"] == 0.0
    assert est["n_obs"] == 20


def test_corwin_schultz_needs_minimum_bars():
    est = estimate_spread_corwin_schultz(make_daily(n=10), window=20)
    assert est["spread_bps"] is None and est["n_obs"] == 0


def test_abdi_ranaldo_positive_and_same_order_of_magnitude():
    daily = _constant_spread_daily(60, price=100.0, spread_frac=0.01, seed=9)
    ar = estimate_spread_abdi_ranaldo(daily, window=20)
    assert ar["spread_bps"] is not None and ar["spread_bps"] > 0
    # order-of-magnitude agreement with the 100 bps injected spread
    assert 25.0 < ar["spread_bps"] < 400.0
