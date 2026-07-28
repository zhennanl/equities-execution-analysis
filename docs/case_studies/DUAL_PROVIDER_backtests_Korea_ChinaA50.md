# Dual-Provider Backtest — MSCI Korea (May 2026) & FTSE China A50 (June 2026)

*Session 7a. Fourth and fifth real-review backtests, extending the engine
to two NEW markets. Truth sets from official/primary sources.*

## Part 0 — What the two providers offer in Asia (the catalog)

**MSCI** (methodology: GIMI coverage cutoffs): country Standard / IMI /
Small Cap indices for Japan, China (plus China A Onshore and All Shares),
Korea, Taiwan, India, Hong Kong, Singapore, and the ASEAN markets;
regional composites (AC Asia ex Japan, AC Asia Pacific, EM Asia); and the
EM/ACWI composites where Asia changes surface. Reviews: Feb/Aug QIRs
(stricter add hurdle), May/Nov SAIRs.

**FTSE Russell** (methodology: rank buffers with reserve lists): GEIS
country slices (FTSE Japan/Korea/Taiwan/China etc., reviewed Mar/Sep for
Asia Pacific); and — more relevant to a PT desk — the **tradable
co-branded indices** with big ETF complexes: FTSE TWSE Taiwan 50
(~US$70B+ tracking), FTSE China A50 (the classic offshore A-share
access index; ~60% of global China-ETF AUM tracks a FTSE China index per
LSEG), FTSE China 50 (H-shares), Straits Times Index (with SGX), FTSE
Bursa Malaysia KLCI, FTSE SET (Thailand), FTSE Vietnam. Quarterly
reviews (Mar/Jun/Sep/Dec).

Engine mapping: MSCI-style = `predict_msci` (coverage + country-segment
rule); FTSE tradables = `predict_ftse` (rank buffers + pairing).

## Test 1 — MSCI Korea, May 2026 SAIR

