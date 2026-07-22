"""
Execution Analytics Platform
Page 1: Execution Algorithm Simulator  — full 5-agent pipeline
Page 2: Index Rebalancing Analysis     — event study (CAR + abnormal volume)
"""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np   # was MISSING in the pre-refactor app.py — a bare `np.` inside a
                     # try/except silently disabled the cost-model -> scorecard bridge
                     # (latent bug found by the B8 pyflakes pass, fixed 2026-07-08)
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
from agents.trader_view import (build_verdict, trade_card_text, schedules_csv,
                                build_playbook, playbook_text, run_basket,
                                record_event, library_stats, library_context_line,
                                crowding_score, expected_move)
from agents.desk_pack import (build_desk_verdict, pretrade_card_text,
                              record_run, run_stats, load_runs)
from agents.trader_view import build_bestex_record, record_bestex, bestex_record_json
from agents.agent11_live_snapshot import live_volume_forecast
from agents.agent13_venue_router import (
    route_order, compare_policies, bar_volumes_for, venues_for,
    MARKET_VENUES, ROUTING_POLICIES, DEFAULT_HALF_SPREAD_BPS,
)


# ── Shared helpers (moved from app.py in the B8 refactor, 2026-07-08) ────────

@st.cache_data(ttl=300, show_spinner=False)
def _cached_fetch(ticker_base, market):
    return fetch_market_data(ticker_base, market, log=None)


@st.cache_data(ttl=300, show_spinner=False)
def _cached_fetch_kdb(ticker, market, host, port, username, password,
                      daily_table, trade_table, sym_col, date_col, time_col,
                      price_col, size_col, bar_minutes):
    """kdb+ path of the market-data fetch. Connection opened per cache-miss
    and closed after — no sockets in session state. Password participates in
    the cache key only as a hash input (st.cache_data hashes args)."""
    from agents.kdb_source import connect_kdb, fetch_market_data_kdb, KdbSchema
    schema = KdbSchema(daily_table=daily_table, trade_table=trade_table,
                       sym_col=sym_col, date_col=date_col, time_col=time_col,
                       price_col=price_col, size_col=size_col)
    h = connect_kdb(host, int(port), username, password)
    try:
        return fetch_market_data_kdb(h, ticker, market, schema=schema,
                                     bar_minutes=int(bar_minutes))
    finally:
        h.close()


def kdb_source_expander():
    """Data-source selector rendered on Page 1: Yahoo Finance (default) or
    the user's own kdb+/q time-series database. Config lives in
    st.session_state["kdb_cfg"] (None = Yahoo)."""
    cfg = st.session_state.get("kdb_cfg")
    tick = st.session_state.get("tick_md")
    label = ("🗄️ Market data source — **kdb+/q connected**" if cfg
             else "🗄️ Market data source — **tick file loaded**" if tick is not None
             else "🗄️ Market data source — Yahoo Finance (default)")
    with st.expander(label):
        use = st.radio("Source", ["Yahoo Finance (free, default)",
                                  "kdb+/q — my own tick database",
                                  "Tick file — LOBSTER / Binance / CSV"],
                       index=2 if tick is not None else 1 if cfg else 0,
                       horizontal=True)
        if use.startswith("Yahoo"):
            if cfg or tick is not None:
                st.session_state["kdb_cfg"] = None
                st.session_state["tick_md"] = None
                st.rerun()
            st.caption("Free yfinance feed; 5-min bars, 60d daily history.")
            return
        if use.startswith("Tick file"):
            st.session_state["kdb_cfg"] = None
            _tick_file_form()
            return
        st.session_state["tick_md"] = None
        c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
        host = c1.text_input("Host", value=(cfg or {}).get("host", "localhost"))
        port = c2.number_input("Port", 1, 65535, int((cfg or {}).get("port", 5000)))
        username = c3.text_input("User", value=(cfg or {}).get("username", ""))
        password = c4.text_input("Password", type="password",
                                 value=(cfg or {}).get("password", ""))
        st.markdown("**Schema mapping** (defaults = canonical kdb+ tick schema)")
        m1, m2, m3, m4 = st.columns(4)
        trade_table = m1.text_input("Trade table", (cfg or {}).get("trade_table", "trade"))
        daily_table = m2.text_input("Daily table", (cfg or {}).get("daily_table", "daily"))
        sym_col = m3.text_input("Sym col", (cfg or {}).get("sym_col", "sym"))
        bar_minutes = m4.number_input("Bar minutes", 1, 60,
                                      int((cfg or {}).get("bar_minutes", 5)))
        with st.container():
            n1, n2, n3, n4 = st.columns(4)
            date_col = n1.text_input("Date col", (cfg or {}).get("date_col", "date"))
            time_col = n2.text_input("Time col", (cfg or {}).get("time_col", "time"))
            price_col = n3.text_input("Price col", (cfg or {}).get("price_col", "price"))
            size_col = n4.text_input("Size col", (cfg or {}).get("size_col", "size"))
        if st.button("Connect / apply", type="primary"):
            from agents.kdb_source import connect_kdb, KdbConnectionError
            try:
                h = connect_kdb(host, int(port), username, password)
                h.close()
                st.session_state["kdb_cfg"] = dict(
                    host=host, port=int(port), username=username,
                    password=password, daily_table=daily_table,
                    trade_table=trade_table, sym_col=sym_col,
                    date_col=date_col, time_col=time_col, price_col=price_col,
                    size_col=size_col, bar_minutes=int(bar_minutes))
                st.success(f"Connected to kdb+ at {host}:{port} "
                           f"({h.kind} driver). Ticker box now takes the sym "
                           "as stored in your database (no Yahoo suffixing).")
            except KdbConnectionError as e:
                st.error(f"❌ {e}")
        st.caption("⚠️ Bars are aggregated server-side with `xbar` — ticks "
                   "never cross the wire. Intraday needs a trade table with "
                   "a time-typed column; daily needs EOD OHLCV. See "
                   "docs/KDB_INTEGRATION.md for the production notes "
                   "(tickerplant subscription, sym enumeration, gateways).")


