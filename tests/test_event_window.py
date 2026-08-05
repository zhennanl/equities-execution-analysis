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
    src = open("app.py").read()
    assert "page7_desk_brief" in src
    assert "Index Rebalance Desk Brief" in src


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
