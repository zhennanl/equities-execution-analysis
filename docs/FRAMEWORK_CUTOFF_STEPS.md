# The Cutoff Framework — Steps 0-6, Sources, Assumptions, and the Q&A (c-88/c-90)

*The written record of views/framework_cutoff.py — ONE template
rendered for all 13 APAC markets. Every number carries a tag:
FACT (from a document/file), RULE (GIMI, section cited),
DERIVED (arithmetic on tagged inputs), ASSUMPTION (our choice,
highlighted and banded), LIMIT (known data limitation), OPEN
(not built for that market — never borrowed). The user's
questions about the framework are recorded at the bottom and
mirrored in INDEX_REVIEW_EXPLAINED_QA.md.*

## Step 0 — the event and its THREE data dates

- Announcement 2026-08-12 (Asia time); effective at the close
  of 2026-08-31. FACT — MSCI review calendar.
- **The rulebook defines three distinct cutoff dates** (the
  precision found by the user's Step-0 question, Q56 —
  CITATIONS UPDATED c-91 to the CURRENT May-2026 edition,
  which restructured the section: one §3.1.9 "Date of Data
  Used for Index Reviews" p.48 now covers all four reviews;
  the old Dec-2022 SAIR/QIR split — §3.1.9/§3.2.6 — is gone,
  and §3.2.6 is now "Early Deletions"):
  - **Price Cutoff Date** — "any one of the last 10 business
    days of January for the February Index Review, of April
    for the May Index Review, of July for the August Index
    Review and of October for the November Index Review"
    (GIMI May-2026 **§3.1.9** p.48). Governs cap prices, FIF
    updates, foreign room, AND NOS updates. MSCI picks ONE
    day, never says which — THE forecaster assumption.
    Footnote 28: the window PREPONES if the effective date
    falls inside the announcement month. Business day defined
    as >80% of ACWI float open (fn 29).
  - **Liquidity Cutoff Date** — deterministic: last business
    day of Dec/Mar/**June**/Sep per review. For Aug-2026:
    **2026-06-30** — our ATVR inputs can align exactly.
  - **Equity Universe Cutoff Date** — deterministic: last
    business day of Nov/Feb/**May**/Aug per review. For
    Aug-2026: **2026-05-29**.
  - **Post-cutoff discretion (now rulebook text):** §3.1.9's
    closing paragraph — extraordinary events between the
    price cutoff and the announcement (fraud allegations,
    takeover bids, suspensions) let MSCI veto a migration.
    The discretion LIMIT, with its trigger list, cited.
- Both editions archived: data/msci_archive/
  MSCI_GIMIMethodology_May2026.pdf (CURRENT — cite this) and
  _Dec2022.pdf (superseded; kept for era work).

## Step 1 — global size reference → corridor

- $15.75B published DM reference. FACT — GIMI worked example
  §2.3.2.1 p.25 (May-2026 edition).
- × 1.042 scaling to this review's prices. ASSUMPTION — proxy
  = broad-DM 3-month move from the factsheet performance
  table; MSCI actually re-runs the DM walk at their price
  date; declared band ±2pts.
- DM forecast $16.41B. DERIVED.
- EM reference = one-half DM = $8.21B. RULE — §2.3.2.1.
- Corridor = 0.5-1.15x the reference. RULE — §2.3.2. EM:
  [$4.10B, $9.44B]; DM: [$8.21B, $18.87B].

## Step 2 — the market's free-float denominator (two frames)

- **Frame A (every market):** index float cap from the MSCI
  country factsheet (FACT — captured monthly in
  data/apac_factsheet_archive.json because MSCI overwrites the
  URL; TW Jul-31: $3,183B) ÷ 0.85 (RULE §2.3.1) = implied
  denominator (TW: $3,745B). ASSUMPTION: index sits exactly at
  85% — banding (80-90%) makes this a ±6% band.
- **Frame B (census, TW only so far):** 2,146-name universe
  (FACT — FinMind TaiwanStockInfo), GIMI screens (float ≥
  0.15, ATVR ≥ 15% — RULES §3.1.2; minimum size ~$0.2B —
  ASSUMPTION), tiered floats (top-10 in-frame implied FIFs >
  member v2 named-insider err 0.022 > default 0.55 swept
  [0.40, 0.70] — ASSUMPTIONS, default share printed), FX 29.5
  — ASSUMPTION. Result $3,883B; agreement +3.7% = inside the
  banding allowance. LIMIT: census coverage partial until the
  harvest completes.
