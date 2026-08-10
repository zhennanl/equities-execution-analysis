# Extending the Taiwan analysis to another APAC market

**What this is.** Taiwan is the worked example. This file
records every step that produced it, in order, with the check
that has to pass before the next step starts and the trap that
has already been fallen into at that step. Follow it for Korea,
Japan, China or anywhere else and the analysis should come out
the same shape without rediscovering the same problems.

**How to use it.** Read Part 1, fill in the adapter for your
market, then work Part 2 top to bottom. Do not skip a gate. A
gate that fails is a stop, not a warning — every one of them
exists because passing it silently produced a wrong published
number at least once.

**Companion documents**
- `docs/TW_REBALANCE_ANALYSIS_BRIEF.md` — the questions and
  their minimum deliverables. Market-agnostic; reuse as is.
- `docs/DESIGN_DECISIONS.md` — binding page design rules.

---

# PART 1 — THE MARKET ADAPTER

Everything market-specific is one of these seven. Fill them in
before starting; if any is `UNKNOWN`, that is the first job.

| # | what | Taiwan's answer | how to find it |
|---|---|---|---|
| 1 | **Event window store** | `data/tw_event_windows.json` | Taiwan and India have their own harvesters; every other market is in `data/apac_event_windows/{Market}.json` |
| 2 | **Price source and whether it is survivor-safe** | TWSE + TPEx day files — **survivor-safe**, delisted names retained | archival exchange day-files are survivor-safe; Yahoo is survivors-only and its deletion sample is missing exactly the names that died |
| 3 | **Boards** | TWSE **and** TPEx — two boards, two endpoints | count the boards before harvesting. A market with two boards and a map that names one has produced a silent hole four times: c-195 Taiwan, c-195 Korea, c-225 China, c-232 TPEx |
| 4 | **Volume unit** | TWSE shares; TPEx **lots (×1000)** | never trust the column header — reconcile `volume × close` against published turnover and refuse the batch if it ties at neither unit (`tw_recover.detect_volume_unit`) |
| 5 | **Market proxy for excess returns** | TAIEX, `data/twii_daily.json`, 2009–2026 | needs to cover ≥95% of event price days. Without one, every return is mostly market and the analysis is not about the index event |
| 6 | **Announcement date provenance** | registry 2015+; pre-2015 estimated and **excluded** | MSCI's announcement dates are global, so `data/msci_tw_events.json` serves every market. Anything estimated is excluded, not down-weighted |
| 7 | **Local calendar hazard** | Lunar New Year truncates February windows | find the multi-day closure and check whether it eats a review month's window. Korea (Seollal, Chuseok), China (CNY, Golden Week), India (Diwali), Japan (Golden Week, New Year) |

Two more that are market-specific but optional:

| | what | Taiwan |
|---|---|---|
| 8 | **Flow datasets** | borrow `sbl_history` (joins 117/136), institutional-by-stock (22 days — dead), limits (23 days — dead), market-wide auction ladder |
| 9 | **Passive holdings source for demand** | SEC EDGAR N-PORT for the US-listed tracker; EWT for Taiwan, CIK 0000930667 |

---

# PART 2 — THE STEPS

## Step 1 — Inventory before anything else

**Purpose.** Know what you have. Every previous failure on this
project began with designing an analysis before verifying its
inputs.

**Do.** For the market's window store, print: windows in file,
priced, day-0 provenance split, price-row schema, volume
completeness, duplicate `(review, code)`, sessions before the
announcement and after the effective close, and the trading-day
span from ann to eff.

**GATE.** You can state the analysable n and its date range in
one sentence. Taiwan: *"136 registry-dated windows, 58 ADD / 78
DEL, 2015–2026."*

**Traps.**
- A row count is not a coverage number. "3,024 days" told us
  nothing; "joins to 117 of 136 events" was the fact.
- The price-row schema may be missing fields the source
  publishes. Every Taiwan window holds `{d, c, v}` — open, high
  and low were fetched and dropped one line before storage, and
  nothing ever failed.

## Step 2 — Measure the join rate of every auxiliary dataset

**Purpose.** Decide which flow datasets can support an event
study before writing a question about them.

**Do.** For each auxiliary file, count how many of the analysable
events have data on their announcement or effective date. Report
that fraction, not the file's size.

**GATE.** Every auxiliary file is labelled *usable*, *recent
only*, or *dead for event work*.

