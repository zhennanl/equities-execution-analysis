"""B2 sell-side migration — the mirror property is the mechanical sign-site
catch (docs/HANDOFF_2026-07-08.md §B2 Step 3):

    a SELL on price path P produces identical costs to a BUY on the reflected
    path (2*P0 - P), with P0 = arrival and the limit mirrored.

If any slippage / opportunity / tracking site is missed, or has the wrong sign,
one of these equalities breaks. Market impact is side-independent (positive-
adverse) and must match in magnitude on both sides.
"""
import numpy as np
import pytest

from agents.agent3_algo_simulation import (
    _sim_vwap, _sim_twap, _sim_pov, _sim_is, _sim_moc, _sim_moo,
    _sim_liquidity_seeking, _sim_stealth, _build_result, _speed_factor,
    simulate_algos,
)
from agents.order_ticket import OrderTicket
from conftest import make_day, make_market_data

_ALGOS = {
    "VWAP": _sim_vwap, "TWAP": _sim_twap, "POV": _sim_pov, "IS": _sim_is,
    "MOC": _sim_moc, "MOO": _sim_moo, "LIQ": _sim_liquidity_seeking,
    "STEALTH": _sim_stealth,
}


def _reflect(day, p0):
    """Reflect OHLC about the constant p0 (high<->low swap keeps H>=L)."""
    return day.assign(
        Open=2 * p0 - day["Open"], Close=2 * p0 - day["Close"],
        High=2 * p0 - day["Low"], Low=2 * p0 - day["High"],
    )


@pytest.mark.parametrize("algo", list(_ALGOS))
def test_sell_mirrors_buy_per_algo(algo):
    fn = _ALGOS[algo]
    order, adv, vol, urg = 5000.0, 1e6, 0.25, "Medium"
    day = make_day(n_bars=78, close_base=100.0, drift_per_bar=0.02, wick_frac=0.002)
    p0 = float(day["Open"].iloc[0])
    period_end = float(day["Close"].iloc[-1])
    sf = _speed_factor(algo, urg)

    buy_sched = fn(day=day, order_shares=order, urgency=urg, side="Buy")
    buy = _build_result(algo, buy_sched, p0, order, adv, vol, sf, period_end,
                        side="Buy")

    rday = _reflect(day, p0)
    sell_sched = fn(day=rday, order_shares=order, urgency=urg, side="Sell")
    sell = _build_result(algo, sell_sched, p0, order, adv, vol, sf,
                         2 * p0 - period_end, side="Sell")

    assert sell.slippage_bps == pytest.approx(buy.slippage_bps, abs=1e-6), algo
    assert sell.opportunity_cost_bps == pytest.approx(buy.opportunity_cost_bps, abs=1e-6), algo
    assert sell.market_impact_bps == pytest.approx(buy.market_impact_bps, abs=1e-6), algo
    assert sell.total_cost_bps == pytest.approx(buy.total_cost_bps, abs=1e-6), algo
    assert sell.completion_pct == pytest.approx(buy.completion_pct, abs=1e-9), algo


def test_impact_is_positive_adverse_for_both_sides():
    day = make_day(n_bars=78, close_base=100.0, drift_per_bar=0.02, wick_frac=0.002)
    p0 = float(day["Open"].iloc[0])
    for side in ("Buy", "Sell"):
        d = day if side == "Buy" else _reflect(day, p0)
        res = _build_result("TWAP", _sim_twap(d, 5000.0), p0, 5000.0, 1e6, 0.25,
                            0.85, float(d["Close"].iloc[-1]), side=side)
        assert res.market_impact_bps >= 0.0, side


def test_sell_limit_gate_via_simulate_algos():
    # A Sell with a limit ABOVE the whole (falling-from-100) path never fills.
    md = make_market_data()
    # market_data intraday is ~flat at 100; a sell limit at 130 blocks nothing,
    # a sell limit at 130 with a downward reflection would... simpler: assert a
    # sell limit far ABOVE market blocks every fill (price always < limit).
    sim = simulate_algos(md, order_pct_adv=5.0, urgency="Medium",
                         ticket=OrderTicket(side="Sell", order_type="Limit",
                                            limit_price=130.0))
    assert sim.algos["TWAP"].completion_pct == 0.0


def test_default_sell_ticket_still_runs_and_signs_costs():
    md = make_market_data()
    buy = simulate_algos(md, order_pct_adv=5.0, urgency="Medium",
                         ticket=OrderTicket(side="Buy"))
    sell = simulate_algos(md, order_pct_adv=5.0, urgency="Medium",
                          ticket=OrderTicket(side="Sell"))
    # On the same (unreflected) path, buy and sell slippage are opposite-signed
    # for a directional algo like TWAP (the fill price is the same, the sign flips).
    assert sell.algos["TWAP"].slippage_bps == pytest.approx(
        -buy.algos["TWAP"].slippage_bps, abs=1e-6)


# ── Agent 4 fast-path mirror ───────────────────────────────────────────────

def test_agent4_sim_day_all_mirrors_buy_and_sell():
    from agents.agent4_performance_comparison import _sim_day_all
    order, adv, vol, urg = 5000.0, 1e6, 0.25, "Medium"
    day = make_day(n_bars=78, close_base=100.0, drift_per_bar=0.02, wick_frac=0.002)
    p0 = float(day["Open"].iloc[0])
    buy = _sim_day_all(day, order, urg, adv, vol, ticket=OrderTicket(side="Buy"))
    sell = _sim_day_all(_reflect(day, p0), order, urg, adv, vol,
                        ticket=OrderTicket(side="Sell"))
    for algo in ("VWAP", "TWAP", "POV", "IS", "MOC", "MOO", "LIQ", "STEALTH"):
        b, sll = buy[algo], sell[algo]
        assert sll[0] == pytest.approx(b[0], abs=1e-6), f"{algo} slip"
        assert sll[2] == pytest.approx(b[2], abs=1e-6), f"{algo} opp"
        assert sll[3] == pytest.approx(b[3], abs=1e-6), f"{algo} total"
        assert sll[4] == pytest.approx(b[4], abs=1e-9), f"{algo} fill"


# ── Agent 6 post-trade benchmark sign ──────────────────────────────────────

def test_agent6_benchmark_slippage_flips_sign_by_side():
    from agents.agent3_algo_simulation import _sim_day
    from agents.agent1_market_data import MARKET_INFO
    from agents.agent6_pretrade_posttrade import compute_benchmark_comparison
    md = make_market_data()
    sim = simulate_algos(md, order_pct_adv=5.0, urgency="Medium")
    day = _sim_day(md.intraday, MARKET_INFO[md.market]["bars"])
    algo = sim.algos["TWAP"]
    buy_tbl = compute_benchmark_comparison(algo, day, side="Buy").table
    sell_tbl = compute_benchmark_comparison(algo, day, side="Sell").table
    col = "Slippage vs Benchmark (bps)"
    for bench in buy_tbl.index:
        assert sell_tbl.loc[bench, col] == pytest.approx(-buy_tbl.loc[bench, col], abs=1e-6), bench