- Other markets: OPEN with the activation path (Korea → India
  → Japan → China per GMSR_MULTIMARKET_DESIGN.md; AU/HK/MY
  honestly capped at Frame A).

## Steps 3-4 — the walk and the corridor check

- Bases (RULES, the Q46 correction): RANK by full company cap
  descending; ACCUMULATE free-float value; stop at 85% of the
  float total; EXPRESS the cutoff as the crossing company's
  FULL cap.
- TW crossing: rank ~53 at $12.95B (DERIVED,
  data/cutoff_walk_v2.json), stable across the default-float
  band ($9.7-15.6B).
- Corridor check: crossing ABOVE the $9.44B ceiling in every
  frame → **the corridor BINDS** — effective cutoff = the
  corridor edge; coverage flexes above 85% (allowed). This is
  concentration speaking; whether another market clamps or
  crosses inside its corridor is unknown until its census
  runs (rendered as a LIMIT for the other 12).

## Step 5 — the trading frontiers

- Existing-member floor = 2/3 × cutoff (RULE §3.1.5.1 buffer
  zones). TW: $6.29B.
- New-add bar = 1.5 × cutoff (RULE §3.1.5.1) + side gates:
  float ≥ 0.15, float-cap half-bar (§3.1.2.3), ATVR
  (§3.1.2.4), foreign room ≥ 15% (§3.1.2.6). TW: $14.16B.

## Step 6 — the shortlist

- TW delete pool = members under the floor (live-ladder caps,
  data/aug26_cutoff_calc.json): 6919 4.94, 2834 5.44, 2609
  5.46, 1101 5.63, 3529 5.69, 5871 5.87, ...
- TW add candidates vs the bar + gates: 2408 QUALIFIES
  (shadow call STRONG, declared T-6, survives three frames),
  8046/2344 qualify frame-sensitively, 6505 BLOCKED (float).
- LIMIT: discretion + the unseen price date + the fresh
  reference recalc make every shortlist probabilistic —
  graded on announcement, misses ship.

## The template contract (for the user's edits)

Edit the step functions in views/framework_cutoff.py — all 13
markets inherit automatically. Market facts assemble from
agents/market_profiles.py + data/apac_factsheet_archive.json;
sparse extras in MARKET_OVERRIDES. Missing artifacts render
OPEN — numbers are never borrowed across markets.

---

## Q&A record (framework questions)

**Q (2026-08-06): What does "MSCI snaps any of the last 10
business days" actually mean, and where does the rulebook say
it?**

A: It is the **Price Cutoff Date** provision. GIMI Dec-2022
edition, §3.2.6 "Date of Data Used for Quarterly Index
Reviews" (p.66): *"Price Cutoff Date: any one of the last 10
business days of January for the February QIR and of July for
the August QIR"* — governing the prices used for market
capitalization, FIF updates, and foreign-room changes. The
SAIR analog is §3.1.9 (p.54): last 10 business days of April/
October. Two further precisions the question surfaced: (1)
MSCI selects ONE date from that window and never discloses
which — that single unannounced choice is the irreducible
input assumption for any outside forecaster (a ~2-week price
window on a concentrated market can move a borderline name
across the line); (2) the OTHER two data dates are
deterministic and knowable — the Liquidity Cutoff (last
business day of March/September; ATVR data) and the Equity
Universe Cutoff (last business day of February/August) — so
our ATVR and universe inputs can be aligned to MSCI's exact
dates even though the price date cannot. The rulebook PDF is
now archived at data/msci_archive/MSCI_GIMIMethodology_
Dec2022.pdf. (Recorded as Q56 in the QA doc.)

**Q (2026-08-06): Explain each of the three cutoff dates and
how each maps to our market analysis.**

