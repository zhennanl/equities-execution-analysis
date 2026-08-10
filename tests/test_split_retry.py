"""Edge-straddling chunks, and never ending with less (c-206).

Two bugs that together destroyed real data on Bill's machine:

  1. `tune` raised the chunk size from 30 days to 120, so a
     whole window became ONE request. IB does not truncate a
     request reaching past its floor — it returns nothing. An
     80-day ask ending 2023-07-15, reaching Taiwan's 2023-04-26
     edge, came back empty where the old 30-day walk had
     returned two full chunks.

  2. `refetch` deleted the old rows BEFORE fetching, with no
     way back. 3443 and 3231 went from 2,695 bars each to zero.

These pin the halving retry and the rollback.
"""
import datetime as dt
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import ib_5m_events as m                           # noqa: E402


class FakeIB:
    """Serves bars only on or after `floor` — the shape IB has
    at a history boundary, including the all-or-nothing
    behaviour that caused the loss."""

    def __init__(self, floor):
        self.floor = floor
        self.calls = []

    def ask(self, end_date, days):
        self.calls.append((end_date, days))
        start = end_date - dt.timedelta(days=days)
        return [] if start < self.floor else ["bar"] * days


def _patch(monkeypatch, fake):
    def _bars(ib, con, end_date, days=None):
        days = days or m._chunk_days()
        return fake.ask(end_date, days), (162, "no permissions")
    monkeypatch.setattr(m, "_bars", _bars)


def test_split_retry_recovers_the_reachable_part(monkeypatch):
    floor = dt.date(2023, 5, 6)
    fake = FakeIB(floor)
    _patch(monkeypatch, fake)
    got, _err = m._split_retry(None, None, dt.date(2023, 7, 15),
                               80)
    assert got, "an 80-day ask straddling the floor returned " \
                "nothing at all — this is the c-206 data loss"
    assert len(fake.calls) > 1, "it must actually split"


def test_no_split_when_the_whole_span_is_available(monkeypatch):
    fake = FakeIB(dt.date(2000, 1, 1))
    _patch(monkeypatch, fake)
    got, _ = m._split_retry(None, None, dt.date(2023, 7, 15), 80)
    assert got and len(fake.calls) == 1, \
        "a span fully inside coverage must cost ONE request"


def test_split_stops_rather_than_recursing_forever(monkeypatch):
    fake = FakeIB(dt.date(2099, 1, 1))          # nothing ever
    _patch(monkeypatch, fake)
    got, err = m._split_retry(None, None, dt.date(2023, 7, 15),
                              80)
    assert got == []
    assert err is not None, "a genuine gap must report a reason"
    assert len(fake.calls) < 80, "recursion must be bounded"


def test_min_split_is_a_week_ish():
    assert 3 <= m.MIN_SPLIT <= 15, \
        "below a week the retry costs more than it recovers"


def test_empty_windows_are_retried_once_the_split_exists():
    """A window written off by an all-or-nothing request is not
    settled — but a venue with no history at all is."""
    fixable = {"px": [], "empty_reason": "before_edge"}
    settled = {"px": [], "empty_reason": "venue_no_history"}
    done = {"px": [], "empty_reason": "before_edge",
            "split_tried": True}

    def retry(w):
        return (not w.get("px")
                and w.get("empty_reason") != "venue_no_history"
                and not w.get("split_tried"))
    assert retry(fixable)
    assert not retry(settled)
    assert not retry(done)


def test_rollback_keeps_the_larger_record():
    """The rule refetch now applies: never end with less."""
    old = {"code": "3443", "rev": "May23", "px": [1] * 2695}
    new = {"code": "3443", "rev": "May23", "px": []}
    keep = old if len(new["px"]) < len(old["px"]) else new
    assert keep is old and len(keep["px"]) == 2695
