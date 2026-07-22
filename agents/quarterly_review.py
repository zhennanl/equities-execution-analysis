"""Quarterly client execution review (QBR) — the Execution Solutions ritual.

Framework (each section = one client-deck page, one function output here):

1. FLOW PROFILE          what the client sent us: orders, algos, markets,
                         size and urgency mix. No judgment yet — the mix IS
                         the context for every number that follows.
2. HEADLINE COSTS        distributions, not means: median/IQR/tails of
                         realized arrival cost, plus model bias
                         (realized − predicted) as the fairness anchor.
3. DECOMPOSITION         by algo / market / size bucket / urgency. A raw
                         league table is shown but NEVER stands alone —
                         difficulty differs across cells.
4. DIFFICULTY-ADJUSTED   predicted-vs-realized residuals put every order on
                         a level field (the pre-trade model absorbs size,
                         spread, vol). Condition-adjusted ranking via the
                         wheel's regression (OVB defense) when the panel
                         supports it.
5. OUTLIER ATTRIBUTION   top-k orders by |cost| and their share of the
                         quarter's total — the client conversation is
                         usually about five orders, not five hundred.
6. TREND & ACTIONS       monthly trend inside the quarter, QoQ vs prior
                         when history exists, and rule-generated
                         recommendations each carrying its supporting
                         number and an honesty caveat.

Statistical house rules: report n everywhere; CIs on means; adjusted (not
raw) ranks are the defensible ones on unbalanced client flow; no verdict on
cells with n below MIN_CELL.

Data source: the run library (agents/desk_pack.record_run) — one row per
executed (simulated) order. `synthesize_demo_quarter` generates a clearly
LABELED synthetic quarter so the page works before a client's library
accumulates.
"""
from __future__ import annotations

import datetime as _dt
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

MIN_CELL = 5           # no per-cell verdicts below this n
MIN_ORDERS = 20        # no review below this
TOP_K_OUTLIERS = 10
SIZE_BUCKETS = ((0.0, 1.0, "<1% ADV"), (1.0, 5.0, "1–5% ADV"),
                (5.0, 10.0, "5–10% ADV"), (10.0, np.inf, ">10% ADV"))
CI_Z = 1.96


# ── helpers ────────────────────────────────────────────────────────────────

def _quarter_of(ts: pd.Timestamp) -> str:
    return f"{ts.year}Q{(ts.month - 1) // 3 + 1}"


def _size_bucket(pct: float) -> str:
    for lo, hi, name in SIZE_BUCKETS:
        if lo <= pct < hi:
            return name
    return SIZE_BUCKETS[-1][2]


def _dist_row(g: pd.Series) -> dict:
    v = g.dropna().to_numpy(dtype=float)
    n = len(v)
    out = {"n": n, "mean_bps": np.nan, "median_bps": np.nan, "p25": np.nan,
           "p75": np.nan, "ci_lo": np.nan, "ci_hi": np.nan}
    if n == 0:
        return out
    se = v.std(ddof=1) / np.sqrt(n) if n > 1 else np.nan
    out.update(mean_bps=round(float(v.mean()), 2),
               median_bps=round(float(np.median(v)), 2),
               p25=round(float(np.percentile(v, 25)), 2),
               p75=round(float(np.percentile(v, 75)), 2))
    if np.isfinite(se):
        out["ci_lo"] = round(float(v.mean() - CI_Z * se), 2)
        out["ci_hi"] = round(float(v.mean() + CI_Z * se), 2)
    return out


def _breakdown(df: pd.DataFrame, by: str) -> pd.DataFrame:
    rows = []
    for key, g in df.groupby(by, sort=False):
        r = {"group": key, **_dist_row(g["realized_bps"])}
        scored = g.dropna(subset=["realized_bps", "predicted_bps"])
        r["bias_bps"] = (round(float((scored["realized_bps"]
                                      - scored["predicted_bps"]).mean()), 2)
                         if len(scored) else np.nan)
        r["verdict_ok"] = r["n"] >= MIN_CELL
        rows.append(r)
    out = pd.DataFrame(rows)
    return out.sort_values("mean_bps", na_position="last").reset_index(drop=True)


