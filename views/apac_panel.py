"""APAC Rebalance Panel — the interactive version (c-275).

Reads `data/apac_panel_events.json`: one row per name-event,
no aggregates. Every median, mean and percentile on this page
is computed here, from the rows the reader's own filters
selected.

THAT IS A DELIBERATE BREAK FROM THE OTHER PANEL PAGE, which
reads pre-aggregated cells and is forbidden from doing
arithmetic. The rule was right for a static page and cannot
survive a user-defined percentile: nothing can precompute "the
37th percentile of Korean deletions between Feb-2019 and
Aug-2023". Both pages call the same `metrics()` in
`index_strategist_qa.py`, so they measure the same things; only
the summarising moved.

`views/apac_strategist.py` is the frozen original and stays on
the site unchanged.

THREE CONTROLS ON EVERY CHART, and each one exists because a
single default was hiding something:

  MARKET   defaults to Taiwan, not to the pooled panel. Pooling
           twelve markets puts China's 1,275 events against New
           Zealand's 13 and calls the result "APAC" — it is a
           chart of China. Taiwan is the honest default because
           it is the market this project actually knows.
  REVIEWS  Feb-2015 to May-2026 by default. The raw panel runs
           back to 2010 for a handful of markets, which is real
           data but a different regime and a much thinner one.
  STATISTIC  median and p90 as before, plus mean and a
           percentile the reader types. The mean matters here
           precisely because it disagrees with the median —
           these distributions have long tails, and seeing the
           two apart is the point.
"""
import json
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from views import design

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "data" / "apac_panel_events.json"

ALL = "__ALL__"
NAVY, GREEN, RED = design.NAVY, design.GREEN, design.RED
FAINT, MUTED, RULE = design.FAINT, design.MUTED, design.RULE
AMBER, INK = design.AMBER, design.INK

DEFAULT_FROM, DEFAULT_TO = 201502, 202605

_LABEL = {"HongKong": "Hong Kong", "NewZealand": "New Zealand"}


def _pretty(m):
    return "All Markets" if m == ALL else _LABEL.get(m, m)


def _stamp():
    """mtime+size of the events file.

    c-287. Bill reported 6919 still on the chart after c-284
    removed it. It was already gone from the data — the page
    was serving a cached frame. `st.cache_data` keys on the
    ARGUMENTS, and `_load()` had none, so regenerating the
    events file changed nothing until the app restarted.

    Passing the file's fingerprint in as an argument makes the
    cache do what everyone assumed it already did. A cache that
    silently serves stale data is worse than no cache: it makes
    a fixed bug look unfixed, which costs a round trip to
    discover.
    """
    try:
        st_ = SRC.stat()
        return (st_.st_mtime_ns, st_.st_size)
    except OSError:
        return (0, 0)


@st.cache_data(show_spinner=False)
def _load(stamp=None):
    if not SRC.exists():
        return None
    return json.loads(SRC.read_text(encoding="utf-8"))


@st.cache_data(show_spinner=False)
def _frame(stamp=None):
    """The panel, with unadjusted corporate actions removed.

    c-284. Nine of 2,175 events contain a session no price
    limit allows — a split or bonus issue in an unadjusted
    source. Taiwan's Caliway (Aug-25) closed at 1,215, was
    suspended, and reopened at 133.50 on a 10-for-1: the event
    drew a line opening at +923%.

    They are dropped from the page, not repaired. Repairing
    means inventing an adjustment factor from the ratio itself,
    and the ratio is contaminated by whatever the price did
    during the suspension — so the "fix" would be a number we
    made up sitting in a chart of measured ones.
    """
    d = _load(_stamp())
    if not d:
        return None, None
    df = pd.DataFrame(d["events"])
    if "price_break" in df:
        df = df[~df["price_break"].astype(bool)]
    return df.reset_index(drop=True), d


# ---------------------------------------------------------------
# statistics
# ---------------------------------------------------------------
def _q(vals, p):
    """Linear-interpolated percentile. Written out rather than
    taken from numpy so the number on screen and the number in
    the generated document come from the same definition."""
    xs = sorted(v for v in vals if v is not None and v == v)
    if not xs:
        return None
    if len(xs) == 1:
        return xs[0]
    i = (len(xs) - 1) * p
    lo = int(i)
    hi = min(lo + 1, len(xs) - 1)
    return xs[lo] + (xs[hi] - xs[lo]) * (i - lo)


def _stat(vals, kind, custom):
    xs = [v for v in vals if v is not None and v == v]
    if not xs:
        return None
    if kind == "Mean":
        return sum(xs) / len(xs)
    if kind == "Median":
        return _q(xs, .5)
    if kind == "90th percentile":
        return _q(xs, .90)
    return _q(xs, custom / 100)


