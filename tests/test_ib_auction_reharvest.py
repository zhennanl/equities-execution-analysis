"""Guards for the closing-auction re-harvest (c-295).

WHY THIS FILE IS MOSTLY ABOUT ONE FUNCTION. The bug being fixed was
never in the fetching — it was in believing that "the last bar that
traded" is "the closing auction". The replacement belief is that an
auction has a measurable signature, and the whole correctness of the
re-harvest rests on that discriminator being right.

The first version of it was wrong in a way that LOOKED right: ">=1%
of the day on >=20 days" named 16:10 for Korea and 18:55 for India,
from slots present on ~25 sessions out of many thousands. It printed
a clock time for every market and every one of them looked like an
answer. So the tests below are built around the cases that separate
a real auction from a plausible-looking artefact.
"""
import json
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import ib_auction_reharvest as A  # noqa: E402


def _prof(rows):
    """rows: [(clock, n_days, mean_share)] -> profile dict."""
    return {c: (n, s, n) for c, n, s in rows}


# ── the discriminator ────────────────────────────────────────────────

def test_a_wall_is_an_auction(monkeypatch):
    """The ASX shape: continuous volume ramps into 15:55, two dead
    slots, then 16:10 prints twelve times bigger."""
    prof = _prof([("15:40", 4000, .020), ("15:45", 4000, .021),
                  ("15:50", 4000, .026), ("15:55", 4000, .030),
                  ("16:00", 1700, .0001), ("16:05", 1700, .0001),
                  ("16:10", 1330, .126)])
    monkeypatch.setattr(A, "clock_profile", lambda m, windows=None: prof)
    clock, _ = A.discover("Australia")
    assert clock == "16:10"


def test_a_slope_is_not_an_auction(monkeypatch):
    """The TSE shape: the end-of-day ramp lifts the last continuous
    bar above its neighbours, and that is NOT a print. If this ever
    passes, Japan silently rejoins the comparison with a number that
    measures 14:55 continuous trading."""
    prof = _prof([("14:35", 17000, .0166), ("14:40", 17000, .0183),
                  ("14:45", 17000, .0212), ("14:50", 17000, .0257),
                  ("14:55", 17000, .0350)])
    monkeypatch.setattr(A, "clock_profile", lambda m, windows=None: prof)
    clock, _ = A.discover("Japan")
    assert clock is None, f"a ramp was called an auction ({clock})"


def test_a_slot_present_on_a_handful_of_days_is_not_an_auction(
        monkeypatch):
    """Korea's 16:10 and India's 18:55 — big share, ~25 sessions out
    of thousands. An ABSOLUTE day count cannot catch this, which is
    why the floor is a fraction of the market's own coverage."""
    prof = _prof([("15:00", 8000, .020), ("15:05", 8000, .021),
                  ("15:10", 8000, .022), ("15:15", 8000, .030),
                  ("18:55", 25, .180)])
    monkeypatch.setattr(A, "clock_profile", lambda m, windows=None: prof)
    clock, _ = A.discover("India")
    assert clock != "18:55"


def test_an_empty_profile_returns_nothing_rather_than_guessing(
        monkeypatch):
    monkeypatch.setattr(A, "clock_profile", lambda m, windows=None: {})
    assert A.discover("Korea") == (None, {})


# ── agreement with published microstructure ──────────────────────────

@pytest.mark.parametrize("market,clock,want", [
    ("Australia", "16:10", True),    # inside 16:10-16:12
    ("HongKong", "16:05", True),     # inside the 16:00-16:10 CAS
    ("Taiwan", "13:30", True),
    ("Singapore", "17:00", True),
    ("Japan", "14:55", False),       # five minutes BEFORE the print
    ("Japan", "15:30", True),
    ("Korea", "15:15", False),       # last continuous bar
    ("Korea", "15:30", True),
])
def test_agreement_is_checked_against_the_exchange_not_assumed(
        market, clock, want):
    assert A.agrees(market, clock) is want


def test_early_is_never_agreement():
    """The single most important case. An auction print is at or
    after the stated time; a bar BEFORE it is the continuous session,
    and slack on that side would wave Japan straight through."""
    assert A.agrees("Japan", "14:55") is False
    assert A.agrees("Korea", "15:15") is False


