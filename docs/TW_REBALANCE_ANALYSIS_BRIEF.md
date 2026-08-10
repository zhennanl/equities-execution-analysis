# MSCI Taiwan — Rebalance Analysis Brief

**Supersedes `REBALANCE_QUESTION_BANK.md`.** That document asked
89 good questions and got a shallow answer, because it never
defined what a finished answer looks like and it described a
dataset nobody had verified. This one fixes both.

Drop this file into a chat and the analysis runs end to end
with no further input.

---

# PART 0 — THE CONTRACT

## 0.1 What this is for

A CLSA program-trading dealer has two clients and they want
opposite things:

- **The passive tracker** is paid to have no tracking error.
  Its benchmark IS the effective-day close, so every schedule
  that is not "trade the close" buys P&L with tracking error.
  The tracker's question is *how much error, for how much
  saving.*
- **The hedge-fund pod** is paid in P&L and sized on risk. Its
  question is *how often does this work, how far offside does
  it go first, and where do I get out.*

**Every recommendation in this analysis carries both answers.**
A finding with only one is unfinished. The PT dealer is the
lead reader — the output has to survive being questioned by a
desk head, not just be correct.

## 0.2 Autonomy

- Work the brief end to end in one pass. Do not stop, do not
  ask for approval, do not wait.
- Every choice this brief does not make is yours. Make it,
  state it in one line, move on.
- Prefer running the analysis to describing it. Write Python,
  execute it, read the output, act on what it says.
- If a question is badly posed once you see the data, answer
  the better version and say you changed it.
- **Report coverage honestly at the end**: how many questions
  met their minimum, how many did not, and why. Silent
  narrowing of scope is the failure mode this brief exists to
  prevent.

## 0.3 The done bar — the most important rule here

**Every question below carries its own MINIMUM. A question is
not answered until its minimum is met.** Nothing is answered
"partially". If the minimum cannot be met, write one line
saying why and mark it `UNRESOLVED — [reason]`.

The general shape of a minimum is a **decision rule**:

> if *[observable condition]*, then *[action]* at *[threshold]*
> — n=X, hit rate Y%, on *[named sample]*.

A distribution without a threshold is raw material. A median
without an action is not an answer. This standard would have
rejected the entire previous pass.

## 0.4 Standard of proof

Each of these has already produced a wrong answer on this
project.

1. **Dispersion, always.** Every median carries n, p10/p25/
   p75/p90, and the share of the sample with the opposite
   sign. Cohorts under 20 are labelled EXPLORATORY in the
   payload, not in a footnote. Never quote a cohort under 10.
2. **Mean and median together where they differ.** Taiwan
   addition drift averages ~+5.8% against a median of ~+1.8%;
   three events carry the gap. Report both or the reader sizes
   on three events.
3. **Never correlate overlapping windows.** `gap1` × `drift`
   and `drift` × `revert` are disjoint by construction and are
   the only return-on-return pairs permitted.
4. **Market-adjust everything.** Excess over TAIEX
   (`twii_daily.json`). Roughly 45% of the previously published
   addition "edge" was market beta.
5. **Day 0 is the announcement close, and it must be real.**
   Only registry-dated events are analysable. See §1.3.
6. **Respect the Feb-2023 regime break** — MSCI moved to a full
   quarterly comprehensive review. Split rather than pool for
   anything cadence-dependent, and note that a period split is
   not a controlled experiment.
7. **Name the sample every time**, including its day-0
   provenance and its session window.
8. **Treat any single extreme outlier as a possible identity
   error** and check the name before featuring it.

## 0.5 Output contract

1. `scripts/tw_rebalance.py` — the generator. One command
   regenerates everything.
2. `data/tw_rebalance.json` — every computed figure, machine
   readable. Nothing downstream may hold a number this file did
   not produce.
3. `docs/TW_REBALANCE_FINDINGS.md` — the written answers, in
   question order, GENERATED from the JSON so the two cannot
   drift.
