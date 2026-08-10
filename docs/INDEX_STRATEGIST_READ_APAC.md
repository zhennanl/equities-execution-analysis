# What the APAC panel actually says — a strategist's read

*c-230. The tables are in `INDEX_STRATEGIST_QA_APAC.md` and
`INDEX_STRATEGIST_BRIEFS_APAC.md`; both are machine-generated
and no number in them is typed by hand. This page is the
judgement layer: what the panel supports, what it does not, and
what I would put in front of a trader. Written in the voice of
the desk strategist, which means it commits to readings — and
labels every one of them as a reading rather than a result.*

**Panel: 2,078 name-events, 12 markets, MSCI reviews 2015-2026
(Taiwan back to 2010). Tier 1 — daily price and volume only.**

---

## The four things I would say in a morning meeting

### 1. China is not a liquidity event market, and the size of the sample makes that the most reliable statement here

61% of Chinese name-events print **under 2x ADV**, median 1.6x,
and only 9% exceed 10x. Every other market in the panel is the
other way round: Hong Kong 95% over 10x, Indonesia 86%,
New Zealand 85%, Malaysia 83%.

n = 1,229. This is not a small-sample artefact, and it lines up
with the independent decade study that found only ~25% of CN
name-events print materially.

**Desk implication:** a China index-rebalance book should be
sized off the *exceptions*, not the average. The default
posture on a Chinese review name is "this is not an event"
until the demand estimate says otherwise. Spending risk budget
uniformly across a Chinese review list is spending it on 61%
non-events.

### 2. The deletion side is bigger, and Taiwan — the one honest deletion sample — is where the gap is widest

Taiwan deletions print **18.2x ADV** against **6.2x** for
additions, a 3x asymmetry, on delisted-safe exchange data.
Korea shows 12.1x vs 4.5x and Malaysia 41.9x vs 13.5x, but
those are survivors-only and therefore *understate* it: the
deletions that went on to die are missing from the sample
entirely.

India is the interesting counter-case — 16.7x additions vs
17.1x deletions, no asymmetry at all — and India is the *other* delisted-safe
market. Two honest samples disagreeing is a real question, not
noise to average away. My hypothesis is index composition: MSCI
India deletions over this period are more often size-drift
exits than distress exits. **Not tested. Registered as an
open question.**

### 3. Indonesia is the violence outlier and nobody should be surprised by an Indonesian print again

Median |effective-day move| 4.05%, 90th percentile **13.9%**,
max 34.9%, and **41% of events move more than 5%**. The next
worst is Malaysia at 8.5% p90. Indonesia is roughly three times
the risk of China, India or Japan at the tail.

**Desk implication:** Indonesian index events deserve a
different pre-trade limit and a different conversation with the
client. The p90 is the number to quote, not the median.

### 4. Trading early beat the close almost everywhere — and I do not trust it as far as it looks

In 18 of 24 market/side cells, `ALL_DAY1` (do the whole thing
at the first close after the announcement) beat printing at the
effective close. Taiwan adds −505 bps, Malaysia deletes
−1,015 bps, Indonesia adds −634 bps.

Three reasons to hold that loosely:

- **It is unconditional.** The Taiwan window study, which had
  the flow data to condition on, found early execution won on
  *early-hot* names and lost on early-cold ones. A median
  across both says the average name drifted, not that the
  strategy is safe.
- **Survivorship inflates the deletion column.** A deletion
  that kept falling after the print is absent, so "selling
  early beat the close" is measured on the names that stopped
  falling.
- **`ALL_DAY1` is not executable at size.** It puts 100% of a
  print that is 12-40x ADV into a single close. It is a
  benchmark for how much drift there was, not a schedule.

The defensible version: **the drift is real and it is worth
front-loading a schedule, but the size of the prize here is an
upper bound.**

---

## What I checked and would not report

### The day+3 signal is arithmetic, not a signal

