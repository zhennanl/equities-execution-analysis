"""Page — "Predict MSCI Index Changes" (c-162, renamed c-248).

Rebuilt from scratch at Bill's request. The v1 design is saved
intact at backup/walkthrough_v1_20260808/ and can be restored
by copying those three files back.

WHAT THIS PAGE IS NOW: one market, one review, written for a
program-trading dealer. Gone from v1: the market selector (only
Taiwan is predicted), the example selector, the "no finance
background" framing, the mode banner, the collapsed "For the
desk" blocks, and the per-step "what this step can get wrong"
callouts. The desk content moved into the main text — there is
no longer a second audience to write down to, and the limits
are consolidated into step 7 as part of the method.

UNCHANGED, deliberately: this module holds NO facts. Every
number on screen comes from walkthrough_story.story(), which
reads the engine's own output.

REVIEW is a module constant rather than a control. Aug-26 is
the open review; after it grades, switch to "May26" (or any
reconstructed review) and the page rewrites itself, including
the step-6 scoreboard.
"""
import json
import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

REVIEW = "Aug26"


def _src_stamp():
    """Fingerprint of the files the story is built from.

    c-308 — THE REASON A FIX KEPT LOOKING UNFIXED. `_story` was
    cached on (market, review) alone. Those two never change, so
    a long-running Streamlit process served the SAME story text
    forever no matter how many times walkthrough_story.py was
    edited. Three rounds of dollar-sign fixes verified green in
    a fresh interpreter and unchanged in Bill's browser, because
    the browser was reading a story built before any of them.
    Reloading the page cannot help: the cache outlives the
    rerun, and Streamlit does not re-import a module that is
    already in sys.modules either.
    It is the same failure apac_panel._stamp fixed at c-287, and
    I reproduced it here rather than reusing the lesson.
    Passing a fingerprint of the sources in as an ARGUMENT makes
    the cache do what everyone assumes it does — an edit to any
    of these files changes the key and the story is rebuilt.
    """
    out = []
    for f in (ROOT / "scripts" / "walkthrough_story.py",
              ROOT / "data" / "aug26_tw_call_v2.json",
              ROOT / "data" / "tw_mieu_universe.json"):
        try:
            st_ = f.stat()
            out.append((f.name, st_.st_mtime_ns, st_.st_size))
        except OSError:
            out.append((f.name, 0, 0))
    return tuple(out)


@st.cache_data(show_spinner=False)
def _story(market, review, stamp=None):
    from walkthrough_story import story
    return story(market, review)


def _inline(md):
    """Bold and links, for the one string that must be HTML.

    `design.sect`'s lead is injected as raw HTML, so markdown
    does not render there. This is the ONLY place on the page
    that still needs the conversion — everything else now lives
    in a keyed container where Streamlit renders markdown
    properly.
    """
    import re
    t = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", md or "")
    return re.sub(r"\[([^\]]+)\]\((https?://[^)]+)\)",
                  r"<a href='\2'>\1</a>", t)


_MONTH = ("Jan Feb Mar Apr May Jun Jul Aug Sep Oct "
          "Nov Dec").split()


def _human(iso):
    """2026-08-31 -> 31 Aug 2026."""
    try:
        y, m, d = str(iso)[:10].split("-")
        return f"{int(d)} {_MONTH[int(m) - 1]} {y}"
    except Exception:                              # noqa: BLE001
        return str(iso or "—")


def _factsheet_month(s):
    """"July 2026" for the factsheet the cutoff was read off.

    Taken from the registered call's own `cutoff_rule` ("MSCI
    Taiwan Index (USD) factsheet, 31 Jul 2026") rather than
    written into the figure, so pointing this page at another
    review moves the date with it instead of leaving last
    quarter's month sitting under this quarter's numbers.
    """
    import re
    rule = ((s.get("call") or {}).get("cutoff_rule") or "")
    m = re.search(r"(\d{1,2})\s+([A-Z][a-z]{2})\s+(\d{4})", rule)
    if not m:
        return None
    full = {"Jan": "January", "Feb": "February", "Mar": "March",
            "Apr": "April", "May": "May", "Jun": "June",
            "Jul": "July", "Aug": "August", "Sep": "September",
            "Oct": "October", "Nov": "November",
            "Dec": "December"}.get(m.group(2), m.group(2))
    return f"{full} {m.group(3)}"


