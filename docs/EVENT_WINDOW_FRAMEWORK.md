# The Announcement→Effective Framework (c-128)

A systematic, point-in-time process for analyzing each stock in
an index review between the announcement and the effective
close — built so the same seven steps run identically on a
2015 window (with the answer known) and on the live Aug-2026
names (with data arriving daily).

The design rule carried over from the prediction engine: every
step produces a NUMBER with a SOURCE and a VINTAGE, every
threshold is registered before grading, and misses ship.

---

## Step 0 — The event frame (conventions, fixed once)

| Item | Convention | Why |
|---|---|---|
| Day 0 | announcement date's **Taipei close** | Geneva announces ~23:00 CET = ~05:00 Taipei next morning; day-0 close is the last pre-news print |
| Day 1 | first session after announcement | first print that can react |
| E | effective date (last trading session of the review month) | the close where trackers must transact |
| Baseline ADV | median daily volume over the **20 sessions ending day 0** | denominators; pre-news by construction |
| Pre-window | day −25 … day 0 | pre-positioning lens |
| Post-window | E+1 … E+20 | reversion measurement |

All flow quantities are expressed two ways: raw, and in
**ADV-multiples** (so a $40B name and a $5B name are
comparable).

## Step 1 — Demand: how much MUST trade

The anchor for everything else. For an addition:

```
expected_passive_shares = weight_in_index × tracking_AUM / price
weight_in_index         ≈ float_cap / index_float_cap
```

- float_cap from the weights-inversion FIFs (members) or the
  add-side float stack;
- index float cap from the factsheet ($3,183B for TW Jul-31);
- tracking_AUM is a DECLARED ASSUMPTION (registered constant
  with a band, tuned later against observed effective-day
  prints — the decade auction data grades it).

Deletions mirror it with sign flipped. Output per stock:
**expected demand in shares, in ADV-multiples, and expected
effective-close share of volume.**

## Step 2 — Flow decomposition, day by day

From the decade caches (2015→, per stock per day, harvested):

| Series | Source | Reading |
|---|---|---|
| Foreign net buy (shares) | t86 | the main index-flow proxy in TW — trackers and arbs are overwhelmingly foreign |
| Borrow balance | TWSE SBL | the short leg on deletions; build = anticipation, unwind = cover |
| Margin long / short sale | margin | the domestic-retail leverage taking the other side |
| Block prints | blocks | negotiated size = desks crossing |
| Volume vs baseline ADV | STOCK_DAY | heat |

The core derived series per stock:

```
progress(t)  = cum_foreign_net(day1..t) / expected_passive_shares
```

**progress is the single most decision-relevant number in the
window**: if 80% of expected demand has printed by E−3, the
close is NOT where the flow will be; if 20%, brace the auction.

## Step 3 — Price-path metrics (per window)

Computed against day-0 close = 0, market-adjusted by the same
metric on **0050** (the market proxy that shares the exact
data source and calendar):

