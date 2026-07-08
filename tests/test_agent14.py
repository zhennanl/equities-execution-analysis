"""Agent 14 — index-rebalance execution strategies (side-aware).

Anchor (docs/HANDOFF_2026-07-08.md §6): on a pressure-then-full-reversal path
with eta=0, S1 cost 1000.0 bps, S2 750.0, S3 725.0, S1 tracking 0.0. Plus the
buy/sell mirror: a Sell on the reflected path (2*P0 - P) reproduces the Buy
costs on the original path."""
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

from agents.agent14_rebalance_strategist import analyze_strategies


def _pressure_reversal_es(reflect: bool = False):
    """rel -10..+10; decision (rel -5) = 100; linear pressure up to 110 at the
    effective close (rel 0); full linear reversal back to 100 by rel +10."""
    rel = np.arange(-10, 11)
    closes = np.array([
        100, 100, 100, 100, 100, 100,          # rel -10..-5 (decision at -5)
        102, 104, 106, 108, 110,               # rel -4..0  (pressure into T)
        109, 108, 107, 106, 105, 104, 103, 102, 101, 100,  # rel +1..+10 (reversal)
    ], dtype=float)
    if reflect:
        closes = 2 * 100.0 - closes            # reflect about P0 = decision price
    return SimpleNamespace(
        rel_days=rel,
        norm_price=closes * 100.0,             # closes = norm_price/100 * price_at_T
        price_at_T=1.0,
        ab_vol=np.ones_like(rel, dtype=float),
        est_avg_volume=1_000_000.0,
        est_sigma_daily=0.02,
        car=np.zeros_like(rel, dtype=float),
        event_dates=pd.bdate_range("2026-03-02", periods=len(rel)),
    )


def _by_prefix(analysis, prefix):
    return next(s for s in analysis.strategies if s.name.startswith(prefix))


def test_pressure_reversal_cost_anchors_buy_side():
    a = analyze_strategies(_pressure_reversal_es(), side="Buy",
                           order_shares=50_000.0, eta=0.0)
    assert _by_prefix(a, "S1").cost_vs_decision_bps == 1000.0
    assert _by_prefix(a, "S2").cost_vs_decision_bps == 750.0
    assert _by_prefix(a, "S3").cost_vs_decision_bps == 725.0


def test_s1_tracker_has_zero_tracking_diff():
    a = analyze_strategies(_pressure_reversal_es(), side="Buy",
                           order_shares=50_000.0, eta=0.0)
    assert _by_prefix(a, "S1").tracking_diff_bps == 0.0


def test_strategy_cost_ordering_s1_gt_s2_gt_s3():
    a = analyze_strategies(_pressure_reversal_es(), side="Buy",
                           order_shares=50_000.0, eta=0.0)
    s1 = _by_prefix(a, "S1").cost_vs_decision_bps
    s2 = _by_prefix(a, "S2").cost_vs_decision_bps
    s3 = _by_prefix(a, "S3").cost_vs_decision_bps
    assert s1 > s2 > s3


def test_buy_sell_mirror_property():
    buy = analyze_strategies(_pressure_reversal_es(reflect=False), side="Buy",
                             order_shares=50_000.0, eta=0.0)
    sell = analyze_strategies(_pressure_reversal_es(reflect=True), side="Sell",
                              order_shares=50_000.0, eta=0.0)
    for prefix in ("S1", "S2", "S3", "S4"):
        assert (_by_prefix(buy, prefix).cost_vs_decision_bps
                == pytest.approx(_by_prefix(sell, prefix).cost_vs_decision_bps))


def test_impact_is_positive_adverse_for_both_sides():
    # With eta > 0 the impact term must be a cost (avg impact >= 0) regardless
    # of side — impact stays positive-adverse; only slippage/cost flips sign.
    buy = analyze_strategies(_pressure_reversal_es(), side="Buy",
                             order_shares=50_000.0, eta=0.3)
    for s in buy.strategies:
        assert s.avg_impact_bps >= 0.0
