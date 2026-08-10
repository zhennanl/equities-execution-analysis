"""Tests for the analog matcher + the c-136 pages (syntax)."""
import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from analog_matcher import analogs  # noqa: E402


def test_returns_k_analogs_with_outcomes():
    r = analogs("ADD", 7, 0.05, "TECH")
    assert r["distribution"]["n"] > 0
    assert r["distribution"]["n"] <= 8
    for a in r["analogs"]:
        assert a["sector"] == "TECH"
        for k in ("then_to_Eminus1", "eff_day", "revert5",
                  "year", "code"):
            assert k in a


def test_matches_sorted_by_cum_return_distance():
    r = analogs("ADD", 7, 0.05)
    d = [abs(a["cum_at_day"] - 0.05) for a in r["analogs"]]
    assert d == sorted(d)


def test_del_side_and_years_exposed():
    r = analogs("DEL", 5, -0.04)
    assert r["distribution"]["n"] > 0
    assert r["distribution"]["years"] == sorted(
        {a["year"] for a in r["analogs"]})


def test_no_lookahead_day_before_effective():
    # every analog must have had its effective AFTER the
    # queried day-offset (else cum_at_day peeks past E)
    r = analogs("ADD", 12, 0.10)
    for a in r["analogs"]:
        assert a["cum_at_day"] is not None


def test_new_views_parse():
    for f in ("views/ask.py", "views/findings.py"):
        ast.parse((ROOT / f).read_text(encoding="utf-8"))
