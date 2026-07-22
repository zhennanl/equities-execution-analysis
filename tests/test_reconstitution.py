"""Rulebook reconstitution predictor (agents/reconstitution.py)."""
import numpy as np
import pandas as pd
import pytest

from agents.reconstitution import (predict_msci, predict_ftse, expected_flow,
                                   demo_universe, MSCIRules, FTSERules)


def _uni(caps, floats=None, atvr=None, advs=None):
    n = len(caps)
    return pd.DataFrame({
        "ticker": [f"S{i:02d}" for i in range(n)],
        "full_mktcap_usd": caps,
        "free_float_frac": floats or [0.8] * n,
        "adv_usd": advs or [1e7] * n,
        "atvr": atvr or [1.0] * n})


# ── MSCI mechanics ─────────────────────────────────────────────────────────

def test_gmsr_is_cap_at_coverage_crossing():
    # 4 equal-float names 40/30/20/10: cum FF coverage .4/.7/.9/1.0 ->
    # 85% crossed at the 3rd name -> GMSR = 20
    u = _uni([40e9, 30e9, 20e9, 10e9])
    r = predict_msci(u, members=set(u["ticker"]))
    assert r["gmsr_usd"] == pytest.approx(20e9)
    assert r["delete_threshold_usd"] == pytest.approx(10e9)      # 0.5x
    assert r["add_threshold_usd"] == pytest.approx(23e9)         # 1.15x


def test_incumbent_inside_buffer_survives_newcomer_needs_more():
    u = _uni([40e9, 30e9, 20e9, 12e9, 22e9])       # S04 non-member at 22B
    members = {"S00", "S01", "S02", "S03"}
    r = predict_msci(u, members)
    # GMSR shifts with S04 in the sorted universe; S03 (12B) must stay if
    # above 0.5x GMSR, and S04 below 1.15x GMSR must NOT add
    dels = set(r["deletes"].get("ticker", []))
    adds = set(r["adds"].get("ticker", []))
    assert "S03" not in dels                        # buffer keeps incumbent
    assert "S04" not in adds                        # 22B < 1.15x GMSR


def test_qir_hurdle_stricter_than_sair():
    u = _uni([40e9, 30e9, 20e9, 10e9, 25e9])       # S04 non-member 25B
    members = {"S00", "S01", "S02", "S03"}
    sair = predict_msci(u, members, MSCIRules(review="SAIR"))
    qir = predict_msci(u, members, MSCIRules(review="QIR"))
    assert "S04" in set(sair["adds"]["ticker"])     # 25B >= 1.15x GMSR
    assert "S04" not in set(qir["adds"].get("ticker", []))   # < 1.8x GMSR


def test_screens_delete_low_float_member_and_block_illiquid_add():
    u = _uni([40e9, 30e9, 20e9, 35e9],
             floats=[0.8, 0.8, 0.10, 0.8],          # S02 member fails float
             atvr=[1.0, 1.0, 1.0, 0.05])            # S03 non-member illiquid
    r = predict_msci(u, members={"S00", "S01", "S02"})
    assert "S02" in set(r["deletes"]["ticker"])
    assert "fails float/liquidity" in r["deletes"].set_index("ticker").loc[
        "S02", "reason"]
    assert "S03" not in set(r["adds"].get("ticker", []))


def test_watchlist_flags_borderline():
    u = _uni([40e9, 30e9, 20e9, 10.5e9, 21e9])     # S03 member just above 0.5x
    r = predict_msci(u, members={"S00", "S01", "S02", "S03"})
    w = r["watchlist"]
    assert "S03" in set(w.get("ticker", []))
    assert (w.set_index("ticker").loc["S03", "side"] == "deletion risk")


# ── FTSE mechanics ─────────────────────────────────────────────────────────

def test_ftse_90_111_rule_scaled():
    # 12-name universe, index of 8, add<=7, delete>=10
    caps = list(np.linspace(50e9, 10e9, 12))
    u = _uni(caps)
    members = {f"S{i:02d}" for i in range(8)}
    # promote a non-member into rank 5, demote a member to rank 11
    u.loc[9, "full_mktcap_usd"] = 45e9              # S09 non-member rises
    u.loc[3, "full_mktcap_usd"] = 11e9              # S03 member sinks
    r = predict_ftse(u, members, FTSERules(index_size=8, add_rank=7,
                                           delete_rank=10))
    assert "S09" in set(r["adds"]["ticker"])
    assert "S03" in set(r["deletes"]["ticker"])
    n_after = len(members) + len(r["adds"]) - len(r["deletes"])
    assert n_after == 8                              # pairing holds size


def test_ftse_reserve_topup_holds_index_size():
    # one deletion, no automatic add -> best-ranked reserve tops up
    caps = list(np.linspace(50e9, 10e9, 12))
    u = _uni(caps)
    members = {f"S{i:02d}" for i in range(8)}
    u.loc[3, "full_mktcap_usd"] = 5e9               # S03 sinks to bottom
    r = predict_ftse(u, members, FTSERules(index_size=8, add_rank=2,
                                           delete_rank=10))
    assert "S03" in set(r["deletes"]["ticker"])
    assert any("reserve top-up" in x for x in r["adds"]["reason"])
    assert len(members) + len(r["adds"]) - len(r["deletes"]) == 8


# ── flow + demo ────────────────────────────────────────────────────────────

def test_expected_flow_math():
    u = _uni([40e9, 60e9], advs=[2e7, 2e7])         # FF caps 32B / 48B
    f = expected_flow(u, ["S00"], passive_aum_usd=80e9).iloc[0]
    # weight = 32/80 = 0.4 -> demand 32B; days = 32B/2e7
    assert f["est_passive_demand_usd"] == pytest.approx(0.4 * 80e9)
    assert f["days_of_adv"] == pytest.approx(0.4 * 80e9 / 2e7, rel=1e-3)


def test_demo_universe_planted_stories_recovered():
    u, m = demo_universe()
    r = predict_msci(u, m)
    assert "NEWBIG" in set(r["adds"]["ticker"])              # planted add
    dels = set(r["deletes"]["ticker"])
    assert {"STK055", "STK058"} <= dels                      # collapse + float
    reasons = r["deletes"].set_index("ticker")["reason"]
    assert "screens" in reasons["STK058"]
