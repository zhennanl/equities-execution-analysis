"""History Explorer — every MSCI APAC review result, by market
(c-101). Page 2 of the new site; reads data/msci_changes_db.pkl
(the validated database, 2015-02 -> 2026-05, 13 markets).

Built around the three questions a PT trader actually asks:
  1. What's this market's review RHYTHM?   (KPIs + timeline)
  2. Has this NAME moved before?           (search + churn)
  3. How big was that review?              (drill-down)
"""
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
_REV_ORDER = {"Feb": 0, "May": 1, "Aug": 2, "Nov": 3}


@st.cache_data(show_spinner=False)
def _db():
    import pandas as pd
    df = pd.read_pickle(ROOT / "data" / "msci_changes_db.pkl")
    df["rk"] = [f"{y}-{m:02d}" for y, m in zip(df.year, df.month)]
    return df


def _all_reviews():
    """Every review label in order (quiet ones included — a
    quiet review is a data point)."""
    out = []
    for y in range(2015, 2027):
        for mon in ("Feb", "May", "Aug", "Nov"):
            if (y, mon) == (2026, "Aug"):
                break
            out.append(f"{mon}{y % 100:02d}")
    return out


def render():
    import pandas as pd
    import plotly.graph_objects as go
    df = _db()
    st.title("Index Review History — APAC")
    st.caption("Source: 46 official MSCI change lists "
               "(STPublicList, archived + parsed; TW validated "
               "against the independent event registry). "
               "Quiet reviews shown — a no-change quarter is a "
               "base rate, not a gap.")

    markets = sorted(df.market.unique())
    mkt = st.selectbox("Market", markets,
                       index=markets.index("Taiwan"))
    rt = st.radio("Review type", ["All", "SAIR (May/Nov)",
                                  "QIR (Feb/Aug)"],
                  horizontal=True)
    sub = df[df.market == mkt]
    if rt.startswith("SAIR"):
        sub = sub[sub.review_type == "SAIR"]
    elif rt.startswith("QIR"):
        sub = sub[sub.review_type == "QIR"]

    # ---- 1. the rhythm ----------------------------------
    revs = _all_reviews()
    if rt.startswith("SAIR"):
        revs = [r for r in revs if r[:3] in ("May", "Nov")]
    elif rt.startswith("QIR"):
        revs = [r for r in revs if r[:3] in ("Feb", "Aug")]
    per = sub.groupby(["review", "action"]).size().unstack(
        fill_value=0).reindex(revs, fill_value=0)
    if "ADD" not in per:
        per["ADD"] = 0
    if "DEL" not in per:
        per["DEL"] = 0
    n_rev = len(revs)
    quiet = int(((per.ADD == 0) & (per.DEL == 0)).sum())
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Reviews", n_rev)
    c2.metric("Quiet (no change)", f"{quiet} "
              f"({quiet / n_rev:.0%})")
    c3.metric("Avg adds / dels",
              f"{per.ADD.mean():.1f} / {per.DEL.mean():.1f}")
    big = (per.ADD + per.DEL).idxmax()
    c4.metric("Biggest review", f"{big} "
              f"(+{per.loc[big, 'ADD']}/-{per.loc[big, 'DEL']})")

    names = sub.groupby(["review", "action"]).security.apply(
        lambda s: "<br>".join(s)).unstack()
    fig = go.Figure()
    fig.add_bar(x=per.index, y=per.ADD, name="adds",
                marker_color="seagreen",
                hovertext=[names.get("ADD", pd.Series()).get(r, "")
                           for r in per.index])
    fig.add_bar(x=per.index, y=-per.DEL, name="deletes",
                marker_color="crimson",
                hovertext=[names.get("DEL", pd.Series()).get(r, "")
                           for r in per.index])
    fig.update_layout(barmode="relative", height=380,
                      title=f"{mkt}: adds up, deletes down — "
                      "the review heartbeat",
                      xaxis_tickangle=60)
    st.plotly_chart(fig, use_container_width=True)

    seas = sub.groupby([sub.review.str[:3], "action"]) \
        .size().unstack(fill_value=0)
    seas = seas.reindex(["Feb", "May", "Aug", "Nov"]).fillna(0)
    with st.expander("Seasonality (total changes by review "
                     "month — SAIRs carry the breadth)"):
        st.dataframe(seas, use_container_width=True)

    # ---- 2. has this name moved before? ------------------
    st.header("Security lookup")
    q = st.text_input("Name substring or TW code "
                      "(e.g. NANYA, 2324, WAN HAI)")
    if q:
        t = q.strip().upper()
        hit = df[(df.security.str.upper()
                  .str.contains(t, regex=False))
                 | (df.code == q.strip())]
        if hit.empty:
            st.info(f"No index-review moves on record for "
                    f"{q!r} (2015-02 -> 2026-05).")
        else:
            st.dataframe(hit[["review", "market", "action",
                              "security", "code",
                              "eff_date_est"]],
                         use_container_width=True,
                         hide_index=True)
    with st.expander("Churn leaderboard — names with the most "
                     "moves (repeat offenders are patterns)"):
        churn = (df[df.market == mkt].groupby("security")
                 .agg(moves=("action", "size"),
                      history=("action",
                               lambda s: " → ".join(s)))
                 .sort_values("moves", ascending=False)
                 .head(15))
        st.dataframe(churn, use_container_width=True)

    # ---- 3. drill-down -----------------------------------
    st.header("Review drill-down")
    active = [r for r in revs
              if per.loc[r, "ADD"] + per.loc[r, "DEL"] > 0]
    if active:
        pick = st.selectbox("Review", list(reversed(active)))
        cols = st.columns(2)
        d1 = sub[(sub.review == pick)]
        with cols[0]:
            st.subheader(f"{mkt} — {pick}")
            st.dataframe(d1[["action", "security", "code"]],
                         use_container_width=True,
                         hide_index=True)
        with cols[1]:
            st.subheader("All-APAC that review")
            ctx = (df[df.review == pick]
                   .groupby(["market", "action"]).size()
                   .unstack(fill_value=0))
            st.dataframe(ctx, use_container_width=True)
    st.download_button(
        "Download current market view (CSV)",
        sub.to_csv(index=False).encode(),
        file_name=f"msci_changes_{mkt}.csv")