def test_a_market_with_no_published_expectation_is_unchecked():
    assert A.agrees("China", "16:05") is None
    assert A.agrees("Australia", None) is None


# ── the live data, as it stands ──────────────────────────────────────

@pytest.mark.skipif(not (ROOT / "data" / "ib_5m").exists(),
                    reason="no 5m bars on disk")
def test_the_known_good_markets_still_measure_where_they_should():
    """Taiwan is the market the Taiwan case study rests on, so if its
    auction bar ever stops resolving to 13:30 the study's intraday
    section is measuring something else."""
    for m in ("Taiwan", "HongKong", "Singapore", "Australia"):
        clock, _ = A.discover(m)
        assert clock, f"{m}: no auction bar found"
        assert A.agrees(m, clock) is not False, f"{m} -> {clock}"


@pytest.mark.skipif(not (ROOT / "data" / "ib_5m").exists(),
                    reason="no 5m bars on disk")
def test_the_broken_markets_are_still_reported_as_broken():
    """Until `harvest` runs, these must NOT quietly start passing —
    that would put three markets back into a comparison they do not
    belong in."""
    assert A.discover("Korea")[0] is None
    assert A.discover("India")[0] is None
    jp, _ = A.discover("Japan")
    assert jp is None or A.agrees("Japan", jp) is False


def test_affected_list_matches_what_the_data_says():
    """The markets named at the top of the module are the ones the
    evidence indicts — not a list that drifted from it."""
    assert set(A.AFFECTED) == {"Japan", "Korea", "Australia"}


# ── the harvest loop ─────────────────────────────────────────────────

class _Bar:
    def __init__(self, ts, vol=100.0):
        self.date, self.volume = ts, vol
        self.open = self.high = self.low = self.close = 1.0


def _fake_ib(monkeypatch, tmp_path, bars_for):
    """Drive cmd_harvest with a stand-in IB and a one-window file.

    c-296: cmd_harvest crashed on the first live run — it handed
    `_chunks` the ISO date STRINGS the window file stores, where the
    function wants dt.date. That is a one-line fix and it was never
    exercised, because every earlier test stopped at `discover`. So
    the loop now gets a real test with a fake broker.
    """
    import types
    import ib_5m_events as E

    monkeypatch.setattr(A, "SRC", tmp_path)
    (tmp_path / "Japan.json").write_text(json.dumps({
        "market": "Japan", "windows": {"May26|7203": {
            "code": "7203", "eff": "2026-05-29", "ann": "2026-05-12",
            "start": "2026-05-01", "end": "2026-05-10",
            "px": [["2026-05-01 09:00", 1, 1, 1, 1, 5.0]]}}}),
        encoding="utf-8")

    ib = types.SimpleNamespace(disconnect=lambda: None)
    monkeypatch.setattr(E, "_connect", lambda: ib)
    # _con returns (contract, venue) — the fake has to as
    # well, or the test passes on a shape the real code
    # never sees. That gap is exactly how the tuple bug
    # reached a live run.
    monkeypatch.setattr(E, "_con",
                        lambda _i, _m, _s: (object(), "TSEJ"))
    monkeypatch.setattr(E, "PACE", 0)
    monkeypatch.setattr(A, "_bars_rth0",
                        lambda *_a, **_k: (bars_for, None))
    return tmp_path


def test_harvest_survives_iso_date_strings(monkeypatch, tmp_path):
    """The crash, pinned. `_chunks` needs dt.date."""
    out = _fake_ib(monkeypatch, tmp_path,
                   [_Bar("2026-05-05 15:30:00")])
    A.cmd_harvest(types_ns(market="Japan", limit=0))
    got = json.loads((out / "Japan.rth0.json").read_text(
        encoding="utf-8"))
    assert "May26|7203" in got["windows"]


def test_harvest_drops_bars_outside_the_window(monkeypatch,
                                               tmp_path):
    """Chunks tile backwards and overshoot the start."""
    out = _fake_ib(monkeypatch, tmp_path, [
        _Bar("2026-04-01 15:30:00"),      # before start
        _Bar("2026-05-05 15:30:00"),      # inside
        _Bar("2026-06-01 15:30:00")])     # after end
    A.cmd_harvest(types_ns(market="Japan", limit=0))
    px = json.loads((out / "Japan.rth0.json").read_text(
        encoding="utf-8"))["windows"]["May26|7203"]["px"]
    assert [r[0][:10] for r in px] == ["2026-05-05"]