**Trap.** A dataset can be large and useless. Taiwan's auction
ladder has 3,024 days and **no security code in it** — it is
market-wide, so it cannot answer any per-name question. That was
called "the highest-value Taiwan-only dataset" in a published
brief before anyone opened it.

## Step 3 — Fix the window width to a uniform ±20 sessions

**Purpose.** Metrics that reach past the end of a series clamp
to the last available day, which makes a "20-day reversion" a
different horizon for every event, averaged as if it were one
measurement.

**Do.** Count sessions each side. If any event is short, top up
— fetch only the calendar gap before the first row and after the
last, merge additively keyed by date, existing rows win. Iterate,
because the gap in sessions is known but the gap in calendar
days is not. `scripts/tw_window_topup.py` is the template.

**GATE.** Minimum sessions before the announcement ≥20 **and**
after the effective close ≥20, across the whole analysable panel.
Print both minima.

**Traps.**
- Calendar pads are not session pads. Taiwan asked for ±25
  calendar days and got ~17 sessions.
- Check whether shortfalls cluster on one review month. Taiwan's
  nine worst were almost all February — Lunar New Year — so
  dropping them would have thinned one month systematically.
- **The APAC panel already passes this** (median 28–30 sessions
  each side, 3 failures in 2,001, all India). Verify, do not
  re-harvest.

## Step 4 — Split day-0 provenance and exclude the estimated

**Purpose.** Day 0 is the pre-news baseline. Every event-time
metric is measured from it.

**Do.** Separate events whose announcement date is MSCI's own
from those where it was inferred. Measure the real ann→eff gap
on the known ones; if the estimate used a different constant,
the estimated events place day 0 inside the reaction.

**GATE.** Only registry-dated events enter event-time
statistics, and the excluded count is stated wherever an n
appears.

**Trap.** Taiwan's estimate used 10 business days; the measured
gap is 12–17, mode 13. Those 40 windows put day 0 two to seven
sessions late, so `pre_drift` absorbed part of the announcement
jump and `drift` lost it — the legs swapped content.

## Step 5 — Market-adjust

**Purpose.** A three-week raw return mostly measures the market.

**Do.** Subtract the proxy's return over the identical dates.
State the proxy and its coverage.

**GATE.** ≥95% of event price days have a proxy value.

**Trap.** Roughly **45% of Taiwan's previously published
addition "edge" was market beta.** Raw addition drift +3.4%
became +2.0% market-adjusted; deletion drift −1.4% became −2.3%.
A published page still shows the raw numbers and says so.

## Step 6 — Verify identity on the extremes

**Purpose.** A wrong ticker that existed at the time returns
clean numbers silently and shows up as a spectacular finding.

**Do.** For the 20 largest events by |total alpha| and by print
size, check the code against the security name. Then run two
mechanical tests across the whole panel: **listing-date
plausibility** (fetch the code's earliest bar; if it postdates
the announcement the mapping is impossible) and **short series**
(a window with far fewer bars than its market's median means
the series starts inside the window, which the three-month
minimum-trading rule forbids for a real constituent).

**GATE.** No unexplained extreme, and both mechanical tests
clean or every exception named.

**Trap.** Three wrong tickers were found on this project only
because the wrong code *failed*. In China, `688139` is mapped to
"QINGDAO HAIER A" — Haier is 600690 — and four windows are
priced under `688660` for "SHANGHAI ELECT A" when 688660 is a
different company. Matching a failed name against the same panel
returns the same wrong code and looks like a fix; it is circular.

## Step 7 — Build the demand model

**Purpose.** "Demand in ADV days" is the number that sizes the
book, and it is the input to every execution answer.

**Do.** Index weight at the review → passive shares → divide by
pre-announcement ADV. Weight comes from the tracker's own
holdings where they can be harvested (SEC EDGAR N-PORT for a
US-listed ETF gives shares and % of net assets, monthly from
2019, quarterly before). Otherwise use full cap ÷ sum of member
full caps as a proxy and measure the proxy's error against any
date where real weights exist.

**GATE.** `demand_adv_days` populated for ≥80% of events, a
named reason for every gap, and a sensitivity table showing
whether the **ranking** of names changes at 0.5×/1×/2× tracking
AUM or only the level.

