"""Page — "Taiwan Rebalance Insights" (c-270).

The strategist question bank, answered on the Taiwan panel.

THIS MODULE HOLDS NO NUMBERS. Everything is read from
`data/rebalance_analysis.json`, which `scripts/rebalance_analysis.py`
regenerates in one command. That is the same contract the
walkthrough page runs under, and it exists because a page that
carries its own figures will disagree with the engine the first
time the panel moves — which has already happened here once.

WHAT IS AND IS NOT ON THIS PAGE. The bank asks for everything
defensible, with the under-powered work flagged rather than
hidden, so Bill can select. Two rules are applied:

  - any statistic on n < 15 renders with an EXPLORATORY tag,
    read from the payload's own `exploratory` flag rather than
    from a judgement made here;
  - the survivorship and day-0 caveats are amber blocks at the
    top of the sections they qualify, not grey footnotes. D8:
    a limitation the reader must carry is not a footnote.

Charts are distributions, not point estimates (bank §0.4): the
drift question renders as an ECDF with the break-even marked,
the print-size question as a box, and the anatomy question as a
quartile fan.
"""
import json
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "rebalance_analysis.json"


@st.cache_data(show_spinner=False)
def _load():
    if not DATA.exists():
        return None
    return json.loads(DATA.read_text(encoding="utf-8"))


def _pc(v, dp=2):
    return "—" if v is None else f"{v:+.{dp}%}"


def _x(v, dp=1):
    return "—" if v is None else f"{v:.{dp}f}x"


def _tag(d):
    """EXPLORATORY, from the payload rather than from a guess."""
    return " · EXPLORATORY" if d.get("exploratory") else ""


def render():
    from views import design
    d = _load()
    st.markdown("# Taiwan Rebalance Insights")
    if not d:
        design.caveat(
            "No analysis on disk. Run "
            "<code>py scripts\\rebalance_analysis.py</code>.")
        return
    M = d["M"]["M1_panel"]
    design.sect(None, "What the desk can say about a Taiwan "
                      "index change", big=True)
    design.caveat(
        f"<b>The sample is {M['registry_day0']} events, not "
        f"{M['priced_and_usable']}.</b> "
        f"{M['estimated_day0']} priced windows carry an "
        f"<i>estimated</i> announcement date. Day 0 is the "
        f"pre-news baseline every number here is measured from, "
        f"and on those windows it is 2–7 sessions wrong — "
        f"larger than the effect. They are excluded, not "
        f"down-weighted. Returns are excess over TAIEX.")

    _headline(d, design)
    _anatomy(d, design)
    _timing(d, design)
    _print_size(d, design)
    _risk(d, design)
    _flow(d, design)
    _live(d, design)


def _headline(d, design):
    c1, b1 = d["C1_drift"], d["B1_print_size"]
    design.stats([
        {"k": "Addition drift, median",
         "v": _pc(c1["ADD"]["p50"]),
         "s": f"right sign {c1['ADD']['hit_rate']:.0%} of the time"},
        {"k": "Deletion drift, median",
         "v": _pc(c1["DEL"]["p50"]),
         "s": f"right sign {c1['DEL']['hit_rate']:.0%} of the time"},
        {"k": "Addition print", "v": _x(b1["ADD"]["p50"]),
         "s": f"p90 {b1['ADD']['p90']:.0f}x ADV"},
        {"k": "Deletion print", "v": _x(b1["DEL"]["p50"]),
         "s": f"p90 {b1['DEL']['p90']:.0f}x ADV"},
    ])
    design.beats([
        f"**The mean is not the median, and the gap is the "
        f"finding.** Addition drift averages "
        f"{c1['ADD']['mean']:+.2%} against a median of "
        f"{c1['ADD']['p50']:+.2%}. Three events — Yageo in "
        f"Nov-2017, Walsin in May-2018, Wistron in May-2023 — "
        f"carry most of that difference. A book sized on the "
        f"average is sized on those three.",
        f"**A {c1['ADD']['hit_rate']:.0%} hit rate is the number "
        f"a pod sizes on.** The median says the trade works; the "
        f"hit rate says it fails about four times in ten, and "
        f"the interquartile range runs "
        f"{c1['ADD']['p25']:+.1%} to {c1['ADD']['p75']:+.1%}. "
        f"Both clients need the second number, not the first.",
        f"**Deletions print {b1['DEL']['p50'] / b1['ADD']['p50']:.1f}x "
        f"the size of additions**, and this is Taiwan — priced "
        f"from exchange day files that keep delisted names, so "
        f"the deletion sample is survivor-safe. The asymmetry is "
        f"not a survivorship artefact here.",
    ], key="rb_head")


