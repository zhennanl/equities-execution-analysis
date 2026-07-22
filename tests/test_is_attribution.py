"""Full IS attribution (gap register I-5) — Perold decomposition must
reconcile to the share-weighted shortfall exactly, on every algo and side."""
import numpy as np
import pandas as pd
import pytest

from agents.agent3_algo_simulation import simulate_algos
from agents.agent6_pretrade_posttrade import build_is_attribution, _sim_day
from agents.agent1_market_data import MARKET_INFO
from agents.order_ticket import OrderTicket
from tests.conftest import make_market_data


def _run(side="Buy", market="US", urgency="Medium", pct=5.0):
    md = make_market_data(market=market)
    ticket = OrderTicket(side=side, locate_confirmed=True)
    sim = simulate_algos(md, order_pct_adv=pct, urgency=urgency, ticket=ticket)
    day = _sim_day(md.intraday, MARKET_INFO[market]["bars"])
    return md, sim, day


def test_reconciles_within_tenth_bp_all_algos_both_sides():
    for side in ("Buy", "Sell"):
        md, sim, day = _run(side=side)
        for name, algo in sim.algos.items():
            isa = build_is_attribution(algo, day, side, md.market, sim.order_shares)
            assert isa.available, name
            assert isa.reconciliation_bps < 0.1, (name, side, isa.reconciliation_bps)
            comp_sum = (isa.delay_bps + isa.trading_bps
                        + isa.opportunity_bps + isa.explicit_bps)
            assert comp_sum == pytest.approx(isa.total_is_bps, abs=0.05), name


def test_full_fill_has_zero_opportunity_and_weighted_slippage():
    md, sim, day = _run(side="Buy")
    algo = sim.algos["TWAP"]                     # always completes
    isa = build_is_attribution(algo, day, "Buy", md.market, sim.order_shares)
    assert isa.filled_frac == pytest.approx(1.0)
    assert isa.opportunity_bps == 0.0
    # delay + trading == slippage vs arrival when fully filled
    assert isa.delay_bps + isa.trading_bps == pytest.approx(algo.slippage_bps, abs=0.05)
    # explicit = full US schedule on buys (1.5 commission + 0.1 fees)
    assert isa.explicit_bps == pytest.approx(1.6, abs=0.01)


def test_partial_fill_scales_components():
    md, sim, day = _run(side="Buy", pct=60.0, urgency="Low")
    pov = sim.algos["POV"]
    if pov.completion_pct >= 1.0:
        pytest.skip("POV completed on this synthetic path")
    isa = build_is_attribution(pov, day, "Buy", md.market, sim.order_shares)
    assert 0 < isa.filled_frac < 1
    # explicit scaled by fill fraction
    assert isa.explicit_bps == pytest.approx(1.6 * isa.filled_frac, abs=0.01)
    # opportunity carries the unfilled mark vs decision
    p_end = float(day["Close"].iloc[-1])
    d = isa.decision_price
    expected_opp = (1 - isa.filled_frac) * (p_end - d) / d * 1e4
    assert isa.opportunity_bps == pytest.approx(expected_opp, abs=0.05)


def test_sell_side_signs_flip_delay_and_trading():
    md_b, sim_b, day_b = _run(side="Buy")
    isa_b = build_is_attribution(sim_b.algos["TWAP"], day_b, "Buy", "US", sim_b.order_shares)
    isa_s = build_is_attribution(sim_b.algos["TWAP"], day_b, "Sell", "US", sim_b.order_shares)
    # same fills, opposite side: implicit components mirror; explicit differs by schedule
    assert isa_s.delay_bps == pytest.approx(-isa_b.delay_bps, abs=0.01)
    assert isa_s.trading_bps == pytest.approx(-isa_b.trading_bps, abs=0.01)


def test_posttrade_tca_carries_attribution():
    from agents.agent4_performance_comparison import compare_performance
    from agents.agent6_pretrade_posttrade import build_posttrade_tca
    md, sim, day = _run(side="Buy")
    comp = compare_performance(md, order_pct_adv=5.0, urgency="Medium")
    tca = build_posttrade_tca(md, sim, comp, "TWAP")
    assert tca.is_attribution is not None and tca.is_attribution.available
    assert tca.is_attribution.reconciliation_bps < 0.1
