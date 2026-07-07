# Execution Algorithm Simulator — Per-Agent Research Base & Design Audit

*Literature review for each stage of Module 1's pipeline, with a verdict per
modeling choice: **KEEP** (aligned with the evidence), **CHANGE** (evidence
justifies a code change), or **ROADMAP** (worthwhile, not urgent). Compiled
2026-07-07. Companion to `INDEX_REBALANCE_RESEARCH.md`.*

---

## Agent 1 — Market Data (ADV, realized volatility, volume profile)

**Current:** ADV from 60-day daily volume; annualized realized volatility from
**close-to-close** daily returns; 5-min intraday volume profile.

**Literature:**
- **Yang & Zhang (2000)** — the minimum-variance unbiased OHLC volatility
  estimator: combines overnight (close-to-open), open-to-close, and
  Rogers-Satchell range components; drift-independent and jump-aware. It is
  **~8× more statistically efficient** than close-to-close on the same data —
  a 5-day YZ window ≈ a 70-day close-to-close window in precision.
- Wood, McInish & Ord (1985), Jain & Joh (1988) — intraday U-shaped volume;
  Admati & Pfleiderer (1988) — theoretical rationale (liquidity clustering).

**Verdict: CHANGE.** σ feeds every impact number in the app (square-root
model, Almgren cross-check, capacity, frontier). Daily OHLC is already
fetched, so switching realized vol to Yang-Zhang is nearly free and improves
every downstream estimate — especially with short histories where
close-to-close is noisiest. Volume-profile treatment: KEEP.

## Agent 2 — Market Regime (volatility, volume shape, trend)

**Current:** intraday vol vs 20-day median; volume-shape classification
(U-shaped/uniform/midday-heavy); trend via **Lo-MacKinlay (1988) variance
ratio** with the **heteroskedasticity-robust z** as the headline statistic.

**Literature:** Lo & MacKinlay (1988); Campbell, Lo & MacKinlay (1997). The
classic misuse is relying on the iid-z, which conflates volatility clustering
with autocorrelation — the robust z* is the correct choice and is already
what the code reports.

**Verdict: KEEP.** The main methodological trap is already avoided.

## Agent 3 — Algorithm Simulation

**(a) VWAP/MOC/MOO volume curves.** Current: leave-one-out 5-day historical
average curve (look-ahead-bias-free).
- **Białkowski, Darolles & Le Fol (2008, JBF)** decompose intraday volume into
  a common (historical average) + stock-specific dynamic component
  (ARMA/SETAR); the dynamic term improves VWAP tracking vs pure historical
  curves. Later comparisons find BDL both more accurate and faster than
  CIR-type alternatives; recent work extends to ML forecasts.
- **Verdict: KEEP the historical common component; ROADMAP the dynamic
  update** — the natural home is the Live Trading Session: re-forecast the
  *remaining* day's curve from elapsed bars (a DVWAP analog), which is
  exactly BDL's use case. Static pre-trade simulation on historical days is
  fine as is.

**(b) Market impact.** Current: square-root law, cost = η·σ_d·√(Q/ADV) with
**η = 0.3**, times a per-algo speed factor.
- The square-root form is among the best-established empirical regularities:
  **Zarinelli et al. (2015)** (8M metaorders: exponents ≈ 0.52-0.54,
  prefactor A ≈ 0.2); **Bershova & Rakhlin (2013)** (proprietary buy-side
  data, consistent); a 2024 Tokyo Stock Exchange survey finds **"strict
  universality"** across stocks; a 2026 single-name AAPL calibration finds
  prefactor 0.34-0.69 depending on bias treatment. Duration/participation
  dependence beyond √Q is empirically weak.
- **Verdict: KEEP, with documentation.** η = 0.3 sits inside the empirical
  0.2-0.7 prefactor band. The per-algo *speed factor* is a practitioner
  heuristic without direct literature support — acceptable because the
  Almgren-2005 calibrated model is reported side-by-side as the cross-check
  precisely for this model risk; the docstring should say so explicitly.

