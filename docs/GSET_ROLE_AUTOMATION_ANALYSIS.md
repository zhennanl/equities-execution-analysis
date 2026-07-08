# GSET Quantitative Execution Consultant — Responsibility Ranking & Automation Design

*Maps the role's responsibilities to this platform, ranks them by day-one
importance/frequency, and specifies the statistical-modeling capability to build
next. Written to be defensible in interview: every ranking and design choice is
justified, and the honesty boundary (simulation vs. real client fills) is
explicit throughout.*

---

## 1. The role in one line

A GSET Quantitative Execution Consultant turns **client execution data → a
statistical read on execution quality → an actionable recommendation** that a
client, trader, or salesperson can act on, and feeds the same evidence back into
GSET's algo/SOR R&D. The daily currency of the job is **transaction-cost
analysis (TCA) and statistical testing**; the deliverable is a **defensible
number with a confidence interval and a mechanism**.

## 2. Responsibilities ranked by day-one importance × frequency

Ranking criteria: (a) how often a *new* consultant touches it in a normal week,
(b) how central it is to the team's output, (c) how much of it is analytical
(automatable) vs. relational (not). Rank 1 = do this constantly from week one.

| # | Responsibility | Rank | Why it ranks here | Automatable? |
|---|---|---|---|---|
| R3 | **Apply transaction cost models; analyze market-microstructure impact on execution** | **1** | This *is* the job's analytical core. Every client conversation, benchmark, and A/B test rests on a cost model. A starter runs TCA daily. | **High** — the cost model is a regression; fitting/applying it is fully automatable. |
| R7 | **Develop & maintain statistical tools for analyzing strategy performance** | **2** | The tooling that makes R3/R6 repeatable. A junior quant lives in these tools and extends them. JD calls out regression, hypothesis testing, time series. | **High** — this is literally building the automation. |
| R6 | **Propose & implement A/B testing to optimize execution quality** | **3** | Signature GSET deliverable ("does algo A beat algo B, net of conditions?"). Frequent, and the JD names it explicitly. | **High** — paired tests + regression-with-controls. |
| R2 | **Client performance benchmarks; continuous-improvement strategies** | **4** | The framing layer around R3 — what is "good," vs. what benchmark. Ongoing, but rests on the R3 engine. | **Medium** — benchmark computation automatable; target-setting is judgment. |
| R5 | **Backtest, calibrate, optimize client trading flows on the GS platform** | **5** | High value but more platform-specific and senior; a starter contributes pieces (calibration runs, grids). | **Medium/High** — calibration grids and backtests automatable; the proprietary platform is not replicable here. |
| R1 | **Discuss execution performance with clients/traders/sales/compliance** | **6** | Mission-critical to the *role*, but it is the *output* of R3/R6/R7 and is relational, not automatable. A starter supports senior consultants here first. | **Low** — automation *feeds* it (charts, one-pagers), doesn't replace it. |
| R4 | **Evaluate & leverage liquidity options to optimize execution** | **7** | Important and specialized (venue/SOR, dark, auctions), but overlaps microstructure and is more episodic than daily for a starter. | **Medium** — already served by the venue/SOR simulation (Agent 13). |

**Reading of the ranking:** the top three (R3, R7, R6) are one cluster — *a
statistical cost-modelling toolkit* — and they are exactly what a new hire uses
most and what is most automatable. That is where to invest.

## 3. What the platform already automates (and the gap)

