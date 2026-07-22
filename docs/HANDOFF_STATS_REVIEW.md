# HANDOFF — Statistics Review Session (for a new chat)

*Written 2026-07-08. Purpose: start a fresh chat whose ONLY job is drilling
Bill's statistical knowledge for the GSET interview. This document is
self-contained — read it fully, then run the session per §7. If file access
is available, the deeper materials are listed in §6; if not, this document
alone is sufficient context.*

---

## 1. Who you're tutoring, and for what

**Candidate:** Bill (Zhennan) Luo. UNC Chapel Hill BSc Computer Science &
Statistics; HKU Master of Finance; CFA Level III passed. Trading internship
at Invesco (2024): built a Taiwan limit-up/limit-down study around index
rebalancing days — his formative project and his most probed interview
material. Since June 2026 he has built a three-page execution-analytics
platform (algo simulator, index-rebalancing event study, program-trading
desk) whose statistics stack he can DEMO live: OLS with HC1/Newey-West,
Friedman+Nemenyi algo wheel, Brown-Warner event inference, paired
tests/bootstrap, condition-adjusted rankings — all pinned by a 181-test
regression suite.

**The seat:** GSET (Goldman Sachs Electronic Trading) Quantitative Execution
Consultant / Execution Solutions. JD core: discuss execution performance
with clients/traders/compliance; client benchmarks and continuous
improvement; apply transaction cost models; evaluate liquidity options;
backtest/calibrate/optimize client flows; **propose and implement A/B
testing methodologies**; **develop statistical tools for strategy
performance**. Basic quals name parametric AND non-parametric tests,
regression, and time series explicitly.

**Interview state:** Round 1 done. **Feedback: round 2 will be heavily
statistics-focused.** Likely interviewer: senior APAC Execution Solutions
(Zhejiang economics → GS Hong Kong 2012–14 → Tokyo 2014–17 → present).
Expect statistics posed through DESK SCENARIOS, not textbook prompts, with
China/HK and Japan market color as the wrapper.

## 2. The statistical knowledge map — what gets TESTED

Priority order, with the specific items Bill must produce cold:

**A. Experiment design & inference (the center of gravity).**
- Paired vs unpaired design; why pairing adds power (the covariance term:
  Var(A−B) = Var A + Var B − 2Cov).
- The power calculation, with THE worked example: n = ((z_α/2+z_β)·σ_d/δ)²;
  σ_d=30bps, δ=2bps, 5%/80% → ((1.96+0.84)·30/2)² ≈ **1,760 paired orders**.
  Implication: wheels take quarters; "not separable at this n" is a finding.
- p-value and CI correct interpretations (and the two classic misreadings).
- Type I/II asymmetry on a desk; pre-registered α AND power target.
- Multiplicity, three layers: within-study (Friedman omnibus → Nemenyi CD =
  q_{α,k,∞}/√2 · √(k(k+1)/6n)); across studies (Benjamini-Hochberg FDR);
  sequential (no peeking; alpha-spending if interim looks are needed).
- Bootstrap: mechanics, and the two failure modes (serial dependence → block
  bootstrap / resample by day; extreme-value statistics).

**B. Regression as the transaction cost model.**
- Assumptions → violations in execution data → fixes (the chain he must
  recite): nonlinearity→√size; endogenous routing→controls/randomization;
  heteroskedasticity→HC1; time dependence→Newey-West; shared day
  shocks→**cluster by day** (the usually-binding one); collinearity→VIF.
- Omitted-variable bias as the WHEEL-DEFENSE formula: bias = β_Z·δ_ZX —
  sign it verbally (harder flow to algo B makes B look worse raw).
- Why R²≈0.05 is fine: precise coefficients at scale beat fit; chasing R²
  = overfitting noise.
- Attribution (small pre-specified OLS, defensible) vs prediction
  (regularization allowed) — different statistical ethics.
- Logistic for fill/limit-hazard models; interpret via odds ratios AND
  marginal probabilities.

**C. Time series.**
- Stationarity; ADF (null=unit root) + KPSS bracketing; spurious regression.
- AR(1): ρ(k)=φ^k; half-life = ln0.5/lnφ (φ=0.9 → ~6.6 periods).
- ACF/PACF signatures; returns ~white noise, squared returns ~long memory →
  GARCH(1,1): σ²_t = ω + αε²_{t−1} + βσ²_{t−1}; EWMA = IGARCH (λ=0.94).
- Variance-ratio test (Lo-MacKinlay, robust z*) — his platform's regime
  classifier; Ljung-Box for whiteness.

**D. Event-study inference (his rebalancing specialty).**
- Brown-Warner single-firm: var(AR_t) = s²(1 + 1/L + (Rm_t−R̄m)²/SSRm);
  CAR σ = √cumsum; bands anti-conservative on event days (BMP critique);
  clustered event dates break naive averaging.
