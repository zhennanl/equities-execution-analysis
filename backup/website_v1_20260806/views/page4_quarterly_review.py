"""Page 4 — Quarterly Client Review (QBR).

The Execution Solutions quarterly ritual, as a page: six sections, each one
client-deck exhibit. Aggregation lives in agents/quarterly_review.py; this
file only renders. Data source is the run library (every Page-1 execution
records a row); a labeled synthetic demo quarter is available so the
workflow can be shown before a library accumulates.
"""
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from agents.quarterly_review import (build_quarterly_review,
                                     synthesize_demo_quarter, MIN_CELL)
from agents.desk_pack import load_runs


def _mix_bar(mix: dict, title: str) -> go.Figure:
    keys = list(mix.keys()); vals = [mix[k] for k in keys]
    fig = go.Figure(go.Bar(x=vals, y=keys, orientation="h",
                           text=[f"{v:.0f}%" for v in vals], textposition="auto"))
    fig.update_layout(title=title, height=220, margin=dict(l=10, r=10, t=40, b=10),
                      xaxis_title="% of orders")
    return fig


def _box_by_algo(panel: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    for a, g in panel.groupby("algo"):
        fig.add_trace(go.Box(y=g["realized_bps"], name=f"{a} (n={len(g)})",
                             boxmean=True))
    fig.update_layout(title="Realized arrival cost by algo — distributions, not means",
                      yaxis_title="bps (＋ = cost)", height=380, showlegend=False)
    return fig


def _pred_vs_real(panel: pd.DataFrame) -> go.Figure:
    sc = panel.dropna(subset=["predicted_bps", "realized_bps"])
    fig = go.Figure()
    for a, g in sc.groupby("algo"):
        fig.add_trace(go.Scatter(x=g["predicted_bps"], y=g["realized_bps"],
                                 mode="markers", name=a, opacity=0.7,
                                 hovertext=g["ticker"]))
    lo = float(min(sc["predicted_bps"].min(), sc["realized_bps"].min()))
    hi = float(max(sc["predicted_bps"].max(), sc["realized_bps"].max()))
    fig.add_trace(go.Scatter(x=[lo, hi], y=[lo, hi], mode="lines",
                             line=dict(dash="dash", color="gray"),
                             name="realized = predicted"))
    fig.update_layout(title="Difficulty-adjusted view — predicted vs realized "
                            "(points above the line ran worse than conditions justified)",
                      xaxis_title="pre-trade predicted (bps)",
                      yaxis_title="realized (bps)", height=420)
    return fig


def _heatmap(panel: pd.DataFrame) -> go.Figure:
    pv = panel.pivot_table(index="market", columns="algo",
                           values="realized_bps", aggfunc="mean")
    ct = panel.pivot_table(index="market", columns="algo",
                           values="realized_bps", aggfunc="count")
    z = pv.where(ct >= MIN_CELL)          # no verdict below MIN_CELL
    txt = [[("" if not np.isfinite(z.iloc[i, j])
             else f"{z.iloc[i, j]:.0f}<br>n={int(ct.iloc[i, j])}")
            for j in range(z.shape[1])] for i in range(z.shape[0])]
    fig = go.Figure(go.Heatmap(z=z.values, x=list(z.columns), y=list(z.index),
                               text=txt, texttemplate="%{text}",
                               colorscale="RdYlGn_r",
                               colorbar_title="mean bps"))
    fig.update_layout(title=f"Mean cost, market × algo (cells with n < {MIN_CELL} blanked)",
                      height=360)
    return fig


def _pareto(outliers: pd.DataFrame, share: float) -> go.Figure:
    o = outliers.copy()
    o["label"] = o["ticker"] + " " + o["side"].str[0] + " (" + o["algo"] + ")"
    fig = go.Figure()
    fig.add_trace(go.Bar(x=o["label"], y=o["realized_bps"].abs(),
                         name="|realized| bps"))
    cum = o["realized_bps"].abs().cumsum() / o["realized_bps"].abs().sum() * share * 100
    fig.add_trace(go.Scatter(x=o["label"], y=cum, yaxis="y2", mode="lines+markers",
                             name="cum. share of book gross |cost|"))
    fig.update_layout(title=f"Outlier attribution — top {len(o)} orders = "
                            f"{share * 100:.0f}% of the quarter\'s gross |cost|",
                      yaxis_title="|bps|", height=380,
                      yaxis2=dict(overlaying="y", side="right", ticksuffix="%",
                                  range=[0, 100]),
                      legend=dict(orientation="h", y=1.12))
    return fig


def _trend(trend: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Bar(x=trend["month"], y=trend["n"], name="orders",
                         yaxis="y2", opacity=0.3))
    fig.add_trace(go.Scatter(x=trend["month"], y=trend["mean_bps"],
                             mode="lines+markers", name="mean bps"))
    fig.add_trace(go.Scatter(x=trend["month"], y=trend["median_bps"],
                             mode="lines+markers", name="median bps",
                             line=dict(dash="dot")))
    fig.update_layout(title="Inside-quarter trend", height=320,
                      yaxis_title="bps", yaxis2=dict(overlaying="y", side="right",
                                                     title="orders"))
    return fig


def render():
    st.title("📋 Quarterly Client Review (QBR)")
    st.caption("Six exhibits: flow profile → headline distributions → "
               "decomposition → difficulty-adjusted ranking → outlier "
               "attribution → trend & actions. Built from the run library "
               "(each Page-1 execution records a row).")

    runs = load_runs()
    demo = st.session_state.get("qbr_demo", False)
    c1, c2 = st.columns([3, 1])
    with c2:
        if st.button("Load labeled demo quarter" if not demo else
                     "Unload demo quarter"):
            st.session_state["qbr_demo"] = not demo
            st.rerun()
    if st.session_state.get("qbr_demo"):
        runs = synthesize_demo_quarter()
        st.info("🧪 SYNTHETIC demo quarter loaded — generated data, clearly "
                "labeled. The workflow is the exhibit, not the numbers.")

    df = pd.DataFrame(runs)
    if df.empty:
        st.warning("Run library is empty. Execute orders on Page 1, or load "
                   "the demo quarter.")
        return
    qs = sorted(pd.to_datetime(df["sim_day"], errors="coerce").dropna()
                .map(lambda t: f"{t.year}Q{(t.month - 1) // 3 + 1}").unique())
    with c1:
        quarter = st.selectbox("Quarter", qs, index=len(qs) - 1)

    r = build_quarterly_review(runs, quarter=quarter,
                               is_synthetic=bool(st.session_state.get("qbr_demo")))
    if not r.available:
        st.warning(r.reason)
        return

    # 1 — flow profile
    st.subheader("1 · Flow profile — what you sent us")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Orders", f"{r.n_orders}")
    m2.metric("Scored (pred+real)", f"{r.n_scored}")
    m3.metric("Median order size", f"{r.flow_profile['median_order_pct_adv']:.1f}% ADV")
    m4.metric("Markets", f"{len(r.flow_profile['market_mix_pct'])}")
    f1, f2 = st.columns(2)
    f1.plotly_chart(_mix_bar(r.flow_profile["algo_mix_pct"], "Algo mix"),
                    use_container_width=True)
    f2.plotly_chart(_mix_bar(r.flow_profile["market_mix_pct"], "Market mix"),
                    use_container_width=True)

    # 2 — headline
    st.subheader("2 · Headline costs — distributions, not means")
    h = r.headline
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Mean cost", f"{h['mean_bps']:+.1f} bps",
              delta=(f"{r.prior_quarter['delta_mean_bps']:+.1f} vs "
                     f"{r.prior_quarter['quarter']}") if r.prior_quarter else None,
              delta_color="inverse")
    m2.metric("Median [IQR]", f"{h['median_bps']:+.1f}",
              delta=f"[{h['p25']:+.1f}, {h['p75']:+.1f}]", delta_color="off")
    m3.metric("Model bias (real − pred)", f"{h.get('bias_bps', float('nan')):+.1f} bps")
    m4.metric("Within model band", f"{h.get('hit_rate_within_model_band', 0):.0f}%")

    # 3 — decomposition
    st.subheader("3 · Decomposition")
    st.plotly_chart(_box_by_algo(r.panel), use_container_width=True)
    st.plotly_chart(_heatmap(r.panel), use_container_width=True)
    t1, t2 = st.columns(2)
    t1.markdown("**By size bucket**")
    t1.dataframe(r.by_bucket, use_container_width=True)
    t2.markdown("**By urgency**")
    t2.dataframe(r.by_urgency, use_container_width=True)

    # 4 — difficulty-adjusted
    st.subheader("4 · Difficulty-adjusted ranking — the fair league table")
    st.plotly_chart(_pred_vs_real(r.panel), use_container_width=True)
    if r.adjusted_ranking.get("available"):
        st.dataframe(r.adjusted_ranking["table"], use_container_width=True)
        if r.adjusted_ranking["movers"]:
            st.warning(f"Rank moves once conditions are held fixed: "
                       f"{r.adjusted_ranking['movers']} — the raw table would "
                       "have mis-told this story.")
        st.caption(r.adjusted_ranking["note"])
    else:
        st.caption(f"Adjusted ranking unavailable: {r.adjusted_ranking.get('reason')}")

    # 5 — outliers
    st.subheader("5 · Outlier attribution")
    st.plotly_chart(_pareto(r.outliers, r.outlier_share), use_container_width=True)
    with st.expander("Outlier order detail"):
        st.dataframe(r.outliers, use_container_width=True)

    # 6 — trend & actions
    st.subheader("6 · Trend & actions")
    st.plotly_chart(_trend(r.monthly_trend), use_container_width=True)
    st.markdown("**Action items (rule-generated, each with its number):**")
    for rec in r.recommendations:
        st.warning(rec, icon="🔧")
    for c in r.caveats:
        st.caption(f"⚠️ {c}")