# ── result container ───────────────────────────────────────────────────────

@dataclass
class QuarterlyReview:
    available: bool
    reason: str = ""
    quarter: str = ""
    is_synthetic: bool = False
    n_orders: int = 0
    n_scored: int = 0
    flow_profile: dict = field(default_factory=dict)     # mixes by algo/market/size/urgency (%)
    headline: dict = field(default_factory=dict)         # dist + bias + hit rate
    by_algo: pd.DataFrame | None = None
    by_market: pd.DataFrame | None = None
    by_bucket: pd.DataFrame | None = None
    by_urgency: pd.DataFrame | None = None
    panel: pd.DataFrame | None = None                    # per-order, for scatter/residuals
    adjusted_ranking: dict = field(default_factory=dict) # from algo_wheel, or unavailable
    outliers: pd.DataFrame | None = None
    outlier_share: float = 0.0                           # top-k share of gross |cost|
    monthly_trend: pd.DataFrame | None = None
    prior_quarter: dict = field(default_factory=dict)    # QoQ deltas if history exists
    recommendations: list = field(default_factory=list)
    caveats: list = field(default_factory=list)


# ── core ───────────────────────────────────────────────────────────────────

def build_quarterly_review(runs: list | None = None, quarter: str | None = None,
                           is_synthetic: bool = False) -> QuarterlyReview:
    """Aggregate the run library into the six-section QBR. `quarter` like
    "2026Q2"; defaults to the latest quarter present in the data."""
    if runs is None:
        from agents.desk_pack import load_runs
        runs = load_runs()
    df = pd.DataFrame(runs)
    if df.empty or "sim_day" not in df.columns:
        return QuarterlyReview(False, reason="Run library is empty — execute "
                               "some orders on Page 1 (or load the demo quarter).")
    df["date"] = pd.to_datetime(df["sim_day"], errors="coerce")
    df = df.dropna(subset=["date"])
    df["quarter"] = df["date"].map(_quarter_of)
    if quarter is None:
        quarter = str(df.sort_values("date")["quarter"].iloc[-1])
    q = df[df["quarter"] == quarter].copy()
    if len(q) < MIN_ORDERS:
        return QuarterlyReview(False, quarter=quarter,
                               reason=f"Only {len(q)} orders in {quarter}; "
                               f"need >= {MIN_ORDERS} for a defensible review.")
    for c in ("realized_bps", "predicted_bps", "order_pct_adv"):
        q[c] = pd.to_numeric(q.get(c), errors="coerce")
    q["size_bucket"] = q["order_pct_adv"].fillna(0.0).map(_size_bucket)
    q["residual_bps"] = q["realized_bps"] - q["predicted_bps"]
    q["month"] = q["date"].dt.strftime("%Y-%m")
    scored = q.dropna(subset=["realized_bps", "predicted_bps"])

    # 1) flow profile ------------------------------------------------------
    def _mix(col):
        vc = q[col].value_counts(normalize=True)
        return {str(k): round(float(v) * 100, 1) for k, v in vc.items()}
    profile = {"algo_mix_pct": _mix("algo"), "market_mix_pct": _mix("market"),
               "size_mix_pct": _mix("size_bucket"), "urgency_mix_pct": _mix("urgency"),
               "side_mix_pct": _mix("side"),
               "median_order_pct_adv": round(float(q["order_pct_adv"].median()), 2)}

    # 2) headline ----------------------------------------------------------
    head = _dist_row(q["realized_bps"])
    if len(scored):
        head["bias_bps"] = round(float(scored["residual_bps"].mean()), 2)
        head["mae_vs_model_bps"] = round(float(scored["residual_bps"].abs().mean()), 2)
        within = (scored["residual_bps"].abs()
                  <= scored["predicted_bps"].abs().clip(lower=5.0)).mean()
        head["hit_rate_within_model_band"] = round(float(within) * 100, 1)

    # 3) decomposition -----------------------------------------------------
    by_algo = _breakdown(q, "algo")
    by_market = _breakdown(q, "market")
    by_bucket = _breakdown(q, "size_bucket")
    by_urgency = _breakdown(q, "urgency")

    # 4) difficulty-adjusted ranking (wheel regression, OVB defense) -------
    adj = _adjusted_ranking(scored)

    # 5) outlier attribution ----------------------------------------------
    ranked = q.dropna(subset=["realized_bps"]).copy()
    ranked["abs_bps"] = ranked["realized_bps"].abs()
    gross = float(ranked["abs_bps"].sum())
    top = ranked.nlargest(TOP_K_OUTLIERS, "abs_bps")[
        ["ticker", "market", "side", "algo", "urgency", "order_pct_adv",
         "sim_day", "predicted_bps", "realized_bps"]].reset_index(drop=True)
    share = float(top["realized_bps"].abs().sum() / gross) if gross > 0 else 0.0

    # 6) trend + prior quarter + recommendations ---------------------------
    trend = (q.groupby("month")["realized_bps"]
             .agg(n="count", mean_bps="mean", median_bps="median")
             .round(2).reset_index())
    prior = {}
    qs = sorted(df["quarter"].unique())
    if quarter in qs and qs.index(quarter) > 0:
        pq = qs[qs.index(quarter) - 1]
        pv = df[df["quarter"] == pq]["realized_bps"].dropna()
        if len(pv) >= MIN_CELL:
            prior = {"quarter": pq, "n": int(len(pv)),
                     "mean_bps": round(float(pv.mean()), 2),
                     "delta_mean_bps": round(head["mean_bps"] - float(pv.mean()), 2)}

    recs, cavs = _recommendations(q, scored, by_algo, by_bucket, by_urgency,
                                  head, adj)
    if is_synthetic:
        cavs.insert(0, "SYNTHETIC DEMO QUARTER — generated data, labeled as "
                    "such. The workflow, not the numbers, is the exhibit.")
    cavs.append("Costs are simulated arrival slippage on historical bars; a "
                "production QBR uses booked fills and client-agreed benchmarks.")
    cavs.append(f"No verdict rendered on any cell with n < {MIN_CELL}; raw "
                "league tables never stand alone (difficulty differs by cell).")

    return QuarterlyReview(True, quarter=quarter, is_synthetic=is_synthetic,
                           n_orders=int(len(q)), n_scored=int(len(scored)),
                           flow_profile=profile, headline=head,
                           by_algo=by_algo, by_market=by_market,
                           by_bucket=by_bucket, by_urgency=by_urgency,
                           panel=q, adjusted_ranking=adj, outliers=top,
                           outlier_share=round(share, 3), monthly_trend=trend,
                           prior_quarter=prior, recommendations=recs,
                           caveats=cavs)


