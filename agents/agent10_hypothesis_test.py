"""
Agent 10: Hypothesis Testing on Execution Parameters

Answers "is Configuration A actually significantly better than Configuration B,
or does it just look lower on average" -- the question a real algo-wheel /
TCA regression is built to answer, adapted to this platform's data (see the
module docstring in agent3_algo_simulation.py for why: no live routing engine,
no real order flow to randomize across).

Methodology -- paired backtest, not a live randomized trial:
  Real desks can't send the same order through two algos at once, so live A/B
  testing (algo wheels on GSET/REDIPlus/EMSX, or vendor products like BestEx
  Research's wheel) works by randomizing MANY different orders across arms
  over weeks/months and regression-adjusting for order size/vol/spread. That
  isn't available here (this platform simulates hypothetical orders against
  historical bars, it doesn't route live flow). What IS available, and what
  quant desks use for a faster read, is a PAIRED backtest: replay the exact
  same historical days under both configurations, so the market-condition
  noise (the price path) is identical across both arms and only the
  configuration differs. That turns the comparison into a classic paired-
  sample problem -- paired t-test as the primary test, Wilcoxon signed-rank
  as a non-parametric robustness check (impact-cost distributions are known
  to be fat-tailed, Almgren et al. 2005), and a bootstrap confidence interval
  on the mean difference since day-count samples are often small.

Fast path vs. slow path:
  If a configuration's (urgency, order_pct_adv) exactly matches what Agent 4
  already computed for the current pipeline run, its daily metric series is
  read directly off Agent 4's existing daily_costs/daily_slips/daily_impact/
  daily_opp/daily_fills frames -- zero extra simulation. Otherwise this module
  re-simulates that one configuration, at its own urgency/size, across
  EXACTLY the same historical day set Agent 4 used (via
  agent4._build_valid_days), so both arms of the test are still paired on
  the same days even when a fresh simulation was needed for one or both.

Scope note: this tests ONE pair of configurations per run (click button, get
a verdict). An "all algos pairwise, Holm-Bonferroni corrected" matrix mode
was discussed as a natural follow-on (it directly answers "is my Agent 5
recommendation actually significantly better than the runner-up") but isn't
built in this pass.
"""

import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from scipy import stats as _stats

from agents.agent1_market_data import MarketData
from agents.agent4_performance_comparison import PerformanceComparison, _build_valid_days, _sim_day_all

# metric label -> (PerformanceComparison field name, index into _sim_day_all's
# per-algo tuple (slip, mi, opp, total, fill))
METRIC_MAP = {
    "Total Cost (bps)":       ("daily_costs",  3),
    "Slippage (bps)":         ("daily_slips",  0),
    "Market Impact (bps)":    ("daily_impact", 1),
    "Opportunity Cost (bps)": ("daily_opp",    2),
    "Fill Rate (%)":          ("daily_fills",  4),
}

ALTERNATIVES = {
    "Two-sided (A ≠ B)": "two-sided",
    "A < B": "less",
    "A > B": "greater",
}

MIN_DAYS_FOR_RELIABLE_T = 20
N_BOOTSTRAP = 5000


@dataclass
class HypothesisTestResult:
    available: bool
    reason: str = ""
    metric: str = ""
    alternative: str = ""
    alpha: float = 0.05
    label_a: str = ""
    label_b: str = ""
    note_a: str = ""
    note_b: str = ""
    n_days: int = 0
    mean_diff: float = 0.0          # mean(A - B)
    median_diff: float = 0.0
    ci_low: float = 0.0             # 95% bootstrap CI on mean(A-B), always two-sided regardless of `alternative`
    ci_high: float = 0.0
    t_stat: float = 0.0
    p_value_t: float = None
    wilcoxon_stat: float = None
    p_value_wilcoxon: float = None
    cohens_d: float = 0.0
    reject_null: bool = False
    verdict_text: str = ""
    caveats: list = field(default_factory=list)
    daily_diffs: pd.Series = None
    series_a: pd.Series = None
    series_b: pd.Series = None


