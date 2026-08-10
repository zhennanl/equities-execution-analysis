"""c-116 pins: the historical backtest and its diagnostics.

What matters here is that the report cannot flatter the engine.
The tests assert the headline numbers against the engine's own
reconstructions, and assert that the two findings which make
the engine look BAD (the mis-specified addition bar, the
untestable float hypothesis) are actually present in the
output.
"""
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
BT = ROOT / "data" / "backtest_taiwan.json"
RD = ROOT / "data" / "reconstruct"


@pytest.mark.skipif(not BT.exists(), reason="no backtest")
def test_headline_ties_to_reconstructions():
    a = json.loads(BT.read_text(encoding="utf-8"))
    h = m = f = 0
    for rev in [p["review"] for p in a["per_review"]]:
        g = json.loads((RD / f"TW_{rev}.json").read_text(encoding="utf-8"))[
            "grading"]
        h += len(g["hits"])
        m += len(g["misses"])
        f += len(g["false_alarms"])
    assert a["deletions"]["hits"] == h
    assert a["deletions"]["misses"] == m
    assert a["deletions"]["false_alarms"] == f
    assert a["deletions"]["recall"] == round(h / (h + m), 3)


@pytest.mark.skipif(not BT.exists(), reason="no backtest")
def test_addition_bar_defect_is_measured_not_asserted():
    """The engine's 1.5x bar must be shown wrong BY the sweep —
    recall AND precision both improving as the bar falls is the
    signature of a mis-specified rule."""
    a = json.loads(BT.read_text(encoding="utf-8"))
    sweep = {s["x_ceiling"]: s for s in a["add_sweep"]}
    hi, lo = sweep[1.5], sweep[0.8]
    assert lo["recall"] > hi["recall"] * 10
    assert lo["precision_partial"] > hi["precision_partial"]
    assert a["additions"]["recall"] < 0.10


@pytest.mark.skipif(not BT.exists(), reason="no backtest")
def test_error_taxonomy_separates_the_two_failure_modes():
    a = json.loads(BT.read_text(encoding="utf-8"))
    cls = {m["class"] for m in a["miss_classes"]}
    assert "MEMBERSHIP GAP" in cls
    assert "ABOVE FLOOR" in cls
    # a membership-gap miss is one where size WOULD have fired
    for m in a["miss_classes"]:
        if m["class"] == "MEMBERSHIP GAP":
            assert m["cap"] < m["floor"]
            assert m["in_pit_membership"] is False
        if m["class"] == "ABOVE FLOOR":
            assert m["cap"] >= m["floor"]


@pytest.mark.skipif(not BT.exists(), reason="no backtest")
def test_negative_result_is_kept():
    """Persistence did not work. It must still be reported —
    dropping negative results is how backtests start lying."""
    a = json.loads(BT.read_text(encoding="utf-8"))
    p = a["features"]["persistence"]
    assert p["deleted_median"] == p["fa_median"]
    assert "NO discriminating power" in p["verdict"]
    d = a["features"]["depth"]
    assert d["deleted_median"] < d["fa_median"]


@pytest.mark.skipif(not BT.exists(), reason="no backtest")
def test_float_gap_is_declared_untestable():
    a = json.loads(BT.read_text(encoding="utf-8"))
    fc = a["float_coverage"]
    assert fc["deleted_with_float"] / fc["deleted_total"] < 0.25
    assert "UNTESTABLE" in fc["verdict"]


@pytest.mark.skipif(not BT.exists(), reason="no backtest")
def test_html_report_self_contained_and_honest():
    from backtest_html import main
    h = main()
    a = json.loads(BT.read_text(encoding="utf-8"))
    assert "<script" not in h
    net = h.replace("xmlns='http://www.w3.org/2000/svg'", "")
    for bad in ("http://", "https://", "cdn."):
        assert bad not in net, bad
    # the unflattering numbers must be on the page
    assert f"{a['deletions']['false_alarms']}" in h
    assert f"{a['deletions']['precision']:.0%}" in h
    assert "mis-specified" in h
    assert "UNTESTABLE" in h
