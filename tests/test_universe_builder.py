"""Universe validator + eligibility + confidence tags — the generic fix
for the FTSE-backtest failure mode (session 6y)."""
import numpy as np
import pandas as pd
import pytest

from agents.universe_builder import (UniverseSpec, validate_universe,
                                     LISTING_ELIGIBILITY, _suffix_ok)
from agents.reconstitution import predict_ftse, FTSERules


def _u(rows):
    return pd.DataFrame([dict(ticker=t, full_mktcap_usd=c*1e9,
                              free_float_frac=f, adv_usd=c*1e9*0.004,
                              atvr=1.0) for t, c, f in rows])


# ── the meta-test: replay the ACTUAL round-1 Taiwan errors ─────────────────

def test_validator_catches_all_three_round1_errors():
    # (1) 49 members where the index holds 50; (2) TPEx-listed MPI in a
    # TWSE-only universe; (3) thin rank ladder at the delete boundary.
    rows = [(f"N{i:02d}.TW", 100 - i, 0.7) for i in range(49)] \
         + [("6223.TWO MPI", 9.5, 0.65)]
    u = _u(rows)
    members = {f"N{i:02d}.TW" for i in range(49)}
    spec = UniverseSpec(market="Taiwan (TWSE)", index_size=50,
                        add_rank=40, delete_rank=61)
    v = validate_universe(u, members, spec)
    assert not v["ok"]
    assert any("membership count 49" in i for i in v["issues"])
    assert any("6223.TWO" in i and "not eligible" in i for i in v["issues"])
    assert any("delete-boundary" in i and "thin" in i for i in v["issues"])


def test_clean_universe_passes():
    rows = [(f"N{i:02d}.TW", 200 - 2 * i, 0.7) for i in range(70)]
    u = _u(rows)
    members = {f"N{i:02d}.TW" for i in range(50)}
    spec = UniverseSpec(market="Taiwan (TWSE)", index_size=50,
                        add_rank=40, delete_rank=61)
    v = validate_universe(u, members, spec)
    assert v["ok"], v["issues"]


def test_duplicate_and_bad_float_flagged():
    u = _u([("A.TW", 10, 0.7), ("A.TW", 10, 0.7), ("B.TW", 8, 1.5)])
    v = validate_universe(u, {"A.TW"}, UniverseSpec(market="Taiwan (TWSE)"))
    assert any("duplicate" in i for i in v["issues"])
    assert any("float outside" in i for i in v["issues"])


def test_suffix_rules_per_market():
    assert _suffix_ok("2330.TW", LISTING_ELIGIBILITY["Taiwan (TWSE)"])
    assert not _suffix_ok("6223.TWO", LISTING_ELIGIBILITY["Taiwan (TWSE)"])
    assert not _suffix_ok("035420.KQ", LISTING_ELIGIBILITY["Korea (KRX)"])
    assert _suffix_ok("AAPL", LISTING_ELIGIBILITY["US"])
    assert not _suffix_ok("2330.TW", LISTING_ELIGIBILITY["US"])


# ── engine-level eligibility (the MPI fix inside predict_ftse) ─────────────

def test_engine_excludes_ineligible_candidate_from_adds():
    rows = [(f"M{i:02d}.TW", 100 - i, 0.7) for i in range(10)] \
         + [("BIG.TWO", 95, 0.7)]                  # huge but TPEx-listed
    u = _u(rows)
    members = {f"M{i:02d}.TW" for i in range(8)}
    r_off = predict_ftse(u, members, FTSERules(index_size=8, add_rank=7,
                                               delete_rank=10))
    r_on = predict_ftse(u, members, FTSERules(index_size=8, add_rank=7,
                                              delete_rank=10,
                                              allowed_suffixes=(".TW",)))
    assert "BIG.TWO" in set(r_off["adds"]["ticker"])   # without the screen
    on_adds = set(r_on["adds"]["ticker"]) if len(r_on["adds"]) else set()
    assert "BIG.TWO" not in on_adds


# ── boundary-confidence tags ───────────────────────────────────────────────

def test_confidence_tags_label_fragile_calls():
    # one clear riser (39% above the boundary cap) and one marginal riser
    # (0.9% above it) — the tags must separate them.
    caps = list(np.linspace(100, 60, 8)) + [80.0, 58.0, 57.5]
    rows = [(f"M{i:02d}.TW", c, 0.7) for i, c in enumerate(caps)]
    u = _u(rows)
    members = {f"M{i:02d}.TW" for i in range(8)}     # index grows 8 -> 10
    r = predict_ftse(u, members, FTSERules(index_size=10, add_rank=10,
                                           delete_rank=12))
    adds = r["adds"].set_index("ticker")
    assert {"confidence", "margin_pct"} <= set(adds.columns)
    assert adds.loc["M08.TW", "confidence"] == "HIGH"          # 80 vs 57.5
    assert adds.loc["M08.TW", "margin_pct"] > 30
    assert adds.loc["M09.TW", "confidence"].startswith("LOW")  # 58 vs 57.5
    assert adds.loc["M09.TW", "margin_pct"] < 2


def test_probabilistic_confidence_monotone_and_bounded():
    caps = list(np.linspace(100, 60, 8)) + [80.0, 58.0, 57.5]
    rows = [(f"M{i:02d}.TW", c, 0.7) for i, c in enumerate(caps)]
    u = _u(rows)
    members = {f"M{i:02d}.TW" for i in range(8)}
    r = predict_ftse(u, members, FTSERules(index_size=10, add_rank=10,
                                           delete_rank=12))
    adds = r["adds"].set_index("ticker")
    p_big = adds.loc["M08.TW", "p_survives_noise"]     # 39% margin
    p_thin = adds.loc["M09.TW", "p_survives_noise"]    # 0.9% margin
    assert 0 <= p_thin < p_big <= 1
    assert p_big > 0.95 and p_thin < 0.60


def test_reserve_list_emitted_excludes_adds():
    caps = list(np.linspace(100, 40, 20))
    rows = [(f"M{i:02d}.TW", c, 0.7) for i, c in enumerate(caps)]
    u = _u(rows)
    members = {f"M{i:02d}.TW" for i in range(10)}
    r = predict_ftse(u, members, FTSERules(index_size=10, add_rank=9,
                                           delete_rank=13))
    res = r["reserve_list"]
    assert 1 <= len(res) <= 5
    assert not set(res["ticker"]) & set(r["adds"].get("ticker", []))
    assert (res["rank"] > 9).all()                     # all below add boundary