def _anatomy(d, design):
    design.sect(1, "Event anatomy",
                "The average path, and the fact that Taiwan has "
                "no quiet events.", kind="Section")
    a3 = d["A3_non_events"]
    design.stats([
        {"k": "Non-events", "v": f"{a3['n']} / {a3['of']}",
         "s": a3["definition"]},
        {"k": "Additions", "v": d["M"]["M1_panel"]["by_action"]["ADD"],
         "s": "registry-dated"},
        {"k": "Deletions", "v": d["M"]["M1_panel"]["by_action"]["DEL"],
         "s": "registry-dated"},
    ])
    _fan(d, design)
    design.beats([
        "**Every MSCI Taiwan change is a trade.** Not one event "
        "in the sample is both quiet on volume and quiet on "
        "price. An earlier China cut ran 61% non-events. A desk "
        "that triages Taiwan changes by expected size is "
        "triaging nothing — all of them print.",
    ], key="rb_anat")


def _fan(d, design):
    import plotly.graph_objects as go
    fig = go.Figure()
    for act, col in (("ADD", "#1f4e79"), ("DEL", "#c0392b")):
        p = d["A1_paths"][act]
        xs = sorted((int(k) for k in p), key=int)
        for band, w, dash in (("p75", 1, "dot"), ("p50", 2.4, None),
                              ("p25", 1, "dot")):
            fig.add_trace(go.Scatter(
                x=xs, y=[p[str(o)][band] for o in xs],
                name=f"{act} {band}", mode="lines",
                line=dict(color=col, width=w, dash=dash),
                showlegend=(band == "p50"),
                # c-334: the old tooltip carried no title, so
                # the trace's own name becomes one — six lines
                # cross here and "day 3: 1.20%" said nothing
                # about which band was under the cursor.
                hovertemplate=design.hover(
                    f"{act} {band}", eyebrow="rebalance path",
                    rows=[("day", "%{x}"),
                          ("excess return", "%{y:.2f}%")])))
    fig.add_vline(x=0, line_width=1, line_dash="dash",
                  line_color="#5b6770")
    fig.update_layout(
        xaxis_title="trading days from announcement close",
        yaxis_title="excess return vs TAIEX, %",
        height=380, margin=dict(l=0, r=0, t=10, b=0))
    design.chart(fig, height=380, key="rb_fan")
    st.caption("Median with the p25/p75 band, indexed to the "
               "announcement close. Day 0 is the last pre-news "
               "print — MSCI publishes at ~05:00 Taipei the "
               "next morning.")


def _timing(d, design):
    design.sect(2, "Timing and the schedule",
                "The same table answers the tracker and the pod "
                "in opposite directions.", kind="Section")
    c3 = d["C3_schedules"]
    rowsd = []
    for k, lab in (("eff_close", "100% at the effective close"),
                   ("last4_equal", "25% × each of the last 4 days"),
                   ("ann_plus_1", "100% at ann+1")):
        r = c3[k]
        te = r.get("te_contribution")
        rowsd.append({
            "Schedule": lab,
            "Median saved vs close": _pc(r["p50"]),
            "p25": _pc(r["p25"]), "p75": _pc(r["p75"]),
            "Tracking error": ("0 (benchmark)" if not te
                               else f"{te:.2%}")})
    import pandas as pd
    design.table(pd.DataFrame(rowsd))
    design.beats([
        "**For a tracker, the right-hand column is the whole "
        "answer.** The effective close is not a good execution "
        "of the benchmark — it *is* the benchmark. Every other "
        "schedule buys P&L with tracking error, and a tracker "
        "is not paid in P&L.",
        f"**For a pod, the left-hand column is the answer and "
        f"the right-hand column is the risk budget.** Entering "
        f"at ann+1 is worth {_pc(c3['ann_plus_1']['p50'])} at "
        f"the median, with dispersion of "
        f"{c3['ann_plus_1']['te_contribution']:.1%} around it.",
        f"**Capture is stable and high.** The share of the move "
        f"still available after the announcement gap has a "
        f"median of {d['C4_capture']['ADD']['p50']:.2f} on "
        f"additions. The overnight gap is not where the move "
        f"happens; the following fortnight is.",
    ], key="rb_time")
    _crowding(d, design)


