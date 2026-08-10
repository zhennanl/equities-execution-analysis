"""T86 layout handling and the T86 harvester (c-291).

THE BUG. TWSE has shipped three T86 column layouts. The parser read the
modern offsets unconditionally, so any historical day came back with
foreign = foreign + trust and trust = a GROSS SELL figure. It never
raised and the numbers looked ordinary. The Taiwan study's heaviest
years, 2015-2017, sit squarely in the 15-column era.

The fixtures are REAL responses (first rows of 2012-05-02, 2016-06-01 and
2018-06-01), not hand-written ones, so a layout assumption cannot be
smuggled into the test and the code at the same time.
"""
import gzip
import json
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from agents.investor_flow import (T86LayoutError,  # noqa: E402
                                  _T86_LAYOUTS, parse_t86)

FIX = json.loads(
    (pathlib.Path(__file__).parent / "fixtures" / "t86_layouts.json")
    .read_text(encoding="utf-8"))


def _n(x):
    return float(str(x).replace(",", ""))


@pytest.mark.parametrize("key", sorted(FIX))
def test_every_layout_parses_and_the_identity_holds(key):
    df = parse_t86(FIX[key])
    assert not df.empty
    assert len(df) == len(FIX[key]["data"])
    got = (df["foreign_net"] + df["trust_net"] + df["dealer_net"]
           - df["total_inst_net"]).abs().max()
    assert got < 1.0


@pytest.mark.parametrize("key", sorted(FIX))
def test_first_row_matches_the_published_columns(key):
    """Tie each layout to the column the exchange actually labelled,
    rather than to whatever the parser happens to do."""
    pay = FIX[key]
    lay = _T86_LAYOUTS[len(pay["fields"])]
    r = pay["data"][0]
    row = parse_t86(pay).iloc[0]
    assert row["ticker"] == str(r[0]).strip()
    assert row["foreign_net"] == sum(_n(r[i]) for i in lay["foreign"])
    assert row["trust_net"] == _n(r[lay["trust"]])
    assert row["dealer_net"] == _n(r[lay["dealer"]])
    assert row["total_inst_net"] == _n(r[lay["total"]])


def test_the_old_modern_only_offsets_would_have_been_wrong():
    """The regression itself, stated numerically.

    Old code: foreign = r[3] + r[6], trust = r[9], total = r[-1]. On an
    11-column row r[6] IS the trust column and r[9] is a gross sell, so
    'foreign' double-counted trust and 'trust' was not a net at all.
    """
    pay = FIX["11col"]
    r = pay["data"][0]
    old_foreign = _n(r[3]) + _n(r[6])
    old_trust = _n(r[9])
    row = parse_t86(pay).iloc[0]

    assert old_foreign != row["foreign_net"], \
        "fixture no longer demonstrates the bug"
    assert old_foreign == row["foreign_net"] + row["trust_net"]
    assert old_trust != row["trust_net"]
    # and the old numbers do NOT satisfy the identity — which is exactly
    # why the identity is the check that would have caught this
    assert abs(old_foreign + old_trust + row["dealer_net"]
               - row["total_inst_net"]) > 1.0


def test_an_unknown_shape_raises_rather_than_guessing():
    with pytest.raises(T86LayoutError, match="unknown T86 layout"):
        parse_t86({"fields": ["a"] * 13, "data": [["2330"] + ["1"] * 12]})


def test_a_known_shape_that_fails_the_identity_still_raises():
    """Shape selects the layout; arithmetic proves it. A future layout
    that happens to reuse a column count must not slip through."""
    pay = json.loads(json.dumps(FIX["18col"]))
    for r in pay["data"]:
        r[17] = "999,999,999"                    # break the total
    with pytest.raises(T86LayoutError, match="fail the identity"):
        parse_t86(pay)


