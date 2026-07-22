"""
Execution Analytics Platform — thin dispatcher (B8 refactor, 2026-07-08).
Page bodies live in views/ (page1_simulator, page2_rebalancing,
page3_program); shared imports/helpers in views/common.py. This file only
configures the app, renders the sidebar, and dispatches — keep it that way:
new UI belongs in a view module, new analytics in agents/.
"""

import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import streamlit as st

st.set_page_config(page_title="Execution Analytics Platform",
                   page_icon="📊", layout="wide",
                   initial_sidebar_state="expanded")

st.sidebar.title("Execution Analytics")
st.sidebar.markdown("---")
page = st.sidebar.radio("Module", [
    "📈 Execution Algorithm Simulator",
    "🔄 Index Rebalancing Analysis",
    "🧺 Program Trading Desk",
    "📋 Quarterly Client Review",
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


from views import (page1_simulator, page2_rebalancing, page3_program,
                   page4_quarterly_review)

if page == "📈 Execution Algorithm Simulator":
    page1_simulator.render()
elif page == "🔄 Index Rebalancing Analysis":
    page2_rebalancing.render()
elif page == "🧺 Program Trading Desk":
    page3_program.render()
elif page == "📋 Quarterly Client Review":
    page4_quarterly_review.render()
