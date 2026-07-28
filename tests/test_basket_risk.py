"""Basket risk decomposition + Stage-0 RFQ artifacts (agents/basket_risk.py)."""
import numpy as np
import pandas as pd
import pytest

from agents.basket_risk import (risk_decomposition, blind_profile,
                                agency_quote_sketch, aggregate_basket_costs,
                                demo_panel)


@pytest.fixture(scope="module")
def demo():
    return demo_panel()


def test_pure_tracker_basket_is_hedgeable(demo):
    basket, prices, index, _ = demo
    trk = basket[basket["ticker"].str.startswith("TRK")]
    r = risk_decomposition(trk, prices, index)
    assert r.available
    assert r.beta == pytest.approx(1.0, abs=0.15)      # built at beta ~1
    assert r.hedgeable_share > 0.75                    # low idio -> high R2
    assert r.te_ann < 0.06                             # tight tracker


def test_idio_names_blow_out_te_and_dominate_contributions(demo):
    basket, prices, index, _ = demo
    r_full = risk_decomposition(basket, prices, index)
    trk = basket[basket["ticker"].str.startswith("TRK")]
    r_trk = risk_decomposition(trk, prices, index)
    assert r_full.te_ann > r_trk.te_ann * 1.5
    assert r_full.contributors.iloc[0]["ticker"].startswith("IDIO")


def test_hedge_notional_is_beta_times_net(demo):
    basket, prices, index, _ = demo
    r = risk_decomposition(basket, prices, index)
    assert r.hedge_notional == pytest.approx(r.beta * r.net_notional, rel=1e-2)
    assert r.gross_notional > abs(r.net_notional)      # two-sided basket


def test_missing_prices_and_short_history_degrade(demo):
    basket, prices, index, _ = demo
    r = risk_decomposition(basket.assign(ticker="NOPE"), prices, index)
    assert not r.available and "missing" in r.reason
    r2 = risk_decomposition(basket, prices.iloc[-20:], index.iloc[-20:])
    assert not r2.available


def test_blind_profile_contains_no_tickers(demo):
    basket, prices, index, adv = demo
    r = risk_decomposition(basket, prices, index)
    prof = blind_profile(basket, adv, r)
    for t in basket["ticker"]:
        assert t not in prof["text"]                   # masking is the point
    assert prof["n_lines"] == 8
    assert prof["te_ann_bps"] == pytest.approx(r.te_ann * 1e4, abs=1)
    assert "P90 line" in prof["text"]


def test_quote_sketch_flags_illiquid_tail(demo):
    basket, prices, index, adv = demo
    prof = blind_profile(basket, adv, risk_decomposition(basket, prices, index))
    q = agency_quote_sketch(prof)
    assert "risk bid would charge most" in q           # >10% ADV tail > 10%
    assert "commission is commercial" in q
    for t in basket["ticker"]:
        assert t not in q


def test_aggregate_costs_pareto_math():
    p = pd.DataFrame({"ticker": ["A", "B", "C", "D"],
                      "notional": [1e6, 1e6, 1e6, 1e6],
                      "est_cost_bps": [40.0, 10.0, 5.0, 5.0]})
    a = aggregate_basket_costs(p, top_k=1)
    assert a["wavg_cost_bps"] == pytest.approx(15.0)
    assert a["top_contributors"].iloc[0]["ticker"] == "A"
    assert a["top_share"] == pytest.approx(40 / 60, abs=0.01)


def test_aggregate_costs_empty_degrades():
    assert not aggregate_basket_costs(pd.DataFrame(
        columns=["ticker", "notional", "est_cost_bps"]))["available"]
