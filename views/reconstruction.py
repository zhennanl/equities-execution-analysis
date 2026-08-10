"""Page 3 — Review Reconstruction (PIT) (c-110).

Pick a review; see MSCI's decision rebuilt with the data and
rules OF THAT DAY (edition-mined GMSR + disclosed price date;
PIT caps at that date's FX), per-move verdicts, and the
grading (would our rules have called it). The backtest table
across all reviews 2018->May-26 is the calibration base for
the prediction model.
"""
import json
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]


def render():
    import pandas as pd
    st.title("Review Reconstruction — point-in-time")
    st.caption("Taiwan (other markets follow the activation "
               "path). Every number uses the ACTUAL rulebook "
               "keys of that review: edition-mined GMSR + the "
               "disclosed Price Cutoff Date, PIT caps at that "
               "month's FX.")

    sp = ROOT / "data" / "reconstruct_summary.json"
    if sp.exists():
        summ = pd.DataFrame(json.loads(sp.read_text(encoding="utf-8")))
        st.subheader("The backtest (2018 → May-26)")
        st.dataframe(summ, use_container_width=True,
                     hide_index=True, height=300)
        ok = summ.dropna(subset=["del_hits"]) \
            if "del_hits" in summ else summ
        if len(ok) and "del_hits" in ok:
            h = int(ok.del_hits.sum())
            m = int(ok.del_misses.sum())
            fa = int(ok.false_alarms.sum())
            c1, c2, c3 = st.columns(3)
            c1.metric("Deletion capture",
                      f"{h}/{h + m} ({h / max(h + m, 1):.0%})")
            c2.metric("False alarms (total)", fa)
            c3.metric("False-alarm interpretation",
                      "MSCI's discretion, measured")
        st.caption("False alarms = names below the floor that "
                   "MSCI did NOT delete — the buffers/"
                   "discretion gap our prediction model must "
                   "learn. QIR misses reflect rank-based QIR "
                   "migration rules our floor model "
                   "approximates (registered refinement).")

    revs = sorted([p.stem.replace("TW_", "") for p in
                   (ROOT / "data" / "reconstruct").glob(
                       "TW_*.json")],
                  key=lambda r: (int("20" + r[-2:]),
                                 {"Feb": 0, "May": 1, "Aug": 2,
                                  "Nov": 3}[r[:3]]))
    if not revs:
        st.info("Run: py scripts\\review_reconstruct.py batch")
        return
    pick = st.selectbox("Review", list(reversed(revs)))
    o = json.loads((ROOT / "data" / "reconstruct" /
                    f"TW_{pick}.json").read_text(encoding="utf-8"))
    k = o["keys"]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("GMSR (actual)", f"${k['gmsr_dm']}B",
              k["source"][:22])
    c2.metric("Price date (disclosed)", k["price_date"])
    c3.metric("Delete floor / Add bar",
              f"${k['floor']}B / ${k['bar']}B")
    c4.metric("FX used", o["fx_used"])
    for lab in o["labels"]:
        st.caption("⚠ " + lab)
    st.subheader("Per-move verdicts")
    st.dataframe(pd.DataFrame(o["verdicts"]),
                 use_container_width=True, hide_index=True)
    g = o["grading"]
    st.subheader("Grading — our rules vs MSCI's decision")
    cc1, cc2, cc3 = st.columns(3)
    cc1.metric("Hits", len(g["hits"]),
               ", ".join(g["hits"][:4]) or None)
    cc2.metric("Misses", len(g["misses"]),
               ", ".join(g["misses"][:4]) or None)
    cc3.metric("False alarms", len(g["false_alarms"]))
    with st.expander("The full below-floor pool that review"):
        st.json(g["pool"])
