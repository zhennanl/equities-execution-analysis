# APAC Index Rebalance — Strategist Question Bank

**A self-executing analysis brief.** Drop this file into a
chat and begin work immediately. Do not summarise it back. Do
not ask which section to start with. Work through it to the
end.

---

# PART 0 — OPERATING INSTRUCTIONS

## 0.1 Who the answers are for

You are the index rebalance strategist on an agency program
trading desk. Two client types read your work and they want
different things from the same numbers:

**Passive trackers** (ETF and index mandates). Their objective
function is **tracking error**, not alpha. They are obliged to
own the index at the effective close. They want to know: how
much of my print will the market absorb, what does deviating
from the close cost me in tracking error, and where is the
risk that I cannot complete. A recommendation that improves
average price but widens tracking error is a *bad* answer for
this client, and you must say which client each conclusion
serves.

**Index rebalance pods** (Millennium-style, market-neutral,
tight risk limits). Their objective function is **risk-adjusted
P&L on a repeatable signal**. They want: what is the edge, what
is the hit rate, what is the distribution of outcomes not the
mean, how crowded is the trade, when does it stop working, and
what is the drawdown when it fails. For them a median is nearly
useless on its own — they need dispersion, tails, and decay.

Write every conclusion so a trader could act on it before the
next print. "Additions drift +3.3%" is an observation.
"Additions drift a median +3.3% between announcement and
effective, but the interquartile range spans -1% to +9% and one
in five is negative, so a schedule that assumes drift is
short volatility" is an answer.

## 0.1b Order of work — Taiwan first, always

**Do Taiwan before anything else, on both daily and 5-minute
data.** Not because it is the biggest market here — China is —
but because it is the only one where the analysis can be
*checked*:

- it is **delisted-safe**, so its deletion sample is not
  survivorship-poisoned;
- it has **six alternative datasets** already harvested
  (§2N), so a price finding can be traced to a flow cause
  rather than left as a correlation;
- it has **prior work to disagree with** — the event-window
  study, the backtest, the Aug-2026 live call — so a result
  that contradicts earlier findings is informative rather than
  merely new;
- it is the market the **live application in Part 3** runs on.

So the sequence is: Taiwan daily → Taiwan alt-data (§2N) →
Taiwan 5-minute when it lands → then the other markets,
largest sample first (China, Japan, India, Korea).

When a cross-market answer disagrees with the Taiwan answer,
say so explicitly and treat Taiwan as the better-instrumented
observation, not the outlier.

## 0.2 Autonomy contract

- **Do not stop.** Work the bank end to end in one pass.
- **Do not ask for input.** Every choice this brief does not
  make is yours; make it, state it, move on.
- **Do not wait for approval** on intermediate results.
- If a question cannot be answered with the data on hand, say
  so *in one line*, mark it `UNANSWERABLE-DAILY`, and continue.
  Do not stall, and do not substitute a weaker question
  silently.
- If a question turns out to be badly posed once you see the
  data, answer the better version and say that you changed it.
- Prefer running the analysis to describing how you would run
  it. Write Python, execute it, read the output.

## 0.3 Standard of proof

These are the rules the desk is held to. They exist because
each has already produced a wrong answer here at least once.

1. **Report dispersion, not just the middle.** Every headline
   median must carry n, IQR or p10/p90, and the share of the
   sample with the opposite sign. A median with n=6 is an
   anecdote and must be labelled one.
2. **Never compare overlapping windows.** Correlating a
   sub-window against a window that contains it manufactures a
   correlation from arithmetic. This has happened here before
   (rho 0.35–0.44 in every market, which collapsed to −0.34..
   +0.22 once the windows were disjoint). If two measures share
   days, either disjoin them or do not correlate them.
3. **Split survivor-safe from survivors-only.** Taiwan and
   India are priced from archival exchange day-files that still
   contain delisted companies. Every other market is priced
   from Yahoo, which carries live listings only — so its
   *deletion* sample is missing exactly the names that died.
   Any deletion statistic pooled across both is biased and you
   must present them separately.
4. **Market-adjust or say you did not.** Raw returns over a
   3-week window mostly measure the market. Taiwan has a 0050
   proxy wired; for other markets either source an index proxy
   or state that the number is unadjusted.
5. **Respect the Feb-2023 regime break.** MSCI moved to a full
   quarterly comprehensive review. Pre- and post-2023 are
   different populations for anything cadence-dependent. Split
   and test rather than pooling.
6. **A period split is not a controlled experiment.** If you
   split on time, something else also changed. Say what.
7. **Distinguish a bad ticker from absent data.** See §1.4.
8. **Name the sample every time.** "APAC" without a market and
   date range is not a result.

## 0.4 Output contract

Produce all four:

1. **`docs/REBALANCE_FINDINGS.md`** — the written answers, in
   question order, each with: the number, the sample, the
   method in one line, the caveat, and the desk implication
   split by client type where they differ.
2. **`data/rebalance_analysis.json`** — every computed figure,
   machine-readable, so nothing on a page is typed by hand.
   Any page must read from this file.
3. **`scripts/rebalance_analysis.py`** — the reproducible
   generator. One command must regenerate everything.
