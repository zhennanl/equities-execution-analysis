"""One design system for the whole site.

c-207 dense -> c-211 calm -> c-212 crafted -> c-213 EDITORIAL.

Bill chose direction B from three mockups, applied site-wide.

WHY EDITORIAL IS THE RIGHT FIT, beyond taste. This site is a
reference document that happens to be interactive: it explains
how an index review works, records what MSCI has done since
2006, and shows what the data can and cannot support. That is a
research note, not a blotter. Research notes have been
typeset well for two hundred years and the conventions are
settled — serif for reading, sans for data, a warm ground, rules
instead of boxes, and colour used sparingly enough that it still
means something when it appears.

The two alternatives were rejected for concrete reasons rather
than taste: A (institutional navy) looked like every internal
bank tool, and C (minimal mono) reduced colour to status dots,
which would have thrown away the add-green / delete-red pairing
that does real work on every page here.

THE DISCIPLINE THAT KEEPS THIS FROM GOING DECORATIVE:
  * serif is for HEADINGS ONLY. Every number, table, ticker and
    control stays in a sans face, because tabular data in a
    serif is harder to scan and this is still a data site.
  * colour is still functional. Green means addition, red means
    deletion, amber means degraded data. The warm ground and
    the rules are the only things that are purely aesthetic.
  * tabular numerals survive, as they have through every
    revision.

REFERENCES, public and inspectable:
  FT Chart Doctor  chart conventions from a newsroom that
                   publishes financial charts daily
  IBM Carbon       the spacing scale, retained from c-212

Usage from any view:
    from views import design
    design.css()                       # once per page
    design.status(...)                 # the context bar
    design.stats([...])                # the figure row
    design.sect(1, "Title", "lead")    # a section rule
    design.chart(fig)                  # EVERY plotly figure
"""
import streamlit as st

# ---- palette -------------------------------------------------
# Warm neutrals. A paper ground rather than a screen ground is
# the single change that makes this read as a document.
PAPER = "#fdfaf6"      # page
CARD = "#ffffff"       # raised surface
RULE = "#e8ddd1"       # hairline, warm
RULE_L = "#f2ebe2"     # lighter hairline
INK = "#2b2724"        # warm near-black
MUTED = "#8a7f76"      # secondary
FAINT = "#a89c92"      # tertiary

NAVY = "#1f4e79"       # structural accent
GREEN = "#2e7d52"      # addition
RED = "#b03a2e"        # deletion
AMBER = "#a5731c"      # degraded data

# ---- scale (Carbon: multiples of 2/4/8) ---------------------
S1, S2, S3, S4 = ".25rem", ".5rem", ".75rem", "1rem"
S5, S6, S7, S8 = "1.5rem", "2rem", "2.5rem", "3rem"

SERIF = ("'Source Serif 4', Georgia, 'Times New Roman', serif")
SANS = ("'Inter', -apple-system, BlinkMacSystemFont, "
        "'Segoe UI', Roboto, sans-serif")
MONO = "'JetBrains Mono', ui-monospace, Menlo, Consolas, monospace"

CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Source+Serif+4:opsz,wght@8..60,400;8..60,600;8..60,700&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500;700&display=swap');

html, body, [class*="css"], .stApp {{ font-family:{SANS} }}
.stApp {{ background:{PAPER} }}
.block-container{{padding-top:{S6}!important;
 padding-bottom:{S8}!important;max-width:1120px}}

/* SERIF FOR HEADINGS ONLY — data stays in a sans face */
h1{{font-family:{SERIF}!important;font-size:2.1rem!important;
 font-weight:600!important;color:{INK}!important;
 letter-spacing:-.01em!important;line-height:1.2!important;
 margin-bottom:{S2}!important}}
h2{{font-family:{SERIF}!important;font-size:1.4rem!important;
 font-weight:600!important;color:{INK}!important;
 margin:{S5} 0 {S2}!important}}
h3{{font-family:{SERIF}!important;font-size:1.15rem!important;
 font-weight:600!important;color:{INK}!important}}
p, li, .stMarkdown{{color:{MUTED};line-height:1.65}}
div[data-testid="stCaptionContainer"]{{color:{FAINT};
 font-size:.8rem;line-height:1.6}}

