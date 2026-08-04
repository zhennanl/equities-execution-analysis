# T-Day Hourly Shape — per-name 60m bars on effective dates

*Session 9i. Source: yfinance 60m (the one free per-name intraday history for TW — 730-day reach, live-verified). 57 name-T-days across 8 events. VERIFIED CAVEAT (3443 exhibit): Yahoo intraday bars EXCLUDE the closing auction — hourly volume summed to 22.5% of official daily on 3443's print day — so all metrics here are CONTINUOUS-SESSION; the last-continuous->close leg is the separately measured gap band (|123|±82). Data-source verdict: FinMind minute/tick sponsor-walled; Stooq bot-walled; TWSE per-name tick = paid Data E-Shop; auction-resolution history stays forward-only (archiver from Aug-11).*

## The finding

**FTSE T-day continuous sessions are the CROWD-UNWIND session**: both sides move AGAINST the index flow (adds fall ~198 bps AM, deletes rise ~120 bps — the pre-positioned crowd exiting into the obligated flow; the 2344 limit-down add and 6919 limit-up delete are this pattern's extremes). **MSCI T-day continuous sessions are FLAT** (adds +62, dels +8) — the action is entirely in the 16x print. Execution reading: on FTSE T-days the worked fraction can harvest the unwind intraday; on MSCI T-days the continuous session offers little — the close is the event.

## Medians by class

|                  |   n |   pm_cont_vol |   am_drift |   pm_cont_move |
|:-----------------|----:|--------------:|-----------:|---------------:|
| ('FTSE', 'Buy')  |  15 |          0.15 |       -198 |            -19 |
| ('FTSE', 'Sell') |  15 |          0.2  |       -120 |            -25 |
| ('MSCI', 'Buy')  |   7 |          0.22 |         62 |             12 |
| ('MSCI', 'Sell') |  20 |          0.22 |          8 |             -6 |

## Per-name table

| event        | provider   |   code | side   |   pm_cont_vol_share |   am_drift_bps |   pm_cont_move_bps |
|:-------------|:-----------|-------:|:-------|--------------------:|---------------:|-------------------:|
| MSCI 2025-08 | MSCI       |   6919 | Buy    |               0.498 |           -126 |               -230 |
| MSCI 2025-08 | MSCI       |   2059 | Buy    |               0.22  |             34 |                -17 |
| MSCI 2025-08 | MSCI       |   9904 | Sell   |               0.238 |            -87 |                 17 |
| MSCI 2025-08 | MSCI       |   9945 | Sell   |               0.196 |           -119 |                -17 |
| MSCI 2025-11 | MSCI       |   3665 | Buy    |               0.165 |            -33 |                131 |
| MSCI 2025-11 | MSCI       |   2360 | Buy    |               0.215 |             62 |                 12 |
| MSCI 2025-11 | MSCI       |   2368 | Buy    |               0.137 |            113 |                -48 |
| MSCI 2025-11 | MSCI       |   2449 | Buy    |               0.211 |            279 |                 90 |
| MSCI 2025-11 | MSCI       |   1504 | Buy    |               0.24  |             80 |                 34 |
| MSCI 2025-11 | MSCI       |   2353 | Sell   |               0.239 |             55 |                 -0 |
| MSCI 2025-11 | MSCI       |   2409 | Sell   |               0.31  |             -0 |                -44 |
| MSCI 2025-11 | MSCI       |   2377 | Sell   |               0.278 |            139 |                 -0 |
| MSCI 2025-11 | MSCI       |   6415 | Sell   |               0.276 |            220 |                100 |
| MSCI 2025-11 | MSCI       |   2347 | Sell   |               0.365 |             16 |                 48 |
| MSCI 2025-11 | MSCI       |   6409 | Sell   |               0.184 |            299 |                -44 |
| MSCI 2025-11 | MSCI       |   3702 | Sell   |               0.167 |            -59 |                 -0 |
| MSCI 2026-02 | MSCI       |   2105 | Sell   |               0.203 |             98 |                -33 |
| MSCI 2026-02 | MSCI       |   1476 | Sell   |               0.29  |            130 |                -12 |
| MSCI 2026-02 | MSCI       |   9910 | Sell   |               0.282 |            105 |                -43 |
| MSCI 2026-02 | MSCI       |   8464 | Sell   |               0.268 |            302 |               -175 |
| MSCI 2026-05 | MSCI       |   1102 | Sell   |               0.191 |           -291 |                 30 |
| MSCI 2026-05 | MSCI       |   1402 | Sell   |               0.162 |           -101 |                 20 |
| MSCI 2026-05 | MSCI       |   1504 | Sell   |               0.126 |           -411 |                 13 |
| MSCI 2026-05 | MSCI       |   2324 | Sell   |               0.063 |           -312 |                 -0 |
| MSCI 2026-05 | MSCI       |   2474 | Sell   |               0.166 |           -492 |                -49 |
| MSCI 2026-05 | MSCI       |   2610 | Sell   |               0.194 |            -26 |                -53 |
| MSCI 2026-05 | MSCI       |   2633 | Sell   |               0.241 |             20 |                -20 |
| FTSE 2025-09 | FTSE       |   6919 | Buy    |               0.062 |           -985 |                  0 |
| FTSE 2025-09 | FTSE       |   2059 | Buy    |               0.181 |           -132 |                -30 |
| FTSE 2025-09 | FTSE       |   6446 | Sell   |               0.196 |             -0 |                 -0 |
| FTSE 2025-09 | FTSE       |   1101 | Sell   |               0.213 |           -135 |                -89 |
| FTSE 2025-12 | FTSE       |   3665 | Buy    |               0.129 |            103 |                -34 |
| FTSE 2025-12 | FTSE       |   2360 | Buy    |               0.15  |            189 |                -40 |
| FTSE 2025-12 | FTSE       |   3653 | Buy    |               0.238 |            -56 |                -19 |
| FTSE 2025-12 | FTSE       |   2408 | Buy    |               0.182 |           -198 |                 58 |
| FTSE 2025-12 | FTSE       |   5871 | Sell   |               0.306 |            -94 |                -47 |
| FTSE 2025-12 | FTSE       |   4938 | Sell   |               0.163 |            -88 |                -14 |
| FTSE 2025-12 | FTSE       |   5876 | Sell   |               0.137 |           -175 |                -25 |
| FTSE 2025-12 | FTSE       |   2609 | Sell   |               0.237 |           -157 |                -58 |
| FTSE 2026-03 | FTSE       |   2368 | Buy    |               0.145 |           -291 |                  0 |
| FTSE 2026-03 | FTSE       |   7769 | Buy    |               0.125 |            -48 |                -85 |
| FTSE 2026-03 | FTSE       |   2449 | Buy    |               0.117 |           -456 |                -49 |
| FTSE 2026-03 | FTSE       |   3037 | Buy    |               0.171 |           -763 |                319 |
| FTSE 2026-03 | FTSE       |   2344 | Buy    |               0.147 |          -1008 |                -45 |
| FTSE 2026-03 | FTSE       |   3665 | Sell   |               0.112 |           -227 |                 -0 |
| FTSE 2026-03 | FTSE       |   3034 | Sell   |               0.11  |           -120 |                -40 |
| FTSE 2026-03 | FTSE       |   2912 | Sell   |               0.201 |            140 |                -47 |
| FTSE 2026-03 | FTSE       |   2379 | Sell   |               0.148 |            -95 |                -21 |
| FTSE 2026-03 | FTSE       |   2615 | Sell   |               0.183 |            -38 |                 -0 |
| FTSE 2026-06 | FTSE       |   3665 | Buy    |               0.15  |            -70 |                -24 |
| FTSE 2026-06 | FTSE       |   3443 | Buy    |               0.206 |           -397 |                  0 |
| FTSE 2026-06 | FTSE       |   8046 | Buy    |               0.224 |           -244 |                 11 |
| FTSE 2026-06 | FTSE       |   4958 | Buy    |               0.271 |            -77 |                 31 |
| FTSE 2026-06 | FTSE       |   6919 | Sell   |               0.076 |           -887 |                -46 |
| FTSE 2026-06 | FTSE       |   2002 | Sell   |               0.233 |            -53 |                -26 |
| FTSE 2026-06 | FTSE       |   1301 | Sell   |               0.196 |           -475 |                -20 |
| FTSE 2026-06 | FTSE       |   2207 | Sell   |               0.235 |           -391 |                -10 |