# c-324, Bill: two clauses come out of every call rationale.
#
# STRIPPED AT RENDER, NOT EDITED IN THE FILE. The `why` strings
# live in data/aug26_tw_call_v2.json, which is the REGISTERED
# call — declared before MSCI announces and the thing this
# project is graded against. Editing it after the fact would
# destroy what makes it a prediction. So the page removes the
# clauses on the way to the screen and the record keeps them.
#
# What goes and why:
#   the §3.1.5 clause  — "a guaranteed addition when a slot
#     exists" overstates it. §3.1.5 governs the buffer, and a
#     slot existing is exactly the count-flex risk the call's own
#     haircut prices at 0.85. A sentence that says "guaranteed"
#     and a probability of 62% cannot both be on the page.
#   the band clause    — replaced by the fuller sentence built
#     in `_results`, which names the number and the consequence
#     instead of asserting a conclusion.
# (pattern, replacement). The §3.1.5 clause is SUBORDINATE — it
# hangs off the preceding sentence with a comma and carries that
# sentence's full stop — so removing the clause alone leaves
# "...addition bar, Free-float cap...". The comma goes with it and
# the full stop comes back.
_STRIP = (
    (", which \u00a73.1.5 makes a guaranteed addition when a "
     "slot exists.", "."),
    ("The verdict does NOT hold across the cutoff band, so it is "
     "carried at a reduced probability.", ""),
)


def _strip_clauses(text):
    out = str(text or "")
    for clause, rep in _STRIP:
        out = out.replace(clause, rep)
    return " ".join(out.split())


def _md_money(text):
    """Escape currency dollars for Streamlit's markdown.

    Streamlit reads `$ ... $` as inline LaTeX, so a calculation
    with two dollar signs in it renders the span between them as
    a formula — which is how "**&#36;15.75B** and EM Standard"
    lost its bold and its spaces. Inside a BACKTICK code span the
    dollar is already literal and must be left alone, so the
    string is split on backticks and only the odd segments (the
    prose) are escaped.
    """
    # c-305: `\\$` DOES NOT WORK, and the proof was on screen the
    # whole time — the one-dollar bullet rendered a visible
    # backslash ("here \\$3.61B") while the two-dollar bullets
    # still came out as LaTeX. So Streamlit's maths pass runs on
    # the raw text and does not honour a markdown backslash
    # escape: escaping either shows the backslash or does
    # nothing, depending on how many dollars are in the
    # paragraph. Two failure modes, one wrong fix.
    #
    # The reliable answer is to not write a dollar sign in prose
    # at all. "USD 15.75B" cannot start a formula. Inside a
    # BACKTICK code span the maths pass does not run, so the
    # arithmetic lines keep their `$` and stay readable as
    # money.
    txt = str(text).replace("&#36;", "$").replace("\\$", "$")
    parts = txt.split("`")
    return "`".join(p.replace("$", "USD ") if i % 2 == 0 else p
                    for i, p in enumerate(parts))


@st.cache_data(show_spinner=False)
def _names(stamp=None):
    """{code: company name}, for the scan tooltip.

    c-318, AND THIS IS THE ACTUAL BUG BEHIND BILL ASKING FOR THIS
    HOVER TWICE. Every one of the eight ADDITION rows in
    aug26_call_v2.json carries `"name": ""` — the deletions have
    names, the additions do not. So the tooltip that did exist
    showed a bare code on exactly the dots a reader most wants to
    identify, which is indistinguishable from no tooltip at all.
    The names are in yahoo_names.json and were simply never
    joined.
    """
    p = ROOT / "data" / "yahoo_names.json"
    if not p.exists():
        return {}
    try:
        raw = json.loads(p.read_bytes().decode("utf-8",
                                               errors="replace"))
    # NARROW, and c-318 is why. The first version of this caught
    # bare `Exception` — and `views/walkthrough.py` does not
    # import json, so `json.loads` raised NameError, the handler
    # swallowed it, and the function returned {} on every call.
    # The tooltip then showed a bare code on all eight additions
    # and looked exactly like "our data has no names for these",
    # which is the wrong conclusion and an unfalsifiable one.
    #
    # A handler here should cover a missing or corrupt FILE.
    # Anything else is a fault in this function and must be
    # allowed to raise.
    except (OSError, ValueError):
        return {}
    out = {}
    for k, v in raw.items():
        code = str(k).split(".")[0]
        if v and code not in out:
            out[code] = str(v)
    return out


# c-320: how far the derived thresholds are allowed to be wrong.
# Bill's call, and it is the right shape of question — the cutoff
# is not published by MSCI, it is reconstructed from an 85%
# coverage walk over a float stack that is itself estimated. A
# name whose verdict survives a +-5% move in the cutoff is a
# different animal from one that flips inside it.
BAND = 0.05