A: Three exposures, not one photograph. (1) **Equity Universe
Cutoff** (Aug-2026: 2026-05-29) freezes WHO can be considered
(§2.1 universe + the §3.1.2.2 minimum-size data): post-May
listings cannot enter this review (an automatic add-candidate
disqualifier); the ~$0.2B floor is computed on May data;
deterministic -> alignable exactly. (2) **Liquidity Cutoff**
(2026-06-30) freezes the ATVR/frequency windows: exact
replication means 12m/3m windows ENDING 6/30 — an actionable
census correction (we use latest-12m today); July volume
surges earn no credit this review. (3) **Price Cutoff** (one
undisclosed day in the last 10 business days of July) freezes
caps/FIFs/foreign room/NOS — the only stochastic date, and it
maps onto frame-robustness: the honest cutline verdict holds
on EVERY candidate day (a formal 10-day ladder sweep is the
upgrade of our blind band); fn 29 (>80% ACWI float open)
defines how the 10 days are counted. (Q57 in the QA doc.)

**Q (2026-08-06): Step 1 term by term — what is $15.75B, why
x1.042 and the ±2pt band, why EM = half, where is the corridor
defined and what does it represent?**

A: **$15.75B** = the Global Minimum Size Reference for DM: MSCI
aggregates the whole developed-markets investable universe,
ranks by full cap, walks cumulative FREE-FLOAT coverage to 85%
— the full cap of the crossing company is the reference
(May-2026 worked example, §2.3.2.1). A global yardstick, not a
Taiwan number. **x1.042**: MSCI recomputes the reference each
review at the new Price Cutoff Date by re-running the DM walk;
we cannot, so we scale the published value by the broad-DM
move between the two price windows (+4.2%, factsheet
performance table). **±2pts** = the proxy's honesty tax: the
marginal company ≠ the average index; the unknown price day;
composition churn. **EM = half** (§2.3.2.1): a fixed
methodological ratio — holding EM to DM scale would gut EM
coverage; half preserves comparability while acknowledging
depth; Taiwan is EM by MSCI classification, so its reference
is 16.41/2 = $8.21B. **The corridor** (§2.3.2): each market's
cutoff must land in 0.5-1.15x its reference — the treaty
between COVERAGE (let the market's own 85% walk speak) and
COMPARABILITY (a Standard company should mean similar size
everywhere). Inside the corridor the walk wins; outside — as
in Taiwan, where concentration drags the crossing to $12.95B —
the corridor wins: the cutoff clamps to $9.44B and coverage
flexes. (Q58 in the QA doc.)

**Q (2026-08-06): I don't quite understand the Global Minimum
Size Reference — explain the concept clearly.**

A: Full answer in QA doc Q60. Kernel: each market's 85% line
lands at wildly different company sizes, so MSCI builds a
GLOBAL yardstick — pool the whole DM investable universe, rank
by FULL cap, walk cumulative FREE-FLOAT coverage, and the full
cap at the 70/85/99% crossings = the Large/Standard/IMI
references ($51.3B / $15.75B / $1.19B, Apr-20-2026 data). The
reference is "the size of the company at the global boundary".
EM = half by rule; FM from its own universe. Each market's own
walk then proposes a cutoff and the 0.5-1.15x range disposes:
the book itself computes DM [7.87, 18.11] and EM [3.94, 9.06]
— our corridor [4.10, 9.44] is exactly those numbers x 1.042
(check passes). BONUS FACT: the passage discloses the May-2026
Price Cutoff Date ex post (April 20 — 2nd business day of the
window) -> edition-mining the disclosed dates per review is a
registered follow-up (grades the 10-day sweep; builds a prior
on where in the window MSCI picks).

**Q (2026-08-06): Must the TW crossing land in [3.94, 9.06],
and what if not? Why the 1.042 scaling — does the rulebook
prescribe it?** (May-2026 edition cited throughout)

A: See QA doc Q61 + Q62. Kernels: the FINAL cutoff must
respect the range, the RAW crossing need not — §2.3.3: inside
the range the crossing IS the cutoff; above the ceiling the
membership count EXPANDS to include every company larger than
the upper bound (Taiwan: hence 77 members, coverage
overshoots); below the floor the count SHRINKS ("priority to
global size integrity over market coverage"). The 1.042 is
NOT in the rulebook — Appendix X p.117 prescribes MSCI's own
update (reprice the SAME-RANK company at the new price date;
rank holds while coverage stays in 85-87%, else resets), and
our scaling is the labeled proxy for that repricing: May's
published $15.75B/[3.94, 9.06] are April-20-priced values,
and August's review gets a fresh rank-anchored repricing at
the July date we cannot observe. Band ±2pts = marginal-vs-
average drift + rank-reset discontinuity. Step 1 on the page
now cites Appendix X.

*(Future framework questions append here.)*
