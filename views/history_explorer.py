"""History Explorer — every MSCI APAC review result, by market
(c-101). Page 2 of the new site; reads data/msci_changes_db.pkl
(the validated database, 2015-02 -> 2026-05, 13 markets).

Built around the three questions a PT trader actually asks:
  1. What's this market's review RHYTHM?   (KPIs + timeline)
  2. Has this NAME moved before?           (search + churn)
  3. How big was that review?              (drill-down)
"""
import json
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
_REV_ORDER = {"Feb": 0, "May": 1, "Aug": 2, "Nov": 3}


# c-202: tickers that carry TWO DIFFERENT ISSUERS, and must
# never be collapsed into one row.
#
# Collapsing on ticker is right for a rename — "IDFC BANK" and
# "IDFC FIRST BANK" are one company either side of a 2018
# merger. It is wrong when the two names are different legal
# entities or different share classes, because the merged row
# then describes a company that does not exist. Auditing all 25
# colliding tickers in the database found exactly two:
#
#   India ENRIN   SIEMENS INDIA (ADD May06, DEL Nov18, ADD
#                 Nov19) and SIEMENS ENERGY INDIA (ADD Nov25).
#                 Siemens Energy India was DEMERGED from
#                 Siemens India and listed separately in 2025 —
#                 two listed companies, not one renamed. The
#                 ticker itself is also wrong for both (NSE
#                 carries SIEMENS and SIEMENSENRG), which is
#                 why both India window fetches for ENRIN
#                 returned nothing. Recorded in OPEN_ITEMS as
#                 an upstream fix; the display must not pretend
#                 it is resolved.
#
#   China 000596  ANHUI GUJING A (HK-C) and ANHUI GUJING
#                 DISTILLER B. Same issuer, but the A line is
#                 000596 and the B line is 200596 — different
#                 share classes with different prices,
#                 liquidity and investor bases. The B row
#                 carries the A ticker, an upstream error that
#                 merging would conceal.
#
# Everything else on the collision list is a genuine rename or
# truncation and merges correctly.
NEVER_MERGE = {
    ("India", "ENRIN"):
        "SIEMENS INDIA and SIEMENS ENERGY INDIA are separate "
        "listed companies after the 2025 demerger — not a "
        "rename. The ticker is also wrong for both.",
    # c-259: ("China", "000596") is GONE from this list, and
    # its removal is the point. The exemption existed because
    # the B line carried the A line's ticker — a display guard
    # around an upstream data error. `ticker_corrections.py`
    # repointed the B row to 200596.SZ, so the two no longer
    # collide and nothing needs exempting. The collision test
    # caught the stale entry, which is what it is for: an
    # exception kept after its cause is fixed quietly asserts a
    # defect that no longer exists.
}

# c-207: the page-local stylesheet is gone. Every rule it
# carried now lives in views/design.py and is injected once from
# app.py, so the Review Database, the prediction page and the
# window study cannot drift apart.
_MON_ORD = {m: i for i, m in enumerate(
    ["Feb", "May", "Aug", "Nov"])}

# The February-2023 methodology change, marked on every chart
# because it is the single biggest structural break in this
# database and every average that straddles it is a blend of
# two different regimes.
REGIME = "Feb23"


# c-214: the changes DB stores market keys without spaces, so
# "HongKong" and "NewZealand" reached the screen unsplit. The
# KEY stays as-is everywhere — it joins to markets.py and to
# every data file — and only the LABEL changes. Two entries,
# not a market list, so page_lint's hardcoded-markets rule is
# not in play.
_LABEL = {"HongKong": "Hong Kong", "NewZealand": "New Zealand"}

# c-240: the all-markets option in the section-2 selector.
#
# A sentinel rather than a magic string in five places, and
# deliberately NOT a market name — `df.market == ALL` must never
# accidentally match a row.
ALL = "__ALL__"


def _pretty(market):
    if market == ALL:
        return "All Markets"
    return _LABEL.get(market, market)


def _rlabel(review):
    """"Feb26" -> "Feb 2026".

    c-221: the stored label is a compact KEY — it sorts, it
    joins to MSCI's filenames, and it is unreadable. "May10"
    invites reading as a day of month. Every place a reader
    SEES a review now goes through here; the key itself is
    untouched, because it is what the PDF URLs are built from.
    """
    r = str(review)
    if len(r) == 5 and r[3:].isdigit():
        return f"{r[:3]} {2000 + int(r[3:])}"
    return r


# c-235: ONE popup style, shared by the section-1 strip and the
# section-2 chart. Bill asked for the chart card to look like
# the strip card; the only way to guarantee that stays true is
# for there to be one stylesheet rather than two that agree
# today.
POP_CSS = (
    ".pop{display:none;position:absolute;z-index:60;"
    "min-width:250px;max-width:330px;max-height:330px;"
    "overflow-y:auto;background:#fff;border:1px solid #d9cbbb;"
    "border-radius:3px;padding:.5rem .65rem;"
    "box-shadow:0 6px 18px rgba(43,39,36,.10)}"
    ".pop .ph{font-size:.64rem;letter-spacing:.12em;"
    "text-transform:uppercase;color:#a89c92;font-weight:600;"
    "padding-bottom:.3rem;margin-bottom:.3rem;"
    "border-bottom:1px solid #f2ebe2}"
    ".pop .pr{display:flex;gap:.5rem;align-items:baseline;"
    "padding:.1rem 0;font-size:.8rem}"
    ".pop .pk{flex:0 0 48px;font-size:.6rem;font-weight:600;"
    "letter-spacing:.1em;text-transform:uppercase}"
    ".pop .pk.add{color:#2e7d52}.pop .pk.del{color:#b03a2e}"
    ".pop .pn{color:#2b2724;flex:1 1 auto}"
    ".pop .pg{position:sticky;top:0;background:#fff;"
    "display:flex;justify-content:space-between;"
    "align-items:baseline;font-size:.6rem;font-weight:600;"
    "letter-spacing:.1em;text-transform:uppercase;"
    "padding:.35rem 0 .18rem;margin-top:.2rem;"
    "border-bottom:1px solid #f2ebe2}"
    ".pop .pg.add{color:#2e7d52}.pop .pg.del{color:#b03a2e}"
    ".pop .pc{color:#a89c92;font-weight:600}"
    # the PDF link — a real anchor, which is the whole reason
    # this card is HTML and not a plotly tooltip
    ".pop .pl{display:block;margin-top:.45rem;padding-top:.4rem;"
    "border-top:1px solid #f2ebe2;font-size:.72rem;"
    "color:#1f4e79;text-decoration:none}"
    ".pop .pl:hover{text-decoration:underline}")


def _pop_body(rev, adds, dels):
    """The inside of a review card: grouped names, then the
    MSCI document link. Shared shape with the section-1 strip."""
    out = [f"<div class='ph'>{_rlabel(rev)}</div>"]
    for lab, names, k in (("Added", adds, "add"),
                          ("Deleted", dels, "del")):
        if not names:
            continue
        out.append(f"<div class='pg {k}'>{lab}"
                   f"<span class='pc'>{len(names)}</span></div>")
        for nm in sorted(names):
            out.append(f"<div class='pr'><span class='pn'>"
                       f"{str(nm).title()}</span></div>")
    if len(out) == 1:
        out.append("<div class='pr'><span class='pn'>No change "
                   "at this review.</span></div>")
    out.append(
        f"<a class='pl' target='_blank' href='{PDF_URL.format(rev)}'>"
        f"MSCI public list for {_rlabel(rev)} &nearr;</a>")
    return "".join(out)


PDF_URL = ("https://www.msci.com/eqb/gimi/stdindex/"
           "MSCI_{}_STPublicList.pdf")

# c-237: 95, down from 150. The card cannot follow the cursor —
# CSS has no way to do that and st.markdown strips script — so
# the only lever on "how far must the mouse travel" is how tall
# the chart is. Halving the height halves the worst-case
# journey, and the card now opens AT THE ZERO LINE rather than
# below the whole column, which halves it again.
HALF = 95           # px per side of the zero line


