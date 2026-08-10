"""The IBKR 5-minute boundary probe (c-201).

The measurement this replaces reported "reaches at least
2010-01-01" for five markets — which measured where WE stopped
looking, not where IBKR stops, and then became a real
constraint downstream because jobs() drops reviews announced
before the recorded edge. These tests pin the three things that
made the old answer untrustworthy: a single probe symbol, a
hard-coded floor, and no confirmation.
"""
import datetime as dt
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import ib_5m_boundary as b                         # noqa: E402


def test_every_venue_has_three_probes_of_different_vintage():
    for v, (_ex, _ccy, probes) in b.VENUES.items():
        assert len(probes) >= 3, \
            f"{v}: one symbol cannot separate IBKR's floor " \
            f"from that company's listing date"
        assert len({s for s, _ in probes}) == len(probes)


def test_the_two_taiwan_boards_are_probed_separately():
    assert b.VENUES["Taiwan"][0] == "TWSE"
    assert b.VENUES["Taiwan_TPEx"][0] == "TPEX"


def test_china_is_probed_on_both_connect_venues():
    assert b.VENUES["China_SH"][0] == "SEHKNTL"
    assert b.VENUES["China_SZ"][0] == "SEHKSZSE"


def test_walk_back_reaches_the_late_nineties():
    oldest = max(b.STEPS_Y)
    reach = dt.date.today() - dt.timedelta(days=365 * oldest)
    assert reach.year <= 1999, \
        "the walk must be able to run out of history, or a " \
        "search limit gets reported as a finding"


def test_earliest_probe_wins():
    syms = [{"symbol": "OLD", "data_by": "2004-03-01",
             "result": "EDGE"},
            {"symbol": "NEW", "data_by": "2015-06-01",
             "result": "EDGE"},
            {"symbol": "MID", "data_by": "2013-01-01",
             "result": "EDGE"}]
    v = b._verdict("X", "EX", syms)
    assert v["edge"] == "2004-03-01"
    # c-204 softened this wording. I had claimed a later probe
    # date IS a listing date. Australia disproved it: BHP and
    # CBA start 2004-05-06 and CSL starts 2007-11-02, but CSL
    # listed in 1994 — so per-symbol coverage varies for
    # reasons other than listing. The venue edge is a CEILING
    # on coverage, not a promise about any one name.
    assert "coverage clearly varies by name" in v["verdict"]
    assert "VENUE floor" in v["verdict"]


def test_agreement_between_probes_is_stated():
    syms = [{"symbol": s, "data_by": d, "result": "EDGE"}
            for s, d in [("A", "2004-03-01"), ("B", "2004-03-20"),
                         ("C", "2004-03-10")]]
    v = b._verdict("X", "EX", syms)
    assert v["spread_days"] <= 30
    assert "IBKR's floor" in v["verdict"]


def test_hitting_the_search_limit_is_not_reported_as_an_edge():
    syms = [{"symbol": "A", "result": "NO BOUNDARY FOUND",
             "reaches_at_least": "1998-08-01"}]
    v = b._verdict("X", "EX", syms)
    assert v["edge_is_a_floor_we_hit"] is True
    assert "OUR limit" in v["verdict"]


def test_no_data_at_the_present_day_is_entitlement():
    """A boundary cannot explain a failure TODAY."""
    syms = [{"symbol": "A", "result": "NO DATA EVEN NOW"}]
    v = b._verdict("X", "EX", syms)
    assert v["edge"] is None
    assert "not a history boundary" in v["verdict"]


def test_unconfirmed_edges_are_labelled():
    syms = [{"symbol": "A", "data_by": "2004-03-01",
             "result": "EDGE UNCONFIRMED"}]
    v = b._verdict("X", "EX", syms)
    assert "UNCONFIRMED" in v["verdict"]


def test_probe_window_is_wide_enough_for_holidays():
    src = (ROOT / "scripts" / "ib_5m_boundary.py").read_text(
        encoding="utf-8")
    assert 'durationStr="10 D"' in src, \
        "a one-day probe cannot tell an absent archive from " \
        "Lunar New Year"