def _config_label(config: dict) -> str:
    return f"{config['algo']} / {config['urgency']} / {config['order_pct_adv']:g}% ADV"


def _get_daily_series(market_data: MarketData, comp: PerformanceComparison,
                      ctx_order_pct_adv: float, ctx_urgency: str,
                      config: dict, comp_field: str, tuple_idx: int):
    """
    Returns (pd.Series indexed by date, provenance note). Reuses Agent 4's
    already-computed daily frame when the config matches the current
    pipeline's (urgency, order_pct_adv) exactly (fast path); otherwise
    re-simulates that one configuration across the same valid_days Agent 4
    used (slow path), so both arms stay paired on the same historical days.
    """
    same_urgency = config["urgency"] == ctx_urgency
    same_size = abs(config["order_pct_adv"] - ctx_order_pct_adv) < 1e-9
    if same_urgency and same_size:
        df = getattr(comp, comp_field)
        if config["algo"] in df.columns:
            return df[config["algo"]].copy(), "reused Agent 4's existing multi-day comparison (no re-simulation needed)"

    valid_days = _build_valid_days(market_data)
    order_shares = market_data.adv_shares * (config["order_pct_adv"] / 100)
    vals = {}
    for d, day, hist_curve in valid_days:
        res = _sim_day_all(day, order_shares, config["urgency"], market_data.adv_shares,
                           market_data.realized_vol_ann, hist_curve=hist_curve)
        if res is None:
            continue
        vals[d.date()] = res[config["algo"]][tuple_idx]
    note = (f"re-simulated at {config['order_pct_adv']:g}% ADV / {config['urgency']} urgency "
           f"across the same {len(vals)} historical days Agent 4 used")
    return pd.Series(vals), note


