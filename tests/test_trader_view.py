"""Trader-view packaging (agents/trader_view.py) — all offline.

Reuses test_agent14's synthetic pressure-reversal event so card/verdict
numbers sit on the same pinned anchors (S1 cost 1000 bps at eta=0)."""
import json

import numpy as np
import pandas as pd
import pytest

from agents.agent14_rebalance_strategist import analyze_strategies
from agents.trader_view import (auction_rag, build_verdict, trade_card_text,
                                schedules_csv, build_playbook, playbook_text,
                                recommended_bucket_split, run_basket,
                                record_event, load_library, library_stats,
                                library_context_line, plain_reversal_read)
from agents.rebalancing_event_study import compute_reversal
from tests.test_agent14 import _pressure_reversal_es


def _es():
    es = _pressure_reversal_es()
    es.ticker, es.index_name, es.T = "TEST.NS", "NIFTY 50", pd.Timestamp("2026-03-16")
    return es


def _ana(**kw):
    return analyze_strategies(_es(), side="Buy", order_shares=50_000.0, eta=0.0, **kw)


# ── RAG thresholds ─────────────────────────────────────────────────────────

def test_auction_rag_thresholds():
    # est auction volume = 10% of 1M = 100k shares
    assert auction_rag(10_000, 1_000_000)[0] == "GREEN"    # 10%
    assert auction_rag(20_000, 1_000_000)[0] == "AMBER"    # 20%
    assert auction_rag(30_000, 1_000_000)[0] == "RED"      # 30%
    flag, frac = auction_rag(25_000, 1_000_000)
    assert flag == "AMBER" and frac == pytest.approx(0.25)  # boundary is amber


# ── verdict ────────────────────────────────────────────────────────────────

def test_verdict_tracker_objective_picks_s1_and_flags_red():
    v = build_verdict(_es(), _ana(), "Index Tracker")
    assert v.strategy_name.startswith("S1")
    assert v.cost_vs_decision_bps == 1000.0
    assert v.tracking_diff_bps == 0.0
    # 50k order vs est auction 10% x 1M = 100k -> 50% -> RED
    assert v.auction_flag == "RED"
    assert "S1" in v.headline and "🔴" in v.headline


def test_verdict_cost_objective_picks_cheapest():
    v = build_verdict(_es(), _ana(), "Cost-Minimizing")
    a = _ana()
    best = min(a.strategies, key=lambda s: (s.cost_vs_decision_bps, s.abs_tracking_bps))
    assert v.strategy_name == best.name


# ── card + exports ─────────────────────────────────────────────────────────

def test_bucket_split_s2_halves():
    a = _ana(pre_frac=0.5)
    s2 = next(s for s in a.strategies if s.name.startswith("S2"))
    split = recommended_bucket_split(s2)
    assert split["auction"] == pytest.approx(25_000.0, abs=1.0)
    assert split["pre"] == pytest.approx(25_000.0, abs=1.0)
    assert split["post"] == 0.0


def test_trade_card_contains_the_numbers_a_desk_needs():
    a = _ana()
    v = build_verdict(_es(), a, "Index Tracker")
    card = trade_card_text(_es(), None, a, v)
    for needle in ("TEST.NS", "BUY 50,000 sh", "S1", "RED",
                   "cost +1000 bps", "2026-03-16"):
        assert needle in card, needle


def test_schedules_csv_has_all_strategies_and_auction_rows():
    csv = schedules_csv(_ana())
    df = pd.read_csv(pd.io.common.StringIO(csv))
    assert set(x.split()[0] for x in df["Strategy"].unique()) == {"S1", "S2", "S3", "S4"}
    assert (df["Venue"] == "Closing auction").sum() >= 4


# ── playbook ───────────────────────────────────────────────────────────────