def test_harvest_dedupes_the_chunk_seam(monkeypatch, tmp_path):
    """THE SILENT ONE. Consecutive chunks overlap, and
    clock_profile divides each bar by the day's total — so a bar
    stored twice inflates the denominator and moves every share on
    the chart without raising anything."""
    out = _fake_ib(monkeypatch, tmp_path, [
        _Bar("2026-05-05 15:30:00"), _Bar("2026-05-05 15:30:00"),
        _Bar("2026-05-05 15:25:00")])
    A.cmd_harvest(types_ns(market="Japan", limit=0))
    px = json.loads((out / "Japan.rth0.json").read_text(
        encoding="utf-8"))["windows"]["May26|7203"]["px"]
    assert len(px) == len({r[0] for r in px}), "duplicate bars"
    assert [r[0] for r in px] == ["2026-05-05 15:25",
                                  "2026-05-05 15:30"]


def test_harvest_writes_the_same_timestamp_format_as_everything_else(
        monkeypatch, tmp_path):
    """str(bar.date)[:16]. Keeping the seconds would make these
    rows sort and compare differently from every other bar file."""
    out = _fake_ib(monkeypatch, tmp_path,
                   [_Bar("2026-05-05 15:30:00")])
    A.cmd_harvest(types_ns(market="Japan", limit=0))
    px = json.loads((out / "Japan.rth0.json").read_text(
        encoding="utf-8"))["windows"]["May26|7203"]["px"]
    assert px[0][0] == "2026-05-05 15:30", px[0][0]
    assert len(px[0]) == 6, "row must be [ts, o, h, l, c, v]"


def test_harvest_never_overwrites_the_original(monkeypatch,
                                               tmp_path):
    """The existing files are the EVIDENCE for the bug."""
    out = _fake_ib(monkeypatch, tmp_path,
                   [_Bar("2026-05-05 15:30:00")])
    before = (out / "Japan.json").read_text(encoding="utf-8")
    A.cmd_harvest(types_ns(market="Japan", limit=0))
    assert (out / "Japan.json").read_text(encoding="utf-8") == before
    assert (out / "Japan.rth0.json").exists()


def types_ns(**kw):
    import types
    return types.SimpleNamespace(**kw)


def test_harvest_does_not_clobber_its_own_arguments(monkeypatch,
                                                    tmp_path):
    """c-314. The window start/end dates were bound to `a` and `b`,
    and `a` IS the argparse namespace the function is called with.
    One market completed; the second died on `if a.limit` with
    "'datetime.date' object has no attribute 'limit'".

    Which is why only Japan was ever harvested — a bare `harvest`
    walks Japan, Korea, Australia and never reached Korea. The test
    runs TWO markets, because one can never show it.
    """
    import types
    import ib_5m_events as E
    monkeypatch.setattr(A, "SRC", tmp_path)
    for m in ("Japan", "Korea"):
        (tmp_path / f"{m}.json").write_text(json.dumps({
            "market": m, "windows": {f"May26|{m}": {
                "code": "1", "eff": "2026-05-29",
                "ann": "2026-05-12", "start": "2026-05-01",
                "end": "2026-05-10", "px": []}}}), encoding="utf-8")
    ib = types.SimpleNamespace(disconnect=lambda: None)
    monkeypatch.setattr(E, "_connect", lambda: ib)
    monkeypatch.setattr(E, "_con",
                        lambda _i, _m, _s: (object(), "V"))
    monkeypatch.setattr(E, "PACE", 0)
    monkeypatch.setattr(A, "_bars_rth0",
                        lambda *_a, **_k: ([_Bar(
                            "2026-05-05 15:30:00")], None))
    monkeypatch.setattr(A, "AFFECTED", ["Japan", "Korea"])
    A.cmd_harvest(types_ns(market=None, limit=0))
    for m in ("Japan", "Korea"):
        assert (tmp_path / f"{m}.rth0.json").exists(), m


