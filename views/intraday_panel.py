"""Index Rebalance — 5-Minute Data Analysis (c-288).

Reads `data/ib_5m_analysis.json`, built by
`scripts/ib_5m_analysis.py` from 8.2 million IB 5-minute bars.

WHY THIS PAGE EXISTS SEPARATELY FROM THE DAILY ONE. The daily
panel answers how big the print was and how far the name moved.
It cannot answer WHEN inside the day — and the index trade is
not a day, it is a closing auction. Every section here is a
question the daily panel is structurally unable to ask.

THE ONE FINDING THAT REORGANISES THE OTHERS: "the index trades
in the close" is a Taiwan and Hong Kong statement, not an APAC
one. Taiwan puts 79% of the effective day into its final bar
and Hong Kong 74%; Korea and Australia barely concentrate at
all. A desk that carries one mental model across the region
will be wrong in half of it, and the direction of the error
flips by market.

EVERY SHARE IS BENCHMARKED PER NAME. A name's effective day is
compared with THAT name's own normal sessions inside the same
window, so a wide market and a narrow one are directly
comparable and no cross-market volume normalisation is needed.
Control sessions exclude the print, its shoulders, and the
announcement reaction.
"""
import json
from pathlib import Path

import plotly.graph_objects as go
import streamlit as st

from views import design

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "data" / "ib_5m_analysis.json"
AUC = ROOT / "data" / "tw_auction_microstructure.json"


def _auc_stamp():
    try:
        s_ = AUC.stat()
        return (s_.st_mtime_ns, s_.st_size)
    except OSError:
        return (0, 0)


@st.cache_data(show_spinner=False)
def _load_auction(stamp=None):
    if not AUC.exists():
        return None
    return json.loads(AUC.read_text(encoding="utf-8"))


IMP = ROOT / "data" / "tw_auction_impact.json"


def _imp_stamp():
    try:
        s_ = IMP.stat()
        return (s_.st_mtime_ns, s_.st_size)
    except OSError:
        return (0, 0)


@st.cache_data(show_spinner=False)
def _load_impact(stamp=None):
    """scripts/tw_auction_impact.py — the auction measured against
    the last CONTINUOUS price instead of against a VWAP the
    auction itself mostly sets."""
    if not IMP.exists():
        return None
    return json.loads(IMP.read_text(encoding="utf-8"))

NAVY, GREEN, RED = design.NAVY, design.GREEN, design.RED
FAINT, MUTED, RULE = design.FAINT, design.MUTED, design.RULE
AMBER, INK = design.AMBER, design.INK

# below this a market's median is a curiosity, not a finding
THIN_N = 20

_LABEL = {"HongKong": "Hong Kong"}


def _pretty(m):
    return _LABEL.get(m, m)


def _stamp():
    """See apac_panel._stamp — c-287. A cache with no arguments
    serves a stale file forever, which once made a fixed bug
    look unfixed."""
    try:
        s = SRC.stat()
        return (s.st_mtime_ns, s.st_size)
    except OSError:
        return (0, 0)


@st.cache_data(show_spinner=False)
def _load(stamp=None):
    if not SRC.exists():
        return None
    return json.loads(SRC.read_text(encoding="utf-8"))


def _q(xs, p):
    xs = sorted(x for x in xs if x is not None and x == x)
    if not xs:
        return None
    i = (len(xs) - 1) * p
    lo = int(i)
    hi = min(lo + 1, len(xs) - 1)
    return xs[lo] + (xs[hi] - xs[lo]) * (i - lo)


def _controls(key, d, side=True):
    markets = sorted(d["markets"], key=lambda m: -d["markets"][m]["n"])
    cols = st.columns([1.4, 1.2] if side else [1.4])
    with cols[0]:
        mkt = st.selectbox(
            "Market", markets,
            index=markets.index("Taiwan") if "Taiwan" in markets
            else 0, format_func=_pretty, key=f"{key}_mkt")
    sd = "Both"
    if side:
        with cols[1]:
            sd = st.selectbox("Side",
                              ["Both", "Additions", "Deletions"],
                              key=f"{key}_side")
    return mkt, sd


