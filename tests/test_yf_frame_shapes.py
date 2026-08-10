"""The yfinance frame-shape bug that ate ~50 windows (c-198).

yfinance 1.5.1 documents `multi_level_index` as "Always return a
MultiIndex DataFrame? Default is True", so download() hands back
MultiIndex columns EVEN FOR A SINGLE TICKER. The old parse only
indexed by ticker when the batch had two or more symbols, so
one-symbol reviews raised KeyError inside a bare `except` and
were written empty with no error printed.

The signature in the stored data: 55 empty windows in
one-symbol reviews, 11 in multi-symbol reviews. REECE, QANTAS,
CATHAY PACIFIC, HANG LUNG, UOL, GENTING SINGAPORE, TOP GLOVE
and RENESAS all trade today.

These tests build both frame shapes by hand — no network — so
the parse is pinned regardless of what yfinance does next.
"""
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import apac_event_days as m                        # noqa: E402

IDX = pd.to_datetime(["2024-05-01", "2024-05-02"])
VALS = {"Open": [10.0, 11.0], "High": [12.0, 12.5],
        "Low": [9.5, 10.5], "Close": [11.5, 12.0],
        "Volume": [1000.0, 2000.0]}


def _ticker_major(sym):
    """group_by='ticker' -> level 0 is the ticker."""
    return pd.DataFrame(
        {(sym, k): v for k, v in VALS.items()}, index=IDX)


def _column_major(sym):
    """group_by='column' (the default) -> level 0 is the field."""
    return pd.DataFrame(
        {(k, sym): v for k, v in VALS.items()}, index=IDX)


def _flat():
    return pd.DataFrame(VALS, index=IDX)


@pytest.mark.parametrize("build", [_ticker_major, _column_major])
def test_multiindex_single_ticker_parses(build):
    """THE REGRESSION. This shape returned zero rows before."""
    rows, why = m._rows(build("REH.AX"), "REH.AX")
    assert why is None, why
    assert len(rows) == 2
    assert rows[0]["c"] == 11.5
    assert rows[0]["o"] == 10.0
    assert rows[0]["v"] == 1000.0


def test_flat_frame_still_parses():
    rows, why = m._rows(_flat(), "REH.AX")
    assert why is None and len(rows) == 2


def test_multi_symbol_batch_picks_the_right_column():
    a, b = _ticker_major("AAA.AX"), _ticker_major("BBB.AX")
    b[("BBB.AX", "Close")] = [99.0, 98.0]
    px = pd.concat([a, b], axis=1)
    rows, _ = m._rows(px, "BBB.AX")
    assert [r["c"] for r in rows] == [99.0, 98.0]


def test_empty_frame_reports_a_reason_not_silence():
    rows, why = m._rows(pd.DataFrame(), "X.AX")
    assert rows == [] and why, \
        "an empty result must carry a reason — silent [] is " \
        "what hid this bug for a whole harvest"


def test_ohlc_is_present_not_close_only():
    rows, _ = m._rows(_ticker_major("REH.AX"), "REH.AX")
    assert set(rows[0]) == {"d", "o", "h", "l", "c", "v"}


def test_nvdr_line_falls_back_to_the_ordinary_share():
    c = m._candidates("Thailand", "TTB-R")
    assert c[0][0] == "TTB-R.BK"
    assert c[1][0] == "TTB.BK"


def test_nz_bond_ticker_falls_back_to_the_equity():
    c = m._candidates("NewZealand", "MCY040")
    assert [s for s, _ in c] == ["MCY040.NZ", "MCY.NZ"]


def test_nz_plain_ticker_gets_no_spurious_fallback():
    assert len(m._candidates("NewZealand", "EBO")) == 1


def test_foreign_primary_listing_drops_the_local_suffix():
    assert m._candidates("Singapore", "GRAB")[0][0] == "GRAB"
    assert m._candidates("HongKong", "FUTU")[0][0] == "FUTU"


def test_korea_keeps_both_boards():
    assert [s for s, _ in m._candidates("Korea", "68760")] == \
        ["068760.KS", "068760.KQ"]


def test_hong_kong_codes_are_zero_padded():
    assert m._candidates("HongKong", "101")[0][0] == "0101.HK"
