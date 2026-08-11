"""Guards for the two c-375 AUM cross-checks.

WHAT EACH ONE IS FOR. The volume inversion (Chinco-Sammon logic)
sees indexed money no register discloses; the fund-by-fund
replication prices the capping the identity deliberately leaves
out. Neither replaces the disclosed-anchor basis (USD 125bn at
c-400; previously the USD 60bn floor) — each tests it from a
direction the basis cannot test itself, so the guards are about
RECONCILIATION and honesty, not about any one value.
"""
import json
import pathlib
import statistics as stats
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
VR = ROOT / "data" / "tw_volume_revealed_aum.json"
TR = ROOT / "data" / "tw_tracker_replication.json"

pytestmark = pytest.mark.skipif(
    not (VR.exists() and TR.exists()),
    reason="run the c-375 cross-check scripts")


@pytest.fixture(scope="module")
def vr():
    return json.loads(VR.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def tr():
    return json.loads(TR.read_text(encoding="utf-8"))


def test_the_revealed_median_reconciles_to_its_events(vr):
    """The headline must be recomputable from the per-event
    rows, and every event's own inversion must re-derive."""
    vals = [r["revealed_aum_usd_b"] for r in vr["events"]]
    assert vals
    assert abs(stats.median(vals)
               - vr["revealed_aum_usd_b"]["median"]) < 0.1
    for r in vr["events"]:
        want = (r["excess_close_usd_m"] / 1000
                / (r["delta_w_pct"] / 100))
        assert abs(want - r["revealed_aum_usd_b"]) < 0.5, r["key"]


def test_the_coverage_is_declared_not_papered_over(vr):
    """A 9-event pilot must SAY it is a 9-event pilot: used plus
    skipped ties to the recent-event universe, and every skip
    carries a reason."""
    c = vr["coverage"]
    assert c["events_used"] == len(vr["events"])
    assert c["events_skipped"] == len(c["skipped"])
    assert all(s.get("why") for s in c["skipped"])
    assert c["events_used"] >= 5, "pilot thinner than built"


def test_the_approximations_stay_confessed(vr):
    """The float cap is TODAY'S, not the event's — remove that
    confession and the number reads as measurement."""
    a = " ".join(vr["method"]["approximations"])
    assert "MOPS as-of" in a
    assert "errs low" in a or "EXCLUDES" in a


def test_the_replication_reconciles_fund_by_fund(tr):
    """Per candidate, the total must equal the sum over funds,
    and each capped fund's amplifier must be the capping formula
    on the on-disk TSMC weight."""
    w_tsmc = tr["assumptions"]["tsmc_uncapped_weight"]
    for cand in tr["candidates"]:
        got = sum(f["buys_usd_m"][cand["code"]]
                  for f in tr["funds"])
        assert abs(got - cand["replicated_etf_usd_m"]) < 1.0
    for f in tr["funds"]:
        cap = tr["assumptions"]["rule_caps"].get(f["index"])
        if cap:
            want = (1 - cap) / (1 - w_tsmc)
            assert abs(f["weight_amplifier"] - want) < 5e-3
        else:
            assert f["weight_amplifier"] == 1.0 or \
                f["index"] not in tr["assumptions"]["rule_caps"]


def test_the_identity_errs_low_and_the_page_says_so(tr):
    """THE FINDING: capping pushes every candidate's fund-by-
    fund total ABOVE the identity — the conservative direction.
    c-388, Bill took the fund-by-fund expander OFF the page, so
    the guard is data-level now: the ratios, and the fact the
    page keeps only the volume cross-check."""
    for r in tr["candidates"]:
        assert r["ratio"] > 1.0, r
    src = (ROOT / "views" / "tw_case_study.py").read_text(
        encoding="utf-8")
    # c-393: no cross-check expander survives on the page
    assert "Cross-check" not in src
    assert "rebuilt fund by" not in src


def test_the_cross_checks_stay_off_the_page():
    from conftest import real_streamlit
    real_streamlit()
    from streamlit.testing.v1 import AppTest
    h = ROOT / "tests" / "_tw_cc_harness.py"
    h.write_text(
        f"import sys; sys.path.insert(0, {str(ROOT)!r})\n"
        "from views import tw_case_study\ntw_case_study.render()\n",
        encoding="utf-8")
    try:
        at = AppTest.from_file(str(h), default_timeout=300).run()
        assert not at.exception, [e.value for e in at.exception]
        labs = [e.label for e in at.expander]
        md = " ".join(str(m.value) for m in at.markdown)
    finally:
        h.unlink(missing_ok=True)
    # c-388 took the fund-by-fund expander off the page;
    # c-393, Bill: the volume-revealed one too. Both survive
    # as data-level evidence (the JSON tests above) and in the
    # Q&A bank — the PAGE carries the registered floor only,
    # and neither expander may creep back.
    assert not any("revealed by the close" in x for x in labs), \
        labs
    assert not any("fund by fund" in x for x in labs), labs
    assert "excess close" not in md


def test_the_effective_floor_folds_capping_and_nothing_else(tr):
    """c-377, Bill: the replication feeds the floor — but only
    its capping arithmetic, and only over the ETF slice. The
    refined number must re-derive as ETF pool x the fund-by-fund
    ratio plus the UNAMPLIFIED mandate slice, and must sit above
    the registered basis (capping can only add for a non-TSMC
    name) without ever replacing it in the JSON."""
    ef = tr["effective_floor_usd_bn"]
    etf = tr["identity_etf_pool_usd_bn"]
    basis = tr["identity_full_basis_usd_bn"]
    ratio = tr["candidates"][0]["ratio"]
    want = etf * ratio + (basis - etf)
    assert abs(ef["value"] - want) < 0.1
    assert ef["value"] > basis
    assert "floor" in ef["note"]
    # c-388: the page text is gone; the fold survives as
    # data-level evidence in the JSON only