My first run correlated the day+1→+3 move against the
day+1→effective-1 drift and got rho 0.35–0.44 in **every single
market**. That uniformity was the tell. The drift window
*contains* the early window, so the correlation is a definition,
not a finding.

Recomputed against the drift that comes *after* day +3, the
honest numbers are −0.34 to +0.22 — noise everywhere. Taiwan
falls from 0.44 to **0.02**.

Both columns are kept side by side in Q9 so the reader can see
the size of the artefact. Anyone who reports a 0.44 here is
reporting their own left-hand side.

### The Feb-2023 QCIR split shows nothing I would act on

Print sizes are flat across the regime break in most markets
(China 1.53→1.65x, Taiwan 11.95→12.67x, Japan 11.20→10.38x).
Korea drops 8.99→6.36x and Singapore 20.4→16.6x, but n is 50ish
and 10ish and 2023-2026 is a different volatility regime
anyway. **A period split is not a controlled experiment.**
Registered, not adopted.

### Anything that requires knowing the answer before the print

Crowding, completion, squeeze risk, wrong-way positioning, the
anticipation clock, auction share — every forecasting element
of the Taiwan playbook — is Tier 2 or Tier 3 and does not exist
for these markets. See `APAC_DATA_GAP_REGISTER.md`.

I want to be exact about what that costs, because it is the
whole difference between this document and the Taiwan one:
**everything above is descriptive. None of it tells you which
name in the next review will be the violent one.**

---

## Per-market one-liners

| market | n | the one thing to know |
|---|---|---|
| **China** | 1,237 | 61% of events are not events. Size off the exceptions. |
| **Japan** | 202 | Orderly — 11x prints, 1.45% median move, deletions barely drift. The adds are where the drift is (+1.71%). |
| **India** | 164 | No add/delete asymmetry, and it is a delisted-safe sample, so that is a real finding rather than a survivorship artefact. |
| **Taiwan** | 157 | The reference market: 3x deletion asymmetry, 12x median print, 35x at p90, and the only Tier-2 read we own. |
| **Korea** | 102 | Second-highest violence of the large samples (7.0% p90) and the highest-value Tier-2 target in the region. |
| **Indonesia** | 51 | The violence outlier: 13.9% p90, 41% of events over 5%. |
| **Thailand** | 41 | Quiet by APAC standards (6.0% p90) and the only non-Taiwan market with both short and foreign flow per stock. |
| **Malaysia** | 37 | Enormous prints relative to liquidity (28x median, 91x p90) on a thin tape. |
| **Australia** | 35 | Moderate everything, and the cheapest census short data in the region. |
| **HongKong** | 20 | Big prints (21x) but only 20 events — the smallest sample that still says something. |
| **Singapore** | 19 | Too few events for a book; the 6-name add cell should not be quoted. |
| **NewZealand** | 13 | 56x median print on a tiny tape. Structurally interesting, economically marginal, and data-dark for Tier 2. |

---

## What I would do next, in order

1. **Australia and Hong Kong Tier 2.** Both are open URLs with
   census-quality short data. This turns two markets from
   descriptive to conditional and proves the Taiwan machinery
   ports before anyone spends on Korea.
2. **Delisted-safe harvesters for Japan and China.** 147 and
   436 deletion-side name-events currently rest on a
   survivors-only source. This is the largest single source of
   bias in the panel and it is a harvester problem, not a
   licensing one.
3. **Test the India asymmetry question.** Two honest samples
   disagree about whether deletions are harder. That is
   answerable with the data we already hold.
4. **Leave the day+3 conditioning alone** until there is flow
   data to condition on. Taiwan's version worked because it
   conditioned on *crowding*, not on price.


---

## Provenance

Every figure on this page was re-read from
`data/index_strategist_qa.json` and checked against the text
before publication. Two did not match on the first pass and
were corrected: the schedule count was 18 of 24 cells, not 19,
and India's asymmetry is 16.7x vs 17.1x, not 17.1x vs 16.8x.
Recorded because a strategist note whose numbers drift from its
own source is worth less than no note.
