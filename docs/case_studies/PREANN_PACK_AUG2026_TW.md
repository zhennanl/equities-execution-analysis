> DATA FRESHNESS [OK]: shorts latest 20260803 vs expected 20260804 (1 bdays stale). cache already current (or expected day not yet published — tolerance 1 bday)

# Pre-Announcement Pack — Aug-2026 TW (LIVE, pre-announcement)
*ann 2026-08-11 / effective 2026-08-31 (QIR). Six-category build, agents/pre_announcement.py; every number carries its basis; crowding as-of and prior staleness stated.*

## 1. Screening — candidates

| side   | ticker                     |   cap_usd_b |   x_threshold |     p | reasoning                                                                                                                                                                                                   |
|:-------|:---------------------------|------------:|--------------:|------:|:------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| ADD    | 2324.TW                    |         4.8 |          0.56 | 0.061 | non-member 0.56x the add bar (needs +78%); P(any add at a TAIWAN QIR) = 46% decade-measured, x visible share 40%, x proximity weight 33%; CAUTION recent deletion — decade re-add-within-4 rate here is 0%  |
| ADD    | 1504.TW                    |         4.6 |          0.53 | 0.049 | non-member 0.53x the add bar (needs +88%); P(any add at a TAIWAN QIR) = 46% decade-measured, x visible share 40%, x proximity weight 27%; CAUTION recent deletion — decade re-add-within-4 rate here is 0%  |
| ADD    | 2633.TW                    |         4.3 |          0.5  | 0.036 | non-member 0.50x the add bar (needs +102%); P(any add at a TAIWAN QIR) = 46% decade-measured, x visible share 40%, x proximity weight 20%; CAUTION recent deletion — decade re-add-within-4 rate here is 0% |
| ADD    | 1402.TW                    |         4.3 |          0.5  | 0.036 | non-member 0.50x the add bar (needs +102%); P(any add at a TAIWAN QIR) = 46% decade-measured, x visible share 40%, x proximity weight 20%; CAUTION recent deletion — decade re-add-within-4 rate here is 0% |
| ADD    | BELOW-FLOOR (unobservable) |       nan   |        nan    | 0.273 | blind-band mass: 13/21 of 2025-26 TW changes sat below the 16-name floor (Nov-25 re-grade vs May-26 grade)                                                                                                  |
| DELETE | 1101.TW                    |         5.2 |          2.19 | 0.149 | member 2.19x the del floor (needs +119%); P(any delete at a TAIWAN QIR) = 50% decade-measured, x visible share 40%, x proximity weight 75%                                                                  |
| DELETE | 2207.TW                    |         8.5 |          3.55 | 0.022 | member 3.55x the del floor (needs +255%); P(any delete at a TAIWAN QIR) = 50% decade-measured, x visible share 40%, x proximity weight 11%                                                                  |
| DELETE | 2002.TW                    |         8.8 |          3.68 | 0.019 | member 3.68x the del floor (needs +268%); P(any delete at a TAIWAN QIR) = 50% decade-measured, x visible share 40%, x proximity weight 9%                                                                   |
| DELETE | 1326.TW                    |        10.4 |          4.33 | 0.01  | member 4.33x the del floor (needs +333%); P(any delete at a TAIWAN QIR) = 50% decade-measured, x visible share 40%, x proximity weight 5%                                                                   |
| DELETE | BELOW-FLOOR (unobservable) |       nan   |        nan    | 0.3   | blind-band mass: 13/21 of 2025-26 TW changes sat below the 16-name floor (Nov-25 re-grade vs May-26 grade)                                                                                                  |

## 2. Crowding watch (dated, alert = |5-obs delta| >= 10%)

|   code | band   |   build_pct |   delta5_pct |   n_obs | read                                      | alert   |     asof |
|-------:|:-------|------------:|-------------:|--------:|:------------------------------------------|:--------|---------:|
|   2324 | LOW    |         -70 |           -2 |      30 | LOW (-70%/30obs)                          | False   | 20260803 |
|   1504 | MED    |           6 |            3 |       8 | MED (+6%/8obs)                            | False   | 20260803 |
|   2633 | LOW    |         -72 |          -12 |      30 | LOW (-72%/30obs)                          | True    | 20260803 |
|   1402 | LOW    |         -17 |           -9 |       8 | LOW (-17%/8obs)                           | False   | 20260803 |
|   1101 | HIGH   |          32 |           -3 |      30 | HIGH (+32%/30obs)                         | False   | 20260803 |
|   2207 | LOW    |         -41 |           -3 |      30 | LOW (-41%/30obs)                          | False   | 20260803 |
|   2002 | LOW    |         -33 |           -4 |      30 | LOW (-33%/30obs); EXITING (-42% off peak) | False   | 20260803 |
|   1326 | LOW    |         -41 |           40 |      30 | LOW (-41%/30obs)                          | True    | 20260803 |

