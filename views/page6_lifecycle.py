"""Page 6 — Index Rebalance Trade Lifecycle (session 8j).

One page, four tabs = the four lifecycle steps
(docs/INDEX_REBALANCE_TRADE_LIFECYCLE.md). Every tab is INTERACTIVE:
the trader edits a basket / moves a slider / types an indicative
print and the framework answers. All logic lives in agents/
(review_engine, event_window, execution_insights, pitch_pack,
pt_dealer); this file only renders.
"""
import json
from pathlib import Path

import pandas as pd
import streamlit as st

DATA = Path(__file__).resolve().parent.parent / "data"


def _crowding_caches():
    """Merged per-market crowding caches (LIVE sources only)."""
    try:
        from scripts.run_full_review_asia import market_short_caches
        return market_short_caches()
    except Exception:
        return {}


def _tab1_win_the_trade():
    from agents.event_data import CROWDING_SOURCES
    from agents.pitch_pack import track_record
    from agents.review_engine import crowding_reads
    st.subheader("Step 1 — Winning the trade (Phase-0 analytics)")
    st.caption(
        "What the sales trader shows the client BEFORE the order "
        "exists: the graded track record, honest probabilities, and "
        "the positioning overlay nobody else sends.")

    st.markdown("**The graded track record (misses included)**")
    st.dataframe(track_record(), use_container_width=True,
                 hide_index=True)

    st.markdown("**Crowding coverage — the honest grid**")
    st.dataframe(pd.DataFrame(CROWDING_SOURCES).T.reset_index()
                 .rename(columns={"index": "market"}),
                 use_container_width=True, hide_index=True)

    st.markdown("**Live positioning read** — type tickers "
                "(TW/JP/HK/CN-H codes), get the crowding color the "
                "pitch quotes")
    tickers = st.text_input(
        "Tickers (comma-separated)", "1101.TW, 0027.HK, 9995.HK",
        key="t1_tickers")
    if st.button("Read positioning", key="t1_go"):
        names = [t.strip() for t in tickers.split(",") if t.strip()]
        caches = _crowding_caches()
        rows = []
        for mkt, cache in caches.items():
            for base, label in crowding_reads(cache, names).items():
                rows.append({"ticker": base, "market": mkt,
                             "crowding": label})
        if rows:
            st.dataframe(pd.DataFrame(rows).drop_duplicates("ticker"),
                         use_container_width=True, hide_index=True)
            st.caption(
                "HIGH build into the event = consensus/priced; LOW "
                "or EXITING = the move is still unpriced — that "
                "distinction is the pitch's rarest line.")
        else:
            st.warning("No archive data for these tickers (see the "
                       "coverage grid; KR/MY/IN/ID have no live "
                       "public source).")


def _tab2_window():
    from agents.event_window import build_window_plan
    from agents.review_engine import crowding_reads
    st.subheader("Step 2 — Announcement → T: the window planner")
    st.caption(
        "Edit the basket, set the client's terms, generate the "
        "2.2 liquidity/risk sheet + 2.3 start schedule + documented "
        "discretion decisions. Live crowding + live TWT93U borrow "
        "where available.")

    default = pd.DataFrame([
        ["1101.TW", "Taiwan (TWSE)", "Sell", 2_500_000, 18_000_000, 30.0],
        ["2002.TW", "Taiwan (TWSE)", "Sell", 55_000_000, 9_500_000, 30.0],
        ["9995.HK", "Hong Kong (HKEX)", "Buy", 3_000_000, 1_400_000, 25.0],
        ["0027.HK", "Hong Kong (HKEX)", "Sell", 9_000_000, 21_000_000, 0.0],
    ], columns=["ticker", "market", "side", "qty_shares",
                "adv_shares", "envelope_pct"])
    basket = st.data_editor(default, num_rows="dynamic",
                            use_container_width=True, key="t2_basket")
    c1, c2, c3, c4 = st.columns(4)
    eff = c1.text_input("Effective date", "2026-09-01", key="t2_eff")
    cap = c2.slider("Participation cap", 0.05, 0.5, 0.25, 0.05,
                    key="t2_cap")
    tmed = c3.number_input("T-multiple (median, measured)", value=16.0,
                           key="t2_tmed")
    tmax = c4.number_input("T-multiple (max)", value=38.0,
                           key="t2_tmax")
    if st.button("Generate window plan", key="t2_go"):
        b = basket.dropna(subset=["ticker"])
        envelopes = dict(zip(b["ticker"], b["envelope_pct"]))
        caches = _crowding_caches()
        crowding = {}
        for cache in caches.values():
            crowding.update(crowding_reads(cache,
                                           list(b["ticker"])))
        sbl = None
        try:
            from agents.event_data import fetch_twse_short_balance
            from agents.event_window import sbl_utilization
            import datetime as dt
            d = dt.date.today()
            for _ in range(5):
                d -= dt.timedelta(days=1)
                if d.weekday() >= 5:
                    continue
                df = fetch_twse_short_balance(d.strftime("%Y%m%d"))
                if not df.empty:
                    sbl = sbl_utilization(df)
                    break
        except Exception:
            st.caption("TWT93U unreachable — borrow column will say "
                       "'no quota data'.")
        plan = build_window_plan(
            b[["ticker", "market", "side", "qty_shares",
               "adv_shares"]], eff, tmed, tmax,
            crowding_map=crowding, envelopes=envelopes,
            sbl_util=sbl, participation_cap=cap)
        st.markdown("**2.2 Liquidity & risk per name**")
        st.dataframe(plan["sheet"], use_container_width=True,
                     hide_index=True)
        st.markdown("**2.3a Start schedule**")
        st.dataframe(plan["schedule"], use_container_width=True,
                     hide_index=True)
        st.markdown("**2.3b Discretion decisions (best-ex rationale "
                    "attached)**")
        for _, r in plan["decisions"].iterrows():
            with st.expander(f"{r['ticker']} ({r['side']}): "
                             f"{r['decision']}"):
                st.write(r["rationale"])