def _history_html(per, by_rev, regime):
    """The add/delete history as HTML, not as a plotly figure.

    c-235 moved this off plotly because Bill wanted a hover card
    that survives the mouse entering it, matches section 1,
    lists every name and carries MSCI's link — none of which an
    SVG tooltip can do.

    c-237 pays back what that cost. Bill: the card was too far
    from the chart, the axis "looks very weird", and the regime
    label and the zoom controls were simply gone. All three were
    real regressions and none of them were forced by the change
    of technology — I had rebuilt the chart and not rebuilt
    everything the old one did.

      * THE CARD opens at the zero line, and the chart is 190px
        tall instead of 300.
      * THE AXIS is one absolutely-positioned label per year on
        its own layer, so a label can be wider than the 12px
        column it belongs to. Before, every column carried a
        label div and the text spilled into its neighbours.
      * THE REGIME LABEL is back, in the same three-part form
        as c-221 so the bar glyph lands on the line.
      * ZOOM is a year-range control (see the caller), which is
        also a fix: plotly's drag-zoom had no way out until
        c-215 added a toolbar for exactly that reason.
    """
    revs = list(per.index)
    n = max(1, len(revs))
    hi = max(1, int(max(per.ADD.max(), per.DEL.max())))
    cells = []
    for i, r in enumerate(revs):
        a, d = int(per.ADD.get(r, 0)), int(per.DEL.get(r, 0))
        adds, dels = by_rev.get(r, ([], []))
        side = " right" if i > n * 0.72 else ""
        cells.append(
            f"<div class='hcol'>"
            f"<div class='htop'><div class='hbar up' "
            f"style='height:{round(HALF * a / hi)}px'></div></div>"
            f"<div class='hzero'></div>"
            f"<div class='hbot'><div class='hbar dn' "
            f"style='height:{round(HALF * d / hi)}px'></div></div>"
            f"<div class='pop{side}'>{_pop_body(r, adds, dels)}"
            f"</div></div>")

    # ---- the axis, on its own layer ------------------------
    # One label per February, placed at that column's centre as
    # a percentage. It can overflow its column freely because
    # nothing else shares the row.
    ticks = []
    for i, r in enumerate(revs):
        if not r.startswith("Feb"):
            continue
        left = (i + 0.5) / n * 100
        ticks.append(
            f"<span class='htick' style='left:{left:.3f}%'>"
            f"{2000 + int(r[3:])}</span>")

    # ---- the regime marker ---------------------------------
    # the LINE belongs to the plot zone and the LABEL to the
    # annotation zone; they share only an x position
    reg_line = reg_label = ""
    if regime in revs:
        at = revs.index(regime) / n * 100
        reg_line = f"<div class='hreg' style='left:{at:.3f}%'></div>"
        # c-242: TWO ROWS. The title sits above, centred on the
        # line; the before/after pair sits under it with the
        # bar glyph still pinned to the same x as the dotted
        # rule. Three anchors on one row could not carry the
        # title as well without pushing the bar off centre —
        # the title is much longer than "after ▶", so a single
        # centred string moves the midpoint.
        reg_label = (
            f"<div class='hregl' style='left:{at:.3f}%'>"
            "<span class='cap'>2023 QUARTERLY REVIEW RULE "
            "CHANGE</span>"
            "<span class='l'>&#9664;&nbsp;before</span>"
            "<span class='b'>&#9474;</span>"
            "<span class='r'>after&nbsp;&#9654;</span></div>")

    return (
        "<style>" + POP_CSS +
        # c-239, DESIGN_DECISIONS D11: THREE STACKED ZONES.
        #
        # Bill: the regime label collides with the legend, and
        # "there are many examples of such problems throughout
        # this page". He is right, and the cause is not any one
        # of them — it is that I had been positioning each new
        # element by eye, absolutely, into whatever vertical
        # space looked free at the time. The legend was a
        # normal-flow div above the chart; the regime label was
        # absolutely placed at top:-1.45rem. Both claimed the
        # same 24 pixels and neither knew about the other.
        #
        # A chart block now owns three zones stacked in NORMAL
        # FLOW — annotations, plot, axis — and an absolutely
        # positioned element may only move HORIZONTALLY within
        # its own zone. Nothing can reach into a neighbour's
        # space, so a new label cannot collide with an old one.
        ".hwrap{position:relative}"
        # zone A: annotations. Reserved height, so the label has
        # somewhere to be that belongs to it.
        # two rows of label now live here, so the zone is
        # taller. Zone heights are the contract (D11) — a label
        # that needs more room enlarges its zone rather than
        # spilling into the plot.
        ".hzone-a{position:relative;height:2.35rem}"
        # zone B: the plot
        ".hgrid{display:flex;align-items:stretch;gap:1px;"
        "position:relative}"
        ".hcol{flex:1 1 0;position:relative;min-width:0}"
        ".hcol:hover .pop{display:block}"
        ".hcol:hover .hbar{filter:brightness(.8)}"
        ".hcol:hover{background:rgba(31,78,121,.06)}"
        f".htop{{height:{HALF}px;display:flex;align-items:flex-end}}"
        f".hbot{{height:{HALF}px;display:flex;align-items:flex-start}}"
        ".hbar{width:100%}"
        ".hbar.up{background:#2e7d52}.hbar.dn{background:#b03a2e}"
        ".hzero{height:1px;background:#e8ddd1}"
        ".pop{top:50%;left:-1px}"
        ".pop.right{left:auto;right:-1px}"
        # zone C: axis, then the legend UNDER it. The legend was
        # above the plot and in the annotation zone's way; below
        # the axis it has the row to itself.
        ".hzone-c{position:relative;height:1.15rem;"
        "margin-top:.3rem;border-top:1px solid #e8ddd1}"
        ".htick{position:absolute;top:.25rem;"
        "transform:translateX(-50%);font-size:.68rem;"
        "color:#a89c92;white-space:nowrap;"
        "font-variant-numeric:tabular-nums}"
        ".hreg{position:absolute;top:0;bottom:0;width:0;"
        "border-left:2px dotted #1f4e79;z-index:2}"
        # horizontal placement only — the zone owns the vertical
        ".hregl{position:absolute;top:.1rem;font-size:.68rem;"
        "color:#1f4e79;white-space:nowrap}"
        # row 1 — the title, centred on the line
        # c-246: set in capitals at Bill's request. Caps at
        # .68rem need the tracking the site gives its other
        # uppercase labels, or the letters run together.
        ".hregl .cap{position:absolute;top:0;left:0;"
        "transform:translateX(-50%);font-weight:600;"
        "letter-spacing:.06em;white-space:nowrap}"
        # row 2 — before / bar / after, the bar pinned to x
        ".hregl .l{position:absolute;top:1.15rem;right:.28em}"
        ".hregl .b{position:absolute;top:1.15rem;left:-.25em}"
        ".hregl .r{position:absolute;top:1.15rem;left:.5em}"
        ".hleg{display:flex;gap:1.1rem;justify-content:flex-end;"
        "font-size:.68rem;color:#6b6058;margin-top:.5rem}"
        ".hleg i{font-style:normal;display:inline-block;"
        "width:9px;height:9px;margin-right:.35rem}"
        "</style>"
        f"<div class='hwrap'>"
        f"<div class='hzone-a'>{reg_label}</div>"
        f"<div class='hgrid'>{reg_line}{''.join(cells)}</div>"
        f"<div class='hzone-c'>{''.join(ticks)}</div>"
        "<div class='hleg'>"
        "<span><i style='background:#2e7d52'></i>Additions</span>"
        "<span><i style='background:#b03a2e'></i>Deletions</span>"
        "</div>"
        f"</div>")


def _sect(n, title, lead=""):
    # c-207: one shared design system across the site
    from views import design
    design.sect(n, title, lead)


def _cards(items):
    from views import design
    design.stats(items)


def _change_rows(rows, limit=14):
    from views import design
    design.rows(rows, limit=limit)