4. A page on the site, registered in `app.py`, following
   `docs/DESIGN_DECISIONS.md` without exception. Survivorship,
   small-n and assumption caveats go in amber `design.caveat`
   blocks, never in grey footnotes.
5. `data/aug26_expected_outcomes.json` — the pre-registered
   live call, dated, written before the announcement.

Charts: distributions, not point estimates. Box plots and
ECDFs beat bars of medians. Where a number drives a decision,
draw the whole distribution and mark the threshold on it.

---

# PART 1 — THE DATASET, AS VERIFIED

Measured on 2026-08-09. Do not re-derive these; do re-check
them if a number below looks wrong.

## 1.1 The event panel

`data/tw_event_windows.json`

```
windows: { "{review}|{code}": {
    rev, code, action(ADD|DEL), name,
    ann, eff, ann_src, day0,
    px: [ {d, c, v}, ... ]
}}
```

| fact | value |
|---|---|
| windows in file | 180 |
| priced | 176 |
| **registry-dated day 0 — the analysable panel** | **136** |
| …of which ADD / DEL | 58 / 78 |
| estimated day 0 (excluded) | 40 |
| date range of the analysable panel | 2015 – 2026 |
| duplicate (review, code) | 0 |
| windows with any volume gap | 0 |
| **windows carrying OHLC** | **0 — close and volume only** |
| trading days ann → eff | 5 to 17, mode 13 |

**There is no open, high or low anywhere in this panel.** Both
TWSE and TPEx day files publish them and the harvester dropped
them; a re-fetch is available (`tw_recover.py ohlc`) but has
not been run. Any question needing intraday range, the
overnight gap, or a close-to-open decomposition is
`UNRESOLVED — no OHLC` until it is.

## 1.2 The window is ±17 sessions and must be topped up to ±20

The harvester asks for ann − 25 **calendar** days → eff + 25.
After weekends and Taiwan holidays that is ~17 sessions each
side, and it varies event by event:

- sessions before the announcement: 10 to 18
- sessions after the effective close: 15 to 19
- **events with 20 clear sessions either side: zero**

The nine worst-truncated events are almost all **February**
reviews, cut short by Lunar New Year — a seasonal bias, not
random attrition.

Consequence: any metric that reaches past the window silently
clamps to the last available day, so it becomes a different
horizon for every event. The previous pass reported a
"20-day reversion" that was really 15–19 days, ragged.

**PREREQUISITE 1 — top up to a uniform ±20 sessions.** Write a
script that, for each of the 136, fetches only the additional
sessions needed to reach 20 before the announcement and 20
after the effective close, and merges them into the existing
series. Do not re-fetch what is already held. Verify after
merging that all 136 have ≥20 each side, and refuse to
continue if any do not.

## 1.3 Day-0 provenance — why 40 events are excluded

40 priced windows carry `ann_src = "EST (eff − 10 b-days)"`.
MSCI's announcement-date registry only begins in 2015; before
that the announcement was inferred. On the 34 reviews where the
real date is known the ann→eff gap is 12–17 business days,
mode 13 — never 10. So those windows place day 0 two to seven
sessions **late**, inside the reaction rather than before it.

`gap1`, `drift`, `pre_drift` and `total_alpha` are all measured
from day 0. If day 0 is three days into the move, `pre_drift`
absorbs part of the announcement jump and `drift` loses it —
the legs swap content. **Excluded from every event-time
statistic.** All 40 fall in 2010–2014.

## 1.4 The market proxy

`data/twii_daily.json` — TAIEX close, 4,204 days,
2009-06-01 → 2026-08-07. Covers 99.8% of event price days.
Every return in this analysis is excess over it.

## 1.5 Auxiliary data — measured JOIN RATES, not row counts

"3,024 days" tells you nothing. This is what actually joins to
the 136:

