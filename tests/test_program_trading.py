"""Program Trading Desk (agents/program_trading.py) — all offline."""
import datetime

import numpy as np
import pandas as pd
import pytest

from agents.program_trading import (market_status, market_status_board,
                                    regulation_reference, lot_check, short_check,
                                    settlement_date, wave_plan,
                                    run_program_pretrade, program_recon, MARKET_REG)
from agents.agent1_market_data import MARKET_INFO


def test_reg_table_covers_every_market():
    assert set(MARKET_REG) == set(MARKET_INFO)
    ref = regulation_reference()
    assert len(ref) == len(MARKET_INFO)
    assert ref["Settlement"].isin(["T+1", "T+2"]).all()


def test_session_phases_at_0300_utc():
    now = datetime.datetime(2026, 7, 8, 3, 0)          # Wednesday
    assert market_status("Japan (TSE)", now)["phase"] == "Lunch"       # 12:00 JST
    assert market_status("China-A Shanghai", now)["phase"] == "Open"   # 11:00 CST
    assert market_status("India (NSE)", now)["phase"] == "Pre-open"    # 08:30 IST
    assert market_status("US", now)["phase"] == "Closed"               # 22:00 EST
    tw = market_status("Taiwan (TWSE)", now)
    assert tw["phase"] == "Open" and tw["mins_to_close"] == 150        # closes 13:30


def test_board_sorts_open_first():
    b = market_status_board(datetime.datetime(2026, 7, 8, 3, 0))
    assert b.iloc[0]["phase"] == "Open"
    assert b.iloc[-1]["phase"] == "Closed"


def test_lot_check_rounding():
    r = lot_check("Taiwan (TWSE)", 12_345)             # lot 1000
    assert not r["ok"] and r["rounded"] == 12_000 and r["odd"] == 345
    assert lot_check("Japan (TSE)", 400)["ok"]         # lot 100
    assert lot_check("US", 12_345)["ok"]               # lot 1
    hk = lot_check("Hong Kong (HKEX)", 777)
    assert hk["ok"] and "per-stock" in hk["note"]


def test_short_check_levels():
    assert short_check("China-A Shanghai", "Sell")["level"] == "BLOCK"
    assert short_check("Vietnam (HOSE)", "Sell")["level"] == "BLOCK"
    assert short_check("Japan (TSE)", "Sell", locate_confirmed=False)["level"] == "WARN"
    assert short_check("Japan (TSE)", "Sell", locate_confirmed=True)["level"] == "ok"
    assert short_check("Japan (TSE)", "Buy")["level"] == "none"


def test_settlement_dates_skip_weekends():
    fri = datetime.date(2026, 7, 10)                   # Friday
    assert settlement_date("US", fri) == datetime.date(2026, 7, 13)        # T+1 Mon
    assert settlement_date("Japan (TSE)", fri) == datetime.date(2026, 7, 14)  # T+2 Tue
    assert settlement_date("India (NSE)", fri) == datetime.date(2026, 7, 13)  # T+1


def test_wave_plan_orders_by_utc_close():
    w = wave_plan(["US", "Japan (TSE)", "Hong Kong (HKEX)", "India (NSE)"],
                  datetime.datetime(2026, 7, 8, 3, 0))
    order = w["Market"].tolist()
    assert order.index("Japan (TSE)") < order.index("Hong Kong (HKEX)") \
           < order.index("India (NSE)") < order.index("US")
    assert w["Wave"].tolist() == [1, 2, 3, 4]


def _fake_fetch(ticker_base, market):
    class MD: pass
    md = MD()
    md.ticker = f"{ticker_base}{MARKET_INFO[market]['suffix']}"
    md.adv_shares = 1_000_000.0
    if ticker_base == "BROKEN":
        raise ValueError("no data")
    return md


def test_program_pretrade_flags_and_ordering():
    prog = pd.DataFrame([
        {"ticker": "AAA", "market": "Japan (TSE)", "side": "Buy", "shares": 50_000},      # GREEN
        {"ticker": "BBB", "market": "Taiwan (TWSE)", "side": "Buy", "shares": 600_000},   # RED (4 days), odd lots? 600k/1000 ok
        {"ticker": "CCC", "market": "China-A Shanghai", "side": "Sell", "shares": 50_050},# BLOCK + odd lot
        {"ticker": "BROKEN", "market": "US", "side": "Buy", "shares": 1_000},
    ])
    out = run_program_pretrade(prog, fetch_fn=_fake_fetch,
                               trade_date=datetime.date(2026, 7, 8))
    assert out.iloc[0]["Error"] != ""                          # errors first
    assert out.iloc[1]["Flag"] == "RED"                        # then RED by %ADV
    ccc = out[out["Ticker"].str.startswith("CCC")].iloc[0]
    assert "BLOCK" in ccc["Notes"] and "odd-lot" in ccc["Notes"]
    assert ccc["Lot-rounded"] == 50_000
    jp = out[out["Market"] == "Japan (TSE)"].iloc[0]
    assert jp["Settles"] == "2026-07-10"                       # T+2 from Wed
    assert jp["Flag"] == "GREEN"


def test_program_recon_ties_out():
    prog = pd.DataFrame([
        {"ticker": "AAA", "market": "Taiwan (TWSE)", "side": "Buy", "shares": 12_345}])
    out = run_program_pretrade(prog, fetch_fn=_fake_fetch,
                               trade_date=datetime.date(2026, 7, 8))
    rep = program_recon(out)
    assert "PROGRAM RECONCILIATION" in rep
    assert "12,345" in rep and "12,000" in rep and "345" in rep
    assert "odd-lot" in rep