def _adjusted_ranking(scored: pd.DataFrame) -> dict:
    """Condition-adjusted algo ranking on the QBR panel: cost ~ algo dummies
    + sqrt(size) + urgency + market fixed effects (via cost_model's
    regression A/B). The run library doesn't carry spread/vol per order, so
    the control set is the subset it CAN support — disclosed."""
    out = {"available": False, "reason": "need >= 20 scored orders and >= 3 algos"}
    panel = scored.rename(columns={"realized_bps": "cost_bps"}).copy()
    if len(panel) < 20 or panel["algo"].nunique() < 3:
        return out
    try:
        from agents.cost_model import ab_test_with_controls
        panel["sqrt_size_pct_adv"] = np.sqrt(panel["order_pct_adv"].clip(lower=0.01))
        panel["urgency_num"] = panel["urgency"].map(
            {"Low": 0.0, "Medium": 1.0, "High": 2.0}).fillna(1.0)
        for m in panel["market"].unique()[1:]:
            panel[f"mkt_{m}"] = (panel["market"] == m).astype(float)
        controls = ["sqrt_size_pct_adv", "urgency_num"] + \
                   [c for c in panel.columns if c.startswith("mkt_")]
        ab = ab_test_with_controls(panel, strategy_col="algo",
                                   cost_col="cost_bps", controls=tuple(controls))
        raw = panel.groupby("algo")["cost_bps"].mean()
        rows = []
        for a_ in raw.index:
            if a_ == ab.baseline:
                adj_c, pv = 0.0, np.nan
            else:
                r = ab.table.loc[a_]
                adj_c = float(r["incremental cost vs baseline (bps)"])
                pv = float(r["P>|t|"])
            rows.append({"Algo": a_, "Raw mean (bps)": round(float(raw[a_]), 2),
                         "Adjusted vs baseline (bps)": round(adj_c, 2),
                         "Separable at 5%?": ("— (baseline)" if a_ == ab.baseline
                                              else ("YES" if pv < 0.05 else "no"))})
        t = pd.DataFrame(rows)
        t["Raw rank"] = t["Raw mean (bps)"].rank(method="min").astype(int)
        t["Adj rank"] = t["Adjusted vs baseline (bps)"].rank(method="min").astype(int)
        movers = ", ".join(
            f"{row['Algo']} {row['Raw rank']}\u2192{row['Adj rank']}"
            for _, row in t.iterrows() if row["Raw rank"] != row["Adj rank"])
        return {"available": True, "table": t, "baseline": ab.baseline,
                "movers": movers,
                "note": "Controls: sqrt(size %ADV), urgency, market FEs — the "
                        "set the run library supports (no per-order spread/vol). "
                        "Adjusted rank is the defensible one on unbalanced flow."}
    except Exception as e:
        return {"available": False, "reason": f"ranking skipped: {e}"}