def run_hypothesis_test(market_data: MarketData, comp: PerformanceComparison,
                        ctx_order_pct_adv: float, ctx_urgency: str,
                        config_a: dict, config_b: dict, metric: str,
                        alternative: str = "Two-sided (A ≠ B)", alpha: float = 0.05,
                        log=None) -> HypothesisTestResult:
    def _log(msg):
        if log: log(msg)

    label_a, label_b = _config_label(config_a), _config_label(config_b)

    if metric not in METRIC_MAP:
        return HypothesisTestResult(available=False, reason=f"Unknown metric '{metric}'.",
                                    metric=metric, label_a=label_a, label_b=label_b)
    comp_field, tuple_idx = METRIC_MAP[metric]

    series_a, note_a = _get_daily_series(market_data, comp, ctx_order_pct_adv, ctx_urgency,
                                         config_a, comp_field, tuple_idx)
    series_b, note_b = _get_daily_series(market_data, comp, ctx_order_pct_adv, ctx_urgency,
                                         config_b, comp_field, tuple_idx)

    paired = pd.concat([series_a.rename("a"), series_b.rename("b")], axis=1, join="inner").dropna()
    n = len(paired)
    if n < 2:
        return HypothesisTestResult(
            available=False,
            reason=f"Only {n} paired historical day(s) available for both configurations -- need at least 2.",
            metric=metric, label_a=label_a, label_b=label_b, note_a=note_a, note_b=note_b, n_days=n,
        )

    a_vals, b_vals = paired["a"].values, paired["b"].values
    diffs = a_vals - b_vals
    mean_diff   = float(np.mean(diffs))
    median_diff = float(np.median(diffs))
    std_diff    = float(np.std(diffs, ddof=1)) if n > 1 else 0.0

    scipy_alt = ALTERNATIVES.get(alternative, "two-sided")

    t_stat, p_t = _stats.ttest_rel(a_vals, b_vals, alternative=scipy_alt)
    t_stat, p_t = float(t_stat), float(p_t)

    w_stat, p_w = None, None
    try:
        w_stat, p_w = _stats.wilcoxon(a_vals, b_vals, alternative=scipy_alt)
        w_stat, p_w = float(w_stat), float(p_w)
    except ValueError:
        pass  # e.g. all paired differences are exactly zero, or n too small

    # Bootstrap CI on the mean difference -- always a 95% two-sided interval
    # regardless of the chosen alternative (a CI describes magnitude/direction
    # of the effect; the alternative only governs the accept/reject rule).
    rng = np.random.RandomState(42)
    idx = np.arange(n)
    boot_means = np.empty(N_BOOTSTRAP)
    for i in range(N_BOOTSTRAP):
        samp = rng.choice(idx, size=n, replace=True)
        boot_means[i] = diffs[samp].mean()
    ci_low, ci_high = (float(np.percentile(boot_means, 2.5)), float(np.percentile(boot_means, 97.5)))

    cohens_d = (mean_diff / std_diff) if std_diff > 1e-12 else 0.0
    reject_null = p_t < alpha

    caveats = [
        f"Paired backtest across the same {n} historical trading day(s) for both configurations -- "
        "not a live randomized algo-wheel A/B test (real desks can't route one order through two algos "
        "at once; this instead replays identical historical bars under each configuration so market-"
        "condition noise is held constant across both arms).",
        "Wilcoxon signed-rank test shown as a non-parametric robustness check alongside the paired "
        "t-test, since impact-cost distributions are known to be fat-tailed (Almgren et al. 2005) "
        "rather than symmetric-Gaussian.",
    ]
    if n < MIN_DAYS_FOR_RELIABLE_T:
        caveats.append(
            f"Small sample (n={n} day(s)) -- the paired t-test's normal-approximation may be unreliable "
            "below ~20 days; weight the Wilcoxon result and the bootstrap CI more heavily than the "
            "t-test p-value alone."
        )
    if p_w is None:
        caveats.append("Wilcoxon signed-rank test unavailable for this pair (e.g. identical paired "
                       "differences every day).")
    if metric == "Fill Rate (%)":
        caveats.append("For Fill Rate, HIGHER is better -- a negative mean difference (A-B) means "
                       "Configuration A filled LESS than Configuration B, the opposite of the cost metrics "
                       "above where negative means A was cheaper.")

    unit = "pp" if metric == "Fill Rate (%)" else "bps"
    disp_mean = mean_diff * 100 if metric == "Fill Rate (%)" else mean_diff
    disp_ci_low = ci_low * 100 if metric == "Fill Rate (%)" else ci_low
    disp_ci_high = ci_high * 100 if metric == "Fill Rate (%)" else ci_high
    direction = "lower" if mean_diff < 0 else "higher"

    verdict_text = (
        f"{'Reject' if reject_null else 'Fail to reject'} H0 at α={alpha:g}: "
        f"[{label_a}]'s {metric} is on average {abs(disp_mean):.2f} {unit} {direction} than [{label_b}] "
        f"across {n} paired historical day(s) (95% CI [{disp_ci_low:+.2f}, {disp_ci_high:+.2f}] {unit}), "
        f"p={p_t:.4f} (paired t-test)"
        + (f", p={p_w:.4f} (Wilcoxon)" if p_w is not None else "") + "."
    )

    _log(f"Hypothesis test [{label_a}] vs [{label_b}] on {metric}: mean_diff={mean_diff:.2f}, "
        f"p_t={p_t:.4f}, reject_null={reject_null}")

    return HypothesisTestResult(
        available=True, metric=metric, alternative=alternative, alpha=alpha,
        label_a=label_a, label_b=label_b, note_a=note_a, note_b=note_b, n_days=n,
        mean_diff=mean_diff, median_diff=median_diff, ci_low=ci_low, ci_high=ci_high,
        t_stat=t_stat, p_value_t=p_t, wilcoxon_stat=w_stat, p_value_wilcoxon=p_w,
        cohens_d=cohens_d, reject_null=reject_null, verdict_text=verdict_text, caveats=caveats,
        daily_diffs=pd.Series(diffs, index=paired.index), series_a=paired["a"], series_b=paired["b"],
    )