def test_playbook_uses_library_median_when_n_sufficient():
    a = _ana()
    v = build_verdict(_es(), a, "Index Tracker")
    steps = build_playbook(_es(), None, a, v,
                           library_stats_row={"n": 5, "median_abs_runup_pct": 4.0,
                                              "median_reversal_fraction": 0.5})
    joined = " ".join(steps)
    assert "6.0%" in joined            # 1.5 x 4.0 median
    assert "library median, n=5" in joined
    assert "RED" in joined and "25%" in joined
    txt = playbook_text(_es(), steps)
    assert txt.splitlines()[0].startswith("CONDITIONAL PLAYBOOK — TEST.NS")


# ── event library ──────────────────────────────────────────────────────────

class _Rev:  # minimal insights stand-in
    def __init__(self):
        self.reversal = compute_reversal(
            np.array([0.0]*6 + [0.01, 0.02, 0.03, 0.04, 0.05]
                     + [0.044, 0.038, 0.032, 0.026, 0.02] + [0.02]*5),
            np.arange(-10, 11))
        self.drift = type("D", (), {"pct_of_pre_event_move_after_announcement": 80.0})()
        self.eta_calib = type("E", (), {"implied_eta": 1.5})()


def test_library_roundtrip_and_stats(tmp_path):
    path = tmp_path / "lib.json"
    es = _es()
    record_event(es, _Rev(), path=path)
    es2 = _es(); es2.ticker = "OTHER.NS"
    record_event(es2, _Rev(), path=path)
    record_event(es, _Rev(), path=path)          # same ticker+T -> update, not dup
    rows = load_library(path)
    assert len(rows) == 2
    stats = library_stats(path)
    assert stats["n"] == 2
    assert stats["median_reversal_fraction"] == pytest.approx(0.6)
    assert stats["median_implied_eta"] == pytest.approx(1.5)
    line = library_context_line(_Rev(), stats)
    assert "n=" in line or "recorded" in line


def test_plain_reversal_read_transient():
    assert "came back within 5 days" in plain_reversal_read(_Rev().reversal)


# ── basket mode (synthetic study runner — no network) ─────────────────────

def test_run_basket_ranks_red_first_and_degrades_per_name():
    def fake_study(ticker_base, market, rebal_date, event_window, index_name):
        if ticker_base == "BROKEN":
            raise ValueError("No data returned for 'BROKEN'.")
        es = _pressure_reversal_es()
        es.ticker = f"{ticker_base}.X"
        es.index_name = index_name
        es.T = pd.Timestamp("2026-03-16")
        return es

    basket = pd.DataFrame([
        {"ticker": "SMALL", "market": "US", "side": "Buy", "shares": 5_000},    # 5%  GREEN
        {"ticker": "BIG",   "market": "US", "side": "Sell", "shares": 60_000},  # 60% RED
        {"ticker": "BROKEN","market": "US", "side": "Buy", "shares": 1_000},
        {"ticker": "MID",   "market": "US", "side": "Buy", "shares": 20_000},   # 20% AMBER
    ])
    out = run_basket(basket, rebal_date=None, event_window=10,
                     index_name="NIFTY 50", study_fn=fake_study)
    assert list(out["Ticker"])[:2] == ["BROKEN", "BIG.X"]   # errors first, then RED
    assert list(out["Auction flag"]) == ["n/a", "RED", "AMBER", "GREEN"]
    assert "No data returned" in out.loc[0, "Error"]
    assert out.loc[1, "% est. auction vol"] == pytest.approx(60.0)


# ── P1: crowding score + expected move (streams D and E) ──────────────────

from agents.trader_view import crowding_score, expected_move, CrowdingScore
from agents.rebalancing_event_study import FlowToTrade


def test_crowding_unavailable_without_any_proxy():
    cs = crowding_score(_es(), None)
    assert not cs.available


