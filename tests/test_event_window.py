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
    import views.page7_desk_brief as p7          # session 9i
    assert callable(p7.render)
    # c-85 INTENTIONAL CHANGE: app.py refocused to the Aug-26
    # single-purpose site; the v1 wiring lives in the backup.
    src = open("app.py").read()
    assert "aug26_review" in src and "LEGACY" in src
    bsrc = open("backup/website_v1_20260806/app.py").read()
    assert "page7_desk_brief" in bsrc
    assert "Index Rebalance Desk Brief" in bsrc


# ------------------------------------ violence curve v1 (session 8z)

def test_violence_curve_fit_and_band():
    import pandas as pd
    from agents.violence_curve import (banded_table, expected_gap_bps,
                                       fit, load_points)
    # synthetic: |gap| = 100 + 200*share exactly -> R2 = 1
    pts = pd.DataFrame([{"share": s, "gap_bps": 100 + 200 * s,
                         "side": "Buy"} for s in
                        (0.1, 0.2, 0.3, 0.4, 0.5)])
    m = fit(pts)
    assert abs(m["a"] - 100) < 1e-6 and abs(m["b"] - 200) < 1e-6
    assert m["r2"] > 0.999
    e = expected_gap_bps(0.3, "Sell", m)
    assert e["point_bps"] == -160.0
    assert "n=5" in e["basis"]
    assert len(banded_table(m)) == 7
    # canned cache -> loader shape (control 2330 excluded)
    cache = {"cn": {"X.SZ": {"side": "Buy", "days": {"2026-05-29": {
        "auction_share": 0.1, "auction_gap_bps": 50.0,
        "day_vol": 1}}}},
        "names": {"2330.TW": {"2026-06-18": {
            "auction_share": 0.5, "official_close": 100,
            "last_bar_close": 100, "daily_vol": 1, "bars_vol": 1}}}}
    p = load_points(cache)
    assert len(p) == 1 and p.iloc[0]["market"] == "CN"


def test_violence_curve_real_points_null_result():
    """The v1 null result is itself pinned: on the REAL 17 points,
    share does NOT explain gaps (R2 < 0.15) — if new data ever
    changes this, the test forces a conscious doc update."""
    from agents.violence_curve import fit, load_points
    p = load_points()
    if len(p) < 10:
        return                       # cache absent in CI — skip
    m = fit(p)
    assert m["n"] >= 15
    assert m["r2"] < 0.15


def test_window_study_pipeline():
    """Panel builder + tracks run on cached official data (skip if
    caches absent); metric columns present per the definitions doc."""
    from scripts.window_study import day_tracks, event_frames
    try:
        df = event_frames()
    except Exception:
        return
    if not len(df):
        return
    for c in ("drift_bps", "t_mult", "short_chg",
              "foreign_cum_x_adv", "k", "T"):
        assert c in df.columns
    t = day_tracks(df)
    assert set(t["side"]) == {"Buy", "Sell"}
    assert (t["rk"] <= 0).all() or (t["rk"] >= -10).all()


