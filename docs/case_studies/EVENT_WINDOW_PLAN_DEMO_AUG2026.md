# Step-2 Window Plan — DEMO basket, Aug-2026 QIR (eff Sep 1)
*Generated 2026-07-28 by agents/event_window.py — lifecycle Step 2 workstreams 2.2 + 2.3. Deterministic; every discretion decision ships with its best-ex rationale. Effective date 2026-09-01.*

## 2.2 Liquidity & risk per name

| ticker   | market           | side   |   adv_days | exp_t_vol_mult   |   auction_footprint_pct |   band_pct | limit_risk       | borrow                          | halt_flag   | bucket    |
|:---------|:-----------------|:-------|-----------:|:-----------------|------------------------:|-----------:|:-----------------|:--------------------------------|:------------|:----------|
| 1101.TW  | Taiwan (TWSE)    | Sell   |       0.14 | 16x (max 38x)    |                     2.9 |         10 | LOCK RISK (±10%) | TIGHT (98% of implied capacity) | -           | MOC       |
| 2207.TW  | Taiwan (TWSE)    | Sell   |       2    | 16x (max 38x)    |                    41.7 |         10 | LOCK RISK (±10%) | TIGHT (97% of implied capacity) | -           | WORK+MOC  |
| 1326.TW  | Taiwan (TWSE)    | Sell   |       1.33 | 16x (max 38x)    |                    27.8 |         10 | LOCK RISK (±10%) | ok (55%)                        | -           | WORK+MOC  |
| 2002.TW  | Taiwan (TWSE)    | Sell   |       5.79 | 16x (max 38x)    |                   120.6 |         10 | LOCK RISK (±10%) | TIGHT (97% of implied capacity) | -           | MULTI-DAY |
| 0027.HK  | Hong Kong (HKEX) | Sell   |       0.43 | 16x (max 38x)    |                     8.9 |        nan | -                | no quota data                   | -           | MOC       |
| 9995.HK  | Hong Kong (HKEX) | Buy    |       2.14 | 16x (max 38x)    |                    44.6 |        nan | -                | no quota data                   | -           | WORK+MOC  |
| 4004.T   | Japan (TSE)      | Buy    |       2    | 16x (max 38x)    |                    41.7 |        nan | -                | no quota data                   | -           | WORK+MOC  |

## 2.3a Start schedule (multi-day names)

| ticker   | bucket    |   days_needed | start_date   | status                                |
|:---------|:----------|--------------:|:-------------|:--------------------------------------|
| 1101.TW  | MOC       |             1 | T            | auction-window name                   |
| 2207.TW  | WORK+MOC  |             1 | T            | auction-window name                   |
| 1326.TW  | WORK+MOC  |             1 | T            | auction-window name                   |
| 2002.TW  | MULTI-DAY |            24 | 2026-07-30   | start 2026-07-30 at 25% participation |
| 0027.HK  | MOC       |             1 | T            | auction-window name                   |
| 9995.HK  | WORK+MOC  |             1 | T            | auction-window name                   |
| 4004.T   | WORK+MOC  |             1 | T            | auction-window name                   |

## 2.3b Discretion decisions (documented)

- **1101.TW** (Sell): WORK AHEAD up to 30% of order pre-close
  - crowded delete: street pre-sold, pressure part-spent, covering bounce enlarged — working ahead beats donating the close to the covering crowd; evidence: crowding read 'HIGH (+53%/30obs)'
- **2207.TW** (Sell): WAIT — MOC the full order
  - uncrowded/unknown delete: pressure arrives at the print; pre-trading a clean close adds impact and tracking for nothing; evidence: crowding read 'LOW (-37%/30obs); EXITING (-43% off peak)'
- **1326.TW** (Sell): WAIT — MOC the full order
  - uncrowded/unknown delete: pressure arrives at the print; pre-trading a clean close adds impact and tracking for nothing; evidence: crowding read 'LOW (-52%/30obs); EXITING (-62% off peak)'
- **2002.TW** (Sell): WAIT — MOC the full order
  - uncrowded/unknown delete: pressure arrives at the print; pre-trading a clean close adds impact and tracking for nothing; evidence: crowding read 'LOW (-12%/30obs); EXITING (-34% off peak)'
- **0027.HK** (Sell): MOC ONLY
  - no discretion envelope granted — benchmark print is the mandate; evidence: crowding read 'HIGH (+84%/8obs)'
- **9995.HK** (Buy): WORK INTO CLOSE — no pre-positioning
  - crowded add: jump already partly priced (consensus); pre-positioning pays the crowd's mark; evidence: crowding read 'HIGH (+45%/8obs)'
- **4004.T** (Buy): PRE-POSITION up to 25% within envelope
  - uncrowded add (unpriced): the close will jump; the envelope exists to capture part of that move; evidence: crowding read 'HIGH (+460%/4obs); EXITING (-18% off peak)' — EXITING tag: crowd leaving pre-T, treated as uncrowded

## Notes

DEMO basket: quantities hypothetical (span the buckets); names/sides = live boundary reads from AUG2026_QIR_ASIA_PACK appendix. T-multiple = measured MSCI-Sell library (median 16x, max 38x) applied to all lines for the demo — per-side/per-provider in production. Borrow utilization live TWT93U (Taiwan only — the one public quota file); HK/JP lines honestly show 'no quota data'. Auction footprint uses the measured ~30% close share of T-day volume. 0027.HK has NO envelope on purpose — the plan shows discretion is not exercised where it was not granted.
