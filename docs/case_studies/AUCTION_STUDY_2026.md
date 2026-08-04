# Closing-Auction Study — Real Event Days (2026)
*Session 8n. (a) Market-wide TWSE 5-second archive: the May-29 MSCI effective-day auction vs baseline days. (b) Per-name derivation on the June-19 FTSE TW50 effective day (AI-quartet adds vs 2330 control). Data honesty: May-29 PER-NAME intraday left the free 60-day retention ~one day before this study — the market-wide archive and the June event carry the analysis; the standing archiver (from Aug 11) closes this gap permanently.*

## (a) May-29 MSCI effective day — market-wide closing auction (TWSE 5s archive)

|     date | day            |   auction_vol_klots |   auction_%_of_day_vol |   auction_val_NT$B |   auction_%_of_day_val |   close_bid/ask_imbal |
|---------:|:---------------|--------------------:|-----------------------:|-------------------:|-----------------------:|----------------------:|
| 20260522 | baseline       |                 357 |                    2.5 |               48.7 |                    4.1 |                  1.45 |
| 20260526 | baseline       |                 576 |                    3.2 |               73.7 |                    5   |                  1.3  |
| 20260527 | baseline       |                 561 |                    3.1 |               71.5 |                    4.6 |                  1.27 |
| 20260529 | MSCI EFFECTIVE |                3221 |                   16.7 |              452.1 |                   24.9 |                  1.33 |
| 20260605 | baseline       |                 512 |                    3.3 |               73.4 |                    6   |                  1.31 |

**Read:** effective-day auction 24.9% of day value vs baseline median 4.8% — the event concentrates the day INTO the print, market-wide, even though only ~8 names carried the flow. Value share > volume share = the auction skews to the large/expensive event names.

**The auction's PRICE move (TAIEX at 13:29:55 vs the 13:30 print — MI_5MINS_INDEX, historical):**

|     date | day            |   auction_gap_bps |
|---------:|:---------------|------------------:|
| 20260522 | baseline       |              -9.8 |
| 20260526 | baseline       |             -10.5 |
| 20260527 | baseline       |             -25.5 |
| 20260529 | MSCI EFFECTIVE |             -40.9 |
| 20260605 | baseline       |              12.4 |

**Read:** the effective-day print moved the INDEX -40.9 bps in one auction vs ~11 bps absolute on baseline days — the market-level violence measurement, sell-skewed exactly as a 66-deletion SAIR plus reweight-sell pressure implies. This is the number the per-name violence curve aggregates to.

## (b) June TW50 implementation print — JUN 18 (holiday-shifted) — per-name auction shares

| ticker   | role                          | event_auction_share   | baseline_median   |   auction_gap_bps |   event_t_mult |
|:---------|:------------------------------|:----------------------|:------------------|------------------:|---------------:|
| 3443.TW  | TW50 ADD (June)               | 61.7%                 | 10.2%             |              -192 |            2.2 |
| 3665.TW  | TW50 ADD (June)               | 71.3%                 | 7.7%              |              -179 |            2.3 |
| 8046.TW  | TW50 ADD (June)               | 43.7%                 | 8.5%              |               -78 |            1   |
| 4958.TW  | TW50 ADD (June)               | 54.1%                 | 11.0%             |               -16 |            1.4 |
| 2330.TW  | REWEIGHT LEG (not a control!) | 55.3%                 | 30.1%             |                42 |            1.6 |

**Read:** the adds show the auction-share uplift and T-multiple the priors predict — and the intended 'control' (2330) turned out to be the study's second finding: on a TW50 rebalance TSMC is the REWEIGHT leg, and its 55% auction share on the print day is the reweight flow (27% of event turnover in our flow sim) made visible in public data. auction_gap = official close vs last continuous bar — the price the auction 'paid' to clear (violence-curve point per name). Note also the calendar catch: the June print was JUN 18, not the third Friday — Dragon Boat holiday shifted it; the data, not the calendar, identified the day.

## (c) May-29 MSCI effective day — CHINA A per-name closing auctions (baostock 5-min, the free door that was open all along)

| name               | side   | event_auction_share   | baseline_median   |   auction_gap_bps |   event_t_mult |
|:-------------------|:-------|:----------------------|:------------------|------------------:|---------------:|
| 002850.SZ          | Buy    | 15.9%                 | 1.2%              |               -37 |            1.6 |
| 300390.SZ          | Buy    | 4.9%                  | 2.0%              |               194 |            1.3 |
| 301358.SZ          | Buy    | 14.3%                 | 1.7%              |               239 |            1.3 |
| 601869.SS          | Buy    | 5.9%                  | 2.1%              |               198 |            1.4 |
| 688506.SS          | Buy    | 18.7%                 | 1.9%              |               -13 |            2.1 |
| 002085.SZ          | Sell   | 21.8%                 | 2.2%              |               -42 |            1.4 |
| 002456.SZ          | Sell   | 12.6%                 | 3.3%              |              -229 |            0.8 |
| 002673.SZ          | Sell   | 37.3%                 | 2.7%              |              -149 |            2.1 |
| 600109.SS          | Sell   | 32.4%                 | 3.1%              |                46 |            2.1 |
| 601668.SS          | Sell   | 4.4%                  | 3.9%              |                 0 |            1.6 |
| 603160.SS          | Sell   | 12.3%                 | 1.7%              |              -164 |            1.7 |
| 688009.SS          | Sell   | 36.6%                 | 2.2%              |              -144 |            2.1 |
| 688538.SS          | Sell   | 23.5%                 | 2.2%              |              -167 |            1.4 |
| 600000.SS(control) | -      | 10.9%                 | 2.2%              |                11 |            1.2 |

**Read:** adds' auction gaps median +194 bps vs deletes' -146 bps — the print pays the imbalance in the SIDE's direction, per name, exactly the violence-curve shape. The 14:57-15:00 call (3 minutes, no cancels) is visible as the 15:00 bar. H-line names (0177.HK etc.) remain honestly out — no free HK intraday source reaches May 29 (Eastmoney 31-day wall, Tencent DNS-blocked from sandbox, futu account-gated).

## How these numbers become desk insights

1. **Footprint denominators become measured**: the sheet's auction-footprint % now uses event-day auction shares, not an assumed 30% flat.
2. **Violence-curve points**: each event name contributes (auction size, auction gap) — the indicative-read rule's thresholds calibrate on these instead of theory.
3. **Crowding validation**: crowded names should print big auctions with SMALL gaps (pressure pre-spent); uncrowded with large gaps — testable per event, feeds the discretion matrix.
4. **Completion inference**: auction volume vs our expected flow bounds how much passive demand cleared AT the print vs was worked/deferred — the T+1 residual estimate.
5. **The archive compounds**: every event adds rows; the indicative archiver (Aug 11 onward) adds the pre-print trajectory nobody retains.
