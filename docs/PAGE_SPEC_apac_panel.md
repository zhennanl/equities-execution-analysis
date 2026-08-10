# PAGE SPEC — APAC Rebalance Panel (interactive)

*c-275. Same contract as the other page specs: every autonomous
change to `views/apac_panel.py` is checked against this file. A
change that cannot be justified from here does not ship.*

---

## 1. WHY THERE ARE TWO PANEL PAGES

`views/apac_strategist.py` is frozen and stays on the site as
**APAC Rebalance Panel (v1)**. It is the version Bill reviewed.

It was duplicated before this redesign for a specific reason:
the pre-c-274 panel files were untracked, edited in place, and
recovered only by reverse-applying a session's worth of diffs.
A copy costs nothing and that recovery cost an hour.

The two pages are allowed to differ. Where they do, this file
says why.

## 2. READER

A CLSA PT trader with a review coming, who covers more than one
market and wants to interrogate the panel rather than read a
fixed cut of it. He knows what a rebalance is.

## 3. THE ARCHITECTURE INVERTS FROM v1

v1's rule was **the page computes nothing** — it renders
pre-aggregated cells from `index_strategist_qa.py`, with a test
forbidding it from importing `statistics` or calling
`median(`.

That rule cannot survive a user-defined percentile. Nothing
precomputes *the 37th percentile of Korean deletions between
Feb-2019 and Aug-2023*; it is a cross-product with a free
parameter in it.

So:

| | v1 | interactive |
|---|---|---|
| reads | `index_strategist_qa.json` (cells) | `apac_panel_events.json` (rows) |
| computes | nothing | its own filters and quantiles |
| generator | `index_strategist_qa.py` | `apac_panel_events.py` |

`apac_panel_events.py` imports `metrics()` from the v1
generator rather than reimplementing it. **Neither page may
define its own event metric.** That is the line that keeps them
honest: they summarise differently, they never measure
differently.

## 4. THE PERCENTILE DIVERGENCE — KNOWN, AND DELIBERATE

The repo holds two percentile definitions:

- `index_strategist_qa._pct` — **nearest-rank**,
  `int(round(p * (n-1)))`
- `rebalance_analysis._pct` — **linear interpolation**

They agree only when `p*(n-1)` is a whole number. On this
panel's own p90 cells they part by up to **2.30pp** — Singapore
additions read 2.18% nearest-rank against 4.48% interpolated,
on n=6.

**This page uses interpolation**, matching the Taiwan engine and
matching what a reader typing "37th percentile" into a box
expects. v1 keeps nearest-rank and is not edited to match, so
the two pages can legitimately show different p90s on a thin
cell. Pinned by `test_the_median_matches_the_taiwan_engine`.

Small samples are where this bites, and this page is precisely
the one that lets a reader narrow to a small sample. If it ever
starts confusing people, the fix is a note on screen, not a
silent change of definition.

## 5. THREE CONTROLS ON EVERY CHART

Per chart, not one shared bar. A reader comparing Taiwan's
print size against Korea's reversion should not lose the first
chart to set up the second.

1. **Market** — defaults to **Taiwan**, with **All Markets**
   leading the list. Not pooled by default: pooling puts
   China's 1,275 events against New Zealand's 13 and calls the
   result "APAC" when it is a chart of China.
2. **Reviews** — a range slider over review tags, defaulting
   **Feb-2015 to May-2026**. The raw feed runs to 2010 for some
   markets; that is real data, thinner and under different
   rules.
3. **Statistic** — per section, not global. Median and Mean
   everywhere a distribution is drawn; **90th percentile on
   effective-day risk alone**, on by default.

   That is the statistic finding its one home rather than
   indecision. On print size the tail is a distraction; on the
   move carried into the close it is the number quoted to a
   client, because the median is the day you plan for and the
   90th is the day that breaks the schedule. A tail nobody
   switches on is a tail nobody sees, hence the default.

**The x-axis follows the market control.** One market plots
against review (a time series); All Markets plots against
market (a cross-section). The question changes with the
selection, so the axis does.

Defaults are tested, because a default is what most readers
will ever see.

## 6. AESTHETICS ARE INHERITED, NOT REINVENTED

From `views/design.py` and the Index Review Database page:

- `design.sect()` for every section rule and divider
- `design.chart()` for every plotly figure — it applies the
  Inter/warm-palette theme and title-cases axis labels
