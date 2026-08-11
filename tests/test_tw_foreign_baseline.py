"""Guards for the foreign-flow-vs-normal study (c-357).

WHAT MAKES THIS ANALYSIS RIGHT OR WRONG. The finding — the flow
lands on the effective day, not across the window — depends
entirely on three methodological choices, and each one has a
failure mode a later edit could quietly introduce:

  1. UNITS. Phases are multi-session windows; the effective day
     is one session. If anyone compares a 20-session cumulation
     to a single day again, the pre phase looks 20x too big and
     the finding inverts.

  2. THE BASELINE IS |NET|. Signed foreign net medians to ~zero
     on ordinary days, so dividing by the signed median would
     produce absurd multiples. The yardstick must be the median
     ABSOLUTE net.

  3. THE BASELINE IS PRE-EVENT AND PER-STOCK. A pooled
     all-history baseline would let a 2016 regime price a 2025
     event.
"""
import json
import pathlib
import statistics as stats
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
SRC = ROOT / "data" / "tw_foreign_baseline.json"
DOC = ROOT / "docs" / "TW_FOREIGN_BASELINE.md"

pytestmark = pytest.mark.skipif(
    not SRC.exists(), reason="run scripts/tw_foreign_baseline.py")


@pytest.fixture(scope="module")
def d():
    return json.loads(SRC.read_text(encoding="utf-8"))


def test_the_multiples_reconcile_to_their_own_events(d):
    """The side-level medians must be recomputable from the
    per-event rows — the aggregation cannot say something the
    events do not."""
    for side in ("ADD", "DEL"):
        g = [r for r in d["events"] if r["action"] == side]
        assert len(g) == d["sides"][side]["n"]
        for ph in ("pre", "mid", "eff", "post"):
            want = d["sides"][side]["x_normal"][ph]["p50"]
            got = stats.median(r[f"x_normal_{ph}"] for r in g)
            assert abs(got - want) < 1e-6, (side, ph)


def test_each_event_multiple_is_rate_over_own_baseline(d):
    """The per-event arithmetic, re-derived: multiple = phase
    rate / that stock's own |net| baseline. And the baseline must
    be positive — a zero baseline would print infinite
    multiples."""
    for r in d["events"]:
        assert r["baseline_abs_adv"] > 0
        assert r["baseline_days"] >= 60
        for ph in ("pre", "mid", "eff", "post"):
            want = r[f"rate_{ph}"] / r["baseline_abs_adv"]
            assert abs(want - r[f"x_normal_{ph}"]) < 5e-3, (
                r["key"], ph)


def test_the_finding_the_flow_lands_on_the_day(d):
    """THE HEADLINE, pinned loosely. The effective-day multiple
    must dominate the pre and mid phases on BOTH sides, in the
    direction of the event — additions buy, deletions sell —
    and the surrounding phases must be same-order with a normal
    day rather than with the print. Pinned as inequalities, not
    values, so a re-harvest moves the numbers without breaking
    the shape unless the shape actually breaks."""
    A = d["sides"]["ADD"]["x_normal"]
    D = d["sides"]["DEL"]["x_normal"]
    assert A["eff"]["p50"] > 2.0
    assert D["eff"]["p50"] < -2.0
    for ph in ("pre", "mid"):
        assert abs(A[ph]["p50"]) < 1.5, ph
        assert abs(D[ph]["p50"]) < 1.5, ph
    assert A["eff"]["p50"] > 3 * abs(A["mid"]["p50"])
    assert abs(D["eff"]["p50"]) > 3 * abs(D["mid"]["p50"])
    # and the asymmetric tail: deletions keep selling after the
    # print, additions do not keep buying
    assert D["post"]["p50"] < -1.0
    assert A["post"]["p50"] > -1.0


