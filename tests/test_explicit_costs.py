"""Explicit-cost table — deterministic, hand-verifiable regression anchors
(docs/HANDOFF_2026-07-08.md §6: UK buy 51.6 bps, Taiwan sell 31.9 bps)."""
from agents.explicit_costs import get_explicit_costs, explicit_cost_note


def test_uk_buy_total_is_51_6_bps():
    # commission 1.5 + fees 0.1 + stamp-on-buys 50.0
    assert get_explicit_costs("UK (LSE)").total_bps("Buy") == 51.6


def test_taiwan_sell_total_is_31_9_bps():
    # commission 1.5 + fees 0.4 + sell tax 30.0
    assert get_explicit_costs("Taiwan (TWSE)").total_bps("Sell") == 31.9


def test_taiwan_buy_has_no_transaction_tax():
    # Taiwan taxes sells only — buy side is commission + fees = 1.9
    assert get_explicit_costs("Taiwan (TWSE)").total_bps("Buy") == 1.9


def test_uk_sell_has_no_stamp():
    # UK stamp is on buys only
    assert get_explicit_costs("UK (LSE)").total_bps("Sell") == 1.6


def test_unknown_market_falls_back_to_default():
    c = get_explicit_costs("Neptune (NSE)")
    assert c.total_bps("Buy") == 1.8   # default 1.5 + 0.3


def test_buy_note_flags_round_trip_sell_tax_for_taiwan():
    note = explicit_cost_note("Taiwan (TWSE)", "Buy")
    assert "Round-trip" in note and "30 bps" in note


def test_breakdown_omits_zero_tax_lines():
    lines = get_explicit_costs("Japan (TSE)").breakdown("Buy")
    assert not any("stamp" in x.lower() or "transaction tax" in x.lower() for x in lines)