| dataset | span | joins to | verdict |
|---|---|---|---|
| `sbl_history.json` | 3,024 d, 2015–26 | **117/136** (71 DEL, 46 ADD) | usable |
| `tw_vintage_cache.json` | daily shares | **136/136**, all 102 codes | usable — full cap is reconstructable |
| `auction5s_history.json` | 3,024 d, 7% empty | 30 of 34 effective days | **market-wide only** |
| `tw_daily_turnover.json` | 266 d, 2025–26 | 30/136 | recent only |
| `tw_limits.json` | 23 d | 13/136 | **dead for event work** |
| `twse_institutional.json` | 22 d | 8/136 | **dead for event work** |

**The auction ladder has no security code in it.** Each row is
`[time, 7 aggregate figures]`. It describes the whole TWSE
close, not any name's print. "What share of *the print* went
through the auction" is not answerable from it — that is a
per-stock or 5-minute question. Use it for market-level context
only and say so.

## 1.6 The demand model — the real blocker, and its solution

Index weight per historical event is the input to every sizing
answer, and it is not on disk: point-in-time FIF and index
total float cap exist for one recent date only.

**PREREQUISITE 2 — harvest EWT holdings from SEC EDGAR.**

- iShares MSCI Taiwan ETF, CIK `0000930667`, series
  `S000004261`.
- **NPORT-P, monthly, mid-2019 → today.** Clean XML; one
  `<invstOrSec>` per holding with `<title>`, `<isin>`,
  `<balance>` (shares), `<valUSD>`, `<pctVal>`.
- **N-Q, quarterly, 2015 – 2019.** HTML, needs parsing.
- Fund fiscal year ends 31 August, so filings land on
  **Feb / May / Aug / Nov quarter-ends — the MSCI review
  months.**
- Enumerate via `https://efts.sec.gov/LATEST/search-index?q=%22iShares+MSCI+Taiwan+ETF%22&forms=NPORT-P`.

**Caveat that must be carried:** EWT tracks the **MSCI Taiwan
25/50** capped index, not the standard one — TSMC sits ~22.6%
there against ~54.8% uncapped. Relative weights among the
*uncapped* names survive, which is what matters because the
names that get added and deleted are never the capped ones.
Absolute weights need rescaling by the cap factor. Cross-check
against Fubon 0057 (uncapped, Taiwan-domiciled) where its
semi-annual holdings are reachable.

FIF is not published anywhere and must be backed out as
weight ÷ full market cap.

**Fetching rules:** `WebSearch` and `web_fetch` only. Never
curl, wget or requests to retrieve a URL. If a fetch is
blocked, record it and move on.

**If the harvest fails**, fall back to the proxy — weight ≈
name's full cap ÷ sum of full caps of reconstructed index
members at that date (`membership_history.json` +
`tw_vintage_cache.json`) — measure its error against the one
date where real weights exist, and carry that error as a
declared assumption on every sizing number.

## 1.7 Known defects — do not rediscover these

- 52 Taiwan changes carry no ticker and have no window. Say
  "tickered events", not "events".
- 79 rows in 2006–2009 have no window and never will: TWSE's
  archive refuses any date before 2010-01-04.
- The visible defect rate is not the defect rate. A wrong
  ticker that existed at the time returns clean numbers
  silently.
- TPEx names entered this panel only at c-261. If a Taiwan
  result differs sharply from work published before that, this
  is why.

---

# PART 2 — BUILD ORDER

Nothing in Part 3 may run until Part 2 is done and verified.

**B1. Top up the windows to ±20 sessions** (§1.2). Verify all
136 clear it. MINIMUM: a printed table of pre/post session
counts showing the minimum is 20 on both sides.

**B2. Harvest EWT holdings** (§1.6). MINIMUM: a file with, per
review quarter 2015–2026, each Taiwanese holding's shares,
USD value and percent of net assets; plus a stated coverage
table of which review quarters were obtained.

