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
    """scripts/tw_mandate_size.py — MSCI's own Q2 2026 filings,
    turned into a conservative floor on the indexed money that
    must buy a Taiwan Standard addition."""
    if not MAND_SRC.exists():
        return None
    return json.loads(MAND_SRC.read_text(encoding="utf-8"))


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


def _pc(v, f="{:+.2%}"):
    return f.format(v) if v is not None else "—"


def _note(txt):
    st.markdown(
        f"<p style='font-size:.8rem;color:{MUTED};margin:"
        f".1rem 0 .5rem;text-align:center'>{txt}</p>",
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

    # ---- has anyone bought them yet? (c-326) ----------------
    PP = _load_prepos(_pp_stamp())
    _pre = 0
    if PP:
        _pre = 1
        W = PP["windows"]["20"]
        B = PP["historical_benchmark"]
        design.sect(_used + 1,
                    "Market Positioning Before Announcement Day",
                    "Foreign flow into the three candidates for "
                    "index inclusion, compared against other "
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
        _note(f"Peer set = the {W['peer_set_n']} largest "
              f"companies listed on the TWSE, which publishes "
              f"daily buying and selling by foreign and other "
              f"investor types. A reading of "
              f"1.00\u00d7 means net buying equal to one normal "
              f"day's total volume in that stock, accumulated "
              f"across all 20 sessions.")
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
        design.caveat(
            "All three candidates sat <b>BELOW the peer "
            "median</b> for foreign net buying over the 20 "
            "sessions to <b>2026-08-07</b>, while foreigners "
            "were <b>net BUYERS of the peer set</b>, the 100 "
            "largest companies listed on the TWSE. The Taiwan "
            "market experienced <b>heightened "
            "volatility</b> over the same period, which may "
            "partly account for the net foreign selling in these "
            "three names. For context, a typical Taiwan index "
            "addition draws <b>"
            f"{B['foreign_pre_announcement_adv_days']['p50']:+.2f}"
            "\u00d7 a normal day's volume</b> of foreign buying in "
            "the 20 sessions before its announcement.")

    # ---- the tracker's capacity question (c-321) ------------
    PB = _load_playbook(_pb_stamp())
    if PB and SCN:
        # c-351 took the close-share card off this section, and
        # with it the last read of `capacity_model` on the page.
        # The playbook is still the gate for the section — no
        # playbook, no sized names — and the close multiple is
        # still in the chart hover, computed per name from
        # `ordinary_close_shares` rather than from this median.
        # c-325, Bill: Phison off the chart. Its addition verdict
        # flips inside the ±5% band on the cutoff, and a capacity
        # ladder is a SIZING tool — sizing a book from a name you
        # are not standing behind is the wrong default. The rank
        # is assigned after the filter, not before, so the chart
        # reads 1-2-3 rather than 2-3-4.
        rows = sorted([kv for kv in PB["names"].items()
                       if kv[1].get("capacity_rank")],
                      key=lambda kv: kv[1]["capacity_rank"])
        design.sect(_used + 1 + _pre,
                    "How Big Is the Market on Close Order",
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
        design.caveat(
            "<b>Tracking AUM Calculation</b>"
            "<br><br>"
            f"<b>USD {T_['uncapped']:.2f}bn:</b> tracks the "
            "UNCAPPED MSCI Taiwan Index \u2014 two Taiwan-domiciled "
            "ETFs, Yuanta 006203 and Fubon 0057."
            "<br><br>"
            f"<b>USD {T_['family']:.1f}bn</b> is the total across "
            "every MSCI Taiwan index, mostly iShares EWT on the "
            "25/50 variant. These buy a Taiwan Standard addition "
            "too \u2014 it enters the MSCI Taiwan Index and its "
            "capped variants at the same review."
            "<br><br>"
            f"<b>USD {T_['case_promotion']:.0f}bn:</b> Taiwan sits "
            "inside MSCI EM and ACWI STANDARD trackers \u2014 EEM, "
            "EMXC, the Xtrackers/Amundi/UBS/HSBC UCITS range, ACWI "
            "and SSAC. Standard indexes have no small-cap segment, "
            "so the addition is a new holding for every one of "
            "them. With the Taiwan funds above, <b>USD "
            f"{TWM['always_buys_named_etf_usd_b']:.0f}bn</b> of "
            "named ETFs must buy."
            "<br><br>"
            f"<b>USD {BASIS:.0f}bn</b> is our conservative "
            "estimate of the FLOOR on MSCI Taiwan tracking "
            "assets, and the number every figure below is built "
            "on. It adds the indexed money that "
            "has no ticker \u2014 separate accounts, index mutual "
            "funds, pension mandates \u2014 which MSCI reports "
            "revenue on and assets for. See the working below."
            if TWM else
            "<b>Tracking AUM Calculation</b>"
            "<br><br>"
            f"<b>USD {BASIS:.0f}bn</b> of named ETFs must buy.")

        design.stats([
            {"k": "Tracking Fund AUM",
             "v": f"USD {BASIS:.0f}bn",
             "s": "conservative floor"},
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
            hovertemplate=design.hover(
                "%{y}", eyebrow=f"at USD {BASIS:.0f}bn",
                rows=[("share of one day's volume", "%{x:.1f}%"),
                      ("shares to buy",
                       "%{customdata[0]:,.1f}m"),
                      ("which is", "USD %{customdata[1]:,.0f}m"),
                      ("ordinary closes",
                       "%{customdata[2]:.1f}\u00d7"),
                      ("index weight",
                       "%{customdata[3]:.3f}%")],
                note="The indexed money that must buy a "
                     "Standard addition whatever size segment it "
                     "came from \u2014 ETFs and mandates both"))
        fig.update_layout(
            height=300, showlegend=False,
            xaxis=dict(title="index demand, as a % of the "
                             "name's average daily volume",
                       range=[0, max(F_[c]["adv_x"] for c, _r
                                     in rows) * 118]),
            yaxis=dict(title=""), margin=dict(l=0, t=16, b=0))
        design.chart(fig)

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
                    f"mandate, and why it is a floor"):
                st.markdown(
                    f"**Where the numbers come from.** MSCI Inc. "
                    f"reports the assets its indexes are licensed "
                    f"against to the SEC. These four figures are "
                    f"from its Q2 2026 results for the quarter "
                    f"ended {M_['as_of']}, filed "
                    f"{M_['filed']}.\n\n"
                    f"| Figure | Value |\n| --- | --- |\n"
                    f"| ETF AUM linked to MSCI equity indexes | "
                    f"USD {M_['etf_aum_total_usd_b']:,.0f}bn |\n"
                    f"| of which Emerging Markets / All Country | "
                    f"USD {M_['etf_aum_em_ac_usd_b']:,.0f}bn |\n"
                    f"| Quarterly fee revenue, ETFs | USD "
                    f"{M_['abf_etf_usd_m']:,.1f}m |\n"
                    f"| Quarterly fee revenue, NON-ETF indexed "
                    f"funds | USD "
                    f"{M_['abf_non_etf_indexed_usd_m']:,.1f}m "
                    f"|\n\n"
                    f"**1 \u00b7 The ETFs that must buy.** USD "
                    f"{T_['case_promotion']:.1f}bn of Taiwan "
                    f"exposure inside Standard EM and ACWI "
                    f"trackers, plus USD {T_['family']:.1f}bn of "
                    f"ETFs on the MSCI Taiwan indexes themselves, "
                    f"which enter the same addition at the same "
                    f"review.\n\n"
                    f"`USD {T_['case_promotion']:.1f}bn + USD "
                    f"{T_['family']:.1f}bn = USD "
                    f"{TWM['always_buys_named_etf_usd_b']:.1f}bn`"
                    f"\n\n"
                    f"**2 \u00b7 The money with no ticker.** MSCI "
                    f"publishes fee REVENUE on non-ETF indexed "
                    f"funds \u2014 separate accounts, index mutual "
                    f"funds, pension mandates \u2014 but not their "
                    f"assets. Invert the revenue at the fee rate "
                    f"MSCI actually earned on ETFs that quarter, "
                    f"{N_['etf_effective_bp_annualised']:.2f} "
                    f"basis points.\n\n"
                    f"`USD {M_['abf_non_etf_indexed_usd_m']:,.1f}m "
                    f"\u00d7 4 \u00f7 "
                    f"{N_['etf_effective_bp_annualised']:.2f}bp = "
                    f"USD "
                    f"{N_['non_etf_indexed_aum_floor_usd_b']:,.0f}"
                    f"bn`\n\n"
                    f"Against the ETF pool that is:\n\n"
                    f"`USD "
                    f"{N_['non_etf_indexed_aum_floor_usd_b']:,.0f}bn "
                    f"\u00f7 USD "
                    f"{M_['etf_aum_total_usd_b']:,.0f}bn = "
                    f"{N_['multiplier_floor']:.2f}\u00d7`\n\n"
                    f"At least "
                    f"{N_['multiplier_floor'] * 100:.0f} cents of "
                    f"mandate money for every dollar in an "
                    f"ETF.\n\n"
                    f"**3 \u00b7 The estimate.**\n\n"
                    f"`USD "
                    f"{TWM['always_buys_named_etf_usd_b']:.1f}bn "
                    f"\u00d7 {TWM['mandate_multiplier']:.2f} = USD "
                    f"{BASIS:.0f}bn`\n\n"
                    f"[MSCI Q2 2026 results]"
                    f"({M_['sources']['release']}) \u00b7 "
                    f"[earnings presentation]"
                    f"({M_['sources']['presentation']})")

        for _c, _r in rows:
            f = F_[_c]
            with st.expander(
                    f"Calculation \u2014 {_r['capacity_rank']}. "
                    f"{_r['name'][:30]} ({_c})  "
                    f"{f['adv_x']:.0%} of ADV"):
                st.markdown(
                    f"**1 \u00b7 Index weight.** Free-float market "
                    f"cap over the index's own free-float value.\n\n"
                    f"`USD {f['float_cap']:.2f}bn \u00f7 USD "
                    f"{A_['index_float_value_usd_b']:,.0f}bn = "
                    f"{_r['index_weight_pct']:.3f}%`\n\n"
                    f"Free float, not full cap \u2014 a tracker buys "
                    f"the shares the index counts.\n\n"
                    f"**2 \u00b7 Money that must buy.** That weight "
                    f"\u00d7 the tracking assets with no choice: "
                    f"USD {BASIS:.0f}bn of ETFs and indexed "
                    f"mandates.\n\n"
                    f"`{_r['index_weight_pct']:.3f}% \u00d7 USD "
                    f"{BASIS:.0f}bn = USD {f['usd_m']:,.0f}m`\n\n"
                    f"**3 \u00b7 Shares.** Converted at USD/TWD "
                    f"{A_['usd_twd']:.2f} and divided by the last "
                    f"close of TWD {f['px']:,.1f}.\n\n"
                    f"`USD {f['usd_m']:,.0f}m \u00d7 "
                    f"{A_['usd_twd']:.2f} \u00f7 TWD {f['px']:,.1f} "
                    f"= {f['shares'] / 1e6:,.1f}m shares`\n\n"
                    f"Price is why two names on similar weights "
                    f"need very different share counts.\n\n"
                    f"**4 \u00b7 Against the stock's own volume.** "
                    f"Divided by its average daily volume of "
                    f"{_r['adv_shares'] / 1e6:,.1f}m shares.\n\n"
                    f"`{f['shares'] / 1e6:,.1f}m \u00f7 "
                    f"{_r['adv_shares'] / 1e6:,.1f}m = "
                    f"{f['adv_x']:.1%} of ADV`")


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
