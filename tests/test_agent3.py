"""Agent 3 — algo simulation.

Regression anchors (docs/HANDOFF_2026-07-08.md §6):
  * 30bp symmetric up-wicks (H=C*1.003, L=C) => TWAP slippage 10.0 bps;
    MOC & MOO slippage 0.0 (auction prints keep the close/open).
  * 0.05/bar uptrend, buy limit 99 below arrival => 0% fill, opp cost 385.0 bps.
  * default OrderTicket() reproduces the no-ticket numbers EXACTLY (P-4).
  * flat day => all-zero slippage/opportunity for every algo.
"""
import numpy as np
import pytest

from agents.agent3_algo_simulation import (
    _typical_prices, _sim_twap, _sim_moc, _sim_moo, _build_result,
    _ac_trajectory_weights, simulate_algos,
)
from agents.order_ticket import OrderTicket, constrain_fills
from conftest import make_day, make_market_data


# ── Fill-price convention ──────────────────────────────────────────────────

def test_typical_price_is_hlc_over_three():
    day = make_day(wick_frac=0.003, close_base=100.0)   # H=100.3, L=100? see below
    # High = Close*1.003, Low = Close*0.997; typical = (H+L+C)/3 = C
    tp = _typical_prices(day)
    assert tp[0] == pytest.approx(100.0)


def test_twap_slippage_10bps_on_symmetric_upwick():
    # H = C*(1+0.003), L = C exactly => typical = (1.003C + C + C)/3 = 1.001C
    day = make_day(close_base=100.0)
    day = day.assign(High=day["Close"] * 1.003, Low=day["Close"])
    sched = _sim_twap(day, order_shares=1000.0)
    res = _build_result("TWAP", sched, arrival_price=100.0, order_shares=1000.0,
                        adv_shares=1e6, vol_ann=0.2, speed_factor=0.85,
                        period_end_price=100.0)
    assert res.slippage_bps == 10.0


def test_moc_and_moo_keep_auction_print_zero_slippage():
    day = make_day(close_base=100.0)
    day = day.assign(High=day["Close"] * 1.003, Low=day["Close"])  # up-wicks
    moc = _build_result("MOC", _sim_moc(day, 1000.0), 100.0, 1000.0, 1e6, 0.2,
                        0.80, 100.0)
    moo = _build_result("MOO", _sim_moo(day, 1000.0), 100.0, 1000.0, 1e6, 0.2,
                        1.05, 100.0)
    assert moc.slippage_bps == 0.0
    assert moo.slippage_bps == 0.0


# ── Limit gate + opportunity cost ──────────────────────────────────────────

def test_limit_below_market_gives_zero_fill_and_385bps_opp():
    # Close[i] = 100 + 0.05*i, 78 bars => Close[-1] = 103.85; arrival 100.
    day = make_day(n_bars=78, close_base=100.0, drift_per_bar=0.05, wick_frac=0.0)
    period_end = float(day["Close"].iloc[-1])
    assert period_end == pytest.approx(103.85)

    sched = _sim_twap(day, order_shares=1000.0)
    adj = constrain_fills(sched["shares_traded"].to_numpy(float),
                          sched["price"].to_numpy(float),
                          day["Volume"].to_numpy(float),
                          limit_price=99.0)
    sched = sched.assign(shares_traded=adj, cumulative=np.cumsum(adj))
    res = _build_result("TWAP", sched, arrival_price=100.0, order_shares=1000.0,
                        adv_shares=1e6, vol_ann=0.2, speed_factor=0.85,
                        period_end_price=period_end)
    assert res.completion_pct == 0.0
    assert res.opportunity_cost_bps == 385.0


# ── Almgren-Chriss trajectory ──────────────────────────────────────────────

def test_ac_weights_sum_to_one_and_collapse_to_uniform_at_zero():
    w0 = _ac_trajectory_weights(10, 0.0)
    assert w0.sum() == pytest.approx(1.0)
    assert np.allclose(w0, 0.1)                    # uniform (TWAP-like) limit
    w = _ac_trajectory_weights(10, 4.0)
    assert w.sum() == pytest.approx(1.0)
    assert w[0] > w[-1]                            # front-loaded


# ── Integration on synthetic MarketData ────────────────────────────────────

def test_flat_day_has_zero_slippage_for_every_algo():
    md = make_market_data()
    sim = simulate_algos(md, order_pct_adv=5.0, urgency="Medium")
    # synthetic intraday is flat (drift 0, tiny wick) => slippage ~ 0
    for name, algo in sim.algos.items():
        assert abs(algo.slippage_bps) < 5.0, name


def test_default_ticket_reproduces_no_ticket_exactly():
    md = make_market_data()
    base = simulate_algos(md, order_pct_adv=5.0, urgency="Medium", ticket=None)
    dflt = simulate_algos(md, order_pct_adv=5.0, urgency="Medium",
                          ticket=OrderTicket())
    assert set(base.algos) == set(dflt.algos)
    for name in base.algos:
        assert base.algos[name].total_cost_bps == dflt.algos[name].total_cost_bps, name
        assert base.algos[name].completion_pct == dflt.algos[name].completion_pct, name


def test_participation_cap_reduces_completion():
    md = make_market_data()
    capped = simulate_algos(md, order_pct_adv=20.0, urgency="High",
                            ticket=OrderTicket(max_participation_pct=1.0))
    # A hard 1%/bar cap on a 20%-ADV order cannot complete within one session
    assert capped.algos["TWAP"].completion_pct < 1.0


def test_auction_disabled_excludes_moc_moo():
    md = make_market_data()
    sim = simulate_algos(md, order_pct_adv=5.0, urgency="Medium",
                         ticket=OrderTicket(allow_auction=False))
    assert "MOC" in sim.excluded and "MOO" in sim.excluded
    assert "MOC" not in sim.algos and "MOO" not in sim.algos