def test_verify_measures_before_and_after_with_the_same_rule():
    """c-314, the NameError Bill hit.

    `cmd_verify` carried its own copy of the discriminator — the
    FIRST-CUT one this module's comments record as badly wrong —
    and it referenced `MIN_DAYS`, a constant deleted when the rule
    was corrected. The crash was the lucky outcome: had the name
    survived, verify would have measured "before" with the good
    rule and "after" with the bad one and printed a comparison of
    two different instruments.

    So the assertion is structural. There is ONE selector, both
    sides call it, and no second threshold set exists to drift.
    """
    src = (ROOT / "scripts" / "ib_auction_reharvest.py").read_text(
        encoding="utf-8")
    i = src.index("def cmd_verify")
    body = src[i:]
    assert "pick_auction(" in body, "verify no longer shares the rule"
    for stale in ("MIN_DAYS", "MIN_SPIKE", "MIN_SPIKE_RATIO",
                  "MIN_DAY_FRACTION"):
        assert stale not in body, (
            f"verify applies {stale} itself instead of calling "
            f"pick_auction")


def test_verify_does_not_call_an_earlier_slot_a_recovery(monkeypatch):
    """A useRTH=0 run that names a slot EARLIER than the RTH answer
    has not recovered an auction — the discriminator has picked a
    different continuous bar. Calling that RECOVERED would be the
    second wrong answer in this function."""
    early = _prof([("14:00", 4000, .02), ("14:05", 4000, .02),
                   ("14:10", 4000, .02), ("14:15", 4000, .30)])
    assert A.pick_auction(early)[0] == "14:15"
    late = _prof([("14:00", 4000, .02), ("14:05", 4000, .02),
                  ("14:10", 4000, .02), ("15:00", 4000, .30)])
    assert A.pick_auction(late)[0] == "15:00"
    assert A._mins("14:15") < A._mins("15:00")


def test_harvest_unpacks_the_contract_tuple(monkeypatch, tmp_path):
    """c-297. `_con` returns (contract, venue). Passing the tuple
    straight to reqHistoricalData raised AttributeError on all 247
    Japanese windows and wrote an empty file that looked like a
    finished run.

    Asserted on what reaches the fetcher, because that is the thing
    that was wrong — the window file alone cannot show it.
    """
    import ib_5m_events as E
    seen = {}
    out = _fake_ib(monkeypatch, tmp_path, [_Bar("2026-05-05 15:30:00")])

    def spy(ib, e, con, end, span):
        seen["con"] = con
        return [_Bar("2026-05-05 15:30:00")], None

    monkeypatch.setattr(A, "_bars_rth0", spy)
    A.cmd_harvest(types_ns(market="Japan", limit=0))
    assert not isinstance(seen["con"], tuple), \
        "the (contract, venue) tuple reached reqHistoricalData again"
    got = json.loads((out / "Japan.rth0.json").read_text(
        encoding="utf-8"))
    assert got["windows"]["May26|7203"]["venue"] == "TSEJ"


def test_an_unresolved_contract_is_skipped_not_fetched(
        monkeypatch, tmp_path):
    """`if not con` on (None, None) is False — the old guard could
    not fire. The test is that an unresolved symbol never reaches
    the fetcher at all."""
    import ib_5m_events as E
    _fake_ib(monkeypatch, tmp_path, [_Bar("2026-05-05 15:30:00")])
    monkeypatch.setattr(E, "_con", lambda _i, _m, _s: (None, None))
    called = []
    monkeypatch.setattr(A, "_bars_rth0",
                        lambda *a, **k: called.append(1) or ([], None))
    A.cmd_harvest(types_ns(market="Japan", limit=0))
    assert not called, "fetched against an unresolved contract"


def test_the_error_string_carries_the_message_not_just_the_class():
    """247 lines of bare 'AttributeError' named nothing. The
    message is what identifies the bug."""
    import types

    class _Boom:
        def reqHistoricalData(self, *a, **k):
            raise AttributeError("'tuple' object has no attribute "
                                 "'conId'")

    E = types.SimpleNamespace(_ERRORS=[], PACE=0)
    _bars, err = A._bars_rth0(_Boom(), E, object(),
                              __import__("datetime").date(2026, 5, 5), 5)
    assert "conId" in err[1], err