- **The censoring point (his signature move):** Taiwan/China/Korea price
  limits CENSOR cost/return distributions — naive TCA averages over limit
  days are biased; model or flag censoring. A statistician's observation
  about the interviewer's exact geography.

**E. Distributions & non-parametrics.**
- Fat tails: medians/trimmed means, Wilcoxon/Mann-Whitney/Friedman, when
  t and rank tests disagree the tails are the finding.
- Quantile regression (pinball loss) for tail cost — clients fear P95.
- CLT failure modes: heavy tails (slow), infinite variance (never),
  dependence (effective n).

**F. Probability warm-ups (asked as screeners).**
- HH=6 vs HT=4 (retained-progress logic); √t dispersion (±1%/day, 100 days →
  σ=10%, E|move|≈8%); Bayes base-rate (90%-accurate flag, 2% base → 27%);
  gambler's ruin k/N + duration k(N−k); coupon collector n·H_n (die: 14.7);
  E[max two dice] = 161/36 via CDF; birthday 23; memorylessness.

## 3. The statistics used DAILY in the seat (frame drills this way)

| Daily workflow | The statistics inside it |
|---|---|
| Morning TCA outlier scan | robust location (medians), control-limit thinking, censoring flags on Asia limit days |
| Client wheel review | condition-adjusted comparison (regression w/ controls), both-ranks honesty, sample-size discipline |
| A/B readout meeting | pre-registered metric, power vs observed n, no-peeking discipline, BH across parallel studies |
| Fitting/refreshing the cost model | OLS + HC1/clustered SEs, diagnostics (BP/DW/JB), temporal OOS validation, predicted-vs-realized tracking |
| Algo/venue deep-dive | markout curves (share-weighted means at horizons), adverse-selection reads, paired designs |
| Event/market-structure notes | event-study inference, before/after with regime controls, stated hypotheses with dated predictions |
| Client "is this real?" calls | effect size + CI in bps, the 1,760 arithmetic, translating significance to money |

## 4. Bill's ready evidence (cite these when drilling answers)

- The **Invesco self-critique** (his best answer): +2% T+1 finding was raw
  means, event-clustered, no market adjustment — he now knows the fixes
  (clustered/bootstrap-by-date errors, market-model adjustment, locked vs
  retreat split) and built them into his platform. Drill until he delivers
  it without defensiveness.
- Platform stats he can demo: cost-model regression (HC1/HAC, diagnostics),
  A/B-with-controls, condition-adjusted ranking (raw rank last → adjusted
  first on confounded flow, pinned by test), wheel CD, CAR bands, IS
  attribution reconciling ±0.1bp, 181 tests.

## 5. Known gaps to probe hardest

- Fluency under pressure: derivations aloud (power formula, Nemenyi CD,
  Brown-Warner variance) — he knows them written, drill spoken.
- Clustered vs HAC vs HC1: WHICH binds WHEN — he defaults to "robust SEs"
  generically; push for the day-clustering answer.
- Sequential testing/alpha-spending: thinnest area; at least the concepts
  and names (O'Brien-Fleming) at recognition level.
- Time-series depth beyond AR(1)/GARCH basics (cointegration, DM test) —
  recognition level is sufficient; don't over-invest.

## 6. Where the full materials live (if folder access granted)

`Downloads/execution_analytics/docs/`: `GSET_Prep_Roadmap.docx/.pdf` (v2,
statistics-first — §3 is the 10-question spoken bank), `TECH_QUESTION_BANK
.md/.html` (96 tiered Q&A; Stats categories are the drill set),
`QUANT_CONSULTANT_QUIZ.md/.html` (31 desk scenarios), `INTERVIEWER_PREP_BANK
.md/.html` (her profile + market-wrapped questions), `AI_AT_GS_PREP.md/.html`,
`BEHAVIORAL_QUESTION_BANK.md/.html`, `QUESTIONS_FOR_HER.md`. Interactive
.html banks: filter Tier 1/2, self-score, "review again" pile = the study
list. Platform code (agents/, tests/) backs every claim in §4.

## 7. How to run the review session (suggested)

1. **Cold-start audit (15 min):** fire §2-A questions unseen; score fluency
   1–3; build the weak-list.
2. **Drill loop:** for each weak item — he answers aloud → you give the
   model answer from §2 → he re-answers in his own words → schedule a
   re-test later in the session (spaced repetition inside one sitting).
3. **Scenario wrappers:** re-ask every formula item INSIDE a desk scenario
   ("client wants the wheel verdict after 3 weeks — talk me through it") —
   round 2 will not ask anything naked.
4. **Derivations aloud:** power formula, Nemenyi CD, Brown-Warner variance,
   OVB sign — spoken, timed, twice each.
5. **The two set-pieces:** the Invesco self-critique (90s) and the censoring
   point (30s) — rehearse verbatim until natural.
6. **Mock close (20 min):** 6 rapid-fire mixed questions, one long scenario,
   one probability warm-up. Score, list residual weak items for a final pass.
