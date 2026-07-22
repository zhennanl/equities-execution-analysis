"""N-arm Algo Wheel — blocked strategy comparison with rank-based inference
(gap register I-7 / backlog B6; design: docs/SIMULATOR_INSTITUTIONAL_ASSESSMENT.md P-B).

Real broker wheels randomize comparable orders across strategies because a live
order can only be executed once. This simulator can do strictly better: every
algo runs on EXACTLY the same historical days (Agent 4's daily cost matrix), a
fully blocked design. Inference is therefore rank-based across blocks:

  * Friedman chi-square across k algos x n days (blocks = days) — "are these
    algos distinguishable at all, net of day effects?"
  * Nemenyi post-hoc critical difference on average ranks,
        CD = q_{alpha,k,inf} / sqrt(2) x sqrt( k(k+1) / (6 n) ),
    marking which algos are statistically separable from the rank leader.
  * League table: mean/median cost, dispersion, average rank, win days, and a
    'Separable from best?' verdict per algo.

Honesty notes baked into the output: ranks are within-simulation (same fill
kernel and impact model for every arm — model error is common-mode and largely
cancels); a real wheel adds venue/broker variation this cannot see; with small
n the Nemenyi CD is wide and 'not separable' is the CORRECT reading, not a
failure.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from scipy.stats import friedmanchisquare, studentized_range

MIN_DAYS = 5
MIN_ALGOS = 3


@dataclass
class AlgoWheelResult:
    available: bool
    reason: str = ""
    n_days: int = 0
    n_algos: int = 0
    friedman_chi2: float = None
    friedman_p: float = None
    critical_difference: float = None      # Nemenyi CD on average ranks
    best_algo: str = ""
    league: pd.DataFrame = None            # the league table
    notes: list = field(default_factory=list)


def run_algo_wheel(daily_costs: pd.DataFrame, alpha: float = 0.05) -> AlgoWheelResult:
    """daily_costs: index = date, columns = algo names, values = cost bps
    (lower = better). Rows with any NaN are dropped (blocked design needs
    complete blocks)."""
    df = daily_costs.dropna(axis=0, how="any").copy()
    k, n = df.shape[1], len(df)
    if k < MIN_ALGOS:
        return AlgoWheelResult(False, f"Need >= {MIN_ALGOS} strategies (have {k}).")
    if n < MIN_DAYS:
        return AlgoWheelResult(False, f"Need >= {MIN_DAYS} complete days (have {n}).")

    chi2, p = friedmanchisquare(*[df[c].values for c in df.columns])

    ranks = df.rank(axis=1, method="average")          # 1 = cheapest that day
    avg_rank = ranks.mean(axis=0)

    q = studentized_range.ppf(1.0 - alpha, k, np.inf)
    cd = float(q / np.sqrt(2.0) * np.sqrt(k * (k + 1) / (6.0 * n)))

    best = avg_rank.idxmin()
    league = pd.DataFrame({
        "Algo": df.columns,
        "Mean cost (bps)": df.mean(axis=0).round(2).values,
        "Median cost (bps)": df.median(axis=0).round(2).values,
        "Std (bps)": df.std(axis=0).round(2).values,
        "Avg rank": avg_rank.round(2).values,
        "Win days": (ranks == 1).sum(axis=0).values,
        "Δrank vs best": (avg_rank - avg_rank.min()).round(2).values,
    })
    league["Separable from best?"] = np.where(
        league["Algo"] == best, "— (leader)",
        np.where(league["Δrank vs best"] > cd, "YES (worse, p<%.2f)" % alpha,
                 "not separable at this n"))
    league = league.sort_values("Avg rank").reset_index(drop=True)

    notes = [
        f"Fully blocked design: all {k} strategies simulated on the same {n} days — "
        "stronger pairing than a live randomized wheel achieves.",
        f"Nemenyi critical difference on average ranks: {cd:.2f} (alpha={alpha:.2f}). "
        "Pairs of algos whose average ranks differ by less than this are NOT "
        "statistically separable on this sample — with small n that is the correct "
        "conclusion, not a shortcoming.",
        "Within-simulation comparison: one fill kernel and one impact model for every "
        "arm, so model error is common-mode; a production wheel additionally samples "
        "broker/venue variation this cannot see.",
        "Multiplicity: Nemenyi controls the family-wise error across pairwise "
        "comparisons WITHIN this run. Re-running the wheel across many configs "
        "(sizes/urgencies) multiplies tests — apply a Benjamini-Hochberg screen "
        "on the Friedman p-values across runs before acting on any single one.",
    ]
    if p >= alpha:
        notes.insert(0, f"Friedman p = {p:.3f} >= {alpha:.2f}: the strategies are NOT "
                        "jointly distinguishable on this sample — treat the league "
                        "ordering as descriptive only.")
    return AlgoWheelResult(True, "", n, k, round(float(chi2), 3), round(float(p), 5),
                           round(cd, 3), str(best), league, notes)


# ──────────────────────────────────────────────────────────────────────────
# Condition-adjusted ranking — "ranking defense" (Execution Solutions angle,
# 2026-07-08). The client-wheel question is not "which algo had the lowest
# raw cost" but "which algo is best NET OF THE FLOW IT RECEIVED": a broker
# handed the biggest, most volatile orders ranks poorly raw even when its
# engine is superior. This view puts raw rank and condition-adjusted rank
# side by side, with the adjustment inherited from the fitted cost model's
# A/B-with-controls (dummy coefficients holding size/vol/participation/
# spread fixed).
# ──────────────────────────────────────────────────────────────────────────

def condition_adjusted_ranking(panel: "pd.DataFrame", cost_col: str = "cost_bps",
                               strategy_col: str = "algo") -> dict:
    """Raw vs condition-adjusted algo ranking from a cost panel.

    Returns {"available", "table", "baseline", "note", "movers"} where table
    has: Algo | Raw mean (bps) | Raw rank | Adjusted vs baseline (bps) |
    Adjusted rank | Δ rank | Separable? (dummy t-test at 5%).
    Adjusted cost for the baseline is 0 by construction; for others it is the
    strategy dummy's coefficient — the incremental cost holding conditions
    fixed. On a balanced simulated grid raw and adjusted ranks coincide; on
    unbalanced (client-flow-like) panels they diverge, and the adjusted rank
    is the defensible one.
    """
    from agents.cost_model import ab_test_with_controls
    algos = list(pd.unique(panel[strategy_col]))
    if len(algos) < MIN_ALGOS or len(panel) < 20:
        return {"available": False,
                "reason": f"Need >= {MIN_ALGOS} strategies and >= 20 panel rows."}
    ab = ab_test_with_controls(panel, strategy_col=strategy_col, cost_col=cost_col)
    raw_mean = panel.groupby(strategy_col)[cost_col].mean()

    rows = []
    for a in algos:
        if a == ab.baseline:
            adj, sig = 0.0, "— (baseline)"
        else:
            r = ab.table.loc[a]
            adj = float(r["incremental cost vs baseline (bps)"])
            sig = "YES" if float(r["P>|t|"]) < 0.05 else "not at 5%"
        rows.append({"Algo": a, "Raw mean (bps)": round(float(raw_mean[a]), 2),
                     "Adjusted vs baseline (bps)": round(adj, 2),
                     "Separable from baseline?": sig})
    t = pd.DataFrame(rows)
    t["Raw rank"] = t["Raw mean (bps)"].rank(method="min").astype(int)
    t["Adjusted rank"] = t["Adjusted vs baseline (bps)"].rank(method="min").astype(int)
    t["Δ rank (adj − raw)"] = t["Adjusted rank"] - t["Raw rank"]
    t = t[["Algo", "Raw mean (bps)", "Raw rank", "Adjusted vs baseline (bps)",
           "Adjusted rank", "Δ rank (adj − raw)", "Separable from baseline?"]]
    t = t.sort_values("Adjusted rank").reset_index(drop=True)
    movers = t[t["Δ rank (adj − raw)"] != 0]["Algo"].tolist()
    note = (f"Baseline = {ab.baseline} (cheapest raw). Adjusted column holds "
            f"size/volatility/participation/spread fixed (R²={ab.r2:.2f}, "
            f"n={ab.n}, {ab.cov_type} SEs). Rank moves — {movers if movers else 'none here'} — "
            "are the ranking-defense story: on client wheels, raw league tables "
            "punish whoever receives the hardest flow; the condition-adjusted "
            "rank is the number to bring to that conversation.")
    return {"available": True, "table": t, "baseline": ab.baseline,
            "note": note, "movers": movers}