def test_baselines_are_sane_scales(d):
    """A normal day's |foreign net| in a covered Taiwan name is a
    few percent of ADV, not half of it. If this drifts to 0.5 the
    join is broken (probably ADV units), and every multiple on
    the page is silently wrong."""
    for side in ("ADD", "DEL"):
        b = d["sides"][side]["baseline_abs_adv"]
        assert 0.01 < b["p50"] < 0.35, (side, b["p50"])


def test_coverage_is_declared(d):
    """The T86 harvest is a watch list, not the market. The
    events that could not be baselined must be counted, and the
    used-plus-skipped total must tie to the study's own flow
    coverage."""
    study = json.loads(
        (ROOT / "data" / "tw_addition_study.json")
        .read_text(encoding="utf-8"))
    with_flow = [e for e in study["events"]
                 if e.get("foreign_eff_adv") is not None
                 and e.get("adv")]
    cov = d["coverage"]
    assert (cov["events_used"]
            + len(cov["skipped"]["thin_baseline"])
            == len(with_flow))
    assert "netting" in d["method"]["netting_caveat"].lower() or \
        "nets" in d["method"]["netting_caveat"]


def test_the_page_renders_the_section(d):
    """Rendered-output guard: the section exists between
    positioning and the order, the cards carry the JSON's own
    multiples, and the netting caveat survives editing —
    without it every multiple on screen quietly understates
    gross demand."""
    from conftest import real_streamlit
    real_streamlit()
    from streamlit.testing.v1 import AppTest
    h = ROOT / "tests" / "_tw_fb_harness.py"
    h.write_text(
        f"import sys; sys.path.insert(0, {str(ROOT)!r})\n"
        "from views import tw_case_study\ntw_case_study.render()\n",
        encoding="utf-8")
    try:
        at = AppTest.from_file(str(h), default_timeout=300).run()
        assert not at.exception, [e.value for e in at.exception]
        s = " ".join(m.value for m in at.markdown)
    finally:
        h.unlink(missing_ok=True)
    assert "Foreign Flow Through the Rebalance Window" in s
    A = d["sides"]["ADD"]["x_normal"]
    D = d["sides"]["DEL"]["x_normal"]
    assert f"{A['eff']['p50']:+.1f}×" in s
    assert f"{D['eff']['p50']:+.1f}×" in s
    # c-361 cut the deletion-tail and netting paragraphs from
    # the caveat; c-370, Bill cut the post-print CARD too — the
    # tail now lives only in the chart's post-phase bar and the
    # doc, so its multiple must NOT appear in the page markdown
    assert f"{D['post']['p50']:+.1f}×" not in s
    assert "Deletions keep selling" not in s
    assert "UNDERSTATE" not in s
    # and the c-368 instrument note is off again (c-370)
    assert "Deeper file, bigger sample" not in s
    # the baseline card went at c-359. The band label moved
    # inside the band and was renamed at c-361 — it lives in the
    # FIGURE, not the markdown, so it is asserted on the view
    # source here and visually on the chart
    src_ = (ROOT / "views" / "tw_case_study.py").read_text(
        encoding="utf-8")
    assert "normal day band" in src_
    assert 'annotation_text="\\u00b11 = a normal day"' not in src_
    # ordering — c-368, Bill: foreign flow MOVES AHEAD of the
    # positioning read. What usually happens through the window,
    # then what is happening now, then the order.
    i_pos = s.index("Market Positioning Before Announcement")
    i_fb = s.index("Foreign Flow Through the Rebalance Window")
    i_ord = s.index("Estimated Trading Volume on the "
                    "Effective Day")
    assert i_fb < i_pos < i_ord


def test_the_doc_quotes_the_json(d):
    if not DOC.exists():
        pytest.skip("doc missing")
    doc = DOC.read_text(encoding="utf-8")
    for side in ("ADD", "DEL"):
        x = d["sides"][side]["x_normal"]["eff"]["p50"]
        assert f"{x:+.1f}x" in doc, side
    assert "per-session rates" in doc
