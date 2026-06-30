"""
Execution Analytics Platform
Multi-module Streamlit app:
  1. Execution Algorithm Simulator  — Agent pipeline (Agents 1-2 live, 3-5 coming soon)
  2. Index Rebalancing Analysis     — Coming soon
"""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import sys, os

sys.path.insert(0, os.path.dirname(__file__))
from agents.agent1_market_data import fetch_market_data, MarketData, MARKET_INFO
from agents.agent2_market_regime import assess_regime, RegimeAssessment

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Execution Analytics Platform",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Cached data fetcher (5-minute TTL) ────────────────────────────────────────
@st.cache_data(ttl=300, show_spinner=False)
def _cached_fetch(ticker_base: str, market: str) -> MarketData:
    return fetch_market_data(ticker_base, market, log=None)

# ── Sidebar navigation ────────────────────────────────────────────────────────
st.sidebar.title("Execution Analytics")
st.sidebar.markdown("---")
page = st.sidebar.radio(
    "Module",
    ["📈 Execution Algorithm Simulator", "🔄 Index Rebalancing Analysis"],
)
st.sidebar.markdown("---")
st.sidebar.caption("Built with yfinance · Claude Agent SDK · Streamlit")


# ── Regime label colour helper ────────────────────────────────────────────────
_VOL_COLOURS = {
    "Tight":               "#3b82f6",   # blue
    "Normal":              "#22c55e",   # green
    "Trending":            "#f97316",   # orange
    "Extremely Trending":  "#ef4444",   # red
}
_TREND_COLOURS = {
    "Trending":        "#f97316",
    "Mean-Reverting":  "#8b5cf6",
    "Neutral":         "#6b7280",
}
_VOL_COLOURS_DEFAULT = "#6b7280"

