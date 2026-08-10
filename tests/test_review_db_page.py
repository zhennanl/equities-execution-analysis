"""The MSCI Index Review Database page actually renders
(c-203).

Every other test on this page parses the source or calls a
helper. None of them execute `render()`, so a broken f-string
in the HTML, a missing DataFrame column, or a market whose
data shape differs would all ship green. These drive the real
Streamlit script and assert on what reaches the browser.

Slow-ish (a few seconds per market), which is why only a
representative spread is exercised: the largest market, the
smallest, and one with a different ticker shape.
"""
import re
import sys
import warnings
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

warnings.filterwarnings("ignore")

APP = """
import sys
sys.path.insert(0, ".")
from views import history_explorer
history_explorer.render()
"""


def _real_streamlit():
    """Undo any stub another test installed.

    c-203: several tests import views.* without a display by
    putting a bare ModuleType into sys.modules["streamlit"].
    That is fine for them and fatal here — `streamlit.testing`
    cannot be imported from a stub, and the failure only shows
    when the whole suite runs in one process, i.e. exactly when
    nobody is watching. Rather than depend on file order, drop
    the stub and every module that imported it, then let the
    real package load.
    """
    mod = sys.modules.get("streamlit")
    if mod is not None and getattr(mod, "__file__", None):
        return                                # already real
    for name in [n for n in sys.modules
                 if n == "streamlit"
                 or n.startswith("streamlit.")
                 or n.startswith("views")]:
        del sys.modules[name]


@pytest.fixture(scope="module")
def at():
    _real_streamlit()
    pytest.importorskip("streamlit")
    from streamlit.testing.v1 import AppTest
    if not (ROOT / "data" / "msci_changes_db.pkl").exists():
        pytest.skip("changes DB unavailable")
    a = AppTest.from_string(APP, default_timeout=240)
    a.run()
    return a


def test_page_renders_without_exceptions(at):
    assert not at.exception, [e.value[:300] for e in at.exception]


def test_status_strip_and_sections_are_present(at):
    """c-207 replaced the gradient hero with a status strip.

    A desk reader must be able to answer "what am I looking at
    and is it current?" without scrolling, so market, span, row
    count and last review sit above everything.
    """
    md = " ".join(str(m.value) for m in at.markdown)
    assert "dstrip" in md, "the status strip did not render"
    assert md.count("dsect") >= 5, \
        "expected the numbered section rules"


def test_latest_review_names_lead_the_page(at):
    """c-203 put the most recent actual changes above the
    aggregates. Nobody arrives wanting a median."""
    md = " ".join(str(m.value) for m in at.markdown)
    assert "drow" in md, "no change rows rendered"
    assert "Addition" in md and "Deletion" in md


def test_add_and_delete_keep_their_colours(at):
    md = " ".join(str(m.value) for m in at.markdown)
    assert "dact add" in md or "dstat add" in md
    assert "dact del" in md or "dstat del" in md


def test_the_controls_exist(at):
    assert len(at.selectbox) >= 1
    assert len(at.radio) >= 1
    assert "Taiwan" in at.selectbox[0].options


def test_philippines_IS_offered_on_this_page(at):
    """c-220 REVERSED this test, and the reversal is the point.

    markets.py excludes the Philippines because there is no
    usable price source, so no market cap, no size screen, no
    prediction. That reason is about the FORWARD pipeline. This
    page makes no predictions — it reports what MSCI already
    did, and the Philippine review history is as complete as
    any other market's.

    Excluding it here applied a data-availability rule to a
    question that does not depend on the missing data.
    """
    assert "Philippines" in at.selectbox[0].options


def test_the_exclusion_still_governs_the_pipeline():
    """The page changed; markets.py did not."""
    import importlib
    sys.path.insert(0, str(ROOT / "scripts"))
    markets = importlib.import_module("markets")
    assert not markets.is_active("Philippines")
    assert "Philippines" not in markets.filter_markets(
        ["Taiwan", "Philippines", "Japan"])


@pytest.mark.parametrize("mkt", ["Japan", "NewZealand", "China"])
def test_other_markets_render(at, mkt):
    """NewZealand has 27 changes total and China has 1,431 with
    a different ticker shape — the two ends that break layout
    code."""
    at.selectbox[0].set_value(mkt).run()
    assert not at.exception, \
        f"{mkt}: {[e.value[:300] for e in at.exception]}"


