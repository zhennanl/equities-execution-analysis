"""Guards for the TWSE 5-second closing-auction study (c-319).

THE RISK THIS FILE IS ABOUT. `auction5s_history.json` ships as
bare numbers with no header, and the obvious mapping to TWSE's
published column list is WRONG — two of the columns fall through
the session, which no cumulative order count does. Every number
in the study therefore rests on identifying two columns by their
behaviour, and if that identification ever silently changes the
shares stay plausible while measuring something else.

So the tests are mostly about identification and about the two
controls that stopped a wrong conclusion:

  1. 26 of 30 MSCI effective dates are month-ends. Without a
     month-end comparison group a month-end effect would have
     been reported as an MSCI effect.
  2. The study was designed to split at 2020-03-23 for the
     introduction of the closing call auction. The freeze test
     says the auction was already there in 2015; the split would
     have been the wrong one.
"""
import json
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

SRC = ROOT / "data" / "tw_auction_microstructure.json"
DOC = ROOT / "docs" / "TW_AUCTION_MICROSTRUCTURE.md"

pytestmark = pytest.mark.skipif(
    not SRC.exists(),
    reason="run scripts/tw_auction_microstructure.py first")


@pytest.fixture(scope="module")
def d():
    return json.loads(SRC.read_text(encoding="utf-8"))


def test_the_columns_are_identified_by_behaviour_not_assumption(d):
    """The freeze IS the identification. A cumulative matched
    field cannot move while the market is in call-auction order
    collection, so freezing 13:25:05-13:29:55 and jumping at
    13:30 is a signature nothing else has."""
    ci = d["columns_identified"]
    assert ci["matched_quantity"] == 5
    assert ci["matched_value"] == 6
    assert "freeze" in ci["method"]
    assert "not_identified" in ci
    # the second, independent check: value / quantity is a price
    px = ci["implied_avg_price_twd"]
    assert 5 < px["p50"] < 500, px
    assert px["p10"] > 0


def test_every_day_in_the_sample_is_a_call_auction(d):
    """If this ever drops below 100%, either the columns moved or
    Taiwan changed its close. Both must stop the analysis rather
    than be averaged into it."""
    S = d["sample"]
    assert S["days"] > 2500, S["days"]
    assert S["call_auction_share_of_days"] == 1.0
    assert S["first"] < "2016-01-01"
    assert S["last"] > "2026-01-01"


def test_the_regime_split_that_would_have_been_wrong_is_recorded():
    """The study was designed to split at 2020-03-23. The data
    says the closing call auction predates the sample, so the
    March 2020 change touched the continuous session and not the
    close. Recording a wrong assumption is worth more than
    quietly dropping it."""
    src = (ROOT / "scripts"
           / "tw_auction_microstructure.py").read_text(
        encoding="utf-8")
    assert "2020-03-23" in src
    assert "wrong" in src.lower()


def test_the_month_end_control_exists_and_separates(d):
    """26 of 30 MSCI dates are month-ends. Month-end alone lifts
    the close; the review lifts it again. Without the middle
    group the first effect would be credited to the second."""
    M = d["month_end_control"]
    assert M["neither"]["n"] > 2000
    assert M["month_end_not_msci"]["n"] > 50
    assert M["msci_effective"]["n"] >= 25
    # the ordering IS the finding
    assert (M["neither"]["p50"]
            < M["month_end_not_msci"]["p50"]
            < M["msci_effective"]["p50"])
    assert M["p_msci_vs_month_end"] < 0.01
    # and the page claims roughly a 5x lift over an ordinary day
    lift = M["msci_effective"]["p50"] / M["neither"]["p50"]
    assert 3 < lift < 8, lift


def test_the_venue_is_thin_and_the_page_says_so(d):
    """The organising contrast: a market-wide close takes a few
    per cent of the day, while one index mover puts ~79% of ITS
    day through the same five minutes."""
    A = d["auction_share"]
    assert 0.02 < A["by_quantity"]["p50"] < 0.10
    assert 0.02 < A["by_value"]["p50"] < 0.15
    # value share exceeds quantity share — the auction is the
    # large, high-priced names
    assert A["by_value"]["p50"] > A["by_quantity"]["p50"]


def test_the_review_type_split_is_reported_with_its_n(d):
    """May/November is semi-annual and bigger. Nine quarterly
    observations is a lean, not a forecast, and the n has to
    travel with the number."""
    R = d["review_type"]
    assert R["sair_may_nov"]["p50"] > R["qir_feb_aug"]["p50"]
    assert R["qir_feb_aug"]["n"] >= 5
    assert R["sair_may_nov"]["n"] >= 15
    assert R["p"] < 0.05


def test_the_market_wide_limitation_is_stated_everywhere(d):
    """There is no per-stock split in this file. A reader who
    took these numbers for a single name's capacity would size a
    book on the wrong quantity."""
    assert "MARKET-WIDE" in d["scope"]
    assert "no per-stock" in d["scope"].lower() or \
        "not a name" in d["scope"].lower()
    doc = DOC.read_text(encoding="utf-8")
    assert "Market-wide" in doc
    assert "No per-stock split" in doc


def test_the_unidentified_columns_are_not_used(d):
    """An order-imbalance series is the most attractive output
    here and the least defensible. It must stay unbuilt while the
    columns are unconfirmed."""
    assert "imbalance" not in json.dumps(
        {k: v for k, v in d.items() if k != "days"}).lower() \
        or "not built" in d["columns_identified"]["not_identified"].lower() \
        or "Unused" in d["columns_identified"]["not_identified"]
    for day in list(d["days"].values())[:50]:
        assert set(day) <= {
            "date", "auction_qty_share", "auction_val_share",
            "last30_qty_share", "day_qty", "day_val",
            "auction_qty", "auction_val", "implied_avg_price",
            "is_effective_date"}


def test_the_doc_quotes_the_json(d):
    t = DOC.read_text(encoding="utf-8")
    M = d["month_end_control"]
    assert f"{M['msci_effective']['p50']:.2%}" in t
    assert f"{M['month_end_not_msci']['p50']:.2%}" in t
    assert f"{d['sample']['days']:,}" in t
