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


def _truncated_tw_cache(upto: str) -> dict:
    """TW short archive truncated for the PIT replay — nothing after
    the announcement date enters the crowding read."""
    try:
        c = json.loads((DATA / "event_data_cache.json").read_text())
        return {"short": {d: v for d, v in c.get("short", {}).items()
                          if d <= upto}}
    except Exception:
        return {}


def _run_event_engine(event, markets):
    """Run the full review engine for the selected event's markets
    from cached universes. Returns (results, boundary, crowding).
    engine=='pit' freezes every input at pre-announcement vintage:
    Apr-30 caps, PRE-May membership, Feb-only ledgers (the May list
    is the answer key), crowding truncated at the announcement."""
    from agents.pre_event_marketing import boundary_watch
    from agents.reconstitution import parse_msci_public_list
    from agents.review_engine import crowding_reads, run_full_review
    from scripts.pit_may2026_asia import ACTUAL
    from scripts.run_full_review_asia import (COUNT, PRE_COUNT, RANGE,
                                              pit_screen, pit_universe,
                                              post_may_universe)
    from scripts.run_qir_aug2026 import TW_ALIASES
    pit = event["engine"] == "pit"
    ledger_files = ("feb26",) if pit else ("feb26", "may26")
    ledgers = [parse_msci_public_list(
        (DATA / f"msci_{p}_public_list.txt").read_text())
        for p in ledger_files]
    try:
        event_cache = json.loads(
            (DATA / "event_flow_study.json").read_text())
    except Exception:
        event_cache = None
    if pit:
        caches = {"Taiwan": _truncated_tw_cache(
            event["ann"].replace("-", ""))}
    else:
        caches = _crowding_caches()
    LEDGER_COUNTRY = {"Taiwan": "TAIWAN", "Japan": "JAPAN",
                      "Korea": "KOREA", "China": "CHINA",
                      "India": "INDIA", "Malaysia": "MALAYSIA",
                      "Indonesia": "INDONESIA",
                      "HongKong": "HONG KONG"}
    results, boundary, crowding = [], {}, {}
    for mkt in markets:
        u = pit_universe(mkt) if pit else post_may_universe(mkt)
        hi, n = RANGE[mkt]
        r = run_full_review(
            mkt, u, TW_ALIASES if mkt == "Taiwan" else {},
            ledgers, LEDGER_COUNTRY[mkt],
            short_cache=caches.get(mkt), event_cache=event_cache,
            review=event["review"],
            member_count=(PRE_COUNT if pit else COUNT)[mkt],
            a_share_tail_mix=(mkt == "China"), tail_hi=hi, tail_n=n,
            recent_deletions=(set() if pit
                              else set(ACTUAL[mkt]["dels"])),
            recent_additions=(set() if pit
                              else set(ACTUAL[mkt]["adds"])),
            screen=(pit_screen(mkt, u) if pit else None))
        results.append(r)
        b = boundary_watch(u, r["gmsr_usd"], r["add_threshold_usd"])
        boundary[mkt] = b
        crowding.update(crowding_reads(
            caches.get(mkt), list(b["ticker"])))
    return results, boundary, crowding


def _workbench_expander():
    """Session 9i c-29: Step-1 universe-assembly workbench — the
    CLEAR NUMBERS behind every name: local cap -> FX -> refresh ->
    USD cap, free-float estimate, float-adjusted cap, and the
    decision bucket each number produces."""
    import json
    from pathlib import Path
    p = Path("data/universe_workbench_tw.json")
    if not p.exists():
        return
    with st.expander("🧮 Step 1 workbench — every number behind the "
                     "universe (Taiwan)"):
        pit = Path("data/universe_workbench_tw_may26pit.json")
        run = st.radio(
            "Frame", ["live", "pit"], horizontal=True,
            key="wb_run", format_func=lambda k:
            ("Aug-2026 QIR (live)" if k == "live" else
             "May-2026 SAIR — PIT validation (data frozen at "
             "Apr-30, graded vs the official result)"))
        if run == "pit" and pit.exists():
            _workbench_pit(json.loads(pit.read_text()))
            return
        b = json.loads(p.read_text())
        thr = b["thresholds"]
        st.markdown(
            f"**The arithmetic, name by name** (as-of {b['asof']}): "
            "cap in TWD (price × shares, Apr-30) ÷ FX "
            f"{b['fx_twd_usd']} × current-price ratio → USD cap. "
            "The **coverage walk uses float-adjusted cap** "
            "(ff × cap) to set the GMSR; the **hurdles use full "
            "cap** — thresholds below.")
        c1, c2, c3 = st.columns(3)
        c1.metric("GMSR (our estimate)", f"${thr['gmsr_usd_b']}B",
                  "85% coverage walk")
        c2.metric("Add bar (QIR 1.8×)", f"${thr['add_bar_usd_b']}B",
                  "full cap must exceed")
        c3.metric("Deletion floor (0.5×)", f"${thr['floor_usd_b']}B",
                  "members below = candidates")
        import plotly.graph_objects as go
        rows = b["rows"]
        fig = go.Figure()
        for memflag, name, color in ((True, "member", "#4C78A8"),
                                     (False, "non-member",
                                      "#E45756")):
            sub = [r for r in rows if r["member"] == memflag]
            fig.add_trace(go.Scatter(
                x=[r["cap_usd_b_now"] for r in sub],
                y=[r["ticker"] for r in sub],
                mode="markers+text", name=name,
                text=[f" {r['cap_usd_b_now']}B" for r in sub],
                textposition="middle right",
                marker=dict(size=11, color=color)))
        for v, lbl, dash in ((thr["floor_usd_b"], "floor 0.5×",
                              "dot"),
                             (thr["gmsr_usd_b"], "GMSR", "dash"),
                             (thr["add_bar_usd_b"], "add bar 1.8×",
                              "dot")):
            fig.add_vline(x=v, line_dash=dash, line_color="#888",
                          annotation_text=lbl,
                          annotation_position="top")
        import math
        xmax = max(r["cap_usd_b_now"] for r in rows)
        fig.update_xaxes(type="log",
                         range=[math.log10(1.5),
                                math.log10(xmax * 4)],
                         title="full market cap, USD B (log)")
        fig.update_layout(height=430,
                          margin=dict(l=10, r=10, t=30, b=10))
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(rows, use_container_width=True,
                     hide_index=True)
        st.caption(
            "Decision logic: members are judged against the floor "
            "(full cap < 0.5× GMSR → DELETE candidate; within 15% → "
            "watch), non-members against the add bar (≥ 1× → ADD "
            "candidate). Free float never decides candidacy "
            "directly — it shapes the GMSR through the coverage "
            "walk and sets index weight. Every input's source: the "
            "Data provenance panel above. Formulas: "
            + "; ".join(f"{k} = {v}"
                        for k, v in b["formulas"].items()))