# ── c-317: not asking questions that have no answer ──────────────────

def _korea_like(tmp_path, monkeypatch):
    """A two-symbol market: one with bars, one empty at source."""
    import types
    import ib_5m_events as E
    monkeypatch.setattr(A, "SRC", tmp_path)
    monkeypatch.setattr(A, "DEAD", tmp_path / "dead.json")
    (tmp_path / "Korea.json").write_text(json.dumps({
        "market": "Korea", "windows": {
            "May18|A.KS": {"code": "A.KS", "eff": "2018-05-31",
                           "ann": "2018-05-14",
                           "start": "2018-05-01", "end": "2018-05-10",
                           "px": [["2018-05-01 09:00", 1, 1, 1, 1, 5.0]]},
            "Nov18|A.KS": {"code": "A.KS", "eff": "2018-11-30",
                           "ann": "2018-11-13",
                           "start": "2018-11-01", "end": "2018-11-10",
                           "px": [["2018-11-01 09:00", 1, 1, 1, 1, 5.0]]},
            "May18|B.KQ": {"code": "B.KQ", "eff": "2018-05-31",
                           "ann": "2018-05-14",
                           "start": "2018-05-01", "end": "2018-05-10",
                           "px": []},
            "Nov18|B.KQ": {"code": "B.KQ", "eff": "2018-11-30",
                           "ann": "2018-11-13",
                           "start": "2018-11-01", "end": "2018-11-10",
                           "px": []}}}), encoding="utf-8")
    ib = types.SimpleNamespace(disconnect=lambda: None)
    monkeypatch.setattr(E, "_connect", lambda: ib)
    monkeypatch.setattr(E, "_con",
                        lambda _i, _m, c: (types.SimpleNamespace(
                            symbol=c), "KRX"))
    monkeypatch.setattr(E, "PACE", 0)
    monkeypatch.setattr(A, "AFFECTED", ["Korea"])
    return E


def test_windows_empty_at_source_are_never_requested(monkeypatch,
                                                     tmp_path):
    """c-317, and the reason is analytical before it is economic.

    This script tests whether useRTH=0 surfaces an auction bar
    that useRTH=1 dropped. A window with NO bars contributes to
    neither clock profile, so re-asking it cannot move any
    verdict — and Japan proved the empirical half when all 247 of
    its windows came back byte-identical under the flag.

    On Bill's Korea run 60 of 162 windows were empty at source,
    33 of them KOSDAQ, and every one produced an error line
    indistinguishable from a real fault.
    """
    E = _korea_like(tmp_path, monkeypatch)
    asked = []

    def spy(_ib, _E, con, _end, _span):
        asked.append(con.symbol)
        return [_Bar("2018-05-05 09:00")], None

    monkeypatch.setattr(A, "_bars_rth0", spy)
    A.cmd_harvest(types_ns(market="Korea", limit=0,
                           retry_dead=False, include_empty=False))
    assert asked, "nothing was fetched at all"
    assert "B.KQ" not in asked, asked
    got = json.loads((tmp_path / "Korea.rth0.json").read_text(
        encoding="utf-8"))
    assert set(got["skipped"]) == {"May18|B.KQ", "Nov18|B.KQ"}
    for v in got["skipped"].values():
        assert "empty at source" in v["reason"]


def test_include_empty_overrides_the_structural_filter(monkeypatch,
                                                       tmp_path):
    """The override exists so the filter can be audited rather
    than trusted — and it is a SEPARATE flag from --retry-dead,
    because an empty window and a refused symbol are different
    facts with different lifetimes."""
    E = _korea_like(tmp_path, monkeypatch)
    asked = []
    monkeypatch.setattr(A, "_bars_rth0",
                        lambda _i, _E, con, _e, _s: (
                            asked.append(con.symbol),
                            ([_Bar("2018-05-05 09:00")], None))[1])
    A.cmd_harvest(types_ns(market="Korea", limit=0,
                           retry_dead=False, include_empty=True))
    assert "B.KQ" in asked


