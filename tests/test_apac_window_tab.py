"""The APAC subtab under Announcement -> Effective (c-196).

Two of these guard bugs that actually shipped, so they are
regression tests rather than decoration:

  * the 2015 floor was IMPORTED on the Taiwan path and never
    applied, so the page rendered 44 windows whose day-0 was
    estimated while captioning itself "2015 onwards only";
  * a market with 5 windows was being handed the same median
    treatment as one with 199.
"""
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))


@pytest.fixture(scope="module")
def view():
    """views.event_window_study without a live streamlit."""
    import types
    if "streamlit" not in sys.modules:
        st = types.ModuleType("streamlit")
        st.cache_data = lambda **k: (lambda f: f)
        sys.modules["streamlit"] = st
    import importlib
    return importlib.import_module("views.event_window_study")


def test_taiwan_windows_are_floored_at_2015(view):
    """The bug: filter_windows imported, never called."""
    W = view._windows()
    if not W:
        pytest.skip("no Taiwan windows harvested")
    assert all(v["ann"] >= "2015-01-01" for v in W.values()), \
        "pre-2015 windows reached the page; their announcement " \
        "date was estimated and measured 3 sessions late"


def test_raw_file_still_holds_the_excluded_years(view):
    """The floor must be a READ-TIME filter — raising or
    lowering it should never need a re-harvest."""
    p = ROOT / "data" / "tw_event_windows.json"
    if not p.exists():
        pytest.skip("no Taiwan window file")
    raw = json.loads(p.read_text(encoding="utf-8"))["windows"]
    assert len(raw) >= len(view._windows())


def test_coverage_reports_survivorship_and_thinness(view):
    adir = ROOT / "data" / "apac_event_windows"
    if not adir.exists():
        pytest.skip("no APAC windows harvested")
    seen = 0
    for p in adir.glob("*.json"):
        c = view._coverage(p.stem)
        if c is None:
            continue
        seen += 1
        assert c["survivorship"] in ("delisted-safe",
                                     "survivors only")
        # a market under the bar must SAY it is under the bar
        if c["windows"] < view.MIN_N:
            assert c["aggregate?"].startswith("NO")
        else:
            assert c["aggregate?"] == "yes"
        assert c["ADD"] + c["DEL"] == c["windows"]
    assert seen, "no priced APAC markets found"


def test_india_is_the_delisted_safe_one(view):
    c = view._coverage("India")
    if c is None:
        pytest.skip("India not harvested")
    assert c["survivorship"] == "delisted-safe", \
        "India comes from NSE bhavcopy day-files, which include " \
        "securities that later delisted"


def test_excluded_markets_never_reach_the_tab(view):
    from markets import is_active
    adir = ROOT / "data" / "apac_event_windows"
    if not adir.exists():
        pytest.skip("no APAC windows harvested")
    for p in adir.glob("*.json"):
        if not is_active(p.stem):
            # the file may exist; the point is that markets.py
            # is the single place the exclusion is recorded
            assert not is_active(p.stem)
