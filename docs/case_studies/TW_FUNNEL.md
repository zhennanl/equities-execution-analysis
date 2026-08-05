# The Screening Funnel — Taiwan (validated replay + Aug-2026 prediction)

*Session 9i. How ~500 names boil down to calls, stage by stage; the funnel observes the engine's own artifacts and can never drift from it. UI: lifecycle Tab 1 expander. Decade scope: official outcomes for all 44 reviews are in MSCI_APAC_CHANGES_2015_2026.md; funnel REPLAY beyond May-2026 is gated on historical share/float vintages — stated, not fudged.*

## May-2026 SAIR — validation

| stage | n | rule | detail |
|---|---|---|---|
| S0 acquisition | 16 | engine Step 1 — named universe from public data: cap = price x shares (yfinance, FX to USD), free-float estimated from holder filings, ADV 60d; membership rolled forward from official review results (never assumed) | 16 named boundary stocks (15 members near the deletion floor, 1 candidates near the add bar); market body below the boundary is modeled, not fetched — see next stage |
| S0 universe | 516 | count-anchored: real named stocks + synthetic tail pinned to the published constituent count (L0) | 16 real named + 500 tail; 83 members |
| S1 eligible | 516 | free float >= 0.15 AND ATVR liquidity floor (L1) | eliminated 0 |
| S2 thresholds | 516 | ladder to 85% coverage -> GMSR; add bar = 1.15x; deletion floor = 0.5x (L2-L3) | GMSR $4.4B | add >= $5.1B | floor $2.2B |
| S3 candidates | 11 | non-members above the add bar; members below the floor or failing screens (L3-L4) | 1 add / 10 delete; 0 in the ±15% watch band |
| S4 churn-buffered | 11 | prior review's changes excluded from opposite-side candidacy (L5) | nothing to exclude |
| S5 verified | 11 | no call ships on unverified membership — the Feng Tay gate (L7) | 0 blocked |
| FINAL calls | 11 | Laplace-shrunk probabilities from the graded record (L8) | ADD 6223.TWO p=0.64; DELETE 1101.TW p=0.6; DELETE 1102.TW p=0.6; DELETE 1326.TW p=0.6; DELETE 1402.TW p=0.6; DELETE 1504.TW p=0.6; DELETE 2207.TW p=0.6; DELETE 2324.TW p=0.6; DELETE 2474.TW p=0.6; DELETE 2610.TW p=0.6; DELETE 2633.TW p=0.6 |

### Name journeys (the shortlist at every stage)

