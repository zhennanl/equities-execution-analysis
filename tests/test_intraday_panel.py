"""The 5-minute panel (c-288).

The page asks questions the daily panel structurally cannot,
so the things worth pinning are the ones that make an intraday
number trustworthy: that the closing bar is the closing bar,
that the benchmark is the name's own ordinary days, and that a
thin market is not quoted as though it were a finding.
"""
import json
import sys
import warnings
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
warnings.filterwarnings("ignore")

SRC = ROOT / "data" / "ib_5m_analysis.json"

APP = """
import sys
sys.path.insert(0, ".")
from views import intraday_panel
intraday_panel.render()
"""


@pytest.fixture(scope="module")
def at():
    pytest.importorskip("streamlit")
    if not SRC.exists():
        pytest.skip("intraday panel not built")
    from streamlit.testing.v1 import AppTest
    a = AppTest.from_string(APP, default_timeout=300)
    a.run()
    return a


@pytest.fixture(scope="module")
def data():
    if not SRC.exists():
        pytest.skip("intraday panel not built")
    return json.loads(SRC.read_text(encoding="utf-8"))


def test_page_renders(at):
    assert not at.exception, [str(e.value)[:400]
                              for e in at.exception]
    md = " ".join(str(m.value) for m in at.markdown)
    # c-293: four, not five — Bill deleted section 5.
    # c-319: seven, with the TWSE 5-second auction added.
    # c-323: FOUR. The page is Taiwan-only now and the two
    # 5-second prose blocks are deleted; what remains is the four
    # charts Bill kept for interpretability. The count is pinned
    # rather than loosened — a section that stops rendering
    # should fail here in either direction.
    # c-327: FIVE. A Data Review section leads, saying what the
    # dataset is and why it is only 43 events, before anything
    # drawn from it is shown.
    # c-368: SIX. The Two Sides of the Rebalance Trade — the
    # framing section with the two formulas both sides run on —
    # sits between the Data Review and the first chart.
    assert md.count("class='dsect") == 6
    assert "5-Minute Data Analysis" in md


def test_taiwan_is_not_four_events_any_more(data):
    """c-288, Bill: *"Why Taiwan only has 4 event windows?"*

    Nothing was wrong with the bars. 43 of Taiwan's 47 priced
    windows carried no `eff` field, so the analysis could not
    locate the print and dropped every one. The harvester
    computed a date span and did not store what the dates
    MEANT.

    They were recovered from the daily event-window file on the
    identical `rev|code` key — 43 of 43 matched — rather than
    by re-fetching 47 windows of bars to recover two strings
    each. And the answer moved: Taiwan's closing-bar share went
    from a 4-event curiosity to 79% on 43 events.
    """
    tw = data["markets"].get("Taiwan")
    assert tw and tw["n"] >= 40, tw["n"] if tw else None
    assert tw["close_share_eff"]["p50"] > 0.5


def test_the_closing_bar_is_never_an_empty_bar(data):
    """c-286. IB emits a bar for every slot in the session
    template, so a market can end with a zero-volume bar after
    the auction. Measuring THAT as the close once reported
    Singapore at 0.0% when its auction is the largest bar of
    the day. A closing share of exactly zero is the signature
    of that bug returning."""
    for m, s in data["markets"].items():
        d = s.get("close_share_eff")
        if d:
            assert d["p50"] > 0, m


def test_the_benchmark_is_the_name_itself(data):
    """Every event carries its OWN control shape. Comparing an
    effective day with a market average would make a thinly
    traded name look concentrated purely because the market's
    typical name is not."""
    for r in data["events"][:200]:
        assert r.get("ctrl_shape"), r["code"]
        assert len(r["ctrl_shape"]) == len(r["eff_shape"])
        assert r["control_days"] >= 5


def test_the_data_review_states_the_ibkr_history_limit(at):
    """c-327, Bill: say why the panel is this small. IB's Taiwanese
    5-minute history does not reach past about May 2023, and that
    limit — not a harvesting choice — is what caps the sample at
    43 events. A reader who does not know that reads 43 as
    carelessness."""
    md = " ".join(str(m.value) for m in at.markdown)
    assert "Data Review" in md
    assert "Interactive Brokers" in md
    assert "2023" in md
    assert "5-minute history" in md
    # c-331, Bill cut the "what that costs" paragraph, so the
    # RECENT-REGIME wording is no longer on the page. The PERIOD
    # and its CAUSE still have to be, because without them 43
    # events reads as carelessness rather than as a hard limit.
    assert "May 2023" in md


