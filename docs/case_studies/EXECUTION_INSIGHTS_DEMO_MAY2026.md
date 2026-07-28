# Execution Insights — May-2026 TW Deletions (Step-4 DEMO)
*Generated 2026-07-28 by agents/execution_insights.py — lifecycle Step 4. Signed bps, positive = cost. Misses ship.*

## 4.2 TCA vs the pre-trade estimate (what we promised vs what printed)

| ticker   | side   |   qty_shares |   realized_bps |   est_bps |   vs_estimate_bps | verdict         |
|:---------|:-------|-------------:|---------------:|----------:|------------------:|:----------------|
| 2324.TW  | Sell   |      1000000 |              8 |        12 |                -4 | WITHIN estimate |
| 1504.TW  | Sell   |      1000000 |              8 |        12 |                -4 | WITHIN estimate |
| 2610.TW  | Sell   |      1000000 |              8 |        12 |                -4 | WITHIN estimate |
| 2474.TW  | Sell   |      1000000 |              8 |        12 |                -4 | WITHIN estimate |
| 1102.TW  | Sell   |      1000000 |              8 |        12 |                -4 | WITHIN estimate |
| 1402.TW  | Sell   |      1000000 |              8 |        12 |                -4 | WITHIN estimate |
| 2633.TW  | Sell   |      1000000 |              8 |        12 |                -4 | WITHIN estimate |

Portfolio: realized 8.0 bps vs estimate delta -4.0 bps (qty-weighted).

## 4.4a Discretion choices, graded against the realized path

| ticker   | side   | decision                  |   cf_gain_bps | verdict                   |
|:---------|:-------|:--------------------------|--------------:|:--------------------------|
| 2324.TW  | Sell   | WAIT — MOC the full order |        -682.3 | staying MOC was right     |
| 1504.TW  | Sell   | WAIT — MOC the full order |        -103.4 | staying MOC was right     |
| 2610.TW  | Sell   | WAIT — MOC the full order |         -39.8 | staying MOC was right     |
| 2474.TW  | Sell   | WAIT — MOC the full order |          29.2 | WORKING WOULD HAVE HELPED |
| 1102.TW  | Sell   | WAIT — MOC the full order |          52   | WORKING WOULD HAVE HELPED |
| 1402.TW  | Sell   | WAIT — MOC the full order |         112.6 | WORKING WOULD HAVE HELPED |
| 2633.TW  | Sell   | WAIT — MOC the full order |         213.1 | WORKING WOULD HAVE HELPED |

## 4.4b Reversal vs the crowding read

| ticker   | crowding_band   |   t_move_bps |   post_reversal_bps | expected           | grade   |
|:---------|:----------------|-------------:|--------------------:|:-------------------|:--------|
| 2324.TW  | LOW             |          955 |                1281 | modest reversal    | AGREE   |
| 1504.TW  | NO              |          578 |                 453 | no read — ungraded | AGREE   |
| 2610.TW  | LOW             |          269 |                 445 | modest reversal    | AGREE   |
| 2474.TW  | LOW             |          682 |                1327 | modest reversal    | AGREE   |
| 1102.TW  | LOW             |          494 |                 118 | modest reversal    | AGREE   |
| 1402.TW  | NO              |          343 |                 741 | no read — ungraded | AGREE   |
| 2633.TW  | LOW             |           20 |                 262 | modest reversal    | AGREE   |

Crowding-implication hit rate: 5/5.

## 4.5 Priors updated (what the next pack quotes)

| prior         |   before_median |   n_before |   after_median |   n_after |
|:--------------|----------------:|-----------:|---------------:|----------:|
| t_mult        |             nan |          0 |          13.3  |         7 |
| auction_share |             nan |          0 |         nan    |         0 |
| reversal_frac |             nan |          0 |           1.66 |         7 |

## Notes

REAL: crowding bands from the short archive truncated to May 12 (the pre-announcement read Step 2 would have had); drift/T-move/reversal/T-multiples from realized prices. HYPOTHETICAL, labeled: fills (uniform -8 bps vs close) and the 12 bps pre-trade estimate — we did not execute; the table demonstrates the reconciliation. auction_share=None for May names (outside the 60-day 5m window — the derivation runs live from Aug). Priors table is an in-memory copy; the real library updates only with graded events.