@pytest.mark.parametrize("idx", [1, 2])
def test_review_type_filters_render(at, idx):
    at.radio[0].set_value(at.radio[0].options[idx]).run()
    assert not at.exception, [e.value[:300] for e in at.exception]


def test_the_snapshot_shows_every_name_not_the_first_eight(at):
    """c-233. The card capped each side at 8 and printed
    "+14 more" for China's May-2026 review. A snapshot whose
    job is to answer "which names" must not send the reader
    somewhere else to find out.
    """
    import re
    md = " ".join(str(m.value) for m in at.markdown)
    assert not re.search(r"\+\d+ more", md), \
        "the snapshot is still truncating a name list"


def _blocks(at, needle):
    """The markdown elements containing a given marker.

    c-235: the earlier version of this test globbed EVERY
    markdown element into one string and sliced it on
    "<div class='amk". That worked while section 1 was the only
    thing on the page emitting cards; when section 2's chart
    started emitting 82 of its own, the last strip cell's slice
    ran to the end of the document and swallowed all of them.
    The test failed on a real change that was not a regression,
    which is the most expensive kind of false alarm.
    """
    return [str(m.value) for m in at.markdown
            if needle in str(m.value)]


def test_every_strip_card_lists_as_many_names_as_it_counts(at):
    """The group heading carries a count; the rows under it must
    match. A count that disagrees with its own list is worse
    than either alone."""
    import re
    blocks = _blocks(at, "class='astrip'")
    assert blocks, "the section-1 strip did not render"
    cells = re.findall(
        r"<div class='amk[^']*'>(.*?)(?=<div class='amk|$)",
        blocks[0], re.S)
    checked = 0
    for c in cells:
        counts = [int(x) for x in
                  re.findall(r"class='pc'>(\d+)", c)]
        if not counts:
            continue
        assert c.count("class='pn'") == sum(counts), \
            re.search(r"class='mm'>([^<]+)", c)
        checked += 1
    assert checked >= 5, f"only {checked} cards had names"


def test_a_long_card_can_scroll(at):
    """46 names would run off the bottom of the screen."""
    md = " ".join(str(m.value) for m in at.markdown)
    assert "overflow-y:auto" in md
    assert "max-height:330px" in md


def test_the_history_chart_is_html_not_plotly(at):
    """c-235. Bill wanted a hover card that survives the mouse
    entering it, matches section 1, lists every name and carries
    a working link. Plotly's SVG tooltip can do none of the
    four, so the chart is HTML columns with CSS cards."""
    blocks = _blocks(at, "class='hgrid'")
    assert blocks, "the section-2 chart did not render as HTML"
    html = blocks[0]
    assert html.count("class='hcol") >= 40
    # the card is a CHILD of the column, which is what keeps
    # :hover alive when the pointer moves onto it
    assert ".hcol:hover .pop{display:block}" in html


def test_every_review_card_carries_its_msci_link(at):
    """The link is the reason this is HTML. One per column."""
    import re
    html = _blocks(at, "class='hgrid'")[0]
    cols = html.count("class='hcol")
    links = len(re.findall(r"class='pl' target='_blank'", html))
    assert links == cols, f"{links} links for {cols} columns"
    assert "MSCI_" in html and "_STPublicList.pdf" in html


def test_the_two_cards_share_one_stylesheet(at):
    """Bill asked for the chart card to look like the strip
    card. Two stylesheets that agree today will not agree in six
    months, so there is one."""
    import views.history_explorer as H
    assert ".pop .pg{" in H.POP_CSS
    assert ".pop .pl{" in H.POP_CSS
    strip = _blocks(at, "class='astrip'")[0]
    chart = _blocks(at, "class='hgrid'")[0]
    for rule in (".pop .pg{", ".pop .pn{", ".pop .ph{"):
        assert rule in strip and rule in chart, rule


def test_tables_sit_on_a_white_card(at):
    """DESIGN_DECISIONS D1. The page ground is PAPER; a table
    drawn straight onto it barely separates from the prose.
    Bill spotted this by noticing the one table inside an
    expander read better than the rest."""
    md = " ".join(str(m.value) for m in at.markdown)
    assert md.count("background:#fff;border:1px solid #e8ddd1"
                    ";border-radius:3px") >= 4


