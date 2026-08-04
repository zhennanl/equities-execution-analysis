# Pre-Announcement Pack — May-2026 TW (PIT BACKTEST)
*ann 2026-05-12 / effective 2026-05-29 (SAIR). Six-category build, agents/pre_announcement.py; every number carries its basis; crowding as-of and prior staleness stated.*

## 1. Screening — candidates

| side   | ticker   |    p | reasoning                       |
|:-------|:---------|-----:|:--------------------------------|
| ADD    | 6223.TWO | 0.64 | L8 engine call (PIT May config) |
| DELETE | 1101.TW  | 0.6  | L8 engine call (PIT May config) |
| DELETE | 1102.TW  | 0.6  | L8 engine call (PIT May config) |
| DELETE | 1326.TW  | 0.6  | L8 engine call (PIT May config) |
| DELETE | 1402.TW  | 0.6  | L8 engine call (PIT May config) |
| DELETE | 1504.TW  | 0.6  | L8 engine call (PIT May config) |
| DELETE | 2207.TW  | 0.6  | L8 engine call (PIT May config) |
| DELETE | 2324.TW  | 0.6  | L8 engine call (PIT May config) |
| DELETE | 2474.TW  | 0.6  | L8 engine call (PIT May config) |
| DELETE | 2610.TW  | 0.6  | L8 engine call (PIT May config) |
| DELETE | 2633.TW  | 0.6  | L8 engine call (PIT May config) |

## 2. Crowding watch (dated, alert = |5-obs delta| >= 10%)

|   code | read             | alert   |     asof | band   |   build_pct |   delta5_pct |   n_obs |
|-------:|:-----------------|:--------|---------:|:-------|------------:|-------------:|--------:|
|   6223 | no data          | False   | 20260511 | nan    |         nan |          nan |     nan |
|   1101 | MED (+14%/10obs) | False   | 20260511 | MED    |          14 |            3 |      10 |
|   1102 | LOW (-1%/10obs)  | False   | 20260511 | LOW    |          -1 |            2 |      10 |
|   1326 | LOW (-27%/10obs) | False   | 20260511 | LOW    |         -27 |           -5 |      10 |
|   1402 | insufficient obs | False   | 20260511 | nan    |         nan |          nan |     nan |
|   1504 | insufficient obs | False   | 20260511 | nan    |         nan |          nan |     nan |
|   2207 | MED (+8%/10obs)  | False   | 20260511 | MED    |           8 |            3 |      10 |
|   2324 | LOW (+1%/10obs)  | False   | 20260511 | LOW    |           1 |            0 |      10 |
|   2474 | LOW (-6%/10obs)  | False   | 20260511 | LOW    |          -6 |           -2 |      10 |
|   2610 | LOW (-2%/10obs)  | False   | 20260511 | LOW    |          -2 |            0 |      10 |
|   2633 | LOW (+2%/10obs)  | False   | 20260511 | LOW    |           2 |            1 |      10 |

## 3. Positioning advisory

- TW adds are MOMENTUM events (6/7 recent adds +30..+107% into announcement) — the tape front-runs the arithmetic; advisory only for an agency desk.
- Window intraday priors (24 events, 5m): MSCI-delete window-day volumes run 1.4x baseline early -> 2.9x late (the obligation trades THROUGH the window; FTSE ~1.0x until the print); delete-name closing auctions grow ~3.6 share points into T (H9b, 86% of events) — late-window MOC participation gets less lonely daily, but the print remains the event. PM-drift concentration toward T: NULL (H10) — no afternoon execution bias warranted.
- Deletes (TW MSCI class): spreading cost +48 bps vs close median (n=20) — MOC-family default; crowded names flip to WORK-AHEAD per the matrix.
- Adds: no measured MSCI TW Buy prints; FTSE-class cross-reference: window-VWAP -184 bps (n=49); MSCI-add WAIT rule remains a demoted hypothesis (Aug-2026 arbitrates).

## 4. Capacity cards (must-start-by at 25% participation)

- **ADD 6223.TWO** p=0.64 | flow $638-1148M | 3.6-6.4 ADV-days (MULTI-DAY) | must start by **2026-04-24** | crowding no live read (run with TW short caches for the daily read)
- **DELETE 1101.TW** p=0.6 | flow $235-423M | 10.2-18.3 ADV-days (MULTI-DAY) | must start by **2026-02-17** | crowding MED (+14%/10obs)
- **DELETE 1102.TW** p=0.6 | flow $137-247M | 7.1-12.9 ADV-days (MULTI-DAY) | must start by **2026-03-19** | crowding LOW (-1%/10obs)
- **DELETE 1326.TW** p=0.6 | flow $259-467M | 2.9-5.3 ADV-days (MULTI-DAY) | must start by **2026-04-30** | crowding LOW (-27%/10obs)
- **DELETE 1402.TW** p=0.6 | flow $142-255M | 4.4-7.8 ADV-days (MULTI-DAY) | must start by **2026-04-16** | crowding no live read (run with TW short caches for the daily read)
- **DELETE 1504.TW** p=0.6 | flow $143-258M | 2.9-5.2 ADV-days (MULTI-DAY) | must start by **2026-05-01** | crowding no live read (run with TW short caches for the daily read)
- **DELETE 2207.TW** p=0.6 | flow $198-357M | 16.3-29.3 ADV-days (MULTI-DAY) | must start by **2025-12-17** | crowding MED (+8%/10obs)
- **DELETE 2324.TW** p=0.6 | flow $180-324M | 1.8-3.2 ADV-days (MULTI-DAY) | must start by **2026-05-13** | crowding LOW (+1%/10obs)
- **DELETE 2474.TW** p=0.6 | flow $133-239M | 2.7-4.9 ADV-days (MULTI-DAY) | must start by **2026-05-04** | crowding LOW (-6%/10obs)
- **DELETE 2610.TW** p=0.6 | flow $97-174M | 2.7-4.9 ADV-days (MULTI-DAY) | must start by **2026-05-04** | crowding LOW (-2%/10obs)
- **DELETE 2633.TW** p=0.6 | flow $80-145M | 7.8-14.1 ADV-days (MULTI-DAY) | must start by **2026-03-12** | crowding LOW (+2%/10obs)

## 6. Microstructure priors snapshot (as-of 20260511)

- Print multiple (Sell): median 16.0x / max 38.1x (n=8); Buy: NO MEASURED PRIOR
- Event-day auction share: {'lo': None, 'hi': None, 'med': 60.0, 'n': 20, 'basis': 'DIRECT IB auction bars, class MSCI/Sell'}
- Gap band: {'mean': 123.0, 'std': 82.0, 'n': 17} (direction not predicted — null pinned)
- Limits: {'base_touch_up': np.float64(3.0), 'base_lock_up': np.float64(2.0), 'event_touch_up': np.float64(5.5), 'n_days': 23}

## GRADE vs the official key

- dels hit ['1102.TW', '1402.TW', '1504.TW', '2324.TW', '2474.TW', '2610.TW', '2633.TW'] | missed visible [] | false ['1101.TW', '1326.TW', '2207.TW']
- adds hit ['6223.TWO'] | missed [] | false []
- Brier score 0.212 over 11 scored candidates (lower is better; 0.25 = coin-flip at p=0.5)