def _workbench_pit(b):
    """May-2026 PIT validation frame (c-32): the engine test the
    user asked for — 'pretend it is one day before the announcement'
    — with the tentative add shortlist derived explicitly and then
    graded against what MSCI actually did."""
    thr = b["thresholds"]
    st.markdown(
        f"**Frame: {b['asof']}** — every number below was computable "
        "one day before the May-2026 announcement. "
        f"**{b['members']} of {b['n_names']}** named stocks were "
        "members at that date, reconstructed from the free public "
        "record (iShares EWT holdings anchor, reverse-rolled "
        "through official reviews — no licensed data).")
    c1, c2, c3 = st.columns(3)
    c1.metric("GMSR (PIT walk)", f"${thr['gmsr_usd_b']}B")
    c2.metric("Add bar (SAIR 1.15×)", f"${thr['add_bar_usd_b']}B")
    c3.metric("Deletion floor (0.5×)", f"${thr['floor_usd_b']}B")
    st.markdown("**How the tentative ADD shortlist is derived — "
                "every step:**")
    for step in b["derivation"]:
        st.caption(step)
    st.markdown("**Tentative adds (PIT) — graded vs the official "
                "May-26 result:**")
    st.dataframe(b["tentative_adds"], use_container_width=True,
                 hide_index=True)
    hits = sum(1 for r in b["tentative_adds"]
               if "ADDED" in r["official"])
    st.warning(
        f"Honest read: {hits} of {len(b['tentative_adds'])} "
        "names above the full-cap bar were actually added (6223 "
        "MPI — which this frame ranks clearly). The rest are "
        "mostly EX-members deleted years ago for float/liquidity "
        "reasons that persist — full-cap proximity alone has poor "
        "precision, and the binding discriminators (MSCI's real "
        "floats, FIF, foreign room) are exactly our stated #1 "
        "data gap. This is why the engine layers float screens, "
        "churn history, and probabilities on top of the raw "
        "ladder — the raw ladder alone would mislead you.")
    st.markdown("**Full PIT universe (all named stocks, Apr-30 "
                "numbers):**")
    st.dataframe(b["rows"], use_container_width=True,
                 hide_index=True)
    st.caption(
        "Columns worth reading: foreign_12m_pp (foreign-ownership "
        "change over the prior year — decade EDA: +5.5pp median "
        "into adds, −4.1pp into deletes) and cap_12m_chg_pct (the "
        "glide path: deleted names median −22%). ff_estimated=True "
        "rows carry our default float — the labeled uncertainty.")


