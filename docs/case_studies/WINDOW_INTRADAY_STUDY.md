# Window Intraday Study — ann->eff at 5m (24 events, post-2023-05 floor)

*Session 9i. 1083 name-days across 24 events; registry-v2 H9/H10 evaluated with the locked criteria (event-clustered, LOO). Full ann->eff coverage audited (CNY-aware); TPEx gap excluded.*

## Verdicts

- **H9** (deletes' window-day auction share rises toward T): **ADOPT** — {"n_events": 22, "mean_bps": 168.9, "winrate": 1.0, "loo_stable": true, "effect_share": 0.169}
- **H10** (PM drift concentration grows toward T): **NULL-PIN** — {"n_events": 24, "mean_bps": -6.2, "winrate": 0.54, "loo_stable": true}

## Descriptive medians (class x window phase)

|                           |   n |   auc_share |   pm_vol |   am_fav |   pm_fav |   vol_x |
|:--------------------------|----:|------------:|---------:|---------:|---------:|--------:|
| ('FTSE', 'Buy', 'early')  |  78 |       0.06  |    0.094 |   17.045 |   11.628 |   0.932 |
| ('FTSE', 'Buy', 'late')   | 104 |       0.079 |    0.096 |   -5.459 |    0     |   1.064 |
| ('FTSE', 'Buy', 'mid')    |  71 |       0.071 |    0.097 |  -17.036 |  -12.723 |   0.874 |
| ('FTSE', 'Sell', 'early') |  78 |       0.083 |    0.103 |  -24.262 |   -0     |   1.071 |
| ('FTSE', 'Sell', 'late')  | 104 |       0.125 |    0.122 |   -0     |   -0     |   1.155 |
| ('FTSE', 'Sell', 'mid')   |  72 |       0.088 |    0.116 |   -0     |   -0     |   0.935 |
| ('MSCI', 'Buy', 'early')  |  48 |       0.075 |    0.097 |  -32.549 |    0     |   0.924 |
| ('MSCI', 'Buy', 'late')   |  64 |       0.075 |    0.101 |  -32.627 |   -6.468 |   1.642 |
| ('MSCI', 'Buy', 'mid')    | 115 |       0.065 |    0.094 |   31.447 |    0     |   1.08  |
| ('MSCI', 'Sell', 'early') |  84 |       0.085 |    0.11  |   -0     |   -0     |   1.418 |
| ('MSCI', 'Sell', 'late')  | 104 |       0.103 |    0.121 |   -0     |   -0     |   2.871 |
| ('MSCI', 'Sell', 'mid')   | 161 |       0.1   |    0.124 |   45.045 |   -0     |   1.452 |
## H9 decomposition (post-hoc, reported not re-verdicted)

The locked "late" bucket (rk >= -3) INCLUDES T-day, and the print
dominates the adopted effect: +0.169 share including T vs **+0.036
excluding T (winrate 0.86, 22 events)**. Honest reading: H9 ADOPT
stands under the locked criteria, but its content is largely "the
print is enormous" (already known); the genuinely new pre-T claim —
delete-name closing auctions grow ~3.6 share points in the final
days before T, in 86% of events — sits BELOW the locked 0.05
threshold and is therefore registered as **H9b for registry v3**
(criteria cannot move after results). Desk translation of the
modest version: the crowd starts using the closes before T, so
late-window MOC participation on deletes gets slightly less lonely
each day — but the print remains the event.

## Descriptive finding worth its own line

**MSCI delete window-day volumes run 1.4x baseline early -> 2.9x
late** (FTSE ~1.0x throughout): the MSCI obligation visibly trades
THROUGH the window, not just at the print — consistent with H1's
rejection (the completion signal exists but is too noisy per-name
per-day to time with) and with the May-26 working-wins result.
