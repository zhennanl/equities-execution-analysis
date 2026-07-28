"""Event-flow study functions — offline on synthetic paths."""
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

from agents.event_flow_study import (summarize_event, aggregate_study,
                                     grade_strategies, close_auction_share)


def _es(pressure=0.05, reversal=0.5, t_mult=6.0):
    rel = np.arange(-10, 11)
    px = np.concatenate([np.full(5, 100.0),
                         100 * (1 + np.linspace(0, pressure, 6)),
                         100 * (1 + pressure
                                - np.linspace(0, pressure * reversal, 10))])
    ab = np.ones(len(rel)); ab[rel == 0] = t_mult
    ab[(rel >= -5) & (rel < 0)] = 1.8
    car = px / 100.0 - 1.0
    return SimpleNamespace(rel_days=rel, norm_price=px * 100, price_at_T=1.0,
                           ab_vol=ab, car=car, est_avg_volume=1e6,
                           est_sigma_daily=0.02,
                           event_dates=pd.bdate_range("2026-06-04",
                                                      periods=len(rel)))


def test_summarize_recovers_planted_metrics():
    s = summarize_event(_es(), side="Buy", ann_rel=-5, label="X")
    assert s["available"]
    assert s["t_day_volume_multiple"] == pytest.approx(6.0)
    assert s["pre_excess_adv_days"] == pytest.approx(0.8 * 5, abs=0.01)
    assert s["car_drift_to_T_pct"] == pytest.approx(4.0, abs=0.3)   # 4/5 of 5%
    # 50% reversal spread over 10 days -> by T+5 (linspace pt 4/9):
    # 0.5 * 4/9 = 0.222 of the move given back
    assert s["reversal_frac"] == pytest.approx(0.22, abs=0.05)


def test_aggregate_groups_by_side():
    rows = [summarize_event(_es(), "Buy", -5, "a"),
            summarize_event(_es(0.04), "Buy", -5, "b"),
            summarize_event(_es(0.06), "Sell", -5, "c")]
    agg = aggregate_study(rows)
    assert set(agg["side"]) == {"Buy", "Sell"}
    assert agg.set_index("side").loc["Buy", "n"] == 2


def test_grading_sell_rides_pressure_buy_avoids_peak():
    es = _es(pressure=0.06, reversal=0.5)
    gs = grade_strategies(es, "Sell")
    gb = grade_strategies(es, "Buy")
    # Seller at the pressured close: S1 realized cost NEGATIVE (favorable)
    s1_sell = gs["frontier"].set_index("S").loc["S1", "Cost vs decision (bps)"]
    assert s1_sell < 0
    assert gs["our_rule"].startswith("S1") and gs["regret_bps"] >= 0
    # Buyer: S1 pays the full pressure; our S3 rule must beat it
    fb = gb["frontier"].set_index("S")
    assert fb.loc["S1", "Cost vs decision (bps)"] > fb.loc["S3", "Cost vs decision (bps)"]
    assert gb["our_rule"] == "S3"


def test_close_auction_share():
    d = pd.DataFrame({"Volume": [100.0] * 9 + [900.0]})
    assert close_auction_share(d) == pytest.approx(0.5)


def test_refined_rule_conditions():
    from agents.event_flow_study import refined_rule
    # MSCI deletions or trough-realized sells -> S3 (avoid selling the low)
    assert refined_rule("Sell", "MSCI", -4.3) == "S3"
    assert refined_rule("Sell", "FTSE", -8.0) == "S3"
    assert refined_rule("Sell", "FTSE", +0.5) == "S1"    # mild FTSE print
    # buys: momentum shifts earlier, flat tape stays tolerance-safe S3
    assert refined_rule("Buy", "FTSE", +9.0) == "S4"
    assert refined_rule("Buy", "MSCI", +1.0) == "S3"


def _es_shaped(front_loaded: bool):
    """Planted build shapes: front-loaded (heavy excess right after A) vs
    back-loaded (all on T)."""
    rel = np.arange(-10, 6)
    ab = np.ones(len(rel), dtype=float)
    if front_loaded:
        ab[(rel >= -8) & (rel <= -6)] = 4.0        # early accumulation
        ab[rel == 0] = 1.5
    else:
        ab[rel == 0] = 9.0                          # everything at the print
    car = np.zeros(len(rel))
    return SimpleNamespace(rel_days=rel, norm_price=np.full(len(rel), 1e4),
                           price_at_T=1.0, ab_vol=ab, car=car,
                           est_avg_volume=1e6, est_sigma_daily=0.02,
                           event_dates=pd.bdate_range("2026-06-01",
                                                      periods=len(rel)))


def test_trajectory_classifies_planted_shapes():
    from agents.event_flow_study import positioning_trajectory
    f = positioning_trajectory(_es_shaped(True), ann_rel=-8, side="Buy")
    b = positioning_trajectory(_es_shaped(False), ann_rel=-8, side="Buy")
    assert f["available"] and f["shape"] == "FRONT-LOADED"
    assert f["half_build_rel"] <= -6 and f["t_day_share"] < 0.2
    assert b["shape"] == "BACK-LOADED" and b["t_day_share"] > 0.9
    tr = pd.DataFrame(f["trajectory"])
    assert tr["build_frac"].iloc[-1] == pytest.approx(1.0)
    assert tr["build_frac"].is_monotonic_increasing


def test_aggregate_trajectories_median_curve():
    from agents.event_flow_study import (positioning_trajectory,
                                         aggregate_trajectories)
    ts = []
    for fl in (True, True, False):
        t = positioning_trajectory(_es_shaped(fl), -8, "Buy")
        t["provider"] = "MSCI"
        ts.append(t)
    agg = aggregate_trajectories(ts)
    assert len(agg) == 1 and agg.iloc[0]["n"] == 3
    assert agg.iloc[0]["by_100pct"] == pytest.approx(1.0)
    assert "FRONT-LOADED" in agg.iloc[0]["shape_mix"]