**B3. Build the demand model.** For each event, at the review
before it: index weight → passive shares demanded → demand in
ADV days, using the topped-up pre-announcement ADV.
MINIMUM: `demand_adv_days` populated for ≥80% of the 136, a
named reason for every gap, and a sensitivity table at 0.5×,
1× and 2× tracking AUM showing whether the **ranking** of names
changes or only the level.

**B4. Re-derive tracking AUM** rather than assuming $180bn.
Bottom-up from identifiable trackers, with a stated residual
for unobservable mandates. MINIMUM: a figure, its components,
and the range it could plausibly take.

**B5. Recompute the event metrics** on the topped-up panel,
market-adjusted, registry-dated only. MINIMUM: every metric
defined by its exact session offsets, with no clamping
anywhere — assert it in a test.

---

# PART 3 — THE QUESTIONS

Each carries **MIN:** — the bare minimum that counts as done.

## S — Sizing: how big is this trade

**S1. What is the distribution of effective-day print size, in
ADV days, by side?**
MIN: ECDF for ADD and DEL with p10/p50/p90, and the share of
events above 5×, 10× and 20× ADV. State the participation rate
at which each threshold becomes unworkable in a single session.

**S2. Does estimated passive demand predict the actual print?**
Regress `vol_mult_eff` on `demand_adv_days`.
MIN: R², slope, residual distribution. **If the relationship is
weak, that IS the finding** — it means the print is not mostly
passive and something else drives it. Say which.

**S3. What multiple of estimated demand actually prints?**
MIN: distribution of `vol_mult_eff ÷ demand_adv_days` by side,
with a stated interpretation of any ratio far above 1.

**S4. Which predicts print size best — weight, market cap, ADV,
or free float?**
MIN: rank correlations in one table, and a plain statement of
which two or three actually matter and which to ignore.

**S5. How much bigger is a deletion print than an addition,
controlling for size?**
MIN: ADD and DEL matched on ADV decile, with the raw gap and
the size-controlled gap side by side. The raw ~3× ratio is
partly a size artefact; strip it and report what survives.

**S6. At what point is a name not completable?**
MIN: days required at 10% and 20% of ADV to clear estimated
demand, distribution and tail, and the count of events where
that exceeds the ann→eff window.

## T — Timing: when to trade

**T1. What is the drift distribution by side, and how often is
the sign wrong?**
MIN: median, IQR, **hit rate**, and mean-vs-median both quoted.
A pod cannot size on a median that is right 60% of the time
without knowing it is 60%.

**T2. Where in the window does the drift actually accumulate?**
MIN: cumulative excess return by session offset; the offsets at
which 50% and 80% of total drift is realised; and a stated
start date for a schedule expressed in sessions before the
effective close.

**T3. Does the announcement-day gap predict the subsequent
drift?** (disjoint windows — legitimate)
MIN: rank correlation with n, and a rule: at what gap size does
the desk trade more on day 1 rather than waiting.

**T4. Is `capture` stable enough to plan around?**
MIN: distribution by side, and its trend by year with n per
year. State plainly whether the post-announcement move is being
competed away.

**T5. What is the best single execution day in hindsight, and
is it predictable in advance?**
MIN: distribution of the best day, the average regret of
choosing the effective close, and a direct yes/no on
predictability with the evidence for it.

**T6. Three schedules compared: 100% at the close, spread over
the last four days, 100% at ann+1.**
MIN: median saving, IQR **and tracking-error contribution** for
each. The tracker reads the TE column, the pod reads the
saving column — both must be present.

**T7. Is there a reliable pre-announcement signal?**
MIN: `pre_drift` by eventual side, and whether it is decaying
over time. If names that will be added already drift up, say by
how much and whether it is tradeable given the call is not
certain.

## P — Price: what the trade costs