4. **A page on the site** — `views/rebalance_insights.py`,
   registered in `app.py`. Follow the design system without
   exception: `design.sect` for headings, `design.stats` for
   figure rows, `design.table` for tables, `design.chart` for
   plotly, `design.beats` for explanation, `design.caveat` for
   limitations. Read `docs/DESIGN_DECISIONS.md` first — D1
   through D15 are binding, not advisory. Put the *survivorship
   and small-n* caveats in amber blocks, not in grey footnotes.

Charts: prefer distributions to point estimates. A box plot or
an ECDF beats a bar of medians for every question in Part 2C
onward. Where a number drives a trading decision, show the
whole distribution and mark the decision threshold on it.

## 0.5 Selection

Bill reviews and selects what stays on the site. Put up
everything you believe is defensible; flag anything you think
is interesting but under-powered as `EXPLORATORY` on the page
itself so the distinction survives the review.

---

# PART 1 — THE DATASET

## 1.1 Event windows (the core panel)

`data/apac_event_windows/{Market}.json`

```
windows: { "{review}|{code}": {
    rev, code, action(ADD|DEL), name,
    ann  (announcement date, ISO),
    eff  (effective date, ISO — the REBALANCE CLOSE),
    ann_src, yf_symbol, src,
    px: [ {d, o, h, l, c, v}, ... ]      # daily OHLCV
}}
```

Window convention: **ann − 45 calendar days → eff + 20**.
`v` is in SHARES for every market and board.

`data/tw_event_windows.json` — Taiwan, same shape, from TWSE
and TPEx day-files (delisted-safe). Note `px` rows here carry
`{d, c, v}` only for some vintages; handle both.

**Coverage (post-c-261):** 2,078+ of 2,097 attemptable windows
priced. Philippines is EXCLUDED (no source). Run
`py scripts\apac_event_days.py coverage` for the live number
and `gaps` for the residue with causes.

## 1.2 The event registry

`data/msci_changes_db.pkl` (pandas): `review, review_type, year,
month, market, action, security, eff_date_est, code, ticker`.
4,400+ rows, 13 markets, Feb-2006 → May-2026. **Only 2015+ has
price windows.**

## 1.3 Auxiliary — join these where the question needs them

| file | what | markets |
|---|---|---|
| `data/event_window_metrics.json` | already-computed per-window metrics and the ADD/DEL playbook | all priced |
| `data/sbl_history.json` | daily securities-borrowing balance `{date: {code: [new, balance]}}` | Taiwan, 2015+ |
| `data/twse_institutional.json` | foreign / trust / dealer net by ticker by day | Taiwan, recent |
| `data/tw_daily_turnover.json` | daily turnover value by code | Taiwan |
| `data/tw_limits.json` | daily OHLC + limit flag | Taiwan |
| `data/auction5s_history.json` | 5-second closing-auction ladder | Taiwan, 2015+ |
| `data/au_event_shorts.json` | ASIC daily short positions per event | Australia |
| `data/tw_atvr.json` | ATVR by month | Taiwan |
| `data/apac_factsheet_top10.json` | index weights, top 10 | all |
| `data/membership_history.json` | reconstructed constituent lists by review | all |
| `data/apac_delisted_movers.json` | the names we could NOT price — the deletion blind spot | all |

## 1.4 Known defects — do not re-derive these

- **894 name-events carry no ticker** and have no window. The
  panel is ~2/3 of all MSCI APAC changes since 2015. Say
  "tickered events", not "events".
- **12 China windows are a TICKER DEFECT**, not missing data —
  the code asked for is provably not that company's. Exclude
  them from "data availability" statements.
- **The visible defect rate is not the defect rate.** Three
  wrong tickers were caught only because the wrong code
  *failed*; a wrong code that existed at the time returns clean
  numbers silently. Treat any single extreme outlier as a
  possible identity error and check the name before featuring
  it.
- **B-shares and OTC boards** behave differently from main
  boards. Taiwan TPEx names were absent from this panel until
  c-261; if a Taiwan result changes sharply versus earlier
  work, that is why.

## 1.5 Metrics already computed (`event_window_metrics.json`)

Reuse rather than recompute, and read the definitions before
you cite them:

- `gap1` — announcement-day gap: ann close → ann+1 close,
  market-adjusted.
- `drift` — ann+1 → eff−1. **The tradeable middle.**
- `eff_day` — eff−1 → eff. The print itself.
- `revert5`, `revert20` — eff → eff+5 / +20.
- `total_alpha` — ann → eff−1.
- `pre_drift` — ann−25 → ann. Pre-announcement positioning.
- `capture` = drift / (gap1 + drift) — how much of the move
  was available *after* the announcement gap.
- `vol_mult_eff` — effective-day volume ÷ ADV. **The print
  size.**
- `vol_mult_win` — median in-window volume ÷ ADV.
- `demand_adv_days` — estimated index demand in ADV days
  (weight × tracking AUM ÷ ADV).
- `PRE`, `SQZ` — pre-positioning and squeeze scores.
- `label` — QUIET / MIXED / CLEAN-DRIFT / FRONT-RUN-FADE /
  SQUEEZE.

