"""Index-event flow simulation + optimal strategy (agents/index_flow.py)."""
import numpy as np
import pandas as pd
import pytest

from agents.index_flow import (simulate_index_flow, recommend_execution,
                               BUCKET_MOC, BUCKET_WORK)


def _u(rows):
    return pd.DataFrame([dict(ticker=t, full_mktcap_usd=c*1e9,
                              free_float_frac=f, adv_usd=a*1e6)
                         for t, c, f, a in rows])


@pytest.fixture
def uni():
    return _u([("A", 100, 0.8, 400), ("B", 50, 0.8, 200),
               ("C", 20, 0.8, 100), ("D", 10, 0.8, 50),
               ("NEW", 15, 0.8, 60), ("OUT", 8, 0.8, 40)])


def test_self_financing_identity(uni):
    r = simulate_index_flow(uni, {"A", "B", "C", "D", "OUT"},
                            adds={"NEW"}, deletes={"OUT"},
                            passive_aum_usd=10e9)
    c = r["checks"]
    assert c["self_financing_gap_pct"] < 0.01        # buys == sells
    assert c["n_add"] == 1 and c["n_delete"] == 1 and c["n_reweight"] == 4


def test_delete_sells_full_before_weight_add_buys_full_after(uni):
    aum = 10e9
    r = simulate_index_flow(uni, {"A", "B", "C", "D", "OUT"},
                            adds={"NEW"}, deletes={"OUT"}, passive_aum_usd=aum)
    f = r["flows"].set_index("ticker")
    assert f.loc["OUT", "flow_usd"] == pytest.approx(
        -f.loc["OUT", "w_before_pct"] / 100 * aum, rel=1e-3)
    assert f.loc["NEW", "flow_usd"] == pytest.approx(
        f.loc["NEW", "w_after_pct"] / 100 * aum, rel=1e-3)


def test_pure_addition_dilutes_every_continuing_member(uni):
    r = simulate_index_flow(uni, {"A", "B", "C", "D"}, adds={"NEW"},
                            deletes=set(), passive_aum_usd=10e9)
    f = r["flows"]
    rw = f[f.kind == "reweight"]
    assert (rw["flow_usd"] < 0).all()                # everyone trimmed
    assert (f[f.kind == "ADD"]["flow_usd"] > 0).all()


def test_pure_deletion_tops_up_every_continuing_member(uni):
    r = simulate_index_flow(uni, {"A", "B", "C", "D", "OUT"}, adds=set(),
                            deletes={"OUT"}, passive_aum_usd=10e9)
    rw = r["flows"][r["flows"].kind == "reweight"]
    assert (rw["flow_usd"] > 0).all()                # everyone topped up


def test_bucketing_thresholds(uni):
    r = simulate_index_flow(uni, {"A", "B", "C", "D", "OUT"},
                            adds={"NEW"}, deletes={"OUT"},
                            passive_aum_usd=10e9)
    f = r["flows"].set_index("ticker")
    for t, row in f.iterrows():
        if row["adv_days"] < BUCKET_MOC:
            assert row["bucket"] == "MOC"
        elif row["adv_days"] < BUCKET_WORK:
            assert row["bucket"] == "WORK+MOC"
        else:
            assert row["bucket"] == "MULTI-DAY"


def test_recommendations_and_buy_sell_asymmetry(uni):
    r = simulate_index_flow(uni, {"A", "B", "C", "D", "OUT"},
                            adds={"NEW"}, deletes={"OUT"},
                            passive_aum_usd=50e9)   # big AUM -> multi-day
    rec = recommend_execution(r["flows"], tracking_tolerance_bps=60.0)
    rr = rec["recommendations"].set_index("ticker")
    # MOC bucket names take the S1 print
    moc = r["flows"][r["flows"].bucket == "MOC"]["ticker"]
    for t in moc:
        assert rr.loc[t, "strategy"] == "S1 100% MOC"
    # On the pressure path, the SELL (delete) rides the pressure -> S1
    # optimal; the BUY (add) avoids paying the peak -> a working strategy.
    assert rr.loc["OUT", "strategy"].startswith("S1")
    assert not rr.loc["NEW", "strategy"].startswith("S1")
    assert "frontier pick" in rr.loc["NEW", "why"]
