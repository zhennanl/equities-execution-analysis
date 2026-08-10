# Index Rebalancing, the Institutional Framing

Generated 2026-08-11T04:39:07 by `scripts/tw_forced_flow.py`. Every figure below comes from the JSON that script writes; nothing here is typed.

## The framework

Forced demand is not fundamental demand. A tracker buys a new constituent because its benchmark contains it, not because it has a view — the flow is price-insensitive and its date is published in advance. That reduces to:

```
Expected Flow = P(index add) x delta-weight x AUM
Alpha         = Expected Flow / Available Liquidity
```

## Applied to the August 2026 candidates

AUM is **USD 60bn** — the sourced floor from `scripts/tw_mandate_size.py`, not the USD 180bn constant this project inherited. Weights are estimated free-float caps over the index's own free-float value, USD 3,183bn.

| Name | P(add) | Weight | Forced flow | x ADV | x one close | Expected x ADV |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Winbond Electronics Corpor (2344) | 62% | 0.396% | USD 238m | 43% | 4.5x | 26% |
| Nanya Technology Corporati (2408) | 62% | 0.512% | USD 307m | 34% | 3.6x | 21% |
| Nan Ya Printed Circuit Boa (8046) | 62% | 0.223% | USD 134m | 27% | 2.8x | 16% |

The **x ADV** column is the framework's ratio against a whole day's liquidity. The **x one close** column divides by the liquidity that is actually there when the flow arrives — on an effective day 79% of volume prints in the closing auction, and an ordinary close in these names takes only 9.5% of the day. That is the denominator a dealer should use, and it is about ten times smaller than a session.

**Expected x ADV** applies the probability. The site itself reports the conditional figure instead, because a desk sizing the order on the effective day does not discount it — either the order is there in full or it is not there at all. The expected version is the number for positioning BEFORE the announcement.

## The four pools of forced demand

| Pool | Counted here? | Where |
| --- | --- | --- |
| index ETFs | yes | tw_tracking_aum.py, fund by fund |
| index mutual funds | yes | inside the non-ETF indexed floor |
| institutional passive mandates | yes | inverted from MSCI's non-ETF fee revenue |
| benchmark-aware active funds | **no** | not visible without holdings data — a manager holding none of a new 1% constituent is running a -1% active bet by standing still, so some of this money buys too |

## What cannot be replicated without institutional data

1. **The fourth pool is invisible.** Benchmark-aware active managers buy too, and holdings data is the only way to size that.
2. **The historical test conditioned on the wrong variable.** The out-of-sample work tested `adv`, `borrow_build`, `gap1`, `n_same_review`, `pre_drift`, `prevol` — none of which is flow over liquidity. Building that feature needs a point-in-time float stack for every review back to 2015.
3. **No cross-section.** A platform diversifies a noisy per-event edge across every index and region. One market cannot.

## What would change with access, in order of value

1. Licensed index files — real free float and the published constituent list. Removes the estimation band from both the weight and P(add).
2. Mandate data — turns the AUM floor into a range with a defensible middle.
3. Holdings data on benchmark-aware active funds — the fourth pool.
4. A borrow book — crowding while it forms, not a week later.