Current pooled playbook, for orientation only — your job is to
break these down, not repeat them: ADD n=64 drift +3.3%,
eff-day vol 6.2× ADV; DEL n=93 drift −1.5%, eff-day vol 18.2×
ADV.

---

# PART 2 — THE QUESTION BANK

Each question carries a **status**:
`DAILY` answerable now · `PARTIAL` answerable with caveats ·
`5M` deferred to intraday data (Part 4).

---

## A. Event anatomy — what does a normal event look like?

**A1. What is the canonical shape of an addition and of a
deletion, from ann−45 to eff+20?** `DAILY`
Build an event-time average path (market-adjusted, indexed to
100 at ann) with a fan chart of p25/p50/p75. Separately for
ADD and DEL, and separately for survivor-safe vs survivors-only
markets. *This is the single most-requested chart on a
rebalance desk and every later answer refers back to it.*

**A2. How much of the total move happens before the
announcement?** `DAILY`
`pre_drift` vs `total_alpha`. If the market has already moved,
the announcement is not news and the trade is crowded. Report
the fraction of names where |pre_drift| > |drift|.

**A3. What share of events are non-events?** `DAILY`
Define a non-event as `vol_mult_eff < 2` AND `|total_alpha| <
1%`. Report by market. *China ran 61% non-events on an earlier
cut — verify against the corrected panel and explain any
change.*

**A4. How does the QUIET / CLEAN-DRIFT / FRONT-RUN-FADE /
SQUEEZE / MIXED mix vary by market and by side?** `DAILY`
Then: is the label stable for a given name across its repeat
appearances? A name that was QUIET last time — is it QUIET
again?

**A5. What does the volume profile look like day by day
through the window?** `DAILY`
Median volume ÷ ADV for each event-day offset, ann−10 to
eff+10. Identify where the volume ramp starts. *This is the
first read on how early other desks are working.*

---

## B. Demand sizing — how big is the trade, really?

**B1. What is the distribution of effective-day print size in
ADV days, by market and side?** `DAILY`
p10/p50/p90/max of `vol_mult_eff`. Present as an ECDF with the
desk's risk thresholds marked. *This is the number that sizes
the book.*

**B2. How well does estimated index demand predict the actual
effective-day volume?** `DAILY`
Regress `vol_mult_eff` on `demand_adv_days`. Report R², slope,
and the residual distribution. **If the relationship is weak,
that is the finding** — it means passive demand is not the main
driver of the print and something else (arb unwind,
discretionary, liquidity provision) is.

**B3. What multiple of estimated demand actually prints?**
`DAILY`
`vol_mult_eff / demand_adv_days`. A ratio far above 1 means the
market is trading around the event, not just for it.

**B4. Which is the better predictor of print size — index
weight, market cap, ADV, or free float?** `DAILY`
Rank-correlate each against `vol_mult_eff`. Join weights from
`apac_factsheet_top10.json` where available.

**B5. Does the estimated tracking AUM assumption change the
ranking of names, or only the level?** `DAILY`
Sensitivity: recompute `demand_adv_days` at 0.5×, 1×, 2× the
registered $180bn. If the ordering is stable the constant does
not matter for name selection — an important robustness result.

**B6. How much bigger is a deletion print than an addition
print, controlling for size?** `DAILY`
Match ADD and DEL on ADV decile and compare `vol_mult_eff`.
*The raw 6× vs 18× gap is partly a size artefact; strip it.*

---

## C. Timing — when should the client execute?

**C1. What is the drift distribution by side and market, and
what fraction has the wrong sign?** `DAILY`
`drift`, market-adjusted. **Report the hit rate, not just the
median.** A pod cannot size a trade on a median that is right
60% of the time without knowing it is 60%.

**C2. What is the optimal single execution day in hindsight,
and how much does it beat the effective close?** `DAILY`
For each event compute the return from each candidate day to
the effective close. Report the *distribution* of the best day
and the *average regret* of choosing the effective close.
**Then state plainly whether the best day is predictable
ex-ante or only in hindsight.**

**C3. How does a front-loaded schedule compare with the
effective close, in both P&L and tracking error?** `DAILY`
Simulate: 100% at eff close (the tracker benchmark); 25/25/25/25
over the last four days; 100% at ann+1. Report mean, median,
IQR and **tracking-error contribution** for each. *For the
tracker client the TE column is the answer, not the P&L
column.*

**C4. Is `capture` — the share of the move still available
after the announcement gap — stable enough to plan around?**
`DAILY`
Distribution of `capture` by market and side.

**C5. Does the announcement-day gap predict the subsequent
drift?** `DAILY`
`gap1` → `drift`. **These windows are disjoint, so this
correlation is legitimate** — contrast with the trap in §0.3.2.
If a large gap predicts weaker drift, the desk should trade
more on day 1 when the gap is large.

**C6. How many days before the effective date does the drift
actually accumulate?** `DAILY`
Cumulative market-adjusted return by event-day offset. Identify
the day at which 50% and 80% of total drift is realised. *This
sets the start date of the schedule.*

**C7. Is there a reliable pre-announcement signal?** `DAILY`
`pre_drift` sign and magnitude vs eventual side. If names that
will be added already drift up before the announcement, the
event is being anticipated — quantify by how much and whether
that is decaying over time.

