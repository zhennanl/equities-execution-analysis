"""Guards for the pre-positioning read (c-326).

THE CLAIM THIS FILE PROTECTS. "Foreigners were net sellers of all
three" is NOT evidence on its own — July 2026 was violent in
Taiwan and a net seller in a drawdown is just a seller. The claim
only becomes evidence with the cross-sectional control: net
sellers of these three WHILE net buyers of the same 130 names
over the same sessions.

So the tests are mostly about the control, the peer set being
described accurately, and the conclusion staying labelled as
suggestive rather than settled.
"""
import json
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

SRC = ROOT / "data" / "tw_prepositioning.json"
DOC = ROOT / "docs" / "TW_PREPOSITIONING.md"

pytestmark = pytest.mark.skipif(
    not SRC.exists(), reason="run scripts/tw_prepositioning.py")


@pytest.fixture(scope="module")
def d():
    return json.loads(SRC.read_text(encoding="utf-8"))


def test_the_cross_sectional_control_exists(d):
    """Without a peer comparison over the SAME sessions, "foreign
    net seller" is a statement about July, not about these
    names."""
    for w in d["windows"].values():
        assert w["peer_set_n"] >= 100, w["peer_set_n"]
        p = w["peer_foreign_adv_days"]
        assert p["p25"] <= p["p50"] <= p["p75"]
        assert "peer_net_shares_m" in w
        for r in w["names"].values():
            assert 0 <= r["foreign_percentile"] <= 1


def test_the_peer_set_is_described_as_what_it_is(d):
    """The T86 harvest is ~130 large TWSE names, not the market.
    A percentile quoted against "all Taiwanese stocks" would be
    a different and wrong claim."""
    assert "130" in d["peer_set"]
    # the description must DISCLAIM the wider reading, not just
    # state the size — "130 names" alone still invites "of the
    # market"
    assert "wrong one" in d["peer_set"].lower()
    assert "whole market" in d["peer_set"].lower()
    for w in d["windows"].values():
        assert w["peer_set_n"] <= 200


def test_the_finding_is_the_gap_not_the_sign(d):
    """The headline is that the candidates sit BELOW their peers
    while the peers were bought. If the peer set ever turns
    negative too, the claim weakens and the file must say so
    rather than keep the verdict."""
    w = d["windows"]["20"]
    assert len(w["names"]) == 3
    for r in w["names"].values():
        assert r["foreign_percentile"] < 0.5, r["name"]
    if w["peer_net_shares_m"] > 0:
        assert "NET BUYERS" in d["verdict"]["peer_direction"]
    else:
        assert "weaker" in d["verdict"]["peer_direction"]


def test_the_verdict_stays_labelled_suggestive(d):
    """Flow is not position, and a NET is not a participant. If
    this ever hardens to a conclusion the reasons have to have
    been answered, not dropped."""
    v = d["verdict"]
    assert v["strength"] == "SUGGESTIVE, NOT CONCLUSIVE"
    joined = " ".join(v["why_not_conclusive"]).lower()
    for reason in ("net", "mandate", "holdings"):
        assert reason in joined, reason
    assert len(v["why_not_conclusive"]) >= 4


def test_phison_is_declared_unmeasurable_not_omitted(d):
    """8299 is TPEx-listed and absent from T86, which is
    TWSE-only. A name that silently vanishes from a positioning
    read looks like a name with no positioning."""
    nm = json.dumps(d["not_measurable"])
    assert "8299" in nm
    assert "TPEx" in nm


def test_the_unobserved_window_is_stated(d):
    """The flow file ends before the announcement. If the
    anticipation arrives late it lands exactly in the gap."""
    assert d["flow_data_to"] < d["announcement"]
    assert d["sessions_unobserved_before_announcement"] >= 1


def test_the_historical_benchmark_is_the_same_window(d):
    """A typical addition's pre-announcement foreign buying is the
    comparison. It must be the PRE window — comparing against the
    announcement-to-effective leg would be a different claim."""
    b = d["historical_benchmark"]
    assert b["foreign_pre_announcement_adv_days"]["n"] >= 30
    assert b["foreign_pre_announcement_adv_days"]["p50"] > 0
    assert b["share_accumulated_before_announcement"]["p50"] > 0


def test_the_doc_quotes_the_json(d):
    t = DOC.read_text(encoding="utf-8")
    w = d["windows"]["20"]
    for r in w["names"].values():
        assert f"{r['foreign_adv_days']:+.2f}" in t
    assert d["flow_data_to"] in t