| Metric | Definition |
|---|---|
| `gap1` | day-1 return (the instant repricing of the news) |
| `drift` | day-2 → E−1 cumulative (what's left for latecomers) |
| `eff_day` | E return (the print trackers receive) |
| `into_close` | E return vs E−1 close — the auction pressure |
| `revert5 / revert20` | E+1→E+5 / E+20 — how much was temporary |
| `total_alpha` | day1 → E−1 (the whole tradeable anticipation) |
| `capture` | drift / (gap1+drift): how much of the move was NOT instantaneous — the room the slow money had |

## Step 4 — Crowding scorecard (the judgment layer, quantified)

Per stock, three scores in [0,1], thresholds registered
BEFORE the Aug-26 grading (percentile-anchored on 2015-2025
windows):

- **PRE**: pre-positioning — pre-window drift percentile +
  borrow build (DEL) or foreign accumulation (ADD) before
  day 0. High PRE = the prediction was consensus; expect small
  gap1, weak drift, larger reversion.
- **PROG**: execution progress vs demand (step 2) at each t.
  High early PROG = flow front-loaded; fade the close.
- **SQZ** (deletions): borrow balance / float vs its own
  history + margin-short share. High SQZ = recall/cover risk
  into E; deletions can RALLY into effective when crowded.

## Step 5 — Window classification (labels for learning)

Each historical window gets one label by registered rule:

| Label | Signature |
|---|---|
| `CLEAN-DRIFT` | low PRE, monotone drift, eff-day flow ≥60% of demand, small reversion |
| `FRONT-RUN-FADE` | high PRE, gap1 ≈ total move, drift ≤0, reversion >50% |
| `SQUEEZE` | DEL with high SQZ and positive drift into E |
| `QUIET` | |gap1| <1σ and volume <2× ADV — the market disagreed with the call |

The label distribution BY ERA is itself a finding: if
FRONT-RUN-FADE share is rising, the trade is getting crowded
secularly, and the desk's advice changes accordingly.

## Step 6 — Cross-event aggregation (the playbook tables)

Aggregated over 2015-2026, split by action and by
demand-in-ADV bucket (<2, 2-5, >5 ADV-days):

1. median cumulative-return path day −25…E+20 (the fan chart)
2. median progress path (when does the flow actually print)
3. effective-day: volume multiple, close-auction share,
   into_close, next-day reversion
4. label frequencies by era

These four tables ARE the desk playbook: "deletions of 2-5
ADV-days typically print x% through fair value by E−1 and
revert y% by E+5" is the sentence a client pays for.

## Step 7 — The live loop (Aug-2026, point-in-time)

From Aug-12 (first reaction session), daily at the close, for
every name on the declared shortlist:

```
py scripts\event_window_live.py pull    # day's t86/SBL/margin/px
py scripts\event_window_live.py report  # scorecards vs history
```

Each daily report states: progress vs demand, PRE/PROG/SQZ vs
the historical distribution at the same day-offset, and the
implied stance for the effective close (how much flow remains).
Every daily report is APPENDED, never overwritten — the ledger
is the deliverable, and it grades itself on Sep-1.

---

## PART II — The effective-day liquidity model (c-128b, the
## decomposition Bill asked for)

GOAL: for each name in a review, predict (a) the LIQUIDITY that
will print on the effective date, especially at the close, and
(b) how much of the index demand is ALREADY PRE-POSITIONED
before that date — using, at every historical evaluation point,
only data available before that point.

Broken into five pieces, each independently buildable, gradable
and small enough to run without supervision:

### Piece A — Ground truth: what actually printed (build first)
For all 115 historical windows: effective-day volume, its
ADV-multiple, and (where derivable) the close-auction share.
Sources: tw_event_windows (have), auction_shares_derived +
auction_expost for recent reviews (have), IB 5-minute bars for
2023+ events (have — intraday close-share directly).
OUTPUT: data/eff_day_truth.json — the label set every later
piece is graded against. NO modelling, pure measurement.

### Piece B — Demand model, calibrated not assumed
expected_shares = weight × AUM / price, with AUM fitted:
regress observed effective-day excess volume (A) on weight/price
across 2015-2025 — the slope IS the effective tracking AUM per
era. Grades the declared $180B and replaces it with a fitted
curve (AUM grew over the decade; one constant is wrong by era).
PIT rule: predicting review r uses the AUM fit from reviews < r.
OUTPUT: aum_fit.json + demand per name per review.

### Piece C — Pre-positioning ledger (the supply side)
Per name, per day t in the window: cumulative ABNORMAL foreign
net buy since day −25 (abnormal = net of that name's own
pre-event baseline), borrow build (DEL), margin-short change,
block prints. All divided by Piece-B demand:
    prepositioned(t) = inventory(t) / expected_demand
OUTPUT: a per-day series ending at E−1 = "how much of the trade
was done before the close" — THE number the desk quotes.

### Piece D — The close-liquidity predictor
Predict effective-day volume and close share from: residual
demand (B minus C at E−1), ADV, action, demand-in-ADV bucket,
era. Start with the median-path lookup table (no ML — medians
by bucket), add regression only if the table's walk-forward
MAPE justifies it. PIT: fit on reviews < r, predict r, ledger
every prediction.
OUTPUT: eff_liquidity_model.json + walk-forward scorecard.

### Piece E — New data worth acquiring (ranked by lift/cost)
1. **Per-stock closing-auction volume history** (TWSE
   after-hours file) — turns close-share from derived to
   measured. [Bill's terminal, one endpoint to find]
2. **EWT daily shares outstanding history** (iShares) — the
   passive creation/redemption leg measured directly.
3. **TAIFEX single-stock futures OI** on movers — the
   borrow-free positioning route (harvester exists: taifex).
4. TDCC weekly dispersion around events (have, wire in).
5. TSM ADR premium series (sentiment tell, cheap).

### Autonomy contract (so this runs while Bill is away)
Run order A -> B -> C -> D; each piece writes its JSON +
appends a session-summary block; each declares thresholds
BEFORE grading; anything anomalous (a piece contradicting an
earlier measurement, coverage below 80%, a sign flip vs the
playbook) HALTS that piece and records the anomaly instead of
proceeding. Data acquisition (E) is proposed, never assumed.

## Data coverage honesty box

| Input | Coverage | Gap |
|---|---|---|
| Price windows (incl. delisted) | 2010→2026 via TWSE | pre-2010 survivors only; TPEx movers pending endpoint |
| Announcement dates | exact 2015+; eff−10bd EST 2010-14 | pre-2010 |
| t86 / SBL / margin | 2015→2026 complete | none in that range. NOTE: 2015 is where WE start, not where TWSE stops — TWT93U served 2014-06-16 on probe (c-225) |
| Blocks / daytrade / auction 5s | 2015→2026 complete | auction detail is market-level pre-2026; and the 5-SECOND grid itself only begins 2014-12-29 (c-228) — coarser before that, so no auction PATH earlier |
| Tracking AUM | declared assumption | graded against effective-day prints |