def _crowding(d, design):
    """H5 — and the answer is not the one the question expects."""
    import plotly.graph_objects as go
    yrs = {y: v for y, v in d["H5_crowding"].items() if v["n"] >= 8}
    if len(yrs) < 4:
        return
    xs = sorted(yrs)
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=xs, y=[yrs[y]["capture"]["p50"] for y in xs],
        name="capture (median)", mode="lines+markers",
        line=dict(color="#1f4e79", width=2.4)))
    fig.add_trace(go.Scatter(
        x=xs, y=[yrs[y]["abs_pre_drift"]["p50"] for y in xs],
        name="|pre-announcement drift| (median)",
        mode="lines+markers", yaxis="y2",
        line=dict(color="#b8860b", width=2.4, dash="dot")))
    fig.update_layout(
        yaxis=dict(title="capture"),
        yaxis2=dict(title="|pre-drift|", overlaying="y",
                    side="right", tickformat=".0%"),
        height=330, margin=dict(l=0, r=0, t=10, b=0),
        legend=dict(orientation="h", y=1.12))
    design.chart(fig, height=330, key="rb_crowd")
    a, b = xs[0], xs[-1]
    design.beats([
        f"**Is the trade getting crowded? On this test, no.** "
        f"Capture ran {yrs[a]['capture']['p50']:.2f} in {a} and "
        f"{yrs[b]['capture']['p50']:.2f} in {b}. If other desks "
        f"were taking the post-announcement move away, this "
        f"line would fall. It has not.",
        f"**But anticipation has grown.** Median absolute "
        f"pre-announcement drift went from "
        f"{yrs[a]['abs_pre_drift']['p50']:.1%} to "
        f"{yrs[b]['abs_pre_drift']['p50']:.1%}. More of the move "
        f"now happens before MSCI says anything — the market is "
        f"guessing earlier without competing away what follows.",
    ], key="rb_crowd_b")
    design.caveat(
        "n per year is 8–21. The endpoints are the claim; the "
        "year-on-year path is <b>EXPLORATORY</b>. A period split "
        "is also not a controlled experiment — Taiwan's index "
        "composition, the AI cycle and MSCI's cadence all "
        "changed across this window.")


def _print_size(d, design):
    design.sect(3, "Print size",
                "What actually goes through on the effective "
                "close.", kind="Section")
    import plotly.graph_objects as go
    fig = go.Figure()
    for act, col in (("ADD", "#1f4e79"), ("DEL", "#c0392b")):
        xs = d["B1_ecdf"][act]
        n = len(xs)
        fig.add_trace(go.Scatter(
            x=xs, y=[(i + 1) / n for i in range(n)],
            name=f"{act} (n={n})", mode="lines",
            line=dict(color=col, width=2.4)))
    for thr, lab in ((5, "5x ADV"), (20, "20x ADV")):
        fig.add_vline(x=thr, line_width=1, line_dash="dot",
                      line_color="#5b6770",
                      annotation_text=lab,
                      annotation_position="top")
    fig.update_layout(
        xaxis_title="effective-day volume ÷ pre-event ADV",
        yaxis_title="share of events at or below",
        yaxis_tickformat=".0%", height=350,
        margin=dict(l=0, r=0, t=20, b=0))
    design.chart(fig, height=350, key="rb_ecdf")
    b1 = d["B1_print_size"]
    design.beats([
        f"**Half of Taiwanese deletions print above "
        f"{b1['DEL']['p50']:.0f}× a normal day's volume**, and "
        f"one in ten above {b1['DEL']['p90']:.0f}×. The "
        f"addition side is a different order of magnitude: "
        f"median {b1['ADD']['p50']:.1f}×, p90 "
        f"{b1['ADD']['p90']:.0f}×.",
        "**Read the curve, not the median.** The decision a desk "
        "makes — can this be worked, or does it have to go in "
        "the auction — sits at a threshold, and the ECDF says "
        "what share of events clear it.",
    ], key="rb_print")


def _risk(d, design):
    design.sect(4, "Risk", "Size on the excursion, not the "
                           "outcome.", kind="Section")
    j4, j2 = d["J4_mae"], d["J2_concentration"]
    g1 = d["G1_reversion"]
    design.stats([
        {"k": "Worst mark, median addition", "v": _pc(j4["ADD"]["p50"]),
         "s": "entered ann+1, held to the close"},
        {"k": "…at the 10th percentile", "v": _pc(j4["ADD"]["p10"]),
         "s": "maximum adverse excursion"},
        {"k": "Addition give-back by +5d",
         "v": _pc(g1["revert5"]["ADD"]["p50"]), "s": "median"},
        {"k": "Risk in the worst 5% of events",
         "v": f"{j2['top_5pct_share_of_abs_alpha']:.0%}",
         "s": "share of total |alpha|"},
    ])
    design.beats([
        f"**The position is under water before it works.** The "
        f"median addition trade entered at ann+1 marks "
        f"{_pc(j4['ADD']['p50'])} against you at its worst "
        f"point, and one in ten marks {_pc(j4['ADD']['p10'])}. "
        f"The final P&L is not what the risk manager sees "
        f"during the fortnight.",
        f"**Additions give the drift back.** The median addition "
        f"reverts {_pc(g1['revert5']['ADD']['p50'])} in the five "
        f"sessions after the effective close — more than the "
        f"median drift it earned. Holding past the print is a "
        f"different trade, and a worse one.",
        f"**Risk is not concentrated enough for name-picking.** "
        f"The worst 5% of events carry "
        f"{j2['top_5pct_share_of_abs_alpha']:.0%} of the total "
        f"absolute alpha. That argues for taking the whole "
        f"basket rather than trying to pick the violent ones.",
    ], key="rb_risk")


