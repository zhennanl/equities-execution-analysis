"""Guards for the opening and closing pages (c-346).

WHY THESE TWO PAGES ARE TESTED AT ALL. They are the only pages
on the site that are pure prose, so the usual guard — "the
figure on screen matches the JSON" — has almost nothing to
bite on. What CAN be pinned is the thing that would actually
embarrass: an intro that states a headline count the analysis no
longer supports, and a closing page whose case for automation
quietly drops the honesty that makes it credible.
"""
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def _render(mod):
    from conftest import real_streamlit
    real_streamlit()
    from streamlit.testing.v1 import AppTest
    h = ROOT / "tests" / f"_bookend_{mod}.py"
    h.write_text(
        f"import sys; sys.path.insert(0, {str(ROOT)!r})\n"
        f"from views import {mod}\n{mod}.render()\n",
        encoding="utf-8")
    try:
        at = AppTest.from_file(str(h), default_timeout=300).run()
        assert not at.exception, [e.value for e in at.exception]
        return " ".join(m.value for m in at.markdown)
    finally:
        h.unlink(missing_ok=True)


@pytest.fixture(scope="module")
def intro():
    return _render("opening")


@pytest.fixture(scope="module")
def outro():
    return _render("whats_next")


def test_the_intro_states_its_two_limits(intro):
    """Bill's brief: lead with what the data will not support.

    Two cards, and each names a MISSING SOURCE and the
    consequence of not having it. Both are claims the rest of the
    site depends on nobody assuming: that the float is measured,
    and that positioning is observable. Neither is true here, and
    both are stated before a single finding.

    Asserted on the CONSEQUENCE rather than on any one phrasing —
    these cards have been reworded three times and a test that
    pins the wording fails on edits that improve it."""
    # 1 · no MSCI licence, so the cutoff is struck from
    #     estimates and the prediction inherits the error
    assert "MSCI" in intro
    assert "cutoff" in intro and "estimate" in intro
    assert "wrong index change prediction" in intro
    # 2 · no institutional data, so positioning is inferred
    assert "borrow book" in intro
    assert "public data only" in intro
    # the reasons Taiwan was chosen, both halves — c-356 dropped
    # the internship mention and the Reason one/two eyebrows
    assert "Prior project experience" in intro
    assert "microstructure" in intro
    assert "TWSE" in intro
    for stale in ("Reason one", "Reason two", "internship",
                  "short interest"):
        assert stale not in intro, stale


def test_the_intro_routes_a_busy_reader_to_the_case_study(intro):
    """A PT dealer has five minutes, so the map is the first
    thing on the site: four pages named, one line each, in the
    order the sidebar puts them.

    c-350 removed the per-page time estimates and levelled the
    rules — all four rows now carry the same navy edge, because a
    muted rule on the first three read as "these are lesser" when
    they are the same site. The case study is marked by a label
    instead."""
    for page in ("MSCI Index Review Database",
                 "Predict MSCI Index Changes",
                 "Index Rebalance Daily Data",
                 "Taiwan Case Study"):
        assert page in intro, page
    assert intro.index("Taiwan Case Study") > intro.index(
        "MSCI Index Review Database")
    # c-364: the tag reads "live example" — the case study is
    # the framework applied to a live review cycle, which is a
    # description, not a ranking
    assert "live example" in intro          # the label
    assert ">the analysis</span>" not in intro
    # estimates and subtitles that were cut must not creep back
    for stale in ("1 min", "2 min", "the rest",
                  "Three pages of setup",
                  "The event set everything else is measured on",
                  "registered before MSCI announced"):
        assert stale not in intro, stale


def test_the_intro_stays_short(intro):
    """c-350, Bill: *"currently it's too long ... it's fine for
    me to speak as a script, but we need less content on the
    website."*

    The page is the first thing a busy reader meets, so its
    length is a feature of the design rather than an accident of
    editing. This is a ratchet: it can be tightened further, but
    a later pass cannot quietly grow it back."""
    assert len(intro) < 17000, len(intro)