| ticker | role | cap_usd_b | threshold | x_threshold | status | final | official |
|---|---|---|---|---|---|---|---|
| 2330.TW | member | 1699.02 | hard 0.5x floor $2.2B | 771.28 | SAFE — comfortably above the floor | no call | unchanged — correct |
| 2308.TW | member | 172.14 | hard 0.5x floor $2.2B | 78.14 | SAFE — comfortably above the floor | no call | unchanged — correct |
| 2454.TW | member | 127.42 | hard 0.5x floor $2.2B | 57.84 | SAFE — comfortably above the floor | no call | unchanged — correct |
| 2317.TW | member | 91.83 | hard 0.5x floor $2.2B | 41.69 | SAFE — comfortably above the floor | no call | unchanged — correct |
| 6223.TWO | non-member | 14.8 | add bar $5.1B | 2.92 | ADD candidate (above the add bar) | ADD (p=0.64) | ADDED — HIT |
| 1326.TW | member | 9.31 | hard 0.5x floor $2.2B | 4.22 | DELETE candidate — below the effective deletion bar (SAIR migration sweep sits ABOVE the hard 0.5x floor; GIMI §3.1.5.1) | DELETE (p=0.6) | RETAINED — false call (cutline resident) |
| 2002.TW | member | 8.75 | hard 0.5x floor $2.2B | 3.97 | SAFE — comfortably above the floor | no call | unchanged — correct |
| 2207.TW | member | 7.83 | hard 0.5x floor $2.2B | 3.56 | DELETE candidate — below the effective deletion bar (SAIR migration sweep sits ABOVE the hard 0.5x floor; GIMI §3.1.5.1) | DELETE (p=0.6) | RETAINED — false call (cutline resident) |
| 1101.TW | member | 5.46 | hard 0.5x floor $2.2B | 2.48 | DELETE candidate — below the effective deletion bar (SAIR migration sweep sits ABOVE the hard 0.5x floor; GIMI §3.1.5.1) | DELETE (p=0.6) | RETAINED — false call (cutline resident) |
| 2633.TW | member | 4.39 | hard 0.5x floor $2.2B | 1.99 | DELETE candidate — below the effective deletion bar (SAIR migration sweep sits ABOVE the hard 0.5x floor; GIMI §3.1.5.1) | DELETE (p=0.6) | DELETED — HIT |
| 1504.TW | member | 4.38 | hard 0.5x floor $2.2B | 1.99 | DELETE candidate — below the effective deletion bar (SAIR migration sweep sits ABOVE the hard 0.5x floor; GIMI §3.1.5.1) | DELETE (p=0.6) | DELETED — HIT |
| 1402.TW | member | 4.04 | hard 0.5x floor $2.2B | 1.84 | DELETE candidate — below the effective deletion bar (SAIR migration sweep sits ABOVE the hard 0.5x floor; GIMI §3.1.5.1) | DELETE (p=0.6) | DELETED — HIT |
| 2324.TW | member | 3.8 | hard 0.5x floor $2.2B | 1.72 | DELETE candidate — below the effective deletion bar (SAIR migration sweep sits ABOVE the hard 0.5x floor; GIMI §3.1.5.1) | DELETE (p=0.6) | DELETED — HIT |
| 1102.TW | member | 3.57 | hard 0.5x floor $2.2B | 1.62 | DELETE candidate — below the effective deletion bar (SAIR migration sweep sits ABOVE the hard 0.5x floor; GIMI §3.1.5.1) | DELETE (p=0.6) | DELETED — HIT |
| 2474.TW | member | 3.35 | hard 0.5x floor $2.2B | 1.52 | DELETE candidate — below the effective deletion bar (SAIR migration sweep sits ABOVE the hard 0.5x floor; GIMI §3.1.5.1) | DELETE (p=0.6) | DELETED — HIT |
| 2610.TW | member | 3.22 | hard 0.5x floor $2.2B | 1.46 | DELETE candidate — below the effective deletion bar (SAIR migration sweep sits ABOVE the hard 0.5x floor; GIMI §3.1.5.1) | DELETE (p=0.6) | DELETED — HIT |

## Aug-2026 QIR — prediction

| stage | n | rule | detail |
|---|---|---|---|
| S0 acquisition | 16 | engine Step 1 — named universe from public data: cap = price x shares (yfinance, FX to USD), free-float estimated from holder filings, ADV 60d; membership rolled forward from official review results (never assumed) | 16 named boundary stocks (9 members near the deletion floor, 7 candidates near the add bar); market body below the boundary is modeled, not fetched — see next stage |
| S0 universe | 516 | count-anchored: real named stocks + synthetic tail pinned to the published constituent count (L0) | 16 real named + 500 tail; 77 members |
| S1 eligible | 516 | free float >= 0.15 AND ATVR liquidity floor (L1) | eliminated 0 |
| S2 thresholds | 516 | ladder to 85% coverage -> GMSR; add bar = 1.8x (QIR); deletion floor = 0.5x (L2-L3) | GMSR $4.8B | add >= $8.6B | floor $2.4B |
| S3 candidates | 0 | non-members above the add bar; members below the floor or failing screens (L3-L4) | 0 add / 0 delete; 0 in the ±15% watch band |
| S4 churn-buffered | 0 | prior review's changes excluded from opposite-side candidacy (L5) | nothing to exclude |
| S5 verified | 0 | no call ships on unverified membership — the Feng Tay gate (L7) | 0 blocked |
| FINAL calls | 0 | Laplace-shrunk probabilities from the graded record (L8) | 0 calls at the OBSERVABLE margin — blind band below the named floor is declared, not denied |

### Name journeys (the shortlist at every stage)

