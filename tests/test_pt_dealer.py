"""PT Dealer cockpit (agents/pt_dealer.py) — limit proximity, auction
countdown, attention triage, audit pack."""
import datetime as dt

import numpy as np
import pandas as pd
import pytest

from agents.pt_dealer import (limit_proximity, auction_countdown,
                              attention_queue, build_audit_pack,
                              save_audit_pack, demo_basket)


# ── limit proximity ────────────────────────────────────────────────────────

def test_taiwan_89pct_of_band_is_alert():
    lp = limit_proximity("Taiwan (TWSE)", 100.0, 108.9)
    assert lp["level"] == "ALERT" and lp["side"] == "upper"
    assert lp["used_frac"] == pytest.approx(0.89)


def test_taiwan_at_limit_is_locked():
    assert limit_proximity("Taiwan (TWSE)", 100.0, 110.0)["level"] == "LOCKED"


def test_downside_band_flagged_with_side():
    lp = limit_proximity("Vietnam (HOSE)", 100.0, 94.0)   # 6% of ±7% band
    assert lp["level"] == "ALERT" and lp["side"] == "lower"


def test_no_static_band_markets_return_na():
    lp = limit_proximity("Hong Kong (HKEX)", 100.0, 109.0)
    assert lp["level"] == "n/a" and "VCM" in lp["note"]


# ── auction countdown ──────────────────────────────────────────────────────

def test_auction_countdown_minutes_math():
    # 04:55 UTC = 12:55 Taipei -> 30.0 min to the 13:25 TWSE cutoff
    now = dt.datetime(2026, 7, 22, 4, 55)
    df = auction_countdown(["Taiwan (TWSE)"], now)
    assert df.iloc[0]["Mins to cutoff"] == pytest.approx(30.0)
    assert df.iloc[0]["Status"] == "🟡 <60m"


def test_auction_countdown_sorted_and_passed_flagged():
    now = dt.datetime(2026, 7, 22, 6, 0)   # 14:00 Taipei (cutoff passed), 15:00 JST
    df = auction_countdown(["Taiwan (TWSE)", "Japan (TSE)"], now)
    assert df.iloc[0]["Market"] == "Taiwan (TWSE)"          # most urgent first
    assert df.iloc[0]["Status"] == "PASSED"
    assert df[df["Market"] == "Japan (TSE)"].iloc[0]["Mins to cutoff"] == \
        pytest.approx(25.0)                                  # 15:25 JST cutoff


# ── attention queue ────────────────────────────────────────────────────────

@pytest.fixture
def basket():
    return demo_basket()


def test_short_block_pins_score_to_100(basket):
    q = attention_queue(basket, dt.datetime(2026, 7, 22, 1, 0))
    top = q.iloc[0]
    assert top["ticker"] == "600519.SS" and top["score"] == 100.0
    assert "SHORT BLOCKED" in top["reasons"]


def test_limit_alert_name_ranks_above_quiet_names(basket):
    q = attention_queue(basket, dt.datetime(2026, 7, 22, 1, 0)).set_index("ticker")
    assert q.loc["2330.TW", "score"] > q.loc["D05.SI", "score"]
    assert "limit ALERT" in q.loc["2330.TW", "reasons"]


def test_behind_schedule_and_dry_tape_reasons(basket):
    q = attention_queue(basket, dt.datetime(2026, 7, 22, 1, 0)).set_index("ticker")
    assert "behind" in q.loc["0700.HK", "reasons"]
    assert "tape running" in q.loc["7203.T", "reasons"]


def test_quiet_name_scores_low(basket):
    q = attention_queue(basket, dt.datetime(2026, 7, 22, 1, 0)).set_index("ticker")
    assert q.loc["D05.SI", "score"] <= 10.0


# ── audit pack ─────────────────────────────────────────────────────────────

def test_audit_pack_contents_and_roundtrip(basket, tmp_path):
    pack = build_audit_pack(basket, "PGM-2026-0722-01",
                            dt.datetime(2026, 7, 22, 1, 0,
                                        tzinfo=dt.timezone.utc))
    assert pack["n_names"] == 6 and len(pack["checks"]) == 6
    tw = next(c for c in pack["checks"] if c["ticker"] == "2330.TW")
    assert tw["limit"]["level"] == "ALERT"
    cn = next(c for c in pack["checks"] if c["ticker"] == "600519.SS")
    assert cn["short"]["level"] == "BLOCK"
    assert len(pack["attention_top3"]) == 3
    p = tmp_path / "audit.json"
    save_audit_pack(pack, p)
    save_audit_pack(pack, p)
    import json
    assert len(json.loads(p.read_text(encoding="utf-8"))) == 2
