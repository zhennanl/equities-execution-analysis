"""Page 4 — "How the prediction works", the plain-English
walkthrough (c-115).

Renders scripts/walkthrough_story.story(). This module holds NO
facts: every number on screen comes from the story object, which
comes from the engine's own output. Point it at another market
and the page rewrites itself.

Two audiences, per Bill's brief: the main column is written for
a reader outside finance; each step carries a collapsed "For the
desk" block with the rulebook citations and error bars, and an
always-visible honesty line.

One interactive lever (step 5): drag the size threshold and
watch companies cross it. That is the single idea the whole
method rests on, so it is the one thing the reader gets to
touch.
"""
import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))


@st.cache_data(show_spinner=False)
def _story(market, review):
    from walkthrough_story import story
    return story(market, review)


def _numbers(nums):
    if not nums:
        return
    cols = st.columns(len(nums))
    for c, n in zip(cols, nums):
        c.metric(n["label"], n["value"])
        if n.get("note"):
            c.caption(n["note"])


def _lever(s):
    """Step 5's interactive line."""
    import pandas as pd
    import plotly.graph_objects as go
    k = s["keys"]
    # show the BOTTOM of the ladder — the decision happens
    # there. Including TSMC at $1.6tn would compress every
    # borderline name into one pixel.
    cand = [u for u in s["universe"] if u["cap"] <= 60]
    moved = [u for u in cand if u.get("actual")]
    small = sorted(cand, key=lambda r: r["cap"])[:30]
    seen, uni = set(), []
    for u in small + moved:
        if u["code"] not in seen:
            seen.add(u["code"])
            uni.append(u)
    if not uni:
        return
    lo = max(0.5, min(u["cap"] for u in uni))
    hi = max(u["cap"] for u in uni)
    default = float(k["floor"])
    thr = st.slider(
        "Drag the size line (US$ billions)",
        min_value=round(lo, 1), max_value=round(hi, 1),
        value=float(min(max(default, lo), hi)), step=0.1,
        help="MSCI's floor for this review sits at "
             f"${k['floor']}B. Move the line and watch which "
             "companies fall below it.")
    d = pd.DataFrame(uni)
    d["side"] = ["below the line" if c < thr else "above"
                 for c in d.cap]
    d["was"] = [{"DEL": "MSCI removed it",
                 "ADD": "MSCI added it"}.get(a, "MSCI left it "
                                                "alone")
                for a in d.actual]
    fig = go.Figure()
    for side, col in [("below the line", "#c0392b"),
                      ("above", "#95a5a6")]:
        g = d[d.side == side]
        fig.add_bar(x=g.cap, y=g.name, orientation="h",
                    marker_color=col, name=side,
                    hovertext=[f"{n}<br>${c}B<br>{w}" for n, c, w
                               in zip(g.name, g.cap, g.was)],
                    hoverinfo="text")
    fig.add_vline(x=thr, line_color="#1f4e79", line_width=3)
    fig.update_layout(
        height=max(320, 15 * len(d)), barmode="stack",
        yaxis=dict(autorange="reversed", title=""),
        xaxis_title="size on the photograph day (US$ bn)",
        margin=dict(l=0, r=0, t=10, b=0), showlegend=False)
    st.plotly_chart(fig, use_container_width=True)
    below = d[d.cap < thr]
    hit = int((below.actual == "DEL").sum())
    tot_del = int((d.actual == "DEL").sum())
    c1, c2, c3 = st.columns(3)
    c1.metric("Companies below your line", len(below))
    if tot_del:
        c2.metric("Actual removals captured",
                  f"{hit}/{tot_del}")
        c3.metric("Companies you would flag wrongly",
                  int(len(below) - hit))
        st.caption(
            "Move the line down and the false alarms disappear "
            "— along with the real removals. Move it up and you "
            "catch everything, at the cost of flagging half the "
            "index. There is no setting that is simply right; "
            "that trade-off IS the problem.")
    else:
        c2.metric("MSCI's floor", f"${k['floor']}B")
        c3.metric("Outcome", "not announced yet")


def render():
    st.title("How we predict MSCI index changes")
    st.caption(
        "A walkthrough of the point-in-time method, written to "
        "be followed with no finance background. Every number "
        "on this page is read from the prediction engine's own "
        "output — nothing here is typed by hand.")

    c1, c2 = st.columns([1, 2])
    market = c1.selectbox("Market", ["Taiwan"],
                          help="Other APAC markets appear here "
                               "as their reconstructions are "
                               "built — the walkthrough itself "
                               "needs no new writing.")
    review = c2.radio(
        "Example", ["May26", "Aug26"], horizontal=True,
        format_func=lambda r: (
            "May 2026 — solved (learn the method with the "
            "answer key)" if r == "May26" else
            "Aug 2026 — live (same machine, answer unknown)"))
    try:
        s = _story(market, review)
    except SystemExit as e:
        st.error(str(e))
        return

    if s["mode"] == "solved":
        st.success(
            "**Learning mode.** This review has already been "
            "announced, so at the end you can see exactly how "
            "the method scored — including where it was wrong.")
    else:
        st.warning(
            "**Live mode.** The identical machine, pointed at a "
            "review MSCI has not announced. The call at the end "
            "was written down in advance and grades on Aug 11-12.")

    for stp in s["steps"]:
        st.markdown("---")
        st.subheader(f"{stp['n']}. {stp['title']}")
        _numbers(stp["numbers"])
        for p in stp["plain"]:
            st.markdown(p)
        if stp["n"] == 5:
            _lever(s)
        if stp.get("desk"):
            with st.expander("For the desk — rules, sources, "
                             "error bars"):
                st.markdown(stp["desk"])
        if stp.get("honesty"):
            st.info(f"**What this step can get wrong:** "
                    f"{stp['honesty']}")

    st.markdown("---")
    st.subheader("Take it with you")
    from walkthrough_export import to_html
    html = to_html(s)
    st.download_button(
        "Download this walkthrough as a single HTML file",
        html.encode("utf-8"),
        file_name=f"walkthrough_{s['market']}_{s['review']}.html",
        mime="text/html",
        help="Self-contained: opens in any browser, no app or "
             "internet needed.")
    st.caption(
        "The exported file carries the same generated numbers, "
        "so it stays honest away from the app — but it is a "
        "snapshot: re-export after the engine reruns.")
