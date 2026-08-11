"""Guards for the institutional-framing view (c-354).

WHAT THIS FILE PROTECTS. Not a new measurement — every number in
tw_forced_flow.json is assembled from files that already have
their own tests. What it protects is the FRAMING, and three
things in it are easy to lose in a later edit:

  1. The conditional and the expected figures must stay
     SEPARATE. Collapsing them is the tempting simplification
     and it makes the answer wrong for one of the two audiences:
     a desk executing on the effective day does not discount the
     order by P(add), and a book positioning beforehand must.

  2. The fourth pool must stay marked as NOT counted.
     Benchmark-aware active managers buy too. The moment that
     row is quietly flipped to counted, the AUM stops being a
     floor and becomes a claim.

  3. The out-of-sample gap must stay stated. The historical test
     never conditioned on flow-over-liquidity, and writing that
     down is what turns a null result into a roadmap.
"""
import json
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
SRC = ROOT / "data" / "tw_forced_flow.json"
DOC = ROOT / "docs" / "INSTITUTIONAL_FRAMEWORK.md"

pytestmark = pytest.mark.skipif(
    not SRC.exists(), reason="run scripts/tw_forced_flow.py")


@pytest.fixture(scope="module")
def d():
    return json.loads(SRC.read_text(encoding="utf-8"))


def test_the_flow_reconciles_to_its_three_inputs(d):
    """P(add) x weight x AUM, re-derived here from the source
    files with no reference to the script that wrote it."""
    scn = json.loads((ROOT / "data" / "aug26_scenarios.json")
                     .read_text(encoding="utf-8"))
    pb = json.loads((ROOT / "data" / "tw_tracker_playbook.json")
                    .read_text(encoding="utf-8"))
    aum = d["inputs"]["tracking_aum_usd_b"]
    for r in d["names"]:
        w = pb["names"][r["code"]]["index_weight_pct"]
        assert abs(w - r["delta_weight_pct"]) < 1e-9
        assert abs(w / 100 * aum * 1000
                   - r["forced_flow_usd_m"]) < 0.15
        p = scn["names"][r["code"]]["prob_of_addition"]
        assert abs(p - r["p_add"]) < 1e-9
        assert abs(p * r["forced_flow_usd_m"]
                   - r["expected_flow_usd_m"]) < 0.15


def test_the_aum_is_the_sourced_estimate_not_the_old_constant(d):
    """The whole point of c-349 — and c-400 moved the basis to
    MSCI's disclosed non-ETF pool (USD ~125bn all-in). The guard
    is not the LEVEL, it is the SOURCE: the input must equal the
    mandate JSON's estimate exactly, and must never be the
    unsourced 180 the framework once carried."""
    md = ROOT / "data" / "tw_mandate_size.json"
    if not md.exists():
        pytest.skip("run scripts/tw_mandate_size.py")
    tw = json.loads(md.read_text(encoding="utf-8"))["taiwan"]
    assert d["inputs"]["tracking_aum_usd_b"] == \
        tw["estimate_always_buys_usd_b"]
    assert d["inputs"]["tracking_aum_usd_b"] != 180.0
    # and the floor variant sits below it, so the downside case
    # is still available to quote
    assert tw["floor_variant_usd_b"] < \
        d["inputs"]["tracking_aum_usd_b"]


def test_conditional_and_expected_are_both_reported(d):
    """THE DISTINCTION THAT MUST NOT COLLAPSE.

    The conditional ratio is the execution question — on the
    effective day the order is there in full or not at all. The
    expected ratio is the positioning question and has to carry
    the probability. Reporting only one would be wrong for
    whichever reader it was not written for."""
    for r in d["names"]:
        assert r["expected_alpha_ratio_day"] < r["alpha_ratio_day"]
        assert abs(r["p_add"] * r["alpha_ratio_day"]
                   - r["expected_alpha_ratio_day"]) < 5e-4
        # and P(add) must actually be a probability, not a flag
        assert 0 < r["p_add"] < 1


def test_the_close_is_the_denominator_that_matters(d):
    """A DAY'S ADV IS THE WRONG DENOMINATOR and this is the one
    place the site improves on the framework as written.

    The forced flow does not arrive across the session. On an
    effective day the overwhelming majority of volume prints in
    the closing auction, and an ordinary close in these names
    takes under a fifth of the day — so measuring the order
    against a full session flatters it by roughly an order of
    magnitude."""
    i = d["inputs"]
    assert i["effective_day_close_share"] > 0.5
    assert i["ordinary_close_share"] < 0.2
    for r in d["names"]:
        assert r["alpha_ratio_close"] > r["alpha_ratio_day"]
        assert abs(r["alpha_ratio_close"] * i["ordinary_close_share"]
                   - r["alpha_ratio_day"]) < 5e-3


def test_the_uncounted_pool_stays_uncounted(d):
    """Benchmark-aware active money buys too, and this project
    cannot see it. The row exists so the AUM keeps being read as
    a floor rather than an estimate."""
    pools = {p["pool"]: p["counted"]
             for p in d["pools_of_forced_demand"]}
    assert len(pools) == 4
    assert sum(pools.values()) == 3
    active = [p for p in d["pools_of_forced_demand"]
              if not p["counted"]][0]
    assert "active" in active["pool"]
    assert "active bet" in active["where"]


def test_the_out_of_sample_gap_is_named(d):
    """The most useful sentence in the file: the historical test
    tested six features and none of them was the ratio. That is
    what makes the null result a roadmap instead of a dead
    end."""
    feats = d["out_of_sample_features_tested"]
    assert len(feats) >= 4
    for f in feats:
        assert "flow" not in f and "liquidit" not in f
    assert "point-in-time" in d["gap"]


def test_the_doc_is_generated_from_the_json():
    """Same rule as every other write-up here."""
    if not DOC.exists():
        pytest.skip("run scripts/tw_forced_flow.py")
    d = json.loads(SRC.read_text(encoding="utf-8"))
    doc = DOC.read_text(encoding="utf-8")
    assert f"USD {d['inputs']['tracking_aum_usd_b']:.0f}bn" in doc
    for r in d["names"]:
        assert r["code"] in doc
        assert f"{r['delta_weight_pct']:.3f}%" in doc
    assert "Expected Flow" in doc and "Available Liquidity" in doc
