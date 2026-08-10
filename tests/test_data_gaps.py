"""The gap checker separates three things a coverage count
cannot (c-232).

Bill is running the harvest one final time and excluding
whatever is still missing. That decision is only as good as the
distinction between "never asked", "asked and the data is not
there", and "the data is there and our code cannot reach it".

The third class is the one this file exists to protect. It is
invisible in a coverage table — a window our harvester was
never written for looks exactly like a window that failed — and
it is the class that would have quietly excluded every TPEx
name in Taiwan from the analysis.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import pytest                                      # noqa: E402

import data_gaps as G                              # noqa: E402


@pytest.fixture(scope="module")
def rows():
    """Built ONCE. five_minute() + daily() walk every job list
    in the repo, which is ~35s a call; three tests calling it
    independently turned a fast suite into a slow one."""
    return G.five_minute() + G.daily()


def test_the_three_classes_are_distinct():
    assert {G.RETRY, G.NEEDS_CODE, G.STRUCTURAL} == {
        "RETRY", "NEEDS_CODE", "STRUCTURAL"}


def test_reasons_normalise_to_one_label():
    assert G._reason(None) == "never_attempted"
    assert G._reason({"stopped_early":
                      "No market data permissions for KOSDAQ"}) \
        == "no_permission"
    assert G._reason({"stopped_early":
                      "HMDS query returned no data"}) \
        == "venue_no_history"
    assert G._reason({"note": "no contract on the primary code"}) \
        == "no_contract"
    assert G._reason({"stopped_early":
                      "empty, IB reported no error"}) == "timeout"
    assert G._reason({"confirmed_delisted": True}) \
        == "confirmed_delisted"


def test_a_suffix_that_contradicts_its_number_is_caught():
    """The c-225 lesson, applied to the daily side: the number
    is the fact and the suffix is decoration. 000909 is a
    Shenzhen code and our changes DB gives it .SS."""
    assert G._suffix_wrong("000909.SS")
    assert G._suffix_wrong("600519.SZ")
    assert not G._suffix_wrong("600519.SS")
    assert not G._suffix_wrong("000001.SZ")
    assert not G._suffix_wrong("2330")
    assert not G._suffix_wrong("0700.HK")


def test_structural_rows_always_carry_a_reason(rows):
    """An exclusion without a stated reason is indistinguishable
    from an oversight six months from now."""
    st = [r for r in rows if r["class"] == G.STRUCTURAL]
    assert st, "no structural exclusions found at all"
    for r in st:
        assert r["fix"] and len(r["fix"]) > 20, r


def test_the_plan_never_sends_taiwan_daily_to_yahoo(rows):
    """Taiwan has its own delisted-safe TWSE/TPEx harvester.
    `yf Taiwan` would harvest a different, survivors-only
    thing under the same name."""
    lines = G.plan_lines(rows)
    assert not any("yf Taiwan" in ln for ln in lines), lines


def test_philippines_is_structural_not_retry(rows):
    ph = [r for r in rows if r["market"] == "Philippines"
          and r["dataset"] == "daily"]
    assert ph
    assert all(r["class"] == G.STRUCTURAL for r in ph)


def test_report_writes_both_artifacts(rows):
    # `rows` handed in on purpose (c-274). Calling G.report()
    # bare re-walked every job list and re-parsed ~14MB of
    # window JSON, duplicating exactly the work the module
    # fixture above exists to pay for once.
    G.report(rows)
    assert (ROOT / "data" / "data_gaps.json").exists()
    doc = (ROOT / "docs" / "DATA_GAPS.md").read_text(
        encoding="utf-8")
    assert "RETRY" in doc and "STRUCTURAL" in doc
    payload = json.loads(
        (ROOT / "data" / "data_gaps.json").read_text(encoding="utf-8"))
    assert payload["rows"]
    for r in payload["rows"]:
        assert r["class"] in (G.RETRY, G.NEEDS_CODE,
                              G.STRUCTURAL)
