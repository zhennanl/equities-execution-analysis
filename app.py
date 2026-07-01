"""
Execution Analytics Platform
Page 1: Execution Algorithm Simulator  — full 5-agent pipeline
Page 2: Index Rebalancing Analysis     — event study (CAR + abnormal volume)
"""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import sys, os, datetime

sys.path.insert(0, os.path.dirname(__file__))
from agents.agent1_market_data      import fetch_market_data, MarketData, MARKET_INFO
from agents.agent3_algo_simulation  import IS_KAPPA_T
from agents.orchestrator            import run_pipeline
from agents.rebalancing_event_study import run_event_study, build_execution_insights

st.set_page_config(page_title="Execution Analytics Platform",
                   page_icon="📊", layout="wide",
                   initial_sidebar_state="expanded")

@st.cache_data(ttl=300, show_spinner=False)
def _cached_fetch(ticker_base, market):
    return fetch_market_data(ticker_base, market, log=None)

st.sidebar.title("Execution Analytics")
st.sidebar.markdown("---")
page = st.sidebar.radio("Module", [
    "📈 Execution Algorithm Simulator",
    "🔄 Index Rebalancing Analysis",
])

# ── Colour helpers ────────────────────────────────────────────────────────────
_VC = {"Tight":"#3b82f6","Normal":"#22c55e","Trending":"#f97316","Extremely Trending":"#ef4444"}
_TC = {"Trending":"#f97316","Mean-Reverting":"#8b5cf6","Neutral":"#6b7280"}
_AC = {"VWAP":"#1f77b4","TWAP":"#2ca02c","POV":"#ff7f0e","IS":"#9467bd",
       "MOC":"#17becf","MOO":"#bcbd22","LIQ":"#e377c2","STEALTH":"#7f7f7f"}

