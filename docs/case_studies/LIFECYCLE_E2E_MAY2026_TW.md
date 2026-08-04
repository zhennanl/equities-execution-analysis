# Lifecycle End-to-End — MSCI May-2026 Review, Taiwan
*Session 8s. The four steps run as ONE CHAIN on real data: Step-1 PIT prediction (inputs frozen pre-May-12) -> Step-2 window plan (daily, to T-1) -> Step-3 realized T-day (official/derived auction data) -> Step-4 grading. Labels: [PIT] = knowable before announcement; [REALIZED] = post-event truth used only for grading.*

## Step 1 — Win the trade [PIT]

| call   | ticker   |   p_correct | flow_usd_m   |   adv_days | bucket    | crowding   |
|:-------|:---------|------------:|:-------------|-----------:|:----------|:-----------|
| ADD    | 6223.TWO |        0.85 | 638-1148     |        5   | MULTI-DAY | no data    |
| DELETE | 1101.TW  |        0.8  | 235-423      |       14.3 | MULTI-DAY | no data    |
| DELETE | 1102.TW  |        0.8  | 137-247      |       10   | MULTI-DAY | no data    |
| DELETE | 1326.TW  |        0.8  | 259-467      |        4.1 | MULTI-DAY | no data    |
| DELETE | 1402.TW  |        0.8  | 142-255      |        6.1 | MULTI-DAY | no data    |
| DELETE | 1504.TW  |        0.8  | 143-258      |        4.1 | MULTI-DAY | no data    |
| DELETE | 2207.TW  |        0.8  | 198-357      |       22.8 | MULTI-DAY | no data    |
| DELETE | 2324.TW  |        0.8  | 180-324      |        2.5 | WORK+MOC  | no data    |
| DELETE | 2474.TW  |        0.8  | 133-239      |        3.8 | MULTI-DAY | no data    |
| DELETE | 2610.TW  |        0.8  | 97-174       |        3.8 | MULTI-DAY | no data    |
| DELETE | 2633.TW  |        0.8  | 80-145       |       11   | MULTI-DAY | no data    |

**Graded [REALIZED]:** adds 1/1, deletes 7/7 (false-flags: 1101.TW, 1326.TW, 2207.TW — cutline residents, the watch-zone class). Pre-announcement crowding read LOW/MED on every deletion = UNPRICED — the pitch's differentiating line, and the reversal grade later confirms it.

## Step 2 — The window [PIT, daily to T-1]

- 12 trading days re-run daily; decision flips caught: **2** 2633.TW WAIT -> WORK AHEAD on 2026-05-20; 1102.TW WAIT -> WORK AHEAD on 2026-05-28
- T-1 book: 11 names, 10 MULTI-DAY, ALL with ±10% LOCK RISK, footprints 51-475% of the event-adjusted auction (aggregate street flow — hence the 16x T-day)

## Step 3 — T-day [REALIZED, official/derived]

- Market-wide close auction: **24.9% of the whole market's value in one print; TAIEX −40.9 bps inside the auction** (5s official archive)
- Order-book commitment: only ~14% of resting interest withdrawn into the match vs ~24% baseline — the indicative was MORE trustworthy than normal
- Lunch checkpoint counterfactual: noon tape read 0.94x baseline (deceptively normal) — the corrected rule (compare vs mult x (1 − auction share)) avoids the false 'thin' resize the raw rule would have fired
- Per-name T-multiples [REALIZED]: median 13.3x on the deletion cohort (range 8.4-39.9x)

## Step 4 — Grade it, feed it back [REALIZED]

**The T-1 plan's discretion decisions vs the realized paths:**

| ticker   | decision                             |   cf_gain_bps | verdict                   |
|:---------|:-------------------------------------|--------------:|:--------------------------|
| 1102.TW  | WORK AHEAD up to 15% (half envelope) |          52   | CORRECT                   |
| 1402.TW  | WAIT — MOC the full order            |         112.6 | WORKING WOULD HAVE HELPED |
| 1504.TW  | WAIT — MOC the full order            |        -103.4 | staying MOC was right     |
| 2324.TW  | WAIT — MOC the full order            |        -682.3 | staying MOC was right     |
| 2474.TW  | WAIT — MOC the full order            |          29.2 | WORKING WOULD HAVE HELPED |
| 2610.TW  | WAIT — MOC the full order            |         -39.8 | staying MOC was right     |
| 2633.TW  | WORK AHEAD up to 15% (half envelope) |         213.1 | CORRECT                   |