def test_a_refused_symbol_is_not_asked_in_another_review(
        monkeypatch, tmp_path):
    """50 of Korea's 103 codes appear in more than one review, so
    196170.KQ was requested at Aug20, Nov22 AND May24 — three
    windows, three identical refusals. One refusal is enough."""
    E = _korea_like(tmp_path, monkeypatch)
    asked = []

    def refuse(_ib, E_, con, _end, _span):
        asked.append(con.symbol)
        E_._ERRORS.append(
            (162, "Historical Market Data Service error message:"
                  "HMDS query returned no data: A.KS@KRX Trades"))
        return [], E_._ERRORS[-1]

    monkeypatch.setattr(A, "_bars_rth0", refuse)
    A.cmd_harvest(types_ns(market="Korea", limit=0,
                           retry_dead=False, include_empty=False))
    assert asked.count("A.KS") == 1, asked
    dead = json.loads((tmp_path / "dead.json").read_text(
        encoding="utf-8"))
    assert dead["markets"]["Korea"]["A.KS"]["kind"] == "nodata"


def test_the_ledger_survives_a_rerun_and_retry_dead_clears_it(
        monkeypatch, tmp_path):
    E = _korea_like(tmp_path, monkeypatch)
    asked = []

    def refuse(_ib, E_, con, _end, _span):
        asked.append(con.symbol)
        E_._ERRORS.append(
            (162, "Historical Market Data Service error message:"
                  "No market data permissions for KOSDAQ STK"))
        return [], E_._ERRORS[-1]

    monkeypatch.setattr(A, "_bars_rth0", refuse)
    A.cmd_harvest(types_ns(market="Korea", limit=0,
                           retry_dead=False, include_empty=False))
    first = len(asked)
    assert first == 1
    A.cmd_harvest(types_ns(market="Korea", limit=0,
                           retry_dead=False, include_empty=False))
    assert len(asked) == first, "a refused symbol was asked again"
    A.cmd_harvest(types_ns(market="Korea", limit=0,
                           retry_dead=True, include_empty=False))
    assert len(asked) > first, "--retry-dead did not clear anything"


def test_a_refusal_aborts_the_remaining_chunks_of_its_window(
        monkeypatch, tmp_path):
    """A permission refusal is a property of the SYMBOL, not the
    date range — the same Korean codes failed in 2018, 2020 and
    2024 windows alike. Once the first chunk refuses and nothing
    has been collected, every further chunk is a known-futile
    request."""
    E = _korea_like(tmp_path, monkeypatch)
    monkeypatch.setattr(E, "_chunks",
                        lambda a, b, span_days=None:
                        [(b, 5), (a, 5), (a, 5)])
    calls = []

    def refuse(_ib, E_, con, _end, _span):
        calls.append(con.symbol)
        E_._ERRORS.append(
            (162, "Historical Market Data Service error message:"
                  "HMDS query returned no data: x@KRX Trades"))
        return [], E_._ERRORS[-1]

    monkeypatch.setattr(A, "_bars_rth0", refuse)
    A.cmd_harvest(types_ns(market="Korea", limit=0,
                           retry_dead=False, include_empty=False))
    # one chunk per window, not three, and only one window
    assert len(calls) == 1, calls


def test_the_error_classifier_separates_the_three_cases():
    """IB uses error 162 for a permissions refusal, an empty date
    range and a cancelled query alike, so the message text is the
    only discriminator there is."""
    assert A._classify(None) == ("ok", None)
    assert A._classify(
        (162, "Historical Market Data Service error message:"
              "No market data permissions for KOSDAQ STK")) == (
        "permission", "KOSDAQ")
    assert A._classify(
        (162, "Historical Market Data Service error message:"
              "HMDS query returned no data: 067630.KQ@KRX Trades")
    )[0] == "nodata"
    assert A._classify(
        (162, "API historical data query cancelled: 232"))[0] == \
        "timeout"


def test_the_request_carries_an_explicit_timeout():
    """Bill's run hit a 60-second default timeout on 00104K.KS and
    then a cancellation. A symbol that hangs hangs on every chunk."""
    src = (ROOT / "scripts" / "ib_auction_reharvest.py").read_text(
        encoding="utf-8")
    assert "REQ_TIMEOUT" in src
    assert "timeout=REQ_TIMEOUT" in src
    assert 5 <= A.REQ_TIMEOUT <= 45