def _badge(txt, col):
    return (f'<span style="background:{col};color:white;padding:3px 10px;'
            f'border-radius:12px;font-weight:600;font-size:0.85rem;">{txt}</span>')


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 1 — EXECUTION ALGORITHM SIMULATOR
# ══════════════════════════════════════════════════════════════════════════════
if page == "📈 Execution Algorithm Simulator":

    st.title("📈 Execution Algorithm Simulator")
    st.markdown("Enter a stock and order parameters. The 5-agent pipeline assesses market "
                "conditions and recommends the optimal execution algorithm.")

    st.markdown("### Inputs")
    c1,c2,c3,c4 = st.columns(4)
    with c1: market = st.selectbox("Market", list(MARKET_INFO.keys()))
    with c2:
        ex = {
            "Taiwan (TWSE)":    "2330",
            "Hong Kong (HKEX)": "0700",
            "Japan (TSE)":      "7203",
            "Korea (KRX)":      "005930",
            "US":               "AAPL",
            "Singapore (SGX)":  "D05",
            "China-A Shanghai": "600519",
            "China-A Shenzhen": "000858",
            "India (NSE)":      "RELIANCE",
            "Australia (ASX)":  "BHP",
            "Thailand (SET)":   "PTT",
            "Indonesia (IDX)":  "BBCA",
            "Malaysia (KLSE)":  "1155",
            "Vietnam (HOSE)":   "VCB",
        }
        sfx = MARKET_INFO[market]["suffix"]
        ticker_input = st.text_input(f"Ticker (excl. '{sfx}')", value=ex.get(market, ""))
    with c3: order_pct_adv = st.slider("Order Size (% ADV)", 1, 25, 5)
    with c4: urgency = st.radio("Urgency", ["Low","Medium","High"], horizontal=True)

    run = st.button("▶ Run Agent Pipeline", type="primary", use_container_width=True)
    st.markdown("---")

    if run:
        # -- Fetch (still owns its own cache — the orchestrator wraps
        # everything downstream of the fetch, not the fetch itself, so
        # re-running the pipeline for a different order size/urgency on the
        # same ticker doesn't get blocked by a stale cached full-pipeline
        # result; see agents/orchestrator.py's module docstring) ----------
        msg = st.empty(); msg.info("⏳ Fetching market data…")
        try:
            data = _cached_fetch(ticker_input, market)
        except RuntimeError as e:
            s = str(e)
            (st.warning if "rate" in s.lower() else st.error)(f"❌ {s}"); st.stop()
        except Exception as e:
            st.error(f"❌ {e}"); st.stop()
        msg.success("✅ Market data loaded — cached 5 min.")

        # -- Orchestrator: runs Agents 2-8, conditionally skipping/degrading
        # at runtime rather than a fixed unconditional sequence; see
        # agents/orchestrator.py and agents/context.py ----------------------
        with st.spinner("Running agent pipeline…"):
            ctx = run_pipeline(data, order_pct_adv, urgency)

        _icon = {"ran": "✅", "skipped": "⏭️", "failed": "❌"}
        _trace_line = "&nbsp;&nbsp;".join(
            f"{_icon[t['status']]} {t['agent'].replace('agent', 'A').replace('_', ' ')}"
            for t in ctx.trace
        )
        st.markdown(f"<div style='font-size:0.85rem'>{_trace_line}</div>", unsafe_allow_html=True)
        with st.expander("Orchestration detail (what ran, what was skipped, and why)"):
            for t in ctx.trace:
                st.caption(f"{_icon[t['status']]} **{t['agent']}** — {t['status']}" + (f": {t['detail']}" if t['detail'] else ""))

        if ctx.memo is None:
            failed = [t for t in ctx.trace if t["status"] == "failed"]
            detail = "; ".join(f"{t['agent']}: {t['detail']}" for t in failed) or "an upstream agent did not complete"
            st.error(f"❌ Could not produce a recommendation — {detail}")
            st.stop()

        regime, sim, comp, memo   = ctx.regime, ctx.sim, ctx.comp, ctx.memo
        pretrade, posttrade       = ctx.pretrade, ctx.posttrade
        earnings, critic          = ctx.earnings, ctx.critic

        st.markdown("---")
        order_shares = ctx.order_shares

        # ── AGENT 5 — RECOMMENDATION (pinned top) ────────────────────────────
        st.markdown("### Agent 5 — Recommendation")
        pri_col = _AC.get(memo.primary_algo, "#6b7280")
        sec_col = _AC.get(memo.secondary_algo, "#6b7280")
        ra, rb = st.columns(2)
        ra.markdown(f"**Primary**")
        ra.markdown(_badge(memo.primary_algo, pri_col) +
                    f"&nbsp;&nbsp;**{comp.summary.loc[memo.primary_algo,'Mean (bps)']:.1f} bps avg**",
                    unsafe_allow_html=True)
        rb.markdown(f"**Secondary / Fallback**")
        rb.markdown(_badge(memo.secondary_algo, sec_col) +
                    f"&nbsp;&nbsp;{comp.summary.loc[memo.secondary_algo,'Mean (bps)']:.1f} bps avg",
                    unsafe_allow_html=True)
        st.markdown("")
        for flag in memo.risk_flags:
            if "No material" in flag:
                st.success(f"✅ {flag}")
            else:
                st.warning(f"⚠️ {flag}")
        with st.expander("📄 Full Recommendation Memo"):
            st.markdown(memo.memo_text)

        # ── AGENT 8 — CRITIC REVIEW (independent second opinion) ─────────────
        st.markdown("")
        if critic is not None:
            if critic.approved:
                st.success("✅ **Critic Review:** No material issues found — recommendation approved as-is.")
            else:
                st.warning("⚠️ **Critic Review:** flagged concerns worth confirming before executing.")
            for f in critic.findings:
                if f.message.startswith("No material"):
                    continue
                (st.warning if f.severity == "override" else st.caption)(
                    f"{'⚠️ ' if f.severity == 'override' else '• '}{f.message}"
                )
        st.caption("Independent second pass over Agent 5's pick (Agent 8) — checks fill-qualification, "
                  "earnings-date risk, and spread-reliability/size interaction. Doesn't silently change "
                  "the recommendation; it flags concerns for the analyst to confirm.")

        # ── AGENT 1 OUTPUT ────────────────────────────────────────────────────
        st.markdown("---")
        st.markdown("### Agent 1 — Market Data")
        k1,k2,k3,k4 = st.columns(4)
        k1.metric("Ticker", data.ticker)
        k2.metric("Price", f"${data.current_price:,.2f}")
        k3.metric("ADV (shares)", f"{data.adv_shares:,.0f}")
        k4.metric("Realised Vol", f"{data.realized_vol_ann:.1%}")
        k5,k6,k7,k8 = st.columns(4)
        k5.metric("Order (shares)", f"{order_shares:,.0f}")
        k6.metric("Order (% ADV)", f"{order_pct_adv}%")
        k7.metric("Notional", f"${order_shares*data.current_price/1e6:.2f}M")
        k8.metric("Urgency", urgency)

        with st.expander("📊 Volume Profile & Price Chart"):
            vp = data.vol_profile
            fv = go.Figure(go.Bar(x=vp["time"], y=vp["volume_pct"]*100, marker_color="#1f77b4"))
            fv.update_layout(xaxis_title="Time",yaxis_title="% Daily Vol",height=240,
                             margin=dict(l=40,r=20,t=10,b=50),plot_bgcolor="white",
                             yaxis=dict(gridcolor="#eee"),showlegend=False)
            n = len(vp)
            fv.update_xaxes(tickvals=vp["time"].iloc[::max(1,n//12)].tolist(), tickangle=-45)
            st.plotly_chart(fv, use_container_width=True)

            ld = data.intraday[data.intraday.index.date == data.intraday.index.date[-1]]
            fp = go.Figure(go.Scatter(x=ld.index,y=ld["Close"],mode="lines",
                                      line=dict(color="#2ca02c",width=1.8)))
            fp.update_layout(xaxis_title="Time",yaxis_title="Price",height=200,
                             margin=dict(l=40,r=20,t=10,b=30),plot_bgcolor="white",
                             yaxis=dict(gridcolor="#eee"),showlegend=False)
            st.plotly_chart(fp, use_container_width=True)

        # ── PRE-TRADE ANALYTICS ───────────────────────────────────────────────
        st.markdown("---")
        st.markdown("### Pre-Trade Analytics")
        st.caption("What this order should cost, and whether the market can absorb it — "
                   "computed before committing to an algorithm.")
        if pretrade is not None:
            pc1, pc2 = st.columns(2)
            with pc1:
                st.markdown("**Estimated Spread Cost**")
                if pretrade.spread_bps is not None:
                    sc1, sc2 = st.columns(2)
                    sc1.metric("Quoted spread (median)", f"{pretrade.spread_bps:.1f} bps")
                    sc2.metric("Est. one-way crossing cost", f"{pretrade.half_spread_bps:.1f} bps")
                    st.caption(f"Corwin-Schultz high-low estimator, {pretrade.spread_n_obs} recent "
                              f"daily observations (mean {pretrade.spread_mean_bps:.1f} bps).")
                    if pretrade.spread_reliability != "Normal":
                        st.warning(f"⚠️ {pretrade.spread_reliability}")
                else:
                    st.info(f"ℹ️ {pretrade.spread_note}")

            with pc2:
                st.markdown("**Capacity — Days to Complete**")
                st.dataframe(pretrade.capacity, use_container_width=True)
                st.caption(f"At {urgency} urgency's participation rate, this order needs "
                          f"~{pretrade.days_at_chosen_urgency:.2f} trading days to complete.")

            st.markdown("")
            st.markdown("**Expected Cost Range by Algorithm (bps)**")
            st.caption(f"Method: {pretrade.cost_range_method}. Percentile bands are used over Mean ± Std "
                      "when enough simulated days are available, since impact-cost distributions are "
                      "known to be fat-tailed (Almgren et al. 2005) rather than symmetric-Gaussian.")
            st.dataframe(pretrade.expected_cost_range.style.format({
                "Low (bps)": "{:+.1f}", "Expected (bps)": "{:+.1f}", "High (bps)": "{:+.1f}",
                "Avg Fill": "{:.1%}",
            }), use_container_width=True)

            if pretrade.almgren.available:
                st.markdown("")
                st.markdown("**Almgren et al. (2005) Calibrated Impact Cross-Check**")
                am1, am2, am3 = st.columns(3)
                am1.metric("Permanent impact", f"{pretrade.almgren.permanent_impact_bps:.1f} bps")
                am2.metric("Temporary impact", f"{pretrade.almgren.temporary_impact_bps:.1f} bps")
                am3.metric("Total expected impact", f"{pretrade.almgren.realized_impact_bps:.1f} bps")
                st.caption(pretrade.almgren.note)

            for note in pretrade.notes:
                if "Spread estimate reliability" in note or "Almgren et al." in note:
                    continue   # already shown inline above
                st.caption(f"• {note}")
        else:
            st.info("ℹ️ Pre-trade estimate not available for this ticker — see Orchestration detail above.")

        st.markdown("")
        st.markdown("**Earnings Calendar Check** (Agent 7)")
        if earnings is not None and earnings.available:
            ne1, ne2 = st.columns(2)
            ne1.metric("Next earnings", str(earnings.next_earnings_date.date()))
            ne2.metric("Trading days until", earnings.trading_days_until,
                      delta="near-term" if earnings.is_near_term else "outside near-term window",
                      delta_color="inverse" if earnings.is_near_term else "off")
            (st.warning if earnings.is_near_term else st.caption)(earnings.risk_note)
        else:
            st.caption(f"ℹ️ {earnings.reason if earnings is not None else 'Earnings check unavailable.'}")

        # ── AGENT 9 — MARKET MICROSTRUCTURE & ORDER-FLOW TOXICITY ────────────
        st.markdown("")
        st.markdown("**Market Microstructure & Liquidity** (Agent 9)")
        micro = ctx.microstructure
        if micro is not None:
            mc1, mc2 = st.columns(2)
            with mc1:
                st.markdown("*Kyle's Lambda (price impact per unit order flow)*")
                kl = micro.kyle_lambda
                if kl.available:
                    st.metric("λ (bps per 1% ADV net flow, next-bar)", f"{kl.lambda_bps_per_pct_adv:+.2f}",
                             delta=f"t={kl.t_stat:.1f}, R²={kl.r_squared:.1%}, n={kl.n_obs}", delta_color="off")
                    st.caption(kl.note)
                else:
                    st.info(f"ℹ️ {kl.reason}")
            with mc2:
                st.markdown("*VPIN (order-flow toxicity, time-bar approximation)*")
                vp = micro.vpin
                if vp.available:
                    vpin_color = {"Low": "#22c55e", "Normal": "#3b82f6",
                                 "Elevated": "#f97316", "High": "#ef4444"}.get(vp.label, "#6b7280")
                    st.markdown(_badge(f"{vp.label} ({vp.vpin_score:.2f})", vpin_color), unsafe_allow_html=True)
                    st.caption(f"{vp.note} ({vp.window_bars}-bar trailing window.)")
                else:
                    st.info(f"ℹ️ {vp.reason}")
            st.caption("Kyle's lambda and VPIN are estimated from Bulk Volume Classification (Easley, "
                      "Lopez de Prado & O'Hara 2012) applied to 5-min OHLCV bars — a time-bar "
                      "approximation, not canonical tick-data microstructure, since no free order-book "
                      "or trade-level feed is available across these markets. See Agent 9's module "
                      "docstring for the full methodology and caveats.")
        else:
            st.info("ℹ️ Microstructure assessment not available — see Orchestration detail above.")

        # ── AGENT 2 OUTPUT ────────────────────────────────────────────────────
        st.markdown("---")
        st.markdown("### Agent 2 — Market Regime")
        st.markdown(f"**{regime.summary}**"); st.markdown("")
        r1,r2,r3 = st.columns(3)

        vc = _VC.get(regime.vol_label,"#6b7280")
        with r1:
            st.markdown("**Intraday Range**")
            st.markdown(_badge(regime.vol_label, vc), unsafe_allow_html=True); st.markdown("")
            pct=(regime.vol_ratio-1)*100
            st.metric("vs 20d median",f"{regime.vol_ratio:.2f}×",delta=f"{pct:+.0f}%",
                      delta_color="inverse" if regime.vol_label=="Tight" else "normal")
            caps={"Tight":"Compressed range — muted impact.","Normal":"In line with history.",
                  "Trending":"Wide range — elevated impact.","Extremely Trending":"Extreme range — consider deferring."}
            st.caption(caps.get(regime.vol_label,""))

        vpc={"U-Shaped":"#3b82f6","Uniform":"#22c55e","Midday-Heavy":"#f97316"}.get(regime.volume_label,"#6b7280")
        with r2:
            st.markdown("**Volume Pattern**")
            st.markdown(_badge(regime.volume_label, vpc), unsafe_allow_html=True); st.markdown("")
            st.metric("U-shape score",f"{regime.u_shape_score:.2f}×",delta="open/close vs midday",delta_color="off")
            vcaps={"U-Shaped":"Heavy open/close — VWAP aligns with flow.",
                   "Uniform":"Even distribution — TWAP minimises timing risk.",
                   "Midday-Heavy":"Unusual pattern — review liquidity timing."}
            st.caption(vcaps.get(regime.volume_label,""))

        tc=_TC.get(regime.trend_label,"#6b7280")
        with r3:
            st.markdown("**Price Trend (Variance Ratio Test)**")
            st.markdown(_badge(regime.trend_label, tc), unsafe_allow_html=True); st.markdown("")
            if regime.vr_available:
                st.metric(f"VR(q={regime.vr_q})", f"{regime.vr_ratio:.2f}",
                         delta=f"z*={regime.vr_zstat:+.2f} ({'significant' if regime.vr_significant else 'not significant'})",
                         delta_color="off")
            else:
                st.metric("VR test", "insufficient bars", delta_color="off")
            tcaps={"Trending":"VR(q)>1, significant — positive serial correlation; IS may front-load beneficially.",
                   "Mean-Reverting":"VR(q)<1, significant — negative serial correlation; patient algos favoured.",
                   "Neutral":"VR(q) not significantly different from 1 (random walk) at this horizon."}
            st.caption(tcaps.get(regime.trend_label,""))
            st.caption(f"Supporting stat — lag-1 autocorr: {regime.autocorr:+.3f}")
            if regime.vr_detail:
                with st.expander("Variance ratio detail (Lo-MacKinlay 1988)"):
                    vr_df = pd.DataFrame(regime.vr_detail)
                    st.dataframe(vr_df, use_container_width=True, hide_index=True)
                    st.caption("z_robust is the heteroskedasticity-robust statistic (used for the "
                              "headline label above); |z| >= 1.96 ≈ 95% significance under the "
                              "random-walk null.")

        # ── AGENT 3 OUTPUT ────────────────────────────────────────────────────
        st.markdown("---")
        st.markdown("### Agent 3 — Algorithm Simulation")
        st.markdown(f"Simulated **{order_pct_adv}% ADV** buy order "
                    f"({order_shares:,.0f} shares · ${order_shares*data.current_price/1e6:.2f}M)  "
                    f"| Arrival price: **${sim.arrival_price:.2f}**")

        tbl = [{
            "Algorithm": n,
            "Avg Exec Price": f"${r.avg_exec_price:.2f}",
            "Slippage (bps)": f"{r.slippage_bps:+.1f}",
            "Mkt Impact (bps)": f"{r.market_impact_bps:.1f}",
            "Opp. Cost (bps)": f"{r.opportunity_cost_bps:+.1f}",
            "Total Cost (bps)": f"{r.total_cost_bps:.1f}",
            "Fill Rate": f"{r.completion_pct:.0%}",
        } for n, r in sim.algos.items()]
        df3 = pd.DataFrame(tbl).set_index("Algorithm")
        best3 = min(sim.algos, key=lambda k: sim.algos[k].total_cost_bps)
        st.dataframe(df3.style.apply(
            lambda row: ["background-color:#dcfce7;"]*len(row) if row.name==best3 else [""]*len(row), axis=1
        ), use_container_width=True)
        st.caption("Opp. Cost = Perold (1988) opportunity cost on any unfilled shares, priced against "
                   "the simulation day's period-end close vs. arrival — already included in Total Cost.")

        a_names = list(sim.algos.keys())
        fc = go.Figure()
        fc.add_trace(go.Bar(name="Slippage",x=a_names,y=[sim.algos[a].slippage_bps for a in a_names],marker_color="#60a5fa"))
        fc.add_trace(go.Bar(name="Mkt Impact",x=a_names,y=[sim.algos[a].market_impact_bps for a in a_names],marker_color="#f87171"))
        fc.add_trace(go.Bar(name="Opp. Cost",x=a_names,y=[sim.algos[a].opportunity_cost_bps for a in a_names],marker_color="#fbbf24"))
        fc.update_layout(barmode="stack",yaxis_title="Cost (bps)",height=260,
                         margin=dict(l=40,r=20,t=10,b=30),plot_bgcolor="white",
                         yaxis=dict(gridcolor="#eee"),
                         legend=dict(orientation="h",yanchor="bottom",y=1.02,xanchor="right",x=1))
        st.plotly_chart(fc, use_container_width=True)

        with st.expander("🕰️ Schedule Data Source (look-ahead-bias check)"):
            for name, r in sim.algos.items():
                st.caption(f"**{name}** — {r.schedule_note}")

        with st.expander("📅 Execution Schedules — Shares per Bar"):
            tabs3 = st.tabs(list(sim.algos.keys()))
            for tab,(name,r) in zip(tabs3,sim.algos.items()):
                with tab:
                    sc=r.schedule
                    fs=go.Figure()
                    fs.add_trace(go.Bar(x=sc["time"],y=sc["shares_traded"],
                                        name="Shares/bar",marker_color=_AC[name]))
                    fs.add_trace(go.Scatter(x=sc["time"],y=sc["cumulative"],
                                            name="Cumulative",yaxis="y2",
                                            line=dict(color="#6b7280",width=1.5,dash="dot")))
                    fs.update_layout(height=240,margin=dict(l=40,r=60,t=10,b=30),
                                     plot_bgcolor="white",yaxis=dict(gridcolor="#eee"),
                                     yaxis2=dict(overlaying="y",side="right",showgrid=False),
                                     legend=dict(orientation="h",yanchor="bottom",y=1.02))
                    st.plotly_chart(fs, use_container_width=True)

        # ── AGENT 4 OUTPUT ────────────────────────────────────────────────────
        st.markdown("---")
        st.markdown("### Agent 4 — Performance Comparison")
        n_days = len(comp.daily_costs)
        wins   = comp.win_counts[comp.best_algo]
        st.markdown(f"**{comp.best_algo}** ranked best on **{wins}/{n_days} simulated days** "
                    f"with {comp.summary.loc[comp.best_algo,'Mean (bps)']:.1f} bps average total cost.")

        with st.expander("📆 Multi-Day Cost Table (bps)", expanded=True):
            disp = comp.daily_costs.copy().round(1)
            disp.loc["Mean"] = comp.daily_costs.mean().round(1)
            disp.loc["Std"]  = comp.daily_costs.std().round(1)
            def _hi(row):
                if row.name in ("Mean","Std"): return [""]*len(row)
                best = row.idxmin()
                return ["background-color:#dcfce7;" if c==best else "" for c in row.index]
            st.dataframe(disp.style.apply(_hi,axis=1), use_container_width=True)

        with st.expander("📐 Order Size Sensitivity — Total Cost (bps)"):
            st.markdown("*Each order size is fully re-simulated across every historical day — not a "
                        "formula shortcut — so fill-rate degradation and Perold opportunity cost show "
                        "up correctly for POV / Liquidity-Seeking / Stealth at larger sizes.*")
            def _color_sens(val):
                try:
                    v=float(val)
                    g = max(0, min(255, int(255 - v*1.5)))
                    return f"background-color:rgba(239,68,68,{min(1,v/200):.2f});" if v>50 \
                        else f"background-color:rgba(34,197,94,{min(1,(100-v)/100):.2f});"
                except: return ""
            st.dataframe(comp.sensitivity.style.applymap(_color_sens), use_container_width=True)

        with st.expander("⚖️ Almgren-Chriss Efficient Frontier (IS trajectory shape)"):
            st.markdown("*Implementation Shortfall now trades the real Almgren-Chriss (2000) optimal "
                        "trajectory. This shows the cost/risk trade-off the urgency setting is picking "
                        "a point on — higher κT front-loads execution to cut timing risk, at the cost "
                        "of concentrating market impact.*")
            cur_kt = IS_KAPPA_T.get(urgency)
            fac = go.Figure()
            fac.add_trace(go.Scatter(x=comp.ac_frontier["risk_score_norm"], y=comp.ac_frontier["pct_in_first_third"],
                                     mode="lines+markers", line=dict(color="#9467bd", width=2),
                                     marker=dict(size=7), name="κT grid",
                                     text=[f"κT={k}" for k in comp.ac_frontier["kappa_T"]],
                                     hovertemplate="%{text}<br>Risk (norm): %{x:.2f}<br>% in first third: %{y:.0f}%<extra></extra>"))
            if cur_kt is not None:
                cur_row = comp.ac_frontier.iloc[(comp.ac_frontier["kappa_T"] - cur_kt).abs().argsort()[:1]]
                fac.add_trace(go.Scatter(x=cur_row["risk_score_norm"], y=cur_row["pct_in_first_third"],
                                         mode="markers", marker=dict(size=14, color="#ef4444", symbol="star"),
                                         name=f"Current ({urgency}, κT={cur_kt})"))
            fac.update_layout(xaxis_title="Timing-risk proxy (normalized)", yaxis_title="% of order in first third of session",
                              height=300, plot_bgcolor="white", yaxis=dict(gridcolor="#eee"), xaxis=dict(gridcolor="#eee"),
                              margin=dict(l=40,r=20,t=10,b=40),
                              legend=dict(orientation="h",yanchor="bottom",y=1.02))
            st.plotly_chart(fac, use_container_width=True)

        # ── POST-TRADE TCA ────────────────────────────────────────────────────
        st.markdown("---")
        st.markdown("### Post-Trade TCA")
        st.caption(f"How the {memo.primary_algo} fill actually did, benchmarked against the standard "
                   "TCA reference set — computed after execution.")
        if posttrade is not None:
            tc1, tc2 = st.columns([3, 2])
            with tc1:
                st.markdown("**Benchmark Comparison**")
                bt = posttrade.benchmarks.table
                st.dataframe(bt.style.format({
                    "Benchmark Price": "${:.4f}", "Slippage vs Benchmark (bps)": "{:+.2f}",
                }).apply(
                    lambda row: ["background-color:#fee2e2;" if row["Slippage vs Benchmark (bps)"] > 0
                                else "background-color:#dcfce7;"] * len(row), axis=1
                ), use_container_width=True)
                st.caption("Positive = paid more than that benchmark; negative = paid less. "
                          "Arrival matches the Total Cost table above; VWAP/TWAP/Close are the "
                          "additional standard TCA reference points.")

            with tc2:
                st.markdown("**Cost Percentile**")
                pctl = posttrade.cost_percentile
                if pctl.available:
                    st.metric(f"{memo.primary_algo} today vs its own history",
                             f"{pctl.percentile:.0f}th percentile",
                             delta="lower = cheaper than usual", delta_color="off")
                    st.caption(f"Based on {pctl.n_obs} historical simulated days.")
                else:
                    st.info(f"ℹ️ {pctl.reason}")

            st.markdown("")
            st.markdown("**Impact Reversion Check**")
            rev = posttrade.reversion
            if rev.available:
                rv1, rv2, rv3 = st.columns(3)
                rv1.metric("Price at last fill", f"${rev.price_at_last_fill:.2f}")
                rv2.metric("Price at day end", f"${rev.price_at_day_end:.2f}")
                rv3.metric("Reversion", f"{rev.reversion_bps:+.1f} bps")
                st.caption(rev.interpretation)
            else:
                st.info(f"ℹ️ {rev.reason}")
            st.caption("⚠️ Directional diagnostic only — there is no control group to isolate impact "
                      "we caused from ordinary intraday drift or news, so this should not be read as "
                      "a precise measurement.")

            st.markdown("")
            st.markdown("**Impact Decomposition** (Almgren et al. 2005 — Permanent / Temporary)")
            decomp = posttrade.impact_decomposition
            if decomp.available:
                dc1, dc2, dc3 = st.columns(3)
                dc1.metric("Permanent (I)", f"{decomp.permanent_impact_bps:+.1f} bps")
                dc2.metric("Realized total (J)", f"{decomp.realized_impact_bps:+.1f} bps")
                dc3.metric("Temporary (K = J - I/2)", f"{decomp.temporary_impact_bps:+.1f} bps")
                st.caption(decomp.note)
            else:
                st.info(f"ℹ️ {decomp.reason}")
            st.caption("⚠️ Same caveat as the reversion check above — no control group, directional "
                      "evidence only. I uses the day's closing price as the 'settled' reference point "
                      "(the paper's convention is ~30 min post-execution); K nets out half of I per "
                      "the model's own bookkeeping (see agent6's module docstring).")


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 2 — INDEX REBALANCING ANALYSIS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "🔄 Index Rebalancing Analysis":

    st.title("🔄 Index Rebalancing Analysis")
    st.markdown(
        "Event study of stock price and volume around an index constituent addition. "
        "Uses the **market model** (OLS) to compute Cumulative Abnormal Returns (CAR) "
        "and abnormal volume over a user-specified window around the effective rebalancing date."
    )

    st.markdown("### Inputs")
    i1,i2,i3 = st.columns(3)
    with i1:
        index_choice = st.selectbox("Index", ["MSCI Taiwan","Hang Seng","Nikkei 225","KOSPI 200"])
        market_added = st.selectbox("Market", list(MARKET_INFO.keys()), key="rebal_mkt")
    with i2:
        rebal_date   = st.date_input("Rebalancing Effective Date",
                                     value=datetime.date.today())
        event_window = st.slider("Event Window (±days)", 5, 20, 10)
    with i3:
        ticker_added = st.text_input("Added Constituent Ticker", value="2330",
                                     placeholder="e.g. 2330 for TSMC")
        st.markdown("")
        st.markdown("")
        run_rebal = st.button("▶ Run Event Study", type="primary", use_container_width=True)

    with st.expander("⚙️ Execution-Cost Analysis Inputs (optional)"):
        st.caption("Feeds the closing-auction concentration, reversal, drift, flow-to-trade, "
                   "and impact-calibration analyses below. All optional — leave blank to skip.")
        e1, e2, e3 = st.columns(3)
        with e1:
            objective = st.radio("Execution Objective", ["Cost-Minimizing", "Index Tracker"],
                                 help="Index Tracker = must match the benchmark's closing print "
                                      "(tracking-error constrained). Cost-Minimizing = no such "
                                      "constraint; free to trade opportunistically.")
        with e2:
            know_announcement = st.checkbox("I know the announcement date")
            announcement_date = st.date_input(
                "Announcement Date", value=datetime.date(2024, 8, 16),
                disabled=not know_announcement
            ) if know_announcement else None
        with e3:
            weight_change_pct = st.number_input(
                "Index weight change (%)", min_value=0.0, value=0.0, step=0.01, format="%.3f",
                help="Full index weight assigned on inclusion (or removed on deletion)."
            )
            tracked_aum_b = st.number_input(
                "AUM tracking this index ($B)", min_value=0.0, value=0.0, step=1.0,
                help="Estimated total AUM benchmarked to this index — drives the flow-to-trade estimate."
            )
            tracked_aum_usd = tracked_aum_b * 1e9

    st.markdown("---")

    if run_rebal:
        with st.spinner("Running event study…"):
            try:
                es = run_event_study(
                    ticker_base=ticker_added,
                    market=market_added,
                    rebal_date=rebal_date,
                    event_window=event_window,
                    index_name=index_choice,
                )
            except ValueError as e:
                st.error(f"❌ {e}"); st.stop()
            except Exception as e:
                st.error(f"❌ Unexpected error: {e}"); st.stop()

            try:
                insights = build_execution_insights(
                    es, market_added, objective=objective,
                    announcement_date=announcement_date,
                    weight_change_pct=weight_change_pct if weight_change_pct > 0 else None,
                    tracked_aum_usd=tracked_aum_usd if tracked_aum_usd > 0 else None,
                )
            except Exception as e:
                insights = None
                st.warning(f"⚠️ Execution-cost insights could not be computed: {e}")

        st.success(f"✅ Event study complete — {es.ticker} · {es.index_name} · T = {es.T.date()}")
        st.markdown(f"**Market model:** α = {es.alpha:.5f}, β = {es.beta:.3f}")
        st.markdown("")

        # ── Summary table ─────────────────────────────────────────────────────
        st.markdown("### Key-Day Summary")
        st.dataframe(es.summary.style.format({
            "CAR (%)": "{:+.2f}", "Ab. Volume (×)": "{:.2f}", "Price (idx)": "{:.1f}"
        }), use_container_width=True)

        # ── Charts ────────────────────────────────────────────────────────────
        st1, st2, st3 = st.tabs(["📈 CAR", "📊 Abnormal Volume", "💹 Price Performance"])

        with st1:
            fig_car = go.Figure()
            fig_car.add_shape(type="line", x0=0, x1=0,
                              y0=min(es.car)*100*1.1, y1=max(es.car)*100*1.1,
                              line=dict(color="red", dash="dash", width=1))
            fig_car.add_trace(go.Scatter(
                x=es.rel_days, y=es.car*100,
                mode="lines+markers", line=dict(color="#1f77b4", width=2),
                marker=dict(size=5), name="CAR (%)"
            ))
            fig_car.add_shape(type="line", x0=min(es.rel_days), x1=max(es.rel_days),
                              y0=0, y1=0, line=dict(color="gray", dash="dot", width=1))
            fig_car.update_layout(
                title=f"Cumulative Abnormal Return — {es.ticker}",
                xaxis_title="Day relative to T (rebalancing date)",
                yaxis_title="CAR (%)",
                height=360, plot_bgcolor="white",
                yaxis=dict(gridcolor="#eee"),
                margin=dict(l=50, r=30, t=50, b=50),
            )
            st.plotly_chart(fig_car, use_container_width=True)
            st.caption(
                "CAR rising before T reflects pre-event price pressure as index trackers "
                "and arbitrageurs front-run the inclusion. Post-T decline indicates reversal."
            )

        with st2:
            colors = ["#f97316" if v > 1.5 else "#3b82f6" for v in es.ab_vol]
            fig_av = go.Figure(go.Bar(
                x=es.rel_days, y=es.ab_vol, marker_color=colors, name="Abnormal Vol (×)"
            ))
            fig_av.add_shape(type="line", x0=min(es.rel_days), x1=max(es.rel_days),
                             y0=1, y1=1, line=dict(color="gray", dash="dot", width=1))
            fig_av.add_shape(type="line", x0=0, x1=0, y0=0, y1=max(es.ab_vol)*1.05,
                             line=dict(color="red", dash="dash", width=1))
            fig_av.update_layout(
                title=f"Abnormal Volume — {es.ticker}",
                xaxis_title="Day relative to T",
                yaxis_title="Volume / Estimation-window Average",
                height=360, plot_bgcolor="white",
                yaxis=dict(gridcolor="#eee"),
                margin=dict(l=50, r=30, t=50, b=50),
            )
            st.plotly_chart(fig_av, use_container_width=True)
            st.caption("Orange bars (>1.5×) indicate significantly elevated volume — "
                       "typical in the 1–3 days surrounding the effective date.")

        with st3:
            fig_px = go.Figure(go.Scatter(
                x=es.rel_days, y=es.norm_price,
                mode="lines+markers", line=dict(color="#2ca02c", width=2),
                marker=dict(size=5), name="Price (T=100)"
            ))
            fig_px.add_shape(type="line", x0=0, x1=0,
                             y0=min(es.norm_price)*0.99, y1=max(es.norm_price)*1.01,
                             line=dict(color="red", dash="dash", width=1))
            fig_px.add_shape(type="line", x0=min(es.rel_days), x1=max(es.rel_days),
                             y0=100, y1=100, line=dict(color="gray", dash="dot", width=1))
            fig_px.update_layout(
                title=f"Indexed Price Performance — {es.ticker} (T = 100)",
                xaxis_title="Day relative to T",
                yaxis_title="Price index (T = 100)",
                height=360, plot_bgcolor="white",
                yaxis=dict(gridcolor="#eee"),
                margin=dict(l=50, r=30, t=50, b=50),
            )
            st.plotly_chart(fig_px, use_container_width=True)

        # ── EXECUTION-COST INSIGHTS ───────────────────────────────────────────
        if insights is not None:
            st.markdown("---")
            st.markdown("### Execution-Cost Insights")
            st.caption("Extends the event study above into inputs for an execution-algorithm "
                       "decision around the rebalancing date, rather than just measuring the "
                       "price/volume effect.")

            ic1, ic2 = st.columns(2)

            with ic1:
                st.markdown("**Closing Auction Concentration**")
                c = insights.concentration
                if c.available:
                    st.metric("Final-window volume concentration",
                             f"{c.concentration_multiple_window:.1f}×" if c.concentration_multiple_window else "n/a",
                             delta=f"T: {c.t_last_window_pct:.1f}% vs baseline {c.baseline_last_window_pct:.1f}%",
                             delta_color="off")
                    st.caption(f"Final bar alone: {c.t_last_bar_pct:.1f}% of day's volume on T "
                              f"vs {c.baseline_last_bar_pct:.1f}% baseline "
                              f"({c.n_baseline_days} comparison days).")
                else:
                    st.info(f"ℹ️ {c.reason}")

                st.markdown("")
                st.markdown("**Post-Event Reversal**")
                r = insights.reversal
                if r.available:
                    st.markdown(_badge(r.classification, "#f97316" if "Transient" in r.classification
                                       else "#3b82f6" if "Partial" in r.classification
                                       else "#22c55e" if "Permanent" in r.classification
                                       else "#8b5cf6" if "Momentum" in r.classification else "#6b7280"),
                               unsafe_allow_html=True)
                    st.caption(f"Pre-event run-up: {r.pre_event_runup_pct:+.2f}% · "
                              f"Post-event move (5d): {r.post_event_move_5d_pct:+.2f}% · "
                              f"Reversal fraction: {r.reversal_fraction_5d:+.0%}"
                              if r.reversal_fraction_5d is not None else
                              f"Pre-event run-up: {r.pre_event_runup_pct}")
                else:
                    st.info(f"ℹ️ {r.reason}")

            with ic2:
                st.markdown("**Pre-Announcement vs Pre-Effective Drift**")
                d = insights.drift
                if d.available:
                    st.caption(f"Pre-announcement CAR: {d.pre_announcement_car_pct:+.2f}% · "
                              f"Announcement→T CAR: {d.announcement_to_effective_car_pct:+.2f}%")
                    if d.pct_of_pre_event_move_after_announcement is not None:
                        st.metric("% of pre-event move after announcement",
                                 f"{d.pct_of_pre_event_move_after_announcement:.0f}%")
                else:
                    st.info(f"ℹ️ {d.reason}")

                st.markdown("")
                st.markdown("**Flow-to-Trade / Impact Calibration**")
                f, ec = insights.flow, insights.eta_calib
                if f is not None:
                    st.caption(f"Estimated flow: {f.shares:,.0f} shares (${f.notional_usd/1e6:.1f}M)"
                              + (f" · {f.flow_pct_adv:.1f}% of estimation-window ADV" if f.flow_pct_adv else ""))
                else:
                    st.caption("Enter index weight change % and tracked AUM above to estimate flow-to-trade.")
                if ec.available:
                    st.caption(f"Implied event-day η ≈ {ec.implied_eta:.2f} vs baseline η = {ec.baseline_eta:.2f} "
                              f"(shock CAR T-1→T+1: {ec.shock_car_pct:+.2f}%)")
                else:
                    st.caption(f"η calibration: {ec.reason}")

            st.markdown("")
            st.warning(f"⚠️ **Crowding caveat:** {insights.crowding_note}")

            st.markdown("")
            rec = insights.recommendation
            algo_col = _AC.get(rec.recommended_algo, "#6b7280")
            st.markdown(f"**Recommended strategy — {rec.objective} objective**")
            st.markdown(_badge(rec.recommended_algo, algo_col), unsafe_allow_html=True)
            st.markdown(rec.rationale)
            for note in rec.notes:
                st.caption(f"• {note}")