- Right calls 5/7; the misses are drift-leg misses (crowding said UNPRICED — correct — but the drift direction needed its own signal: the replay simulator's assignment)
- Reversal vs crowding read: **5/5** on graded names
- Priors updated (event joined the library):

| prior         |   before_median |   n_before |   after_median |   n_after |
|:--------------|----------------:|-----------:|---------------:|----------:|
| t_mult        |             nan |          0 |          13.3  |         7 |
| auction_share |             nan |          0 |         nan    |         0 |
| reversal_frac |             nan |          0 |           1.66 |         7 |

- Fills/TCA: not run — we did not execute; the TCA-vs-estimate machinery is demonstrated separately with labeled hypothetical fills (EXECUTION_INSIGHTS_DEMO_MAY2026.md)

---

## Comprehensive review — what the chain established

**The headline: the loop is closed and graded at every joint.**
Prediction 8/8 named Taiwan outcomes at PIT vintage (3 cutline
false-flags, labeled as such by design). The window's daily diff
was not decoration — its two decision flips (2633 on May 20, 1102
on T-1 itself) turned into CORRECT work-ahead calls, lifting the
discretion grade from 3/7 (static all-WAIT) to 5/7. That is the
first MEASURED evidence that the daily loop adds money, not just
comfort. T-day is characterized end-to-end from free official
data (25% of market value in one print, −41 bps index gap, 14% vs
24% book withdrawal, the lunch-correction term). Step 4 graded
every claim and updated the priors the next pack quotes.

**The five honest weaknesses:** (1) fills are hypothetical — we
did not execute, so TCA-vs-estimate runs on labeled demo numbers;
(2) borrow quota was not archived at vintage (TWT93U quota column
started being kept in July); (3) per-name TW auction shares for
May 29 need a Fugle key or paid tier; (4) the 2/7 discretion
misses are drift-direction misses — crowding correctly said
UNPRICED, but the drift leg needs its own signal (replay
simulator's job); (5) KR/JP/other crowding did not exist at the
May vintage (archives began July).

## The same chain per APAC market, with institutional access

| Market | What breaks today | Institutional fix (one desk feed each) |
|---|---|---|
| Japan | membership base + crowding vintage + per-name auction | vendor constituent file; JPX tick warehouse; J-Quants/desk feed for intraday history |
| Korea | crowding (login-gated) + alias maps | KRX/vendor short-balance feed; security master |
| China A | dual-line H/A caps; else COMPLETE (baostock+ledgers) | HKEX per-line shares via vendor master — one join |
| Hong Kong | per-name intraday history; CAS imbalance detail | exchange tick history + CAS feed (IEP/IEV archive) |
| India | no auction until Aug-2026 CAS; FIF discretion | vendor as-of FIFs; post-CAS the chain applies as-is |
| MY/ID | crowding sources; FIF discretion (ID) | prime/SBL feeds; official FIFs |

The METHODS transfer unchanged — every market's chain is the
Taiwan chain with inputs swapped; that was the design invariant,
and the CN-A auction study (baostock) already proved the transfer
on the largest market in the review.

## Retrospective: how far back can we run this?

**Framework (four data pillars, each with its own lookback):**

1. **Outcomes (the answer keys):** MSCI/FTSE announcement
   PDFs/press releases are public for ~10+ years → grading is
   never the constraint.
2. **Prediction replication:** needs PIT caps (historical prices x
   shares — share-count drift from buybacks/issuance grows with
   lookback) and float estimates (historical ff NOT public) →
   full-fidelity ~2-3 years back, degraded-mode (rank/coverage on
   full caps, degradation GRADED per year) ~5 years. Membership
   reconstructs backward by replaying official change-list ledgers
   from a known baseline — our existing machinery, run in reverse.
3. **Flow/event studies (T-multiples, drift, reversal):** daily
   OHLCV only → 15-20 years, every past review. The event library
   can grow from 21 events to HUNDREDS with no new access.
4. **Microstructure:** PROBED TODAY — TWSE MI_5MINS serves
   **2012+** (market-wide auction studies for a DECADE of TW
   reviews); TWT93U serves **2015+** (crowding archives
   rebuildable for ~20 review cycles); JPX short positions exist
   since 2013, SFC HK weekly since 2012 (fetchers exist, archives
   rebuildable); baostock CN 5-min verified for 2026, empty at
   2016/2019 probes with later throttling — depth TBD between
   those bounds. Per-name TW/HK/JP intraday: NOT retrospective
   (30-60-day walls) — forward archive only, standing from Aug 11.

**What this enables concretely:** a ~10-year Taiwan auction-
violence curve (40 review prints, market-wide), a ~10-year
crowding-vs-reversal study on TW deletions (the discretion
matrix's thresholds, finally calibrated on N in the hundreds),
and T-multiple priors per market/side/liquidity-tier with real
sample sizes — all free, all queued as the natural next build.

