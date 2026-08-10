"""Guards for the TDCC dispersion harvester (c-331).

THE BUG THESE EXIST TO CATCH, and it is worth stating because it
cost a probe run. The first version of the harvester posted five
form fields, three of which do not exist and two of which had the
wrong case, and omitted the CSRF token entirely. TDCC answered
**200 OK with 55KB of HTML** — the empty form, re-rendered. From
a traceback that is indistinguishable from success; the only tell
was that no rows came back.

So the fixture here is the ACTUAL reply from that failed attempt,
saved verbatim. Two things must hold forever after:

  1. `parse_table` must return None on it, not {} and not a row
     of zeros. A parser that yields an empty-but-truthy result
     turns a rejected request into a data point.
  2. `_form_state` must recover the four hidden fields off it, so
     the request that replaced it is built from the page rather
     than from a memory of the page.
"""
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import tdcc_dispersion_harvest as T          # noqa: E402

FIX = ROOT / "tests" / "fixtures" / "tdcc_empty_form.html"


@pytest.fixture(scope="module")
def empty_form():
    return FIX.read_text(encoding="utf-8")


def test_the_empty_form_parses_to_nothing(empty_form):
    """The exact failure mode of c-331."""
    assert T.parse_table(empty_form) is None


def test_the_hidden_fields_are_read_off_the_page(empty_form):
    """Every one of these was guessed wrong the first time."""
    st = T._form_state(empty_form)
    assert st["SYNCHRONIZER_TOKEN"], "the CSRF token is not carried"
    assert st["SYNCHRONIZER_URI"].endswith("qryStock")
    assert st["method"] == "submit"
    assert "firDate" in st


def test_the_post_body_uses_the_live_field_names(monkeypatch,
                                                 empty_form):
    """The field names are lowercase `stockNo` / `sqlMethod` and
    the date field is `scaDate`, NOT `StockNo` / `SqlMethod` /
    `scaDates`. Asserted on the body actually sent."""
    sent = {}

    class R:
        text = ""
        encoding = "utf-8"

    def fake_post(url, data=None, headers=None, **kw):
        sent.update(data or {})
        return R()

    monkeypatch.setattr(T.H, "post", fake_post)
    T._post("2408", "20260807", T._form_state(empty_form))
    assert sent["stockNo"] == "2408"
    assert sent["scaDate"] == "20260807"
    assert sent["sqlMethod"] == "StockNo"
    assert sent["method"] == "submit"
    assert sent["SYNCHRONIZER_TOKEN"]
    for dead in ("StockNo", "SqlMethod", "scaDates", "REQ_OPR",
                 "clkStockNo"):
        assert dead not in sent, f"{dead} was invented, not on the form"


def test_the_dates_come_from_the_page_not_a_calendar(empty_form):
    """TDCC's stamps move for holidays — 20260709 and 20260703 are
    both real — so a generated Friday sequence would request weeks
    that were never published and miss the ones that were."""
    ds = T.parse_dates(empty_form)
    assert len(ds) >= 50
    assert ds == sorted(ds, reverse=True)
    assert "20260709" in ds and "20260703" in ds


def test_summarise_is_shared_by_both_routes():
    """The HTML scrape and the OpenAPI feed must produce the same
    shape for the same week, or a chart could mix them."""
    rows = [{"level": i, "lots": str(i), "holders": 10.0 * i,
             "shares": 100.0 * i, "pct": float(i)}
            for i in range(1, 16)]
    rows += [{"level": 16, "lots": "差異數調整（說明4）",
              "holders": None, "shares": 0.0, "pct": 0.0},
             {"level": 17, "lots": "合　計", "holders": 1200.0,
              "shares": 12000.0, "pct": 100.0}]
    a = T._summarise(rows)
    b = T._summarise(rows, src="openapi")
    assert set(a) == set(b)
    assert a["b15_pct"] == 15.0
    assert a["n_brackets"] == 15
    assert a["total_shares"] == 12000.0


# ── c-332: the two published layouts ────────────────────────────

def _bracket(i, pct=1.0, shares=100.0, holders=10.0):
    return {"level": i, "lots": f"{i}", "holders": holders,
            "shares": shares, "pct": pct}


SHORT = [_bracket(i) for i in range(1, 16)] + [
    {"level": 16, "lots": "合　計", "holders": 150.0,
     "shares": 1500.0, "pct": 100.0}]

LONG = [_bracket(i) for i in range(1, 16)] + [
    {"level": 16, "lots": "差異數調整（說明4）", "holders": None,
     "shares": -4.0, "pct": -0.0},
    {"level": 17, "lots": "合　計", "holders": 150.0,
     "shares": 1496.0, "pct": 100.0}]


@pytest.mark.parametrize("rows,n", [(SHORT, 16), (LONG, 17)])
def test_the_total_row_is_found_in_both_layouts(rows, n):
    """c-332, and it is the bug Bill's "is the data complete?"
    caught. TDCC publishes 16 rows when there is no adjustment
    line and 17 when there is, so 合計 is level 16 in one and
    level 17 in the other. Keying on the NUMBER read the short
    layout as having no total at all and stored null — on 96 of
    204 harvested weeks, silently.

    A row number is still positional when the set of rows varies.
    The label is not."""
    s = T._summarise(rows)
    assert s["layout_rows"] == n
    assert s["total_shares"] is not None
    assert s["total_holders"] == 150.0
    assert s["n_brackets"] == 15, "the total leaked into brackets"


def test_the_adjustment_row_is_never_counted_as_a_bracket():
    s = T._summarise(LONG)
    assert s["n_brackets"] == 15
    assert s["adjustment_shares"] == -4.0
    # and the brackets plus the adjustment must reconcile
    br = sum(r["shares"] for r in LONG if 1 <= r["level"] <= 15)
    assert br + s["adjustment_shares"] == s["total_shares"]


def test_bracket_15_is_the_last_bracket_not_level_15():
    """Same reasoning: b15 is "the top holding band", and taking
    it by level number would break the moment TDCC adds or drops
    a band."""
    assert T._summarise(SHORT)["b15_pct"] == SHORT[14]["pct"]
    assert T._summarise(LONG)["b15_shares"] == LONG[14]["shares"]


HARVEST = ROOT / "data" / "tdcc_dispersion.json"


@pytest.mark.skipif(not HARVEST.exists(), reason="no harvest")
def test_the_harvest_on_disk_is_complete_and_reconciles():
    """Asserts the actual file, because "is the data complete?"
    should be answerable by the suite and not by hand."""
    import json as _json
    d = _json.loads(HARVEST.read_text(encoding="utf-8"))
    codes = [c for c in d if not c.startswith("_")]
    assert len(codes) >= 3
    offered = len(d["_meta"]["dates_offered"])
    for c in codes:
        wk = d[c]
        assert len(wk) == offered, f"{c} has {len(wk)} of {offered}"
        for date, v in wk.items():
            assert v, f"{c} {date} is empty"
            assert v["n_brackets"] == 15, (c, date)
            assert v["total_shares"], (c, date)
            br = sum(r["shares"] or 0 for r in v["rows"]
                     if not T._is_total(r) and not T._is_adjustment(r))
            adj = v.get("adjustment_shares") or 0
            assert abs(br + adj - v["total_shares"]) < 1, (c, date)
