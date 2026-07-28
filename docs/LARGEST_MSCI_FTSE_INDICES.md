# MSCI & FTSE Russell Indices — Asia-Only and Asia-Containing, by Size

*Reference file, revised 2026-07-28 (Asia scope). Market-cap figures
APPROXIMATE (mid-2026, USD) — verify from current factsheets before
client use. Ranked by approximate index market cap within each group.*

## Group A — Asia-only indices

### MSCI country/regional (reviews Feb/May/Aug/Nov)

| Rank | Index | Approx. mkt cap | Notes |
|---|---|---|---|
| 1 | MSCI Japan | ~$4T | largest Asia country index |
| 2 | MSCI China | ~$2.5–3T | A (inclusion factor) + H + ADR, three venues |
| 3 | MSCI Taiwan | ~$2–2.5T | TSMC ~half; our graded market |
| 4 | MSCI India | ~$1.5–2T | fastest-growing EM weight |
| 5 | MSCI AC Asia ex Japan | ~$8T | the regional mandate composite |
| 6 | MSCI Korea | ~$1–1.5T | our graded market |
| 7 | MSCI EM Asia | ~$7T | EM composite's Asia block (~80% of EM) |
| 8 | MSCI HK / SG / TH / MY / ID / PH | <$1T each | smaller country slices |

### FTSE Russell Asia (GEIS Mar/Sep; co-brands quarterly)

| Rank | Index | Approx. mkt cap | Notes |
|---|---|---|---|
| 1 | FTSE Japan | ~$4T | GEIS slice |
| 2 | FTSE TWSE Taiwan 50 | ~$2T+ | ~US$70B+ tracked; graded market |
| 3 | FTSE China A50 | ~$1.5T | offshore A-share access; graded market |
| 4 | FTSE Asia Pacific ex Japan | ~$10T (incl. AU) | regional composite |
| 5 | FTSE China 50 (H) | ~$1T | HK-listed China |
| 6 | STI / KLCI / FTSE SET / FTSE Vietnam | <$0.5T each | exchange co-brands; Vietnam gains Secondary-EM entry Sep 2026 |

## Group B — global composites CONTAINING Asia (where Asia flow also lands)

| Index | Approx. mkt cap | Asia share | Why a desk cares |
|---|---|---|---|
| MSCI ACWI IMI / ACWI | ~$90T / ~$80T | ~12–14% | Japan 5.7%, Taiwan 3.4% of ACWI — every TW/JP change trades here too |
| MSCI World | ~$70–75T | ~7% (JP/HK/SG) | DM-only; Japan events hit World + EAFE |
| MSCI EM | ~$8–9T | ~80% | THE composite for Asia EM events; ~$1.8T benchmarked |
| MSCI EAFE | ~$17–18T | ~25% | classic international mandate; big Japan weight |
| FTSE Global All Cap / All-World | ~$85–90T / ~$75T | ~12% | Vanguard-complex trackers |
| FTSE Emerging | ~$8T | ~80% | +Vietnam from Sep 2026 |
| FTSE Developed | ~$70T | ~8% | Japan/HK/SG/KR (FTSE classes Korea DM) |

**AUM stacking — the reason Group B matters:** one Taiwan Standard-index
add is bought simultaneously by MSCI Taiwan trackers, AC Asia ex Japan,
EM Asia, EM, and ACWI trackers. The flow estimate must SUM tracking AUM
across every composite containing that market — the country-index AUM
alone understates the event severalfold. (EM-linked AUM dominates for
Asia EM names; ACWI/World dominate for Japan.)

## How composite (Asia + Western) index changes work — and how to predict

**MSCI: decided at the country level, inherited by composites.** MSCI
runs the GIMI methodology per market (the 85% coverage cutoffs we
model); EM, ACWI, EAFE are UNIONS of country indices. There is no
separate ACWI review — predict the country review correctly and the
composite changes follow automatically. Prediction approach: unchanged
(our country screens ARE the composite prediction); only the FLOW math
changes (AUM stacking above). Composite weight changes additionally
drift with cross-country performance and FX, but those are continuous,
not review events.

**FTSE: decided at the REGIONAL level — a real methodological
difference.** GEIS assigns large/mid/small size bands by ranking within
REGION (Asia Pacific), not within country. Predicting FTSE All-World
changes for a Taiwanese name therefore requires the Asia-Pacific
regional ranking, not a Taiwan-only ranking — a country-level model
mis-places names near band boundaries. Our rank-buffer engine handles
this structurally (it's the same mechanism at regional scale) but needs
a REGIONAL universe file. The co-brands (TW50, A50) remain
single-market and are unaffected.

**Execution implication:** composite events concentrate on the same
effective close as the country event (MSCI implements everything at the
month-end close), so the T-day print aggregates all layers — which is
exactly why measured T-multiples (16–38x for MSCI deletes) dwarf what
country-index AUM alone would predict.

*Sources: [MSCI ACWI factsheet](https://www.msci.com/www/index-factsheets/msci-acwi/05737588),
[MSCI indexes](https://www.msci.com/indexes),
[MSCI EM](https://www.msci.com/indexes/group/emerging-markets-indexes),
[FTSE China reviews](https://www.lseg.com/en/media-centre/press-releases/ftse-russell/2026/ftse-china-index-series-quarterly-review-q2-2026).*