div[data-testid="stVerticalBlock"]{{gap:{S4}}}
div[data-testid="stMetricValue"]{{font-size:1.6rem;
 font-weight:500;color:{INK};font-variant-numeric:tabular-nums}}
div[data-testid="stMetricLabel"]{{font-size:.7rem;
 letter-spacing:.1em;text-transform:uppercase;color:{FAINT}}}
table,td,th,div[data-testid="stDataFrame"],
div[data-testid="stMetric"]{{font-variant-numeric:tabular-nums}}
.stDataFrame{{font-size:.86rem}}

section[data-testid="stSidebar"]{{width:262px!important;
 background:{CARD};border-right:1px solid {RULE}}}
div[data-testid="stExpander"] details{{border:1px solid {RULE};
 border-radius:4px;background:{CARD}}}
div[data-testid="stExpander"] summary{{font-size:.86rem;
 font-weight:500;color:{MUTED}}}
.stButton button, .stDownloadButton button, .stLinkButton a{{
 border-radius:4px;font-weight:500;font-size:.84rem;
 border:1px solid {RULE};color:{INK}}}

/* ---- status strip ---------------------------------------
   A masthead line, not a control panel.                     */
.dstrip{{display:flex;align-items:center;gap:{S3};
 flex-wrap:wrap;border-top:1px solid {INK};
 border-bottom:1px solid {RULE};padding:{S2} 0;
 margin:{S1} 0 {S5};font-family:{SANS};font-size:.72rem;
 color:{MUTED};letter-spacing:.03em;text-transform:uppercase}}
.dstrip b{{color:{INK};font-weight:600;letter-spacing:0;
 font-variant-numeric:tabular-nums}}
.dstrip .sep{{color:{RULE}}}
.dstrip .ok{{color:{GREEN};font-weight:600}}
.dstrip .warn{{color:{AMBER};font-weight:600}}
.dstrip .push{{margin-left:auto}}

/* ---- figure row -----------------------------------------
   Rules between figures instead of boxes around them. This is
   the change that most makes the page read as a document.   */
.dstats{{display:flex;flex-wrap:wrap;gap:0;margin:0 0 {S5};
 border-top:1px solid {RULE};border-bottom:1px solid {RULE}}}
.dstat{{flex:1 1 140px;min-width:0;padding:{S3} {S4};
 border-right:1px solid {RULE_L}}}
.dstat:last-child{{border-right:none}}
.dstat .k{{font-size:.66rem;letter-spacing:.12em;color:{FAINT};
 text-transform:uppercase;font-weight:600;white-space:nowrap;
 overflow:hidden;text-overflow:ellipsis}}
.dstat .v{{font-family:{SERIF};font-size:2rem;font-weight:400;
 color:{INK};line-height:1.3;font-variant-numeric:tabular-nums}}
.dstat .s{{font-size:.72rem;color:{FAINT};white-space:normal;
 overflow:hidden;text-overflow:ellipsis}}
.dstat.add .v{{color:{GREEN}}}
.dstat.del .v{{color:{RED}}}
/* c-245: a figure row can carry a WORD as well as a number —
   "each name's own daily history" is a legitimate value. At
   2rem serif it wrapped to three lines and dwarfed the numbers
   beside it, so a long value steps down to prose size. Applied
   by stats() on measurement, not by the caller. */
.dstat.txt .v{{font-family:{SANS};font-size:1rem;
 font-weight:500;line-height:1.5;white-space:normal}}

/* ---- section rule ---------------------------------------
   An eyebrow above a serif title — the standard opening of a
   printed section, and it gives the number somewhere to live
   that is not in the reader's way.                          */
.dsect{{margin:{S8} 0 {S3};border-bottom:1px solid {INK};
 padding-bottom:{S2}}}
.dsect .n{{display:block;font-family:{SANS};font-size:.64rem;
 letter-spacing:.16em;color:{NAVY};font-weight:600;
 text-transform:uppercase;margin-bottom:{S1}}}
.dsect .t{{font-family:{SERIF};font-size:1.5rem;font-weight:600;
 color:{INK};letter-spacing:-.01em}}