STAT_COLOUR = {"Median": NAVY, "Mean": AMBER,
               "90th percentile": RED}
STAT_DASH = {"Mean": "dot", "90th percentile": "dash"}
STAT_MARK = {"Mean": "diamond", "90th percentile": "triangle-up"}


# ---------------------------------------------------------------
# the control row
# ---------------------------------------------------------------
def _controls(key, d, stats=True, default_stats=None,
              side=False, stat_options=None):
    """Market, review range, statistic, and optionally side.

    Every chart carries its own set rather than sharing one bar
    at the top. A reader comparing Taiwan's print size against
    Korea's reversion should not have to change a global filter
    and lose the first chart to see the second.

    c-277: the free-text percentile box is gone. c-279 puts the
    90th percentile back on ONE section — effective-day risk —
    because that is the only chart where the tail is the
    subject rather than a distraction. The menu is per-section
    (`stat_options`) rather than global, so adding a statistic
    where it earns its place does not add it everywhere.
    """
    markets = d["markets"]
    opts = [ALL] + markets
    labels = d["review_labels"]
    revs = list(d["reviews"])

    widths = [1.15, 2.1]
    if stats:
        widths.append(1.5)
    if side:
        widths.append(1.15)
    cols = st.columns(widths)
    with cols[0]:
        mkt = st.selectbox(
            "Market", opts,
            index=opts.index("Taiwan") if "Taiwan" in opts else 0,
            format_func=_pretty, key=f"{key}_mkt")
    with cols[1]:
        lo_i = min(range(len(revs)),
                   key=lambda i: abs(revs[i] - DEFAULT_FROM))
        hi_i = min(range(len(revs)),
                   key=lambda i: abs(revs[i] - DEFAULT_TO))
        lo, hi = st.select_slider(
            "Reviews", options=revs,
            value=(revs[lo_i], revs[hi_i]),
            # c-283: .get, not []. Streamlit hands the widget's
            # own value back through format_func on a rerun, and
            # by then it may already BE the label — so a plain
            # lookup raises KeyError('May-2010') and takes the
            # whole page down on a slider drag. A formatter must
            # be total: it is display code, and it should never
            # be the thing that throws.
            format_func=lambda o: labels.get(str(o), str(o)),
            key=f"{key}_rng")
    kinds = default_stats or ["Median"]
    if stats:
        with cols[2]:
            kinds = st.multiselect(
                "Statistic", stat_options or ["Median", "Mean"],
                default=default_stats or ["Median"],
                key=f"{key}_stat")
    sd = "Both"
    if side:
        with cols[-1]:
            sd = st.selectbox("Side",
                              ["Both", "Additions", "Deletions"],
                              key=f"{key}_side")
    return mkt, lo, hi, kinds, sd


def _slice(df, mkt, lo, hi):
    s = df[(df["ord"] >= lo) & (df["ord"] <= hi)]
    return s if mkt == ALL else s[s.market == mkt]


def _axis(mkt):
    """Single market -> plot against time. All markets -> plot
    against market. The question changes with the selection, so
    the x-axis does too."""
    return "review" if mkt != ALL else "market"


def _groups(sub, mkt, labels):
    """[(label, frame)] in display order."""
    if _axis(mkt) == "review":
        return [(labels[str(o)], g) for o, g in
                sorted(sub.groupby("ord"))]
    return [(_pretty(m), g) for m, g in sub.groupby("market")]


def _time_x(groups, mkt):
    """(x values, axis kwargs) for a chart grouped by review.

    c-284, Bill: *"the year label on the graph is still not
    properly aligned, the spacing between each label is not
    equally divided."*

    The cause was the axis TYPE, not the tick placement. A
    categorical axis spaces its slots evenly and knows nothing
    about time, so a year with four reviews in the panel takes
    twice the width of a year with two, and the year labels
    land wherever those slots happen to fall.

    So a review axis is numeric now: the review's own date as a
    decimal year, Feb-2015 -> 2015.08. Years are then evenly
    spaced because they are evenly spaced in time, `dtick=1`
    puts a tick on each one, and a review the panel is missing
    shows as a gap rather than being closed up.
    """
    if _axis(mkt) != "review":
        names = [g[0] for g in groups]
        return names, dict(tickmode="array", tickvals=names,
                           ticktext=names)
    xs = []
    for lab, _g in groups:
        mon, yr = lab.split("-")
        xs.append(int(yr) + (_MON_N.get(mon, 1) - 1) / 12)
    # TICK STYLE, ASKED FOR TWICE IN BOTH DIRECTIONS — c-309 put
    # a "Feb-15" tick on every review, c-310 took the month back
    # off. Year-only is the resting state; the month lives in the
    # hover, which is where a reader looks for a single point.
    #
    # What is NOT a preference and must not be traded away: the
    # axis stays NUMERIC. That is c-284's fix and the reason the
    # spacing is true to time — a year with four reviews occupies
    # a year of width, and a review the panel is missing shows as
    # a gap instead of being closed up. Changing the ticks is a
    # taste call; changing the axis type would silently distort
    # every one of these charts.
    return xs, dict(tickmode="linear", dtick=1, tickformat="d",
                    tickangle=0)


