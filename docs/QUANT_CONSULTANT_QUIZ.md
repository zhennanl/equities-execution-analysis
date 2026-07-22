# GSET Quant Execution Consultant — Study Quiz (July 2026)

*31 questions with standard answers and practical-application
notes. Source of truth: `docs/quiz_src/questions.py` — edit there and re-run
`build_bank.py` to regenerate this file and `QUANT_CONSULTANT_QUIZ.html` together.*

**Categories:** Benchmarks & TCA (5) · Microstructure & Impact (5) · US Market Structure (6) · Backtesting & Calibration (3) · A/B Testing (3) · Statistics (4) · KDB+/q (2) · Client & Compliance (3)

**Tiers:** Tier 1 · Fundamental (0) · Tier 2 · Role-critical (31) · Tier 3 · Good-to-know (0) — study Tier 1 to fluency first, Tier 2 is where the interview lives, Tier 3 differentiates.

## Benchmarks & TCA

**Q1. A PM sends a 500k-share buy at 10:00 with instruction 'beat VWAP'. The fill beats interval VWAP by 3 bps but arrival slippage is +45 bps. Did you do a good job?**  
*[Tier 2 · Role-critical]*

*Standard answer:* Depends entirely on the benchmark that matches the client's intent — and these two answer different questions. Beating interval VWAP says the schedule tracked the market's volume profile well DURING execution; +45 bps vs arrival says the stock ran away after the decision, which VWAP-tracking cannot prevent and partially rewards (a rising tape drags VWAP up with you). If the client's alpha is short-horizon, arrival/IS is the right yardstick and 45 bps is the real cost; if they are benchmark-agnostic rebalancing flow, VWAP is defensible. The professional answer: report both, and agree the benchmark BEFORE the order, not after.

*Practical application:* This is the single most common client-review conversation; the desk's standard slide shows arrival, interval VWAP, full-day VWAP and close side by side.

**Q2. Decompose implementation shortfall into its standard components.**  
*[Tier 2 · Role-critical]*

*Standard answer:* Perold: paper return minus actual return. Standard decomposition — delay cost (decision price to first fill opportunity: the market moving while you stage), trading/execution cost (first fill reference to average fill price: spread plus impact plus timing within execution), opportunity cost (unfilled shares marked at period end vs decision), and explicit costs (commissions, fees, taxes). The components must reconcile to the total — if they don't, the attribution is wrong, not 'approximate'.

*Practical application:* IS attribution is the deep-dive TCA artifact for clients; the reconciliation property is what makes it defensible in a best-ex review.

**Q3. Why is a participation-weighted price (PWP) benchmark sometimes preferred to interval VWAP, and what's its main gaming risk?**  
*[Tier 2 · Role-critical]*

*Standard answer:* PWP (e.g., PWP-20%) benchmarks against the price achievable by trading a FIXED participation rate from arrival, so unlike interval VWAP it doesn't let the algo's own schedule define the interval — an algo that finishes early or late is measured against a consistent counterfactual. Gaming risk: the choice of participation rate; a desk that picks the PWP rate after seeing the tape can always find one it beat. Rate must be fixed ex ante, matched to the order's instruction.

*Practical application:* PWP is standard in US TCA packs; expect clients to ask why their PWP-20 number differs from VWAP on fast days.

**Q4. A client compares your algo's average slippage to another broker's average across THEIR flow and finds you 4 bps worse. What's wrong with the comparison, and what do you propose?**  
*[Tier 2 · Role-critical]*

*Standard answer:* Different flow: order size distribution, name liquidity, side/urgency mix, time-of-day, and market regime all differ across brokers — raw averages measure the flow as much as the algo. Propose a like-for-like framework: condition on order characteristics (size %ADV, spread, volatility, momentum), either by matched samples or a regression with broker dummy plus controls, and compare within strata. Better still, offer a randomized wheel allocation so future comparison is by design rather than adjustment.

*Practical application:* This is the wheel-ranking defense conversation — the bread and butter of execution consulting.

**Q5. What is markout analysis and how do you read a markout curve for a parent order's fills?**  
*[Tier 2 · Role-critical]*

