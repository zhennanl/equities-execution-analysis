# GSET Technical Question Bank — Statistics, Programming, Math (July 2026)

*96 questions with standard answers and practical-application
notes. Source of truth: `docs/quiz_src/tech_questions.py` — edit there and re-run
`build_bank.py` to regenerate this file and `TECH_QUESTION_BANK.html` together.*

**Categories:** Stats: Inference (17) · Stats: Regression (13) · Stats: Time Series (9) · Programming: Python (13) · Programming: SQL (6) · Programming: kdb+/q (2) · Programming: Algorithms (7) · Math: Probability (12) · Math: LinAlg (6) · Math: Optimization (5) · Math: Stochastic (6)

**Tiers:** Tier 1 · Fundamental (39) · Tier 2 · Role-critical (39) · Tier 3 · Good-to-know (18) — study Tier 1 to fluency first, Tier 2 is where the interview lives, Tier 3 differentiates.

## Stats: Inference

**Q1. What exactly is a p-value — and give the two most common misreadings.**  
*[Tier 1 · Fundamental]*

*Standard answer:* The probability, computed under the null hypothesis, of observing a test statistic at least as extreme as the one you got. Misreadings: (1) 'the probability the null is true' — it is not; that's a posterior and needs a prior; (2) 'the probability the result is due to chance' — same confusion. A small p says the data are unlikely IF the null holds; it says nothing about effect size, importance, or replicability.

*Practical application:* Saying this cleanly is a screening question; misstating it ends quant interviews early.

**Q2. Interpret a 95% confidence interval correctly.**  
*[Tier 1 · Fundamental]*

*Standard answer:* A procedure statement: if you repeated the experiment many times and built the interval the same way each time, 95% of those intervals would contain the true parameter. It is NOT 'the parameter is in this interval with 95% probability' — the parameter is fixed, the interval is random. Practically: width tracks precision (n and dispersion), and any value inside the interval would not be rejected at 5%.

*Practical application:* CIs on slippage effects are how you report A/B results without overclaiming — the width IS the message at small n.

**Q3. Type I vs Type II error, size vs power — and the trading-desk asymmetry between them.**  
*[Tier 1 · Fundamental]*

*Standard answer:* Type I: rejecting a true null (false positive), rate = size α. Type II: failing to reject a false null (missed effect), rate β; power = 1−β. On a desk the asymmetry flips by context: shipping an algo change on a false positive costs real client money and credibility (Type I expensive), while missing a genuine 1 bp improvement across billions of notional is also expensive (Type II). Hence pre-registered α AND a power target — one without the other is theater.

*Practical application:* Every A/B protocol states both; the power target is what determines the test horizon.

**Q4. Standard deviation vs standard error — the distinction and the formula.**  
*[Tier 1 · Fundamental]*

*Standard answer:* SD describes dispersion of the DATA; SE describes dispersion of an ESTIMATOR across hypothetical repeated samples. For the sample mean, SE = σ/√n: quadrupling the data halves the SE but leaves SD unchanged. Confusing them either overstates precision (quoting SD-scale uncertainty for a mean) or understates spread.

*Practical application:* Client packs must label which one a whisker shows; mixing them up in a chart is a credibility hit.

**Q5. Law of Large Numbers vs Central Limit Theorem — what does each actually say?**  
*[Tier 1 · Fundamental]*

*Standard answer:* LLN: the sample mean CONVERGES to the true mean as n grows (a statement about the destination). CLT: the FLUCTUATIONS of the sample mean around the truth, scaled by √n, converge to a normal distribution (a statement about the shape of the error en route). LLN justifies 'more data → right answer'; CLT justifies the ±1.96·SE machinery.

*Practical application:* The one-liner: LLN says you get there, CLT says how the wobble is distributed on the way.

**Q6. Independence vs zero correlation — which implies which, and the standard counterexample.**  
*[Tier 1 · Fundamental]*

*Standard answer:* Independence implies zero correlation; the converse fails. Counterexample: X standard normal, Y = X². Cov(X,Y) = E[X³] = 0, yet Y is a deterministic function of X. Correlation only measures LINEAR association — nonlinear dependence is invisible to it.

*Practical application:* Why 'uncorrelated with market returns' never suffices as an independence claim in a validation memo.

**Q7. One-sided vs two-sided tests: when is one-sided legitimate, and what's the abuse?**  
*[Tier 1 · Fundamental]*

*Standard answer:* One-sided is legitimate when the hypothesis is directional BEFORE the data (a cost-reduction change can only help or do nothing, by design) — it buys power in the pre-declared direction. The abuse: choosing the side after seeing the data, which doubles the effective false-positive rate. Declare sidedness in the protocol, or default to two-sided.

*Practical application:* A/B protocols state sidedness up front for exactly this reason.

**Q8. Effect size vs statistical significance — why can each exist without the other?**  
*[Tier 1 · Fundamental]*

*Standard answer:* Significance is effect divided by noise-of-estimate: huge n makes trivial effects 'significant' (0.1 bps with millions of orders); small n leaves large real effects insignificant. Decisions need both: the magnitude (is 2 bps worth engineering effort?) and the precision (is the CI narrow enough to act?). P-values alone conflate the two.

*Practical application:* The desk translation: 'statistically detectable' and 'economically material' are separate columns in the readout.

**Q9. Paired vs unpaired comparisons — why does pairing add power?**  
*[Tier 1 · Fundamental]*

*Standard answer:* Pairing differences out shared noise: comparing algos on the SAME day removes the day effect, so the variance of the paired difference is Var(A)+Var(B)−2Cov(A,B) — much smaller when both arms co-move with the market. Unpaired tests carry the full common variance and need far more data for the same power.

*Practical application:* Why every algo comparison here is same-day blocked; the covariance term is where the power comes from.

**Q10. When does the Central Limit Theorem fail you in practice?**  
*[Tier 2 · Role-critical]*

