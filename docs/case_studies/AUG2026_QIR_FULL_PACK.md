# MSCI Aug-2026 QIR (ann Aug 12, eff Sep 1) — Full-Engine Pre-Registration Pack
*Generated 2026-07-28 by agents/review_engine.py — all eight layers, one pipeline. Point-in-time; NO-CALL where unvalidated; blocked calls shown, not hidden.*

## Taiwan (QIR: GMSR $5.5B, add ≥ $10.0B)
| call   | ticker   |   cap_usd_b |   x_gmsr |   p_correct | flow_usd_m   |   adv_days | bucket    | crowding         | rationale                                                                     | verified                                   |
|:-------|:---------|------------:|---------:|------------:|:-------------|-----------:|:----------|:-----------------|:------------------------------------------------------------------------------|:-------------------------------------------|
| ADD    | 3443.TW  |        15.1 |     2.73 |        0.85 | 464-836      |       10.8 | MULTI-DAY | HIGH (+67%/30d)  | non-member above threshold: cap $15.1B = 2.73x GMSR ($5.5B); threshold $10.0B | YES — reconciled vs official change ledger |
| ADD    | 3665.TW  |        13.3 |     2.4  |        0.8  | 588-1058     |       15.5 | MULTI-DAY | HIGH (+116%/30d) | non-member above threshold: cap $13.3B = 2.40x GMSR ($5.5B); threshold $10.0B | YES — reconciled vs official change ledger |
| ADD    | 8046.TW  |        19.4 |     3.51 |        0.85 | 355-640      |        6.4 | MULTI-DAY | LOW (-26%/30d)   | non-member above threshold: cap $19.4B = 3.51x GMSR ($5.5B); threshold $10.0B | YES — reconciled vs official change ledger |
| ADD    | 4958.TW  |        14.2 |     2.57 |        0.85 | 492-886      |       12.1 | MULTI-DAY | LOW (-37%/30d)   | non-member above threshold: cap $14.2B = 2.57x GMSR ($5.5B); threshold $10.0B | YES — reconciled vs official change ledger |

Expected correct calls: **3.35** of 4

**Measured T-day behavior (2026 events):** MSCI Sell: median 16.0x (n=8); MSCI Buy: no measured events — stated, not guessed
- RISK 3443.TW: SIZE: 5.0 ADV-days — multi-day plan required; LIMIT: ±10% band — lock risk on event day
- RISK 3665.TW: SIZE: 5.0 ADV-days — multi-day plan required; LIMIT: ±10% band — lock risk on event day
- RISK 8046.TW: SIZE: 5.0 ADV-days — multi-day plan required; LIMIT: ±10% band — lock risk on event day
- RISK 4958.TW: SIZE: 5.0 ADV-days — multi-day plan required; LIMIT: ±10% band — lock risk on event day

## Korea (QIR: GMSR $4.3B, add ≥ $7.7B)
| call   | ticker    |   cap_usd_b |   x_gmsr |   p_correct | flow_usd_m   |   adv_days | bucket    | crowding   | rationale                                                               | verified                                      |
|:-------|:----------|------------:|---------:|------------:|:-------------|-----------:|:----------|:-----------|:------------------------------------------------------------------------|:----------------------------------------------|
| DELETE | 011170.KS |         1.7 |     0.41 |         0.6 | 37-67        |        7.5 | MULTI-DAY | no data    | member below threshold: cap $1.7B = 0.41x GMSR ($4.3B); threshold $2.1B | NO — verify before committing (Feng Tay rule) |

Expected correct calls: **0.6** of 1

**Measured T-day behavior (2026 events):** MSCI Sell: median 16.0x (n=8); MSCI Buy: no measured events — stated, not guessed

## Japan (QIR: GMSR $3.9B, add ≥ $7.0B)
| call   | ticker   |   cap_usd_b |   x_gmsr |   p_correct | flow_usd_m   |   adv_days | bucket    | crowding   | rationale                                                                      | verified                                      |
|:-------|:---------|------------:|---------:|------------:|:-------------|-----------:|:----------|:-----------|:-------------------------------------------------------------------------------|:----------------------------------------------|
| ADD    | 285A.T   |       157.3 |    40.51 |        0.64 | 5326-9587    |       11.9 | MULTI-DAY | no data    | non-member above threshold: cap $157.3B = 40.51x GMSR ($3.9B); threshold $7.0B | NO — verify before committing (Feng Tay rule) |
| ADD    | 3659.T   |        12.6 |     3.24 |        0.64 | 260-469      |        7.2 | MULTI-DAY | no data    | non-member above threshold: cap $12.6B = 3.24x GMSR ($3.9B); threshold $7.0B   | NO — verify before committing (Feng Tay rule) |
| ADD    | 4755.T   |        11.7 |     3.01 |        0.64 | 295-531      |        8.8 | MULTI-DAY | no data    | non-member above threshold: cap $11.7B = 3.01x GMSR ($3.9B); threshold $7.0B   | NO — verify before committing (Feng Tay rule) |

