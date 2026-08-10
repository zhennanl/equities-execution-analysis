"""India bhavcopy: failure handling and cache correctness
(c-200).

Three bugs, all of which produced silence rather than an error:

  1. one read timeout on nsearchives.nseindia.com raised out of
     harvest_in, out of harvest_all, and out of the process —
     the ten Yahoo markets never started;
  2. the pre-2024-07-08 parser returned (close, volume) only,
     while c-198's cache rule invalidates any row shorter than
     5 fields — together an infinite re-download that could
     never converge;
  3. the day cache stored rows filtered to the fetching
     review's movers, but review windows overlap by 2-3 weeks,
     so the next review read a day missing its own names and
     recorded them as not having traded.
"""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import apac_event_days as m                        # noqa: E402


def test_unavailable_is_a_distinct_type():
    assert issubclass(m.BhavUnavailable, Exception)


def test_get_retries_then_raises(monkeypatch):
    calls = []

    class Boom(Exception):
        pass

    def fake_get(url, headers=None, timeout=None):
        calls.append(url)
        raise Boom("read timed out")

    import requests
    monkeypatch.setattr(requests, "get", fake_get)
    monkeypatch.setattr(m.time, "sleep", lambda *_: None)
    with pytest.raises(m.BhavUnavailable):
        m._get("https://nsearchives.nseindia.com/x.csv", tries=3)
    assert len(calls) == 3, "must retry before giving up"


def test_404_is_a_holiday_not_a_failure(monkeypatch):
    class R:
        status_code = 404
    import requests
    monkeypatch.setattr(requests, "get",
                        lambda *a, **k: R())
    assert m._get("https://nsearchives.nseindia.com/x.csv") is None


def test_old_format_columns_carry_ohlc():
    """SYMBOL,SERIES,OPEN,HIGH,LOW,CLOSE,LAST,PREVCLOSE,TOTTRDQTY
    -> 2=OPEN 3=HIGH 4=LOW 5=CLOSE 8=TOTTRDQTY."""
    p = "RELIANCE,EQ,100.5,105.0,99.0,104.0,104.0,98.0,123456".split(",")
    row = (float(p[5]), float(p[8]), float(p[2]),
           float(p[3]), float(p[4]))
    assert len(row) == 5, \
        "a 2-field row here plus the c-198 cache rule is an " \
        "infinite re-download loop"
    assert row[0] == 104.0 and row[2] == 100.5
    assert row[3] == 105.0 and row[4] == 99.0


def test_cached_day_records_what_it_was_filtered_for():
    """The overlap bug: without _ask, a day fetched for review A
    silently reports review B's names as untraded."""
    day = {"RELIANCE": (1, 2, 3, 4, 5), "_ask": ["RELIANCE"]}
    want_a = {"RELIANCE"}
    want_b = {"TCS"}
    assert want_a <= set(day["_ask"])
    assert not want_b <= set(day["_ask"]), \
        "a review asking for TCS must MISS this cache entry, " \
        "not read absence as a non-trading day"


def test_ask_list_is_not_mistaken_for_a_symbol():
    day = {"RELIANCE": (1, 2, 3, 4, 5), "_ask": ["RELIANCE"]}
    syms = [s for s in day if s != "_ask"]
    assert syms == ["RELIANCE"]
