# P(Addition), From Evidence

Generated 2026-08-11T06:00:23 by `scripts/tw_add_probability.py` — nothing typed.

## Model

```
P(add) = P_size   (discretion NOT priced)
```

`P_size`: 20,000 Monte Carlo draws over the three measured input errors — cutoff ±5%, MSCI's one-of-ten price dates scaled by each name's realised daily vol, and our FIF error against MSCI's implied FIF (n=10, mean -3.7%, sd 6.0%). The rule stays sharp in every draw; only inputs move — the Russell-literature fuzzy-threshold method.

**Not priced:** MSCI discretion — the member count can flex (§2.3.3) and ATVR runs on MSCI's own data. Stated wherever the probability is shown, multiplied nowhere.

| Name | x cutoff | **P(add)** | old flat |
| --- | ---: | ---: | ---: |
| Nanya Technology Corpora (2408) | 4.78x | **100%** | 62% |
| Nan Ya Printed Circuit B (8046) | 2.54x | **99%** | 62% |
| Winbond Electronics Corp (2344) | 2.50x | **100%** | 62% |
| Phison Electronics Corp. (8299) | 1.55x | **66%** | 37% |

## The backtest's warning

Per-band precision across 32 reviews (cap as a multiple of the addition bar):

| Band | added | not | precision | 95% CI |
| --- | ---: | ---: | ---: | --- |
| 0.4-0.445x | 2 | 51 | 0.038 | (0.01, 0.128) |
| 0.445-0.467x | 0 | 21 | 0.0 | (0, 0.155) |
| 0.467-0.5x | 1 | 17 | 0.056 | (0.01, 0.258) |
| 0.5-0.533x | 1 | 20 | 0.048 | (0.008, 0.227) |
| 0.533-0.6x | 6 | 12 | 0.333 | (0.163, 0.563) |
| 0.6-0.667x | 6 | 9 | 0.4 | (0.198, 0.643) |
| 0.667-0.833x | 6 | 4 | 0.6 | (0.313, 0.832) |
| 0.833-1.0x | 5 | 3 | 0.625 | (0.306, 0.863) |
| >1.0x | 1 | 19 | 0.05 | (0.009, 0.236) |

The top band reads 5% because a handful of very large names fail the float and foreign-room gates at every review — size clearance alone is nowhere near sufficient. Our candidates are screened through those gates before any probability is struck.
