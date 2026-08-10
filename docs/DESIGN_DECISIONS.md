# Design decisions — Bill's standing choices

*The durable memory for how this site looks. A preference
recorded in a chat is gone next session; a preference recorded
here governs every page and can be pointed at in review. New
pages inherit from this file, not from whichever page was
copied.*

---

## D1 — Tables sit on WHITE, not on the page background (c-236)

**Bill, c-236:** *"I like the white background for this chart,
which adds to the contrast of the table and makes the content
more visible… Find a way to apply the same design for other
tables in this page. Apply the same design to 'Predict MSCI
Index Changes — Taiwan' and rest of pages."*

The page background is `PAPER #fdfaf6`. A table rendered
directly onto it has almost no separation from the surrounding
prose — the effect Bill noticed is that tables INSIDE a
Streamlit expander get a white backing and read considerably
better.

So every data table gets a white card: `background:#fff`, a
`1px solid #e8ddd1` border, small radius, and the header band
in `#faf5ef` so the header still separates from the body.

**Scope, in order:**

1. **DONE (c-236)** — MSCI Index Review Database
   (`views/history_explorer.py`, via `_rtable`) and any page
   using `design.table`.
2. **DONE (c-245)** — Predict MSCI Index Changes
   (`views/walkthrough.py`). Extended there from tables to
   PROSE — see D13.
3. **TODO** — every other page. `page1_simulator`,
   `page4_quarterly_review`, `page6_lifecycle`,
   `event_window_study`, `findings`, `reconstruction`,
   `aug26_review`.

Items 2 and 3 are deliberately deferred: Bill asked for the
review-database page now and the rest later. They are written
down so "later" has an address.

**The mechanism matters as much as the rule.** `design.table()`
is the single place this lives for new pages;
`history_explorer._rtable` is the older private copy and should
eventually call it. Two implementations of one design decision
is how a design decision stops being one.

---

## D2 — Hover cards are HTML, never plotly tooltips (c-235)

Any card a reader might want to READ — rather than glance at —
must be an HTML element that is a CHILD of the thing it
describes. Plotly's hover is an SVG label: it tracks the
cursor, cannot be entered, and an `<a href>` inside it renders
as literal characters.

This cost the section-2 chart its plotly implementation
entirely, after three revisions of trying to satisfy the
requirement inside the library (c-219, c-221, c-234). The rule
that came out of it: **if a card needs to be entered, styled,
complete, or linked, it is not a tooltip.**

One stylesheet, `history_explorer.POP_CSS`, so the cards cannot
drift apart.

**c-242 AMENDMENT — POP_CSS carries APPEARANCE ONLY.** How a
card OPENS belongs to its host, because each host anchors it
differently: the strip below its cell, the chart at its zero
line, the seasonality bars below theirs. When c-236 replaced
section 1's hand-written block with POP_CSS it took the
appearance rules and deleted the behaviour rules interleaved
with them, leaving the card `display:none` with nothing to turn
it on — section 1's hover was dead for six revisions.

Every host must supply its own `X:hover .pop{display:block}`
and its own position. Tested per host, because a global CSS
string search passes as long as ANY host supplies the rule.

**Sharing a stylesheet is only safe if you can say which half
you shared.**

---

## D3 — Calm, not dense (c-211, reversed from c-207)

**Bill:** *"It feels to me that the website has too much
information going on… I would rather make each section
interesting, keep information less dense, and let the user
scroll down to check for further information."*

- one idea per section
- generous space between sections
- scrolling is free, crowding is not
- tabular numerals stay (a legibility win, not a density one)

## D4 — Title Case for chart and section titles (c-221)

Applied centrally in `design.chart()` so it cannot drift.
Acronyms and unit abbreviations are preserved (`USD`, `×ADV`,
`bps`, `(log)`); minor words stay lower unless they lead.

## D5 — Every table header shares its column's alignment (c-221)

Numbers right, text left, header matching its own values.
`st.dataframe` right-aligns numbers under left-aligned headers,
which reads as two columns that happen to overlap.

## D6 — Full country names, never storage keys (c-214)

`HongKong` and `NewZealand` are keys that join to `markets.py`
and the data files. The reader sees `Hong Kong` and
`New Zealand`. Handled by `_pretty` / `format_func`, never by
renaming the key.

## D7 — A review is shown as "May 2010", never "May10" (c-221)