_MON_N = {"Feb": 2, "May": 5, "Aug": 8, "Nov": 11}


def _year_axis(names, on=True):
    """tickvals/ticktext for a review axis.

    c-279: the labels were misaligned. The old version handed
    plotly EVERY category as a tickval with blank ticktext for
    three in four, and plotly then spaced and rotated the whole
    set as though all of them carried text — so the year that
    did print drifted off the bar it belonged to. Passing only
    the ticks that have a label lets plotly place each one on
    its own category.
    """
    if not on:
        return dict(tickmode="array", tickvals=names,
                    ticktext=names)
    txt = _year_ticks(names)
    keep = [(n, t) for n, t in zip(names, txt) if t]
    return dict(tickmode="array",
                tickvals=[n for n, _t in keep],
                ticktext=[t for _n, t in keep],
                tickangle=0)


def _year_ticks(names):
    """Tick text for a review axis: the year, once.

    c-277, Bill: *"Standardize the x-axis label to include only
    year."* Four reviews a year means the naive version prints
    2015 four times in a row, which is noise pretending to be an
    axis. The label appears on the first review of each year and
    is blank on the other three; the full tag stays in the hover
    where it is still useful.
    """
    out, seen = [], set()
    for nm in names:
        yr = nm.split("-")[-1] if "-" in nm else nm
        if yr in seen:
            out.append("")
        else:
            seen.add(yr)
            out.append(yr)
    return out


def _sided(sub, side):
    if side == "Additions":
        return sub[sub.action == "ADD"]
    if side == "Deletions":
        return sub[sub.action == "DEL"]
    return sub


def _empty(n=0):
    st.caption(f"Nothing in this selection"
               f"{f' — {n} events' if n else ''}. Widen the "
               f"review range or pick another market.")


def _note(txt):
    st.caption(txt)


# c-277, Bill: *"For all graphs on this page, add a note about
# how many days of ADV we calculated, from which period."*
#
# One string, used under every chart, because the denominator is
# the same everywhere and a reader who reads it once on section
# 2 should meet the identical wording on section 6 rather than a
# paraphrase that might mean something else.
#
# The definition is `metrics()` in index_strategist_qa.py:
# `adv = median(vol[i0-20 : i0])`, where i0 is the last session
# on or before the announcement. Two things worth spelling out —
# it is a MEDIAN, which a single halted or block-crossed session
# cannot move, and the window ENDS BEFORE the announcement, so
# the arbitrage volume the event itself creates is not in its
# own denominator.
ADV_NOTE = ("Note: ADV = median daily volume over the 20 "
            "sessions ending the day before the announcement")


def _axis_note(html, fig=None):
    """A summary that reads as an x-axis label.

    c-293, Bill: these lines describe the WHOLE chart, so they belong
    tight under the axis rather than floating below it as a caption.
    The negative top margin closes the gap Plotly leaves beneath its
    tick labels; without it the line sits low enough to read as a
    separate paragraph.
    """
    # c-301, Bill: *"why doesn't 135 of 135 paths drawn sit in
    # the middle?"* Because it was centred on the CONTAINER and
    # the plot is not. design.chart insets the figure by its own
    # margins — section 2 carries the widest left margin of any
    # chart on the page, for the "cumulative return (%)" axis
    # title — so the plot's centre sits right of the container's
    # and a container-centred caption reads as left-shifted.
    # Padding the short side by the margin difference moves the
    # text centre onto the PLOT centre, which is what the eye
    # compares it against.
    pad = ""
    try:
        m = fig.layout.margin
        l, r = float(m.l or 0), float(m.r or 0)
        if abs(l - r) >= 1:
            side = "left" if l > r else "right"
            pad = f"padding-{side}:{abs(l - r):.0f}px;"
    except Exception:                              # noqa: BLE001
        pad = ""
    st.markdown(
        f"<p style='font-size:.8rem;color:{MUTED};margin:"
        f"-.55rem 0 .55rem;{pad}text-align:center'>{html}</p>",
        unsafe_allow_html=True)


