# What else this page could do — ranked

*c-244. Bill: "check whether we can build additional tools,
purely based on historical MSCI index change history, to make
the page more useful for PT traders. Rank the ideas based on
their importance."*

**The constraint is the interesting part.** Everything below
uses `data/msci_changes_db.pkl` alone — 4,403 rows, 13 markets,
81 reviews, Feb-2006 to May-2026, columns `review /
review_type / year / month / market / action / security /
eff_date_est / code / ticker` — plus the membership
reconstruction already built from it. No prices, no volumes, no
flow, no float. Nothing here needs a new data source, a
licence, or an IB session.

**Ranking rule.** Not "how clever" but: *does it change a
number a trader writes down, and is the signal actually there?*
So each Tier A idea is quoted with the measured result, because
an idea that turns out to have no dispersion is not worth a
section however good it sounds.

**What this data can never do, stated once.** Change history is
a record of *which names moved*. It cannot tell you which name
will print violently, how many days of ADV the trade is, or
where the crowding sits — that is Tier 2 and Tier 3, and
`APAC_DATA_GAP_REGISTER.md` already says which markets we can
and cannot reach. Everything below is a **base rate**. Base
rates are what you use before the announcement, when nothing
else exists.

---

## TIER A — build these

### A1. Review-size forecast band — "how big will Aug-26 be?"

The only genuinely **forward-looking** thing derivable from
change history alone, and it answers the question a desk head
asks first: how much risk budget, and how many people, does the
next review need?

Per market and per review month, the historical distribution of
adds and deletes gives a prediction interval weeks before MSCI
announces anything.

| market | reviews | adds med | p10 | p90 | dels med | p90 |
|---|---|---|---|---|---|---|
| China | 73 | 7 | 1 | 37 | 4 | 32 |
| India | 61 | 3 | 1 | 8 | 1 | 4 |
| Korea | 58 | 2 | 1 | 4 | 2 | 5 |
| Japan | 55 | 2 | 1 | 6 | 4 | 15 |
| Taiwan | 55 | 2 | 1 | 6 | 1 | 7 |

The China row is the point: a **1-to-37** add range means the
median tells you almost nothing and the desk should be planning
against the p90, not the middle. That is a different staffing
conversation from Taiwan's 1-to-6.

Split by review month (Feb/Aug semi-annual vs May/Nov
quarterly) — the page already knows the Feb-2023 QCIR regime
break, so the band should be estimated on the post-2023 rule
set with the pre-2023 shown behind it.

**Why #1:** forward-looking, cheap, and the interval is the
honest form of the answer. A single-number forecast from this
data would be false precision.

### A2. Addition survival — "is this add sticky?"

Of every addition with a fully observed horizon, the share
deleted again within N reviews. Right-censoring handled by
only counting additions old enough to have been observed for
the full horizon (n falls from 2,250 to 2,069 as the horizon
lengthens).

| horizon | n | deleted again |
|---|---|---|
| 4 reviews (1y) | 2,250 | **10.1%** |
| 8 reviews (2y) | 2,196 | **21.8%** |
| 12 reviews (3y) | 2,069 | **30.2%** |

And the dispersion across markets at the 2-year horizon is
where the trade is:

| market | n | deleted within 2y |
|---|---|---|
| Hong Kong | 51 | **31.4%** |
| Korea | 145 | 27.6% |
| China | 1,273 | 24.7% |
| Taiwan | 135 | 22.2% |
| Thailand | 52 | 13.5% |
| Australia | 57 | 12.3% |
| Japan | 171 | 10.5% |
| India | 189 | **7.9%** |

**A four-fold spread between Hong Kong and India.** One in
three Hong Kong additions is gone inside two years; one in
thirteen Indian ones. That is a real difference in how long a
desk should expect an index-driven position to stay index-
driven, and it is measurable from names and dates alone.

### A3. Deletion recidivism — "will this one come back?"

**336 of 2,005 deletions (16.8%) were later re-added.** Median
gap **9 reviews**, quartiles 5 and 20. Only **3.7%** come back
within a year.

