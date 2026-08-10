"""c-115 pins: the plain-English walkthrough.

The design promise is that the narrative is GENERATED, never
written — so the tests assert exactly that: every headline
number in the story must equal the engine's own output, and no
step may hardcode a figure. If that ever breaks, the
walkthrough could tell a comforting story the engine does not
support, which is the one failure mode that matters here.
"""
import json
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _step(story, key):
    """A step by its stable key. c-282 removed step 4 and
    renumbered the rest, so a test that hunts by number is
    testing a position rather than a thing."""
    return next(x for x in story["steps"] if x.get("key") == key)
sys.path.insert(0, str(ROOT / "scripts"))
REC = ROOT / "data" / "reconstruct" / "TW_May26.json"


@pytest.mark.skipif(not REC.exists(), reason="no reconstruction")
def test_every_number_ties_to_the_engine():
    from walkthrough_story import story
    s = story("Taiwan", "May26")
    eng = json.loads(REC.read_text(encoding="utf-8"))
    assert s["keys"] == eng["keys"]
    assert s["fx"] == eng["fx_used"]
    # step 3's quoted lines must be the engine's lines
    s3 = _step(s, "cutoff")
    # c-268 CONTRACT CHANGE. Step 3's figure row is deleted —
    # the diagram now carries the six layers, with the reason
    # for each. So the tie moves to the DIAGRAM: the thresholds
    # it draws must be the engine's, which is the promise the
    # row used to hold up.
    assert s3["numbers"] == []
    from views import diagrams as D
    ek = eng["keys"]
    svg = D.size_ladder(
        dm_ref=ek["gmsr_dm"], em_ref=round(ek["gmsr_dm"] / 2, 2),
        lo=ek["em_range"][0], hi=ek["em_range"][1],
        cutoff=7.0, lower=ek["floor"], upper=ek["bar"])
    for v in (ek["gmsr_dm"], ek["em_range"][0], ek["em_range"][1],
              ek["floor"], ek["bar"]):
        assert f"&#36;{v}B" in svg, v
    # c-253 CONTRACT CHANGE. A reconstructed review has no
    # Market Size-Segment Cutoff on file, and its stored floor
    # and bar were derived from the ceiling of the global range
    # — the wrong base (§3.1.5.1 applies the buffers to the
    # MARKET cutoff). The step withholds them rather than
    # printing figures we know are mis-based, and the page
    # draws no ladder at all without a cutoff, so this asserts
    # the withholding in the prose. Re-running
    # review_reconstruct.py under the corrected rule is the
    # follow-up job.
    assert not ek.get("cutoff")
    body = " ".join(s3["plain"])
    assert "has not been recomputed" in body
    # step 6's scoreboard must be the engine's grading
    g = eng["grading"]
    s6 = _step(s, "call")
    v6 = {n["label"]: n["value"] for n in s6["numbers"]}
    h, m = len(g["hits"]), len(g["misses"])
    assert v6["Removals caught"] == f"{h}/{h + m}"
    assert v6["Removals missed"] == m
    assert v6["False alarms"] == len(g["false_alarms"])


@pytest.mark.skipif(not REC.exists(), reason="no reconstruction")
def test_story_shape_and_honesty_contract():
    from walkthrough_story import story
    s = story("Taiwan", "May26")
    assert s["mode"] == "solved"
    assert s["title"] == "Predict MSCI Index Changes"
    # c-282 removed step 4 and renumbered, so every reference
    # here keys off `key` rather than the display number. A
    # number is a position; a key is an identity.
    # c-287: five. The limits step was removed at Bill's
    # request — see the note in walkthrough_story, which records
    # what that costs rather than pretending it costs nothing.
    assert [x["n"] for x in s["steps"]] == list(range(1, 6))
    assert [x["key"] for x in s["steps"]] == [
        "timeline", "data", "cutoff", "buffers", "call"]
    for x in s["steps"]:
        assert x["plain"] and x["title"]
    # c-162 CONTRACT CHANGE. The per-step "honesty" and "desk"
    # blocks were removed at Bill's instruction when the page was
    # rebuilt for a PT-trader audience. The honesty requirement is
    # NOT dropped — it moved, so the test moves with it: the
    # limits must still appear, consolidated in step 7, naming
    # discretion, float, off-cycle exits and blind spots.
    # c-287: the limits STEP is gone from the page, so the
    # honesty requirement moves to where the limits still live
    # — the registered call file, which travels with every
    # prediction. If that ever empties, the project has stopped
    # declaring what it cannot see.
    import json as _j
    call = _j.loads(
        (ROOT / "data" / "aug26_tw_call_v2.json").read_text(
            encoding="utf-8"))
    lim = " ".join(call.get("limits") or []).lower()
    assert lim, "the call declares no limits at all"
    for limit in ("deletion", "float"):
        assert limit in lim, limit
    # the misses must be VISIBLE in prose, not just in a metric
    assert "false alarm" in " ".join(
        _step(s, "call")["plain"]).lower()


def test_live_mode_declares_before_the_answer():
    from walkthrough_story import story
    s = story("Taiwan", "Aug26")
    assert s["mode"] == "live"
    s6 = _step(s, "call")
    # c-312, Bill: the prose standfirst ("Registered before MSCI
    # announces, so there is nothing to grade against yet") is
    # deleted from the step. WORTH BEING HONEST ABOUT WHAT THAT
    # COSTS: the page no longer states in words that the call is
    # ungraded, so this test can no longer check the sentence.
    #
    # What it checks instead is the part that actually protects
    # the reader — that a live story cannot ACQUIRE a scoreboard.
    # The declaration date survives in the step's own figure row
    # and in the registered call file, which is where a claim
    # about timing belongs anyway: a date in prose can drift out
    # of step with the file, a date read from the file cannot.
    assert "declared" in " ".join(
        n["label"].lower() for n in s6["numbers"])
    # a live story must never claim a scoreboard
    assert s["grading"] is None


@pytest.mark.skipif(not REC.exists(), reason="no reconstruction")
def test_no_hardcoded_financial_figures_in_prose():
    """Guard the generation promise: prose may not contain a
    '$<number>B' literal — those must be interpolated."""
    src = (ROOT / "scripts" / "walkthrough_story.py").read_text(
        encoding="utf-8")
    prose = re.findall(r'"\s*([^"]{40,})\s*"', src)
    bad = [p for p in prose
           if re.search(r"\$\d", p) and "{" not in p]
    assert not bad, bad[:3]


@pytest.mark.skipif(not REC.exists(), reason="no reconstruction")
def test_html_export_is_self_contained():
    from walkthrough_export import to_html
    from walkthrough_story import story
    h = to_html(story("Taiwan", "May26"))
    assert h.startswith("<!doctype html")
    assert "<svg" in h                      # chart is inline
    # no network dependencies. The SVG xmlns is a namespace
    # identifier, never fetched — strip it before checking.
    net = h.replace('xmlns="http://www.w3.org/2000/svg"', "")
    # a HYPERLINK does not break self-containment; a fetched
    # RESOURCE does. c-162 added the MSCI rulebook link, so the
    # check now targets what it always meant: no external script,
    # stylesheet, image or iframe.
    import re
    for bad in ("<script", "cdn.", "<iframe"):
        assert bad not in net, bad
    for tag in re.findall(r"<(?:link|img|source)[^>]*>", net):
        assert "http" not in tag, tag
    eng = json.loads(REC.read_text(encoding="utf-8"))
    assert f"${eng['keys']['floor']}B" in h


APP = """
import sys
sys.path.insert(0, ".")
from views import walkthrough
walkthrough.render()
"""


@pytest.fixture(scope="module")
def at():
    """c-245: this page had SIX tests and none of them drew it.

    Every one asserted on `story()` — the data — so the page
    could have raised on every load and the suite would have
    stayed green. The step redesign is a rendering change, so
    it needs a rendering test."""
    for name in [n for n in sys.modules
                 if n == "streamlit" or n.startswith("streamlit.")
                 or n.startswith("views")]:
        mod = sys.modules[name]
        if getattr(mod, "__file__", None) is None:
            del sys.modules[name]
    pytest.importorskip("streamlit")
    from streamlit.testing.v1 import AppTest
    a = AppTest.from_string(APP, default_timeout=240)
    a.run()
    return a