*Standard answer:* Markouts track the signed move from each fill price to the mid at fixed horizons after the fill (seconds to minutes), share-weighted across fills. For a buy: persistently RISING markouts mean price kept moving against the order after fills — momentum/adverse persistence, the order was behind the market; FALLING markouts mean post-fill reversion — you paid temporary liquidity concession a slower or more passive schedule could have partly recaptured. Flat is clean. Horizon choice matters: seconds diagnose venue/fill quality, minutes diagnose schedule.

*Practical application:* Markout curves by venue are how SOR changes get justified to R&D; markouts by algo are how schedule aggressiveness gets tuned.

## Microstructure & Impact

**Q6. State the square-root impact law and its practical implications for scheduling a 10% ADV order.**  
*[Tier 2 · Role-critical]*

*Standard answer:* Impact ≈ η·σ·√(Q/V): cost scales with volatility and the square root of size-over-volume, with η empirically near 0.3–1 depending on fitting convention. Concavity is the operational point: doubling size less than doubles impact, but SPEED loads cost too — trading the same Q faster (higher participation) raises realized impact roughly with the square root of the participation rate. For 10% ADV: expected impact is meaningful but the marginal bps of slowing down decline — the trade-off is against timing risk (variance of arrival slippage grows with duration), which is exactly the Almgren-Chriss frontier.

*Practical application:* This is the pre-trade cost estimate conversation, and the sanity check on any vendor's pre-trade model.

**Q7. Distinguish temporary from permanent impact, and give the standard empirical test.**  
*[Tier 2 · Role-critical]*

*Standard answer:* Permanent impact is the information content — the price level shift that survives after trading stops; temporary is the liquidity concession that decays once demand pressure stops. Empirically: compare average execution price to arrival (total), then price some interval after completion to arrival (permanent proxy); the wedge that reverts is temporary. Almgren et al. 2005 fit permanent as linear in rate and temporary as concave power-law (~0.6). Practical caveat: on a single order there's no control group — reversion measures ARE directional diagnostics, not causal estimates.

*Practical application:* Post-trade reversion panels; also the argument for post-effective completion strategies in rebalance flow (capture reversal of temporary pressure).

**Q8. What is adverse selection for a passive (resting) order, and how does queue position interact with it?**  
*[Tier 2 · Role-critical]*

*Standard answer:* A resting bid gets filled disproportionately when the market is about to move down through it — fills arrive exactly when the informed flow is selling. Payoff to passive fills = spread capture minus adverse selection. Queue position governs both: front-of-queue fills capture spread on benign flow too, back-of-queue fills only when the level is about to break (the worst adverse-selection cohort). This is why fill RATE is a misleading venue metric alone — markouts on those fills tell you what the fills were worth.

*Practical application:* Venue analysis and SOR tuning: two venues with identical fill rates and different post-fill markouts are NOT equal.

**Q9. Kyle's lambda and VPIN — what does each measure, and what's the honest limitation of estimating them from bars?**  
*[Tier 2 · Role-critical]*

*Standard answer:* Kyle's λ is price impact per unit of signed order flow — the depth/informativeness slope from regressing price changes on net flow. VPIN proxies the probability of informed (toxic) flow via volume-bucketed order-flow imbalance, classically using Bulk Volume Classification when trade signs aren't observed. From OHLCV bars both are approximations: BVC infers signing statistically from price changes, and λ from bar aggregation misses within-bar dynamics — fine for regime comparison across time, weak as absolute levels. Say the approximation out loud before someone else does.

*Practical application:* Toxicity spikes on the live blotter (widen limits, slow down); λ regime shifts flag days when standard impact assumptions understate cost.

**Q10. How do bar-based spread estimators (Roll, Corwin-Schultz, EDGE) work at a high level, and why keep several?**  
*[Tier 2 · Role-critical]*