**P1. What is the effective-day return distribution, and how
often does it move against the flow?**
MIN: distribution by side plus the count of additions that fall
and deletions that rise on the print — that is the
liquidity-provision opportunity, quantified.

**P2. Is the effective-day move related to print size?**
MIN: bucketed by ADV multiple, not fitted as a line. State the
bucket where the relationship changes.

**P3. Does illiquidity amplify the move super-linearly?**
MIN: median |total alpha| and print size by ADV decile, and a
statement of the shape — linear, or a tail that dominates.

**P4. Is a repeat mover different from a first-timer?**
MIN: magnitude and drift for first appearance versus repeat,
with n for each.

**P5. Does the number of simultaneous changes dilute each one?**
MIN: per-name magnitude against changes-per-review, with the
correlation and a statement of whether a heavy review night
changes the trade.

## R — Risk

**R1. What is the maximum adverse excursion?**
MIN: for a position entered at ann+1 and held to the effective
close, the worst mark-to-market, distribution by side. **A pod
sizes on this, not on the final P&L.**

**R2. What is the reversion profile to +20 sessions?**
MIN: reversion at +5 and +20 by side with dispersion, on the
topped-up uniform window. State where the pod's exit is.

**R3. Is the round trip profitable, and for whom?**
MIN: enter ann+1, exit at the close / +5 / +20, net of a
**stated** cost assumption swept at 0/20/40/80bp. Hit rate at
each. State the cost assumption explicitly.

**R4. Under what conditions does the drift signal fail?**
MIN: profile the events where drift went the wrong way against
those where it worked, and give one testable common feature —
or state that there is none, which is equally useful.

**R5. What is the worst case, named?**
MIN: the ten largest events by |total alpha| and by print size,
each with one line on what happened, and confirmation that the
ticker matches the security.

**R6. How concentrated is the risk?**
MIN: share of total absolute alpha in the worst 5% of events,
and a direct answer on whether to trade the basket or pick
names.

## F — Flow: who is on the other side

**F1. Does borrow build before deletions, and does it predict
the squeeze?**
MIN: build distribution on the 117 joinable events, and its
correlation with the effective-day move and the reversion. **A
null result is a complete answer** — say whether borrow earns
its place in the pitch.

**F2. Is the borrow pool constrained?**
MIN: balance against new lending into the print, and the count
of events where the short side looks full.

**F3. What does the market-wide close look like on a review
night versus a normal night?**
MIN: aggregate auction size on the 30 reachable effective days
versus a matched sample of ordinary days. Label it clearly as
market-level; per-name auction share is out of reach.

## C — Cadence and regime

**C1. Did the Feb-2023 quarterly comprehensive review change
event magnitude?**
MIN: split test per side with n, and a note on what else
changed in that period.

**C2. Do the four review months differ?**
MIN: magnitude and drift by month with n, and an explicit check
on whether February is distorted by Lunar New Year.

**C3. Does the ann→eff window length matter?**
MIN: length distribution (5–17 sessions) against drift and
capture. A longer window may mean more front-running.

## B — Benchmarking and TCA

**B1. What is the right benchmark for an index rebalance
order?**
MIN: arrival, interval VWAP and closing price compared against
realised outcomes, and a statement of how the choice changes
the desk's apparent skill.

**B2. What would implementation shortfall have been for each
schedule in T6?**
MIN: a number per schedule against a stated cost model.

**B3. Two scorecards — how to report to a tracker versus a
pod.**
MIN: both proposed, with the metrics each contains and why they
differ.

---

# PART 4 — VALIDATION

Nothing from Part 3 may be presented as predictive until it
passes here.

**V1. Time split.** Build every rule on events before
2023-02-01; test on 2023-02-01 onwards (~40 events the method
has never seen).
MIN: hit rate and error on the test set, reported even when
poor. A negative result is published, not buried.

**V2. Leave-one-out.** Rebuild without each event, predict it,
repeat across all 136.
MIN: out-of-sample error distribution.

