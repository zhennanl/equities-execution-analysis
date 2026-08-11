"""Explanatory diagrams for the method pages (c-249).

**Bill:** *"still too text dense … especially when we don't
have graphs to make contents more visualizing. Let's try to
modify the content instead: for each step, try our best to fit
descriptions with some graphs."*

Right, and the two things a diagram must NOT become here:

1. **Decoration.** Each diagram has to carry a claim the prose
   would otherwise have to make, so that adding it lets text
   come OUT. Step 1 loses two paragraphs to the two below.
2. **A place for facts to hide.** Every date rendered here is
   passed in from `walkthrough_story`, which reads
   `data/msci_review_dates.json` — MSCI's own published
   dates, with the source URLs in the file. Nothing is typed
   into a drawing.

**Why hand-written SVG rather than plotly.** These are
relationship and time diagrams, not plots of data. Plotly
would need a hidden axis, invisible traces and pixel-nudged
annotations to draw a box with an arrow out of it, and the
result would still not survive the HTML export cleanly. An
inline `<svg>` is what the exporter already emits for the size
ladder, so it stays self-contained (see the export test).

Everything is drawn on a 0-880 viewBox with `width:100%`, so
the figures scale with the column instead of fixing a size.
"""
import calendar as _cal
import datetime as _dt

from views.design import (CARD, FAINT, GREEN, INK, MUTED,
                          NAVY, RED, RULE)

SANS = "Inter, -apple-system, 'Segoe UI', Roboto, sans-serif"
MONO = "'JetBrains Mono', ui-monospace, Menlo, monospace"

# ---- TYPE SCALE ---------------------------------------------
# c-250, Bill: *"make sure the text style, font size are
# consistent with the rest of the page design."*
#
# An SVG on a 880-unit viewBox rendered into a 1088px column is
# scaled UP by 1088/880, so a font-size chosen by eye in SVG
# units lands at some unrelated CSS size on the page. The first
# pass picked 13 / 11.5 / 10.5 because they looked right, which
# is exactly the drift the design system exists to prevent.
#
# So the sizes are DERIVED: take the rem value the design
# system already uses for that role, convert to CSS pixels, and
# divide by the scale factor. A diagram's body text now renders
# at the same size as a beat, and its eyebrow at the same size
# as a figure-row label.
#
# Faces follow the same rule as the rest of the site: serif is
# for headings only, and a diagram is data, so everything here
# is Inter — except a date, which is a figure and takes the
# tabular mono the status strip uses.
COL_PX = 1088                  # block-container 1120 less padding
VIEW_W = 880


def _px(rem):
    """The site's rem size, in viewBox units.

    c-405, Bill: the root moved from the browser's 16px to 20px
    at c-402, and the diagrams — whose whole point (c-250) is
    that their type matches the page's — were still deriving
    from 16. One constant, and every diagram's body text is
    again exactly the size of a beat."""
    return round(rem * 20 * VIEW_W / COL_PX, 1)


FS_TITLE = _px(1.0)            # a node's name
FS_BODY = _px(0.95)            # matches design's beat text
FS_SMALL = _px(0.82)           # matches .dsect .l
FS_CAP = _px(0.78)             # matches a caption
FS_EYEBROW = _px(0.66)         # matches .dstat .k


def _r(v):
    """One decimal place.

    c-254: coordinates were being formatted straight from
    floating-point arithmetic, so the SVG carried strings like
    "223.2096" and "89.30133333333333". That bloats the markup
    and — the reason it was caught — a run of digits inside one
    of them tripped the test that forbids a typed-in YEAR. A
    drawing needs a tenth of a pixel, not seventeen.
    """
    return round(float(v), 1)


def _end(parts):
    """Close an SVG, with the dollar signs neutralised.

    c-268, and this one was live on the site. Streamlit's
    markdown renderer treats `$ ... $` as inline LaTeX. The
    size ladder emits twelve dollar signs — six pairs — so the
    renderer took the SVG apart, rendered the spans between
    each pair as maths, and spilled the rest onto the page as
    raw markup. Step 3 was showing tag soup.

    The tell was in the wreckage: "US BN, FULL MARKET CAP" had
    lost its dollar sign, and so had every price. An odd count
    survives (two_measure_walk has one and rendered fine),
    which is why this looked like a step-3 problem rather than
    a dollar-sign problem.

    `&#36;` is invisible to the markdown pass and renders as a
    dollar sign in the browser, so every figure keeps its
    currency and nothing has to avoid writing money.
    """
    return "".join(parts).replace("$", "&#36;")


def _open(w, h):
    return (f'<svg viewBox="0 0 {w} {h}" '
            f'xmlns="http://www.w3.org/2000/svg" '
            f'style="width:100%;height:auto;display:block;'
            f'margin:.2rem 0 .9rem" '
            f'font-family="{SANS}">')


def _fitw(lines, fs, pad=56, ls=0.0, floor=180):
    """Width a box needs for its longest line.

    c-298, Bill: *"it's too wide, the text should sit in the
    middle."* Both box groups carried a width chosen before the
    copy was written — 330 units for text that needs about 250 —
    so every card trailed a band of white on the right.

    The 0.52 factor is an average advance width for this sans
    stack at these sizes, rounded UP rather than fitted: a box a
    few units too wide is invisible, a box one unit too narrow
    clips a letter. Derived from the lines themselves so the
    width follows the text if the wording changes, instead of
    being a constant that silently stops matching.
    """
    # pad is 40, not 28: text is inset 14 either side, so the
    # extra 12 is deliberate slack. The width model is an
    # ESTIMATE of a font the browser picks, and an exactly
    # fitting box clips the moment the fallback differs by a
    # hair. Twelve units of air costs nothing and is the
    # difference between "tight" and "broken".
    if not lines:
        return floor
    # c-302, Bill: the MSCI box overflowed. A FLAT factor per
    # character is the wrong model — it has to be tuned to the
    # widest line on the page and then makes every other box too
    # wide. Raising 0.52 to 0.62 fixed the overflow and swelled
    # the ladder cards from 290 to 341 for text that never
    # needed it.
    #
    # So width is summed PER CHARACTER against a four-bucket
    # model of this sans stack. "in index constituents on
    # announcement day" is mostly narrow letters; "GLOBAL
    # MINIMUM SIZE REFERENCE" is all caps. A flat average
    # cannot tell those apart and this can.
    return max(floor, int(max(_linew(x, fs, ls)
                              for x in lines)) + pad)


_W_NARROW = set("iljtfrIJ.,;:'\"!|()[]{}- ")
_W_WIDE = set("mwMW@%")


def _linew(text, fs, ls=0.0):
    """Advance width of one line, in units.

    Four buckets, deliberately coarse: narrow letters and
    punctuation, wide letters, upper case and digits, everything
    else lower case. Coarse beats a flat average by a wide
    margin and needs no font metrics to be shipped.
    """
    w = 0.0
    for ch in str(text):
        # c-309: every weight raised ~12%, and the pad with it.
        # The model has now UNDER-called twice on the same box,
        # which means it is biased low against whatever font the
        # browser actually resolves — this stack falls back
        # differently on Windows than the metrics I fitted to. A
        # box a little wider than it needs is invisible; one a
        # few units short spills its last word, and that is the
        # error the reader sees. Bias the estimate high on
        # purpose.
        if ch in _W_NARROW:
            w += 0.34
        elif ch in _W_WIDE:
            w += 0.98
        elif ch.isupper() or ch.isdigit():
            w += 0.70
        else:
            w += 0.58
    return w * fs + ls * len(str(text))


def _box(x, y, w, h, title, sub, body, accent=NAVY):
    """A node: hairline card, small caps eyebrow, one claim."""
    out = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" '
           f'rx="3" fill="{CARD}" stroke="{RULE}"/>',
           f'<rect x="{x}" y="{y}" width="3" height="{h}" '
           f'fill="{accent}"/>',
           f'<text x="{x + 16}" y="{y + 24}" font-size="{FS_TITLE}" '
           f'font-weight="700" fill="{INK}">{title}</text>',
           f'<text x="{x + 16}" y="{y + 41}" '
           f'font-size="{FS_EYEBROW}" letter-spacing="1.1" '
           f'fill="{FAINT}">{sub.upper()}</text>']
    for i, line in enumerate(body):
        out.append(f'<text x="{x + 16}" y="{y + 63 + i * 16}" '
                   f'font-size="{FS_BODY}" fill="{MUTED}">'
                   f'{line}</text>')
    return "".join(out)


def _arrow(x1, x2, y, label, colour=NAVY, back=False):
    """A labelled horizontal arrow between two boxes.

    c-266: `back` points it the other way. The relationship
    between an index provider and the funds tracking it is
    NOT one-directional — MSCI publishes, and the funds are
    contractually bound to follow. Drawing only the outbound
    arrow made it look like an announcement rather than an
    obligation, which is the whole reason the flow is
    predictable.
    """
    # c-268, Bill: *"The arrow for 'must follow' should point to
    # the left, not right."* It was — and so was PUBLISHES,
    # which pointed left as well. `d` had the wrong sign, so
    # the head's BASE was drawn beyond its apex on both arrows:
    # every arrowhead on this figure has been drawn back to
    # front, and the shaft overshot its tip by 7 units to hide
    # it. Reading order made it invisible on the forward arrow
    # (an apex touching the box it points at looks fine either
    # way) and obvious on the return one.
    #
    # `d` now points from the apex BACK along the shaft, which
    # is the direction the two base corners belong in.
    mid = (x1 + x2) / 2
    tip, tail = (x1, x2) if back else (x2, x1)
    d = 1 if back else -1
    return (
        f'<line x1="{tail}" y1="{y}" x2="{tip + 7 * d}" '
        f'y2="{y}" stroke="{colour}" stroke-width="1.5"/>'
        f'<path d="M{tip} {y} L{tip + 8 * d} {y - 4.5} '
        f'L{tip + 8 * d} {y + 4.5} Z" fill="{colour}"/>'
        f'<text x="{mid}" y="{y - 9}" font-size="{FS_EYEBROW}" '
        f'text-anchor="middle" letter-spacing=".6" '
        f'fill="{colour}" font-weight="600">'
        f'{label.upper()}</text>')