def _apac_strip(df, markets):
    """The latest review, every market, as a ruled panel.

    c-214 redesign. The first version squeezed twelve markets
    into one row of three-letter codes, which forced "IND" to
    mean both India and Indonesia and gave the reader a number
    with no way to ask what it was made of.

    Now: full country names on a grid, and HOVER on any market
    to see the actual securities MSCI moved. The figures answer
    "how much"; the hover answers "which names" without
    spending any vertical space until asked.

    A dash means no change. Zero would be a number, and a
    market that did nothing did not score zero — it was not
    part of the review at all.
    """
    last = None
    for r in reversed(_all_reviews()):
        if (df.review == r).any():
            last = r
            break
    if not last:
        return
    _sect(1, f"Latest Review — {_rlabel(last)}",
          "Hover a market to see the index review changes.")
    cur = df[df.review == last]
    cells = []
    for m in markets:
        g = cur[cur.market == m]
        adds = g[g.action == "ADD"].security.tolist()
        dels = g[g.action == "DEL"].security.tolist()
        a, d = len(adds), len(dels)
        quiet = not (a or d)
        # c-233: EVERY NAME, not the first eight. China's May-26
        # review moved 30 names and the card said "+14 more" —
        # which is the one thing a snapshot must never do, since
        # the whole point is to answer "which names" without
        # making the reader go somewhere else.
        #
        # With the cap gone the label cannot repeat on every
        # row: "Added" printed twenty-two times is noise, and it
        # was already redundant the second time. One group
        # heading carrying its own count, then bare names. The
        # card scrolls (see .pop max-height) rather than growing
        # off the bottom of the screen.
        pop = []
        for lab, names, k in (("Added", adds, "add"),
                              ("Deleted", dels, "del")):
            if not names:
                continue
            pop.append(f"<div class='pg {k}'>{lab}"
                       f"<span class='pc'>{len(names)}</span>"
                       f"</div>")
            for nm in sorted(names):
                pop.append(f"<div class='pr'>"
                           f"<span class='pn'>{nm.title()}</span>"
                           f"</div>")
        if not pop:
            pop.append("<div class='pr'><span class='pn'>"
                       "No change at this review.</span></div>")
        q = " q" if quiet else ""
        cells.append(
            f"<div class='amk{q}'>"
            f"<div class='mm'>{_pretty(m)}</div>"
            f"<div class='mv'>"
            + ("<span class='nc'>–</span>" if quiet else
               f"<span class='a'>{a}</span>"
               f"<span class='x'>/</span>"
               f"<span class='d'>{d}</span>")
            + "</div><div class='pop'>"
            + f"<div class='ph'>{_pretty(m)} · {_rlabel(last)}"
              f"</div>"
              + "".join(pop) + "</div></div>")
    st.markdown(
        "<style>"
        ".astrip{display:grid;"
        "grid-template-columns:repeat(auto-fit,minmax(150px,1fr));"
        "border-top:1px solid #e8ddd1;border-left:1px solid "
        "#f2ebe2;margin:.25rem 0 .5rem;overflow:visible}"
        ".amk{position:relative;padding:.6rem .7rem;"
        "border-right:1px solid #f2ebe2;"
        "border-bottom:1px solid #f2ebe2;min-width:0}"
        ".amk:hover{background:#fffdfa}"
        ".amk .mm{font-size:.74rem;color:#8a7f76;"
        "white-space:nowrap;overflow:hidden;"
        "text-overflow:ellipsis;margin-bottom:.1rem}"
        ".amk .mv{font-family:'Source Serif 4',Georgia,serif;"
        "font-size:1.5rem;font-weight:400;line-height:1.15;"
        "font-variant-numeric:tabular-nums}"
        ".amk .a{color:#2e7d52}.amk .d{color:#b03a2e}"
        ".amk .x{color:#e8ddd1;margin:0 3px}"
        ".amk .nc{color:#c9bdb1}"
        # the hover card. Absolute so it costs no layout height
        # until the reader asks for it.
        + POP_CSS +
        # c-242: THESE THREE RULES WENT MISSING AT c-236 AND
        # SECTION 1'S HOVER HAS BEEN DEAD SINCE.
        #
        # POP_CSS carries how a card LOOKS. How it OPENS is the
        # host's business, because each host anchors it
        # differently — the chart opens at its zero line, the
        # seasonality bars below theirs. When I replaced this
        # block with POP_CSS I took the appearance rules and
        # deleted the behaviour rules that were sitting among
        # them, so the card was left `display:none` with nothing
        # to turn it on.
        #
        # Section 2 and the seasonality panel were written after
        # the split and supply their own; section 1 was written
        # before it and silently lost them. Sharing a stylesheet
        # is only safe if you can say which half you shared.
        ".amk:hover .pop{display:block}"
        ".amk .pop{top:calc(100% - 2px);left:-1px}"
        ".amk:nth-child(6n) .pop,.amk:last-child .pop"
        "{left:auto;right:-1px}"
        "</style>"
        f"<div class='astrip'>{''.join(cells)}</div>",
        unsafe_allow_html=True)


def _seasonality(sub):
    """Which month moves the index most — SPEC section 7.

    c-209 BACKLOG 5. This sat directly under the timeline, in
    the second-most valuable slot on the page, for a question
    almost nobody arrives with. The spec ranks it last, so it
    now renders last.
    """
    seas = sub.groupby([sub.review.str[:3], "action"]) \
        .size().unstack(fill_value=0)
    seas = seas.reindex(["Feb", "May", "Aug", "Nov"]).fillna(0)
    for c in ("ADD", "DEL"):
        if c not in seas:
            seas[c] = 0
    # c-236: HTML bars with the section-1 card, same as the
    # section-2 chart at c-235. Bill asked for one popup design
    # on this page and this was the last plotly tooltip left in
    # a place a reader would want to read.
    by_mon = {}
    for mon in seas.index:
        g = sub[sub.review.str[:3] == mon]
        by_mon[mon] = (g[g.action == "ADD"].security.tolist(),
                       g[g.action == "DEL"].security.tolist())
    hi = max(1, int(max(seas.ADD.max(), seas.DEL.max())))
    cols = []
    for mon in seas.index:
        a, d = int(seas.ADD.get(mon, 0)), int(seas.DEL.get(mon, 0))
        adds, dels = by_mon.get(mon, ([], []))
        side = " right" if mon == "Nov" else ""
        cols.append(
            f"<div class='mcol'>"
            f"<div class='mpair'>"
            f"<div class='mb up' style='height:"
            f"{round(120 * a / hi)}px' title='{a} additions'>"
            f"</div>"
            f"<div class='mb dn' style='height:"
            f"{round(120 * d / hi)}px' title='{d} deletions'>"
            f"</div></div>"
            f"<div class='mlab'>{mon}<span class='mct'>"
            f"{a} / {d}</span></div>"
            f"<div class='pop{side}'>"
            f"<div class='ph'>{mon} reviews · all years</div>"
            + _pop_body(mon, adds, dels)
              .split("</div>", 1)[1]
              .rsplit("<a class='pl'", 1)[0]
            + "</div></div>")
    with st.expander("Index Review Change Count by Quarter"):
        st.markdown(
            "<style>" + POP_CSS +
            ".mgrid{display:flex;gap:2rem;align-items:flex-end;"
            "padding:1rem 0 .2rem}"
            ".mcol{flex:1 1 0;position:relative;min-width:0}"
            ".mcol:hover .pop{display:block}"
            ".mcol:hover .mb{filter:brightness(.82)}"
            ".mpair{display:flex;gap:6px;align-items:flex-end;"
            "height:120px}"
            ".mb{flex:1 1 0}"
            ".mb.up{background:#2e7d52}.mb.dn{background:#b03a2e}"
            ".mlab{border-top:1px solid #e8ddd1;margin-top:4px;"
            "padding-top:.35rem;font-size:.8rem;color:#2b2724;"
            "display:flex;justify-content:space-between}"
            ".mct{color:#a89c92;font-variant-numeric:tabular-nums}"
            ".pop{top:calc(100% - 2px);left:-1px}"
            ".pop.right{left:auto;right:-1px}"
            "</style>"
            f"<div class='mgrid'>{''.join(cols)}</div>",
            unsafe_allow_html=True)
        # c-241: Bill asked for a more formal register and a
        # "Note:" prefix. The old line read like a chart key;
        # this states what is counted and over what period,
        # which is what a reader needs before comparing bars.
        st.caption(
            "Note: additions (green) and deletions (red) are "
            "counted across every review of that month since "
            "2006.")
        # c-241: the index was named "Review" and then
        # reset_index() turned it into a column — but the
        # groupby key was `review.str[:3]`, an UNNAMED series,
        # so pandas emitted a blank spacer column ahead of it.
        # Building the frame explicitly removes the empty
        # column and the whitespace Bill saw.
        import pandas as _pd
        seas = _pd.DataFrame({
            # c-243: the column is headed "Review"; repeating
            # the word in every cell is the label twice.
            "Review": list(seas.index),
            "Addition": seas.ADD.astype(int).values,
            "Deletion": seas.DEL.astype(int).values})
        _rtable(seas, first_width=None)


def _scoreboard(df, markets):
    """All 13 markets on one table — SPEC section 7.

    c-209 BACKLOG 7. Every column comes from the changes DB and
    nothing is modelled: counts, the add/delete skew, and the
    share of reviews that moved nothing. The Philippines is
    INCLUDED here, because this is a history view and the
    exclusion is about the forward pipeline having no price
    source — a reason that does not apply to counting what MSCI
    already did. It is tagged so the distinction is visible.
    """
    import pandas as pd
    revs = _all_reviews()
    rows = []
    for m in sorted(df.market.unique()):
        g = df[df.market == m]
        per = (g.groupby(["review", "action"]).size()
               .unstack(fill_value=0).reindex(revs, fill_value=0))
        for c in ("ADD", "DEL"):
            if c not in per:
                per[c] = 0
        a, d = int(per.ADD.sum()), int(per.DEL.sum())
        quiet = int(((per.ADD == 0) & (per.DEL == 0)).sum())
        tk = (g.ticker.astype(str).str.strip() != "").sum()
        rows.append({
            "Market": _pretty(m) + ("" if m in markets
                                    else " *"),
            "Changes": a + d,
            "Additions": a,
            "Deletions": d,
            "Add/Del": round(a / d, 2) if d else None,
            "Busiest": (per.ADD + per.DEL).idxmax(),
            "Quiet Reviews": f"{quiet / len(revs):.0%}",
            "Tickered": f"{tk / len(g):.0%}" if len(g) else "—",
        })
    _rtable(pd.DataFrame(rows).sort_values(
        "Changes", ascending=False))
    if any(m not in markets for m in df.market.unique()):
        st.caption("* history retained, excluded from the "
                   "forward pipeline — see scripts/markets.py.")