def _rows(d, mkt, sd="Both"):
    rs = [r for r in d["events"] if r["market"] == mkt]
    if sd == "Additions":
        rs = [r for r in rs if r["action"] == "ADD"]
    elif sd == "Deletions":
        rs = [r for r in rs if r["action"] != "ADD"]
    return rs


def render():
    """The standalone page. c-321 folded these sections into the
    Taiwan Case Study at Bill's request, so nothing routes here
    any more — the module is kept because it OWNS the section
    bodies that the case study now calls."""
    design.css()
    st.markdown("# Index Rebalance — 5-Minute Data Analysis")
    sections(1)


def _note(txt):
    """A centred caption under a figure. c-323: these sections
    used it before they were rewritten and it lived on the host
    page; it belongs here, with the sections that call it."""
    st.markdown(
        f"<p style='font-size:.8rem;color:{MUTED};margin:"
        f".1rem 0 .5rem;text-align:center'>{txt}</p>",
        unsafe_allow_html=True)


def _two_sides(n):
    """The trade's two sides and the two numbers both run on.

    c-368, Bill: *"explain the two important metrics for both
    liquidity seeker/consumers of the rebalance trade, which is
    passive index trackers, and liquidity providers, hedge funds
    like millennium ... create a visualization for these two
    relationships, then provide the perspective for both
    parties."* DRAFT — Bill will refine the wording; the
    structure is formulas -> the flow drawn -> one card per
    party.
    """
    design.sect(n, "Two Sides of the Rebalance Trade",
                # c-370, Bill: the subtitle names the two roles.
                "The liquidity consumer and the liquidity "
                "provider of the trade")
    INK = design.INK
    # c-387 drew two columns with an Alpha band; c-389, Bill:
    # the ALPHA BAND IS DELETED, the CLOSING-AUCTION box returns
    # to the centre linking the two parties (the c-370 form),
    # and the behaviour texts ride ALONG the converging arrows
    # as captions instead of sitting in boxes. Below the trio,
    # each party keeps its quantity: trackers -> Expected Flow
    # -> P \u00d7 \u0394w \u00d7 AUM; hedge funds -> Available Liquidity.

    def _wrap(txt, n):
        words, line, out = txt.split(" "), "", []
        for w_ in words:
            if len(line) + len(w_) > n:
                out.append(line)
                line = w_
            else:
                line = (line + " " + w_).strip()
        out.append(line)
        return out

    def _sides_svg():
        W = 952
        p_ = [f'<svg viewBox="0 0 {W} 324" width="100%" '
              f'xmlns="http://www.w3.org/2000/svg" '
              f'style="max-width:952px;display:block;'
              f'margin:.2rem auto .6rem">'
              f'<defs><marker id="sfa" viewBox="0 0 10 10" '
              f'refX="9" refY="5" markerWidth="7" '
              f'markerHeight="7" orient="auto-start-reverse">'
              f'<path d="M 0 0 L 10 5 L 0 10 z" fill="{MUTED}"/>'
              f'</marker></defs>']

        def box(x, y, w, h, fill, stroke):
            p_.append(f'<rect x="{x}" y="{y}" width="{w}" '
                      f'height="{h}" rx="4" fill="{fill}" '
                      f'stroke="{stroke}" stroke-width="1.4"/>')

        def ctext(cx, y, txt, size, fill, weight=None,
                  family="Inter,sans-serif"):
            wgt = f' font-weight="{weight}"' if weight else ""
            p_.append(f'<text x="{cx}" y="{y}" '
                      f'text-anchor="middle" '
                      f'font-family="{family}" '
                      f'font-size="{size}"{wgt} '
                      f'fill="{fill}">{txt}</text>')

        # \u2500\u2500 row 1: trackers -> closing auction <- funds \u2500\u2500
        for x, cx, name, sub in (
                (8, 148, "Passive index trackers",
                 "liquidity consumer"),
                (664, 804, "Hedge funds",
                 "liquidity provider")):
            box(x, 8, 280, 56, design.CARD, NAVY)
            ctext(cx, 30, name, 13.5, INK, weight=600)
            ctext(cx, 48, sub, 10, MUTED)
        box(336, 8, 280, 56, NAVY, NAVY)
        ctext(476, 30, "Closing auction", 13.5, "#ffffff",
              weight=600, family=design.SERIF)
        ctext(476, 48, "effective day, 13:30", 10, "#cfd8e3")
        p_.append(f'<line x1="288" y1="36" x2="330" y2="36" '
                  f'stroke="{MUTED}" stroke-width="1.6" '
                  f'marker-end="url(#sfa)"/>')
        p_.append(f'<line x1="664" y1="36" x2="622" y2="36" '
                  f'stroke="{MUTED}" stroke-width="1.6" '
                  f'marker-end="url(#sfa)"/>')

        # \u2500\u2500 the behaviours, riding along their arrows \u2500\u2500
        beh_l = ["rebalances to match the updated index,",
                 "mostly as market-on-close orders,",
                 "to minimise tracking error"]
        beh_r = ["accumulates inventory before the",
                 "effective day, supplies liquidity",
                 "into the market close"]
        for cx, lines in ((312, beh_l), (640, beh_r)):
            for j, ln in enumerate(lines):
                ctext(cx, 84 + j * 14, ln, 10.5, MUTED)

        # -- each party's quantity, below its box --
        # c-392, Bill: title-only navy bars -- Expected DEMAND
        # under the trackers, Expected SUPPLY under the funds;
        # the descriptions come off.
        for pcx, y1 in ((148, 64), (804, 64)):
            p_.append(f'<line x1="{pcx}" y1="{y1}" x2="{pcx}" '
                      f'y2="139" stroke="{MUTED}" '
                      f'stroke-width="1.4" '
                      f'marker-end="url(#sfa)"/>')
        for x, cx, name in ((8, 148, "Expected Demand"),
                            (664, 804, "Expected Supply")):
            box(x, 142, 280, 44, NAVY, NAVY)
            ctext(cx, 170, name, 14, "#ffffff",
                  family=design.SERIF)
        # c-399, Bill: this arrow runs slightly longer — the
        # factor row drops 12 units to give it room.
        p_.append(f'<line x1="148" y1="186" x2="148" y2="211" '
                  f'stroke="{MUTED}" stroke-width="1.4" '
                  f'marker-end="url(#sfa)"/>')

        # -- the decomposition, under Expected Demand --
        # c-392, Bill: P reworded; \u0394w carries the ACTIVE-
        # WEIGHT formula (benchmark weight minus current
        # portfolio weight); Tracking AUM ends "accordingly".
        # c-394, Bill: P's accent goes NAVY to match the other
        # boxes; \u0394w carries the formula as a maths line of its
        # own (serif italic) over the plain-words reading.
        facs = [
            (NAVY, "P(add / delete)", None,
             "The probability that the stock gets added or "
             "deleted at the MSCI index review."),
            (NAVY, "\u0394w",
             # c-395, Bill: w_index, not w_benchmark
             "\u0394w = w_index \u2212 w_portfolio",
             "the weight the index review assigns minus the "
             "weight currently held in portfolio."),
            (NAVY, "Tracking AUM", None,
             "The money that tracks the index and must buy "
             "or sell accordingly."),
        ]
        fw = 130
        fx = [8, 158, 308]
        for k, (acc, name, formula, desc) in enumerate(facs):
            x = fx[k]
            box(x, 214, fw, 96, design.CARD, NAVY)
            p_.append(f'<rect x="{x}" y="214" width="{fw}" '
                      f'height="3" fill="{acc}"/>')
            ctext(x + fw / 2, 234, name, 11.5, NAVY,
                  family=design.SERIF)
            dy = 250
            if formula:
                p_.append(
                    f'<text x="{x + fw / 2}" y="{dy}" '
                    f'text-anchor="middle" '
                    f'font-family="{design.SERIF}" '
                    f'font-style="italic" font-size="9.5" '
                    f'fill="{INK}">{formula}</text>')
                dy += 14
            for j, ln in enumerate(_wrap(desc, 24)[:5]):
                ctext(x + fw / 2, dy + j * 12, ln, 8.5, MUTED)
            if k < 2:
                ctext(fx[k] + fw + 10, 264, "\u00d7", 15, MUTED,
                      family=design.SERIF)
        p_.append("</svg>")
        return "".join(p_)

    st.markdown(_sides_svg(), unsafe_allow_html=True)
    # c-373, Bill: the two per-party cards are REMOVED — the
    # captions under each box in the diagram carry the read
    # now, attached to the party they describe.


