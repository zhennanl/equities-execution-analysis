"""The APAC Rebalance Panel page renders, and carries its
caveats (c-231).

This page shows a survivors-only panel for ten of twelve
markets, market-ADJUSTED as of c-274, from non-independent
events. Those three facts are not footnotes — they are the
difference between a useful page and a misleading one, so they
are tested like functionality.

c-274 CHANGED ONE OF THEM, and the test changed with it rather
than being loosened. This file used to assert the page said
returns were "total, not excess", which was the honest label
when no benchmark existed for every market. A benchmark now
exists for all twelve at 98.5%+ coverage, so the page says the
opposite and the assertion is inverted: the page must now
claim EXCESS and must still show the raw number beside it. A
caveat test that only checks for the presence of some warning
text would have passed silently through this reversal, which
is why the phrases are pinned rather than counted.

The page also COMPUTES NOTHING: every number is read from
data/index_strategist_qa.json. That is tested too, because a
view that quietly starts doing its own arithmetic is a view
that will eventually disagree with the document it came from.
"""
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
from views import apac_strategist
apac_strategist.render()
"""


def _real_streamlit():
    mod = sys.modules.get("streamlit")
    if mod is not None and getattr(mod, "__file__", None):
        return
    for name in [n for n in sys.modules
                 if n == "streamlit" or n.startswith("streamlit.")
                 or n.startswith("views")]:
        del sys.modules[name]


@pytest.fixture(scope="module")
def at():
    _real_streamlit()
    pytest.importorskip("streamlit")
    from streamlit.testing.v1 import AppTest
    if not (ROOT / "data" / "index_strategist_qa.json").exists():
        pytest.skip("panel not built")
    a = AppTest.from_string(APP, default_timeout=300)
    a.run()
    return a


def test_page_renders_without_exceptions(at):
    assert not at.exception, [e.value[:300] for e in at.exception]


def test_every_section_reaches_the_screen(at):
    md = " ".join(str(m.value) for m in at.markdown)
    # 9 since c-274 — "Does the Print Revert" was added once the
    # +/-20 top-up made a strict 20-session horizon computable.
    assert md.count("dsect") == 9, md.count("dsect")


def test_the_three_caveats_are_rendered_not_footnoted(at):
    """Survivorship, market adjustment, non-independence.

    A caveat printed as small grey text under a chart is a
    caveat nobody reads. These get the amber block.
    """
    md = " ".join(str(m.value) for m in at.markdown)
    assert md.count("#b8860b") >= 3, "caveat blocks missing"
    low = md.lower()
    for phrase in ("survivors-only", "excess over that market",
                   "not independent observations"):
        assert phrase in low, phrase
    # the reversal must be stated, not silently applied
    assert "used to say the opposite" in low


def test_raw_returns_survive_beside_the_adjusted_ones(at):
    """c-274. Adjusting is only half the decision; keeping the
    raw number is the other half.

    The size of the adjustment IS the finding — on Taiwan it
    removes roughly 45% of the published addition drift. A page
    that showed only the adjusted figure would be more correct
    and less useful, because the reader could no longer see how
    much of the old answer was the market."""
    md = " ".join(str(m.value) for m in at.markdown)
    for col in ("Drift (excess)", "Drift (raw)", "Market's Part",
                "+20 (excess)", "+20 (raw)", "Linear (raw)"):
        assert col in md, col


def test_the_strict_horizon_is_stated_and_counted(at):
    """rev20 is 20 sessions or nothing. The page must show the
    count of windows that HAVE 20 sessions next to the count
    that has anything, because before c-274 the shortfall was
    invisible — the horizon shortened instead of failing."""
    md = " ".join(str(m.value) for m in at.markdown)
    assert "n\u2082\u2080" in md or "n₂₀" in md
    low = md.lower()
    assert "twenty sessions or nothing" in low


def test_the_limits_section_says_what_is_missing(at):
    """The page must state that it cannot forecast. That is the
    honest difference between it and the Taiwan pages."""
    md = " ".join(str(m.value) for m in at.markdown).lower()
    assert "everything above is descriptive" in md
    assert "taiwan only" in md


def test_the_page_computes_nothing(at):
    """Every figure comes from the generated JSON. A view doing
    its own arithmetic will drift from the document."""
    src = (ROOT / "views" / "apac_strategist.py").read_text(
        encoding="utf-8")
    for banned in ("statistics", "median(", "np.", "groupby"):
        assert banned not in src, \
            f"{banned!r} in the view — analysis belongs in " \
            f"scripts/index_strategist_qa.py"


def test_market_names_are_spaced_for_readers(at):
    """HongKong and NewZealand are storage keys, not names."""
    md = " ".join(str(m.value) for m in at.markdown)
    assert "HongKong" not in md
    assert "NewZealand" not in md


def test_the_market_picker_offers_every_market(at):
    assert at.selectbox
    opts = at.selectbox[0].options
    assert len(opts) >= 10
    assert "Hong Kong" in opts and "New Zealand" in opts


@pytest.mark.parametrize("mkt", ["China", "Japan", "NewZealand"])
def test_other_markets_render(at, mkt):
    """NewZealand has 13 events and China 1,237 — the two ends
    that break formatting code."""
    at.selectbox[0].set_value(mkt).run()
    assert not at.exception, \
        f"{mkt}: {[e.value[:300] for e in at.exception]}"