def test_crowding_components_and_tiers():
    es = _es()
    # drift stub: 20% of the move after announcement -> 80 before -> crowded
    ins = type("I", (), {"drift": type("D", (), {
        "available": True, "pct_of_pre_event_move_after_announcement": 20.0})()})()
    ann = pd.Timestamp(es.event_dates[6])          # rel day -4
    # ab_vol == 1.0 pre-announcement -> volume component 0 -> mean(80, 0) = 40
    cs = crowding_score(es, ins, announcement_date=ann)
    assert cs.available and cs.score == pytest.approx(40.0)
    assert cs.tier == "MODERATE"
    # add heavy short build: mean(80, 0, 100) = 60 -> still MODERATE; 2 comps -> HIGH
    cs2 = crowding_score(es, ins, short_interest_change_pct=60.0)
    assert cs2.score == pytest.approx(90.0) and cs2.tier == "HIGH"
    assert "S3" in cs2.insight
    cs3 = crowding_score(es, None, short_interest_change_pct=5.0)
    assert cs3.tier == "LOW" and "S2/S4" in cs3.insight
    assert "Components" in cs.detail


def test_playbook_appends_step_on_high_crowding():
    a = _ana()
    v = build_verdict(_es(), a, "Index Tracker")
    base = build_playbook(_es(), None, a, v)
    high = build_playbook(_es(), None, a, v, crowding_tier="HIGH")
    assert len(high) == len(base) + 1 and "Crowding score is HIGH" in high[-1]


def test_expected_move_bands():
    es = _es()                                    # ADV 1M, sigma 0.02
    flow = FlowToTrade(notional_usd=1_000_000.0, shares=10_000.0, flow_pct_adv=1.0)
    em = expected_move(flow, es)                  # eta 0.3 x 0.02 x sqrt(1%) = 6 bps
    assert em.available
    assert em.sqrt_low_bps == pytest.approx(6.0)
    assert em.sqrt_high_bps is None               # no library median yet
    em2 = expected_move(flow, es, float_mcap_usd=100e6,
                        lib={"n": 5, "median_implied_eta": 0.6})
    assert em2.sqrt_high_bps == pytest.approx(12.0)
    # flow = 1% of float cap -> M 3-8 -> 300-800 bps
    assert em2.mult_low_bps == pytest.approx(300.0)
    assert em2.mult_high_bps == pytest.approx(800.0)
    assert "crowding" in em2.detail


def test_expected_move_needs_flow():
    assert not expected_move(None, _es()).available


def test_library_side_split(tmp_path):
    path = tmp_path / "lib.json"
    es = _es()
    record_event(es, _Rev(), path=path, action="Delete")
    es2 = _es(); es2.ticker = "OTHER.NS"
    record_event(es2, _Rev(), path=path, action="Add")
    assert library_stats(path)["n"] == 2
    assert library_stats(path, action="Delete")["n"] == 1
    assert library_stats(path, action="Add")["n"] == 1


# ── Best-ex record store (proposal P2) ─────────────────────────────────────

from agents.trader_view import build_bestex_record, record_bestex


def test_bestex_record_roundtrip_and_dedupe(tmp_path):
    path = tmp_path / "bestex.json"
    a = _ana()
    v = build_verdict(_es(), a, "Index Tracker")
    steps = build_playbook(_es(), None, a, v)
    rec = build_bestex_record(_es(), v, a, "Index Tracker", steps, library_n=4)
    record_bestex(rec, path=path)
    record_bestex(rec, path=path)                       # rerun -> update, not dup
    rec2 = build_bestex_record(_es(), v, a, "Cost-Minimizing", steps)
    record_bestex(rec2, path=path)
    rows = json.loads(path.read_text())
    assert len(rows) == 2
    r = rows[0]
    assert r["decision"]["strategy"].startswith("S1")
    assert r["decision"]["expected_cost_vs_decision_bps"] == 1000.0
    assert r["evidence"]["event_library_n"] == 4
    assert len(r["evidence"]["frontier"]) == 4          # S1-S4 snapshot
    assert len(r["playbook"]) >= 5
