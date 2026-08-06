"""Page 0 — Guided Demo: one basket, end to end, five minutes.

The nine-stage PT trade cycle (docs/PT_BASKET_TRADE_CYCLE.md) walked with
live demo data at every stage. Deliberately linear — an interviewer or
recruiter should scroll once and see the whole desk. Deep dives live on
Pages 1-4; every section says where.
"""
import datetime as _dt
import json as _json

import numpy as np
import pandas as pd
import streamlit as st


def render():
    st.title("🚀 Guided Demo — one basket through the whole desk")
    st.caption("Five minutes, nine stages, real logic at every step (demo "
               "data, clearly labeled — the workflow is the exhibit). Full "
               "tools: Pages 1-4 in the sidebar. Cycle doc: "
               "docs/PT_BASKET_TRADE_CYCLE.md")

    # ── Stage 0: RFQ ──────────────────────────────────────────────────────
    st.header("0 · A client asks for a quote — blind")
    from agents.basket_risk import (demo_panel, risk_decomposition,
                                    blind_profile, agency_quote_sketch)
    _b, _px, _ix, _adv = demo_panel()
    _risk = risk_decomposition(_b, _px, _ix)
    _prof = blind_profile(_b, _adv, _risk)
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**What the client sends (no names):**")
        st.code(_prof["text"])
    with c2:
        st.markdown("**Our agency response framework:**")
        st.code(agency_quote_sketch(_prof))
    st.caption(f"Under the mask: basket beta {_risk.beta:.2f}, tracking "
               f"error {_risk.te_ann:.1%} ann., {_risk.hedgeable_share:.0%} "
               f"hedgeable. Top tracking-risk name: "
               f"{_risk.contributors.iloc[0]['ticker']} "
               f"({_risk.contributors.iloc[0]['te_contribution_bps']:.0f} bps "
               "of TE). This split is exactly what a principal risk bid "
               "prices — and why tight trackers should trade agency.")

    # ── Stage 1: the file lands ───────────────────────────────────────────
    st.header("1 · We win it — and the file is a mess")
    from agents.pt_ops import normalize_client_file
    _raw = pd.DataFrame({
        "Symbol": ["2330 TT", "700 HK", "7203 JT", "700 HK", "MYSTERY XX"],
        "Side": ["B", "SELL", "1", "S", "B"],
        "Qty": [1000, 2000, 300, 1000, 100]})
    st.dataframe(_raw, use_container_width=True, hide_index=True)
    _nr = normalize_client_file(_raw)
    st.dataframe(_nr["basket"], use_container_width=True, hide_index=True)
    for _i in _nr["issues"]:
        st.warning(_i, icon="📎")
    st.caption("Bloomberg codes normalized, duplicates aggregated — and "
               "every guess is an explicit ISSUE, never silent. "
               "(Page 3 · A8)")

    # ── Stage 2: pre-open pack ────────────────────────────────────────────
    st.header("2 · Pre-open pack to the sales trader")
    from agents.pt_dealer import demo_basket
    from agents.pt_automation import preopen_pack
    _cb = demo_basket()
    _cb["adv_shares"] = [5e6, 8e5, 2e7, 1e7, 3e6, 2e6]
    _pp = preopen_pack(_cb)
    st.code(_pp["text"])
    st.caption("Lot rounding, blocked shorts caught BEFORE the open, "
               "capacity RAG, imbalance, auction cutoffs — one pack. "
               "(Page 3 · A1)")

    # ── Stage 3: the day ──────────────────────────────────────────────────
    st.header("3 · The execution day — who needs eyes NOW")
    from agents.pt_dealer import attention_queue
    _q = attention_queue(_cb, _dt.datetime(2026, 7, 22, 5, 15))
    st.dataframe(_q, use_container_width=True, hide_index=True)
    st.caption("A Taiwan name at 89% of its limit band, a blocked China-A "
               "short pinned to 100, a dry Tokyo tape, a cutoff 10 minutes "
               "out — one ranked list with reasons the dealer can "
               "challenge. (Page 3 · Cockpit; fire-once alerts · A2)")

    # ── Stage 5: EOD ──────────────────────────────────────────────────────
    st.header("4 · Same evening — the client email drafts itself")
    from agents.pt_automation import eod_client_summary
    st.code(eod_client_summary(_cb, "PGM-DEMO", _dt.date(2026, 7, 22)))
    st.caption("Numbers from the deterministic layer; the dealer edits "
               "10%; the sales trader sends. (Page 3 · A3)")

    # ── Stages 6-7: settle + recon ────────────────────────────────────────
    st.header("5 · Settlement knows the holidays; recon triages itself")
    from agents.pt_ops import settlement_date_holiday_aware
    _sd = settlement_date_holiday_aware("Taiwan (TWSE)", _dt.date(2026, 2, 12))
    st.info(f"TWSE trade on 2026-02-12 settles **{_sd['settles']}** — "
            f"pushed across {len(_sd['holidays_skipped'])} CNY closures. "
            "Fund accordingly. (Page 3 · A9; break classifier · A4)")

    # ── Stage 8: QBR ──────────────────────────────────────────────────────
    st.header("6 · The quarter ends — defend the ranking")
    from agents.quarterly_review import (build_quarterly_review,
                                         synthesize_demo_quarter)
    _r = build_quarterly_review(synthesize_demo_quarter(), quarter="2026Q2",
                                is_synthetic=True)
    if _r.available and _r.adjusted_ranking.get("available"):
        st.dataframe(_r.adjusted_ranking["table"],
                     use_container_width=True, hide_index=True)
        if _r.adjusted_ranking["movers"]:
            st.warning("Rank moves once conditions are held fixed: "
                       f"{_r.adjusted_ranking['movers']} — the raw table "
                       "would have mis-told the story.")
    st.caption("Difficulty-adjusted, CI-gated — the review that wins the "
               "next RFQ. (Page 4 · full QBR)")

    # ── the loop + honesty ────────────────────────────────────────────────
    st.markdown("---")
    st.markdown(
        "**The loop:** RFQ → staging → pre-trade → execute → report → "
        "settle → reconcile → review → next RFQ. Six of nine stages "
        "automated here; risk-bid pricing and OMS booking are honestly out "
        "of scope (docs/PT_BASKET_TRADE_CYCLE.md).\n\n"
        "**House rules throughout:** every model gated against a naive "
        "baseline (a model that can't beat the 20-day median ships the "
        "median); every rule table version-hashed; every check written to "
        "an audit pack as a by-product. Simulated fills on historical "
        "bars, free data only — all disclosed, because agency desks audit "
        "claims.")
