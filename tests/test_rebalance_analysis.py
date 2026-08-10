"""c-270: the strategist question bank, answered on Taiwan.

The bank's own standards of proof are the test surface here.
Each of the four below has already produced a wrong answer in
this repo, so each is asserted on the OUTPUT rather than left
to the reader of the script.
"""
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
OUT = ROOT / "data" / "rebalance_analysis.json"


@pytest.fixture(scope="module")
def R():
    if not OUT.exists():
        pytest.skip("run scripts/rebalance_analysis.py first")
    return json.loads(OUT.read_text(encoding="utf-8"))


def test_estimated_day0_windows_are_excluded(R):
    """The single most important exclusion in the study.

    44 Taiwan windows carry an announcement date estimated as
    effective minus a fixed number of business days, and the
    measured gap is 12-17 days with a mode of 13 — so day 0 on
    those windows is several sessions wrong. Day 0 is the
    pre-news baseline every event-time number is measured from,
    which makes those windows unable to measure an announcement
    effect at all. Excluding them is what makes the sample 136
    rather than 176, and a future edit that quietly pools them
    would inflate every n on the page.
    """
    M = R["M"]["M1_panel"]
    assert M["analysable"] == M["registry_day0"]
    assert M["registry_day0"] < M["priced_and_usable"]
    n = M["by_action"]["ADD"] + M["by_action"]["DEL"]
    assert n == M["registry_day0"]
    # and every distribution must be built on that sample
    assert R["C1_drift"]["ADD"]["n"] == M["by_action"]["ADD"]
    assert R["C1_drift"]["DEL"]["n"] == M["by_action"]["DEL"]


def test_every_distribution_carries_n_and_dispersion(R):
    """§0.3.1. A median with no n is an anecdote, and this desk
    has published one before."""
    def check(d, path):
        if not isinstance(d, dict):
            return
        if "p50" in d:
            for k in ("n", "p10", "p25", "p75", "p90",
                      "exploratory"):
                assert k in d, f"{path} missing {k}"
            assert isinstance(d["exploratory"], bool)
        for k, v in d.items():
            check(v, f"{path}.{k}")
    for key in ("C1_drift", "B1_print_size", "D1_eff_day",
                "G1_reversion", "J4_mae", "C4_capture"):
        check(R[key], key)


def test_hit_rate_accompanies_every_directional_median(R):
    """A pod cannot size on a median that is right 60% of the
    time without being told it is 60%."""
    for key in ("C1_drift", "D1_eff_day"):
        for side in ("ADD", "DEL"):
            d = R[key][side]
            assert "hit_rate" in d and "wrong_sign" in d, key
            assert abs(d["hit_rate"] + d["wrong_sign"] - 1) < 1e-6


def test_only_disjoint_windows_are_correlated(R):
    """§0.3.2, the trap that manufactured rho 0.35-0.44 across
    every market on an earlier cut.

    `gap1` runs ann -> ann+1 and `drift` runs ann+1 -> eff-1;
    `drift` ends at eff-1 and `revert20` starts at eff. Neither
    pair shares a day. These are the only two correlations of
    return against return in the payload, and the note saying
    why has to survive with them.
    """
    assert "C5_gap_predicts_drift" in R
    assert "disjoint" in R["C5_note"] or "§0.3.2" in R["C5_note"]
    assert "G2_drift_to_revert" in R
    for side in ("ADD", "DEL"):
        assert R["C5_gap_predicts_drift"][side]["n"] > 0


def test_capture_cannot_explode_on_a_tiny_denominator(R):
    """capture = drift / (gap1 + drift) is undefined when the
    total move is nothing. A 1e-6 guard let three events reach
    |1000| and dragged the deletion mean to 14.6."""
    for side in ("ADD", "DEL"):
        d = R["C4_capture"][side]
        assert abs(d["max"]) < 20, side
        assert abs(d["mean"]) < 5, side


def test_the_live_call_is_placed_not_invented(R):
    """Part 3 must read the registered call rather than restate
    it, and must express expectations as percentiles of the
    historical population rather than as point forecasts."""
    L = R["LIVE_AUG26"]
    assert L["n_calls"] > 0
    codes = {r["code"] for r in L["names"]}
    call = json.loads((ROOT / "data" / "aug26_tw_call_v2.json")
                      .read_text(encoding="utf-8"))
    assert codes == {str(c["code"]) for c in call["calls"]}
    for r in L["names"]:
        assert r["action"] in ("ADD", "DEL")
        for k in ("p25", "p50", "p75"):
            assert k in r["expected_print_x_adv"]
        assert "hit_rate" in r["expected_drift"]


def test_the_page_holds_no_numbers_of_its_own(R):
    """Same contract as the walkthrough: a page that carries
    its own figures disagrees with the engine the first time
    the panel moves."""
    src = (ROOT / "views" / "rebalance_insights.py").read_text(
        encoding="utf-8")
    import re
    body = re.sub(r'""".*?"""', "", src, flags=re.S)
    body = re.sub(r"#.*", "", body)
    # a percentage or a multiple typed into the view would be a
    # fact living outside data/rebalance_analysis.json
    assert not re.search(r"\d+\.\d+%", body)
    assert not re.search(r"=\s*\d+\.\d+[x×]", body)
    assert "rebalance_analysis.json" in src


def test_findings_doc_is_generated_from_the_same_file(R):
    doc = ROOT / "docs" / "REBALANCE_FINDINGS.md"
    if not doc.exists():
        pytest.skip("findings not generated")
    t = doc.read_text(encoding="utf-8")
    assert "rebalance_analysis.json" in t
    M = R["M"]["M1_panel"]
    assert str(M["registry_day0"]) in t
