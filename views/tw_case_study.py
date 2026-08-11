"""Taiwan Case Study — the close, and the order that goes into it.

TAIWAN ONLY, and that is a decision rather than a default
(c-323). Every section here measures one market. The intraday
sections were cross-market until this pass — and that comparison
earned its keep, because it is how the data-quality problem was
found: Taiwan and Hong Kong resolve their closing auction and
Japan, Korea, Australia, China and India do not. That verdict now
lives in `scripts/ib_auction_reharvest.py` and in docs/, which is
where a per-venue judgement belongs. What the page shows instead
is Taiwan's own 43 events, individually, with their dispersion —
which a cross-section cannot show and a desk sizing one trade
actually needs.

WHAT THIS PAGE NO LONGER CARRIES. Nine sections built on the
daily panel — the borrow headline, the squeeze split, the
crowding trend, the price-limit study, the addition anatomy, the
schedule comparison and the negative results — were removed at
Bill's request. None of the analysis is deleted. It is still
generated, still tested, and still written up in
docs/TW_CASE_STUDY.md and docs/TW_ADDITION_STUDY.md, with every
figure in data/tw_case_study.json and
data/tw_addition_study.json. Restoring a section is a route and a
call; recovering deleted work is not.

THE ARGUMENT THE PAGE MAKES, IN ORDER:
  1-4  what the Taiwanese close does on an index day, measured
       four ways, from IB 5-minute bars and TWSE's own 5-second
       auction file;
  5    how big the August order is in units of that close;
  6    what the history says happens to the names, if MSCI adds
       them.
"""
import json
from pathlib import Path

import plotly.graph_objects as go
import streamlit as st

from views import design

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "data" / "tw_case_study.json"

NAVY, GREEN, RED = design.NAVY, design.GREEN, design.RED
FAINT, MUTED, RULE = design.FAINT, design.MUTED, design.RULE
AMBER, INK = design.AMBER, design.INK


def _stamp():
    """See apac_panel._stamp — c-287. A no-argument cache serves
    a stale file forever, which once made a fixed bug look
    unfixed."""
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


ADD_SRC = ROOT / "data" / "tw_addition_study.json"
SCN_SRC = ROOT / "data" / "aug26_scenarios.json"


def _add_stamp():
    out = []
    for p in (ADD_SRC, SCN_SRC):
        try:
            s_ = p.stat()
            out.append((s_.st_mtime_ns, s_.st_size))
        except OSError:
            out.append((0, 0))
    return tuple(out)


@st.cache_data(show_spinner=False)
def _load_addition(stamp=None):
    """Both files, or neither — sections 8-12 are one argument and
    half of it would be a page that reasons from history to a
    forecast that is not there."""
    if not (ADD_SRC.exists() and SCN_SRC.exists()):
        return None, None
    return (json.loads(ADD_SRC.read_text(encoding="utf-8")),
            json.loads(SCN_SRC.read_text(encoding="utf-8")))


PP_SRC = ROOT / "data" / "tw_prepositioning.json"


def _pp_stamp():
    try:
        s_ = PP_SRC.stat()
        return (s_.st_mtime_ns, s_.st_size)
    except OSError:
        return (0, 0)


@st.cache_data(show_spinner=False)
def _load_prepos(stamp=None):
    if not PP_SRC.exists():
        return None
    return json.loads(PP_SRC.read_text(encoding="utf-8"))


AUM_SRC = ROOT / "data" / "tw_tracking_aum.json"


def _aum_stamp():
    try:
        s_ = AUM_SRC.stat()
        return (s_.st_mtime_ns, s_.st_size)
    except OSError:
        return (0, 0)


@st.cache_data(show_spinner=False)
def _load_aum(stamp=None):
    """scripts/tw_tracking_aum.py — the sourced anchors and the
    flow-revealed estimate that the section-7 slider sits on."""
    if not AUM_SRC.exists():
        return None
    return json.loads(AUM_SRC.read_text(encoding="utf-8"))


MAND_SRC = ROOT / "data" / "tw_mandate_size.json"


def _mand_stamp():
    try:
        s_ = MAND_SRC.stat()
        return (s_.st_mtime_ns, s_.st_size)
    except OSError:
        return (0, 0)


@st.cache_data(show_spinner=False)
def _load_mandate(stamp=None):
    """scripts/tw_mandate_size.py — MSCI's own Q2 2026 filings
    and earnings-call disclosure, turned into an estimate of the
    indexed money that must buy a Taiwan Standard addition."""
    if not MAND_SRC.exists():
        return None
    return json.loads(MAND_SRC.read_text(encoding="utf-8"))


FB_SRC = ROOT / "data" / "tw_foreign_baseline.json"


def _fb_stamp():
    try:
        s_ = FB_SRC.stat()
        return (s_.st_mtime_ns, s_.st_size)
    except OSError:
        return (0, 0)


@st.cache_data(show_spinner=False)
def _load_foreign_baseline(stamp=None):
    """scripts/tw_foreign_baseline.py — foreign flow by phase of
    the rebalance window, as a multiple of the same stock's own
    normal day."""
    if not FB_SRC.exists():
        return None
    return json.loads(FB_SRC.read_text(encoding="utf-8"))


PB_SRC = ROOT / "data" / "tw_tracker_playbook.json"


def _pb_stamp():
    try:
        s_ = PB_SRC.stat()
        return (s_.st_mtime_ns, s_.st_size)
    except OSError:
        return (0, 0)


@st.cache_data(show_spinner=False)
def _load_playbook(stamp=None):
    if not PB_SRC.exists():
        return None
    return json.loads(PB_SRC.read_text(encoding="utf-8"))


