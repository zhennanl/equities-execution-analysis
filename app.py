"""
Execution Analytics Platform
Page 1: Execution Algorithm Simulator  — full 5-agent pipeline
Page 2: Index Rebalancing Analysis     — event study (CAR + abnormal volume)
"""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import sys, os, datetime, time

sys.path.insert(0, os.path.dirname(__file__))
from agents.agent1_market_data      import fetch_market_data, MarketData, MARKET_INFO
from agents.agent3_algo_simulation  import IS_KAPPA_T, simulate_with_interventions
from agents.agent10_hypothesis_test import run_hypothesis_test, METRIC_MAP, ALTERNATIVES
from agents.agent11_live_snapshot   import (
    live_regime, live_microstructure, live_pretrade_remaining,
    live_recommendation_check, live_tca, build_live_alerts,
)
from agents.orchestrator            import run_pipeline
from agents.rebalancing_event_study import run_event_study, build_execution_insights, INDEX_PROXIES
from agents.agent12_index_calendar  import (
    PROVIDERS as A12_PROVIDERS, fetch_all as a12_fetch_all,
    load_cache as a12_load_cache, save_cache as a12_save_cache,
    upcoming_reviews as a12_upcoming_reviews, suggest_yahoo_ticker,
)
from agents.order_ticket import OrderTicket, check_order
from agents.agent14_rebalance_strategist import analyze_strategies
from agents.agent13_venue_router import (
    route_order, compare_policies, bar_volumes_for, venues_for,
    MARKET_VENUES, ROUTING_POLICIES, DEFAULT_HALF_SPREAD_BPS,
)

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

