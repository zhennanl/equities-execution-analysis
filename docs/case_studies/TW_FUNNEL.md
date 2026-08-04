# The Screening Funnel — Taiwan (validated replay + Aug-2026 prediction)

*Session 9i. How ~500 names boil down to calls, stage by stage; the funnel observes the engine's own artifacts and can never drift from it. UI: lifecycle Tab 1 expander. Decade scope: official outcomes for all 44 reviews are in MSCI_APAC_CHANGES_2015_2026.md; funnel REPLAY beyond May-2026 is gated on historical share/float vintages — stated, not fudged.*

## May-2026 SAIR — validation

| stage | n | rule | detail |
|---|---|---|---|
| S0 universe | 516 | count-anchored: real named stocks + synthetic tail pinned to the published constituent count (L0) | 16 real named + 500 tail; 83 members |
| S1 eligible | 516 | free float >= 0.15 AND ATVR liquidity floor (L1) | eliminated 0 |
| S2 thresholds | 516 | ladder to 85% coverage -> GMSR; add bar = 1.15x; deletion floor = 0.5x (L2-L3) | GMSR $4.4B | add >= $5.1B | floor $2.2B |
| S3 candidates | 11 | non-members above the add bar; members below the floor or failing screens (L3-L4) | 1 add / 10 delete; 0 in the ±15% watch band |
| S4 churn-buffered | 11 | prior review's changes excluded from opposite-side candidacy (L5) | nothing to exclude |
| S5 verified | 11 | no call ships on unverified membership — the Feng Tay gate (L7) | 0 blocked |
| FINAL calls | 11 | Laplace-shrunk probabilities from the graded record (L8) | ADD 6223.TWO p=0.64; DELETE 1101.TW p=0.6; DELETE 1102.TW p=0.6; DELETE 1326.TW p=0.6; DELETE 1402.TW p=0.6; DELETE 1504.TW p=0.6; DELETE 2207.TW p=0.6; DELETE 2324.TW p=0.6; DELETE 2474.TW p=0.6; DELETE 2610.TW p=0.6; DELETE 2633.TW p=0.6 |

## Aug-2026 QIR — prediction

| stage | n | rule | detail |
|---|---|---|---|
| S0 universe | 516 | count-anchored: real named stocks + synthetic tail pinned to the published constituent count (L0) | 16 real named + 500 tail; 83 members |
| S1 eligible | 516 | free float >= 0.15 AND ATVR liquidity floor (L1) | eliminated 0 |
| S2 thresholds | 516 | ladder to 85% coverage -> GMSR; add bar = 1.8x (QIR); deletion floor = 0.5x (L2-L3) | GMSR $4.8B | add >= $8.6B | floor $2.4B |
| S3 candidates | 0 | non-members above the add bar; members below the floor or failing screens (L3-L4) | 0 add / 0 delete; 0 in the ±15% watch band |
| S4 churn-buffered | 0 | prior review's changes excluded from opposite-side candidacy (L5) | nothing to exclude |
| S5 verified | 0 | no call ships on unverified membership — the Feng Tay gate (L7) | 0 blocked |
| FINAL calls | 0 | Laplace-shrunk probabilities from the graded record (L8) | 0 calls at the OBSERVABLE margin — blind band below the named floor is declared, not denied |

## Validation grade (May-26, vs official key)

- Deletions hit (visible): ['1102.TW', '1402.TW', '1504.TW', '2324.TW', '2474.TW', '2610.TW', '2633.TW']
- Deletions missed (visible): []
- Adds hit: ['6223.TWO'] / missed visible: []
- False calls: adds [], dels ['1101.TW', '1326.TW', '2207.TW']
- Ungradable below the named floor: []

Reading: the funnel recovers the graded engine result — visible deletions caught at the thresholds stage, the below-floor names are the declared breadth class, and the Aug-26 funnel shows the same structure ending at zero VISIBLE candidates with the blind band stated.