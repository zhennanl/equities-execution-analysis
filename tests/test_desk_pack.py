"""Desk pack (P-A), run library (P-C), live volume re-forecast (B4/P-D)."""
import numpy as np
import pandas as pd
import pytest

from agents.desk_pack import (build_desk_verdict, pretrade_card_text,
                              record_run, load_runs, run_stats,
                              CAPACITY_GREEN_MAX_DAYS, CAPACITY_RED_MIN_DAYS)
from agents.agent11_live_snapshot import live_volume_forecast
from agents.agent1_market_data import MARKET_INFO
from agents.orchestrator import run_pipeline
from tests.conftest import make_market_data


@pytest.fixture(scope="module")
def pipe():
    md = make_market_data()
    ctx = run_pipeline(md, 5.0, "Medium")     # same entry point the app uses
    assert ctx.memo is not None and ctx.pretrade is not None
    return md, ctx.sim, ctx.comp, ctx.regime, ctx.memo, ctx.pretrade, ctx.critic


def test_desk_verdict_headline_and_capacity_flag(pipe):
    md, sim, comp, regime, memo, pretrade, critic = pipe
    dv = build_desk_verdict(memo, critic, pretrade, sim, md.adv_shares * 0.05,
                            md.adv_shares, "Medium")
    assert memo.primary_algo in dv.headline
    assert "5.0% ADV" in dv.headline
    assert dv.flag in ("GREEN", "AMBER", "RED")
    exp_flag = ("GREEN" if dv.days_to_complete <= CAPACITY_GREEN_MAX_DAYS
                else "RED" if dv.days_to_complete > CAPACITY_RED_MIN_DAYS else "AMBER")
    assert dv.flag == exp_flag


def test_pretrade_card_contains_desk_essentials(pipe):
    md, sim, comp, regime, memo, pretrade, critic = pipe
    dv = build_desk_verdict(memo, critic, pretrade, sim, md.adv_shares * 0.05,
                            md.adv_shares, "Medium")
    card = pretrade_card_text("TEST", "US", memo, critic, pretrade, regime, sim,
                              md.adv_shares * 0.05, md.adv_shares, "Medium", dv)
    for needle in ("PRE-TRADE REPORT — TEST", "ORDER", "RECOMMENDED",
                   "CAPACITY", "REGIME", memo.primary_algo):
        assert needle in card, needle


def test_run_library_roundtrip_dedupe_and_stats(tmp_path):
    path = tmp_path / "runs.json"
    kw = dict(ticker="T", market="US", side="Buy", order_pct_adv=5.0,
              urgency="Medium", algo="VWAP", sim_day="2026-06-04", path=path)
    record_run(predicted_bps=10.0, realized_bps=14.0, **kw)
    record_run(predicted_bps=10.0, realized_bps=12.0, **kw)      # same key -> update
    record_run(predicted_bps=8.0, realized_bps=6.0, ticker="U", market="US",
               side="Buy", order_pct_adv=5.0, urgency="Medium", algo="TWAP",
               sim_day="2026-06-04", path=path)
    rows = load_runs(path)
    assert len(rows) == 2
    st = run_stats(path)
    assert st["n"] == 2 and st["n_scored"] == 2
    assert st["bias_bps"] == pytest.approx(((12 - 10) + (6 - 8)) / 2)   # 0.0
    assert st["mae_bps"] == pytest.approx(2.0)
    assert st["by_algo"] == {"VWAP": 1, "TWAP": 1}


# ── live volume re-forecast ────────────────────────────────────────────────

def _lv_fixture(mult=2.0, k=20, n=78):
    md = make_market_data()
    bars = MARKET_INFO["US"]["bars"]
    dates = sorted(md.intraday.index.normalize().unique())
    today = dates[-1]
    day_full = md.intraday[md.intraday.index.normalize() == today].copy()
    n = len(day_full)
    day_full["Volume"] = day_full["Volume"] * mult      # today runs at mult x normal
    view_day = day_full.iloc[:k]
    return md, today, view_day, day_full, n


def test_volume_run_rate_detects_hot_tape():
    md, today, view_day, day_full, n = _lv_fixture(mult=2.0, k=20)
    f = live_volume_forecast(md.intraday, today, view_day, day_full,
                             md.adv_shares, remaining_shares=1000.0)
    assert f.available
    assert f.run_rate is not None and f.run_rate > 1.25          # tape is hot
    assert "ABOVE" in f.note
    assert f.projected_vs_adv is not None and f.projected_vs_adv > 1.2


def test_volume_forecast_completion_projection():
    md, today, view_day, day_full, n = _lv_fixture(mult=1.0, k=20)
    tiny = live_volume_forecast(md.intraday, today, view_day, day_full,
                                md.adv_shares, remaining_shares=100.0,
                                participation_rate=0.15)
    assert tiny.available and tiny.completion_feasible
    assert tiny.projected_finish_time not in ("", "not by the close at this participation")
    huge = live_volume_forecast(md.intraday, today, view_day, day_full,
                                md.adv_shares,
                                remaining_shares=md.adv_shares * 10,
                                participation_rate=0.10)
    assert huge.available and not huge.completion_feasible
    assert "not by the close" in huge.projected_finish_time


def test_volume_forecast_degrades_without_bars():
    md, today, view_day, day_full, n = _lv_fixture()
    f = live_volume_forecast(md.intraday, today, view_day.iloc[:0], day_full,
                             md.adv_shares, 100.0)
    assert not f.available