- `design.caveat()`, `design.stats()`, `design.table()`,
  `design.status()`
Every chart goes through `design.chart()`, so a figure cannot
opt out of the site's palette or type scale by accident.

## 7. SECTIONS

Page title: **Index Rebalance — Daily Data Analysis**, set with
`st.markdown("# ...")` as on the Review Database page.

Six, numbered contiguously:

1. **The rebalance window** — cumulative return from the
   announcement close, one line per event with the aggregate
   over the top, split by side
2. **What this panel covers** — the dataset, in two sentences
3. **How big is the print** — T-multiple, dots
4. **Volume around the effective date** — volume as a multiple
   of ADV, aligned on the EFFECTIVE date, not the announcement
5. **How many reviews trade above normal liquidity** — the
   share CLEARING a threshold the reader sets
6. **Effective-day risk** — |effective-day move| by side

### CHART TYPE FOR A DISCONTINUOUS SERIES (c-285)

Section 5 is quarterly: the series exists four times a year and
nowhere in between. **Bars, with the width pinned to the
sampling interval.**

A line is wrong here. It draws a segment between two reviews
and so asserts a value for every day between them, when no such
value was ever measured. Bars carry the opposite claim — this
value belongs to THIS interval and nowhere else.

The width must be set EXPLICITLY on a numeric time axis
(`width = 0.22` of a year, against a 0.25 quarter). Plotly
sizes bars from the smallest gap it can find, so a single
missing review would make every bar on the chart narrower.
Pinned, a bar always occupies its own quarter and a review the
panel lacks shows as white space rather than being closed up.

The same reasoning is why sections 1 and 4 ARE lines: they are
indexed on consecutive trading sessions, so the value between
two points is real and a segment is an honest claim about it.

### WHAT WAS REMOVED, AND WHAT SURVIVED IT (c-285)

Days to Trade and Direction Hit Rate are gone. `sessions_to_
fill` and `censored_median` stay on the module with their
tests: the right-censoring argument they encode — that dropping
unfilled orders and taking the median of the rest always
flatters — is the most reusable thing this page produced. A
helper with a passing test is not dead weight; an unreferenced
200-line section would have been.

c-279 deleted the old pop-vs-drift and schedule-cost tables;
c-280 deleted the closing "what this page cannot tell you"
block and added section 1.

**Section 1 is the Announcement → Effective page's first chart,
rebuilt on all APAC data.** That page draws one line per event,
which works for a dozen Taiwan names and not for 2,175. So it
aggregates: median or mean cumulative return per session
offset, per side.

**Day 0 is the announcement close and reads exactly zero.** It
is the last price set with nobody knowing — MSCI publishes from
Geneva before the Asian open. Anchoring one session later would
fold the jump into the baseline and flatten the move the chart
exists to show. Verified two ways: day 0 is zero by
construction, and day 1 of the path equals the independently
computed `gap1` median to the storage rounding (2.1e-4pp on
Taiwan, both sides).

**An offset below `MIN_N_AT_OFFSET` = 5 events is left blank.**
Windows are ragged at the right — all 2,175 events reach day
+20, only 1,771 reach day +40 — so without a floor the line
keeps going and quietly becomes the median of whichever markets
have the longest windows.

**Section 3 states the positive.** The share that CLEARS the
threshold, not the share that fails it — same data, but "94%
traded at or above 2x ADV" is a capacity statement a desk can
act on where "6% printed under 2x" is a statement about what
did not happen.

**One chart grammar.** Every chart is dots: a marker per group
per statistic, each statistic its own colour, dash and symbol.
Section 2 used to be an HTML bar chart carrying the Review
Database's hover card; c-279 dropped it for consistency, and
the per-name detail went with it. That trade is recorded, not
hidden — `_bar_pop` and `POP_CSS` are deleted rather than left
defined-but-unused, because unreferenced code is not an asset
in reserve.

Section 5 is not an afterthought. It keeps the other four
honest and does not move into an expander.

## 8. COPY

Plain and short. State the point and stop.

Specifically avoided: em-dash appositive chains, "this is not X
but Y", triads for their own sake, restating what the chart
already shows, and preambles that delay the number. A caption
that survives being cut in half should have been half as long.

## 9. EMPTY SELECTIONS ARE A FIRST-CLASS STATE

A reader can pick New Zealand and a two-review range. That is
four events or none, and it must say so rather than crash or
draw an empty axis as though it meant zero. Tested.
