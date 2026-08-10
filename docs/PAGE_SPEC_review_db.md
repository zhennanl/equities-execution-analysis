# PAGE SPEC — MSCI Index Review Database

Approved once by Bill (c-209). Every autonomous change to
`views/history_explorer.py` is checked against this file. If a
change cannot be justified from this spec, it does not ship —
it goes to `docs/PARKED.md` instead.

---

## 1. READER

Primary: **a CLSA interviewer who is himself a PT trader.**

Both halves matter and they pull in different directions:

- *Interviewer* means the page is evidence of judgement. Sloppy
  numbers, unlabelled caveats and decorative charts cost more
  than a missing feature.
- *PT trader* means it must be genuinely useful, not a demo. He
  already knows what a SAIR is. Anything explaining it to him
  is condescending and wastes the screen.

When the two conflict, **useful to the trader wins** — an
interviewer who is a trader is unimpressed by polish that gets
in his way.

## 2. THE JOB

**Organise every MSCI APAC index review change since 2006 into
something a person can actually read, and surface whatever the
data honestly supports.**

This page is INFORMATIONAL. Explicitly out of scope:

- prediction of any kind (that is the Taiwan page)
- trading-flow or execution analysis (that is the window study)
- anything requiring point-in-time weights or size, which we do
  not have

Bill's framing, verbatim: *"Basically anyone can use MSCI index
review changes and derive these information. But we still want
to organize the data in a neat way, and provide any meaningful
insights we can find."*

So the edge is ORGANISATION, not exclusivity of data. The bar
is: could someone with the same raw file get here faster than
by reading our page? If yes, the page has failed.

## 3. CONTENT, IN PRIORITY ORDER

The order is the spec. Most important first, and "important"
means "answers a question the reader actually has".

1. **Latest review across all 13 markets** — a COMPACT snapshot.
   Bill: *"only a snapshot, that is very easy to read, and
   doesn't take a lot of space."* This is a strip, not a
   section. It answers "what just happened" before any scroll.
2. **Index Review History** — the add/delete history with
   the Feb-2023 regime break drawn on it. Four figures:
   additions median and mean, deletions median and mean.
   The median/mean PAIR is the point — this distribution is
   skewed by the pre-2023 May/Nov rebuilds, so mean above
   median is itself the signal.
3. **Who is in the index right now** — current constituents by
   weight and YEARS IN THE INDEX. (This is what Bill meant by
   "breakdown by company weight" — a CURRENT view, not a
   historical one.) Do not use the word "tenure"; it is HR
   language for a count of years.
4. **Security Lookup** — search a company or ticker; every time MSCI has moved it.
5. **Individual Index Review History** — one review in full: the names this market moved (NAME only, no ticker — that is section 4's job), beside every other APAC market's count.

Seasonality lives INSIDE section 2, with the rest of a market's
history. The all-APAC scoreboard was removed at c-218; its
_scoreboard() is still in the file, unused.

Numbering must be CONTIGUOUS from 1. The Membership time
machine (composition at any past review) is written but never
called; it is parked outside the sequence rather than holding
a number the reader sees skipped.

## 4. VOICE AND DENSITY

**Minimal text.** Bill: *"This particular page should be
informational... let's try to keep text to a minimal."*

- section leads: one line, or none
- no paragraph teaches a concept the reader knows
- method and caveats live in a collapsed block, not in prose
- a number on screen without a source is a defect

**CALM, NOT DENSE — reversed at c-211.**

c-207 pushed this page toward desk density: tight spacing,
flush statistic cells, 22px rows, maximum information per
screen. That came from my Bloomberg/Koyfin reference, Bill
approved the direction in the abstract, and then saw it built:

> *"It feels to me that the website has too much information
> going on... I don't want to present too much information to
> make the user feel overwhelmed. I would rather make each
> section interesting, keep information less dense, and let the
> user scroll down to check for further information."*

So the density argument was right about trading TOOLS and wrong
about THIS page. A blotter is read in glances by someone who
already knows what they are looking for. This page is browsed.
The reader is discovering what is here, and a wall of numbers
reads as work rather than as an invitation.

The rules that follow from that:

- **one idea per section.** A section should be comprehensible
  without the reader holding anything else in mind.
- **space is the instrument.** Generous gaps between sections,
  so each occupies its own visual field and the eye rests
  between them.
- **scrolling is free, crowding is not.** Prefer a taller page
  over a denser one. Nothing needs to be above the fold except
  the first thing.
- **fewer rows visible at once.** Tables scroll; a shorter
  viewport with roomier rows shows the same data and demands
  less.
- **tabular numerals stay.** That was a legibility win, not a
  density one, and it survives the reversal.

CONTENT IS UNCHANGED by this. Bill: *"without changing the
content of the website at this moment."* Nothing is removed,
merged or hidden — only given room.

## 5. FINDINGS

Present data. Do **not** assert findings on the page
autonomously.

When a finding turns up while building, append it to
`docs/CANDIDATE_FINDINGS.md` with its n, method and a one-line
statement. **Bill decides what gets promoted onto the page.**
This is his explicit instruction, and it is also the safer
default: an asserted finding is a claim I would have to defend
in his interview, not mine.

## 6. ACCEPTANCE CHECKS (mechanical)

Run by `tests/test_review_db_page.py` and
`scripts/page_lint.py`. A change is DONE when all pass:

- page renders with zero exceptions for Japan, NewZealand,
  China and Taiwan (the size and ticker-shape extremes)
- section numbering is unique and every expected section
  actually reaches the screen (not just exists in source)
- section order matches section 3 of this spec
- no section lead exceeds 200 characters (voice: minimal)
- every table of numbers uses tabular numerals
- tables sit on a WHITE card, not the page ground (DESIGN_DECISIONS D1)
- section titles are Title Case (D4)
- the market selector offers **All markets** first, which
  aggregates sections 2, 4 and 5. Section 3 REFUSES it rather
  than aggregating — MSCI publishes a separate index per
  country, so a combined constituent list would be a portfolio
  nobody holds (c-240)
- a section heading is rendered by the PAGE, not by a helper,
  so a number can never appear twice in source
- the section-2 chart is HTML, not plotly. Its hover card must
  be a CHILD of the column (so the pointer can enter it), share
  `POP_CSS` with the section-1 strip, list every name, and
  carry MSCI's document link. Plotly's SVG tooltip cannot do
  any of the four — c-235
- every column header shares its column's alignment (numbers
  right, text left) — `_rtable`, never `st.dataframe`, which
  right-aligns values under a left-aligned header
- chart titles are title-cased by `design.chart`, not by hand
- a review is shown to the reader as "May 2010", never as the
  storage code "May10" — `_rlabel` at every display site
- no hardcoded market list — markets come from `markets.py`
- Philippines IS offered here (c-220) — the markets.py
  exclusion is about the forward pipeline, and this page
  makes no predictions. markets.py itself is unchanged
- pytest suite green
- every number rendered traces to `msci_changes_db.pkl` or a
  file in `data/`, never to a literal in the view

## 7. NON-GOALS

Stated so I do not drift into them:

- no prediction, no probability, no recommendation
- no point-in-time weight or size analysis (no data)
- no execution or flow metrics
- no explanation of index-review mechanics
- no new page in the sidebar
