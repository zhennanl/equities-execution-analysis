# Counterfactual Impact Model — Propagator + Sensitivity Bands

*2026-07-09. Motivated by a direct interviewer question (GSET Execution
Solutions): "if we re-run history with a more aggressive strategy, the tape
doesn't reflect the new strategy's impact — how do you model that?" This doc
records the implemented answer and the statistical roadmap that takes the
model toward industry practice.*

## 1. The problem, precisely

A strategy-switch simulation replays historical bars under a counterfactual
policy. Three lies threaten it: (a) fills priced against a tape that never
felt the counterfactual's impact; (b) an aggressive morning that should make
the afternoon more expensive, but doesn't, because the path is frozen;
(c) on a real account's history, the tape already embeds the ORIGINAL
strategy's footprint, so naive overlays double-count where old and new
overlap. The platform already handled (a) as a labeled cost overlay
(Level 1). This build addresses (b) (Level 2) and documents (c).

## 2. What was implemented (`agents/impact_propagator.py`)

**Kernel.** Each simulated fill's instantaneous impact η·σ_d·√(q/ADV) splits
into a permanent fraction (default 40%, never decays — information) and a
temporary fraction (decays exponentially with a half-life, default grid 10
and 30 minutes at 5-min bars — liquidity concession). Signed adverse to the
order's side.

**Causal path perturbation.** perturb(t) = Σ_{fills i, bar_i < t}
[perm_i + temp_i·0.5^((t−bar_i)/t½)]. A fill never perturbs bars at or
before itself; own-slice instantaneous impact is NOT re-charged (that is the
existing Level-1 overlay), so the two compose without double counting.

**Schedule-invariant repricing.** Fill sizes/times come from the raw-tape
simulation; only prices are adjusted — exact for volume/time-driven
schedules, approximate for price-reactive tactics (disclosed).

**Sensitivity bands.** `counterfactual_with_bands()` runs base vs
base-plus-interventions through the same kernels across a grid
(η ∈ {0.3, 0.45, 0.6} × t½ ∈ {2, 6} bars) and reports the DELTA band with a
robustness verdict: sign stable across the grid → conclusion robust to the
impact model; sign flips → "the simulation cannot decide this switch; it
needs a live A/B" — printed verbatim in the UI.

**UI.** Live Trading Session → "Counterfactual impact model" expander,
active once interventions exist. Raw-tape reconciled numbers elsewhere on
the page are untouched; the propagator view is additive.

**Tests** (`tests/test_impact_propagator.py`, 5): exact decay/permanent-floor
arithmetic; causality; buy/sell mirror; end-to-end bands with robust-flag
consistency; monotonicity of feedback in η. Suite: 181 → 186.

## 3. Statistical roadmap — toward industry practice

1. **Calibrate the kernel from the platform's own event studies.** The event
   library already backs out implied η from rebalancing events; extend it to
   fit the permanent/temporary split and the decay half-life by regressing
   post-completion reversion paths (and markout curves) on the kernel's
   functional form (nonlinear least squares). Kernel *shape* selection —
   exponential vs power-law decay — by out-of-sample fit on held-out events.
2. **Bayesian shrinkage instead of a flat grid.** Literature priors
   (Almgren-2005 magnitudes, reversion-study half-lives) updated with own
   events → a posterior over (η, perm_frac, t½). The sensitivity band then
   becomes a credible interval — "the switch saves 4–9 bps with 80%
   posterior probability" — rather than an assumption sweep.
3. **Uncertainty propagation.** Bootstrap the event library (block/by-event)
   → kernel parameter distribution → Monte Carlo the counterfactual → a CI
   on the delta that carries calibration uncertainty, not just grid width.
4. **Sim-to-real validation loop.** Wherever a live A/B exists, regress
   realized deltas on the propagator's predicted deltas: slope ≈ 1 and
   intercept ≈ 0 is the calibration test; the run-library pattern tracks it
   over time. This is what graduates the model from assumption to instrument.
5. **Regime-conditional kernels.** η and t½ vary with volatility/spread
   state — estimate via interactions in the calibration regression; the
   regime agent already classifies the state to condition on.
6. **De-impacting real account history** (the interviewer's subtlest point):
   when the tape embeds the original strategy's own footprint, subtract the
   fitted kernel's estimate of that footprint before adding the new
   strategy's — feasible exactly when (1)–(3) have produced a trusted kernel;
   documented as the dependency chain it is.

## 3b. Registered upgrade (c-72): the AUCTION LEG

The kernel above is continuous-session physics; a closing-call
fill needs its own term. Design registered before building:

- **Wrong model for the close:** √(q/ADV) + forward propagation
  assumes a walked book and a remaining session. A call auction
  is one simultaneous match — impact = shift of the clearing
  price along the aggregate step function (lumpy: zero until a
  price level exhausts, then a tick), and the "temporary"
  component has no afternoon to decay into: it becomes the
  OVERNIGHT revert (measured from the print in
  data/auction_expost.json: adds fade +182 bps, deletes bounce
  +50 bps median at T+1).
- **The deciding variable:** marginal_share = q_yours ÷ expected
  cross. Effective dates: cross = 8–21× ADV (deletes put ~72%
  of day volume through it) → a single desk's slice is
  second-order; below ~5% marginal share, skip the adjustment
  as sub-noise. Normal days: the cross is ~6% of day volume →
  the SAME order is a dominant share; the auction leg is
  mandatory for any schedule that moves size into a non-event
  close.
- **Calibration path:** elasticity slope from the ex-post TCA
  panel — pressure_bps regressed on forced-flow size across the
  80 name-events (a crude aggregate supply-curve slope, from
  our own events); refined per-stock once the Aug-31 5-sec
  captures accumulate indicative-price step functions.
- **Composition rule:** auction fills charge the auction leg
  INSTEAD of the continuous kernel (never both), and propagate
  nothing intraday; their temporary component reverts at T+1
  open/close in multi-day simulations.

## 4. The interview one-liner

"The path now remembers what the simulation did to it — under assumptions we
sweep rather than hide; and when the conclusion doesn't survive the sweep,
the tool says 'run the experiment' instead of pretending."
