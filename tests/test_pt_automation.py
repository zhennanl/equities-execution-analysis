"""Desk automations (agents/pt_automation.py) — pre-open pack, transition
alerts + ack log, EOD draft, recon classifier, event radar, rule version."""
import datetime as dt
import json

import numpy as np
import pandas as pd
import pytest

from agents.pt_automation import (preopen_pack, alert_scan, acknowledge,
                                  eod_client_summary, classify_breaks,
                                  event_radar)
from agents.pt_dealer import demo_basket, rules_version


@pytest.fixture
def basket():
    b = demo_basket()
    b["adv_shares"] = [5e6, 8e5, 2e7, 1e7, 3e6, 2e6]
    return b


# ── A1: pre-open pack ──────────────────────────────────────────────────────

def test_preopen_pack_flags_and_imbalance(basket):
    p = preopen_pack(basket, trade_date=dt.date(2026, 7, 22),
                     now_utc=dt.datetime(2026, 7, 21, 22, 0))
    assert p["n_names"] == 6
    assert p["n_blocked_shorts"] == 1               # China-A sell
    buy = (basket[basket.side == "Buy"].shares
           * basket[basket.side == "Buy"].prev_close).sum()
    sell = (basket[basket.side == "Sell"].shares
            * basket[basket.side == "Sell"].prev_close).sum()
    assert p["net_imbalance_frac"] == pytest.approx((buy - sell) / (buy + sell),
                                                    abs=1e-3)
    assert "PRE-OPEN BASKET PACK" in p["text"] and "BLOCKED" in p["text"]
    assert p["rules_version"] == rules_version()


def test_preopen_pack_capacity_rag(basket):
    p = preopen_pack(basket, trade_date=dt.date(2026, 7, 22))
    per = p["per_name"].set_index("ticker")
    # 600519.SS: 40k shares / (800k adv * 0.15) = 0.33 days -> GREEN
    assert per.loc["600519.SS", "flag"] == "GREEN"
    assert per.loc["600519.SS", "capacity_days"] == pytest.approx(0.33, abs=0.01)


# ── A2: alert engine ───────────────────────────────────────────────────────

def test_alerts_fire_once_per_transition(basket):
    now = dt.datetime(2026, 7, 22, 1, 0)
    a1, s1 = alert_scan(basket, None, now)
    kinds = {(a["ticker"], a["kind"]) for a in a1}
    assert ("2330.TW", "LIMIT") in kinds            # 89% of band -> ALERT
    assert ("7203.T", "LIQUIDITY") in kinds         # runrate 0.5
    a2, s2 = alert_scan(basket, s1, now + dt.timedelta(minutes=1))
    assert not a2                                    # no re-fire, no change


def test_alert_refires_on_escalation(basket):
    now = dt.datetime(2026, 7, 22, 1, 0)
    _, s1 = alert_scan(basket, None, now)
    b2 = basket.copy()
    b2.loc[b2.ticker == "2330.TW", "last_price"] = 110.0   # ALERT -> LOCKED
    a2, _ = alert_scan(b2, s1, now + dt.timedelta(minutes=5))
    assert any(a["ticker"] == "2330.TW" and "LOCKED" in a["message"]
               for a in a2)


def test_cutoff_alert_and_ack_log(basket, tmp_path):
    # 05:15 UTC = 13:15 Taipei -> 10 min to TWSE 13:25 cutoff, TW name 45% unfilled
    now = dt.datetime(2026, 7, 22, 5, 15)
    alerts, _ = alert_scan(basket, None, now)
    cut = [a for a in alerts if a["kind"] == "CUTOFF"]
    assert any(a["ticker"] == "2330.TW" for a in cut)
    log = tmp_path / "alerts.json"
    n = acknowledge(cut, who="dealer1", note="MOC submitted", path=log)
    saved = json.loads(log.read_text())
    assert len(saved) == n and saved[0]["acknowledged_by"] == "dealer1"
    assert saved[0]["rules_version"] == rules_version()


# ── A3: EOD summary ────────────────────────────────────────────────────────

def test_eod_summary_contents(basket):
    basket = basket.copy()
    basket["slippage_bps"] = [12.0, np.nan, 8.0, -3.0, 5.0, 4.0]
    txt = eod_client_summary(basket, "PGM-0722",
                             trade_date=dt.date(2026, 7, 22))
    assert "Subject: PGM-0722" in txt
    assert "Residuals" in txt and "roll to 2026-07-23" in txt
    assert "daily band" in txt                      # TW limit note
    assert "short unavailable" in txt               # China-A block
    assert "avg slippage" in txt
    assert rules_version() in txt


# ── A4: recon classifier ───────────────────────────────────────────────────

def test_classify_breaks_all_classes():
    ours = pd.DataFrame([
        dict(ticker="A", market="US", shares=1000, avg_price=10.00),
        dict(ticker="B", market="US", shares=2000, avg_price=20.00),
        dict(ticker="C", market="US", shares=3000, avg_price=30.00),
        dict(ticker="D", market="US", shares=4000, avg_price=40.00),
    ])
    street = pd.DataFrame([
        dict(ticker="A", market="US", shares=1000, avg_price=10.0001),  # tol
        dict(ticker="B", market="US", shares=1900, avg_price=20.00),    # qty
        dict(ticker="C", market="US", shares=3000, avg_price=30.30),    # px
        dict(ticker="E", market="US", shares=500,  avg_price=5.00),     # ours missing
    ])
    df, summary = classify_breaks(ours, street)
    cls = df.set_index("ticker")["class"]
    assert cls["A"] == "AUTO_CLEAR" and cls["B"] == "QTY_BREAK"
    assert cls["C"] == "PRICE_BREAK" and cls["D"] == "MISSING_STREET"
    assert cls["E"] == "MISSING_OURS"
    assert summary["needs_human"] == 4


# ── A5: event radar ────────────────────────────────────────────────────────

def test_event_radar_flags_window(basket):
    # MSCI May review effective ~ last business day of May
    df = event_radar(basket, today=dt.date(2026, 5, 26))
    assert (df["days_to_effective"] != "").any()
    assert df.iloc[0]["basket_names_at_risk"] == 6


def test_event_radar_quiet_period_returns_note(basket):
    df = event_radar(basket, today=dt.date(2026, 7, 12))
    if df.iloc[0]["provider"] == "—":
        assert "No provider review window" in df.iloc[0]["note"]


# ── A6: rules version ──────────────────────────────────────────────────────

def test_rules_version_stable_and_sensitive(monkeypatch):
    v1 = rules_version()
    assert v1 == rules_version() and len(v1) == 12
    import agents.pt_dealer as ptd
    monkeypatch.setitem(ptd.LIMIT_BANDS["Taiwan (TWSE)"], "band", 0.15)
    assert rules_version() != v1