LIM_SRC = ROOT / "data" / "tw_limit_moves.json"


def _lim_stamp():
    try:
        st_ = LIM_SRC.stat()
        return (st_.st_mtime_ns, st_.st_size)
    except OSError:
        return (0, 0)


@st.cache_data(show_spinner=False)
def _load_limits(stamp=None):
    if not LIM_SRC.exists():
        return None
    return json.loads(LIM_SRC.read_text(encoding="utf-8"))


VR_SRC = ROOT / "data" / "tw_volume_revealed_aum.json"
TR_SRC = ROOT / "data" / "tw_tracker_replication.json"


def _vr_stamp():
    out = []
    for p in (VR_SRC, TR_SRC):
        try:
            st_ = p.stat()
            out.append((st_.st_mtime_ns, st_.st_size))
        except OSError:
            out.append((0, 0))
    return tuple(out)


@st.cache_data(show_spinner=False)
def _load_aum_crosschecks(stamp=None):
    """The two c-375 cross-checks on the AUM basis: the close's
    own volume inverted into revealed AUM, and the fund-by-fund
    replication of the ETF slice."""
    vr = (json.loads(VR_SRC.read_text(encoding="utf-8"))
          if VR_SRC.exists() else None)
    tr = (json.loads(TR_SRC.read_text(encoding="utf-8"))
          if TR_SRC.exists() else None)
    return vr, tr


DB_SRC = ROOT / "data" / "tw_deletion_borrow.json"


def _db_stamp():
    try:
        st_ = DB_SRC.stat()
        return (st_.st_mtime_ns, st_.st_size)
    except OSError:
        return (0, 0)


@st.cache_data(show_spinner=False)
def _load_del_borrow(stamp=None):
    if not DB_SRC.exists():
        return None
    return json.loads(DB_SRC.read_text(encoding="utf-8"))


def _pc(v, f="{:+.2%}"):
    return f.format(v) if v is not None else "—"


def _note(txt):
    # c-401, Bill: left-aligned — both callers are numbered
    # multi-line Notes now, and a centred list reads ragged.
    st.markdown(
        f"<p style='font-size:.8rem;color:{MUTED};margin:"
        f".1rem 0 .5rem;text-align:left'>{txt}</p>",
        unsafe_allow_html=True)