def _size_verdict(cap, lo, cut, hi, member, gates_ok):
    """(category, reason) for one candidate, from THIS page's
    thresholds.

    c-320 BUG FIX, AND IT WAS NOT A LABEL. The verdicts stored in
    aug26_call_v2.json were computed against that file's own
    thresholds — cutoff 6.74, addition bar 10.11 — which this
    project superseded when the buffers were re-based onto
    Taiwan's own Market Size-Segment Cutoff (7.22, bar 10.83).
    The chart drew its LINES at the corrected frame and its DOTS
    at the old one.

    The visible consequence was 3189 Kinsus at USD 10.30bn shown
    as QUALIFIES: it clears the superseded 10.11 bar and fails the
    corrected 10.83 one. The registered call on the same page does
    NOT include 3189 — so the figure contradicted the prediction
    beside it, and only Bill reading the multiple off the axis
    caught it.

    The second fault was the reason text. "blocked: above upper
    buffer" is the GATE'S NAME being printed as the failure, so a
    name below the bar was described as blocked for being above
    it. Failures now name the direction they actually failed in.
    """
    if member:
        if cap < lo:
            return "delete", "below the deletion floor"
        return "hold", "inside the buffer — held"
    if cap < hi:
        return "fails_size", "below the addition bar"
    if not gates_ok:
        return "fails_gate", "clears size, fails a float or "\
                             "foreign-room screen"
    return "qualifies", "clears every screen"


