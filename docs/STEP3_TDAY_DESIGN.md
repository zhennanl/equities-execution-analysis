# Step 3 — T-Day Execution: Data, AI Leverage, and the Simulation Suite

*Design doc, session 8i (2026-07-28). Lifecycle Step 3 (3.1-3.4) is
the one step that is intrinsically REAL-TIME — so the honest design
question is: what can be built now that is (a) genuinely useful with
public data, (b) gradable, and (c) shaped so desk feeds slot in
without redesign. Answer: a measured-parameter layer + a replay
simulator, with the live cockpit as the desk-side endpoint.*

---

## Part 1 — The data landscape (probed and verified today)

### What T-day analysis actually needs

Intraday volume curves (run-rate model), per-name closing-auction
volume (footprint + violence), indicative auction feeds (the one
real-time decision), limit states, halts/amendments. Daily OHLCV —
our current yfinance diet — sees NONE of this directly. But:

### Verified today, free, from this sandbox

| Source | What it gives | Verified fact |
|---|---|---|
| yfinance intraday | 1-min bars ~7 days back; 5-min bars ~60 days back, TW/JP/HK/KR | 2330.TW and 0027.HK pulled clean; 60 days covers the June TW50 AND May-MSCI effective days — event-day curves are measurable NOW |
| yfinance auction derivation (TW) | TW intraday bars END at 13:20-13:25 — the 13:30 auction print is EXCLUDED. So **close-auction volume = daily volume − Σ intraday bars** | 2330.TW Jul-24: 21.6M daily − 16.3M bars = 5.4M ⇒ **24.8% auction share, derived** — per name, per day, free |
| yfinance auction read (HK) | The CAS print IS the last bar (16:05-16:08) | 0027.HK Jul-24: bars sum ≈ daily; last bar = the auction |
| TWSE OpenAPI (openapi.twse.com.tw) | Free, keyless, ~143 endpoints; **MI_5MINS = 5-SECOND market-wide accumulated bid/ask orders/volume** — auction-period order-flow context, archivable daily | probed live today, JSON clean |
| TWSE MIS indicative snapshot | 13:25-13:30 indicative price/volume — the T-day decision input | parser exists (`parse_auction_snapshot`); live-only, no history — we ARCHIVE our own starting now |

### Upgrade paths (researched, not yet needed)

- **J-Quants (JPX official)**: free tier is 12-week-delayed daily —
  useless for T-day; minute bars + ticks are a ¥5,500/month add-on on
  Light plan or higher (added Jan 2026). The cheap, official JP
  intraday-history upgrade when the event library needs depth.
