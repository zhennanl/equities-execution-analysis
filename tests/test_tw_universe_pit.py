"""c-120 pins: the full-universe PIT harvest and the §2.3.3
cutoff calibration.

The load-bearing test is the IMPLIED-FIF IDENTITY: MSCI's ten
published float caps, divided by OUR full caps, must sum back
to the factsheet's own top-10 total. That check passes only if
price x shares / FX is right, so it validates the entire input
chain before any float judgement enters. If it ever breaks,
every number downstream is suspect.
"""
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
U = ROOT / "data" / "tw_universe_pit.json"
C = ROOT / "data" / "tw_cutoff_calibration.json"


@pytest.mark.skipif(not U.exists(), reason="no universe harvest")
def test_universe_scale_and_shape():
    u = json.loads(U.read_text(encoding="utf-8"))
    d = u["dates"]
    assert len(d) >= 3
    for k, v in d.items():
        if not v.get("rows"):
            continue
        # the whole point of c-120: ~2,000 companies, not 148
        assert v["n"] > 1800, (k, v["n"])
        assert v["n_with_float"] / v["n"] > 0.99
        r = v["rows"]["2330"]
        assert r["mkt"] == "twse"
        assert r["shares"] > 2.5e10          # TSMC NOS
        assert 1000 < r["cap_usd_b"] < 3000
        # both boards present
        mk = {x["mkt"] for x in v["rows"].values()}
        assert mk == {"twse", "tpex"}


@pytest.mark.skipif(not U.exists(), reason="no universe harvest")
def test_pit_inputs_are_dated_not_current():
    """Shares and foreign holdings come from the dated MI_QFIIS
    feed, so they are point-in-time — the thing the engine
    previously could not do."""
    u = json.loads(U.read_text(encoding="utf-8"))
    a = u["dates"]["20260420"]["rows"]
    b = u["dates"]["20260731"]["rows"]
    assert a["2330"]["close"] != b["2330"]["close"]
    # foreign holding is carried per date
    assert a["2330"]["foreign"] is not None
    # FX must differ across the two months
    assert (u["dates"]["20260420"]["fx"]
            != u["dates"]["20260731"]["fx"])


@pytest.mark.skipif(not C.exists(), reason="no calibration")
def test_implied_fif_identity_holds():
    c = json.loads(C.read_text(encoding="utf-8"))
    chk = c["implied_fif_check"]
    assert chk["matches"], chk
    assert abs(chk["sum_top10_float_usd_b"]
               - chk["factsheet_total"]) < 0.05
    # TSMC's implied FIF must reflect the ~6% government stake
    assert 0.92 <= c["implied_fifs"]["2330"] <= 0.99


@pytest.mark.skipif(not C.exists(), reason="no calibration")
def test_tdcc_proxy_is_biased_low_and_worst_in_financials():
    """Negative result kept: the TDCC bracket-15 proxy runs
    below MSCI's FIF, and by far the worst cases are the
    financials (2881 Fubon, 2891 CTBC) — bracket 15 lumps
    domestic institutions in with strategic holders."""
    c = json.loads(C.read_text(encoding="utf-8"))
    e = c["tdcc_proxy_error_vs_implied"]
    assert e["median"] < 0
    worst = dict(e["worst"])
    assert "2881" in worst and worst["2881"] < -0.3


@pytest.mark.skipif(not C.exists(), reason="no calibration")
def test_cutoff_calibration_brackets_the_truth():
    """No scenario is declared correct — the point is that the
    published answer (rank 77) sits INSIDE the range the float
    assumptions produce, so the remaining error is float, not
    method."""
    c = json.loads(C.read_text(encoding="utf-8"))
    ranks = [v["rank"] for v in c["scenarios"].values()]
    assert min(ranks) < c["targets"]["segment_number_of_companies"]
    assert max(ranks) > c["targets"]["segment_number_of_companies"]
    # the tail assumption dominates the rank
    assert (c["scenarios"]["E_tail_flat_0.85"]["rank"]
            > c["scenarios"]["C_tail_flat_0.55"]["rank"])