That shape is the finding. The revolving door is real but
**slow**, which is exactly the input a borrow or inventory
decision needs: a re-entry is likely enough to keep the name on
a watchlist and far enough away that carrying a position for it
is not the trade.

Deliverable: per market, a re-entry curve plus the named list
of repeat travellers, hung off the existing Security Lookup so
it costs no new page furniture.

**Accuracy limit, and it is the binding one.** A2 and A3 both
rest on matching a security to itself across twenty years of
name changes. The rename work at c-202 and the collision guard
in `_roster` are what make this possible at all, and
`NAME_COLLISIONS.md` is the register of where it is still
imperfect. Any published curve must say that identity
resolution, not sample size, is its error bar.

### A4. APAC concurrency calendar — the region-wide load

A program desk does not trade one market on review night, it
trades the region. The binding constraint is the **total**
basket on that close, and nothing on the page currently shows
it.

Names effective on a single date, all markets pooled: median
**40**, p90 **127**, max **346**.

| effective date | names | markets |
|---|---|---|
| 2018-05-31 | **346** | 11 |
| 2019-11-29 | 273 | 13 |
| 2008-05-30 | 209 | 13 |
| 2020-11-30 | 175 | 12 |
| 2020-05-29 | 169 | 13 |

The 2018 spike is the China A-share inclusion — an eight-fold
day against the median. A desk that plans against "a typical
review" plans against 40 names and is wrong by a factor of
nine roughly once a decade, always on the night that matters.

Cheap to build, operationally direct, and I have not seen it
anywhere else.

---

## TIER B — worth building, second pass

### B1. Off-cycle event base rates

`review_type` is in the database and unused by the page: 787
QIR rows against 3,616 SAIR. Off-cycle changes — fast-entry
IPOs, M&A deletions — are the ones that surprise a desk because
they arrive without the review calendar's notice. Frequency per
market per year, and the notice period implied by
`eff_date_est`, turn "we got surprised" into a budgeted
expectation.

### B2. Net imbalance per review

2,398 adds against 2,005 deletes overall, but the per-review
imbalance is what sets the desk's net exposure and funding on
the night. Historical distribution of (adds − deletes) per
market per review, with the tails named.

### B3. Market turnover league table

Annualised one-way turnover — changes divided by constituent
count, which the membership reconstruction already provides.
Ranks markets by how much index business each actually
generates, rather than by index size. A resourcing and client-
marketing number more than a trading one, which is why it sits
in Tier B.

---

## TIER C — colour, not decisions

### C1. Cluster / regime flags

Reviews whose size sits above the market's own p90, labelled
with what was happening (2008, the 2018 and 2019 A-share
inclusions, the 2023 QCIR change). Gives a current print its
historical company. Context for a reader, not an input to a
trade.

### C2. Longevity leaderboard

Longest continuously held members and the never-moved list.
Good client-deck material, no trading value, and it inherits
the Time Machine's standing caveat that a 2006 member's tenure
is a **minimum** rather than a measurement.

### C3. Cross-market co-movement of review size

Whether a heavy China review coincides with a heavy Korea one.
Testable here, but with 81 reviews and the A-share inclusions
dominating the variance, any correlation would mostly be
describing 2018 and 2019. Registered so it is not proposed
again, not recommended.

---

## Deliberately not proposed

- **Sector or industry rotation.** The database has no sector
  column and adding one means an external mapping per market,
  point-in-time. That is a data project, not a page idea.
- **Anything predicting WHICH name moves next.** That is the
  Taiwan MIEU screen chain and it needs float, cap and ATVR —
  the whole reason `walkthrough.py` exists as a separate page
  for one market.
- **Add/delete P&L or drift.** Needs prices. It is the APAC
  panel, already built, and it belongs on that page.

---

*Every figure above was computed from
`data/msci_changes_db.pkl` at c-244 and is reproducible; none
is typed by hand. Per D9, none of it is asserted as a finding
on a page until Bill promotes it.*