def _tab3_tday():
    from agents.event_window import indicative_read
    from agents.pt_dealer import AUCTION_CUTOFFS
    st.subheader("Step 3 — T-day: the cascade cockpit")
    st.caption(
        "The run-sheet, and the day's ONE real-time decision — the "
        "indicative-vs-expected read — as an interactive calculator. "
        "Live feeds are PROTOCOL; the logic is the desk logic.")

    st.markdown("**The Asia cascade run-sheet (close cutoffs, "
                "local time)**")
    rs = (pd.DataFrame(AUCTION_CUTOFFS).T.reset_index()
          .rename(columns={"index": "market"}))
    st.dataframe(rs, use_container_width=True, hide_index=True)

    st.markdown("**Indicative-auction read (TW 13:25–13:30 style)**")
    c1, c2, c3, c4 = st.columns(4)
    exp = c1.number_input("Expected T-multiple", value=16.0,
                          key="t3_exp")
    ind = c2.number_input("Indicative multiple (live)", value=9.0,
                          key="t3_ind")
    side = c3.selectbox("Side", ["Sell", "Buy"], key="t3_side")
    env = c4.slider("Envelope remaining %", 0, 50, 20, key="t3_env")
    r = indicative_read(exp, ind, side, env)
    tone = (st.error if "THIN" in r["read"] else
            st.success if "RICH" in r["read"] else st.info)
    tone(f"**{r['read']}** → {r['action']}")
    st.caption(f"Why: {r['rationale']} (ratio {r.get('ratio', '-')}). "
               "The dealer takes the decision; this frames it.")

    st.markdown("**Auction-share derivation (the free-data trick)**")
    tk = st.text_input("Ticker (TW derives daily−Σbars; HK/JP read "
                       "the last bar)", "2330.TW", key="t3_tk")
    if st.button("Derive auction share", key="t3_go"):
        try:
            import yfinance as yf
            h5 = yf.Ticker(tk).history(period="5d", interval="5m")
            hd = yf.Ticker(tk).history(period="5d", interval="1d")
            day = h5[h5.index.date == h5.index.date[-1]]
            dv = float(hd["Volume"].iloc[-1])
            bars = float(day["Volume"].sum())
            if tk.endswith(".TW") or tk.endswith(".TWO"):
                share = max(dv - bars, 0) / dv if dv else float("nan")
                how = "derived: (daily − Σ intraday bars) / daily"
            else:
                share = (float(day["Volume"].iloc[-1]) / dv
                         if dv else float("nan"))
                how = "read: last bar / daily"
            st.metric(f"Close-auction share — {tk} (latest session)",
                      f"{share:.1%}")
            st.caption(f"{how}; daily {dv:,.0f} vs bars {bars:,.0f}. "
                       "Odd-lot noise included — stated, small.")
        except Exception as e:
            st.warning(f"Fetch failed: {e}")