---

## D. The effective-day print

**D1. What is the effective-day return distribution, and how
often does it move against the flow?** `DAILY`
`eff_day` by side. *An addition that falls on the effective day
is a liquidity-provision opportunity; count how often it
happens.*

**D2. Is the effective-day return related to print size?**
`DAILY`
`eff_day` vs `vol_mult_eff`. Non-linear — bucket rather than
fit a line.

**D3. What is the intraday cost of concentration?** `5M`
Deferred. Daily data cannot separate the closing auction from
the continuous session.

**D4. What share of effective-day volume goes through the
close?** `5M` (Taiwan `PARTIAL` — `auction5s_history.json` can
answer this for Taiwan alone; do that and label it as a
single-market result.)

**D5. How often does the effective-day print hit a price
limit?** `PARTIAL`
`tw_limits.json` carries a limit flag for Taiwan. Answer for
Taiwan; mark other markets as needing exchange limit data.

---

## E. Cross-sectional drivers — what makes a violent event?

**E1. Rank every candidate driver against event magnitude.**
`DAILY`
Drivers: ADV, market cap, index weight, free float, price
level, pre-event volatility, `demand_adv_days`, market,
side, review month, pre_drift. Targets: `vol_mult_eff`,
|`total_alpha`|, `eff_day`. Use rank correlation and report a
clean table. **Then say which two or three actually matter.**

**E2. Build a simple ex-ante "violence score" and test it out
of sample.** `DAILY`
Fit on 2015–2022, test on 2023–2026. Report lift over the
base rate in the top decile. **If it does not beat the base
rate, say so** — a negative result here is worth more than a
fitted curve.

**E3. Does illiquidity amplify the move super-linearly?**
`DAILY`
Bucket by ADV decile; plot median |total_alpha| and
`vol_mult_eff`. *Expect the small-ADV tail to dominate the risk
budget; quantify the shape.*

**E4. Do small markets behave differently from large ones after
controlling for name-level liquidity?** `DAILY`
Is "Malaysia is violent" a market effect or a size effect?

**E5. Does the number of simultaneous changes in a market
dilute or amplify each one?** `DAILY`
Count changes per market per review; test against per-name
magnitude. *A 40-name China review and a 2-name Taiwan review
are different trades.*

**E6. Is a repeat mover different from a first-timer?** `DAILY`
Join the changes DB history: has this name moved before? Test
magnitude and drift.

---

## F. The addition / deletion asymmetry

**F1. Quantify the asymmetry properly, survivor-safe only.**
`DAILY`
Taiwan and India only. Report drift, eff-day volume and total
alpha for ADD vs DEL. *The pooled 3× deletion asymmetry is
contaminated by survivorship; this is the honest number.*

**F2. How large is the survivorship bias?** `DAILY`
Compare the DEL statistics for survivor-safe markets against
survivors-only markets, controlling for ADV and market. The gap
is an *estimate of the bias*, and it is one of the most useful
things this dataset can produce.

**F3. India shows no add/delete asymmetry while Taiwan shows
3×. Both are survivor-safe. Why?** `DAILY`
Test the composition hypothesis: are Indian deletions
size-drift exits while Taiwanese ones are distress exits? Proxy
distress with pre-event drawdown and volatility.

**F4. Are deletions harder to trade than additions at the same
ADV multiple?** `DAILY`
Compare reversion and effective-day adverse moves.

---

## G. Reversion — what happens after

**G1. What is the reversion profile out to +20 days?** `DAILY`
`revert5`, `revert20` by side and market, with dispersion.
*Reversion is where the pod's exit lives.*

**G2. Does a bigger drift produce a bigger reversion?** `DAILY`
`drift` → `revert20`. **Disjoint windows — legitimate.**

**G3. Is the round trip profitable, and for whom?** `DAILY`
Enter at ann+1, exit at eff close vs eff+5 vs eff+20. Report
distribution and hit rate for each exit, net of a stated
round-trip cost assumption. **State the cost assumption
explicitly and test sensitivity to it.**

**G4. How long until the name trades like itself again?**
`DAILY`
Days until volume returns to within 1.5× of pre-event ADV.
*This is the desk's answer to "when is my position no longer an
index position".*

---

## H. Positioning, borrow and crowding

**H1. Does securities-borrowing build ahead of deletions?**
`PARTIAL` (Taiwan)
`borrow_build_pre` from `sbl_history.json`. Distribution, and
whether it predicts a squeeze.

**H2. Does a crowded short into a deletion produce a squeeze on
the print?** `PARTIAL` (Taiwan)
Test `SQZ` against `eff_day` and `revert5`.

**H3. Does Australian short interest behave the same way?**
`PARTIAL` (Australia)
`au_event_shorts.json`. *Two independent markets agreeing is
worth far more than one market's result.*

**H4. Do foreign, trust and dealer flows separate around
Taiwanese events?** `PARTIAL` (Taiwan, recent only)
`twse_institutional.json`. Who is on the other side of the
index trade?

**H5. Is the trade getting more crowded over time?** `DAILY`
Test whether `pre_drift` magnitude and `capture` have trended
since 2015. **A declining capture ratio is the single clearest
evidence of crowding**, and it is directly relevant to whether
the pod's strategy still works.