| ticker | role | cap_usd_b | threshold | x_threshold | status | final |
|---|---|---|---|---|---|---|
| 2330.TW | member | 1846.33 | hard 0.5x floor $2.4B | 771.86 | SAFE — comfortably above the floor | no call |
| 2454.TW | member | 188.68 | hard 0.5x floor $2.4B | 78.88 | SAFE — comfortably above the floor | no call |
| 2308.TW | member | 128.81 | hard 0.5x floor $2.4B | 53.85 | SAFE — comfortably above the floor | no call |
| 2317.TW | member | 104.6 | hard 0.5x floor $2.4B | 43.73 | SAFE — comfortably above the floor | no call |
| 6223.TWO | member | 17.73 | hard 0.5x floor $2.4B | 7.41 | SAFE — comfortably above the floor | no call |
| 1326.TW | member | 10.36 | hard 0.5x floor $2.4B | 4.33 | SAFE — comfortably above the floor | no call |
| 2002.TW | member | 8.79 | hard 0.5x floor $2.4B | 3.68 | SAFE — comfortably above the floor | no call |
| 2207.TW | member | 8.5 | hard 0.5x floor $2.4B | 3.55 | SAFE — comfortably above the floor | no call |
| 1101.TW | member | 5.25 | hard 0.5x floor $2.4B | 2.19 | SAFE — comfortably above the floor | no call |
| 2324.TW | non-member | 4.85 | add bar $8.6B | 0.56 | NOT CLOSE — below the add bar | no call |
| 1504.TW | non-member | 4.59 | add bar $8.6B | 0.53 | NOT CLOSE — below the add bar | no call |
| 2633.TW | non-member | 4.27 | add bar $8.6B | 0.5 | NOT CLOSE — below the add bar | no call |
| 1402.TW | non-member | 4.26 | add bar $8.6B | 0.5 | NOT CLOSE — below the add bar | no call |
| 2610.TW | non-member | 4.04 | add bar $8.6B | 0.47 | NOT CLOSE — below the add bar | no call |
| 1102.TW | non-member | 3.3 | add bar $8.6B | 0.38 | NOT CLOSE — below the add bar | no call |
| 2474.TW | non-member | 2.9 | add bar $8.6B | 0.34 | NOT CLOSE — below the add bar | no call |

## Selection method per stage (GIMI May-2026 book citations)

- **S0 acquisition** — OURS. The book reviews the full equity universe (GIMI §3.1.1); changes only occur at the size boundary, so we curate the names nearest it from our own cap ranking and model the rest as a count-anchored tail. Caps = price x shares (yfinance, FX to USD) as of the frame date.
- **S0 universe** — OURS + MSCI factsheet. Total member count pinned to the published constituent count so the coverage walk (GIMI §2.3.5) lands where the real index size puts it.
- **S1 eligible** — GIMI §2.2 / §3.1.2: investability screens — free float >= 0.15 and ATVR liquidity floor. Existing constituents get 2/3-of-threshold retention grace (§3.1.2.4, §3.1.6.2).
- **S2 thresholds** — GIMI §2.3.2 (p.24): walk the cap ladder to 85% free-float coverage -> GMSR reference; Range = 0.5x to 1.15x. QIR add bar 1.8x, SAIR 1.15x; deletion floor 0.5x.
- **S3 candidates** — GIMI §3.1.4-3.1.5: non-members above the add bar become ADD candidates; members below the floor DELETE candidates; the +-15% band is the watch zone (hazard class, ~2/3 convert - our decade measurement, not the book's).
- **S4 churn-buffered** — GIMI §3.1.5.1 (p.44): buffer zones control migration and index turnover — the prior review's changes are excluded from opposite-side candidacy.
- **S5 verified** — OURS (Feng Tay gate): no call ships on unverified membership. The book assumes MSCI knows its own index; a predictor must prove it does.
- **FINAL calls** — OURS: Laplace-shrunk probabilities from the graded record (L8) — the book has no probabilities; this layer is why a call says p=0.6 instead of pretending certainty.
## Validation grade (May-26, vs official key)

- Deletions hit (visible): ['1102.TW', '1402.TW', '1504.TW', '2324.TW', '2474.TW', '2610.TW', '2633.TW']
- Deletions missed (visible): []
- Adds hit: ['6223.TWO'] / missed visible: []
- False calls: adds [], dels ['1101.TW', '1326.TW', '2207.TW']
- Ungradable below the named floor: []

Reading: the funnel recovers the graded engine result — visible deletions caught at the thresholds stage, the below-floor names are the declared breadth class, and the Aug-26 funnel shows the same structure ending at zero VISIBLE candidates with the blind band stated.