def test_the_page_renders(at):
    assert not at.exception, [e.value[:400] for e in at.exception]


def test_steps_use_the_site_section_rule_and_say_step(at):
    """Bill, c-245: same treatment as the review database, but
    the eyebrow reads "Step". One word, one parameter — not a
    second heading system."""
    md = " ".join(str(m.value) for m in at.markdown)
    for n in range(1, 6):
        assert f"<span class='n'>Step {n}</span>" in md, n
    assert "<span class='n'>Step 6</span>" not in md
    assert "Section 1" not in md
    # the page-local heading stylesheet is gone for good
    for dead in ("steptitle", "stepnum", "class='lead'"):
        assert dead not in md, dead


def test_explanations_render_as_beats_not_a_box(at):
    """c-247, D13 amended. The white prose card is gone: a box
    is for DATA, and this site's rule is rules-not-boxes. Beats
    are numbered by a CSS counter so nothing needs renumbering
    when a step gains a paragraph."""
    from views import design
    assert "st-key-dbeats_" in design.CSS
    assert "counter-increment:beat" in design.CSS
    assert "st-key-dprose" not in design.CSS, "the box is back"
    assert not hasattr(design, "prose")


def test_step_1_draws_the_two_diagrams_from_MSCI_dates(at):
    """c-249. Bill asked for a graph in every step, starting
    with step 1. The dates in them are MSCI's own, read from
    data/msci_review_dates.json — a date drawn into a picture
    is still a fact, and this page holds no facts."""
    md = " ".join(str(m.value) for m in at.markdown)
    # c-301: four, not five. The conviction waterfall went with
    # the call step's figure row at Bill's request.
    # c-318: THREE, not four. The step-4 shortlist scan is no
    # longer an SVG — it is a plotly figure, because its tooltip
    # had to work and an SVG <title> on a 5px dot does not. The
    # three that remain are step 1's two and the size ladder.
    #
    # Counting SVGs was always a proxy for "the diagrams are
    # there". The scan is now asserted by identity in
    # test_the_scan_is_drawn_on_real_taiwan_market_caps rather
    # than by tag, which is the better test anyway.
    assert md.count("<svg") >= 3, "a step diagram is missing"
    assert "Index-replicating funds" in md
    # c-251: MSCI's press releases label the fields
    # "Announcement date" and "Effective date". The GIMI
    # methodology has NO defined term "Index Announcement Date"
    # or "Index Effective Date" — it capitalises the three data
    # cutoffs and leaves these two in lower case — so the page
    # uses MSCI's labels without an "Index" prefix.
    assert "Announcement Date" in md
    assert "Effective Date" in md
    assert "Index Announcement Date" not in md
    assert "Index Effective Date" not in md
    # c-267: ONE tick, not two. Showing MSCI's calendar label a
    # day after the close it describes read as two events, so
    # the second tick is gone and the surviving one is valued
    # at the CLOSE — which is when the trade actually prints.
    #
    # This used to need scoping to the flow diagram, because
    # step 2's screen-windows figure legitimately cited 1 Sep as
    # the implementation anchor for minimum length of trading.
    # c-268 removed that figure, so 1 Sep is now absent from the
    # whole page — and the page-wide check the scoping worked
    # around is the one that would have caught it coming back.
    from views import diagrams as D
    flow = D.review_flow("12 Aug 2026", "31 Aug 2026")
    assert "Close of 31 Aug 2026" in flow
    assert "1 Sep" not in flow
    assert "Effective Date" in flow
    # step 2: the three rulebook cutoffs, c-250
    for lab in ("Equity Universe Cutoff", "Liquidity Cutoff",
                "Price Cutoff"):
        assert lab in md, lab
    for dt in ("29 May 2026", "30 Jun 2026", "20 Jul 2026",
               "31 Jul 2026"):
        assert dt in md, dt
    # MSCI: announced 12 Aug 2026, changes as of the close of
    # 31 Aug 2026. The calendar's "effective date" of 1 Sep is
    # the one-day trap (see the test below) and must not appear
    # anywhere on the page as a date of its own.
    for d in ("12 Aug 2026", "31 Aug 2026"):
        assert d in md, d
    assert "1 Sep 2026" not in md


def test_no_date_is_typed_into_a_drawing(at):
    """The generation promise, extended to the diagrams.

    Asserted on the OUTPUT rather than the source: a first
    version grepped diagrams.py for a year and kept firing on
    the rulebook edition named in a docstring, which is
    documentation, not a rendered fact. Feed the functions
    sentinels and check nothing else comes out."""
    from views import diagrams
    out = (diagrams.review_flow("D1", "D2", "D3", "D4")
           + diagrams.cutoff_timeline("D5", "D6", "D7", "D8",
                                      "D9", "D10")
)
    # the size ladder takes numbers, not dates, so it is
    # checked for a stray YEAR only
    out += diagrams.size_ladder(1.1, 2.2, 3.3, 4.4, 5.5, 6.6,
                                7.7, 8.8)
    out += diagrams.two_measure_walk(85, 115, 6.74)
    _c = [{"cap_usd_b": 5.0, "verdict": "QUALIFIES"}]
    out += diagrams.shortlist_scan(_c, _c, 4.4, 6.6, 10.1)
    out = out.replace("www.w3.org/2000/svg", "")
    assert not re.search(r"\d{4}-\d{2}-\d{2}", out)
    assert not re.search(r"\b(19|20)\d{2}\b", out)


def test_the_one_day_trap_is_not_collapsed(at):
    """MSCI describes one event with two dates a day apart: the
    change is made "as of the close" of the last trading day,
    while the calendar's "effective date" is the day after. The
    trade prints at the earlier one. A page that shows only the
    later date sends a desk a day late."""
    import json
    d = json.loads((ROOT / "data" / "msci_review_dates.json")
                   .read_text(encoding="utf-8"))["reviews"]
    a = d["Aug26"]
    assert a["rebalance_close"] < a["effective"]
    md = " ".join(str(m.value) for m in at.markdown)
    assert "as of the close" in md


def test_step_3_buffers_hang_off_the_market_cutoff(at):
    """c-253. §3.1.5.1 p.44 applies the 2/3 and 1.5 buffers to
    the MARKET SIZE-SEGMENT CUTOFF. The page applied them to
    the ceiling of the global EM range, which is not Taiwan's
    number at all — so this pins the base, not the values."""
    from walkthrough_story import story
    k = story("Taiwan", "Aug26")["keys"]
    cut = k["cutoff"]
    assert abs(k["floor"] - 2 / 3 * cut) < 0.01
    assert abs(k["bar"] - 1.5 * cut) < 0.01
    assert abs(k["min_float_cap"] - 0.5 * cut) < 0.01
    # the old, wrong base must not reappear
    assert abs(k["floor"] - 2 / 3 * k["ceiling"]) > 0.5
    # 1.8x is the market-stress multiple (fn24 p.44 / p.107),
    # not a property of a quarterly review
    assert abs(k["bar"] - 1.8 * cut) > 0.5


def test_the_provider_relationship_is_drawn_both_ways(at):
    """c-266, Bill: add an arrow back from the funds to MSCI.

    One outbound arrow made this read as an announcement. It
    is an obligation — MSCI publishes, and the funds are
    contractually bound to follow — and that obligation is the
    entire reason the resulting flow is forecastable. A reader
    who sees only "publishes" has no reason to expect anyone
    to trade."""
    from views import diagrams as D
    svg = D.review_flow("A", "B", "C")
    assert "PUBLISHES" in svg
    assert "MUST FOLLOW" in svg
    # one head pointing right, one pointing left
    import re
    heads = re.findall(r'<path d="M([\d.]+) [\d.]+ '
                       r'L([\d.]+) ', svg)
    dirs = {"right" if float(b) < float(a) else "left"
            for a, b in heads}
    assert dirs == {"right", "left"}, dirs


