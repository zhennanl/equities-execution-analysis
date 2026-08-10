"""Guards for the Taiwan top-up harvester (c-292).

THE TWO BUGS THIS EXISTS TO PREVENT.

1. A top-up that silently DROPS history. The merge is the whole point of
   the script; if it ever replaces rather than unions, the cache loses
   eleven years to gain five days and nothing raises.

2. An investor label landing in the wrong bucket. The reason for using
   FinMind's long format over the exchange's positional columns is that
   categories are NAMED — so the one thing that must be tested is that an
   unrecognised name is reported rather than quietly counted as zero, or
   worse, folded into "foreign".
"""
import json
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import tw_live_topup as T  # noqa: E402


# ── merge ────────────────────────────────────────────────────────────

def test_merge_unions_and_never_loses_history():
    old = [{"date": "2026-07-30", "close": 10.0},
           {"date": "2026-07-31", "close": 11.0}]
    new = [{"date": "2026-08-03", "close": 12.0}]
    got, added = T._merge_by_date(old, new)
    assert [r["date"] for r in got] == ["2026-07-30", "2026-07-31",
                                        "2026-08-03"]
    assert added == 1


def test_merge_lets_a_restated_bar_win_without_duplicating():
    old = [{"date": "2026-07-31", "close": 11.0}]
    new = [{"date": "2026-07-31", "close": 11.5}]
    got, added = T._merge_by_date(old, new)
    assert len(got) == 1 and got[0]["close"] == 11.5
    assert added == 0, "a restatement is not a new session"


def test_merge_sorts_even_when_the_feed_does_not():
    got, _ = T._merge_by_date(
        [{"date": "2026-08-03"}], [{"date": "2026-07-31"}])
    assert [r["date"] for r in got] == ["2026-07-31", "2026-08-03"]


def test_merge_of_nothing_is_the_original():
    old = [{"date": "2026-07-31", "close": 1.0}]
    got, added = T._merge_by_date(old, [])
    assert got == old and added == 0


# ── investor labels ──────────────────────────────────────────────────

# a real response shape: long format, one row per (date, investor type)
ROWS = [
    {"date": "2026-08-03", "name": "Foreign_Investor",
     "buy": 2801976, "sell": 1938194},
    {"date": "2026-08-03", "name": "Foreign_Dealer_Self",
     "buy": 0, "sell": 0},
    {"date": "2026-08-03", "name": "Investment_Trust",
     "buy": 142006, "sell": 139},
    {"date": "2026-08-03", "name": "Dealer_self",
     "buy": 139000, "sell": 357466},
    {"date": "2026-08-03", "name": "Dealer_Hedging",
     "buy": 232601, "sell": 155196},
]


def test_nets_match_the_arithmetic_of_the_response():
    out, unknown = T._net(ROWS)
    assert not unknown
    d = out["2026-08-03"]
    assert d["foreign"] == pytest.approx(2801976 - 1938194)
    assert d["trust"] == pytest.approx(142006 - 139)
    assert d["dealer"] == pytest.approx(
        (139000 - 357466) + (232601 - 155196))


def test_foreign_follows_the_same_convention_as_t86():
    """Foreign must be the main book PLUS the foreign dealers' own
    account — T86's modern [3]+[6]. If the two sources disagree on the
    definition, every comparison between them is quietly wrong."""
    rows = [dict(ROWS[0]), {"date": "2026-08-03",
                            "name": "Foreign_Dealer_Self",
                            "buy": 500, "sell": 100}]
    out, _ = T._net(rows)
    assert out["2026-08-03"]["foreign"] == pytest.approx(
        (2801976 - 1938194) + 400)


def test_an_unknown_investor_label_is_reported_not_absorbed():
    rows = ROWS + [{"date": "2026-08-03", "name": "Sovereign_Fund",
                    "buy": 9_999_999, "sell": 0}]
    out, unknown = T._net(rows)
    assert unknown == {"Sovereign_Fund"}
    # and it must NOT have leaked into a real bucket
    assert out["2026-08-03"]["foreign"] == pytest.approx(2801976 - 1938194)


def test_missing_buy_or_sell_is_zero_not_a_crash():
    out, _ = T._net([{"date": "2026-08-03", "name": "Foreign_Investor",
                      "buy": None, "sell": 5}])
    assert out["2026-08-03"]["foreign"] == pytest.approx(-5)


# ── writes ───────────────────────────────────────────────────────────

def test_save_is_atomic_and_leaves_no_temp(tmp_path):
    p = tmp_path / "x.json"
    T._save(p, {"a": 1})
    assert json.loads(p.read_text(encoding="utf-8")) == {"a": 1}
    assert not list(tmp_path.glob("*.tmp"))


def test_status_touches_no_network(monkeypatch, capsys):
    def boom(*a, **k):
        raise AssertionError("status hit the network")

    monkeypatch.setattr(T, "_get", boom)
    assert T.cmd_status(None) == 0
    assert "no network touched" in capsys.readouterr().out


def test_called_codes_come_from_the_registered_call():
    codes = T.called_codes()
    if not codes:
        pytest.skip("no call file")
    call = json.loads((ROOT / "data" / "aug26_tw_call_v2.json")
                      .read_text(encoding="utf-8"))
    assert codes == [str(c["code"]) for c in call["calls"]]


def test_lending_units_start_unverified():
    """The lending series must not be presented as calibrated until
    `calibrate` has actually run against real overlapping days."""
    src = (ROOT / "scripts" / "tw_live_topup.py").read_text(
        encoding="utf-8")
    assert '"_lending_units": "UNVERIFIED' in src