`_rlabel` at every display site. The compact code stays in
storage because MSCI's PDF filenames are built from it.

## D8 — Caveats get the amber block, not grey text (c-231)

A limitation the reader must carry is not a footnote.
`design.caveat()` — ruled, amber, above the thing it qualifies.
Survivorship, missing market adjustment and non-independence
all qualify.

## D10 — Top-level headings use `design.sect`, numbered or not (c-238)

`design.sect(n, title, lead)` takes `n=None` and drops the
eyebrow. Before this, pages written earlier than the design
system carried their own heading styles — the Taiwan page's two
top-level headings were 1.02rem against the site's 1.5rem, for
no reason except that they predated it.

The lead goes INSIDE the section rule, where there is already a
slot for it, rather than below as a separate `st.caption` line.

## D11 — A block owns stacked ZONES; nothing crosses them (c-239)

**Bill, c-239:** *"the 2023 Quarterly review label collides
with the addition and deletion legends. There are many examples
of such problems throughout this page… think about a high-level
solution that addresses the design problems systematically."*

He is right that these were symptoms. The cause was that I
positioned each new element by eye, absolutely, into whatever
vertical space looked free — so the legend (normal flow, above
the chart) and the regime label (absolute, `top:-1.45rem`)
claimed the same 24 pixels and neither knew about the other.

**The contract:**

1. A chart block is three stacked zones in NORMAL FLOW —
   annotations, plot, axis/legend. Each has a reserved height.
2. An absolutely positioned element may move only
   HORIZONTALLY, and only within its own zone. It may never
   reach into a neighbour's space.
3. A colour bar or legend gets its own reserved strip
   (`margin.b` in plotly terms), never a negative offset over
   the plot.
4. Scrolling containers set `scrollbar-gutter:stable`, so the
   content box does not move depending on whether a scrollbar
   appeared. This was Bill's "the whitespace makes the table
   asymmetrical".
5. **`design.chart()` sets defaults, it does not overrule.** It
   was applying the theme's margin AFTER the caller's, so a
   figure reserving 54px for its colour bar silently got 8px
   back. A caller knows things about its figure that a
   site-wide default cannot.

## D12 — The framework styles our HTML too (c-244)

**Bill, twice:** *"there is very weird spacing at the end of
table."* At c-243 I blamed the white card's 2px padding,
removed it, and reported it fixed. The band survived, so the
second report was the same bug — my explanation had been wrong.

The cause was never in this repository. Streamlit's markdown
theme sets, in its compiled bundle:

```
table: {display:'table', borderCollapse:'collapse',
        marginBottom: theme.spacing.lg}      // lg = 1rem
```

and that applies to raw HTML injected through
`unsafe_allow_html`, not just to markdown tables. Every table
on the site carried a 16px bottom margin. `overflow:hidden` on
the card could not remove it — an overflow container
establishes a block formatting context, which keeps the margin
*inside*.

**Two rules come out of this:**

1. **When a symptom is not explained by our own CSS, read the
   framework's.** One `grep` through
   `streamlit/static/static/js` found the declaration. I spent
   c-243 inspecting only code I had written, which is the one
   place the cause could not be.
2. **An inline style is the only thing that reliably beats an
   emotion class.** `design.TABLE_ATTR` carries `margin:0` on
   the table element itself, and `history_explorer._rtable`
   imports the same constant so the two cannot drift.

**D11.6 — a shorthand and a longhand must never fight over one
axis in source order.** c-243 also appended `overflow:hidden`
after `overflow-y:auto` in the same declaration block. The
shorthand resets both axes, so every height-limited table
stopped scrolling — Bill: *"the scroll up and down side button
is gone."* Section 3 became a 330px window onto a list nobody
could move. `design.table_card(height)` now emits
`overflow-x:hidden; overflow-y:auto` explicitly, and the test
asserts the RESOLVED value rather than the presence of a
string, because both strings were present while the behaviour
was broken.

---

## D13 — Explanation gets the white card too, and a figure row must close (c-245)

**Bill:** *"when we are explaining what we do, like here in
section 1 what the review decides, let's add a white background
to these text to make the content more readable. Especially
when we have header status bar like `Companies in the index /
77` … and there isn't any divider between this header and the
text box below."*

Two symptoms, one cause. D1 gave tables a white card because
PAPER offers a table almost no separation; the same is true of
a block of explanation, and it is worst directly under a figure
row, where the row's own hairline was the only boundary and the
eye ran straight through it into the prose.