def _scan_chart(sc, k):
    """Step 4: every candidate against the two buffers.

    c-318 REPLACED AN SVG WITH A PLOTLY FIGURE, and the reason is
    not taste. The old `diagrams.shortlist_scan` carried its
    tooltip as an SVG `<title>` child — a ~5px target with a
    one-second browser delay — next to eight dots whose name field
    was empty. Bill asked for the hover twice.

    c-320 re-derives every verdict here rather than trusting the
    call file's stored one. See `_size_verdict`.
    """
    import math
    import plotly.graph_objects as go
    from views import design
    nm = _names(_src_stamp())
    lo, cut, hi = k["floor"], k["cutoff"], k["bar"]

    def label(r):
        code = str(r.get("code") or "")
        n = (str(r.get("name") or "").strip()
             or nm.get(code, ""))
        return f"{n} ({code})" if n else code

    def gates_ok(r):
        g = r.get("gates") or {}
        # every gate EXCEPT the size one, which is re-derived
        return all(v for kk, v in g.items()
                   if "buffer" not in str(kk).lower())

    pts = []
    for lane, items, member in (("non-members", sc.get("adds") or [],
                                 False),
                                ("incumbents", sc.get("deletes") or [],
                                 True)):
        for r in items:
            cap = r["cap_usd_b"]
            cat, why = _size_verdict(cap, lo, cut, hi, member,
                                     gates_ok(r))
            # does the verdict survive the threshold band?
            edge_lo = _size_verdict(cap, lo * (1 - BAND),
                                    cut * (1 - BAND),
                                    hi * (1 - BAND), member,
                                    gates_ok(r))[0]
            edge_hi = _size_verdict(cap, lo * (1 + BAND),
                                    cut * (1 + BAND),
                                    hi * (1 + BAND), member,
                                    gates_ok(r))[0]
            pts.append({"lane": lane, "cap": cap, "cat": cat,
                        "why": why, "label": label(r),
                        "robust": edge_lo == cat == edge_hi})

    # THE FOUR CATEGORIES. Bill: *"hollow is ambiguous, it can
    # mean blocked for additional failed screens, or blocked for
    # failing the size screen."* Exactly — one hollow marker was
    # carrying two different verdicts, so the legend is now
    # explicit and the two failures have different symbols.
    #
    # c-353, Bill: *"the legend is colliding with the content of
    # the graph."* IT IS A WIDTH PROBLEM, not a position one.
    # Four entries at the old wording ran to about 130
    # characters, which is wider than the chart column — so
    # plotly wrapped the legend onto a second row, and the second
    # row grew down past the bottom margin reserved for it.
    # Moving the legend without shortening it just moves the
    # collision. These say the same things in half the width; the
    # full reason for every marker is in its own hover.
    STYLE = {
        "qualifies": ("clears every screen", design.GREEN,
                      "circle", True),
        "fails_gate": ("clears size, fails another screen",
                       design.GREEN, "circle", False),
        "fails_size": ("fails on size", design.MUTED, "x", False),
        "delete": ("below the deletion floor", design.RED,
                   "circle", True),
        "hold": ("inside the buffer, held", design.RED,
                 "circle", False),
    }
    fig = go.Figure()
    for cat, (leg, colour, sym, filled) in STYLE.items():
        g = [p for p in pts if p["cat"] == cat]
        if not g:
            continue
        fig.add_scatter(
            x=[p["cap"] for p in g], y=[p["lane"] for p in g],
            mode="markers", name=leg,
            marker=dict(size=13, symbol=sym,
                        color=colour if filled else "white",
                        line=dict(color=colour, width=2)),
            # c-322: the robustness line is off the tooltip. It
            # is carried by the shaded band, which is visible
            # without hovering, and by the reason text in step 5.
            customdata=[[p["label"], p["cap"], p["cap"] / cut,
                         p["why"]] for p in g],
            # c-334: the verdict becomes the note rather than a
            # row — it is a sentence, not a label-and-value.
            hovertemplate=design.hover(
                "%{customdata[0]}", eyebrow="size screen",
                rows=[("full market cap",
                       "US$%{customdata[1]:.2f}bn"),
                      ("vs the cutoff",
                       "%{customdata[2]:.2f}x")],
                note="%{customdata[3]}"))
    caps = [p["cap"] for p in pts]
    x0 = min(caps + [lo]) * 0.85
    x1 = max(caps + [hi]) * 1.15
    fig.add_vrect(x0=x0, x1=lo, fillcolor=design.RED, opacity=.06,
                  line_width=0, layer="below")
    fig.add_vrect(x0=hi, x1=x1, fillcolor=design.GREEN,
                  opacity=.07, line_width=0, layer="below")
    # c-324, Bill: his labels, and NO band on the market cutoff.
    #
    # The cutoff losing its band is the right call and worth
    # saying why. The ±5% is an error bar on the cutoff
    # CALCULATION, and the two buffers are derived FROM it — 2/3x
    # and 1.5x — so the uncertainty propagates to them. Drawing a
    # band on the cutoff as well as on its own derivatives shows
    # one error three times and invites a reader to think there
    # are three independent uncertainties. There is one.
    # c-331, Bill, second attempt: *"I still cannot see the label
    # ... unless I zoom out. And even when zoomed out, the labels
    # are not aligned with the vertical lines."*
    #
    # TWO SEPARATE BUGS, which is why the first fix only half
    # worked.
    #
    # 1. MISALIGNMENT IS THE LOG AXIS. `add_vline`'s annotation is
    #    positioned in the axis's own coordinate space, and this
    #    axis is `type="log"` — where a coordinate of 7.22 means
    #    10^7.22, not 7.22. The LINE is converted for you; the
    #    ANNOTATION is not, so every label was placed at an x
    #    astronomically off-scale and got clamped to the plot
    #    edge. That is also why it looked like a right-shift and
    #    why zooming changed it.
    #
    # 2. CLIPPING IS THE MARGIN. Annotations drawn at the top of
    #    the plot area have nowhere to go when the top margin is
    #    62px and the text is two lines.
    #
    # So the annotations are now added EXPLICITLY, at
    # `math.log10(v)`, against `yref="paper"` above the plot, with
    # the top margin opened to fit them. Line and label are drawn
    # by two calls that each state their own coordinate space
    # rather than one call that silently uses two.
    for v, colour, txt, banded, yy in (
            # INTERPOLATED, never typed. This module holds no
            # facts — pointing the page at another review has to
            # move these labels with it, and a hard-coded "$7.22B"
            # would sit under a line drawn somewhere else.
            (lo, design.RED, "lower buffer", True, 1.005),
            (cut, design.MUTED, "market cutoff", False, 1.075),
            (hi, design.GREEN, "upper buffer", True, 1.005)):
        # Value on the first line, name on the second. Halving the
        # width is what stops three centred labels colliding on a
        # log axis where they sit close together; the stagger
        # above only has to separate the middle one.
        label = f"<b>${v}B</b><br>{txt}"
        if banded:
            label += (f"<br>{v * (1 - BAND):.2f}–"
                      f"{v * (1 + BAND):.2f}")
            fig.add_vrect(x0=v * (1 - BAND), x1=v * (1 + BAND),
                          fillcolor=colour, opacity=.13,
                          line_width=0, layer="below")
        fig.add_vline(x=v, line_color=colour,
                      line_width=1 if v == cut else 2,
                      line_dash="dot" if v == cut else None)
        fig.add_annotation(
            x=math.log10(v), xref="x", y=yy, yref="paper",
            text=label, showarrow=False, align="center",
            xanchor="center", yanchor="bottom",
            font=dict(size=10.5, color=colour))
    fig.update_layout(
        height=430,
        # c-336, Bill: *"the legends are interfering with our
        # chart."* The legend sat at y=-0.42 with a 0px bottom
        # margin, so it had no reserved space and overlapped the
        # axis title and the lowest lane. Pushed further below
        # and given a bottom margin to live in.
        #
        # c-353: and pinned to the CONTAINER rather than to the
        # plot area. `y=-0.30` was measured against the plotting
        # region, which is only ~230px tall here — so the legend
        # floated 70px under the axis and then had 16px of the
        # 86px margin left for a row that needed more. Against
        # `yref="container"` it sits at the bottom edge of the
        # figure itself and cannot drift when the number of lanes
        # changes the plot height.
        legend=dict(orientation="h", yanchor="bottom", y=0.01,
                    yref="container", xanchor="left", x=0,
                    font=dict(size=11), bgcolor="rgba(0,0,0,0)"),
        xaxis=dict(title="full market capitalisation, US$bn "
                         "(log scale)",
                   type="log", range=[math.log10(x0),
                                      math.log10(x1)]),
        yaxis=dict(title="", autorange="reversed"),
        # c-331: t=62 clipped a three-line label. The labels sit
        # ABOVE the plot area now, so the margin has to hold them.
        # c-336: the legend now sits below the axis title, so the
        # bottom margin has to hold both.
        margin=dict(l=0, r=10, t=112, b=92))
    design.chart(fig)
    st.caption(
        "**Note:** The shaded band on the addition bar and the "
        "deletion floor is ±5%, an error bar accounting for error "
        "in the cutoff-value calculation.")


