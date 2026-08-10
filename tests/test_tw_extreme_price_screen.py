"""Guards for the §2.3.6.3 extreme-price-increase screen (c-315).

THE TWO WAYS THIS SCREEN GOES WRONG SILENTLY, both pinned below.

1. THE PERIOD UNIT. The table's footnote says "Number of days
   (Mon-Fri) prior to the price cutoff date". Reading that as
   TRADING sessions reaches about 5% further back through
   Taiwan's holiday calendar and moves the base price of every
   window — and since the screen only ever compares a number to a
   threshold, nothing raises. 250 weekdays and 250 sessions are
   nearly seven weeks apart.

2. THE VERDICT LEANING ON OUR BENCHMARK PROXY. MSCI measures
   excess against the average return of Taiwan IMI constituents in
   the same GICS sector. We do not hold that membership. The
   screen is therefore built to state, per window, the sector
   return a breach would REQUIRE, so a reader can judge it
   without trusting our equal-weighted electronics basket.
"""
import datetime as dt
import json
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import tw_extreme_price_screen as S  # noqa: E402

SRC = ROOT / "data" / "tw_extreme_price_screen.json"

pytestmark = pytest.mark.skipif(
    not SRC.exists(),
    reason="run scripts/tw_extreme_price_screen.py first")


@pytest.fixture(scope="module")
def d():
    return json.loads(SRC.read_text(encoding="utf-8"))


def test_the_thresholds_match_the_published_table():
    """Transcribed from GIMI May-2026 §2.3.6.3, p.31. Typed
    numbers are the thing this project distrusts most, so they are
    pinned against the table as printed."""
    assert S.THRESHOLDS == [
        (5, 1.0), (10, 1.0), (15, 1.0), (20, 1.0),
        (25, 2.0), (30, 2.0), (35, 2.0), (40, 2.0),
        (45, 4.0), (50, 4.0), (55, 4.0), (60, 4.0),
        (90, 5.0), (120, 8.0), (150, 15.0), (180, 15.0),
        (250, 25.0)]
    # the shape of the table: four periods per threshold step in
    # the first block, then the 2024 extension
    assert len(S.THRESHOLDS) == 17


def test_periods_are_weekdays_not_trading_sessions():
    """See note 1. A Friday minus 5 weekdays is the Friday before,
    NOT four calendar days earlier."""
    fri = dt.date(2026, 7, 31)
    assert fri.weekday() == 4
    assert S.weekdays_before(fri, 5) == dt.date(2026, 7, 24)
    assert S.weekdays_before(fri, 1) == dt.date(2026, 7, 30)
    # crossing a weekend
    mon = dt.date(2026, 7, 27)
    assert mon.weekday() == 0
    assert S.weekdays_before(mon, 1) == dt.date(2026, 7, 24)
    # 250 weekdays is ~350 calendar days, and every one of the
    # weekdays inside it counts whether Taiwan traded or not
    back = S.weekdays_before(fri, 250)
    assert 340 <= (fri - back).days <= 360, (fri - back).days


def test_the_price_cutoff_pool_is_the_last_ten_business_days(d):
    """§3.1.9. MSCI uses any ONE of them and does not say which, so
    the screen has to answer at all ten — a verdict at a single
    arbitrary date is a nine-in-ten chance of answering a
    different question than MSCI did."""
    pool = S.last_business_days(2026, 7, 10)
    assert pool[-1] == dt.date(2026, 7, 31)
    assert len(pool) == 10
    assert all(p.weekday() < 5 for p in pool)
    assert len(d["price_cutoff_pool"]) >= 8
    # every name is evaluated at every cutoff in the pool
    for code, r in d["names"].items():
        assert len(r["cutoffs"]) == len(d["price_cutoff_pool"]), code


def test_a_lookup_never_reads_a_price_from_the_future():
    """`px_on_or_before` is the whole point-in-time discipline of
    this screen. If it ever returns a later bar the window
    silently measures a different span."""
    s = [("2026-07-20", 10.0), ("2026-07-22", 11.0),
         ("2026-07-24", 12.0)]
    assert S.px_on_or_before(s, dt.date(2026, 7, 21))[0] == "2026-07-20"
    assert S.px_on_or_before(s, dt.date(2026, 7, 22))[0] == "2026-07-22"
    assert S.px_on_or_before(s, dt.date(2026, 7, 25))[0] == "2026-07-24"
    assert S.px_on_or_before(s, dt.date(2026, 7, 19)) is None


def test_the_required_sector_return_is_the_thing_that_decides(d):
    """Note 2. A breach needs r_sector <= r_stock - threshold, so
    that figure — not our proxy — carries the verdict. Where it
    falls below -100% the window is impossible on arithmetic and
    no benchmark is needed at all."""
    for code, r in d["names"].items():
        for c in r["cutoffs"]:
            for w in c["windows"]:
                if not w.get("measurable"):
                    continue
                assert w["sector_return_needed"] == pytest.approx(
                    w["stock_return"] - w["threshold"])
                assert w["arithmetically_impossible"] == (
                    w["sector_return_needed"] < -1.0)


def test_the_verdict_is_no_breach_and_is_not_marginal(d):
    """The finding. Every window at every candidate cutoff clears,
    and the closest one clears by a margin no plausible sector
    move could close — recorded so a re-run that narrows it fails
    loudly instead of quietly changing the answer."""
    assert d["any_breach_on_proxy"] is False
    for code, r in d["names"].items():
        assert r["verdict"] == "NO BREACH", code
        assert r["breaches_proxy"] == 0, code
        w = r["closest_window"]
        # the tightest case still needs the Taiwan IT sector to
        # halve, at least, over the same span
        assert w["sector_return_needed"] < -0.5, (code, w)


def test_most_windows_do_not_need_the_benchmark_at_all(d):
    """If the proxy were load-bearing everywhere, the screen would
    be an estimate wearing a verdict's clothes."""
    imp = sum(r["windows_impossible_by_arithmetic"]
              for r in d["names"].values())
    tot = sum(r["n_windows"] for r in d["names"].values())
    assert imp / tot > 0.9, f"{imp}/{tot}"


def test_the_screen_records_that_it_is_a_hard_gate(d):
    """§2.3.6.3 removes a name from Standard ADDITION eligibility
    outright — it is not a haircut on a probability. If this file
    is ever wired into the call model it must be as a gate."""
    assert d["treatment"].startswith("hard gate")
    assert "not eligible for addition" in d["treatment"]
    assert d["rulebook"].startswith("MSCI_GIMIMethodology_May2026")


def test_the_benchmark_is_declared_as_a_proxy(d):
    """We do not hold MSCI's Taiwan IMI membership by GICS sector.
    A file that quietly called our electronics basket "the
    country-sector" would be the same class of error as the
    superseded cutoff frame."""
    b = d["benchmark"]
    assert b["held"] is False
    assert "proxy" in b and b["proxy_members"] > 30
    assert "country-sector" in b["rule"]