## 3. Positioning advisory

- TW adds are MOMENTUM events (6/7 recent adds +30..+107% into announcement) — the tape front-runs the arithmetic; advisory only for an agency desk.
- Window intraday priors (24 events, 5m): MSCI-delete window-day volumes run 1.4x baseline early -> 2.9x late (the obligation trades THROUGH the window; FTSE ~1.0x until the print); delete-name closing auctions grow ~3.6 share points into T (H9b, 86% of events) — late-window MOC participation gets less lonely daily, but the print remains the event. PM-drift concentration toward T: NULL (H10) — no afternoon execution bias warranted.
- Deletes (TW MSCI class): spreading cost +48 bps vs close median (n=20) — MOC-family default; crowded names flip to WORK-AHEAD per the matrix.
- Adds: no measured MSCI TW Buy prints; FTSE-class cross-reference: window-VWAP -184 bps (n=49); MSCI-add WAIT rule remains a demoted hypothesis (Aug-2026 arbitrates).

## 4. Capacity cards (must-start-by at 25% participation)

- **ADD 2324.TW** p=0.061 | flow $229-413M | 2.2-4.0 ADV-days (MULTI-DAY) | must start by **2026-08-10** | crowding LOW (-70%/30obs)
- **ADD 1504.TW** p=0.049 | flow $150-271M | 3.0-5.5 ADV-days (MULTI-DAY) | must start by **2026-07-31** | crowding MED (+6%/8obs)
- **ADD 2633.TW** p=0.036 | flow $78-141M | 7.6-13.7 ADV-days (MULTI-DAY) | must start by **2026-06-16** | crowding LOW (-72%/30obs)
- **ADD 1402.TW** p=0.036 | flow $149-269M | 4.6-8.3 ADV-days (MULTI-DAY) | must start by **2026-07-15** | crowding LOW (-17%/8obs)
- ADD BELOW-FLOOR (unobservable) p=0.273: blind-band mass: 13/21 of 2025-26 TW changes sat below the 16-name floor (Nov-25 re-grade vs May-26 grade) — no per-name card is computable for the unobservable band; this row exists so the probability mass stays visible.
- **DELETE 1101.TW** p=0.149 | flow $226-407M | 9.8-17.6 ADV-days (MULTI-DAY) | must start by **2026-05-25** | crowding HIGH (+32%/30obs)
- **DELETE 2207.TW** p=0.022 | flow $215-388M | 17.7-31.8 ADV-days (MULTI-DAY) | must start by **2026-03-05** | crowding LOW (-41%/30obs)
- **DELETE 2002.TW** p=0.019 | flow $319-574M | 8.7-15.7 ADV-days (MULTI-DAY) | must start by **2026-06-04** | crowding LOW (-33%/30obs); EXITING (-42% off peak)
- **DELETE 1326.TW** p=0.01 | flow $289-520M | 3.3-5.9 ADV-days (MULTI-DAY) | must start by **2026-07-29** | crowding LOW (-41%/30obs)
- DELETE BELOW-FLOOR (unobservable) p=0.3: blind-band mass: 13/21 of 2025-26 TW changes sat below the 16-name floor (Nov-25 re-grade vs May-26 grade) — no per-name card is computable for the unobservable band; this row exists so the probability mass stays visible.

## 6. Microstructure priors snapshot (as-of latest)

- Print multiple (Sell): median 16.0x / max 38.1x (n=8); Buy: NO MEASURED PRIOR
- Event-day auction share: {'lo': None, 'hi': None, 'med': 60.0, 'n': 20, 'basis': 'DIRECT IB auction bars, class MSCI/Sell'}
- Gap band: {'mean': 123.0, 'std': 82.0, 'n': 17} (direction not predicted — null pinned)
- Limits: {'base_touch_up': np.float64(3.0), 'base_lock_up': np.float64(2.0), 'event_touch_up': np.float64(5.5), 'n_days': 23}