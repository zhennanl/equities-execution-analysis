# Data-Science Integration Map (c-70, 2026-08-05)

*Where established DS/ML frameworks plug into our five-stage
workflow, with the external reference each idea borrows from.
Nothing here overrides the honesty rules: registries lock before
evaluation, nulls get pinned, rules stay interpretable — ML is
added where it grades, sizes, or bounds, not where it decides.*

## The one-line thesis

Our workflow is already a data-science pipeline (hypothesis
registry = pre-registration, clustered permutation = inference,
PIT caches = feature store). The upgrades below adopt the
*named* frameworks practitioners use for exactly our problems,
so each future improvement references a documented method
instead of an invented one.

## Stage-by-stage integration

### Step 1 — add/delete prediction → CALIBRATED CLASSIFICATION

- Recast the funnel verdicts as probabilistic forecasts: rules
  produce the candidate + direction; a thin layer maps features
  (distance-to-cutoff, float, foreign room, ATVR margin,
  frame-robustness) to P(add)/P(delete).
- Grade with proper scoring rules (Brier / log-loss) across the
  44-review PIT history, not hit-rates — a 60% call that misses
  is a *good* forecast if calibrated; binary grading can't see
  that.
- Literature basis: the economics are documented — predictable
  index/ETF rebalancing is front-run profitably (hedge-fund
  outperformance of 0.86%/mo pre-event per the Duke/QuantPedia
  studies; NBER w33554 on the cost of mechanical rebalancing).
  We are building the *prediction layer* that literature assumes
  exists.

### Step 1 verdicts → META-LABELING (Lopez de Prado, AFML ch.3)

- The exact fit for our culture: the RULE ENGINE keeps deciding
  the SIDE (2408 = add candidate — mechanical, citable,
  frame-robust). ML decides only the CONFIDENCE/SIZE — a
  secondary model predicting "will the rule's call be right?"
  from context features.
- Direction stays interpretable for the desk; the learned layer
  only throttles conviction. If the meta-model is useless, the
  rules are unharmed.

### Step 2 — effective-day print → the OPTIVER "TRADING AT THE
### CLOSE" framework

- Optiver's 2023 Kaggle competition is literally our T-day
  problem: predict closing-auction movements from order-book +
  auction-imbalance features (winning stacks: LightGBM/GBDT on
  engineered imbalance features, per-stock MAE evaluation).
- Our mirror: auction_capture.py's 5-sec TWSE MIS snapshots →
  the same feature family (imbalance ratio, matched vs unmatched
  size, reference-price drift over the last minutes) → predict
  final print vs our M1–M4 range mid. First live sample:
  Aug-31.
- Adopt their evaluation grammar too: per-name MAE vs a naive
  baseline, so the model must beat "predict the range mid".

### Step 2 ranges → CONFORMAL PREDICTION

- Our M1∪M3 print ranges are hand-built intervals. Conformal
  prediction gives distribution-free intervals with a coverage
  guarantee: calibrate on the 133 name-event panel, declare 80%
  intervals, then GRADE EMPIRICAL COVERAGE every review (an 80%
  interval that covers 60% is broken; one that covers 99% is
  wastefully wide). This turns "range felt right" into a scored
  property.

### Steps 3–4 outcomes → TRIPLE-BARRIER LABELS (AFML ch.3)

- Replace fixed-horizon T+3 returns with first-barrier-hit
  labels (upper %, lower %, time-out) sized by each name's
  volatility. H16/H17-style reversal claims become path-aware:
  "bounced 8% before dropping" and "dropped then bounced" stop
  being the same label.

### Validation everywhere → PURGED/EMBARGOED CV + PBO (AFML ch.7, 11-12)

- Our clustered-LOO-by-event is a cousin of purged k-fold;
  formalize the EMBARGO: windows from adjacent reviews overlap
  (Nov window touches Feb positioning), so training folds must
  exclude a buffer around test events, not just the test event.
- For the strategy leaderboard (post_event.py): Probability of
  Backtest Overfitting / deflated performance metrics — with
  several strategy variants graded on one history, the winner is
  partly luck; PBO quantifies how much.

### Data layer → the ML4T / MLOps reference architecture

- Stefan Jansen's ML4T repo is the canonical open
  research-to-production layout: data sourcing → feature store →
  walk-forward evaluation → live execution, with an explicit
  "evidence boundary" separating exploration from confirmation
  (our registry-lock rule, independently named).
- MLOps mappings we already half-have, now nameable: sentinels =
  drift detection; atomic caches with PIT discipline = feature
  store; registry docs = experiment tracking; "failures never
  cached" = data-quality gate. Missing piece worth adding:
  per-dataset EXPECTATION CHECKS (row counts, field counts nf,
  value bounds) run at harvest time — the mieu ghost-cache bug
  is exactly the failure class these catch.

## Priority order (proposed)

1. Conformal grading of print ranges (cheap; uses the existing
   panel; live-gradeable Aug-31)
2. Brier-scored calibrated probabilities for Step-1 calls
   (grades the Aug-11 shadow call properly)
3. Embargoed CV adopted into the v5 protocol's OOS rule
4. Optiver-style auction feature model (after first 5-sec
   capture accumulates)
5. Meta-labeling layer + triple-barrier labels (after the
   decade harvest lands and v5 grades)
6. Expectation checks on all harvesters

## References

- Lopez de Prado, *Advances in Financial Machine Learning*
  (Wiley 2018) — purged/embargoed CV, meta-labeling,
  triple-barrier, backtest-overfitting metrics
- Optiver — Trading at the Close (Kaggle 2023):
  https://www.kaggle.com/competitions/optiver-trading-at-the-close
- ETF rebalancing front-running: Duke FinReg Blog (2023),
  QuantPedia summary; NBER w33554 *The Unintended Consequences
  of Rebalancing*
- Stefan Jansen, *Machine Learning for Trading* (code:
  https://github.com/stefan-jansen/machine-learning-for-trading)
- Pavlova & Sikorskaya, *Benchmarking Intensity* (RFS 2023) —
  already the basis of the lambda flow model
