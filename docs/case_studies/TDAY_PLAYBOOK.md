# T-Day Situations Playbook — 'you are here -> history says'

*Session 9i. 96 historical T-day observations (24 events, 5m with auction bars). Conditioning = what a trader OBSERVES BY NOON (side, tape direction vs flow, morning volume vs the name's own pre-announcement baseline). Outcomes = what happened AFTER noon. Cells under 8 days / 4 events are DATA-THIN and carry no recommendation. This is a descriptive lookup, refreshed every event — not a promise.*

## The table (favorable bps = helping the index-flow side)

|                                    |   n |   n_events |   pm_fav |   gap_fav |   p_gap_fav |   share |   t1_rev | label     |
|:-----------------------------------|----:|-----------:|---------:|----------:|------------:|--------:|---------:|:----------|
| ('Buy', 'AGAINST-flow', 'HEAVY')   |  10 |          9 |     0.47 |    -14.7  |        0.1  |    0.43 |   -10.91 | OK        |
| ('Buy', 'AGAINST-flow', 'NORMAL')  |  17 |         11 |     0    |    -56.88 |        0.24 |    0.61 |   254.87 | OK        |
| ('Buy', 'WITH-flow', 'HEAVY')      |   4 |          4 |   -30.17 |     34.89 |        0.75 |    0.45 |   174.93 | DATA-THIN |
| ('Buy', 'WITH-flow', 'NORMAL')     |  11 |          8 |   -34.07 |      0    |        0.18 |    0.27 |    79.01 | OK        |
| ('Sell', 'AGAINST-flow', 'HEAVY')  |  19 |         10 |    -0    |    -44.25 |        0.11 |    0.74 |   -14.68 | OK        |
| ('Sell', 'AGAINST-flow', 'NORMAL') |  12 |          8 |   -22.73 |    -54.72 |        0.08 |    0.71 |  -107.93 | OK        |
| ('Sell', 'WITH-flow', 'HEAVY')     |  13 |          9 |    -0    |     -0    |        0.38 |    0.76 |   -85.29 | OK        |
| ('Sell', 'WITH-flow', 'NORMAL')    |  10 |          7 |    -5.14 |    -31.25 |        0.1  |    0.6  |     9.17 | OK        |

## Reactions per situation (only OK-labeled cells)

- **Sell / WITH-flow / HEAVY** (n=13): Delete falling hard on heavy volume by noon. Measured: PM flat, gap ~flat (p_fav 0.38 — the least punitive print of any cell), share 0.76, T+1 continues DOWN (-85). Reading: the pressure is orderly and the close is fair here — MOC core carries it; no need to chase the morning.
- **Sell / WITH-flow / NORMAL** (n=10): Delete drifting down quietly. Measured: gap -31 against you (p_fav 0.10), T+1 ~flat. Reading: the print charges a moderate immediacy toll; envelope working ahead of the close earns its keep on this tape.
- **Sell / AGAINST-flow / HEAVY** (n=19): Delete RISING on heavy volume by noon — the squeeze tape (6919 family). Measured: PM flat, gap -44 against the seller (p_fav 0.11), and T+1 keeps going (-15): the squeeze usually completes AT and AFTER the close, not before it. Reading: do NOT count on the print to bail out a late sale; if crowding shows shorts covering, sell what you can into the strength you're given.
- **Sell / AGAINST-flow / NORMAL** (n=12): Delete firm on quiet tape. Measured: PM -23, gap -55 (p_fav 0.08 — the most punitive cell), and T+1 CONTINUES against (-108). Reading: quiet strength in a delete is the worst sell tape in the book — work early, expect the print to cost, plan the completion leg for further adverse drift, not a comeback.
- **Buy / WITH-flow / NORMAL** (n=11): Add drifting up quietly. Measured: PM gives back -34, gap ~flat (p_fav 0.18), T+1 reverses +79. Reading: midday strength fades into the close — patience beats chasing; the completion leg benefits from the T+1 give-back.
- **Buy / AGAINST-flow / HEAVY** (n=10): Add FALLING on heavy volume by noon — the crowd-unwind tape (2344 family). Measured: PM flat, gap -15 (p_fav 0.10), share only 0.43, T+1 ~flat. Reading: the unwind dominates through the close; buying weakness intraday is supported, but do not expect the print itself to favor you.
- **Buy / AGAINST-flow / NORMAL** (n=17): Add soft on quiet tape. Measured: gap -57 against the buyer (p_fav 0.24) but **T+1 reverses +255 — the strongest completion-leg signal in the table**. Reading: a soft add's print overshoots down and comes back hard; residuals bought patiently on T+1 historically beat chasing the close.

## The synthesis

**The systematic lesson across cells: the closing print typically lands AGAINST the obligated side** — favorable-gap probability runs 8-38%, median toll 15-55 bps. That is the measured cost of demanding immediacy at the bell (Dimensional's reconstitution result, reproduced at 5-minute scale on our own market). The limit-lock cases where the print FAVORS the obligated side (6919/2344) are the tails, not the rule. Second lesson: T+1 behavior is CELL-DEPENDENT — squeezes continue (Sell/AGAINST cells), soft-add prints snap back (+255) — so the completion-leg plan must be conditioned on the same midday observables, not a blanket reversal prior.

## Completion-leg note
t1_rev > 0 means the price came BACK after the print — median reversal per cell above feeds the residual/completion decision (patient completion historically beats chasing where t1_rev is positive and large).