def _tab4_posttrade():
    from agents.execution_insights import (discretion_counterfactual,
                                           render_debrief,
                                           reversal_grade,
                                           tca_vs_estimate,
                                           update_priors)
    st.subheader("Step 4 — Post-trade: prove it, grade it, feed it "
                 "back")
    st.caption(
        "Enter fills and realized paths (prefilled with the REAL "
        "May-2026 TW deletion paths); get the TCA-vs-estimate "
        "reconciliation, the discretion counterfactual, the reversal "
        "grade, and the prior shift — then download the client "
        "debrief.")

    st.markdown("**Fills (TCA vs pre-trade estimate)**")
    tca_default = pd.DataFrame([
        ["2324.TW", "Sell", 1_000_000, 108.41, 108.50, 12.0],
        ["1102.TW", "Sell", 1_000_000, 33.42, 33.45, 12.0],
    ], columns=["ticker", "side", "qty_shares", "avg_px", "close_px",
                "est_cost_bps"])
    fills = st.data_editor(tca_default, num_rows="dynamic",
                           use_container_width=True, key="t4_fills")

    st.markdown("**Discretion outcomes (choice vs realized drift)**")
    cf_default = pd.DataFrame([
        ["2324.TW", "Sell", "WAIT — MOC the full order", 0.0, 2274.0],
        ["2633.TW", "Sell", "WAIT — MOC the full order", 0.0, -710.0],
        ["1101.TW", "Sell", "WORK AHEAD 30%", 0.3, -150.0],
    ], columns=["ticker", "side", "decision", "worked_frac",
                "pre_close_drift_bps"])
    cf_in = st.data_editor(cf_default, num_rows="dynamic",
                           use_container_width=True, key="t4_cf")

    st.markdown("**Reversal vs the crowding read**")
    rev_default = pd.DataFrame([
        ["2324.TW", "LOW", -76.0, 44.0],
        ["2633.TW", "LOW", 88.0, -14.0],
    ], columns=["ticker", "crowding_band", "t_move_bps",
                "post_reversal_bps"])
    rev_in = st.data_editor(rev_default, num_rows="dynamic",
                            use_container_width=True, key="t4_rev")

    if st.button("Grade the event", key="t4_go"):
        tca = tca_vs_estimate(fills.dropna(subset=["ticker"]))
        cf = discretion_counterfactual(cf_in.dropna(subset=["ticker"]))
        rev = reversal_grade(rev_in.dropna(subset=["ticker"]))
        st.markdown("**4.2 TCA vs estimate**")
        st.dataframe(tca, use_container_width=True, hide_index=True)
        st.caption(f"Portfolio realized "
                   f"{tca.attrs.get('portfolio_realized_bps', '-')} "
                   "bps; vs estimate "
                   f"{tca.attrs.get('portfolio_vs_estimate_bps', '-')}"
                   " bps (qty-weighted).")
        st.markdown("**4.4a Discretion counterfactuals**")
        st.dataframe(cf, use_container_width=True, hide_index=True)
        st.markdown("**4.4b Reversal grade**")
        st.dataframe(rev, use_container_width=True, hide_index=True)
        st.caption(f"Crowding-implication hit rate: "
                   f"{rev.attrs.get('hit_rate', 'n/a')} (HIGH/LOW "
                   "reads only — MED and no-data never count).")
        try:
            cache = json.loads(
                (DATA / "event_flow_study.json").read_text())
        except Exception:
            cache = {"events": []}
        priors = update_priors(dict(cache), [])
        st.markdown("**4.5 Current priors (the library the next "
                    "pack quotes)**")
        st.dataframe(priors, use_container_width=True,
                     hide_index=True)
        md = render_debrief(
            tca, cf, rev, priors,
            "Client Debrief — interactive session", "generated in-app",
            notes="Generated from user-entered fills/paths in the "
                  "lifecycle page; library priors shown read-only.")
        st.download_button("Download client debrief (.md)", md,
                           file_name="client_debrief.md",
                           key="t4_dl")


def render():
    st.header("🔁 Index Rebalance Trade Lifecycle")
    st.caption(
        "The four steps of an index rebalance trade, end to end — "
        "Phase-0 analytics win it, the window plans it, T-day "
        "executes it, post-trade proves it. Backend: the graded "
        "4-step framework (docs/INDEX_REBALANCE_TRADE_LIFECYCLE.md).")
    t1, t2, t3, t4 = st.tabs([
        "1️⃣ Win the trade", "2️⃣ The window (ann → T)",
        "3️⃣ T-day cascade", "4️⃣ Post-trade & learning"])
    with t1:
        _tab1_win_the_trade()
    with t2:
        _tab2_window()
    with t3:
        _tab3_tday()
    with t4:
        _tab4_posttrade()