---

## I. Regime, calendar and seasonality

**I1. Did the Feb-2023 quarterly comprehensive review change
event magnitude?** `DAILY`
Split and test per market. Register that a period split is not
a controlled experiment.

**I2. Do the four review months behave differently?** `DAILY`
Feb / May / Aug / Nov, on magnitude and drift.

**I3. Has the announcement-to-effective window length changed,
and does length matter?** `DAILY`
Compute days between ann and eff per review; test against
drift and capture. *A longer window may mean more front-running
and less capture.*

**I4. What does the APAC-wide effective-day load look like, and
does a heavy night change per-name behaviour?** `DAILY`
Total names effective per date across markets (median 40, p90
127, max 346 on 2018-05-31). Test per-name magnitude against
the region-wide load. *Direct evidence on whether the desk's
capital is the binding constraint on the night.*

---

## J. Risk, tails and failure modes

**J1. What is the worst case?** `DAILY`
p99 and max of |total_alpha| and `vol_mult_eff`, named. For
each of the ten worst events, one line on what happened.

**J2. What fraction of total event risk sits in the top 5% of
events?** `DAILY`
Concentration of risk. *Determines whether a name-by-name or a
portfolio approach is right.*

**J3. Under what conditions does the drift signal fail?**
`DAILY`
Characterise the events where drift went the wrong way. Is
there a common feature — small ADV, high pre_drift, a heavy
review night, a specific market?

**J4. What is the maximum adverse excursion within the
window?** `DAILY`
For a position entered at ann+1 and held to eff, the worst
intra-window mark-to-market. **A pod sizes on MAE, not on the
final P&L.**

**J5. How often is a position not completable at reasonable
participation?** `DAILY`
Days at 20% of ADV required to complete the estimated demand.
Report the tail.

---

## K. Portfolio construction across markets

**K1. Which markets deserve the risk budget?** `DAILY`
Per market: median edge, dispersion, n per year, and edge per
unit of dispersion. Present as a scatter with n as the marker
size. **This is the capital-allocation answer.**

**K2. Are event outcomes correlated across markets within the
same review?** `DAILY`
If all APAC events move together on the night, the pod has one
position, not forty.

**K3. What is the capacity of the strategy?** `DAILY`
Aggregate estimated demand per review in USD, and per-name
ADV-day requirements. *At what AUM does this stop working?*

**K4. Does a market-neutral ADD-minus-DEL basket work?**
`DAILY`
Construct per review, report the return series, hit rate and
drawdown. **This is the closest thing here to a backtest of the
pod's actual book, so treat it with the most suspicion:** state
costs, state survivorship, state n.

---

## L. Benchmarking and TCA

**L1. What is the right benchmark for an index rebalance
order?** `DAILY`
Compare arrival, interval VWAP and closing price as benchmarks
against realised outcomes. Show why the choice changes the
apparent skill of the desk.

**L2. What would an implementation shortfall have been for each
of the three schedules in C3?** `DAILY`
Against a stated cost model. State it.

**L3. How should the desk report performance to a tracker
client versus a pod client?** `DAILY`
Two different scorecards from the same events; propose both.

---

## M. Data integrity (run these FIRST)

**M1. Re-run coverage and confirm the panel is what this brief
claims.** `DAILY`
`py scripts\apac_event_days.py coverage` and `gaps`. Record the
numbers you actually analysed.

**M2. Outlier identity check.** `DAILY`
For the 20 most extreme events by |total_alpha| and by
`vol_mult_eff`, verify the ticker matches the security name.
**Wrong-ticker events masquerade as spectacular findings** —
three were found this way already.

**M3. How much does the no-ticker third bias the panel?**
`DAILY`
Compare the tickered and untickered populations on market,
review, action and year. If untickered events are
systematically smaller or older, say so and bound the effect.

**M4. Does the Taiwan panel change materially now that TPEx
names are included?** `DAILY`
Compare pre-c-261 and post-c-261 Taiwan statistics. *OTC names
are smaller and less liquid; their absence biased Taiwan toward
the calm end.*

---

## N. Taiwan alternative data — the flow layer

Price data says *what happened*. These six datasets say *who
did it*, and they exist for Taiwan alone. Answer this section
before any other market, and treat it as the template for what
to go looking for elsewhere (Part 6).

**What is on disk, and what each one buys you:**

| dataset | file | shape | the question it unlocks |
|---|---|---|---|
| Closing-auction ladder, 5-second | `auction5s_history.json` | 3,024 days, 13:00→13:30 snapshots of bid/ask/matched | how the print *forms* |
| Securities borrowing balance | `sbl_history.json` | 3,024 days, `{code: [new, balance]}` | short positioning before deletions |
| Institutional net by stock | `twse_institutional.json` | foreign / trust / dealer net, per ticker per day | **who is on the other side** |
| Daily turnover value | `tw_daily_turnover.json` | 266 days by code | participation and ADV in value |
| Limit-hit flags | `tw_limits.json` | daily OHLC + limit flag | did the print jam against a limit |
| Turnover ratio (ATVR) | `tw_atvr.json` | monthly by code | the rulebook's liquidity screen |

