"""Page 5 — Reg-Watch (JD bullet 5: market-specific regulations).

Three tabs mirroring the three layers: current rules (versioned
registry), notice triage (daily digest), and the pending-approval queue
— the human gate through which every rule change must pass. Logic lives
in agents/reg_watch.py; this file only renders.
"""
import json

import pandas as pd
import streamlit as st

from agents import reg_watch as rw


def render():
    st.header("🛡️ Reg-Watch — market rules & regulatory change")
    st.caption(
        "Single source of truth for the rules the desk trades on. "
        "Nothing auto-mutates: every change is proposed with a source, "
        "approved by a human, and version-stamped into audit packs.")

    reg = rw.load_registry()
    t1, t2, t3 = st.tabs(["📖 Current rules", "📰 Notice triage",
                          "✅ Pending approvals"])

    with t1:
        cat = st.selectbox("Category", ["limit_band", "auction_cutoff",
                                        "market_reg"])
        df = rw.current(reg, category=cat)
        if not df.empty:
            show = df[["market", "value", "version", "effective_date",
                       "source", "approved_by"]].sort_values("market")
            st.dataframe(show, use_container_width=True, hide_index=True)
        st.caption(f"Registry version {rw.registry_version(reg)} — this "
                   "hash is stamped into every audit pack "
                   "(pt_dealer.rules_version).")
        mkt = st.selectbox("History for market",
                           sorted(df["market"]) if not df.empty else [])
        if mkt:
            st.dataframe(rw.history(reg, cat, mkt), hide_index=True,
                         use_container_width=True)

    with t2:
        st.markdown(
            "Feeds: " + " · ".join(
                f"**{k}** ({v['status'].split(' ')[0]})"
                for k, v in rw.NOTICE_SOURCES.items()))
        cache_path = rw.REGISTRY_PATH.parent / "reg_notices_cache.json"
        if cache_path.exists():
            cache = json.loads(cache_path.read_text(encoding="utf-8"))
            day = sorted(cache.keys())[-1]
            tri = rw.triage_notices(cache[day]["notices"])
            basket_raw = st.text_input(
                "Working-basket names (comma-separated, optional) — "
                "boosts stories touching YOUR names", "")
            basket = [b.strip() for b in basket_raw.split(",")
                      if b.strip()] or None
            stories = sorted(
                (rw.score_story(s, basket)
                 for s in rw.cluster_stories(tri)),
                key=lambda s: -s["score"])
            n_raw = len(tri)
            st.caption(f"Latest fetch {day}: {n_raw} raw notices → "
                       f"{len(stories)} stories. Traders read stories; "
                       "notices are one click deeper.")
            tiers = st.multiselect("Tier", ["FLASH", "NOTABLE",
                                            "ROUTINE"],
                                   default=["FLASH", "NOTABLE"])
            for s in [x for x in stories if x["tier"] in tiers][:25]:
                badge = {"FLASH": "🔴", "NOTABLE": "🟡",
                         "ROUTINE": "⚪"}[s["tier"]]
                with st.expander(
                        f"{badge} {s['tier']} · [{s['source']}] "
                        f"{s['headline'][:100]}  (score {s['score']})"):
                    st.markdown(f"**Why it matters:** {s['impact']}")
                    st.caption("Scoring: " + "; ".join(s["reasons"]))
                    for l in s["links"]:
                        st.markdown(f"- [{l['date']}] "
                                    f"[{l['title'][:110]}]({l['url']})")
            st.download_button(
                "⚡ Flash brief (markdown)",
                rw.flash_brief([dict(s) for s in stories], 6, basket)
                or "no FLASH/NOTABLE stories",
                file_name=f"reg_flash_{day}.md")
            st.download_button(
                "Full daily digest (markdown)",
                rw.daily_digest(tri, reg, date=day),
                file_name=f"reg_digest_{day}.md")
        else:
            st.info("No notice cache yet — run "
                    "`python scripts/fetch_reg_notices.py` (TWSE/JPX/NSE "
                    "live; other feeds PROTOCOL from this environment).")
        st.caption("Classifier: deterministic multilingual keyword "
                   "engine (zh/ja/ko/en). LLM summaries plug in via "
                   "`llm_summarize_hook` only where a desk-approved "
                   "endpoint exists — a slot, not a dependency.")

    with t3:
        pend = rw.pending(reg)
        if pend.empty:
            st.success("No pending proposals.")
        else:
            for _, p in pend.iterrows():
                with st.container(border=True):
                    st.markdown(
                        f"**{p['proposal_id']}** — {p['category']} / "
                        f"{p['market']}\n\n{p['old_value']} → "
                        f"**{p['new_value']}**\n\nSource: {p['source']}")
                    c1, c2 = st.columns(2)
                    if c1.button("Approve", key=f"a{p['proposal_id']}"):
                        rw.approve(reg, p["proposal_id"],
                                   approver="dealer")
                        rw.save_registry(reg)
                        st.rerun()
                    if c2.button("Reject", key=f"r{p['proposal_id']}"):
                        rw.reject(reg, p["proposal_id"], "dealer",
                                  "rejected via UI")
                        rw.save_registry(reg)
                        st.rerun()
        with st.expander("Propose a change manually"):
            cat2 = st.selectbox("Category ", ["limit_band",
                                              "auction_cutoff",
                                              "market_reg"], key="pc")
            mkts = sorted({e["market"] for e in reg["entries"]})
            mkt2 = st.selectbox("Market", mkts, key="pm")
            val = st.text_area("New value (JSON)", "{}")
            src = st.text_input("Source (notice URL / circular no.)")
            if st.button("Submit proposal") and src:
                try:
                    rw.propose_change(reg, cat2, mkt2, json.loads(val),
                                      source=src)
                    rw.save_registry(reg)
                    st.rerun()
                except json.JSONDecodeError:
                    st.error("Value must be valid JSON.")
