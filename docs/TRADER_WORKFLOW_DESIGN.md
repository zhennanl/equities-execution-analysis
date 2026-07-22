# Trader Workflow Design — Making Page 2 Useful Mid-Rebalance

*2026-07-08. Companion to `INDEX_REBALANCE_RESEARCH.md`. Status: features F1–F5
implemented this session; F6–F7 specified here for a next build.*

## 1. The problem

Page 2 was built analyst-shaped: single name, charts first, recommendation
last, rationale in paragraphs, ex-post framing. A trader executing a
reconstitution runs 50+ names across markets, has seconds per decision, and
manages by exception. Two distinct users, one page:

| | Analyst (pre/post event) | Trader (inside the event) |
|---|---|---|
| Unit of work | one name, deep | a basket, wide |
| Reads | evidence → conclusion | conclusion → evidence (if ever) |
| Wants | methodology, caveats | shares, bps, buckets, RAG flags |
| Time budget | an hour | seconds |

Design rule: **invert the pyramid for the trader, keep the evidence layer for
the analyst.** Nothing analytic was removed — it moved below the verdict.

## 2. Implemented features

### F1. Verdict banner (recommendation-first)
After a study runs, the FIRST thing rendered is a one-line verdict computed
from the event study + insights + a default Agent-14 pass: side and shares,
recommended strategy for the selected objective, expected cost vs decision,
tracking vs the print, and an auction-capacity traffic light. Evidence
(summary table, charts, insight panels) renders below, unchanged.
Auction RAG thresholds: order as % of estimated closing-auction volume —
GREEN < 15%, AMBER 15–25%, RED > 25% (25% = Agent 14's AUCTION_STRESS_WARN).
Order size defaults to the flow-to-trade estimate when weight/AUM inputs are
provided, else 5% of ADV; side defaults from the Agent-12 event action
(Delete → Sell) and is overrideable in Agent 14's controls.

### F2. Trade card + exports
A plain-text, desk-readable card per name (ticker, side, order, bucket split
of the recommended schedule, auction RAG, expected cost/tracking, top risk
line, one-line reversal read) with download buttons:
- `<ticker>_trade_card.txt` — the card;
- `<ticker>_schedules.csv` — every strategy's day-by-day schedule (rel day,
  date, venue, shares, modeled fill/impact) for staging into an EMS.
Language rule: trader layer says "cheap to beta / crowd pressure / comes
back"; CAR, market model and citations stay in the analyst layer.

### F3. Conditional playbook (triggers, not allocations)
Traders execute triggers well; they don't re-derive analysis mid-event. The
playbook renders the recommended strategy as decision gates with computed
thresholds, e.g.: "If abnormal move A→T−1 exceeds 1.5× the event-library
median run-up, shift 20% of the remaining pre-position to post-effective";
"If order > 25% of estimated auction volume at T−1, pre-position the excess."
Thresholds are proposals anchored on this event + the library; the trader
confirms or overrides. Downloadable as text.

### F4. Basket mode (exception blotter)
Upload a CSV (`ticker,market,side,shares` — `shares` optional, defaults to
flow sizing) for the whole program; the app runs the event study per name
against one effective date and returns a severity-ranked exception table:
auction-capacity RAG, reversal class, run-up so far, est. cost of the
tracker trade — worst first, CSV-downloadable. Failures degrade per name
(IPO/spin-off names report their error in-row; the rest still run).
Network note: one study per name — a 50-name basket is ~100 yfinance daily
fetches; run it once pre-event, not repeatedly.

### F5. Event library (anecdotes → priors)
Every completed study auto-records one row (ticker, index, market, T, run-up,
reversal fraction & class, drift %-after-announcement, implied η, σ, ADV) to
`data/event_library.json`. The insights section then shows "this event vs
library median (n=…)" context, and the playbook pulls its thresholds from
library medians once n ≥ 3. This is the pragmatic first step toward
cross-sectional calibration — single-event η stays labelled order-of-magnitude.

## 3. Specified, not yet built

### F6. Live-day mode (= backlog B4, extended)
Intraday volume-run-rate vs expected ("volume running 1.8× — auction capacity
revised up"), auction-imbalance proxy from the final bars, "you are here" on
the schedule. Belongs with Page 1's live session plumbing; do B4 first, then
surface it on Page 2's card.

### F7. Distributional strategy simulation
Replace the single realized path with the event library's normalized
pressure/reversal path distribution once n is meaningful (≥ ~15 events per
market): simulate S1–S4 across percentile paths → expected cost ± bands, and
recommend by minimax regret rather than ex-post optimality. The honest
labelling requirement carries over: report n, dispersion, and market mix of
the library sample on every output.

### F8. One click to execution (Page 1 handoff)
"Stage in simulator" button: recommended schedule → Agent 3 ticket(s) per leg
(MOC/POV/IS already exist), then post-event TCA feeds the library back.

## 4. Files

- `agents/trader_view.py` — all F1–F5 logic (pure functions, injectable
  study-runner for offline tests; no Streamlit imports).
- `app.py` Page 2 — banner, downloads, playbook expander, basket expander,
  library capture + context captions.
- `tests/test_trader_view.py` — offline coverage of RAG thresholds, card and
  CSV content, playbook trigger arithmetic, basket ranking with a synthetic
  study runner, library round-trip and medians.
- `data/event_library.json` — created on first recorded run (git-ignorable;
  it is derived data).