def _cards(at):
    """Every table card's own style string."""
    md = " ".join(str(m.value) for m in at.markdown)
    return [s for s in re.findall(r"<div style='([^']*)'>", md)
            if "background:#fff" in s]


def test_a_table_card_leaves_a_gap_before_the_next_element(at):
    """c-246. Bill: "leave a little extra space between the end
    of the table and the next element."

    This is c-244's shadow. Streamlit's `table{margin-bottom:
    1rem}` was producing a band INSIDE the card and a gap
    OUTSIDE it at the same time; killing it fixed the band and
    took the gap with it. The gap belongs outside the border,
    so the CARD carries it — putting it back on the table would
    land it on the white again."""
    cards = _cards(at)
    assert cards, "no table card rendered"
    for s in cards:
        assert "margin:0 0 1rem" in s, s


def test_a_height_limited_table_can_still_be_scrolled(at):
    """c-244. Bill: *"the scroll up and down side button is
    gone."* c-243 wrote `overflow-y:auto` and then a shorthand
    `overflow:hidden` into the SAME declaration block; the
    shorthand resets both axes, so section 3 became a 330px
    window onto a list nobody could move.

    The regression is invisible to a substring search — both
    strings were present and the old test asserted the one that
    broke it. So this asserts the RESOLVED value: whatever else
    a card says, a card with a max-height must end up scrollable
    on the y axis."""
    scrollers = [s for s in _cards(at) if "max-height" in s]
    assert scrollers, "no height-limited table rendered"
    for s in scrollers:
        assert "overflow-y:auto" in s
        assert "scrollbar-gutter:stable" in s, "D11.4"
        # the killer: a later shorthand overruling the longhand
        assert "overflow:hidden" not in s, s


def test_the_seasonality_chart_uses_the_same_card(at):
    """c-236. The last plotly tooltip on this page a reader
    would want to READ. One popup design per page, or the
    design is not a design."""
    blocks = _blocks(at, "class='mgrid'")
    assert blocks, "the seasonality chart did not render as HTML"
    h = blocks[0]
    assert h.count("class='mcol'") == 4
    assert ".mcol:hover .pop{display:block}" in h
    for rule in (".pop .pg{", ".pop .pn{", ".pop .ph{"):
        assert rule in h, rule
    # a MONTH is not a review, so it gets no MSCI document link
    assert "class='pl'" not in h


def test_section_titles_are_title_case(at):
    """DESIGN_DECISIONS D4."""
    import re
    md = " ".join(str(m.value) for m in at.markdown)
    # c-242: SCOPED to the section rule. The bare class='t'
    # pattern also matched the chart's regime label once that
    # label gained a title span — a test reading markup by a
    # class name is only as specific as the name.
    titles = re.findall(r"class='dsect'>.*?class='t'>([^<]+)", md)
    assert titles
    minor = {"a", "an", "and", "as", "at", "in", "of", "or",
             "the", "to", "for", "is"}
    for t in titles:
        words = [w for w in re.findall(r"[A-Za-z]+", t)]
        for i, w in enumerate(words):
            if i and w.lower() in minor:
                continue
            assert w[0].isupper(), f"{t!r}: {w!r} is lower-case"


def test_all_markets_is_offered_and_leads_the_list(at):
    """c-240. Bill asked for an aggregate option on the
    section-2 selector."""
    opts = at.selectbox[0].options
    assert opts[0] == "All Markets"
    assert "Taiwan" in opts


def test_all_markets_renders_every_section(at):
    """The selector drives sections 2 through 5, not just the
    chart, so the aggregate has to survive all of them."""
    at.selectbox[0].set_value("__ALL__").run()
    assert not at.exception, [e.value[:300] for e in at.exception]
    blocks = _blocks(at, "class='hgrid'")
    assert blocks, "the chart did not render under All markets"


def test_all_markets_refuses_section_3_rather_than_faking_it(at):
    """MSCI publishes a separate index per country. There is no
    combined constituent list, so aggregating section 3 would
    invent a portfolio nobody holds — it says so instead."""
    at.selectbox[0].set_value("__ALL__").run()
    msgs = " ".join(str(i.value) for i in at.info)
    assert "separate index" in msgs


def test_the_sentinel_can_never_match_a_market_row(at):
    """ALL is deliberately not a market name: `df.market == ALL`
    must never accidentally select rows."""
    import views.history_explorer as H
    import pandas as pd
    df = pd.read_pickle(ROOT / "data" / "msci_changes_db.pkl")
    assert H.ALL not in set(df.market.unique())
    assert H._pretty(H.ALL) == "All Markets"


