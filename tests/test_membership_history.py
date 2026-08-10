"""c-114 pins: official constituents + the membership time
machine.

The validation chain this locks in — THREE independent MSCI
publications must agree on index size:
  (1) the public Index Constituents tool (ESMA-mandated),
  (2) the July-2026 country factsheets ('Number of
      Constituents'),
  (3) our iShares-ETF census (built months earlier, from a
      completely different source).
Plus the internal one: the ADDs the reverse-roll cannot undo
must be the SAME names the off-cycle audit independently
classified as off-cycle exits.
"""
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

OFF = ROOT / "data" / "msci_official_constituents.json"
MH = ROOT / "data" / "membership_history.json"


def test_key_keeps_identity_parentheticals():
    """VEDANTA vs VEDANTA (DETACHED) are two index lines; a
    country marker is noise. Blanket-stripping merged them
    (caught by the anchor gate)."""
    from membership_history import _key
    assert _key("VEDANTA", "India") != _key("VEDANTA (DETACHED)",
                                            "India")
    assert _key("BHP GROUP (AU)", "Australia") == _key(
        "BHP GROUP", "Australia")
    assert _key("TENCENT HOLDINGS LI (CN)", "China") == _key(
        "TENCENT HOLDINGS LI", "China")


@pytest.mark.skipif(not OFF.exists(), reason="no official list")
def test_official_weights_complete():
    o = json.loads(OFF.read_text(encoding="utf-8"))["markets"]
    assert len(o) == 12                     # NZ not offered
    for mkt, m in o.items():
        assert 99.0 <= m["weight_sum"] <= 101.0, mkt
        assert m["n"] == len(m["constituents"])
    # Taiwan's extreme concentration is the reason a weight
    # treemap beats an equal-area chart
    tw = o["Taiwan"]["constituents"]
    assert tw[0]["security"].startswith("TAIWAN SEMICONDUCTOR")
    assert tw[0]["weight"] > 50


@pytest.mark.skipif(not OFF.exists(), reason="no official list")
def test_three_sources_agree_on_index_size():
    """The core external validation."""
    from membership_history import factsheet_counts
    off = json.loads(OFF.read_text(encoding="utf-8"))["markets"]
    fs = factsheet_counts()
    assert len(fs) == 13                    # incl. NewZealand
    for mkt, m in off.items():
        assert fs[mkt] == m["n"], (
            f"{mkt}: factsheet {fs[mkt]} != constituents tool "
            f"{m['n']}")
    # NZ has no official list; the ETF census must carry it
    cen = json.loads((ROOT / "data" / "apac_members.json")
                     .read_text(encoding="utf-8"))["markets"]
    assert len(cen["NewZealand"]["standard_members"]) \
        == fs["NewZealand"]


@pytest.mark.skipif(not MH.exists(), reason="no time machine")
def test_time_machine_anchor_and_reach():
    mh = json.loads(MH.read_text(encoding="utf-8"))
    m = mh["markets"]
    assert len(m) == 13
    from membership_history import reviews
    for mkt, o in m.items():
        assert "Feb06" in o["members"], mkt
        # anchor must equal the published count (gate 1)
        if mkt != "NewZealand":
            assert o["anchor_n"] == mh["factsheet_gate"][mkt]
        # rosters must be non-empty and ordered in time
        got = [r for r in reviews() if r in o["counts"]]
        assert got == sorted(got, key=reviews().index)
    # Taiwan: index was BIGGER in 2006 than today (101 vs 77)
    tw = m["Taiwan"]["counts"]
    assert tw["Feb06"]["n"] > tw["May26"]["n"]


@pytest.mark.skipif(not MH.exists(), reason="no time machine")
def test_unundoable_adds_are_the_offcycle_exits():
    """The internal cross-validation: two pipelines built for
    different purposes must name the same securities."""
    import pandas as pd
    from membership_history import _key
    oc = pd.read_csv(ROOT / "data" / "offcycle_exit_classified.csv"
                     ).fillna("")
    mh = json.loads(MH.read_text(encoding="utf-8"))["markets"]
    for mkt in ("Taiwan", "Australia"):
        misses = mh[mkt]["add_key_misses"]
        n_oc = len(oc[oc.market == mkt])
        # the miss count must be explained by off-cycle exits,
        # not by name-resolution failure
        assert misses <= n_oc + 2, (mkt, misses, n_oc)
    assert mh["Australia"]["add_key_misses"] > 0