Expected correct calls: **1.92** of 3

**Measured T-day behavior (2026 events):** MSCI Sell: median 16.0x (n=8); MSCI Buy: no measured events — stated, not guessed

## NO-CALL markets
China, Hong Kong, Singapore, India, Thailand, Malaysia, Indonesia, Philippines — no validated universe; explicit refusal, not omission.

## Graded track record (misses included)
| claim                              | record                                                                                                                              | caveat                                                                                    | source                                    |
|:-----------------------------------|:------------------------------------------------------------------------------------------------------------------------------------|:------------------------------------------------------------------------------------------|:------------------------------------------|
| Addition predictions               | 11/11 across 5 real reviews, 2 providers, 3 markets                                                                                 | 1 false positive (Korea) — diagnosed input data quality, kept in report                   | DUAL_PROVIDER_backtests_Korea_ChinaA50.md |
| Coverage-rule deletion predictions | 14/14 (TW May 7/7, TW Feb 4/4, KR May 3/3)                                                                                          | buffer calibrated on one review pair; Aug 12 is the frozen live test                      | MSCI_Taiwan_May2026_backtest.md           |
| Rank-boundary deletion predictions | ~50-60%, every call self-labeled LOW confidence                                                                                     | structurally noise-fragile (measured by Monte Carlo); shipped as watch zone, not signal   | FTSE_Taiwan50_Jun2026_backtest.md         |
| T-day volume multiples             | measured per provider x side on 21 real 2026 names (MSCI deletes median 16x; FTSE ~5x)                                              | one cycle of events; ranges shown, not points                                             | EVENT_FLOW_STUDY_2026Q2.md                |
| Execution strategy rules           | own rule falsified twice by realized grading, refined in-sample 355->0 bps regret                                                   | refined rule FROZEN, unvalidated until Aug/Sep cycle — stated before the event, not after | EVENT_FLOW_STUDY_2026Q2.md                |
| Positioning reads                  | arb->tracker handoff measured 8/8; within-foreign split via SBL ledger; STREET-ONLY overlay caught our own China Steel miss ex ante | Taiwan/Korea data depth; other markets thinner                                            | EVENT_DATA_USEFULNESS_2026Q2.md           |

## Notes
Flow estimates: passive-ownership-rate heuristic (5-9% of float cap, MSCI-linked trackers, EM stacking) — v1, validated against Sep-1 realized prints. ADV proxied at 0.4% of cap (overstates ADV-days for liquid AI names — direction disclosed). Korea/Japan alias maps pending -> their deletes carry UNVERIFIED probability; Japan candidates remain conditional WATCH per addendum 7w (Kioxia cap flag + membership unverified). Finalize + git-commit before Aug 11; grade after Sep 1 with the pre-declared criteria in QIR_AUG2026_PRERUN.md.
---

## ⚠️ CORRECTION (session 7z) — Taiwan ADD calls INVALIDATED by the PIT May replication

The point-in-time May-2026 replication (PIT_MAY2026_TAIWAN.md) exposed
a stale-membership error ON THE ADD SIDE: GUC's April-30 cap was
$17.5B and BizLink's $16.5B — both far above May's SAIR add threshold
($5.9B) — yet MSCI added NEITHER in May. The only consistent reading:
**3443/3665/8046/4958 were already MSCI Taiwan Standard members**, and
our universe wrongly marked them non-members by conflating their June
FTSE-TW50 additions with MSCI membership (different index).

Status of the Taiwan section: **ALL FOUR ADD CALLS WITHDRAWN pending
membership verification** (EWT holdings file = definitive check,
manual download). The crowding readings on these names remain valid as
positioning data, but the "MSCI add" thesis they decorated is
unverified at best, wrong at worst. Korea and Japan sections
unaffected (already unverified-discounted). Portfolio expectation
drops from ~5.9 to ~2.5 pending verification.

Root cause class: STALE_NONMEMBER — the ledger reconciliation only
replays RECENT official change lists; it cannot establish the BASE
membership state. Fix (engine-level): a full membership baseline from
fund holdings (ingest_holdings.py pipeline, EWT for Taiwan) becomes a
mandatory pre-registration input alongside the change-list ledger.
The Feng Tay rule now has a sibling: no add call without a verified
non-membership baseline.