def _funnel_expander():
    """Session 9i: the screening funnel — universe -> conditions ->
    candidates, from data/funnel_tw.json (scripts/funnel_demo.py).
    Shows the validated May-26 replay next to the Aug-26 prediction."""
    import json
    from pathlib import Path
    p = Path("data/funnel_tw.json")
    if not p.exists():
        return
    with st.expander("🔻 Screening funnel — how ~500 names become "
                     "the call sheet (Taiwan)"):
        blob = json.loads(p.read_text())
        st.caption(
            "Starts at **engine Step 1 — universe acquisition**: "
            "caps from price × shares (yfinance, FX→USD), free-float "
            "estimated, membership rolled forward from official "
            "results, count anchored to MSCI's published constituent "
            "count. Every later stage applies one published rule.")
        which = st.radio("Run", ["prediction", "validation"],
                         horizontal=True, key="funnel_which",
                         format_func=lambda k:
                         blob[k]["event"])
        stages = blob[which]["stages"]
        import plotly.graph_objects as go
        fig = go.Figure(go.Funnel(
            y=[s["stage"] for s in stages],
            x=[max(s["n"], 0) for s in stages],
            textinfo="value",
            marker={"color": ["#4C78A8"] * (len(stages) - 1)
                    + ["#E45756"]}))
        fig.update_layout(height=380,
                          margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(
            [{"stage": s["stage"], "n": s["n"], "rule": s["rule"],
              "detail": s["detail"]} for s in stages],
            use_container_width=True, hide_index=True)
        # session 9i cont-28: the shortlist AT each stage — every
        # real name's journey with the deciding rule, plus the
        # selection method per stage cited to the GIMI book.
        if blob[which].get("journeys"):
            st.markdown("**Name journeys — the shortlist at every "
                        "stage** (members shown vs the hard 0.5× "
                        "floor, non-members vs the add bar):")
            st.dataframe(blob[which]["journeys"],
                         use_container_width=True, hide_index=True)
            if which == "validation":
                st.caption(
                    "Why delete candidates sit ABOVE the hard floor "
                    "here: May is a SAIR, where the migration sweep "
                    "(GIMI §3.1.5.1 buffers) removes Standard names "
                    "at a higher effective bar than the absolute "
                    "0.5×-GMSR floor — decade-validated: 62–90% of "
                    "deletions happen at SAIRs this way.")
        if blob.get("methods"):
            with st.popover("📖 Selection method per stage — GIMI "
                            "May-2026 citations"):
                for k, v in blob["methods"].items():
                    st.markdown(f"**{k}** — {v}")
        if which == "validation" and "grade" in blob[which]:
            g = blob[which]["grade"]
            st.markdown(
                f"**Graded vs the official May-26 key:** deletions "
                f"hit {len(g['dels_hit'])}/7, add hit "
                f"{len(g['adds_hit'])}/1; false deletes "
                f"{g['false_dels']} — the known cutline residents "
                "(the hazard class, ~2/3 convert at a later SAIR); "
                "nothing ungradable in this run.")
        else:
            st.caption(
                "Zero calls at the OBSERVABLE margin. The blind band "
                "below the 16-name floor is DECLARED (decade says ~2 "
                "TW Aug-QIR changes typically live there) — see "
                "TAIWAN_MARKET_ANALYSIS §6c.")


def _tday_cards_expander():
    """Session 9i: T-day forecast cards for shortlist names —
    every metric carries its formula/source/basis (METHOD table)."""
    import json
    from pathlib import Path
    p = Path("data/tday_cards_aug26.json")
    if not p.exists():
        return
    with st.expander("🃏 T-day forecast cards — Aug-2026 TW "
                     "shortlist (transparent methodology)"):
        blob = json.loads(p.read_text())
        from agents.tday_cards import METHOD
        with st.popover("METHOD — how every number is calculated"):
            for m, d in METHOD.items():
                st.markdown(f"**{m}** — {d['rule']}  \n"
                            f"*source: {d['source']} | basis: "
                            f"{d['basis']}*")
        for c in blob["cards"]:
            if "note" in c:
                st.info(f"{c['side']} {c['ticker']} "
                        f"p={c['p_convert']}: {c['note']}")
                continue
            head = (f"**{c['side']} {c['ticker']}** — "
                    f"p={c['p_convert']:.3f} | flow if converts "
                    f"${c['flow_if_converts_usd_m'][0]}-"
                    f"{c['flow_if_converts_usd_m'][1]}M | "
                    f"{c['bucket']}")
            with st.container(border=True):
                st.markdown(head)
                cols = st.columns(3)
                pm = c.get("print_multiple", {})
                cols[0].metric("Print multiple (med)",
                               f"{pm.get('median', '—')}x"
                               if pm.get("median") else "no prior")
                fp = c.get("auction_footprint_pct", "—")
                cols[1].metric("Auction footprint", f"{fp}%")
                cols[2].metric("Gap band",
                               c.get("gap_band_bps", {}).get(
                                   "band", "—"))
                st.caption(f"Crowding: {c['crowding']} · "
                           f"Playbook: {c['playbook']}")


def _sentinel_strip():
    """C-38: Layer-0 sentinel report — six watchers, one line each.
    The trader reads deltas, not data sources."""
    import json
    from pathlib import Path
    p = Path("data/sentinel_report.json")
    if not p.exists():
        st.caption("Sentinels not yet run — `python -m "
                   "agents.sentinels` (daily). See "
                   "docs/SENTINELS_GUIDE.md")
        return
    rep = json.loads(p.read_text())
    icon = {"OK": "🟢", "CHANGED": "🟡", "ALERT": "🔴",
            "DEGRADED": "⚫"}
    head = (f"{icon.get(rep['overall'], '❓')} Sentinels: "
            f"**{rep['overall']}** (as of {rep['generated'][:16]})")
    with st.expander(head,
                     expanded=rep["overall"] in ("ALERT",
                                                 "DEGRADED")):
        for r in rep["results"]:
            st.markdown(f"{icon.get(r['status'], '❓')} "
                        f"`{r['sentinel']:<9s}` {r['delta']}")
        st.caption(
            "Six automated watchers: shorts freshness, fund "
            "membership (corporate-event detector), ladder pool "
            "moves, calendar deadlines, FX drift, artifact "
            "staleness. Statuses: 🟢 nothing to do · 🟡 noted, "
            "no action · 🔴 look today · ⚫ data broken, distrust "
            "downstream. Full guide: docs/SENTINELS_GUIDE.md")


@st.cache_data(ttl=3600, show_spinner="Reconstructing the index "
               "as of that date (PIT)...")
def _pit_ladder(date: str):
    from agents.pit_constituents import ladder_asof
    return ladder_asof(date)


def _constituents_expander():
    """C-42: market selector -> the FULL current MSCI country
    Standard membership, from the cached 3-source pipeline
    (data/apac_members.json). Cache refresh is EVENT-DRIVEN: the
    members sentinel diffs 12 funds daily and rewrites the cache
    whenever the provider's changes reach the tracking funds."""
    import json
    from pathlib import Path
    p = Path("data/apac_members.json")
    if not p.exists():
        return
    blob = json.loads(p.read_text())
    mkts = blob["markets"]
    with st.expander("🌏 Current MSCI constituents by market "
                     "(cached, sentinel-refreshed)", expanded=False):
        c1, c2 = st.columns([1, 3])
        with c1:
            mkt = st.selectbox("Market", sorted(mkts),
                               index=sorted(mkts).index("Taiwan"),
                               key="const_mkt")
        m = mkts[mkt]
        if "error" in m:
            st.warning(f"{mkt}: harvest error — {m['error']}")
            return
        std = set(m.get("standard_members", []))
        conf = set(m.get("confirmed_both", []))
        rows = []
        for t in sorted(std):
            rows.append({
                "ticker": t,
                "company": (m.get("names") or {}).get(t, ""),
                "confidence": ("CONFIRMED (both funds)"
                               if t in conf else
                               "LIKELY (one fund)")})
        with c2:
            st.metric(f"MSCI {mkt} Standard — members",
                      len(rows),
                      f"{len(conf & std)} confirmed by 2+ funds")
        st.dataframe(rows, use_container_width=True,
                     hide_index=True, height=380)
        # ── c-43: PIT time-travel (Taiwan first — vintage caps +
        # print-verified change history are TW-complete) ──
        if mkt == "Taiwan":
            st.markdown("---")
            hist = st.toggle("🕰️ Test with historical data — "
                             "reconstruct the index at ANY date "
                             "(PIT)", key="const_hist")
            if hist:
                import datetime as _dt
                d = st.date_input(
                    "As-of date", value=_dt.date(2026, 5, 1),
                    min_value=_dt.date(2016, 1, 1),
                    max_value=_dt.date.today(), key="const_date")
                L = _pit_ladder(str(d))
                st.success(f"Resolved: {L['resolved']} — "
                           f"**{L['n_members']} members** "
                           f"(unpriced: "
                           f"{len(L['unpriced_members'])})")
                st.markdown("**Full constituent list, ranked by "
                            "market cap as of that date:**")
                st.dataframe(
                    [r for r in L["ladder"] if r["member"]],
                    use_container_width=True, hide_index=True,
                    height=350)
                st.markdown(
                    f"**Next step — the candidates** (PIT GMSR "
                    f"walk: **${L['gmsr_usd_b']}B**):")
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown("**DELETE candidates** (members "
                                "inside the buffer band):")
                    st.dataframe(L["delete_candidates"],
                                 use_container_width=True,
                                 hide_index=True)
                with c2:
                    st.markdown("**ADD candidates** (non-members "
                                "near/over the bar, dual hurdle):")
                    st.dataframe(L["add_candidates"],
                                 use_container_width=True,
                                 hide_index=True)
                st.caption(L["breadth_note"] + " Validated: this "
                           "frame reproduces May-26 (7/7 deletes "
                           "led the candidate list) and Nov-25 "
                           "(7/7) against official keys.")
                return
        imi = "IMI" in m.get("anchor_variant", "")
        st.caption(
            f"Source: {m['fund']} holdings (as of {m['asof']}) "
            f"cross-checked vs {m['composite']} subset (as of "
            f"{m['composite_asof']})"
            + ("; NOTE: this market's single-country fund tracks "
               "the IMI variant, so the Standard list here is the "
               "composite subset — the fund's extra names are "
               "Small Cap" if imi else "")
            + ". **Refresh policy:** the cache updates "
            "automatically when the members sentinel (daily) "
            "detects the provider's changes reaching the tracking "
            "funds — review implementations and mid-quarter "
            "corporate events both trigger it; nothing refreshes "
            "on a timer for its own sake. Methodology: "
            "docs/CONSTITUENT_PIPELINE_FRAMEWORK.md")


def _provenance_expander():
    """Session 9i continued-27: data provenance — who produces each
    input, how it is computed, when it was last updated. Directly
    answers 'is this from MSCI or calculated by us?' in the UI."""
    import datetime as dt
    from pathlib import Path

    def _age(p):
        f = Path(p)
        if not f.exists():
            return "missing", None
        m = dt.datetime.fromtimestamp(f.stat().st_mtime)
        return m.strftime("%Y-%m-%d %H:%M"), \
            (dt.datetime.now() - m).days

    caps_ts, caps_age = _age("data/aug26_cap_refresh.json")
    pit_ts, _ = _age("data/pit_may26_asia_cache.json")
    with st.expander("🔎 Data provenance — what MSCI publishes vs "
                     "what we compute"):
        st.markdown(
            "**MSCI publishes the rules, not the answers.** Nothing "
            "below arrives from MSCI pre-announcement except the "
            "methodology book and the factsheet constituent count — "
            "everything else is computed by this platform from "
            "public market data, with its refresh time shown.")
        st.dataframe([
            {"input": "Boundary name list (16 TW names)",
             "produced by": "US — curated from our own cap ranking "
                            "near the GMSR boundary",
             "how": "members nearest the 0.5× deletion floor + "
                    "non-members nearest the add bar",
             "last updated": "membership rolled forward from "
                             "official May-26 results"},
            {"input": "Market caps",
             "produced by": "US — computed, not vendor-fed",
             "how": "price × shares outstanding (yfinance), "
                    "TWD→USD; Apr-30 base × current-price ratio",
             "last updated": f"ratios refreshed {caps_ts}"},
            {"input": "Free-float estimates",
             "produced by": "US — estimated (MSCI's own floats are "
                            "licensed, a stated source of misses)",
             "how": "holder filings via yfinance, capped at 1.0",
             "last updated": f"base cache {pit_ts}"},
            {"input": "GMSR / add bar / deletion floor",
             "produced by": "US — re-derived every run",
             "how": "85% coverage walk over the assembled universe "
                    "(MSCI's published arithmetic)",
             "last updated": "computed live from the caps above"},
            {"input": "Constituent count anchor (83)",
             "produced by": "MSCI — public factsheet",
             "how": "pins the modeled tail so the coverage walk "
                    "lands where the real index size puts it",
             "last updated": "May-2026 review"},
            {"input": "Short interest / borrow",
             "produced by": "TWSE — official, free",
             "how": "auto-refreshed on every visit (TTL 4h), "
                    "no-data days ledgered",
             "last updated": "see freshness line above"},
        ], use_container_width=True, hide_index=True)
        if caps_age is not None and caps_age >= 3:
            st.warning(
                f"Cap-refresh ratios are {caps_age} days old — run "
                "`python scripts/refresh_aug_caps.py` for "
                "current-price caps. (The Aug-11 protocol refreshes "
                "them same-morning before the pack finalizes.)")
        st.caption(
            "Honesty note: MSCI's official GMSR, float estimates, "
            "and price-cutoff date are not public pre-announcement. "
            "Ours are labeled estimates; every graded miss has been "
            "traced to one of these gaps, never to the rules.")


def _tab1_win_the_trade():
    from agents.pre_event_marketing import (EVENTS, days_to,
                                            render_marketing_md)
    st.subheader("Step 1 — Winning the trade")
    st.caption(
        "Pick the event the client is asking about; the engine runs "
        "and generates the pre-event marketing pack — the call "
        "sheet, the boundary watch, the positioning overlay, and "
        "the client note to send.")
    # session 9i: the freshness guarantee — every live UI visit
    # checks (TTL-guarded) that the short cache is at the most
    # recent published day, auto-refreshing if not. Never silent.
    try:
        from agents.data_freshness import (ensure_fresh_shorts,
                                           freshness_line)
        fr = ensure_fresh_shorts()
        (st.warning if fr["status"] == "DEGRADED" else st.caption)(
            freshness_line(fr))
        if fr["fetched_days"]:
            st.caption("Note: pre-generated artifacts (cards/packs) "
                       "may predate this refresh — regenerate via "
                       "scripts/pre_announcement_demo.py for "
                       "current reads.")
    except Exception as e:                             # noqa: BLE001
        st.warning(f"Freshness check unavailable ({e}) — reads may "
                   "be stale.")
    _sentinel_strip()
    _constituents_expander()
    _provenance_expander()
    _workbench_expander()
    _funnel_expander()
    _tday_cards_expander()

    event_name = st.selectbox("Index rebalance event",
                              list(EVENTS.keys()), key="t1_event")
    event = EVENTS[event_name]
    c1, c2, c3, c4 = st.columns(4)
    dta = days_to(event["ann"])
    c1.metric("Announcement", event["ann"],
              f"T-{dta}" if dta >= 0 else "announced")
    c2.metric("Effective close", event["eff"])
    c3.metric("Provider / review",
              f"{event['provider']} {event['review']}")
    c4.metric("Engine", event["engine"].upper())
    st.caption(event["note"])

    if event["engine"] == "reference":
        st.info(
            "**Reference mode (honesty line).** No validated live "
            "rank universe for this event yet — we show the graded "
            "reference, not a fabricated list. June-2026 TW50 "
            "record: adds 4/4 at the 40/61 rank buffers; deletion "
            "side shipped as a watch zone (rank-boundary calls are "
            "~50-60% by construction — cutline mechanics, stated). "
            "See docs/case_studies/PITCH_PACK_TW50_Jun2026.md.")
        return
    if event["engine"] == "pit":
        st.warning(
            "**Point-in-time replay.** Inputs frozen BEFORE the "
            "May-12 announcement: Apr-30 caps (historical prices), "
            "pre-May membership, ledgers through Feb only, crowding "
            "archive truncated at the announcement. The official "
            "outcome exists but does NOT enter the run — generate "
            "the prediction first, then open the self-grade at the "
            "bottom.")

    markets = st.multiselect("Markets in scope", event["markets"],
                             default=event["markets"], key="t1_mkts")
    if st.button("Run the engine → generate pre-event pack",
                 type="primary", key="t1_go"):
        with st.spinner("Screening universes, reconciling ledgers, "
                        "reading positioning..."):
            try:
                results, boundary, crowding = _run_event_engine(
                    event, markets)
            except Exception as e:
                st.error(f"Engine run failed: {e} — cached universe "
                         "files required (data/pit_may26_asia_cache"
                         ".json + MSCI public lists).")
                return
        st.session_state["t1_pack"] = (results, boundary, crowding,
                                       event_name)

    if st.session_state.get("t1_pack") and \
            st.session_state["t1_pack"][3] == event_name:
        results, boundary, crowding, _ = st.session_state["t1_pack"]
        n_calls = sum(len(r["calls"][r["calls"]["call"] != "BLOCKED"])
                      if len(r["calls"]) else 0 for r in results)
        m1, m2, m3 = st.columns(3)
        m1.metric("Markets screened", len(results))
        m2.metric("Live calls", n_calls)
        m3.metric("Ledger violations",
                  sum(len(r["violations"]) for r in results))
        if n_calls == 0:
            st.success(
                "**Zero calls — and that IS the pitch.** Post-SAIR "
                "QIRs are structurally quiet (66 deletions cleared "
                "in May); telling the client 'nothing breaches, "
                "here is who sits near the line' beats a fabricated "
                "list. The boundary watch below is the conversation.")

        st.markdown("### The call sheet")
        for r in results:
            calls = r["calls"]
            live = (calls[calls["call"] != "BLOCKED"]
                    if len(calls) else calls)
            b = boundary.get(r["market"])
            label = (f"{r['market']} — {len(live)} calls, "
                     f"{int(b['at_risk'].sum()) if b is not None else 0} "
                     "boundary names at watch")
            with st.expander(label, expanded=len(live) > 0):
                st.caption(f"GMSR ${r['gmsr_usd'] / 1e9:.1f}B · add "
                           f"hurdle ${r['add_threshold_usd'] / 1e9:.1f}B")
                if len(live):
                    st.dataframe(live, use_container_width=True,
                                 hide_index=True)
                else:
                    st.write("No calls at current caps.")
                if b is not None and len(b):
                    bb = b.copy()
                    bb["crowding"] = [
                        crowding.get(str(t).split(".")[0], "no data")
                        for t in bb["ticker"]]
                    st.markdown("**Boundary watch** (who moves this "
                                "note before announcement)")
                    st.dataframe(bb, use_container_width=True,
                                 hide_index=True)

        st.markdown("### What T-day looks like (measured)")
        hist = results[0]["history"] if results else {}
        hc1, hc2, hc3 = st.columns(3)
        sell = hist.get("MSCI Sell", {})
        if isinstance(sell, dict) and sell.get("available"):
            hc1.metric("T-day volume (deletes)",
                       f"{sell['median']:.0f}x ADV",
                       f"max {sell['max']:.0f}x, n={sell['n']}")
        hc2.metric("Front-run drift", "−4.3%", "MSCI deletes, measured")
        hc3.metric("Reversal by T+5", "~50%", "completion leg planned")

        st.markdown("### How every number is produced")
        from agents.pre_event_marketing import METHODOLOGY
        mcols = {"prediction": "🎯 Predictions (the rules engine)",
                 "crowding": "📊 Crowding color",
                 "flows": "💧 Expected flows",
                 "probabilities": "🎲 The probabilities"}
        for k, label in mcols.items():
            with st.expander(label):
                st.write(METHODOLOGY[k])

        st.markdown("### Why believe this")
        st.dataframe(results[0]["track_record"],
                     use_container_width=True, hide_index=True)

        if event["engine"] == "pit":
            with st.expander("🔓 Reveal the official outcome — "
                             "self-grade this prediction",
                             expanded=False):
                from agents.pre_event_marketing import \
                    grade_predictions
                from scripts.pit_may2026_asia import ACTUAL
                g = grade_predictions(results, ACTUAL)
                st.dataframe(g, use_container_width=True,
                             hide_index=True)
                st.caption(
                    "Same grading discipline as every case study: "
                    "hits, misses, AND false flags shown. Deletion "
                    "false-flags cluster at the cutline (boundary "
                    "survivors ~45-60% each — the watch-zone "
                    "product exists for exactly this). Known named "
                    "misses: 6201.T Toyota Industries (buyout "
                    "deletion — cap unfetchable post-delisting; the "
                    "corporate-action radar's job, rule exists), "
                    "Indonesia FIF cuts (structural — provider "
                    "discretion invisible to public float data). "
                    "The full graded arc (34%→69% across 8 "
                    "iterations) is docs/case_studies/"
                    "PIT_MAY2026_ALL_ASIA.md.")

        md = render_marketing_md(
            event_name, EVENTS[event_name], results, boundary,
            crowding, pd.Timestamp.today().strftime("%Y-%m-%d"))
        st.download_button(
            "📄 Download the client note (.md)", md,
            file_name=f"pre_event_note_{event_name.split(' ')[0]}"
                      f"_{EVENTS[event_name]['ann']}.md",
            key="t1_dl")
        st.caption(
            "The note enforces the honesty rules in the artifact "
            "itself: probabilities on every call, watch zones "
            "labeled, NO-CALL where unvalidated, misses in the "
            "record — the differentiation IS the honesty.")


_MKT_FROM_SUFFIX = {".TW": "Taiwan (TWSE)", ".TWO": "Taiwan (TWSE)",
                    ".HK": "Hong Kong (HKEX)", ".T": "Japan (TSE)",
                    ".KS": "Korea (KRX)", ".SS": "China-A Shanghai",
                    ".SZ": "China-A Shenzhen"}


def _seed_basket_from_pack(pack) -> pd.DataFrame | None:
    """The Step-1 → Step-2 handoff: at-risk boundary names + live
    calls become the draft basket (client typically trades exactly
    these). Quantities default to 1 ADV-day — the trader overwrites
    with the client's real sizes."""
    results, boundary, _, _ = pack
    rows = []
    for r in results:
        calls = r["calls"]
        live = calls[calls["call"] != "BLOCKED"] if len(calls) else calls
        for _, c in live.iterrows():
            rows.append((c["ticker"],
                         "Buy" if c["call"] == "ADD" else "Sell"))
        b = boundary.get(r["market"])
        if b is not None and len(b):
            for _, w in b[b["at_risk"]].iterrows():
                rows.append((w["ticker"],
                             "Sell" if w["side"] == "member"
                             else "Buy"))
    if not rows:
        return None
    out = []
    for t, side in rows:
        mkt = next((m for s, m in _MKT_FROM_SUFFIX.items()
                    if str(t).endswith(s)), "Taiwan (TWSE)")
        out.append([t, mkt, side, 1_000_000, 1_000_000, 30.0])
    df = pd.DataFrame(out, columns=["ticker", "market", "side",
                                    "qty_shares", "adv_shares",
                                    "envelope_pct"])
    return df.drop_duplicates("ticker")


def _tab2_window():
    from agents.event_window import (build_window_plan,
                                     render_window_plan)
    from agents.review_engine import crowding_reads
    st.subheader("Step 2 — The order is live: plan the window")
    st.caption(
        "The client awarded the trade and the basket arrived. Set "
        "THEIR terms, generate the plan, scan the exceptions, send "
        "the strategy memo.")

    default = pd.DataFrame([
        ["1101.TW", "Taiwan (TWSE)", "Sell", 2_500_000, 18_000_000, 30.0],
        ["2002.TW", "Taiwan (TWSE)", "Sell", 55_000_000, 9_500_000, 30.0],
        ["9995.HK", "Hong Kong (HKEX)", "Buy", 3_000_000, 1_400_000, 25.0],
        ["0027.HK", "Hong Kong (HKEX)", "Sell", 9_000_000, 21_000_000, 0.0],
    ], columns=["ticker", "market", "side", "qty_shares",
                "adv_shares", "envelope_pct"])
    if st.session_state.get("t1_pack"):
        if st.button("⬅️ Seed basket from the Step-1 pack "
                     "(calls + at-risk boundary names)", key="t2_seed"):
            seeded = _seed_basket_from_pack(
                st.session_state["t1_pack"])
            if seeded is not None:
                st.session_state["t2_seeded"] = seeded
            else:
                st.info("Step-1 pack has no calls or at-risk names "
                        "to seed — edit the basket directly.")
    basket = st.data_editor(
        st.session_state.get("t2_seeded", default),
        num_rows="dynamic", use_container_width=True, key="t2_basket")

    st.markdown("**The client's terms** (this is their mandate, "
                "not ours)")
    c1, c2, c3, c4 = st.columns(4)
    eff = c1.text_input("Effective date", "2026-09-01", key="t2_eff")
    cap = c2.slider("Participation cap", 0.05, 0.5, 0.25, 0.05,
                    key="t2_cap")
    tmed = c3.number_input("T-multiple (median, measured)",
                           value=16.0, key="t2_tmed")
    tmax = c4.number_input("T-multiple (max)", value=38.0,
                           key="t2_tmax")

    if st.button("Generate window plan", type="primary", key="t2_go"):
        b = basket.dropna(subset=["ticker"])
        envelopes = dict(zip(b["ticker"], b["envelope_pct"]))
        caches = _crowding_caches()
        crowding = {}
        for cache in caches.values():
            crowding.update(crowding_reads(cache, list(b["ticker"])))
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
        st.session_state["t2_plan"] = {"plan": plan, "basket": b,
                                       "eff": eff}

    stored = st.session_state.get("t2_plan")
    if not stored:
        return
    plan, b = stored["plan"], stored["basket"]
    sheet, sched = plan["sheet"], plan["schedule"]

    # ------ the exception row: what the trader scans FIRST
    late = int(sched["status"].str.contains("LATE START").sum())
    tight = int(sheet["borrow"].str.startswith("TIGHT").sum())
    big = int((sheet["auction_footprint_pct"] > 30).sum())
    multi = int((sheet["bucket"] == "MULTI-DAY").sum())
    e1, e2, e3, e4 = st.columns(4)
    e1.metric("MULTI-DAY names", multi)
    e2.metric("LATE starts", late,
              "escalate now" if late else "on time",
              delta_color="inverse" if late else "off")
    e3.metric("Auction footprint >30%", big,
              "client conversation" if big else "clean",
              delta_color="inverse" if big else "off")
    e4.metric("Borrow TIGHT", tight,
              "pre-arrange locates" if tight else "ok",
              delta_color="inverse" if tight else "off")

    st.markdown("**2.2 Liquidity & risk per name**")
    st.dataframe(sheet, use_container_width=True, hide_index=True)
    st.markdown("**2.3a Start schedule**")
    st.dataframe(sched, use_container_width=True, hide_index=True)
    st.markdown("**2.3b Discretion decisions** (approve before "
                "anything trades — the rationale is pre-written, "
                "the judgment is yours)")
    for _, r in plan["decisions"].iterrows():
        with st.expander(f"{r['ticker']} ({r['side']}): "
                         f"{r['decision']}"):
            st.write(r["rationale"])

    md = render_window_plan(
        plan, "Strategy memo — index rebalance basket",
        pd.Timestamp.today().strftime("%Y-%m-%d"),
        notes="Sent per our acknowledgment; discretion decisions "
              "carry their best-ex rationale; daily progress notes "
              "follow for multi-day names.")
    st.download_button("📄 Download client strategy memo (.md)", md,
                       file_name="strategy_memo.md", key="t2_dl")
    st.caption("Plan stored — Step 3 reads it for the T-day watch "
               "list; Step 4 grades it.")


def _tab5_time_machine():
    """Go back to any keyed review, stand on any day inside its
    window, and see the Step-2 state with ONLY data <= that day.
    Logic: agents/time_machine.py (structural PIT gate)."""
    from agents.time_machine import (asof_panel, asof_step2,
                                     ensure_window, event_panel,
                                     list_events)
    st.subheader("🕰️ Step-2 Time Machine — any review, any day, "
                 "no peeking")
    st.caption(
        "Pick a keyed review (all TW50 quarters 2016-2026 + the "
        "2026 MSCI events), fetch its official window data if "
        "needed, then scrub the as-of day: every table and chart "
        "is built from data ≤ that day — the future is never "
        "loaded, not merely hidden. Formulas: "
        "WINDOW_STUDY_2021_2026.md §0.")
    ev = list_events()
    ev_disp = ev[ev["n_changes"] > 0]
    label = st.selectbox(
        "Review event", ev_disp.apply(
            lambda r: f"{r['event']}  ({r['n_changes']} changes, "
                      f"window cached {r['days_cached']})",
            axis=1), key="tm_event")
    event = label.split("  (")[0]
    row = ev_disp[ev_disp["event"] == event].iloc[0]
    have, need = (int(x) for x in row["days_cached"].split("/"))
    if have < need:
        st.info(f"Window data: {have}/{need} sessions cached. "
                "Fetching pulls official TWSE files "
                "(quotes/shorts/foreign) for this window.")
        if st.button("⬇️ Fetch official window data (~30-90s)",
                     key="tm_fetch"):
            with st.spinner("Backfilling from TWSE official "
                            "endpoints (threaded)..."):
                ensure_window(event)
            st.rerun()
        return
    if st.session_state.get("tm_cache_key") != event:
        st.session_state["tm_panel"] = event_panel(event)
        st.session_state["tm_cache_key"] = event
    panel = st.session_state["tm_panel"]
    if not len(panel):
        st.warning("No names computable for this window (data gaps "
                    "at vintage — stated, not padded).")
        return
    days = sorted(panel["date"].unique())
    asof = st.select_slider(
        "As-of day (announcement is day 0, after the close)",
        options=days, value=days[min(2, len(days) - 1)],
        key="tm_asof")
    p = asof_panel(panel, asof)

    st.markdown(f"**Step-2 decision state as of {asof} "
                f"(day {int(p['k'].max())} of {len(days)})**")
    s2 = asof_step2(panel, asof)
    st.dataframe(
        s2[["code", "side", "fav_drift_bps", "t_mult_today",
            "short_build", "A3_gate", "crowding_decision"]],
        use_container_width=True, hide_index=True)
    with st.expander("Decision rationales (best-ex evidence)"):
        for _, r in s2.iterrows():
            st.write(f"**{r['code']}** ({r['side']}): "
                     f"{r['rationale']}")

    import plotly.graph_objects as go
    METRICS = {"Drift WITH the flow (bps)": "fav_drift_bps",
               "Volume multiple vs baseline": "t_mult",
               "Short-interest change since ann (%)":
                   "short_chg_pct",
               "Cumulative foreign net (x ADV)":
                   "foreign_cum_x_adv"}
    mlabel = st.selectbox("Metric evolution (up to the as-of day "
                          "only)", list(METRICS), key="tm_metric")
    col = METRICS[mlabel]
    fig = go.Figure()
    for code, g in p.groupby("code"):
        g = g.sort_values("date")
        fig.add_trace(go.Scatter(
            x=g["date"], y=g[col],
            name=f"{code} ({g['side'].iloc[0]})",
            mode="lines+markers", marker=dict(size=4)))
    fig.update_layout(height=400,
                      margin=dict(l=10, r=10, t=30, b=10),
                      yaxis_title=mlabel,
                      title=f"{mlabel} — through {asof}")
    st.plotly_chart(fig, use_container_width=True)
    st.caption(
        "What you CANNOT know yet on this day: the remaining "
        "window's drift, the print, and the official outcome — "
        "the chart ends at your as-of day because the data does. "
        "Scrub forward to watch the information arrive.")


def _playbook_expander():
    """Session 9i: the T-day situations playbook — midday
    observables -> measured outcomes, per cell."""
    import json
    from pathlib import Path
    p = Path("data/tday_playbook.json")
    if not p.exists():
        return
    with st.expander("📖 Situations playbook — 'you are here at "
                     "noon → history says' (96 T-days, 24 events)"):
        blob = json.loads(p.read_text())
        c1, c2, c3 = st.columns(3)
        side = c1.selectbox("Side", ["Sell", "Buy"], key="pb_side")
        tape = c2.selectbox("Tape by noon",
                            ["WITH-flow", "AGAINST-flow"],
                            key="pb_tape")
        vol = c3.selectbox("AM volume", ["HEAVY", "NORMAL"],
                           key="pb_vol")
        cell = next((c for c in blob["cells"]
                     if c["side"] == side and c["am_tape"] == tape
                     and c["am_vol"] == vol), None)
        if not cell:
            st.info("No cell found.")
        elif cell["label"] == "DATA-THIN":
            st.warning(f"DATA-THIN cell (n={cell['n']}, "
                       f"{cell['n_events']} events) — no "
                       "recommendation by rule.")
        else:
            m = st.columns(4)
            m[0].metric("PM drift (med)", f"{cell['pm_fav']:+.0f} bp")
            m[1].metric("Print gap (med)",
                        f"{cell['gap_fav']:+.0f} bp")
            m[2].metric("P(print favorable)",
                        f"{cell['p_gap_fav']:.0%}")
            m[3].metric("T+1 reversal (med)",
                        f"{cell['t1_rev']:+.0f} bp")
            st.caption(f"n={cell['n']} name-days across "
                       f"{cell['n_events']} events | realized "
                       f"auction share med {cell['share']}. Full "
                       "reactions: docs/case_studies/"
                       "TDAY_PLAYBOOK.md")


def _tab3_tday():
    from agents.event_window import indicative_read
    from agents.pt_dealer import AUCTION_CUTOFFS
    st.subheader("Step 3 — T-day: the cascade cockpit")
    st.caption(
        "The day is the disciplined execution of Step 2's plan. "
        "Morning check → lunch checkpoint → the close read per "
        "market. Live feeds are PROTOCOL; the logic is the desk "
        "logic.")
    _playbook_expander()

    stored = st.session_state.get("t2_plan")

    # ------ 3.1 morning check: the watch list from the plan
    st.markdown("### 3.1 Morning check")
    if stored:
        sheet = stored["plan"]["sheet"]
        sched = stored["plan"]["schedule"]
        watch = sheet[
            sheet["limit_risk"].str.contains("LOCK")
            | sheet["borrow"].str.startswith("TIGHT")
            | (sheet["auction_footprint_pct"] > 30)].copy()
        late = sched[sched["status"].str.contains("LATE START")]
        w1, w2 = st.columns(2)
        w1.metric("Names on the watch list", len(watch),
                  "contingency notes attached" if len(watch)
                  else "clean")
        w2.metric("Working legs due today",
                  int((sched["status"].str.contains("start")).sum()))
        if len(watch):
            st.dataframe(
                watch[["ticker", "side", "bucket", "limit_risk",
                       "borrow", "auction_footprint_pct"]],
                use_container_width=True, hide_index=True)
        if len(late):
            st.error("LATE-START names — escalate before the open: "
                     + ", ".join(late["ticker"]))
        mkts = sorted(stored["basket"]["market"].unique())
    else:
        st.info("No Step-2 plan stored — generate one in the "
                "previous tab and the watch list appears here. "
                "Showing the full cascade meanwhile.")
        mkts = list(AUCTION_CUTOFFS)

    st.markdown("**The run-sheet (your basket's markets, close "
                "cutoffs local time)**")
    rs = (pd.DataFrame(AUCTION_CUTOFFS).T.reset_index()
          .rename(columns={"index": "market"}))
    st.dataframe(rs[rs["market"].isin(mkts)],
                 use_container_width=True, hide_index=True)

    # ------ 3.2 the lunch checkpoint
    st.markdown("### 3.2 Lunch checkpoint — is the tape confirming "
                "the T-multiple?")
    l1, l2, l3 = st.columns(3)
    lexp = l1.number_input("Expected T-multiple (plan)", value=16.0,
                           key="t3_lexp")
    lobs = l2.number_input("Volume run-rate so far (x same-time "
                           "normal)", value=8.0, key="t3_lobs")
    lenv = l3.slider("Envelope remaining % (lunch)", 0, 50, 30,
                     key="t3_lenv")
    lr = indicative_read(lexp, lobs, "Sell", lenv)
    ltone = (st.error if "THIN" in lr["read"] else
             st.success if "RICH" in lr["read"] else st.info)
    ltone(f"**Run-rate {lr['read'].replace('x expected', 'x pace')}**"
          f" → resize the auction orders NOW, not at the cutoff: "
          f"{lr['action']}")
    st.caption("Rule from the design doc: if the tape says 8x, not "
               "16x, auction sizing changes at lunch — the proposal "
               "shows its arithmetic, the dealer decides.")

    # ------ 3.3 the close sequence read
    st.markdown("### 3.3 The close read (TW 13:25–13:30 indicative "
                "style) — the day's ONE real-time decision")
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
    st.caption(f"Why: {r['rationale']} (ratio {r.get('ratio', '-')}).")

    with st.expander("Auction-share derivation (the free-data "
                     "trick) — check any ticker"):
        tk = st.text_input("Ticker (TW derives daily−Σbars; HK/JP "
                           "read the last bar)", "2330.TW",
                           key="t3_tk")
        if st.button("Derive auction share", key="t3_go"):
            try:
                import yfinance as yf
                h5 = yf.Ticker(tk).history(period="5d", interval="5m")
                hd = yf.Ticker(tk).history(period="5d", interval="1d")
                day = h5[h5.index.date == h5.index.date[-1]]
                dv = float(hd["Volume"].iloc[-1])
                bars = float(day["Volume"].sum())
                if tk.endswith(".TW") or tk.endswith(".TWO"):
                    share = (max(dv - bars, 0) / dv if dv
                             else float("nan"))
                    how = "derived: (daily − Σ intraday bars) / daily"
                else:
                    share = (float(day["Volume"].iloc[-1]) / dv
                             if dv else float("nan"))
                    how = "read: last bar / daily"
                st.metric(f"Close-auction share — {tk} (latest "
                          "session)", f"{share:.1%}")
                st.caption(f"{how}; daily {dv:,.0f} vs bars "
                           f"{bars:,.0f}. Odd-lot noise included — "
                           "stated, small.")
            except Exception as e:
                st.warning(f"Fetch failed: {e}")


def _post_event_expander():
    """Session 9i: the NO-FILLS post-event pack (benchmark strips,
    strategy leaderboard, estimate ledger, reversal paths)."""
    import json
    from pathlib import Path
    p = Path("data/post_event_may26.json")
    if not p.exists():
        return
    with st.expander("🌙 Post-event pack (no fills needed) — "
                     "May-2026 demo: strips, leaderboard, estimate "
                     "ledger, reversal paths"):
        d = json.loads(p.read_text())
        rows = [r for r in d["names"] if "note" not in r]
        st.dataframe(
            [{"name": f"{r['side']} {r['code']}",
              "close": r["official_close"],
              "day VWAP": r["day_vwap_exact"],
              "gap bp": r["gap_bps"],
              "auction share": r["auction_share"],
              "winner": r["strategies"]["winner"],
              "gap in band": r["grades"].get("gap_in_band"),
              "T-mult": r["grades"].get("t_mult_realized"),
              "T+3 reversal bp": (r["reversal_T1_T5"][2]
                                  if r.get("reversal_T1_T5")
                                  and len(r["reversal_T1_T5"]) > 2
                                  else None)}
             for r in rows], use_container_width=True,
            hide_index=True)
        st.caption("The client self-grades fills against the strip; "
                   "our estimates are graded in the 'gap in band' "
                   "column — misses shown (1402). Full pack: "
                   "docs/case_studies/POST_EVENT_PACK_MAY2026.md")


def _tab4_posttrade():
    from agents.execution_insights import (discretion_counterfactual,
                                           render_debrief,
                                           reversal_grade,
                                           tca_vs_estimate,
                                           update_priors)
    st.subheader("Step 4 — Post-trade: prove it, grade it, feed it "
                 "back")
    _post_event_expander()
    st.caption(
        "Enter the fills and realized paths; get the "
        "TCA-vs-estimate reconciliation, the discretion "
        "counterfactual, the reversal grade — then download the "
        "client debrief. This document is next quarter's pitch.")

    stored = st.session_state.get("t2_plan")
    if stored and st.button("⬅️ Seed from the Step-2 plan (tickers, "
                            "sides, decisions)", key="t4_seed"):
        b = stored["basket"]
        st.session_state["t4_fills_seed"] = pd.DataFrame({
            "ticker": b["ticker"], "side": b["side"],
            "qty_shares": b["qty_shares"],
            "avg_px": 100.0, "close_px": 100.0,
            "est_cost_bps": 12.0})
        dec = stored["plan"]["decisions"]
        st.session_state["t4_cf_seed"] = pd.DataFrame({
            "ticker": dec["ticker"], "side": dec["side"],
            "decision": dec["decision"],
            "worked_frac": [0.3 if str(d).startswith(("WORK",
                                                      "PRE-POS"))
                            else 0.0 for d in dec["decision"]],
            "pre_close_drift_bps": 0.0})
        st.caption("Seeded — overwrite prices/drifts with the "
                   "realized numbers.")

    st.markdown("**Fills (TCA vs pre-trade estimate)**")
    tca_default = pd.DataFrame([
        ["2324.TW", "Sell", 1_000_000, 108.41, 108.50, 12.0],
        ["1102.TW", "Sell", 1_000_000, 33.42, 33.45, 12.0],
    ], columns=["ticker", "side", "qty_shares", "avg_px", "close_px",
                "est_cost_bps"])
    fills = st.data_editor(
        st.session_state.get("t4_fills_seed", tca_default),
        num_rows="dynamic", use_container_width=True, key="t4_fills")

    st.markdown("**Discretion outcomes (choice vs realized drift)**")
    cf_default = pd.DataFrame([
        ["2324.TW", "Sell", "WAIT — MOC the full order", 0.0, 2274.0],
        ["2633.TW", "Sell", "WAIT — MOC the full order", 0.0, -710.0],
        ["1101.TW", "Sell", "WORK AHEAD 30%", 0.3, -150.0],
    ], columns=["ticker", "side", "decision", "worked_frac",
                "pre_close_drift_bps"])
    cf_in = st.data_editor(
        st.session_state.get("t4_cf_seed", cf_default),
        num_rows="dynamic", use_container_width=True, key="t4_cf")

    st.markdown("**Reversal vs the crowding read**")
    rev_default = pd.DataFrame([
        ["2324.TW", "LOW", -76.0, 44.0],
        ["2633.TW", "LOW", 88.0, -14.0],
    ], columns=["ticker", "crowding_band", "t_move_bps",
                "post_reversal_bps"])
    rev_in = st.data_editor(rev_default, num_rows="dynamic",
                            use_container_width=True, key="t4_rev")

    if st.button("Grade the event", type="primary", key="t4_go"):
        tca = tca_vs_estimate(fills.dropna(subset=["ticker"]))
        cf = discretion_counterfactual(cf_in.dropna(subset=["ticker"]))
        rev = reversal_grade(rev_in.dropna(subset=["ticker"]))
        # ------ the headline row: what the client hears first
        g1, g2, g3, g4 = st.columns(4)
        g1.metric("Realized (qty-wtd)",
                  f"{tca.attrs.get('portfolio_realized_bps', 0)} bps")
        delta = tca.attrs.get("portfolio_vs_estimate_bps", 0)
        g2.metric("vs our estimate", f"{delta:+.1f} bps",
                  "kept our word" if abs(delta) <= 6 else
                  ("beat it" if delta < 0 else "explain it"),
                  delta_color="inverse")
        ok = int((cf["verdict"] == "CORRECT").sum())
        graded = int(cf["verdict"].isin(["CORRECT",
                                         "INCORRECT"]).sum())
        g3.metric("Discretion calls right",
                  f"{ok}/{graded}" if graded else "n/a")
        g4.metric("Crowding implications",
                  rev.attrs.get("hit_rate", "n/a"))
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
    t1, t2, t3, t4, t5 = st.tabs([
        "1️⃣ Win the trade", "2️⃣ The window (ann → T)",
        "3️⃣ T-day cascade", "4️⃣ Post-trade & learning",
        "🕰️ Time Machine"])
    with t1:
        _tab1_win_the_trade()
    with t2:
        _tab2_window()
    with t3:
        _tab3_tday()
    with t4:
        _tab4_posttrade()
    with t5:
        _tab5_time_machine()
