"""PT ops automations round 2 (agents/pt_ops.py) — file normalizer,
holiday-aware settlement, crossing detector, exposure scheduler."""
import datetime as dt

import numpy as np
import pandas as pd
import pytest

from agents.pt_ops import (normalize_client_file, settlement_date_holiday_aware,
                           closure_warnings, crossing_report,
                           exposure_schedule, FX_NOTES)


# ── A8: normalizer ─────────────────────────────────────────────────────────

def test_bloomberg_conventions_normalized():
    r = normalize_client_file(pd.DataFrame({
        "Symbol": ["2330 TT", "700 HK", "7203 JT", "5930 KS"],
        "Side": ["B", "SELL", "1", "S"],
        "Qty": [1000, 2000, 300, 400]}))
    b = r["basket"].set_index("ticker")
    assert b.loc["2330.TW", "market"] == "Taiwan (TWSE)"
    assert "0700.HK" in b.index                      # HK zero-padded to 4
    assert b.loc["005930.KS", "side"] == "Sell"      # KR padded to 6
    assert b.loc["7203.T", "side"] == "Buy"          # side code 1 -> Buy


def test_duplicates_aggregated_and_unknowns_flagged():
    r = normalize_client_file(pd.DataFrame({
        "ticker": ["2330 TT", "2330 TT", "WEIRD XX"],
        "side": ["B", "BUY", "B"], "shares": [500, 500, 100]}))
    b = r["basket"].set_index("ticker")
    assert b.loc["2330.TW", "shares"] == 1000
    assert any("duplicate" in i for i in r["issues"])
    assert any("ASSIGN market manually" in i for i in r["issues"])


def test_notional_conversion_needs_price_and_both_sides_flagged():
    r = normalize_client_file(pd.DataFrame({
        "ticker": ["700 HK", "700 HK", "2330 TT"],
        "side": ["B", "S", "B"],
        "shares": [np.nan, 1000, np.nan],
        "notional": [350_000.0, np.nan, 100_000.0]}),
        prev_close={"0700.HK": 350.0})
    b = r["basket"].set_index(["ticker", "side"])
    assert b.loc[("0700.HK", "Buy"), "shares"] == pytest.approx(1000.0)
    assert any("BOTH-SIDES" in i for i in r["issues"])
    assert any("no prev close" in i for i in r["issues"])   # 2330 skipped


def test_unusable_file_fails_loudly():
    r = normalize_client_file(pd.DataFrame({"a": [1], "b": [2]}))
    assert not r["ok"]


# ── A9: holidays ───────────────────────────────────────────────────────────

def test_cny_cluster_pushes_taiwan_settlement():
    r = settlement_date_holiday_aware("Taiwan (TWSE)", dt.date(2026, 2, 12))
    assert r["settles"] == dt.date(2026, 2, 24)      # T+2 across CNY week
    assert len(r["holidays_skipped"]) >= 5
    assert "verify" in r["note"]


def test_no_holiday_matches_naive_tplus2():
    r = settlement_date_holiday_aware("Taiwan (TWSE)", dt.date(2026, 7, 20))
    assert r["settles"] == dt.date(2026, 7, 22) and not r["holidays_skipped"]


def test_closure_warnings_golden_week():
    w = closure_warnings(["Japan (TSE)", "US"], dt.date(2026, 4, 28))
    assert any("Japan" in x and "tomorrow" in x for x in w)
    assert not any("US" in x for x in w)


def test_fx_notes_flag_restricted_currencies():
    d = pd.DataFrame(FX_NOTES).set_index("Ccy")
    for ccy in ("TWD", "KRW", "INR"):
        assert "Restricted" in d.loc[ccy, "Note"]


# ── A10: crossing ──────────────────────────────────────────────────────────

def _blot():
    return pd.DataFrame({
        "client": ["A", "B", "C", "A", "B"],
        "ticker": ["0700.HK", "0700.HK", "0700.HK", "600519.SS", "600519.SS"],
        "market": ["Hong Kong (HKEX)"] * 3 + ["China-A Shanghai"] * 2,
        "side": ["Buy", "Sell", "Sell", "Buy", "Sell"],
        "shares": [10_000, 6_000, 3_000, 5_000, 5_000],
        "price": [350.0] * 3 + [1500.0] * 2})


def test_crossable_is_min_of_sides_with_mechanism():
    r = crossing_report(_blot(), half_spread_bps=5.0)
    c = r["crosses"].set_index("ticker")
    assert c.loc["0700.HK", "crossable_shares"] == 9_000
    assert "report to HKEX" in c.loc["0700.HK", "mechanism"]
    assert "NO off-exchange" in c.loc["600519.SS", "mechanism"]
    # both sides save the half-spread: 9000*350*5bp*2
    assert c.loc["0700.HK", "est_spread_saved_usd"] == pytest.approx(
        9000 * 350 * 5e-4 * 2, rel=1e-6)


def test_same_client_both_ways_is_not_a_cross():
    b = pd.DataFrame({"client": ["A", "A"], "ticker": ["X", "X"],
                      "market": ["US", "US"], "side": ["Buy", "Sell"],
                      "shares": [100, 100], "price": [10.0, 10.0]})
    assert crossing_report(b)["n"] == 0


# ── A11: exposure scheduler ────────────────────────────────────────────────

def test_schedule_caps_path_deviation_at_band():
    es = exposure_schedule(pd.DataFrame(
        {"side": ["Buy", "Sell"], "shares": [100_000, 80_000],
         "price": [100.0, 100.0]}))
    assert es["available"]
    assert es["max_dev_scheduled"] <= es["band_usd"] + 1
    assert es["max_dev_frontloaded"] > es["max_dev_scheduled"]
    assert es["terminal_net"] == pytest.approx(2_000_000.0)


def test_schedule_completes_both_sides():
    es = exposure_schedule(pd.DataFrame(
        {"side": ["Buy", "Sell"], "shares": [50_000, 50_000],
         "price": [100.0, 100.0]}))
    sc = es["schedule"]
    assert sc["buy_notional"].sum() == pytest.approx(5_000_000.0)
    assert sc["sell_notional"].sum() == pytest.approx(5_000_000.0)
    assert abs(sc["cum_net"].iloc[-1]) < 1.0         # balanced basket ends flat
