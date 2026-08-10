# Round two — stressing the capacity ladder

Generated 2026-08-10T11:17:59. Prices to 2026-07-31 (**live refresh not run**).

## 1 · Does the ranking survive the ADV horizon?

The ladder divides index demand by `0.095 x ADV` — the share of a day's volume that an ordinary Taiwanese closing auction takes. ADV was struck on one horizon and the horizon was never named. Here it is struck on four.

| ADV horizon | Winbond Electronics (2344) | Nanya Technology (2408) | Nan Ya (8046) | order |
|---|---|---|---|---|
| 20d | 14.9 | 10.6 | 8.2 | 2344 > 2408 > 8046 |
| 60d | 8.7 | 7.4 | 8.2 | 2344 > 8046 > 2408 |
| 120d | 9.2 | 7.6 | 8.5 | 2344 > 8046 > 2408 |
| 250d | 9.1 | 7.6 | 7.7 | 2344 > 8046 > 2408 |

*Cells are closing auctions of ordinary liquidity the order would consume.*

**The ranking does NOT hold.** Different horizons give different orders: 2344 > 2408 > 8046; 2344 > 8046 > 2408. Round one's single ranking was an artefact of an undeclared horizon choice and should be withdrawn in favour of the range below.

## 2 · The names, as they stand

### 2344 Winbond Electronics Corporation

- last close **130.0** (2026-07-31), 20d -29.2%, 30d -34.7%, -41.4% off the 30d high, 30d vol 92%
- order size **8.7 to 14.9 ordinary closes** depending on ADV horizon (round one said 13.4)
- trading at 0.97x its own median volume — 61% of the market that session
- foreign net, in days of 20d ADV: 5d +0.56, 20d -0.04, 60d -0.92
- 8 block prints in 30 sessions (0.13 days of ADV)
- borrow 20d change -0.47 days of ADV

### 2408 Nanya Technology Corporation

- last close **360.5** (2026-07-31), 20d -11.4%, 30d -17.5%, -28.6% off the 30d high, 30d vol 109%
- order size **7.4 to 10.6 ordinary closes** depending on ADV horizon (round one said 10.8)
- trading at 0.67x its own median volume — 45% of the market that session
- foreign net, in days of 20d ADV: 5d +0.51, 20d -0.31, 60d +0.38
- 4 block prints in 30 sessions (0.02 days of ADV)
- borrow 20d change +0.79 days of ADV

### 8046 Nan Ya Printed Circuit Board Corporation

- last close **920.0** (2026-07-31), 20d -19.7%, 30d +4.0%, -35.0% off the 30d high, 30d vol 114%
- order size **7.7 to 8.5 ordinary closes** depending on ADV horizon (round one said 8.4)
- trading at 0.24x its own median volume — 9% of the market that session
- foreign net, in days of 20d ADV: 5d -0.05, 20d -0.92, 60d +0.56
- 2 block prints in 30 sessions (0.16 days of ADV)
- borrow 20d change -0.00 days of ADV

### 8299 Phison Electronics Corp.  *(not carried)*

- last close **1640.0** (2026-07-31), 20d -26.8%, 30d -29.6%, -36.4% off the 30d high, 30d vol 75%
- trading at 1.06x its own median volume — 64% of the market that session

## 3 · The holder-side test (TDCC)

Bracket 15 is holdings above 1,000,000 shares — where non-resident institutions, government funds and the ETF trusts sit. A passive pre-position shows up as a RISING bracket-15 share.

**Read the change against the noise, not against zero.** These shares move 1-2pp week to week on their own, so `z` places the eight-week change against that weekly volatility scaled by sqrt(8). Below 1 is indistinguishable from drift.

| code | weeks | b15 now | range | 8-week change | weekly SD | z | read |
|---|---|---|---|---|---|---|---|
| 2344 | 51 | 67.16% | 52.8–71.3% | -1.41pp | 1.87pp | -0.27 | no signal |
| 2408 | 51 | 80.31% | 75.3–84.8% | +0.65pp | 1.22pp | +0.19 | no signal |
| 8046 | 51 | 80.80% | 72.9–83.6% | +2.71pp | 1.34pp | +0.72 | no signal |
| 8299 | 51 | 34.62% | 33.2–50.6% | -1.28pp | 1.56pp | -0.29 | no signal |

### Holders, and the denominator

| code | holders first → last | change | custody shares first → last | change |
|---|---|---|---|---|
| 2344 | 316,335 → 555,252 | +76% | 4,500,000,193 → 4,720,490,802 | +4.9% |
| 2408 | 170,348 → 354,553 | +108% | 3,098,627,894 → 3,450,205,894 | +11.3% |
| 8046 | 63,302 → 89,065 | +41% | 646,165,487 → 646,165,487 | +0.0% |
| 8299 | 48,062 → 190,193 | +296% | 206,696,328 → 221,349,247 | +7.1% |

*A moving custody total is a corporate action, and it changes what the percentage means — the denominator is not the same security week to week.*

*TDCC retains one year, so this cannot reach the May-2026 review — only the August one.*

## What is still missing

- **Broker-branch (券商分點).** The single most direct positioning source in Taiwan, and unreachable: TWSE publishes per-branch, per-stock buy/sell only via bsr.twse.com.tw, CAPTCHA-gated and latest-session-only. Vendor purchase or manual daily capture; not a harvest.
- **The USD 180bn tracking-AUM assumption**, which sets the LEVEL of every demand number above and is a hand-set constant with no external source. It cancels in the ranking and does not cancel in the level.
- **Per-name auction share.** The 9.5% is a market-wide median applied to every name; TWSE per-stock intraday does not reach back far enough to measure it per name.