**Trap.** Point-in-time FIF and index float cap are not on disk
for any market — they exist for one recent date. Assuming the
current FIF held historically is wrong for exactly the names
that get deleted, because their float is what changed.

## Step 8 — Compute event metrics with no clamping

**Purpose.** One definition per metric, identical across events.

**Do.** Define every metric by explicit session offsets from
day 0 and the effective close. Assert in a test that none of
them clamps.

**GATE.** A test fails if any metric's realised horizon differs
across events.

**Trap.** `capture = drift / (gap1 + drift)` explodes when the
total move is near zero. A 1e-6 guard let three events reach
|1000| and dragged a published mean to 14.6. Require the
denominator to be materially non-zero — 50bp — or leave the
ratio undefined.

## Step 9 — Answer the questions to their minimum

**Purpose.** A distribution is raw material; a decision rule is
an answer.

**Do.** Work `TW_REBALANCE_ANALYSIS_BRIEF.md` Part 3. Every
question ends in *if [condition] then [action] at [threshold],
n=X*, plus the tracker reading and the pod reading.

**GATE.** Coverage statement: questions met, unresolved, and
what would unblock each.

**Trap.** Reporting the pooled median as if it were a per-name
forecast. A previous pass gave all eight called additions the
same expected print, drift and effective-day move — the
population median pasted into eight rows.

## Step 10 — Validate before claiming prediction

**Purpose.** Distinguish a rule from a description of the past.

**Do.** Train on the older events, test on the recent ones the
method never saw. Then leave-one-out across all events. Compare;
if they disagree, the method is unstable and must be labelled so
everywhere it appears.

**GATE.** No predictive claim is published without its
out-of-sample number attached, including when that number is
bad.

**Trap.** With ~58 events per side, two splits leave 7–13 per
cell. A cell of 9 showing +16.9% may be one AI-cycle name.

## Step 11 — Publish with the caveats load-bearing

**Do.** One generator script, one JSON, a generated findings
doc, and a page that holds no numbers of its own. Survivorship,
small-n and assumption caveats go in amber blocks at the top of
what they qualify.

**GATE.** A test asserts no figure is typed into the view.

## Step 12 — Record what you learned here

Append any new trap to this file, in the step where it belongs.
That is the only reason this document is worth keeping.

---

# PART 3 — MARKET STATUS

| market | windows priced | ±20 sessions | survivor-safe | proxy | flow data | analysis |
|---|---|---|---|---|---|---|
| **Taiwan** | 176 / 180 | **top-up in progress** | yes | TAIEX ✓ | borrow ✓, rest thin | **in progress** |
| China | 1277 / 1289 | ✓ | no (Yahoo) | none wired | none | not started |
| Japan | 228 / 228 | ✓ | no | none wired | none | not started |
| India | 166 / 166 | ✓ (3 exceptions) | yes (bhavcopy) | none wired | none | not started |
| Korea | 108 / 108 | ✓ | no | none wired | none | not started |
| Indonesia | 52 / 54 | ✓ | no | none wired | none | not started |
| Australia | 42 / 42 | ✓ | no | none wired | ASIC shorts ✓ | not started |
| Thailand | 41 / 41 | ✓ | no | none wired | NVDR ✓ | not started |
| Malaysia | 37 / 37 | ✓ | no | none wired | none | not started |
| Hong Kong | 20 / 20 | ✓ | no | none wired | none | not started |
| Singapore | 19 / 19 | ✓ | no | none wired | none | not started |
| New Zealand | 13 / 13 | ✓ | no | none wired | none | not started |
| Philippines | 0 / 14 | — | — | — | — | **blocked, no source** |

**The first job for any new market is item 5 of the adapter — a
market proxy.** Only Taiwan has one. Without it Step 5 cannot
run, and an unadjusted three-week return is mostly the market.

## Known unrecoverable

- **Philippines, 14 events.** Yahoo's PSE feed returns empty
  frames for live large caps. Needs a different source.
- **Indonesia, 2 events.** Waskita Karya, delisted; a
  survivors-only source cannot return it. This is the
  survivorship hole in its purest form — a deletion that
  vanished because the company died.
- **China, 12 events.** Not missing data: the code requested is
  provably not that company. Needs identity resolution plus a
  listing-date gate, not a re-fetch.
- **Taiwan 2006–2009, 79 events.** TWSE's archive refuses any
  date before 2010-01-04.
