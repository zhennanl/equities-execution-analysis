# Step-2 Window Replay — May 2026 TW Basket (announcement -> T-1)
*Session 8n. Basket = the Step-1 PIT predictions, sized by the engine's own flow midpoints. Analysis re-run each trading day on data through that day only; below: the daily decision-flip log and the full T-1 (May 28) plan — the night-before state. Grading context: 7/7 deletions and the MPI add were correct calls; 2324.TW read is the one the Step-4 replay later graded (WAIT was wrong there — drift +2274bps into the close).*

## Daily loop (12 trading days, May 13 -> May 28)

**Day-1 baseline reads (May 13):** 1101 MED (+16%/12obs); 1102 LOW (-0%/12obs); 1326 LOW (-31%/12obs); 2207 MED (+9%/12obs); 2324 LOW (+1%/12obs); 2474 LOW (-5%/12obs); 2610 LOW (-2%/12obs); 2633 LOW (+4%/12obs)

**Decision flips during the window** (the daily diff — silence on unchanged names):

| date       | ticker   | flip               | trigger         |
|:-----------|:---------|:-------------------|:----------------|
| 2026-05-20 | 2633.TW  | WAIT -> WORK AHEAD | MED (+6%/17obs) |
| 2026-05-28 | 1102.TW  | WAIT -> WORK AHEAD | MED (+6%/23obs) |

**T-1 crowding reads (through May 28):** 1101 HIGH (+44%/23obs); 1102 MED (+6%/23obs); 1326 LOW (-13%/23obs); 2207 MED (+17%/23obs); 2324 LOW (+1%/23obs); 2474 LOW (-7%/23obs); 2610 LOW (-2%/23obs); 2633 MED (+15%/23obs)

## The T-1 plan (the night-before book state)

### 2.2 Liquidity & risk

| ticker   | market        | side   |   adv_days | exp_t_vol_mult   |   auction_footprint_pct |   band_pct | limit_risk       | borrow        | halt_flag   | bucket    |
|:---------|:--------------|:-------|-----------:|:-----------------|------------------------:|-----------:|:-----------------|:--------------|:------------|:----------|
| 6223.TWO | Taiwan (TWSE) | Buy    |       4.98 | 16x (max 38x)    |                   103.8 |         10 | LOCK RISK (±10%) | no quota data | -           | MULTI-DAY |
| 1101.TW  | Taiwan (TWSE) | Sell   |      14.27 | 16x (max 38x)    |                   297.3 |         10 | LOCK RISK (±10%) | no quota data | -           | MULTI-DAY |
| 1102.TW  | Taiwan (TWSE) | Sell   |       9.99 | 16x (max 38x)    |                   208.1 |         10 | LOCK RISK (±10%) | no quota data | -           | MULTI-DAY |
| 1326.TW  | Taiwan (TWSE) | Sell   |       4.09 | 16x (max 38x)    |                    85.3 |         10 | LOCK RISK (±10%) | no quota data | -           | MULTI-DAY |
| 1402.TW  | Taiwan (TWSE) | Sell   |       6.1  | 16x (max 38x)    |                   127.1 |         10 | LOCK RISK (±10%) | no quota data | -           | MULTI-DAY |
| 1504.TW  | Taiwan (TWSE) | Sell   |       4.05 | 16x (max 38x)    |                    84.4 |         10 | LOCK RISK (±10%) | no quota data | -           | MULTI-DAY |
| 2207.TW  | Taiwan (TWSE) | Sell   |      22.78 | 16x (max 38x)    |                   474.6 |         10 | LOCK RISK (±10%) | no quota data | -           | MULTI-DAY |
| 2324.TW  | Taiwan (TWSE) | Sell   |       2.47 | 16x (max 38x)    |                    51.4 |         10 | LOCK RISK (±10%) | no quota data | -           | WORK+MOC  |
| 2474.TW  | Taiwan (TWSE) | Sell   |       3.81 | 16x (max 38x)    |                    79.4 |         10 | LOCK RISK (±10%) | no quota data | -           | MULTI-DAY |
| 2610.TW  | Taiwan (TWSE) | Sell   |       3.8  | 16x (max 38x)    |                    79.2 |         10 | LOCK RISK (±10%) | no quota data | -           | MULTI-DAY |
| 2633.TW  | Taiwan (TWSE) | Sell   |      10.95 | 16x (max 38x)    |                   228.2 |         10 | LOCK RISK (±10%) | no quota data | -           | MULTI-DAY |

### 2.3a Schedule state at T-1