def _step_visuals(key, s):
    """The diagrams that belong to a step (c-249).

    Bill wants a graph in every step. They arrive one step at a
    time, and each has to EARN its place by letting prose out —
    step 1 shed two paragraphs for the two below. A step with
    no entry here simply draws nothing.
    """
    d = s.get("dates") or {}
    from views import diagrams
    if key == "cutoff":
        # c-253: the two-stage funnel — a global number opens a
        # corridor, the market's own walk picks a point inside
        # it, buffers straddle that point. Drawn only when the
        # Market Size-Segment Cutoff exists; a reconstructed
        # review has none (see the step's own text).
        k = s["keys"]
        if not k.get("cutoff"):
            return
        # c-283 BUG FIX. `pub_idx` and `cross_rank` were never
        # passed, so card 4 formatted `None or 0` and shipped
        # reading "the factsheet gives the index $0B of free
        # float ... the —th company". Both values are in the
        # story already — `crossing` carries the factsheet
        # figure and the rank it produces — so the card was
        # printing zeros next to data that was sitting one
        # dictionary away.
        cr = s.get("crossing") or {}
        args = dict(
            dm_ref=k["gmsr_dm"],
            em_ref=k.get("em_ref", round(k["gmsr_dm"] / 2, 2)),
            lo=k["em_range"][0], hi=k["em_range"][1],
            cutoff=k["cutoff"], lower=k["floor"],
            upper=k["bar"], min_float=k.get("min_float_cap"),
            # c-268: the DM card states that the figure shown
            # is MSCI's published reference scaled to this
            # review's pricing. Both inputs come from the
            # rulebook constants file, so the drawing still
            # holds no facts of its own.
            pub_dm=(s.get("published") or {}).get("dm"),
            pub_asof=(s.get("published") or {}).get("asof"),
            pub_idx=cr.get("target_busd"),
            cross_rank=cr.get("crossing_rank"))
        # c-294, Bill: *"Revert the old step by step design, and
        # recover my old graph on the right hand side."*
        #
        # c-293 had split the ladder into seven standalone cards
        # so each Calculation dropdown could sit directly under
        # its own box. That bought interleaving and cost two
        # things: the connector arrows, each of which IS a
        # multiplication, and the right-hand scale that shows
        # where the buffers actually land against the cutoff.
        # The composed figure is back, with the seven dropdowns
        # beneath it in card order — a Streamlit expander cannot
        # live inside an SVG, so under the figure is as close to
        # "inside the textbox" as this page can get.
        st.markdown(diagrams.size_ladder(**args),
                    unsafe_allow_html=True)
        for n, name, val, calc in diagrams.size_ladder_steps(
                coverage=cr.get("coverage", 0.85),
                screened=cr.get("screened"),
                idx_asof=_factsheet_month(s), **args):
            # `&#36;` is an HTML entity and an expander LABEL
            # is plain markdown, so it would print literally.
            # "USD" rather than "$" because two dollar signs in
            # one label (the range card has a low and a high)
            # are a LaTeX pair to Streamlit's renderer — the
            # same trap that mangled step 3's SVG at c-268.
            lab = val.replace("$", "USD ")
            with st.expander(f"Calculation — {n}. {name} "
                             f"{lab}"):
                st.markdown(_md_money(calc))
        return
    if key == "call":
        # c-257: how a conviction number is built. Bill: "I
        # don't even know how we calculate this either" — the
        # model was in a script and nowhere on the page.
        c = s.get("call") or {}
        br = (c.get("registered_base_rates") or {})
        hc = (c.get("registered_haircuts") or {})
        ex = next((r for r in (c.get("calls") or [])
                   if r.get("action") == "ADD"
                   and "guaranteed" in str(r.get("zone", ""))),
                  None)
        if not (ex and br and hc):
            return
        st.markdown(diagrams.conviction_waterfall(
            "base rate: above the 1.5x bar",
            br["add_guaranteed"],
            # c-276: clause number dropped. Every §-reference on
            # this page now lives in "Rulebook References" under
            # the step, with its page number and quoted text.
            # On a waterfall bar it was the least readable copy
            # of a citation that already appears in full below.
            [("the member count can flex",
              hc["count_flex"]),
             ("float is our estimate, not MSCI's",
              hc["float_estimated"]),
             ("names we cannot see take slots",
              hc["blind_band"])],
            ex["prob"]), unsafe_allow_html=True)
        st.caption(
            f"Worked on {ex['code']}, a representative addition "
            f"call. Every figure is read from the registered "
            f"call file, not typed here.")
        return
    if key == "buffers":
        # c-255: step 3 derived the lines, this applies
        # them.
        # Different job, so a different figure: who is on which
        # side, and by how much.
        k, sc = s["keys"], (s.get("scan") or {})
        if not (sc.get("adds") and k.get("cutoff")):
            return
        _scan_chart(sc, k)
        return
    # c-282: the crossing figure went with step 4. Bill asked
    # for that step removed entirely, and the figure only ever
    # existed to illustrate it. `diagrams.coverage_crossing` and
    # `walkthrough_story._crossing` are LEFT IN PLACE — they are
    # tested, they reproduce the cutoff of record from the
    # screened universe, and that reproduction is the thing that
    # caught step 3 and step 4 quoting two different crossings.
    # Deleting the check because the picture it drew is gone
    # would throw away the verification with the illustration.
    if key not in ("timeline", "data") or not d.get(
            "rebalance_close"):
        return
    if key == "timeline":
        # c-251: one figure, not two — the flow now lands on the
        # timeline it used to sit above.
        st.markdown(diagrams.review_flow(
            announced=_human(d.get("announced")),
            close=_human(d.get("rebalance_close")),
            announced_time=d.get("announced_time_lines"),
            market_close_label="TWSE closing auction"),
            unsafe_allow_html=True)
        st.caption(
            "Source: [MSCI Review Dates]"
            "(https://www.msci.com/eqb/pressreleases/archive/"
            "ir_dates.pdf) and [August 2026 Announcement]"
            "(https://ir.msci.com/news-releases/news-release-"
            "details/msci-august-index-review-announcement-"
            "scheduled-august-12-2026)")
        return
    if not d.get("equity_universe_cutoff"):
        return
    st.markdown(diagrams.cutoff_timeline(
        universe=_human(d.get("equity_universe_cutoff")),
        liquidity=_human(d.get("liquidity_cutoff")),
        price_from=_human(d.get("price_window_start")),
        price_to=_human(d.get("price_window_end")),
        announced=_human(d.get("announced")),
        close=_human(d.get("rebalance_close"))),
        unsafe_allow_html=True)
    # c-268: the window-screens figure is gone at Bill's
    # request — the four screens measured over a period are
    # covered in this step's notes, and a second figure was
    # spending a lot of the reader's attention on inputs that
    # decide far fewer calls than the three cutoffs above.
    # `diagrams.screen_windows` is deleted rather than left
    # unused; it is recoverable from history if it is wanted
    # back.
    # c-330, Bill: the source line moves OUT of the visuals and
    # below the Rulebook References toggle — see `_step_source`,
    # called after design.beats in render(). A source that sits
    # above the references it belongs to reads as a caption on
    # the figure instead of an attribution for the step.