def test_each_box_sits_directly_above_the_tick_it_feeds(at):
    """c-265, Bill: the blue box should point straight at the
    announcement, the green and red boxes straight at the
    rebalance close.

    So the TICKS are placed on the boxes' centres, not the
    boxes wired sideways to arbitrary ticks. This pins the
    relationship rather than the pixel values — a later change
    to the box widths must move the ticks with them."""
    import re

    from views import diagrams as D
    svg = D.review_flow("A", "B", "C")
    # every CONNECTOR must be a straight vertical drop: the
    # elbow's x coordinates equal. Match on fill="none", which
    # is what separates a connector from an arrowhead triangle
    # — the first version of this test caught the PUBLISHES
    # arrow's head and failed on a shape that is meant to be
    # diagonal.
    paths = re.findall(
        r'<path d="M([\d.]+) [\d.]+ L([\d.]+) [\d.]+ '
        r'L([\d.]+) [\d.]+" fill="none"', svg)
    assert paths, "no connectors found"
    for x1, x2, x3 in paths:
        assert x1 == x2 == x3, (x1, x2, x3)
    # and the ticks must be under the boxes, not beside them
    rects = re.findall(r'<rect x="(\d+)" y="16" width="(\d+)"',
                       svg)
    centres = {float(x) + float(w) / 2 for x, w in rects}
    drops = {float(p[0]) for p in paths}
    assert drops <= centres, (drops, centres)


def test_step_6_shows_how_the_conviction_number_is_built(at):
    """c-257. Bill: "I don't even know how we calculate this
    either." The model lived in a script and nowhere on the
    page. It is base rate x haircuts, and the two things that
    must travel with it are that the inputs are REGISTERED
    JUDGEMENTS and that they are UNCALIBRATED — a percentage
    nobody has scored is a ranking, not a probability."""
    from walkthrough_story import story
    s = story("Taiwan", "Aug26")
    # c-306, Bill removed the explainer from the step, so the
    # three prose assertions go with it. WORTH RECORDING: c-257
    # existed because Bill could not tell how the number was
    # computed, and the page no longer says. The base rates,
    # the haircuts and the uncalibrated warning still travel in
    # the registered call file — which is what the surviving
    # half of this test checks, and it is the half that
    # protects the NUMBER rather than the paragraph about it.
    #
    # The arithmetic must still reproduce a real registered call
    c = s["call"]
    br, hc = (c["registered_base_rates"],
              c["registered_haircuts"])
    ex = next(r for r in c["calls"]
              if r["action"] == "ADD"
              and "guaranteed" in r["zone"]
              and "float from" in " ".join(r["caveats"]).lower()
              and "atvr" not in " ".join(r["caveats"]).lower())
    p = (br["add_guaranteed"] * hc["count_flex"]
         * hc["float_estimated"] * hc["blind_band"])
    assert abs(p - ex["prob"]) < 0.005, (p, ex["prob"])


def test_the_download_block_is_off_the_page(at):
    """c-257. Bill removed "Take It With You". The EXPORTER
    stays — it is what keeps the numbers honest away from the
    app, and it is still tested — only the button is gone."""
    assert not at.button
    md = " ".join(str(m.value) for m in at.markdown)
    assert "Take It With You" not in md
    from walkthrough_export import to_html
    assert callable(to_html)


def test_the_light_rebalancing_is_a_stress_rule_not_a_cadence(at):
    """c-256. Bill: keep 1.8x documented as the
    light-rebalancing contingency, not as the August rule.

    It has to survive as LIVE knowledge — what would trigger
    it, who decides, and what it would do to the two lines —
    rather than only as a footnote about a mistake we made.
    The failure mode this guards is the original one: reading
    fn24's 1.8x as a property of quarterly reviews.

    c-269: it MOVED. Bill deleted it from step 3, correctly —
    it is not a link in the derivation chain, it is a rule that
    can widen both buffers with almost no notice, which makes
    it a limit on the call. So it lives in step 7 now, and this
    test follows it rather than being deleted with the
    paragraph. The knowledge is the thing being guarded, not
    its address; the one addition is that step 3 must NOT carry
    it, which is what Bill asked for."""
    from walkthrough_story import story
    steps = story("Taiwan", "Aug26")["steps"]
    s3 = _step({"steps": steps}, "cutoff")
    assert "light rebalancing" not in " ".join(s3["plain"])
    # c-287, AND THIS IS A REAL LOSS, recorded rather than
    # quietly dropped. The 1.8x light-rebalancing contingency
    # lived in the limits step, and that step was removed at
    # Bill's request — so the PAGE no longer carries it. The
    # knowledge survives in docs/MSCI_SIZE_SEGMENT_SPEC.md and
    # docs/STEP3_RULEBOOK_VERIFICATION.md, which is where this
    # test now looks. If it ever leaves those too, the project
    # has forgotten the rule rather than relocated it.
    body = " ".join(
        (ROOT / "docs" / f).read_text(encoding="utf-8")
        for f in ("MSCI_SIZE_SEGMENT_SPEC.md",
                  "STEP3_RULEBOOK_VERIFICATION.md"))
    assert "light rebalancing" in body
    assert "market-stress" in body or "market stress" in body
    assert "Index Policy Committee" in body
    # the alternative multiples are stated, and are NOT live
    assert "1.8x" in body and "0.5x" in body
    # the SUBSTANCE, not the page's old sentence: the
    # multiplier itself, which is the thing a desk would
    # act on if MSCI ever invoked the contingency
    assert "1.8" in body


def test_step_3_labels_the_corridor_as_global_not_taiwans(at):
    """It is the Global Minimum Size Range for EM Standard and
    applies to every emerging market. Calling it "Taiwan's
    permitted band" made the one genuinely Taiwanese number —
    the Market Size-Segment Cutoff — invisible."""
    md = " ".join(str(m.value) for m in at.markdown)
    assert "Taiwan's permitted band" not in md
    assert "Global Minimum Size Range" in md
    assert "Market Size-Segment Cutoff" in md


def test_step_7_hides_nothing(at):
    """D8. Step 7 is the limits of the method. A limitation
    behind a click is a limitation the reader does not carry,
    so it is the one step with no detail toggle."""
    from views import design
    import views.walkthrough as W
    seen = {}
    real = design.beats

    def spy(paras, key, shown=2, detail_label=None):
        seen[key] = (len(paras), shown)
        return real(paras, key, shown, detail_label)

    design.beats = spy
    try:
        W._method(W._story("Taiwan", W.REVIEW))
    finally:
        design.beats = real
    # c-282: the limits step is 6 now, not 7 — step 4 was
    # removed and everything after it moved up one.
    # c-287: no limits step to check. The shown=None case is
    # gone with it, which is worth stating plainly rather than
    # quietly deleting the assertion.
    assert 6 not in seen, "an unexpected sixth step appeared"
    # c-268: step 2 is now the mirror image — it shows NOTHING
    # open, because its two figures carry the step and the whole
    # rulebook block belongs behind "Rulebook References". Both
    # exceptions are deliberate, so both are named here rather
    # than loosening the rule to "anything goes".
    assert seen[2][1] == 0, "step 2 leaked its rulebook block"
    # c-278: step 3 joins it. Its seven-card ladder carries the
    # whole derivation with the arithmetic on every card, so the
    # paragraphs that used to sit above the figure were a second
    # telling and moved behind the expander. Named here rather
    # than loosening the rule to "anything goes" — the default
    # is still 2, and a step that wants to differ has to be
    # listed in this test before it can.
    assert seen[3][1] == 0, "step 3 leaked its rulebook block"
    # c-293: step 4 (the shortlist) joins them, with shown=None
    # rather than 0 — Bill removed its "Rulebook References"
    # toggle, and None shows every paragraph inline so no toggle
    # is created. Named here rather than loosening the rule to
    # "anything goes": every remaining step still defaults to 2.
    assert seen[4][1] is None, "step 4 grew a toggle back"
    # c-301: step 5 (the call) joins them — Bill removed its
    # Rulebook References too, and shown=None creates no toggle.
    assert seen[5][1] is None, "step 5 grew a toggle back"
    assert all(v[1] == 2 for k, v in seen.items()
               if k not in (2, 3, 4, 5))