def _elbow(x1, y1, x2, axis, colour=NAVY):
    """A dropped connector: down, across, into a tick's head."""
    # the head stops ABOVE the shaded window, not on its edge —
    # first render landed both arrowheads exactly on the band's
    # top rule and they read as part of the box, not as arrows.
    mid = axis - 46
    return (f'<path d="M{x1} {y1} L{x1} {mid} L{x2} {mid}" '
            f'fill="none" stroke="{colour}" stroke-width="1.2" '
            f'stroke-dasharray="4 3"/>'
            f'<path d="M{x2} {axis - 32} L{x2 - 4.5} {mid} '
            f'L{x2 + 4.5} {mid} Z" fill="{colour}"/>')


def review_flow(announced, close, announced_time=None,
                market_close_label="closing auction"):
    """Who is forced to trade, and exactly when (c-251).

    **Bill:** *"Can we make MSCI point to the right to
    Index-replicating funds, then point to below Forced buying
    and selling, then point to index change date on the
    timeline."*

    That merges what were two figures, and it is the better
    structure: they were making one argument. The relationship
    said *who* has no choice, the timeline said *when* — drawn
    apart, the reader has to carry the first into the second.
    Drawn as one, MSCI's box lands on the announcement tick and
    the forced-flow box lands on the rebalance close, so the
    chain from "a list changed" to "this auction" is a single
    unbroken path.

    ON THE NAMES, which Bill asked me to verify. There is no
    defined term "Index Announcement Date" or "Index Effective
    Date" in the GIMI methodology. The rulebook capitalises its
    three data cutoffs — Price, Liquidity, Equity Universe —
    precisely because those ARE defined terms, and refers to
    these two in lower case ("announcement date", "the
    effective date of the Index Review"). MSCI's press releases
    label the fields **Announcement date** and **Effective
    date**, so those are the names used here, without an
    "Index" prefix MSCI does not use.
    """
    W, H = 880, 528
    # c-268, Bill: *"make the gap between Announcement date and
    # Effective date wider on the timeline, so we can fit more
    # content."* The ticks sit on the boxes' centres (c-265),
    # so the gap is a property of the LAYOUT, not of the axis —
    # widening it means moving the right-hand column right and
    # letting the boxes grow into the space that was being
    # wasted at the canvas edge. 240 units of separation
    # becomes 470.
    # c-268, Bill: *"Let's reorganize the space on the timeline
    # to make this more symmetric. Put announcement date, blue
    # box on the left side, effective date, green and red box on
    # the right side. Leave enough room in between to put
    # text."*
    #
    # The previous pass widened the gap but left 150 units of
    # dead canvas past the right-hand column, so the figure was
    # wide on the left and short on the right. Both columns are
    # now flush to their own edge and the same width, which puts
    # the ticks at 140 and 740 — mirror positions — and leaves
    # the middle 300 units clear for the band that says what
    # happens between the two dates.
    # c-296: wB 280 -> 330 so the MSCI box holds its sentence in
    # THREE lines. At 280 the same text wrapped to four and the
    # box grew a ragged last line carrying two words.
    _bodies = [
        ["Decides which companies get added or",
         "deleted from the index. Publishes index",
         "changes on announcement day."],
        ["Obliged to track the index, so they",
         "align their holdings with the new",
         "constituents and weights."],
        ["Funds are benchmarked against the",
         "close price on the effective date."]]
    bh, top = 112, 16
    # c-405: fitted at FS_BODY — the size `_box` actually draws
    # bodies at. Fitting at FS_CAP was a latent mismatch the
    # 20px root exposed as a right-edge overflow.
    wB = _fitw([ln for b in _bodies for ln in b], FS_BODY)
    # xF DERIVED, not fixed: the right column ends where the
    # canvas does. The ticks already track box centres
    # (tA, tC = wB/2, xF + wB/2), so both follow automatically.
    xF, axis = W - wB, 356
    # c-265, Bill: each box should sit directly ABOVE the tick
    # it feeds. So the ticks are placed on the boxes' centres
    # rather than the boxes being wired sideways to arbitrary
    # ticks: MSCI's centre is wB/2 = 120, and the funds and
    # forced-flow boxes share a centre at xF + wB/2 = 450.
    #
    # Both connectors become straight vertical drops, and the
    # green and red boxes form one unbroken spine down to the
    # rebalance close. An elbow made the reader trace a path;
    # a straight line is read without being traced.
    # c-267: the separate "Effective Date — 1 Sep" tick is
    # gone at Bill's request. Showing MSCI's calendar label a
    # day after the close it describes read as two events. One
    # tick now carries both: named Effective Date, valued at
    # the CLOSE of 31 August, which is when the trade prints.
    tA, tC = wB / 2, xF + wB / 2
    s = [_open(W, H)]

    s.append(_box(
        0, top, wB, bh, "MSCI", "index provider",
        _bodies[0]))
    # the pair reads as a contract, not an announcement. Both
    # tips stop 4px short of the box: an arrowhead landing on
    # the accent bar is hidden by it.
    # c-268: identical span for both, and the return arrow is
    # GREEN. The first version staggered them by 4px so their
    # heads would not sit on an accent bar, which made two
    # arrows of the same length look like two different
    # lengths; insetting both by 2 does the same job
    # symmetrically. The colour is not decoration — green is
    # the funds' colour everywhere else on this figure, so the
    # obligation now reads as coming FROM them.
    s.append(_arrow(wB + 2, xF - 2, top + 46, "publishes"))
    s.append(_arrow(wB + 2, xF - 2, top + 82, "must follow",
                    colour=GREEN, back=True))
    s.append(_box(
        xF, top, wB, bh, "Index-replicating funds",
        "ETFs and index mandates",
        _bodies[1], accent=GREEN))
    # funds -> the forced flow, straight down
    cx, gap = xF + wB / 2, 40
    s.append(f'<line x1="{cx}" y1="{top + bh}" x2="{cx}" '
             f'y2="{top + bh + gap - 8}" stroke="{GREEN}" '
             f'stroke-width="1.5"/>')
    s.append(f'<path d="M{cx} {top + bh + gap} L{cx - 4.5} '
             f'{top + bh + gap - 8} L{cx + 4.5} '
             f'{top + bh + gap - 8} Z" fill="{GREEN}"/>')
    s.append(f'<text x="{cx + 12}" y="{top + bh + 26}" '
             f'font-size="{FS_EYEBROW}" letter-spacing=".6" '
             f'font-weight="600" fill="{GREEN}">MUST '
             f'TRADE</text>')
    # c-266 renamed "Forced buying and selling" to "Replication"
    # (the duty). c-366, Bill: "Rebalance" — the EVENT. It is the
    # word the rest of the site already uses (the daily-data page,
    # the case study's "rebalance window"), so the timeline stops
    # introducing a third term for the same day.
    s.append(_box(
        xF, top + bh + gap, wB, bh, "Rebalance",
        "on the effective date",
        _bodies[2],
        accent=RED))

    # the two connectors down onto the timeline
    s.append(_elbow(wB / 2, top + bh, tA, axis, NAVY))
    s.append(_elbow(cx, top + bh * 2 + gap, tC, axis, RED))

    s.append(f'<rect x="{tA}" y="{axis - 26}" '
             f'width="{tC - tA}" height="26" fill="#f5efe6"/>')
    s.append(f'<text x="{(tA + tC) / 2}" y="{axis - 9}" '
             f'font-size="{FS_CAP}" text-anchor="middle" '
             f'fill="{MUTED}">Review changes are known · The '
             f'market prepares to rebalance</text>')
    s.append(f'<line x1="24" y1="{axis}" x2="856" y2="{axis}" '
             f'stroke="{RULE}" stroke-width="1.5"/>')
    # c-268: centred, not left aligned. With the columns
    # mirrored, a centred block under each tick is the only
    # arrangement that reads as one symmetric figure — start
    # aligning the left block and end aligning the right one
    # would pull both toward the middle they are meant to leave
    # empty.
    s.append(_mark(axis, tA, NAVY, 1.5, "Announcement Date",
                   announced, announced_time or []))
    # no note under this tick: the full-width block below says
    # where the print lands, and a centred line here ran into
    # the announcement note on the left.
    # c-268, Bill: *"Remove 'index funds' job…'. Put 'MSCI…'
    # and 'Index Funds' below the effective date, like the same
    # horizontal positioning for Aug 12's note."*
    #
    # So they become the tick's OWN note, left aligned at the
    # tick exactly as the announcement note is — which is what
    # c-267 could not do when the tick sat at x=450 with only
    # 430 units of canvas to its right. Widening the gap bought
    # the room; the full-width block at the bottom of the
    # figure, and the "index funds' job" line above it, are
    # gone.
    s.append(_mark(axis, tC, RED, 3, "Effective Date",
                   f"Close of {close}",
                   ["MSCI: all changes are made",
                    f"as of the close of {close}.",
                    "",
                    "Index funds: rebalance at this close to",
                    "the new index composition to minimise",
                    "tracking error, so the fund matches the",
                    "index on the next day."]))
    s.append("</svg>")
    return _end(s)


