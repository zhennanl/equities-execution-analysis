"""c-259: the three ticker corrections, and the machinery that
keeps a wrong ticker from looking like missing data.

The defect class these guard against is the dangerous one. A
missing window announces itself; a WRONG window returns clean
prices for a different company and passes every downstream
sanity check. MEITU priced four of six windows against
Meituan — roughly twenty times the market cap — and nothing
complained.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))


def _db():
    import pandas as pd
    return pd.read_pickle(ROOT / "data" / "msci_changes_db.pkl")


def test_meitu_is_not_meituan():
    d = _db()
    t = set(d[(d.market == "China")
              & (d.security == "MEITU")].ticker)
    assert t == {"1357.HK"}, t
    assert "3690.HK" not in t, "3690.HK is Meituan"


def test_two_securities_never_share_one_code():
    """The rule that proved the Anhui Gujing defect without any
    external source: an A line and a B line of the same issuer
    are different securities and cannot share a listing."""
    d = _db()
    d = d[(d.year >= 2015)
          & (d.ticker.astype(str).str.strip() != "")]
    g = d.groupby(["market", "ticker"]).security.nunique()
    shared = g[g > 1]
    # the remaining shared codes are RENAMES of one issuer,
    # audited at c-202 and c-259 and listed here so a NEW one
    # cannot appear unnoticed.
    known = {("China", "002081.SZ"), ("China", "002797.SZ"),
             ("China", "601818.SS"), ("China", "688009.SS"),
             ("China", "688396.SS"), ("India", "ENRIN"),
             ("India", "IDFCFIRSTB"), ("Japan", "3288.T"),
             ("Thailand", "TTB-R.BK")}
    assert set(shared.index) <= known, (
        f"new ticker collision: {set(shared.index) - known}")


def test_bank_of_queensland_uses_the_ordinary_line():
    d = _db()
    t = set(d[(d.market == "Australia")
              & (d.security == "BANK OF QUEENSLAND")].ticker)
    assert t == {"BOQ.AX"}, t


def test_every_correction_records_why():
    """A correction that cannot say why it is right is
    indistinguishable from the error it replaced."""
    p = ROOT / "data" / "ticker_corrections.json"
    log = json.loads(p.read_text(encoding="utf-8"))
    assert log
    for r in log:
        assert r["was"] != r["now"]
        assert len(r["why"]) > 40, r


def test_a_ticker_defect_is_not_counted_as_missing_data():
    """Bill, c-259: treat the China rows as a ticker defect,
    not as absent market data, in every downstream count."""
    import apac_event_days as A
    assert "TICKER_DEFECT" in A._CAUSE
    cal = A.calendar()
    rev = next(r for r in cal if r.startswith("May1"))
    # a STAR code quoted before the STAR board opened
    cls = A._why_unpriced(
        "China", {"rev": rev}, ["688009.SS"], {})
    assert cls == "TICKER_DEFECT"
    # a code whose earliest bar post-dates the window
    eff = cal[rev][1]
    later = {"999999": "2099-01-01"}
    assert A._why_unpriced("China", {"rev": rev},
                           ["999999.SS"], later) == \
        "TICKER_DEFECT"
    # and an ordinary empty window is NOT relabelled
    assert A._why_unpriced("China", {"rev": rev},
                           ["600000.SS"], {}) == "UNEXPLAINED"
    assert eff


def test_excluded_markets_are_named_not_folded_into_the_total():
    """Quoting a coverage rate that includes a market we have
    decided not to cover flatters and misleads at once."""
    import inspect

    import apac_event_days as A
    src = inspect.getsource(A.coverage)
    assert 'startswith("EXCLUDED")' in src
    assert "EXCLUDED markets not " in src
    assert "excluded from the total" in src