def test_a_figure_row_is_ruled_off_from_the_text_below(at):
    """Bill: "there isn't any divider between this header and
    the text box below." The steps used st.metric, the one
    figure treatment on the site with no rule under it."""
    md = " ".join(str(m.value) for m in at.markdown)
    # c-268: steps 1, 2 and 3 have no figure row now — their
    # diagrams carry those numbers, with the reason for each,
    # which a row of values cannot. The assertion is about the
    # TREATMENT, so it drops to the count that survives rather
    # than being deleted: any row that exists is `dstats`, and
    # st.metric never comes back.
    # c-282: three, not four — the step that carried one of
    # these rows was removed.
    # c-293: two. Bill deleted the shortlist step's figure row
    # (lower buffer / upper buffer / incumbents below the
    # floor), so one more row is gone.
    # c-300: one. The size-line chart's three-cell readout goes
    # too on an UNGRADED review — it said "Names below the floor
    # 0" and "Outcome: not announced yet", which the chart and
    # the page already say. The graded branch still builds a row,
    # so this floor holds for a solved review as well.
    #
    # The assertion was always about the TREATMENT, not the
    # count: any row that survives is `dstats`, and st.metric
    # never comes back. That second clause is the one that
    # matters and it is unchanged.
    # c-301: ZERO on a live review. The call step was the last
    # one carrying a figure row and Bill removed it, so there is
    # no row left to rule off. The test keeps the clause that
    # actually protects the design — st.metric, the one figure
    # treatment on this site with no rule under it, must never
    # come back — and drops a count that now has nothing to
    # count. A graded review still builds a row (see _lever), so
    # this is a property of the OPEN review, not of the page.
    assert not at.metric, "st.metric is back on this page"


def test_the_market_left_the_page_title(at):
    assert any("# Predict MSCI Index Changes" in str(m.value)
               and "Taiwan" not in str(m.value).split("\\n")[0]
               for m in at.markdown)


def test_page_wired_into_app():
    src = (ROOT / "app.py").read_text(encoding="utf-8")
    assert "walkthrough" in src
    assert "Predict MSCI Index Changes" in src
    import ast
    ast.parse((ROOT / "views" / "walkthrough.py").read_text(
        encoding="utf-8"))


def test_no_diagram_emits_a_bare_dollar_sign(at):
    """c-268 — this one shipped, and Bill saw it.

    Streamlit's markdown renders `$ ... $` as inline LaTeX. The
    size ladder writes twelve dollar signs, so the renderer
    paired them off, treated the SVG between each pair as
    maths, and spilled the rest onto the page as visible tag
    soup. Step 3 was broken on the live site.

    The failure mode is nasty because it is PARITY-dependent:
    the walk diagram has a single dollar sign and rendered
    fine, so the bug looked specific to step 3 rather than
    general to money. Assert the property, not the symptom —
    no diagram may hand markdown a raw dollar.
    """
    from views import diagrams as D
    out = {
        "ladder": D.size_ladder(1.1, 2.2, 3.3, 4.4, 5.5, 6.6,
                                7.7, 8.8),
        "walk": D.two_measure_walk(85, 115, 6.74),
        "shortlist": D.shortlist_scan(
            [{"cap_usd_b": 5.0, "verdict": "QUALIFIES"}],
            [{"cap_usd_b": 5.0, "verdict": "BELOW"}],
            4.4, 6.6, 10.1),
        "flow": D.review_flow("A", "B"),
        "cutoffs": D.cutoff_timeline("A", "B", "C", "D", "E", "F"),
        "waterfall": D.conviction_waterfall("BAND", 0.55, [], 0.55),
    }
    for name, svg in out.items():
        assert "$" not in svg, name
    # and the entity is what reaches the browser instead
    assert "&#36;" in out["ladder"]


def test_arrowheads_point_where_the_label_says(at):
    """c-268 — every arrowhead on step 1 was drawn backwards.

    `_arrow` offset the head's two base corners in the same
    direction the arrow travels, so the apex sat BEHIND the
    base and the shaft overran the tip by 7 units to cover it.
    Bill caught it on the return arrow ("should point to the
    left, not right"); PUBLISHES had the same defect and nobody
    saw it, because an apex touching the box it points at reads
    as correct either way.

    Asserted on geometry, not on eyeballs: for a right-pointing
    arrow the apex must be to the RIGHT of both base corners.
    """
    import re
    from views import diagrams as D

    def head(svg, colour):
        m = re.search(
            r'<path d="M([\d.]+) [\d.]+ L([\d.]+) [\d.]+ '
            r'L[\d.]+ [\d.]+ Z" fill="' + colour + '"/>', svg)
        assert m, colour
        return float(m.group(1)), float(m.group(2))

    fwd = D._arrow(100, 300, 50, "publishes")
    apex, base = head(fwd, D.NAVY)
    assert apex > base, "publishes must point right"
    assert apex == 300                      # lands on its target

    back = D._arrow(100, 300, 50, "must follow", colour=D.GREEN,
                    back=True)
    apex, base = head(back, D.GREEN)
    assert apex < base, "must follow must point left"
    assert apex == 100


def test_a_note_label_is_bolded_but_a_timestamp_is_not(at):
    """c-268, Bill: *"Bold the word 'Note:'"*.

    A rule rather than three edits — the effective-date tick
    carries "MSCI:" and "Index funds:" and wants the same
    treatment. The guard that matters is the NEGATIVE one: the
    time-zone line contains "05:00", and a lazy 'bold up to the
    first colon' would have bolded half a sentence.
    """
    from views import diagrams as D
    assert D._lead_bold("Note: MSCI posts the list") == (
        '<tspan font-weight="700">Note:</tspan> MSCI posts '
        'the list')
    assert D._lead_bold("Index funds: complete the switch")\
        .startswith('<tspan font-weight="700">Index funds:</tspan>')
    for plain in ("Central European Summer Time — 05:00 Hong Kong",
                  "time the following morning, 13 August.",
                  "as of the close of 31 Aug 2026."):
        assert "<tspan" not in D._lead_bold(plain), plain


def test_steps_are_separated_by_one_hairline(at):
    """c-268: a divider between steps, and exactly one design
    for it. Six breaks for seven steps — none above the first,
    which the part heading already opens.

    c-287: four breaks for five steps."""
    md = " ".join(str(m.value) for m in at.markdown)
    assert md.count("<div class='dbreak'></div>") == 4
    from views import design
    assert ".dbreak{" in design.CSS


def test_clause_numbers_live_in_rulebook_references_not_in_figures(at):
    """c-276. Bill, on step 3: *"move this text into 'Rulebook
    References'"*.

    Every step already carries a Rulebook References block that
    lists each clause with its page number and the quoted
    sentence. The figures were ALSO printing bare section marks
    — §2.3.2.1 at the end of a card, §2.2.3 in a caption,
    §2.3.3 on a waterfall bar — so the same citation appeared
    twice on one screen, and the copy inside the drawing was
    the shorter and less useful of the two.

    Asserted on the rendered page rather than on the source,
    because the point is what a reader sees. The count outside
    the figures must stay high: the references did not go away,
    they went somewhere better.
    """
    import re
    md = " ".join(str(m.value) for m in at.markdown)
    figures = re.findall(r"<svg.*?</svg>", md, re.S)
    assert figures, "no figures rendered"
    inside = sum(f.count("§") for f in figures)
    assert inside == 0, f"{inside} clause numbers still in figures"
    # c-324: was >20. Four §3.1.5 clauses were stripped from the
    # call rationales — "a guaranteed addition when a slot exists"
    # overstates a rule that the call's own 0.85 count-flex
    # haircut already prices as uncertain. The floor is lowered
    # rather than removed: the point of the assertion is that the
    # rulebook references have not ALL vanished, which would mean
    # the references block stopped rendering.
    assert md.count("§") >= 15, "the references vanished entirely"


