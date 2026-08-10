"""Page: Findings (c-136) — the visual digest of everything the
question campaigns measured. One screen a desk head can scan.

Sections: the auction verdict (hero numbers), the window
anatomy (volume U-profile), the era path (inverted U), the
decision tables (hot-start, attribution, borrow), the client
x-table, the analog matcher (interactive), and the honesty
panel (negative results + flags).
"""
import json
import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))


def _j(n):
    p = ROOT / "data" / n
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def render():
    import pandas as pd
    import plotly.graph_objects as go
    qa = _j("liquidity_qa_tw.json").get("answers", {})
    cond = _j("event_conditional_tw.json")
    strat = _j("strategist_tw.json")
    pers = _j("persona_study_tw.json")

    st.title("Findings — Taiwan rebalance windows")
    st.caption("157 windows, 2010→2026, delisted-safe, flows "
               "attached 2015+. Every number links to a result "
               "file; negative results shown, not hidden.")

    # ---- hero: the auction verdict -----------------------
    a = qa.get("AUCTION_close_vs_1325", {})
    st.header("The effective-day close auction")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Share of day's volume IN the auction",
              f"{a.get('auction_vol_share_med', 0):.0%}",
              help="median; p90 "
              f"{a.get('auction_vol_share_p90', 0):.0%}")
    c2.metric("Price jump close vs 13:25 (adds)",
              f"{a.get('ADD_jump_med', 0):+.1%}",
              help=f"n={a.get('ADD_n')}")
    c3.metric("(deletions)",
              f"{a.get('DEL_jump_med', 0):+.1%}",
              help=f"n={a.get('DEL_n')}")
    x = qa.get("Q33_tail_slippage_ADD", {})
    c4.metric("p95 |effective-day move|, high demand",
              f"{x.get('high_demand_p95_|eff_day|', 0):.1%}")
    st.info("**The verdict:** the auction does ~4/5 of the "
            "day at a median jump of ~zero — enormous in "
            "size, tiny in typical impact. The risk is the "
            "tail, not the median.")

    # ---- window anatomy ----------------------------------
    st.header("Anatomy of the window")
    prof = qa.get("Q6_volume_profile", {})
    if prof:
        ks = sorted(prof, key=int)
        fig = go.Figure(go.Bar(
            x=[int(k) for k in ks],
            y=[prof[k] for k in ks],
            marker_color=["#c0392b" if k == "0" else
                          "#1f4e79" for k in ks]))
        fig.update_layout(
            height=280, xaxis_title="days to effective (0=E)",
            yaxis_title="volume ×ADV (median)",
            margin=dict(t=10, b=0))
        st.plotly_chart(fig, use_container_width=True)
        st.caption("The U: a mid-window liquidity trough "
                   "(~1.2×) — where early orders pay most "
                   "impact — then 1.9× at E−1 and 12.3× at E. "
                   "Hangover: volume renormalizes in a median "
                   f"{qa.get('Q10_hangover_days_to_1.5xADV', {}).get('med')} days.")

    # ---- era path ----------------------------------------
    st.header("The era path (the trade grew, then crowded)")
    h1 = pers.get("H1_alpha_and_decay", {}).get("ADD_by_era",
                                                {})
    if h1:
        eras = list(h1)
        fig = go.Figure(go.Scatter(
            x=eras, y=[100 * (h1[e] or 0) for e in eras],
            mode="lines+markers+text",
            text=[f"{100 * (h1[e] or 0):.1f}%" for e in eras],
            textposition="top center",
            line=dict(color="#1f4e79", width=3)))
        fig.update_layout(height=260,
                          yaxis_title="ADD alpha day0→E−1 (%)",
                          margin=dict(t=10, b=0))
        st.plotly_chart(fig, use_container_width=True)

    # ---- the decision tables -----------------------------
    st.header("The decision tables")
    t1, t2, t3 = st.tabs(["Hot start (enter or skip?)",
                          "Early-strength attribution",
                          "Deletions: the borrow tell"])
    with t1:
        B = cond.get("B_hot_start_ADD", {})
        rows = [{"day-5 start": k, **v} for k, v in B.items()
                if isinstance(v, dict)]
        st.dataframe(pd.DataFrame(rows),
                     use_container_width=True, hide_index=True)
        st.caption("Hot starts keep paying (+6.7% more); cold "
                   "starts never wake. 'I missed it' is "
                   "empirically a reason to enter.")
    with t2:
        A = cond.get("A_early_attribution_ADD", {})
        rows = [{"bucket": k, **v} for k, v in A.items()
                if isinstance(v, dict)]
        st.dataframe(pd.DataFrame(rows),
                     use_container_width=True, hide_index=True)
        st.caption("Early strength WITH foreign flow = "
                   "accumulation (sticks). Without = froth "
                   "(runs hotter, round-trips −7.4%).")
    with t3:
        C = cond.get("C_del_borrow", {})
        pre = C.get("pre_ann_build", {})
        st.dataframe(pd.DataFrame([
            {"pre-ann borrow build": "low",
             **pre.get("low", {})},
            {"pre-ann borrow build": "high (>1.28×)",
             **pre.get("high", {})}]),
            use_container_width=True, hide_index=True)
        st.caption("Crowded shorts push the del further down "
                   "AND produce the only reliable bounce "
                   "(+3.3%) — buy-the-close works ONLY here.")

    # ---- the client x-table ------------------------------
    st.header("The tracker's x-table")
    xt = qa.get("Q31_client_x_table_ADD", {})
    rows = [{"execution": k, "cost vs close benchmark": v}
            for k, v in xt.items() if k != "read"]
    st.dataframe(pd.DataFrame(rows),
                 use_container_width=True, hide_index=True)
    st.caption("Early tranches buy BELOW the eventual close "
               "(the drift makes the close the top). The close "
               "buys zero tracking error at ~3.2% expected "
               "cost — that trade-off IS the client "
               "conversation.")

    # ---- analog matcher ----------------------------------
    st.header("Find historical analogs")
    c1, c2, c3, c4 = st.columns(4)
    act = c1.selectbox("Action", ["ADD", "DEL"])
    day = c2.slider("Days since announcement", 1, 14, 7)
    cr = c3.slider("Cumulative return so far (%)", -15.0,
                   25.0, 5.0) / 100
    sec = c4.selectbox("Sector", ["Any", "TECH", "FINANCIAL",
                                  "SHIPPING", "HEALTHCARE",
                                  "OTHER"])
    from analog_matcher import analogs
    res = analogs(act, day, cr,
                  None if sec == "Any" else sec)
    d = res["distribution"]
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Analogs", f"{d['n']} / {d['n_candidates']}")
    m2.metric("Then → E−1",
              f"{(d['then_to_Eminus1_med'] or 0):+.1%}")
    m3.metric("Effective day",
              f"{(d['eff_day_med'] or 0):+.1%}")
    m4.metric("Revert E+5", f"{(d['revert5_med'] or 0):+.1%}")
    st.dataframe(pd.DataFrame(res["analogs"]),
                 use_container_width=True, hide_index=True)
    st.caption("Named cases first, medians second — eight "
               "faces resist false precision better than one "
               "number. Years shown to expose era clustering.")

    # ---- honesty panel -----------------------------------
    st.header("What did NOT survive testing")
    st.markdown(
        "- **No era compression** of the volume profile — "
        "timing rules aren't going stale (Q8)\n"
        "- **No elasticity kink** — the TW close is deep "
        "(Q13)\n"
        "- **Borrow build SPEED adds nothing** over its level "
        "(Q24)\n"
        "- **The volume-up/drift-down 'scissors' is not in "
        "the data** (Q27)\n"
        "- **The PRE crowding score does not predict the "
        "close** (C4) — replaced by excess-vs-tide flow\n"
        "- Flagged small-n: the engine-surprise deletions "
        "(n=4), November-post-2023 (the Nov-25 cluster), "
        "large-ADV era confound")