**Truth set** ([Seoul Economic Daily](https://en.sedaily.com/finance/2026/05/13/msci-removes-hanjin-kal-hd-hyundai-marine-solution-sk)):
zero additions; three deletions — Hanjin KAL, HD Hyundai Marine
Solution, SK Biopharmaceuticals. Control: Rainbow Robotics was tipped
for addition in previews and NOT added.

**Result** (validator: clean; country rule at the Taiwan-calibrated 2%
buffer, untouched):

| Metric | Result |
|---|---|
| Deletions | **3/3, zero named false flags** |
| Additions | 0 actual; **1 false positive — Rainbow Robotics** |

**The deletion result is the headline:** the country-segment rule, with
a buffer calibrated on Taiwan events, transferred to a THIRD review and
a SECOND market at 3/3 with no false flags. Coverage-cutoff deletion
logic is now 14/14 across three events (TW May 7/7, TW Feb 4/4, KR May
3/3).

**The false positive is kept, not tuned away.** Rainbow passed the
full-cap hurdle AND the new min-FF-cap rule at my assumed 0.20 float.
The real block was reportedly float/liquidity — meaning MSCI's actual
FIF for Rainbow is likely below my guess, or the ATVR screen binds (I
assumed healthy liquidity). Diagnosis: **candidate-level float/liquidity
data quality is the binding input for add-side precision** — a desk with
real FIF data catches this; tweaking my reconstruction until the block
fires would be curve-fitting, so the miss stays in the report.

*(Engine improvement shipped anyway: `min_ffcap_frac_of_add` — the GIMI
book's requirement that FREE-FLOAT cap clear ~50% of the size cutoff —
now blocks big-cap/low-float names with an explicit "blocked add" watch
entry. Tested on a synthetic anchor-shareholder case; Rainbow at my
assumed float sits just above the block, which is exactly the point
about data quality.)*

## Test 2 — FTSE China A50, June 2026 quarterly

**Truth set** ([official LSEG press release](https://www.lseg.com/en/media-centre/press-releases/ftse-russell/2026/ftse-china-index-series-quarterly-review-q2-2026)):
IN — GigaDevice, Montage, Dongshan Precision, Victory Giant, Weichai;
OUT — CSCEC, Foshan Haitian, Haier Smart Home, Ping An Bank, Mindray.
Effective open of June 22.

**Result** (ranked on free-float-adjusted cap per A50 methodology —
disclosed; validator clean; .SS/.SZ eligibility on):

| Metric | Result |
|---|---|
| Additions | **5/5, zero false positives — every one tagged HIGH confidence (margins 30–63%)** |
| Deletions | 3/5 (CSCEC, Haitian, Ping An Bank; missed Haier & Mindray, false-flagged CRRC & CTG DutyFree) — **every deletion call self-labeled LOW (watch zone)** |
| Index size after pairing | exactly 50 ✓ |

The deletion pattern is the Taiwan-50 finding repeating on schedule:
crowded rank boundary (my FF-cap estimates put Haier/Mindray ~$16B just
above names I placed lower), ordering noise flips neighbors — and the
confidence tags did precisely what they were built for: the adds page
was actionable, the deletes page announced its own fragility.

## The five-backtest scoreboard

| Review | Engine | Adds | Deletes |
|---|---|---|---|
| MSCI Taiwan May SAIR | coverage | 1/1 | 7/7 (country rule) |
| MSCI Taiwan Feb QIR (OOS) | coverage | 1/1 | 4/4 + 7 early warnings |
| FTSE Taiwan 50 Jun | rank | 4/4, 0 false+ | 2/4, all LOW-tagged |
| MSCI Korea May SAIR | coverage | 0 actual, 1 false+ (data-quality diagnosis) | **3/3, 0 false flags** |
| FTSE China A50 Jun | rank | **5/5, 0 false+, all HIGH** | 3/5, all LOW-tagged |

Aggregate: **11/11 actual additions captured** across five reviews, two
providers, three markets; one add false positive, diagnosed as input
data quality (float), not rules. Coverage-based deletions **14/14**;
rank-based deletions ~50–60% with self-labeling confidence tags — the
mechanism split has now replicated out-of-market, twice.

## Honest boundaries

All universes reconstructed with ±30% approximate caps/floats and
imperfect membership lists (validator-passed but reconstruction-grade);
A50 rank basis is FF-cap per methodology but my FF estimates are coarse;
Korea ATVR assumed healthy for all names. The standing protocol fixes
(as-of data locally; Aug-12 pre-registration) apply. Rainbow's false
positive is the useful kind: it prices exactly what real FIF data is
worth to the add-side precision.


---

## Addendum (session 7b) — scorecard-driven improvements + full coverage map

### What the scorecard says to fix, and what was fixed now

| Scorecard signal | Binding constraint | Action |
|---|---|---|
| Add precision: 1 false+ (Rainbow) in 12 calls | candidate FLOAT/LIQUIDITY data quality (FIF, ATVR) | protocol: as-of pipeline w/ real float data (local script); min-FF-cap rule already shipped |
| Rank deletes ~50-60% | live-cap precision at crowded boundaries | **NOW: `p_survives_noise`** — margins converted to a per-name survival probability under the assumed cap error (normal approx of the Monte-Carlo finding); the delete page is now probabilistic, not binary |
| FTSE grading used the published reserve list | we graded against it but didn't emit one | **NOW: `reserve_list`** output — top-5 eligible non-members below the add boundary, per review |
| Buffer calibrated on 2 events | sample size | roadmap: calibration harness over the growing graded-backtest library |
| Caller picks SAIR/QIR + country rule | manual | roadmap: Agent-12 calendar drives review-type automatically |

### Exhaustive market-coverage map (verified July 2026)

**MSCI** ([classification framework](https://www.msci.com/indexes/index-resources/market-classification)):
**23 Developed + 24 Emerging** (= ACWI's 47) **+ ~31 Frontier/related**
plus Standalone markets — **~80 country markets** in total, each with
Standard/IMI/Small Cap variants, reviewed Feb/May/Aug/Nov. Asia in scope:
JP/HK/SG (DM); CN, KR, TW, IN, TH, MY, ID, PH (EM); VN, BD, LK, PK (FM/
related).

**FTSE Russell** ([country classification](https://www.lseg.com/en/media-centre/press-releases/ftse-russell/2026/ftse-russell-announces-results-march-2026-semi-annual-country-classification-review-equities-fixed-income)):
four tiers — **Developed 24→25** (Greece promoted Sep-2026), **Advanced
Emerging 10** (incl. Taiwan, Malaysia, Thailand), **Secondary Emerging
~13** (incl. China, India, Indonesia, Philippines; **+Vietnam from
Sep 21, 2026**), **Frontier ~24** — roughly 70+ equity markets in GEIS,
plus the tradable co-brands (TW50, A50, China 50, STI, KLCI, SET,
Vietnam Index).

### The actionable find: Vietnam, Sep 21 2026

FTSE promotes **Vietnam frontier → Secondary Emerging effective the
Sep-2026 semi-annual** (final eligible-securities list publishing
Aug 21). This is the largest scheduled Asia index event of H2-2026 —
a one-off reclassification flow (EM trackers buying an entire market)
rather than a routine review, hitting a ±7%-band, foreign-room-
constrained market our platform already models (HOSE bands, ATC
mechanics, no practical shorting). The screener/flow-sim pipeline
applies directly: universe = HOSE eligibles, flow = EM-tracker AUM x
assigned weights, execution = the index_flow strategy engine under
band and foreign-room constraints. For a PT desk interview in
July-2026, THIS is the event to bring a view on.