def _rev_key(step):
    """Sort key for a history step like 'ADD Nov16'.

    Reviews are named MonYY, so plain string order puts Aug
    before Feb before May before Nov inside a year, and 06
    after 05 but before 99. Sorting on (year, quarter) instead
    keeps a merged history in the order it happened.
    """
    import re as _r
    m = _r.search(r"(Feb|May|Aug|Nov)(\d{2})", str(step or ""))
    if not m:
        return (0, 0)
    yy = int(m.group(2))
    return (yy + (2000 if yy < 90 else 1900),
            _MON_ORD[m.group(1)])


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
    for y in range(2006, 2027):
        for mon in ("Feb", "May", "Aug", "Nov"):
            if (y, mon) == (2026, "Aug"):
                break
            out.append(f"{mon}{y % 100:02d}")
    return out


@st.cache_data(show_spinner=False)
def _official():
    p = ROOT / "data" / "msci_official_constituents.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


@st.cache_data(show_spinner=False)
def _memhist():
    p = ROOT / "data" / "membership_history.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def _tenure(mkt, current_keys):
    """First review from which each current member has been
    CONTINUOUSLY present, per the reverse-roll."""
    mh = _memhist()
    if not mh or mkt not in mh["markets"]:
        return {}
    import sys
    sys.path.insert(0, str(ROOT / "scripts"))
    from membership_history import _key, reviews
    mem = mh["markets"][mkt]["members"]
    order = [r for r in reviews() if r in mem]
    out = {}
    for k in current_keys:
        first = order[-1] if order else None
        for r in reversed(order):        # newest -> oldest
            if k in {_key(n, mkt) for n in mem[r]}:
                first = r
            else:
                break
        out[k] = first
    return out


def _members_now(mkt):
    """The current index composition — MSCI's own published
    constituents with CLOSING WEIGHTS. A weight treemap is
    the right visual here: an index is a weighted set, and
    for a PT desk the weight IS the trade size. Equal-area
    charts would hide that TSMC alone is 55% of Taiwan."""
    import pandas as pd
    from views import design
    import plotly.express as px
    # c-216: "tenure" retired. It is HR language, and the thing
    # being measured is simply how many years a company has
    # been in the index — so the label says that.
    # c-240: the heading is the PAGE's, not this helper's.
    # page_lint caught _sect(3, ...) appearing twice in source
    # once the all-markets branch needed its own — correctly,
    # because two calls with the same number is exactly the
    # defect it watches for, and "they never both run" is an
    # argument the next reader should not have to reconstruct.
    off = _official()
    if not off or mkt not in off.get("markets", {}):
        st.info(
            f"MSCI's public constituents tool does not offer "
            f"{mkt} — no official weighted list. "
            f"({(off or {}).get('not_offered', {}).get(mkt, '')})"
            if off else
            "Run `py scripts\\msci_constituents.py harvest` "
            "to populate the official constituent lists.")
        return
    m = off["markets"][mkt]
    d = pd.DataFrame(m["constituents"])
    import sys
    sys.path.insert(0, str(ROOT / "scripts"))
    from membership_history import _key
    d["k"] = [_key(s, mkt) for s in d.security]
    ten = _tenure(mkt, list(d.k))
    d["since"] = [ten.get(k) or "since Feb06" for k in d.k]
    d["yrs"] = [(2026 - (2000 + int(s[-2:]))) if s != "since Feb06"
                else 21 for s in d.since]
    # c-221: display copy. `since` stays the raw code because
    # `yrs` is parsed from its last two characters.
    d["since_txt"] = [_rlabel(s) for s in d.since]
    c = d.weight.sort_values(ascending=False).cumsum()
    k1, k2 = st.columns(2)
    k1.metric("Constituents", m["n"])
    k2.metric("Top 10", f"{c.iloc[min(9, len(c) - 1)]:.1f}%")
    fig = px.treemap(
        d, path=[px.Constant(mkt), "security"], values="weight",
        color="yrs", color_continuous_scale="Blues",
        custom_data=["weight", "since_txt"])
    fig.update_traces(
        # c-334: this one gains the "<extra></extra>" suffix the
        # hand-rolled string never had — the builder always
        # emits it, and the tile name it suppresses is the
        # label the card already carries.
        hovertemplate=design.hover(
            "%{label}", eyebrow="constituent",
            rows=[("weight", "%{customdata[0]:.3f}%"),
                  ("in the index since", "%{customdata[1]}")]))
    # c-216: the tile labels were rendering in Plotly's default
    # face while the rest of the site is Inter. design.chart()
    # sets the LAYOUT font, but a treemap draws its tile text
    # from the TRACE, so it ignored the theme entirely — the
    # largest text on the page was the only text not in the
    # site's typeface.
    fig.update_traces(textfont=dict(family="Inter, sans-serif",
                                    size=13),
                      insidetextfont=dict(
                          family="Inter, sans-serif"))
    # c-220: horizontal colour bar. A vertical bar on the right
    # took a column of width from every tile for its whole
    # height; laid along the bottom it costs ~40px once and
    # gives the treemap the full page width, which matters
    # because tile AREA is the quantity being read.
    # c-239: the colorbar was at y=-0.12 with b=0, so it sat ON
    # the tiles rather than under them — the same zone collision
    # as the chart label, in plotly's coordinate system. The
    # bottom margin now RESERVES the strip the colorbar lives
    # in, and the bar sits inside it.
    fig.update_layout(
        height=470, margin=dict(t=10, b=54, l=0, r=0),
        coloraxis_colorbar=dict(
            # c-221: the same footnote governs the legend and
            # the table column. Both carry ¹ so the reader sees
            # ONE caveat covering both, rather than two notes
            # saying the same thing in different words.
            title=dict(text="Years in Index¹", side="top"),
            orientation="h", yanchor="top", y=-0.02,
            xanchor="center", x=0.5, thickness=11, len=0.42))
    design.chart(fig)
    st.caption("Box area = index weight as of 01 Jun 2026. "
               "Shade = years in the index.")
    # c-236: the rule other sections get, between the chart and
    # the table it introduces.
    st.markdown("<hr style='border:none;border-top:1px solid "
                "#e8ddd1;margin:1.6rem 0 1.1rem'>",
                unsafe_allow_html=True)
    # c-209 BACKLOG 6: out of the expander. PAGE_SPEC ranks
    # "who is in the index right now" third, and this table IS
    # that section — it is what Bill meant by the weight
    # breakdown. A first-class section does not hide behind a
    # click.
    #
    # c-219: the Feb-2006 caveat moved OUT of the chart caption
    # and became a numbered footnote on the column it actually
    # qualifies. It was previously buried mid-sentence between
    # two unrelated facts, three elements above the table whose
    # values it describes — so the one reader who needed it was
    # the least likely to connect it.
    _rtable(d[["security", "weight", "since_txt"]]
            .sort_values("weight", ascending=False)
            .rename(columns={"security": "Security",
                             "weight": "Closing Weights (%)",
                             "since_txt": "Member Since¹"}),
            height=330)
    st.markdown(
        "<div style='font-size:.78rem;color:#a89c92;"
        "line-height:1.6;margin:.35rem 0 0;padding-top:.4rem;"
        "border-top:1px solid #f2ebe2'>"
        "<b>1.</b> MSCI's published record of index changes "
        "commences in February 2006. A constituent shown as "
        "&ldquo;since Feb06&rdquo; may therefore have been "
        "admitted to the index prior to that date, and its "
        "years in the index should be read as a minimum.<br>"
        # c-313, Bill: the source becomes a link. It is raw HTML
        # rather than markdown because this whole footnote block
        # is one `unsafe_allow_html` string — an inline [text](url)
        # here would print as its own source.
        "Source: <a href='https://www-cdn.msci.com/web/msci/"
        "index-tools/constituents' target='_blank' "
        "rel='noopener'>MSCI's Index Constituents tool</a>."
        "</div>",
        unsafe_allow_html=True)


