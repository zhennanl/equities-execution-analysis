"""Order ticket + the shared constrain_fills kernel + pre-trade compliance.

Regression anchors (docs/HANDOFF_2026-07-08.md §6):
  * 20% ADV order, 5% cap, 78 bars x 10k volume  => 25% fill (39,000 of 156,000)
  * default OrderTicket() short-circuits the constraint path (is_default True)
"""
import datetime as dt

import numpy as np
import pytest

from agents.order_ticket import (
    OrderTicket, constrain_fills, windowed_curve, check_order, side_sign,
)


# -- Side convention --------------------------------------------------------

def test_side_sign():
    assert side_sign("Buy") == 1.0
    assert side_sign("Sell") == -1.0
    assert side_sign("SELL") == -1.0


def test_sell_limit_gate_blocks_below_limit():
    prices = np.array([98.0, 101.0, 99.0])
    planned = np.array([10.0, 10.0, 10.0])
    volumes = np.full(3, 1e9)
    out = constrain_fills(planned, prices, volumes, limit_price=100.0, side="Sell")
    assert out[0] == 0.0 and out[2] == 0.0
    assert out[1] == pytest.approx(20.0)   # own 10 + 10 carried from bar 0


def test_buy_and_sell_limit_gates_are_mirror_images():
    prices = np.array([98.0, 101.0, 99.0, 102.0])
    planned = np.full(4, 10.0)
    volumes = np.full(4, 1e9)
    buy = constrain_fills(planned, prices, volumes, limit_price=100.0, side="Buy")
    sell = constrain_fills(planned, prices, volumes, limit_price=100.0, side="Sell")
    assert set(np.flatnonzero(buy > 0)).isdisjoint(np.flatnonzero(sell > 0))


# -- constrain_fills kernel -------------------------------------------------

def test_participation_cap_25pct_fill_anchor():
    n = 78
    volumes = np.full(n, 10_000.0)
    order = 0.20 * n * 10_000            # 156,000
    planned = np.full(n, order / n)
    prices = np.full(n, 100.0)
    out = constrain_fills(planned, prices, volumes, cap_frac=0.05)
    assert out.sum() == pytest.approx(39_000.0)
    assert out.sum() / order == pytest.approx(0.25)


def test_cap_carries_forward_blocked_shares():
    volumes = np.array([1000.0, 1000.0, 1000.0])
    planned = np.array([3000.0, 0.0, 0.0])
    prices = np.full(3, 10.0)
    out = constrain_fills(planned, prices, volumes, cap_frac=0.5)
    assert list(out) == [500.0, 500.0, 500.0]
    assert out.sum() == 1500.0


def test_limit_gate_blocks_bars_above_buy_limit():
    prices = np.array([98.0, 101.0, 99.0])
    planned = np.array([10.0, 10.0, 10.0])
    volumes = np.full(3, 1e9)
    out = constrain_fills(planned, prices, volumes, limit_price=100.0)
    assert out[1] == 0.0
    assert out[2] == pytest.approx(20.0)


def test_limit_gate_all_blocked_when_market_through_limit():
    prices = np.full(5, 105.0)
    planned = np.full(5, 10.0)
    out = constrain_fills(planned, prices, np.full(5, 1e9), limit_price=99.0)
    assert out.sum() == 0.0


def test_exempt_bar_ignores_cap():
    volumes = np.array([1000.0, 1000.0])
    planned = np.array([0.0, 5000.0])
    prices = np.full(2, 10.0)
    out = constrain_fills(planned, prices, volumes, cap_frac=0.1, exempt=frozenset({1}))
    assert out[1] == 5000.0


def test_windowed_curve_renormalizes_to_one():
    curve = np.array([0.1, 0.2, 0.3, 0.4])
    seg = windowed_curve(curve, 1, 2)
    assert seg.sum() == pytest.approx(1.0)
    assert seg[0] == pytest.approx(0.4)


# -- OrderTicket helpers ----------------------------------------------------

def test_default_ticket_is_default():
    assert OrderTicket().is_default() is True


