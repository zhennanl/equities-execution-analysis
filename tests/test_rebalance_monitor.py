"""AI rebalance-interest monitor (agents/rebalance_monitor.py)."""
import numpy as np
import pandas as pd
import pytest

from agents.rebalance_monitor import (interest_features, interest_score,
                                      learn_weights, monitor_report,
                                      monitor_alerts, demo_monitor_panel,
                                      demo_event_panel, STATIC_W)


def test_features_scale_and_bounds():
    d = demo_monitor_panel()["HOT.T"]
    f = interest_features(d)
    assert f["available"]
    assert f["vol"] == 1.0                          # 3.5x tape caps at 1
    assert 0 <= f["drift"] <= 1 and f["drift_sign"] == 1.0
    assert f["vol_ratio_raw"] > 3.0


def test_score_composite_and_reasons():
    sc = interest_score({"vol": 1.0, "drift": 0.5, "range": 0.0,
                         "short": 0.0, "news": 0.0})
    assert sc["score"] == pytest.approx(52.5)       # 40 + 12.5
    assert "vol=1.00" in sc["reasons"]


def test_learned_weights_win_when_static_is_wrong():
    lw = learn_weights(demo_event_panel(40, signal=3.0))
    assert lw.available and lw.source == "learned"
    assert lw.weights["news"] > STATIC_W["news"]    # recovers true driver
    assert lw.dm_p < 0.10 and lw.mae_learned < lw.mae_static


def test_gate_ships_static_on_noise():
    lw = learn_weights(demo_event_panel(40, signal=0.0))
    assert lw.available and lw.source == "static"
    assert lw.weights == STATIC_W
    assert "house rule" in lw.note


def test_thin_library_ships_static_with_disclosure():
    lw = learn_weights(demo_event_panel(8))
    assert not lw.available and lw.weights == STATIC_W
    assert "8" in lw.reason


def test_monitor_ranks_planted_names():
    r = monitor_report(demo_monitor_panel(),
                       extras={"HOT.T": {"news_count": 8}})
    assert list(r["ticker"]) == ["HOT.T", "WARM.HK", "QUIET.SI"]
    tiers = r.set_index("ticker")["tier"]
    assert tiers["HOT.T"] == "HOT" and tiers["WARM.HK"] == "WARM"
    assert tiers["QUIET.SI"] == "quiet"


def test_alerts_fire_once_and_escalate():
    r = monitor_report(demo_monitor_panel())        # HOT.T is WARM w/o news
    a1, t1 = monitor_alerts(r)
    assert {x["ticker"] for x in a1} == {"HOT.T", "WARM.HK"}
    a2, t2 = monitor_alerts(r, t1)
    assert a2 == []                                 # no re-fire
    r2 = monitor_report(demo_monitor_panel(),
                        extras={"HOT.T": {"news_count": 8}})
    a3, _ = monitor_alerts(r2, t2)                  # WARM -> HOT escalation
    assert [x["ticker"] for x in a3] == ["HOT.T"]
    assert a3[0]["tier"] == "HOT"


def test_short_history_degrades():
    d = demo_monitor_panel()["HOT.T"].iloc[-10:]
    r = monitor_report({"X": d})
    assert r.iloc[0]["tier"] == "n/a"