def _mark(y, x, colour, width, top, date, note, anchor="middle",
          above=False, fs_note=None):
    """One dated tick on a timeline, labelled below or above.

    c-409, Bill: `fs_note` lets a caller step ONLY the note
    lines down a size. cutoff_timeline's five ticks sit close
    enough that at the c-405 face their second note row
    overlapped; the titles and dates still fit and keep
    FS_SMALL."""
    fs_note = fs_note or FS_CAP
    # ABOVE STILL READS DOWNWARDS. First render simply negated
    # the offsets, which stacked the label in reverse — notes,
    # then date, then title — so the eye met the detail before
    # the name. Flipping a label's SIDE must not flip its
    # reading order; only the block moves.
    o = [f'<line x1="{x}" y1="{y - 34}" x2="{x}" '
         f'y2="{y + 12}" stroke="{colour}" '
         f'stroke-width="{width}"/>']
    base = (y - 46 - 17 - 15 * len(note)) if above else y + 32
    o.append(f'<text x="{x}" y="{base}" font-size="{FS_SMALL}" '
             f'font-weight="700" text-anchor="{anchor}" '
             f'fill="{INK}">{top}</text>')
    o.append(f'<text x="{x}" y="{base + 17}" '
             f'font-size="{FS_SMALL}" text-anchor="{anchor}" '
             f'font-family="{MONO}" fill="{colour}">{date}</text>')
    for i, line in enumerate(note):
        o.append(f'<text x="{x}" y="{base + 36 + i * 15}" '
                 f'font-size="{fs_note}" text-anchor="{anchor}" '
                 f'fill="{MUTED}">{_lead_bold(line)}</text>')
    return "".join(o)


def _lead_bold(line):
    """Bold a leading `Label:` on a note line.

    c-268, Bill: *"Bold the word 'Note:'"* — and the same
    applies to "MSCI:" and "Index funds:" on the other tick, so
    it is a rule rather than three edits. Done here rather than
    in the data, because `data/msci_review_dates.json` holds
    MSCI's published dates and has no business holding SVG
    markup.

    Deliberately narrow: an initial capital, at most fifteen
    letters and spaces, then a colon. "Central European Summer
    Time — 05:00" does not match (the em dash breaks it before
    the colon), and a line starting lower case never does.
    """
    import re
    return re.sub(r"^([A-Z][A-Za-z ]{0,14}:)",
                  r'<tspan font-weight="700">\1</tspan>', line)


def _lastbd(y, m):
    d = _dt.date(y, m, _cal.monthrange(y, m)[1])
    while d.weekday() > 4:
        d -= _dt.timedelta(days=1)
    return d


def _minus_bd(d, n):
    while n:
        d -= _dt.timedelta(days=1)
        if d.weekday() < 5:
            n -= 1
    return d


def _day(iso):
    y, m, d = str(iso)[:10].split("-")
    return _dt.date(int(y), int(m), int(d))


def _hum(d):
    # the year stays on: every other date on this page is
    # written in full, and the surveillance window crosses a
    # review boundary, so "30 Apr" alone invites the reader to
    # assume it belongs to some other year than it does.
    return f"{d.day} {_MON[d.month - 1]} {d.year}"


_MON = ("Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec").split()


def coverage_crossing(c):
    """Taiwan's actual crossing, on real ranked data (c-278).

    Replaces the schematic that used to sit in step 4. Same
    three jobs — sort key, running total, answer — but with the
    market's own names, so the reader looks at the thing rather
    than an illustration of it.

    Each bar is one company's FULL market cap with its
    free-float part filled darker. The step line is the
    cumulative free-float total. Where that line reaches the
    target, the crossing rank is marked and an arrow points
    back down at the company whose FULL cap becomes the cutoff
    — which is the whole trick of the rule, and the reason two
    measures have to share one chart.

    The window is the ranks either side of the crossing rather
    than the top of the list. TSMC is eleven times the size of
    rank 2, so a chart starting at rank 1 is one bar, a row of
    slivers, and a crossing too far right to see.
    """
    rows = c.get("rows") or []
    if len(rows) < 6:
        return ""
    W, H = 880, 400
    x0, base, top = 46, 268, 46
    aw = W - x0 - 30
    gap = aw / len(rows)
    bw = gap * 0.62
    hi_cap = max(r["cap"] for r in rows) * 1.06
    cums = [r["cum"] for r in rows]
    c_lo, span = min(cums), (max(cums) - min(cums)) or 1
    tgt = c["target_busd"]
    priced = c.get("priced") or "at the cutoff date"

    def BY(v):
        return _r(base - (base - top) * 0.78 * v / hi_cap)

    def CY(v):
        return _r(base - 14 - (base - top - 20)
                  * (v - c_lo) / span)

    s = [_open(W, H)]
    s.append(f'<line x1="{x0 - 8}" y1="{base}" x2="{W - 22}" '
             f'y2="{base}" stroke="{RULE}" stroke-width="1"/>')

    for i, r in enumerate(rows):
        x = _r(x0 + i * gap)
        cross = r["rank"] == c["crossing_rank"]
        col = RED if cross else NAVY
        s.append(f'<rect x="{x}" y="{BY(r["cap"])}" '
                 f'width="{_r(bw)}" '
                 f'height="{_r(base - BY(r["cap"]))}" '
                 f'fill="{col}" opacity=".18"/>')
        s.append(f'<rect x="{x}" y="{BY(r["fcap"])}" '
                 f'width="{_r(bw)}" '
                 f'height="{_r(base - BY(r["fcap"]))}" '
                 f'fill="{col}" opacity=".85"/>')
        s.append(f'<text x="{_r(x + bw / 2)}" y="{base + 13}" '
                 f'font-size="{FS_EYEBROW}" text-anchor="middle" '
                 f'fill="{RED if cross else FAINT}">'
                 f'{r["rank"]}</text>')
        s.append(f'<text x="{_r(x + bw / 2)}" y="{base + 25}" '
                 f'font-size="{FS_EYEBROW}" text-anchor="middle" '
                 f'fill="{INK if cross else FAINT}">'
                 f'{r["code"]}</text>')

    pts = " ".join(f"{_r(x0 + i * gap + bw / 2)},{CY(r['cum'])}"
                   for i, r in enumerate(rows))
    s.append(f'<polyline points="{pts}" fill="none" '
             f'stroke="{GREEN}" stroke-width="2"/>')
    for i, r in enumerate(rows):
        s.append(f'<circle cx="{_r(x0 + i * gap + bw / 2)}" '
                 f'cy="{CY(r["cum"])}" r="2.6" fill="{GREEN}"/>')

    ty = CY(tgt)
    s.append(f'<line x1="{x0 - 8}" y1="{ty}" x2="{W - 22}" '
             f'y2="{ty}" stroke="{GREEN}" stroke-width="1.2" '
             f'stroke-dasharray="4 3"/>')
    s.append(f'<text x="{W - 24}" y="{_r(ty - 6)}" '
             f'font-size="{FS_CAP}" text-anchor="end" '
             f'fill="{GREEN}">85% of the investable market, '
             f'&#36;{tgt:,.0f}B</text>')

    ci = next((i for i, r in enumerate(rows)
               if r["rank"] == c["crossing_rank"]), None)
    if ci is not None:
        x = _r(x0 + ci * gap + bw / 2)
        cy = BY(rows[ci]["cap"])
        s.append(f'<line x1="{x}" y1="{CY(rows[ci]["cum"])}" '
                 f'x2="{x}" y2="{_r(cy - 12)}" stroke="{RED}" '
                 f'stroke-width="1.2" stroke-dasharray="3 3"/>')
        s.append(f'<path d="M{x} {_r(cy - 4)} '
                 f'L{_r(x - 4.5)} {_r(cy - 13)} '
                 f'L{_r(x + 4.5)} {_r(cy - 13)} Z" '
                 f'fill="{RED}"/>')
        s.append(f'<text x="{x}" y="{_r(cy - 20)}" '
                 f'font-size="{FS_TITLE}" font-weight="700" '
                 f'text-anchor="middle" fill="{RED}">'
                 f'&#36;{c["crossing_cap_busd"]}B</text>')
        s.append(f'<text x="{x}" y="{_r(cy - 34)}" '
                 f'font-size="{FS_EYEBROW}" letter-spacing="1.1" '
                 f'text-anchor="middle" fill="{RED}">'
                 f'MARKET SIZE-SEGMENT CUTOFF</text>')

    s.append(f'<text x="{x0 - 8}" y="{top - 20}" '
             f'font-size="{FS_CAP}" fill="{MUTED}">'
             f'Bars: full market cap, free-float part filled. '
             f'Line: cumulative free float.</text>')
    s.append(f'<text x="{x0 - 8}" y="{base + 44}" '
             f'font-size="{FS_CAP}" fill="{FAINT}">'
             f'Rank and code, from {c["screened"]} screened '
             f'companies priced {priced}. The running total '
             f'crosses at rank {c["crossing_rank"]}; that '
             f'company&#8217;s FULL cap sets the cutoff.</text>')
    s.append("</svg>")
    return _end(s)


