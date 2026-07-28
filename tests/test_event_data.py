"""Canned-payload tests for agents/event_data.py — no network."""
import numpy as np
import pandas as pd
import pytest

from agents.event_data import (
    EVENT_DATA_COVERAGE,
    block_prints,
    parse_auction_snapshot,
    parse_bfiauu,
    parse_tdcc_distribution,
    parse_twt93u,
    phase_deltas,
    short_balance_series,
    tdcc_concentration,
)

# Payload shapes copied from live probes (2026-06-10)
TWT93U = {"stat": "OK", "data": [
    ["2002", "1,000", "500", "0", "0", "1,500", "9,999",
     "20,000", "3,000", "1,000", "0", "22,000", "8,888", " "],
    ["2330", "0", "0", "0", "0", "0", "1",
     "5,000", "0", "0", "0", "5,000", "2", " "],
]}

BFIAUU = {"stat": "OK", "data": [
    ["2002", "Paired Trade", "25.10", "10,000,000", "251,000,000"],
    ["0050", "Paired Trade", "200.00", "1,000,000", "200,000,000"],
]}

TDCC_CSV = "\n".join([
    "資料日期,證券代號,持股分級,人數,股數,占集保庫存數比例%",
    "20260717,2002,1,100,50000,0.5",
    "20260717,2002,12,10,4000000,40.0",
    "20260717,2002,15,2,5950000,59.5",
    "20260717,2002,17,112,10000000,100.00",
    "20260717,9999,15,1,1,100.0",
])


def test_parse_twt93u_splits_margin_and_sbl():
    df = parse_twt93u(TWT93U)
    r = df[df["ticker"] == "2002"].iloc[0]
    assert r["margin_short_bal"] == 1500 and r["sbl_bal"] == 22000
    assert r["sbl_sold"] == 3000 and r["sbl_returned"] == 1000


def test_parse_bfiauu():
    df = parse_bfiauu(BFIAUU)
    assert len(df) == 2
    assert df[df["ticker"] == "2002"]["value"].iloc[0] == 251_000_000


def test_parse_tdcc_filters_and_concentration():
    df = parse_tdcc_distribution(TDCC_CSV, tickers=["2002"])
    assert set(df["ticker"]) == {"2002"}
    c = tdcc_concentration(df, "2002")
    # brackets<=15 only: total 10,000,000; large (>=12) 9,950,000 = 99.5%
    assert c["available"] and c["large_holder_pct"] == pytest.approx(99.5)
    assert c["retail_holders"] == 100


def test_auction_snapshot_parser_handles_ladders_and_dashes():
    s = parse_auction_snapshot(
        {"c": "2330", "z": "1000.0", "tv": "5,000", "v": "40,000",
         "b": "999.0_998.0_997.0", "a": "-"})
    assert s["indicative_price"] == 1000.0
    assert s["indicative_volume_lots"] == 5000
    assert s["best_bid"] == 999.0 and np.isnan(s["best_ask"])


def _synthetic_cache():
    # Short build pre-ann (10->14k), surge A->T (14->30k), unwind after
    dates = pd.bdate_range("2026-05-01", "2026-06-10").strftime("%Y-%m-%d")
    cache = {"short": {}}
    for i, d in enumerate(dates):
        if d < "2026-05-12":
            total = 10000 + 600 * i
        elif d <= "2026-05-29":
            total = 14000 + 1200 * (i - 6)
        else:
            total = 30000 - 2000 * (i - 20)
        cache["short"][d] = {"1102": [total * 0.2, total * 0.8]}
    return cache


def test_phase_deltas_signs():
    cache = _synthetic_cache()
    s = short_balance_series(cache, "1102")
    p = phase_deltas(s, "2026-05-12", "2026-05-29")
    assert p["available"]
    assert p["pre_ann_build"] > 0          # shorts built before announcement
    assert p["ann_to_T"] > 0               # kept building into T
    assert p["post_T"] < 0                 # unwound after effective
    assert p["ann_to_T_sbl"] > p["ann_to_T_margin"]  # SBL-led


def test_block_prints_window():
    cache = {"blocks": {
        "2026-06-10": [["2002", "Paired Trade", 25.1, 1e6, 2.5e7]],
        "2026-06-30": [["2002", "Paired Trade", 25.1, 1e6, 2.5e7]],
    }}
    b = block_prints(cache, "2002", "2026-06-01", "2026-06-18")
    assert b["n_prints"] == 1 and b["total_value_twd"] == 2.5e7