def test_step_three_cards_share_one_left_edge():
    """c-276, Bill: *"make the substep 5 to 7 align vertically
    with step 1-4."*

    Cards 5-7 were indented to x=26 to read as a branch off the
    cutoff, which put two left margins in one figure to show a
    relationship the connector line was already showing.

    The connector had to be redrawn, not just moved: the old
    one was a vertical spine at x=8 with a horizontal elbow
    into each card's left edge, and once the cards start at
    x=0 that spine runs straight through them.
    """
    import re
    from views import diagrams
    svg = diagrams.size_ladder(
        16.41, 8.21, 4.1, 9.44, 7.22, 4.81, 10.83,
        min_float=3.61, pub_dm=15.75, pub_asof="Apr-2026",
        pub_idx=3183.0, cross_rank=69).replace("&#36;", "$")
    cards = re.findall(
        r'<rect x="([0-9.]+)" y="[0-9.]+" width="(\d+)" '
        r'height="[0-9.]+" rx="3"', svg)
    assert len(cards) == 7, f"{len(cards)} cards, expected 7"
    assert len({x for x, _w in cards}) == 1, \
        f"cards do not share a left edge: {sorted({x for x, _w in cards})}"
    assert len({w for _x, w in cards}) == 1, \
        f"cards do not share a width: {sorted({w for _x, w in cards})}"


def test_step_three_explanations_stay_inside_their_card():
    """No explanation line may overrun the card that holds it.

    c-312 REWROTE THIS TEST, and the reason is worth keeping.
    It used to assert "no line longer than 52 characters",
    which was a stand-in for "fits inside 330 units" back when
    330 was a constant in `size_ladder`. The width is now
    `_fitw` over the card's own lines, so a character count
    measures the wrong thing in both directions: it fails a
    wider card whose text fits perfectly, and it passes a
    narrow card full of capitals that does not. Bill's c-312
    request — widen the box so a line does not end on one
    orphaned word — tripped exactly that false failure.

    So the assertion is now the thing the proxy stood for: the
    measured advance width of every line, plus the 14-unit
    inset on each side, against the rendered card width.
    """
    import re
    from views import diagrams
    svg = diagrams.size_ladder(
        16.41, 8.21, 4.1, 9.44, 7.22, 4.81, 10.83,
        min_float=3.61, pub_dm=15.75, pub_asof="Apr-2026",
        pub_idx=3183.0, cross_rank=69).replace("&#36;", "$")
    cw = max(int(m) for m in
             re.findall(r'<rect x="0" y="\d+" width="(\d+)"', svg))
    body = re.findall(
        r'<text x="14" y="[0-9.]+" font-size="[^"]+" '
        r'fill="[^"]+">([^<]*)</text>', svg)
    assert body, "no explanation lines found"
    over = [(b, round(diagrams._linew(b, diagrams.FS_CAP)))
            for b in body
            if diagrams._linew(b, diagrams.FS_CAP) + 28 > cw]
    assert not over, (cw, over)


def test_the_corridor_labels_do_not_reach_into_the_card_column():
    """The ladder's dashed labels grow LEFTWARD, toward the cards.

    c-312: widening the cards moved their right edge toward the
    value axis, and the corridor labels ("ceiling", "floor") are
    anchored `end` just left of that axis — so the two families
    close on each other from opposite sides and nothing in the
    code notices. This is the collision that would print a card's
    last word underneath the word "floor".
    """
    import re
    from views import diagrams
    svg = diagrams.size_ladder(
        16.41, 8.21, 4.1, 9.44, 7.22, 4.81, 10.83,
        min_float=3.61, pub_dm=15.75, pub_asof="Apr-2026",
        pub_idx=3183.0, cross_rank=69).replace("&#36;", "$")
    cw = max(int(m) for m in
             re.findall(r'<rect x="0" y="\d+" width="(\d+)"', svg))
    ends = re.findall(
        r'<text x="([0-9.]+)" y="[0-9.]+" font-size="[^"]+" '
        r'text-anchor="end" fill="[^"]+">([^<]*)</text>', svg)
    assert ends, "no end-anchored corridor labels found"
    clash = [(t, round(float(x) - diagrams._linew(t, diagrams.FS_CAP)))
             for x, t in ends
             if float(x) - diagrams._linew(t, diagrams.FS_CAP) < cw]
    assert not clash, (cw, clash)


def test_step_four_uses_real_taiwan_data_not_a_schematic():
    """c-278, Bill: *"check if you can replace the bar graphs
    with actual results from our Taiwan walk. If not, then
    delete the entire section 4."*

    It could, and doing it fixed a live contradiction rather
    than just improving a picture. The schematic was labelled
    from `story()["walk"]` — crossing rank 115, crossing cap
    6.74 — which is the bottom-up frame c-273 RETRACTED. Step 3
    on the same page has shown rank 69 since. The page was
    carrying two different crossings and the figure quoted the
    withdrawn one.

    So this asserts the two now agree, which is the property
    that was actually broken.
    """
    import walkthrough_story as WS
    c = WS._crossing()
    assert c, "no crossing computed"
    calc = (WS._j("aug26_cutoff_calc.json") or {})
    C = calc.get("derivation", {}).get("C_cutoff", {})
    assert c["crossing_rank"] == C["crossing_rank"], (
        c["crossing_rank"], C["crossing_rank"])
    assert abs(c["crossing_cap_busd"] - C["cutoff_busd"]) < 0.01
    # and it must NOT be the retracted frame
    walk = WS.story()["walk"] or {}
    assert c["crossing_rank"] != walk.get("crossing_rank"), \
        "step 4 is reading the superseded bottom-up walk again"


def test_the_crossing_figure_is_drawn_from_the_passed_rows():
    """The diagram holds no facts. Feed it a different crossing
    and every number on it must move — otherwise something is
    typed into the drawing, which is the failure mode
    diagrams.py exists to prevent."""
    import xml.etree.ElementTree as ET
    from views import diagrams
    fake = {"target_busd": 100.0, "implied_universe_busd": 117.6,
            "coverage": 0.85, "crossing_rank": 4,
            "crossing_cap_busd": 12.34, "screened": 42,
            "priced": "20991231",
            "rows": [{"rank": i, "code": f"X{i}",
                      "cap": 20 - i, "fcap": (20 - i) * .6,
                      "cum": 40 + i * 12} for i in range(1, 9)]}
    svg = diagrams.coverage_crossing(fake)
    ET.fromstring(svg.replace("&#36;", "$").replace("&#8217;", "'"))
    plain = svg.replace("&#36;", "$")
    assert "12.34B" in plain and "42 screened" in plain
    assert "rank 4" in plain and "20991231" in plain
    # nothing from the real Taiwan figures leaked through
    assert "7.22" not in plain and "398" not in plain


def test_the_play_the_walk_animation_is_gone():
    """c-278. It accumulated FULL market cap over the top 40
    names — the right sort order but the wrong measure, since
    the coverage test accumulates FLOAT. Step 4 now shows the
    real crossing on real float, so the animation was the less
    accurate of two pictures of one thing."""
    src = (ROOT / "views" / "walkthrough.py").read_text(
        encoding="utf-8")
    assert "_walk_animation" not in src
    assert "Play the walk" not in src


def test_the_masthead_is_gone(at):
    """c-278. The standfirst, the MKT/REVIEW/PRICE-CUTOFF strip
    and four stat cards filled the screen above step 1 with
    numbers that all appear again where they are derived — the
    floor and bar are cards 5 and 6 of the step-3 ladder, the
    price cutoff is on the step-2 timeline."""
    md = " ".join(str(m.value) for m in at.markdown)
    for gone in ("Four times a year MSCI reshuffles",
                 "PRICE CUTOFF", "Steps in the method",
                 "below this, MSCI cuts", "called in advance"):
        assert gone not in md, gone
    assert "# Predict MSCI Index Changes" in md or \
        "Predict MSCI Index Changes" in md


