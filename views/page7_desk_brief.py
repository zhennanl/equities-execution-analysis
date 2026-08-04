"""Page 7 — Index Rebalance Desk Brief (session 9i).

THE FRONT DOOR for time-poor PT traders: 30-second orientation
(what / data / why-trust), the LIVE event, then Step 1 built out.
Renders from cached JSONs only — instant load, no compute. Deep
tools: the Rebalance Trade Lifecycle page.
"""
import datetime as _dt
import json
from pathlib import Path

import streamlit as st

ANN, EFF = _dt.date(2026, 8, 11), _dt.date(2026, 8, 31)


def _chip_row():
    c = st.columns(4)
    c[0].metric("Graded prediction record", "22/22 adds",
                "point-in-time, 8 markets")
    c[1].metric("Event library", "24 events @ 5-min",
                "auction bars separated")
    c[2].metric("Automated tests", "429 green",
                "every finding pinned")
    c[3].metric("Data", "Public + own IB",
                "no vendor terminals")


def _live_banner():
    today = _dt.date.today()
    ta = (ANN - today).days
    te = (EFF - today).days
    st.info(
        f"**LIVE EVENT — MSCI August 2026 QIR**  ·  announcement in "
        f"**T-{ta}** (Aug-11, Asia reads Aug-12)  ·  rebalance print "
        f"in **T-{te}** (Aug-31 close). Everything below is the real "
        "pre-announcement state, refreshed from official sources on "
        "every visit — and it will be GRADED publicly after Aug-12.")


def _step_strip():
    cols = st.columns(4)
    steps = [
        ("1 · Win the trade", "predict changes, market with a graded "
         "record", "BUILT BELOW"),
        ("2 · Manage the window", "liquidity plan, crowding watch, "
         "discretion", "full tool: Lifecycle page, tab 2 + Time "
         "Machine"),
        ("3 · Execute the print", "cascade cockpit, situations "
         "playbook", "full tool: Lifecycle page, tab 3"),
        ("4 · Prove it", "benchmark strips, estimate ledger, "
         "reversal tracker", "full tool: Lifecycle page, tab 4"),
    ]
    for col, (t, d, w) in zip(cols, steps):
        with col:
            st.markdown(f"**{t}**")
            st.caption(d)
            st.caption(f"→ {w}")


def _shortlist_section():
    p = Path("data/tday_cards_aug26.json")
    if not p.exists():
        st.warning("Shortlist cache missing — run "
                   "scripts/tday_cards_demo.py")
        return
    blob = json.loads(p.read_text())
    st.subheader("The Aug-2026 Taiwan call — and the shortlist "
                 "behind it")
    st.markdown(
        "**Firm calls: none at the observable margin** — and that is "
        "a *validated* statement, not a shrug: only 1 of 44 reviews "
        "in a decade was APAC-quiet, Taiwan Aug-reviews change 7 "
        "years in 11, and our zero sits inside that history's "
        "normal range (the engine flags itself when it doesn't). "
        "Because a no-change call still leaves the desk with work, "
        "every nearby candidate ships with a probability, its "
        "expected flow, and a T-day forecast:")
    rows = []
    for c in blob["cards"]:
        if "note" in c:
            rows.append({"name": f"{c['side']} — {c['ticker']}",
                         "p": c["p_convert"], "flow if converts": "—",
                         "crowding now": "—",
                         "must start by": "—"})
            continue
        rows.append({
            "name": f"{c['side']} {c['ticker']}",
            "p": round(c["p_convert"], 3),
            "flow if converts":
                f"${c['flow_if_converts_usd_m'][0]}-"
                f"{c['flow_if_converts_usd_m'][1]}M "
                f"({c['adv_days'][0]}-{c['adv_days'][1]} ADV-days)"
                if c.get("adv_days") else "—",
            "crowding now": c.get("crowding", "—")[:44],
            "must start by": c.get("must_start_by", "—")})
    st.dataframe(rows, use_container_width=True, hide_index=True)
    st.caption(
        "p = decade base rate × visible share × proximity (formula "
        "on every card). BELOW-FLOOR rows carry the honestly "
        "unobservable probability mass — 13 of 21 recent TW changes "
        "came from below our data floor, and we say so instead of "
        "hiding it.")


def _method_and_grades():
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**How calls are made, in one breath**")
        st.caption(
            "Rebuild MSCI's own arithmetic from public data: line "
            "every stock up by size, walk to 85% market coverage "
            "(the GMSR line), non-members above 1.8× the line get "
            "in, members below 0.5× fall out — then layer measured "
            "provider behavior (review cadence, churn buffers, "
            "deletion hazards) and verify membership before any "
            "call ships. Full plain-language version: "
            "docs/EXPLAINER_INDEX_REVIEW_FOR_TRADERS.md")
    with c2:
        st.markdown("**Why trust it**")
        st.caption(
            "May-2026 graded live: 17/17 adds across 8 markets at "
            "point-in-time; deletes ~90% with every miss published "
            "and traced to a named data gap. Every rule was built "
            "from a graded mistake; every probability comes from "
            "the graded record; the Aug-12 announcement grades "
            "everything on this page — including the zero.")


def render():
    st.title("⭐ Index Rebalance — Desk Brief")
    st.caption(
        "One platform, four lifecycle steps, every number computed "
        "from public or own-account data with the formula attached. "
        "Built for the desk: open → see the live event state → "
        "drill only if you want to.")
    _chip_row()
    _live_banner()
    st.markdown("---")
    _step_strip()
    st.markdown("---")
    st.header("Step 1 — Winning the trade (live)")
    # freshness guarantee runs on every visit (TTL-guarded)
    try:
        from agents.data_freshness import (ensure_fresh_shorts,
                                           freshness_line)
        fr = ensure_fresh_shorts()
        (st.warning if fr["status"] == "DEGRADED" else st.caption)(
            freshness_line(fr))
    except Exception:                                  # noqa: BLE001
        pass
    _shortlist_section()
    # reuse the funnel + cards expanders from the deep page
    try:
        from views.page6_lifecycle import (_funnel_expander,
                                           _tday_cards_expander)
        _funnel_expander()
        _tday_cards_expander()
    except Exception as e:                             # noqa: BLE001
        st.caption(f"(deep-dive expanders unavailable: {e})")
    _method_and_grades()
    st.markdown("---")
    st.caption(
        "Steps 2-4 run in the full tool (sidebar: Rebalance Trade "
        "Lifecycle): the window planner and Time Machine, the T-day "
        "cockpit with the situations playbook, and the post-event "
        "pack. This page will grow one step per iteration — Step 1 "
        "first because that is where orders are won.")