**N1. Who absorbs an index addition — foreign, trust, dealer or
retail?** `DAILY`
`twse_institutional.json` around ADD events. Decompose net
buying by investor type across ann→eff. *Passive trackers in
Taiwan are largely foreign; the trust column is domestic
active. If trust is selling into foreign buying, the desk has a
natural counterparty and the print is cheaper than the ADV
multiple suggests.*

**N2. Does institutional net flow lead or lag the price
drift?** `DAILY`
Cross-correlate daily net flow against market-adjusted return
through the window. **Disjoint lags only** — see §0.3.2.

**N3. Does the borrow balance build before deletions, and does
it predict the squeeze?** `DAILY`
`sbl_history.json`. `borrow_build_pre` is already computed in
`event_window_metrics.json`; extend it to the full window and
test against `eff_day` and `revert5`. *A crowded short into a
deletion is the single most dangerous position on the desk.*

**N4. Does borrow *cost or availability* constrain the trade?**
`DAILY`
Balance vs the new-lending column. A balance near the available
pool means the short side is full and the squeeze risk is real.

**N5. What share of effective-day volume goes through the
closing auction, and how does that compare with a normal day?**
`PARTIAL`
`auction5s_history.json` gives Taiwan the answer that every
other market has to wait for 5-minute data to reach. **Do this
one now** — it is the single highest-value Taiwan-only result
in the bank.

**N6. How does the auction imbalance evolve over the last 30
minutes on an event day?** `PARTIAL`
The 5-second ladder from 13:00 to 13:30. Is the imbalance
visible early enough to trade against?

**N7. Do index events hit price limits more often than normal
days?** `DAILY`
`tw_limits.json`. A limit-locked print is an execution failure,
not a cost — the client does not get filled at all.

**N8. Does the foreign-ownership ratio move measurably around
the event?** `PARTIAL`
Foreign holdings per stock (MI_QFIIS). *A direct measurement of
passive accumulation, and the closest thing available to
watching the tracker buy.*

**N9. Combine them: build a Taiwan-only "who is trading this"
attribution for the ten largest events.** `DAILY`
One panel per event: price, volume, foreign/trust/dealer net,
borrow balance, auction share. **This is the exhibit a client
asks for after every big print**, and no other market in the
panel can produce it.

**N10. Which of these six signals actually adds predictive
power over price alone?** `DAILY`
Fit magnitude on price-based features, then add each flow
feature and measure the lift. **A flow dataset that does not
improve the forecast should be dropped from the pitch**, and
saying so is more valuable than adding it.

---

# PART 3 — LIVE APPLICATION: MSCI TAIWAN, AUGUST 2026

Apply the historical findings to the registered call. Announced
**12 Aug 2026**; rebalance close **31 Aug 2026**; effective
**1 Sep 2026**.

Source the names from `data/aug26_tw_call_v2.json` (and
`data/aug26_call_v2.json` for the corrected-threshold variant).
Do not retype them.

**Additions called:** 2408, 8046, 2344, 8299, 3189, 6274 (above
the 1.5× bar); 6770, 3036 (priority queue).
**Deletions called:** 2615 Wan Hai (float gate); 6919, 2834,
2609, 1101 Taiwan Cement, 3529 eMemory, 5871 Chailease, 3533
Lotes (displaced).

**P1.** For each name, estimate the index demand in shares and
in ADV days, using current ADV from the Taiwan panel. `DAILY`

**P2.** Place each name on the historical Taiwan distributions
from Part 2 — print size, expected drift, expected effective-day
move — and give a **percentile**, not a point estimate. `DAILY`

**P3.** Identify which of these names the history says will be
the violent ones, and why. Rank them. `DAILY`

**P4.** For each name, recommend a schedule, **stating which
client it is for**. The tracker answer and the pod answer will
differ and both should be given. `DAILY`

**P5.** Flag the borrow and squeeze risk on the deletion list
using `sbl_history.json`. eMemory (3529) and Lotes (3533) are
TPEx names — check whether TPEx names behave differently, given
they were absent from this panel until c-261. `DAILY`

**P6.** State the three things that would most change this
plan if they happened between now and 31 August, and how the
desk would detect each. `DAILY`

**P7.** Pre-register the expected outcome per name — print size
in ADV days, drift, effective-day move — so the call can be
graded on 1 September. Write these to
`data/aug26_expected_outcomes.json` **before** the print.
*A prediction that is not written down before the event is not
a prediction.* `DAILY`

---

# PART 4 — PARKED FOR 5-MINUTE DATA

Do not attempt these now. Record them as the intraday agenda.

**X1.** What share of effective-day volume executes in the
closing auction versus the continuous session, by market?

**X2.** What is the intraday shape of the effective day — when
does the index flow actually arrive?

**X3.** How much does the closing auction move against the
flow, and how quickly does it revert the next morning?

**X4.** Is there a measurable pre-auction imbalance signal in
the last 30 minutes?

**X5.** What is the realised cost of a VWAP schedule versus a
close-heavy schedule, at 5-minute resolution?

**X6.** Where in the day does the drift accumulate — overnight
gaps or the session?

**X7.** How wide are spreads through the event window, and what
does that do to the cost of trading early?

