"""Aug-2026 MSCI Taiwan Index Review — the single-purpose site
(c-85). Everything on this page is loaded from committed data
artifacts; declared calls carry their timestamps; nothing is
computed live so the page shows exactly what was on record
before the announcement.
"""
import datetime as dt
import json
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]

ANN = dt.date(2026, 8, 12)
EFF = dt.date(2026, 8, 31)


@st.cache_data(show_spinner=False)
def _load():
    def j(name):
        p = ROOT / "data" / name
        return json.loads(p.read_text()) if p.exists() else {}
    return {"cut": j("aug26_cutoff_calc.json"),
            "walk": j("cutoff_walk_v2.json"),
            "adv": j("preann_advisory_aug26.json"),
            "clock": j("anticipation_clock.json"),
            "sbl": j("sbl_history.json")}


def _latest_sbl(sbl, codes):
    days = sorted(d for d, v in sbl.items() if v)
    out = {}
    for d in reversed(days[-10:]):
        for c in codes:
            if c not in out and c in sbl[d]:
                out[c] = (d, sbl[d][c][1])
    return out


def render():
    d = _load()
    today = dt.date.today()
    st.title("MSCI Aug-2026 Index Review — Taiwan")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Announcement (TW)", ANN.isoformat(),
              f"T-{max((ANN - today).days, 0)} days")
    c2.metric("Effective close", EFF.isoformat(),
              f"{max((EFF - today).days, 0)} days")
    c3.metric("Effective cutoff (corridor-clamped)", "$9.44B",
              "corridor BINDS (Q46)")
    c4.metric("Denominator frames", "$3,745B / $3,883B",
              "+3.7% gap — inside banding")
    st.caption("Single-purpose site for this review. Prior "
               "platform preserved at backup/website_v1_20260806 "
               "(set app.py LEGACY=True to restore).")

    # ---- the declared calls -------------------------------
    st.header("The declared calls (timestamped, grade on "
              "announcement)")
    sh = d["cut"].get("shadow_add_call", {})
    st.markdown(f"**Declared:** {sh.get('declared', 'n/a')} — "
                f"{sh.get('engine', '')}")
    for call in sh.get("calls", []):
        with st.container(border=True):
            st.subheader(f"ADD — {call['code']} "
                         f"{call.get('name', '')}")
            st.markdown(f"**{call['strength']}**")
            st.markdown(call.get("why", ""))
    st.markdown("Post-correction check (c-79): the corrected "
                "walk RAISED the add bar to 1.5 x 9.44 = "
                "\\$14.16B — 2408 clears at \\$46.7B full cap: "
                "the call survives its third frame.")

    cols = st.columns(2)
    with cols[0]:
        st.subheader("Add candidates (gate verdicts)")
        rows = [{"code": c.get("code"),
                 "verdict": c.get("verdict", "")}
                for c in d["cut"].get("add_candidates", [])]
        st.dataframe(rows, use_container_width=True,
                     hide_index=True)
    with cols[1]:
        st.subheader("Delete pool (members vs the $6.29B "
                     "buffer floor)")
        dels = [{"code": c.get("code"),
                 "full cap $B": c.get("cap_usd_b")}
                for c in d["cut"].get("delete_candidates", [])]
        st.dataframe(dels, use_container_width=True,
                     hide_index=True)
        st.caption("Floor = 2/3 x corridor-clamped cutoff. "
                   "Names below it are at risk; MSCI discretion "
                   "and the blind price-date band apply "
                   "(cadence lesson, Q21).")

    # ---- the derivation ----------------------------------
    st.header("The cutoff, derived (corrected walk, c-79)")
    w = d["walk"].get("base", {})
    st.markdown(
        "Reference \\$15.75B x 1.042 = \\$16.41B (DM) -> EM = "
        "half = \\$8.21B -> corridor **[\\$4.10B, \\$9.44B]**. "
        "Walk (rank FULL cap, accumulate FLOAT, 85% of "
        f"\\${w.get('denominator_busd', '—')}B): crossing at "
        f"rank {w.get('cross_rank', '—')} = "
        f"\\${w.get('cutoff_full_cap_busd', '—')}B full cap — "
        "ABOVE the corridor ceiling in every float frame -> "
        "**the corridor binds**: effective cutoff ~\\$9.44B, "
        "delete floor \\$6.29B, add bar \\$14.16B.")
    with st.expander("Frames + honesty labels"):
        st.json({"frames": d["walk"].get("frames"),
                 "float_band": d["walk"].get("band"),
                 "census_coverage":
                 d["walk"].get("census_coverage"),
                 "declared_proxies": "1.042 DM move (+/-2pt), "
                 "FX 29.5, census partial, default floats "
                 "12.4% of D"})

    # ---- positioning monitor ------------------------------
    st.header("Positioning monitor (standing borrow — the "
              "PRIMARY reading, per the anticipation clock)")
    ck = d["clock"]
    st.markdown(
        f"Historical calibration (n={ck.get('n_del_curves', '—')}"
        f" deletions): **~{round(ck.get('median_build_at_ann_advdays', 0), 1)} "
        "ADV-days of excess borrow is already in place BY "
        "announcement day**; the ann->eff window adds ~nothing "
        "at the median. Watch the LEVEL now, not the window "
        "build.")
    watch = [c.get("code") for c in
             d["cut"].get("delete_candidates", [])][:10]
    latest = _latest_sbl(d["sbl"], watch)
    rows = [{"code": c, "as of": latest.get(c, ("—",))[0],
             "SBL balance (M sh)":
             round(latest[c][1] / 1e6, 1)
             if c in latest else None}
            for c in watch]
    st.dataframe(rows, use_container_width=True,
                 hide_index=True)
    st.caption("TPEx-listed names (3529, 8069, 3293...) show "
               "None — TWSE SBL covers the main board only; "
               "TPEx feed = registered gap, roadmap item 11.")

    # ---- liquidity preview --------------------------------
    st.header("Effective-day liquidity preview (per-name "
              "forced flow + print ranges)")
    for card in d["adv"].get("cards", []):
        with st.expander(f"{card['code']} ({card['side']}) — "
                         f"{card.get('status', '')}"):
            st.json({k: card[k] for k in
                     ("adv_sh_m", "float_sh_m", "ff",
                      "forced_flow_m_sh",
                      "expected_auction_share",
                      "sbl_adv_days", "print_range_x_adv",
                      "print_methods") if k in card})

    # ---- grading ledger -----------------------------------
    st.header("Grading ledger")
    st.markdown(
        "- **Shadow add call 2408** — grades on the "
        "announcement (declared T-6).\n"
        "- **Delete pool (buffer-floor list)** — graded "
        "against the published change list.\n"
        "- **Print ranges (M1-M4)** — graded at the Aug-31 "
        "close (conformal coverage grading queued).\n"
        "- **H16/H17 + registry v5 (H18-H26)** — graded per "
        "protocol on forward events.\n"
        "- **Split table + RED alert precision (T-day "
        "decider)** — graded after Aug-31.\n\n"
        "Misses ship. The ledger stays on this page after "
        "grading.")
    st.caption("Provenance: every number above comes from a "
               "committed artifact (aug26_cutoff_calc, "
               "cutoff_walk_v2, preann_advisory_aug26, "
               "anticipation_clock, sbl_history). Docs: "
               "INDEX_REVIEW_EXPLAINED_QA.md Q22-Q53.")