**(c) IS trajectory.** Current: Almgren-Chriss (2001) optimal trajectory,
urgency → κT mapping. Canonical; the urgency mapping is a labeled heuristic.
**KEEP.**

**(d) Opportunity cost.** Perold (1988) implementation-shortfall accounting
on unfilled shares. Canonical. **KEEP.**

## Agent 4 — Performance Comparison

**Current:** re-simulation across all available days, fill-qualification gate
(90%) for "best algo", full order-size sensitivity by re-simulation.

**Literature:** cross-day averaging with paired conditions is the same logic
as broker **algo wheels** (randomized assignment); Agent 10's paired
hypothesis tests supply the statistical machinery. **Verdict: KEEP;
ROADMAP** the N-arm randomized wheel (register I-7).

## Agent 5 / Agent 8 — Recommendation + Critic

Rule-based selection given regime/benchmark/urgency, with an independent
critic that flags rather than overrides. This is a deliberate design stance
(deterministic, auditable — see PROJECT_CONTEXT.md), not a modeling claim
with a literature to test. **KEEP.**

## Agent 6 — Pre-Trade / Post-Trade

**(a) Spread estimate.** Current: **Corwin-Schultz (2012)** high-low
estimator from daily bars, with reliability labeling; capped at 15 bps when
feeding venue routing.
- Known CS weaknesses: negative estimates needing ad-hoc treatment, bias
  when trading is infrequent, and **overshoot at daily frequency for liquid
  names** (the reason the routing cap exists).
- **Abdi & Ranaldo (2017, RFS)** — close-high-low estimator: uses more of the
  daily bar, independent of trade-direction dynamics, generally more accurate
  across liquidity regimes (CS has lower variance in small samples).
- **Ardia, Guidotti & Kroencke (2024, JFE)** — "EDGE" OHLC estimator, current
  state of the art for efficiency.
- **Verdict: CHANGE.** Add **Abdi-Ranaldo** as a second estimator computed
  from the same daily bars; report both with agreement/disagreement feeding
  the reliability label, and use the median of {CS, AR} as the routing input
  (still capped). EDGE: ROADMAP.

**(b) Almgren, Thum, Hauptmann & Li (2005) cross-check.** Calibrated on
~29,500 real institutional orders; permanent linear + temporary 3/5-power.
Best-practice as an independent second model. **KEEP.**

**(c) Post-trade TCA.** Multi-benchmark (Arrival/VWAP/TWAP/Close), cost
percentile vs history, reversion check, permanent/temporary decomposition —
consistent with standard TCA practice. Full IS attribution with explicit
fees: **ROADMAP** (register I-5/I-6).

## Agent 7 — Earnings Calendar

Overnight-gap risk flag when a print falls inside the horizon. Consistent
with the event-risk literature (announcement-window variance is elevated —
e.g. Dubinsky & Johannes). Proportionate as a flag. **KEEP.**

## Agent 9 — Market Microstructure (Kyle's λ, VPIN)

