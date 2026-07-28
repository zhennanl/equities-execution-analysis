"""Historical event-flow study — how MSCI/FTSE Asia rebalance events
actually traded, measured on real data (session 7c).

Three questions, three functions:

    summarize_event     ONE event-name: how did flow build into the
                        effective date and what happened at/after it —
                        T-day volume multiple, pre-positioning excess
                        volume (ADV-days between announcement and T-1),
                        CAR drift into T, the T-day move, and the
                        post-event reversal fraction.
    aggregate_study     MANY event-names: the adds-vs-deletes trading
                        guide a desk actually uses (medians + IQRs, the
                        metrics that set MOC sizing and pre-position vs
                        post-complete decisions).
    grade_strategies    execution quality vs the ACTUAL tape: run the
                        S1-S4 strategy set on the realized path (eta=0 —
                        real prices, no modeled impact double-count),
                        find the realized-optimal, and score the regret
                        of the rule we recommended ex ante (6z: adds ->
                        S3 post-effective, deletes -> S1 MOC).

All functions consume the standard EventStudyResult-shaped object, so
they test offline on synthetic paths and run identically on real ones.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

POST_REVERSAL_DAYS = 5


def _at(es, rel):
    r = np.asarray(es.rel_days)
    idx = np.where(r == rel)[0]
    return int(idx[0]) if len(idx) else None


def summarize_event(es, side: str, ann_rel: int = -9,
                    label: str = "") -> dict:
    """Flow metrics for one event name. `side` = index flow direction
    ('Buy' for adds, 'Sell' for deletes). ann_rel = announcement day in
    rel-days (default -9 ~= two weeks of trading days)."""
    rel = np.asarray(es.rel_days)
    ab = np.asarray(es.ab_vol, dtype=float)
    car = np.asarray(es.car, dtype=float)
    px = np.asarray(es.norm_price, dtype=float)
    iT = _at(es, 0)
    if iT is None:
        return {"available": False, "reason": "T not in window", "label": label}
    pre = (rel >= ann_rel) & (rel < 0)
    post = (rel > 0) & (rel <= POST_REVERSAL_DAYS)
    t_mult = float(ab[iT])
    pre_excess = float(np.clip(ab[pre] - 1.0, 0, None).sum())
    car_drift = float(car[iT - 1] - car[pre.argmax()]) if iT > 0 else np.nan
    t_ret = float(px[iT] / px[iT - 1] - 1.0) if iT > 0 else np.nan
    # reversal: how much of the announcement->T CAR gives back by T+5
    total_move = float(car[iT] - car[pre.argmax()])
    post_move = float(car[post][-1] - car[iT]) if post.any() else np.nan
    reversal_frac = (float(-post_move / total_move)
                     if np.isfinite(post_move) and abs(total_move) > 1e-4
                     else np.nan)
    return {"available": True, "label": label, "side": side,
            "t_day_volume_multiple": round(t_mult, 2),
            "pre_excess_adv_days": round(pre_excess, 2),
            "car_drift_to_T_pct": round(car_drift * 100, 2),
            "t_day_return_pct": round(t_ret * 100, 2),
            "post5_move_pct": (round(post_move * 100, 2)
                               if np.isfinite(post_move) else None),
            "reversal_frac": (round(reversal_frac, 2)
                              if np.isfinite(reversal_frac) else None)}


def aggregate_study(rows: list) -> pd.DataFrame:
    """The trading guide: per side, median [IQR] of every metric."""
    df = pd.DataFrame([r for r in rows if r.get("available")])
    if df.empty:
        return df
    out = []
    metrics = ["t_day_volume_multiple", "pre_excess_adv_days",
               "car_drift_to_T_pct", "t_day_return_pct", "reversal_frac"]
    for side, g in df.groupby("side"):
        row = {"side": side, "n": len(g)}
        for m in metrics:
            v = pd.to_numeric(g[m], errors="coerce").dropna()
            if len(v):
                row[m] = (f"{v.median():.2f} "
                          f"[{v.quantile(.25):.2f}, {v.quantile(.75):.2f}]")
        out.append(row)
    return pd.DataFrame(out)


RULE_PICKS = {"Buy": "S3", "Sell": "S1"}     # the 6z ex-ante recommendation


def grade_strategies(es, side: str, order_pct_adv: float = 100.0) -> dict:
    """Execution quality on the ACTUAL path: realized cost of each S1-S4
    strategy (eta=0: real prices carry the crowding; modeled impact would
    double-count it), the realized-optimal, and the regret of the ex-ante
    rule pick."""
    from agents.agent14_rebalance_strategist import analyze_strategies
    ana = analyze_strategies(es, side=side, order_pct_adv=order_pct_adv,
                             eta=0.0)
    fr = ana.frontier.copy()
    fr["S"] = fr["Strategy"].str.split().str[0]
    best = fr.sort_values("Cost vs decision (bps)").iloc[0]
    pick = RULE_PICKS.get(side, "S1")
    ours = fr[fr["S"] == pick]
    if ours.empty:                          # e.g. S3 unavailable (window cut)
        ours = fr[fr["S"] == "S1"]
        pick = "S1 (fallback)"
    ours = ours.iloc[0]
    return {"realized_best": str(best["S"]),
            "best_cost_bps": round(float(best["Cost vs decision (bps)"]), 1),
            "our_rule": pick,
            "our_cost_bps": round(float(ours["Cost vs decision (bps)"]), 1),
            "regret_bps": round(float(ours["Cost vs decision (bps)"]
                                      - best["Cost vs decision (bps)"]), 1),
            "our_tracking_bps": round(float(ours["|Tracking diff| (bps)"]), 1),
            "frontier": fr[["S", "Cost vs decision (bps)",
                            "|Tracking diff| (bps)"]]}


def close_auction_share(intraday_t_day: pd.DataFrame,
                        last_bars: int = 1) -> float:
    """Share of T-day volume in the closing bar(s) — real MOC capacity."""
    v = intraday_t_day["Volume"].to_numpy(dtype=float)
    return float(v[-last_bars:].sum() / v.sum()) if v.sum() > 0 else np.nan


# ── the refined, history-conditioned rule (FITTED on the 2026 Q2 sample —
#    21 names, 3 review cycles, one momentum quarter; validate next cycle
#    before trusting out-of-sample) ─────────────────────────────────────────

def refined_rule(side: str, provider: str, drift_pct: float,
                 momentum_threshold: float = 5.0,
                 trough_threshold: float = -3.0) -> str:
    """What the real 2026-Q2 tape says, conditioned on the two metrics
    that separated winners from losers:

    SELLS: MSCI deletions realized their pressure BEFORE T (median drift
    -4.3%) and the effective close printed near the trough — dumping 100%
    MOC sold the low. If the name is already down > |trough_threshold|
    into T (or it's an MSCI Standard deletion, where median T-mult 16x
    says the crowd sells with you), split: S3 (partial MOC + post-
    effective completion into the bounce). FTSE tradable-index deletions
    (milder 5.5x prints, less pre-realization) stayed S1-optimal.

    BUYS: in a momentum tape (drift > +momentum_threshold), waiting cost
    real money — every 2026-Q2 add kept running and S4/S2 front-loading
    won. Shift earlier IF the client's tracking tolerance allows; S3
    remains the tolerance-safe default in a flat tape."""
    if side == "Sell":
        if provider == "MSCI" or drift_pct <= trough_threshold:
            return "S3"
        return "S1"
    # Buy
    if drift_pct >= momentum_threshold:
        return "S4"          # subject to the client's tracking tolerance
    return "S3"


def regrade_with_refined_rule(cache: dict) -> "pd.DataFrame":
    """Apply refined_rule to every cached event and compare regret vs the
    original flat rule. IN-SAMPLE by construction — the honest use is
    direction-of-improvement, not the level."""
    rows = []
    for label, r in cache.items():
        if label.startswith("_") or not r.get("available"):
            continue
        fr = pd.DataFrame(r["frontier"]).set_index("S")
        pick = refined_rule(r["side"], r["provider"],
                            r.get("car_drift_to_T_pct", 0.0) or 0.0)
        if pick not in fr.index:
            pick = "S1"
        best = fr["Cost vs decision (bps)"].min()
        rows.append({"label": label, "group": f"{r['provider']} {r['side']}",
                     "old_rule": r["grade"]["our_rule"],
                     "old_regret": r["grade"]["regret_bps"],
                     "refined_rule": pick,
                     "refined_regret": round(
                         float(fr.loc[pick, "Cost vs decision (bps)"] - best), 1)})
    return pd.DataFrame(rows)


# ── positioning trajectory: A-day -> T-day, day by day (session 7d) ────────

def positioning_trajectory(es, ann_rel: int, side: str,
                           label: str = "") -> dict:
    """How positioning BUILT between announcement and effective date.

    For each day in [A, T]: daily excess volume (ab_vol - 1, floored at
    0) as the accumulation proxy, its cumulative share of the window's
    total excess ("build fraction"), and the CAR path. Summary shape
    metrics:

        t_day_share     share of total event-window excess volume that
                        printed ON the effective day — how much of the
                        trade the street left for the print.
        half_build_rel  the rel-day by which 50% of total excess had
                        traded — early = pre-positioned, late = everyone
                        waited.
        shape           FRONT-LOADED (50% done before the calendar
                        midpoint of A->T), BACK-LOADED (T-day alone >=
                        50%), else STEADY.

    Same disclosed limitation as positioning_footprint: volume cannot
    distinguish who — this measures WHEN the event-related activity
    happened, not who did it."""
    rel = np.asarray(es.rel_days)
    ab = np.asarray(es.ab_vol, dtype=float)
    car = np.asarray(es.car, dtype=float)
    m = (rel >= ann_rel) & (rel <= 0)
    if m.sum() < 3:
        return {"available": False, "reason": "window too short", "label": label}
    r = rel[m]
    excess = np.clip(ab[m] - 1.0, 0.0, None)
    total = float(excess.sum())
    if total <= 0:
        return {"available": False, "reason": "no excess volume in window",
                "label": label}
    cum = np.cumsum(excess) / total
    rows = [{"rel_day": int(r[i]), "daily_excess_adv": round(float(excess[i]), 2),
             "build_frac": round(float(cum[i]), 3),
             "car_pct": round(float(car[m][i] - car[m][0]) * 100, 2)}
            for i in range(len(r))]
    t_share = float(excess[-1] / total)
    half_idx = int(np.argmax(cum >= 0.5))
    half_rel = int(r[half_idx])
    midpoint = (int(r[0]) + 0) / 2.0
    shape = ("BACK-LOADED" if t_share >= 0.5 else
             "FRONT-LOADED" if half_rel <= midpoint else "STEADY")
    return {"available": True, "label": label, "side": side,
            "trajectory": rows, "total_excess_adv_days": round(total, 2),
            "t_day_share": round(t_share, 3), "half_build_rel": half_rel,
            "shape": shape}


BUILD_GRID = (0.25, 0.50, 0.75, 0.90, 1.00)   # normalized A->T time


def aggregate_trajectories(trajs: list) -> pd.DataFrame:
    """Median build curve per provider-x-side group on a normalized
    announcement->effective clock (0 = A, 1 = T): 'by X% of the window,
    what fraction of the event-related volume had traded?' Plus median
    t_day_share and the shape mix — the WHEN-does-the-street-position
    answer."""
    rows = []
    for t in trajs:
        if not t.get("available"):
            continue
        tr = pd.DataFrame(t["trajectory"])
        a0, a1 = tr["rel_day"].iloc[0], 0
        span = max(a1 - a0, 1)
        x = (tr["rel_day"] - a0) / span
        interp = {g: float(np.interp(g, x, tr["build_frac"]))
                  for g in BUILD_GRID}
        rows.append({"group": f"{t.get('provider', '?')} {t['side']}",
                     **{f"by_{int(g*100)}pct": round(v, 2)
                        for g, v in interp.items()},
                     "t_day_share": t["t_day_share"], "shape": t["shape"]})
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    out = []
    for g, gg in df.groupby("group"):
        row = {"group": g, "n": len(gg)}
        for c in [c for c in gg.columns if c.startswith("by_")] + ["t_day_share"]:
            row[c] = round(float(pd.to_numeric(gg[c]).median()), 2)
        row["shape_mix"] = dict(gg["shape"].value_counts())
        out.append(row)
    return pd.DataFrame(out)