def test_card_four_gets_the_arguments_it_prints():
    """c-283, THE BUG BILL SPOTTED ON SCREEN.

    Card 4 printed "the factsheet gives the index $0B of free
    float ... the —th company". Nothing was wrong with the
    card: `pub_idx` and `cross_rank` were never passed, so
    `(pub_idx or 0)` formatted a zero and `cross_rank or '—'`
    formatted a dash. Both values were sitting in
    `story()["crossing"]` one dictionary away.

    A default that formats cleanly is worse than one that
    raises — this rendered as a confident, wrong sentence for
    several revisions. So the test asserts the WIRING, not just
    that the figure draws.
    """
    import re
    import walkthrough_story as WS
    from views import diagrams as D
    s = WS.story()
    k, cr = s["keys"], s["crossing"]
    svg = D.size_ladder(
        dm_ref=k["gmsr_dm"], em_ref=k["em_ref"],
        lo=k["em_range"][0], hi=k["em_range"][1],
        cutoff=k["cutoff"], lower=k["floor"], upper=k["bar"],
        min_float=k["min_float_cap"],
        pub_dm=s["published"]["dm"],
        pub_asof=s["published"]["asof"],
        pub_idx=cr["target_busd"],
        cross_rank=cr["crossing_rank"]).replace("&#36;", "$")
    assert "$0B" not in svg
    assert "—th" not in svg
    # c-299: the rank left the CARD at Bill's request ("reached
    # sets the cutoff." now ends it) and lives in the Calculation
    # box instead. The assertion follows it rather than being
    # deleted — the point of this test is that `pub_idx` and
    # `cross_rank` REACH the renderer, and the calc text is where
    # that is now visible.
    calc = " ".join(c for _n, _nm, _v, c in D.size_ladder_steps(
        dm_ref=k["gmsr_dm"], em_ref=k["em_ref"],
        lo=k["em_range"][0], hi=k["em_range"][1],
        cutoff=k["cutoff"], lower=k["floor"], upper=k["bar"],
        min_float=k["min_float_cap"],
        pub_dm=s["published"]["dm"],
        pub_asof=s["published"]["asof"],
        pub_idx=cr["target_busd"],
        coverage=cr.get("coverage", 0.85),
        screened=cr.get("screened"),
        cross_rank=cr["crossing_rank"])).replace("&#36;", "$")
    assert f"{cr['crossing_rank']}th company" in calc, calc[:300]
    assert "$0B" not in calc
    assert "—th" not in calc
    # and the view must actually pass them
    src = (ROOT / "views" / "walkthrough.py").read_text(
        encoding="utf-8")
    assert "pub_idx=cr.get(\"target_busd\")" in src
    assert "cross_rank=cr.get(\"crossing_rank\")" in src


def test_the_ladder_cards_are_evenly_spaced():
    """c-283, Bill: *"Make each box of sub step 1-7 same
    distance from each other."* Three different gaps — 32 in
    the chain, 26 at the join, 24 in the branch — read as three
    different relationships when there is only one."""
    import re
    import walkthrough_story as WS
    from views import diagrams as D
    s = WS.story()
    k, cr = s["keys"], s["crossing"]
    svg = D.size_ladder(
        dm_ref=k["gmsr_dm"], em_ref=k["em_ref"],
        lo=k["em_range"][0], hi=k["em_range"][1],
        cutoff=k["cutoff"], lower=k["floor"], upper=k["bar"],
        min_float=k["min_float_cap"],
        pub_idx=cr["target_busd"],
        cross_rank=cr["crossing_rank"])
    # c-298: the width is NOT hardcoded any more. It used to be
    # `width="330"`, so when the cards were sized to their text
    # the regex matched nothing and the test failed with "0 == 7"
    # — a spacing test broken by a width change it does not care
    # about. Capture the width instead and assert the seven cards
    # AGREE on it, which is the thing worth pinning.
    cards = [(y, w, h) for y, w, h in re.findall(
        r'<rect x="0" y="([0-9.]+)" width="([0-9.]+)" '
        r'height="([0-9.]+)"', svg)
        # each card draws a 3px accent stripe at the same x and
        # y as its body. The old `width="330"` filter excluded
        # those by accident; relaxing it caught 14 rects, so the
        # exclusion is now deliberate.
        if float(w) > 10]
    assert len(cards) == 7, len(cards)
    assert len({w for _y, w, _h in cards}) == 1, \
        f"cards disagree on width: {sorted({w for _y, w, _h in cards})}"
    cards = [(y, h) for y, _w, h in cards]
    gaps, prev = [], None
    for y, h in cards:
        y, h = float(y), float(h)
        if prev is not None:
            gaps.append(round(y - prev))
        prev = y + h
    assert len(set(gaps)) == 1, gaps
    assert gaps[0] == 32, gaps


def test_the_calculation_lives_in_a_dropdown_not_the_cards():
    """c-283. The cards carry the plain reason; the sums moved
    to a "Calculation" expander. Both come from the SAME call
    arguments, so a card cannot show one number while the
    working shows another — which is the failure a separate
    hand-written table would invite."""
    import walkthrough_story as WS
    from views import diagrams as D
    s = WS.story()
    k, cr = s["keys"], s["crossing"]
    args = dict(
        dm_ref=k["gmsr_dm"], em_ref=k["em_ref"],
        lo=k["em_range"][0], hi=k["em_range"][1],
        cutoff=k["cutoff"], lower=k["floor"], upper=k["bar"],
        min_float=k["min_float_cap"],
        pub_dm=s["published"]["dm"],
        pub_asof=s["published"]["asof"],
        pub_idx=cr["target_busd"],
        cross_rank=cr["crossing_rank"])
    svg = D.size_ladder(**args).replace("&#36;", "$")
    calc = D.size_ladder_calc(**args).replace("&#36;", "$")
    # the arithmetic is OUT of the drawing
    for sign in (" x 2/3", " x 1.5", " x 0.5", " x 50%"):
        assert sign not in svg, sign
        assert sign in calc, sign
    # every threshold appears in the working, with its value
    for v in (k["gmsr_dm"], k["em_ref"], k["floor"], k["bar"],
              k["cutoff"], k["min_float_cap"]):
        assert f"${v}B" in calc, v
    assert "How it is computed" in calc


def test_the_ordinal_is_english():
    """"61th" is the kind of thing a client notices instead of
    the number."""
    from views import diagrams as D
    for n, want in ((69, "69th"), (1, "1st"), (2, "2nd"),
                    (3, "3rd"), (11, "11th"), (12, "12th"),
                    (13, "13th"), (21, "21st"), (61, "61st")):
        assert D._ordinal(n) == want, (n, D._ordinal(n))
    assert D._ordinal(None) == "—"


# ── c-318: the step-4 scan hover ─────────────────────────────────────

def _scan_fig(monkeypatch):
    """Build step 4's figure and hand it back, without Streamlit."""
    import sys as _s
    _s.path.insert(0, str(ROOT / "scripts"))
    from views import design, walkthrough as W
    from walkthrough_story import story
    caught = []
    monkeypatch.setattr(design, "chart",
                        lambda fig, **k: caught.append(fig))
    import streamlit as _st
    monkeypatch.setattr(_st, "caption", lambda *a, **k: None)
    s = story("Taiwan", REVIEW_FOR_TEST)
    W._scan_chart(s["scan"], s["keys"])
    return caught[-1], s


REVIEW_FOR_TEST = "Aug26"


def test_every_scan_dot_names_its_company(monkeypatch):
    """c-318, and this is the bug behind Bill asking for the hover
    twice. All eight ADDITION rows in aug26_call_v2.json carry
    `"name": ""` — the deletions have names, the additions do not
    — so the tooltip showed a bare code on exactly the dots a
    reader wants to identify. Indistinguishable from no tooltip.
    """
    fig, _s = _scan_fig(monkeypatch)
    rows = [r for tr in fig.data for r in list(tr.customdata or [])]
    assert len(rows) >= 20, len(rows)
    bare = [r[0] for r in rows if str(r[0]).strip().isdigit()]
    assert not bare, f"dots showing only a code: {bare}"
    for r in rows:
        assert "(" in r[0] and ")" in r[0], r[0]


