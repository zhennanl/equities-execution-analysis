"""MSCI China spans three venues; one exchange code cannot
serve it (c-199).

MSCI's own description of the index: it "captures large and mid
cap representation across China A shares, H shares, B shares,
Red chips, P chips and foreign listings (e.g. ADRs)".

Before this fix, EXCH pinned all 1,431 China movers to
"SEHKNTL" — Stock Connect SHANGHAI. That is right for the .SS
names and wrong for roughly 80% of the rest. It is the third
instance of the same one-venue-per-market assumption after
Taiwan TWSE/TPEx and Korea KOSPI/KOSDAQ, so it gets a test.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import ib_5m_events as m                           # noqa: E402


def test_shanghai_goes_northbound_shanghai():
    assert m._china_venue("600519.SS")[:2] == ("SEHKNTL", "CNH")


def test_shenzhen_main_board_goes_northbound_shenzhen():
    assert m._china_venue("000333.SZ")[:2] == ("SEHKSZSE", "CNH")
    assert m._china_venue("002594.SZ")[:2] == ("SEHKSZSE", "CNH")


def test_chinext_and_star_are_their_OWN_ib_exchanges():
    """c-225 REVERSED both of these, and the reason matters.

    They asserted what I believed about the MARKETS: ChiNext is
    physically part of Shenzhen and STAR part of Shanghai, both
    true. But IB does not organise its exchange codes by which
    building the board sits in, and the c-224 pre-flight
    measured what it actually does:

        Stock('300620','SEHKSZSE','CNH') -> error 200, then
          resolved on CHINEXT and served 144 bars
        Stock('688313','SEHKNTL','CNH')  -> error 200, then
          resolved on SEHKSTAR and served 144 bars

    A test that encodes my model of the world rather than the
    vendor's answer will pass happily while the code it guards
    is wrong. These two did, for three revisions.
    """
    assert m._china_venue("300750.SZ")[:2] == ("CHINEXT", "CNH")
    assert m._china_venue("300620")[0] == "CHINEXT"
    assert m._china_venue("688981")[0] == "SEHKSTAR"
    assert m._china_venue("688313.SS")[0] == "SEHKSTAR"


def test_hong_kong_lines_stay_in_hkd():
    for t in ("2777.HK", "1088"):
        exch, ccy, _sym = m._china_venue(t)
        assert (exch, ccy) == ("SEHK", "HKD")


def test_hong_kong_codes_are_NOT_zero_padded_for_ib():
    """c-204 reversed this test, because it was pinning a bug.

    IB wants the bare number on SEHK; YAHOO wants four digits
    ("0700.HK"). The boundary probe returned "NO CONTRACT" for
    0005, 0941 and 0700 while plain "700" resolves — so the
    padding, copied over from the Yahoo path, would have failed
    every Hong Kong request.
    """
    assert m._china_venue("861.HK")[2] == "861"
    assert m._china_venue("0700.HK")[2] == "700"
    assert m._china_venue("5")[2] == "5"


def test_adr_routes_to_the_us_in_usd():
    assert m._china_venue("TAL")[:2] == ("SMART", "USD")


def test_suffix_is_stripped_from_the_symbol():
    for t in ("600519.SS", "000333.SZ", "2777.HK"):
        assert "." not in m._china_venue(t)[2]


def test_the_real_mover_set_uses_all_venues():
    """A regression on the actual data, not a toy case."""
    try:
        import pandas as pd
        df = pd.read_pickle(ROOT / "data" / "msci_changes_db.pkl")
    except Exception:                              # noqa: BLE001
        import pytest
        pytest.skip("changes DB unavailable")
    g = df[(df.market == "China") & (df.ticker != "")]
    if g.empty:
        import pytest
        pytest.skip("no China movers")
    venues = {m._china_venue(t)[0] for t in g.ticker}
    assert {"SEHKNTL", "SEHKSZSE", "SEHK"} <= venues, \
        "China must reach Shanghai, Shenzhen AND Hong Kong — " \
        "routing it all to one code silently misroutes ~80%"


def test_japan_has_an_exchange_code_now():
    assert m.EXCH.get("Japan") == ("TSEJ", "JPY")


def test_japan_is_probed_separately_for_entitlement():
    assert "Japan" in m.PROBE
