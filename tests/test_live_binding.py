"""B3 — order-ticket constraints bind the live trading session.

Property: a single-leg live session (no interventions) must reproduce the
Agent-3 static result for the same algo under the same ticket, since both apply
the identical `constrain_fills` kernel. (Base algo TWAP, which has no historical-
curve dependence, gives an exact match.)"""
import pytest

from agents.agent3_algo_simulation import simulate_algos, simulate_with_interventions
from agents.order_ticket import OrderTicket
from conftest import make_market_data


def _live_single_leg(md, ticket, algo="TWAP", urg="Medium"):
    order_shares = md.adv_shares * 0.20   # 20% ADV so the cap actually binds
    return simulate_with_interventions(
        md, order_shares, algo, urg, interventions=[], side=ticket.side, ticket=ticket)


def test_live_cap_matches_static_pipeline():
    md = make_market_data()
    ticket = OrderTicket(max_participation_pct=1.0)   # tight cap => binds
    static = simulate_algos(md, order_pct_adv=20.0, urgency="Medium", ticket=ticket)
    live = _live_single_leg(md, ticket)
    assert live["blended"].completion_pct == pytest.approx(
        static.algos["TWAP"].completion_pct, abs=1e-9)
    assert live["blended"].slippage_bps == pytest.approx(
        static.algos["TWAP"].slippage_bps, abs=1e-6)
    assert live["blended"].total_cost_bps == pytest.approx(
        static.algos["TWAP"].total_cost_bps, abs=1e-6)


def test_live_cap_reduces_completion_vs_unconstrained():
    md = make_market_data()
    capped = _live_single_leg(md, OrderTicket(max_participation_pct=1.0))
    free = _live_single_leg(md, OrderTicket())     # default => is_default, no binding
    assert capped["blended"].completion_pct < 1.0
    assert free["blended"].completion_pct == pytest.approx(1.0, abs=1e-9)


def test_live_sell_limit_gate_binds():
    md = make_market_data()
    # market ~flat at 100; a Sell limit at 130 is above every bar => no fills
    ticket = OrderTicket(side="Sell", order_type="Limit", limit_price=130.0)
    live = _live_single_leg(md, ticket, algo="TWAP")
    assert live["blended"].completion_pct == 0.0


def test_default_ticket_live_unchanged_from_no_ticket():
    md = make_market_data()
    order = md.adv_shares * 0.05
    a = simulate_with_interventions(md, order, "VWAP", "Medium", interventions=[])
    b = simulate_with_interventions(md, order, "VWAP", "Medium", interventions=[],
                                    ticket=OrderTicket())
    assert a["blended"].total_cost_bps == pytest.approx(b["blended"].total_cost_bps, abs=1e-9)


def test_live_window_matches_static_pipeline():
    """Execution WINDOW binds the live session (2026-07-08 fix): a single-leg
    live TWAP with a time-window ticket must equal Agent 3's static windowed
    TWAP exactly — and both must trade ZERO shares outside the window."""
    import datetime
    md = make_market_data()
    ticket = OrderTicket(start_time=datetime.time(10, 30), end_time=datetime.time(14, 30))
    static = simulate_algos(md, order_pct_adv=5.0, urgency="Medium", ticket=ticket)
    live = simulate_with_interventions(md, md.adv_shares * 0.05, "TWAP", "Medium",
                                       interventions=[], side="Buy", ticket=ticket)
    assert live["blended"].slippage_bps == pytest.approx(
        static.algos["TWAP"].slippage_bps, abs=1e-6)
    assert live["blended"].total_cost_bps == pytest.approx(
        static.algos["TWAP"].total_cost_bps, abs=1e-6)
    assert live["blended"].completion_pct == pytest.approx(
        static.algos["TWAP"].completion_pct, abs=1e-9)
    sched = live["schedule"]
    filled = sched[sched["shares_traded"] > 0]
    times = [t.time() for t in filled["time"]]
    assert min(times) >= datetime.time(10, 30)
    assert max(times) <= datetime.time(14, 30)


def test_live_window_plus_intervention_stays_inside_window():
    import datetime
    md = make_market_data()
    ticket = OrderTicket(start_time=datetime.time(10, 30), end_time=datetime.time(14, 30))
    day0 = md.intraday.index[md.intraday.index.normalize()
                             == md.intraday.index.normalize().max()]
    mid = day0[len(day0) // 2]
    live = simulate_with_interventions(
        md, md.adv_shares * 0.05, "TWAP", "Medium",
        interventions=[{"checkpoint_time": mid, "algo": "POV", "urgency": "High"}],
        side="Buy", ticket=ticket)
    sched = live["schedule"]
    filled = sched[sched["shares_traded"] > 0]
    times = [t.time() for t in filled["time"]]
    assert min(times) >= datetime.time(10, 30)
    assert max(times) <= datetime.time(14, 30)