def _adv_note(extra=""):
    st.markdown(
        f"<p style='font-size:.78rem;color:{FAINT};margin:"
        f".15rem 0 .1rem'>{ADV_NOTE}"
        f"{' ' + extra if extra else ''}</p>",
        unsafe_allow_html=True)


MIN_N_AT_OFFSET = 5

# how many individual event paths to draw before thinning. Past
# a few hundred translucent lines the chart stops adding
# information and starts costing render time; the aggregate on
# top is always computed on the full selection regardless.
MAX_SPAGHETTI = 250

# after the volume path runs out, assume the name is back to
# normal turnover. Measured, not assumed to be generous: median
# volume is already back to about 2x ADV the session after the
# effective date, so 1.0 is the conservative floor a schedule
# should plan on rather than an optimistic tail.
TAIL_MULT = 1.0
MAX_SESSIONS = 30


def sessions_to_fill(vpath, i_eff, order_days, participation):
    """How many sessions to work `order_days` of ADV, starting
    on the effective day, at a participation cap.

    Uses THIS EVENT'S OWN volume path rather than a flat ADV
    assumption. That matters: the effective day carries roughly
    twelve times normal volume in Taiwan and the next session
    about two, so a model that spreads an order over "n days of
    ADV" understates what the print absorbs and overstates what
    the week after it can.

    Returns None when the order cannot be filled inside
    MAX_SESSIONS, which is a real answer — it means the order
    is not a schedule, it is a negotiation.

    THOSE Nones ARE CENSORED OBSERVATIONS, NOT MISSING ONES,
    and `censored_median` below is what stops that mattering.
    Dropping them and taking the median of what is left is
    wrong in a way that always flatters: at 10% participation
    on a 5-day order, 71 of Taiwan's 136 events never fill, and
    the median of the 65 that do reads 13 sessions when the
    true median is beyond the horizon entirely.
    """
    if not order_days or participation <= 0:
        return None
    left, k = float(order_days), 0
    while left > 1e-9 and k < MAX_SESSIONS:  # noqa: E501
        j = i_eff + k
        m = None
        if vpath is not None and 0 <= j < len(vpath):
            m = vpath[j]
        if m is None or m != m:
            m = TAIL_MULT
        left -= participation * m
        k += 1
    return k if left <= 1e-9 else None


def censored_median(filled, n_unfilled):
    """(value, is_censored) for a set with right-censoring.

    A median survives censoring as long as fewer than half the
    observations are censored: order everything, put the
    unfilled at the top since they are all larger than any
    filled value, and read the middle. If the middle lands
    among the unfilled, the honest answer is "beyond the
    horizon", not a number.
    """
    n = len(filled) + n_unfilled
    if not n:
        return None, False
    if n_unfilled * 2 >= n:
        return None, True
    xs = sorted(filled)
    i = (n - 1) / 2
    lo, hi = int(i), min(int(i) + 1, len(xs) - 1)
    return xs[lo] + (xs[hi] - xs[lo]) * (i - int(i)), False


def _path_series(sub, offsets, kind):
    """(y, n) per offset for one subset.

    An offset is left EMPTY below MIN_N_AT_OFFSET rather than
    plotted thin. The window lengths are ragged at the far right
    — 2,175 events reach day +20 but only 1,771 reach day +40 —
    so without a floor the line would keep going and quietly
    become the median of whichever handful of markets happen to
    have the longest windows.
    """
    paths = [r for r in sub["path"] if isinstance(r, list)]
    ys, ns = [], []
    for i in range(len(offsets)):
        vals = [p[i] for p in paths
                if p[i] is not None and p[i] == p[i]]
        ns.append(len(vals))
        ys.append(_stat(vals, kind, 50)
                  if len(vals) >= MIN_N_AT_OFFSET else None)
    return ys, ns