def test_the_page_shows_taiwan_alone(at):
    """c-323 REPLACED `test_thin_markets_are_left_out_of_the_vwap
    _table`. That test guarded a cross-market table which had a
    minimum-n rule so a market with six events could not sit
    beside one with two hundred. The page is one market now, so
    the rule has nothing to exclude — and the risk it was
    guarding against has moved: the danger is no longer a thin
    market on the table, it is a market OTHER than Taiwan on it
    at all.
    """
    md = " ".join(str(m.value) for m in at.markdown)
    assert "Taiwan" in md
    import re
    labels = re.findall(r"<td[^>]*>([A-Z][a-z]+(?: Kong)?)</td>",
                        md)
    for bad in ("Japan", "Korea", "Australia", "China", "India",
                "Singapore", "Hong Kong"):
        assert bad not in labels, f"{bad} is a data label"


def test_the_auction_sections_reach_the_screen(at):
    """c-319 added three sections built on TWSE's own 5-second
    file; c-323 cut two of them. The one that remains carries the
    eleven-year Taiwanese close, and a page that silently drops it
    is back to three graphs off 43 windows.

    The deleted blocks are not lost — the review-type split and
    the column-identification limits live in
    docs/TW_AUCTION_MICROSTRUCTURE.md and are asserted by
    test_tw_auction_microstructure.py."""
    md = " ".join(str(m.value) for m in at.markdown)
    assert "How Much Volume the Close Can Absorb" in md
    for gone in ("The Review Type Is a Capacity Input",
                 "What the 5-Second File Cannot Tell You"):
        assert gone not in md, gone


def test_the_market_wide_limitation_is_recorded_off_page(at):
    """c-329, Bill: the prose under the auction chart is deleted,
    so the venue-versus-name distinction is no longer ON the page.

    THE TEST DID NOT BECOME POINTLESS — it moved. The claim still
    has to exist somewhere a reader can reach, and the guard now
    asserts the doc carries it. What must NOT happen is the page
    asserting a per-name capacity it never measured, so the
    negative half of the check stays on the rendered output."""
    doc = (ROOT / "docs" / "TW_AUCTION_MICROSTRUCTURE.md")
    if not doc.exists():
        pytest.skip("run scripts/tw_auction_microstructure.py")
    t = doc.read_text(encoding="utf-8")
    assert "market-wide" in t.lower()
    md = " ".join(str(m.value) for m in at.markdown)
    assert "per-name auction share" not in md, (
        "the page is claiming a per-name capacity that this file "
        "cannot measure")


def test_the_close_vs_vwap_section_is_split_by_side(at):
    """c-329, Bill: *"we need to categorize the data points based
    on addition and deletion... the theoretical price increase and
    decrease for add and deletion will cancel out each other."*

    He is right about the OVERNIGHT gap, which is a directional
    return and has no business being pooled. The cards must
    therefore carry a per-side figure, not one pooled median.

    The measured answer turned out to be more interesting than
    the hypothesis — both sides gap UP, so the pooled number was
    hiding a common market factor rather than a cancellation —
    and the page now says that. This guard is on the SPLIT, which
    is what makes the statement checkable either way."""
    md = " ".join(str(m.value) for m in at.markdown)
    assert "Next open · add" in md
    assert "Next open · delete" in md
    assert "Close vs VWAP · add" in md
    assert "Close vs VWAP · delete" in md
    # and the pooled overnight card must be gone, or a reader can
    # still take the number that averages two opposite predictions
    assert "from the close · n=43" not in md


def test_the_auction_error_bars_are_not_drawn_in_the_bar_colour(
        monkeypatch):
    """c-329, Bill: *"I don't see the bars and whiskers."* They
    were there — in the same colour as the bar they sat on, so
    the lower half was invisible inside the bar and the upper
    half was a hairline in the bar's own tint. A chart caption
    that promises whiskers has to produce visible ones.

    AppTest exposes markdown but not chart objects, so this
    renders the sections with design.chart intercepted and
    inspects the Figure directly. That is the only way to assert
    on a colour rather than on the string that sets it."""
    from views import design, intraday_panel
    figs = []
    monkeypatch.setattr(design, "chart", lambda f, **k: figs.append(f))
    intraday_panel.sections(1)
    bars = [tr for f in figs for tr in f.data
            if getattr(tr, "error_y", None) is not None
            and tr.error_y.array is not None]
    assert bars, "no error bars found at all"
    for tr in bars:
        assert tr.error_y.color == design.INK, (
            f"error bar drawn in {tr.error_y.color}; the bar's "
            f"own colour is {tr.marker.color}")
        assert tr.error_y.color != tr.marker.color