*Standard answer:* Slow convergence with heavy tails (finite but large kurtosis — execution costs are exactly this: the mean's sampling distribution needs far more than the folklore n=30); infinite variance (stable/power-law tails — CLT doesn't apply at all, normalized sums go to stable laws); dependence (serially correlated data — effective n is much smaller than nominal n; the CLT needs mixing conditions); and non-identical distributions with dominating terms (one giant order dominating a month's mean).

*Practical application:* The reason cost analyses use medians, trimmed means, bootstrap, and clustered errors rather than naive t-tests.

**Q11. Bayes' rule applied: a toxicity flag fires on 90% of truly toxic order flow, false-fires on 5% of benign flow, and 2% of flow is toxic. A flag just fired — probability the flow is toxic?**  
*[Tier 2 · Role-critical]*

*Standard answer:* P(toxic|flag) = 0.9×0.02 / (0.9×0.02 + 0.05×0.98) = 0.018/0.067 ≈ 27%. Despite a ' 90% accurate' detector, base rates dominate: most flags are false because toxic flow is rare. Design consequence: rare-event detectors need very low false-positive rates or corroborating signals before anyone acts on them.

*Practical application:* Exactly the arithmetic behind alert-blotter design — why alert thresholds are set to keep the false-alarm burden tolerable.

**Q12. Bootstrap: how it works, and the two situations where the vanilla version is invalid.**  
*[Tier 2 · Role-critical]*

*Standard answer:* Resample the data with replacement, recompute the statistic each time, and use the resulting distribution for SEs/CIs — it substitutes computation for distributional assumptions. Invalid (1) under serial dependence: iid resampling destroys the dependence structure — use block bootstrap (resample contiguous blocks) or resample at the independent-unit level (days, orders); (2) for statistics driven by extremes (max, tail quantiles with small n) where bootstrap distributions are inconsistent. Also biased when the statistic isn't smooth in the data.

*Practical application:* Bootstrap-by-day is the workhorse for slippage CIs; forgetting the 'by-day' is the classic error.

**Q13. What is a permutation test and when would you prefer it to a t-test?**  
*[Tier 2 · Role-critical]*

*Standard answer:* Under the null of no difference, group labels are exchangeable — so shuffle labels many times, recompute the statistic, and the empirical distribution of shuffled statistics is the exact null distribution. Prefer it when distributional assumptions are dubious (heavy tails, small n) and the design justifies exchangeability (randomized A/B arms). Caveats: exchangeability fails under serial dependence or stratified designs unless you permute within strata/blocks.

*Practical application:* Within-day label permutation is a clean significance check for wheel comparisons on modest samples.

**Q14. What is maximum likelihood estimation, and when does it coincide with OLS?**  
*[Tier 2 · Role-critical]*

*Standard answer:* Choose parameters maximizing the probability (density) of the observed data. Under the linear model with iid GAUSSIAN errors, maximizing likelihood is minimizing the sum of squared residuals — MLE = OLS exactly. With non-normal errors they part ways: MLE under Laplace errors gives least absolute deviations (median regression). MLE's general appeal: asymptotic efficiency and a unified recipe (logistic, GARCH, hazard models are all MLE).

*Practical application:* Logistic fill models and GARCH vol are MLE in practice — knowing the umbrella concept ties the toolkit together.

**Q15. Correlation vs causation in execution data: give the standard confounder story and the three escape routes.**  
*[Tier 2 · Role-critical]*

*Standard answer:* Orders routed to the dark pool show better prices — because the ROUTER sends easy flow there (selection on conditions), not because the venue improves fills. Escapes: (1) randomization (A/B) — gold standard; (2) conditioning on the confounders (regression with controls, matching) — only as good as the observed controls; (3) natural experiments/instruments — rule changes, index cutoffs — rare but powerful. Rank them in that order in any proposal.

*Practical application:* Every venue and algo claim faces this challenge; leading with the design answer is what marks a professional.

**Q16. How do you handle missing data in a TCA panel without biasing results?**  
*[Tier 2 · Role-critical]*

*Standard answer:* First diagnose the mechanism: missing completely at random (drop rows, lose only power), missing at random given observables (model or weight on observables), or missing NOT at random — the dangerous case: fills missing BECAUSE they were bad (a venue's dropped messages on stressed prints) biases everything. Rules: never silently drop; report coverage rates; test whether missingness correlates with conditions; sensitivity-check conclusions under worst-case imputation.

*Practical application:* Feed gaps and vendor data holes are routine; 'coverage rate by venue' belongs in every data-quality appendix.

**Q17. The delta method in one line — and a TCA use.**  
*[Tier 3 · Good-to-know]*

*Standard answer:* A smooth function of an asymptotically normal estimator is asymptotically normal with variance g'(θ)²·Var(θ̂) — first-order Taylor propagation of uncertainty. Use: you estimate mean cost per share and mean shares per order separately; the SE of their PRODUCT (cost per order) comes via the delta method (or bootstrap the ratio directly).

*Practical application:* Quick error bars on derived quantities without re-deriving estimators.

## Stats: Regression

**Q18. State the OLS assumptions and, for each, what breaks in execution-cost data.**  
*[Tier 1 · Fundamental]*

*Standard answer:* Linearity in parameters (costs are concave in size — fixed by transforming to √size); exogeneity E[ε|X]=0 (broken by endogenous strategy choice: hard orders routed to certain algos); homoskedasticity (broken: variance grows with size/volatility → robust SEs); no autocorrelation (broken across time → HAC/clustered errors); no perfect multicollinearity (participation and size are near-collinear in some flows); and for exact small-sample t-tests, normal errors (fat tails → rely on asymptotics or bootstrap). Consistency of coefficients only needs the first two; the rest attack the standard errors.

*Practical application:* The interview follow-up chain is predictable: assumption → violation → fix. Have this table memorized.

**Q19. Multicollinearity: what it does and doesn't do, and how you detect/handle it.**  
*[Tier 1 · Fundamental]*

*Standard answer:* It does NOT bias coefficients or hurt prediction; it inflates the variance of individual coefficients — you can't attribute the effect between near-duplicate regressors (huge SEs, unstable signs), though their joint effect is fine. Detect: VIFs, condition number, coefficient instability across subsamples. Handle: drop or combine near-duplicates, orthogonalize (residualize one on the other), or accept joint interpretation. In cost models, participation and %ADV are the usual near-collinear pair.

*Practical application:* Explains why a cost model's individual t-stats can be weak while its F-test and predictions are strong.

**Q20. R² vs adjusted R² — definitions and why adjusted can fall when you add a regressor.**  
*[Tier 1 · Fundamental]*

*Standard answer:* R² = 1 − SSR/SST, the in-sample variance share explained; it NEVER decreases when regressors are added (fitting noise counts). Adjusted R² penalizes by degrees of freedom: 1 − (1−R²)(n−1)/(n−k−1); it falls when a new regressor's contribution is weaker than chance. Neither is an out-of-sample statement — that requires validation splits.

*Practical application:* A cost model gaining ten features and 0.002 adjusted-R² is telling you to stop.

**Q21. The dummy-variable trap — what breaks and what's the convention?**  
*[Tier 1 · Fundamental]*

*Standard answer:* Including a dummy for EVERY category plus an intercept makes the dummies sum to the intercept column — perfect collinearity, X'X singular. Convention: k categories → k−1 dummies; the omitted category is the baseline, and each coefficient reads 'versus baseline'. Alternative: drop the intercept and keep all k, coefficients become per-category means — but interactions and comparisons get clumsier.

*Practical application:* Algo/venue dummies in cost models; also why the A/B-with-controls has an explicit baseline strategy.

**Q22. How do you read residual plots? Name the three classic patterns and their diagnoses.**  
*[Tier 1 · Fundamental]*

*Standard answer:* Residuals vs fitted: (1) funnel shape — variance grows with level: heteroskedasticity → robust SEs or transform; (2) curvature — the mean is misspecified: missing nonlinearity (add √size, interactions); (3) trends over TIME order — serial correlation or regime drift → HAC errors, time controls, or split samples. Clean models have structureless residuals; structure in residuals is unmodeled signal.

*Practical application:* The first thing a reviewer looks at in any fitted cost model — before the coefficient table.

**Q23. Omitted variable bias: give the formula's logic and an execution example.**  
*[Tier 2 · Role-critical]*

*Standard answer:* If the true model includes Z but you omit it, the coefficient on X absorbs β_Z times the regression of Z on X — bias = β_Z·δ_ZX. Sign logic: bias is positive when the omitted variable both raises cost AND correlates positively with X. Example: regress cost on a strategy dummy omitting order size; if strategy B receives systematically larger orders (δ>0) and size raises cost (β>0), B looks worse than it is — the ranking-defense problem in one formula.

*Practical application:* This formula IS the wheel-defense argument; being able to sign the bias verbally is the skill.

**Q24. Interpret a logistic regression coefficient, and give a fill-probability example.**  
*[Tier 2 · Role-critical]*

*Standard answer:* A coefficient β is the change in log-odds per unit of X; e^β is the odds ratio. Example: modeling P(passive child order fills within 1 min) on queue position, spread, volatility — β on 'spread (ticks)' = −0.7 means each extra tick of spread multiplies fill odds by e^−0.7 ≈ 0.5. Marginal effect on probability depends on the baseline level (∂p/∂x = β·p·(1−p)), so quote probabilities at representative points, not just odds.

*Practical application:* Fill-probability and limit-lock (hazard) models are logistic at heart; interpreting in probabilities is the client-facing skill.

**Q25. Why can a regression with R² = 0.05 still be extremely valuable in execution analytics?**  
*[Tier 2 · Role-critical]*

*Standard answer:* Because most cost variance is genuinely idiosyncratic noise no model should explain — the systematic component is small but economically huge at scale. A 2 bps expected-cost difference on billions of notional matters even if order-level R² is tiny; what you need is precise COEFFICIENTS (large n gives small SEs despite low R²), not high fit. Chasing R² in this domain usually means overfitting noise or leaking outcome information.

*Practical application:* Pre-empts the 'your model barely fits' challenge — the answer is effect precision, not variance explained.

**Q26. Interaction terms: interpret cost ~ size + urgent + size×urgent.**  
*[Tier 2 · Role-critical]*

*Standard answer:* The size coefficient is the slope for NON-urgent orders; size + interaction is the slope for urgent ones — the interaction measures how urgency AMPLIFIES the size effect (impact steepens when demanding immediacy). Main effects change meaning once interactions enter (they're slopes at the other variable's zero/baseline), so center variables or interpret at representative values.

*Practical application:* Client questions are usually interactions: 'does size hurt ME more?' is size×client-profile.

**Q27. How do you validate a cost model out-of-sample without fooling yourself?**  
*[Tier 2 · Role-critical]*

*Standard answer:* Temporal splits only — train on months 1–9, test on 10–12; random row splits leak regime information both ways in time-ordered data. Walk-forward re-fitting mimics production. Metrics: out-of-sample bias (mean predicted-minus-realized) and calibration by decile, not just RMSE. And freeze the spec before looking at test data — a spec tuned on the test window is in-sample with extra steps.

*Practical application:* 'Backtest, calibrate, optimize' done honestly is exactly this discipline.

**Q28. When would you reach for ridge or lasso in a cost model, and what do you give up?**  
*[Tier 3 · Good-to-know]*

*Standard answer:* When regressors are many and collinear (venue dummies × time buckets × features) and the goal is prediction stability: ridge shrinks coefficients (handles collinearity, keeps all features), lasso zeroes some (feature selection). You give up unbiasedness for variance reduction (bias-variance trade), and naive inference — penalized SEs/p-values aren't standard, so for DEFENSIBLE attribution (client/compliance) prefer a small pre-specified OLS with robust errors; use regularization for forecasting engines, not for testimony.

*Practical application:* Sharp distinction to make in interview: prediction models vs attribution models have different statistical ethics.

**Q29. Instrumental variables in one minute: the two conditions and why they're hard in execution work.**  
*[Tier 3 · Good-to-know]*

*Standard answer:* An instrument must be (1) relevant — correlated with the endogenous regressor — and (2) excluded — affecting the outcome ONLY through it. Execution example: using an index-inclusion rank cutoff as an instrument for passive flow (the RDD literature). Hard in practice because most desk variables that move routing also touch cost directly, violating exclusion; weak instruments additionally destroy inference.

*Practical application:* Good-to-know for reading the academic literature the desk cites (Chang-Hong-Liskovich's design is exactly this).

**Q30. Quantile regression: the loss function and the execution question it answers.**  
*[Tier 3 · Good-to-know]*

*Standard answer:* Minimize the pinball loss Σρ_τ(y−Xβ) where ρ_τ weights positive residuals by τ and negatives by 1−τ; τ=0.5 gives median regression, τ=0.95 the conditional 95th percentile. It answers 'what drives TAIL cost' — the conditions under which the worst 5% of orders get expensive — which mean regression averages away.

*Practical application:* Clients fear the tail; a P95-cost model is a differentiating deliverable.

## Stats: Time Series

**Q31. Stationarity: define it, test it, and explain spurious regression.**  
*[Tier 1 · Fundamental]*

*Standard answer:* Weak stationarity: constant mean, variance, and autocovariances depending only on lag. Test: ADF (null = unit root; rejection ⇒ stationary), KPSS as the reverse-null complement — using both brackets the answer. Spurious regression: two independent unit-root series regressed on each other yield high R² and 'significant' t-stats far too often, because standard asymptotics fail — the residuals are nonstationary. Fix: difference to returns, or model cointegration explicitly if a long-run relation is the hypothesis.

*Practical application:* Why execution analytics regresses returns/costs, never price levels — and a favorite screening question.

**Q32. For an AR(1) x_t = φx_{t−1} + ε, give the autocorrelation function, stationarity condition, and half-life of a shock.**  
*[Tier 1 · Fundamental]*

*Standard answer:* ACF: ρ(k) = φ^k (geometric decay). Stationary iff |φ| < 1. Half-life: k* = ln(0.5)/ln(φ) — e.g., φ = 0.9 gives ≈ 6.6 periods. Intuition worth saying: near-unit-root series (φ→1) have shocks that persist ~forever, which is why high-persistence regressors need care and why 'mean reversion with φ=0.98 daily' is a slow trade.

*Practical application:* Half-life arithmetic prices how long a liquidity/volatility regime shift should affect strategy settings.

**Q33. ACF vs PACF: what signatures identify AR vs MA processes?**  
*[Tier 1 · Fundamental]*

*Standard answer:* AR(p): ACF decays gradually (geometric/oscillating), PACF cuts off after lag p. MA(q): ACF cuts off after lag q, PACF decays gradually. Mixed ARMA: both decay. In practice on financial returns: raw returns show near-zero ACF (efficient-markets-ish) while squared returns show long, slow ACF decay — the signature of volatility clustering, pointing to GARCH-type structure rather than ARMA on returns.

*Practical application:* The two-plot diagnosis is a standard 'show me you've actually done time series' question.

**Q34. Define white noise, and state what a random walk with drift implies for mean and variance over time.**  
*[Tier 1 · Fundamental]*

*Standard answer:* White noise: zero mean, constant variance, zero autocorrelation at all lags (iid normal is 'strict' white noise). Random walk with drift x_t = μ + x_{t−1} + ε: mean grows linearly (x_0 + μt), variance grows linearly (tσ²) — nonstationary in both, so sample statistics don't converge and standard inference fails. Differencing recovers stationary increments.

*Practical application:* The null model for prices; every 'signal' must beat it.

**Q35. GARCH(1,1) in one minute: the equation, what each term captures, and why desks care.**  
*[Tier 2 · Role-critical]*

*Standard answer:* σ²_t = ω + α·ε²_{t−1} + β·σ²_{t−1}: α is the reaction to yesterday's shock (news), β the persistence of the volatility level, α+β the total persistence (typically 0.95–0.99 for equities — vol regimes decay slowly); unconditional variance ω/(1−α−β). Desks care because expected cost scales with σ: a GARCH-style vol forecast makes pre-trade estimates condition on the current regime rather than a long-run average.

*Practical application:* The one vol model worth reciting; also explains why yesterday's chaos should raise today's cost estimates.

**Q36. Ljung-Box test — what does it test and where does it fit in a TCA workflow?**  
*[Tier 2 · Role-critical]*

*Standard answer:* Joint null that autocorrelations up to lag m are all zero: Q = n(n+2)Σρ̂²_k/(n−k) ~ χ²_m. Uses: on model residuals (did the cost model leave serial structure → need HAC or a time regressor), and on return series when classifying regimes (rejecting whiteness supports trending/reverting structure worth exploiting or defending against in scheduling).

*Practical application:* The formal backstop behind 'is there autocorrelation here or am I seeing things'.

**Q37. EWMA volatility (RiskMetrics): the recursion, the λ, and its relation to GARCH.**  
*[Tier 2 · Role-critical]*

*Standard answer:* σ²_t = λσ²_{t−1} + (1−λ)r²_{t−1}, classically λ=0.94 daily — an exponentially weighted average of squared returns, trivially recursive and O(1) to update. It is GARCH(1,1) with α+β=1 and ω=0 (integrated GARCH): no mean reversion, so shocks never fully decay and there's no unconditional variance. Fine for short-horizon condition monitoring; use proper GARCH when horizon matters.

*Practical application:* The pragmatic live-blotter vol estimate — cheap, causal, and good enough for regime flags.

**Q38. Cointegration in one minute: definition, test, and the pairs-trading connection.**  
*[Tier 3 · Good-to-know]*

*Standard answer:* Two unit-root series are cointegrated when some linear combination is stationary — they wander, but tethered. Engle-Granger: regress one on the other, ADF-test the residual (with adjusted critical values). Connection: the stationary spread mean-reverts, which is the statistical license for pairs trading — and the same machinery flags when an ETF and its basket, or dual listings, drift beyond noise.

*Practical application:* Good-to-know for cross-listing and ETF-arb conversations; not daily TCA fare.

**Q39. Comparing forecasts: why RMSE and MAE can disagree, and what the Diebold-Mariano test adds.**  
*[Tier 3 · Good-to-know]*

*Standard answer:* RMSE squares errors — it punishes large misses disproportionately; MAE treats all misses linearly. A forecaster with rare big errors wins MAE and loses RMSE: choose the loss that matches the economic cost of errors. Diebold-Mariano tests whether two forecasts' loss differentials differ SIGNIFICANTLY, HAC-adjusted for serial correlation in the loss series — the difference between 'model A looks better' and 'model A is better'.

*Practical application:* Volume-forecast bake-offs (which curve feeds the scheduler) should end with a DM test, not a bar chart.

## Programming: Python

**Q40. Floating point: why does 0.1 + 0.2 != 0.3, and when does it actually matter on a desk?**  
*[Tier 1 · Fundamental]*

*Standard answer:* Binary floating point can't represent most decimal fractions exactly; errors of ~1e-16 accumulate through arithmetic. Usually harmless for statistics, but it matters for: equality comparisons (use tolerances, never == on floats), money/P&L accounting that must tie to the penny (use integers in minor units or Decimal), tick-price arithmetic (round to tick via integers), and summation of many small terms (pairwise/Kahan summation or math.fsum).

*Practical application:* Reconciliation reports that must tie exactly cannot be built on float equality.

**Q41. Core container complexities: list, dict, set — lookup, insert, membership. When does a list beat a dict?**  
*[Tier 1 · Fundamental]*

*Standard answer:* dict/set: O(1) average membership, insert, lookup (hashing). list: O(1) append and index access, O(n) membership and arbitrary insert. A list wins when order matters, when you iterate everything anyway, or when n is tiny (constant factors beat asymptotics). The classic slow-code diagnosis: 'if x in some_list' inside a loop — O(n²) that a set makes O(n).

*Practical application:* The single most common pandas-adjacent performance bug in analyst code.

**Q42. The mutable default argument gotcha — what happens and why?**  
*[Tier 1 · Fundamental]*

*Standard answer:* def f(x, acc=[]) evaluates the default ONCE at definition; every call without acc shares the SAME list, so state leaks across calls — the function 'remembers'. Idiom: default to None, create inside: acc = [] if acc is None else acc. Same trap with dicts and any mutable default.

*Practical application:* A staple screening question, and a real bug generator in shared analytics utilities.

**Q43. 'is' vs '==', and shallow vs deep copy — the two identity confusions.**  
*[Tier 1 · Fundamental]*

*Standard answer:* '==' compares values; 'is' compares object identity (same memory) — use 'is' only for None/sentinels (small-int caching makes 'is' on numbers a trap). copy.copy duplicates the outer container but SHARES nested objects; deepcopy recurses. A shallow-copied config whose nested dict you mutate changes the 'original' — the classic action-at-a-distance bug.

*Practical application:* Parameter-set mutation bugs in backtest sweeps almost always trace to one of these.

**Q44. pandas merge_asof: what it does and why it's THE TCA join.**  
*[Tier 2 · Role-critical]*

*Standard answer:* For each row of the left frame (trades), attach the most recent right-frame row (quotes) at or before its timestamp — direction='backward' by default, with by='sym' for per-symbol alignment and tolerance to bound staleness. It's the pandas equivalent of kdb's aj, and it's how you attach prevailing quotes to fills for effective-spread and midpoint benchmarks without an O(n²) interval join. Both inputs must be sorted by the join key.

*Practical application:* Effective spread, quote-at-order-arrival, NBBO-at-fill: all one merge_asof.

**Q45. groupby().apply() vs .transform() vs .agg() — pick the right one and explain the performance trap.**  
*[Tier 2 · Role-critical]*

*Standard answer:* agg: many-rows→one-value per group (mean slippage per algo). transform: many→many, result aligned to original index (demean costs within day — subtract group mean while keeping row shape). apply: arbitrary function, most flexible, slowest — it's a Python loop over groups and should be last resort. The trap: apply for things agg/transform express natively can be 10–100x slower and hides vectorization; also groupby(...).apply with side effects breaks on empty groups.

*Practical application:* Within-day demeaning via transform is exactly how paired/blocked cost comparisons get built.

**Q46. You must process 200GB of tick data on a 32GB machine in Python. Strategy?**  
*[Tier 2 · Role-critical]*

*Standard answer:* Don't load it: read columnar (parquet) with column pruning and predicate pushdown; chunk by natural partition (date/symbol) and aggregate incrementally; downcast dtypes (float32 where tolerable, categoricals for symbols — often 5-10x memory); use streaming/online algorithms for running stats (Welford for variance) so state stays O(1); and push heavy grouping to a tool built for it (duckdb/polars on parquet, or the tick store itself — kdb) rather than pandas. Ensure per-chunk results compose exactly (sums and counts, not averages of averages).

*Practical application:* Tick-data reality on any desk; 'averages of averages' is the correctness trap they'll probe.

**Q47. Name three datetime/timezone pitfalls that corrupt execution analytics.**  
*[Tier 2 · Role-critical]*

*Standard answer:* (1) Mixing naive and aware timestamps — pandas silently misaligns or raises depending on operation; standardize to UTC internally, convert at the display edge. (2) Exchange-local session logic done in UTC — Tokyo lunch or US DST transitions shift bar boundaries; bucket in exchange time. (3) Comparing feeds with different clock conventions (exchange timestamp vs receipt time) — a merge_asof against the wrong clock quietly attaches wrong quotes. Honorable mention: nanosecond truncation when round-tripping through formats.

*Practical application:* Cross-market TCA dies quietly on these; UTC-in, local-at-the-edge is the discipline.

**Q48. Why are seeds, versions, and deterministic tests non-negotiable for desk analytics?**  
*[Tier 2 · Role-critical]*

*Standard answer:* Because numbers shown to clients/compliance must reproduce: a bootstrap CI that changes on re-run is indefensible. Discipline: fixed RNG seeds passed explicitly (not global state), pinned dependency versions, pure functions over shared mutable state, and regression tests that pin known outputs — so a library upgrade that shifts a number is CAUGHT, not discovered by a client. Determinism is also what makes code review of analytics meaningful.

*Practical application:* Best-ex evidence is reproducibility; my platform pins ~180 output anchors for exactly this reason.

**Q49. Pandas index alignment: what happens when you add two Series with different indexes?**  
*[Tier 2 · Role-critical]*

*Standard answer:* Pandas aligns on the index UNION and fills non-overlapping labels with NaN — it will not error. Adding two per-symbol series with mismatched symbols silently produces NaNs (and skipna aggregation then hides them). Discipline: align explicitly (reindex, join='inner'), assert expected shapes, and treat NaN counts as a checked invariant rather than a surprise.

*Practical application:* Cross-venue metric joins produce silent NaN rot exactly this way; assert-your-alignment is desk hygiene.

**Q50. NaN semantics: three behaviors that corrupt analytics if forgotten.**  
*[Tier 2 · Role-critical]*

*Standard answer:* (1) NaN != NaN — equality tests and drop_duplicates on float keys misbehave; use isna(). (2) Aggregations default skipna=True — a mean over 10% coverage looks confident; track counts alongside. (3) NaN is float — an int column with one NaN silently upcasts, breaking joins on 'integer' ids (use nullable Int64). Groupby historically dropping NaN group keys is the fourth horseman (dropna=False).

*Practical application:* Coverage-weighted reporting exists because of behavior (2); id-join breakage from (3) is a recurring incident.

**Q51. Generators vs lists: memory semantics, and the one-shot trap.**  
*[Tier 2 · Role-critical]*

*Standard answer:* A list materializes all elements; a generator yields lazily — O(1) memory for streaming transforms (reading a 50GB fill file line by line). Traps: generators EXHAUST (second iteration yields nothing — silent empty results); no len(); and holding one open keeps file handles alive. Rule: generate through pipelines, materialize at aggregation boundaries.

*Practical application:* Tick-file ETL is generator country; the exhausted-generator empty-result bug is a rite of passage.

**Q52. The GIL: what it prevents, and the three standard escapes for heavy analytics.**  
*[Tier 3 · Good-to-know]*

*Standard answer:* CPython's Global Interpreter Lock allows one thread to execute Python bytecode at a time — threads don't parallelize CPU-bound pure-Python work (they're fine for I/O waits). Escapes: (1) vectorize into C-backed libraries (numpy/pandas release the GIL inside kernels); (2) multiprocessing — separate interpreters, real parallelism, serialization cost; (3) move the heavy joins/scans to engines built for it (duckdb/polars/kdb).

*Practical application:* Explains why 'add threads' never speeds a pandas backtest and what to say instead.

## Programming: SQL

**Q53. LEFT JOIN with a WHERE on the right table's column — what's the classic bug?**  
*[Tier 1 · Fundamental]*

*Standard answer:* A WHERE right.col = x filters out the NULL rows that the LEFT JOIN preserved, silently converting it to an INNER JOIN. Fix: put the right-side condition in the ON clause, or explicitly handle NULLs (WHERE right.col = x OR right.col IS NULL if that's the intent). Same family: aggregates over LEFT JOINs double-counting when the right side has multiplicity — de-duplicate before joining.

*Practical application:* Coverage reports ('orders WITHOUT fills') are exactly the queries this bug corrupts.

**Q54. GROUP BY vs window functions: when is each correct for TCA aggregates?**  
*[Tier 1 · Fundamental]*

*Standard answer:* GROUP BY when the deliverable is one row per group (average slippage per algo per day). Window functions when each row needs group context but must survive (each fill tagged with its percentile within the parent order; each order compared to its client's trailing average). Mixing them: aggregate first in a CTE, then join/window — trying to do both in one pass is where wrong numbers come from.

*Practical application:* Client packs are GROUP BY; blotter enrichment is windows; knowing which is which keeps queries honest.

**Q55. WHERE vs HAVING, and NULL three-valued logic — the two classic filters that surprise.**  
*[Tier 1 · Fundamental]*

*Standard answer:* WHERE filters rows BEFORE aggregation, HAVING filters groups AFTER (conditions on aggregates live in HAVING). NULLs: comparisons with NULL yield UNKNOWN, not false — NULL = NULL is not true, so WHERE col != 5 silently drops NULL rows too; membership via IS NULL / IS NOT DISTINCT FROM. NOT IN with a NULL in the list matches NOTHING — the cruellest version.

*Practical application:* The NOT-IN-with-NULL empty result is a real production incident pattern in exclusion lists.

**Q56. UNION vs UNION ALL, and the standard de-duplication pattern for 'latest row per key'.**  
*[Tier 1 · Fundamental]*

*Standard answer:* UNION de-duplicates (a sort/hash cost and sometimes WRONG semantics when duplicates are legitimate); UNION ALL concatenates — default to ALL unless dedup is intended. Latest-per-key: ROW_NUMBER() OVER (PARTITION BY key ORDER BY ts DESC) = 1 — the canonical pattern for last order state, latest quote per symbol, most recent client mapping.

*Practical application:* Order-state snapshots from event logs are the ROW_NUMBER pattern verbatim.

**Q57. Write the logic for per-symbol running VWAP over a day using window functions.**  
*[Tier 2 · Role-critical]*

*Standard answer:* SUM(price*qty) OVER (PARTITION BY sym ORDER BY ts ROWS UNBOUNDED PRECEDING) / SUM(qty) OVER (same window). The concept being tested: window functions compute per-row running aggregates without collapsing rows (unlike GROUP BY), and the frame clause (ROWS vs RANGE) controls exactly which rows accumulate. RANGE with duplicate timestamps includes peers — a subtle correctness difference on busy ticks.

*Practical application:* Running benchmarks (VWAP-to-date on the blotter) are window functions verbatim.

**Q58. How does a B-tree index speed queries, what does it cost, and why does composite-index column order matter?**  
*[Tier 3 · Good-to-know]*

*Standard answer:* A B-tree keeps keys sorted in a shallow balanced tree: point lookups and range scans become O(log n) + sequential leaf reads instead of full scans; costs are write amplification (every insert/update maintains the tree) and space. Composite (a,b) serves 'a =' and 'a =, b range' but NOT 'b alone' — leftmost-prefix rule; order columns by equality-first, selectivity-aware.

*Practical application:* Enough index literacy to reason about why the fills-by-client query is slow — and to talk to the data engineers.

## Programming: kdb+/q

**Q59. aj vs wj in q — when do you need the window join?**  
*[Tier 2 · Role-critical]*

*Standard answer:* aj attaches the single prevailing right-side row as of each left timestamp — quote at trade time. wj aggregates over a WINDOW around each left timestamp — e.g., min/max/avg of quotes in [t−1s, t+5s] around each fill, which is exactly a markout or a pre/post-trade quote context. aj answers 'what was the state', wj answers 'what happened around it'.

*Practical application:* Markout curves at tick resolution are one wj; recognizing that is real q fluency.

**Q60. Why is kdb fast — and what do the s/p/g attributes do?**  
*[Tier 3 · Good-to-know]*

*Standard answer:* Column-oriented memory layout (scan only needed columns), vector primitives over columns, and date-partitioned on-disk tables so queries touch only relevant partitions. Attributes: `s# (sorted) enables binary search and is required for fast aj; `p# (parted) groups equal values contiguously — the standard sym-column attribute in partitioned tick DBs; `g# (grouped) builds a hash index for lookups on unsorted data. Applying `s# to an unsorted column throws — attributes are promises, not hints.

*Practical application:* Enough depth to clear the 'is KDB+ on your CV real' probe honestly.

## Programming: Algorithms

**Q61. Hash map vs sorted structure — pick for: (a) order-id lookup, (b) 'all orders within price band', (c) time-ordered replay.**  
*[Tier 1 · Fundamental]*

*Standard answer:* (a) Hash map — O(1) exact-key lookup, no ordering needed. (b) Sorted structure (tree/sorted array) — range queries need order; hash maps can't answer bands without full scans. (c) Neither — a queue/append-only log in arrival order; replay is sequential iteration. The meta-answer interviewers want: choose by the QUERY pattern, not the data type.

*Practical application:* The generic DS screening question; the meta-answer is what scores.

**Q62. Sorting: complexity bounds and which algorithm behavior actually matters in analytics work.**  
*[Tier 1 · Fundamental]*

*Standard answer:* Comparison sorts are Ω(n log n) — quicksort average n log n (worst n², mitigated by randomization), mergesort guaranteed n log n and STABLE, heapsort in-place n log n. What matters in practice: stability (preserving original order among ties — needed when sorting fills by price then relying on time order), nearly-sorted data (timsort exploits runs — pandas/Python default), and that counting/radix beat the bound for bounded integer keys.

*Practical application:* 'Sort by price, stable within timestamp' correctness depends on knowing which sorts are stable.

**Q63. Compute a running mean and variance in one pass over a stream (Welford). Why not the naive sum-of-squares formula?**  
*[Tier 2 · Role-critical]*

*Standard answer:* Welford: keep n, mean, M2; per observation δ=x−mean; mean+=δ/n; M2+=δ·(x−mean); variance=M2/(n−1). The naive E[x²]−E[x]² computed from running sums catastrophically cancels when variance is small relative to the mean's magnitude (two huge nearly-equal numbers subtracted in floating point), producing garbage or negative variance. Welford is numerically stable and O(1) memory — the streaming-analytics workhorse.

*Practical application:* Live blotter stats (running slippage dispersion) are Welford loops; the cancellation story shows numeracy.

**Q64. Binary search: the two implementation bugs everyone writes, and a desk use beyond arrays.**  
*[Tier 2 · Role-critical]*

*Standard answer:* Bugs: (1) mid = (lo+hi)/2 overflow in fixed-width languages (use lo + (hi−lo)/2 — moot in Python but say it); (2) off-by-one loop invariants — be rigorous about [lo, hi) vs [lo, hi] and which side moves, or the loop misses boundaries/spins. Beyond arrays: bisecting on ANY monotone predicate — largest order size whose predicted cost ≤ budget is a binary search over the cost model.

*Practical application:* Invert-the-cost-model queries ('max size within X bps') are monotone bisection in production.

**Q65. Sliding-window technique: compute rolling 5-minute notional in O(n) over a tick stream.**  
*[Tier 2 · Role-critical]*

*Standard answer:* Two pointers over the time-sorted stream: advance the right pointer adding each trade's notional to a running sum; advance the left pointer subtracting trades older than t−5min. Each element enters and leaves once — O(n) total versus O(n·w) recompute. Extensions: monotonic deques give rolling max/min in O(n) (for rolling high/low bands).

*Practical application:* Every rolling blotter metric (participation, notional, VWAP-window) is this pattern; recompute-per-tick kills dashboards.

**Q66. Why are order books natural heap/tree structures, and what operations must be O(log n) or better?**  
*[Tier 3 · Good-to-know]*

*Standard answer:* A book needs: best bid/ask lookup (O(1) at the top), insert new level, delete/cancel arbitrary levels, and update quantities. Sorted structures (balanced BST / skip list) give O(log n) for all with ordered traversal for depth; heaps give O(1) top and O(log n) insert but O(n) arbitrary cancel unless paired with a hash map of handles (the standard combo: hash map for id→node + price-ordered structure for levels). Naive sorted arrays make cancels O(n) — fatal at market data rates.

*Practical application:* Not building matching engines in this seat — but the data-structure instinct question is common.

**Q67. Reservoir sampling: uniform sample of k items from a stream of unknown length — how, and why it works?**  
*[Tier 3 · Good-to-know]*

*Standard answer:* Keep the first k; for item i>k, accept it with probability k/i and, if accepted, evict a uniformly random resident. Induction shows every item ends resident with probability k/n exactly. One pass, O(k) memory — the tool for 'representative sample of today's fills' without knowing the day's count in advance.

*Practical application:* Sampling fills for expensive per-order diagnostics without loading the day.

## Math: Probability

**Q68. Expected number of fair-coin tosses to see HH, and to see HT — and why they differ.**  
*[Tier 1 · Fundamental]*

*Standard answer:* HH: 6. HT: 4. Why they differ: track progress states. For HT, once you've seen an H, every subsequent toss either finishes (T) or LEAVES YOU at 'have H' (another H) — progress never resets, so E = 2 (reach H) + 2 (then reach T) = 4. For HH, after an H, a T throws you back to scratch — the pattern's self-overlap forces resets, giving 6 via E = 2 + 2·(1/2·0 + 1/2·(E+... )) solved as E=6. General principle: self-overlapping patterns wait longer than patterns whose partial progress is retained.

*Practical application:* Classic trading-interview warm-up; the reset-vs-retain intuition is the point, not the memorized numbers.

**Q69. You see a stock move +1% or −1% each day with equal probability, independently. What's the expected absolute distance from start after 100 days, roughly?**  
*[Tier 1 · Fundamental]*

*Standard answer:* Sum of 100 iid ±1% steps: standard deviation = 1%·√100 = 10%. Expected ABSOLUTE displacement of a (approximately) normal variable = σ·√(2/π) ≈ 0.8σ ≈ 8%. The √t scaling is the takeaway: dispersion grows with the square root of horizon — the mathematical heart of why timing risk grows as execution slows, and of the Almgren-Chriss trade-off.

*Practical application:* √t scaling connects a coin puzzle directly to the impact-vs-risk frontier — say that connection out loud.

**Q70. Expectation and variance rules: state them, and where does independence actually matter?**  
*[Tier 1 · Fundamental]*

*Standard answer:* E is linear ALWAYS: E[aX+bY] = aE[X]+bE[Y], independence irrelevant. Var(aX+bY) = a²Var(X)+b²Var(Y)+2abCov(X,Y) — independence (or just zero covariance) kills the cross term. Products: E[XY] = E[X]E[Y] only under independence/uncorrelatedness. Most quick-math interview errors are misplacing the independence requirement.

*Practical application:* Portfolio-of-orders risk arithmetic uses exactly these; the covariance term is the whole story on correlated fills.

**Q71. Birthday problem: how many people for a 50% shared-birthday chance, and why does intuition fail?**  
*[Tier 1 · Fundamental]*

*Standard answer:* 23. Intuition fails because collisions grow with PAIRS: n people have n(n−1)/2 ≈ 253 pairs at n=23, each a ~1/365 shot; P(no collision) = Π(1−k/365) ≈ e^{−n²/730} ≈ 0.49. The square law is the point: collision-type events (hash clashes, order-ID collisions, coincidental fills) arrive far sooner than linear intuition expects.

*Practical application:* The reason ID spaces and sampling schemes get sized off pair counts, not object counts.

**Q72. Monty Hall: the answer and the cleanest reasoning.**  
*[Tier 1 · Fundamental]*

*Standard answer:* Switch — it wins 2/3. Cleanest framing: your initial pick is right 1/3 of the time; the host's reveal is INFORMATIVE because he always opens a goat door among the others — the remaining unopened door inherits the full 2/3 mass of 'you were initially wrong'. The host's constraint (never reveals the car) is what breaks symmetry; with a random-revealing host it's 1/2 conditional on seeing a goat.

*Practical application:* A conditioning-discipline test: what the information COULD have been matters, not just what it was.

**Q73. Memorylessness: which distributions have it, and what does it mean operationally?**  
*[Tier 1 · Fundamental]*

*Standard answer:* Exponential (continuous) and geometric (discrete) — uniquely. P(T > s+t | T > s) = P(T > t): having waited tells you nothing about remaining wait. Operationally: under Poisson arrivals, 'we've had no fills for 5 minutes' does NOT make a fill more due — the due-ness intuition is a memoryless-violation claim that needs evidence (e.g., self-exciting flow).

*Practical application:* Kills a whole family of 'we're due' arguments on the desk unless the data shows clustering.

**Q74. Conditional expectation as a projection: what does E[Y|X] minimize, and why does that matter for benchmarks?**  
*[Tier 2 · Role-critical]*

*Standard answer:* E[Y|X] is the function of X minimizing E[(Y−f(X))²] — the L² projection of Y onto information X. Regression estimates exactly this under its assumptions. Benchmark relevance: an expected-cost benchmark E[cost|order characteristics] is BY CONSTRUCTION the fair conditional yardstick — deviations from it (realized minus predicted) are the mean-zero surprise component, which is why predicted-vs-realized is the statistically clean way to track performance drift.

*Practical application:* Elevates the expected-cost benchmark from 'a model' to 'the projection-theory-correct object'.

**Q75. A martingale in one sentence, why efficient prices are ~martingales, and one execution consequence.**  
*[Tier 2 · Role-critical]*

*Standard answer:* A process where the expected next value, given everything known now, equals the current value: E[P_{t+1}|F_t]=P_t. If prices predictably drifted, arbitrage would trade the drift away — hence 'no free lunch' pushes prices toward martingale behavior (microstructure noise aside). Execution consequence: you cannot systematically 'wait for a better price' without a genuine signal — waiting buys variance (timing risk), not expected improvement; only impact reduction justifies patience.

*Practical application:* The clean answer to a client's 'why not just wait for dips' — patience buys variance, not edge.

**Q76. Coupon collector: expected rolls to see all 6 faces of a die, and the general scaling.**  
*[Tier 2 · Role-critical]*

*Standard answer:* n·H_n: 6·(1+1/2+...+1/6) = 14.7. Each new face is a geometric wait with success probability (n−k)/n, and expectations add. General scaling n ln n + γn: completeness gets expensive at the END — the last few 'coupons' dominate. Practical echo: sampling every venue/regime combination at least once takes far longer than uniform intuition suggests.

*Practical application:* Why 'we've seen every market condition' claims need n ln n-scale samples, not n.

**Q77. Gambler's ruin, fair game: starting at k with absorbing barriers at 0 and N — probability of reaching N, and expected duration.**  
*[Tier 2 · Role-critical]*

*Standard answer:* P(reach N first) = k/N (a martingale argument: stopped fair game preserves expectation). Expected steps: k(N−k) — maximized mid-range. Two desk echoes: a fair (no-edge) strategy's chance of hitting a profit target before a stop is just the distance ratio; and time-to-resolution is longest when you're far from both barriers.

*Practical application:* The martingale-stopping argument is a favorite 'prove it cleanly' interview follow-up.

**Q78. Expected value of the maximum of two fair dice — compute it cleanly.**  
*[Tier 2 · Role-critical]*

*Standard answer:* Use P(max ≤ m) = (m/6)²: P(max = m) = (m² − (m−1)²)/36 = (2m−1)/36. E[max] = Σ m(2m−1)/36 = 161/36 ≈ 4.47. The CDF-first method is the transferable skill — it generalizes to max of n draws and to order statistics generally (E[max of n uniforms] = n/(n+1)).

*Practical application:* Order-statistics fluency shows up in best-of-venue and extreme-fill analyses.

**Q79. Order arrivals are often modeled as Poisson. Give the key properties and one place the model breaks.**  
*[Tier 3 · Good-to-know]*

*Standard answer:* Poisson(λ): independent increments, exponential inter-arrival times (memoryless), count variance = mean, superposition of independent Poissons is Poisson. Breaks: real order flow is self-exciting — arrivals cluster (one trade triggers others), variance far exceeds mean (overdispersion) — which is why Hawkes processes (intensity jumps after each event, then decays) fit tick data better. Practical reading: liquidity begets liquidity; quiet begets quiet.

*Practical application:* Volume-curve and fill-probability assumptions inherit this; overdispersion is why realized volume misses forecasts so often.

## Math: LinAlg

**Q80. Matrix multiplication: when is it defined, why non-commutative, and why does association order matter computationally?**  
*[Tier 1 · Fundamental]*

*Standard answer:* (m×n)·(n×p) → m×p; AB ≠ BA in general (dimensions may not even permit both). Associativity holds mathematically but cost depends on parenthesization: for A(1000×2)·B(2×1000)·C(1000×2), (AB)C costs ~4M multiplies, A(BC) costs ~8k — chain order is a real optimization. Also the reading skill: a matrix IS a linear map; multiplication is composition.

*Practical application:* Covariance sandwich computations (X'ΣX) done in the wrong order are a genuine slow-code source.

**Q81. Determinant and invertibility: what does det = 0 mean geometrically and statistically?**  
*[Tier 1 · Fundamental]*

*Standard answer:* det measures signed volume scaling of the linear map; det = 0 means the map collapses space onto a lower dimension — columns linearly dependent, no inverse. Statistically: a singular X'X is perfect multicollinearity (dummy trap), a singular covariance means some portfolio has exactly zero variance — usually an artifact (n < dimension, or duplicated series) rather than a fact about markets.

*Practical application:* The 'matrix is singular' error decoded: your regressors or your risk inputs are redundant.

**Q82. OLS as geometry: what is β̂ = (X'X)⁻¹X'y doing, and what does rank deficiency mean here?**  
*[Tier 2 · Role-critical]*

*Standard answer:* Projecting y orthogonally onto the column space of X: fitted values ŷ = X β̂ are the closest point in span(X) to y, residuals are orthogonal to every column (X'e = 0 — the normal equations). Rank deficiency (perfectly collinear columns) means the projection is fine but its COORDINATES aren't unique — infinitely many β give the same ŷ; that's multicollinearity in geometric form, and why prediction survives collinearity while attribution doesn't.

*Practical application:* The geometric telling is the difference between 'used statsmodels' and 'understands regression'.

**Q83. Why must a covariance matrix be positive semi-definite, and what does a 'negative eigenvalue' in an estimated one tell you?**  
*[Tier 2 · Role-critical]*

*Standard answer:* For any weights w, w'Σw is the variance of the portfolio w — variances can't be negative, so Σ is PSD by construction. An estimated Σ with negative eigenvalues means estimation error broke the property: usually too few observations relative to dimension, asynchronous data, or pairwise-deleted missing values. Fixes: shrinkage (Ledoit-Wolf), factor structure, or eigenvalue clipping. Using it raw makes optimizers print arbitrage that doesn't exist.

*Practical application:* Shows up whenever cross-asset execution risk or basket TCA touches an estimated covariance.

**Q84. PCA in three sentences, and one honest execution-analytics use.**  
*[Tier 3 · Good-to-know]*

*Standard answer:* Diagonalize the covariance matrix; eigenvectors are orthogonal directions of maximal variance, eigenvalues their variances; keeping the top k gives the best rank-k approximation of the data (in L² sense). Use: compressing dozens of correlated market-condition features (spreads, vols, volumes across names) into a few regime factors before regressing costs — controlling for 'market state' without 40 collinear regressors. Honesty note: components are statistical, not causal, and can rotate meaning across samples.

*Practical application:* A defensible dimension-reduction answer that doesn't overclaim interpretability.

**Q85. Why do orthonormal transformations matter numerically, and where does QR appear in regression?**  
*[Tier 3 · Good-to-know]*

*Standard answer:* Orthonormal Q preserves lengths and angles (Q'Q = I), so operations through Q don't amplify rounding error — condition numbers stay controlled. OLS via QR: factor X = QR, solve Rβ = Q'y by back-substitution — numerically superior to forming X'X (which SQUARES the condition number). It's what mature libraries do under the hood.

*Practical application:* Why statsmodels doesn't invert X'X, and what 'ill-conditioned' warnings are telling you.

## Math: Optimization

**Q86. Unconstrained optimality: first- and second-order conditions, and the convex shortcut.**  
*[Tier 1 · Fundamental]*

*Standard answer:* FOC: gradient = 0 (stationary point). SOC: Hessian positive semi-definite at the point for a local min (PD for strict). The convex shortcut: for convex f, FOC alone is sufficient AND any local min is global — which is why convex formulations are prized: the conditions you can check actually certify the answer.

*Practical application:* The two-line calculus that underwrites every calibration fit's 'this is THE minimum' claim.

**Q87. Why does convexity matter so much in optimization, and where does it appear in optimal execution?**  
*[Tier 2 · Role-critical]*

*Standard answer:* Convex objectives over convex sets have no spurious local minima — any local optimum is global, first-order conditions are sufficient, and duality/Lagrange machinery behaves. Almgren-Chriss is the canonical execution case: expected impact cost (convex in the trading rate) plus risk-aversion times variance (convex quadratic) minimized over schedules — convexity is what makes the optimal trajectory characterizable in closed form and lets urgency map cleanly onto the frontier.

*Practical application:* One sentence of convexity theory + the AC application is the expected depth here.

**Q88. Set up the Lagrangian for 'minimize expected impact cost subject to completing Q shares' and interpret the multiplier.**  
*[Tier 2 · Role-critical]*

*Standard answer:* min Σ c(q_t) s.t. Σ q_t = Q → L = Σ c(q_t) − λ(Σ q_t − Q). First-order: c'(q_t) = λ for all t — trade so MARGINAL cost is equalized across periods (with convex per-period costs, this spreads trading; with time-varying liquidity, trade more when marginal impact is lower). λ itself is the shadow price: the cost of the last marginal share — exactly the number that tells you what relaxing the completion constraint (working the tail tomorrow) would be worth.

*Practical application:* Marginal-cost-equalization is WHY volume-profile-following schedules are near-optimal — a beautiful thing to say in an interview.

**Q89. Gradient descent: role of the step size, and what problem conditioning does to convergence.**  
*[Tier 2 · Role-critical]*

*Standard answer:* Iterate x ← x − η∇f. Too-large η diverges/oscillates; too-small crawls. For quadratics, convergence rate is governed by the condition number κ = λ_max/λ_min: ill-conditioned (elongated) bowls force tiny steps along steep directions while creeping along flat ones — hence preconditioning, feature scaling, momentum/Adam. Standardizing regressors IS preconditioning.

*Practical application:* Why the GARCH/logistic fit 'didn't converge' and why scaling features fixed it.

**Q90. KKT conditions in one breath — what do they add to Lagrange multipliers?**  
*[Tier 3 · Good-to-know]*

*Standard answer:* For inequality constraints g(x) ≤ 0: stationarity of the Lagrangian, primal feasibility, dual feasibility (multipliers ≥ 0), and complementary slackness (μ·g = 0 — a constraint is either binding or its multiplier is zero). They generalize equality-only Lagrange to inequalities; under convexity they're sufficient. Reading: nonzero multiplier ⇔ binding constraint, and the multiplier prices it.

*Practical application:* Participation caps in optimal schedules: the multiplier on a binding cap is literally the bps value of relaxing it.

## Math: Stochastic

**Q91. Brownian motion vs a random walk: connection, variance scaling, and one execution use of each.**  
*[Tier 1 · Fundamental]*

*Standard answer:* Brownian motion is the scaling limit of random walks (Donsker): steps shrink, frequency grows, and W_t has independent normal increments with Var(W_t)=t — the √t dispersion law. Discrete walk use: bar-level simulations and bootstrap paths. Continuous use: the AC risk term (σ²∫x_t²dt uses BM variance scaling) and any 'cost of delay' variance calculation. The √t law is the practical content: half the horizon, ~70% of the timing risk.

*Practical application:* √t appears in every timing-risk estimate the desk quotes; know where it comes from.

**Q92. The Markov property, and what a stationary distribution of a chain means.**  
*[Tier 1 · Fundamental]*

*Standard answer:* The future depends on the present state only, not the path: P(X_{t+1}|X_t, history) = P(X_{t+1}|X_t). A stationary distribution π satisfies π = πP — running the chain from π keeps marginals fixed; for irreducible aperiodic finite chains, any start converges to π, and long-run time-averages equal π-averages (ergodicity). Modeling regimes as a Markov chain gives switching dynamics with tractable long-run behavior.

*Practical application:* Regime models (calm/trending/stressed) with transition matrices are the desk's simplest useful dynamics.

**Q93. Symmetric random walk on {0,...,N} starting at k: expected time to hit a boundary?**  
*[Tier 2 · Role-critical]*

*Standard answer:* k(N−k) steps — the discrete second-moment identity (solve E_k = 1 + (E_{k−1}+E_{k+1})/2 with E_0=E_N=0; quadratic ansatz). Note it matches gambler's-ruin duration, as it must. Scale intuition: doubling the distance to both barriers quadruples expected time — diffusive, not linear.

*Practical application:* Back-of-envelope for 'how long until price exits this band' under no-drift assumptions.

**Q94. Ornstein-Uhlenbeck process: dynamics, stationary distribution, and why it's the mean-reversion workhorse.**  
*[Tier 3 · Good-to-know]*

*Standard answer:* dx = θ(μ−x)dt + σdW: pulled toward μ at rate θ, diffused by σ. Stationary distribution N(μ, σ²/2θ); autocorrelation e^{−θτ} — the continuous-time AR(1), half-life ln2/θ. Workhorse because spreads, imbalances, and short-horizon liquidity states are pull-to-level phenomena: fitting θ gives the decay speed that tells an algo how long a dislocation is worth waiting out versus crossing.

*Practical application:* 'How long does a wide spread stay wide' is an OU half-life question — connects theory to a routing decision.

**Q95. Geometric Brownian motion: solution, distribution, and the −σ²/2 term's meaning.**  
*[Tier 3 · Good-to-know]*

*Standard answer:* dS/S = μdt + σdW solves to S_t = S_0·exp((μ−σ²/2)t + σW_t): log-price is normal, price log-normal. The −σ²/2: E[S_t] = S_0e^{μt} despite the median growing at μ−σ²/2 — volatility drags the TYPICAL path below the mean path (Jensen). That wedge is why high-vol assets' median outcomes disappoint their expected returns.

*Practical application:* Light-touch here (not a derivatives seat), but the vol-drag intuition earns nods.

**Q96. Itô's lemma, stated simply — why do stochastic calculus rules differ from ordinary calculus?**  
*[Tier 3 · Good-to-know]*

*Standard answer:* For f(S,t) with dS = μdt + σdW: df = (∂f/∂t + μ∂f/∂S + ½σ²∂²f/∂S²)dt + σ(∂f/∂S)dW. The extra ½σ²f'' term exists because (dW)² = dt — Brownian paths accumulate quadratic variation at rate t, so second-order terms survive where ordinary calculus discards them. It's the mathematical source of the GBM −σ²/2 and of convexity corrections generally.

*Practical application:* One clean paragraph of it signals mathematical maturity; more is out of scope for this seat.