def two_measure_walk(target_pct=85, crossing_rank=None,
                     crossing_cap=None):
    """One row, two measures, three jobs (c-254).

    Bill: *"can you think of any visualization to make the
    calculation more intuitive?"*

    The thing that needs making intuitive is that the walk uses
    TWO different measures of the same company and reads back a
    THIRD number:

        sort key      full market capitalisation
        running total free-float-adjusted capitalisation
        answer        the FULL cap of the company where the
                      running total crosses the target

    Prose has to say that three times. One picture says it once:
    each company is a full-cap bar with the float-adjusted part
    filled in, the bars are already in sort order, and a step
    line accumulates only the FILLED parts. Where the line hits
    the target, an arrow points back down at the whole bar.

    **SCHEMATIC, and labelled as such.** The rulebook makes the
    same choice — §2.2.3 p.17 explains this walk with an
    invented table of companies A, B, C rather than with real
    constituents, because the mechanism is the point and real
    data would need 150 rows to reach the crossing. Taiwan's
    actual crossing is passed in and printed as text, so no
    real figure is implied by a schematic bar.
    """
    # deliberately unlabelled companies; the shape is the point
    full = [30, 26, 23, 19, 17, 14, 12, 10, 9, 8, 7, 6]
    fif = [.95, .35, .80, .55, .90, .30, .75, .85, .40, .70,
           .60, .80]
    # A PARETO, after a first attempt that gave the cumulative
    # curve its own 50px strip under the bars: squashed into a
    # twentieth of the height it read as a flat line along the
    # floor, which is the opposite of the point. Bars and
    # cumulative share one vertical scale here, which is the
    # shape every reader already knows.
    W, H = 880, 372
    x0, bw, gap = 40, 46, 22
    base, top = 250, 42
    s = [_open(W, H)]
    scale = (base - top) * 0.92 / max(full)
    ffcap = [f * p for f, p in zip(full, fif)]
    tot = sum(ffcap)
    run, cross = 0.0, None
    cum = []
    for i, v in enumerate(ffcap):
        run += v
        cum.append(run / tot * 100)
        if cross is None and run / tot * 100 >= target_pct:
            cross = i

    # c-268, Bill: *"Please label each bar on the graph.
    # Currently it's impossible to identify which company the
    # bar represents."*
    #
    # Correct, and the honest label is a LETTER, not a name.
    # These twelve bars are invented — the real crossing is at
    # rank 115, so a truthful chart of Taiwan would be 150 bars
    # wide and unreadable. §2.2.3 p.17 has the same problem and
    # solves it the same way: the rulebook's own worked example
    # is a table of companies A, B and C. Putting real tickers
    # on schematic heights would make up data; letters make the
    # bars referable ("the crossing is company G") without
    # claiming anything about a real company. The rank sits
    # under the letter because rank is what the sort produces
    # and what the crossing is quoted in.
    for i, (f, ff) in enumerate(zip(full, ffcap)):
        x = x0 + i * (bw + gap)
        s.append(f'<rect x="{x}" y="{_r(base - f * scale)}" '
                 f'width="{bw}" height="{_r(f * scale)}" '
                 f'fill="{RULE}" opacity=".85"/>')
        s.append(f'<rect x="{x}" y="{_r(base - ff * scale)}" '
                 f'width="{bw}" height="{_r(ff * scale)}" '
                 f'fill="{NAVY}" opacity=".75"/>')
        hit = cross is not None and i == cross
        s.append(f'<text x="{_r(x + bw / 2)}" y="{base + 26}" '
                 f'font-size="{FS_BODY}" text-anchor="middle" '
                 f'font-weight="700" '
                 f'fill="{RED if hit else INK}">'
                 f'{chr(65 + i)}</text>')
        s.append(f'<text x="{_r(x + bw / 2)}" y="{base + 39}" '
                 f'font-size="{FS_EYEBROW}" text-anchor="middle" '
                 f'fill="{RED if hit else FAINT}">'
                 f'#{i + 1}</text>')
    s.append(f'<line x1="{x0 - 12}" y1="{base}" '
             f'x2="{x0 + 12 * (bw + gap)}" y2="{base}" '
             f'stroke="{RULE}" stroke-width="1.5"/>')

    # the cumulative float-coverage line, on the same panel
    def CY(pct):
        return _r(base - pct / 100 * (base - top))

    pts = " ".join(
        f"{_r(x0 + i * (bw + gap) + bw / 2)},{CY(c)}"
        for i, c in enumerate(cum))
    s.append(f'<polyline points="{pts}" fill="none" '
             f'stroke="{GREEN}" stroke-width="2"/>')
    for i, c in enumerate(cum):
        s.append(f'<circle cx="{x0 + i * (bw + gap) + bw / 2}" '
                 f'cy="{CY(c)}" r="2.6" fill="{GREEN}"/>')
    # the label sits ABOVE the rule and right-aligned to the
    # canvas: hung off the end of the line it ran past the
    # right edge and was clipped.
    s.append(f'<line x1="{x0 - 12}" y1="{CY(target_pct)}" '
             f'x2="700" y2="{CY(target_pct)}" stroke="{GREEN}" '
             f'stroke-width="1" stroke-dasharray="4 3"/>')
    s.append(f'<text x="876" y="{CY(target_pct) - 6}" '
             f'font-size="{FS_CAP}" text-anchor="end" '
             f'fill="{GREEN}" font-weight="700">{target_pct}% '
             f'cumulative float coverage</text>')

    if cross is not None:
        cx = x0 + cross * (bw + gap) + bw / 2
        s.append(f'<line x1="{cx}" y1="{CY(cum[cross])}" '
                 f'x2="{cx}" y2="{base + 6}" stroke="{RED}" '
                 f'stroke-width="1.2" stroke-dasharray="3 3"/>')
        s.append(f'<path d="M{cx} {base + 2} L{cx - 4.5} '
                 f'{base + 11} L{cx + 4.5} {base + 11} Z" '
                 f'fill="{RED}"/>')
        s.append(f'<rect x="{x0 + cross * (bw + gap) - 3}" '
                 f'y="{_r(base - full[cross] * scale - 3)}" '
                 f'width="{bw + 6}" '
                 f'height="{_r(full[cross] * scale + 6)}" '
                 f'fill="none" stroke="{RED}" '
                 f'stroke-width="1.5"/>')
        s.append(f'<text x="{x0}" y="{top - 20}" '
                 f'font-size="{FS_CAP}" font-weight="700" '
                 f'fill="{RED}">Where the green line crosses '
                 f'{target_pct}%, the answer is the boxed bar’s '
                 f'FULL height — not its filled part, and not '
                 f'the running total.</text>')

    # legend
    s.append(f'<rect x="{x0}" y="{base + 56}" width="11" '
             f'height="11" fill="{RULE}"/>')
    s.append(f'<text x="{x0 + 17}" y="{base + 65}" '
             f'font-size="{FS_CAP}" fill="{MUTED}">full market '
             f'cap — the SORT key</text>')
    s.append(f'<rect x="{x0 + 196}" y="{base + 56}" width="11" '
             f'height="11" fill="{NAVY}" opacity=".75"/>')
    s.append(f'<text x="{x0 + 213}" y="{base + 65}" '
             f'font-size="{FS_CAP}" fill="{MUTED}">free '
             f'float-adjusted cap — the RUNNING TOTAL</text>')
    # c-276: the clause number is gone from the caption for the
    # same reason it left the size-ladder cards — the step's
    # "Rulebook References" block already carries it with the
    # page and the quoted text, so printing it here as well put
    # the same citation on screen twice in its least useful
    # form. The caption keeps the thing a reader needs, which is
    # that the figure is a schematic.
    s.append(f'<text x="{x0}" y="{base + 87}" '
             f'font-size="{FS_CAP}" fill="{FAINT}">Schematic, '
             f'in the shape of the rulebook’s own worked '
             f'example — real data needs 150 rows to reach the '
             f'crossing.</text>')
    if crossing_rank and crossing_cap:
        s.append(f'<text x="{x0}" y="{base + 102}" '
                 f'font-size="{FS_CAP}" fill="{FAINT}">Taiwan '
                 f'this review: the crossing falls at rank '
                 f'{crossing_rank}, whose full cap is '
                 f'${crossing_cap}B.</text>')
    s.append("</svg>")
    return _end(s)


def conviction_waterfall(base_label, base, steps, final):
    """How one conviction number is built (c-257).

    Bill: *"Maybe show how we assign conviction probability… I
    don't even know how we calculate this either."*

    Fair, because the model is nowhere on the page. It is a
    base rate for the name's ZONE, multiplied by one haircut
    per declared weakness. Multiplication is the whole model,
    which makes a waterfall the honest picture: a starting
    height, one labelled deduction per known problem, and
    whatever is left.

    Drawing it also makes the model's weak point visible in a
    way prose does not — the deductions are large and there are
    several of them, so most of the distance from the base rate
    to the final number is uncertainty about OUR data, not
    about MSCI.
    """
    W = 880
    rows = [(base_label, base, None)]
    run = base
    for lab, mult in steps:
        run *= mult
        rows.append((lab, run, mult))
    # the answer gets its OWN row. Emphasising the last haircut
    # instead made the final number look like a property of
    # that one deduction rather than of the whole chain.
    rows.append(("the call", final, None))
    H = 92 + len(rows) * 34
    x0, x1 = 300, 700
    s = [_open(W, H)]

    def X(p):
        return _r(x0 + p * (x1 - x0))

    s.append(f'<text x="{x0}" y="30" font-size="{FS_EYEBROW}" '
             f'letter-spacing="1.1" fill="{FAINT}">'
             f'PROBABILITY THIS NAME MOVES AT THIS REVIEW</text>')
    for i, (lab, val, mult) in enumerate(rows):
        y = 52 + i * 34
        first, last = i == 0, i == len(rows) - 1
        colour = NAVY if first else (RED if last else MUTED)
        s.append(f'<rect x="{x0}" y="{y}" width="{X(val) - x0}" '
                 f'height="20" fill="{colour}" '
                 f'fill-opacity="{0.75 if last or first else 0.3}"/>')
        s.append(f'<text x="{x0 - 12}" y="{y + 14}" '
                 f'font-size="{FS_CAP}" text-anchor="end" '
                 f'fill="{INK if first or last else MUTED}" '
                 f'font-weight="{700 if first or last else 400}">'
                 f'{lab}</text>')
        s.append(f'<text x="{X(val) + 8}" y="{y + 14}" '
                 f'font-size="{FS_CAP}" fill="{colour}" '
                 f'font-weight="700">{val * 100:.0f}%</text>')
        if mult is not None:
            s.append(f'<text x="{X(val) + 46}" y="{y + 14}" '
                     f'font-size="{FS_CAP}" fill="{FAINT}">'
                     f'x {mult}</text>')
    s.append(f'<text x="0" y="{H - 28}" font-size="{FS_CAP}" '
             f'fill="{FAINT}">Every step is a multiplication. '
             f'The base rate and the haircuts are REGISTERED '
             f'JUDGEMENTS, declared before the review — not '
             f'frequencies fitted to history.</text>')
    s.append(f'<text x="0" y="{H - 12}" font-size="{FS_CAP}" '
             f'fill="{FAINT}">They are also uncalibrated: '
             f'nobody has checked whether names called at '
             f'{final * 100:.0f}% happen that often.</text>')
    s.append("</svg>")
    return _end(s)