**X8.** Does the announcement (23:00 CEST, so the Asian
morning) produce a measurable opening gap and how fast does it
resolve?

**X9.** At what participation rate does market impact become
non-linear for these names?

**X10.** Can the effective-day auction imbalance be forecast
from the continuous session that day?

---

# PART 6 — THE ALTERNATIVE-DATA MANDATE

## 6.1 The task

**Run a comprehensive search for alternative datasets that
would let this question bank be answered better, market by
market.** This is a research task with a deliverable, not a
reading exercise.

For every candidate source, establish and record:

1. **What it is** — the exact report or endpoint name.
2. **Granularity** — per stock or market-wide? daily or
   weekly? *Market-wide weekly flow cannot answer a per-name
   event question, and a source that fails this test should be
   marked and dropped rather than harvested.*
3. **History** — how far back, and is it delisted-safe?
4. **Access** — free public endpoint, registration, or paid.
5. **Which questions it unlocks** — cite the question IDs.
6. **Retrieval** — a URL template with the parameters spelled
   out, or a clear statement that it needs a browser session.

Write the result to **`docs/ALTDATA_CATALOGUE.md`**, one
section per market, and update
**`data/altdata_registry.json`** so the probe script can test
it. Run `py scripts\altdata_probe.py` to check reachability
and record the actual response shape — **do not write a
harvester against a format you have not seen**. That mistake
cost this project the entire TPEx board for months (c-261) and
a thousand-fold volume error underneath it.

Where a source needs a browser session, a captcha, or a login,
**do not attempt to automate it**. Write the extraction script
so Bill can run it, document exactly what he must do by hand,
and mark the source `MANUAL` in the registry.

## 6.2 Taiwan is the worked example — six data TYPES

Taiwan is not special because it is Taiwan. It is special
because TWSE publishes six *types* of data, and every market
in this panel has some subset of the same six. Use this
taxonomy to know what to look for elsewhere.

| # | type | Taiwan source | why a rebalance desk needs it |
|---|---|---|---|
| 1 | **Closing-auction microstructure** | `MI_5MINS`, the 5-second ladder | The print happens in the auction. Without this you can measure the *result* but never the *formation*. |
| 2 | **Securities borrowing / short balance** | `TWT93U` | Crowding on the deletion side. The squeeze that hurts most is visible here days early. |
| 3 | **Investor-type net flow per stock** | `T86`, `TWT38U` | Identifies the counterparty. Foreign net buying into an addition IS the tracker; domestic active selling into it is the desk's liquidity. |
| 4 | **Foreign ownership / foreign room** | `MI_QFIIS` | A rulebook input (§2.2.8) *and* a passive-accumulation proxy. |
| 5 | **Turnover ratio** | `FMSRFK` | The ATVR liquidity screen — required to predict membership, not just to trade it. |
| 6 | **Price limits and halts** | daily files with a limit flag | A limit-locked print is a failure to execute, not a cost. |

**The transferable question for every other market is simply:
which of these six does the exchange publish, at what
granularity, and how far back?**

## 6.3 Per-market catalogue — what to look for

Confidence markers: `HAVE` already harvested · `LIKELY` public
and near-certain to exist, verify the format · `RESEARCH` find
out.

### Korea — the highest-value target after Taiwan
Korea has 102 priced windows and the second-worst violence in
the panel, and KRX publishes unusually well.

- `LIKELY` **KRX investor-type trading by issue** (foreign /
  institution / individual net, daily) — data.krx.co.kr, the
  same MDC/MDI loader we already call for other series.
  *Type 3. Unlocks N1–N2 for Korea.*
- `LIKELY` **KRX short-selling balance by issue**, daily.
  *Type 2. Unlocks H1–H2 outside Taiwan — and a second market
  agreeing is worth more than one market's result.*
- `LIKELY` **Foreign ownership limit and holdings by issue.**
  *Type 4.*
- `RESEARCH` **KOFIA** for securities lending detail.
- `RESEARCH` closing single-price auction data (KRX runs a
  10-minute closing call — richer than most).

### Hong Kong / China — CCASS is the prize
- `LIKELY` **HKEX CCASS shareholding by participant**, daily,
  per stock. *There is nothing else like this in the region:
  it shows WHICH custodian's holdings changed, so index-fund
  accumulation is directly observable. Type 3, and better than
  Taiwan's.*
- `LIKELY` **HKEX short-selling turnover by stock**, daily.
  *Type 2.*
- `LIKELY` **Stock Connect Northbound holdings per A-share**,
  daily. *The single most useful China series — foreign
  positioning in mainland names, which is exactly the passive
  flow.*
- `LIKELY` **SSE / SZSE margin-trading balance by stock**,
  daily. *Type 2 for the mainland.*

### Japan
- `LIKELY` **JPX short-selling balance ratio by issue**, daily.
  *Type 2.*
- `LIKELY` **Margin transaction balances by issue**, weekly.
- `RESEARCH` **Investor-type flow** — JPX publishes it weekly
  and *by market, not by stock*. **Check this carefully: if it
  is market-wide it fails the granularity test and cannot
  answer N1.** Say so rather than harvesting it.