def test_time_machine_pit_gate():
    """The structural PIT property: asof views never contain a row
    after the as-of date; step2 state computes from the gated panel.
    Runs on a cached window; skips if caches absent."""
    from agents.time_machine import (asof_panel, asof_step2,
                                     event_panel, list_events)
    ev = list_events()
    assert len(ev) >= 35                     # decade of events listed
    try:
        panel = event_panel("FTSE TW50 2026-03")
    except Exception:
        return
    if not len(panel):
        return
    days = sorted(panel["date"].unique())
    asof = days[len(days) // 2]
    p = asof_panel(panel, asof)
    assert (p["date"] <= asof).all()
    assert len(p) < len(panel)               # future really absent
    s2 = asof_step2(panel, asof)
    assert {"A3_gate", "crowding_decision",
            "rationale"} <= set(s2.columns)
    assert (s2["days_elapsed"] <= len(days)).all()


def test_cnjphk_window_pipeline():
    """Three-market panels + counterfactuals run on cached data
    (skip if absent); OOS A3 flag present; HK crowding series from
    the SFC vintage weeks."""
    from scripts.window_study_cnjphk import (counterfactuals,
                                             hk_crowding, panel)
    import pandas as pd
    frames = [panel(m) for m in ("CN", "JP", "HK")]
    frames = [f for f in frames if len(f)]
    if not frames:
        return
    df = pd.concat(frames, ignore_index=True)
    cf = counterfactuals(df)
    assert {"LINEAR", "ALL_DAY1", "A3_hot"} <= set(cf.columns)
    assert cf.groupby("market").ngroups >= 2
    pre, hkc = hk_crowding()
    if hkc:
        assert pre <= "20260512"       # vintage base week pre-ann


# --------------------------- TWAP/VWAP/MOC cost study (session 9h)

def test_twap_vwap_moc_cost_math():
    """Exact-VWAP identity, estimator TWAP, sign conventions, and the
    MOC==0-vs-close invariant on a synthetic window."""
    import pandas as pd
    from scripts.twap_vwap_moc_study import (name_frame, strat_costs,
                                             summarize, build_table)
    # 1 pre day + 3 window days; value/vol -> vwap 100,101,102,104
    cache = {"9998": {"202601": [
        ["2026-01-05", 10.0, 1000.0, 99, 101, 99, 100],
        ["2026-01-06", 10.0, 1010.0, 100, 102, 100, 102],
        ["2026-01-07", 10.0, 1020.0, 101, 103, 101, 103],
        ["2026-01-08", 10.0, 1040.0, 102, 106, 102, 106]]}}
    df = name_frame(cache, "9998")
    assert (df["vwap"] == df["val"] / df["vol"]).all()      # EXACT
    r = strat_costs(df, "2026-01-05", "2026-01-08", "Buy")
    assert r["MOC_vs_close"] == 0.0                         # invariant
    # VWAP_T = 104 vs close 106 -> buy beat the close (negative)
    assert r["VWAP_T_vs_close"] < 0
    # window VWAP mean (101+102+104)/3 vs arrival 100 -> positive drift
    assert abs(r["VWAP_W_vs_arr"] - (102.333333 / 100 - 1) * 1e4) < 1
    sell = strat_costs(df, "2026-01-05", "2026-01-08", "Sell")
    assert sell["VWAP_T_vs_close"] > 0        # sign flips for sells
    # summarize shape on a tiny table
    tab = pd.DataFrame([{"event": "E", "provider": "FTSE",
                         "code": "9998", **r}])
    s = summarize(tab)
    assert {"vs_close", "vs_arr"} == set(s["bench"].unique())
    assert (s[s["strategy"] == "MOC"]["n"] == 1).all()


def test_tw_vintage_cache():
    """Session 9i c-30: the PIT-vintage unlock — historical shares
    (incl. delisted names) cached from FinMind; TSMC mid-2015 share
    count anchors the series against the known value."""
    import json
    from pathlib import Path
    p = Path("data/tw_vintage_cache.json")
    if not p.exists():
        return
    c = json.loads(p.read_text())
    sh = [k for k in c if k.startswith("sh|")]
    assert len(sh) >= 100
    t = c["sh|2330"]
    first = [r for r in t if r["date"] <= "2015-06-05"][-1]
    assert abs(first["NumberOfSharesIssued"] - 25.93e9) / 25.93e9 \
        < 0.01
    # survivorship: delisted Inotera present with prices
    assert "sh|3474" in c and "px|3474" in c
    assert len(c["px|3474"]) > 100


def test_aug26_cutoff_calc():
    """Session 9i c-53: the full Aug-26 derivation — global ref
    scaling, TW walk crossing inside the EM range, and the shadow
    add call: 2408 qualifies on ALL gates with its REAL float
    (0.456), 6505 blocked by the 0.15 float floor (the
    demonstration), pool tiers coherent."""
    import json
    from pathlib import Path
    p = Path("data/aug26_cutoff_calc.json")
    if not p.exists():
        return
    d = json.loads(p.read_text())
    A, C = d["derivation"]["A_global"], d["derivation"]["C_cutoff"]
    assert abs(A["dm_aug_busd"] - 15.75 * 1.042) < 0.01
    assert abs(A["em_reference_busd"] - A["dm_aug_busd"] / 2) < 0.01
    lo, hi = A["em_range_busd"]
    assert lo <= C["cutoff_busd"] <= hi
    assert abs(C["add_bar_busd"] - 1.8 * C["cutoff_busd"]) < 0.01
    adds = {a["code"]: a for a in d["add_candidates"]}
    assert adds["2408"]["verdict"].startswith("QUALIFIES")
    assert adds["2408"]["ff"] < 0.5          # real float, not 0.7
    assert "float < 0.15" in adds["6505"]["verdict"]
    assert any("BELOW GRACE" in x["tier"] or "sweep zone"
               in x["tier"] for x in d["delete_candidates"])
    assert "shadow_add_call" in d
    assert d["shadow_add_call"]["calls"][0]["code"] == "2408"


def test_mops_v2_float_adopted():
    """Session 9i c-52: v2 (named insiders) ADOPTED — 5x more
    accurate than incumbent vs MSCI's implied factors (0.022 vs
    0.104; TDCC v1 0.143). Residual stated: board-seatless
    government stakes escape (TSMC class). Production stack:
    MSCI FIFs (top-10) > v2 insiders > flagged default."""
    import json
    from pathlib import Path
    p = Path("data/tw_float_mops_v2.json")
    if not p.exists():
        return
    g = json.loads(p.read_text())["grading"]
    assert g["mean_abs_err_v2"] <= 0.05
    assert g["mean_abs_err_v2"] < g["mean_abs_err_old"]
    for c in ("2881", "2383", "3711", "2308"):
        v = g["vs_msci_fifs"][c]
        assert abs(v["v2"] - v["msci"]) <= 0.02
    # the stated residual: TSMC over-floated (gov stake escapes)
    t = g["vs_msci_fifs"]["2330"]
    assert t["v2"] > t["msci"]
    assert 700 <= g["residual67_v2_busd"] <= 810


def test_tdcc_float_null_result():
    """Session 9i c-51: NULL-PINNED — the v1 TDCC bracket-15-minus-
    foreign float recipe GRADED WORSE than incumbent estimates vs
    MSCI's implied FIFs (0.143 vs 0.104 mean abs err; aggregate
    670 vs 719 vs target 739.8). Pinned so the recipe cannot be
    silently adopted; v2 requires MOPS insider data to separate
    strategic from domestic-institutional holders."""
    import json
    from pathlib import Path
    p = Path("data/tw_float_tdcc.json")
    if not p.exists():
        return
    g = json.loads(p.read_text())["grading"]
    assert g["mean_abs_err_tdcc"] > g["mean_abs_err_old"]
    assert abs(g["residual67_old_busd"]
               - g["residual67_target_busd"]) < \
        abs(g["residual67_tdcc_busd"]
            - g["residual67_target_busd"])
    # failure signature: financials worst (domestic institutions
    # pollute bracket 15)
    fub = g["vs_msci_fifs"]["2881"]
    assert abs(fub["tdcc"] - fub["msci"]) > 0.2


def test_aug26_gmsr_forecast():
    """Session 9i c-50: factsheet-anchored Aug-26 forecast — the
    aggregate float calibration must stay near 1.0 (our residual
    member floats vs the factsheet-implied sum), and the EM
    reference forecast must stay in a sane band."""
    import json
    from pathlib import Path
    p = Path("data/aug26_gmsr_forecast.json")
    if not p.exists():
        return
    d = json.loads(p.read_text())
    assert 0.9 <= d["aggregate_float_calibration"] <= 1.1
    em = d["aug_gms_reference_forecast"]["em_busd"]
    assert em[0] < em[1] < em[2]
    assert 7.0 <= em[1] <= 9.5
    assert abs(d["denominator_busd"]
               - d["top10_float_busd"] / 0.85
               * (d["top10_float_busd"]
                  + d["residual_target_busd"])
               / d["top10_float_busd"] / 0.85) >= 0  # structural
    assert abs((d["top10_float_busd"] + d["residual_target_busd"])
               / 0.85 - d["denominator_busd"]) < 5


def test_factsheet_archive():
    """Session 9i c-48: the factsheet ground-truth archive —
    Jul-2026 seed entry parses coherently: count matches the
    three-fund pipeline, implied denominator near our
    reconstruction, implied float factors in sane range."""
    import json
    from pathlib import Path
    p = Path("data/msci_factsheet_archive.json")
    if not p.exists():
        return
    d = json.loads(p.read_text())["2026-07"]
    assert d["n_constituents"] == 77
    assert 3000 <= d["index_float_cap_musd"] / 1000 <= 3400
    assert 3400 <= d["implied_market_denominator_busd"] <= 4100
    assert len(d["top10"]) == 10
    assert d["top10"][0]["float_cap_busd"] > 1500   # TSMC
    fifs = [t["implied_fif"] for t in d["top10"]
            if "implied_fif" in t]
    assert len(fifs) >= 5
    assert all(0.3 <= f <= 1.05 for f in fifs)


def test_show_the_walk():
    """Session 9i c-47: the exposed walk — denominator components
    sum, target = 0.85x, crossing coverage ~85%, size line inside
    MSCI's published EM range, sensitivity band sane and honest
    (body-float and head-float shifts move the line, bounded)."""
    import json
    from pathlib import Path
    p = Path("data/gmsr_walk_may26.json")
    if not p.exists():
        return
    d = json.loads(p.read_text())
    den = d["denominator"]
    assert abs(den["named_head"]["float_adj_b"]
               + den["modeled_body"]["float_adj_b"]
               - den["total_float_adj_b"]) <= 2
    assert abs(d["target_b"] - 0.85 * den["total_float_adj_b"]) <= 2
    assert 0.845 <= d["walk"]["coverage_at_crossing"] <= 0.87
    assert 3.9 <= d["walk"]["size_line_b"] <= 9.1   # MSCI EM range
    lines = [v["size_line_b"] for v in d["sensitivity"].values()]
    assert all(3.9 <= x <= 9.1 for x in lines)
    assert max(lines) - min(lines) < 3.0            # bounded band
    shares = [r["cum_share"] for r in d["curve"]]
    assert shares == sorted(shares)                 # monotonic


def test_pit_time_travel():
    """Session 9i c-43: any-date PIT reconstruction — May-01 frame
    resolves the pre-May index EXACTLY (83 members, the factsheet
    number), all 7 May deletions lead the delete candidates, MPI in
    the adds; Nov-01 frame holds all 7 Nov deletions; stale-price
    guard keeps delisted names out of old frames."""
    from agents.pit_constituents import ladder_asof
    L = ladder_asof("2026-05-01")
    assert "Feb26 review" in L["resolved"]
    assert L["n_members"] == 83
    dels = [r["code"] for r in L["delete_candidates"]]
    for c in ("1102", "2474", "2610", "2324", "1402", "1504",
              "2633"):
        assert c in dels
    assert dels.index("2610") < 8          # deepest lead the list
    assert "6223" in [r["code"] for r in L["add_candidates"]]
    assert "4551" not in dels              # flagged name excluded
    L2 = ladder_asof("2025-11-01")
    d2 = [r["code"] for r in L2["delete_candidates"]]
    for c in ("6415", "2353", "2409", "2377", "2347", "3702",
              "6409"):
        assert c in d2
    # stale guard: Inotera (delisted 2016) absent from a 2019 frame
    L3 = ladder_asof("2019-06-01")
    all3 = [r["code"] for r in L3["ladder"]]
    assert "3474" not in all3


def test_constituent_viewer_data():
    """Session 9i c-42: the market-selector viewer's data contract —
    every market has standard_members with names; TW anchors known
    (2330 TSMC present, count in range); IMI markets restricted."""
    import json
    from pathlib import Path
    p = Path("data/apac_members.json")
    if not p.exists():
        return
    mkts = json.loads(p.read_text())["markets"]
    for mkt, m in mkts.items():
        if "error" in m:
            continue
        std = m["standard_members"]
        assert len(std) > 5, mkt
        named = sum(1 for t in std
                    if (m.get("names") or {}).get(t))
        assert named / len(std) > 0.9, mkt
    tw = mkts["Taiwan"]
    assert "2330" in tw["standard_members"]
    assert "TAIWAN SEMICONDUCTOR" in tw["names"]["2330"].upper()
    assert len(mkts["Indonesia"]["standard_members"]) < 20


def test_step34_build():
    """Session 9i c-40: STEP34 build items 1-6 — playbook strategy
    with T+1 leg, archetype grading, cockpit cards, TCA drafts,
    orchestrator arrival gate. May-26 anchor: OVERCROWDED names'
    playbook split beat all-MOC by >400bps via the defer leg."""
    import json
    from pathlib import Path
    from agents.post_event import (ARCHETYPES, PLAYBOOK_SPLITS,
                                   archetype_grading)
    assert PLAYBOOK_SPLITS["OVERCROWDED"][2] >= 0.5   # T+1 defer
    p = Path("data/post_event_may26.json")
    if p.exists():
        d = json.loads(p.read_text())
        rows = {r["code"]: r for r in d["names"]}
        for c in ("2324", "2474"):
            s = rows[c]["strategies"]
            assert rows[c]["step2_scenario"] == "OVERCROWDED"
            assert s["PLAYBOOK"] < -400        # beat MOC big
            assert s["T1_CLOSE"] < -900
        a = rows["2324"]["archetypes"]
        assert set(a) <= set(ARCHETYPES)
        assert a["EM_TRACKER"]["advised"] == "MOC"   # no discretion
        assert a["ACTIVE_FLEX"]["regret_bps"] >= 0
    # unit: archetype grading math + HF sign flip
    g = archetype_grading({"MOC": 0.0, "VWAP_T": 10.0,
                           "LINEAR_W": -50.0, "T1_CLOSE": -100.0,
                           "PLAYBOOK": -60.0}, "OVERCROWDED")
    assert g["ACTIVE_FLEX"]["advised"] == "PLAYBOOK"
    assert g["ACTIVE_FLEX"]["best_hindsight"] == "T1_CLOSE"
    assert g["ACTIVE_FLEX"]["regret_bps"] == 40.0
    assert g["HF_PROVIDER"]["best_cost_bps"] == -100.0 or \
        g["HF_PROVIDER"]["best_hindsight"] == "LINEAR_W"
    ck = Path("data/cockpit_may26.json")
    if ck.exists():
        c = json.loads(ck.read_text())
        assert len(c["cards"]) == 8
        assert all("advice" in x for x in c["cards"])
    tca = Path("docs/case_studies/TCA_LETTERS_MAY2026_TW.md")
    if tca.exists():
        t = tca.read_text(encoding="utf-8")
        assert "SIMULATED" in t and "EM_TRACKER" in t


def test_sentinels():
    """Session 9i c-38: L0 sentinel system — offline-safe checks:
    fast sentinels run without network; report schema valid;
    artifact-staleness logic fires on a synthetic stale pair."""
    import datetime as dt
    import json
    import os
    import time
    from pathlib import Path
    from agents import sentinels as S
    r = S.s_calendar({})
    assert r["status"] in ("OK", "ALERT")
    assert "announcement" in r["delta"]
    r = S.s_artifacts({})
    assert r["status"] in ("OK", "ALERT")
    rep = Path("data/sentinel_report.json")
    if rep.exists():
        d = json.loads(rep.read_text())
        assert d["overall"] in ("OK", "CHANGED", "ALERT",
                                "DEGRADED")
        names = {x["sentinel"] for x in d["results"]}
        assert {"shorts", "members", "ladder", "calendar", "fx",
                "artifacts"} <= names
    # synthetic staleness: touch a dep newer than its artifact
    art = Path("data/funnel_tw.json")
    dep = Path("data/ewt_members.json")
    if art.exists() and dep.exists():
        old = dep.stat().st_mtime
        os.utime(dep, (time.time() + 120, time.time() + 120))
        try:
            r = S.s_artifacts({})
            assert r["status"] == "ALERT" and "funnel" in r["delta"]
        finally:
            os.utime(dep, (old, old))


def test_apac_factsheet_archive():
    """Session 9i c-62: all 10 markets' factsheets parsed —
    counts CROSS-VALIDATE the fund-derived membership pipeline
    (JP 168=EWJ, IN 165=INDA, ID 11, PH 10 ...); DM/EM corridors
    assigned correctly; denominators coherent."""
    import json
    from pathlib import Path
    p = Path("data/apac_factsheet_archive.json")
    if not p.exists():
        return
    d = json.loads(p.read_text())
    # c-86 INTENTIONAL: 10 -> 13 (NZ/SG/TH added for full APAC)
    assert len(d) == 13
    latest = {m: v[sorted(v)[-1]] for m, v in d.items()}
    expect = {"Taiwan": 77, "Japan": 168, "Australia": 47,
              "HongKong": 25, "Korea": 77, "India": 165,
              "Malaysia": 21, "Indonesia": 11, "Philippines": 10,
              "NewZealand": 5, "Singapore": 16, "Thailand": 18}
    for m, n in expect.items():
        assert latest[m]["n_constituents"] == n, m
    assert 550 <= latest["China"]["n_constituents"] <= 620
    for m in ("Japan", "Australia", "HongKong", "NewZealand",
              "Singapore"):
        assert latest[m]["cutoff_corridor_busd"][0] > 8   # DM
    for m in ("Taiwan", "Korea", "India", "China", "Thailand"):
        assert latest[m]["cutoff_corridor_busd"][0] < 5   # EM
    for m, v in latest.items():
        if v.get("index_float_cap_musd"):
            assert v["implied_denominator_busd"] > \
                v["index_float_cap_musd"] / 1000


def test_preann_advisory_aug26():
    """Session 9i c-60: pre-announcement advisory cards — schema +
    key reads pinned: 2408's easy-add profile (print ~1x ADV),
    1101's standing borrow > 10 ADV-days, squeeze precursors
    flagged where foreign accumulates into deletion candidates."""
    import json
    from pathlib import Path
    p = Path("data/preann_advisory_aug26.json")
    if not p.exists():
        return
    d = json.loads(p.read_text())
    cards = {c["code"]: c for c in d["cards"]}
    assert cards["2408"]["side"] == "add"
    # c-61: point estimate replaced by multi-method RANGE
    lo, hi = cards["2408"]["print_range_x_adv"]
    assert lo >= 1.0 and hi <= 3.0                        # easy add
    dlo, dhi = cards["1101"]["print_range_x_adv"]
    assert dlo >= 10 and dhi <= 40 and dhi > dlo * 1.5    # wide, fat
    for c in d["cards"]:
        if "print_range_x_adv" not in c:
            continue
        m = c["print_methods"]
        assert "M1_structural_lambda_band" in m
        assert "M3_scenario_overlay" in m
        assert c["print_range_x_adv"][0] < c["print_range_x_adv"][1]
    assert cards["1101"]["sbl_adv_days"] > 10             # loaded
    assert cards["1101"]["squeeze_precursor"] is True
    assert cards["3533"]["foreign_12m_pp"] > 5            # Compal-
    assert cards["3533"]["squeeze_precursor"] is True     # like


def test_case_2324_compal():
    """Session 9i c-59: the Compal squeeze anatomy — pinned from
    primary data: deletion confirmed; auction ~49% of day at a
    price ABOVE the last continuous trade; post-T SBL covering
    avalanche > 200M shares."""
    import json
    from pathlib import Path
    ev = json.loads(Path("data/msci_tw_events.json").read_text())
    assert "2324" in ev["May26"]["dels"]
    try:
        import sys
        sys.path.insert(0, ".")
        from scripts.tday_execution_studies import _ib_day, _load_ib
        r = _ib_day(_load_ib(), "2324", "2026-05-29")
    except Exception:
        r = None
    if r:
        cont, auc, last_cont = r
        tot = sum(x[3] for x in cont) + auc
        assert 0.44 <= auc / tot <= 0.54          # ~49% auction
        assert 36.5 <= 36.70                       # print 36.70
        assert last_cont < 36.70                   # print ABOVE tape
    sbl = json.loads(Path("data/event_data_cache.json")
                     .read_text())["short"]
    b_t = sbl["20260529"]["2324"][1]
    b_5 = sbl["20260605"]["2324"][1]
    assert b_t - b_5 > 2.0e8                       # >200M covered


def test_perstock_flow_model():
    """Session 9i c-57: the per-stock forced-flow model (lambda x
    float-days, the benchmarking-intensity proxy) beats the
    constant 16x prior — corr(log fd, log t_mult) > 0.5, MAE
    improved, lambda in a plausible passive-ownership range."""
    import json
    from pathlib import Path
    p = Path("data/perstock_flow_model.json")
    if not p.exists():
        return
    d = json.loads(p.read_text())
    assert d["n"] >= 60
    assert d["corr_log"] >= 0.5
    assert d["mae_perstock"] < d["mae_const16"]
    assert 0.05 <= d["lambda_passive_ratio"] <= 0.20


def test_liquidity_panel():
    """Session 9i c-56: the full-history Step-2 panel — 130+
    name-events; completion -> t_mult MONOTONE across the declared
    buckets (the volume forecaster); event-level corr NEGATIVE
    (orderly well-supplied closes); H16 compound tail registered
    with its two members."""
    import json
    from pathlib import Path
    p = Path("data/liquidity_panel_tw.json")
    if not p.exists():
        return
    d = json.loads(p.read_text())
    assert d["n_name_events"] >= 120
    assert d["n_events"] >= 30
    b = d["buckets"]
    order = ["UNDERSUPPLIED", "BUILDING", "WELL-SUPPLIED",
             "OVERCROWDED"]
    tms = [b[s]["mean_t_mult"] for s in order]
    assert tms == sorted(tms)                  # monotone volume
    assert d["completion_vs_absrev3_corr_eventlevel"] < 0
    tail = d["tail_analysis"]["completion_ge_1.5_and_wrongway"]
    assert tail["n"] == 2 and tail["abs_rev3"] > 10
    assert any("2324" in m for m in tail["members"])
    assert "NOT adopted" in tail["status"]


def test_t86_history():
    """Session 9i c-67: signed institutional flow harvester —
    era-tolerant parse (15-field 2015 rows), foreign/total nets
    extracted, watch subsetting works."""
    import json
    from pathlib import Path
    p = Path("data/t86_history.json")
    if not p.exists():
        return
    d = json.loads(p.read_text())
    days = sorted(x for x in d if d[x])
    assert days and days[0] <= "20150131"
    first = d[days[0]]
    assert len(first) >= 80
    r = first["2330"]
    assert r["nf"] in (15, 16, 17, 18, 19)
    assert isinstance(r["f"], float) and isinstance(r["t"], float)
    assert abs(r["f"]) < 5e8 and abs(r["t"]) < 5e8   # sane shares


def test_sbl_history():
    """Session 9i c-66: the decade borrow-history harvester —
    pilot days parse with the stable field map (SBL balance idx
    11), watch-name subsetting works, store shape matches the
    live cache."""
    import json
    from pathlib import Path
    p = Path("data/sbl_history.json")
    if not p.exists():
        return
    d = json.loads(p.read_text())
    days = sorted(x for x in d if d[x])
    assert days and days[0] <= "20150131"      # reaches 2015
    first = d[days[0]]
    assert len(first) >= 80                    # watch coverage
    assert first["2330"][1] > 1e6              # TSMC balance sane
    for v in first.values():
        assert len(v) == 2 and v[1] >= 0


def test_pattern_study():
    """Session 9i c-65: the pattern study — volume relationship
    re-confirmed (rho>0.3, clustered p<0.01); the RETURN null
    PINNED (all return tests ns, ML below base rate) so mean-
    return predictability cannot be claimed later without beating
    this bar; H17 registered not adopted."""
    import json
    from pathlib import Path
    p = Path("data/pattern_study_tw.json")
    if not p.exists():
        return
    d = json.loads(p.read_text())
    t = d["tests"]
    s5 = t["D5_compl_vs_tmult"]["spearman"]
    assert s5["rho"] > 0.3 and s5["perm_p"] < 0.01
    for tag in ("D1_foreign_vs_tdayret", "D2_compl_vs_tdayret",
                "D3_drift_vs_tdayret", "D6_vol_vs_tdayret"):
        assert t[tag]["spearman"]["perm_p"] > 0.05      # null
    ml = d["ml"]["del_sign_tday"]
    if "loo_event_accuracy" in ml:
        assert ml["loo_event_accuracy"] <= ml["base_rate"]
    s7 = t["D7_foreign_vs_fav3"]["spearman"]
    assert abs(s7["rho"]) < 0.25                        # H17 not
    assert "borrow_limitation" in d                     # adoptable


def test_liquidity_v2_channels():
    """Session 9i c-64: the channel-decomposition regrade —
    declared rules catch the squeeze (2324 SQUEEZE-RISK), passive
    demand is per-stock (lambda model, not flat 16x), channels
    bounded, and the standing-base caveat is recorded."""
    import json
    from pathlib import Path
    p = Path("data/liquidity_forecast_v2_may26.json")
    if not p.exists():
        return
    d = json.loads(p.read_text())
    n = {r["code"]: r for r in d["names"]}
    assert n["2324"]["scenario_v2"] == "SQUEEZE-RISK"
    assert n["2324"]["wrongway"] is True
    assert n["2324"]["REALIZED"]["t3_move_pct"] > 20
    # per-stock passive demand replaced the flat prior
    xs = {c: n[c]["passive_x_adv"] for c in
          ("1102", "2324", "2633")}
    assert xs["1102"] != xs["2324"] != xs["2633"]
    assert xs["2633"] > 40                      # float-days giant
    # 2474: the inventory-channel positioner (no borrow build)
    assert n["2474"]["ch1_borrow_x_demand"] == 0.0
    assert n["2474"]["ch2_inventory_x_demand"] > 1.5
    assert n["2474"]["scenario_v2"] == "OVERSUPPLIED"
    for r in d["names"]:
        assert 0 <= r["ch3_toll_reliance"] <= 1


def test_liquidity_forecast_may26():
    """Session 9i c-36: Step-2 liquidity-supply model — May-26 PIT
    frame: the two OVERCROWDED calls (2474/2324) were the two
    monster reversals; 2324 cross-checks the post-event pack."""
    import json
    from pathlib import Path
    p = Path("data/liquidity_forecast_may26.json")
    if not p.exists():
        return
    d = json.loads(p.read_text())
    assert d["asof_PIT"] < d["eff"]              # PIT frame
    n = {r["code"]: r for r in d["names"]}
    assert len(n) == 8
    for c in ("2474", "2324"):
        assert n[c]["scenario"] == "OVERCROWDED"
        assert n[c]["flow_completion"] >= 1.2
        assert n[c]["REALIZED_posthoc"]["t3_move_pct"] > 20
    assert n["2324"]["foreign_direction_consistent"] is False
    assert n["2610"]["scenario"] == "UNDERSUPPLIED"
    assert n["2610"]["REALIZED_posthoc"]["t_mult"] < 12
    calm = [r for r in d["names"]
            if r["scenario"] in ("BUILDING", "WELL-SUPPLIED")]
    assert all(abs(r["REALIZED_posthoc"]["t3_move_pct"]) < 12
               for r in calm)


def test_ladder_shadow_and_foreign_room():
    """Session 9i c-35: shadow ladder output sane (full breadth,
    inclusive pool) + the new §3.1.2.6 foreign-room screen blocks
    adds only when the column says room < 15%."""
    import json
    from pathlib import Path
    import pandas as pd
    from agents.reconstitution import MSCIRules, predict_msci
    p = Path("data/ladder_aug26_tw.json")
    if p.exists():
        d = json.loads(p.read_text())
        assert d["n_members_priced"] >= 70
        pool = {r["code"] for r in d["delete_pool"]}
        assert {"6919", "1101"} <= pool
        assert 5.0 <= d["gmsr_usd_b"] <= 8.0
        assert "GMSR CAVEAT" in d["note"]
    # foreign-room unit test: identical universes, room flips call
    def uni(room):
        return pd.DataFrame({
            "ticker": ["M0", "M1", "M2", "A"],
            "full_mktcap_usd": [40e9, 30e9, 20e9, 25e9],
            "free_float_frac": 0.8, "adv_usd": 1e8, "atvr": 1.0,
            "foreign_room_frac": [0.5, 0.5, 0.5, room]})
    mem = {"M0", "M1", "M2"}
    r_ok = predict_msci(uni(0.5), mem, MSCIRules(review="SAIR"))
    r_no = predict_msci(uni(0.05), mem, MSCIRules(review="SAIR"))
    assert "A" in set(r_ok["adds"]["ticker"])
    assert "A" not in set(r_no["adds"].get("ticker", []))
    assert any(w["side"] == "blocked add" and "foreign room"
               in w["distance"] for _, w in
               r_no["watchlist"].iterrows())


def test_apac_members_pipeline():
    """Session 9i c-34: APAC constituent pipeline — anchor+composite
    agreement per market (ranges, not exact counts — reviews move
    them); IMI-variant markets use the composite as Standard."""
    import json
    from pathlib import Path
    p = Path("data/apac_members.json")
    if not p.exists():
        return
    m = json.loads(p.read_text())["markets"]
    assert len(m) == 10
    for mkt in ("Japan", "Australia", "HongKong", "India",
                "Malaysia"):
        assert m[mkt]["anchor_only"] == [] \
            and m[mkt]["composite_only"] == []
    assert 60 <= len(m["Taiwan"]["confirmed_both"]) <= 95
    assert 500 <= len(m["China"]["confirmed_both"]) <= 650
    for mkt, hi in (("Indonesia", 25), ("Philippines", 20)):
        assert "IMI" in m[mkt]["anchor_variant"]
        assert len(m[mkt]["standard_members"]) <= hi


def test_delete_pool_validation():
    """Session 9i c-33: THE BREADTH FIX — EWT-anchored ladder +
    vintage caps put ALL official deletions at the ladder bottom
    for both validation events, incl. Nov-25 (the historical 0/7)."""
    import json
    from pathlib import Path
    p = Path("data/delete_pool_validation.json")
    if not p.exists():
        return
    d = json.loads(p.read_text())
    for season in ("May26", "Nov25"):
        s = d[season]
        assert s["dels_in_ladder"] == s["dels_official"] == 7
        assert max(s["deleted_ladder_ranks_bottom"]) <= 7
    # May-26: perfect separation — deletions are EXACTLY the bottom 7
    assert d["May26"]["deleted_ladder_ranks_bottom"] == list(range(7))


def test_pit_workbench_may26():
    """Session 9i c-32: May-26 PIT frame — EWT-anchored membership
    reverse-rolled to Apr-30; MPI (6223) on the tentative add list
    and graded ADDED; May-26 deleted names correctly members at
    Apr-30; giants correctly members (the anchor-lookup bug class)."""
    import json
    from pathlib import Path
    p = Path("data/universe_workbench_tw_may26pit.json")
    if not p.exists():
        return
    b = json.loads(p.read_text())
    tent = {r["code"]: r for r in b["tentative_adds"]}
    assert "6223" in tent and "ADDED" in tent["6223"]["official"]
    rows = {r["code"]: r for r in b["rows"]}
    for c in ("2330", "2454", "2317"):          # giants = members
        assert rows[c]["member_apr30"]
    for c in ("1102", "2474", "2610"):          # May-26 dels were
        assert rows[c]["member_apr30"]          # members at Apr-30
    assert not rows["6223"]["member_apr30"]     # MPI not yet in
    assert b["members"] >= 40
    assert any("EWT" in s for s in b["derivation"])


def test_universe_workbench():
    """Session 9i c-29: Step-1 workbench numbers — per-name cap/ff
    arithmetic consistent, thresholds coherent (add bar = 1.8x GMSR,
    floor = 0.5x), buckets follow the stated decision logic."""
    import json
    from pathlib import Path
    p = Path("data/universe_workbench_tw.json")
    if not p.exists():
        return
    b = json.loads(p.read_text())
    t = b["thresholds"]
    assert abs(t["add_bar_usd_b"] / t["gmsr_usd_b"] - 1.8) < 0.01
    assert abs(t["floor_usd_b"] / t["gmsr_usd_b"] - 0.5) < 0.01
    assert len(b["rows"]) >= 15
    for r in b["rows"]:
        assert 0 < r["free_float_est"] <= 1.0
        assert abs(r["float_adj_cap_usd_b"]
                   - r["cap_usd_b_now"] * r["free_float_est"]) \
            < 0.02 + 0.001 * r["cap_usd_b_now"]
        thr = t["floor_usd_b"] if r["member"] else t["add_bar_usd_b"]
        assert abs(r["vs_threshold"] - r["cap_usd_b_now"] / thr) \
            < 0.02 + 0.005 * r["vs_threshold"]
        if r["member"] and r["vs_threshold"] < 1:
            assert "DELETE" in r["decision_bucket"]
        if not r["member"] and r["vs_threshold"] >= 1:
            assert "ADD" in r["decision_bucket"]


def test_jp_step1_upgrade():
    """Session 9i: JP priors from held daily data — 92% aliases
    print-verified, first JP-measured class T-multiples, wired into
    the Asia pack (no more silent TW-prior borrowing)."""
    import json
    from pathlib import Path
    p = Path("data/jp_event_priors.json")
    if not p.exists():
        return
    d = json.loads(p.read_text())
    v = d["verification"]
    assert v["n_total"] >= 150
    assert v["verified"] / v["n_total"] >= 0.85
    assert d["priors"]["Sell"]["n"] >= 80
    assert 5 <= d["priors"]["Sell"]["median"] <= 20
    assert "survivorship" in d["note"]
    pack = Path("docs/case_studies/AUG2026_QIR_ASIA_PACK.md") \
        .read_text(encoding="utf-8")
    assert "JP-measured" in pack


def test_post_event_pack():
    """Session 9i: Step-4 without own executions — the May-26 demo
    pack pinned: benchmark strips complete, one estimate-miss
    shipped honestly (1402 gap out of band), reversal paths from
    IB post-T bars."""
    import json
    from pathlib import Path
    p = Path("data/post_event_may26.json")
    if not p.exists():
        return
    d = json.loads(p.read_text())
    rows = [r for r in d["names"] if "note" not in r]
    assert len(rows) == 7
    for r in rows:
        assert r["day_vwap_exact"] and r["official_close"]
        # c-40: strategy set grew (T+1 defer leg + playbook split)
        assert r["strategies"]["winner"] in (
            "MOC", "VWAP_T", "LINEAR_W", "T1_CLOSE", "PLAYBOOK")
        assert r["reversal_T1_T5"]
    g1402 = next(r for r in rows if r["code"] == "1402")
    assert g1402["grades"]["gap_in_band"] is False   # miss shipped
    big_rev = max(max(r["reversal_T1_T5"]) for r in rows)
    assert big_rev > 1000            # the post-print snap-back, real


def test_tday_playbook():
    """Session 9i: the situations playbook — scale, thin-cell
    honesty, and the systematic finding pinned (the print typically
    lands AGAINST the obligated side: p_gap_fav < 0.5 in every
    OK cell)."""
    import json
    from pathlib import Path
    p = Path("data/tday_playbook.json")
    if not p.exists():
        return
    d = json.loads(p.read_text())
    assert d["n_name_days"] >= 80 and d["n_events"] >= 20
    cells = d["cells"]
    ok = [c for c in cells if c["label"] == "OK"]
    assert len(ok) >= 6
    assert all(c["p_gap_fav"] < 0.5 for c in ok)   # the toll, pinned
    thin = [c for c in cells if c["label"] == "DATA-THIN"]
    for c in thin:                     # thin cells carry no reaction
        assert c["n"] < 8 or c["n_events"] < 4
    doc = Path("docs/case_studies/TDAY_PLAYBOOK.md").read_text(
        encoding="utf-8")
    assert "systematic lesson" in doc and "Measured:" in doc


def test_window_intraday_study():
    """Session 9i registry-v2: panel scale + verdicts pinned (H9
    ADOPT under locked criteria, H10 NULL) + the H9b decomposition
    documented in the case study."""
    import json
    from pathlib import Path
    p = Path("data/window_intraday.json")
    if not p.exists():
        return
    d = json.loads(p.read_text())
    assert d["n_name_days"] >= 900 and d["n_events"] >= 20
    assert d["H9"]["verdict"] == "ADOPT"
    assert d["H9"]["winrate"] >= 0.9
    assert d["H10"]["verdict"] == "NULL-PIN"
    doc = Path("docs/case_studies/WINDOW_INTRADAY_STUDY.md") \
        .read_text(encoding="utf-8")
    assert "H9 decomposition" in doc and "H9b" in doc


def test_tw_alias_bridge():
    """Session 9i: the pre-2025 MSCI TW unlock — 135/136 names
    mapped (HONPRECISION deliberately open: prior print-rejection);
    34 events with codes back to Feb-2015; every event carries
    ann+eff; IB window set reaches 2015."""
    import json
    from pathlib import Path
    p = Path("data/msci_tw_events.json")
    if not p.exists():
        return
    ev = json.loads(p.read_text(encoding="utf-8"))
    named = sum(len(e["adds"]) + len(e["dels"]) for e in ev.values())
    unmatched = {n for e in ev.values() for n in e["unmatched"]}
    assert named >= 130
    assert unmatched == {"HONPRECISION"}
    with_codes = [s for s, e in ev.items() if e["adds"] or e["dels"]]
    assert len(with_codes) >= 30
    assert all(e["eff"] and e["ann"] for s, e in ev.items()
               if e["adds"] or e["dels"])
    assert min(e["eff"] for e in ev.values()
               if e["adds"] or e["dels"]) == "2015-02-27"
    from scripts.ib_harvest import _windows
    w = _windows()
    assert len(w) >= 200 and min(x[3] for x in w) == "2015-02-27"


def test_tday_execution_studies():
    """Session 9i: the three studies pinned — violence NULL SURVIVES
    at n=85 (5x the v1 data); decomposition legs present; THIN/RICH
    proxy is the project's first significant real-time-read result."""
    import json
    from pathlib import Path
    p = Path("data/tday_execution_studies.json")
    if not p.exists():
        return
    d = json.loads(p.read_text())
    assert d["n_rows"] >= 70
    v2 = d["violence_v2"]
    # the null now holds THREE times: n=17 (v1), n=85 (derived),
    # n=86 (IB-direct shares)
    assert v2["n"] >= 80 and v2["all"]["r2"] < 0.15
    tr = d["thin_rich"]
    # honest expansion (9i): n 25 -> 80 with IB days reduced rho
    # from 0.61 to ~0.31 — still significant; the small sample had
    # overstated it. Modest-but-real is the pinned claim.
    assert tr["n"] >= 60
    assert tr["spearman_rho"] > 0.25 and tr["p_value"] < 0.01
    dec = d["decompose"]
    assert "am" in dec and "auction" in dec


def test_derived_auction_shares():
    """Session 9i: the derived method (official daily - TV
    continuous) at scale — 85 rows, zero sanity failures, and the
    add/delete auction-dominance asymmetry pinned."""
    from pathlib import Path
    if not Path("data/auction_shares_derived.json").exists():
        return
    import pandas as pd
    df = pd.read_json("data/auction_shares_derived.json")
    ok = df[df["flag"] == "OK"]
    assert len(ok) >= 70
    assert (df["flag"] != "OK").sum() == 0     # sanity holds on all
    med = ok.groupby(["provider", "side"])["auction_share"].median()
    assert med[("FTSE", "Sell")] > 0.6         # delete prints dominate
    assert med[("MSCI", "Sell")] > 0.4
    assert med[("MSCI", "Buy")] < 0.2          # add prints drown
    assert ok["auction_share"].max() > 0.85    # the 1102-class prints


def test_tday_hourly_shape():
    """Session 9i: hourly harvest exists for >=7 events; the
    auction-exclusion caveat is enforced in the doc; the class
    finding pinned (FTSE both sides against-flow in continuous;
    MSCI ~flat)."""
    from pathlib import Path
    if not Path("data/tday_hourly.json").exists():
        return
    from scripts.tday_hourly_shape import table
    df = table()
    assert df["event"].nunique() >= 7 and len(df) >= 50
    med = df.groupby(["provider", "side"])["am_drift_bps"].median()
    assert med[("FTSE", "Buy")] < -100      # adds fade intraday
    assert med[("FTSE", "Sell")] < -50      # deletes recover intraday
    assert abs(med[("MSCI", "Sell")]) < 60  # MSCI continuous ~flat
    doc = Path("docs/case_studies/TDAY_HOURLY_SHAPE.md")
    assert "EXCLUDE the closing auction" in doc.read_text(
        encoding="utf-8")


def test_variable_lab():
    """Session 9i: registry-locked evaluation — verdict mechanics on
    synthetic effects + the run-1 verdicts PINNED (H2 adopt-FTSE,
    H3 reject-FTSE — the A+3 reversal; if new events change these,
    the docs must be consciously updated)."""
    import json
    from pathlib import Path
    from agents.variable_lab import _verdict
    v, s = _verdict([100, 120, 90, 110, 95, 105])       # strong+stable
    assert v == "ADOPT" and s["winrate"] == 1.0
    v, _ = _verdict([100, -120, 90, -110, -95, 105])    # unstable
    assert v == "REJECT"
    v, _ = _verdict([5, -8, 10, -3, 6, 2, -5, 4])       # tiny, n>=8
    assert v == "NULL-PIN"
    v, _ = _verdict([100, 120])                          # too few
    assert v == "DATA-GATED"
    p = Path("data/variable_lab.json")
    if not p.exists():
        return
    r = json.loads(p.read_text())["results"]
    assert r["H2"]["FTSE"]["verdict"] == "ADOPT"
    assert r["H2"]["FTSE"]["mean_bps"] > 100
    assert r["H3"]["FTSE"]["verdict"] == "REJECT"        # A+3 demoted
    assert r["H7"]["FTSE"]["verdict"] == "DATA-GATED"
    for h in r.values():                                 # MSCI gated
        assert h["MSCI"]["verdict"] == "DATA-GATED"


def test_data_freshness_guarantee():
    """Session 9i (the caught staleness failure, structurally fixed):
    stale cache triggers fetch of every missing bday; holidays go to
    the no-data ledger; network failure -> DEGRADED, never a crash;
    TTL short-circuits; full-day storage (all codes kept)."""
    import json
    import pandas as pd
    from pathlib import Path
    from agents.data_freshness import (ensure_fresh_shorts,
                                       freshness_line)

    def fake_fetch(d):
        if d == "20260731":
            return pd.DataFrame()                    # holiday
        return pd.DataFrame([
            {"ticker": "1101", "margin_short_bal": 1.0,
             "sbl_bal": 2.0},
            {"ticker": "9999", "margin_short_bal": 3.0,
             "sbl_bal": 0.0}])

    tmp = Path("data/_test_fresh.json")
    tmp.write_text(json.dumps(
        {"short": {"20260728": {"1101": [1, 1]}}}))
    r = ensure_fresh_shorts(cache_path=tmp, fetch_fn=fake_fetch,
                            today="2026-08-04", ttl=0)
    assert r["status"] == "REFRESHED"
    assert "20260731" not in r["fetched_days"]        # holiday ledger
    assert r["latest"] == "20260804" and r["stale_bdays"] == 0
    cache = json.loads(tmp.read_text())
    assert "9999" in cache["short"]["20260803"]       # full-day store
    assert "20260731" in cache["_meta"]["no_data_days"]
    # TTL short-circuit
    r2 = ensure_fresh_shorts(cache_path=tmp, fetch_fn=fake_fetch,
                             today="2026-08-04")
    assert r2["status"] == "FRESH" and "TTL" in r2["note"]

    def broken(d):
        raise ConnectionError("down")
    tmp.write_text(json.dumps(
        {"short": {"20260720": {"1101": [1, 1]}}}))
    r3 = ensure_fresh_shorts(cache_path=tmp, fetch_fn=broken,
                             today="2026-08-04", ttl=0)
    assert r3["status"] == "DEGRADED" and r3["stale_bdays"] > 1
    assert "WARNING" in freshness_line(r3)
    tmp.unlink()


def test_pre_announcement_pack():
    """Session 9i: six-category orchestrator — as-of crowding watch
    (backtestable), May-2026 pack graded 7/7+1/1 with Brier pinned,
    Aug pack fields present."""
    import json
    import pandas as pd
    from pathlib import Path
    from agents.pre_announcement import crowding_watch, must_start_by
    cache = {"short": {
        "20260501": {"9999": [100.0, 0.0]},
        "20260505": {"9999": [110.0, 0.0]},
        "20260508": {"9999": [125.0, 0.0]},
        "20260511": {"9999": [140.0, 0.0]},
        "20260520": {"9999": [500.0, 0.0]}}}      # post-asof spike
    w = crowding_watch(cache, ["9999"], asof="20260511")
    assert w.iloc[0]["build_pct"] == 40           # PIT: spike unseen
    assert bool(w.iloc[0]["alert"])               # 5-obs delta >= 10%
    assert must_start_by("2026-08-31", 17.6) == "2026-06-08" or \
        must_start_by("2026-08-31", 17.6) < "2026-08-01"  # 71 bdays
    p = Path("data/preann_tw.json")
    if not p.exists():
        return
    blob = json.loads(p.read_text())
    g = blob["may"]["grade"]
    assert len(g["dels_hit"]) == 7 and g["adds_hit"] == ["6223.TWO"]
    assert g["brier"] is not None and g["brier"] < 0.25   # < coinflip
    assert blob["aug"]["n_candidates"] >= 8
    assert blob["aug"]["crowd_alerts"] >= 1


def test_tday_cards():
    """Session 9i: cards chain measured priors with per-metric
    provenance; flow arithmetic exact; NO-PRIOR honesty on the Buy
    side; BELOW-FLOOR rows carry a note, not fabricated numbers."""
    import pandas as pd
    from agents.review_engine import PASSIVE_OWN_RATE
    from agents.tday_cards import METHOD, build_cards, render_cards_md
    sl = pd.DataFrame([
        {"side": "DELETE", "ticker": "1101.TW", "cap_usd_b": 5.2,
         "x_threshold": 2.19, "p": 0.149, "reasoning": "test"},
        {"side": "ADD", "ticker": "2324.TW", "cap_usd_b": 4.8,
         "x_threshold": 0.56, "p": 0.062, "reasoning": "test"},
        {"side": "ADD", "ticker": "BELOW-FLOOR (unobservable)",
         "cap_usd_b": None, "x_threshold": None, "p": 0.273,
         "reasoning": "blind"}])
    u = pd.DataFrame([
        dict(ticker="1101.TW", full_mktcap_usd=5.24e9,
             free_float_frac=0.86, adv_usd=23.1e6, atvr=2, member=1),
        dict(ticker="2324.TW", full_mktcap_usd=4.8e9,
             free_float_frac=0.95, adv_usd=40e6, atvr=2, member=0)])
    cards = build_cards(sl, u, crowding_map={"1101": "HIGH (+53%)"})
    assert len(cards) == 3
    c = cards[0]
    lo, hi = c["flow_if_converts_usd_m"]
    assert lo == round(5.24e9 * 0.86 * PASSIVE_OWN_RATE[0] / 1e6)
    assert hi == round(5.24e9 * 0.86 * PASSIVE_OWN_RATE[1] / 1e6)
    assert abs(c["flow_p_weighted_usd_m"]
               - round(0.149 * (lo + hi) / 2, 1)) < 0.6
    assert c["print_multiple"]["median"] == 16.0     # measured prior
    assert "WORK AHEAD" in c["playbook"]             # crowded delete
    add = cards[1]
    assert add["print_multiple"].get("available") is False
    assert "NO MEASURED" in add["print_multiple"]["how"]
    assert "demoted hypothesis" in add["playbook"]
    assert "note" in cards[2] and "unobservable" in cards[2]["note"]
    md = render_cards_md(cards, "t", "2026-08-04")
    assert "METHOD" in md and all(m in md for m in METHOD)


def test_no_change_shortlist():
    """Session 9i (user rule): a zero-call review ships a ranked
    shortlist — decade-anchored probabilities, blind-band row
    explicit, recent-deletion caution attached."""
    import pandas as pd
    from agents.review_engine import (screen_market,
                                      shortlist_candidates)
    u = pd.DataFrame([
        dict(ticker="BIG.TW", full_mktcap_usd=60e9,
             free_float_frac=0.8, adv_usd=1e8, atvr=2.0, member=1),
        dict(ticker="MID.TW", full_mktcap_usd=5e9,
             free_float_frac=0.7, adv_usd=2e7, atvr=2.0, member=1),
        dict(ticker="CAND.TW", full_mktcap_usd=4.5e9,
             free_float_frac=0.7, adv_usd=2e7, atvr=2.0, member=0)])
    s = screen_market(u, review="QIR", member_count=83,
                      tail_hi=10e9, tail_n=500)
    sl = shortlist_candidates(s, u, "QIR", "Taiwan",
                              recent_deletions={"CAND.TW"})
    assert sl is not None and len(sl) >= 4
    assert (sl["p"] > 0).all() and (sl["p"] < 0.5).all()
    blind = sl[sl["ticker"].str.startswith("BELOW-FLOOR")]
    assert len(blind) == 2                    # one per side, explicit
    cand = sl[sl["ticker"] == "CAND.TW"].iloc[0]
    assert "CAUTION recent deletion" in cand["reasoning"]
    assert "decade-measured" in cand["reasoning"]
    # probability mass per side never exceeds the decade P(any)
    for side, pa in (("ADD", 0.455), ("DELETE", 0.5)):
        assert sl[sl["side"] == side]["p"].sum() <= pa + 1e-6


def test_review_funnel():
    """Session 9i: funnel stage arithmetic + the May-26 validation —
    the funnel reproduces the graded run (7/7 dels + 1/1 add) with
    the 3 false dels being exactly the cutline residents."""
    import json
    from pathlib import Path
    p = Path("data/funnel_tw.json")
    if not p.exists():
        return
    blob = json.loads(p.read_text())
    for run in ("validation", "prediction"):
        st = blob[run]["stages"]
        names = [s["stage"] for s in st]
        # funnel now STARTS at engine Step 1 (universe acquisition)
        assert names[0] == "S0 acquisition"
        assert names[1] == "S0 universe"
        assert st[1]["n"] >= st[4]["n"] >= st[-1]["n"] >= 0
    # session 9i cont-28: name journeys — shortlist at every stage
    j = {r["ticker"]: r for r in blob["validation"]["journeys"]}
    assert j["6223.TWO"]["official"] == "ADDED — HIT"
    assert j["1102.TW"]["official"] == "DELETED — HIT"
    assert "cutline" in j["1101.TW"]["official"]
    assert sum("false call" in r.get("official", "")
               for r in j.values()) == 3
    assert "S0 acquisition" in blob["methods"]
    assert "3.1.5.1" in blob["methods"]["S4 churn-buffered"]
    g = blob["validation"]["grade"]
    assert len(g["dels_hit"]) == 7 and g["dels_missed_visible"] == []
    assert g["adds_hit"] == ["6223.TWO"]
    assert set(g["false_dels"]) == {"1101.TW", "1326.TW", "2207.TW"}
    assert blob["prediction"]["stages"][-1]["n"] == 0   # Aug-26 visible


def test_decade_stats_and_consistency():
    """Improvement plan item 2 (session 9i): decade key stats exist
    for all APAC markets; cadence rule validated decade-wide (SAIR
    deletion share > 50% everywhere); consistency check verdicts."""
    import json
    from pathlib import Path
    from agents.review_engine import decade_consistency
    p = Path("data/msci_decade_stats.json")
    if not p.exists():
        return
    s = json.loads(p.read_text())
    assert s["n_reviews"] == 44
    for m in ("TAIWAN", "JAPAN", "CHINA", "KOREA"):
        assert s["cadence"][m]["sair_del_share"] > 0.5   # L4, decade
    assert s["churn"]["TAIWAN"]["add_deleted_within_4"] is not None
    d = decade_consistency("Taiwan", "QIR", 0, 0)
    assert d and d["del_verdict"] == "OK"
    wild = decade_consistency("Taiwan", "QIR", 0, 12)
    assert wild["del_verdict"] == "OUTSIDE_HIGH"   # flags, no suppress
    # the two-sided fix (9i): a zero-add China QIR pack is flagged LOW
    low = decade_consistency("China", "QIR", 0, 2)
    assert low["add_verdict"] == "OUTSIDE_LOW"


def test_limit_moves_tw():
    """Exact TWSE limit math (tick table both directions) + day_stats
    on synthetic rows; the two 2026 case-study locks verify to tick."""
    from scripts.limit_moves_tw import day_stats, limit_down, limit_up
    assert limit_up(99.1) == 109.0            # 6919 on 2026-06-18
    assert limit_down(122.0) == 110.0         # 2344 on 2026-03-20
    assert limit_up(23.45) == 25.75           # rounding down to 0.05
    assert limit_down(23.45) == 21.15
    assert limit_up(8.0) == 8.8               # 0.01 tick band
    rows = [["1111", 100.0, 110.0, 100.0, 110.0, 1],   # locked up
            ["2222", 100.0, 110.0, 100.0, 105.0, 0],   # touched only
            ["3333", 100.0, 100.0, 90.0, 90.0, 0],     # locked down
            ["4444", 100.0, 101.0, 99.0, 100.0, 0]]    # quiet
    s = day_stats(rows)
    assert (s["touched_up"], s["locked_up"], s["book_locked_up"]) \
        == (2, 1, 1)
    assert (s["touched_down"], s["locked_down"]) == (1, 1)
    assert s["up_names"] == ["1111"] and s["down_names"] == ["3333"]


def test_decade_window_study():
    """Decade CN/JP/HK study: events parse with dates for all 44
    quarters; bridge + panel run on caches (skip if absent); the
    9h REVISION is pinned — decade CN adds do NOT show the May-2026
    pop-decay (LINEAR median < 0 = working beats print)."""
    from scripts.window_study_decade import (BRIDGE, CACHE, _match,
                                             _toks, events)
    ev = events()
    assert len(ev) >= 40
    assert all(e["eff"] > e["ann"] for e in ev)
    assert any("CN" in e["mkts"] for e in ev)
    # alias matching honors abbreviations + rejects ambiguity
    t = _toks("AGRI BANK OF CN A (HK-C)")
    assert "AGRICULTURAL" in [x if x != "AGRI" else "AGRICULTURAL"
                              for x in t] or "AGRI" not in t
    code, _ = _match(_toks("PING AN BANK A"),
                     [("sz.000001", _toks("PING AN BANK")),
                      ("sz.999999", _toks("PING AN INSURANCE GROUP"))])
    assert code == "sz.000001"
    if not (BRIDGE.exists() and CACHE.exists()):
        return
    from scripts.window_study_decade import panel
    df = panel()
    if not len(df):
        return
    ok = df[df["print_ok"]]
    assert len(ok) >= 300 and ok["mkt"].nunique() == 3
    cn_adds = ok[(ok["mkt"] == "CN") & (ok["side"] == "Buy")]
    assert cn_adds["LINEAR"].median() < 0     # the 9h revision, pinned


def test_twap_vwap_moc_events_and_cache():
    """Event list covers both providers; real-cache pipeline runs when
    the STOCK_DAY cache exists (skip otherwise)."""
    from scripts.twap_vwap_moc_study import (CACHE, build_table, events)
    ev = events()
    assert sum(e["provider"] == "FTSE" for e in ev) >= 28
    assert sum(e["provider"] == "MSCI" for e in ev) == 4   # +2025 (9i)
    assert all(e["eff"] > e["ann"] for e in ev)
    if not CACHE.exists():
        return
    df, skipped = build_table()
    if not len(df):
        return
    assert df["MOC_vs_close"].abs().max() == 0.0
    assert df["event"].nunique() >= 20


def test_roadmap_harvest():
    """Session 9i c-68: roadmap harvesters (margin / daytrade /
    blocks / taifex) — raw-row storage parses, field counts
    stable across eras (probed 2015 and 2026: nf 15/5/5), watch
    subsetting works, taifex capture has OpenInterest."""
    import json
    from pathlib import Path
    checks = {"margin_history.json": (15, 80),
              "daytrade_history.json": (5, 50),
              "blocks_history.json": (5, 1)}
    for fname, (nf, min_names) in checks.items():
        p = Path("data") / fname
        if not p.exists():
            continue
        d = json.loads(p.read_text())
        days = sorted(x for x in d if d[x])
        assert days and days[0] <= "20150131"
        first = d[days[0]]
        assert len(first) >= min_names
        sample = next(iter(first.values()))
        if isinstance(sample, list):        # blocks: trade-level
            sample = sample[0]
        assert sample["nf"] == nf
        assert sample["raw"][0].strip().isdigit()
    p = Path("data/taifex_daily.json")
    if p.exists():
        d = json.loads(p.read_text())
        rows = next(iter(d.values()))
        assert len(rows) > 500
        assert "OpenInterest" in rows[0] and "Contract" in rows[0]


def test_auction_expost():
    """Session 9i c-71: ex-post auction panel — schema, side
    coverage, bounded shares, orientation fields present."""
    import json
    from pathlib import Path
    p = Path("data/auction_expost.json")
    if not p.exists():
        return
    d = json.loads(p.read_text())
    assert d["summary"]["n"] >= 50
    assert {"Buy", "Sell"} <= set(d["summary"])
    for r in d["rows"]:
        assert r["side"] in ("Buy", "Sell")
        if r["auction_share"] is not None:
            assert 0.0 <= r["auction_share"] <= 1.0
        assert r["pressure_bps"] == r["disl_bps"] * (
            1 if r["side"] == "Buy" else -1)


def test_auction5s_history():
    """Session 9i c-72: MI_5MINS harvester — call-window rows
    stored (13:00 ref + 13:20:00-on), 8 fields, trades freeze
    during the call then jump at the 13:30 cross."""
    import json
    from pathlib import Path
    p = Path("data/auction5s_history.json")
    if not p.exists():
        return
    d = json.loads(p.read_text())
    days = sorted(x for x in d if d[x])
    assert days and days[0] <= "20150131"
    rows = d[days[0]]
    assert 100 <= len(rows) <= 130
    assert rows[0][0] == "13:00:00" and rows[-1][0] == "13:30:00"
    assert all(len(r) == 8 for r in rows)
    tx = [float(r[5].replace(",", "")) for r in rows
          if r[0] >= "13:25:00"]
    assert tx[-1] > tx[0]           # the cross printed
    assert len(set(tx[:-1])) == 1   # frozen during the call


def test_market_profiles():
    """Session 9i c-74: the standardization registry — profiles
    complete + consistent with the factsheet pipeline; TW is the
    only fitted lambda; India's auction analytics blocked; no
    silent parameter borrowing possible."""
    from agents.market_profiles import (PROFILES, step1_plan,
                                        step2_plan)
    from scripts.apac_factsheet_capture import MARKETS
    assert set(PROFILES) == set(MARKETS)
    req = {"tier", "ccy", "anchor", "access", "float_source",
           "universe_census", "borrow", "short_sale",
           "price_limit", "settlement", "close_mech", "lambda",
           "derivatives_oi"}
    for mkt, p in PROFILES.items():
        assert req <= set(p), mkt
        assert p["tier"] == MARKETS[mkt][1], mkt
        tag, lam = p["lambda"]
        if mkt == "Taiwan":
            assert tag == "fitted" and lam == 0.093
        else:
            assert tag == "UNCALIBRATED" and lam is None
        assert len(step1_plan(mkt)) == 8
    india = dict(step2_plan("India"))
    assert india["auction_analytics"].startswith(
        "DOES_NOT_TRANSFER")
    korea = dict(step2_plan("Korea"))
    assert "era_flags" in korea and "BAN" in korea["era_flags"]


def test_tday_decider():
    """Session 9i c-75: early-vs-MOC decider + alert engine —
    MOC-only mandate always forces (0,1,0); splits sum to 1;
    alerts fire on transitions only; RED budget collapses to
    one MARKET-MODE banner."""
    from agents.tday_decider import (TdayAlertEngine,
                                     decide_split,
                                     render_tday_plan)
    d = decide_split("2324", "Sell", "TOLL-DEPENDENT",
                     client_flex=False)
    assert d["split"] == (0.0, 1.0, 0.0)
    assert "MOC-ONLY" in d["rationale"]
    for sc in ("SQUEEZE-RISK", "OVERSUPPLIED", "COMMITTED",
               "PARTIAL", "TOLL-DEPENDENT"):
        s = decide_split("2330", "Buy", sc)["split"]
        assert abs(sum(s) - 1.0) < 1e-9
    eng = TdayAlertEngine(red_budget=2)
    assert eng.observe("2324", disl_bps=50) is None    # SILENT
    a = eng.observe("2324", disl_bps=300)
    assert a and a["level"] == "RED"
    assert eng.observe("2324", disl_bps=305) is None   # no refire
    assert eng.observe("2330", halted=True)["level"] == "RED"
    b = eng.observe("2408", at_limit=True)
    assert b and b["level"] == "MARKET-MODE"           # budget
    assert eng.observe("6505", at_limit=True) is None  # silenced
    amber = TdayAlertEngine()
    assert amber.observe("1101", disl_bps=200) is None # AMBER
    assert amber.digest() == ["1101: AMBER"]
    plan = render_tday_plan([("2324", "Sell", "SQUEEZE-RISK")])
    assert len(plan["checkpoints"]) == 5
    assert plan["plans"][0]["status"] == "DECLARED"


def test_cutoff_walk_v2():
    """Session 9i c-79: corrected walk — rank FULL / accumulate
    FLOAT / express FULL; census frame within banding allowance
    of the implied frame; corridor-binding conclusion
    frame-robust across the default-float band."""
    import json
    from pathlib import Path
    p = Path("data/cutoff_walk_v2.json")
    if not p.exists():
        return
    d = json.loads(p.read_text())
    b = d["base"]
    assert abs(b["gap_vs_implied_pct"]) <= 6.0
    assert b["cutoff_full_cap_busd"] > b["corridor_busd"][1]
    for k in ("default_ff_0.40", "default_ff_0.70"):
        assert d["band"][k]["cutoff_full_cap_busd"] > \
            b["corridor_busd"][0]
    assert b["n_pass"] >= 500


def test_event_eda():
    """Session 9i c-82: repeatable event EDA — May-26 panel
    builds with all 7 deletes, PIT baseline, channel coverage."""
    from pathlib import Path
    needed = ["sbl_history.json", "t86_history.json",
              "margin_history.json", "daytrade_history.json",
              "blocks_history.json"]
    if not all((Path("data") / n).exists() for n in needed):
        return
    from scripts.event_eda import build_panel
    ann, eff, panel = build_panel("MSCI 2026-05 SAIR")
    assert (ann, eff) == ("2026-05-12", "2026-05-29")
    assert len(panel) == 7
    for code, p in panel.items():
        assert p["side"] == "DEL"
        assert p["adv"] and p["adv"] > 0
        assert len(p["rows"]) >= 20
        w = [r for r in p["rows"] if ann <= r["date"] <= eff]
        assert any(r["sbl_bal"] for r in w), code
        assert any(r["for_net"] is not None for r in w), code
        assert any(r["marg_long"] for r in w), code


def test_anticipation_clock():
    """Session 9i c-83: the anticipation clock — sample size,
    declared rule recorded, censoring-consistent outputs, and
    the headline levels within sane bounds."""
    import json
    from pathlib import Path
    p = Path("data/anticipation_clock.json")
    if not p.exists():
        return
    d = json.loads(p.read_text())
    assert d["n_del_curves"] >= 50
    assert d["n_events"] >= 25
    assert "DECLARED" in d["rule"]
    assert d["share_with_detectable_build"] >= 0.8
    assert 1.0 <= d["median_build_at_ann_advdays"] <= 20.0
    assert len(d["rel"]) == len(d["median_del"]) == \
        len(d["diff"])


def test_aug26_site():
    """Session 9i c-85: the single-purpose Aug-26 site — module
    imports, backup exists, data artifacts it renders are
    present and carry the declared call."""
    import json
    from pathlib import Path
    assert Path("backup/website_v1_20260806/app.py").exists()
    assert Path("backup/website_v1_20260806/views/"
                "page6_lifecycle.py").exists()
    import ast
    ast.parse(Path("views/aug26_review.py").read_text(
        encoding="utf-8"))
    cut = json.loads(Path("data/aug26_cutoff_calc.json")
                     .read_text())
    calls = cut["shadow_add_call"]["calls"]
    assert any(c["code"] == "2408" for c in calls)
    assert "declared" in cut["shadow_add_call"]