def test_the_workflow_page_is_one_section(outro):
    """c-350 cut six prose sections and kept the loop; c-351 cut
    the built-against-missing ledger too.

    What is left has to stand on the loop alone, so the guard is
    that the removed material stays removed — this page has been
    trimmed twice and the failure mode now is old text creeping
    back in a later edit."""
    assert "Agentic AI Workflow" in outro
    for gone in ("Agent 1", "Agent 2", "Jefferies", "Strands",
                 "ONE LOOP", "What It Would Take",
                 "Already built", "Still missing"):
        assert gone not in outro, gone


def test_the_loop_is_drawn_and_explained_in_plain_words(outro):
    """WRITTEN FOR A DEALER, NOT AN ENGINEER.

    Bill's brief was that a PT trader with no technical
    background should follow this on one read. So the four boxes
    are named for what they do to the work, and the words that
    would send a non-technical reader away — cron, pipeline, API
    — must not appear."""
    assert "<svg" in outro
    # c-369, Bill: the Collector is renamed the Fetcher, and the
    # old name must not creep back
    for box in ("Fetcher", "Analyst", "Author", "Reviewer"):
        assert box in outro, box
    assert "Collector" not in outro
    for jargon in ("cron", "pipeline", "API", "CSRF", "HTTP 200"):
        assert jargon not in outro, jargon
    # the loop is a loop: something has to come back
    assert "does not match" in outro
    assert "rerun" in outro


def test_the_gate_survives_the_cut(outro):
    """THE FOURTH BOX IS THE WHOLE ARGUMENT.

    Three agents that collect, compute and write are a
    publishing machine. What makes it a research one is that the
    fourth can stop the note. If the reviewer ever becomes a
    formatting step, this page is selling something."""
    # c-375, Bill: the subtitle carries the outcome — but the
    # BODY must still carry the gate, because a reviewer that
    # only refines is a formatting step. c-377 rewrote the body:
    # the gate is now "mismatched number or flawed reasoning →
    # flagged for a rerun", and that pair is what must survive.
    assert "Reviews the draft and refines it for production" \
        in outro
    assert "Blocks anything" not in outro
    assert "mismatched number" in outro
    assert "flagged for a rerun" in outro
    # c-375: both failure gates on the arm, and the green EXIT
    # ARROW is gone — the loop ends at the Reviewer. GREEN
    # itself stays in the SVG (it colours the Author box), so
    # the assertion targets the arrow's own geometry: its
    # arrowhead was the only green-filled "l-7,-4 l0,8 z" path.
    assert "reasoning is flawed" in outro
    from views import design as _dz
    i_svg = outro.index("<svg")
    svg = outro[i_svg:outro.index("</svg>")]
    assert f'l-7,-4 l0,8 z" fill="{_dz.GREEN}"' not in svg
    assert 'l16,0' not in svg          # the arrow's shaft


def test_the_evening_timeline_is_concrete(outro):
    """The second register. A dealer reads "18:00 — collect"
    and knows exactly which files those are — an abstract loop
    does not survive that translation, and this is where it is
    tested."""
    # c-370, Bill: the timeline heading is "Example workflow";
    # c-371: the first row's label is the STEP, not the city
    assert "Example workflow" in outro
    assert "One evening" not in outro
    for stamp in ("18:00", "07:00"):
        assert stamp in outro, stamp
    assert "collect" in outro
    assert "Taipei" not in outro
    # c-371: the worked example is an unusual mover; c-373: an
    # AI slip in calculation or reasoning goes to a HUMAN —
    # that phrase is the page's whole safety argument, so it is
    # pinned
    assert "unusual price and volume movement" in outro
    assert "flagged for human review" in outro
    assert "illogical argument" not in outro
    # it ends where the reader's day starts
    assert "inbox" in outro or "before the open" in outro


def test_both_pages_are_routed(intro, outro):
    """A page nobody can reach is a file, not a page."""
    src = (ROOT / "app.py").read_text(encoding="utf-8")
    assert "Start Here" in src and "opening.render()" in src
    assert "Agentic AI Workflow" in src
    assert "whats_next.render()" in src
