"""Offline unit tests for the Page-2 event-study analytics (pure functions
only — run_event_study() itself needs network and is exercised by the live
smoke test path, not here).

Synthetic CAR path (decimal): flat to T-5, linear run-up to +5% at T, gives
back 3 of the 5 points by T+5, flat after. Deterministic anchors:
  pre-event run-up (T-5..T)      = +5.00%
  post-event move (T..T+5)       = -3.00%
  reversal fraction (5d)         = 0.600  -> "Transient -- mostly reverses"
  drift with announcement at T-4 : pre-ann +1.00%, ann->T +4.00%, 80% after ann
"""
import numpy as np
import pandas as pd
import pytest

from agents.rebalancing_event_study import (
    compute_reversal, compute_drift_decomposition, estimate_flow_to_trade,
    calibrate_event_day_eta, basket_crowding_note,
    recommend_rebalance_execution, ClosingConcentration,
)


def _synthetic_car():
    rel = np.arange(-10, 11)
    car = np.array([0.0]*6 + [0.01, 0.02, 0.03, 0.04, 0.05]
                   + [0.044, 0.038, 0.032, 0.026, 0.02] + [0.02]*5)
    dates = pd.bdate_range("2026-06-11", periods=len(rel))
    return rel, car, dates


def test_reversal_anchors_transient_classification():
    rel, car, _ = _synthetic_car()
    r = compute_reversal(car, rel)
    assert r.available
    assert r.pre_event_runup_pct == pytest.approx(5.0)
    assert r.post_event_move_5d_pct == pytest.approx(-3.0)
    assert r.reversal_fraction_5d == pytest.approx(0.6)
    assert r.classification == "Transient -- mostly reverses"


def test_reversal_indeterminate_when_no_runup():
    rel = np.arange(-10, 11)
    r = compute_reversal(np.zeros_like(rel, dtype=float), rel)
    assert r.available
    assert "Indeterminate" in r.classification


def test_drift_decomposition_anchors():
    rel, car, dates = _synthetic_car()
    T = dates[int(np.where(rel == 0)[0][0])]
    ann = dates[int(np.where(rel == -4)[0][0])]
    d = compute_drift_decomposition(car, dates.values, T, ann)
    assert d.available
    assert d.pre_announcement_car_pct == pytest.approx(1.0)
    assert d.announcement_to_effective_car_pct == pytest.approx(4.0)
    assert d.pct_of_pre_event_move_after_announcement == pytest.approx(80.0)


def test_drift_rejects_announcement_after_T():
    rel, car, dates = _synthetic_car()
    T = dates[int(np.where(rel == 0)[0][0])]
    d = compute_drift_decomposition(car, dates.values, T, dates[-1])
    assert not d.available


def test_flow_to_trade_arithmetic():
    f = estimate_flow_to_trade(weight_change_pct=0.5, tracked_aum_usd=10e9,
                               stock_price=100.0, adv_shares=1_000_000.0)
    assert f.notional_usd == pytest.approx(50e6)
    assert f.shares == pytest.approx(500_000.0)
    assert f.flow_pct_adv == pytest.approx(50.0)


def test_eta_calibration_arithmetic():
    rel = np.array([-1, 0, 1])
    car = np.array([0.0, 0.02, 0.04])
    ec = calibrate_event_day_eta(car, rel, flow_pct_adv=25.0, sigma_daily=0.02)
    assert ec.available
    # |0.04| / (0.02 * sqrt(0.25)) = 4.0
    assert ec.implied_eta == pytest.approx(4.0)


def test_recommendation_tracker_mandate_is_moc():
    rel, car, dates = _synthetic_car()
    rec = recommend_rebalance_execution(
        "Index Tracker",
        ClosingConcentration(available=False, reason="test"),
        compute_reversal(car, rel),
        compute_drift_decomposition(car, dates.values,
                                    dates[int(np.where(rel == 0)[0][0])],
                                    dates[int(np.where(rel == -4)[0][0])]),
        None, calibrate_event_day_eta(car, rel, None, 0.02),
        basket_crowding_note("Test Index"))
    assert rec.recommended_algo == "MOC"


def test_recommendation_cost_minimizer_prefers_stealth_on_transient_reversal():
    rel, car, dates = _synthetic_car()
    rec = recommend_rebalance_execution(
        "Cost-Minimizing",
        ClosingConcentration(available=False, reason="test"),
        compute_reversal(car, rel),
        compute_drift_decomposition(car, dates.values,
                                    dates[int(np.where(rel == 0)[0][0])],
                                    dates[int(np.where(rel == -4)[0][0])]),
        None, calibrate_event_day_eta(car, rel, None, 0.02),
        basket_crowding_note("Test Index"))
    assert rec.recommended_algo == "STEALTH"