def _dots(names, series, ytitle, fmt=".1%", height=380,
          xaxis=None, labels=None):
    """The page's one chart shape: a dot per group per statistic.

    c-279, Bill: *"can you change the bar graph to a dot graph
    design like section 4?"* One chart grammar across the page
    means a reader learns to read it once. Each statistic is its
    own colour, dash and marker, so the series stay apart in
    print and for anyone who cannot separate navy from amber.

    WHAT THIS COST, recorded because it is not free: section 2
    was an HTML bar chart with a hover card that listed the
    names behind each bar and survived the mouse entering it.
    A plotly dot cannot hold a list, so the per-name detail is
    gone and the hover carries n instead.
    """
    # c-313, Bill: *"we accidentally removed the month label in
    # the hover."* THE CAUSE, because it will recur otherwise.
    # c-284 made the review axis NUMERIC — x is a decimal year,
    # Feb-2015 -> 2015.08 — so `%{x}` in a hovertemplate stopped
    # printing "Feb-15" and started printing 2015.0833333. The
    # tick change was innocent; the hover had been reading the
    # x VALUE all along and nobody noticed while x was still the
    # label.
    #
    # So the label travels in `customdata` rather than being
    # recovered from the axis. customdata, not `text`: a bar
    # trace RENDERS its `text` on the chart by default, and the
    # bar chart in section 5 needs the same treatment as these
    # dots. One mechanism for both.
    fig = go.Figure()
    for label, ys, extra in series:
        cd = (list(zip(labels, extra)) if labels is not None
              else extra)
        head = ("%{customdata[0]}" if labels is not None
                else "%{x}")
        n = ("%{customdata[1]}" if labels is not None
             else "%{customdata}")
        fig.add_scatter(
            x=names, y=ys, mode="markers+lines",
            name=label,
            line=dict(width=1, color=STAT_COLOUR.get(label, NAVY),
                      dash=STAT_DASH.get(label)),
            marker=dict(size=9,
                        color=STAT_COLOUR.get(label, NAVY),
                        symbol=STAT_MARK.get(label, "circle")),
            customdata=cd,
            # c-334: section 3 is the only caller, so the
            # eyebrow can name what a dot IS — one review — even
            # though the helper itself is generic.
            hovertemplate=design.hover(
                head, eyebrow="index review",
                rows=[(label.lower(), "%{y:" + fmt + "}"),
                      ("n", n)]))
    fig.update_layout(height=height,
                      yaxis=dict(title=ytitle, tickformat=fmt),
                      xaxis=dict(title="",
                                 **(xaxis or {})))
    return fig


# c-279: `_bar_pop` and POP_CSS are DELETED, not left behind.
#
# Section 2 was an HTML bar chart carrying the hover card from
# the Index Review Database page — a card that listed the names
# behind each bar, scrolled, and survived the mouse entering
# it. Bill asked for section 2 to match section 4's dot design,
# and a plotly dot cannot hold a list, so the card had no chart
# left to sit on.
#
# Removing it rather than keeping it "for later" is the point:
# 130 lines of CSS and geometry that nothing calls is not an
# asset, it is a thing that rots. It is in git history and in
# views/history_explorer.py, which still uses the pattern for
# the chart it was built for.