def _pctl(xs, q):
    xs = sorted(x for x in xs if x is not None and x == x)
    if not xs:
        return None
    i = (len(xs) - 1) * q
    lo = int(i)
    hi = min(lo + 1, len(xs) - 1)
    return xs[lo] + (xs[hi] - xs[lo]) * (i - lo)


def sections(start_n=1):
    """The four Taiwan intraday sections, numbered from `start_n`.

    c-321 folded these into the Taiwan Case Study. c-323, Bill:
    *"For all sections on this page, I want to analyze Taiwan
    market alone."*

    THAT IS A REAL CHANGE, NOT A FILTER. The old versions were
    cross-market bar charts and tables whose POINT was the
    comparison — Taiwan at 79% against Australia at 4% was how
    the data-quality problem got found. Restricted to one market
    those charts collapse to a single bar, so each one is rebuilt
    around the thing a one-market view can show and a
    cross-section cannot: the 43 Taiwanese events INDIVIDUALLY,
    with their dispersion.

    What the cross-market comparison established is not lost —
    it is recorded in docs/ and in ib_auction_reharvest.py, which
    is where the verdict on each venue's data lives.
    """
    d = _load(_stamp())
    if not d:
        st.info("Run `py scripts\\ib_5m_analysis.py` to build "
                "the intraday panel.")
        return 0
    ev = [e for e in d["events"] if e["market"] == "Taiwan"]
    M = d["markets"].get("Taiwan")
    if not (ev and M):
        st.info("No Taiwan windows in the intraday panel.")
        return 0
    _n = [start_n - 1]

    def nxt():
        _n[0] += 1
        return _n[0]

    def lab(e):
        return f"{e['code']} {e['rev']} {e['action']}"

    # ---- 1 · data review ------------------------------------
    #
    # c-327, Bill asked for the same treatment the daily panel
    # gets: say what the dataset IS before showing anything drawn
    # from it, and say why it is this small.
    design.sect(nxt(), "Data Review",
                "How the stock trades before and after its index "
                "review, measured from 5-minute bars")
    # c-378: `dts` went with the hard-coded date range — the
    # caveat now states IB's edge and "now" rather than the
    # panel's own first/last effective dates.
    # c-330, Bill: the four-card table is deleted. Every figure it
    # carried — the event count, the period, the bar count and the
    # control-day median — is stated in the prose below, where it
    # sits next to the reason it matters instead of standing alone
    # as a number a reader has to place.
    # c-331, Bill rewrote this section down to two paragraphs.
    #
    # WHAT WENT, SO IT IS A DECISION AND NOT A DRIFT. Two blocks
    # were cut: the arithmetic of why the panel is 43 events
    # (twelve reviews x a handful of Taiwanese names), and the
    # "what that costs" paragraph naming every result here as a
    # RECENT-REGIME result that cannot speak to 2015-2022. The
    # second is a real limitation and it is not being hidden — the
    # period is still stated in the first paragraph with its
    # cause, and the full caveat is in docs/TW_CASE_STUDY.md. But
    # a reader who skims now sees the window without being told
    # what the window costs, so this is worth revisiting if the
    # page is ever used to argue a structural claim about Taiwan.
    design.caveat(
        # c-337, Bill's wording, with one correction to it. His
        # draft said the panel "stops there because" of the IB
        # limit — but that limit sets the START, not the end. The
        # end is simply the most recent review. Saying it the
        # other way round would have a reader thinking the data
        # runs out before the present, which is the opposite of
        # the constraint.
        # c-366, Bill's wording again, with one correction to
        # it. His draft said the window is "20 sessions before
        # the announcement and 20 sessions after the effective
        # date" — that is the DAILY panel's window. This
        # harvest's is wider: PRE_ANN_DAYS = POST_EFF_DAYS = 45
        # calendar days (~31 trading sessions a side) in
        # scripts/ib_5m_events.py, so the page states those.
        "<b>The dataset:</b> for companies added to or deleted "
        "from the MSCI Taiwan index at a quarterly review, "
        "5-minute bar data is collected across a window, 45 "
        "calendar days before the announcement and 45 calendar "
        "days after the effective date. The panel runs "
        # c-378, Bill: the range reads 2023-05-01 to now — the
        # start is IB's history edge, the end is wherever the
        # latest review sits.
        "from 2023-05-01 to now, as Interactive Brokers' "
        "5-minute history for Taiwanese stocks begins around May "
        "2023."
        "<br><br>"
        "<b>Data collected:</b> open, high, low, close and volume "
        "on each bar, from Interactive Brokers, during regular "
        "trading hours, including the closing auction.")

    _two_sides(nxt())

    # ---- 2 · where the volume prints ------------------------
    design.sect(nxt(), "Where the Volume Actually Prints",
                "Every Taiwan index event, its effective-day "
                "closing bar compared against its own normal days")
    good = [e for e in ev if e.get("close_share") is not None
            and e.get("close_share_control")]
    fig = go.Figure()
    # c-368, Bill: capitalised legend labels, matching the
    # foreign-flow section's
    for act, colour, nm in (("ADD", GREEN, "Additions"),
                            ("DEL", RED, "Deletions")):
        g = [e for e in good if e["action"] == act]
        if not g:
            continue
        fig.add_scatter(
            x=[e["close_share_control"] for e in g],
            y=[e["close_share"] for e in g], mode="markers",
            name=nm, marker=dict(size=11, color=colour,
                                 opacity=.75,
                                 line=dict(color="white", width=1)),
            customdata=[[lab(e), e["close_share_lift"]]
                        for e in g],
            # c-340, Bill: the card applies here too. c-334 had
            # exempted this chart; he has now seen both and wants
            # ONE treatment across the page.
            hovertemplate=design.hover(
                "%{customdata[0]}", eyebrow=nm[:-1],
                rows=[("effective day", "%{y:.0%} in the close"),
                      ("normal day", "%{x:.1%}"),
                      ("lift", "%{customdata[1]:.1f}\u00d7")]))
    m = max([e["close_share"] for e in good] + [.9])
    fig.add_scatter(x=[0, m], y=[0, m], mode="lines",
                    line=dict(color=RULE, width=1, dash="dot"),
                    showlegend=False, hoverinfo="skip")
    fig.update_layout(
        height=390,
        legend=dict(orientation="h", y=-0.22, x=0),
        xaxis=dict(title="share of a NORMAL day in the "
                         "closing bar", tickformat=".0%"),
        yaxis=dict(title="share of the EFFECTIVE day",
                   tickformat=".0%"))
    design.chart(fig)
    _note("The dotted line is where the two shares are equal, so "
          "a dot above it is an event whose closing auction took "
          "a bigger share of the day than that same stock's close "
          "normally does.")
    design.caveat(
        "<b>On the effective day, the five-minute closing auction "
        "takes up most of the volume.</b> The typical index mover "
        # c-366, Bill: the two numbers that carry the claim are
        # bold — the share routed through the call, and the lift.
        f"routes <b>{M['close_share_eff']['p50']:.0%}</b> of "
        "that day's trading through the 13:30 call, where the "
        "same stock normally puts "
        f"{M['close_share_ctrl']['p50']:.1%} through it — a "
        f"<b>{M['close_share_lift']['p50']:.0f}x lift</b>, and "
        f"{sum(1 for e in good if e['close_share'] > .5)} of "
        f"{len(good)} events put more than half of the day's "
        "volume in the close.")

    # ---- 2 · the shape of the day ---------------------------
    design.sect(nxt(), "Volume Profile on the Effective Day",
                "Where the day's volume sits through the session, "
                "against the same names on normal days")
    L = max(len(e["eff_shape"]) for e in ev)
    prof, ctrl = [], []
    for i in range(L):
        prof.append(_pctl([e["eff_shape"][i] for e in ev
                           if i < len(e["eff_shape"])], .5))
        ctrl.append(_pctl([e["ctrl_shape"][i] for e in ev
                           if i < len(e["ctrl_shape"])], .5))
    xs = list(range(L))
    fig = go.Figure()
    fig.add_scatter(x=xs, y=ctrl, mode="lines", name="normal day",
                    line=dict(color=FAINT, width=2),
                    hovertemplate=design.hover(
                        "Normal day", eyebrow="volume profile",
                        rows=[("5-minute bar", "%{x}"),
                              ("share of the day", "%{y:.2%}")]))
    fig.add_scatter(x=xs, y=prof, mode="lines",
                    name="effective day",
                    line=dict(color=NAVY, width=2.6),
                    hovertemplate=design.hover(
                        "Effective day", eyebrow="volume profile",
                        rows=[("5-minute bar", "%{x}"),
                              ("share of the day", "%{y:.2%}")]))
    fig.update_layout(
        height=360, legend=dict(orientation="h", y=-0.22, x=0),
        xaxis=dict(title="5-minute bar through the session "
                         "(last bar = the 13:30 auction)"),
        yaxis=dict(title="share of the day's volume",
                   tickformat=".0%"))
    design.chart(fig)
    _note(f"Each line is the median 5-minute trading volume "
          f"across {len(ev)} Taiwan index events.")

    # ---- 3 · the close against fair value -------------------
    design.sect(nxt(), "Market on Close vs VWAP",
                "The closing price against the day's own VWAP, "
                "and the next day open")
    cv = [e for e in ev if e.get("close_vs_vwap") is not None]
    ng = [e for e in ev if e.get("next_open_gap") is not None]
    # c-329, Bill: SPLIT THE OVERNIGHT NUMBER BY SIDE. He is right
    # and this was a real defect. An addition should gap up and a
    # deletion down, so a pooled median of next_open_gap averages
    # two opposite predictions and the pooled figure means nothing
    # — it is small either because neither side moves or because
    # both move and cancel, and the pooled number cannot tell you
    # which.
    #
    # The close-vs-VWAP number does NOT have that problem, and the
    # difference is worth being precise about. VWAP is measured on
    # the SAME day as the close, so `close/VWAP - 1` already nets
    # out wherever the stock went that day; it is a cost, and a
    # buyer and a seller both want it near zero. The overnight gap
    # has no such anchor — it is a directional return. So the side
    # split is reported for BOTH, but it is the overnight number
    # that changes meaning.
    cv_a = [e for e in cv if e["action"] == "ADD"]
    cv_d = [e for e in cv if e["action"] == "DEL"]
    ng_a = [e for e in ng if e["action"] == "ADD"]
    ng_d = [e for e in ng if e["action"] == "DEL"]
    design.stats([
        {"k": "Close vs VWAP · add",
         "v": f"{_pctl([e['close_vs_vwap'] for e in cv_a], .5):+.2%}",
         "s": f"median · n={len(cv_a)}"},
        {"k": "Close vs VWAP · delete",
         "v": f"{_pctl([e['close_vs_vwap'] for e in cv_d], .5):+.2%}",
         "s": f"median · n={len(cv_d)}"},
        {"k": "Next open · add",
         "v": f"{_pctl([e['next_open_gap'] for e in ng_a], .5):+.2%}",
         "s": f"from the close · n={len(ng_a)}"},
        {"k": "Next open · delete",
         "v": f"{_pctl([e['next_open_gap'] for e in ng_d], .5):+.2%}",
         "s": f"from the close · n={len(ng_d)}"},
    ])
    fig = go.Figure()
    # c-328, Bill: "add"/"delete" on the y axis. The full words
    # pushed the plot area right for no extra information.
    for act, colour, nm in (("ADD", GREEN, "add"),
                            ("DEL", RED, "delete")):
        g = [e for e in cv if e["action"] == act]
        if not g:
            continue
        fig.add_box(
            x=[e["close_vs_vwap"] for e in g], y=[nm] * len(g),
            name=nm, marker_color=colour, boxpoints="all",
            # c-331, Bill: kill the box's own tooltip on both
            # traces. Plotly's default `hoveron="points+boxes"`
            # pops a seven-line summary — min / q1 / median / q3 /
            # max / lower fence / upper fence — and the two fence
            # lines are Tukey outlier bounds (q1-1.5*IQR and
            # q3+1.5*IQR) that this page never uses and never
            # explains. Points only; the per-event tooltip below
            # is the one that carries meaning.
            hoveron="points",
            jitter=.5, pointpos=0, orientation="h",
            hovertext=[lab(e) for e in g],
            hovertemplate=design.hover(
                "%{hovertext}", eyebrow=nm,
                rows=[("close vs VWAP", "%{x:+.2%}")]))
    fig.add_vline(x=0, line_color=RULE, line_width=1)
    fig.update_layout(
        height=300, showlegend=False,
        xaxis=dict(title="closing price against the day's own "
                         "VWAP", tickformat=".1%"),
        yaxis=dict(title=""))
    design.chart(fig)
    # c-331, Bill: ONE comment for this section, interpreting the
    # cards and the boxes together.
    #
    # It replaces a conclusion that read "the dislocation is
    # small, and that is the finding" — which this measurement is
    # not entitled to say. An index mover puts ~79% of its
    # effective-day volume through the same auction, so the close
    # is most of the VWAP it is being compared with and the
    # statistic is pulled toward zero whatever happened.
    # scripts/tw_auction_impact.py reproduces the measured -0.06%
    # by scaling for exactly that dilution, which is what makes
    # the circularity a demonstrated mechanism and not a worry.
    # c-332, Bill: shorter. The 13:20 measurement and the
    # dispersion lift are NOT on the page any more — they are in
    # docs/TW_AUCTION_IMPACT.md and data/tw_auction_impact.json,
    # generated by scripts/tw_auction_impact.py. What stays here
    # is the one thing a reader cannot recover from the cards
    # alone: that this benchmark is partly circular.
    body = (
        "<b>The close prints near the day's average.</b> "
        "Additions settle "
        f"{_pctl([e['close_vs_vwap'] for e in cv_a], .5):+.2%} "
        "against their own VWAP and deletions "
        f"{_pctl([e['close_vs_vwap'] for e in cv_d], .5):+.2%}. "
        "Bear in mind an index mover routes "
        f"{M['close_share_eff']['p50']:.0%} of its effective-day "
        "volume through this same auction, which is what pulls "
        "the gap between close and VWAP toward zero. The "
        "following open adds "
        f"{_pctl([e['next_open_gap'] for e in ng_a], .5):+.2%} on "
        "additions and "
        f"{_pctl([e['next_open_gap'] for e in ng_d], .5):+.2%} on "
        "deletions.")
    design.caveat(body)

    # ---- 5 to 7: TWSE's own 5-second auction file --------------
    AU = _load_auction(_auc_stamp())
    if not AU:
        return
    # c-323: `A` and `RT` went with the two deleted sections.
    # c-329: `CAP` went with the four-card table.
    MC = AU["month_end_control"]

    design.sect(nxt(), "How Much Volume the Close Can Absorb",
                "Comparison of closing auction as a percentage of "
                "the day's volume")
    # c-329, Bill: the four-card table is deleted. Every number it
    # carried is on the chart below or in its hover, and CAP is
    # still read from the file — see the note under the chart.
    fig = go.Figure()
    for lab, key, colour in (
            ("normal day", "neither", FAINT),
            ("month-end, not MSCI", "month_end_not_msci", NAVY),
            ("MSCI effective date", "msci_effective", RED)):
        b = MC[key]
        fig.add_bar(x=[lab], y=[b["p50"]], marker_color=colour,
                    marker_line_width=0, name=lab,
                    # c-329, Bill: "I don't see the whiskers."
                    # They were drawn — in the SAME colour as the
                    # bar. The lower half sits inside the bar and
                    # is invisible by construction, and the upper
                    # half was a 1.2px light-grey line on cream
                    # for the "normal day" bar. Ink, thicker,
                    # with an explicit cap width.
                    error_y=dict(type="data", symmetric=False,
                                 array=[b["p75"] - b["p50"]],
                                 arrayminus=[b["p50"] - b["p25"]],
                                 color=INK, thickness=1.6, width=9),
                    customdata=[[b["n"], b["p25"], b["p75"]]],
                    hovertemplate=design.hover(
                        "%{x}", eyebrow="closing auction",
                        rows=[("median share", "%{y:.1%}"),
                              ("quartiles",
                               "%{customdata[1]:.1%} – "
                               "%{customdata[2]:.1%}"),
                              ("sessions", "%{customdata[0]:,}")]))
    fig.update_layout(
        height=330, showlegend=False,
        yaxis=dict(title="closing auction, share of the day's "
                         "value", tickformat=".0%"),
        xaxis=dict(title=""), margin=dict(t=20))
    design.chart(fig)
    st.markdown(
        f"<p style='font-size:.8rem;color:{MUTED};margin:"
        f".1rem 0 .5rem;text-align:center'>Bars represent medians, "
        f"whiskers represent the interquartile range</p>",
        unsafe_allow_html=True)
    # c-333, Bill asked what the 114 month-end datapoints are.
    # They are SESSIONS, not stocks — and nothing on the page said
    # so, which is why the question had to be asked. Every one of
    # the 2,815 trading days in TWSE's 5-second file falls in
    # exactly one of the three bars.
    # c-367, Bill: the mechanics sentence LEADS and the scope
    # sentence follows it, with the load-bearing phrases bold \u2014
    # what is measured (the auction's volume), what it is
    # divided by, and the number the example turns on.
    design.caveat(
        "Each bar takes the volume traded in the "
        "<b>13:25\u201313:30 closing auction</b> across every "
        "listed company, and divides it by the volume traded "
        "in the <b>whole session</b>. This chart sums the "
        "volume for the <b>whole exchange</b>. Ex. a median of "
        f"<b>{MC['neither']['p50']:.1%}</b> means that on a "
        # c-371, Bill: both occurrences bold
        f"normal day, <b>{MC['neither']['p50']:.1%}</b> of a "
        "full session's trading happens in those final five "
        "minutes.")
    # c-329, Bill: the three prose blocks under this chart are
    # deleted. NOTHING IS LOST FROM THE PROJECT — the month-end
    # control (26/30 of MSCI dates are month-ends; month-end alone
    # lifts the close to 11.2% and the review lifts it again to
    # 30.3%, p<0.0001), the market-wide caveat and the
    # May/November-versus-February/August split all live in
    # docs/TW_AUCTION_MICROSTRUCTURE.md and in
    # data/tw_auction_microstructure.json, and the middle bar is
    # still ON THE CHART, which is where the control does its
    # work. What went is prose, not evidence.

    # c-323, Bill: "The Review Type Is a Capacity Input" and
    # "What the 5-Second File Cannot Tell You" are deleted.
    #
    # NEITHER FINDING IS LOST. The May/November-versus-
    # February/August split (31.4% against 19.3%, p=0.0005) and
    # the column-identification limits both live in
    # docs/TW_AUCTION_MICROSTRUCTURE.md and in
    # data/tw_auction_microstructure.json, which the section
    # above still reads from. What went is two blocks of prose on
    # a page Bill is shortening to the four charts that carry
    # themselves.

    return _n[0] - start_n + 1
