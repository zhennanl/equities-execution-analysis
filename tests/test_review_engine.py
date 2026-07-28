"""Unified review-engine tests — canned data, all eight layers."""
import pandas as pd
import pytest

from agents import review_engine as re_


def _universe():
    return pd.DataFrame([
        # anchors
        dict(ticker="BIG1", full_mktcap_usd=600e9, free_float_frac=0.7,
             adv_usd=600e9 * 0.004, atvr=1.0, member=1),
        dict(ticker="BIG2", full_mktcap_usd=80e9, free_float_frac=0.7,
             adv_usd=80e9 * 0.004, atvr=1.0, member=1),
        # clear add candidate (>=2.5x GMSR under QIR)
        dict(ticker="ADDME", full_mktcap_usd=20e9, free_float_frac=0.6,
             adv_usd=20e9 * 0.004, atvr=1.0, member=0),
        # stale member: ledger says deleted -> any call must BLOCK
        dict(ticker="STALE", full_mktcap_usd=0.9e9, free_float_frac=0.7,
             adv_usd=0.9e9 * 0.004, atvr=1.0, member=1),
        # genuine small member -> DELETE candidate
        dict(ticker="TINY", full_mktcap_usd=1.0e9, free_float_frac=0.7,
             adv_usd=1.0e9 * 0.004, atvr=1.0, member=1),
    ])


ALIASES = {"STALE": "STALE CORP", "TINY": "TINY CORP",
           "ADDME": "ADDME CORP"}
LEDGER = [{"TESTLAND": {"adds": [], "deletes": ["STALE CORP"]}}]


def _run(short_cache=None, event_cache=None):
    return re_.run_full_review(
        "Testland", _universe(), ALIASES, LEDGER, "TESTLAND",
        short_cache=short_cache, event_cache=event_cache,
        names_risk=pd.DataFrame([
            {"ticker": "ADDME", "side": "Buy", "adv_days": 6.0,
             "band_pct": 10.0, "borrow_constrained": False}]))


def test_stale_member_call_is_blocked_not_hidden():
    r = _run()
    calls = r["calls"]
    stale = calls[calls["ticker"] == "STALE"]
    assert len(stale) == 1 and stale.iloc[0]["call"] == "BLOCKED"
    assert stale.iloc[0]["p_correct"] == 0.0
    assert "BLOCKED" in stale.iloc[0]["verified"]
    assert any(v["type"] == "STALE_MEMBER" for v in r["violations"])


def test_add_and_delete_calls_with_probability_and_flow():
    r = _run()
    calls = r["calls"]
    add = calls[calls["ticker"] == "ADDME"].iloc[0]
    # a violation exists in this fixture -> market is UNVERIFIED ->
    # even HIGH-margin adds take the 0.75 discount (0.85 -> 0.64)
    assert add["call"] == "ADD"
    assert add["p_correct"] == pytest.approx(0.85 * 0.75, abs=0.01)
    assert "-" in add["flow_usd_m"]            # a range, not a point
    assert add["bucket"] in ("MOC", "WORK+MOC", "MULTI-DAY")
    tiny = calls[calls["ticker"] == "TINY"].iloc[0]
    # violations exist -> deletes are UNVERIFIED-probability class
    assert tiny["call"] == "DELETE"
    assert tiny["p_correct"] == re_.PROB["DELETE_UNVERIFIED"]


def test_expected_hits_excludes_blocked():
    r = _run()
    live = r["calls"][r["calls"]["call"] != "BLOCKED"]
    assert r["expected_hits"] == pytest.approx(
        float(live["p_correct"].sum()), abs=0.01)


def test_history_says_no_data_honestly():
    cache = {"E1": {"available": True, "provider": "MSCI",
                    "side": "Sell", "t_day_volume_multiple": 16.0}}
    r = _run(event_cache=cache)
    assert r["history"]["MSCI Sell"]["available"]
    assert not r["history"]["MSCI Buy"]["available"]


def test_crowding_layer_reads_short_cache():
    dates = pd.bdate_range("2026-06-01", "2026-07-25")
    short = {"short": {d.strftime("%Y%m%d"):
                       {"ADDME": [0, 10000 * (1 + 0.02 * i)]}
                       for i, d in enumerate(dates)}}
    r = _run(short_cache=short)
    add = r["calls"][r["calls"]["ticker"] == "ADDME"].iloc[0]
    assert add["crowding"].startswith(("HIGH", "MED", "LOW"))


def test_render_contains_all_sections():
    r = _run(event_cache={})
    md = re_.render_review_markdown(
        [r], "TEST EVENT", "2026-07-28", ["Nowhere"], notes="n")
    for frag in ["Full-Engine", "Ledger violations", "BLOCKED",
                 "Expected correct calls", "NO-CALL markets",
                 "track record", "Notes"]:
        assert frag in md


def test_early_exit_signature_detected():
    """Build-then-shed: peak mid-window, 25% given back -> EXITING tag
    (crowding is a stock, not a flow — remaining inventory is what
    meets the auction)."""
    dates = pd.bdate_range("2026-06-15", "2026-07-25")
    n = len(dates)
    vals = []
    for i in range(n):
        if i < n // 2:
            vals.append(10000 * (1 + 0.08 * i))          # build
        else:
            vals.append(vals[n // 2 - 1] * (1 - 0.02 * (i - n // 2 + 1)))
    short = {"short": {d.strftime("%Y%m%d"): {"ADDME": [0, v]}
                       for d, v in zip(dates, vals)}}
    from tests.test_review_engine import _run
    r = _run(short_cache=short)
    add = r["calls"][r["calls"]["ticker"] == "ADDME"].iloc[0]
    assert "EXITING" in add["crowding"]