def render():
    design.css()
    st.markdown("# Taiwan Case Study")
    # c-323, Bill: SECTIONS 1-9 ARE REMOVED and the intraday
    # charts lead the page.
    #
    # WHAT WENT AND WHERE IT LIVES NOW. Nine sections built on the
    # DAILY panel — the borrow headline, the squeeze split, the
    # crowding trend, the price-limit study, the addition anatomy,
    # the schedule comparison and the negative results — are off
    # this page. Every one of them is still generated, still
    # tested, and still written up:
    #
    #   docs/TW_CASE_STUDY.md        the borrow join and the limits
    #   docs/TW_ADDITION_STUDY.md    the addition anatomy, the
    #                                schedules, the era split and
    #                                the out-of-sample result
    #   data/tw_case_study.json      every figure behind them
    #   data/tw_addition_study.json
    #
    # A route is one line to restore; the analysis is not being
    # deleted, the page is being narrowed to what a reader can
    # act on without decoding it first.
    #
    # THE PAGE IS NOW TAIWAN-ONLY AND SAYS SO. The intraday
    # sections used to be cross-market — that comparison is what
    # found the data-quality problem in the first place — and are
    # rebuilt around Taiwan's own 43 events with their dispersion.
    from views import intraday_panel
    _used = intraday_panel.sections(1) or 0

    # Loaded once, up here, because BOTH remaining sections read
    # it — the capacity ladder needs the demand assumptions and
    # the August section needs the scenarios.
    ADD, SCN = _load_addition(_add_stamp())

    # ---- foreign flow vs a normal day (c-357) ---------------
    #
    # Bill: can we measure daily foreign net buying for
    # index-change stocks ON the effective date, against normal
    # times — and ideally the whole window, before the
    # announcement and after the effective date?
    #
    # YES, AND THE BASELINE WAS THE MISSING PIECE. The phase
    # aggregates existed in the addition study; what nothing on
    # the site had was the yardstick that makes them readable —
    # each stock's OWN normal day, measured over the 100 sessions
    # ending 21 before its announcement. With phases converted to
    # per-session rates the comparison is finally one unit, and
    # the answer is sharp: the pre and mid phases sit INSIDE the
    # normal range; the flow lands on the effective day.
    FB = _load_foreign_baseline(_fb_stamp())
    _fb = 0
    if FB:
        _fb = 1
        design.sect(_used + 1,
                    "Foreign Flow Through the Rebalance Window",
                    "Daily foreign net buying by phase, as a "
                    "multiple of the same stock's own normal day")
        A_fb = FB["sides"]["ADD"]
        D_fb = FB["sides"]["DEL"]
        # c-359, Bill: the "A normal day / 8% of ADV" card is
        # off. The baseline still exists — it is the DENOMINATOR
        # of every multiple on the chart and stays in the hover
        # and the doc — but as a headline card it read as a
        # finding, and it is a yardstick.
        design.stats([
            {"k": "Effective day, additions",
             "v": f"{A_fb['x_normal']['eff']['p50']:+.1f}\u00d7",
             "s": f"a normal day \u00b7 n={A_fb['n']}"},
            {"k": "Effective day, deletions",
             "v": f"{D_fb['x_normal']['eff']['p50']:+.1f}\u00d7",
             "s": f"a normal day \u00b7 n={D_fb['n']}"},
            # c-370, Bill: the post-print card is OFF. The
            # deletion tail survives in the chart's post-phase
            # bar and in the doc.
        ])
        _phases = [("pre", "30 sessions before announcement"),
                   ("mid", "announcement \u2192 effective"),
                   ("eff", "the effective day"),
                   ("post", "10 sessions after")]
        fig = go.Figure()
        for side, col, sd in (("ADD", GREEN, A_fb),
                              ("DEL", RED, D_fb)):
            xs = [sd["x_normal"][ph]["p50"] for ph, _ in _phases]
            fig.add_bar(
                y=[lab for _, lab in _phases][::-1],
                x=xs[::-1], orientation="h",
                # c-368, Bill: full words on the legend, matching
                # the volume sections' legends
                name=("Additions" if side == "ADD"
                      else "Deletions"),
                marker_color=col, marker_line_width=0,
                # c-370, Bill: the IQR row and the per-session
                # disclosure are OFF the hover \u2014 three rows, two
                # significant figures each.
                customdata=[[sd["rates_adv"][ph]["p50"] * 100,
                             sd["n"]]
                            for ph, _ in _phases][::-1],
                # c-378, Bill: every hover figure at TWO
                # significant figures \u2014 the deletions'
                # effective-day rate was printing three
                # ("-77.2% of ADV"); d3's .2g trims all of
                # them to two.
                hovertemplate=design.hover(
                    "%{y}",
                    eyebrow=("additions" if side == "ADD"
                             else "deletions"),
                    rows=[("median, \u00d7 a normal day",
                           "%{x:+.2g}\u00d7"),
                          ("flow per session",
                           "%{customdata[0]:+.2g}% of ADV"),
                          ("events", "%{customdata[1]}")]))
        # c-361, Bill asked whether these n's should match the
        # intraday sections'. NO, AND THE DIFFERENCE IS THE
        # INSTRUMENT, NOT A MISTAKE. Sections 1-4 run on IB
        # 5-minute bars, which reach back only to May 2023 — 43
        # Taiwan events. This section runs on the daily T86 flow
        # file, 2015-2026 — 107 events carry flow, and 97 also
        # support a clean pre-event baseline. Forcing this
        # section down to the intraday window would discard
        # two-thirds of its own sample to match a limit it does
        # not have. Each section uses the deepest history its
        # source supports, and the Data Review section names
        # each source.
        fig.add_vline(x=1, line_color=RULE, line_width=1,
                      line_dash="dot")
        fig.add_vline(x=-1, line_color=RULE, line_width=1,
                      line_dash="dot")
        # c-361 put the label inside the band; c-368 moved it to
        # the top of the plot area \u2014 where the first row's bars
        # still ran over it. c-370, Bill: it goes ABOVE the plot
        # entirely, into the top margin beside the legend, where
        # no bar can reach it.
        fig.add_annotation(
            x=0, y=1.02, yref="paper", yanchor="bottom",
            showarrow=False,
            text="\u00b11 normal day band",
            font=dict(size=10.5, color=MUTED))
        fig.update_layout(
            height=310, barmode="group",
            legend=dict(orientation="h", yanchor="bottom",
                        y=1.0, x=0),
            xaxis=dict(title="median foreign net flow per "
                             "session, \u00d7 the stock's own "
                             "normal day"),
            yaxis=dict(title=""),
            # c-370: the top margin holds the legend AND the
            # band label now
            margin=dict(l=0, t=48, b=40))
        design.chart(fig)
        # c-370, Bill: the instrument note (c-368) is off the
        # page again; the per-side n stays in the hover and on
        # the cards.
        design.caveat(
            "On the effective day, the median addition "
            f"draws <b>{A_fb['x_normal']['eff']['p50']:.1f}"
            "\u00d7</b> the stock's normal day and the median "
            "deletion prints "
            f"<b>{D_fb['x_normal']['eff']['p50']:.1f}\u00d7</b>, "
            "reflecting the same one-day concentration shown "
            "in the volume chart above.")

    # ---- has anyone bought them yet? (c-326) ----------------
    PP = _load_prepos(_pp_stamp())
    _pre = 0
    if PP:
        _pre = 1
        W = PP["windows"]["20"]
        B = PP["historical_benchmark"]
        design.sect(_used + 1 + _fb,
                    # c-370, Bill: the addition half of the
                    # positioning pair — the deletion half (the
                    # borrow) follows it.
                    "Market Positioning Before Announcement "
                    "Day — Addition",
                    "Foreign flow into the candidates for "
                    "index addition, compared against other "
                    "large caps over the same sessions")
        # c-334, Bill: *"the ADV days unit needs to be rewritten.
        # People don't associate this with volume unit right
        # away."* He is right — "0.60 ADV days" reads as a
        # duration. It is not: it is a QUANTITY OF SHARES,
        # expressed in units of one normal day's total trading
        # volume in that name.
        #
        # And it is a SUM, not a rate. `tot_f[c] / adv[c]` in
        # tw_prepositioning.py adds twenty daily net figures and
        # divides once by a single day's ADV — so +0.60 means
        # foreigners bought, in net and across the whole twenty
        # sessions, shares worth 0.60 of ONE normal day's volume.
        # Nothing on the card said either of those things.
        UNIT = " \u00d7 a normal day's volume"
        design.stats([
            # c-341, Bill: the historical benchmark comes off
            # the card row. It is still ON the chart as the
            # dotted reference line, which is where a reader
            # compares it against the three candidates rather
            # than reading it as a fourth measurement of them.
            {"k": "Peer companies draw",
             "v": f"{W['peer_foreign_adv_days']['p50']:+.2f}\u00d7",
             "s": f"median of {W['peer_set_n']} large cap "
                  f"companies, from the same 20 sessions"},
            # c-335: kind="num" keeps the serif figure treatment
            # that design.stats would otherwise drop for a value
            # this long. See the note in design.stats.
            {"k": "Index review candidates draw", "kind": "num",
             "v": f"{min(r['foreign_adv_days'] for r in W['names'].values()):+.2f}"
                  f" to "
                  f"{max(r['foreign_adv_days'] for r in W['names'].values()):+.2f}\u00d7",
             "s": "all below the peer median"},
        ])
        fig = go.Figure()
        peers_p50 = W["peer_foreign_adv_days"]["p50"]
        nm = sorted(W["names"].items(),
                    key=lambda kv: kv[1]["foreign_adv_days"])
        fig.add_bar(
            y=[f"{r['name'][:24]} ({c})" for c, r in nm],
            x=[r["foreign_adv_days"] for _c, r in nm],
            orientation="h", marker_color=RED,
            marker_line_width=0, name="candidates",
            customdata=[[r["foreign_percentile"],
                         r["domestic_adv_days"]] for _c, r in nm],
            hovertemplate=design.hover(
                "%{y}", eyebrow="foreign flow",
                # c-338, Bill: two significant figures. These
                # are numbers around 1, so `g` keeps two digits
                # below 1.0 and drops to one decimal above it,
                # which is what "2 sig figs" means here.
                rows=[("foreign net",
                       "%{x:+.2g}" + UNIT),
                      ("peer percentile", "%{customdata[0]:.0%}"),
                      ("domestic net",
                       "%{customdata[1]:+.2g}" + UNIT)],
                note="net, summed over the 20 sessions"))
        # c-338, Bill: both reference lines labelled the same
        # way, both at the TOP. They are the same kind of thing —
        # a benchmark the candidates get read against — and one
        # styled like a heading beside one hanging below the plot
        # invited a reader to rank them.
        _ADD_REF = B["foreign_pre_announcement_adv_days"]["p50"]
        for _x, _col, _lab, _dash in (
                (peers_p50, NAVY, "peer median", None),
                (_ADD_REF, GREEN, "typical index addition", "dot")):
            fig.add_vline(
                x=_x, line_color=_col, line_width=2,
                line_dash=_dash,
                annotation_text=f"{_lab} {_x:+.2f}",
                annotation_position="top",
                annotation_font=dict(size=11, color=_col))
        fig.add_vline(x=0, line_color=RULE, line_width=1)
        fig.update_layout(
            height=290, showlegend=False,
            xaxis=dict(title="foreign net buying over the 20 "
                             "sessions to "
                             + PP["flow_data_to"]
                             + ", in multiples of one normal "
                               "day's volume"),
            yaxis=dict(title=""), margin=dict(l=0, t=50, b=40))
        design.chart(fig)
        # c-401, Bill: same numbered bold-Note grammar as the
        # sizing table's note.
        _note("<b>Note:</b><br>"
              f"1. Peer set = the {W['peer_set_n']} largest "
              "companies listed on the TWSE, which publishes "
              "daily buying and selling by foreign and other "
              "investor types.<br>"
              "2. A reading of 1.00\u00d7 means net buying equal "
              "to one normal day's total volume in that stock, "
              "accumulated across all 20 sessions.")
        # c-343, Bill: use 2026-08-07.
        #
        # RECORDED SO A LATER READER IS NOT MISLED. The T86 flow
        # file ends 2026-08-05; 08-07 is the last day in the
        # turnover file and the TDCC dispersion stamp. Bill has
        # made the call to quote 08-07 as the "as at" date for
        # the section, so it is written here as a literal rather
        # than read from PP["flow_data_to"] — which means it will
        # NOT move when the flow harvest advances. Anyone
        # re-running this should check both.
        # c-370, Bill's wording: the volatility sentence and the
        # TPEx qualifier are cut.
        design.caveat(
            "All three candidates for addition sat <b>BELOW "
            "the peer median</b> for foreign net buying over "
            "the 20 sessions to 2026-08-07, while "
            "foreigners were <b>net BUYERS of the peer set</b>, "
            "the 100 largest companies listed on the TWSE. For "
            "context, a typical Taiwan index addition draws <b>"
            f"{B['foreign_pre_announcement_adv_days']['p50']:+.2f}"
            "\u00d7 a normal day's volume</b> of foreign buying in "
            "the 20 sessions before its announcement.")

    # ---- the deletion's footprint (c-368) --------------------
    #
    # Bill: the call carries one border deletion, Caliway 6919,
    # P(delete) 36%. A fund positioned for it is SHORT, a short
    # needs a borrow, and TWSE publishes every name's SBL balance
    # daily — so if the trade is crowded, THIS series says so.
    DB = _load_del_borrow(_db_stamp())
    _db = 0
    if DB:
        _db = 1
        L_ = DB["latest"]
        C_ = DB["change"]
        _lb = DB["lending_began"]
        _lb_iso = f"{_lb[:4]}-{_lb[4:6]}-{_lb[6:]}"
        # c-370, Bill: retitled as the deletion half of the
        # positioning pair, and it sits directly under the
        # addition half.
        design.sect(_used + 1 + _pre + _fb,
                    "Market Positioning Before Announcement "
                    "Day — Deletion",
                    "Securities-lending balance of the "
                    "candidates for index deletion")
        # c-376, Bill: both cards value-only, one format — the
        # ADV multiple and the returned/built read move to the
        # caveat's prose.
        design.stats([
            # kind="num" on both: the change card's 13-character
            # value would otherwise trip the phrase treatment
            # and the two figures would render in two styles —
            # the exact mismatch Bill asked to avoid.
            {"k": "Borrow balance", "kind": "num",
             "v": f"{L_['balance_shares'] / 1e6:.1f}m shares"},
            {"k": f"Change, last {C_['sessions']} sessions",
             "kind": "num",
             "v": f"{C_['shares'] / 1e6:+.2f}m shares"},
        ])
        fig = go.Figure()
        _ds = [f"{r['d'][:4]}-{r['d'][4:6]}-{r['d'][6:]}"
               for r in DB["series"]]
        fig.add_scatter(
            x=_ds, y=[r["bal"] / 1e6 for r in DB["series"]],
            mode="lines", line=dict(color=NAVY, width=2.2),
            hovertemplate=design.hover(
                DB["name"], eyebrow="SBL borrow balance",
                rows=[("date", "%{x}"),
                      ("on loan", "%{y:.2f}m shares")]))
        fig.update_layout(
            height=300, showlegend=False,
            # c-376, Bill: month-only ticks — the day of the
            # month is noise on a five-month axis; the exact
            # date stays in the hover.
            xaxis=dict(title="", type="date",
                       tickformat="%b %Y", dtick="M1"),
            yaxis=dict(title="shares on loan (millions)"))
        design.chart(fig)
        # c-376, Bill: the caveat leads with the RECENT TREND —
        # the last three months, computed from the series — and
        # mentions the zero-before-March fact briefly. The ADV
        # multiple and the returned/built read move here from
        # the cards.
        _s = DB["series"]
        _ref = _s[-min(63, len(_s))]
        _ref_mon = {
            "01": "January", "02": "February", "03": "March",
            "04": "April", "05": "May", "06": "June",
            "07": "July", "08": "August", "09": "September",
            "10": "October", "11": "November",
            "12": "December"}[_ref["d"][4:6]]
        _chg3m = (L_["balance_shares"] / _ref["bal"] - 1
                  if _ref["bal"] else None)
        # c-385, Bill's two-sentence version: the trend, then
        # the zero-before-March note — everything else is cut.
        design.caveat(
            f"Over the past three months the borrow has been "
            f"<b>steadily unwound</b>: from "
            f"<b>{_ref['bal'] / 1e6:.1f}m shares</b> in early "
            f"{_ref_mon} to "
            f"<b>{L_['balance_shares'] / 1e6:.1f}m</b> "
            f"(<b>{_chg3m:+.0%}</b>), falling "
            f"(<b>{C_['pct']:+.0%}</b>) over the last "
            f"{C_['sessions']} sessions. Note: the data "
            f"extracted from TWSE shows a zero balance "
            f"before {_lb_iso}."
            if _chg3m is not None else
            f"The balance stands at "
            f"<b>{L_['balance_shares'] / 1e6:.1f}m shares</b> "
            f"({C_['pct']:+.0%} over the last "
            f"{C_['sessions']} sessions). Note: the data "
            f"extracted from TWSE shows a zero balance before "
            f"{_lb_iso}.")

    # ---- the tracker's capacity question (c-321) ------------
    PB = _load_playbook(_pb_stamp())
    if PB and SCN:
        # c-351 took the close-share card off this section, and
        # with it the last read of `capacity_model` on the page.
        # The playbook is still the gate for the section — no
        # playbook, no sized names — and the close multiple is
        # still in the chart hover, computed per name from
        # `ordinary_close_shares` rather than from this median.
        # c-325 kept Phison off the chart while its verdict was
        # a coin-flip zone. c-368, Bill: the call is FOUR
        # additions with a per-name Monte Carlo P(add) — Phison
        # prices at 65%, not a shrug — so the playbook now ranks
        # all four and this ladder sizes all four.
        rows = sorted([kv for kv in PB["names"].items()
                       if kv[1].get("capacity_rank")],
                      key=lambda kv: kv[1]["capacity_rank"])
        design.sect(_used + 1 + _pre + _fb + _db,
                    # c-381, Bill: named for what it estimates.
                    "Estimated Trading Volume on the "
                    "Effective Day",
                    "Expected order size at the closing auction "
                    "on the effective day")

        # ── c-347: THE FLOOR, DRAWN AS A SHARE OF ADV ─────────
        #
        # Bill: the bar chart should show what the trackers have
        # to buy AS A SHARE OF THE NAME'S OWN VOLUME, priced off
        # the bottom-up tracking-AUM floor rather than the 180bn
        # constant the demand model had been carrying.
        #
        # THIS IS NOT A COSMETIC CHANGE. The 180 was typed into
        # scripts/event_window_analyze.py as `TRACKING_AUM_USD_B
        # = 180.0  # MSCI TW passive proxy` and never sourced.
        # The floor is SUMMED from published fund assets: USD
        # 31.7bn of Standard EM and ACWI trackers, whose indexes
        # have no small-cap segment, so a Taiwan Standard
        # addition is a new holding for every one of them. That
        # is the number that always applies.
        #
        # It cuts every demand figure by 5.7x — Winbond goes from
        # 1.27x ADV to 0.22x — and the smaller number is the
        # defensible one, because it is the only one with a
        # source under it. Anyone who wants the larger figure has
        # to name the funds it comes from.
        #
        # THE IMI CASE IS NOT PLOTTED. USD 85.5bn applies only
        # where the name enters the IMI from outside rather than
        # being promoted out of Small Cap, which is a per-name
        # fact; a bar that is right half the time is worse than a
        # bar that is right always. It is carried in each
        # expander instead, with its own arithmetic.
        AUMD = _load_aum(_aum_stamp())
        A_ = SCN["assumptions"]
        T_ = (AUMD["method1_bottom_up"]["totals"] if AUMD
              else {"uncapped": 0.0, "family": 0.0})
        # c-349, Bill: *"add an estimate to the size of
        # investment mandate ... make it more conservative, but
        # can show evidence to back up our claim."*
        #
        # THE BASIS MOVES FROM USD 32bn TO USD 60bn, and both
        # corrections that get it there are things the old number
        # was missing rather than opinions about it.
        #
        #   1. The USD 13.4bn of ETFs on the MSCI Taiwan indexes
        #      themselves were not in the always-buys pool. A
        #      stock entering MSCI Taiwan Standard enters the
        #      MSCI Taiwan Index and its 25/50 and 20/35 variants
        #      at the same review — EWT has to buy it exactly as
        #      EEM does. 31.7 + 13.4 = 45.0.
        #
        #   2. MSCI earns ABF revenue on NON-ETF INDEXED FUNDS —
        #      separate accounts, index mutual funds, pension
        #      mandates — and reports the revenue without the
        #      assets. Inverting it at the ETF fee rate implies
        #      at least USD 0.33 of mandate money per dollar of
        #      ETF money, and that inversion is a floor because
        #      institutional mandates pay an index provider LESS
        #      per dollar than a retail ETF does.
        #
        # 45.0 x 1.33 = 60. Every input is in
        # scripts/tw_mandate_size.py with its filing and table.
        #
        # c-400, Bill: "use 0.45bp as the fee rate, and update
        # all estimates." THE BASIS MOVES FROM 60 TO 125. MSCI
        # stated ~USD 5tn of NON-ETF indexed AUM on its Q2 2026
        # call, which replaces the fee-inversion step: 5,000 /
        # 2,818 = 1.77x per ETF dollar (not 0.33x), and the
        # implied non-ETF fee rate is 56.0 x 4 / 5,000bn =
        # 0.45bp -- a fifth of the 2.28bp ETF rate, which is
        # WHY the inversion at the ETF rate was a floor. 45.0 x
        # 2.77 = 125. The 60 survives in the JSON and in the
        # expander as floor_variant.
        MAND = _load_mandate(_mand_stamp())
        TWM = MAND["taiwan"] if MAND else None
        BASIS = (TWM["estimate_always_buys_usd_b"] if TWM
                 else (T_["case_promotion"] if AUMD
                       else A_["tracking_aum_usd_b"]))
        # c-350, Bill: the IMI paragraph and the close-multiple
        # paragraph come OFF all three per-name dropdowns. Each
        # was repeated verbatim three times for a distinction
        # that is the same in all three, and the working is what
        # the dropdown is for. Both survive where they are
        # generated — docs/TW_MANDATE_SIZE.md carries the IMI
        # case and its two worked reviews, and the close multiple
        # is still in the chart hover.

        def _at_basis(code, r):
            """Weight -> dollars -> shares -> share of ADV.

            Recomputed from the index weight rather than scaled
            off the playbook's own `demand_adv_days`, so every
            figure inside an expander is the one the bar above it
            is drawn from. test_tw_case_study_page.py checks the
            two agree."""
            s = SCN["names"][code]
            usd_m = r["index_weight_pct"] / 100 * BASIS * 1000
            sh = usd_m * 1e6 * A_["usd_twd"] / s["last_close_twd"]
            return {"usd_m": usd_m, "shares": sh,
                    "adv_x": sh / r["adv_shares"],
                    "closes": sh / r["ordinary_close_shares"],
                    "px": s["last_close_twd"],
                    "float_cap": s["float_cap_usd_b"]}

        F_ = {c: _at_basis(c, r) for c, r in rows}

        # c-348/c-349: the scope block. Four lines, each a
        # different pot of money, ending on the one the chart is
        # drawn from. The IMI paragraph and the holdings test
        # live in the per-name dropdowns, where they attach to
        # the name they might apply to.
        # c-381, Bill: the 13.4 line is shortened and now SAYS
        # how it relates to the 0.08 (it contains it); the
        # mandate money gets its own explicit line instead of
        # hiding inside the 60; and the 60 line becomes the sum.
        # c-397 cut the title and ETF bullets; c-398, Bill:
        # they return in a new layout \u2014 each bold dollar label
        # on its own line, the roster trimmed, and a summary
        # line before the no-ticker money.
        design.caveat(
            "<b>Tracking AUM Calculation</b>"
            "<br><br>"
            f"<b>USD {T_['uncapped']:.2f}bn:</b><br>"
            "Tracks the UNCAPPED MSCI Taiwan Index \u2014 two "
            "Taiwan-domiciled ETFs, Yuanta 006203 and Fubon "
            "0057."
            "<br><br>"
            f"<b>USD {T_['family']:.1f}bn:</b><br>"
            "Every ETF on the MSCI Taiwan indexes themselves "
            "\u2014 the two uncapped funds above plus the capped "
            "variants, led by iShares EWT. A Standard "
            "addition enters all of these indexes at the "
            "same review."
            "<br><br>"
            f"<b>USD {T_['case_promotion']:.0f}bn:</b><br>"
            "Taiwan sits inside MSCI EM and ACWI STANDARD "
            "trackers (ex. EEM, EMXC). Standard indexes have "
            "no small-cap segment, so the addition is a new "
            "holding for every one of these tracking funds."
            "<br><br>"
            "In total, approximately <b>USD "
            f"{TWM['always_buys_named_etf_usd_b']:.0f}bn</b> "
            "of ETFs track the Taiwan market."
            "<br><br>"
            f"<b>USD "
            f"{BASIS - TWM['always_buys_named_etf_usd_b']:.0f}"
            f"bn:</b><br>"
            "The indexed money not in the form of ETFs \u2014 "
            "separate accounts, index mutual funds, pension "
            "mandates. MSCI disclosed this pool at ~USD 5 "
            "trillion on its Q2 2026 earnings call, which is "
            "1.77\u00d7 its ETF pool. Assuming that non-ETF to "
            "ETF ratio holds for Taiwan, applying 1.77\u00d7 to "
            "the USD 45bn of Taiwan ETFs above derives a "
            "non-ETF pool of USD "
            f"{BASIS - TWM['always_buys_named_etf_usd_b']:.0f}"
            "bn. For more details, see the calculation below."
            "<br><br>"
            f"<b>USD {BASIS:.0f}bn = "
            f"{TWM['always_buys_named_etf_usd_b']:.0f}bn + "
            f"{BASIS - TWM['always_buys_named_etf_usd_b']:.0f}"
            f"bn</b> \u2014 becomes our estimate of all MSCI "
            "Taiwan tracking money."
            if TWM else
            "<b>Tracking AUM Calculation</b>"
            "<br><br>"
            f"<b>USD {BASIS:.0f}bn</b> of named ETFs must buy.")

        # c-396, Bill: the mandate working sits DIRECTLY
        # under the Tracking AUM Calculation it explains,
        # before the stat cards and the chart.
        # c-347, Bill: the four-step derivation moves OUT of a
        # paragraph and into one dropdown per name, in the shape
        # the Predict page already uses for the size ladder.
        #
        # WHY PER NAME AND NOT ONE WORKED EXAMPLE. The old block
        # walked the largest order only, and every other bar was
        # then a number a reader had to trust. Three dropdowns
        # cost nothing when closed and remove the trust step
        # entirely. It also puts the per-name IMI multiplier
        # where it belongs — next to the name it might apply to,
        # rather than as a general remark about the chart.
        if MAND:
            # c-349, Bill asked for the evidence to sit ON the
            # page, in the same dropdown shape as the per-name
            # working. It is first in the row because it is the
            # multiplier every bar below it rests on.
            M_ = MAND["msci_disclosure"]
            N_ = MAND["non_etf_indexed"]
            with st.expander(
                    f"Calculation \u2014 the USD {BASIS:.0f}bn "
                    f"mandate, and where each number comes "
                    f"from"):
                st.markdown(
                    f"**Where the numbers come from.** Every "
                    f"input is MSCI Inc.'s own Q2 2026 "
                    f"reporting for the quarter ended "
                    f"{M_['as_of']}, filed {M_['filed']}.\n\n"
                    f"| Figure | Value | Source |\n"
                    f"| --- | --- | --- |\n"
                    f"| ETF AUM linked to MSCI equity indexes | "
                    f"USD {M_['etf_aum_total_usd_b']:,.0f}bn | "
                    f"8-K Table 7 |\n"
                    f"| Non-ETF indexed AUM | ~USD "
                    f"{M_['non_etf_aum_disclosed_usd_b']:,.0f}"
                    f"bn | Q2-26 earnings call |\n"
                    f"| Quarterly fee revenue, ETFs | USD "
                    f"{M_['abf_etf_usd_m']:,.1f}m | presentation "
                    f"p13 |\n"
                    f"| Quarterly fee revenue, non-ETF indexed "
                    f"funds | USD "
                    f"{M_['abf_non_etf_indexed_usd_m']:,.1f}m | "
                    f"presentation p13 |\n\n"
                    f"**1 \u00b7 The ETFs that must buy.** USD "
                    f"{T_['case_promotion']:.1f}bn of Taiwan "
                    f"exposure inside Standard EM and ACWI "
                    f"trackers, plus USD {T_['family']:.1f}bn "
                    f"of ETFs on the MSCI Taiwan indexes "
                    f"themselves.\n\n"
                    f"`USD {T_['case_promotion']:.1f}bn + USD "
                    f"{T_['family']:.1f}bn = USD "
                    f"{TWM['always_buys_named_etf_usd_b']:.1f}"
                    f"bn`\n\n"
                    f"**2 \u00b7 Non-ETF size.** MSCI "
                    f"now DISCLOSES the non-ETF indexed pool "
                    f"\u2014 ~USD "
                    f"{M_['non_etf_aum_disclosed_usd_b']:,.0f}"
                    f"bn (stated on the Q2 2026 call). "
                    f"Against the ETF pool:\n\n"
                    f"`USD "
                    f"{M_['non_etf_aum_disclosed_usd_b']:,.0f}"
                    f"bn \u00f7 USD "
                    f"{M_['etf_aum_total_usd_b']:,.0f}bn = "
                    f"{N_['multiplier_disclosed']:.2f}\u00d7`\n\n"
                    f"The implied non-ETF fee rate:\n\n"
                    f"`USD "
                    f"{M_['abf_non_etf_indexed_usd_m']:,.1f}m "
                    f"\u00d7 4 \u00f7 USD "
                    f"{M_['non_etf_aum_disclosed_usd_b']:,.0f}"
                    f"bn = {N_['non_etf_bp_derived']:.2f}bp`\n\n"
                    f"**3 \u00b7 Total tracking AUM.**\n\n"
                    f"`USD "
                    f"{TWM['always_buys_named_etf_usd_b']:.1f}bn "
                    f"\u00d7 {TWM['mandate_multiplier']:.2f} = "
                    f"USD {BASIS:.0f}bn`\n\n"
                    f"[Q2 2026 results]"
                    f"({M_['sources']['release']}) \u00b7 "
                    f"[earnings presentation]"
                    f"({M_['sources']['presentation']}) \u00b7 "
                    f"[earnings call]"
                    f"({M_['sources']['earnings_call']})")



        design.stats([
            {"k": "Tracking AUM",
             "v": f"USD {BASIS:.0f}bn",
             "s": "estimate only"},
            {"k": "Largest order",
             "v": f"{F_[rows[0][0]]['adv_x']:.0%} of ADV",
             "s": f"{rows[0][1]['name'][:22]}"},
            {"k": "Smallest order",
             "v": f"{F_[rows[-1][0]]['adv_x']:.0%} of ADV",
             "s": f"{rows[-1][1]['name'][:22]}"},
        ])
        fig = go.Figure()
        fig.add_bar(
            y=[f"{r['name'][:24]} ({c})" for c, r in rows][::-1],
            x=[F_[c]["adv_x"] * 100 for c, _r in rows][::-1],
            orientation="h", marker_color=NAVY,
            marker_line_width=0,
            text=[f"  {F_[c]['adv_x']:.0%}" for c, _r in rows][::-1],
            textposition="outside",
            textfont=dict(size=12, color=NAVY),
            customdata=[[F_[c]["shares"] / 1e6, F_[c]["usd_m"],
                         F_[c]["closes"], r["index_weight_pct"]]
                        for c, r in rows][::-1],
            # c-401, Bill: eyebrow, note and the ordinary-closes
            # row off; "which is" -> "notional amount".
            hovertemplate=design.hover(
                "%{y}",
                rows=[("share of one day's volume", "%{x:.1f}%"),
                      ("shares to buy",
                       "%{customdata[0]:,.1f}m"),
                      ("notional amount",
                       "USD %{customdata[1]:,.0f}m"),
                      ("index weight",
                       "%{customdata[3]:.3f}%")]))
        fig.update_layout(
            height=300, showlegend=False,
            xaxis=dict(title="index demand, as a % of the "
                             "name's average daily volume",
                       range=[0, max(F_[c]["adv_x"] for c, _r
                                     in rows) * 118]),
            yaxis=dict(title=""), margin=dict(l=0, t=16, b=0))
        design.chart(fig)

        # c-386, Bill: the four per-name Calculation dropdowns
        # fold into ONE table in the step-5 call-table grammar \u2014
        # the derivation's four steps become four columns, one
        # row per name. The chart-vs-derivation agreement test
        # re-derives every cell.
        def _sz_hd(label, flex):
            return (f"<span style='flex:{flex};"
                    f"text-align:right;font-size:.62rem;"
                    f"letter-spacing:.11em;text-transform:"
                    f"uppercase;color:#a89c92;font-weight:600'>"
                    f"{label}</span>")
        st.markdown(
            "<div style='display:flex;align-items:baseline;"
            "gap:.55rem;padding:.4rem 0 .3rem'>"
            "<span style='flex:0 0 30px'></span>"
            "<span style='flex:1 1 auto;font-size:.62rem;"
            "letter-spacing:.11em;text-transform:uppercase;"
            "color:#a89c92;font-weight:600'>Company</span>"
            "<span style='flex:0 0 auto;font-size:.62rem;"
            "letter-spacing:.11em;text-transform:uppercase;"
            "color:#a89c92;font-weight:600'>Ticker</span>"
            + _sz_hd("Index weight", "0 0 92px")
            + _sz_hd("Must buy", "0 0 96px")
            + _sz_hd("Shares", "0 0 108px")
            + _sz_hd("Share of ADV", "0 0 104px")
            + "</div>", unsafe_allow_html=True)
        st.markdown(
            "".join(
                f"<div class='drow'>"
                f"<span class='dact add'>ADD</span>"
                f"<span class='dnm'>{_r['name']}</span>"
                f"<span class='dcode'>{_c}</span>"
                f"<span class='dcode' style='flex:0 0 92px;"
                f"text-align:right'>"
                f"{_r['index_weight_pct']:.3f}%</span>"
                f"<span class='dcode' style='flex:0 0 96px;"
                f"text-align:right'>"
                f"USD {F_[_c]['usd_m']:,.0f}m</span>"
                f"<span class='dcode' style='flex:0 0 108px;"
                f"text-align:right'>"
                f"{F_[_c]['shares'] / 1e6:,.1f}m shares</span>"
                f"<span class='dcode' style='flex:0 0 104px;"
                f"text-align:right;font-weight:700;"
                f"color:#1f4e79'>"
                f"{F_[_c]['adv_x']:.1%} of ADV</span></div>"
                for _c, _r in rows),
            unsafe_allow_html=True)
        # c-397, Bill: a numbered Note, its label bold.
        _note("<b>Note:</b><br>"
              "1. Index weight = float cap \u00f7 the index's own "
              f"free-float value (USD "
              f"{A_['index_float_value_usd_b']:,.0f}bn as of "
              "31 July 2026)<br>"
              f"2. Tracking AUM is estimated at USD "
              f"{BASIS:.0f}bn<br>"
              "3. USD/TWD conversion rate estimated at "
              f"{A_['usd_twd']:.2f}")

        # c-393, Bill: the volume-revealed expander is OFF the page
        # too (the fund-by-fund one went at c-388). Both cross-
        # checks survive as data-level evidence -- scripts, JSONs
        # and reconciliation tests -- and in the Q&A bank; the
        # page carries the disclosed-anchor estimate only.

    # c-344, Bill: SECTION 8 IS DELETED FROM THE PAGE.
    #
    # NOTHING IS LOST. The historical addition distributions, the
    # era split, the round trip and the out-of-sample result are
    # all generated by scripts/tw_addition_study.py and
    # scripts/aug26_scenarios.py, tested in
    # test_tw_addition_study.py, and written up in
    # docs/TW_ADDITION_STUDY.md. The page stops at the size of
    # the order rather than forecasting what the price does with
    # it — which is the honest place to stop, since the
    # out-of-sample test found nothing that predicts direction.