def _recommendations(q, scored, by_algo, by_bucket, by_urgency, head, adj):
    """Rule-generated action items, each carrying its supporting number.
    Rules fire only on cells with n >= MIN_CELL."""
    recs, cavs = [], []
    ok = by_algo[by_algo["verdict_ok"]]
    if len(ok) >= 2:
        best, worst = ok.iloc[0], ok.iloc[-1]
        gap = worst["mean_bps"] - best["mean_bps"]
        overlap = worst["ci_lo"] <= best["ci_hi"]
        if gap > 5.0 and not overlap:
            recs.append(f"Review wheel allocation to {worst['group']}: mean "
                        f"{worst['mean_bps']:+.1f} bps vs {best['group']} "
                        f"{best['mean_bps']:+.1f} (n={worst['n']}/{best['n']}, "
                        "95% CIs do not overlap). Confirm on the adjusted "
                        "ranking before acting — raw gaps can be mix.")
        elif gap > 5.0:
            cavs.append(f"Raw algo gap of {gap:.1f} bps ({worst['group']} vs "
                        f"{best['group']}) is NOT separable at 95% — more "
                        "data or a designed wheel A/B before reallocating.")
    if isinstance(adj, dict) and adj.get("available") and adj.get("movers"):
        recs.append(f"Condition-adjusted ranking moves: {adj['movers']} — "
                    "discuss mix (who got the hard orders) before the raw table.")
    big = by_bucket[by_bucket["group"] == ">10% ADV"]
    if len(big) and big.iloc[0]["verdict_ok"] and big.iloc[0]["mean_bps"] > head["mean_bps"] * 1.5:
        recs.append(f">10% ADV orders averaged {big.iloc[0]['mean_bps']:+.1f} bps "
                    f"vs book average {head['mean_bps']:+.1f} (n={big.iloc[0]['n']}): "
                    "candidates for multi-day scheduling or dark-patient routing.")
    if abs(head.get("bias_bps", 0.0)) > 5.0:
        d = "under" if head["bias_bps"] > 0 else "over"
        recs.append(f"Pre-trade model {d}-predicts cost by {abs(head['bias_bps']):.1f} "
                    f"bps on average (n={len(scored)}): recalibrate impact "
                    "coefficients before next quarter's expectations are set.")
    hi = by_urgency[by_urgency["group"] == "High"]
    lo = by_urgency[by_urgency["group"] == "Low"]
    if len(hi) and len(lo) and hi.iloc[0]["verdict_ok"] and lo.iloc[0]["verdict_ok"]:
        prem = hi.iloc[0]["mean_bps"] - lo.iloc[0]["mean_bps"]
        if prem > 10.0:
            recs.append(f"High-urgency premium is {prem:.1f} bps over Low "
                        f"(n={hi.iloc[0]['n']}/{lo.iloc[0]['n']}): quantify which "
                        "orders truly needed the urgency — this is the "
                        "cheapest bps in the book.")
    if not recs:
        recs.append("No rule-based action items fired this quarter — costs in "
                    "line with model and no separable algo gaps. Watch items "
                    "carried in caveats.")
    return recs, cavs


