"""Daily-harvest coverage and the predecessor map (c-223).

Two failures this file exists to prevent.

ONE LIST, NOT TWO. c-205 added China to harvest_all()'s market
list and left the `yf` sub-command's copy untouched. The two
disagreed for three revisions, and the visible result was a run
that printed "all stages completed" over 1,253 unpriced Chinese
windows — 60% of the APAC sample.

CURRENT SYMBOL, HISTORICAL WINDOW. Our ticker map carries the
code a company trades under today. Yahoo and the NSE bhavcopy
answer honestly for a window that predates a rename — the
symbol did not exist — and the window then looks like a
delisting.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import apac_event_days as A                        # noqa: E402


def test_china_is_in_the_harvest_list():
    """THE REGRESSION."""
    assert "China" in A.YF_MARKETS


def test_the_market_list_is_not_duplicated_in_source():
    """A literal list in two places is the defect itself."""
    src = (ROOT / "scripts" / "apac_event_days.py").read_text(
        encoding="utf-8")
    body = "\n".join(ln for ln in src.splitlines()
                     if not ln.lstrip().startswith("#"))
    assert body.count('"Singapore", "Thailand", "Malaysia"') <= 1


def test_predecessor_only_applies_before_the_change():
    """A rename must not leak backwards into a window where the
    current symbol is the right one."""
    assert A._predecessor("India", "IDFCFIRSTB",
                          "2018-07-15")[0] == "IDFCBANK"
    assert A._predecessor("India", "IDFCFIRSTB",
                          "2026-05-01") is None
    assert A._predecessor("Korea", "456040",
                          "2020-07-13")[0] == "010060"
    assert A._predecessor("Korea", "456040",
                          "2025-01-01") is None


def test_a_collision_has_no_date_so_it_always_applies():
    """BANKBETF is not a rename — it is the wrong security in
    the ticker map, and it is wrong in every period."""
    for end in ("2016-01-01", "2026-01-01"):
        assert A._predecessor("India", "BANKBETF",
                              end)[0] == "BAJAJFINSV"


def test_every_predecessor_entry_carries_a_source():
    """A symbol swap without a source is a guess that will look
    like a measurement six months from now."""
    for key, (old, since, why, src) in A.PREDECESSOR.items():
        assert old and why and src, key
        assert len(why) > 25, f"{key}: reason is too thin"
        assert since is None or len(since) == 10, key


def test_predecessor_is_tried_last_not_first():
    """Second-board and NVDR fallbacks are far more common than
    a rename; trying the rename first would risk pricing a
    window off the predecessor when the current line is right."""
    cands = A._candidates("Korea", "456040", "2020-07-13")
    syms = [c for c, _ in cands]
    assert syms[0] == "456040.KS"
    assert syms[-1] == "010060.KS"


def test_candidates_without_a_window_end_still_work():
    """Every pre-c-223 caller must keep working."""
    assert A._candidates("Thailand", "TTB-R")[0][0] == "TTB-R.BK"
    assert A._candidates("China", "601111")[0][0] == "601111.SS"


def test_taiwan_is_priced_elsewhere_not_missing():
    """Taiwan has its own delisted-safe TWSE harvester. Without
    this mapping the coverage report calls it a hole."""
    assert "Taiwan" in A.ELSEWHERE
    path, _how = A.ELSEWHERE["Taiwan"]
    assert (ROOT / path).exists(), path
    assert A._windows_for("Taiwan"), "Taiwan windows not found"