def _rtable(d, height=None, first_width="55%"):
    """A table where every header sits over its own values.

    st.dataframe right-aligns numbers and left-aligns their
    HEADERS, so a numeric column reads as two columns that
    happen to overlap — which is what Bill was seeing. Streamlit
    exposes no alignment control, so these render as HTML.

    c-221: alignment is decided PER COLUMN and applied to the
    header and the cells together — numbers right, text left.
    That is the rule Bill asked for ("column name and column
    values have the same alignment"); forcing one direction on
    the whole table would satisfy the letter of it and put
    company names against the right edge, which no financial
    table does.
    """
    # c-216: THE WIDTH RULE NEVER APPLIED. pandas' Styler scopes
    # every selector under the table's own id, so a selector of
    # "table" compiles to "#T_xxx table" — a DESCENDANT table,
    # of which there is none. The rule matched nothing and the
    # table sized itself to its content, which is why a
    # three-column table sat in a narrow strip on a 1120px page.
    # Width has to be set as a table ATTRIBUTE, not a style rule.
    import pandas.api.types as pt
    from views.design import TABLE_ATTR, table_card
    rules = [
        {"selector": "th",
         "props": [("background", "#faf5ef"),
                   ("position", "sticky"), ("top", "0")]},
        {"selector": "td, th",
         "props": [("padding", "9px 14px"),
                   ("font-size", "0.9rem"),
                   ("border-bottom", "1px solid #f2ebe2")]},
        # c-243: the LAST row's rule sat above the empty band,
        # so it read as a rule with nothing under it. The card
        # border already closes the table.
        {"selector": "tbody tr:last-child td",
         "props": [("border-bottom", "none")]}]
    for i, col in enumerate(d.columns, start=1):
        side = "right" if pt.is_numeric_dtype(d[col]) else "left"
        props = [("text-align", side)]
        if i == 1 and first_width:
            props.append(("width", first_width))
        rules.append({"selector": f"td:nth-child({i}), "
                                  f"th:nth-child({i})",
                      "props": props})
    sty = (d.style
           .set_table_attributes(TABLE_ATTR)
           .set_table_styles(rules))
    # c-236, DESIGN_DECISIONS D1: tables sit on WHITE.
    #
    # Bill noticed that the one table inside an expander read
    # better than the rest of the page's tables and worked out
    # why before I did — Streamlit gives an expander a white
    # backing, and the page background is PAPER (#fdfaf6), so
    # every other table was sitting on a surface almost the
    # same colour as itself. The card is the fix, applied here
    # so every table on this page gets it at once.
    # c-239, DESIGN_DECISIONS D11: SCROLLBAR GUTTER.
    #
    # Bill: "the whitespace from the scroll bar makes the table
    # asymmetrical." Exactly right, and it is a layout-contract
    # problem rather than a styling one. An overflow container
    # only reserves space for a scrollbar WHEN one appears, so
    # the content width changes depending on how many rows the
    # filter left — the table is 15px narrower on the right than
    # the left, and only sometimes. `scrollbar-gutter:stable`
    # reserves the track whether or not it is needed, so the
    # content box stops moving.
    # c-244: the card style and the table attribute both come
    # from design.py now — see the comment on TABLE_ATTR for why
    # the trailing band was never ours, and on _card for why
    # `overflow:hidden` took the scrollbar with it.
    st.markdown(f"<div style='{table_card(height)}background:#fff;"
                f"border:1px solid #e8ddd1;border-radius:3px'>"
                f"{sty.hide(axis='index').to_html()}</div>",
                unsafe_allow_html=True)


def _time_machine(mkt):
    """Index composition at any past review, by reverse-roll."""
    import pandas as pd
    from views import design
    import plotly.graph_objects as go
    mh = _memhist()
    _sect(9, "Membership Time Machine",
          "Index composition at any review since 2006.")
    if not mh or mkt not in mh["markets"]:
        st.info("Run `py scripts\\membership_history.py build`.")
        return
    o = mh["markets"][mkt]
    cnt = o["counts"]
    import sys
    sys.path.insert(0, str(ROOT / "scripts"))
    from membership_history import reviews
    order = [r for r in reviews() if r in cnt]
    n = [cnt[r]["n"] for r in order]
    band = [cnt[r].get("offcycle_uncertainty", 0) for r in order]
    fig = go.Figure()
    fig.add_scatter(x=order, y=[a + b for a, b in zip(n, band)],
                    line=dict(width=0), showlegend=False,
                    hoverinfo="skip")
    fig.add_scatter(x=order, y=n, name="reconstructed size",
                    line=dict(color="#1f4e79", width=2),
                    fill="tonexty",
                    fillcolor="rgba(31,78,121,0.15)")
    fig.update_layout(height=320, xaxis=dict(tickangle=60),
                      yaxis_title="constituents",
                      title=f"{mkt} — index size, reconstructed")
    design.chart(fig)
    st.caption(
        f"Anchor: {o['anchor_source']}. Rolled backwards one "
        "review at a time through the count-validated changes "
        "database. Shaded band = the KNOWN undercount from "
        "off-cycle exits (M&A/delisting/sanction deletions "
        "never printed in a review list) whose addition "
        "predates that point — the estimate's floor is the "
        "line, its ceiling is the top of the band.")
    pick = st.selectbox("Reconstruct membership after review",
                        list(reversed(order)), key="tm")
    mem = o["members"].get(pick, [])
    prev_i = order.index(pick) - 1
    prev = o["members"].get(order[prev_i]) if prev_i >= 0 else None
    cc1, cc2 = st.columns([1, 2])
    cc1.metric(f"Members after {pick}", len(mem))
    cc1.metric("Off-cycle uncertainty",
               f"+{cnt[pick].get('offcycle_uncertainty', 0)}")
    if prev is not None:
        gone = sorted(set(prev) - set(mem))
        came = sorted(set(mem) - set(prev))
        cc1.caption(f"vs {order[prev_i]}: +{len(came)} / "
                    f"-{len(gone)}")
    cc2.dataframe(pd.DataFrame({"security": mem}),
                  use_container_width=True, hide_index=True,
                  height=300)
    st.download_button(
        f"Download {mkt} {pick} membership (CSV)",
        pd.DataFrame({"security": mem}).to_csv(index=False)
        .encode(), file_name=f"msci_{mkt}_{pick}_members.csv")