/* c-247: a PART heading — one level above a section, one below
   the page title. The Taiwan page has two of these ("The
   Call", "How We Predict"), and they open halves of the page
   rather than items in a list.

   c-248: A PART IS MARKED FROM ABOVE, A SECTION FROM BELOW.
   Bill: "because there are two dividers, to me it doesn't look
   very good." Both headings were drawing a full-width rule
   UNDER themselves, so a part immediately followed by its
   first step put two dark rules a line and a half apart and
   the title in between read as a band nobody designed.

   Two rules cannot stack if only one of them points down. The
   part now opens with a short navy mark above it — the
   printed chapter-opener convention — and draws nothing
   underneath. The step rule beneath is then the only
   horizontal line in that space, which is what it was for.  */
.dsect.big{{margin:{S8} 0 0;border-bottom:none;
 padding-bottom:0}}
.dsect.big::before{{content:'';display:block;width:44px;
 height:3px;background:{NAVY};margin-bottom:{S3}}}
.dsect.big .t{{font-size:1.9rem;line-height:1.25;
 display:block}}
.dsect.big .l{{margin-top:{S2}}}
.dsect .l{{display:block;font-family:{SANS};font-size:.82rem;
 color:{FAINT};margin-top:{S1};line-height:1.55}}
/* c-268: THE BREAK BETWEEN TWO STEPS.
   Bill: "Can we add a divider between steps? Choose one design
   that makes things most consistent."

   The consistent choice is the one already in the file's own
   vocabulary — a rule, not a box, not a background. What it
   must NOT do is repeat c-248: the step heading already draws a
   1px INK rule UNDER its title, so a second dark line above the
   eyebrow would put two heavy rules either side of a heading
   again.

   So this one is deliberately the LIGHTER of the two. A hairline
   in the table-rule colour reads as the end of a block; the ink
   rule below the title reads as the start of one. Weight is
   what tells them apart, and it is the same distinction the
   page already uses between a table's inner rules and its
   header. The margins are symmetric — this one contributes the
   space above, `.dsect`'s own top margin the space below.     */
.dbreak{{border-top:1px solid {RULE};margin:{S8} 0 0}}

/* ---- BEATS — explanation as a sequence, not a block -------
   c-247, replacing c-245's white prose card. See D13.

   The card was the wrong instrument and this file said so
   already: "rules instead of boxes", and a box is reserved for
   DATA (D1) precisely because prose is the paper's native
   content. Bill: "still looks a little awkward and out of
   place… long paragraphs are very prone to make the reader
   disengaged."

   A beat is one paragraph carrying one idea, numbered in the
   margin, on a shared left rule. The number is a CSS counter,
   so nothing has to be renumbered when a step gains or loses
   a paragraph.                                               */
div[class*="st-key-dbeats_"]{{counter-reset:beat;
 max-width:68ch;border-left:2px solid {RULE};
 padding-left:{S4};margin:0 0 {S4}}}
div[class*="st-key-dbeat_"]{{counter-increment:beat;
 position:relative;padding-left:2.4rem}}
div[class*="st-key-dbeat_"]::before{{
 content:counter(beat,decimal-leading-zero);position:absolute;
 left:0;top:.2rem;font-family:{MONO};font-size:.68rem;
 font-weight:700;color:{NAVY};letter-spacing:.06em}}
div[class*="st-key-dbeat_"] p{{color:{INK};font-size:.95rem;
 line-height:1.75;margin:0}}
/* the appendix behind the toggle: reading width, no numbers —
   the beats are the spine, this is the reference material */
div[class*="st-key-dmore_"]{{max-width:68ch}}
div[class*="st-key-dmore_"] p,
div[class*="st-key-dmore_"] li{{color:{MUTED};font-size:.9rem;
 line-height:1.7}}

/* ---- change rows ----------------------------------------
   Ruled list, no boxes. The action label is small, letter-
   spaced and coloured — enough to group a column at a glance
   without drawing a border around every name.               */
.drow{{display:flex;align-items:baseline;gap:{S3};
 padding:{S2} 0;border-bottom:1px solid {RULE_L};
 font-size:.92rem}}
.drow:first-child{{border-top:1px solid {RULE}}}
.dact{{font-family:{SANS};font-size:.62rem;font-weight:600;
 letter-spacing:.14em;text-transform:uppercase;
 flex:0 0 30px}}
.dact.add{{color:{GREEN}}}.dact.del{{color:{RED}}}
.dnm{{color:{INK};flex:1 1 auto;overflow:hidden;
 text-overflow:ellipsis;white-space:nowrap}}
