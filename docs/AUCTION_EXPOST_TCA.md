# Close-Auction Ex-Post Review (TCA) — TW effective days (c-71)

*What the closing auction actually did on index effective days,
measured from data already on disk. DESCRIPTIVE ONLY: nothing
here is a registered hypothesis; patterns below are v6-registry
candidates and adopt nothing (v5 protocol rule 8).*

## Data honesty — what exists and what doesn't

Three layers, three very different answers to "do we have
auction data back to 2015?":

1. **The PER-STOCK intra-auction path (5-sec indicative
   price/volume, 13:25–13:30): disclosed live since June 29,
   2015, but NOT publicly archived.** [CORRECTED c-72 — this
   section originally said the disclosure began Mar-2020; that
   was the continuous-trading date. Simulated closing
   price/volume + best-5 disclosure started 2015-06-29, with a
   lighter form from Feb-2012.] The MIS feed remains real-time
   only; free historical per-stock paths do not exist, so this
   layer is still capture-forward for us
   (scripts/auction_capture.py, first live event Aug-31-2026).
1b. **The MARKET-WIDE 5-sec order/trade aggregates (MI_5MINS):
   OFFICIAL HISTORY 2015+ — found c-72 after the user pushed
   back on layer 1.** TWSE archives accumulated bid/ask order
   count+volume and accumulated trades every 5 seconds,
   09:00:00→13:30:00, INCLUDING the whole call window: trades
   freeze 13:25→13:29:55, order arrival keeps printing, and the
   13:30:00 row is the cross itself. Harvester added
   (roadmap_harvest.py auction5s — stores 13:00 reference +
   13:20:00-on rows, 122/day). The 2015 pilot already shows
   accumulated bid volume SHRINKING into the cross =
   cancellation-era behavior, a regime marker to respect when
   comparing eras.
2. **The auction OUTCOME (final print price + volume): YES,
   2015+.** The daily close IS the auction print; close price
   and volume are in the vintage/stock_day caches. The "78%
   median of deletion-day tape" figure came from this layer.
3. **The dislocation AROUND the auction (last continuous price
   vs the print, at 5-minute resolution): 2023+ only** — from
   the IB bar harvest (IB_FLOOR 2023-05). That layer is what
   this study measures.

## Panel

scripts/auction_expost.py -> data/auction_expost.json.
80 name-events, 17 events, 2023-05 -> 2026-05. Columns per name:
last_cont (last 5m close before 13:25), auction_px (official
close), disl_bps, pressure_bps (dislocation oriented WITH the
forced flow), pm_drift_bps, auction_share, t1_revert_bps
(oriented so + = dislocation decayed).

## What the data says (descriptive)

| | Adds (Buy) n=34 | Deletes (Sell) n=46 |
|---|---|---|
| median pressure_bps | **-14.8** | **-45.2** |
| % of prints pressed WITH the flow | 29% | 20% |
| median abs dislocation | 66 bps | 75 bps |
| median auction share of day volume | 44% | 72% |
| median T+1 revert (+ = decayed) | +182 | +50 |
| % decayed by T+1 | 65% | 57% |

**The headline: the auction print usually moves AGAINST the
forced flow.** On deletions, the close prints ABOVE the last
continuous price 80% of the time (median +45 bps against the
selling). On adds, the close prints BELOW the last continuous
price 71% of the time. The mechanism consistent with everything
else we've measured: by 13:25 the continuous tape has already
absorbed the day's pressure (pm drift), pre-positioned suppliers
are DONE, and the auction is where the other side — covering
shorts on deletes, supply on adds — finally prints. 2324 Compal
was the extreme of this pattern (deletion closing +9.6%), not an
exception to a rule.

**Practical TCA readings (rules-of-thumb, not adopted
signals):**

- A tracker selling a deletion at the close is NOT, on median,
  worse off than the 13:24 price — the print typically comes
  back through it. The MOC benchmark is less punitive than the
  pm tape makes it look.
- The T+1 decay medians are positive on both sides (adds fade
  hard, +182 bps; deletes bounce, +50 bps) — consistent with
  the panel's earlier reversal findings, now measured FROM THE
  PRINT rather than close-to-close.
- Deletes concentrate in the auction (72% of day volume) far
  more than adds (44%): add demand works the continuous
  session; delete supply waits for the cross.

## What the Aug-31 capture adds (ex-ante layer)

The 5-sec indicative path turns these post-mortems into
real-time decisions: convergence timing (when is the final
print knowable within x bps), late-surge anatomy (matched-size
steps in the last 30s), fade/pull detection (indicative pushed
then withdrawn), and imbalance-direction flips. Feature grammar
imported from the Optiver contest (Q37): indicative drift =
near/far spread, unmatched = imbalance, per-name MAE vs "predict
the range mid".

## Registry discipline

The against-the-flow print pattern and the auction-share split
are hereby NAMED as v6-registry candidates (direction on
record: pressure_bps < 0 on both sides; delete auction share >
add auction share). They were noticed IN this data, so they
may NOT be adopted from it — they get graded on data this study
never touched: Aug-2026 forward events.
