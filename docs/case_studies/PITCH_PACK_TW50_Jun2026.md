# Pre-Event Analytics Pack — FTSE TWSE Taiwan 50 — June 2026 review
*Prepared 2026-06-01 · announcement 2026-06-05 · effective 2026-06-18*

*Every number below is generated from public data with a stated method; the track record section includes our misses. Point-in-time: nothing in this pack uses data after 2026-06-01.*

## 1. Predicted changes
|   ticker | name           | change   | confidence   |   margin_pct |
|---------:|:---------------|:---------|:-------------|-------------:|
|     3443 | Global Unichip | ADD      | HIGH         |           78 |
|     3665 | BizLink        | ADD      | HIGH         |           34 |
|     8046 | Nan Ya PCB     | ADD      | HIGH         |           22 |
|     4958 | Zhen Ding      | ADD      | HIGH         |           17 |
|     6919 | Compermed      | DELETE   | LOW          |            8 |
|     2207 | Hotai          | DELETE   | LOW          |            6 |
|     1101 | Taiwan Cement  | DELETE   | LOW          |            4 |
|     1326 | FCFC           | DELETE   | LOW          |            3 |
|     2615 | Wan Hai        | DELETE   | LOW          |            2 |

## 2. Expected flows
|   ticker | side   |   flow_usd_m |   adv_days | bucket    |
|---------:|:-------|-------------:|-----------:|:----------|
|     3443 | Buy    |          340 |       7.3  | MULTI-DAY |
|     3665 | Buy    |          310 |       7.4  | MULTI-DAY |
|     8046 | Buy    |          300 |       7.2  | MULTI-DAY |
|     4958 | Buy    |          330 |       7.3  | MULTI-DAY |
|     6919 | Sell   |          120 |       7.8  | MULTI-DAY |
|     2207 | Sell   |          350 |       7.4  | MULTI-DAY |
|     2330 | Sell   |          440 |       0.08 | MOC       |

## 3. What event days actually look like (measured)
- **MSCI deletions (Sell)**: T-day volume median 16.0x normal (range 7.1-38.1x, n=8 measured 2026 events)
- **FTSE deletions (Sell)**: no measured events yet (stated, not guessed)
- **FTSE additions (Buy)**: no measured events yet (stated, not guessed)

## 4. Street positioning (short-ledger read, pre-2026-06-05 data only)
|   ticker | label                             |   pre_ann_build_pct | crowding   | read                                                                               |
|---------:|:----------------------------------|--------------------:|:-----------|:-----------------------------------------------------------------------------------|
|     3443 | GUC (add candidate)               |                27.4 | HIGH       | street heavily positioned — pressure part-spent; expect bigger post-event reversal |
|     3665 | BizLink (add candidate)           |                -9.7 | LOW        | unpriced — full event pressure still ahead                                         |
|     8046 | NanYaPCB (add candidate)          |                24.8 | MED        | moderate positioning                                                               |
|     4958 | ZhenDing (add cand.)              |               -12.9 | LOW        | unpriced — full event pressure still ahead                                         |
|     6919 | Compermed (del candidate)         |                -8.9 | LOW        | unpriced — full event pressure still ahead                                         |
|     2207 | Hotai (del cand.)                 |                16.8 | MED        | moderate positioning                                                               |
|     1101 | TaiwanCement (del candidate)      |                46.1 | HIGH       | street heavily positioned — pressure part-spent; expect bigger post-event reversal |
|     1326 | FCFC (del cand.)                  |               -12.3 | LOW        | unpriced — full event pressure still ahead                                         |
|     2615 | WanHai (del candidate)            |               -14   | LOW        | unpriced — full event pressure still ahead                                         |
|     2002 | China Steel (boundary watch)      |                74.5 | HIGH       | street heavily positioned — pressure part-spent; expect bigger post-event reversal |
|     1301 | Formosa Plastics (boundary watch) |                13.5 | MED        | moderate positioning                                                               |

## 5. Per-name risk flags
- **3443**: SIZE: 7.3 ADV-days — multi-day plan required; LIMIT: ±10% band — lock risk on event day
- **6919**: SIZE: 7.8 ADV-days — multi-day plan required; LIMIT: ±10% band — lock risk on event day; BORROW: constrained lending — short-side hedging impaired, squeeze risk; REVERSAL: large delete — plan the completion leg for the covering bounce
- **2207**: SIZE: 7.4 ADV-days — multi-day plan required; LIMIT: ±10% band — lock risk on event day; REVERSAL: large delete — plan the completion leg for the covering bounce
- **2330**: LIMIT: ±10% band — lock risk on event day

## 6. Our graded track record (misses included)
| claim                              | record                                                                                                                              | caveat                                                                                    | source                                    |
|:-----------------------------------|:------------------------------------------------------------------------------------------------------------------------------------|:------------------------------------------------------------------------------------------|:------------------------------------------|
| Addition predictions               | 11/11 across 5 real reviews, 2 providers, 3 markets                                                                                 | 1 false positive (Korea) — diagnosed input data quality, kept in report                   | DUAL_PROVIDER_backtests_Korea_ChinaA50.md |
| Coverage-rule deletion predictions | 14/14 (TW May 7/7, TW Feb 4/4, KR May 3/3)                                                                                          | buffer calibrated on one review pair; Aug 12 is the frozen live test                      | MSCI_Taiwan_May2026_backtest.md           |
| Rank-boundary deletion predictions | ~50-60%, every call self-labeled LOW confidence                                                                                     | structurally noise-fragile (measured by Monte Carlo); shipped as watch zone, not signal   | FTSE_Taiwan50_Jun2026_backtest.md         |
| T-day volume multiples             | measured per provider x side on 21 real 2026 names (MSCI deletes median 16x; FTSE ~5x)                                              | one cycle of events; ranges shown, not points                                             | EVENT_FLOW_STUDY_2026Q2.md                |
| Execution strategy rules           | own rule falsified twice by realized grading, refined in-sample 355->0 bps regret                                                   | refined rule FROZEN, unvalidated until Aug/Sep cycle — stated before the event, not after | EVENT_FLOW_STUDY_2026Q2.md                |
| Positioning reads                  | arb->tracker handoff measured 8/8; within-foreign split via SBL ledger; STREET-ONLY overlay caught our own China Steel miss ex ante | Taiwan/Korea data depth; other markets thinner                                            | EVENT_DATA_USEFULNESS_2026Q2.md           |

## Notes
Universe is reconstruction-grade (public caps/floats, +-30%) — a desk build replaces it with vendor cap files. Rank-boundary deletion calls are structurally LOW-confidence (measured by Monte Carlo, see track record) and shipped as a WATCH ZONE, not a signal: the boundary names 2002/1301 sit in the zone our model cannot rank reliably — and the short ledger (section 4) shows the street positioned for 2002 regardless of any model. TSMC reweight trim (-$440M) is the second-largest flow of the event and costs nothing to execute (0.08 ADV-days, MOC).


---

## Post-event validation (the pack graded against reality)
- Predictions: 6/8 actual changes called (9 calls made)
- HIGH-confidence precision: 4/4 HIGH-confidence calls correct
- Missed calls: 1101, 1326, 2615
- Changes we did not predict: 2002, 1301

*This section is generated by the same code that built the pack — the desk grades itself before the client does.*