| ticker   | bucket    |   days_needed | start_date   | status                                                          |
|:---------|:----------|--------------:|:-------------|:----------------------------------------------------------------|
| 6223.TWO | MULTI-DAY |            20 | 2026-05-04   | LATE START — escalate: cap must rise or completion slips past T |
| 1101.TW  | MULTI-DAY |            58 | 2026-03-11   | LATE START — escalate: cap must rise or completion slips past T |
| 1102.TW  | MULTI-DAY |            40 | 2026-04-06   | LATE START — escalate: cap must rise or completion slips past T |
| 1326.TW  | MULTI-DAY |            17 | 2026-05-07   | LATE START — escalate: cap must rise or completion slips past T |
| 1402.TW  | MULTI-DAY |            25 | 2026-04-27   | LATE START — escalate: cap must rise or completion slips past T |
| 1504.TW  | MULTI-DAY |            17 | 2026-05-07   | LATE START — escalate: cap must rise or completion slips past T |
| 2207.TW  | MULTI-DAY |            92 | 2026-01-22   | LATE START — escalate: cap must rise or completion slips past T |
| 2324.TW  | WORK+MOC  |             1 | T            | auction-window name                                             |
| 2474.TW  | MULTI-DAY |            16 | 2026-05-08   | LATE START — escalate: cap must rise or completion slips past T |
| 2610.TW  | MULTI-DAY |            16 | 2026-05-08   | LATE START — escalate: cap must rise or completion slips past T |
| 2633.TW  | MULTI-DAY |            44 | 2026-03-31   | LATE START — escalate: cap must rise or completion slips past T |

*(At T-1, MULTI-DAY names showing LATE START are the residual-risk names: whatever was not worked in the window must now clear in one auction — see the footprint column and CLOSING_AUCTIONS_ASIA.md.)*

### 2.3b Discretion decisions at T-1 (documented)

- **6223.TWO** (Buy): PRE-POSITION up to 30% within envelope
  - uncrowded add (unpriced): the close will jump; the envelope exists to capture part of that move; evidence: crowding read 'no data'
- **1101.TW** (Sell): WORK AHEAD up to 30% of order pre-close
  - crowded delete: street pre-sold, pressure part-spent, covering bounce enlarged — working ahead beats donating the close to the covering crowd; evidence: crowding read 'HIGH (+44%/23obs)'
- **1102.TW** (Sell): WORK AHEAD up to 15% (half envelope)
  - moderate crowding: split the difference, keep optionality; evidence: crowding read 'MED (+6%/23obs)'
- **1326.TW** (Sell): WAIT — MOC the full order
  - uncrowded/unknown delete: pressure arrives at the print; pre-trading a clean close adds impact and tracking for nothing; evidence: crowding read 'LOW (-13%/23obs)'
- **1402.TW** (Sell): WAIT — MOC the full order
  - uncrowded/unknown delete: pressure arrives at the print; pre-trading a clean close adds impact and tracking for nothing; evidence: crowding read 'no data'
- **1504.TW** (Sell): WAIT — MOC the full order
  - uncrowded/unknown delete: pressure arrives at the print; pre-trading a clean close adds impact and tracking for nothing; evidence: crowding read 'no data'
- **2207.TW** (Sell): WORK AHEAD up to 15% (half envelope)
  - moderate crowding: split the difference, keep optionality; evidence: crowding read 'MED (+17%/23obs)'
- **2324.TW** (Sell): WAIT — MOC the full order
  - uncrowded/unknown delete: pressure arrives at the print; pre-trading a clean close adds impact and tracking for nothing; evidence: crowding read 'LOW (+1%/23obs)'
- **2474.TW** (Sell): WAIT — MOC the full order
  - uncrowded/unknown delete: pressure arrives at the print; pre-trading a clean close adds impact and tracking for nothing; evidence: crowding read 'LOW (-7%/23obs)'
- **2610.TW** (Sell): WAIT — MOC the full order
  - uncrowded/unknown delete: pressure arrives at the print; pre-trading a clean close adds impact and tracking for nothing; evidence: crowding read 'LOW (-2%/23obs)'
- **2633.TW** (Sell): WORK AHEAD up to 15% (half envelope)
  - moderate crowding: split the difference, keep optionality; evidence: crowding read 'MED (+15%/23obs)'

### T-1 checklist state

- Names: 11; MULTI-DAY 10; footprint>30% 11 (client conversations held); LOCK-RISK all TW names (±10% band) — queue-or-retreat playbook attached
- Final index file reconciliation, FX confirmation, staged auction orders: DESK OPS (out of replay scope, on the checklist)
- Cutoff: TW 13:25 order-rest; indicative broadcast 13:25-13:30 is tomorrow's one real-time decision