### India
- `LIKELY` **NSE security-wise delivery position**, daily —
  delivered vs traded quantity. *No Taiwan equivalent, and a
  genuinely good crowding proxy: a spike in traded volume with
  flat delivery is intraday churn, not accumulation.*
- `LIKELY` **SLB (securities lending & borrowing) data.**
  *Type 2.*
- `LIKELY` **Bulk and block deals**, daily. *Names the
  counterparty on large prints — occasionally names the
  tracker outright.*
- `RESEARCH` FII/DII daily — likely market-wide only.

### Australia
- `HAVE` **ASIC short positions**, daily, per stock, in
  `au_event_shorts.json`. *Type 2, and delisted-safe.*
- `RESEARCH` **ASX closing auction** volume share.
- `RESEARCH` **Substantial holder notices** — a 5% crossing is
  public and names the holder.

### Thailand
- `LIKELY` **NVDR trading by stock**, daily. *Thailand's
  foreign-flow instrument. This IS the type-3 dataset for
  Thailand and there is no substitute.*
- `LIKELY` **SET investor-type summary** — check granularity.
- `LIKELY` **Short-selling report by stock.**

### Singapore, Malaysia, Indonesia, Philippines, New Zealand
- `LIKELY` **SGX daily short-sell report** by counter.
- `LIKELY` **Bursa short-selling and monthly foreign
  ownership.**
- `LIKELY` **IDX foreign net buy/sell by stock**, daily.
  *Indonesia is the violence outlier in this panel (p90 13.9%),
  so knowing whether foreigners drove it is disproportionately
  valuable.*
- `LIKELY` **PSE foreign buying/selling per stock** — note
  Philippines has no usable *price* source, so flow data
  cannot rescue it. Record and move on.
- `RESEARCH` NZX — expect little.

## 6.4 Ranking the effort

Do not harvest everything. Rank by **questions unlocked per
unit of work**, and prefer a dataset that lets a Taiwan finding
be *replicated* in a second market over one that adds a new
market with no Taiwan counterpart. A result that holds in
Taiwan and Korea is a finding; a result in one market is a
hypothesis.

Suggested order unless the research says otherwise:

1. **HKEX CCASS** — best-in-region, unlocks China and Hong Kong
   at once.
2. **KRX investor-type + short balance** — replicates N1–N4 and
   H1–H2 in a second market.
3. **Stock Connect Northbound** — the China passive proxy.
4. **NSE delivery** — a crowding measure nothing else provides.
5. **Thailand NVDR**, **IDX foreign net** — small n, but
   Indonesia is the tail-risk market.

---

# PART 5 — WHEN YOU ARE DONE

Write a closing section in `docs/REBALANCE_FINDINGS.md`:

1. **The five findings a client should act on**, each with its
   number, its sample and its confidence.
2. **The three results that surprised you** and why they might
   still be wrong.
3. **What the daily data cannot answer** and which of Part 4
   would close it.
4. **What you would harvest next**, ranked by value per unit of
   effort.

Then stop. Do not ask what to do next.

---

# PART 7 — STATUS AFTER THE TAIWAN PASS (c-270)

Answered in `docs/REBALANCE_FINDINGS.md`, computed by
`scripts/rebalance_analysis.py`, rendered at
**🔬 Taiwan Rebalance Insights**.

## Newly blocked, and NOT by the lack of intraday data

These were written as `DAILY` and are not. The obstacle is
source length, not resolution, so they will not be unblocked by
the 5-minute harvest.

- **N1, N4, N7 — `UNANSWERABLE-DAILY (source too short)`.**
  `twse_institutional.json` holds 22 days and `tw_limits.json`
  23, both recent. Neither can be joined to a 2015–2026 event
  panel. Backfilling TWSE's institutional day-files is the
  single highest-value data job left for Taiwan: "who is on the
  other side" is the question a client asks after every print.
- **F2, K1–K4 — deferred, not blocked.** They need the other
  twelve markets recomputed on the same market-adjusted,
  day-0-clean basis that Taiwan now uses. Running them on the
  old panel would compare a corrected market against
  uncorrected ones.

## Answerable now and worth doing next

- **N5, N6 — the closing-auction share and imbalance.**
  `auction5s_history.json` carries 3,024 days of the 13:00→13:30
  ladder. This is the highest-value Taiwan-only result still
  open and it does not need 5-minute data.

## What the Taiwan pass changed about the questions

- **A3 is answered in the negative and the negative is the
  finding.** Taiwan runs 0% non-events against China's 61%.
  Any question in this bank that assumes events can be triaged
  by expected size does not apply to Taiwan.
- **H5's premise did not survive.** Capture has *risen* since
  2015, not fallen, so on the bank's own test the trade is not
  getting more crowded — while pre-announcement drift has
  roughly doubled. The two move in opposite directions and the
  bank assumed they would move together.
- **N3 is a negative result.** Borrow build into a deletion has
  no relationship with the effective-day move (rho −0.02,
  n=62). The bank asks whether each flow dataset earns its
  place in the pitch; on this test borrow does not.
- **Every event-time statistic must state the day-0 sample.**
  44 of 176 priced Taiwan windows have an estimated
  announcement date that is 2–7 sessions wrong. §0.3.8 should
  be read as: name the sample *and its day-0 provenance*.