def test_the_strip_card_can_actually_open(at):
    """c-242, and this is the regression that hurt.

    POP_CSS carries how a card LOOKS; how it OPENS is the
    host's business, because each anchors it differently. When
    c-236 replaced section 1's hand-written block with POP_CSS
    it took the appearance rules and deleted the behaviour
    rules sitting among them — leaving the card `display:none`
    with nothing to turn it on. Section 1's hover was dead for
    six revisions and every existing test still passed, because
    they all checked CSS strings GLOBALLY and sections 2 and 3
    supplied their own.

    A shared stylesheet is only safe if you can say which half
    you shared. This test asserts the half that was lost.
    """
    strip = _blocks(at, "class='astrip'")[0]
    assert ".amk:hover .pop{display:block}" in strip
    assert ".amk .pop{top:calc(100% - 2px)" in strip


def test_every_card_host_supplies_its_own_open_rule(at):
    """The general form: three hosts, three show rules. If a
    fourth is added without one, its card is invisible."""
    for needle, rule in (
            ("class='astrip'", ".amk:hover .pop{display:block}"),
            ("class='hgrid'", ".hcol:hover .pop{display:block}"),
            ("class='mgrid'", ".mcol:hover .pop{display:block}")):
        blocks = _blocks(at, needle)
        assert blocks, needle
        assert rule in blocks[0], f"{needle} has no open rule"


def test_the_regime_label_is_two_rows_sharing_one_x(at):
    """c-242. The title sits above; the before/bar/after row
    below keeps the bar glyph pinned to the dotted line."""
    import re
    h = _blocks(at, "class='hgrid'")[0]
    m = re.search(r"<div class='hregl' style='left:([\d.]+)%'>"
                  r"(.*?)</div>", h, re.S)
    assert m, "the regime label did not render"
    parts = dict(re.findall(r"class='(cap|l|b|r)'>([^<]*)",
                            m.group(2)))
    # c-246: set in capitals at Bill's request
    assert "2023 QUARTERLY REVIEW RULE" in parts.get("cap", "")
    assert "before" in parts.get("l", "")
    assert "after" in parts.get("r", "")
    assert "9474" in parts.get("b", "")     # the bar glyph


def test_section_5_shows_names_not_tickers(at):
    """c-243. Section 4 is where a reader resolves a name to a
    code; section 5 answers "which names moved at this review",
    and 35% of the codes are blank anyway (TICKER_AUDIT)."""
    import re
    blocks = [b for b in [str(m.value) for m in at.markdown]
              if ">Action<" in b]
    assert blocks, "the review-detail table did not render"
    hdr = [re.sub("<[^>]*>", "", h).strip()
           for h in re.findall(r"<th[^>]*>(.*?)</th>",
                               blocks[0], re.S)]
    assert hdr == ["Action", "Security"], hdr


def test_the_seasonality_column_does_not_repeat_its_header(at):
    """The column is headed "Review"; "Feb reviews" in every
    cell is the label twice."""
    import re
    blocks = [b for b in [str(m.value) for m in at.markdown]
              if ">Review<" in b]
    assert blocks
    cells = re.findall(r"<td[^>]*>(Feb|May|Aug|Nov)[^<]*</td>",
                       blocks[0])
    assert cells, "no month rows found"
    assert "reviews" not in blocks[0].lower().split(
        "<tbody>")[-1]


def test_tables_do_not_leave_a_band_under_the_last_row(at):
    """c-244. Bill reported this twice, and at c-243 I fixed the
    wrong thing and said it was done.

    The band is Streamlit's, not ours: its markdown theme sets
    `table {margin-bottom: 1rem}`, which applies to raw HTML we
    inject too. An overflow container establishes a BFC, so the
    margin stays INSIDE the white card — no card styling could
    ever have removed it.

    Only an inline style on the table beats an emotion class,
    so that is what this pins."""
    md = " ".join(str(m.value) for m in at.markdown)
    assert "tbody tr:last-child td" in md, "last rule still drawn"
    tables = re.findall(r"<table[^>]*style=\"([^\"]*)\"", md)
    assert tables, "no HTML table rendered"
    for s in tables:
        assert "margin:0" in s, (
            "Streamlit's table margin-bottom:1rem is back")
