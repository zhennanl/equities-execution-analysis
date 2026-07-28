"""Investor-type attribution (agents/investor_flow.py) — offline parser
and handoff logic on canned payloads."""
import numpy as np
import pandas as pd
import pytest

from agents.investor_flow import parse_t86, attribute_window, handoff_metrics


CANNED = {"stat": "OK", "data": [
    # code, fB, fS, fNet, fdB, fdS, fdNet, tB, tS, tNet, dealerNet,
    # dsB, dsS, dsNet, dhB, dhS, dhNet, total
    ["3665", "1,248,393", "5,611,485", "-4,363,092", "0", "0", "0",
     "4,599,708", "99,708", "4,500,000", "x", "0", "0", "0",
     "0", "0", "0", "236,908"],
    ["2330", "12,633,000", "1,000,000", "11,633,000", "0", "0", "0",
     "100,000", "50,000", "50,000", "x", "0", "0", "0",
     "0", "0", "0", "11,700,000"],
]}


def test_parse_t86_columns():
    df = parse_t86(CANNED).set_index("ticker")
    assert df.loc["3665", "foreign_net"] == pytest.approx(-4_363_092)
    assert df.loc["3665", "trust_net"] == pytest.approx(4_500_000)
    # dealer = total - foreign - trust
    assert df.loc["3665", "dealer_net"] == pytest.approx(
        236_908 - (-4_363_092) - 4_500_000)


def test_attribute_window_filters_and_orders():
    cache = {"2026-06-17": parse_t86(CANNED).to_dict(orient="records"),
             "2026-06-18": parse_t86(CANNED).to_dict(orient="records")}
    f = attribute_window(cache, ["3665"])
    assert len(f) == 2 and set(f["ticker"]) == {"3665"}
    assert list(f["date"]) == ["2026-06-17", "2026-06-18"]


def test_handoff_detected_for_add():
    # ADD day: trusts (trackers) BUY, foreigners SELL -> handoff True
    cache = {"2026-06-17": [{"ticker": "3665", "foreign_net": 2e6,
                             "trust_net": 1e5, "dealer_net": 0,
                             "total_inst_net": 2.1e6}],
             "2026-06-18": [{"ticker": "3665", "foreign_net": -4.4e6,
                             "trust_net": 4.5e6, "dealer_net": 0.1e6,
                             "total_inst_net": 0.2e6}]}
    f = attribute_window(cache, ["3665"])
    h = handoff_metrics(f, "3665", "2026-06-18", side="Buy")
    assert h["available"] and h["t_handoff"]
    assert h["arb_prepositioned"]            # foreigners were long before T


def test_no_handoff_when_same_direction():
    cache = {"2026-06-18": [{"ticker": "X", "foreign_net": 1e6,
                             "trust_net": 1e6, "dealer_net": 0,
                             "total_inst_net": 2e6}]}
    f = attribute_window(cache, ["X"])
    h = handoff_metrics(f, "X", "2026-06-18", side="Buy")
    assert h["available"] and not h["t_handoff"]


def test_coverage_table_has_implemented_markets():
    from agents.investor_flow import INVESTOR_FLOW_COVERAGE
    df = pd.DataFrame(INVESTOR_FLOW_COVERAGE)
    impl = df[df["Status"] == "IMPLEMENTED"]["Market"].tolist()
    assert "Taiwan (TWSE)" in impl and "Korea (KRX)" in impl
    assert "Taiwan (TPEx)" in impl
    assert (df["Status"] == "protocol").sum() >= 2      # honest non-claims


def test_parse_naver_frgn_canned():
    from agents.investor_flow import parse_naver_frgn
    df = pd.DataFrame({
        ("날짜", ""): ["2026.05.29", "2026.05.28", "전체"],
        ("종가", ""): [10000, 10100, None],
        ("기관", "순매매량"): ["-1,234", "+500", None],
        ("외국인", "순매매량"): ["-9,876", "-100", None],
    })
    out = parse_naver_frgn(df)
    assert len(out) == 2
    assert out.iloc[-1]["date"] == "2026-05-29"
    assert out.iloc[-1]["foreign_net"] == pytest.approx(-9876)
    assert out.iloc[-1]["inst_net"] == pytest.approx(-1234)
