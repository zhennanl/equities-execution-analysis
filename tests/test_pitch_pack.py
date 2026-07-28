"""Pitch-pack tests — canned data, no network."""
import numpy as np
import pandas as pd
import pytest

from agents import pitch_pack as pp


EVENT_CACHE = {
    "MSCI-TW del A": {"available": True, "provider": "MSCI",
                      "side": "Sell", "t_day_volume_multiple": 16.0,
                      "eff": "2026-05-29"},
    "MSCI-TW del B": {"available": True, "provider": "MSCI",
                      "side": "Sell", "t_day_volume_multiple": 38.0,
                      "eff": "2026-05-29"},
    "TW50 del C": {"available": True, "provider": "FTSE",
                   "side": "Sell", "t_day_volume_multiple": 5.0,
                   "eff": "2026-06-18"},
    "_meta": [1, 2, 3],
}


def test_t_multiples_point_in_time_gating():
    s = pp.expected_t_multiples(EVENT_CACHE, "MSCI", "Sell",
                                as_of="2026-06-01")
    assert s["available"] and s["n"] == 2 and s["median"] == 27.0
    # FTSE event effective Jun 18 must NOT leak into a Jun-1 pack
    f = pp.expected_t_multiples(EVENT_CACHE, "FTSE", "Sell",
                                as_of="2026-06-01")
    assert not f["available"]
    # ...but appears without the gate
    f2 = pp.expected_t_multiples(EVENT_CACHE, "FTSE", "Sell")
    assert f2["available"] and f2["n"] == 1


def test_crowding_table_respects_as_of():
    cache = {"short": {
        "20260520": {"X": [0, 10000]},
        "20260601": {"X": [0, 20000]},
        "20260610": {"X": [0, 90000]},      # post-as_of: must be unseen
    }}
    df = pp.crowding_table(cache, {"X": "x"}, ann_date="2026-06-05",
                           as_of="2026-06-04")
    assert df.iloc[0]["pre_ann_build_pct"] == pytest.approx(100.0)


def test_risk_flags_rules():
    names = pd.DataFrame([
        {"ticker": "A", "side": "Sell", "adv_days": 7.0,
         "band_pct": 10.0, "borrow_constrained": True},
        {"ticker": "B", "side": "Buy", "adv_days": 0.1,
         "band_pct": np.nan, "borrow_constrained": False},
    ])
    f = pp.risk_flags(names)
    a = f[f["ticker"] == "A"].iloc[0]
    assert a["n_flags"] == 4          # size, limit, borrow, reversal
    assert f[f["ticker"] == "B"].iloc[0]["n_flags"] == 0


def test_track_record_ships_misses():
    tr = pp.track_record()
    text = " ".join(tr["record"]) + " ".join(tr["caveat"])
    assert "50-60%" in text                 # the weak spot is IN
    assert "falsified" in text              # self-falsification is IN
    assert (tr["caveat"].str.len() > 0).all()   # every claim caveated


def _pack():
    preds = pd.DataFrame([("X", "XCo", "ADD", "HIGH", 30),
                          ("Y", "YCo", "DELETE", "LOW", 5)],
                         columns=["ticker", "name", "change",
                                  "confidence", "margin_pct"])
    flows = pd.DataFrame([("X", "Buy", 100, 6.0, "MULTI-DAY")],
                         columns=["ticker", "side", "flow_usd_m",
                                  "adv_days", "bucket"])
    crowd = pd.DataFrame([{"ticker": "X", "label": "x",
                           "pre_ann_build_pct": 30.0,
                           "crowding": "HIGH", "read": "r"}])
    flags = pp.risk_flags(pd.DataFrame([
        {"ticker": "X", "side": "Buy", "adv_days": 6.0,
         "band_pct": 10.0, "borrow_constrained": False}]))
    return pp.build_pitch_pack(
        "TEST EVENT", "2026-08-12", "2026-09-01", "2026-08-01",
        preds, flows, crowd,
        {"MSCI deletions (Sell)": {"available": True, "n": 2,
                                   "median": 16.0, "min": 7.0,
                                   "max": 38.0}},
        flags, notes="n")


def test_render_contains_all_sections_and_pit_statement():
    md = pp.render_pitch_markdown(_pack())
    for sec in ["Predicted changes", "Expected flows", "measured",
                "Street positioning", "risk flags", "track record"]:
        assert sec.lower() in md.lower()
    assert "2026-08-01" in md            # point-in-time statement


def test_validate_pack_scores_hits_misses_and_blindspots():
    pack = _pack()
    outcomes = pd.DataFrame([("X", True), ("Y", False), ("Z", True)],
                            columns=["ticker", "actual_change"])
    s = pp.validate_pack(pack, outcomes,
                         {"MSCI deletions (Sell)": 20.0})
    assert s["predictions"].startswith("1/2")
    assert s["high_conf_precision"] == "1/1 HIGH-confidence calls correct"
    assert s["misses"] == ["Y"] and s["not_predicted"] == ["Z"]
    assert "IN RANGE" in s["t_multiple_checks"][0]
    md = pp.render_validation_markdown(s)
    assert "grades itself" in md