# ---------------------------------------------------------------
def render():
    # c-281: css() then the title, FIRST — the order every other
    # page uses. The title used to be emitted after the data
    # load, which put it a stylesheet later than its siblings
    # and sat it a few pixels off theirs. It also meant a
    # missing data file showed an st.info with no heading above
    # it.
    design.css()
    st.markdown("# Index Rebalance Daily Data")
    df, d = _frame(_stamp())
    if df is None:
        st.info("Run `py scripts\\apac_panel_events.py` to build "
                "the panel.")
        return
    labels = d["review_labels"]
    safe = set(d["delisted_safe"])
    offsets = d.get("path_offsets") or []

    # ---- 1 ------------------------------------------------
    design.sect(1, "Data Review",
                "How the stock trades before and after its "
                "index review, measured from daily bars")
    design.caveat(
        "<b>The dataset:</b> for companies added to or deleted "
        "from an MSCI Standard index at a quarterly review, 20 "
        "sessions before the announcement and 20 sessions after "
        "the effective date of daily bar data are collected."
        "<br><br>"
        "<b>Data collected:</b> daily close price and daily "
        "trading volume.")

    # ---- 2 ------------------------------------------------
    design.sect(2, "The Rebalance Window",
                "Cumulative return from the announcement day")
    design.caveat(
        "<b>Day 0 is the announcement day</b>, where "
        "cumulative return indexed at 0. The dashed line "
        "represents the effective date.")
    mkt, lo, hi, kinds, side = _controls(
        "s1", d, default_stats=["Median"], side=True)
    sub = _sided(_slice(df, mkt, lo, hi), side)
    if sub.empty or not offsets:
        _empty()
    else:
        # c-282: ONE LINE PER EVENT, as on the Announcement ->
        # Effective page, with the aggregate drawn over the top.
        #
        # The aggregate alone answers "what usually happens" and
        # hides the thing a desk is sizing against — that the
        # usual is an average of paths which go in opposite
        # directions. The spaghetti alone is unreadable past a
        # few dozen names. Together the median says what to
        # expect and the mesh behind it says how much to trust
        # that, which is the pair the source chart got right.
        SIDES = ([("ADD", "Additions", GREEN),
                  ("DEL", "Deletions", RED)] if side == "Both"
                 else [("ADD" if side == "Additions" else "DEL",
                        side, GREEN if side == "Additions"
                        else RED)])
        fig = go.Figure()
        effs = [int(v) for v in sub["eff_off"]
                if v is not None and v == v]
        drawn, capped = 0, False
        for act, slab, colour in SIDES:
            g = sub[sub.action == act]
            if g.empty:
                continue
            rows = list(g.itertuples())
            if len(rows) > MAX_SPAGHETTI:
                # deterministic thinning — every kth event, so
                # the same selection always draws the same
                # picture. Random sampling would redraw
                # differently on each rerun and a reader would
                # not know whether the shape had changed or the
                # sample had.
                step = len(rows) // MAX_SPAGHETTI + 1
                rows, capped = rows[::step], True
            op = 0.30 if len(rows) > 40 else 0.55
            for r in rows:
                if not isinstance(r.path, list):
                    continue
                drawn += 1
                fig.add_scatter(
                    x=offsets, y=r.path, mode="lines",
                    line=dict(color=colour, width=0.8),
                    opacity=op, showlegend=False,
                    hovertemplate=design.hover(
                        f"{r.code} {r.rev}",
                        eyebrow=slab[:-1].lower(),
                        rows=[("day", "%{x}"),
                              ("cumulative",
                               "%{y:.1f}%")]))
        for act, slab, colour in SIDES:
            g = sub[sub.action == act]
            if g.empty:
                continue
            for k in (kinds or ["Median"]):
                ys, ns = _path_series(g, offsets, k)
                fig.add_scatter(
                    x=offsets, y=ys, mode="lines",
                    # c-289: the statistic is back on the
                    # legend. It was removed as duplication of
                    # the control above, which was wrong once
                    # TWO statistics can be drawn together —
                    # then the legend is the only thing telling
                    # a solid line from a dotted one.
                    name=f"{slab} — {k.lower()}",
                    line=dict(width=3, color=colour,
                              dash=STAT_DASH.get(k)),
                    customdata=ns,
                    # c-334: the old tooltip had no title at all,
                    # so the side becomes one — it is what tells
                    # the two aggregate lines apart.
                    hovertemplate=design.hover(
                        slab, eyebrow="rebalance window",
                        rows=[("day", "%{x}"),
                              ("cumulative", "%{y:.2f}%"),
                              ("n", "%{customdata}")]))
        fig.add_hline(y=0, line_color=RULE, line_width=1)
        fig.add_vline(x=0, line_dash="dot", line_color=MUTED,
                      annotation_text="announcement")
        if effs:
            med_eff = sorted(effs)[len(effs) // 2]
            # c-313, Bill: the "(median day +13)" parenthesis is
            # deleted. The line still SITS at the median offset —
            # that is what `med_eff` is and it has not changed —
            # so the drawing is unaltered; only the label stops
            # spelling out a number the axis underneath already
            # gives.
            fig.add_vline(
                x=med_eff, line_dash="dash", line_color=NAVY,
                annotation_text="effective")
        fig.update_layout(
            height=520, hovermode="closest",
            xaxis=dict(title="trading days from announcement "
                             "date"),
            yaxis=dict(title="cumulative return (%)"))
        design.chart(fig)
        _axis_note(
            f"{drawn:,} of {len(sub):,} paths drawn"
            + (f" — thinned to keep the chart readable; the "
               f"bold median uses ALL {len(sub):,}."
               if capped else "."), fig)

    # ---- 3 ------------------------------------------------
    design.sect(3, "How Big Is the Print",
                "Effective-day volume against normal.")
    mkt, lo, hi, kinds, _sd = _controls(
        "s2", d, default_stats=["Median"])
    sub = _slice(df, mkt, lo, hi)
    if sub.empty:
        _empty()
    else:
        groups = _groups(sub, mkt, labels)
        names = [lab for lab, _g in groups]
        ns = [int(g["t_mult"].notna().sum()) for _lab, g in groups]
        series = [(k, [_stat(g["t_mult"].tolist(), k, 50)
                       for _lab, g in groups], ns)
                  for k in (kinds or ["Median"])]
        xs, xax = _time_x(groups, mkt)
        design.chart(_dots(xs, series, "multiple of ADV",
                           fmt=".1f", xaxis=xax, labels=names))
        parts = [f"{k.lower()} <b>{_stat(sub['t_mult'].tolist(), k, 50):.1f}x</b>"
                 for k in kinds
                 if _stat(sub["t_mult"].tolist(), k, 50) is not None]
        # c-285: centred under the axis. It is a summary of the
        # whole chart, not a note about its left edge, and left
        # alignment made it read as a caption on the first bar.
        _axis_note(
            f"Across the whole selection: "
            f"{' &nbsp;·&nbsp; '.join(parts)}"
            f" &nbsp;·&nbsp; number of data points = "
            f"<b>{len(sub):,}</b>", fig)
        _adv_note()

    # ---- 4 ------------------------------------------------
    design.sect(4, "Volume Around the Effective Date",
                "Daily volume as a multiple of ADV, aligned on "
                "the effective date.")
    mkt, lo, hi, kinds, side = _controls(
        "s4", d, default_stats=["Median"], side=True)
    sub = _sided(_slice(df, mkt, lo, hi), side)
    if sub.empty or not offsets:
        _empty()
    else:
        # aligned on the EFFECTIVE date, not the announcement.
        # The announcement-to-effective gap runs 5 to 17
        # sessions, so an announcement-aligned volume chart
        # smears the one spike every event has across twelve
        # columns and shows no spike at all.
        LO, HI = -10, 20
        rel = list(range(LO, HI + 1))
        i0 = offsets.index(0) if 0 in offsets else 20
        SIDES = ([("ADD", "Additions", GREEN),
                  ("DEL", "Deletions", RED)] if side == "Both"
                 else [("ADD" if side == "Additions" else "DEL",
                        side, GREEN if side == "Additions"
                        else RED)])
        fig = go.Figure()
        for act, slab, colour in SIDES:
            g = sub[sub.action == act]
            if g.empty:
                continue
            for k in (kinds or ["Median"]):
                ys, ns = [], []
                for t in rel:
                    vals = []
                    for r in g.itertuples():
                        if (r.vpath is None
                                or r.eff_off is None
                                or r.eff_off != r.eff_off):
                            continue
                        j = i0 + int(r.eff_off) + t
                        if 0 <= j < len(r.vpath) and \
                                r.vpath[j] is not None:
                            vals.append(r.vpath[j])
                    ns.append(len(vals))
                    ys.append(_stat(vals, k, 50)
                              if len(vals) >= MIN_N_AT_OFFSET
                              else None)
                fig.add_scatter(
                    x=rel, y=ys, mode="lines",
                    # c-289: restored, same reason as section 2
                    # — with two statistics selectable the
                    # legend is what distinguishes them.
                    name=f"{slab} — {k.lower()}",
                    line=dict(width=2, color=colour,
                              dash=STAT_DASH.get(k)),
                    customdata=ns,
                    hovertemplate=design.hover(
                        slab, eyebrow="effective-day volume",
                        rows=[("days from effective", "%{x}"),
                              ("volume", "%{y:.2f}x ADV"),
                              ("n", "%{customdata}")]))
        fig.add_hline(y=1, line_color=RULE, line_width=1,
                      annotation_text="normal (1x ADV)")
        fig.add_vline(x=0, line_dash="dash", line_color=NAVY,
                      annotation_text="effective")
        fig.update_layout(
            height=400,
            xaxis=dict(title="trading days from the effective "
                             "date"),
            yaxis=dict(title="volume (x ADV)"))
        design.chart(fig)
        _adv_note()

    # ---- 5 ------------------------------------------------
    design.sect(5, "How Many Stocks Trade Above Normal Liquidity",
                "Percentage of names whose effective-day volume "
                "reaches the threshold user set.")
    c1, c2 = st.columns([3.4, 1.1])
    with c1:
        mkt, lo, hi, _k, _sd = _controls("s5", d, stats=False)
    with c2:
        thr = st.number_input("Threshold (× ADV)", 1.0, 20.0,
                              2.0, 0.5, key="s5_thr")
    sub = _slice(df, mkt, lo, hi)
    if sub.empty:
        _empty()
    else:
        # c-279, Bill: state it as the share that CLEARS the
        # threshold, not the share that fails it. Same data, and
        # the complement of the old number — but "38% traded
        # above 2x ADV" is a capacity statement a desk can act
        # on, where "62% printed under 2x" is a statement about
        # what did not happen.
        groups = _groups(sub, mkt, labels)
        names, ys, ns = [], [], []
        for lab, g in groups:
            t = [v for v in g["t_mult"] if v is not None and v == v]
            if not t:
                continue
            names.append(lab)
            ys.append(sum(1 for v in t if v >= thr) / len(t))
            ns.append(len(t))
        # c-280: bars, not dots. Bill asked for this one back.
        # It is right — the other charts plot a LEVEL that moves
        # continuously, where this plots a SHARE of a count. A
        # line joining two shares implies the value in between
        # meant something, and it did not.
        fig = go.Figure()
        # c-313: the review label rides in customdata — see the
        # note in `_dots`. `%{x}` would print a decimal year once
        # `_time_x` swaps the axis below.
        fig.add_bar(x=names, y=ys, marker_color=NAVY,
                    marker_line_width=0,
                    customdata=list(zip(names, ns)),
                    hovertemplate=design.hover(
                        "%{customdata[0]}",
                        eyebrow="index review",
                        rows=[("reached " + f"{thr:g}× ADV",
                               "%{y:.0%}"),
                              ("n", "%{customdata[1]}")]))
        # c-285, Bill asked what chart type suits a
        # DISCONTINUOUS series. Bars, with the width pinned to
        # the sampling interval.
        #
        # A line would be wrong: it draws a segment between two
        # reviews and so asserts a value for every day in
        # between, when the series only exists four times a
        # year. Bars carry the opposite claim — this value
        # belongs to THIS interval and nowhere else — which is
        # what a quarterly observation actually is.
        #
        # The width has to be set explicitly on a numeric time
        # axis. Plotly's default sizes bars from the smallest
        # gap it finds, so one missing review would make every
        # bar on the chart narrower. Pinning it to just under a
        # quarter means a bar always occupies its own quarter
        # and a review the panel lacks shows as white space
        # rather than being closed up.
        xs, xax = _time_x([(n2, None) for n2 in names], mkt)
        fig.data[0].x = xs
        if _axis(mkt) == "review":
            fig.data[0].width = 0.22          # years, of 0.25
        fig.update_layout(
            height=340, showlegend=False, bargap=0,
            yaxis=dict(title=f"share reaching {thr:g}×",
                       tickformat=".0%"),
            xaxis=dict(title="", **xax))
        design.chart(fig)
        t_all = [v for v in sub["t_mult"]
                 if v is not None and v == v]
        share = sum(1 for v in t_all if v >= thr) / len(t_all)
        # c-289: the headline is a summary of the whole chart,
        # so it sits centred under the axis; the ADV definition
        # stays left, where a footnote belongs.
        _axis_note(
            f"<b>{share:.0%}</b> of this selection traded at or "
            f"above {thr:g}× ADV on the effective day.", fig)
        _adv_note()

    # ---- 6 ------------------------------------------------
    design.sect(6, "Effective-Day Risk",
                "How far a name moves on the effective day.")
    mkt, lo, hi, kinds, side = _controls(
        "s6", d, default_stats=["Median", "90th percentile"],
        side=True,
        # c-279: the tail belongs HERE and only here. This is
        # the risk carried into the close, and the 90th
        # percentile is the number a desk quotes to a client —
        # the median is the day you plan for.
        stat_options=["Median", "Mean", "90th percentile"])
    sub = _sided(_slice(df, mkt, lo, hi), side)
    if sub.empty:
        _empty()
    else:
        # c-277, Bill: split by addition and deletion. Pooling
        # them was hiding the one asymmetry a desk cares about
        # — a forced seller into a name nobody has to own is
        # not the mirror of a forced buyer, and the pooled
        # median averaged the two into a number describing
        # neither.
        SIDES = ([("ADD", "Additions", GREEN),
                  ("DEL", "Deletions", RED)] if side == "Both"
                 else [("ADD" if side == "Additions" else "DEL",
                        side, GREEN if side == "Additions"
                        else RED)])
        groups = _groups(sub, mkt, labels)
        names = [lab for lab, _g in groups]
        fig = go.Figure()
        for act, slab, colour in SIDES:
            for k in (kinds or ["Median"]):
                ys = [_stat([abs(v) for v in
                             g[g.action == act]["eff_day"]
                             if v is not None and v == v], k, 50)
                      for _lab, g in groups]
                fig.add_scatter(
                    x=names, y=ys, mode="markers+lines",
                    name=f"{slab} — {k.lower()}",
                    line=dict(width=1, color=colour,
                              dash=STAT_DASH.get(k)),
                    marker=dict(size=9, color=colour,
                                symbol=STAT_MARK.get(k, "circle")),
                    # c-313: see `_dots` — the label cannot come
                    # from `%{x}` on a numeric review axis.
                    customdata=names,
                    hovertemplate=design.hover(
                        "%{customdata}",
                        eyebrow="effective-day risk",
                        rows=[(slab.lower(), "%{y:.2%}")]))
        xs, xax = _time_x(groups, mkt)
        for tr in fig.data:
            tr.x = xs
        fig.update_layout(
            height=380,
            yaxis=dict(title="|effective-day move|",
                       tickformat=".1%"),
            xaxis=dict(title="", **xax))
        design.chart(fig)
        # c-289: the reader has to know this is |move|. A
        # median of signed effective-day returns would be near
        # zero because additions rise and deletions fall, and
        # the chart would say the print is harmless.
        _axis_note("Each event's effective-day return is taken "
                   "as an <b>absolute value</b>.", fig)
        _adv_note()
