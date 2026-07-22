"""Counterfactual impact propagator — kernel math, causality, composition,
and the sensitivity-band verdict. All offline."""
import numpy as np
import pandas as pd
import pytest

from agents.impact_propagator import (ImpactKernel, propagate_impact,
                                      apply_kernel_to_schedule,
                                      counterfactual_with_bands)
from tests.conftest import make_market_data


def test_kernel_decay_and_permanent_floor():
    # one buy fill of 1% ADV at bar 0; sigma_d=0.02; eta=0.5, perm 40%, t1/2=4
    k = ImpactKernel(eta=0.5, perm_frac=0.4, half_life_bars=4.0)
    p = propagate_impact(np.array([0]), np.array([10_000.0]), 20,
                         sigma_daily=0.02, adv_shares=1_000_000.0, side="Buy", kernel=k)
    inst = 0.5 * 0.02 * np.sqrt(0.01) * 1e4          # 10 bps instantaneous
    assert p[0] == 0.0                                # causal: own bar untouched here
    assert p[1] == pytest.approx(0.4*inst + 0.6*inst*0.5**(1/4), rel=1e-9)
    assert p[5] == pytest.approx(0.4*inst + 0.6*inst*0.5**(5/4), rel=1e-9)
    # far future -> permanent floor only
    assert p[19] == pytest.approx(0.4*inst + 0.6*inst*0.5**(19/4), rel=1e-9)
    assert p[19] > 0.4*inst and p[19] - 0.4*inst < 0.05 * inst
    # decays toward the floor monotonically
    assert np.all(np.diff(p[1:]) < 0)


def test_causality_and_sell_mirror():
    k = ImpactKernel(eta=0.5, perm_frac=0.5, half_life_bars=3.0)
    buy = propagate_impact(np.array([10]), np.array([40_000.0]), 30,
                           0.02, 1_000_000.0, "Buy", k)
    sell = propagate_impact(np.array([10]), np.array([40_000.0]), 30,
                            0.02, 1_000_000.0, "Sell", k)
    assert np.all(buy[:11] == 0.0)                    # nothing before/at the fill bar
    assert np.all(buy[11:] > 0.0)                     # buys push the path UP
    assert np.allclose(sell, -buy)                    # sells mirror exactly


def test_aggressive_early_fills_raise_later_costs_for_buys():
    # two schedules, same total: front-loaded vs back-loaded
    idx = pd.date_range("2026-06-04 09:30", periods=12, freq="5min")
    px = np.full(12, 100.0)
    def sched(weights):
        q = np.array(weights, dtype=float)
        return pd.DataFrame({"time": idx, "shares_traded": q, "price": px,
                             "cumulative": q.cumsum()})
    front = sched([50_000]*3 + [0]*9)
    spread_out = sched([12_500]*12)
    bar_index = {t: i for i, t in enumerate(idx)}
    k = ImpactKernel(eta=0.5, perm_frac=0.4, half_life_bars=4.0)
    f = apply_kernel_to_schedule(front, 12, bar_index, 0.02, 1_000_000.0, "Buy", k)
    s = apply_kernel_to_schedule(spread_out, 12, bar_index, 0.02, 1_000_000.0, "Buy", k)
    # both pay positive cross-slice feedback; the flat price path isolates it
    assert f["extra_cost_bps"] > 0 and s["extra_cost_bps"] > 0
    # concave impact: 3 big slices each perturb sqrt(4x q) = 2x per slice, but
    # far fewer perturbing pairs -> which side wins is kernel-dependent; the
    # pinned property is compositionality: repricing never touches quantities
    assert f["n_fills"] == 3 and s["n_fills"] == 12
    assert f["raw_avg_px"] == pytest.approx(100.0) and s["raw_avg_px"] == pytest.approx(100.0)
    assert f["perturbed_avg_px"] > 100.0 and s["perturbed_avg_px"] > 100.0


def test_counterfactual_bands_end_to_end_and_robust_flag():
    md = make_market_data()
    day0 = md.intraday.index[md.intraday.index.normalize()
                             == md.intraday.index.normalize().max()]
    mid = day0[len(day0)//2]
    out = counterfactual_with_bands(md, md.adv_shares*0.05, "TWAP", "Medium",
                                    interventions=[{"checkpoint_time": mid,
                                                    "algo": "IS", "urgency": "High"}],
                                    side="Buy")
    assert out.available
    assert len(out.table) == 6                          # 3 eta x 2 half-life
    assert set(["Base cost (bps)", "Switch cost (bps)",
                "Δ switch − base (bps)"]).issubset(out.table.columns)
    assert out.delta_min_bps <= out.delta_max_bps
    assert out.robust in (True, False)
    assert ("ROBUST" in out.note) == out.robust
    assert len(out.caveats) >= 4
    # feedback columns are side-adverse (>= 0 for a buy)
    assert (out.table["Path feedback, base (bps)"] >= 0).all()
    assert (out.table["Path feedback, switch (bps)"] >= 0).all()


def test_bands_monotone_in_eta():
    md = make_market_data()
    day0 = md.intraday.index[md.intraday.index.normalize()
                             == md.intraday.index.normalize().max()]
    mid = day0[len(day0)//2]
    out = counterfactual_with_bands(md, md.adv_shares*0.10, "TWAP", "Medium",
                                    interventions=[{"checkpoint_time": mid,
                                                    "algo": "POV", "urgency": "High"}],
                                    side="Buy", half_life_grid=(4.0,))
    t = out.table
    fb = t["Path feedback, base (bps)"].to_numpy()
    assert fb[0] < fb[1] < fb[2]                       # eta 0.3 < 0.45 < 0.6