def test_registry_honest_statuses():
    st = {k: v["status"] for k, v in EVENT_DATA_COVERAGE.items()}
    assert st["short_balances_tw"] == "IMPLEMENTED"
    assert "latest-week" in st["tdcc_distribution"]
    assert "live-only" in st["indicative_auction_tw"].lower()
    assert st["etf_units"] == "PROTOCOL"


# ---------------------------------------------------- 7i improvement layer

def _series_build(pre_growth, mid_growth, post_growth):
    dates = pd.bdate_range("2026-05-01", "2026-06-10")
    total, rows = 10000.0, []
    for d in dates:
        ds = d.strftime("%Y-%m-%d")
        g = pre_growth if ds < "2026-05-12" else \
            mid_growth if ds <= "2026-05-29" else post_growth
        total *= (1 + g)
        rows.append({"date": d, "margin_short": total * 0.2,
                     "sbl": total * 0.8, "total_short": total})
    return pd.DataFrame(rows).set_index("date")


def test_crowding_score_bands():
    from agents.event_data import crowding_score
    hot = crowding_score(_series_build(0.06, 0, 0), "2026-05-12")
    cold = crowding_score(_series_build(0.001, 0, 0), "2026-05-12")
    assert hot["crowding"] == "HIGH" and cold["crowding"] == "LOW"


def test_crowding_overlay_reads():
    from agents.event_data import crowding_overlay
    cache = {"short": {}}
    for d in pd.bdate_range("2026-05-01", "2026-05-11"):
        i = (d - pd.Timestamp("2026-05-01")).days
        cache["short"][d.strftime("%Y-%m-%d")] = {
            "AAA": [0, 10000 * (1 + 0.08 * i)],   # hot, flagged
            "BBB": [0, 10000],                    # cold, flagged
            "CCC": [0, 10000 * (1 + 0.08 * i)],   # hot, NOT flagged
        }
    df = crowding_overlay({"AAA": True, "BBB": True, "CCC": False},
                          cache, "2026-05-12")
    reads = dict(zip(df["ticker"], df["read"]))
    assert reads["AAA"].startswith("CONSENSUS")
    assert reads["BBB"].startswith("UNPRICED")
    assert reads["CCC"].startswith("STREET-ONLY")


def test_drift_composition_labels():
    from agents.event_data import drift_composition
    s = _series_build(0.0, 0.01, 0.0)     # modest SBL build A->T
    heavy_long = drift_composition(s, -1_000_000, "2026-05-12",
                                   "2026-05-29")
    assert heavy_long["composition"] == "LONG_SELLER_LED"
    short_led = drift_composition(s, -2_000, "2026-05-12", "2026-05-29")
    assert short_led["composition"] == "SHORT_LED"
    assert not drift_composition(s, +5_000, "2026-05-12",
                                 "2026-05-29")["available"]


def test_completion_clock_phases_and_settlement_guard():
    from agents.event_data import completion_clock
    done = completion_clock(_series_build(0.02, 0.03, -0.25),
                            "2026-05-29")
    assert done["phase"].startswith("MOSTLY_DONE")
    flat = completion_clock(_series_build(0.02, 0.03, 0.0), "2026-05-29")
    assert flat["phase"] == "NOT_STARTED"
    dates = pd.bdate_range("2026-05-01", "2026-06-01")   # 1 post session
    early = completion_clock(_series_build(0.02, 0.03, -0.25).loc[:  \
        "2026-06-01"], "2026-05-29")
    assert early["phase"].startswith("PRE-SETTLEMENT")


def test_crowding_adjusted_params_and_frontier_hook():
    from agents.event_data import crowding_adjusted_params
    p_hi, r_hi = crowding_adjusted_params(500, "HIGH")
    p_lo, r_lo = crowding_adjusted_params(500, "LOW")
    assert p_hi < 500 < p_lo and r_hi > 0.5 > r_lo
    # hook end-to-end: a crowded multi-day delete still gets a frontier
    from agents.index_flow import recommend_execution
    flows = pd.DataFrame([{"ticker": "DDD", "side": "Sell",
                           "bucket": "MULTI-DAY", "adv_days": 5.0}])
    out = recommend_execution(flows, crowding={"DDD": "HIGH"})
    assert len(out["recommendations"]) == 1
    assert "DDD" in out["frontiers"]


