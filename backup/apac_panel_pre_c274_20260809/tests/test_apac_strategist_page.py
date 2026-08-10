"""The APAC Rebalance Panel page renders, and carries its
caveats (c-231).

This page shows a survivors-only panel for ten of twelve
markets, unadjusted for market moves, from non-independent
events. Those three facts are not footnotes — they are the
difference between a useful page and a misleading one, so they
are tested like functionality.

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
    assert md.count("dsect") == 8, md.count("dsect")


def test_the_three_caveats_are_rendered_not_footnoted(at):
    """Survivorship, no market adjustment, non-independence.

    A caveat printed as small grey text under a chart is a
    caveat nobody reads. These get the amber block.
    """
    md = " ".join(str(m.value) for m in at.markdown)
    assert md.count("#b8860b") >= 3, "caveat blocks missing"
    low = md.lower()
    for phrase in ("survivors-only", "total, not excess",
                   "not independent observations"):
        assert phrase in low, phrase


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
