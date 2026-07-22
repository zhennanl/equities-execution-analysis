"""Page 2 — Index Rebalancing Analysis (extracted from app.py, B8)."""
from views.common import *          # noqa: F401,F403 — shared imports
from views.common import _badge, _AC, _VC, _TC, _cached_fetch  # noqa: F401


def render():

    st.title("🔄 Index Rebalancing Analysis")
    st.markdown(
        "Event study of stock price and volume around an index constituent addition. "
        "Uses the **market model** (OLS) to compute Cumulative Abnormal Returns (CAR) "
        "and abnormal volume over a user-specified window around the effective rebalancing date."
    )

    # ── Agent 12 — Rebalance Calendar Monitor (auto-fetched index changes) ───
    # Defaults for the manual inputs below (setdefault → the "Use selected
    # event" button can overwrite them programmatically without widget-state
    # conflicts).
    st.session_state.setdefault("rebal_ticker", "2330")
    st.session_state.setdefault("rebal_date", datetime.date.today())
    st.session_state.setdefault("rebal_ann_date", datetime.date(2024, 8, 16))

    st.markdown("### 📅 Latest Index Changes — Agent 12 (Rebalance Calendar Monitor)")
    st.caption(
        "Fetches real constituent adds/deletes from the three major providers' public "
        "announcement pages — **MSCI** (structured announcement feed, fully parsed), "
        "**FTSE Russell** (LSEG press releases at URLs constructed from the review calendar), "
        "**S&P DJI** (PR Newswire releases, summary table parsed). Pick an event to "
        "auto-fill the event-study inputs below instead of typing them manually."
    )
    with st.expander("📡 Fetch / pick a real index change", expanded=False):
        a12_tab_ch, a12_tab_cal = st.tabs(["📋 Latest changes", "🗓 Review calendar"])

        with a12_tab_ch:
            f1, f2 = st.columns([3, 1])
            with f1:
                a12_sel = st.multiselect("Providers", list(A12_PROVIDERS),
                                         default=list(A12_PROVIDERS), key="a12_providers")
            with f2:
                st.markdown("")
                a12_refresh = st.button("🔄 Refresh now", use_container_width=True,
                                        help="On-demand fetch of the providers' public "
                                             "announcement pages (a handful of requests).")

            a12_cache = st.session_state.get("a12_cache")
            if a12_cache is None:
                a12_disk = a12_load_cache()
                if a12_disk:
                    a12_cache = a12_disk
                    st.session_state["a12_cache"] = a12_cache
            if a12_refresh:
                with st.spinner("Fetching announcements from providers…"):
                    a12_evs, a12_errs = a12_fetch_all(tuple(a12_sel) or A12_PROVIDERS)
                if a12_evs:
                    a12_save_cache(a12_evs, a12_errs)
                a12_cache = {
                    "fetched_at": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
                    "events": a12_evs, "errors": a12_errs,
                }
                st.session_state["a12_cache"] = a12_cache
                for a12_p, a12_msg in a12_errs.items():
                    st.warning(f"⚠️ {a12_p}: {a12_msg}")

            if a12_cache and a12_cache["events"]:
                st.caption(f"Data as of **{a12_cache['fetched_at']}** (UTC). These are public "
                           "provider pages meant for manual reading — refresh on demand; "
                           "don't turn this into a high-frequency poller.")
                a12_evs = [e for e in a12_cache["events"]
                           if e.provider in (a12_sel or list(A12_PROVIDERS))]
                a12_df = pd.DataFrame([{
                    "Provider": e.provider, "Index": e.index_name, "Action": e.action,
                    "Security": e.security_name, "Ticker": e.ticker or "—",
                    "Market": e.market or "—", "Effective": e.effective_date or "—",
                    "Announced": e.announced_date or "—", "Event": e.event_type,
                    "Note": e.notes,
                } for e in a12_evs])
                st.dataframe(a12_df, use_container_width=True, height=240)

                a12_runnable = [e for e in a12_evs if e.market and e.effective_date]
                if a12_runnable:
                    a12_labels = [f"{e.provider} · {e.index_name} · {e.action} · "
                                  f"{e.security_name} · eff {e.effective_date}"
                                  for e in a12_runnable]
                    a12_pick = st.selectbox("Event to load into the inputs below",
                                            a12_labels, key="a12_pick")
                    if st.button("⤵️ Use selected event"):
                        a12_ev = a12_runnable[a12_labels.index(a12_pick)]
                        a12_tkr = a12_ev.ticker
                        if not a12_tkr:
                            with st.spinner(f"Looking up Yahoo ticker for {a12_ev.security_name}…"):
                                a12_tkr = suggest_yahoo_ticker(a12_ev.security_name, a12_ev.market)
                        a12_sfx = MARKET_INFO.get(a12_ev.market, {}).get("suffix", "")
                        if a12_sfx and a12_tkr.endswith(a12_sfx):
                            a12_tkr = a12_tkr[:-len(a12_sfx)]
                        st.session_state["rebal_mkt"] = a12_ev.market
                        st.session_state["p2_side14"] = ("Sell (deletion)"
                            if a12_ev.action == "Delete" else "Buy (addition)")
                        st.session_state["rebal_action_hint"] = a12_ev.action
                        st.session_state["rebal_date"] = datetime.date.fromisoformat(a12_ev.effective_date)
                        if a12_ev.index_name in INDEX_PROXIES:
                            st.session_state["rebal_index"] = a12_ev.index_name
                        if a12_ev.announced_date:
                            st.session_state["rebal_ann_know"] = True
                            st.session_state["rebal_ann_date"] = datetime.date.fromisoformat(a12_ev.announced_date)
                        if a12_tkr:
                            st.session_state["rebal_ticker"] = a12_tkr
                            st.success(f"Loaded **{a12_ev.security_name}** → ticker "
                                       f"`{a12_tkr}`, market *{a12_ev.market}*, effective "
                                       f"{a12_ev.effective_date}. Review the inputs below, "
                                       "then run the event study.")
                        else:
                            st.warning(f"Loaded market/date for **{a12_ev.security_name}**, but "
                                       "couldn't auto-resolve a Yahoo ticker — please type the "
                                       "ticker manually below.")
                else:
                    st.info("No fetched event has both a supported market and an effective "
                            "date — enter the inputs manually below.")
            else:
                st.info("No index-change data yet — click **🔄 Refresh now** to fetch the "
                        "latest announcements (or let the scheduled refresh job populate "
                        "the cache).")

        with a12_tab_cal:
            st.caption("Approximate next review/rebalance dates per provider, from their "
                       "published cadence rules (exact dates can shift — always confirm "
                       "against the provider notice).")
            st.dataframe(pd.DataFrame(a12_upcoming_reviews()),
                         use_container_width=True, hide_index=True)


    st.markdown("### Inputs")
    i1,i2,i3 = st.columns(3)
    with i1:
        index_choice = st.selectbox("Index", list(INDEX_PROXIES.keys()), key="rebal_index")
        market_added = st.selectbox("Market", list(MARKET_INFO.keys()), key="rebal_mkt")
    with i2:
        rebal_date   = st.date_input("Rebalancing Effective Date", key="rebal_date")
        event_window = st.slider("Event Window (±days)", 5, 20, 10)
    with i3:
        ticker_added = st.text_input("Added Constituent Ticker", key="rebal_ticker",
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
            know_announcement = st.checkbox("I know the announcement date", key="rebal_ann_know")
            announcement_date = st.date_input(
                "Announcement Date", key="rebal_ann_date",
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
        e4, e5, _e6 = st.columns(3)
        with e4:
            float_mcap_b = st.number_input(
                "Float market cap ($B, optional)", min_value=0.0, value=0.0, step=0.5,
                help="Feeds the expected-move calculator's flow-multiplier band "
                     "(Gabaix-Koijen M=3-8 on flow as % of float cap). Leave 0 to "
                     "show the sqrt-law band only.")
        with e5:
            si_change_pct = st.number_input(
                "Short-interest change into event (%, optional)", min_value=-100.0,
                max_value=500.0, value=0.0, step=5.0,
                help="Change in reported shares short over the run-up to the event "
                     "(exchange data lags ~2 weeks). Feeds the crowding score; "
                     "leave 0 if unknown.")

    with st.expander("📦 Basket mode — run the whole program (exception blotter)"):
        st.caption("Upload the rebalance program as CSV with columns `ticker,market,side"
                   "[,shares]` (shares optional → 5% of each name's ADV). Uses the "
                   "effective date, event window and index proxy from the Inputs above. "
                   "One event study per name — run it once pre-event, not repeatedly "
                   "(Yahoo rate-limits).")
        bk_file = st.file_uploader("Program CSV", type="csv", key="p2_basket_csv")
        if st.button("▶ Run basket", key="p2_basket_run", disabled=bk_file is None):
            try:
                bk_df = pd.read_csv(bk_file)
                bk_df.columns = [c.strip().lower() for c in bk_df.columns]
                bk_missing = {"ticker", "market"} - set(bk_df.columns)
                if bk_missing:
                    st.error(f"❌ CSV missing column(s): {', '.join(sorted(bk_missing))}")
                else:
                    with st.spinner(f"Running {len(bk_df)} event studies…"):
                        st.session_state["p2_basket_res"] = run_basket(
                            bk_df, rebal_date, event_window, index_choice)
            except Exception as bk_e:
                st.error(f"❌ Basket failed: {bk_e}")
        bk_res = st.session_state.get("p2_basket_res")
        if bk_res is not None:
            bk_red = int((bk_res["Auction flag"] == "RED").sum())
            bk_err = int((bk_res["Error"] != "").sum())
            st.markdown(f"**Exception blotter — worst first** · {bk_red} RED auction "
                        f"flag(s) · {bk_err} failed name(s)")
            st.dataframe(bk_res, use_container_width=True, hide_index=True)
            st.download_button("⬇️ Blotter (.csv)", bk_res.to_csv(index=False),
                               file_name="rebalance_blotter.csv")

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

        # Persist so the Best-Execution Strategy section below survives
        # widget-triggered reruns (same pattern as Page 1's pipeline results).
        st.session_state["p2_es"] = es
        st.session_state["p2_insights"] = insights
        st.session_state["p2_objective"] = objective

        # ── Trader verdict — the one line to read first (evidence follows) ──
        try:
            _side_hint = str(st.session_state.get("p2_side14", "Buy (addition)"))
            _vside = "Sell" if _side_hint.startswith("Sell") else "Buy"
            _vsize = 5.0
            if insights is not None and insights.flow is not None and insights.flow.flow_pct_adv:
                _vsize = max(float(insights.flow.flow_pct_adv), 0.5)
            _vana = analyze_strategies(es, side=_vside, order_pct_adv=_vsize)
            _verd = build_verdict(es, _vana, objective)
            (st.error if _verd.auction_flag == "RED"
             else st.warning if _verd.auction_flag == "AMBER"
             else st.success)(f"🎯 **{_verd.headline}**")
            st.caption("Defaults: side from the loaded event, size from flow-to-trade "
                       "(else 5% ADV) — refine both in the Agent 14 section below, "
                       "where the trade card and playbook are generated.")
        except Exception as _verr:
            st.caption(f"Verdict banner unavailable: {_verr}")
        try:
            _i_T0 = int(np.where(np.asarray(es.rel_days) == 0)[0][0])
            record_event(es, insights,           # event library (data/event_library.json)
                         action=st.session_state.get("rebal_action_hint", ""),
                         t_day_volume_multiple=float(np.asarray(es.ab_vol)[_i_T0]))
        except Exception:
            pass

        st.success(f"✅ Event study complete — {es.ticker} · {es.index_name} · T = {es.T.date()}")
        st.markdown(f"**Market model:** α = {es.alpha:.5f}, β = {es.beta:.3f}")
        st.markdown("")

        # ── Summary table ─────────────────────────────────────────────────────
        st.markdown("### Key-Day Summary")
        st.dataframe(es.summary.style.format({
            "CAR (%)": "{:+.2f}", "CAR t": "{:+.2f}", "Ab. Volume (x)": "{:.2f}", "Price (idx)": "{:.1f}"
        }), use_container_width=True)

        # ── Charts ────────────────────────────────────────────────────────────
        st1, st2, st3 = st.tabs(["📈 CAR", "📊 Abnormal Volume", "💹 Price Performance"])

        with st1:
            fig_car = go.Figure()
            fig_car.add_shape(type="line", x0=0, x1=0,
                              y0=min(es.car)*100*1.1, y1=max(es.car)*100*1.1,
                              line=dict(color="red", dash="dash", width=1))
            if getattr(es, "car_sigma", None) is not None:
                _b = 1.96 * es.car_sigma * 100
                fig_car.add_trace(go.Scatter(x=es.rel_days, y=_b, mode="lines",
                                             line=dict(width=0), showlegend=False,
                                             hoverinfo="skip"))
                fig_car.add_trace(go.Scatter(x=es.rel_days, y=-_b, mode="lines",
                                             line=dict(width=0), fill="tonexty",
                                             fillcolor="rgba(150,150,150,0.15)",
                                             name="±1.96σ (null band)", hoverinfo="skip"))
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
                "and arbitrageurs front-run the inclusion. Post-T decline indicates reversal. "
                "Shaded band = ±1.96σ under the no-abnormal-return null (Brown-Warner "
                "single-firm, forecast-error corrected): CAR outside the band is "
                "statistically distinguishable from normal co-movement. Event-induced "
                "variance makes the band anti-conservative on the event days themselves — "
                "read as guidance, not a hard test."
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
            st.caption(library_context_line(insights, library_stats()))

            st.markdown("")
            cx1, cx2 = st.columns(2)
            with cx1:
                st.markdown("**Crowding Score** — anticipatory arbitrage proxies")
                _cs = crowding_score(
                    es, insights, announcement_date=announcement_date,
                    short_interest_change_pct=si_change_pct if si_change_pct != 0 else None)
                if _cs.available:
                    st.markdown(_badge(f"{_cs.tier} · {_cs.score:.0f}/100", _cs.color),
                                unsafe_allow_html=True)
                    st.caption(_cs.detail)
                    st.caption(f"→ {_cs.insight}")
                    st.session_state["p2_crowding"] = _cs
                else:
                    st.info(f"ℹ️ {_cs.reason}")
            with cx2:
                st.markdown("**Expected Move** — pre-event flow calibration")
                _em = expected_move(
                    insights.flow, es,
                    float_mcap_usd=float_mcap_b * 1e9 if float_mcap_b > 0 else None,
                    lib=library_stats())
                if _em.available:
                    st.caption(_em.detail)
                else:
                    st.info(f"ℹ️ {_em.reason}")

            with st.expander("🕵️ Positioning check — who is already in this "
                             "name? (footprint + official sources)"):
                from agents.positioning import (positioning_footprint,
                                                positioning_sources_table)
                _ann_rel = None
                try:
                    if announcement_date is not None:
                        _ed = pd.DatetimeIndex(pd.to_datetime(es.event_dates))
                        _pos = _ed.searchsorted(pd.Timestamp(announcement_date))
                        if 0 <= _pos < len(es.rel_days):
                            _ann_rel = int(np.asarray(es.rel_days)[_pos])
                except Exception:
                    _ann_rel = None
                _pf = positioning_footprint(es, announcement_rel=_ann_rel)
                if _pf.available:
                    _pcol = {"HEAVY": "#ef4444", "MODERATE": "#f97316",
                             "LIGHT": "#22c55e"}[_pf.verdict]
                    st.markdown(_badge(f"Footprint: {_pf.verdict}", _pcol),
                                unsafe_allow_html=True)
                    st.caption(_pf.detail)
                    for _c in _pf.caveats:
                        st.caption(f"⚠️ {_c}")
                else:
                    st.info(f"ℹ️ Footprint: {_pf.reason}")
                st.markdown("**Official positioning data by market (what a "
                            "desk actually pulls):**")
                st.dataframe(positioning_sources_table(),
                             use_container_width=True, hide_index=True)
                st.caption("Free sources cover the SHORT side and investor-"
                           "type flows well; long pre-positioning has no "
                           "public register anywhere — the footprint above "
                           "is the honest estimator. Broker-only channels "
                           "listed in the last row for completeness.")

            with st.expander("🤖 AI rebalance-interest monitor — daily "
                             "tracking ahead of the event (demo)"):
                from agents.rebalance_monitor import (monitor_report,
                                                      monitor_alerts,
                                                      learn_weights,
                                                      demo_monitor_panel,
                                                      demo_event_panel)
                st.caption("Candidates from the rulebook screener, scored "
                           "daily on abnormal volume / drift / range (+ "
                           "short-balance and news feeds when wired). "
                           "Weights are LEARNED from the event library and "
                           "shipped only if they beat the transparent "
                           "static composite under a DM gate — otherwise "
                           "static ships (house rule). Transition alerts "
                           "fire once, like the dealer cockpit.")
                _lw = learn_weights(demo_event_panel(40, signal=3.0))
                st.caption(f"Weight source: **{_lw.source}** — {_lw.note or _lw.reason}")
                _mr = monitor_report(demo_monitor_panel(), _lw,
                                     extras={"HOT.T": {"news_count": 8}})
                st.dataframe(_mr, use_container_width=True, hide_index=True)
                _al, _tiers = monitor_alerts(
                    _mr, st.session_state.get("rebal_mon_tiers"))
                st.session_state["rebal_mon_tiers"] = _tiers
                if _al:
                    for _a in _al:
                        st.warning(f"🔔 {_a['ticker']} — {_a['message']}",
                                   icon="🤖")
                else:
                    st.caption("No new tier transitions this scan.")
                st.caption("⚠️ Demo panel + synthetic event library shown. "
                           "Live deployment: candidates from the screener, "
                           "bars from kdb+/tick store, short balances from "
                           "the official regimes, news counts from an NLP "
                           "layer. Design: docs/AI_REBALANCE_MONITOR_DESIGN.md")

            _ls = getattr(es, "liquidity_shift", None)
            if _ls is not None:
                st.markdown("")
                st.markdown("**Post-Event Liquidity & Beta Shift** — estimation window vs T+1 onward "
                            "(Hegde-McDermott 2003; Barberis-Shleifer-Wurgler 2005)")
                if _ls.available:
                    lsc1, lsc2, lsc3 = st.columns(3)
                    lsc1.metric("Beta", f"{_ls.beta_pre:.2f} → {_ls.beta_post:.2f}",
                                help="Market-model beta re-fit on post-event days — comovement "
                                     "typically jumps on inclusion / drops on deletion.")
                    if _ls.edge_pre_bps and _ls.edge_post_bps:
                        lsc2.metric("EDGE spread (bps)",
                                    f"{_ls.edge_pre_bps:.1f} → {_ls.edge_post_bps:.1f}")
                    if _ls.amihud_pre is not None and _ls.amihud_post is not None:
                        lsc3.metric("Amihud (bps/$1M)",
                                    f"{_ls.amihud_pre:.2f} → {_ls.amihud_post:.2f}")
                    st.caption(_ls.note)
                else:
                    st.info(f"ℹ️ Liquidity shift: {_ls.reason}")

            st.markdown("")
            rec = insights.recommendation
            algo_col = _AC.get(rec.recommended_algo, "#6b7280")
            st.markdown(f"**Recommended strategy — {rec.objective} objective**")
            st.markdown(_badge(rec.recommended_algo, algo_col), unsafe_allow_html=True)
            st.markdown(rec.rationale)
            for note in rec.notes:
                st.caption(f"• {note}")


    # ── AGENT 14 — BEST-EXECUTION STRATEGY (renders after a study has run;
    #    persists across reruns so its widgets are interactive) ─────────────
    if "p2_es" in st.session_state:
        es14 = st.session_state["p2_es"]
        st.markdown("---")
        st.markdown("## 🎯 Best-Execution Strategy — Agent 14 (Rebalance Strategist)")
        st.caption(
            "Simulates the four literature-anchored rebalance execution strategies on this "
            "event's **actual** price/volume path and scores the trade-off institutional "
            "clients care about: implementation cost vs the pre-announcement decision price "
            "**versus** tracking difference vs the effective-day closing print. Evidence base "
            "and strategy anchors: `docs/INDEX_REBALANCE_RESEARCH.md` (Harris-Gurel 1986; "
            "Madhavan 2003; Petajisto 2011; Greenwood-Sammon 2025)."
        )

        _w = int(es14.rel_days[-1])
        a141, a142, a143, a144 = st.columns(4)
        with a141:
            side14 = st.selectbox("Side", ["Buy (addition)", "Sell (deletion)"], key="p2_side14")
        with a142:
            size14 = st.number_input("Order size (% of ADV)", min_value=0.5, max_value=500.0,
                                     value=5.0, step=0.5, key="p2_size14",
                                     help="Tip: the flow-to-trade estimate above (index weight "
                                          "change × tracked AUM) is the institutional way to "
                                          "size this.")
        with a143:
            prefrac14 = st.slider("S2 pre-position fraction", 0.1, 0.9, 0.5, 0.1, key="p2_prefrac14")
        with a144:
            postfrac14 = st.slider("S3 post-effective fraction", 0.1, 0.9, 0.5, 0.1, key="p2_postfrac14")

        with st.expander("⚙️ Event-timing & model parameters"):
            e141, e142, e143 = st.columns(3)
            with e141:
                _ann_default = -5
                try:
                    if st.session_state.get("rebal_ann_know") and st.session_state.get("rebal_ann_date"):
                        _ann_ts = pd.Timestamp(st.session_state["rebal_ann_date"])
                        _diffs = abs(pd.to_datetime(es14.event_dates) - _ann_ts)
                        _ann_default = int(es14.rel_days[int(_diffs.argmin())])
                except Exception:
                    pass
                _lo14 = int(es14.rel_days[0])
                _ann_default = int(max(min(_ann_default, -1), _lo14))
                if _lo14 <= -2:
                    ann14 = st.slider("Announcement day (relative to T)", _lo14, -1,
                                      _ann_default, key="p2_ann14",
                                      help="Defaults to the announcement date entered above when "
                                           "provided (e.g. from Agent 12), else T-5 "
                                           "(Greenwood-Sammon mean A→E gap).")
                else:
                    ann14 = -1
                    st.caption("Announcement day fixed at T-1 — the event window has no "
                               "earlier pre-event days (widen the event window to move it).")
            with e142:
                if _w >= 2:
                    post14 = st.slider("Post-effective horizon (trading days)", 1, _w,
                                       min(10, _w), key="p2_post14")
                else:
                    post14 = max(_w, 0)
                    st.caption(f"Post-effective horizon fixed at {post14} trading day(s) — "
                               "no further post-event history exists yet for this effective "
                               "date. S3 (post-effective completion) is skipped when this is 0.")
            with e143:
                auc14 = st.slider("Closing-auction share of T-day volume", 0.05, 0.30, 0.10,
                                  0.01, key="p2_auc14",
                                  help="Auction capacity assumption — measured against the "
                                       "observed effective-day volume, which already includes "
                                       "the rebalance surge.")

        try:
            ana14 = analyze_strategies(
                es14, side="Buy" if side14.startswith("Buy") else "Sell",
                order_pct_adv=float(size14), ann_rel_day=int(ann14),
                pre_frac=float(prefrac14), post_frac=float(postfrac14),
                post_days=int(post14), auction_normal_share=float(auc14))
        except Exception as e14:
            st.error(f"❌ Strategy analysis failed: {e14}")
            ana14 = None

        if ana14 is not None:
            k141, k142, k143, k144 = st.columns(4)
            k141.metric("Decision price (A close)", f"{ana14.decision_price:,.2f}")
            k142.metric("Effective close (T)", f"{ana14.effective_close:,.2f}")
            k143.metric("Order", f"{ana14.order_shares:,.0f} sh · {ana14.order_pct_adv:.1f}% ADV")
            k144.metric(f"Realized move T→T+{ana14.params['post_days']}",
                        f"{ana14.realized_post_reversal_bps:+,.0f} bps",
                        help="Abnormal (market-model) move after the effective date — the "
                             "reversal S3 is designed to capture, measured on this event.")

            st.dataframe(ana14.frontier, use_container_width=True, hide_index=True)

            fig14 = go.Figure()
            for s14 in ana14.strategies:
                fig14.add_trace(go.Scatter(
                    x=[s14.abs_tracking_bps], y=[s14.cost_vs_decision_bps],
                    mode="markers+text", text=[s14.name.split()[0]],
                    textposition="top center", marker=dict(size=14),
                    name=s14.name))
            fig14.update_layout(
                height=340, margin=dict(l=10, r=10, t=40, b=10),
                title="The client trade-off: cost vs tracking (lower-left dominates)",
                xaxis_title="|Tracking difference| vs effective close (bps)",
                yaxis_title="Implementation cost vs decision price (bps)",
                showlegend=False)
            st.plotly_chart(fig14, use_container_width=True)

            _obj14 = st.session_state.get("p2_objective", "Cost-Minimizing")
            if _obj14 == "Index Tracker":
                _best14 = min(ana14.strategies, key=lambda s: (s.abs_tracking_bps, s.cost_vs_decision_bps))
            else:
                _best14 = min(ana14.strategies, key=lambda s: (s.cost_vs_decision_bps, s.abs_tracking_bps))
            st.success(f"**Recommended for a {_obj14} mandate: {_best14.name}** — "
                       f"cost {_best14.cost_vs_decision_bps:+.1f} bps vs decision, "
                       f"tracking {_best14.tracking_diff_bps:+.1f} bps vs the print, "
                       f"{_best14.auction_pct:.0f}% of the order in the closing auction.")
            st.markdown(ana14.rationale)

            for s14 in ana14.strategies:
                with st.expander(f"📋 {s14.name} — schedule & fills"):
                    st.caption(s14.description)
                    st.dataframe(s14.schedule, use_container_width=True, hide_index=True)
                    for n14 in s14.notes:
                        st.warning(f"⚠️ {n14}")

            with st.expander("⚠️ Model caveats (read before showing a client)"):
                for c14 in ana14.caveats:
                    st.markdown(f"- {c14}")

            # ── Trader pack: card, EMS export, conditional playbook ─────────
            st.markdown("### 🧾 Trader Pack")
            _obj14v = st.session_state.get("p2_objective", "Cost-Minimizing")
            verd14 = build_verdict(es14, ana14, _obj14v,
                                   auction_normal_share=float(auc14))
            _ins14 = st.session_state.get("p2_insights")
            card_txt = trade_card_text(es14, _ins14, ana14, verd14)
            st.code(card_txt, language=None)
            _steps14 = build_playbook(
                es14, _ins14, ana14, verd14, library_stats_row=library_stats(),
                crowding_tier=getattr(st.session_state.get("p2_crowding"), "tier", None))
            d141, d142, d143 = st.columns(3)
            with d141:
                st.download_button("⬇️ Trade card (.txt)", card_txt,
                                   file_name=f"{es14.ticker}_trade_card.txt",
                                   use_container_width=True)
            with d142:
                st.download_button("⬇️ All schedules (.csv)", schedules_csv(ana14),
                                   file_name=f"{es14.ticker}_schedules.csv",
                                   use_container_width=True)
            with d143:
                st.download_button("⬇️ Playbook (.txt)", playbook_text(es14, _steps14),
                                   file_name=f"{es14.ticker}_playbook.txt",
                                   use_container_width=True)
            with st.expander("📋 Conditional playbook — triggers to confirm before the event"):
                st.caption("Thresholds are proposals anchored on this event and the "
                           "event library; confirm or override them at the desk.")
                for _pi, _ps in enumerate(_steps14, 1):
                    st.markdown(f"**{_pi}.** {_ps}")

            # ── Best-ex record: the decision documented AT decision time ─────
            try:
                _bx = build_bestex_record(es14, verd14, ana14, _obj14v, _steps14,
                                          library_n=library_stats().get("n", 0))
                record_bestex(_bx)
                bx1, bx2 = st.columns([1, 3])
                with bx1:
                    st.download_button("⬇️ Best-ex record (.json)", bestex_record_json(_bx),
                                       file_name=f"{es14.ticker}_{_bx['effective_date']}_bestex.json",
                                       use_container_width=True)
                with bx2:
                    st.caption("📋 Decision, evidence, and thresholds persisted at decision "
                               "time (data/bestex_records.json) — the quarterly best-ex "
                               "narrative assembles from these records instead of being "
                               "reconstructed after the fact.")
            except Exception:
                pass




    # ── Rulebook reconstitution screener (session 6j) ─────────────────────
    st.markdown("---")
    with st.expander("🔮 Reconstitution screener — predict adds/deletes from "
                     "the rulebooks (MSCI GIMI / FTSE approximations)"):
        from agents.reconstitution import (predict_msci, predict_ftse,
                                           expected_flow, demo_universe,
                                           MSCIRules, FTSERules)
        st.caption("Applies the PUBLIC structure of each methodology to a "
                   "candidate universe: MSCI-style GMSR at 85% cumulative "
                   "free-float coverage with the 0.5–1.15× size range (QIR "
                   "hurdle configurable); FTSE-style 90/111 rank buffer "
                   "with reserve pairing. Approximations — country-level "
                   "size interplay, FIF granularity, nationality/fast-entry "
                   "rules and provider discretion are NOT modeled.")
        _ru, _rm = demo_universe()
        _prov = st.radio("Methodology", ["MSCI-style (SAIR)", "MSCI-style (QIR)",
                                         "FTSE-style (rank buffer)"],
                         horizontal=True, key="recon_prov")
        _aum = st.number_input("Passive AUM benchmarked to index (USD bn, "
                               "your estimate — an input, not a claim)",
                               1.0, 20000.0, 500.0) * 1e9
        if _prov.startswith("MSCI"):
            _res = predict_msci(_ru, _rm, MSCIRules(
                review="QIR" if "QIR" in _prov else "SAIR"))
            st.caption(f"GMSR ≈ ${_res['gmsr_usd']:,.0f} | add above "
                       f"${_res['add_threshold_usd']:,.0f} | delete below "
                       f"${_res['delete_threshold_usd']:,.0f}")
        else:
            _res = predict_ftse(_ru, _rm, FTSERules(index_size=60,
                                                    add_rank=54,
                                                    delete_rank=67))
        _c1, _c2 = st.columns(2)
        with _c1:
            st.markdown(f"**Predicted adds ({len(_res['adds'])})**")
            st.dataframe(_res["adds"], use_container_width=True, hide_index=True)
        with _c2:
            st.markdown(f"**Predicted deletes ({len(_res['deletes'])})**")
            st.dataframe(_res["deletes"], use_container_width=True, hide_index=True)
        if len(_res["watchlist"]):
            st.markdown("**Watchlist (within the buffer bands)**")
            st.dataframe(_res["watchlist"], use_container_width=True, hide_index=True)
        _chg = (list(_res["adds"].get("ticker", []))
                + list(_res["deletes"].get("ticker", [])))
        if _chg:
            st.markdown("**Passive-flow estimate (naive, input-driven)**")
            st.dataframe(expected_flow(_ru, _chg, _aum),
                         use_container_width=True, hide_index=True)
        st.caption(f"⚠️ {_res['note']} Demo universe shown — feed the real "
                   "candidate universe (cap/float/ADV) to screen a live "
                   "review. Sources: MSCI GIMI methodology, FTSE UK ground "
                   "rules (see docs/INDEX_REBALANCE_RESEARCH.md).")