def test_the_name_lookup_does_not_swallow_its_own_faults():
    """The deeper c-318 lesson. The first `_names` caught bare
    `Exception`, and this module does not import json — so
    `json.loads` raised NameError, the handler ate it, and the
    function returned {} forever. A broad except turned a code
    fault into a plausible empty result.
    """
    import inspect
    from views import walkthrough as W
    src = inspect.getsource(W._names)
    assert "except (OSError, ValueError)" in src
    assert "except Exception" not in src
    assert len(W._names(W._src_stamp())) > 500


def test_the_scan_hover_carries_cap_and_verdict(monkeypatch):
    """Bill asked for name and market cap; the verdict is what
    makes a hollow marker legible, so it travels too."""
    fig, _s = _scan_fig(monkeypatch)
    for tr in fig.data:
        ht = tr.hovertemplate or ""
        assert "%{customdata[0]}" in ht        # name (code)
        assert "full market cap" in ht
        assert "the cutoff" in ht
        assert "%{x}" not in ht, ht
    rows = [r for tr in fig.data for r in list(tr.customdata or [])]
    for r in rows:
        assert r[1] > 0                        # cap in US$bn
        assert r[3] and r[3] != "—"            # verdict


def test_the_scan_is_drawn_on_real_taiwan_market_caps(monkeypatch):
    """Bill's question. The x-axis is not a schematic — every dot
    is a real company's full market capitalisation, and it must
    tie to the registered call file rather than be recomputed
    here."""
    fig, s = _scan_fig(monkeypatch)
    plotted = sorted(round(r[1], 2) for tr in fig.data
                     for r in list(tr.customdata or []))
    filed = sorted(round(r["cap_usd_b"], 2)
                   for side in ("adds", "deletes")
                   for r in s["scan"][side])
    assert plotted == filed
    assert fig.layout.xaxis.type == "log"


def test_threshold_labels_have_room_to_render(monkeypatch):
    """c-318, Bill: *"we can't see the full text."* A vline
    annotation at position 'top' is drawn ABOVE the plot area and
    plotly does not grow the margin to fit it — so a 10px top
    margin clipped the label. Both figures on this page carry
    top-anchored threshold labels."""
    fig, _s = _scan_fig(monkeypatch)
    texts = [a.text for a in (fig.layout.annotations or [])]
    assert len(texts) == 3, texts
    assert any("market cutoff" in t for t in texts)
    # c-331: the labels moved OUT of the plot area entirely and
    # are now three lines deep, so the margin has to be much
    # bigger than the old 40.
    assert fig.layout.margin.t >= 100, fig.layout.margin.t
    # c-324: a bare "$" is safe HERE. The LaTeX trap is
    # Streamlit's markdown pass; a plotly annotation is SVG text
    # and never goes through it. The rule still binds on captions
    # and prose, which is where it was learned.
    for t in texts:
        assert t.startswith("<b>$"), t


def test_threshold_labels_are_placed_in_log_space(monkeypatch):
    """c-331, Bill, twice: *"the labels are not aligned with the
    vertical lines."*

    THE CAUSE WAS THE AXIS TYPE, not the anchor. This x axis is
    `type="log"`, where an annotation's x coordinate means the
    EXPONENT — x=7.22 is 10^7.22, not 7.22. `add_vline` converts
    for the shape and not for its annotation, so every label was
    placed astronomically off-scale and clamped to the plot edge,
    which is why it looked like a right-shift and why zooming
    moved it.

    So each label's x must equal log10 of the threshold it names.
    This asserts the arithmetic, because "it looks right now" is
    what the first fix also claimed."""
    import math
    fig, s = _scan_fig(monkeypatch)
    k = s["keys"]
    want = sorted(math.log10(v) for v in
                  (k["floor"], k["cutoff"], k["bar"]))
    got = sorted(a.x for a in (fig.layout.annotations or []))
    assert len(got) == 3
    for g, w in zip(got, want):
        assert abs(g - w) < 1e-9, (got, want)
    # and they must sit above the plot, in paper coordinates
    for a in fig.layout.annotations:
        assert a.yref == "paper" and a.y >= 1.0
        assert a.xanchor == "center"


# ── c-320: the scan verdicts, and the threshold frame ────────────────

def test_scan_verdicts_use_this_pages_thresholds_not_the_files(
        monkeypatch):
    """c-320, Bill: *"You mislabel 3189 as 'qualified', it's only
    1.43x the cutoff and should not be added."* He is right, and
    the cause was not a label.

    The verdicts stored in aug26_call_v2.json were computed at
    that file's own thresholds — cutoff 6.74, addition bar 10.11 —
    which this project superseded when the buffers were re-based
    onto Taiwan's own Market Size-Segment Cutoff (7.22, bar
    10.83). The chart drew its LINES at the corrected frame and
    its DOTS at the old one, so 3189 Kinsus at USD 10.30bn showed
    as QUALIFIES while sitting below the line drawn beside it —
    and while being absent from the registered call on the same
    page.
    """
    fig, s = _scan_fig(monkeypatch)
    k = s["keys"]
    rows = [r for tr in fig.data for r in list(tr.customdata or [])]
    by_code = {r[0].split("(")[-1].rstrip(")"): r for r in rows}
    kin = by_code["3189"]
    assert kin[1] < k["bar"], kin
    assert "below the addition bar" in kin[3], kin[3]
    assert "clears every screen" not in kin[3]
    # and the chart now agrees with the registered call
    qualifies = {c for c, r in by_code.items()
                 if r[3] == "clears every screen"}
    called = {str(x["code"]) for x in s["call"]["calls"]
              if x["action"] == "ADD"}
    assert qualifies == called, (qualifies, called)


def test_a_failure_names_the_direction_it_failed_in(monkeypatch):
    """The second half of c-320. "blocked: above upper buffer" was
    the GATE'S NAME printed as the failure reason, so a name BELOW
    the bar was described as blocked for being above it. Bill:
    *"the reason should be 'below upper buffer', do you agree?"*
    """
    fig, s = _scan_fig(monkeypatch)
    k = s["keys"]
    for tr in fig.data:
        for r in list(tr.customdata or []):
            cap, why = r[1], r[3]
            if "below the addition bar" in why:
                assert cap < k["bar"], r
            if why == "clears every screen":
                assert cap >= k["bar"], r
            if "below the deletion floor" in why:
                assert cap < k["floor"], r
    codes = {r[0].split("(")[-1].rstrip(")"): r[3]
             for tr in fig.data for r in list(tr.customdata or [])}
    for c in ("6770", "2337"):
        assert "below" in codes[c], (c, codes[c])
        assert "above" not in codes[c], (c, codes[c])


def test_hollow_is_disambiguated_into_two_failures(monkeypatch):
    """Bill: *"hollow is ambiguous, it can mean blocked for
    additional failed screens, or blocked for failing the size
    screen."* One marker was carrying two verdicts."""
    fig, _s = _scan_fig(monkeypatch)
    names = {t.name for t in fig.data}
    assert "clears every screen" in names
    # c-353 shortened these labels — the legend was wrapping to a
    # second row and colliding with the plot. WHAT MATTERS IS THE
    # DISTINCTION, not the wording: a name that clears the size
    # screen and fails another must not look like a name that
    # fails on size. So the test now pins the two entries by the
    # half they disagree about, and by their symbols.
    assert any("fails another screen" in n for n in names)
    assert any("fails on size" in n for n in names)
    sym = {t.name: t.marker.symbol for t in fig.data}
    gate = next(v for k, v in sym.items()
                if "fails another screen" in k)
    size = next(v for k, v in sym.items() if "fails on size" in k)
    assert gate != size, (gate, size)
    # and the legend must stay narrow enough to sit on one row,
    # which is the actual fix — a wider label set re-creates the
    # collision no matter where the legend is anchored
    assert sum(len(n) for n in names) < 110, names
    assert fig.layout.legend.yref == "container", (
        "a plot-area anchored legend drifts with the lane count")


