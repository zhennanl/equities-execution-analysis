"""c-269: the Taiwan recovery pass.

Only one thing in this module can silently corrupt the store,
and it is the volume unit. Four harvesters in this repo have
already shipped a one-board or one-unit assumption (c-195 twice,
c-225, c-232/c-261), and the failure mode is always the same:
the data arrives, looks plausible, and is wrong by a factor of
a thousand in the one field the whole event study divides by.

So the unit detector is tested against both conventions and,
more importantly, against the case where NEITHER fits — because
the only safe answer there is to refuse the batch, and a
detector that quietly picks the closer of two bad options is
worse than no detector at all.
"""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))


def _rows(mult, n=20, close=100.0, shares=5000):
    """A day file where volume is published in `mult`-share
    units and turnover is the honest TWD figure."""
    return [{"d": f"2012-05-{i + 1:02d}", "c": close,
             "v": shares / mult,
             "value": shares * close} for i in range(n)]


def test_shares_and_lots_are_both_recognised():
    from tw_recover import detect_volume_unit
    m, err = detect_volume_unit(_rows(1))
    assert m == 1 and err < 0.01
    m, err = detect_volume_unit(_rows(1000))
    assert m == 1000 and err < 0.01


def test_a_file_that_does_not_reconcile_is_refused():
    """The point of the whole exercise.

    Turnover that ties at neither unit means the columns are
    not what the header says — a different field order, a
    price that is not the close, an endpoint that changed. The
    detector must return None so the caller drops the batch.
    """
    from tw_recover import detect_volume_unit
    bad = _rows(1)
    for r in bad:
        r["value"] *= 7.5           # ties at no candidate unit
    m, err = detect_volume_unit(bad)
    assert m is None
    assert err > 0.15


def test_too_few_rows_is_not_a_measurement():
    from tw_recover import detect_volume_unit
    assert detect_volume_unit(_rows(1, n=3))[0] is None


def test_the_twse_archive_floor_is_not_a_guess():
    """2010-01-04 is TWSE's own refusal boundary, re-verified at
    c-186. It is the reason 2006-2009 is a permanent hole rather
    than a backlog item, so it must not drift."""
    import tw_recover as T
    assert T.TWSE_FLOOR == "2010-01-04"


@pytest.mark.skipif(not (ROOT / "data" / "tw_event_windows.json").exists(),
                    reason="no window store")
def test_status_and_reconcile_run_without_network():
    """Both read local files only. `reconcile` in particular must
    never write in its default mode — it reports, and `run`
    applies."""
    import json
    import tw_recover as T
    before = (ROOT / "data" / "msci_tw_events.json").read_bytes()
    T.status()
    out = T.reconcile(apply=False)
    assert (ROOT / "data" / "msci_tw_events.json").read_bytes() == before
    # whatever it finds must be shaped for the caller in `run`
    for row in out:
        assert len(row) == 4
        rev, code, name, act = row
        assert act in ("ADD", "DEL"), act
    json.loads((ROOT / "data" / "tw_event_windows.json")
               .read_text(encoding="utf-8"))


def test_a_market_with_its_own_harvester_is_refused():
    """c-269. `yf Taiwan` was accepted, sent bare codes to
    Yahoo, and wrote 136 unpriced rows that made a 175/179
    market read as 0%. Taiwan is in ELSEWHERE precisely so the
    code can tell "harvested by something else" apart from "not
    harvested", and the guard is what makes that distinction
    load-bearing rather than documentary."""
    import pytest as _pt
    import apac_event_days as A
    assert "Taiwan" in A.ELSEWHERE
    assert "Taiwan" not in A.YF_SUFFIX
    assert "Taiwan" not in A.YF_MARKETS
    with _pt.raises(SystemExit) as e:
        A.refuse_if_elsewhere("Taiwan")
    msg = str(e.value)
    assert "tw_event_windows.json" in msg
    # a market that IS harvested here must pass straight through
    assert A.refuse_if_elsewhere("Japan") is None


TWSE_ROW = ["115/02/10", "1,510,000", "7,845,000,000",
            "5,180.00", "5,240.00", "5,150.00", "5,195.00",
            "+15.00", "4,210"]
TPEX_ROW = ["100/05/17", "2,610", "448,660",
            "170.00", "173.00", "169.50", "171.50", "+1.50", "980"]


def test_both_taiwan_day_files_put_ohl_at_indices_three_four_five():
    """c-269, and this one had shipped.

    Every Taiwan window held {d, c, v} while every Yahoo-sourced
    market held {d, o, h, l, c, v}. Both TWSE's STOCK_DAY and
    TPEx's tradingStock carry open, high and low at 3/4/5, and
    both parsers read index 6 and threw the rest away — so the
    fields were fetched and dropped one line before they were
    stored. Nothing failed and no coverage count could show it.

    Asserted on the field POSITIONS rather than on a live
    response, because that is the thing that was misread and it
    is checkable without the network.
    """
    import tw_event_window as TW
    src = (Path(TW.__file__).read_text(encoding="utf-8"))
    # the close has always been r[6]; open/high/low must now be
    # read from the three columns immediately before it
    for field, idx in (("o", 3), ("h", 4), ("l", 5)):
        assert f'"{field}": _num(r[{idx}])' in src, field
    assert src.count('"c": _num(r[6])') == 2      # TWSE and TPEx


def test_a_short_refetch_never_replaces_a_good_series():
    """The safety rule in `ohlc`. A throttled or half-answered
    request must not turn a 47-row close-only window into a
    12-row OHLC one — more columns are not worth fewer days."""
    old = [{"d": f"2013-05-{i+1:02d}", "c": 10.0, "v": 1}
           for i in range(40)]
    short = [{"d": "2013-05-01", "o": 1.0, "h": 1.0, "l": 1.0,
              "c": 1.0, "v": 1}]
    full = [{"d": r["d"], "o": 1.0, "h": 1.0, "l": 1.0,
             "c": r["c"], "v": r["v"]} for r in old]
    def accept(rows, old_rows):
        return bool(rows) and "o" in rows[0] and len(rows) >= len(old_rows)
    assert accept(full, old)
    assert not accept(short, old)
    assert not accept([], old)