*Standard answer:* Roll infers effective spread from negative serial covariance of price changes (bid-ask bounce); Corwin-Schultz from the ratio of high-low ranges over one vs two days (variance scales linearly, spread doesn't); EDGE (2024) generalizes OHLC-based estimation with better efficiency. All are daily-bar approximations with known failure modes — Roll is undefined when trend swamps bounce (positive autocovariance), CS misbehaves in high overnight-vol regimes. Keeping several with a disagreement flag turns estimator variance into information: agreement within 2x supports the level; disagreement says treat it as order-of-magnitude.

*Practical application:* Pre-trade spread inputs to routing and cost estimates when you lack quote data — and a good interview story about honest uncertainty.

## US Market Structure

**Q11. Walk through the US closing auction mechanics that matter for a MOC-heavy client (times, imbalance data, risks).**  
*[Tier 2 · Role-critical]*

*Standard answer:* NYSE: MOC/LOC orders due by 3:50pm ET with imbalance publication from 3:50 (offset restrictions after); Nasdaq: MOC by 3:55, LOC by 3:58, with the NOII imbalance feed disseminating from 3:50 and updating frequently into 4:00. The close is the deepest single liquidity event of the US day (order of 10%+ of volume; more on rebalance days). Risks: information leakage from your own imbalance contribution, price dislocation vs last continuous print on imbalance days, and cutoff misses forcing next-day completion. On index rebalance dates the auction absorbs enormous size but the print can carry substantial pressure — participation strategy should be pre-agreed.

*Practical application:* Every index-tracking client conversation touches this; the imbalance windows drive the desk's late-day workflow.

**Q12. What are LULD bands and market-wide circuit breakers, and how should an algo behave near them?**  
*[Tier 2 · Role-critical]*

*Standard answer:* LULD: per-stock limit-up/limit-down bands around a rolling 5-minute reference price — 5% for Tier 1 (S&P/Russell 1000 + active ETPs), 10% Tier 2, with bands doubled in the open/close periods; touching a band triggers a limit state and possibly a 5-minute trading pause. Market-wide: S&P 500 down 7%/13% → 15-minute halts (before 3:25pm), 20% → day halt. Algo behavior: recognize limit states (don't chase through a band), re-plan schedules across pauses, and treat band-adjacent prints as unreliable references for benchmarks and signals.

*Practical application:* Halt/band handling is a standard algo-spec item; TCA must also exclude or flag halt-window intervals or benchmarks get polluted.

**Q13. Reg NMS in one minute: what do Rules 611 and 610 do, and what changed recently?**  
*[Tier 2 · Role-critical]*

*Standard answer:* Rule 611 (order protection): no trade-throughs of protected top-of-book quotes on automated markets — routing must respect the NBBO's protected quotes. Rule 610 caps access fees (historically 30 mils/share) and bans locked/crossed markets. Recent evolution: the SEC's 2024 amendments introduced half-penny minimum ticks for tick-constrained names and cut the access-fee cap (to 10 mils), with staged compliance dates — worth stating you'd verify current implementation status rather than quoting from memory. Rule 605 execution-quality disclosures were also modernized in 2024.

*Practical application:* Fee-cap and tick changes feed directly into SOR economics and maker-taker routing tables — a live product-evolution topic.

**Q14. Map the main US liquidity options a parent order can access, and the core trade-off of each.**  
*[Tier 2 · Role-critical]*

*Standard answer:* Lit exchanges (displayed; certainty and queue economics vs full information leakage); dark pools/ATSs including broker pools (midpoint spread capture, reduced pre-trade leakage vs adverse selection and lower certainty); conditional venues/IOIs for block discovery (size vs firm-up risk and leakage through the invite itself); auctions — opening/closing (depth vs concentration risk); SDPs/wholesalers largely for retail flow; and principal liquidity where offered (risk transfer vs price). An execution consultant's framing: each option trades information leakage against immediacy against price improvement, and the right mix is order- and client-specific — which is what algo customization actually means.

*Practical application:* 'Evaluate and leverage liquidity options' is verbatim in the JD — this taxonomy with trade-offs is the expected fluency.

**Q15. A client asks whether routing more to dark pools would improve their outcomes. How do you evaluate it?**  
*[Tier 2 · Role-critical]*

*Standard answer:* Define the metric first (arrival slippage of parent orders, not just fill-level price improvement — dark fills look cheap per fill while delaying completion). Then measure: current dark participation, fill markouts by venue (adverse selection), fill rates conditional on quote state, and reversion after fills. Then experiment: an A/B on comparable orders with different dark-participation caps, powered properly, rather than an anecdote month. Expected honest answer: more dark helps spread-sensitive, patient flow in liquid names; it hurts urgent flow via opportunity cost and can hurt in toxic names where dark fills select against you.

*Practical application:* A canonical customization consult — and a chance to show experiment-first thinking rather than opinion-first.

**Q16. T+1 settlement: what changed operationally in 2024 and why does an execution desk care?**  
*[Tier 2 · Role-critical]*

*Standard answer:* US moved to T+1 in May 2024: affirmation/allocation deadlines compressed to trade date (same-evening affirmation), FX funding for international clients tightened (buy USD assets with less time to source dollars), and fail costs became more immediate. Execution desk relevance: later-day executions leave less post-trade buffer for allocation breaks; international clients (notably Asia time zones) may shift execution timing or pre-fund; securities lending recalls compress. Not a microstructure change, but it changes client behavior around the close and cutoffs.

*Practical application:* Comes up with APAC-domiciled clients trading US flows — a differentiator question for someone with Asia background.

## Backtesting & Calibration

**Q17. Name the three deadliest biases in backtesting an execution algo change, with the standard defense for each.**  
*[Tier 2 · Role-critical]*

*Standard answer:* Look-ahead (using information not available at decision time — e.g., volume curves that include the day being simulated; defense: strictly prior-data inputs, enforced in code not convention). Counterfactual-fill optimism (assuming your simulated child orders would have filled at historical prints without moving them — the tape you backtest on didn't contain your order; defense: conservative fill assumptions, impact overlays clearly labeled as model, and validation against real-fill experiments). Selection/survivorship (testing on names, days, or regimes chosen after seeing outcomes; defense: pre-registered universes and walk-forward splits).

*Practical application:* Any calibration proposal to R&D gets exactly these three challenges; answering them before asked is what 'defensible' means.

**Q18. How would you calibrate the urgency parameter mapping (participation rates) for an IS algo from historical data?**  
*[Tier 2 · Role-critical]*

*Standard answer:* Frame it as the Almgren-Chriss trade-off empirically: for each candidate participation level, estimate realized cost distribution (impact side) and arrival-slippage variance (timing-risk side) from comparable historical orders, stratified by size/spread/volatility; fit the frontier; then choose urgency mappings so Low/Medium/High correspond to defensible points on the frontier (e.g., risk-aversion levels), not folklore. Validate out-of-sample: does the new mapping's predicted cost-risk hold on later data? Ship with a monitoring metric (predicted vs realized by urgency band).

*Practical application:* 'Backtest, calibrate and optimize client flows' — this is the concrete version of that JD bullet.

**Q19. Your backtest says the new SOR logic saves 1.8 bps. What has to be true before you believe it?**  
*[Tier 2 · Role-critical]*

*Standard answer:* Sample: enough orders across regimes that 1.8 bps clears the noise floor (power calc, not vibes). Distribution: not driven by a handful of outlier fills (check trimmed effect, quantiles). Independence: errors clustered by day/name handled. Mechanism: the saving has a microstructure story consistent with WHERE it appears (venue, time of day, spread state) — a saving without a mechanism is usually leakage of a bias. Counterfactual honesty: fill assumptions on the alternative route audited. Then the real test: a live A/B, because backtests don't move markets and SOR changes do.

*Practical application:* The 'gate' checklist between analysis and a production change proposal.

## A/B Testing

**Q20. Design an A/B test for a new default participation cap. Full protocol.**  
*[Tier 2 · Role-critical]*

*Standard answer:* Unit: parent order. Randomization: within strata of client × size-bucket × liquidity-bucket, so arms face matched flow; blocked by day. Metric: pre-registered — arrival IS in bps, with completion rate as guardrail (a cap change can 'win' on price by not finishing). Power: from historical dispersion, compute n for the minimum effect worth shipping (e.g., 1.5 bps at σ_d≈30 → thousands of orders → plan the horizon honestly). No peeking: fixed horizon or alpha-spending. Analysis: as randomized (intention-to-treat), paired/blocked estimator, plus regression with controls as robustness. Rollout rule and rollback trigger pre-agreed.

*Practical application:* 'Propose and implement A/B testing methodologies' — recite this protocol; it maps one-to-one.

**Q21. Why is peeking at an A/B test as results accrue so damaging, and what are the acceptable alternatives?**  
*[Tier 2 · Role-critical]*

*Standard answer:* Repeatedly testing at 5% as data arrives inflates false positives massively — the max of a random walk crosses any fixed boundary far more often than the endpoint does (optional stopping). With weekly peeks over a quarter, nominal 5% can behave like 20–30%. Alternatives: fixed-horizon discipline; group-sequential designs with alpha-spending boundaries (O'Brien-Fleming style) that price the peeks; or Bayesian monitoring with pre-agreed decision thresholds — but pick the regime BEFORE launch. Also pre-register the metric to kill its cousin, outcome-switching.

*Practical application:* Wheel readouts and pilot rollouts generate constant 'can we call it yet?' pressure from sales — this is the answer you'll give weekly.

**Q22. A live A/B shows Algo B better overall, but worse for one large client. Ship it?**  
*[Tier 2 · Role-critical]*

*Standard answer:* First check whether the interaction is real: subgroup analyses multiply comparisons, so test the client-arm interaction properly (and note the subgroup's n — one large client's month is often noise). If real, look for mechanism: that client's flow profile (size, names, urgency) interacting with B's behavior — which suggests customization (client-specific parameters) rather than blocking the global rollout. Decision framework: ship the default where evidence supports it, carve out or customize where a REAL interaction exists, and document both — clients are heterogeneous and 'one default fits all' is not the product.

*Practical application:* Execution Solutions in one scenario: global product evolution + per-client customization, decided statistically.

## Statistics

**Q23. Parametric vs non-parametric tests for slippage comparisons — when and why?**  
*[Tier 2 · Role-critical]*

*Standard answer:* Slippage distributions are fat-tailed and skewed; a handful of tail orders dominate means. Parametric (paired t) is fine when n is large enough for the CLT to protect the mean comparison AND the mean is the decision-relevant quantity. Non-parametric (Wilcoxon signed-rank, Mann-Whitney) tests location robustly at some power cost, and rank-based omnibus (Friedman) handles k algos on blocked data. In practice: report both; when they disagree, the tails are driving the mean — which is itself a finding (investigate the outlier orders before testing anything).

*Practical application:* The daily 'is this difference real' question; disagreement between t and Wilcoxon is a data-quality alarm.

**Q24. You regress cost on sqrt(size), volatility, participation, spread. Interpret the sqrt(size) coefficient and defend the SE choice.**  
*[Tier 2 · Role-critical]*

*Standard answer:* The sqrt(size) coefficient is the impact-curvature loading: bps of cost per unit of √(%ADV), holding conditions fixed — its significance and stability are the empirical content of the square-root law in your flow. SEs: heteroskedasticity is structural (variance grows with size/vol) so HC1 minimum; observations sharing days share shocks, so cluster by day; serial dependence across a time-ordered panel argues Newey-West. Report R² honestly — execution cost regressions live at low R² because most variance is noise; the coefficients, not the fit, carry the value.

*Practical application:* This regression IS the transaction cost model the JD names; the SE defense is the difference between a number and a defensible number.

**Q25. What does a variance-ratio test tell you that autocorrelation at lag 1 doesn't?**  
*[Tier 2 · Role-critical]*

*Standard answer:* VR(q) compares the variance of q-period returns to q times one-period variance: a random walk gives VR=1; VR>1 indicates positive dependence (trending), VR<1 mean-reversion — aggregating dependence across horizons rather than one lag, with Lo-MacKinlay's heteroskedasticity-robust z* making it valid under volatility clustering. Lag-1 autocorrelation is noisy and horizon-blind; VR gives a horizon-structured, robust read — which is why it's a better regime classifier for choosing between momentum-sensitive and reversion-sensitive execution tactics.

*Practical application:* Regime classification feeding algo choice — and a favorite 'do you actually know time series' interview probe.

**Q26. How many paired orders to detect a 2 bps algo improvement, and what does the answer imply for how the team works?**  
*[Tier 2 · Role-critical]*

*Standard answer:* n = ((z_α/2+z_β)·σ_d/δ)²; with σ of paired differences ≈30 bps, δ=2, 5%/80%: ((1.96+0.84)·30/2)² ≈ 1,760 pairs. Implications: single-client months rarely decide anything; wheels and A/Bs run for quarters; 'not statistically separable at this n' is a frequent, CORRECT readout; and the highest-leverage way to shrink n is reducing σ_d — better pairing, stratification, and covariate adjustment — which is why design work is worth more than test choice.

*Practical application:* The number that disciplines every readout meeting; memorize the worked example.

## KDB+/q

**Q27. Why is kdb+/q the standard for tick data, and what is an asof join?**  
*[Tier 2 · Role-critical]*

*Standard answer:* Column-oriented storage with time-ordered partitioning makes scanning billions of quotes/trades fast, and q-sql expresses time-series operations natively. The asof join (aj) is the canonical TCA operation: for each trade, attach the prevailing quote as of (at or before) the trade's timestamp — aj[`sym`time; trades; quotes] — giving effective spread and midpoint benchmarks without expensive interval logic. Knowing aj, wj (window join), and xbar (time bucketing) covers most execution-analytics queries.

*Practical application:* Effective-spread and markout computations on desk tick stores are aj/wj one-liners; even basic fluency differentiates.

**Q28. Sketch the q for average 5-minute-bucketed volume by symbol for one day.**  
*[Tier 2 · Role-critical]*

*Standard answer:* select sum size by sym, 5 xbar time.minute from trade where date=2026.07.08 — xbar buckets timestamps to 5-minute bins, by groups per symbol and bin, sum aggregates. The pattern (aggregate by sym, xbar time) generalizes to VWAP per bucket (size wavg price), participation, and volume curves.

*Practical application:* Building volume curves for scheduling and 'volume running vs expected' monitors — daily bread on the desk.

## Client & Compliance

**Q29. A compliance officer asks you to evidence best execution for a large order that underperformed VWAP by 30 bps. Structure the response.**  
*[Tier 2 · Role-critical]*

*Standard answer:* Best execution is process, not outcome. Evidence: the pre-trade record (benchmark and strategy agreed with the client, expected-cost estimate under prevailing conditions), the in-flight record (parameters, alerts, interventions and their reasons), and the post-trade attribution (WHERE the 30 bps came from — delay vs trading vs opportunity; conditions vs comparable orders; whether realized sat inside the pre-trade confidence band). If the process was sound and documented at decision time, an adverse outcome is variance; if documentation is reconstructed after the fact, that's the finding. This is why decision-time record capture matters more than eloquent post-mortems.

*Practical application:* Maps to the 'discuss with compliance' bullet; decision-time documentation is the modern best-ex standard.

**Q30. Translate for a non-quant PM: 'the strategy dummy is -2.1 bps, t=2.4, controlling for size, vol and spread.'**  
*[Tier 2 · Role-critical]*

*Standard answer:* 'Comparing like-for-like orders — same size, same volatility, same spread environment — the new strategy saved about 2 bps per order, and the pattern is strong enough that it's unlikely to be luck: if there were truly no difference, we'd see a result this clear maybe twice in a hundred samples. On your typical order that's roughly $X saved; across your annual flow, $Y.' Then one caveat, chosen not recited: 'measured over the last quarter's conditions — we re-check as regimes change.' Numbers → money → one honest caveat; never lead with the regression.

*Practical application:* The two-minute client translation is the job's core communication move — practice the money conversion.

**Q31. A trader on the desk says your analysis 'doesn't match what I see on the screen'. How do you handle it?**  
*[Tier 2 · Role-critical]*

*Standard answer:* Take it as data, not offense — traders see conditioning your aggregates wash out. Ask for the specific orders/sessions they mean; re-run conditioned on those (time-of-day, names, regime); the disagreement usually resolves to either a subgroup your average hid (their intuition wins — refine the model) or an availability bias toward memorable bad fills (your data wins — show the full distribution WITH their examples highlighted). Either resolution builds credibility; the losing move is defending the average.

*Practical application:* The internal-stakeholder bullet; execution consulting lives on desk trust.
