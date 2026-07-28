"""Step-2 window planner (2.2 + 2.3) — deterministic behavior."""
import numpy as np
import pandas as pd

from agents.event_window import (build_window_plan, discretion_decision,
                                 liquidity_risk_sheet, render_window_plan,
                                 sbl_utilization, start_schedule)

BASKET = pd.DataFrame([
    ["AAA.TW", "Taiwan (TWSE)", "Sell", 500_000, 1_000_000],   # 0.5 MOC
    ["BBB.TW", "Taiwan (TWSE)", "Buy", 2_000_000, 1_000_000],  # 2.0 WORK
    ["CCC.KS", "Korea (KRX)", "Sell", 6_000_000, 1_000_000],   # 6.0 MULTI
], columns=["ticker", "market", "side", "qty_shares", "adv_shares"])


def _sheet():
    return liquidity_risk_sheet(BASKET, t_mult_med=16.0,
                                t_mult_max=38.0,
                                sbl_util={"AAA": 0.97, "BBB": 0.20})


def test_sheet_buckets_footprint_and_flags():
    s = _sheet()
    assert list(s["bucket"]) == ["MOC", "WORK+MOC", "MULTI-DAY"]
    # footprint: qty / (adv * 16 * 0.30); AAA: 0.5/4.8 = 10.4%
    assert abs(s.iloc[0]["auction_footprint_pct"] - 10.4) < 0.1
    assert "LOCK RISK" in s.iloc[0]["limit_risk"]        # TW ±10%
    assert "WATCH" in s.iloc[2]["limit_risk"]            # KR ±30%
    assert s.iloc[0]["borrow"].startswith("TIGHT")
    assert s.iloc[1]["borrow"].startswith("ok")
    assert s.iloc[2]["borrow"] == "no quota data"


def test_sbl_utilization_capacity_proxy():
    """Quota col = REMAINING quota -> util = bal/(bal+quota)."""
    df = pd.DataFrame([{"ticker": "2002", "sbl_bal": 900.0,
                        "sbl_quota": 100.0},
                       {"ticker": "9999", "sbl_bal": 0.0,
                        "sbl_quota": 0.0},
                       {"ticker": "1101", "sbl_bal": np.nan,
                        "sbl_quota": 5.0}])
    u = sbl_utilization(df)
    assert u["2002"] == 0.9
    assert "9999" not in u and "1101" not in u


def test_start_schedule_dates_and_late_flag():
    s = _sheet()
    sched = start_schedule(s, "2026-09-01", participation_cap=0.25,
                           today="2026-07-28")
    multi = sched[sched["ticker"] == "CCC.KS"].iloc[0]
    # 6.0 ADV-days at 25% -> 24 days; start = Sep 1 minus 23 bdays
    assert multi["days_needed"] == 24
    assert multi["start_date"] == "2026-07-30"
    assert "start" in multi["status"]
    late = start_schedule(s, "2026-08-05", participation_cap=0.25,
                          today="2026-07-28")
    assert "LATE START" in late[late["ticker"] == "CCC.KS"
                                ].iloc[0]["status"]
    assert sched[sched["ticker"] == "AAA.TW"].iloc[0][
        "start_date"] == "T"


def test_discretion_rule_matrix():
    # no envelope -> MOC only regardless of color
    d = discretion_decision("Sell", "HIGH (+53%/30obs)", 0.0)
    assert d["decision"] == "MOC ONLY"
    # crowded delete -> work ahead
    d = discretion_decision("Sell", "HIGH (+53%/30obs)", 30.0)
    assert d["decision"].startswith("WORK AHEAD")
    assert "pressure part-spent" in d["rationale"]
    # uncrowded delete -> wait
    d = discretion_decision("Sell", "LOW (-12%/30obs)", 30.0)
    assert d["decision"].startswith("WAIT")
    # crowded add -> no pre-positioning
    d = discretion_decision("Buy", "HIGH (+84%/8obs)", 25.0)
    assert "no pre-positioning" in d["decision"]
    # uncrowded add -> pre-position within envelope
    d = discretion_decision("Buy", "LOW (-5%/8obs)", 25.0)
    assert d["decision"].startswith("PRE-POSITION up to 25%")
    # EXITING flips crowded toward uncrowded logic
    d = discretion_decision("Sell",
                            "HIGH (+40%/30obs); EXITING (-43% off peak)",
                            30.0)
    assert d["decision"].startswith("WAIT")
    assert "EXITING" in d["rationale"]
    # no data: delete waits, add uses envelope
    d = discretion_decision("Buy", None, 20.0)
    assert d["decision"].startswith("PRE-POSITION")
    assert "no data" in d["rationale"]


def test_build_and_render_end_to_end():
    plan = build_window_plan(
        BASKET, "2026-09-01", 16.0, 38.0,
        crowding_map={"AAA": "HIGH (+53%/30obs)"},
        envelopes={"AAA.TW": 30.0}, today="2026-07-28")
    assert len(plan["sheet"]) == 3
    assert len(plan["decisions"]) == 3
    md = render_window_plan(plan, "t", "2026-07-28", notes="n")
    for sec in ("2.2 Liquidity", "2.3a Start schedule",
                "2.3b Discretion", "AAA.TW", "rationale"):
        assert sec.split()[0] in md
    # every decision line carries documented evidence
    assert md.count("evidence: crowding read") == 3


def test_indicative_read_rule():
    from agents.event_window import indicative_read
    thin = indicative_read(16.0, 9.0, "Sell", 20.0)
    assert thin["read"].startswith("THIN")
    assert "retreat" in thin["action"]
    thin0 = indicative_read(16.0, 9.0, "Sell", 0.0)
    assert "no envelope left" in thin0["action"]
    rich = indicative_read(16.0, 22.0, "Buy", 10.0)
    assert rich["read"].startswith("RICH")
    assert "size UP" in rich["action"]
    inline = indicative_read(16.0, 15.0, "Sell", 10.0)
    assert inline["read"].startswith("IN LINE")
    assert indicative_read(0.0, 9.0)["read"] == "NO EXPECTATION"


def test_lifecycle_page_imports():
    """The UI page must import cleanly (render() is exercised only
    under streamlit; logic lives in agents and is tested there)."""
    import views.page6_lifecycle as p
    assert callable(p.render)