def render():
    # c-235: pandas and plotly were imported here for the
    # section-2 chart. That chart is HTML now, and every other
    # section imports what it needs locally.
    from views import design
    df = _db()
    design.css()
    st.markdown("# MSCI Index Review Database")

    # c-220: the PHILIPPINES IS BACK, everywhere on this page.
    # (This supersedes c-174, which excluded it here.)
    #
    # markets.py excludes it because there is no usable price
    # source — Yahoo returns null on every PSE symbol — so no
    # market cap, no size screen, no prediction. That reason is
    # about the FORWARD pipeline, and this page makes no
    # predictions: it reports what MSCI already did, and the
    # Philippine review history is as real and as complete as
    # any other market's (46 changes, 2006-2026).
    #
    # Excluding it here was applying a data-availability rule
    # to a question that does not depend on the missing data.
    # markets.py is untouched; the exclusion still governs
    # every forward-looking script.
    markets = sorted(df.market.unique())
    _apac_strip(df, markets)
    # c-217: the market selector belongs to SECTION 2, not to
    # the page. Section 1 is all-markets by design, so a control
    # sitting above it implied it filtered the strip — which it
    # never did. It now renders inside _timeline(), immediately
    # under the section rule it actually governs.
    #
    # The dropdown shows "Hong Kong" and "New Zealand" while
    # returning the unspaced KEY, because the key joins to
    # markets.py and every data file. format_func is exactly
    # the seam for that: label on screen, key in the code.
    # c-234: the lead was three sentences of instruction — how
    # to read the axis, what a tick means, what a click does. A
    # chart that needs a manual has a problem the manual does
    # not fix, and the reader who scrolls past it is the one who
    # needed it. One line naming the control, and the chart
    # explains itself.
    #
    # NOTE: the click-to-open-in-section-5 behaviour still
    # works; it is simply no longer advertised here. If it turns
    # out nobody discovers it, the honest fix is to make the
    # affordance visible on the chart, not to put the sentence
    # back.
    _sect(2, "Index Review History",
          "Select a market to view its index review history.")
    # c-240: "All markets" leads the list. It aggregates the
    # section-2 statistics across all thirteen; the sections
    # below it that are inherently per-market say so rather than
    # silently showing one market's numbers under an
    # all-markets heading.
    _opts = [ALL] + markets
    mkt = st.selectbox("Market", _opts,
                       index=_opts.index("Taiwan"),
                       format_func=_pretty)
    rt = st.radio("Review type",
                  ["All", "Semi-Annual Index Review (May/Nov)",
                   "Quarterly Index Review (Feb/Aug)"],
                  horizontal=True)
    # c-214: the status strip is GONE from this page at
    # Bill's request. The ticker-coverage disclosure it carried
    # (BACKLOG 4) is not lost — section 7's scoreboard has a
    # "Tickered" column per market, so the honesty requirement
    # still has a home. Dropping the number without checking
    # that would have been a quiet regression.
    with st.expander("Note on Semi-Annual and Quarterly Index Reviews"):
        st.markdown(
            "<p style='font-size:0.82rem;color:#5b6770;"
            "line-height:1.55;margin:0'>"
            "<b>These labels describe the old rules, not "
            "today's.</b><br><br>"
            "MSCI moved the Global Investable Market Indexes to "
            "a <b>Quarterly Comprehensive Index Review</b> "
            "schedule from the February 2023 review, after a "
            "market consultation. The February and August "
            "reviews now get the same comprehensive treatment "
            "the May and November reviews always had.<br><br>"
            "Until February 2023, MSCI ran two different kinds "
            "of review. The <b>Semi-Annual Index Review</b>, "
            "each May and November, rebuilt the index from "
            "scratch. The <b>Quarterly Index Review</b>, each "
            "February and August, was a lighter check that only "
            "picked up companies whose size had moved "
            "sharply.<br><br>"
            "The difference was significant — average number "
            "of "
            "index changes across all 13 APAC markets, per "
            "review:<br>"
            "&nbsp;&nbsp;<b>Before 2023</b> &nbsp;May/Nov "
            "<b>117</b> &nbsp;·&nbsp; Feb/Aug <b>13</b> "
            "&nbsp;<i>(9x)</i><br>"
            "&nbsp;&nbsp;<b>Since 2023</b> &nbsp;&nbsp;&nbsp;May/"
            "Nov <b>81</b> &nbsp;·&nbsp; Feb/Aug <b>73</b> "
            "&nbsp;<i>(roughly equal)</i><br><br>"
            "MSCI now applies the full semi-annual method "
            "every quarter, so a February or August review is "
            "as likely to move the index as any other "
            "quarterly review.</p>",
            unsafe_allow_html=True)
    sub = df if mkt == ALL else df[df.market == mkt]
    if rt.startswith("Semi-Annual"):
        sub = sub[sub.review_type == "SAIR"]
    elif rt.startswith("Quarterly"):
        sub = sub[sub.review_type == "QIR"]

    # ---- 1. the rhythm ----------------------------------
    revs = _all_reviews()
    if rt.startswith("Semi-Annual"):
        revs = [r for r in revs if r[:3] in ("May", "Nov")]
    elif rt.startswith("Quarterly"):
        revs = [r for r in revs if r[:3] in ("Feb", "Aug")]
    per = sub.groupby(["review", "action"]).size().unstack(
        fill_value=0).reindex(revs, fill_value=0)
    if "ADD" not in per:
        per["ADD"] = 0
    if "DEL" not in per:
        per["DEL"] = 0
    # c-215: n_rev and quiet were only feeding the two cards
    # Bill removed. Left as dead locals they would read as a
    # statistic someone forgot to display.

    # c-214: the per-market "Most recent change" block is GONE.
    #
    # It rendered as a SECOND "Section 1" — same number, same
    # question — because the new all-markets strip answers
    # exactly what it answered, for every market rather than
    # one, and the hover card carries the names it used to list.
    # Keeping both would have shown the reader "Section 1"
    # twice.
    #
    # Nothing is lost: the strip covers the selected market too,
    # and its four statistics (review label, adds, dels, quiet
    # rate) are either in the strip or in section 2 below. If
    # Bill wants the named list back for the selected market
    # specifically, it is PARKED P7.
    # ---- the rhythm --------------------------------------
    # (the section rule and its market selector render above,
    #  next to the control they govern)
    # c-215: exactly four figures, as Bill asked — median AND
    # mean for each side, each its own card rather than a
    # subtitle. The pair matters: this distribution is skewed by
    # the pre-2023 May/Nov rebuilds, so mean above median IS the
    # signal, and burying the mean in small type under the
    # median hid the comparison the reader needs to make.
    #
    # "Busiest review" and "Total changes" are gone at Bill's
    # request. The quiet-review rate went with them to keep the
    # row at four; it is one line to restore.
    _cards([
        {"k": "Additions per review", "kind": "add",
         "v": f"{per.ADD.median():.0f}", "s": "median"},
        {"k": "Additions per review", "kind": "add",
         "v": f"{per.ADD.mean():.1f}", "s": "mean"},
        {"k": "Deletions per review", "kind": "del",
         "v": f"{per.DEL.median():.0f}", "s": "median"},
        {"k": "Deletions per review", "kind": "del",
         "v": f"{per.DEL.mean():.1f}", "s": "mean"}])
    # mean sits beside the median on purpose: this distribution
    # is skewed by the pre-2023 May/Nov rebuilds, so mean >
    # median is itself the signal.

    # c-218's NaN-to-empty-string fix is no longer needed here:
    # by_rev builds two plain lists per review, so a side with
    # no names is an empty list rather than a NaN that renders
    # as the word "nan".
    # c-235: HTML, not plotly. See _history_html for why —
    # the short version is that Bill asked for a hover card
    # that can be entered, styled like section 1, complete, and
    # carrying a link, and plotly's SVG tooltip can do none of
    # the four.
    by_rev = {}
    for r in per.index:
        g = sub[sub.review == r]
        by_rev[r] = (g[g.action == "ADD"].security.tolist(),
                     g[g.action == "DEL"].security.tolist())
    # c-237: ZOOM, restored as a year range.
    #
    # Bill asked where the zoom controls went. Plotly's were
    # drag-to-zoom, which is why c-215 had to add a toolbar —
    # without one there was no way back out. A range control
    # cannot strand anyone: the state is visible, and dragging
    # it back is the same gesture as dragging it in.
    _yrs = sorted({2000 + int(r[3:]) for r in per.index})
    if len(_yrs) > 3:
        lo, hi = st.select_slider(
            "Years shown", options=_yrs,
            value=(_yrs[0], _yrs[-1]))
        keep = [r for r in per.index
                if lo <= 2000 + int(r[3:]) <= hi]
        if keep:
            per = per.loc[keep]
    st.markdown(_history_html(per, by_rev, REGIME),
                unsafe_allow_html=True)
    # c-218: seasonality belongs here, with the rest of this
    # market's history, rather than stranded at the foot of the
    # page under a different section.
    _seasonality(sub)

    # ---- 1b. who is IN the index right now ---------------
    _sect(3, "Who Is in the Index Right Now",
          "Current constituents, by weight and years in the "
          "index.")
    if mkt == ALL:
        # c-240: this section reads ONE market's official
        # constituent list with weights. There is no all-APAC
        # constituent list — MSCI publishes a separate index per
        # country — so aggregating here would invent a portfolio
        # nobody holds.
        st.info("Pick a single market above to see its current "
                "constituents. MSCI publishes a separate index "
                "per country, so there is no combined "
                "constituent list to show here.")
    else:
        _members_now(mkt)

    # ---- 2. the roster + lookup --------------------------
    # c-216: RENUMBERED, because Bill saw section 3 followed by
    # section 5 and rightly read it as a mistake. It was: the
    # Membership time machine holds number 4 and has never
    # rendered — _time_machine() is defined and never called
    # (PARKED P6). The lint has printed it as a KNOWN GAP on
    # every run since c-211, but a gap the lint tolerates is
    # still a gap the READER sees.
    #
    # Numbers now run 1-6 with nothing missing. If the time
    # machine is restored it takes the next free number rather
    # than reopening a hole in the middle.
    _sect(4, "Security Lookup",
          "Search for an individual company's index review "
          "history.")

    @st.cache_data(show_spinner=False)
    def _roster(mkt):
        """Every company ever in this market's index since
        2006: all changed names (from the DB) + current members
        that never changed (pre-2006 incumbents). Status is
        inferred from the LAST recorded action; current-member
        names are matched by normalized name (imperfect for a
        few markets — unmatched incumbents still listed)."""
        import json as _json
        import re as _re

        _ABBR = {"HLDG": "HOLDING", "HLDGS": "HOLDINGS",
                 "INTL": "INTERNATIONAL", "GRP": "GROUP",
                 "MFG": "MANUFACTURING", "SVCS": "SERVICES",
                 "FINL": "FINANCIAL", "INDS": "INDUSTRIES",
                 "TRANSP": "TRANSPORT"}
        _DROP = {"CO", "LTD", "CORP", "INC", "COMPANY",
                 "CORPORATION", "ADR", "THE", "LIMITED", "PLC",
                 "HK"}
        # share-class letters are IDENTITY in China (A/H lines
        # are separate index securities) — stripped elsewhere
        _CLS = ({"A", "B", "H", "C"} if mkt != "China"
                else set())

        def _n(s):
            s = _re.sub(r"\(.*?\)", " ", str(s).upper())
            s = _re.sub(r"[^A-Z0-9 ]", " ", s)
            toks = [_ABBR.get(t, t) for t in s.split()]
            while len(toks) > 1 and toks[-1] in (_DROP | _CLS):
                toks.pop()
            return " ".join(toks)
        g = df[df.market == mkt].sort_values(["year", "month"])
        rows = {}
        for _, r in g.iterrows():
            # c-107 (user design): TICKER-FIRST entity key —
            # a verified ticker is ground truth; canonical
            # name is the fallback for unresolved (mostly
            # delisted) names. Populated by
            # scripts/ticker_backfill.py + changes_db rebuild.
            t = str(r.get("ticker", "") or "")
            k = f"T:{t}" if t else _n(r.security)
            e = rows.setdefault(k, {
                "security": r.security, "aka": set(),
                "ticker": r.get("ticker", r.code) or r.code,
                "hist": []})
            e["security"] = r.security      # most recent variant
            e["aka"].add(r.security)
            e["ticker"] = (r.get("ticker", r.code) or r.code
                           or e["ticker"])
            e["hist"].append((r.review, r.action,
                              r.eff_date_est))
        mem = _json.loads((ROOT / "data" / "apac_members.json")
                          .read_text(encoding="utf-8"))["markets"]
        # STRICT Standard membership: standard_members only —
        # the names dict is the ANCHOR UNION, which for IMI-
        # anchor markets (ID/PH/NZ/TH) includes Small-Cap-only
        # names (the bug the census caught: 13 "members" in an
        # 11-member index)
        _m = mem.get(mkt, {})
        _names = _m.get("names") or {}
        curn = {_n(_names.get(t) or t): t
                for t in _m.get("standard_members", [])}
        seen = set(rows)
        out = []
        for k, e in rows.items():
            s = e["security"]
            last = e["hist"][-1]
            # status reconciled vs the CURRENT member list:
            # review lists miss OFF-CYCLE exits (M&A/delisting
            # "Early Deletions"), so last=ADD alone is not
            # proof of membership
            _tick = str(e["ticker"] or "")
            _std = _m.get("standard_members", [])
            _root = _tick.split(".")[0]
            # c-113 venue-aware match: HK-listed codes are
            # stored zero-stripped ('0914.HK' vs '914');
            # onshore 6-digit codes keep leading zeros
            _hkf = (_tick.endswith(".HK")
                    or (mkt in ("HongKong", "China")
                        and _re.fullmatch(r"\d{1,5}", _root)))
            _is_mem = (k in curn
                       or _tick in _std
                       or _root in _std
                       or (_hkf and (_root.lstrip("0") or "0")
                           in {x.lstrip("0") or "0"
                               for x in _std})
                       or _n(s) in curn)
            if _is_mem:
                status = ("IN — re-entry not in review "
                          "record (off-cycle, est.)"
                          if last[1] == "DEL"
                          else "IN the index")
            elif last[1] == "ADD":
                status = "OUT — off-cycle exit (est.)"
            else:
                status = "OUT of the index"
            out.append({
                "security": s, "ticker": e["ticker"],
                "status": status,
                "last change": f"{last[1]} {last[0]}",
                "last change date": last[2],
                "moves": len(e["hist"]),
                "history since 2006": " → ".join(
                    f"{a} {rv}" for rv, a, _ in e["hist"]),
                "aka": (" | ".join(sorted(e["aka"] - {s}))
                        if len(e["aka"]) > 1 else "")})
        for nn, tick in curn.items():
            if nn not in seen:
                out.append({
                    "security": nn.title(), "ticker": tick,
                    "status": "IN the index",
                    "last change": "none since 2006",
                    "last change date": "pre-2006 incumbent",
                    "moves": 0,
                    "history since 2006": "member throughout",
                    "aka": ""})
        # c-156: ONE ROW PER TICKER. MSCI has spelled the
        # same company several ways over 20 years ("ACCTON
        # TECHNOLOGY CORP" in a 2007 list, "Accton Technology"
        # in the current constituent file), which produced two
        # rows for 2345. The ticker is the stable identity, so
        # rows are collapsed on it: histories merge, the
        # richest status wins, and the display name comes from
        # Yahoo (data/yahoo_names.json) with the MSCI spellings
        # kept in "aka".
        import pandas as _pd
        _yn = ROOT / "data" / "yahoo_names.json"
        _names = json.loads(_yn.read_text(encoding="utf-8")) if _yn.exists() \
            else {}
        _sfx = {"Australia": ".AX", "HongKong": ".HK",
                "India": ".NS", "Indonesia": ".JK",
                "Japan": ".T", "Korea": ".KS",
                "Malaysia": ".KL", "NewZealand": ".NZ",
                "Philippines": ".PS", "Singapore": ".SI",
                "Taiwan": ".TW", "Thailand": ".BK",
                "China": ".SS"}.get(mkt, "")

        def _yahoo_name(tk):
            tk = str(tk or "").strip()
            if not tk:
                return None
            return (_names.get(tk) or
                    _names.get(tk + _sfx) or
                    _names.get(tk.split(".")[0] + _sfx))

        # c-159: ticker hygiene before the merge —
        #   1. strip the exchange suffix (".TW" etc); the code
        #      is the identity, the venue is decoration
        #   2. backfill blanks from the verified name->ticker
        #      lookup (data/yahoo_tickers.json)
        #   3. anything still blank is labelled from the
        #      CURATED delisting register, else "Not matched"
        #      — we never assert a delisting we cannot cite
        _tp = ROOT / "data" / "yahoo_tickers.json"
        _tmap = json.loads(_tp.read_text(encoding="utf-8")) if _tp.exists() \
            else {}
        _dp = ROOT / "data" / "delisted_register.json"
        _dreg = (json.loads(_dp.read_text(encoding="utf-8")).get(mkt, {})
                 if _dp.exists() else {})
        for r in out:
            tk = str(r.get("ticker") or "").strip()
            if tk.lower() in ("", "nan", "none"):
                tk = _tmap.get(f"{mkt}|{r['security']}", "")
            tk = tk.split(".")[0]
            if not tk:
                nm = str(r["security"]).upper()
                tk = "Delisted" if nm in _dreg else "Not matched"
            r["ticker"] = tk

        merged, by_tick = [], {}
        for r in out:
            tk = str(r.get("ticker") or "").strip()
            if tk in ("Delisted", "Not matched") or not tk:
                merged.append(r)      # unresolved: never merge
                continue
            k = tk.split(".")[0].upper()
            if (mkt, k) in NEVER_MERGE:
                # c-202: two DIFFERENT issuers wearing one
                # ticker. Collapsing them invents a company.
                r = dict(r)
                r["ticker"] = f"{k} ⚠"
                r["aka"] = NEVER_MERGE[(mkt, k)]
                merged.append(r)
                continue
            if k not in by_tick:
                by_tick[k] = dict(r)
                continue
            a = by_tick[k]
            names = {a["security"], r["security"]} | {
                x for x in (a.get("aka", "") + "|"
                            + r.get("aka", "")).split("|") if x}
            # c-202: UNION THE HISTORIES, do not pick a winner.
            #
            # The old rule kept whichever spelling had more
            # moves and threw the other away. Measured across
            # the database: ALL 25 merged tickers lost history
            # and 28 index changes disappeared from the
            # timelines on this page. IDFC is the clean example
            # — "IDFC BANK" ADD Nov16 / DEL May18 and "IDFC
            # FIRST BANK" ADD Aug23 are one company across a
            # rename, and the row showed only the Aug23 leg
            # while the Moves column said 1. The whole point of
            # collapsing on ticker is to reunite a split
            # history; discarding half of it defeats that.
            steps = []
            for h in (a.get("history since 2006", ""),
                      r.get("history since 2006", "")):
                steps += [x.strip() for x in h.split("→")
                          if x.strip()
                          and x.strip() != "member throughout"]
            uniq = sorted(set(steps), key=_rev_key)
            if uniq:
                a["history since 2006"] = " → ".join(uniq)
                a["moves"] = len(uniq)
                last = uniq[-1]
                a["last change"] = last
            # the status of the LATER record wins, since status
            # is a statement about today
            if _rev_key(r.get("last change", "")) >= \
                    _rev_key(a.get("last change", "")):
                a["status"] = r["status"]
                a["last change date"] = r["last change date"]
            a["aka"] = " | ".join(sorted(names))
        # c-241: A DISPLAY NAME MAY NOT ERASE A DISTINCTION THE
        # SOURCE MAKES.
        #
        # Bill: three rows read "Hyundai Motor Company" with
        # tickers 005380, 005385 and 005387 and asked why the
        # tickers differ. They differ because they are three
        # different securities — the common line and two
        # preferred lines — and MSCI names them apart ("HYUNDAI
        # MOTOR S1 PREF"). Yahoo does not: it returns the
        # ISSUER name for all three, and c-156 preferred Yahoo's
        # spelling because it is tidier. Tidier, and in this
        # case wrong: the table showed one company three times.
        #
        # Measured across yahoo_names.json, 130 names serve more
        # than one ticker. They are three different situations
        # and only the first is safe to rename:
        #   * a genuine rename or spelling variant (one
        #     security) — Yahoo's name is an improvement
        #   * share classes (Hyundai common/PREF1/PREF2)
        #   * dual listings (Anhui Conch 0914.HK / 600585.SS)
        # The last two are DIFFERENT SECURITIES, and a shared
        # display name makes the table say something false.
        #
        # So the Yahoo name is used only when it stays unique
        # within the market. Where it would collide, the MSCI
        # name is kept, because MSCI is the source that draws
        # the distinction the reader needs.
        _yn_use = {}
        for k, a in by_tick.items():
            yn = _yahoo_name(a.get("ticker"))
            if yn:
                _yn_use.setdefault(yn, []).append(k)
        _collide = {n for n, ks in _yn_use.items() if len(ks) > 1}
        for k, a in by_tick.items():
            yn = _yahoo_name(a.get("ticker"))
            if yn and yn not in _collide:
                a["aka"] = " | ".join(
                    sorted({x for x in a.get("aka", "")
                            .split(" | ") if x
                            and x != yn} | {a["security"]}
                           - {yn}))
                a["security"] = yn
            elif yn:
                # keep MSCI's name; record the issuer name so
                # the link between the lines is not lost
                a["aka"] = " | ".join(
                    sorted({x for x in a.get("aka", "")
                            .split(" | ") if x} | {yn}))
            merged.append(a)
        return _pd.DataFrame(merged).sort_values(
            ["status", "security"]).reset_index(drop=True)

    if mkt == ALL:
        import pandas as _pd
        ros = _pd.concat(
            [_roster(m).assign(market=_pretty(m))
             for m in markets], ignore_index=True)
    else:
        ros = _roster(mkt)
    # c-154: the IN/OUT/total KPI row removed. "Currently IN"
    # was counting 116 for Taiwan against 77 actual
    # constituents — the roster falls back to IN when
    # normalized-fuzzy matching cannot pair a historical name
    # with a deletion, so unmatched names inflated the count.
    # The per-name status in the table below is still useful;
    # the aggregate was not, and was wrong.
    # c-155: the placeholder example is now the market's
    # LARGEST index member (by MSCI weight), with its ticker
    # from the roster where we have one — so it stays correct
    # as membership changes instead of being a hard-coded
    # guess per market.
    _ex = "NANYA, 2408"
    _off = _official()
    _cons = ((_off or {}).get("markets", {}).get(mkt, {})
             .get("constituents") or [])
    if _cons:
        _top = max(_cons, key=lambda x: x.get("weight", 0))
        # c-163: matching on the FIRST WORD alone put "Taiwan
        # Business Bank" in the example box, because MSCI's
        # largest name is "TAIWAN SEMICONDUCTOR MFG" and dozens
        # of Taiwanese companies start with "Taiwan". Require
        # the first TWO distinctive words, which pins TSMC.
        _tok = [t for t in str(_top["security"]).upper().split()
                if len(t) > 2][:2]
        _up = ros.security.str.upper()
        _hit = ros[[all(t in n for t in _tok) for n in _up]]
        if not len(_hit):
            _hit = ros[_up.str.startswith(_tok[0])]
        if len(_hit) > 1:            # prefer a row with a ticker
            _wt = _hit[_hit.ticker.astype(str).str.strip()
                       .ne("")]
            _hit = _wt if len(_wt) else _hit
        if len(_hit):
            _nm = str(_hit.iloc[0].security)   # Yahoo full name
            _tk = (str(_hit.iloc[0].ticker).split(".")[0]
                   if _hit.iloc[0].ticker else "")
        else:
            _nm, _tk = str(_top["security"]), ""
        _ex = f"{_nm}, {_tk}" if _tk else _nm
    q = st.text_input("Company name or stock ticker "
                      f"(e.g. {_ex})")
    show = ros
    if q:
        t = q.strip().upper()
        rt_ = ros.ticker.astype(str).str.upper()
        show = ros[(ros.security.str.upper()
                    .str.contains(t, regex=False))
                   | (rt_ == t)
                   | (rt_.str.split(".").str[0] == t)]
        if show.empty:
            st.info(f"No record for {q!r} in {mkt} "
                    "(2006 -> now).")
    _cols = {"security": "Security", "ticker": "Ticker",
             "status": "Status", "last change": "Last Change",
             "moves": "Moves",
             "history since 2006": "History Since 2006"}
    # c-218: "Last Change Date" dropped, and "none since 2006"
    # becomes a dash. The phrase was doing two jobs badly — it
    # is not a change, and it is not a date. A dash says "no
    # change on record" without pretending to be either, and it
    # matches the mark used for a quiet market in section 1.
    _show = (show.drop(columns=[c for c in
                                ("aka", "k", "last change date")
                                if c in show.columns])
                 .copy())
    _show["last change"] = [
        "–" if str(v).strip().lower() == "none since 2006" else v
        for v in _show["last change"]]
    # c-221: through _rtable, so the headers line up with their
    # own values. Six columns here, so no forced first-column
    # width — "History Since 2006" needs the room more than the
    # name does.
    _rtable(_show.rename(columns=_cols), height=330,
            first_width=None)
    # c-218: the ticker-collision audit is OFF the page at
    # Bill's request and kept on file instead — it is a
    # DATA-QUALITY record, and this page is for readers,
    # not auditors. Regenerate with
    #     py scripts\\ticker_collisions.py
    # which writes docs/TICKER_COLLISIONS.md. NEVER_MERGE
    # still governs the roster; only the DISPLAY moved.
    with st.expander("Most Frequently Reclassified Securities"):
        # c-157: built from the DEDUPED roster, not the raw
        # change list — otherwise one company split across two
        # MSCI spellings shows two half-histories and neither
        # ranks correctly.
        churn = (ros[ros["moves"] > 0]
                 .sort_values("moves", ascending=False)
                 .head(15)[["security", "ticker", "moves",
                            "history since 2006"]]
                 .rename(columns={"security": "Security",
                                  "ticker": "Ticker",
                                  "moves": "Moves",
                                  "history since 2006":
                                      "History Since 2006"}))
        _rtable(churn, first_width=None)

    # ---- 2b. the time machine ----------------------------

    # ---- 3. individual review study ----------------------
    _sect(5, "Individual Index Review History",
          "Pick a review period to see the index changes.")
    active = [r for r in revs
              if per.loc[r, "ADD"] + per.loc[r, "DEL"] > 0]
    if active:
        # c-235: the key no longer receives a click from section
        # 2 — that chart's card carries MSCI's link directly, so
        # the indirection through this picker is gone. The key
        # and the guard stay because they cost nothing and a
        # keyed widget is the thing any future cross-section
        # link would target. format_func keeps the compact
        # review CODE as the value (the PDF URL is built from
        # it) while the reader sees a real date.
        _opts = list(reversed(active))
        if st.session_state.get("rev_pick") not in _opts:
            st.session_state.pop("rev_pick", None)
        pick = st.selectbox("Review", _opts, key="rev_pick",
                            format_func=_rlabel)
        cols = st.columns(2)
        d1 = sub[(sub.review == pick)]
        _ACT = {"ADD": "Addition", "DEL": "Deletion"}
        with cols[0]:
            st.subheader(f"{_pretty(mkt)} — {_rlabel(pick)}")
            # c-243: the Ticker column is gone at Bill's
            # request. Section 4 is where a reader goes to
            # resolve a name to a code; here the question is
            # "which names moved at this review", and 35% of
            # the codes are blank anyway (see TICKER_AUDIT).
            _d = d1[["action", "security"]].copy()
            _d["action"] = _d.action.map(_ACT).fillna(
                _d.action)
            _rtable(_d.rename(columns={"action": "Action",
                                       "security": "Security"}),
                    first_width="26%")
        with cols[1]:
            st.subheader(f"All-APAC — {_rlabel(pick)}")
            ctx = (df[df.review == pick]
                   .groupby(["market", "action"]).size()
                   .unstack(fill_value=0)
                   .rename(columns=_ACT))
            ctx.index.name = "Market"
            ctx = ctx.reset_index()
            ctx["Market"] = [_pretty(m) for m in ctx.Market]
            _rtable(ctx, first_width=None)

        # c-163: the two actions sit BELOW both tables, spanning
        # the full width, so they read as belonging to the whole
        # review rather than to the left-hand table only.
        b1, b2 = st.columns(2)
        b1.link_button(
            "Official Change List (PDF)",
            f"https://www.msci.com/eqb/gimi/stdindex/"
            f"MSCI_{pick}_STPublicList.pdf",
            use_container_width=True)
        b2.download_button(
            f"Download Historical Index Changes For "
            f"{mkt} (CSV)",
            sub.to_csv(index=False).encode(),
            file_name=("msci_changes_"
                       + ("all_markets" if mkt == ALL else mkt)
                       + ".csv"),
            use_container_width=True)

    # c-218: section 6 "All APAC compared" REMOVED at Bill's
    # request, and the seasonality chart moved up under section
    # 2 where the rest of this market's history lives.
    #
    # _scoreboard() is left in the file, unused. It carried the
    # per-market TICKERED column, which was the last home of the
    # coverage disclosure from BACKLOG 4 — so that number is now
    # nowhere on the site. Recorded in PARKED P8 rather than
    # dropped silently; the underlying figure is still in the
    # database and one call restores the table.