# c-330, Bill: the GIMI attribution, rendered BELOW a step's
# Rulebook References rather than above them, and carried by both
# the data step and the cutoff step. The section reference was
# dropped from the visible text at his request — the link still
# goes to the same document.
_GIMI = ("Source: *[MSCI GIMI methodology, May 2026]"
         "(https://www.msci.com/eqb/methodology/meth_docs/"
         "MSCI_GIMIMethodology_May2026.pdf)*")
_SOURCED_STEPS = ("data", "cutoff")


def _step_source(key):
    if key in _SOURCED_STEPS:
        st.caption(_GIMI)


def _numbers(nums):
    """A step's figures, in the site's ruled figure row.

    c-245: these were `st.columns` + `st.metric`, which is the
    one figure treatment on the site that has NO rule under it.
    Bill: *"there isn't any divider between this header and the
    text box below."* Exactly — `design.stats` is ruled top and
    bottom and carries its own bottom margin, so the boundary
    the metrics never had comes for free, on every step at once.
    """
    from views import design
    design.stats([{"k": n["label"], "v": n["value"],
                   "s": n.get("note", "&nbsp;")} for n in nums])


# c-320, Bill: *"I want to delete the bar graph for step 5. In
# this step 5, we just show the prediction result."* `_lever` is
# removed rather than hidden. It drew the 30 smallest candidates
# as horizontal bars against the cutoff — which is the SAME
# comparison step 4's scan now makes, on the same thresholds, with
# a working hover and a legend. Two figures answering one question
# is how they drift apart, and step 4's is the better of the two.


# c-245: THE PAGE-LOCAL STYLESHEET IS GONE.
#
# It held four rules — `.steptitle`, `.stepnum`, `.lead`,
# `.sect` — that were a second, smaller heading system living
# alongside the site's. c-238 had already raised this page's
# two TOP-level headings to `design.sect` and left the seven
# step headings behind at 1.02rem, so the page had a hierarchy
# in which a step title and a page title were nearly the same
# size and neither matched anything on the review-database
# page.
#
# Bill, c-245: *"follow the same 'section' design as MSCI Index
# Review Database, but instead of section, we call them
# 'step'."* That is one word of difference, so it became a
# parameter on `design.sect(kind=...)` rather than a private
# copy here. A page-local stylesheet is how two designs start.


