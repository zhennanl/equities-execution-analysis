"""The symbol IB is actually asked for (c-222).

This exists because of a 33-window loss that was invisible in
code review and obvious in the console: on the Hong Kong run,
every ticker that failed began with a zero and every ticker
that succeeded did not.

c-204 had already established the rule — Yahoo says "0700.HK",
IB says "700" — and implemented it as

    if market == "HongKong" and sym.isdigit():
        sym = str(int(sym))
    ...
    if "." in sym:
        sym = sym.split(".")[0]

which is correct in isolation and wrong in sequence:
"0700.HK".isdigit() is False, so the de-padding never ran on a
suffixed ticker, the suffix came off afterwards, and IB was
asked for "0700" — the exact string c-204 proved does not
resolve. Fixing a transformation without checking the pipeline
around it is the failure mode these tests are for.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from ib_5m_events import _norm_sym, SINCE          # noqa: E402


def test_hong_kong_suffixed_ticker_loses_its_padding():
    """THE REGRESSION. Tencent is the headline case."""
    assert _norm_sym("HongKong", "0700.HK") == "700"
    assert _norm_sym("HongKong", "0005.HK") == "5"
    assert _norm_sym("HongKong", "0017.HK") == "17"


def test_hong_kong_bare_ticker_still_works():
    """The path that accidentally kept working, so the fix has
    to not break it."""
    assert _norm_sym("HongKong", "0700") == "700"
    assert _norm_sym("HongKong", "669") == "669"
    assert _norm_sym("HongKong", "2878.HK") == "2878"


def test_korea_pads_after_the_suffix_comes_off():
    """Korea is the mirror image — it needs SIX digits, and the
    same ordering bug would have under-padded a short code."""
    assert _norm_sym("Korea", "5930.KS") == "005930"
    assert _norm_sym("Korea", "011210.KQ") == "011210"
    assert _norm_sym("Korea", "005930") == "005930"


def test_letter_codes_are_left_alone():
    """An ADR or a word ticker must survive untouched — int()
    on these would raise, and str.lstrip('0') would eat a real
    leading character."""
    assert _norm_sym("HongKong", "FUTU") == "FUTU"
    assert _norm_sym("India", "BAJAJ-AUTO.NS") == "BAJAJ-AUTO"
    assert _norm_sym("Korea", "0126Z0") == "0126Z0"
    assert _norm_sym("Australia", "RHCPA.AX") == "RHCPA"


def test_the_2015_cap_is_a_date_not_a_flag():
    """Bill capped the left boundary at 2015 even where IB
    offers more. Recorded as a date so it can be moved."""
    assert SINCE == "2015-01-01"


def test_jobs_drops_pre_2015_reviews():
    import ib_5m_events as M
    cal = M.calendar()
    for m in ("HongKong", "Korea", "Australia"):
        if not M._edge_for(m):
            continue
        anns = [cal[rev][0] for rev, *_ in M.jobs(m)]
        assert anns, f"{m} has no jobs at all"
        assert min(anns) >= SINCE, \
            f"{m} still asks for {min(anns)}, before the cap"


def test_the_cap_does_not_truncate_the_pre_window():
    """A review announced just after the cap keeps its full
    45-day run-up, which reaches back BEFORE the cap. The floor
    applies to the event, not to the data around it."""
    import ib_5m_events as M
    cal = M.calendar()
    early = [(rev, start) for m in ("Korea", "Australia")
             if M._edge_for(m)
             for rev, _t, _a, _n, start, _e in M.jobs(m)
             if cal[rev][0] < "2015-04-01"]
    assert early, "no review close enough to the cap to test"
    assert any(s.isoformat() < SINCE for _r, s in early), \
        "every window was clipped at the cap — the pre-window " \
        "should be allowed to precede it"


def test_probe_venue_splits_the_boards_behind_one_exchange():
    """c-224. IB names one exchange for Korea; KOSPI and KOSDAQ
    are different ENTITLEMENTS behind it, and only one of them
    is live on this account. A pre-flight keyed on the exchange
    code would test KOSPI, report Korea ready, and lose every
    KOSDAQ window in the real run."""
    import ib_5m_events as M
    assert M._probe_venue("Korea", "348370.KQ") == "KRX_KOSDAQ"
    assert M._probe_venue("Korea", "326030.KS") == "KRX_KOSPI"
    assert M._probe_venue("HongKong", "1972.HK") == "SEHK"
    assert M._probe_venue("Japan", "5801") == "TSEJ"


def test_probe_venue_covers_every_china_venue():
    """SIX, not four — and this test asserted four one revision
    ago, which is why it had to fail before the c-225 fix could
    land. The pre-flight measured ChiNext and STAR as separate
    IB exchanges; a test written from my assumption rather than
    from IB's answer was defending the wrong number.
    """
    import ib_5m_events as M
    got = {M._probe_venue("China", t) for t in
           ("300620.SZ", "688313.SS", "600519.SS", "000001.SZ",
            "2357.HK", "YMM")}
    assert got == {"CHINEXT", "SEHKSTAR", "SEHKNTL",
                   "SEHKSZSE", "SEHK", "SMART"}


def test_china_board_routing_survives_the_suffix():
    """c-225, and this is the c-222 bug committed a second time.

    _china_venue branched per SUFFIX first and had a separate
    branch for bare codes, so the four-board logic only ever ran
    on bare codes: "688313.SS" returned from the .SS branch
    before reaching it. Same shape as the Hong Kong padding bug,
    same file, while writing the fix the padding bug taught me.
    The suffix is decoration; the number is the fact.
    """
    import ib_5m_events as M
    for tick, want in (("688313.SS", "SEHKSTAR"),
                       ("688313", "SEHKSTAR"),
                       ("300620.SZ", "CHINEXT"),
                       ("300620", "CHINEXT"),
                       ("301269.SZ", "CHINEXT"),
                       ("600519.SS", "SEHKNTL"),
                       ("000001.SZ", "SEHKSZSE"),
                       ("002594.SZ", "SEHKSZSE")):
        assert M._china_venue(tick)[0] == want, tick


def test_china_hk_lines_keep_their_depadding():
    """The HK rule inside China must not regress either."""
    import ib_5m_events as M
    assert M._china_venue("0700.HK") == ("SEHK", "HKD", "700")
    assert M._china_venue("1776") == ("SEHK", "HKD", "1776")
    assert M._china_venue("YMM") == ("SMART", "USD", "YMM")


def test_kospi_names_mislabelled_kq_route_to_kospi():
    """c-227. The harvest showed "two KOSDAQ windows with bars"
    and I nearly read it as KOSDAQ working. Both are KOSPI
    companies carrying .KQ in our ticker map — evidence about
    our suffix field, not about the venue. Every genuinely
    KOSDAQ name returned nothing."""
    import ib_5m_events as M
    assert M._probe_venue("Korea", "011200.KQ") == "KRX_KOSPI"
    assert M._probe_venue("Korea", "011210.KQ") == "KRX_KOSPI"
    assert M._probe_venue("Korea", "348370.KQ") == "KRX_KOSDAQ"


def test_kosdaq_has_a_boundary_venue_to_measure():
    """28 windows ride on it. Suggestive evidence is not a
    measurement — that conflation is how c-197 declared TPEx
    empty off two failures."""
    import ib_5m_boundary as B
    assert "Korea_KOSDAQ" in B.VENUES
    exch, ccy, probes = B.VENUES["Korea_KOSDAQ"]
    assert (exch, ccy) == ("KRX", "KRW")
    assert len(probes) >= 3
    import ib_5m_events as M
    for code, _why in probes:
        assert M._probe_venue("Korea", code + ".KQ") \
            == "KRX_KOSDAQ", code


def test_india_nse_symbols_are_truncated_to_nine_chars():
    """c-229. `symbols India` separated 46 codes perfectly by
    LENGTH — 35 resolved, longest 9; 11 unresolved, every one
    exactly 10 — and IB's own search gave the mechanism away on
    the one case where it returned anything: asked for
    BAJAJ-AUTO it offered "BAJAJ-AUT/INR@NSE".

    Asserted here as the SHAPE of the extra candidate, not as a
    claim about IB. The truncation is only ever tried after the
    full symbol, and the harvester records which form paid.
    """
    import json
    from pathlib import Path
    root = Path(__file__).resolve().parents[1]
    f = root / "data" / "ib_5m" / "India.json"
    if not f.exists():
        return
    W = json.loads(f.read_text(encoding="utf-8"))["windows"]
    ok = {v["code"].split(".")[0] for v in W.values()
          if v.get("px")}
    no = {v["code"].split(".")[0] for v in W.values()
          if not v.get("px")
          and str(v.get("note") or "").startswith("no contract")}
    if not (ok and no):
        return
    # c-231: THIS ASSERTION WAS INVERTED, and the fix failing it
    # is how I found out.
    #
    # I first wrote "every resolved symbol is <= 9 chars", which
    # described the BROKEN state — the state the truncation
    # candidate exists to end. Bill ran the fetch, five 10-char
    # names resolved (APOLLOHOSP, BAJFINANCE, BHARATFORG,
    # IDFCFIRSTB, PIDILITIND), and the test failed because the
    # code had started working. A test that fails when the bug
    # is fixed is pinning the bug.
    #
    # What should hold from here: short symbols never needed the
    # candidate, and long ones can now succeed.
    assert min(len(s) for s in no) > 9, \
        "a symbol of 9 chars or fewer failed to resolve — " \
        "length is not the whole story and the candidate needs " \
        "re-examining"
    long_ok = [s for s in ok if len(s) > 9]
    assert long_ok, \
        "no symbol longer than 9 chars has resolved yet. Either " \
        "the fetch has not reached them or the truncation " \
        "candidate is not firing."


def test_measured_venue_edges_are_actually_consumed():
    """c-229. The boundary file had Korea_KOSDAQ in it and
    _edge_for_code never read it, so 28 windows would have been
    fetched and stamped as absences against a floor we had
    already measured. A measurement no code consumes is a note,
    not a control."""
    import ib_5m_events as M
    import ib_5m_boundary as B                      # noqa: F401
    kosdaq = M._boundary_edge("Korea_KOSDAQ")
    if not kosdaq:
        return                       # not measured on this box
    assert M._edge_for_code("Korea", "348370.KQ") == kosdaq
    assert M._edge_for_code("Korea", "326030.KS") != kosdaq
    for code, venue in (("300750.SZ", "China_ChiNext"),
                        ("688981.SS", "China_STAR")):
        e = M._boundary_edge(venue)
        if e:
            assert M._edge_for_code("China", code) == e, code


def test_kosdaq_windows_drop_out_of_the_job_list():
    """With the floor at 2026-02-02, a 2015-2026 study has no
    KOSDAQ windows to ask for. Better to not request them than
    to request them and record 28 false absences."""
    import ib_5m_events as M
    if not M._boundary_edge("Korea_KOSDAQ"):
        return
    kq = [t for _r, t, *_ in M.jobs("Korea")
          if M._probe_venue("Korea", str(t)) == "KRX_KOSDAQ"]
    assert not kq, f"still asking for KOSDAQ windows: {kq[:5]}"