.dcode{{font-family:{MONO};color:{FAINT};font-size:.76rem;
 flex:0 0 auto;font-variant-numeric:tabular-nums}}
</style>
"""

# ---- plotly theme -------------------------------------------
# Charts sit ON the paper, not on a white card, so a figure
# reads as part of the page rather than pasted onto it.
CHART = dict(
    font=dict(family="Inter, sans-serif", size=12, color=MUTED),
    plot_bgcolor=PAPER, paper_bgcolor=PAPER,
    margin=dict(l=8, r=8, t=30, b=8),
    # c-338, Bill: *"the axis labels for all graphs are very
    # light."* They were FAINT (#a89c92) at 11px, which is the
    # site's TERTIARY ink — a weight meant for footnotes, not for
    # the label that says what an axis measures. Raised to MUTED
    # at 11.5px and semibold. Tick labels get MUTED too; they
    # were inheriting the figure-level FAINT.
    #
    # `weight` needs plotly >= 5.23 (this project runs 6.8). On an
    # older build it is ignored rather than raising, so the size
    # and colour still carry most of the improvement.
    xaxis=dict(showgrid=False, linecolor=RULE, ticks="outside",
               tickcolor=RULE, ticklen=4,
               tickfont=dict(size=11, color=MUTED),
               title_font=dict(size=11.5, color=MUTED, weight=600)),
    yaxis=dict(gridcolor=RULE_L, zerolinecolor=RULE,
               zerolinewidth=1, linecolor="rgba(0,0,0,0)",
               tickfont=dict(size=11, color=MUTED),
               title_font=dict(size=11.5, color=MUTED, weight=600)),
    legend=dict(orientation="h", yanchor="bottom", y=1.02,
                xanchor="right", x=1, font=dict(size=11),
                bgcolor="rgba(0,0,0,0)"),
    # c-282: ONE HOVER DESIGN FOR THE WHOLE SITE.
    #
    # Bill: *"Change all hover window design across this website
    # to the same as the design for index review history
    # timeline."* That card is an HTML `.pop` — white surface,
    # warm 1px border, small radius, soft shadow, Inter, a muted
    # uppercase eyebrow over dark body text.
    #
    # A plotly tooltip is an SVG element and cannot be given a
    # border-radius or a box-shadow, so it cannot be that card
    # literally. What it CAN match is everything that carries
    # the card's identity: the same surface, the same warm
    # border rather than plotly's default black, the same face
    # and size, dark warm ink rather than white-on-colour, and
    # left-aligned text so a label and its number line up the
    # way they do in the card.
    #
    # This is the only place it is set. Every figure on the site
    # goes through chart(), so the two hover styles cannot drift
    # apart by someone theming one chart and forgetting nine.
    # c-333, Bill: *"it looks very plain, and easy to lose
    # audience."* Fair. The surface was already right; what was
    # missing is HIERARCHY — every line rendered at one weight in
    # one colour, so a reader had to parse the tooltip instead of
    # glancing at it.
    #
    # What an SVG tooltip can and cannot have, since this gets
    # rediscovered: plotly's text engine supports <b>, <i>, <br>
    # and <span style="color:...;font-size:...">. It does NOT
    # support border-radius, box-shadow, padding, letter-spacing
    # or background on a span. So the hierarchy has to be built
    # out of weight, colour and size alone — which is what
    # `hover()` below does.
    #
    # `namelength=-1` stops plotly truncating a trace name at 15
    # characters with an ellipsis, which it does silently.
    hoverlabel=dict(bgcolor=CARD, bordercolor="#d9cbbb",
                    align="left", namelength=-1,
                    font=dict(family="Inter, sans-serif",
                              size=12.5, color=INK)),
    colorway=[NAVY, GREEN, RED, AMBER, FAINT],
)


# c-221: TITLE CASE, CENTRALLY. Bill asked for capitalised
# chart titles "on all titles on this website". Twenty-odd
# axis titles are spread over eight view files, so editing the
# strings would fix today's set and let tomorrow's drift. Every
# plotly figure on the site passes through chart(), so the rule
# is applied HERE and cannot be forgotten by a later caller.
#
# Two exceptions, because blind capitalisation is worse than
# none: a token that ALREADY carries a capital is left alone
# (USD, ADV, MSCI, E-1), and unit abbreviations that are
# conventionally lower-case stay lower ("bps", not "Bps").
# Minor words drop to lower-case unless they lead the title,
# which is ordinary title case rather than shouting every word.
_MINOR = {"a", "an", "and", "as", "at", "but", "by", "for",
          "from", "in", "of", "on", "or", "per", "the", "to",
          "vs", "with"}
_UNITS = {"bps", "sh", "px", "x", "bn", "mn", "k", "log"}


def title_case(text):
    """Title-case a label without mangling units or acronyms."""
    if not text:
        return text
    out, first = [], True
    for tok in str(text).split(" "):
        core = tok.strip("()[]{}<>,.:;—–-·%")
        low = core.lower()
        if not core or any(c.isupper() for c in core) \
                or low in _UNITS or not core[0].isalpha():
            out.append(tok)
            if core:
                first = False
            continue
        if low in _MINOR and not first:
            out.append(tok.replace(core, low, 1))
        else:
            out.append(tok.replace(core, core[0].upper()
                                   + core[1:], 1))
        first = False
    return " ".join(out)


def _cap_titles(fig):
    """Apply title_case to every title a reader can see."""
    lay = fig.layout
    if getattr(lay.title, "text", None):
        lay.title.text = title_case(lay.title.text)
    for name in dir(lay):
        if not (name.startswith("xaxis")
                or name.startswith("yaxis")
                or name.startswith("polar")
                or name == "coloraxis"):
            continue
        ax = getattr(lay, name, None)
        t = getattr(getattr(ax, "title", None), "text", None)
        if t:
            ax.title.text = title_case(t)
        bar = getattr(ax, "colorbar", None)
        bt = getattr(getattr(bar, "title", None), "text", None)
        if bt:
            bar.title.text = title_case(bt)
    for tr in fig.data:
        bar = getattr(getattr(tr, "marker", None),
                      "colorbar", None)
        bt = getattr(getattr(bar, "title", None), "text", None)
        if bt:
            bar.title.text = title_case(bt)



# ── the hover card (c-333) ──────────────────────────────────────

_HOVER_RULE = "─" * 22


def hover(title, rows=(), eyebrow=None, note=None):
    """Build a hovertemplate in the site's card idiom.

    ONE BUILDER, so tooltips cannot drift apart chart by chart —
    the same reason the hoverlabel style itself lives in exactly
    one place. Before this, every figure hand-rolled its own
    string and the result was a stack of same-weight lines.

    The card has four optional parts, in order:

        EYEBROW      small, uppercase, muted — what kind of thing
        Title        bold, ink, larger — which thing
        ─────        a hairline in the site's rule colour
        label value  muted label, bold navy value, one per row
        note         small muted italic, for a caveat

    `rows` is a sequence of (label, value) where value is usually
    a plotly format token like "%{y:.1%}". Both are inserted
    verbatim, so a caller can put a `%{customdata[n]}` anywhere.

    Returns a string ending in "<extra></extra>", which suppresses
    plotly's second box carrying the trace name — that box cannot
    be styled and duplicates what the title already says.
    """
    out = []
    if eyebrow:
        out.append(f"<span style='font-size:10px;color:{FAINT}'>"
                   f"{str(eyebrow).upper()}</span>")
    if title:
        out.append(f"<span style='font-size:13.5px;color:{INK}'>"
                   f"<b>{title}</b></span>")
    if rows:
        out.append(f"<span style='color:{RULE}'>{_HOVER_RULE}</span>")
        for label, value in rows:
            out.append(
                f"<span style='color:{MUTED}'>{label}</span>  "
                f"<span style='color:{NAVY}'><b>{value}</b></span>")
    if note:
        out.append(f"<span style='font-size:10.5px;color:{FAINT}'>"
                   f"<i>{note}</i></span>")
    return "<br>".join(out) + "<extra></extra>"


def chart(fig, height=None, zoom=False, select=False, key=None):
    """Theme a figure and render it. Every plotly call on the
    site goes through here.

    c-215: `zoom` exists because hiding the toolbar created a
    ONE-WAY DOOR. Plotly still zooms on drag even with the bar
    hidden, so a reader could zoom in and then have no control
    to get back — the chart simply stayed stuck until the page
    was rerun. Charts that reward zooming now get a minimal
    toolbar: zoom, pan, reset, and nothing else.
    """
    # c-239, DESIGN_DECISIONS D11: THE THEME MUST NOT OVERWRITE
    # A DELIBERATE LAYOUT CHOICE.
    #
    # CHART carries a default margin, and this line applied it
    # AFTER the caller's own update_layout — so a figure that
    # reserved 54px at the bottom for its colour bar silently
    # got 8px back and the bar landed on the plot. The caller
    # knows things about its figure that a site-wide default
    # cannot: the theme sets a default, it does not overrule.
    _own = fig.layout.margin
    _set = {k: getattr(_own, k) for k in ("l", "r", "t", "b")
            if getattr(_own, k) is not None}
    fig.update_layout(**{k: v for k, v in CHART.items()})
    if _set:
        fig.update_layout(margin=_set)
    _cap_titles(fig)
    if height:
        fig.update_layout(height=height)
    cfg = {"displayModeBar": False}
    if zoom:
        cfg = {"displayModeBar": True, "displaylogo": False,
               "doubleClick": "reset",
               "modeBarButtonsToRemove": [
                   "select2d", "lasso2d", "autoScale2d",
                   "toggleSpikelines", "hoverClosestCartesian",
                   "hoverCompareCartesian"]}
    # c-219: `select` returns the click event so a caller can
    # react to which bar was picked. Plotly hover labels are
    # SVG and cannot hold a working link, so click-then-link is
    # the only way to get from a bar to its source document.
    if select:
        return st.plotly_chart(fig, use_container_width=True,
                               config=cfg, on_select="rerun",
                               selection_mode="points", key=key)
    st.plotly_chart(fig, use_container_width=True, config=cfg)
    return None


def css():
    st.markdown(CSS, unsafe_allow_html=True)


def status(items, right=None, state="ok"):
    """The masthead line — what am I looking at, is it current."""
    bits = []
    for i, (k, v) in enumerate(items):
        if i:
            bits.append("<span class='sep'>│</span>")
        bits.append(f"{k} <b>{v}</b>")
    if right:
        cls = "warn" if state == "warn" else "ok"
        bits.append(f"<span class='push {cls}'>{right}</span>")
    st.markdown(f"<div class='dstrip'>{''.join(bits)}</div>",
                unsafe_allow_html=True)


def stats(items):
    """Figures separated by rules rather than boxed in cards.

    c-245: an empty list renders NOTHING rather than an empty
    ruled strip. The Taiwan page's step 7 carries no figures,
    and a pair of hairlines with nothing between them reads as
    a rendering fault.
    """
    if not items:
        return
    out = []
    for i in items:
        kind = i.get("kind", "")
        # a long value is a phrase, not a figure — see .dstat.txt
        #
        # c-335, Bill: a RANGE is still a figure. "-0.95 to
        # -0.02x" is 15 characters, tripped this rule, and got
        # the 1rem sans phrase treatment next to two 2rem serif
        # numbers — which is exactly the mismatch he spotted.
        # Passing kind="num" opts out; the guard stays the
        # default because most long values really are phrases.
        if len(str(i["v"])) > 12 and not kind:
            kind = "txt"
        out.append(f"<div class='dstat {kind}'>"
                   f"<div class='k'>{i['k']}</div>"
                   f"<div class='v'>{i['v']}</div>"
                   f"<div class='s'>{i.get('s', '&nbsp;')}</div>"
                   "</div>")
    st.markdown("<div class='dstats'>" + "".join(out) + "</div>",
                unsafe_allow_html=True)


def beats(paras, key, shown=2, detail_label=None):
    """Explanation as a numbered sequence, not a block of text.

    c-247, and it REPLACES c-245's white prose card — see D13.
    Bill asked for the white background at c-245 and it did fix
    the missing divider, but the box itself fought the design:
    this file's own rule is "rules instead of boxes", and D1
    reserves the card for DATA because prose is what PAPER is
    for. Bill again: *"still looks a little awkward and out of
    place… long paragraphs are very prone to make the reader
    disengaged."*

    `shown` beats stay open; the rest go behind one toggle, so
    a step defaults to two short paragraphs instead of six.
    Pass `shown=None` to keep everything open — step 7 is the
    limits of the method, and a limitation behind a click is a
    limitation the reader does not carry (D8).

    KEYED CONTAINERS rather than raw HTML, so Streamlit renders
    the markdown. Raw HTML is why this page had grown a private
    regex for bold and links.
    """
    paras = [p for p in (paras or []) if str(p).strip()]
    if not paras:
        return
    head = paras if shown is None else paras[:shown]
    tail = [] if shown is None else paras[shown:]
    with st.container(key=f"dbeats_{key}"):
        for i, p in enumerate(head):
            with st.container(key=f"dbeat_{key}_{i}"):
                st.markdown(p)
    if tail:
        # c-268: "Rulebook References". The old label was a
        # sentence describing the act of reading, which made
        # the toggle feel like an invitation rather than a
        # place. A reader looking for §2.3.3 scans for the
        # noun.
        with st.expander(detail_label or "Rulebook References"):
            with st.container(key=f"dmore_{key}"):
                for p in tail:
                    st.markdown(p)


def step_break():
    """A hairline between two steps. See `.dbreak` in the CSS."""
    st.markdown("<div class='dbreak'></div>",
                unsafe_allow_html=True)


def sect(n, title, lead="", kind="Section", big=False):
    """A section rule. `n=None` drops the eyebrow.

    c-238: some pages have top-level headings that are not part
    of a numbered sequence — the Taiwan page's two are "The
    call" and "How we predict". They were using a page-local
    1.02rem style, which made them smaller than section
    headings elsewhere on the site for no reason other than
    that they were written before the design system existed.

    c-245: `kind` renames the eyebrow. Bill wanted the Taiwan
    page to use this exact treatment but to say "Step", because
    its seven blocks are a sequence to follow rather than
    sections to browse. That is a word, not a second design —
    so it is a parameter here rather than a copy over there.
    """
    eyebrow = (f"<span class='n'>{kind} {n}</span>"
               if n is not None else "")
    st.markdown(
        f"<div class='dsect{' big' if big else ''}'>{eyebrow}"
        f"<span class='t'>{title}</span>"
        # c-301, Bill: no full stop on a subtitle. Done HERE
        # rather than by editing ~30 call sites, so a section
        # added next month cannot reintroduce one. Only a single
        # trailing period goes — an ellipsis or an abbreviation
        # mid-string is left alone.
        + (f"<span class='l'>{str(lead).rstrip()[:-1]}</span>"
           if lead and str(lead).rstrip().endswith(".")
           and not str(lead).rstrip().endswith("..")
           else f"<span class='l'>{lead}</span>" if lead else "")
        + "</div>", unsafe_allow_html=True)


# c-244: THE BAND UNDER EVERY TABLE WAS STREAMLIT'S, NOT OURS.
#
# Bill, twice: *"there is very weird spacing at the end of
# table."* At c-243 I blamed the white card's own 2px padding,
# removed it, and reported the fix. The band survived, which
# means my explanation was wrong and the second report was the
# same bug, not a new one.
#
# It is Streamlit's markdown theme. In the compiled bundle:
#
#     table: {display:'table', borderCollapse:'collapse',
#             marginBottom: theme.spacing.lg}   // lg = 1rem
#
# Every table Streamlit renders — including raw HTML we inject
# through `unsafe_allow_html` — carries a 16px bottom margin.
# Inside a white card that is 16px of white below the last row,
# and `overflow:hidden` on the card cannot collapse it away
# (an overflow container establishes a BFC, which keeps the
# margin INSIDE). No amount of styling the card would ever have
# fixed it; the margin belongs to the table.
#
# An INLINE style on the table beats an emotion class rule at
# any specificity, so this is where it has to be killed. The
# same string is used by history_explorer._rtable so the two
# implementations cannot drift on it.
#
# The lesson is worth more than the rule: I diagnosed by
# inspecting my own code, and my own code did not contain the
# cause. Reading the framework's stylesheet took one grep.
TABLE_ATTR = ('style="width:100%;border-collapse:collapse;'
              'table-layout:auto;margin:0"')


def table_card(height):
    """The white card's own style string.

    c-244: SPLIT THE OVERFLOW AXES. c-243 appended a shorthand
    `overflow:hidden` AFTER `overflow-y:auto` in the same
    declaration block, and the shorthand resets BOTH axes — so
    every height-limited table silently stopped scrolling. Bill:
    *"the scroll up and down side button is gone."* Section 3
    became a 330px window onto a list you could not move.

    Two properties that fight over one axis must never be
    written as a shorthand plus a longhand in source order.

    c-246: THE CARD CARRIES ITS OWN BOTTOM MARGIN. Bill: *"for
    the tables that are wrapped inside a textbox … leave a
    little extra space between the end of the table and the
    next element."* Right, and the reason it was missing is
    c-244 — killing Streamlit's `table{margin-bottom:1rem}`
    removed the accidental gap along with the band inside the
    card. The gap belongs OUTSIDE the border, so it is set
    here, once, rather than restored on the table where it
    would land back on the white.
    """
    gap = f"margin:0 0 {S4};"
    if height:
        return (f"max-height:{height}px;overflow-x:hidden;"
                f"overflow-y:auto;scrollbar-gutter:stable;{gap}")
    return f"overflow:hidden;{gap}"


def table(d, height=None, first_width=None, note=None):
    """A table where every header sits over its own values.

    c-231: promoted into the design system. `st.dataframe`
    right-aligns numbers under left-aligned headers, so a
    numeric column reads as two columns that happen to overlap,
    and Streamlit exposes no control. history_explorer._rtable
    solved this at c-221 and then kept the solution to itself —
    a second page needing the same fix is the moment a private
    helper should have been shared. That page is unchanged;
    this is where new pages get it from.

    Alignment is decided PER COLUMN and applied to the header
    and the cells together: numbers right, text left.
    """
    import pandas.api.types as pt
    rules = [
        {"selector": "th",
         "props": [("background", "#faf5ef"),
                   ("position", "sticky"), ("top", "0"),
                   ("font-weight", "600")]},
        {"selector": "td, th",
         "props": [("padding", "9px 14px"),
                   ("font-size", "0.9rem"),
                   ("border-bottom", "1px solid #f2ebe2")]},
        # c-243: the LAST row's rule sat above the card's own
        # padding, which read as a stray empty band under the
        # table. The card border already closes the table.
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
    # c-236, DESIGN_DECISIONS D1: white card. The page
    # background is PAPER; a table drawn straight onto it has
    # almost no separation from the prose around it.
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
    st.markdown(f"<div style='{table_card(height)}background:#fff;"
                f"border:1px solid {RULE};border-radius:3px'>"
                f"{sty.hide(axis='index').to_html()}</div>",
                unsafe_allow_html=True)
    if note:
        st.markdown(
            "<div style='font-size:.78rem;color:#a89c92;"
            "line-height:1.6;margin:.35rem 0 0;padding-top:.4rem;"
            f"border-top:1px solid #f2ebe2'>{note}</div>",
            unsafe_allow_html=True)


def caveat(text):
    """A limitation the reader must carry, not a footnote.

    c-231: this page rests on a survivors-only panel for ten of
    twelve markets. A caveat rendered as small grey text below
    a chart is a caveat nobody reads, so it gets its own
    treatment — ruled, amber, at the top of the thing it
    qualifies.
    """
    st.markdown(
        "<div style='border-left:3px solid #b8860b;"
        "background:#fdf8ee;padding:.6rem .9rem;margin:.2rem 0 "
        ".9rem;font-size:.86rem;line-height:1.55;color:#4a4038'>"
        f"{text}</div>", unsafe_allow_html=True)


def rows(items, limit=12, extra=None):
    """A ruled list of movers."""
    html = []
    for r in items[:limit]:
        add = str(r.get("action")).upper() == "ADD"
        k = "add" if add else "del"
        tk = str(r.get("code") or r.get("ticker") or "")
        tk = tk.split(".")[0]
        html.append(
            f"<div class='drow'>"
            f"<span class='dact {k}'>{'Add' if add else 'Del'}"
            f"</span><span class='dnm'>{r.get('security', '')}"
            f"</span><span class='dcode'>{tk}</span>"
            + (f"<span class='dcode'>{extra(r)}</span>"
               if extra else "") + "</div>")
    st.markdown("".join(html), unsafe_allow_html=True)
    if len(items) > limit:
        st.caption(f"+{len(items) - limit} more")