def shortlist_scan(adds, deletes, lower, cutoff, upper):
    """Every candidate against the two buffers (c-255).

    THE PAGE NO LONGER USES THIS — see `walkthrough._scan_chart`.
    c-318 moved step 4 to plotly because the tooltip below is an
    SVG `<title>`: a browser-native hover on a 6-unit-radius
    circle inside an 880-unit viewBox that the page scales to
    roughly 700px. That is a ~5px target with a one-second delay
    and no styling, and Bill asked for the hover twice before it
    was accepted that it did not work.

    It is KEPT rather than deleted because it is the only
    renderer that can put this figure in the self-contained HTML
    export, which has no JavaScript. If step 4 is ever wanted
    there, this is what draws it — but do not wire it back into
    the page.

    Step 3 derived the lines; this is where they are applied,
    so the figure's job is different: not "where do the
    thresholds come from" but "who is on which side, and by how
    much".

    Two rows, because the two sides are not symmetric and the
    picture should say so before the prose does. Incumbents are
    tested against ONE line. Non-members must clear the upper
    buffer AND three further gates, so a hollow marker — clears
    the bar on size, fails something else — is a state that
    only exists on the top row.

    LOG SCALE on the x axis. The candidates run from about $5B
    to $34B, and on a linear axis the entire deletion cluster
    collapses into a strip narrower than its own dots while one
    outlier owns half the width. Market cap is the canonical
    case for a log axis, and the caption says it is one.
    """
    import math
    # the row labels live in the left margin, so the margin
    # has to be wide enough for them — at x0=60 they were
    # clipped to "members" and "umbents".
    W, H = 880, 286
    x0, x1 = 196, 820
    lo_v = min([lower * 0.85]
               + [r["cap_usd_b"] for r in (adds + deletes)])
    hi_v = max([upper * 1.1]
               + [r["cap_usd_b"] for r in (adds + deletes)])
    la, lb = math.log10(lo_v), math.log10(hi_v)

    def X(v):
        return _r(x0 + (math.log10(v) - la) / (lb - la)
                  * (x1 - x0))

    s = [_open(W, H)]
    yA, yD = 104, 186              # additions row, deletions row
    # zones
    s.append(f'<rect x="{x0}" y="58" width="{X(lower) - x0}" '
             f'height="172" fill="{RED}" fill-opacity=".06"/>')
    s.append(f'<rect x="{X(upper)}" y="58" '
             f'width="{x1 - X(upper)}" height="172" '
             f'fill="{GREEN}" fill-opacity=".07"/>')
    for v, colour, lab, sub in (
            (lower, RED, "lower buffer", "below: at risk"),
            (cutoff, MUTED, "cutoff", ""),
            (upper, GREEN, "upper buffer", "above: in range")):
        s.append(f'<line x1="{X(v)}" y1="52" x2="{X(v)}" '
                 f'y2="236" stroke="{colour}" '
                 f'stroke-width="{2 if v != cutoff else 1}"'
                 + ('' if v != cutoff
                    else ' stroke-dasharray="4 3"') + '/>')
        s.append(f'<text x="{X(v)}" y="38" '
                 f'font-size="{FS_CAP}" text-anchor="middle" '
                 f'font-weight="700" fill="{colour}">'
                 f'${v}B</text>')
        s.append(f'<text x="{X(v)}" y="24" '
                 f'font-size="{FS_CAP}" text-anchor="middle" '
                 f'fill="{MUTED}">{lab}</text>')
        if sub:
            s.append(f'<text x="{X(v)}" y="252" '
                     f'font-size="{FS_CAP}" '
                     f'text-anchor="middle" fill="{FAINT}">'
                     f'{sub}</text>')

    def row(y, rows, label, note, ok_test, hit):
        out = [f'<line x1="{x0}" y1="{y}" x2="{x1}" y2="{y}" '
               f'stroke="{RULE}" stroke-width="1"/>',
               f'<text x="{x0 - 10}" y="{y - 4}" '
               f'font-size="{FS_CAP}" text-anchor="end" '
               f'font-weight="700" fill="{INK}">{label}</text>',
               f'<text x="{x0 - 10}" y="{y + 10}" '
               f'font-size="{FS_CAP}" text-anchor="end" '
               f'fill="{FAINT}">{note}</text>']
        for r in rows:
            ok = ok_test(r)
            # the "hit" colour differs by row: a qualifying
            # non-member is an addition (green), a below-buffer
            # incumbent is a deletion (red). One colour for
            # both would have said they were the same event.
            c = hit if ok else MUTED
            # c-300, Bill: hover names the dot. A <title> child
            # is the SVG-native tooltip — no JavaScript, works in
            # the Streamlit iframe, and survives the standalone
            # HTML export, which a Plotly rewrite would not.
            # `$` is escaped to `&#36;` by _end for the whole
            # figure, so it is written plainly here.
            # every field read with .get: these rows come from
            # the registered call file and a name or a verdict
            # can legitimately be absent. A tooltip must never be
            # the thing that stops a figure rendering.
            code = str(r.get("code") or "")
            nm = str(r.get("name") or "").strip()
            lab = f"{nm} ({code})" if nm and nm != code else code
            tip = [lab or "—",
                   f'full market cap ${r["cap_usd_b"]:,.2f}B']
            if r.get("verdict"):
                tip.append(str(r["verdict"]))
            out.append(
                f'<circle cx="{X(r["cap_usd_b"])}" cy="{y}" '
                f'r="6" fill="{c if ok else "none"}" '
                f'fill-opacity=".75" stroke="{c}" '
                f'stroke-width="1.6">'
                f'<title>{chr(10).join(tip)}</title></circle>')
        return "".join(out)

    s.append(row(yA, adds, "non-members",
                 f"{sum(1 for r in adds if r['verdict'].startswith('QUALIFIES'))}"
                 f" of {len(adds)} clear all gates",
                 lambda r: r["verdict"].startswith("QUALIFIES"),
                 GREEN))
    s.append(row(yD, deletes, "incumbents",
                 f"{sum(1 for r in deletes if r['verdict'].startswith('BELOW'))}"
                 f" of {len(deletes)} below it",
                 lambda r: r["verdict"].startswith("BELOW"),
                 RED))
    s.append(f'<text x="{x0}" y="{H - 6}" font-size="{FS_CAP}" '
             f'fill="{FAINT}">Full market cap, US$bn, LOG scale. '
             f'Filled = '
             f'passes every gate; hollow = fails at least '
             f'one.</text>')
    s.append("</svg>")
    return _end(s)