def test_any_constraint_makes_ticket_non_default():
    assert OrderTicket(max_participation_pct=15.0).is_default() is False
    assert OrderTicket(order_type="Limit", limit_price=100.0).is_default() is False
    assert OrderTicket(must_complete=True).is_default() is False
    assert OrderTicket(allow_auction=False).is_default() is False


def test_effective_limit_only_when_limit_order():
    assert OrderTicket(order_type="Market", limit_price=100.0).effective_limit is None
    assert OrderTicket(order_type="Limit", limit_price=100.0).effective_limit == 100.0


def test_cap_frac_conversion():
    assert OrderTicket(max_participation_pct=15.0).cap_frac == pytest.approx(0.15)
    assert OrderTicket().cap_frac is None


def test_window_indices_maps_times_to_bars():
    import pandas as pd
    idx = pd.date_range("2026-06-15 09:30", periods=78, freq="5min")
    t = OrderTicket(start_time=dt.time(10, 0), end_time=dt.time(11, 0))
    s, e = t.window_indices(idx)
    assert idx[s].time() >= dt.time(10, 0)
    assert idx[e].time() <= dt.time(11, 0)
    assert e > s


def test_fix_fields_include_buy_side_and_limit_tags():
    rows = OrderTicket(order_type="Limit", limit_price=123.0).to_fix_fields("AAPL", 1000)
    tags = {r["Tag"]: r["Value"] for r in rows}
    assert tags[54] == "1 (Buy)"
    assert tags[40] == "2 (Limit)"
    assert tags[44] == "123"


# -- Pre-trade compliance ---------------------------------------------------

def test_fat_finger_over_25pct_adv_blocks():
    findings = check_order(OrderTicket(), "AAPL", order_pct_adv=30.0)
    assert any(f.severity == "BLOCK" and "size" in f.rule.lower() for f in findings)


def test_size_between_10_and_25pct_warns():
    findings = check_order(OrderTicket(), "AAPL", order_pct_adv=15.0)
    assert any(f.severity == "WARN" for f in findings)
    assert not any(f.severity == "BLOCK" for f in findings)


def test_small_order_is_clean():
    assert check_order(OrderTicket(), "AAPL", order_pct_adv=2.0) == []


def test_limit_order_without_price_blocks():
    findings = check_order(OrderTicket(order_type="Limit", limit_price=None),
                           "AAPL", order_pct_adv=2.0)
    assert any(f.severity == "BLOCK" and "validity" in f.rule.lower() for f in findings)


def test_limit_far_through_last_price_warns():
    t = OrderTicket(order_type="Limit", limit_price=110.0)
    findings = check_order(t, "AAPL", order_pct_adv=2.0, last_price=100.0)
    assert any("sanity" in f.rule.lower() for f in findings)


def test_inverted_window_blocks():
    t = OrderTicket(start_time=dt.time(11, 0), end_time=dt.time(10, 0))
    findings = check_order(t, "AAPL", order_pct_adv=2.0)
    assert any(f.severity == "BLOCK" and "validity" in f.rule.lower() for f in findings)


# -- Short-sale locate (B2 Step 4) ------------------------------------------

def test_sell_without_locate_blocks():
    t = OrderTicket(side="Sell", locate_confirmed=False)
    findings = check_order(t, "AAPL", order_pct_adv=2.0)
    assert any(f.severity == "BLOCK" and "locate" in f.rule.lower() for f in findings)


def test_sell_with_locate_is_clean():
    assert check_order(OrderTicket(side="Sell", locate_confirmed=True),
                       "AAPL", order_pct_adv=2.0) == []


def test_buy_never_needs_locate():
    findings = check_order(OrderTicket(side="Buy", locate_confirmed=False),
                           "AAPL", order_pct_adv=2.0)
    assert not any("locate" in f.rule.lower() for f in findings)


def test_sell_default_ticket_is_still_default():
    assert OrderTicket(side="Sell").is_default() is True
    assert OrderTicket(side="Sell").to_fix_fields("AAPL", 1000)[1]["Value"] == "2 (Sell)"