def test_the_five_per_cent_band_is_drawn_and_flags_phison(
        monkeypatch):
    """c-320, Bill asked for a ±5% band on the derived cutoff. The
    cutoff is not published by MSCI — it is an 85% coverage walk
    over an estimated float stack — so a verdict that flips inside
    that band rests on arithmetic rather than evidence."""
    from views import walkthrough as W
    fig, s = _scan_fig(monkeypatch)
    assert W.BAND == 0.05
    shapes = [sh for sh in (fig.layout.shapes or [])
              if sh.type == "rect"]
    # two zone shadings plus a band on each BUFFER. c-324 removed
    # the band from the market cutoff, so four, not five.
    assert len(shapes) == 4, [sh.x0 for sh in shapes]
    # c-322: the robustness column left the tooltip, so the flip
    # is asserted against the thresholds directly — which is the
    # thing the tooltip was only reporting anyway.
    k = s["keys"]
    caps = {r[0].split("(")[-1].rstrip(")"): r[1]
            for tr in fig.data for r in list(tr.customdata or [])}
    assert caps["8299"] < k["bar"] * (1 + W.BAND), caps["8299"]
    assert caps["8299"] >= k["bar"], "Phison should clear the bar"
    for c in ("2408", "8046", "2344"):
        assert caps[c] >= k["bar"] * (1 + W.BAND), c


def test_step_five_shows_the_result_and_not_a_second_chart(at):
    """c-320, Bill: *"I want to delete the bar graph for step 5.
    In this step 5, we just show the prediction result."* The bar
    chart drew the same comparison step 4's scan makes, on the
    same thresholds — two figures answering one question is how
    they drift apart."""
    from views import walkthrough as W
    assert not hasattr(W, "_lever"), "_lever is still defined"
    md = " ".join(str(m.value) for m in at.markdown)
    assert "Index Review Prediction" not in md
    # the call rows carry a market cap, not a percentage
    assert "USD 34.37bn" in md or "USD 34.48bn" in md
    assert "The companies selected for index review change" in md


# ── c-322: the band, the carried list, and the reasoning ─────────────

def test_the_band_edges_are_on_the_floor_and_bar_labels(monkeypatch):
    """c-322, Bill: the floor and the bar show the ±5% threshold
    in the label. The cutoff keeps a bare one — it is the
    reference the other two derive from, and three multi-part
    annotations on one axis is a wall."""
    from views import walkthrough as W
    fig, s = _scan_fig(monkeypatch)
    k = s["keys"]
    texts = {a.text for a in (fig.layout.annotations or [])}
    lo_lab = next(t for t in texts if "lower buffer" in t)
    hi_lab = next(t for t in texts if "upper buffer" in t)
    cut_lab = next(t for t in texts if "market cutoff" in t)
    for lab, v in ((lo_lab, k["floor"]), (hi_lab, k["bar"])):
        assert f"{v * (1 - W.BAND):.2f}" in lab, lab
        assert f"{v * (1 + W.BAND):.2f}" in lab, lab
    # c-324, Bill: NO band on the market cutoff. The ±5% is an
    # error bar on the cutoff CALCULATION and both buffers are
    # derived from it, so banding the cutoff too would show one
    # uncertainty three times.
    assert "(" not in cut_lab, cut_lab
    rects = [sh for sh in (fig.layout.shapes or [])
             if sh.type == "rect"]
    for sh in rects:
        mid = (sh.x0 + sh.x1) / 2
        assert abs(mid - k["cutoff"]) > 0.01, (
            "the market cutoff still has a band")


def test_the_hover_drops_the_robustness_row(monkeypatch):
    """Bill asked for the last row off every tooltip. The shaded
    band carries that information without a hover, and the reason
    text in step 5 carries it in words."""
    fig, _s = _scan_fig(monkeypatch)
    for tr in fig.data:
        ht = tr.hovertemplate or ""
        assert "FLIPS" not in ht
        assert "holds across" not in ht
        assert "%{customdata[4]}" not in ht
        for row in list(tr.customdata or []):
            assert len(row) == 4, row


def test_the_caption_is_about_the_band_only(at):
    """Asserted on what RENDERS, not on the source. A Python
    string split across lines does not appear in the file as the
    reader sees it, and a source grep would have passed on the
    old caption too."""
    caps = " ".join(str(c.value) for c in at.caption)
    assert "**Note:**" in caps, "the Note prefix is not bold"
    assert "shaded band on the addition bar and the deletion" in caps
    assert "±5%" in caps
    assert "error in the cutoff-value calculation" in caps
    assert "Filled = clears every screen" not in caps


def test_the_table_reports_all_four_adds_and_the_border_del(at):
    """c-358, Bill: PHISON GOES BACK IN — the table reports what
    the screens produced, four additions, and confidence lives in
    the probability model rather than in a smaller table. c-322's
    "not carried" hedge sentence is gone with it.

    AND THE SAME STANDARD RUNS ON THE DELETION SIDE. A member
    above the floor but inside its +5% band is the mirror image
    of Phison at the addition bar, so it joins the Deletions
    table as band-borderline — one rule, both directions."""
    md = " ".join(str(m.value) for m in at.markdown)
    assert "**Additions (4)**" in md
    rows = re.findall(r"dcode'>(\d{4})</span>", md)
    assert "8299" in rows, "Phison must be in the table"
    # the hedge sentence must be gone
    assert "not carried as a confident addition" not in md
    assert "However, Phison" not in md
    # the deletion side carries the band-borderline member(s)
    m_del = re.search(r"\*\*Deletions \((\d+)\)", md)
    assert m_del and int(m_del.group(1)) >= 1, "no deletion rows"
    assert "band-borderline deletion" in md
    # and the borderline member really is inside the band —
    # re-derived from the scan, not trusted from the view
    import walkthrough_story as W
    from views.walkthrough import REVIEW as _REV
    s_ = W.story("Taiwan", _REV)
    k = s_["keys"]
    border = [r for r in s_["scan"]["deletes"]
              if r.get("cap_usd_b") is not None
              and k["floor"] <= r["cap_usd_b"]
              < k["floor"] * 1.05]
    assert border, "no member inside the floor band in the scan"
    for r in border:
        assert str(r["code"]) in rows, r["code"]


def test_the_screen_results_moved_behind_a_click(at):
    """c-358, Bill: the five whys move from an always-open amber
    block into an expander shaped like Rulebook References. Five
    screen results are reference material — a reader checks the
    one name they care about."""
    labs = [e.label for e in at.expander]
    assert any("Screen Results" in x for x in labs), labs
    md = " ".join(str(m.value) for m in at.markdown)
    # every call's why is inside it, including the generated
    # border-deletion why
    for code in ("2408", "8046", "2344", "8299"):
        assert f"({code}) — ADD" in md, code
    assert ") — DEL" in md
    assert "deletion floor by" in md


def test_the_reasoning_is_not_hidden_behind_a_click(at):
    """Bill moved the reasoning out of the collapsed expander and
    into the amber block. A reason a reader has to click for is a
    reason most readers never see."""
    src = (ROOT / "views" / "walkthrough.py").read_text(
        encoding="utf-8")
    assert 'st.expander("Reason for Addition / Deletion")' not in src
    assert "Calls that survive" not in src
    md = " ".join(str(m.value) for m in at.markdown)
    for code in ("2408", "8046", "2344", "8299"):
        assert f"({code})" in md, code


def test_the_border_deletion_why_is_generated_not_typed():
    """c-358 replaced the Phison band sentence with a generated
    why on band-borderline DELETIONS. Same rule as before: the
    text must name no company, so it attaches to whichever member
    is inside the floor band after a re-run rather than to
    Caliway forever."""
    src = (ROOT / "views" / "walkthrough.py").read_text(
        encoding="utf-8")
    # the sentence may survive in COMMENTS (provenance); it must
    # not survive in a string that can reach the screen
    live = "\n".join(l for l in src.split("\n")
                     if not l.lstrip().startswith("#"))
    assert "not carried as a confident" not in live
    i = src.index("for b in _border_dels:")
    block = src[i:src.index("if body:", i)]
    assert "Caliway" not in block and "6919" not in block
    assert "deletion floor" in block
    assert '_k["floor"] <= r["cap_usd_b"]' in src