def _badge(text: str, colour: str) -> str:
    return (
        f'<span style="background:{colour};color:white;padding:3px 10px;'
        f'border-radius:12px;font-weight:600;font-size:0.85rem;">{text}</span>'
    )


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 1 — EXECUTION ALGORITHM SIMULATOR
# ══════════════════════════════════════════════════════════════════════════════
if page == "📈 Execution Algorithm Simulator":

    st.title("📈 Execution Algorithm Simulator")
    st.markdown(
        "Enter a stock and order parameters. The agent pipeline assesses "
        "market conditions and compares VWAP, TWAP, and Implementation Shortfall algorithms."
    )

    # ── Input panel ──────────────────────────────────────────────────────────
    st.markdown("### Inputs")
    col1, col2, col3, col4 = st.columns([2, 2, 2, 2])

    with col1:
        market = st.selectbox("Market", list(MARKET_INFO.keys()), index=0)

    with col2:
        suffix = MARKET_INFO[market]["suffix"]
        example = {"Taiwan (TWSE)": "2330", "Hong Kong (HKEX)": "0005",
                   "Japan (TSE)": "7203", "Korea (KRX)": "005930", "US": "AAPL"}
        ticker_input = st.text_input(
            f"Ticker (without suffix '{suffix}')",
            value=example[market],
            placeholder=example[market],
        )

    with col3:
        order_pct_adv = st.slider(
            "Order Size (% of ADV)", min_value=1, max_value=25, value=5, step=1
        )

    with col4:
        urgency = st.radio("Execution Urgency", ["Low", "Medium", "High"], horizontal=True)

    run_btn = st.button("▶ Run Agent Pipeline", type="primary", use_container_width=True)

    st.markdown("---")

    # ── Agent pipeline ────────────────────────────────────────────────────────
    if run_btn:
        status_cols = st.columns(5)
        agent_labels = [
            "1 · Market Data",
            "2 · Regime",
            "3 · Simulation",
            "4 · Comparison",
            "5 · LLM Memo",
        ]
        status_placeholders = [c.empty() for c in status_cols]

        def set_status(idx, state):
            icons = {"waiting": "⬜", "running": "🔄", "done": "✅", "soon": "🔲"}
            status_placeholders[idx].markdown(f"**{icons[state]} Agent {agent_labels[idx]}**")

        for i in range(5):
            set_status(i, "waiting")

        # ── Agent 1: Market Data ──────────────────────────────────────────────
        set_status(0, "running")
        fetch_msg = st.empty()
        fetch_msg.info("⏳ Fetching market data from Yahoo Finance...")

        try:
            data = _cached_fetch(ticker_input, market)
            set_status(0, "done")
        except RuntimeError as e:
            set_status(0, "waiting")
            msg = str(e)
            if "rate-limiting" in msg or "rate limit" in msg.lower():
                st.warning(f"⚠️ {msg}")
            else:
                st.error(f"❌ {msg}")
            st.stop()
        except Exception as e:
            set_status(0, "waiting")
            st.error(f"❌ Unexpected error: {e}")
            st.stop()

        fetch_msg.success("✅ Market data loaded — cached for 5 minutes.")

        # ── Agent 2: Market Regime ────────────────────────────────────────────
        set_status(1, "running")
        try:
            regime = assess_regime(data)
            set_status(1, "done")
        except Exception as e:
            set_status(1, "waiting")
            st.error(f"❌ Agent 2 failed: {e}")
            st.stop()

        for i in range(2, 5):
            set_status(i, "soon")

        st.markdown("---")

        # ── Agent 1 Output: Market Data ───────────────────────────────────────
        st.markdown("### Agent 1 — Market Data")

        kpi1, kpi2, kpi3, kpi4 = st.columns(4)
        kpi1.metric("Ticker", data.ticker)
        kpi2.metric("Current Price", f"${data.current_price:,.2f}")
        kpi3.metric("ADV (shares)", f"{data.adv_shares:,.0f}")
        kpi4.metric("Realised Vol (ann.)", f"{data.realized_vol_ann:.1%}")

        order_shares = data.adv_shares * (order_pct_adv / 100)
        kpi5, kpi6, kpi7, kpi8 = st.columns(4)
        kpi5.metric("Order Size (shares)", f"{order_shares:,.0f}")
        kpi6.metric("Order Size (% ADV)", f"{order_pct_adv}%")
        kpi7.metric("Order Notional", f"${order_shares * data.current_price / 1e6:.2f}M")
        kpi8.metric("Urgency", urgency)

        st.markdown("#### Intraday Volume Profile")
        vp = data.vol_profile
        fig_vol = go.Figure()
        fig_vol.add_trace(go.Bar(
            x=vp["time"],
            y=vp["volume_pct"] * 100,
            marker_color="#1f77b4",
            name="Avg Volume %",
        ))
        fig_vol.update_layout(
            xaxis_title="Time of Day",
            yaxis_title="Share of Daily Volume (%)",
            height=300,
            margin=dict(l=40, r=20, t=20, b=60),
            plot_bgcolor="white",
            yaxis=dict(gridcolor="#eeeeee"),
            showlegend=False,
        )
        n = len(vp)
        tickvals = vp["time"].iloc[::max(1, n // 12)].tolist()
        fig_vol.update_xaxes(tickvals=tickvals, tickangle=-45)
        st.plotly_chart(fig_vol, use_container_width=True)

        st.markdown("#### Recent Intraday Price (Last Day)")
        last_day = data.intraday[data.intraday.index.date == data.intraday.index.date[-1]]
        fig_price = go.Figure()
        fig_price.add_trace(go.Scatter(
            x=last_day.index,
            y=last_day["Close"],
            mode="lines",
            line=dict(color="#2ca02c", width=1.8),
        ))
        fig_price.update_layout(
            xaxis_title="Time",
            yaxis_title="Price",
            height=240,
            margin=dict(l=40, r=20, t=20, b=40),
            plot_bgcolor="white",
            yaxis=dict(gridcolor="#eeeeee"),
            showlegend=False,
        )
        st.plotly_chart(fig_price, use_container_width=True)

        # ── Agent 2 Output: Market Regime ─────────────────────────────────────
        st.markdown("---")
        st.markdown("### Agent 2 — Market Regime")
        st.markdown(f"**Regime:** {regime.summary}")
        st.markdown("")

        r1, r2, r3 = st.columns(3)

        # --- Volatility ---
        vol_colour = _VOL_COLOURS.get(regime.vol_label, _VOL_COLOURS_DEFAULT)
        pct_vs = (regime.vol_ratio - 1) * 100
        with r1:
            st.markdown("**Intraday Range**")
            st.markdown(_badge(regime.vol_label, vol_colour), unsafe_allow_html=True)
            st.markdown("")
            st.metric("Range vs 20d median", f"{regime.vol_ratio:.2f}×",
                      delta=f"{pct_vs:+.0f}%",
                      delta_color="inverse" if regime.vol_label == "Tight" else "normal")
            if regime.vol_label == "Tight":
                st.caption("Compressed range — low intraday movement. Execution impact likely muted.")
            elif regime.vol_label == "Normal":
                st.caption("Range in line with recent history. Standard execution conditions.")
            elif regime.vol_label == "Trending":
                st.caption("Wide range — elevated intraday volatility. Expect higher price impact.")
            else:
                st.caption("Extreme range — exceptional volatility. Consider splitting or deferring.")

        # --- Volume pattern ---
        vol_pattern_colour = {"U-Shaped": "#3b82f6", "Uniform": "#22c55e", "Midday-Heavy": "#f97316"}.get(regime.volume_label, "#6b7280")
        with r2:
            st.markdown("**Volume Pattern**")
            st.markdown(_badge(regime.volume_label, vol_pattern_colour), unsafe_allow_html=True)
            st.markdown("")
            st.metric("U-shape score", f"{regime.u_shape_score:.2f}×",
                      delta="open/close vs midday", delta_color="off")
            if regime.volume_label == "U-Shaped":
                st.caption("Heavy open/close, light midday. VWAP benefits from trading with the open/close flow.")
            elif regime.volume_label == "Uniform":
                st.caption("Even volume distribution. TWAP performs well; minimal timing risk.")
            else:
                st.caption("Unusual midday concentration. Review liquidity timing before executing.")

        # --- Price trend ---
        trend_colour = _TREND_COLOURS.get(regime.trend_label, "#6b7280")
        with r3:
            st.markdown("**Return Autocorrelation**")
            st.markdown(_badge(regime.trend_label, trend_colour), unsafe_allow_html=True)
            st.markdown("")
            st.metric("Lag-1 autocorr", f"{regime.autocorr:+.3f}",
                      delta="5-min returns", delta_color="off")
            if regime.trend_label == "Trending":
                st.caption("Positive autocorrelation — intraday momentum. IS algo may benefit from faster execution.")
            elif regime.trend_label == "Mean-Reverting":
                st.caption("Negative autocorrelation — typical equity microstructure. Patient VWAP/TWAP favoured.")
            else:
                st.caption("Near-zero autocorrelation. No strong directional bias in intraday returns.")

        # ── Agents 3-5 placeholders ───────────────────────────────────────────
        st.markdown("---")
        for label, desc in [
            ("Agent 3 — Algorithm Simulation",
             "Simulates VWAP, TWAP, POV, and Implementation Shortfall on synthetic orders."),
            ("Agent 4 — Performance Comparison",
             "Compares execution cost in bps across algorithms and market conditions."),
            ("Agent 5 — LLM Recommendation Memo",
             "Generates a natural language recommendation explaining which algorithm minimises cost and why."),
        ]:
            with st.expander(f"🔲 {label} — Coming Soon"):
                st.info(desc)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 2 — INDEX REBALANCING ANALYSIS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "🔄 Index Rebalancing Analysis":

    st.title("🔄 Index Rebalancing Analysis")
    st.markdown(
        "Analyse stock price and volume dynamics around index rebalancing events "
        "using public constituent change data and yfinance market data."
    )

    col1, col2, col3 = st.columns([2, 2, 2])
    with col1:
        index_choice = st.selectbox(
            "Index", ["MSCI Taiwan", "Hang Seng", "Nikkei 225", "KOSPI 200"]
        )
    with col2:
        rebal_date = st.date_input("Rebalancing Effective Date")
    with col3:
        event_window = st.slider("Event Window (days around T)", 5, 20, 10)

    ticker_added = st.text_input(
        "Added Constituent Ticker", placeholder="e.g. 2330 for TSMC"
    )
    market_added = st.selectbox("Market", list(MARKET_INFO.keys()), key="rebal_market")

    st.button("▶ Run Rebalancing Analysis", type="primary", use_container_width=True, disabled=True)
    st.info("🔲 Index Rebalancing Analysis module — coming in next build.")