def _tick_file_form():
    """Upload a historical tick file (free sources: LOBSTER samples, Binance
    public data, any trades CSV) and build MarketData from it. The loaded
    object is pinned in session state; the ticker/market inputs below are
    then IGNORED until it\'s unloaded (disclosed loudly)."""
    from agents.tick_ingest import (load_lobster, load_binance_trades,
                                    load_csv_trades, market_data_from_trades)
    from agents.agent1_market_data import MARKET_INFO
    if st.session_state.get("tick_md") is not None:
        md = st.session_state["tick_md"]
        st.success(f"Loaded: **{md.ticker}** — {len(md.intraday)} bars, "
                   f"{len(md.daily)} daily row(s). The ticker/market inputs "
                   "below are ignored while this is loaded.")
        if st.button("Unload tick file"):
            st.session_state["tick_md"] = None
            st.rerun()
        return
    fmt = st.selectbox("Format", ["LOBSTER message file",
                                  "Binance trades / aggTrades",
                                  "Generic trades CSV"])
    up = st.file_uploader("Tick file (.csv or .zip)", type=["csv", "zip"])
    c1, c2, c3 = st.columns(3)
    sym = c1.text_input("Symbol", value="AAPL")
    market = c2.selectbox("Market (session/bars context)",
                          list(MARKET_INFO.keys()))
    bar_minutes = c3.number_input("Bar minutes", 1, 60, 5)
    if fmt.startswith("LOBSTER"):
        trade_date = st.date_input("Trade date (LOBSTER files carry only "
                                   "seconds-after-midnight)")
    if fmt.startswith("Generic"):
        g1, g2, g3, g4 = st.columns(4)
        ts_col = g1.text_input("Timestamp col", "timestamp")
        px_col = g2.text_input("Price col", "price")
        sz_col = g3.text_input("Size col", "size")
        epoch = g4.selectbox("Epoch unit", ["(datetime strings)", "s", "ms",
                                            "us", "ns"])
    if up is not None and st.button("Load tick file", type="primary"):
        import tempfile, os
        suffix = os.path.splitext(up.name)[1] or ".csv"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as f:
            f.write(up.getvalue()); tmp = f.name
        try:
            if fmt.startswith("LOBSTER"):
                trades = load_lobster(tmp, sym, trade_date)
            elif fmt.startswith("Binance"):
                trades = load_binance_trades(tmp, sym)
            else:
                trades = load_csv_trades(
                    tmp, sym, ts_col, px_col, sz_col,
                    epoch_unit="" if epoch.startswith("(") else epoch)
            st.session_state["tick_md"] = market_data_from_trades(
                trades, market, bar_minutes=int(bar_minutes))
            st.rerun()
        except Exception as e:
            st.error(f"❌ Could not ingest: {e}")
        finally:
            os.unlink(tmp)
    st.caption("Free sources: LOBSTER samples (data.lobsterdata.com), "
               "Binance public data (data.binance.vision), IEX HIST (needs "
               "`pip install IEXTools`, API-level only). ⚠️ One file usually "
               "= one day: ADV/vol context is thin and disclosed in the vol "
               "note. `agents.tick_ingest.to_kdb_csv` exports the same "
               "trades as a q-loadable table for the kdb+ path.")


def fetch_any(ticker_base, market):
    """Route the fetch by configured source. kdb+ and tick-file fall back
    loudly, never silently — a broken config must not quietly become Yahoo
    data, and a pinned tick file must be visibly pinned."""
    if st.session_state.get("tick_md") is not None:
        return st.session_state["tick_md"]
    cfg = st.session_state.get("kdb_cfg")
    if cfg:
        return _cached_fetch_kdb(ticker_base, market, **cfg)
    return _cached_fetch(ticker_base, market)


_VC = {"Tight":"#3b82f6","Normal":"#22c55e","Trending":"#f97316","Extremely Trending":"#ef4444"}
_TC = {"Trending":"#f97316","Mean-Reverting":"#8b5cf6","Neutral":"#6b7280"}
_AC = {"VWAP":"#1f77b4","TWAP":"#2ca02c","POV":"#ff7f0e","IS":"#9467bd",
       "MOC":"#17becf","MOO":"#bcbd22","LIQ":"#e377c2","STEALTH":"#7f7f7f"}

def _badge(txt, col):
    return (f'<span style="background:{col};color:white;padding:3px 10px;'
            f'border-radius:12px;font-weight:600;font-size:0.85rem;">{txt}</span>')
