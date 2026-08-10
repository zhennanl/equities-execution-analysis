"""Guards for the tracker playbook (c-321).

WHAT IT ADDS AND WHY IT NEEDED A TEST. The headline number —
"your order is N times this name's normal closing auction" — is a
CHAIN of three estimates: a demand model built on an assumed
tracking AUM, an ADV, and a closing-bar share that is one median
applied to every name. Each link is defensible on its own and the
product is easy to quote as if it were measured. So the tests
pin the chain, not the number.
"""
import json
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

SRC = ROOT / "data" / "tw_tracker_playbook.json"
DOC = ROOT / "docs" / "TW_TRACKER_PLAYBOOK.md"

pytestmark = pytest.mark.skipif(
    not SRC.exists(),
    reason="run scripts/tw_tracker_playbook.py first")


@pytest.fixture(scope="module")
def d():
    return json.loads(SRC.read_text(encoding="utf-8"))


def test_the_capacity_multiple_reconstructs_from_its_inputs(d):
    """The headline is demand / (close share x ADV). If the
    arithmetic ever stops tying, the number is a leftover."""
    share = d["capacity_model"]["ordinary_close_share"]
    for code, r in d["names"].items():
        want = r["demand_shares"] / (share * r["adv_shares"])
        assert r["order_in_normal_closes"] == pytest.approx(want)
        # and the effective-day version must be SMALLER, because
        # the close it is measured against is bigger
        assert r["order_in_effective_day_closes"] < \
            r["order_in_normal_closes"], code


def test_the_close_shares_are_the_measured_ones(d):
    """Both come from the IB panel, not from a constant typed
    here. The ordinary share is around a tenth of the day and the
    effective-day share is most of it — if those ever converge,
    the panel is measuring the wrong bar."""
    C = d["capacity_model"]
    assert 0.05 < C["ordinary_close_share"] < 0.15
    assert 0.6 < C["effective_day_close_share"] < 0.95
    assert C["effective_day_close_share"] > \
        5 * C["ordinary_close_share"]
    assert "n=" in C["source"]


def test_days_of_adv_and_closes_disagree_about_the_ranking(d):
    """The whole point of the section. If the two units ranked the
    names identically the new number would be decoration."""
    by_days = [c for c, _ in sorted(
        d["names"].items(), key=lambda kv: -kv[1]["demand_adv_days"])]
    by_closes = [c for c, _ in sorted(
        d["names"].items(),
        key=lambda kv: -kv[1]["order_in_normal_closes"])]
    # they may agree on the leader; they must not be identical in
    # magnitude — the spread is what the section is about
    mult = [r["order_in_normal_closes"] for r in d["names"].values()]
    days = [r["demand_adv_days"] for r in d["names"].values()]
    assert max(mult) / min(mult) > 1.5
    assert max(days) / min(days) > 1.5
    assert by_days and by_closes


def test_nothing_here_forecasts_a_price(d):
    """The addition study found nothing that predicts direction
    out of sample. A capacity page that quietly grew a slippage
    estimate would be claiming what that test denied."""
    # the PER-NAME records, not the whole file — the disclaimer
    # itself contains the word "slippage", and a test that cannot
    # tell a denial from a claim is worse than no test
    blob = json.dumps(d["names"]).lower()
    for word in ("slippage", "expected_return", "price_target",
                 "expected_price", "forecast_return"):
        assert word not in blob, word
    # every per-name field must be a quantity or a percentile,
    # never a modelled price outcome
    allowed_price_fields = {"pre_ann_excess_25d",
                            "pre_ann_percentile"}
    for code, r in d["names"].items():
        for k in r:
            if any(w in k for w in ("return", "excess", "price")):
                assert k in allowed_price_fields, (code, k)


def test_the_three_phases_each_carry_a_reference_and_threshold(d):
    """A metric with no historical level beside it is a number a
    reader cannot act on."""
    W = d["watchlist"]
    assert len(W) == 3
    for w in W:
        for k in ("phase", "question", "metric", "reference",
                  "threshold", "reading", "why_it_matters"):
            assert w.get(k), (w.get("phase"), k)
    assert "before the announcement" in W[0]["phase"].lower()
    assert "effective date" in W[2]["phase"].lower()


def test_the_limits_of_the_capacity_model_are_stated(d):
    lims = " ".join(d["capacity_model"]["limits"]).lower()
    assert "median" in lims
    assert "market-wide" in lims
    assert "not a slippage forecast" in lims
    assert d["conditional_on"].startswith("MSCI adding")


def test_the_doc_quotes_the_json(d):
    """c-325: the CARRIED names only. Phison is in the file — its
    capacity is still computed and still recorded — but it is not
    in the ladder, because the ladder is a sizing tool and its
    addition verdict flips inside the ±5% band on the cutoff."""
    t = DOC.read_text(encoding="utf-8")
    shown = [r for r in d["names"].values()
             if r.get("capacity_rank")]
    assert len(shown) == 3, len(shown)
    for r in shown:
        assert f"{r['order_in_normal_closes']:.1f}×" in t
    # and the excluded name is still measured, not dropped
    held = [r for r in d["names"].values()
            if not r.get("capacity_rank")]
    assert held and all(r["order_in_normal_closes"] for r in held)


def test_the_ladder_ranks_without_a_hole(d):
    """Bill: *"the rank is off, it only has 2, 3, 4."* The rank
    used to be assigned across every called name and the page then
    filtered one out, so the chart read 2-3-4. A rank with a gap
    in it reads as a missing row rather than as a deliberate
    exclusion — so it is assigned AFTER the filter."""
    ranks = sorted(r["capacity_rank"] for r in d["names"].values()
                   if r.get("capacity_rank"))
    assert ranks == list(range(1, len(ranks) + 1)), ranks