def _ordinal(n):
    """69 -> 69th.

    c-283: the card printed "{n}th", which would have written
    61st as "61th" — and with `cross_rank` unset it printed a
    literal em dash where a number belonged, which is how the
    card shipped reading "the —th company".
    """
    if not n:
        return "—"
    n = int(n)
    suf = ("th" if 11 <= n % 100 <= 13
           else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th"))
    return f"{n}{suf}"


def size_ladder_steps(dm_ref, em_ref, lo, hi, cutoff, lower,
                      upper, min_float=None, pub_dm=None,
                      pub_asof=None, pub_idx=None,
                      cross_rank=None, coverage=0.85,
                      screened=None, idx_asof=None):
    """[(n, name, value, calculation)] — one row per card.

    c-287, Bill: a Calculation dropdown for EACH substep rather
    than one table for all seven. Same source values as the
    figure, so a card and its working cannot disagree; the only
    change is that the arithmetic is split to sit under the box
    it explains.
    """
    # NOT `&#36;`. These strings are markdown rendered inside an
    # expander, where an HTML entity prints as its own source
    # text. The view escapes the ones outside code spans — see
    # walkthrough._md_money.
    d = "$"
    rows = []
    if pub_dm:
        up = round((dm_ref / pub_dm - 1) * 100, 1)
        c1 = (f"Rank the 23 developed markets by size, add up "
              f"free-float value, and stop at 85% of the total. "
              f"The company you stop on sets the global bar.\n\n"
              f"MSCI publishes that figure at {d}{pub_dm}B priced "
              f"{pub_asof or 'at its own cutoff'}, so it is "
              f"scaled to this review with the MSCI ACWI IMI "
              f"past 3-month return ({up}%):\n\n"
              f"`{d}{pub_dm}B x (1 + {up}%) = {d}{dm_ref}B`")
    else:
        c1 = ("85% of the free-float value of the 23 developed "
              "markets, ranked by size.")
    rows.append((1, "Developed Markets Global Minimum "
                 "Size Reference", f"{d}{dm_ref}B", c1))
    rows.append((2, "Emerging Markets Global Minimum "
                 "Size Reference", f"{d}{em_ref}B",
                 f"Half the developed reference:\n\n"
                 f"`{d}{dm_ref}B x 50% = {d}{em_ref}B`"))
    rows.append((3, "Global Minimum Size Range",
                 f"{d}{lo}B – {d}{hi}B",
                 f"A 0.5x to 1.15x band around it:\n\n"
                 f"`{d}{em_ref}B x 0.5 = {d}{lo}B`\n\n"
                 f"`{d}{em_ref}B x 1.15 = {d}{hi}B`"))
    if pub_idx:
        uni = pub_idx / coverage
        # c-299: the factsheet is DATED, and the date is passed
        # in from the registered call rather than typed here —
        # "July 2026" hard-coded would go quietly wrong the
        # moment the page is pointed at another review.
        c4 = (f"The {idx_asof + ' ' if idx_asof else ''}MSCI "
              f"Taiwan factsheet gives the index "
              f"{d}{pub_idx:,.0f}B "
              f"of free-float value covering {coverage:.0%} of "
              f"Taiwan's investable market, so that market "
              f"totals:\n\n"
              f"`{d}{pub_idx:,.0f}B / {coverage:.2f} = "
              f"{d}{uni:,.0f}B`\n\n"
              + (f"Ranking {screened} companies that pass the "
                 f"investability screens by size "
                 if screened else "Ranking by size ")
              + f"and accumulating free-float value, "
              f"{coverage:.0%} of {d}{uni:,.0f}B is reached at "
              f"the {_ordinal(cross_rank)} company. Its FULL "
              f"market value is {d}{cutoff}B.")
    else:
        c4 = "The coverage test on Taiwan's investable universe."
    rows.append((4, "Market Size-Segment Cutoff", f"{d}{cutoff}B",
                 c4))
    rows.append((5, "Deletion floor", f"{d}{lower}B",
                 f"Two thirds of the cutoff:\n\n"
                 f"`{d}{cutoff}B x 2/3 = {d}{lower}B`"))
    rows.append((6, "Addition bar", f"{d}{upper}B",
                 f"One and a half times the cutoff:\n\n"
                 f"`{d}{cutoff}B x 1.5 = {d}{upper}B`"))
    if min_float:
        rows.append((7, "Minimum free-float value",
                     f"{d}{min_float}B",
                     f"Half the cutoff, measured on free float:"
                     f"\n\n`{d}{cutoff}B x 0.5 = "
                     f"{d}{min_float}B`"))
    return rows


def size_ladder_calc(dm_ref, em_ref, lo, hi, cutoff, lower,
                     upper, min_float=None, pub_dm=None,
                     pub_asof=None, pub_idx=None, cross_rank=None,
                     coverage=0.85, screened=None):
    """The arithmetic behind every card, as markdown.

    c-283. The cards used to carry their own sums; Bill asked
    for those in a "Calculation" dropdown instead. Keeping the
    two in one module matters — the figure and the working are
    generated from the SAME arguments in the same call, so a
    card cannot show one number while the expander shows
    another.

    Nothing is typed. Every value is a parameter, and every
    product is computed here rather than written out, so a
    changed input moves both the drawing and the working.
    """
    rows = [
        "| # | Number | How it is computed |",
        "|---|---|---|",
    ]
    dm = f"**&#36;{dm_ref}B**"
    if pub_dm:
        up = round((dm_ref / pub_dm - 1) * 100, 1)
        dm_calc = (f"MSCI publishes &#36;{pub_dm}B priced "
                   f"{pub_asof or 'at its own cutoff'}. Scaled to "
                   f"this review with the MSCI ACWI IMI 3-month "
                   f"return: &#36;{pub_dm}B x (1 + {up}%) = "
                   f"&#36;{dm_ref}B")
    else:
        dm_calc = ("85% of the free-float value of the 23 "
                   "developed markets, ranked by size")
    rows.append(f"| 1 | DM Standard reference {dm} | {dm_calc} |")
    rows.append(f"| 2 | EM Standard reference **&#36;{em_ref}B** | "
                f"&#36;{dm_ref}B x 50% = &#36;{em_ref}B |")
    rows.append(f"| 3 | Global Minimum Size Range "
                f"**&#36;{lo}B – &#36;{hi}B** | "
                f"&#36;{em_ref}B x 0.5 = &#36;{lo}B and "
                f"&#36;{em_ref}B x 1.15 = &#36;{hi}B |")
    if pub_idx:
        uni = pub_idx / coverage
        c4 = (f"MSCI's factsheet gives the index "
              f"&#36;{pub_idx:,.0f}B of free-float value and "
              f"states it covers {coverage:.0%} of Taiwan's "
              f"investable market, so that market totals "
              f"&#36;{pub_idx:,.0f}B / {coverage:.2f} = "
              f"&#36;{uni:,.0f}B. Ranking"
              + (f" {screened} screened companies" if screened
                 else " Taiwan's companies")
              + f" by size and accumulating free-float value, "
              f"{coverage:.0%} of &#36;{uni:,.0f}B is reached at "
              f"the {_ordinal(cross_rank)} company, whose FULL "
              f"market value is &#36;{cutoff}B")
    else:
        c4 = ("the coverage test on Taiwan's own investable "
              "universe")
    rows.append(f"| 4 | Market Size-Segment Cutoff "
                f"**&#36;{cutoff}B** | {c4} |")
    rows.append(f"| 5 | Deletion floor **&#36;{lower}B** | "
                f"&#36;{cutoff}B x 2/3 = &#36;{lower}B |")
    rows.append(f"| 6 | Addition bar **&#36;{upper}B** | "
                f"&#36;{cutoff}B x 1.5 = &#36;{upper}B |")
    if min_float:
        rows.append(f"| 7 | Minimum free-float value "
                    f"**&#36;{min_float}B** | "
                    f"&#36;{cutoff}B x 0.5 = &#36;{min_float}B |")
    return "\n".join(rows)


def size_ladder(dm_ref, em_ref, lo, hi, cutoff, lower, upper,
                min_float=None, pub_dm=None, pub_asof=None,
                pub_idx=None, cross_rank=None):
    """How the size thresholds are related, and WHY (c-253).

    Bill: *"First think about how these numbers are related,
    what is their relationship. Then give your best efforts to
    visualize this relationship."*

    The relationship is a **two-stage funnel**. A GLOBAL number,
    computed from the developed-market universe and halved for
    emerging markets, opens a corridor. The market's OWN 85%
    walk then picks a point inside that corridor. Buffers
    straddle that point. Every arrow is a multiplication, and
    nothing in the chain is a number MSCI publishes for Taiwan.

    c-268 — EACH LAYER NOW SAYS WHY IT EXISTS. Bill: *"We need
    to explain what this number represents… why divided by 2,
    why times 0.5 and 1.15. Add an easy-to-understand
    explanation to each of these steps."*

    Right, and the figure row above the step is deleted, so
    this is the only place those numbers appear. A card that
    prints a value and a multiplier answers "what happened"
    and leaves "why" to a paragraph nobody reads; the
    explanation belongs on the layer it explains.

    The DM card also has to own an honesty problem. MSCI
    publishes the reference priced at a date months before this
    review, and the figure shown is that published number
    scaled to this review's pricing. The card says so and
    prints the scalar, which is COMPUTED here from the two
    values rather than typed.

    The figure stays in two panels:

      LEFT   the chain — where each number comes from, the
             operator on each arrow, and one plain-English
             reason per layer;
      RIGHT  the ladder — the same numbers on one US$bn scale,
             which is the only way to see that the upper buffer
             sits ABOVE the corridor's ceiling and the lower
             buffer BELOW its floor. The corridor bounds the
             CUTOFF, not the buffers, and a reader who has only
             seen the arithmetic will assume otherwise.
    """
    cx, cw = 0, 330
    # c-272. Two changes, both Bill's.
    #
    # 1. NO "WALK" ANYWHERE. It is desk shorthand for the
    #    cumulative coverage test and it means nothing to a
    #    reader. Every occurrence is now "coverage test" or a
    #    plain description of what is being counted.
    # 2. EVERY LAYER SHOWS ITS ARITHMETIC. Bill: *"if the reader
    #    doesn't pay close attention, it's very easy for them to
    #    lose track of the calculation."* So each card carries
    #    the sum that produced its own number, and each cites
    #    the clause it follows rather than leaving the rulebook
    #    reference to a footnote.
    #
    # The section marks (§) sit at the END of the reason in
    # muted type rather than mid-sentence, so they stop
    # interrupting the explanation.
    # c-276, TWO CHANGES FROM BILL, both about the same thing —
    # the cards were doing a job that belonged somewhere else.
    #
    # 1. SHORTER. *"I like that the current explanations are
    #    more intuitive, but they are slightly too long."* Each
    #    card now carries the plain reason and its own
    #    arithmetic, and stops. What was cut was mostly
    #    re-statement: a card that says what a threshold is FOR
    #    does not also need to say what it is not for.
    #
    # 2. NO SECTION MARKS. Every §-reference moves out to the
    #    "Rulebook References" block under the step, which
    #    already lists all five with page numbers and quoted
    #    text. Carrying them here too meant the same citation
    #    appeared twice on one screen, in the shorter and less
    #    useful form. This also continues c-268's instruction
    #    that a rulebook reference should be available rather
    #    than intrusive.
    # c-283: THE ARITHMETIC LEAVES THE CARDS. Bill asked for
    # the explanation reformatted and the sums moved into a
    # "Calculation" dropdown. A card now answers one question —
    # what is this number FOR — in the same shape every time:
    # what is measured, then what the threshold does. The
    # arithmetic lives in `size_ladder_calc`. A reader following
    # the logic and a reader checking the maths want different
    # things on screen, and the card was trying to be both.
    # c-313, Bill: *"there is a lot of white space on the right,
    # I want to see less white space, while making sure that all
    # text are still within the textbox."*
    #
    # WHY THE CARD WAS SO WIDE. Every card shares one width, and
    # that width was set by the single longest line anywhere in
    # the figure. c-312 had raised the branch wrap to 54
    # characters to kill an orphaned last word, which made THAT
    # line the longest and dragged all seven cards out with it —
    # so six cards were sized for a sentence that is not in them.
    #
    # 40 characters is the setting where NO card ends on a
    # one-word line and the longest line is shortest; it was
    # found by sweeping 32-52 and checking both conditions, not
    # guessed. The cards get a line or two taller and about 90
    # units narrower, which is the trade Bill is asking for.
    #
    # Every body is wrapped from a SENTENCE now. Four of them
    # used to be hand-broken lists, which is why re-tuning the
    # width used to mean re-typing the copy.
    WRAP = 40
    dm_why = _wrap("The size of the company that sits at the 85% "
                   "coverage line across the 23 developed "
                   "markets.", WRAP)
    # c-296, Bill: the two reference cards carry their full names
    # over three lines each. A list is a multi-line eyebrow; a
    # plain string stays one line, so the other five are untouched.
    chain = [
        (["Developed Markets",
          "Global Minimum Size Reference"], f"${dm_ref}B", "", NAVY,
         dm_why),
        (["Emerging Markets",
          "Global Minimum Size Reference"], f"${em_ref}B",
         "÷ 2", NAVY,
         # c-312, Bill: no line may begin with a single orphaned
         # word. c-313 keeps that promise at a narrower wrap —
         # "developed bar." is two words, not one.
         _wrap("Emerging markets are held to half the developed "
               "bar.", WRAP)),
        ("Global Minimum Size Range", f"${lo}B – ${hi}B",
         "× 0.5 and × 1.15", MUTED,
         _wrap("A band around EM reference, giving each market "
               "room to differ. Every emerging market's cutoff "
               "has to land inside it.", WRAP)),
        ("Market Size-Segment Cutoff", f"${cutoff}B",
         "Taiwan's own coverage test", RED,
         _wrap("Sum the free-float market cap of Taiwan's "
               "largest companies, in size order, until 85% of "
               "the market is covered. The last company added "
               "to reach 85% \u2014 its full market cap \u2014 "
               "becomes the cutoff.", WRAP)),
    ]
    branch = [("5 · Deletion floor", f"${lower}B", "× 2/3", RED,
               "A member is removed only if it falls below "
               "this, not when it crosses the cutoff, so small "
               "price moves do not push companies in and out every "
               "quarter."),
              ("6 · Addition bar", f"${upper}B", "× 1.5", GREEN,
               "A non-member "
               "has to clear this higher bar \u2014 not just the "
               "cutoff \u2014 to join, so a company sitting near "
               "the cutoff is not added one quarter and deleted "
               "the next.")]
    if min_float:
        branch.append(
            ("7 · Minimum free-float value", f"${min_float}B",
             "× 0.5", MUTED,
             "A new constituent also needs enough shares "
             "available in free float \u2014 a large company "
             "whose shares are mostly locked up does not have "
             "enough freely tradable shares for index tracking "
             "funds to buy."))

    # c-276: cards 5-7 share the chain's left edge and width.
    # They were indented to x=26 to read as a branch off the
    # cutoff, which put two left margins on one figure for a
    # relationship the connector line already shows. Bill:
    # *"make the substep 5 to 7 align vertically with step
    # 1-4."* The connector stays; only the indent goes.
    bwhy = [_wrap(b[4], WRAP) for b in branch]
    # The card hugs its longest line rather than sitting at a
    # width nobody re-measured.
    #
    # c-313 BUG FIX, found while narrowing: only the BODY was
    # ever measured. The eyebrow is a different font size with
    # letter-spacing, and "4 · MARKET SIZE-SEGMENT CUTOFF" is
    # wider than several bodies — at 330 units that never
    # mattered, but a width derived from the body alone would
    # have clipped it the moment the body got short enough.
    # Measure all three text families and take the widest.
    _lab_all = [f"{i} · {n if isinstance(n, str) else n[0]}"
                for i, (n, *_r) in enumerate(chain, 1)]
    _lab_all += [ln for _n, name, *_r in chain
                 if isinstance(name, list) for ln in name[1:]]
    _lab_all += [b[0] for b in branch]
    cw = max(
        _fitw([ln for c in chain for ln in c[4]]
              + [ln for w in bwhy for ln in w], FS_CAP),
        _fitw([x.upper() for x in _lab_all], FS_EYEBROW, ls=1.1),
        _fitw([c[1] for c in chain] + [b[1] for b in branch],
              FS_TITLE))
    BX, BW = cx, cw

    def _lab_lines(c):
        """A card's eyebrow, as lines. Index prefix included."""
        n, name = c
        return ([f"{n} · {name[0]}"] + list(name[1:])
                if isinstance(name, list) else [f"{n} · {name}"])

    def _card_h(n_lines, n_label=1):
        return 56 + 13 * n_lines + 13 * (n_label - 1)

    # c-283, Bill: *"Make each box of sub step 1-7 same distance
    # from each other."* One constant for every gap — the chain
    # used 32, the chain-to-branch join 26 and the branch 24,
    # which read as three different relationships when there is
    # only one.
    GAP = 32
    tops, y = [], 30
    for i, c in enumerate(chain):
        tops.append(y)
        y += _card_h(len(c[4]),
                     len(_lab_lines((i + 1, c[0])))) + GAP
    brow, y = [], y
    for w in bwhy:
        brow.append(y)
        y += _card_h(len(w)) + GAP
    # c-313: THE CANVAS IS DERIVED FROM THE CARDS, not typed.
    # `ax` was a constant that had to be nudged by hand every
    # time the card width moved (380 at c-269, 400 at c-312, and
    # it would have needed a third value now). Hanging it off
    # `cw` means the gap between the two panels is the same
    # whatever the copy does.
    #
    # 90 units of gap is what the corridor labels need: they are
    # anchored END at ax-8 and the widest of them ("$9.44B") runs
    # about 45 units, so 90 leaves ~35 of air. The 110 on the
    # right is the mirror — the widest right-hand label there is
    # "upper buffer", about 62 units from ax+aw+8.
    ax, aw = cw + 90, 300         # value axis, line length
    W, H = ax + aw + 110, int(y + 18)
    s = [_open(W, H)]

    def card(x, w, y, label, val, why, colour):
        """One layer. Same object whether it is in the chain or
        on the branch — that is the whole point of the change.

        `label` may be a string or a list of lines; a multi-line
        eyebrow pushes the value and the body down by exactly the
        height it added, so nothing overlaps.
        """
        lab = label if isinstance(label, list) else [label]
        extra = 13 * (len(lab) - 1)
        h = _card_h(len(why), len(lab))
        out = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" '
               f'rx="3" fill="{CARD}" stroke="{RULE}"/>',
               f'<rect x="{x}" y="{y}" width="3" height="{h}" '
               f'fill="{colour}"/>']
        for n, line in enumerate(lab):
            out.append(f'<text x="{x + 14}" y="{y + 21 + n * 13}" '
                       f'font-size="{FS_EYEBROW}" '
                       f'letter-spacing="1.1" fill="{FAINT}">'
                       f'{line.upper()}</text>')
        out.append(f'<text x="{x + 14}" y="{y + 42 + extra}" '
                   f'font-size="{FS_TITLE}" font-weight="700" '
                   f'fill="{INK}">{val}</text>')
        for n, line in enumerate(why):
            out.append(f'<text x="{x + 14}" '
                       f'y="{y + 58 + extra + n * 13}" '
                       f'font-size="{FS_CAP}" fill="{MUTED}">'
                       f'{line}</text>')
        return "".join(out)

    # ---- LEFT: the derivation chain -------------------------
    for i, (name, val, how, colour, why) in enumerate(chain):
        y = tops[i]
        s.append(card(cx, cw, y, _lab_lines((i + 1, name)), val,
                      why, colour))
        if i:
            # c-278, Bill: *"The arrows for section 3, between
            # substep 1-4, are different from 5-7. Make the
            # color match their textbox."* Every connector now
            # takes the accent colour of the card it points
            # INTO, so an arrow and the stripe it lands on
            # match. Cards 1-4 were all navy and 5-7 all grey,
            # which read as two unrelated systems in one figure.
            s.append(f'<text x="{cx + 14}" y="{y - 10}" '
                     f'font-size="{FS_CAP}" fill="{colour}">'
                     f'{how}</text>')
            s.append(f'<line x1="{cx + 8}" y1="{y - 32}" '
                     f'x2="{cx + 8}" y2="{y - 6}" '
                     f'stroke="{colour}" stroke-width="1.2"/>')
            s.append(f'<path d="M{cx + 8} {y} L{cx + 4} '
                     f'{y - 7} L{cx + 12} {y - 7} Z" '
                     f'fill="{colour}"/>')

    # ---- the branch: what the cutoff produces ---------------
    # c-276. The old drawing was a vertical spine at cx+8 with a
    # horizontal elbow into each card's left edge. That worked
    # only while the cards were indented to x=26 — once they
    # align with the chain the spine runs THROUGH them and the
    # elbow has nowhere to go.
    #
    # So the branch borrows the chain's connector instead: a
    # short stub and an arrowhead in the gap ABOVE each card,
    # where nothing else is drawn.
    #
    # c-278: and it takes the colour of the card it points into,
    # exactly as the chain now does. What separates the two
    # groups is the OPERATOR TEXT, not the colour — a branch
    # stub reads "× 2/3 of the cutoff", naming card 4 as its
    # parent, where a chain arrow names only its multiplier and
    # inherits its parent from the card directly above it.
    for i, (name, val, how, colour, why) in enumerate(branch):
        y = brow[i]
        s.append(f'<line x1="{cx + 8}" y1="{y - GAP}" '
                 f'x2="{cx + 8}" y2="{y - 6}" stroke="{colour}" '
                 f'stroke-width="1.2"/>')
        s.append(f'<path d="M{cx + 8} {y} L{cx + 4} {y - 7} '
                 f'L{cx + 12} {y - 7} Z" fill="{colour}"/>')
        s.append(card(BX, BW, y, name, val, bwhy[i], colour))
        # c-287: the branch operators used to read "x 2/3 of
        # the cutoff" against the chain's bare "x 1.5", so the
        # two halves of one figure captioned themselves
        # differently. Both are now the operator alone, at the
        # same offset — the Calculation box under each card
        # names the parent, which is where that belongs.
        s.append(f'<text x="{cx + 14}" y="{y - 10}" '
                 f'font-size="{FS_CAP}" fill="{colour}">'
                 f'{how}</text>')

    # ---- RIGHT: the same numbers on one scale ---------------
    # GEOMETRY, third time lucky. The lines used to run to
    # ax+360 with their labels beyond that, which put both off
    # the right of the canvas; and the range floor/ceiling were
    # labelled on the same side as the buffers, where the two
    # values sit 16px apart and printed on top of one another.
    # Solid lines label RIGHT, dashed corridor bounds label
    # LEFT, so the two families can never collide.
    # c-269: the ladder is CAPPED, not stretched to the left
    # column. Once layers 5-7 became full cards the chain grew
    # to ~940 units and a ladder drawn to match turned the
    # corridor into a 580-unit empty box — the band's height
    # started reading as a quantity, which it is not. It is a
    # value axis; it needs enough room to separate five lines
    # and no more.
    top = 46
    bot = min(H - 70, top + 520)   # y for vmax, vmin
    vals = [lo, hi, cutoff, lower, upper]
    vmax, vmin = max(vals) * 1.06, min(vals) * 0.80

    def Y(v):
        return _r(bot - (v - vmin) / (vmax - vmin) * (bot - top))

    s.append(f'<text x="{ax + aw}" y="{top - 20}" '
             f'font-size="{FS_EYEBROW}" letter-spacing="1.1" '
             f'text-anchor="end" fill="{FAINT}">'
             f'US$</text>')
    s.append(f'<rect x="{ax}" y="{Y(hi)}" width="{aw}" '
             f'height="{_r(Y(lo) - Y(hi))}" fill="#f0eade"/>')
    s.append(f'<text x="{ax + 8}" y="{Y(hi) + 15}" '
             f'font-size="{FS_CAP}" fill="{MUTED}">Global '
             f'Minimum Size Range</text>')

    def dashed(v, label):
        y = Y(v)
        return (f'<line x1="{ax}" y1="{y}" x2="{ax + aw}" '
                f'y2="{y}" stroke="{MUTED}" stroke-width="1" '
                f'stroke-dasharray="4 3"/>'
                f'<text x="{ax - 8}" y="{y - 2}" '
                f'font-size="{FS_CAP}" text-anchor="end" '
                f'fill="{MUTED}">{label}</text>'
                f'<text x="{ax - 8}" y="{y + 12}" '
                f'font-size="{FS_CAP}" text-anchor="end" '
                f'fill="{FAINT}">${v}B</text>')

    # c-268: the buffers take the colours they carry everywhere
    # else on the site — green is the line a non-member clears
    # to be ADDED, red the line an incumbent falls through to
    # be DELETED.
    def solid(v, label, note, weight=1.5, colour=RED):
        y = Y(v)
        return (f'<line x1="{ax}" y1="{y}" x2="{ax + aw}" '
                f'y2="{y}" stroke="{colour}" '
                f'stroke-width="{weight}"/>'
                f'<text x="{ax + aw + 8}" y="{y - 2}" '
                f'font-size="{FS_CAP}" font-weight="700" '
                f'fill="{colour}">${v}B</text>'
                f'<text x="{ax + aw + 8}" y="{y + 12}" '
                f'font-size="{FS_CAP}" fill="{MUTED}">'
                f'{label}</text>'
                + (f'<text x="{ax + 8}" y="{y - 6}" '
                   f'font-size="{FS_CAP}" fill="{colour}">'
                   f'{note}</text>' if note else ""))

    s.append(dashed(hi, "ceiling"))
    s.append(dashed(lo, "floor"))
    s.append(solid(upper, "upper buffer",
                   "× 1.5 — a non-member clears this to join",
                   colour=GREEN))
    s.append(solid(cutoff, "market cutoff",
                   "Taiwan at 85% coverage", 3, NAVY))
    s.append(solid(lower, "lower buffer",
                   "× 2/3 — an incumbent is held above this"))
    # c-269: the "corridor bounds the cutoff" caption is
    # deleted. The ladder already shows both buffers outside
    # the shaded band, and a caption explaining a picture the
    # picture makes is the density Bill keeps removing.
    s.append("</svg>")
    return _end(s)


