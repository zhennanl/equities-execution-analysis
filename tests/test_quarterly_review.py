"""QBR — quarterly client review aggregation (agents/quarterly_review.py).

The synthetic quarter plants known structure (LIQ +8 bps edge, IS -1;
>10% ADV pain; High-urgency premium) — the review must recover it, and the
gates (min orders, min cell n) must hold."""
import numpy as np
import pandas as pd
import pytest

from agents.quarterly_review import (build_quarterly_review,
                                     synthesize_demo_quarter, MIN_ORDERS)


@pytest.fixture(scope="module")
def demo():
    return build_quarterly_review(synthesize_demo_quarter(), quarter="2026Q2",
                                  is_synthetic=True)


def test_demo_quarter_builds(demo):
    assert demo.available and demo.quarter == "2026Q2"
    assert demo.n_orders == 180
    assert set(demo.by_algo["group"]) == {"VWAP", "TWAP", "POV", "IS", "LIQ"}
    assert 0 < demo.outlier_share <= 1
    assert demo.recommendations
    assert any("SYNTHETIC" in c for c in demo.caveats)


def test_planted_structure_recovered(demo):
    # LIQ was planted 8 bps worse than IS: adjusted ranking must flag it
    # separable, and IS (cheapest raw mean) is the regression baseline.
    adj = demo.adjusted_ranking
    assert adj["available"] and adj["baseline"] == "IS"
    t = adj["table"].set_index("Algo")
    assert t.loc["LIQ", "Adjusted vs baseline (bps)"] > 4.0
    assert t.loc["LIQ", "Separable at 5%?"] == "YES"


def test_size_bucket_pain_and_urgency_premium(demo):
    big = demo.by_bucket.set_index("group").loc[">10% ADV"]
    assert big["mean_bps"] > demo.headline["mean_bps"]      # planted size pain
    u = demo.by_urgency.set_index("group")
    assert u.loc["High", "mean_bps"] > u.loc["Low", "mean_bps"]


def test_quarter_filter_excludes_other_quarters():
    rows = synthesize_demo_quarter("2026Q2", n=120) + \
           synthesize_demo_quarter("2026Q1", n=60, seed=7)
    r = build_quarterly_review(rows, quarter="2026Q2")
    assert r.n_orders == 120
    assert r.prior_quarter and r.prior_quarter["quarter"] == "2026Q1"


def test_min_orders_gate():
    r = build_quarterly_review(synthesize_demo_quarter(n=MIN_ORDERS - 1))
    assert not r.available and "need" in r.reason


def test_empty_library_unavailable():
    r = build_quarterly_review([])
    assert not r.available