| Capability | Where | Serves |
|---|---|---|
| Multi-benchmark post-trade TCA (Arrival/VWAP/TWAP/Close), reversion, permanent/temporary split | Agent 6 | R3, R2 |
| Microstructure impact/toxicity (Kyle's λ, VPIN), square-root impact | Agent 9, Agent 3 | R3 |
| Cross-day comparison + size-sensitivity grid + AC frontier | Agent 4 | R3, R5 |
| A/B test as a **paired backtest** (t-test, Wilcoxon, bootstrap, Cohen's d) | Agent 10 | R6 |
| Venue/SOR & liquidity simulation | Agent 13 | R4 |
| Spread/vol estimators (Corwin-Schultz, Abdi-Ranaldo, Yang-Zhang) | Agents 1/6 | R3 |

**The gap — a fitted transaction cost model.** Everything above *applies* fixed
coefficients (η = 0.3 square-root law) or compares two configs in isolation.
What a GSET desk actually does, and what the JD's "regression analysis" and
"transaction cost models" language points at, is **estimate the cost model from
data by regression** — a cost curve `cost_bps ~ f(size%ADV, volatility,
participation, spread, duration, side, momentum)` with proper standard errors,
diagnostics, and out-of-sample validation. This is missing, and it is the
highest-leverage thing to build because it upgrades R3, R6, and R7 at once:

- **R3 (apply TCM):** the fitted regression *is* the transaction cost model —
  and it produces an *expected-cost benchmark* every order can be measured
  against (predicted vs. realized shortfall).
- **R6 (A/B with controls):** an A/B test run as a regression with a strategy
  dummy **and** condition controls measures the incremental cost of algo A vs. B
  *net of confounders* (size, volatility, spread) — strictly better than a raw
  paired mean difference, because in real client flow the two algos are never
  run on identical conditions.
- **R7 (statistical tools):** it delivers the parametric/non-parametric test
  battery the JD asks for — OLS with heteroskedasticity-robust (White/HC1) and
  autocorrelation-robust (Newey-West HAC) standard errors, F-test, plus
  Breusch-Pagan, Durbin-Watson, and Jarque-Bera residual diagnostics.

## 4. What is being built (top feature)

**`agents/cost_model.py` — a regression-based Transaction Cost Model**, plus a
**cost-panel assembler** that turns the existing multi-day × order-size × algo
simulation into a regression dataset (which also exercises R5: backtest &
calibrate). Surfaced in the app as a **"Cost Model (TCA Regression)"** section
that shows the fitted cost curve, coefficient table with robust t-stats/p-values,
R²/adjusted-R²/F, residual diagnostics, a predicted-vs-realized plot, and an
**A/B-with-controls** readout.

Design choices (all interview-defensible):
- **numpy/scipy only** — no new dependency; the linear algebra and the robust
  variance estimators are implemented explicitly so every number is auditable
  (no black-box `statsmodels` call to hand-wave over).
- **Square-root law as the functional form** — `sqrt(size%ADV)` is the primary
  regressor, matching the empirical market-impact literature the platform
  already cites (Almgren 2005; Zarinelli 2015). The regression *estimates* the
  prefactor instead of assuming η = 0.3, which is precisely "calibrate the cost
  model."
- **Robust inference by default** — execution-cost residuals are heteroskedastic
  (bigger orders → wider cost dispersion) and, in time order, autocorrelated;
  HC1 and Newey-White SEs are the correct, defensible choice, and the naive-OLS
  SE is shown alongside to make the difference explicit.
- **Honesty boundary** — on this platform the "realized" cost is *simulated*, so
  the residual variance is structural, not true client noise. The module is
  written so the identical code fits **real client fills** the moment a panel of
  them is supplied; the simulated panel demonstrates the method and recovers the
  square-root coefficient. This is stated in-app.

## 5. How this enhances efficiency & adds value for the GSET team

1. **Collapses the daily TCA loop from hours to seconds.** Assembling a cost
   panel, fitting a regression, computing robust SEs and diagnostics, and
   plotting predicted-vs-realized is otherwise manual, per-client, per-week work.
   Automating it lets a consultant spend time on the *interpretation and the
   client conversation* (R1) — the part that isn't automatable — instead of the
   plumbing.
2. **Makes A/B conclusions defensible.** Regression-with-controls removes the
   single biggest objection to an execution A/B claim ("but algo A only looks
   better because it ran on easier orders"). The dummy coefficient is the
   apples-to-apples incremental cost, with a confidence interval — exactly what
   a client's head of trading will challenge.
3. **Turns the cost model into a live benchmark.** Predicted cost from the fitted
   model is a *conditional* benchmark (expected bps for *this* order's size, vol,
   spread), sharper than a static VWAP/Arrival benchmark and directly usable in
   R2's continuous-improvement framing.
4. **Feeds GSET R&D with calibrated coefficients.** The estimated square-root
   prefactor and participation-rate sensitivity are exactly the inputs the algo/
   SOR team needs to recalibrate schedules — closing the loop the JD describes.
5. **Standardizes the method across the desk.** One audited, tested tool means
   every consultant's TCA uses the same estimator, robust SEs, and diagnostics —
   consistent, reviewable, and onboarding-friendly for the next new hire.

*Scope honesty: this is a research/consulting analytics layer on free simulated
data, not GS's production TCA. Its value proposition is the **method and the
tooling** — which transfer directly to a real fill panel — not the specific
coefficients estimated on simulated executions.*

---

## 6. Seven-responsibility coverage map (implemented)

Each JD responsibility now maps to concrete, tested platform features:

| # | Responsibility | Implemented feature(s) | Module |
|---|---|---|---|
| R1 | Discuss execution performance with clients | Client-ready **TCA one-pager** generator (markdown, downloadable) | `client_analytics.client_report` |
| R2 | Client benchmarks + continuous improvement | **Benchmark scorecard** (realized vs benchmarks vs model-expected vs own history, with grade + improvement delta) | `client_analytics.benchmark_scorecard` |
| R3 | Apply TCM; microstructure impact | **Regression cost model**; **EDGE/CS/AR** spreads; **Amihud** illiquidity; intraday **seasonality**; Kyle λ/VPIN (existing) | `cost_model`, `microstructure_analytics`, `agent9` |
| R4 | Liquidity options optimisation | Venue/SOR sim (existing); **price-limit bands** + flag; **closing-auction concentration**; seasonality-aware scheduling | `agent13`, `asian_markets`, `microstructure_analytics` |
| R5 | Backtest, calibrate, optimise flows | Multi-day comparison + size sensitivity (existing); **cost-panel calibration** across size×algo×day | `agent4`, `cost_panel` |
| R6 | A/B testing for execution quality | Paired backtest (existing) **+ A/B-with-controls** regression (confounder-adjusted) | `agent10`, `cost_model.ab_test_with_controls` |
| R7 | Statistical tools for strategy performance | OLS + HC1/HAC robust SEs, F-test, DW/BP/JB diagnostics; **ACF + Ljung-Box** time series | `cost_model`, `microstructure_analytics` |

All grounded in the microstructure literature (Asia-focused where possible):
`docs/MICROSTRUCTURE_RESEARCH_IMPROVEMENTS.md`.