# ── labeled synthetic quarter (demo before a library accumulates) ─────────

def synthesize_demo_quarter(quarter: str = "2026Q2", n: int = 180,
                            seed: int = 42) -> list:
    """Generate a synthetic but structurally realistic quarter of run-library
    rows: sqrt-law expected cost + urgency/market effects + heavy-tailed
    noise + a genuinely worse algo and a size-punished bucket, so every QBR
    section has something honest to find. CLEARLY LABELED synthetic."""
    rng = np.random.default_rng(seed)
    y, qn = int(quarter[:4]), int(quarter[-1])
    days = pd.bdate_range(f"{y}-{3 * qn - 2:02d}-01", periods=64)[:62]
    algos = ["VWAP", "TWAP", "POV", "IS", "LIQ"]
    algo_edge = {"VWAP": 0.0, "TWAP": 1.5, "POV": 0.5, "IS": -1.0, "LIQ": 8.0}
    markets = ["US", "Japan", "Hong Kong", "Taiwan (TWSE)", "Australia"]
    mkt_spread = {"US": 3.0, "Japan": 5.0, "Hong Kong": 9.0,
                  "Taiwan (TWSE)": 12.0, "Australia": 7.0}
    urgencies = ["Low", "Medium", "High"]
    urg_add = {"Low": 0.0, "Medium": 3.0, "High": 12.0}
    tickers = [f"SYN{i:02d}" for i in range(14)]
    rows = []
    for _ in range(n):
        algo = str(rng.choice(algos, p=[0.35, 0.15, 0.2, 0.2, 0.1]))
        mkt = str(rng.choice(markets, p=[0.3, 0.25, 0.2, 0.15, 0.1]))
        urg = str(rng.choice(urgencies, p=[0.45, 0.4, 0.15]))
        pct = float(np.round(np.exp(rng.normal(1.0, 1.0)), 2))     # lognormal %ADV
        expected = 0.9 * mkt_spread[mkt] * np.sqrt(max(pct, 0.05)) + urg_add[urg]
        realized = (expected + algo_edge[algo]
                    + rng.standard_t(4) * (3.0 + 0.8 * np.sqrt(pct)))
        if pct > 10:
            realized += rng.exponential(6.0)                        # size pain
        rows.append({"ticker": str(rng.choice(tickers)), "market": mkt,
                     "side": str(rng.choice(["Buy", "Sell"])),
                     "order_pct_adv": pct, "urgency": urg, "algo": algo,
                     "sim_day": str(pd.Timestamp(rng.choice(days)).date()),
                     "predicted_bps": round(float(expected), 2),
                     "realized_bps": round(float(realized), 2),
                     "recorded_at": _dt.datetime.now(_dt.timezone.utc)
                                        .isoformat(timespec="seconds"),
                     "synthetic": True})
    return rows