def test_etf_creation_proxy():
    from agents.event_data import etf_creation_proxy
    cache = {"blocks": {"2026-06-10":
                        [["0050", "Paired Trade", 200.0, 1e6, 2e8]]}}
    p = etf_creation_proxy(cache, "0050", "2026-06-01", "2026-06-18")
    assert p["n_prints"] == 1 and p["creation_proxy_value_twd"] == 2e8


def test_crowding_flips_buy_strategy():
    """HIGH crowding (pressure part-spent, bigger bounce) makes
    pre-positioning optimal for a large buy; baseline stays S3."""
    from agents.index_flow import recommend_execution
    flows = pd.DataFrame([{"ticker": "X", "side": "Buy",
                           "bucket": "MULTI-DAY", "adv_days": 7.3}])
    base = recommend_execution(flows)
    hot = recommend_execution(flows, crowding={"X": "HIGH"})
    pick = lambda o: (o["recommendations"].iloc[0]["strategy"]
                      if hasattr(o["recommendations"], "iloc")
                      else o["recommendations"][0]["strategy"])
    assert pick(base).startswith("S3") and pick(hot).startswith("S2")


# ---------------------------------------- multi-market crowding (8g)

def test_parse_sfc_short_csv_zero_pads_codes():
    from agents.event_data import parse_sfc_short_csv
    txt = ("Date,Stock Code,Stock Name,Shares,HKD\n"
           "17/07/2026,1,CKH HOLDINGS,53772769,3807112045\n"
           "17/07/2026,177,JIANGSU EXPRESS,8000000,64000000\n"
           "bad,row\n")
    df = parse_sfc_short_csv(txt)
    assert list(df["ticker"]) == ["0001", "0177"]
    assert df.iloc[1]["short_shares"] == 8000000


def test_parse_tpex_margin_short_balance_column():
    from agents.event_data import parse_tpex_margin
    payload = {"tables": [{"data": [
        ["6223", "MPI", "966", "43", "66", "0", "943", "39", "3.84",
         "24,495", "6", "1", "3", "0", "1,234", "0", "0.01",
         "24,495", "0", ""],
        ["00679B", "bond ETF", *[""] * 18]]}]}
    df = parse_tpex_margin(payload)
    assert len(df) == 1                      # non-digit code dropped
    assert df.iloc[0]["ticker"] == "6223"
    assert df.iloc[0]["short_bal_lots"] == 1234.0


def test_merge_into_short_cache_roundtrip_series():
    """Any market's frame lands in the TWT93U schema and
    short_balance_series reads it back unchanged."""
    import pandas as pd
    from agents.event_data import (merge_into_short_cache,
                                   short_balance_series)
    cache = {}
    for date, bal in (("2026-07-01", 100.0), ("2026-07-08", 150.0),
                      ("2026-07-15", 130.0)):
        df = pd.DataFrame([{"ticker": "0177", "short_shares": bal}])
        merge_into_short_cache(cache, date, df, "short_shares")
    s = short_balance_series(cache, "0177")
    assert len(s) == 3 and s["total_short"].iloc[-1] == 130.0


def test_crowding_sources_registry_complete():
    """Every covered pack market has an honest status entry."""
    from agents.event_data import CROWDING_SOURCES
    for mkt in ("Taiwan", "Japan", "Korea", "China", "India",
                "Malaysia", "Indonesia", "HongKong"):
        s = CROWDING_SOURCES[mkt]
        assert any(k in s["status"]
                   for k in ("LIVE", "PROTOCOL", "STRUCTURAL"))
        assert s["source"]


def test_crowding_reads_multi_market_label():
    """crowding_reads works on a weekly-cadence cache and labels the
    actual observation count (no fake '30d' on 5 weekly points)."""
    import pandas as pd
    from agents.event_data import merge_into_short_cache
    from agents.review_engine import crowding_reads
    cache = {}
    for i, bal in enumerate((100, 110, 120, 128, 140)):
        df = pd.DataFrame([{"ticker": "0027", "short_shares": bal}])
        date = f"2026-0{6 + (5 + 7 * i) // 30}-{(5 + 7 * i) % 30:02d}"
        merge_into_short_cache(cache, date, df, "short_shares")
    reads = crowding_reads(cache, ["0027.HK"])
    assert reads["0027"].startswith("HIGH (+40%/5obs")
    assert crowding_reads(None, ["0027.HK"]) == {}