1. ~~**`design.prose(key)`** — a white card for explanatory
   text.~~ **REVERSED at c-247 — see D14.** The card fixed the
   divider but was the wrong instrument for prose.
2. **`design.stats` is the only figure row.** The Taiwan steps
   used `st.columns` + `st.metric`, which is the one figure
   treatment on this site with no rule above or below it. Every
   figure block on the page now uses `design.stats`, which
   closes with a hairline and carries its own bottom margin —
   so the divider Bill was missing arrives on all seven steps
   at once rather than being drawn in seven places.
3. `stats([])` renders **nothing**. Step 7 has no figures, and
   two hairlines with nothing between them read as a fault.
4. A value longer than 12 characters drops to prose size
   (`.dstat.txt`). "each name's own daily history" is a
   legitimate value and at 2rem serif it dwarfed the numbers
   beside it.

**And the eyebrow is a parameter, not a page.** Bill asked the
Taiwan page to use this exact treatment while calling its
blocks **Step** rather than **Section**, because seven blocks
in sequence are followed, not browsed. `design.sect(kind=...)`
takes the word. The page-local stylesheet that held
`.steptitle`, `.stepnum`, `.lead` and `.sect` is deleted — it
was a second, smaller heading system, and it is why c-238 could
raise this page's two top-level headings and leave its seven
step headings behind at 1.02rem.

**A step now has a fixed order:** step rule (with the step's
own first line as the lead) → figure row → white prose card →
anything interactive. Before, the lead sat *below* the figures,
so every step opened with numbers the reader had not yet been
told the meaning of.

**Testing note.** This page had six tests and not one of them
drew it — every assertion ran against `story()`, the data. The
page could have raised on load and the suite would have stayed
green. It now has a render fixture, and the first thing that
fixture caught was a stray `st.metric` in the step-5 lever.

---

## D14 — Explanation is a SEQUENCE of beats, never a box (c-247)

**This reverses half of D13, two revisions after I wrote it.**

**Bill, c-245:** *"add a white background to these text to make
the content more readable."* I did, and it fixed the real
problem underneath (D13.2 — the missing divider).

**Bill, c-247:** *"it is better visually than previous
versions, but still looks a little awkward and out of place…
long paragraphs are very prone to make the reader
disengaged."*

He is right, and the reason was written in `design.py`'s own
header before I started: **"rules instead of boxes."** D1
reserves the white card for DATA precisely because a table has
no natural edge on PAPER — prose does not need one, because
prose is what the paper ground is FOR. A box around a
paragraph announces a container when what a method needs is a
sequence.

**The beat.** One paragraph, one idea, numbered in the margin
in mono, sharing one left rule. The number is a **CSS
counter**, so a step that gains or loses a paragraph
renumbers itself.

**Two beats open, the rest behind one toggle.** A step
defaults to two short paragraphs rather than six. This is the
interactivity that pays on a page read top to bottom — detail
on demand — rather than tabs, which hide content behind clicks
and would have been lost by the HTML export.

**Step 7 is the exception and it is not negotiable.** It is
the limits of the method. Per D8, a limitation the reader must
carry is not a footnote — so it is certainly not a click.
`beats(shown=None)`, and a test asserts it.

**What survives from D13:** `design.stats` as the only figure
row, `stats([])` rendering nothing, long values dropping to
prose size, and `sect(kind=...)` for the "Step" eyebrow. Those
were about the divider and the hierarchy, and they were right.

**The lesson.** I reached for the mechanism that had just
worked on a different problem instead of asking what prose
needs. When a fix looks out of place, check the design
system's own stated rules before inventing a new treatment —
this one had already answered the question.

## D15 — A PART heading sits above a section (c-247)

`design.sect(..., big=True)` — 1.9rem, between the page title
(2.1rem) and a section (1.5rem). The Taiwan page has two, "The
Call" and "How We Predict Index Review Changes", and they open
halves of the page rather than items in a list.

**Both take it, or neither.** Bill asked for one of them to be
enlarged; enlarging only that one would have re-created
exactly the false hierarchy c-238 removed, where two peer
headings were different sizes for no reason.

---

## D9 — Findings are not asserted on a page (standing)

Data and method on the page; candidate findings to
`docs/CANDIDATE_FINDINGS.md` for Bill to promote. An asserted
finding is a claim he has to defend, not me.