**V3. Agreement.** Compare V1 and V2.
MIN: a direct statement — if they disagree, the method is
unstable and must be labelled so wherever it appears.

**V4. Two methods per name.** Every per-name expectation is
produced twice: by matched **cohort** (median of similar past
events, n stated, never below 10) and by a **fitted model**
across all events.
MIN: both numbers side by side per name. **Where they disagree,
that gap is the honest uncertainty** — report it as the range,
and prefer the cohort.

---

# PART 5 — THE LIVE CALL, AUGUST 2026

Announced 12 Aug 2026, rebalance close 31 Aug, effective 1 Sep.

**L1. Regenerate the constituent call** using the existing
"Predict MSCI Index Changes" framework on the freshest
available data — the 85% walk, the market size-segment cutoff,
the 2/3 and 1.5× buffers, the minimum float gate.
MIN: the additions and deletions with their zone and
conviction, and a stated diff against the previously
registered call with a reason for every change.

**L2. Size each name.** Passive demand in shares and in ADV
days, using the demand model from B3.
MIN: per name, with the ADV source and date stated, and
`UNKNOWN` where there is no ADV rather than a filled default.

**L3. Place each name on the historical distributions.**
MIN: per name, expected print / drift / effective-day move as a
**range**, from its matched cohort AND the fitted model, with
the cohort's n. **Two names may not carry the same expectation
unless their inputs are the same** — the previous pass gave
every addition an identical forecast, which is the specific
failure this line exists to prevent.

**L4. Rank the names by expected violence and say why.**
MIN: an ordered list with the driver named per name.

**L5. Recommend a schedule per name, per client type.**
MIN: tracker answer and pod answer, both with a participation
rate and a start session.

**L6. Flag borrow and squeeze risk on the deletion list.**
MIN: current borrow balance versus its own history per
deletion, and a specific check on whether TPEx names behave
differently.

**L7. Pre-register the expected outcomes.**
Write to `data/aug26_expected_outcomes.json` **before the
announcement**, dated.
MIN: per name — expected print in ADV days, drift, effective-day
move, each as a range with its cohort n; plus a stated
falsifier per name (the observation that would prove the call
wrong early). Plus a grading script that scores it after 1 Sep.
*A prediction not written down before the event is not a
prediction.*

**L8. What would change this plan.**
MIN: three specific events, each with how the desk would
detect it and what it would do.

---

# PART 6 — OUT OF REACH, AND WHY

Record, do not attempt.

**Needs the OHLC re-fetch** (`tw_recover.py ohlc`): intraday
range, overnight gap versus the prior close, any close-to-open
decomposition of the announcement reaction.

**Needs per-stock auction or 5-minute data:** what share of a
name's effective-day volume goes through the closing auction;
the intraday shape of the effective day; pre-auction imbalance
as a signal; realised cost of a VWAP versus close-heavy
schedule; the participation rate at which impact turns
non-linear.

**Needs a backfill, not better resolution:** who is on the
other side (`twse_institutional`, 22 days) and whether the
print hit a price limit (`tw_limits`, 23 days). Backfilling
TWSE's institutional day files is the highest-value remaining
Taiwan data job.

**Permanently unavailable:** 2006–2009 events (TWSE archive
floor), and the 52 Taiwan changes with no ticker.

---

# PART 7 — DONE

The analysis is finished when **all** of these hold:

1. Both prerequisites in Part 2 are complete, or their failure
   is documented with the fallback in force.
2. Every question in Part 3 either meets its MINIMUM or is
   marked `UNRESOLVED` with a one-line reason.
3. Part 4 has run and its results are attached to every
   predictive claim.
4. Part 5 exists as a dated file written before 12 August.
5. All five output artefacts in §0.5 exist, the page renders,
   and the test suite passes.
6. A coverage statement is printed: questions met, unresolved,
   and what would unblock each.

Then stop and hand back. Bill selects what stays on the site.