def _hero(s):
    """The page title, and nothing else.

    c-207 removed a gradient banner in favour of a status strip
    and four stat cards. c-278 removes those too, so what is
    left is a heading — which is the honest end state of a
    masthead that has been shrinking for three revisions.
    """
    from views import design
    design.css()
    # c-278: THE WHOLE MASTHEAD IS GONE at Bill's request — the
    # standfirst, the MKT/REVIEW/PRICE-CUTOFF strip, and the
    # four stat cards under it.
    #
    # Worth recording what it cost and what it did not. The
    # strip and the cards were answering "what am I looking at,
    # is it current, what are the thresholds" before the reader
    # had asked any of them, and between them they filled the
    # screen above step 1 with numbers that all reappear where
    # they belong: the deletion floor and addition bar are
    # cards 5 and 6 of the step-3 ladder, with their derivation
    # attached, and the price cutoff is drawn on the step-2
    # timeline against the ten days MSCI picks from. A figure
    # printed twice is not twice as clear.
    #
    st.markdown("# Predict MSCI Index Changes")


def _call_rows(rows, kind, caps):
    """Dense call rows, carrying the name's market cap.

    c-320, Bill: the probability bar is replaced by the company's
    market capitalisation. The probabilities have not been
    deleted from the project — they are fields on every call in
    data/aug26_tw_call_v2.json and still travel with the
    registered prediction. What went is their prominence on a
    step whose job is to state the result.
    """
    st.markdown(
        "".join(
            f"<div class='drow'>"
            f"<span class='dact {kind.lower()}'>{kind}</span>"
            f"<span class='dnm'>{r['name']}</span>"
            f"<span class='dcode'>{r['code']}</span>"
            f"<span class='dcode' style='flex:0 0 120px;"
            f"text-align:right;font-weight:700;color:#1f4e79'>"
            f"{_cap_txt(caps.get(str(r['code'])))}</span></div>"
            for r in rows),
        unsafe_allow_html=True)


def _cap_txt(v):
    return f"USD {v:,.2f}bn" if v else "—"


def _results(s):
    """THE ANSWER, above the method (c-171).

    Bill's read is right: most visitors want the names, not the
    derivation. The seven steps still exist and still generate
    every number — they simply move below a fold now.
    """
    from views import design
    c = s.get("call")
    if not c:
        return
    adds = [x for x in c["calls"] if x["action"] == "ADD"]
    dels = [x for x in c["calls"] if x["action"] != "ADD"]
    # c-320: sorted by SIZE now that size is the column shown.
    # Sorting by a probability the reader can no longer see would
    # be an order with no visible reason for it.
    caps = {str(u["code"]): u.get("cap")
            for u in (s.get("universe") or []) if u.get("code")}
    for r in (s.get("scan") or {}).get("adds", []) + \
            (s.get("scan") or {}).get("deletes", []):
        caps.setdefault(str(r["code"]), r.get("cap_usd_b"))
    adds.sort(key=lambda x: -(caps.get(str(x["code"])) or 0))
    dels.sort(key=lambda x: -(caps.get(str(x["code"])) or 0))
    # c-322, Bill: a name whose verdict flips inside the ±5% band
    # comes OFF the headline table. It is not deleted from the
    # page — its reasoning is in the amber block below, with the
    # band sentence attached — but a list headed "Additions" should
    # contain the calls this method is willing to stand behind.
    _k = s["keys"]
    _shaky = [x for x in adds
              if (caps.get(str(x["code"])) or 0) < _k["bar"] * 1.05]
    adds = [x for x in adds if x not in _shaky]
    # c-320, Bill: the "Index Review Prediction — MSCI Taiwan,
    # August 2026" heading is removed. It sat directly under the
    # step-5 rule and repeated it — the step already says this is
    # the prediction, and the market and review are named in the
    # page title.
    a, b = st.columns(2)
    with a:
        st.markdown(f"**Additions ({len(adds)})**")
        _call_rows(adds, "ADD", caps)
    with b:
        st.markdown(f"**Deletions ({len(dels)})**")
        _call_rows(dels, "DEL", caps)
    # ── WHY EACH NAME IS ON THE LIST ────────────────────────
    #
    # c-322, Bill: the reasoning moves OUT of a collapsed
    # expander and INTO the amber block, and the ±5% scoreboard
    # that used to sit here is deleted. The scoreboard restated in
    # four cells what one sentence about Phison says better, and
    # a reason a reader has to click for is a reason most readers
    # never see.
    k = s["keys"]
    body = []
    for r in c["calls"]:
        # c-296: the call file stores its rationale with `&#36;`
        # in it — right for a figure, printed as raw source in
        # markdown. This is the last place that renders it.
        why = _strip_clauses(
            _md_money(r.get("why", "")).replace("`", ""))
        cap = caps.get(str(r["code"]))
        # THE BAND SENTENCE, added only where it is true. Phison
        # clears the addition bar by about 3%, which is inside the
        # ±5% band on a cutoff nobody publishes — so the arithmetic
        # says ADD and the uncertainty on the arithmetic says do
        # not lean on it. Generated from the numbers rather than
        # typed, so it appears on whichever name is borderline
        # after a re-run rather than on Phison forever.
        extra = ""
        if cap and r["action"] == "ADD" and cap < k["bar"] * 1.05:
            over = cap / k["bar"] - 1
            extra = (
                f" <b>However, {r['name'].split()[0]} clears the "
                f"USD {k['bar']}bn bar by only {over:.1%}, which "
                f"is inside the ±5% error-bar band on the addition "
                f"bar. A slightly differently calculated addition "
                f"bar could exclude {r['name'].split()[0]} from "
                f"the index addition altogether. It is therefore "
                f"reported, but not carried as a confident "
                f"addition.</b>")
        body.append(f"<b>{r['name']} ({r['code']}) — "
                    f"{r['action']}</b><br>{why}{extra}")
    if body:
        design.caveat("<br><br>".join(body))