- **EODHD** (~$30-80/mo): Asian 5m/1m history back to Oct-2020,
  coverage varies by ticker — the cheap cross-market historical-depth
  path (event days older than yfinance's 60-day window).
- **KRX/KIS**: account-gated APIs; desk feeds supersede.
- **On the desk**: real-time everything — the design below keeps
  every consumer replay-driven so live feeds are a drop-in.

---

## Part 2 — AI leverage on T-day: high execution quality by design

**The principle (from the lifecycle doc): T-day is the disciplined
execution of decisions already made. So T-day AI adds ZERO new
judgment — it compresses reaction time on pre-made decisions and
keeps vigilance constant while the cascade runs.** Every trigger
below is deterministic; the LLM's only job is drafting language on
top of computed numbers.

**3.1 Pre-open.** The overnight sweep is a machine pass: Reg-Watch
diff (provider late amendments, halts) + CA radar → any touched name
re-versions the basket and re-runs the full validation chain before
the dealer sits down; staged orders diff against the final file
mechanically; the run-sheet (every market's cutoff cascade in HKT)
generates from the rules registry. Dealer's pre-open act: read the
exception list, not build it.

**3.2 Continuous session.** An exception engine, ranked by
dollar-at-risk: run-rate vs plan bands per working leg; limit
proximity (live price vs band table — the LOCK RISK names from the
Step-2 sheet get tighter thresholds); halt detection; cash-balance
drift vs the client's neutrality constraint. THE LUNCH CHECKPOINT
MECHANIZED: posterior T-multiple from the half-day run-rate (the
mapping measured from event-library intraday curves — Part 3.4) →
if the tape says 8x not 16x, the engine proposes the auction resize
with its arithmetic shown; the dealer approves or overrides.

**3.3 The close cascade.** Per market: countdown discipline off the
registry cutoffs (TW 13:25 / KR 15:20 / JP 15:25 / CN 14:57
no-cancel / HK CAS phases); for Taiwan, the indicative read
13:25-13:30 — indicative volume vs expected T-multiple, indicative
price vs limit bands — feeds the ONE real-time decision (final
envelope sizing) as a framed recommendation: "indicative at 9x vs
16x expected ⇒ thin auction, violence risk HIGH ⇒ within envelope,
retreat X% to T+1 plan B." AI frames it with the violence curve
(Part 3.2); the dealer takes it. Special-handling playbooks
(limit-locked queue-or-retreat, halted fallback, foreign-room-full)
surface from the T-1 contingency notes automatically when their
trigger fires.

**3.4 Post-close.** Fills vs official close verified per line the
moment both exist; the client flash drafts itself ("done; 96% at the
close; tracking +2.1 bps; residual plan"); exceptions write the
intraday note. The cascade rolls to the next market and the same
machinery repeats. Nothing waits for the evening.

---

## Part 3 — The simulation suite: the analysis we can generate NOW

Six analyses, ordered by build value. Each has a defined output and
a grading path — the same discipline as the prediction engine.

### 3.1 Auction-share measurement study (build FIRST — data verified)

Per-name close-auction share: TW derived (daily − Σ intraday), HK
read (last bar), JP (close bar at 15:30), across the trailing 60
days — normal-day baseline vs EVENT-day share for the June TW50 and
May-MSCI names. Output: measured per-market auction shares with
event uplift, replacing the assumed flat 30% in the Step-2 footprint
column. Gradable: Sep-1 event days land inside the 60-day window of
a early-Sep run — predicted vs realized share per name.

### 3.2 The auction violence curve

Across the 21+ event library: event-day close-auction return vs
volume multiple (and auction share). The claim "thin auction =
violent print" becomes a fitted curve with scatter shown — the
quantitative core of the 3.3 indicative-read rule ("indicative 9x vs
16x expected ⇒ expected print deviation Y bps"). Honest caveat: ~20
points, so a banded prior, not a precision model; every new event
adds a point.

### 3.3 The T-day replay simulator (the centerpiece)

Replay measured event days bar-by-bar (5m curves) and execute the
FULL Step-2 plan against the realized path: MOC leg at the derived
auction print, WORK+MOC legs at planned participation on realized
bars, MULTI-DAY legs across days, discretion choices as branches.
Output per plan variant (MOC-only / work-ahead / pre-position):
slippage vs the official close, tracking difference, completion
rate, limit-lock encounters. THE COUNTERFACTUAL ENGINE: "on the May
deletion names, what would each discretion choice have cost?" —
which turns the Step-2 rule matrix from argued to measured, and
produces the client-facing artifact ("our discretion logic, graded
on the last event, with the counterfactuals shown").

### 3.4 Lunch re-forecast backtest

On every event day in the library: at half-session, predict the
final T-multiple from the run-rate curve; measure the error
distribution. Output: either a validated 3.2-checkpoint rule
("half-day run-rate predicts final multiple ±X%") or an honest kill
("no signal at lunch — resize at 13:00 instead"). Both are useful;
only one gets deployed.

### 3.5 Limit-lock scenario model

For static-band markets: P(close unreachable) given the measured
event-day drift distribution per side; expected T+1 residual and its
cost under band reset. Quantifies the deferral taxonomy and prices
the "queue-or-retreat" decision the 3.3 playbook triggers.

### 3.6 Cascade run-sheet generator

Deterministic and small: the HKT timeline across all covered markets
from the rules registry, per-basket (only markets with lines),
cutoffs + no-cancel windows + indicative windows, contingency
references attached to flagged names. The T-day cockpit's skeleton.

### Plus one standing data job

**Archive the indicative auction feed ourselves from Aug 11**: the
MIS snapshot is live-only; nobody has its history. Every event we
archive builds the indicative-vs-final dataset that desk-grade
auction models train on — a proprietary asset from a free feed.

---

## Honest limits

yfinance 5m depth is 60 days (older events need EODHD/J-Quants);
TW auction derivation includes odd-lot noise (small, stated);
indicative history starts when our archive does; the violence curve
is ~20 points; KR intraday untested from sandbox; and the live
cockpit remains PROTOCOL until desk feeds exist — everything else
runs today.

## Proposed build order

1. Auction-share study (3.1) — data verified, feeds Step-2 today
2. Replay simulator (3.3) — the centerpiece analysis
3. Violence curve (3.2) + lunch backtest (3.4) — from the same replay
   data pass
4. Run-sheet generator (3.6) + indicative archiver (standing job)
5. Limit-lock model (3.5)