**Current:** Kyle's lambda and VPIN estimated via Bulk Volume Classification
(Easley, López de Prado & O'Hara 2012) on 5-min bars.

**Literature:**
- Kyle (1985) — λ as price impact per unit signed flow: canonical.
- **The VPIN dispute**: **Andersen & Bondarenko (2014, JFM)** show VPIN's
  predictive content is largely a **mechanical reflection of volume and
  volatility**, that it peaked *after* (not before) the Flash Crash, and that
  results flip under standard trade-classification rules; **Easley, López de
  Prado & O'Hara's rejoinder** defends the toxicity→liquidity→volatility
  channel. The honest reading: VPIN is a **monitoring signal correlated with
  stress**, not a validated predictor.
- BVC classification accuracy at bar granularity is itself contested
  (tick-rule comparisons are mixed) — worth stating since no tick data is
  available here anyway.

**Verdict: CHANGE (disclosure, not computation).** Keep computing both, but
the UI and docstring must present VPIN as a contested monitoring signal with
the Andersen-Bondarenko citation, and note the BVC dependence. The critic
(Agent 8) consuming λ/VPIN as *flags* — not automatic actions — is already
the right posture given this literature.

## Agent 13 — Venue Router

Stylized venue parameters. Literature anchors for the parameter *directions*:
**Zhu (2014, RFS)** — dark pools concentrate uninformed flow (midpoint fills
carry adverse selection when informed traders migrate); **Battalio, Corwin &
Jennings (2016, JF)** — routing to maximize rebates degrades fill quality
(why the inverted venue carries a markout penalty). Already documented as
stylized constants in the module docstring. **KEEP.**

---

## Summary of verdicts

| Item | Verdict | Action |
|---|---|---|
| Realized vol estimator (Agent 1) | **CHANGE** ✅ shipped 2026-07-08 | Yang-Zhang (2000) from existing daily OHLC; disclose in UI |
| Spread estimator (Agent 6) | **CHANGE** ✅ shipped 2026-07-08 | Add Abdi-Ranaldo (2017) beside Corwin-Schultz; median feeds routing; agreement drives reliability label |
| VPIN presentation (Agent 9) | **CHANGE** (disclosure) ✅ shipped 2026-07-08 | Andersen-Bondarenko caveat in UI + docstring; frame as monitoring signal |
| Impact η documentation (Agent 3) | **CHANGE** (docs) ✅ shipped 2026-07-08 | State the 0.2-0.7 empirical prefactor band (Zarinelli et al.) and that speed factors are heuristic |
| VR test, AC trajectory, Perold, Almgren-2005 cross-check, TCA suite, rule-based Agent 5 + critic | KEEP | — |
| Dynamic (BDL-style) volume re-forecast in live session | ROADMAP | Pairs with live-session constraint binding |
| EDGE spread estimator; N-arm algo wheel; IS attribution + fees | ROADMAP | Register I-5/I-6/I-7 |

## Sources

- [Yang-Zhang estimator overview & efficiency](https://trendsandbreakouts.com/yang-zhang-volatility) · [Salt Financial volatility forecasting guide](https://saltfinancial.com/static/uploads/2021/05/The%20Laymans%20Guide%20to%20Volatility%20Forecasting.pdf)
- [Lo & MacKinlay (1988) variance ratio — as implemented]
- [Białkowski, Darolles & Le Fol (2008) — Improving VWAP strategies (SSRN)](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=932699) · [KIT symposium version](https://www.fbv.kit.edu/symposium/10th/papers/Bialkowski_Darolles_LeFol%20-%20Decomposing%20volume%20for%20VWAP%20strategies.pdf)
- [Zarinelli et al. (2015) / square-root law empirics — Donier slides](https://www.imperial.ac.uk/media/imperial-college/research-centres-and-groups/cfm-imperial-institute-of-quantitative-finance/events/imperial-eth-2016/Jonathan-Donier-.pdf) · [Strict universality on TSE (arXiv 2024)](https://arxiv.org/pdf/2411.13965) · [AAPL calibration (arXiv 2026)](https://arxiv.org/pdf/2606.24019)
- [Abdi & Ranaldo (2017) close-high-low estimator — slides](https://ba-odegaard.no/teach/notes/liquidity_estimators/abdi_ranaldo_high_low_estimator/slides_high_low_ar.pdf) · [Ardia, Guidotti & Kroencke (2024, JFE) EDGE](https://www.sciencedirect.com/science/article/pii/S0304405X24001399) · [Tremacoldi-Rossi — bias of simple spread estimators](https://pedrotrossi.github.io/JMP/spreads.pdf)
- [Andersen & Bondarenko — VPIN and the Flash Crash (SSRN)](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1881731) · [Reflecting on the VPIN Dispute](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2305905) · [ELO rejoinder (JFM)](https://www.sciencedirect.com/science/article/abs/pii/S1386418113000293)
- Zhu (2014, RFS); Battalio, Corwin & Jennings (2016, JF) — venue-parameter directions (Agent 13)