st.sidebar.markdown("---")
with st.sidebar.expander("ℹ️ Data Sources & Limitations"):
    st.markdown(
        "**Provider:** [Yahoo Finance](https://finance.yahoo.com) via the free "
        "`yfinance` Python library — no API key, no paid feed."
    )
    st.markdown("**What this app fetches:**")
    st.markdown(
        "- 5-min intraday OHLCV bars, trailing **5 days** (Execution Simulator)\n"
        "- Daily OHLCV bars, trailing **60 days** (ADV, volatility, spread estimate)\n"
        "- Best-effort shares outstanding (used for one turnover-liquidity factor; "
        "silently omitted if unavailable)\n"
        "- Earnings-date calendar (past/upcoming print dates)\n"
        "- Daily OHLCV over a custom date range + 5-min intraday, capped at yfinance's "
        "~60-day retention (Index Rebalancing event study)"
    )
    st.markdown("**What it does *not* include:**")
    st.markdown(
        "- No order book, bid/ask quotes, or market depth\n"
        "- No individual trade prints — only bar-aggregated OHLCV\n"
        "- No venue/dark-pool breakdown\n"
        "- No index-constituent-change feed — rebalancing ticker & date are user-supplied, "
        "not auto-detected"
    )
    st.caption(
        "Every metric built on top of this feed (spread, VPIN, Kyle's lambda) is a "
        "disclosed *approximation* reconstructed from OHLCV bars — see each metric's "
        "own caption for its specific caveat. Free-tier requests are also subject to "
        "occasional rate-limiting."
    )

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
    c1,c2,c3,c4,c5 = st.columns(5)
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
            "UK (LSE)":         "AZN",
        }
        sfx = MARKET_INFO[market]["suffix"]
        ticker_input = st.text_input(f"Ticker (excl. '{sfx}')", value=ex.get(market, ""))
    with c3: order_pct_adv = st.slider("Order Size (% ADV)", 1, 25, 5)
    with c4: urgency = st.radio("Urgency", ["Low","Medium","High"], horizontal=True)
    with c5:
        benchmark_target = st.selectbox(
            "Benchmark Target", ["Arrival", "VWAP", "Close", "Open"],
            help="The TCA benchmark this order is measured against — mirrors the client-stated "
                 "objective a GSET-style algo wheel takes as an input. 'Arrival' is neutral (every "
                 "algo's cost is already arrival-relative); VWAP/Close/Open each steer the "
                 "recommendation toward the algo built to track that specific benchmark, unless a "
                 "higher-priority urgency/volatility rule overrides it."
        )

    # ── Institutional Order Ticket — constraints that BIND the simulation ──
    with st.expander("🎫 Order Ticket — institutional constraints (optional)"):
        tk_tab, vn_tab, fix_tab = st.tabs(["Constraints", "🛣 Venues & routing", "📨 FIX 4.4 view"])
        with tk_tab:
            st.caption(
                "The parameters a buy-side EMS actually attaches to an algo order. "
                "Defaults reproduce an unconstrained order. Active constraints bind "
                "the simulated fills — no fills through a limit, per-bar participation "
                "throttling with carry-forward — and residual unfilled shares are "
                "priced as Perold opportunity cost. Constraints currently apply to the "
                "static pipeline; live-session enforcement is the next build."
            )
            o1, o2, o3 = st.columns(3)
            with o1:
                tk_type = st.selectbox("Order type", ["Market", "Limit"], key="tk_type")
                tk_limit = st.number_input(
                    "Limit price", min_value=0.0, value=0.0, step=0.01, format="%.2f",
                    disabled=(tk_type != "Limit"), key="tk_limit",
                    help="Buy limit: no fills in bars priced above this level; blocked "
                         "shares roll forward to later eligible bars.")
            with o2:
                _mi = MARKET_INFO[market]
                _open_t  = datetime.datetime.strptime(_mi["open"],  "%H:%M").time()
                _close_t = datetime.datetime.strptime(_mi["close"], "%H:%M").time()
                # Reset window defaults when the market (and thus its session
                # hours) changes — otherwise the previous market's open/close
                # linger in the widgets and read as a custom window.
                if st.session_state.get("tk_market") != market:
                    st.session_state.pop("tk_start", None)
                    st.session_state.pop("tk_end", None)
                    st.session_state["tk_market"] = market
                tk_start = st.time_input("Execution window start", value=_open_t, key="tk_start",
                                         help="FIX Tag 168 EffectiveTime")
                tk_end   = st.time_input("Execution window end", value=_close_t, key="tk_end",
                                         help="FIX Tag 126 ExpireTime")
            with o3:
                tk_cap_on = st.checkbox("Apply max participation cap", key="tk_cap_on",
                                        help="FIX Tag 849 ParticipationRate — hard ceiling on the "
                                             "share of each bar's volume this order may consume.")
                tk_cap = st.slider("Cap (% of bar volume)", 1, 50, 15,
                                   disabled=not tk_cap_on, key="tk_cap")
                tk_auction = st.checkbox("Allow auction participation (MOC/MOO)", value=True,
                                         key="tk_auction")
                tk_must = st.checkbox("Must-complete order", key="tk_must",
                                      help="Unfilled residual is a client-constraint violation, "
                                           "not just an opportunity cost.")

        with vn_tab:
            _venue_names = [v.name for v in MARKET_VENUES.get(market, [])]
            if len(_venue_names) <= 1:
                st.info(f"**{market} is a single-venue market** — all flow executes on the "
                        "primary exchange; there is no routing choice to make. (This is the "
                        "institutional reality in this market, not a simulator limitation.)")
            st.caption("Routing preferences feed Agent 13's smart-order-routing simulation — a "
                       "statistical venue-allocation model (see Strategy & Venue Selection in the "
                       "results). They allocate fills across venues; they don't change the algo's "
                       "fill schedule.")
            v1c, v2c = st.columns(2)
            with v1c:
                tk_sor = st.selectbox("SOR policy", list(ROUTING_POLICIES), key="tk_sor")
                tk_dark = st.checkbox("Allow dark/midpoint venues", value=True, key="tk_dark",
                                      disabled=len(_venue_names) <= 1)
            with v2c:
                tk_excl_venues = st.multiselect(
                    "Exclude venues", [v for v in _venue_names][1:], key="tk_excl_venues",
                    help="Venue exclusion lists are a standard client instruction (e.g. 'no "
                         "inverted venues', 'no broker dark pools').")

    ticket = OrderTicket(
        order_type=st.session_state.get("tk_type", "Market"),
        limit_price=(float(st.session_state.get("tk_limit", 0.0))
                     if st.session_state.get("tk_type") == "Limit"
                     and st.session_state.get("tk_limit", 0.0) > 0 else None),
        start_time=(st.session_state.get("tk_start")
                    if st.session_state.get("tk_start") not in (None, _open_t) else None)
                   if "tk_start" in st.session_state else None,
        end_time=(st.session_state.get("tk_end")
                  if st.session_state.get("tk_end") not in (None, _close_t) else None)
                 if "tk_end" in st.session_state else None,
        max_participation_pct=(float(st.session_state.get("tk_cap", 15))
                               if st.session_state.get("tk_cap_on") else None),
        must_complete=bool(st.session_state.get("tk_must", False)),
        allow_auction=bool(st.session_state.get("tk_auction", True)),
        sor_policy=st.session_state.get("tk_sor", "Cost-optimized"),
        allow_dark=bool(st.session_state.get("tk_dark", True)),
        excluded_venues=list(st.session_state.get("tk_excl_venues", [])),
    )
    _active_constraints = ticket.constraint_summary()
    if _active_constraints:
        st.markdown("🎫 **Active order-ticket constraints:** " + " · ".join(_active_constraints))

    with fix_tab:
        st.caption("The ticket as (a subset of) the FIX 4.4 tags an EMS would put on the "
                   "wire to a broker algo — order quantity resolves against ADV at route time.")
        _fix_rows = ticket.to_fix_fields(ticker_input or "—", 0)
        for _r in _fix_rows:
            if _r["Tag"] == 38:
                _r["Value"] = f"{order_pct_adv}% of ADV (resolved at route time)"
        st.dataframe(pd.DataFrame(_fix_rows), use_container_width=True, hide_index=True)

    run = st.button("▶ Run Agent Pipeline", type="primary", use_container_width=True)
    st.markdown("---")

    if run:
        # -- Pre-trade compliance (OMS-style checks BEFORE anything routes) --
        _findings = check_order(ticket, ticker_input, order_pct_adv)
        for _f in [f for f in _findings if f.severity == "WARN"]:
            st.warning(f"⚠️ **{_f.rule}:** {_f.message}")
        _blocks = [f for f in _findings if f.severity == "BLOCK"]
        if _blocks:
            for _f in _blocks:
                st.error(f"⛔ **{_f.rule}:** {_f.message}")
            if not st.session_state.get("tk_override"):
                st.checkbox("Supervisor override — acknowledge findings and proceed (logged)",
                            key="tk_override")
                st.caption("Check the override box, then click **Run Agent Pipeline** again — "
                           "mirroring a real OMS override workflow, the block stands until a "
                           "supervisor acknowledgement is on record.")
                st.stop()
            st.info("Supervisor override acknowledged — proceeding despite blocking findings.")

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

        for _f in check_order(ticket, ticker_input, order_pct_adv,
                              last_price=data.current_price):
            if _f.rule == "Limit-price sanity":
                st.warning(f"⚠️ **{_f.rule}:** {_f.message}")

        # -- Orchestrator: runs Agents 2-8, conditionally skipping/degrading
        # at runtime rather than a fixed unconditional sequence; see
        # agents/orchestrator.py and agents/context.py ----------------------
        with st.spinner("Running agent pipeline…"):
            ctx = run_pipeline(data, order_pct_adv, urgency, benchmark_target=benchmark_target, ticket=ticket)

        # Persist to session_state so results (and the Mid-Session Adjustment
        # widgets below) survive later reruns triggered by *other* widgets --
        # Streamlit reruns the whole script on every interaction, and `run`
        # (st.button's return value) is only True on the exact rerun where
        # this button was clicked, so without this the whole page would blank
        # out the moment the user touches the mid-session checkpoint slider.
        st.session_state["p1_ctx"] = ctx
        st.session_state["p1_data"] = data
        st.session_state["p1_order_pct_adv"] = order_pct_adv
        st.session_state["p1_urgency"] = urgency
        st.session_state["p1_benchmark_target"] = benchmark_target
        # A fresh pipeline run means any previously-queued interventions or
        # hypothesis-test result were computed against the OLD ticker/order/
        # urgency's schedule -- drop them and reseed the Live Execution
        # Monitor's base algo/urgency from THIS run's own recommendation, so
        # the sections below always start clean for the run just completed.
        st.session_state["p1_interventions"] = []
        st.session_state["p1_base_algo"] = ctx.memo.primary_algo if ctx.memo is not None else None
        st.session_state["p1_base_urgency"] = urgency
        st.session_state["p1_base_benchmark"] = benchmark_target
        st.session_state.pop("p1_ht_result", None)
        # Playback transport state -- fresh run always restarts the simulation
        # from the first bar, paused, at Normal speed.
        st.session_state["lm_cursor_idx"] = 0
        st.session_state["p1_playing"] = False
        st.session_state["p1_speed"] = "Normal"

    if "p1_ctx" in st.session_state:
        ctx = st.session_state["p1_ctx"]
        data = st.session_state["p1_data"]
        order_pct_adv = st.session_state["p1_order_pct_adv"]
        urgency = st.session_state["p1_urgency"]
        benchmark_target = st.session_state["p1_benchmark_target"]

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

        a_names = list(sim.algos.keys())

        # ── LIVE TRADING SESSION (interactive simulation) ─────────────────────
        st.markdown("### 🔴 Live Trading Session — Interactive Simulation")
        if getattr(sim, "constraint_notes", None):
            st.caption("🎫 Note: order-ticket constraints currently bind the static pipeline "
                       "(above/below) only — live-session enforcement is the next build.")
        st.caption(
            "Press **Play** and watch the session unfold bar-by-bar, exactly as a trader would "
            "experience it on a broker execution-management-system (EMS) blotter — every panel "
            "below (Market Regime, Microstructure, Pre-Trade re-underwrite, the recommendation "
            "check, and TCA) recomputes using ONLY the bars observed so far, not the full "
            "(already-known) day the sections above use. Change the algo, urgency, or benchmark "
            "target below to alter the execution strategy — at the start of the day, or mid-session "
            "via an intervention — and pause at any point to review the effect before resuming. "
            "Backtest-style — the same historical bars are replayed on a timer, not a live feed."
        )

        if "lm_cursor_idx" not in st.session_state:
            st.session_state["lm_cursor_idx"] = 0
        if "p1_playing" not in st.session_state:
            st.session_state["p1_playing"] = False
        if "p1_speed" not in st.session_state:
            st.session_state["p1_speed"] = "Normal"

        live = simulate_with_interventions(
            data, order_shares, st.session_state["p1_base_algo"], st.session_state["p1_base_urgency"],
            st.session_state["p1_interventions"],
        )
        full_schedule = live["schedule"]
        scrub_options = list(full_schedule["time"])[1:]   # exclude the very first bar -- nothing filled yet
        n_opts = len(scrub_options)

        if n_opts >= 1:
            st.session_state["lm_cursor_idx"] = min(st.session_state["lm_cursor_idx"], n_opts - 1)

            # -- Autoplay advance happens HERE, before the slider widget below
            # is instantiated this run -- Streamlit forbids writing to
            # st.session_state[key] AFTER a widget with that key has already
            # been created in the same script pass. Sleeping first paces the
            # simulation; the slider (and everything below it) then renders
            # using the just-advanced position.
            if st.session_state["p1_playing"]:
                if st.session_state["lm_cursor_idx"] >= n_opts - 1:
                    st.session_state["p1_playing"] = False
                else:
                    delay = {"Slow": 1.2, "Normal": 0.6, "Fast": 0.2}[st.session_state["p1_speed"]]
                    time.sleep(delay)
                    st.session_state["lm_cursor_idx"] += 1

            if "p1_base_benchmark" not in st.session_state:
                st.session_state["p1_base_benchmark"] = benchmark_target

            lm1, lm2, lm3 = st.columns(3)
            with lm1:
                base_algo_choice = st.selectbox(
                    "Algo you started the day on", a_names,
                    index=a_names.index(st.session_state["p1_base_algo"])
                    if st.session_state["p1_base_algo"] in a_names else 0,
                    key="lm_base_algo")
            with lm2:
                base_urgency_choice = st.selectbox(
                    "Starting urgency", ["Low", "Medium", "High"],
                    index=["Low", "Medium", "High"].index(st.session_state["p1_base_urgency"]),
                    key="lm_base_urgency")
            with lm3:
                base_benchmark_choice = st.selectbox(
                    "Starting benchmark target", ["Arrival", "VWAP", "Close", "Open"],
                    index=["Arrival", "VWAP", "Close", "Open"].index(st.session_state["p1_base_benchmark"])
                    if st.session_state["p1_base_benchmark"] in ["Arrival", "VWAP", "Close", "Open"] else 0,
                    key="lm_base_benchmark",
                    help="What this order is measured against -- steers Agent 5's rule when it "
                         "re-fires against the live regime below.")

            # Changing the starting point invalidates any interventions already
            # queued against the OLD starting point -- clear rather than mix plans.
            if (base_algo_choice != st.session_state["p1_base_algo"]
                    or base_urgency_choice != st.session_state["p1_base_urgency"]
                    or base_benchmark_choice != st.session_state["p1_base_benchmark"]):
                st.session_state["p1_base_algo"] = base_algo_choice
                st.session_state["p1_base_urgency"] = base_urgency_choice
                st.session_state["p1_base_benchmark"] = base_benchmark_choice
                st.session_state["p1_interventions"] = []
                st.session_state["lm_cursor_idx"] = 0
                st.session_state["p1_playing"] = False
                st.rerun()

            # -- Transport controls ------------------------------------------
            t1, t2, t3, t4 = st.columns([1.1, 1.1, 1.1, 2])
            with t1:
                at_end = st.session_state["lm_cursor_idx"] >= n_opts - 1
                play_label = "⏸ Pause" if st.session_state["p1_playing"] else ("↻ Replay" if at_end else "▶ Play")
                if st.button(play_label, key="lm_play_pause", use_container_width=True):
                    if st.session_state["p1_playing"]:
                        st.session_state["p1_playing"] = False
                    else:
                        if at_end:
                            st.session_state["lm_cursor_idx"] = 0
                        st.session_state["p1_playing"] = True
                    st.rerun()
            with t2:
                if st.button("⏮ Reset", key="lm_reset_cursor", use_container_width=True):
                    st.session_state["lm_cursor_idx"] = 0
                    st.session_state["p1_playing"] = False
                    st.rerun()
            with t3:
                if st.button("⏭ Step", key="lm_step", use_container_width=True,
                            disabled=st.session_state["p1_playing"]):
                    st.session_state["lm_cursor_idx"] = min(st.session_state["lm_cursor_idx"] + 1, n_opts - 1)
                    st.rerun()
            with t4:
                speed = st.select_slider("Speed", options=["Slow", "Normal", "Fast"],
                                         value=st.session_state["p1_speed"], key="lm_speed_slider")
                st.session_state["p1_speed"] = speed

            cursor_idx = st.slider("Playback position (bar index)", 0, n_opts - 1, key="lm_cursor_idx")
            scrub_time = scrub_options[cursor_idx]
            is_final = cursor_idx == n_opts - 1
            st.caption(f"Viewing execution as of **{pd.Timestamp(scrub_time).strftime('%H:%M')}** "
                      f"— bar {cursor_idx + 1}/{n_opts}" + (" — session complete" if is_final else ""))

            view = full_schedule[full_schedule["time"] <= pd.Timestamp(scrub_time)]
            day_full = live["day"]
            view_day = day_full[day_full.index <= pd.Timestamp(scrub_time)]
            today_date = day_full.index[0].normalize()
            last = view.iloc[-1]
            pct_complete = (last["cumulative"] / order_shares) if order_shares > 0 else 0.0
            remaining_shares = max(0.0, order_shares - last["cumulative"])

            # Current effective urgency/benchmark AT this playback position --
            # the most recent intervention at or before scrub_time overrides
            # the starting value, so tweaking the inputs mid-session actually
            # feeds through to the live regime/recommendation re-checks below,
            # not just the schedule.
            def _effective_at(field, base_value):
                applied = [iv for iv in st.session_state["p1_interventions"]
                          if pd.Timestamp(iv["checkpoint_time"]) <= pd.Timestamp(scrub_time)]
                return applied[-1].get(field, base_value) if applied else base_value

            current_urgency = _effective_at("urgency", st.session_state["p1_base_urgency"])
            current_benchmark = _effective_at("benchmark", st.session_state["p1_base_benchmark"])

            sv1, sv2, sv3, sv4 = st.columns(4)
            sv1.metric("Filled so far", f"{last['cumulative']:,.0f} sh",
                      delta=f"{pct_complete:.0%} of order", delta_color="off")
            sv2.metric("Avg exec price so far", f"${last['cum_avg_price']:.2f}")
            sv3.metric("Slippage vs Arrival", f"{last['running_slip_vs_arrival_bps']:+.1f} bps",
                      delta="worse" if last["running_slip_vs_arrival_bps"] > 0 else "better",
                      delta_color="inverse")
            sv4.metric("Slippage vs VWAP-to-date", f"{last['running_slip_vs_vwap_bps']:+.1f} bps",
                      delta="worse" if last["running_slip_vs_vwap_bps"] > 0 else "better",
                      delta_color="inverse")

            fev = go.Figure()
            fev.add_trace(go.Scatter(x=view["time"], y=view["running_slip_vs_arrival_bps"],
                                     name="vs Arrival", mode="lines", line=dict(color="#1f77b4", width=2)))
            fev.add_trace(go.Scatter(x=view["time"], y=view["running_slip_vs_vwap_bps"],
                                     name="vs VWAP-to-date", mode="lines", line=dict(color="#f97316", width=2)))
            fev.add_shape(type="line", x0=view["time"].iloc[0], x1=view["time"].iloc[-1],
                         y0=0, y1=0, line=dict(color="gray", dash="dot", width=1))
            for iv in st.session_state["p1_interventions"]:
                ck = pd.Timestamp(iv["checkpoint_time"])
                if ck <= pd.Timestamp(scrub_time):
                    fev.add_shape(type="line", x0=ck, x1=ck, y0=0, y1=1, yref="paper",
                                 line=dict(color="#ef4444", dash="dash", width=1))
            fev.update_layout(height=280, margin=dict(l=40, r=20, t=10, b=30),
                             plot_bgcolor="white",
                             yaxis=dict(gridcolor="#eee", title="Running slippage (bps)"),
                             legend=dict(orientation="h", yanchor="bottom", y=1.02))
            st.plotly_chart(fev, use_container_width=True)
            st.caption(
                "Positive = paid more than that benchmark so far (buy order). Red dashed lines "
                "mark interventions already applied."
            )

            # -- Live Agent Readouts ------------------------------------------
            st.markdown("")
            st.markdown("**Live Agent Readouts — synced to the playback position above**")
            l_regime = live_regime(data.intraday, data.daily, today_date, view_day)
            l_micro = live_microstructure(
                data.intraday, today_date, view_day, data.adv_shares, remaining_shares,
                current_urgency, data.realized_vol_ann,
                getattr(data, "shares_outstanding", None))
            l_pretrade = live_pretrade_remaining(
                remaining_shares, data.adv_shares, current_urgency,
                data.realized_vol_ann, getattr(data, "shares_outstanding", None))
            l_rec = live_recommendation_check(
                l_regime, regime, comp, current_urgency, current_benchmark,
                memo.primary_algo, memo.secondary_algo)

            lg1, lg2 = st.columns(2)
            with lg1:
                st.markdown("*Market Regime (live)*")
                st.markdown(
                    _badge(l_regime.vol_label, _VC.get(l_regime.vol_label, "#6b7280")) + "&nbsp;" +
                    _badge(l_regime.volume_label, "#6b7280") + "&nbsp;" +
                    _badge(l_regime.trend_label, _TC.get(l_regime.trend_label, "#6b7280")),
                    unsafe_allow_html=True)
                st.caption(f"At decision time: {regime.vol_label} · {regime.volume_label} · {regime.trend_label}")
            with lg2:
                st.markdown("*Microstructure (live)*")
                if l_micro.vpin.available:
                    st.caption(f"VPIN: **{l_micro.vpin.label}** ({l_micro.vpin.vpin_score:.2f}) — {l_micro.vpin.note}")
                else:
                    st.caption(f"VPIN: {l_micro.vpin.reason}")
                if l_micro.kyle_lambda.available:
                    st.caption(f"Kyle's λ: {l_micro.kyle_lambda.lambda_bps_per_pct_adv:+.2f} bps/1%ADV "
                              f"(t={l_micro.kyle_lambda.t_stat:.1f}, n={l_micro.kyle_lambda.n_obs})")
                else:
                    st.caption(f"Kyle's λ: {l_micro.kyle_lambda.reason}")

            if l_rec.still_on_track:
                st.success(f"✅ **Still on track** — Agent 5's rule, re-run against the live regime "
                          f"at **{current_urgency}** urgency / **{current_benchmark}** benchmark, "
                          f"still picks **{l_rec.live_primary}**, matching the original recommendation.")
            else:
                st.warning(f"⚠️ **Reconsider** — Agent 5's rule, re-run against the live regime "
                          f"at **{current_urgency}** urgency / **{current_benchmark}** benchmark, now "
                          f"picks **{l_rec.live_primary}** instead of the original **{memo.primary_algo}**.")
            for c in l_rec.changes:
                st.caption(f"• {c}")
            if current_urgency != st.session_state["p1_base_urgency"] or current_benchmark != st.session_state["p1_base_benchmark"]:
                st.caption(f"Currently in effect (via intervention): {current_urgency} urgency, "
                          f"{current_benchmark} benchmark — started the day on "
                          f"{st.session_state['p1_base_urgency']} / {st.session_state['p1_base_benchmark']}.")

            st.markdown("*Pre-Trade Re-Underwrite — remaining order*")
            lp1, lp2 = st.columns(2)
            lp1.metric("Shares remaining", f"{remaining_shares:,.0f}")
            if l_pretrade.almgren.available:
                lp2.metric("Est. impact on remainder (Almgren 2005)",
                          f"{l_pretrade.almgren.realized_impact_bps:.1f} bps")
            else:
                lp2.metric("Est. impact on remainder", "N/A")
            with st.expander("Capacity table for the remaining order"):
                st.dataframe(l_pretrade.capacity, use_container_width=True)
            st.caption(l_pretrade.note)

            st.markdown(f"**Live TCA{' — Session Complete' if is_final else ' (to date)'}**")
            tca_hist = comp if is_final else None
            tca_algo_hist = st.session_state["p1_base_algo"] if is_final else None
            tca = live_tca(
                view, view_day, live["legs"], st.session_state["p1_base_algo"],
                st.session_state["p1_base_urgency"], live["arrival_price"], order_shares,
                data.adv_shares, data.realized_vol_ann, is_final,
                comparison=tca_hist, algo_name_for_history=tca_algo_hist)
            st.dataframe(tca.benchmarks_to_date.style.format({
                "Benchmark Price": "${:.4f}", "Slippage vs Benchmark (bps)": "{:+.2f}",
            }), use_container_width=True)
            ltc1, ltc2 = st.columns(2)
            ltc1.metric("Mark-to-market cost of unfilled remainder",
                       f"{tca.mark_to_market_unfilled_bps:+.1f} bps",
                       help="Unfilled shares marked at the current price vs. arrival — what you're "
                            "on the hook for if trading stopped right now (Perold 1988 style).")
            if is_final and tca.reversion is not None:
                ltc2.metric("Impact reversion",
                          f"{tca.reversion.reversion_bps:+.1f} bps" if tca.reversion.available else "N/A")
                if tca.decomposition is not None and tca.decomposition.available:
                    st.caption(tca.decomposition.note)
                if tca.cost_percentile is not None and tca.cost_percentile.available:
                    st.caption(f"Cost percentile vs. history: {tca.cost_percentile.percentile:.0f}th "
                              f"({tca.cost_percentile.n_obs} historical days).")
            st.caption(tca.note)

            # -- Alert blotter (EMS-style threshold rules over the live metrics) --
            _al_part = None
            if len(view) and len(view_day) and float(view_day["Volume"].iloc[-1]) > 0:
                _al_part = float(view["shares_traded"].iloc[-1]) / float(view_day["Volume"].iloc[-1]) * 100
            _al_slip = None
            try:
                _bt = tca.benchmarks_to_date
                _match = [ix for ix in _bt.index if current_benchmark.lower() in str(ix).lower()]
                if _match:
                    _al_slip = float(_bt.loc[_match[0], "Slippage vs Benchmark (bps)"])
            except Exception:
                pass
            _alerts = build_live_alerts(
                filled_shares=order_shares - remaining_shares, order_shares=order_shares,
                elapsed_frac=(cursor_idx + 1) / max(n_opts, 1),
                algo_name=st.session_state["p1_base_algo"] or "",
                last_bar_participation_pct=_al_part,
                cap_pct=ticket.max_participation_pct,
                limit_price=ticket.effective_limit,
                current_price=float(view_day["Close"].iloc[-1]) if len(view_day) else None,
                vpin_label=l_micro.vpin.label if l_micro.vpin.available else None,
                slip_vs_benchmark_bps=_al_slip, benchmark_name=current_benchmark,
                reconsider=not l_rec.still_on_track)
            st.markdown("**🚨 Alert Blotter**")
            if _alerts:
                for _al in _alerts:
                    if _al.severity == "HIGH":
                        st.error(f"🔴 **{_al.rule}:** {_al.message}")
                    elif _al.severity == "MEDIUM":
                        st.warning(f"🟠 **{_al.rule}:** {_al.message}")
                    else:
                        st.caption(f"🔵 {_al.rule}: {_al.message}")
            else:
                st.caption("🟢 No active alerts — execution within all thresholds.")
            st.caption("Threshold rules over the live metrics (completion pace, participation "
                       "cap, limit state, toxicity, benchmark slippage). Alerts inform — "
                       "nothing auto-acts, same posture as the critic.")

            # -- Intervene ------------------------------------------------------
            with st.expander("🔀 Intervene here — switch algo/urgency/benchmark for the remainder"):
                iv1, iv2, iv3, iv4 = st.columns(4)
                with iv1:
                    iv_algo = st.selectbox(
                        "New algo", a_names,
                        index=a_names.index(memo.primary_algo) if memo.primary_algo in a_names else 0,
                        key="lm_iv_algo")
                with iv2:
                    iv_urg = st.selectbox(
                        "New urgency", ["Low", "Medium", "High"],
                        index=["Low", "Medium", "High"].index(current_urgency), key="lm_iv_urgency")
                with iv3:
                    iv_bench = st.selectbox(
                        "New benchmark target", ["Arrival", "VWAP", "Close", "Open"],
                        index=["Arrival", "VWAP", "Close", "Open"].index(current_benchmark)
                        if current_benchmark in ["Arrival", "VWAP", "Close", "Open"] else 0,
                        key="lm_iv_benchmark")
                with iv4:
                    st.markdown("")
                    st.markdown("")
                    add_iv = st.button("➕ Add intervention here", key="lm_add_iv",
                                       use_container_width=True)
                if add_iv:
                    existing = [pd.Timestamp(iv["checkpoint_time"]) for iv in st.session_state["p1_interventions"]]
                    if pd.Timestamp(scrub_time) in existing:
                        st.warning("⚠️ An intervention already exists at this exact bar — "
                                  "move to a different bar first.")
                    else:
                        st.session_state["p1_interventions"].append(
                            {"checkpoint_time": scrub_time, "algo": iv_algo, "urgency": iv_urg,
                             "benchmark": iv_bench})
                        st.session_state["p1_playing"] = False
                        st.rerun()

            if st.session_state["p1_interventions"]:
                st.markdown("**Interventions applied (in order):**")
                for i, iv in enumerate(st.session_state["p1_interventions"]):
                    st.caption(f"{i + 1}. @ {pd.Timestamp(iv['checkpoint_time']).strftime('%H:%M')} "
                              f"→ switch to **{iv['algo']}** ({iv['urgency']}, "
                              f"{iv.get('benchmark', st.session_state['p1_base_benchmark'])} benchmark)")
                ub1, ub2 = st.columns(2)
                with ub1:
                    if st.button("↩️ Undo last intervention", key="lm_undo", use_container_width=True):
                        st.session_state["p1_interventions"].pop()
                        st.session_state["p1_playing"] = False
                        st.rerun()
                with ub2:
                    if st.button("🔄 Reset to no interventions", key="lm_reset", use_container_width=True):
                        st.session_state["p1_interventions"] = []
                        st.session_state["p1_playing"] = False
                        st.rerun()

            st.markdown("")
            st.markdown(f"**Final outcome if this plan holds for the rest of the day** "
                       f"({len(st.session_state['p1_interventions'])} intervention(s) applied):")
            blended = live["blended"]
            fo1, fo2, fo3, fo4 = st.columns(4)
            fo1.metric("Fill rate", f"{blended.completion_pct:.0%}")
            fo2.metric("Avg exec price", f"${blended.avg_exec_price:.2f}")
            fo3.metric("Total cost", f"{blended.total_cost_bps:.1f} bps")
            baseline_algo = st.session_state["p1_base_algo"]
            baseline_total = (sim.algos[baseline_algo].total_cost_bps
                              if baseline_algo in sim.algos else blended.total_cost_bps)
            delta_bps = blended.total_cost_bps - baseline_total
            fo4.metric(f"vs. staying on {baseline_algo} all day", f"{delta_bps:+.1f} bps",
                      delta="worse" if delta_bps > 0 else "better", delta_color="inverse")
            st.caption(blended.schedule_note)

            # -- Autoplay: trigger the next frame ------------------------------
            # The actual sleep-then-advance happened at the top of this block
            # (before the slider widget was instantiated -- Streamlit forbids
            # mutating st.session_state[key] after that key's widget has
            # already been created in the same script pass). All that's left
            # here is to kick off the next rerun so the just-advanced position
            # actually renders.
            if st.session_state["p1_playing"]:
                st.rerun()
        else:
            st.info("ℹ️ Not enough bars in this session to demo the live trading session.")

        # ══ STAGE 1 — PRE-TRADE ANALYTICS ════════════════════════════════════
        st.markdown("---")
        st.markdown("## 🧭 Stage 1 — Pre-Trade Analytics")
        st.caption("What the desk knows **before** choosing how to trade: liquidity and data "
                   "quality (Agent 1), expected cost/capacity/spread (Agent 6 + Agent 9 "
                   "cross-check), event risk (Agent 7), microstructure toxicity (Agent 9), and "
                   "the market-regime read (Agent 2).")

        # ── AGENT 1 OUTPUT ────────────────────────────────────────────────────
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
                   "computed before committing to an algorithm, using the full historical dataset. "
                   "See **Live Trading Session** below for how this re-underwrites as the day plays out.")
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
        st.caption("Decision-time snapshot, pooled across the full fetch window — see **Live Trading "
                  "Session** below for the same readout recomputed bar-by-bar as the session plays.")
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
            st.caption("**VPIN validity note:** Andersen & Bondarenko (2014) show VPIN's predictive "
                      "content largely reflects volume/volatility mechanically and that it peaked *after* "
                      "the 2010 Flash Crash — treat it as a monitoring signal correlated with stress, not "
                      "a validated predictor (Easley-López de Prado-O'Hara's rejoinder defends the "
                      "toxicity channel; see docs/EXECUTION_SIMULATOR_RESEARCH.md).")
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
        st.caption("Decision-time snapshot (full simulation day) — see **Live Trading Session** below "
                  "for how this classification evolves as only part of the day has actually happened.")
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

        # ══ STAGE 2 — STRATEGY & VENUE SELECTION ═════════════════════════════
        st.markdown("---")
        st.markdown("## 🎯 Stage 2 — Strategy & Venue Selection")
        st.caption("The trader's decision layer: Agent 5's rule-based strategy pick (with Agent 8's "
                   "independent critic review), then venue selection and smart-order-routing "
                   "simulation (Agent 13). Override the strategy or routing policy below — the "
                   "routing view recomputes without re-running the pipeline.")
        st.markdown("---")
        # ── AGENT 5 — RECOMMENDATION ──────────────────────────────────────────
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


        # ── AGENT 13 — VENUE SELECTION & SOR SIMULATION ───────────────────────
        st.markdown("")
        st.markdown("#### 🛣 Venue Selection & Smart Order Routing (Agent 13)")
        st.caption("**Statistical simulation** — a stylized venue set per market (fees, addressable "
                   "volume, fill probability, spread capture, adverse selection) with slices "
                   "allocated by marginal expected cost: the objective of a real SOR without the "
                   "microsecond mechanics. Queue position, latency, and true dark-liquidity "
                   "discovery are NOT modeled (see INSTITUTIONAL_GAP_REGISTER.md).")

        _hs_used = (pretrade.half_spread_bps
                    if pretrade is not None and pretrade.half_spread_bps
                    else DEFAULT_HALF_SPREAD_BPS)
        vr1, vr2, vr3 = st.columns(3)
        with vr1:
            rt_algo = st.selectbox("Strategy to route", list(sim.algos.keys()),
                                   index=list(sim.algos.keys()).index(memo.primary_algo)
                                         if memo.primary_algo in sim.algos else 0,
                                   key="rt_algo",
                                   help="Defaults to Agent 5's pick — override to see how routing "
                                        "changes with the schedule shape.")
        with vr2:
            rt_policy = st.selectbox("Routing policy", list(ROUTING_POLICIES),
                                     index=list(ROUTING_POLICIES).index(
                                         st.session_state.get("tk_sor", "Cost-optimized")),
                                     key="rt_policy")
        with vr3:
            rt_dark = st.checkbox("Allow dark/midpoint", value=st.session_state.get("tk_dark", True),
                                  key="rt_dark")

        _rt_sched = sim.algos[rt_algo].schedule
        _rt = route_order(_rt_sched, bar_volumes_for(_rt_sched, data.intraday), data.market,
                          policy=rt_policy, half_spread_bps=_hs_used, allow_dark=rt_dark,
                          excluded=list(st.session_state.get("tk_excl_venues", [])))
        for _n in _rt.notes:
            st.info(f"ℹ️ {_n}")

        m1, m2, m3 = st.columns(3)
        m1.metric("Blended routing cost", f"{_rt.blended_cost_bps:.2f} bps",
                  help="Share-weighted expected venue cost: spread paid + fees + adverse "
                       "selection. Additive to (not part of) the algo's slippage/impact numbers.")
        m2.metric("Routed shares", f"{_rt.routed_shares:,.0f}")
        _dk = _rt.venue_summary.loc[_rt.venue_summary["Type"] == "dark", "% of order"].sum() \
              if len(_rt.venue_summary) else 0.0
        m3.metric("Dark/midpoint share", f"{_dk:.1f}%")

        st.dataframe(_rt.venue_summary, use_container_width=True, hide_index=True)

        if len(_rt.fills_by_venue.columns) > 1:
            _fv = _rt.fills_by_venue
            fig_rt = go.Figure()
            for _vn in _fv.columns:
                fig_rt.add_trace(go.Bar(x=_fv.index, y=_fv[_vn], name=_vn))
            fig_rt.update_layout(barmode="stack", height=280,
                                 margin=dict(l=10, r=10, t=30, b=10),
                                 title="Child-order allocation by venue over the session",
                                 legend=dict(orientation="h", y=-0.25))
            st.plotly_chart(fig_rt, use_container_width=True)

        with st.expander("⚖️ Why this policy? — cost under each routing policy"):
            _cp = compare_policies(_rt_sched, bar_volumes_for(_rt_sched, data.intraday),
                                   data.market, half_spread_bps=_hs_used,
                                   allow_dark=rt_dark,
                                   excluded=list(st.session_state.get("tk_excl_venues", [])))
            st.dataframe(_cp, use_container_width=True, hide_index=True)
            st.caption(f"Half-spread input: {_hs_used:.2f} bps"
                       + (" (capped at 15 bps for routing — see note above)" if _hs_used > 15 else "")
                       + ". Venue parameters are stylized constants calibrated to public "
                       "fee schedules and market-share statistics — right order of magnitude, "
                       "not a live feed.")

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
            if getattr(sim, "excluded", None):
                st.info("🎫 Excluded by order ticket: "
                        + " · ".join(f"**{k}** — {v}" for k, v in sim.excluded.items()))
            if getattr(sim, "constraint_notes", None):
                st.caption("Order-ticket constraints bound these fills: "
                           + "; ".join(sim.constraint_notes))
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
            st.dataframe(comp.sensitivity.style.map(_color_sens), use_container_width=True)

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

        # ── HYPOTHESIS TESTING ────────────────────────────────────────────────
        st.markdown("---")
        st.markdown("### 🧪 Hypothesis Testing — Is Configuration A Actually Better Than B?")
        st.caption(
            "Real algo-wheel A/B testing (GSET/REDIPlus/EMSX, or vendor wheels like BestEx "
            "Research's) randomizes many different LIVE orders across arms over weeks and "
            "regression-adjusts for order size/vol/spread — not available here, since this "
            "platform simulates hypothetical orders against historical bars rather than "
            "routing live flow. This instead runs the paired-backtest version quant desks use "
            "for a faster read: replay the SAME historical days under both configurations, so "
            "market-condition noise is held constant and only the configuration differs — then "
            "a paired t-test (plus a Wilcoxon signed-rank check and bootstrap CI, since "
            "impact-cost distributions are fat-tailed) tells you if the difference is real."
        )

        ht1, ht2 = st.columns(2)
        with ht1:
            st.markdown("**Configuration A**")
            ha1, ha2, ha3 = st.columns(3)
            with ha1:
                ht_algo_a = st.selectbox("Algo", a_names,
                                         index=a_names.index(memo.primary_algo) if memo.primary_algo in a_names else 0,
                                         key="ht_algo_a")
            with ha2:
                ht_urg_a = st.selectbox("Urgency", ["Low", "Medium", "High"],
                                        index=["Low", "Medium", "High"].index(urgency), key="ht_urg_a")
            with ha3:
                ht_size_a = st.slider("% ADV", 1, 25, order_pct_adv, key="ht_size_a")
        with ht2:
            st.markdown("**Configuration B**")
            hb1, hb2, hb3 = st.columns(3)
            with hb1:
                ht_algo_b = st.selectbox("Algo", a_names,
                                         index=a_names.index(memo.secondary_algo) if memo.secondary_algo in a_names else 1,
                                         key="ht_algo_b")
            with hb2:
                ht_urg_b = st.selectbox("Urgency", ["Low", "Medium", "High"],
                                        index=["Low", "Medium", "High"].index(urgency), key="ht_urg_b")
            with hb3:
                ht_size_b = st.slider("% ADV", 1, 25, order_pct_adv, key="ht_size_b")

        ht3, ht4, ht5, ht6 = st.columns(4)
        with ht3:
            ht_metric = st.selectbox("Metric to test", list(METRIC_MAP.keys()), key="ht_metric")
        with ht4:
            ht_alt = st.selectbox("Alternative hypothesis", list(ALTERNATIVES.keys()), key="ht_alt")
        with ht5:
            ht_alpha = st.selectbox("Significance level (α)", [0.01, 0.05, 0.10], index=1, key="ht_alpha")
        with ht6:
            st.markdown("")
            st.markdown("")
            run_ht = st.button("▶ Run Hypothesis Test", key="ht_run", use_container_width=True)

        if run_ht:
            config_a = {"algo": ht_algo_a, "urgency": ht_urg_a, "order_pct_adv": ht_size_a}
            config_b = {"algo": ht_algo_b, "urgency": ht_urg_b, "order_pct_adv": ht_size_b}
            st.session_state["p1_ht_result"] = run_hypothesis_test(
                data, comp, order_pct_adv, urgency, config_a, config_b,
                ht_metric, ht_alt, ht_alpha,
            )

        if "p1_ht_result" in st.session_state:
            ht_res = st.session_state["p1_ht_result"]
            if not ht_res.available:
                st.warning(f"⚠️ {ht_res.reason}")
            else:
                (st.success if ht_res.reject_null else st.info)(
                    ("✅ " if ht_res.reject_null else "ℹ️ ") + ht_res.verdict_text
                )
                htc1, htc2, htc3, htc4 = st.columns(4)
                htc1.metric("Mean difference (A-B)", f"{ht_res.mean_diff:+.2f}")
                htc2.metric("95% CI", f"[{ht_res.ci_low:+.2f}, {ht_res.ci_high:+.2f}]")
                htc3.metric("Cohen's d", f"{ht_res.cohens_d:+.2f}")
                htc4.metric("n (paired days)", ht_res.n_days)

                with st.expander("Distribution of daily paired differences (A − B)"):
                    fhd = go.Figure(go.Histogram(
                        x=ht_res.daily_diffs, marker_color="#8b5cf6",
                        nbinsx=min(20, max(5, ht_res.n_days))))
                    fhd.add_shape(type="line", x0=0, x1=0, y0=0, y1=1, yref="paper",
                                 line=dict(color="red", dash="dash", width=1.5))
                    fhd.update_layout(height=240, margin=dict(l=40, r=20, t=10, b=30),
                                     plot_bgcolor="white",
                                     xaxis_title=f"Daily difference ({ht_res.metric})",
                                     yaxis=dict(gridcolor="#eee"))
                    st.plotly_chart(fhd, use_container_width=True)
                    st.caption(f"Configuration A data source: {ht_res.note_a}")
                    st.caption(f"Configuration B data source: {ht_res.note_b}")

                with st.expander("Assumptions & caveats"):
                    for c in ht_res.caveats:
                        st.caption(f"• {c}")
        else:
            st.caption("Configure both sides above and click **Run Hypothesis Test** to see results.")

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
                _bench_row_map = {"Arrival": "Arrival (Open)", "VWAP": "Full-Day VWAP",
                                 "Close": "Close", "Open": "Arrival (Open)"}
                _target_row = _bench_row_map.get(benchmark_target, "Arrival (Open)")

                def _style_bench(row):
                    bg = ("background-color:#fee2e2;" if row["Slippage vs Benchmark (bps)"] > 0
                         else "background-color:#dcfce7;")
                    if row.name == _target_row:
                        bg += "border:2px solid #1f2937;font-weight:700;"
                    return [bg] * len(row)

                st.dataframe(bt.style.format({
                    "Benchmark Price": "${:.4f}", "Slippage vs Benchmark (bps)": "{:+.2f}",
                }).apply(_style_bench, axis=1), use_container_width=True)
                st.caption(f"Positive = paid more than that benchmark; negative = paid less. "
                          f"Bordered/bold row = client's stated **Benchmark Target** ({benchmark_target}). "
                          f"Arrival matches the Total Cost table above; VWAP/TWAP/Close are the "
                          f"additional standard TCA reference points.")

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
                _ann_default = int(max(min(_ann_default, -1), int(es14.rel_days[0])))
                ann14 = st.slider("Announcement day (relative to T)", int(es14.rel_days[0]), -1,
                                  _ann_default, key="p2_ann14",
                                  help="Defaults to the announcement date entered above when "
                                       "provided (e.g. from Agent 12), else T-5 "
                                       "(Greenwood-Sammon mean A→E gap).")
            with e142:
                post14 = st.slider("Post-effective horizon (trading days)", 1, _w,
                                   min(10, _w), key="p2_post14")
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