def test_a_couple_of_odd_rows_are_dropped_not_fatal():
    pay = json.loads(json.dumps(FIX["18col"]))
    good = len(pay["data"])
    pay["data"] = pay["data"] + [["9999"] + ["0"] * 16 + ["12345"]]
    df = parse_t86(pay)
    assert len(df) == good
    assert "9999" not in set(df["ticker"])


def test_empty_payload_is_empty_not_an_error():
    assert parse_t86({"stat": "OK", "data": []}).empty


# ── harvester ────────────────────────────────────────────────────────────

def test_calendar_comes_from_real_sessions_not_weekdays():
    import tw_t86_harvest as H
    cal = H.sessions()
    assert cal and cal[0] >= H.T86_EPOCH
    assert all(a < b for a, b in zip(cal, cal[1:])), "unsorted or duped"
    # The point of using the real calendar: Taiwan closes for lunar new
    # year and typhoons, so a weekday rule would spend hundreds of
    # requests on days the exchange never opened. Measure that gap rather
    # than assert it — if it were small the harvester could stop carrying
    # a calendar dependency at all.
    import datetime as dt
    lo, hi = dt.date.fromisoformat(cal[0]), dt.date.fromisoformat(cal[-1])
    weekdays = {(lo + dt.timedelta(days=i)).isoformat()
                for i in range((hi - lo).days + 1)
                if (lo + dt.timedelta(days=i)).weekday() < 5}
    wasted = weekdays - set(cal)
    assert len(wasted) > 200, (
        f"only {len(wasted)} closed weekdays — a naive weekday rule would "
        f"be nearly as good, so the calendar dependency needs justifying")


def test_window_dates_are_a_strict_subset_that_covers_both_anchors():
    import tw_t86_harvest as H
    cal = H.sessions()
    keep = H.window_dates(cal)
    if not keep:
        pytest.skip("no event windows on disk")
    assert keep <= set(cal)
    assert len(keep) < len(cal), "windows-only saves nothing"
    w = json.loads((ROOT / "data" / "tw_event_windows.json")
                   .read_text(encoding="utf-8"))["windows"]
    for v in list(w.values())[:25]:
        for anchor in (v.get("ann"), v.get("eff")):
            if anchor and anchor in set(cal) and anchor >= H.T86_EPOCH:
                assert anchor in keep, f"{anchor} not covered"


def test_shard_round_trip_reconstructs_the_total(tmp_path, monkeypatch):
    import tw_t86_harvest as H
    monkeypatch.setattr(H, "OUT", tmp_path)
    H.write_shard("2016", {"2016-06-01": [["2330", 13012028, -45000,
                                           -620000]]})
    got = H.load_t86(start="2016-01-01", end="2016-12-31")
    row = got["2016-06-01"]["2330"]
    assert row["foreign_net"] == 13012028
    assert row["total_inst_net"] == 13012028 - 45000 - 620000
    # ticker filter
    assert H.load_t86(tickers=["9999"]) == {}


def test_shard_write_is_atomic_and_leaves_no_temp(tmp_path, monkeypatch):
    import tw_t86_harvest as H
    monkeypatch.setattr(H, "OUT", tmp_path)
    H.write_shard("2020", {"2020-01-02": [["1101", 1, 2, 3]]})
    assert (tmp_path / "2020.json.gz").exists()
    assert not list(tmp_path.glob("*.tmp"))
    with gzip.open(tmp_path / "2020.json.gz", "rt", encoding="utf-8") as fh:
        assert json.load(fh)["2020-01-02"][0][0] == "1101"


def test_dry_run_plans_without_touching_the_network(monkeypatch, capsys):
    """--dry-run must be safe to run blind: if it can reach requests at
    all, the flag is not doing its job."""
    import tw_t86_harvest as H
    monkeypatch.setattr(sys, "argv",
                        ["tw_t86_harvest.py", "--dry-run", "--windows-only"])

    def boom(*a, **k):
        raise AssertionError("dry run touched the network")

    monkeypatch.setattr(H, "fetch_day", boom)
    assert H.main() == 0
    out = capsys.readouterr().out
    assert "dry run" in out and "to fetch" in out
