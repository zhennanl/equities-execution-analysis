"""
Agent 14 — Rebalance Best-Execution Strategist.

Simulates the four literature-anchored execution strategies for an index
rebalancing event at DAY-level granularity over the event's ACTUAL price/
volume path (consumed straight from Agent's event study — no separate fetch),
and scores each on the two dimensions institutional clients actually trade
off (see docs/INDEX_REBALANCE_RESEARCH.md for the evidence base):

  * implementation cost vs. the pre-announcement decision price, and
  * tracking difference vs. the effective-day closing print (the index
    tracker's benchmark).

Strategies (literature anchors in the research doc):
  S1 Tracker baseline — 100% in the effective-day closing auction. Zero
     benchmark risk, maximum crowding (Petajisto's measured drag).
  S2 Pre-position     — fraction spread A+1…T-1, remainder at the T close
     (Madhavan 2003: gradual advance acquisition, minimal extra TE).
  S3 Post-effective   — partial at the T close, remainder T+1…T+m capturing
     any reversal of the temporary price-pressure component (Harris-Gurel).
  S4 Announcement-anchored — equal spread A+1…T ("S&P game" profile;
     Greenwood-Sammon: this alpha has compressed since 2010).

Modeling choices (all disclosed in `caveats`):
  * Day fills at the day's close (auction fills at the closing print) plus a
    square-root impact adjustment at day-level participation — same eta as
    the intraday simulator.
  * Effective-day auction capacity = auction_normal_share x the day's
    OBSERVED volume (which already includes the rebalance surge), so auction
    stress is measured against the real event-day tape.
  * Pre/post slices are equal-weighted (causal — no realized-volume
    weighting hindsight).
  * Both sides supported: "Buy" (addition) and "Sell" (deletion) — signs
    flip so cost is always "positive = worse".
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import numpy as np
import pandas as pd

from agents.agent3_algo_simulation import IMPACT_ETA

DEFAULT_ANN_REL_DAY = -5          # Greenwood-Sammon: mean A->E gap 4.8/5.8 days
DEFAULT_POST_DAYS = 10            # mid of the 5-20 day reversal literature
DEFAULT_AUCTION_NORMAL_SHARE = 0.10
AUCTION_STRESS_WARN = 0.25        # order > 25% of estimated auction volume


@dataclass
class StrategyOutcome:
    name: str
    description: str
    avg_exec_price: float
    cost_vs_decision_bps: float      # vs pre-announcement close; positive = worse
    tracking_diff_bps: float         # vs effective close; positive = worse than print
    abs_tracking_bps: float
    auction_pct: float               # % of order in the T closing auction
    avg_impact_bps: float            # share-weighted modeled impact
    max_day_participation_pct: float # largest single-day % of that day's volume
    schedule: pd.DataFrame           # rel_day / date / shares / fill price / venue
    notes: list = field(default_factory=list)


@dataclass
class RebalanceStrategyAnalysis:
    side: str
    order_shares: float
    order_pct_adv: float
    decision_price: float            # close at announcement day
    effective_close: float
    realized_post_reversal_bps: float  # abnormal move T -> T+m (from the event study CAR)
    strategies: list                 # [StrategyOutcome]
    frontier: pd.DataFrame           # strategy x (cost, |tracking|, auction%, impact)
    recommended: str
    rationale: str
    params: dict
    caveats: list


def _impact_bps(shares: float, day_volume: float, sigma_daily: float,
                eta: float) -> float:
    if shares <= 0 or day_volume <= 0:
        return 0.0
    return eta * sigma_daily * np.sqrt(shares / day_volume) * 10_000


def _fill_price(close: float, impact_bps: float, side: str) -> float:
    sgn = 1.0 if side == "Buy" else -1.0
    return close * (1 + sgn * impact_bps / 10_000)


def _signed_cost_bps(avg_px: float, ref_px: float, side: str) -> float:
    """Positive = worse than the reference for this side."""
    raw = (avg_px - ref_px) / ref_px * 10_000
    return raw if side == "Buy" else -raw


def analyze_strategies(es, side: str = "Buy",
                       order_pct_adv: float = 5.0,
                       order_shares: Optional[float] = None,
                       ann_rel_day: int = DEFAULT_ANN_REL_DAY,
                       pre_frac: float = 0.5,
                       post_frac: float = 0.5,
                       post_days: int = DEFAULT_POST_DAYS,
                       auction_normal_share: float = DEFAULT_AUCTION_NORMAL_SHARE,
                       eta: float = IMPACT_ETA) -> RebalanceStrategyAnalysis:
    """Score S1-S4 on the event's actual price path.

    es : EventStudyResult from run_event_study() — supplies the event-window
         prices (norm_price x price_at_T), volumes (ab_vol x est_avg_volume),
         daily sigma, ADV, and the realized CAR path.
    """
    rel = np.asarray(es.rel_days)
    closes = np.asarray(es.norm_price, dtype=float) / 100.0 * float(es.price_at_T)
    vols = np.clip(np.asarray(es.ab_vol, dtype=float), 0.0, None) * float(es.est_avg_volume)
    dates = pd.to_datetime(es.event_dates)
    n = len(rel)
    i_T = int(np.where(rel == 0)[0][0])
    adv = float(es.est_avg_volume)
    sigma_d = float(es.est_sigma_daily)

    if order_shares is None:
        order_shares = adv * order_pct_adv / 100.0
    else:
        order_pct_adv = order_shares / adv * 100.0 if adv > 0 else 0.0

    # clamp the announcement and post horizons to the available window
    ann_rel_day = int(max(ann_rel_day, int(rel[0])))
    i_A = int(np.where(rel == ann_rel_day)[0][0])
    post_days = int(min(post_days, int(rel[-1])))

    decision_px = float(closes[i_A])
    T_close = float(closes[i_T])
    T_volume = float(vols[i_T])
    auction_vol_est = max(auction_normal_share * T_volume, 1.0)

    # realized post-event abnormal move (reversal if it opposes the pre-T move)
    car = np.asarray(es.car, dtype=float)
    i_Tm = int(np.where(rel == post_days)[0][0]) if post_days >= 1 else i_T
    realized_post_bps = float((car[i_Tm] - car[i_T]) * 10_000)

    pre_idx = [i for i in range(i_A + 1, i_T)]                  # A+1 .. T-1
    post_idx = [i for i in range(i_T + 1, i_Tm + 1)]            # T+1 .. T+m

    def _run(name: str, description: str, day_alloc: dict[int, float],
             auction_shares: float) -> StrategyOutcome:
        rows, notes = [], []
        tot_px_sh = 0.0
        tot_impact = 0.0
        max_part = 0.0
        for i, q in sorted(day_alloc.items()):
            if q <= 0:
                continue
            imp = _impact_bps(q, vols[i], sigma_d, eta)
            px = _fill_price(closes[i], imp, side)
            part = q / vols[i] * 100 if vols[i] > 0 else 0.0
            max_part = max(max_part, part)
            tot_px_sh += px * q
            tot_impact += imp * q
            rows.append({"Rel day": int(rel[i]), "Date": dates[i].date(),
                         "Shares": round(q, 0), "Venue": "Continuous",
                         "Fill price": round(px, 4), "Impact (bps)": round(imp, 1),
                         "% of day volume": round(part, 1)})
        if auction_shares > 0:
            imp = _impact_bps(auction_shares, auction_vol_est, sigma_d, eta)
            px = _fill_price(T_close, imp, side)
            a_part = auction_shares / auction_vol_est * 100
            tot_px_sh += px * auction_shares
            tot_impact += imp * auction_shares
            rows.append({"Rel day": 0, "Date": dates[i_T].date(),
                         "Shares": round(auction_shares, 0), "Venue": "Closing auction",
                         "Fill price": round(px, 4), "Impact (bps)": round(imp, 1),
                         "% of day volume": round(a_part, 1)})
            if auction_shares > AUCTION_STRESS_WARN * auction_vol_est:
                notes.append(f"Auction stress: order is {a_part:.0f}% of the estimated "
                             f"closing-auction volume (> {AUCTION_STRESS_WARN:.0%} threshold) — "
                             "impact model is least reliable in this regime.")
        filled = sum(q for q in day_alloc.values()) + auction_shares
        avg_px = tot_px_sh / filled if filled > 0 else T_close
        avg_imp = tot_impact / filled if filled > 0 else 0.0
        cost = _signed_cost_bps(avg_px, decision_px, side)
        track = _signed_cost_bps(avg_px, T_close, side)
        return StrategyOutcome(
            name=name, description=description,
            avg_exec_price=round(avg_px, 4),
            cost_vs_decision_bps=round(cost, 1),
            tracking_diff_bps=round(track, 1),
            abs_tracking_bps=round(abs(track), 1),
            auction_pct=round(100 * auction_shares / filled, 1) if filled else 0.0,
            avg_impact_bps=round(avg_imp, 1),
            max_day_participation_pct=round(max_part, 1),
            schedule=pd.DataFrame(rows), notes=notes)

    strategies: list[StrategyOutcome] = []

    # S1 — tracker baseline: everything in the T closing auction
    strategies.append(_run(
        "S1 Tracker (100% MOC at T)",
        "Full order in the effective-day closing auction — the mechanical "
        "indexer's trade (zero benchmark risk, maximum crowding).",
        {}, order_shares))

    # S2 — pre-position over A+1..T-1, remainder at the T close
    if pre_idx:
        per = order_shares * pre_frac / len(pre_idx)
        strategies.append(_run(
            f"S2 Pre-position ({pre_frac:.0%} over T-{len(pre_idx)}..T-1)",
            "Gradual advance acquisition after the announcement, remainder in "
            "the closing auction (Madhavan 2003).",
            {i: per for i in pre_idx}, order_shares * (1 - pre_frac)))

    # S3 — partial MOC, remainder spread after the effective date
    if post_idx:
        per = order_shares * post_frac / len(post_idx)
        strategies.append(_run(
            f"S3 Post-effective ({post_frac:.0%} over T+1..T+{len(post_idx)})",
            "Partial auction print, remainder completed after the event to "
            "capture reversal of the temporary price-pressure component.",
            {i: per for i in post_idx}, order_shares * (1 - post_frac)))

    # S4 — equal spread from announcement through the effective close
    span = pre_idx + [i_T]
    per = order_shares / len(span)
    alloc = {i: per for i in pre_idx}
    strategies.append(_run(
        f"S4 Announcement-anchored (equal A+1..T)",
        "Equal daily slices from the announcement through the effective day "
        "(final slice at the close). The classic 'index game' profile — "
        "note Greenwood-Sammon: this alpha has compressed since 2010.",
        alloc, per))

    frontier = pd.DataFrame([{
        "Strategy": s.name,
        "Cost vs decision (bps)": s.cost_vs_decision_bps,
        "|Tracking diff| (bps)": s.abs_tracking_bps,
        "Auction share (%)": s.auction_pct,
        "Avg impact (bps)": s.avg_impact_bps,
        "Max day participation (%)": s.max_day_participation_pct,
    } for s in strategies])

    # objective-aware recommendation
    def _pick(objective: str) -> tuple[str, str]:
        if objective == "Index Tracker":
            best = min(strategies, key=lambda s: (s.abs_tracking_bps, s.cost_vs_decision_bps))
            why = (f"minimizes tracking difference vs the effective close "
                   f"({best.abs_tracking_bps:.1f} bps) at a cost of "
                   f"{best.cost_vs_decision_bps:.1f} bps vs the decision price")
        else:
            best = min(strategies, key=lambda s: (s.cost_vs_decision_bps, s.abs_tracking_bps))
            why = (f"minimizes implementation cost vs the decision price "
                   f"({best.cost_vs_decision_bps:.1f} bps) with a tracking "
                   f"difference of {best.tracking_diff_bps:+.1f} bps vs the print")
        return best.name, why

    # store both picks; the UI chooses per the page's objective input
    rec_tracker, why_tracker = _pick("Index Tracker")
    rec_cost, why_cost = _pick("Cost-Minimizing")
    rationale = (f"Index-Tracker mandate → **{rec_tracker}** ({why_tracker}). "
                 f"Cost-Minimizing mandate → **{rec_cost}** ({why_cost}). "
                 f"Realized post-event abnormal move T→T+{post_days}: "
                 f"{realized_post_bps:+.0f} bps"
                 + (" — the temporary component did revert, favoring "
                    "post-effective completion for cost-minimizers."
                    if (realized_post_bps < 0 and side == "Buy") or
                       (realized_post_bps > 0 and side == "Sell")
                    else " — no favorable reversal materialized on this event."))

    caveats = [
        "Day-level fills at closing prices + square-root impact at daily "
        "participation — no intraday path within days.",
        f"Auction capacity = {auction_normal_share:.0%} of the observed effective-day "
        "volume (which already includes the rebalance surge).",
        "Scores are computed on THIS event's realized path — ex-post, single-name, "
        "no basket/crowding interaction. It is a case study, not an expected-value "
        "forecast; see docs/INDEX_REBALANCE_RESEARCH.md for the cross-sectional "
        "evidence (and its post-2010 compression).",
        "Pre/post slices are equal-weighted (causal); no realized-volume hindsight.",
    ]

    return RebalanceStrategyAnalysis(
        side=side, order_shares=round(order_shares, 0),
        order_pct_adv=round(order_pct_adv, 2),
        decision_price=round(decision_px, 4), effective_close=round(T_close, 4),
        realized_post_reversal_bps=round(realized_post_bps, 0),
        strategies=strategies, frontier=frontier,
        recommended=rec_tracker, rationale=rationale,
        params={"ann_rel_day": ann_rel_day, "pre_frac": pre_frac,
                "post_frac": post_frac, "post_days": post_days,
                "auction_normal_share": auction_normal_share, "eta": eta},
        caveats=caveats)