def render():
    try:
        s = _story("Taiwan", REVIEW, _src_stamp())
    except SystemExit as e:
        st.title("Predict MSCI Index Changes")
        st.error(str(e))
        return
    _hero(s)

    # c-301, Bill: the "How We Predict Index Review Changes"
    # part heading is removed, and the prediction block moves
    # from the top of the page into the step that makes the
    # call. The page now opens straight on the method and ends
    # on the answer, which is the order the reader works in.
    _method(s)


def _method(s):
    """The seven steps, in the site's section grammar (c-245).

    THE ORDER OF A STEP IS FIXED (c-245):

        1. the step rule — eyebrow "Step n", serif title, and
           the step's own first line as the LEAD, so a reader
           who skims only the seven leads still gets the method
           end to end;
        2. the figure row, ruled top and bottom;
        3. the explanation, as BEATS (c-247);
        4. anything interactive.

    Before c-245 the lead sat BELOW the figures in a block of
    its own, so each step opened with numbers the reader had
    not yet been told the meaning of.

    STEP 7 KEEPS EVERY BEAT OPEN. It is the limits of the
    method, and D8 says a limitation the reader must carry is
    not a footnote — so it is certainly not a click.
    """
    from views import design
    for i, stp in enumerate(s["steps"]):
        body = [p for p in stp["plain"] if p.strip()]
        lead, rest = (body[0] if body else ""), body[1:]
        # c-268: a hairline closes the previous step. Not before
        # the first — there is nothing above it to divide from,
        # and the part heading already opens that block.
        if i:
            design.step_break()
        design.sect(stp["n"], stp["title"], _inline(lead),
                    kind="Step")
        # c-301, Bill: the call step loses its figure row
        # (Declared / Grades / Delete watchlist) and its
        # conviction waterfall. Both restated what the
        # prediction block below now says directly, and the
        # waterfall's base rate and haircuts still travel in the
        # registered call file.
        if stp["key"] != "call":
            _numbers(stp["numbers"])
            _step_visuals(stp["key"], s)
        # c-268: step 2 shows NOTHING open. Its two figures say
        # what the step is for, and Bill's instruction is that
        # the whole rulebook block sits behind the toggle
        # rather than leaking its first two paragraphs. Step 7
        # is the opposite case and shows everything (D8).
        # c-278: step 3 joins step 2 at shown=0 — every
        # paragraph goes behind "Rulebook References" and the
        # step is the figure plus its one-line lead. Bill:
        # *"Put these text inside rulebook references, and
        # delete the textbox."* The seven cards already carry
        # the derivation with the arithmetic on each one, so
        # the prose above them was a second telling.
        # keyed on `key`, not on the display number, for the
        # same reason the figures are — c-282 removed a step
        # and renumbered everything after it.
        design.beats([_md_money(r) for r in rest], key=stp["n"],
                     shown={"data": 0, "cutoff": 0,
                            # c-293, Bill: no Rulebook References
                            # on the shortlist step — None shows
                            # every paragraph, so no toggle is
                            # created to hide them behind.
                            "buffers": None,
                            # c-301: no Rulebook References on
                            # the call step either.
                            "call": None,
                            "limits": None}.get(stp["key"], 2))
        _step_source(stp["key"])
        # c-300, Bill: the size-line bar chart moves from the
        # shortlist step to the CALL step. The shortlist step now
        # ends on the dotted scan, which is the one figure that
        # answers "who is in range"; the bar chart is about which
        # names sit below the floor, which belongs next to the
        # call being made on them.
        if stp["key"] == "call":
            _results(s)

    # c-257: the "Take It With You" download block is off the
    # page at Bill's request. `walkthrough_export.to_html` is
    # untouched and still tested — the exporter is the thing
    # that keeps the numbers honest away from the app, and it
    # can be re-surfaced by restoring four lines. Only the
    # button is gone.
