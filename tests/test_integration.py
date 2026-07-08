"""Offline integration test over a recorded yfinance fixture (AAPL), plus one
live-marked smoke test that actually hits the network (skipped by default).

The fixture (tests/fixtures/AAPL_*.parquet + AAPL_meta.json) was recorded once
via agents.agent1_market_data.fetch_market_data("AAPL", "US"); regenerate it by
re-running that fetch if the schema ever changes. Keeping it in-repo means the
full pre-trade -> simulation -> routing path is exercised on real data shapes
without any network dependency in CI."""
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from agents.agent1_market_data import MarketData
from agents.agent3_algo_simulation import simulate_algos
from agents.agent6_pretrade_posttrade import (
    estimate_spread_corwin_schultz, estimate_spread_abdi_ranaldo,
)
from agents.agent13_venue_router import route_order, bar_volumes_for

FIX = Path(__file__).resolve().parent / "fixtures"


def _load_fixture_market_data() -> MarketData:
    meta = json.load(open(FIX / "AAPL_meta.json"))
    intraday = pd.read_parquet(FIX / "AAPL_intraday.parquet")
    daily = pd.read_parquet(FIX / "AAPL_daily.parquet")
    return MarketData(
        ticker=meta["ticker"], market=meta["market"], intraday=intraday,
        daily=daily, adv_shares=float(meta["adv_shares"]),
        adv_usd=float(meta["adv_usd"]), current_price=float(meta["current_price"]),
        realized_vol_ann=float(meta["realized_vol_ann"]),
        vol_profile=pd.DataFrame(), vol_note=meta.get("vol_note", ""),
    )


@pytest.fixture(scope="module")
def aapl():
    if not (FIX / "AAPL_meta.json").exists():
        pytest.skip("AAPL fixture not recorded")
    return _load_fixture_market_data()


def test_full_simulation_runs_offline_on_real_shapes(aapl):
    sim = simulate_algos(aapl, order_pct_adv=5.0, urgency="Medium")
    assert set(sim.algos) == {"VWAP", "TWAP", "POV", "IS", "MOC", "MOO",
                              "LIQ", "STEALTH"}
    for name, a in sim.algos.items():
        assert 0.0 <= a.completion_pct <= 1.0, name
        assert np.isfinite(a.total_cost_bps), name
        assert a.market_impact_bps >= 0.0, name        # impact is positive-adverse


def test_spread_estimators_run_on_real_daily(aapl):
    cs = estimate_spread_corwin_schultz(aapl.daily, window=20)
    ar = estimate_spread_abdi_ranaldo(aapl.daily, window=20)
    # both should produce a finite, non-negative estimate on 60 daily bars
    assert cs["spread_bps"] is not None and cs["spread_bps"] >= 0.0
    assert ar["spread_bps"] is not None and ar["spread_bps"] >= 0.0


def test_routing_on_a_real_schedule(aapl):
    sim = simulate_algos(aapl, order_pct_adv=5.0, urgency="Medium")
    sched = sim.algos["VWAP"].schedule
    vols = bar_volumes_for(sched, aapl.intraday)
    r = route_order(sched, vols, "US", policy="Cost-optimized", half_spread_bps=2.0)
    assert r.routed_shares == pytest.approx(sched["shares_traded"].sum(), rel=1e-6)
    assert np.isfinite(r.blended_cost_bps)


# ── Live smoke (network) — skipped unless `pytest -m live` ──────────────────

@pytest.mark.live
def test_live_fetch_market_data():
    from agents.agent1_market_data import fetch_market_data
    md = fetch_market_data("AAPL", "US")
    assert md.adv_shares > 0
    assert md.current_price > 0
    assert len(md.intraday) > 50
    assert {"Open", "High", "Low", "Close", "Volume"}.issubset(md.intraday.columns)
