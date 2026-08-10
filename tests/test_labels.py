"""Label helpers: title case and review dates (c-221).

Two rules that now apply site-wide from one place each, which
is exactly the kind of thing that is cheap to test and
expensive to get wrong quietly.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def _real_streamlit():
    """Drop any stub another test file installed.

    Several tests put a bare ModuleType into sys.modules to
    import a view without a display. history_explorer calls
    st.cache_data at import time, so a stub is fatal here — and
    only when the suite runs in one process.
    """
    mod = sys.modules.get("streamlit")
    if mod is not None and getattr(mod, "__file__", None):
        return
    for name in [n for n in sys.modules
                 if n == "streamlit" or n.startswith("streamlit.")
                 or n.startswith("views")]:
        del sys.modules[name]


def _design():
    _real_streamlit()
    import importlib
    return importlib.import_module("views.design")


def title_case(s):
    return _design().title_case(s)


def test_ordinary_titles_capitalise():
    assert title_case("Review period") == "Review Period"
    assert title_case("changes since 2006") == \
        "Changes Since 2006"


def test_minor_words_stay_lower_unless_leading():
    """"Number Of Index Changes" is shouting, not title case."""
    assert title_case("Number of index changes") == \
        "Number of Index Changes"
    assert title_case("of the index") == "Of the Index"


def test_acronyms_and_units_survive():
    """The reason blind .title() was not used.

    .title() turns "USD" into "Usd", "×ADV" into "×Adv" and
    "bps" into "Bps" — three ways to make a correct axis label
    wrong.
    """
    assert title_case("volume ×ADV (median)") == \
        "Volume ×ADV (Median)"
    assert title_case("bps (cost)") == "bps (Cost)"
    assert title_case("full market cap, USD B (log)") == \
        "Full Market Cap, USD B (log)"


def test_empty_and_none_pass_through():
    assert title_case("") == ""
    assert title_case(None) is None


def _rlabel():
    _real_streamlit()
    import importlib
    return importlib.import_module(
        "views.history_explorer")._rlabel


def test_review_codes_become_readable_dates():
    f = _rlabel()
    assert f("Feb26") == "Feb 2026"
    assert f("May10") == "May 2010"
    assert f("Nov06") == "Nov 2006"


def test_non_codes_are_left_alone():
    """The caveat string and anything unexpected must survive.

    _rlabel is applied to a column that mixes review codes with
    "since Feb06", so a greedy rule would corrupt the caveat it
    was never meant to touch.
    """
    f = _rlabel()
    assert f("since Feb06") == "since Feb06"
    assert f("") == ""
    assert f("2026") == "2026"
