# MSCI Aug-2026 QIR — ALL COVERED ASIA (ann Aug 12, eff Sep 1) — Full-Engine Pre-Registration Pack
*Generated 2026-07-28 by agents/review_engine.py — all eight layers, one pipeline. Point-in-time; NO-CALL where unvalidated; blocked calls shown, not hidden.*

## Taiwan (QIR: GMSR $4.4B, add ≥ $7.9B)
No calls.

**Measured T-day behavior (2026 events):** MSCI Sell: median 16.0x (n=8); MSCI Buy: no measured events — stated, not guessed

## Japan (QIR: GMSR $4.0B, add ≥ $7.2B)
No calls.

**Measured T-day behavior (2026 events):** MSCI Sell: median 16.0x (n=8); MSCI Buy: no measured events — stated, not guessed

## Korea (QIR: GMSR $4.1B, add ≥ $7.4B)
No calls.

**Measured T-day behavior (2026 events):** MSCI Sell: median 16.0x (n=8); MSCI Buy: no measured events — stated, not guessed

## China (QIR: GMSR $3.9B, add ≥ $7.0B)
No calls.

**Measured T-day behavior (2026 events):** MSCI Sell: median 16.0x (n=8); MSCI Buy: no measured events — stated, not guessed

## India (QIR: GMSR $2.4B, add ≥ $4.3B)
No calls.

**Measured T-day behavior (2026 events):** MSCI Sell: median 16.0x (n=8); MSCI Buy: no measured events — stated, not guessed

## Malaysia (QIR: GMSR $1.2B, add ≥ $2.2B)
No calls.

**Measured T-day behavior (2026 events):** MSCI Sell: median 16.0x (n=8); MSCI Buy: no measured events — stated, not guessed

## Indonesia (QIR: GMSR $1.2B, add ≥ $2.2B)
No calls.

**Measured T-day behavior (2026 events):** MSCI Sell: median 16.0x (n=8); MSCI Buy: no measured events — stated, not guessed

## HongKong (QIR: GMSR $2.1B, add ≥ $3.7B)
No calls.

**Measured T-day behavior (2026 events):** MSCI Sell: median 16.0x (n=8); MSCI Buy: no measured events — stated, not guessed

## NO-CALL markets
Singapore, Thailand, Philippines — no validated universe; explicit refusal, not omission.

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
Configuration = the May-replication-graded setup (69% of all 98 actual May changes at PIT; adds 17/17 zero false positives). Caps are APRIL vintage from the PIT cache — MANDATORY refresh at Aug-11 finalization along with the membership cross-check. Deletion calls are a probability-ranked watch zone (May-measured: delete precision 82% / recall 89%; cutline residents ~45-60%). Crowding now MULTI-MARKET (session 8g): Taiwan TWSE+TPEx daily, Japan JPX daily disclosed shorts, HK + China-H via SFC weekly CSV; KR/MY PROTOCOL (login/403 from sandbox), IN/ID structural — see appendix. KR/JP/other alias maps pending -> unverified discounts apply. FIF-cut deletions (Indonesia-class) and H-line share splits are DISCLOSED blind spots pending HKEX per-line shares + holdings baselines. SG/TH/PH remain NO-CALL (no validated universe).
## Appendix — multi-market crowding coverage (live reads, boundary names)

**Taiwan** — LIVE (daily): TWSE TWT93U (margin-short + SBL, shares) + TPEx margin/balance for .TWO (lots)
- 1101.TW (member, boundary): HIGH (+53%/30obs)
- 2207.TW (member, boundary): LOW (-37%/30obs); EXITING (-43% off peak)
- 2002.TW (member, boundary): LOW (-12%/30obs); EXITING (-34% off peak)
- 1326.TW (member, boundary): LOW (-52%/30obs); EXITING (-62% off peak)
- 2633.TW (non-member, boundary): LOW (-65%/30obs)
- 2324.TW (non-member, boundary): LOW (-70%/30obs)

**Japan** — LIVE (daily): JPX Short_Positions.xls — disclosed positions >=0.5%, summed per stock (floor, not census; deltas valid)
- 8136.T (member, boundary): LOW (-75%/6obs)
- 5706.T (member, boundary): LOW (-58%/4obs)
- 4004.T (member, boundary): HIGH (+460%/4obs); EXITING (-18% off peak)
- 2413.T (non-member, boundary): LOW (-10%/4obs)

**Korea** — PROTOCOL (daily): KRX short balance — login-gated from sandbox; desk/vendor feed on-site
- no data from sandbox (see status above)

**China** — LIVE (H-lines) / PROTOCOL (A-lines) (weekly): H-lines via the SFC HK file; A-line margin balances (SSE/SZSE) TLS-blocked from sandbox
- 9995.HK (member, boundary): HIGH (+45%/8obs)
- 2799.HK (non-member, boundary): LOW (-28%/8obs)
- 0177.HK (non-member, boundary): LOW (-31%/8obs)

**India** — STRUCTURAL (-): no public per-stock short-balance product; SLB volumes only (thin)
- no data from sandbox (see status above)

**Malaysia** — PROTOCOL (daily): Bursa RSS short-sale reports — 403 from sandbox
- no data from sandbox (see status above)

**Indonesia** — STRUCTURAL (-): short selling restricted to a small eligible list; no balance disclosure
- no data from sandbox (see status above)

**HongKong** — LIVE (weekly): SFC aggregated reportable short positions CSV (shares + HK$)
- 0083.HK (member, boundary): LOW (-10%/8obs)
- 0027.HK (member, boundary): HIGH (+84%/8obs)
- 0002.HK (member, boundary): MED (+22%/8obs)
- 0066.HK (member, boundary): MED (+7%/8obs)
- 0004.HK (non-member, boundary): LOW (-39%/8obs)