def _wrap(text, n):
    """Greedy wrap to `n` characters, for SVG (no text flow)."""
    out, line = [], ""
    for w in text.split():
        if line and len(line) + 1 + len(w) > n:
            out.append(line)
            line = w
        else:
            line = f"{line} {w}".strip()
    if line:
        out.append(line)
    return out


def cutoff_timeline(universe, liquidity, price_from, price_to,
                    announced, close):
    """The THREE data cutoffs, on one axis (c-250).

    Bill: *"which date of data should we use for, this should
    strictly follow MSCI's rulebook."* It does, and the point
    the picture makes faster than a paragraph is that there is
    no such thing as "the cutoff": three different dates govern
    three different inputs, they are two months apart end to
    end, and only ONE of them is uncertain.

    GIMI May-2026 §3.1.9, p.48. For an August review:
      Equity Universe Cutoff  last business day of MAY
      Liquidity Cutoff        last business day of JUNE
      Price Cutoff            any one of the last 10 business
                              days of JULY, and that single
                              unknown is the forecasting
                              problem.

    c-268: EVERY LABEL IS NOW BELOW THE AXIS. The first version
    alternated sides because five dated marks in a row seemed
    impossible to label on one, and the liquidity block went
    above. Bill: *"I think there is enough room… We can stretch
    equity universe cutoff to leftmost, and index changes to
    rightmost."*

    He is right, and the fix costs nothing, because the two
    outer marks were not at the canvas edges to begin with —
    they sat at 92 and 848 with dead margin outside them. Once
    the scale is stretched so the first cutoff starts the axis
    and the change date ends it, the same five blocks have
    another 90 units of room and the outer two can anchor to
    their own ends instead of centring. Proportionality
    survives: the positions are still the real calendar gaps,
    now spread over the full width rather than over 756 units
    of it, and the figure loses half its height because nothing
    needs the space above the line any more.

    THE NOTES ARE IN ENGLISH, NOT IN RULEBOOK. Bill: *"I know
    you are quoting from rule book, but try to explain things
    and not use abbreviation."* So "ATVR" becomes what it
    measures, and §3.1.9's four price-cutoff bullets — prices
    for market cap, FIF updates per §3.1.7, foreign room
    changes, NOS updates per §3.1.8 — become the four questions
    they answer. Four items in, four items out; only the
    language changes.
    """
    # x positions are PROPORTIONAL to the real calendar gaps
    # (29 May → 31 Aug is 94 days), so the picture does not
    # imply an even cadence the dates do not have.
    W, H = 880, 210
    y = 52
    x0, x1 = 24, 856

    def X(day):                       # day 0 = universe cutoff
        return _r(x0 + (x1 - x0) * day / 94)

    xU, xL, pA, pB = X(0), X(32), X(52), X(63)
    xN, xC = X(75), X(94)
    s = [_open(W, H)]
    s.append(f'<line x1="{x0}" y1="{y}" x2="{x1}" y2="{y}" '
             f'stroke="{RULE}" stroke-width="1.5"/>')
    # the price window: a BAND, because the day is unknown
    s.append(f'<rect x="{pA}" y="{y - 13}" width="{_r(pB - pA)}" '
             f'height="26" fill="#f6e7e3" stroke="{RED}" '
             f'stroke-dasharray="3 3"/>')
    # c-409, Bill: the three cutoff ticks pass fs_note one
    # size down — their second note row was overlapping at the
    # c-405 face.
    s.append(_mark(y, xU, NAVY, 2, "Equity Universe Cutoff",
                   universe,
                   ["Which companies exist and",
                    "are big enough to be considered"], "start",
                   fs_note=_px(0.66)))
    s.append(_mark(y, xL, GREEN, 2, "Liquidity Cutoff", liquidity,
                   ["How much of the company",
                    "actually trades, and how often"],
                   fs_note=_px(0.66)))
    s.append(_mark(y, _r((pA + pB) / 2), RED, 0, "Price Cutoff",
                   f"{price_from} – {price_to}",
                   ["The share price used to calculate "
                    "market cap",
                    "What percentage of shares foreigners may own",
                    "How much foreign ownership limit is left",
                    "The total number of shares"],
                   fs_note=_px(0.66)))
    # THE RED LINE BELONGS TO THE PRICE MARK, not floating over
    # the axis. As a free-standing headline it collided with
    # whichever label happened to be above the axis nearby.
    s.append(f'<text x="{_r((pA + pB) / 2)}" y="{y + 130}" '
             f'font-size="{FS_CAP}" text-anchor="middle" '
             f'font-weight="700" fill="{RED}">MSCI picks any '
             f'one of these 10 days</text>')
    # c-268: "Index changes" was the odd one out — four marks
    # named a DATE and the fifth named an event. Bill wanted
    # "Effective" and was right that it did not fit, because
    # it is an adjective where the others are noun phrases.
    # Naming both ends in full settles it and, more usefully,
    # makes step 2 agree with step 1, which labels the same two
    # moments "Announcement Date" and "Effective Date".
    s.append(_mark(y, xN, FAINT, 1.5, "Announcement Date",
                   announced, []))
    s.append(_mark(y, xC, FAINT, 1.5, "Effective Date", close,
                   [], "end"))
    # The rulebook citation lives in the caption BELOW, not in
    # here: a caption can carry a link, an SVG label cannot,
    # and the test that forbids typed-in facts is right to
    # count an edition date as one.
    s.append("</svg>")
    return _end(s)