def test_the_box_traces_do_not_pop_a_fence_summary(monkeypatch):
    """c-331, Bill: *"remove the lower and upper fence popup."*

    Plotly boxes default to hoveron="points+boxes", which shows a
    seven-line summary including Tukey fences at q1-1.5*IQR and
    q3+1.5*IQR. This page never computes outliers that way and
    never explains the term, so the box tooltip was stating a
    statistic the page does not stand behind."""
    from views import design, intraday_panel
    figs = []
    monkeypatch.setattr(design, "chart", lambda f, **k: figs.append(f))
    intraday_panel.sections(1)
    boxes = [tr for f in figs for tr in f.data
             if tr.type == "box"]
    assert boxes, "the close-vs-VWAP boxes are gone"
    for tr in boxes:
        assert tr.hoveron == "points", tr.name


def test_the_close_vs_vwap_conclusion_is_not_the_circular_one(at):
    """c-331. The old conclusion said the dislocation "is small,
    and that is the finding". It is not entitled to: an index
    mover puts ~79% of its effective-day volume through the same
    auction, so close-vs-VWAP compares the print against a
    benchmark it mostly sets and is pulled toward zero either way.

    scripts/tw_auction_impact.py reproduces the measured -0.06%
    by scaling for that dilution, which is what makes the
    circularity a demonstrated mechanism rather than a worry. The
    page must therefore state the caveat and give the
    uncorrelated measurement, not the comfortable reading."""
    md = " ".join(str(m.value) for m in at.markdown)
    # c-340 shortened the clause again. What must survive every
    # rewording is the MECHANISM — that the auction is most of
    # the volume the VWAP is built from, which is the one thing
    # a reader cannot recover from the four cards. The specific
    # phrasing is Bill's to choose; the causal link is not.
    assert "79%" in md and "same auction" in md, (
        "the circularity mechanism is no longer stated")
    assert "pulls the gap between close and VWAP toward zero" in md
    # c-332, Bill shortened this to four sentences, so the
    # 13:20 measurement moved OFF the page into
    # docs/TW_AUCTION_IMPACT.md. The caveat itself must stay,
    # because it is the one thing a reader cannot infer from the
    # four cards — and the old comfortable headline must not
    # creep back in its place.
    assert "and that is the finding" not in md
    assert "absorbing an order worth many times" not in md
    assert (ROOT / "docs" / "TW_AUCTION_IMPACT.md").exists(), (
        "the measurement this caveat points at is gone")


def test_every_tooltip_uses_the_shared_hover_card(monkeypatch):
    """c-333, Bill: *"the popup window ... looks very plain, and
    easy to lose audience."*

    The fix is a single builder, design.hover(), not a nicer
    string per chart — the hoverlabel STYLE has lived in one
    place since c-282 and the CONTENT drifting chart by chart is
    what made the tooltips look unrelated to each other.

    A plotly tooltip is SVG: it supports <b>, <i>, <br> and
    <span style="color:...;font-size:...">, and it does not
    support radius, shadow, padding or letter-spacing. So the
    hierarchy is built from weight, colour and size, and this
    asserts the parts of it that identify the card."""
    from views import design, intraday_panel
    figs = []
    monkeypatch.setattr(design, "chart", lambda f, **k: figs.append(f))
    intraday_panel.sections(1)
    tips = [tr.hovertemplate for f in figs for tr in f.data
            if getattr(tr, "hovertemplate", None)]
    assert tips, "no tooltips at all"
    # c-340, Bill: the close-share scatter is no longer
    # exempt. c-334 had carved it out; he compared both and
    # chose ONE treatment, so EVERY tooltip on this page must
    # carry the card — no exceptions list to drift out of date.
    assert len(tips) >= 5, "the sweep did not reach every chart"
    for t in tips:
        assert design.INK in t, "no ink title"
        assert design.NAVY in t, "values are not the accent colour"
        assert design.FAINT in t, "no muted eyebrow"
        assert t.endswith("<extra></extra>"), (
            "plotly's unstyleable second box is still showing")
        # the hairline that separates title from body
        assert "─" in t