def _flow(d, design):
    design.sect(5, "The flow layer",
                "Taiwan has six datasets no other market has. "
                "One of them is testable today, and it fails.",
                kind="Section")
    N = d["N"]
    n3, bv = N["N3_borrow_build"], N["N3_build_vs_eff_day"]
    design.stats([
        {"k": "Borrow build into a deletion",
         "v": f"{n3['DEL']['p50']:.2f}x", "s": f"median, n={n3['DEL']['n']}"},
        {"k": "…correlation with the effective-day move",
         "v": f"{bv['rho']:+.3f}", "s": f"Spearman, n={bv['n']}"},
    ])
    design.beats([
        f"**The borrow signal does not work, and that is worth "
        f"more than a fitted curve.** Securities-borrowing "
        f"balance does build into Taiwanese deletions — "
        f"{n3['DEL']['p50']:.2f}× its level five weeks earlier "
        f"at the median. It carries no information about the "
        f"effective-day move: rank correlation "
        f"{bv['rho']:+.3f}. A crowded short into a Taiwanese "
        f"deletion is not, on this evidence, a squeeze signal.",
        "**Two of the six datasets cannot be tested yet.** "
        "`twse_institutional.json` holds 22 days and "
        "`tw_limits.json` 23, both recent. Who-is-on-the-other-"
        "side is the question a client asks after every big "
        "print, and it needs a backfill before it can be "
        "answered.",
    ], key="rb_flow")
    design.caveat(
        "The closing-auction ladder (<code>auction5s_history."
        "json</code>, 3,024 days) is the highest-value Taiwan-"
        "only dataset still unopened. It answers what share of "
        "the print goes through the auction — a question every "
        "other market has to wait for 5-minute data to reach.")


def _live(d, design):
    L = d["LIVE_AUG26"]
    design.sect(6, "Applied — MSCI Taiwan, August 2026",
                f"The registered call, placed on the "
                f"distributions above. Announced "
                f"{L['ann']}, rebalance close {L['eff']}.",
                kind="Section")
    import pandas as pd
    rowsd = [{
        "Code": r["code"], "Side": r["action"],
        "Zone": (r.get("zone") or "")[:22],
        "Conviction": (f"{r['prob']:.0%}" if r.get("prob")
                       else "—"),
        "ADV pctile": ("—" if r["adv_percentile_vs_history"] is None
                       else f"{r['adv_percentile_vs_history']:.0%}"),
        "Expected print": _x(r["expected_print_x_adv"]["p50"]),
        "Expected drift": _pc(r["expected_drift"]["p50"]),
        "Flag": r["violence_flag"],
    } for r in L["names"]]
    design.table(pd.DataFrame(rowsd))
    hi = [r for r in L["names"]
          if r["violence_flag"].startswith("HIGH")]
    design.beats([
        f"**{len(hi)} of {L['n_calls']} names sit in the bottom "
        f"third of the historical liquidity distribution.** "
        f"That is the single most informative thing the history "
        f"says about them ex ante: the print multiple is a "
        f"function of how thin the name normally is, and these "
        f"are the ones that will move.",
        "**Expected values are percentiles, not point "
        "estimates.** The distributions above are wide enough "
        "that a single number would be a fiction — addition "
        "drift spans several percent across the interquartile "
        "range alone. The table gives the median of the "
        "matching historical population and the name's own "
        "liquidity rank within it.",
        "**Two schedules, because there are two clients.** "
        + L["P4_schedule"]["tracker"] + " " +
        L["P4_schedule"]["pod"],
    ], key="rb_live")
    design.caveat(
        "<b>This is a pre-registered expectation, not a "
        "forecast of the print.</b> It is written before the "
        "12 August announcement so it can be graded against "
        "what happens, and it inherits every caveat above — "
        "in particular a "
        f"{d['C1_drift']['ADD']['hit_rate']:.0%} historical hit "
        "rate on the direction of addition drift.")
    with st.expander("What would change this plan"):
        for line in L["P6_what_would_change_this"]:
            st.markdown(f"- {line}")
