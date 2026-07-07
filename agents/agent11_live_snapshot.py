"""
Agent 11: Live Point-in-Time Snapshot

Every other agent in this pipeline answers a PRE-TRADE question ("what
should I do") using the full, already-known trading day -- which is
exactly right for the decision made before execution starts, but wrong for
a dashboard meant to play back that execution as a time-lapse: a trader
watching the blotter at 10:35am does not get to see the 3:55pm close yet.

This module recomputes Market Regime (Agent 2), Microstructure (Agent 9),
a Pre-Trade re-underwrite for whatever's left of the order (Agent 6), a
"is the original algo choice still the right one" check (Agent 5's own
selection rule, re-run), and a live TCA reading (Agent 6's post-trade
benchmarks, computed to-date rather than end-of-day) -- all using ONLY the
bars up to a given cutoff time, exactly mirroring what a desk would
actually know at that moment. Prior (non-simulated) days are always kept
whole, since those are genuinely already-closed history a trader would
have in full regardless of where "now" is inside today's session.

Design choice: rather than duplicating Agent 2/6/9's math, every function
here calls those modules' own internal helpers (_classify_volatility,
_classify_volume, _classify_trend, estimate_kyle_lambda, compute_vpin,
almgren_2005_impact, compute_benchmark_comparison, etc.) on a truncated /
reconstructed slice of the data, so a change to the underlying methodology
only ever needs to happen in one place. Zero changes were made to
agent2/6/9 themselves -- this module only READS their public and internal
functions, so the existing "at decision time" baseline sections elsewhere
in the app carry no regression risk from this file.
"""

import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from typing import Optional

from agents.agent2_market_regime import RegimeAssessment, _classify_volatility, _classify_volume, _classify_trend
from agents.agent9_microstructure import (
    MicrostructureAssessment, KyleLambdaEstimate, VPINEstimate, AlmgrenImpactEstimate,
    estimate_kyle_lambda, compute_vpin, almgren_2005_impact,
)
from agents.agent6_pretrade_posttrade import (
    capacity_table, compute_impact_reversion, compute_impact_decomposition,
    compute_cost_percentile, ImpactReversion, ImpactDecomposition, CostPercentile,
)
from agents.agent3_algo_simulation import AlgoResult, _build_result, _speed_factor, POV_RATES
from agents.agent5_recommendation import _select_algos


# ══════════════════════════════════════════════════════════════════════════
# Data reconstruction -- "what a trader would know as of cutoff_time today"
# ══════════════════════════════════════════════════════════════════════════

def _stitch_intraday(full_intraday: pd.DataFrame, today_date, view_day: pd.DataFrame) -> pd.DataFrame:
    """Every OTHER day kept whole (already-closed history); today replaced
    by only the bars observed so far. This is what feeds Agent 2's volume/
    trend classifiers (which key off the LAST date present) and Agent 9's
    Kyle's-lambda pooling (which sums across every day present)."""
    other_days = full_intraday[full_intraday.index.normalize() != pd.Timestamp(today_date).normalize()]
    keep_cols = [c for c in other_days.columns if c in ("Open", "High", "Low", "Close", "Volume")]
    stitched = pd.concat([other_days[keep_cols], view_day[keep_cols]])
    return stitched.sort_index()


def _synthetic_daily_with_partial_today(daily: pd.DataFrame, today_date, view_day: pd.DataFrame) -> pd.DataFrame:
    """Agent 2's volatility classifier reads daily["High"]/["Low"] and
    treats the LAST row as "today". yfinance's own daily bar for today may
    be stale, absent, or (depending on fetch timing) already reflect the
    full session -- none of which is safe to trust for a live readout. This
    drops any existing same-day row and appends a synthetic one built from
    only the intraday bars observed so far, so the volatility-ratio
    denominator (trailing 20 days, computed via .iloc[:-1] in
    _classify_volatility) never accidentally includes today twice and the
    numerator never leaks future range."""
    today_norm = pd.Timestamp(today_date).normalize()
    hist = daily[daily.index.normalize() != today_norm].copy()
    synthetic = pd.DataFrame({
        "Open":   [float(view_day["Open"].iloc[0])],
        "High":   [float(view_day["High"].max())],
        "Low":    [float(view_day["Low"].min())],
        "Close":  [float(view_day["Close"].iloc[-1])],
        "Volume": [float(view_day["Volume"].sum())],
    }, index=[today_norm])
    return pd.concat([hist, synthetic]).sort_index()


# ══════════════════════════════════════════════════════════════════════════
# Live Agent 2 -- Market Regime, as of cutoff
# ══════════════════════════════════════════════════════════════════════════

def live_regime(full_intraday: pd.DataFrame, daily: pd.DataFrame, today_date,
                view_day: pd.DataFrame) -> RegimeAssessment:
    live_daily = _synthetic_daily_with_partial_today(daily, today_date, view_day)
    stitched = _stitch_intraday(full_intraday, today_date, view_day)

    vol_label, vol_ratio = _classify_volatility(live_daily)
    volume_label, u_score = _classify_volume(stitched)
    trend_label, autocorr, vr_primary, vr_detail = _classify_trend(stitched)

    summary = f"{vol_label} · {volume_label} volume · {trend_label} returns (as of cutoff)"
    return RegimeAssessment(
        vol_label=vol_label, vol_ratio=vol_ratio,
        volume_label=volume_label, u_shape_score=u_score,
        trend_label=trend_label, autocorr=autocorr,
        vr_available=vr_primary.get("available", False),
        vr_q=vr_primary.get("q", 0),
        vr_ratio=vr_primary.get("vr", 1.0),
        vr_zstat=vr_primary.get("z_robust", 0.0),
        vr_significant=abs(vr_primary.get("z_robust", 0.0)) >= 1.96,
        vr_detail=vr_detail,
        summary=summary,
    )


# ══════════════════════════════════════════════════════════════════════════
# Live Agent 9 -- Microstructure, as of cutoff (Almgren re-underwritten for
# the REMAINING shares, since that's the size a trader would actually be
# assessing impact for at this point)
# ══════════════════════════════════════════════════════════════════════════

def live_microstructure(full_intraday: pd.DataFrame, today_date, view_day: pd.DataFrame,
                        adv_shares: float, remaining_shares: float, urgency: str,
                        vol_ann: float, shares_outstanding: Optional[float] = None) -> MicrostructureAssessment:
    stitched = _stitch_intraday(full_intraday, today_date, view_day)
    kyle = estimate_kyle_lambda(stitched, adv_shares)
    vpin = compute_vpin(view_day)   # pass ONLY today's truncated slice so day-selection can't pick a different, fuller day
    rate = POV_RATES.get(urgency, 0.15)
    almgren = almgren_2005_impact(remaining_shares, adv_shares, vol_ann, rate, shares_outstanding)
    return MicrostructureAssessment(kyle_lambda=kyle, vpin=vpin, almgren_impact=almgren)


# ══════════════════════════════════════════════════════════════════════════
# Live Agent 6a -- Pre-Trade re-underwrite for what's left of the order
# ══════════════════════════════════════════════════════════════════════════

@dataclass
class LivePretradeRemaining:
    remaining_shares: float
    capacity: pd.DataFrame
    almgren: AlmgrenImpactEstimate
    note: str


def live_pretrade_remaining(remaining_shares: float, adv_shares: float, urgency: str,
                           vol_ann: float, shares_outstanding: Optional[float] = None) -> LivePretradeRemaining:
    cap = capacity_table(remaining_shares, adv_shares)
    rate = POV_RATES.get(urgency, 0.15)
    almgren = almgren_2005_impact(remaining_shares, adv_shares, vol_ann, rate, shares_outstanding)
    note = (f"Re-underwritten for the {remaining_shares:,.0f} shares still unfilled, at the current "
           f"{urgency}-urgency participation rate -- not the original full order. The Expected Cost "
           f"Range and spread estimate shown in the decision-time Pre-Trade section below are left "
           f"as originally computed (they describe the historical cost DISTRIBUTION this security/algo "
           f"combination tends to realize, which doesn't rescale in a simple way with remaining size).")
    return LivePretradeRemaining(remaining_shares=remaining_shares, capacity=cap, almgren=almgren, note=note)


# ══════════════════════════════════════════════════════════════════════════
# Live Agent 5 -- "is the original algo choice still the right one?"
# Reuses Agent 5's own selection rule verbatim against the LIVE regime
# (comparison/urgency/benchmark_target are unchanged -- those aren't
# time-of-day dependent), so this is the actual rule engine re-firing, not
# a bespoke heuristic.
# ══════════════════════════════════════════════════════════════════════════

@dataclass
class LiveRecommendationCheck:
    still_on_track: bool
    live_primary: str
    live_secondary: str
    original_primary: str
    changes: list


def live_recommendation_check(live_reg: RegimeAssessment, original_regime: RegimeAssessment,
                              comparison, urgency: str, benchmark_target: str,
                              original_primary: str, original_secondary: str) -> LiveRecommendationCheck:
    live_primary, live_secondary = _select_algos(live_reg, comparison, urgency, benchmark_target)

    changes = []
    if live_reg.vol_label != original_regime.vol_label:
        changes.append(f"Volatility regime shifted: **{original_regime.vol_label}** → **{live_reg.vol_label}** "
                       f"({live_reg.vol_ratio:.2f}× 20d median, was {original_regime.vol_ratio:.2f}×).")
    if live_reg.volume_label != original_regime.volume_label:
        changes.append(f"Volume pattern shifted: **{original_regime.volume_label}** → **{live_reg.volume_label}**.")
    if live_reg.trend_label != original_regime.trend_label:
        changes.append(f"Trend classification shifted: **{original_regime.trend_label}** → **{live_reg.trend_label}**"
                       + (f" (VR(q={live_reg.vr_q})={live_reg.vr_ratio:.2f}, z*={live_reg.vr_zstat:+.2f})"
                          if live_reg.vr_available else "") + ".")

    return LiveRecommendationCheck(
        still_on_track=(live_primary == original_primary),
        live_primary=live_primary, live_secondary=live_secondary,
        original_primary=original_primary, changes=changes,
    )


# ══════════════════════════════════════════════════════════════════════════
# Live Agent 6b -- TCA to-date (converges to the real, final Post-Trade TCA
# once cutoff reaches the last bar of the day)
# ══════════════════════════════════════════════════════════════════════════

def _benchmarks_to_date(live_algo: AlgoResult, view_day: pd.DataFrame, is_final: bool) -> pd.DataFrame:
    vol = view_day["Volume"].values
    px = view_day["Close"].values
    tv = vol.sum()
    vwap_to_date = float((px * vol).sum() / tv) if tv > 0 else float(px.mean())
    twap_to_date = float(view_day["Close"].mean())
    last_price = float(view_day["Close"].iloc[-1])

    label_vwap = "Full-Day VWAP" if is_final else "VWAP (to date)"
    label_twap = "Full-Day TWAP" if is_final else "TWAP (to date)"
    label_last = "Close" if is_final else "Last Price"

    rows = []
    for name, bench in [("Arrival (Open)", live_algo.arrival_price), (label_vwap, vwap_to_date),
                        (label_twap, twap_to_date), (label_last, last_price)]:
        slip = (live_algo.avg_exec_price - bench) / bench * 10_000 if bench > 0 else 0.0
        rows.append({"Benchmark": name, "Benchmark Price": round(bench, 4),
                    "Slippage vs Benchmark (bps)": round(slip, 2)})
    return pd.DataFrame(rows).set_index("Benchmark")


@dataclass
class LiveTCA:
    is_final: bool
    live_algo: AlgoResult
    benchmarks_to_date: pd.DataFrame
    mark_to_market_unfilled_bps: float
    reversion: Optional[ImpactReversion]
    decomposition: Optional[ImpactDecomposition]
    cost_percentile: Optional[CostPercentile]
    note: str


def _speed_factor_asof(legs_meta: list, view: pd.DataFrame, base_algo: str, base_urgency: str) -> float:
    """Fill-weighted blend of every leg's speed factor, using ONLY shares
    filled up to the cutoff (not the full-day blend simulate_with_interventions
    already computes for the complete plan)."""
    num, den = 0.0, 0.0
    for leg in legs_meta:
        leg_view = view[(view["time"] > leg["start_time"]) & (view["time"] <= leg["end_time"])]
        filled = float(leg_view["shares_traded"].sum()) if len(leg_view) else 0.0
        if filled > 0:
            num += filled * _speed_factor(leg["algo"], leg["urgency"])
            den += filled
    return (num / den) if den > 0 else _speed_factor(base_algo, base_urgency)


def live_tca(view: pd.DataFrame, view_day: pd.DataFrame, legs_meta: list, base_algo: str, base_urgency: str,
            arrival_price: float, order_shares: float, adv_shares: float, vol_ann: float,
            is_final: bool, comparison=None, algo_name_for_history: Optional[str] = None) -> LiveTCA:
    sf_asof = _speed_factor_asof(legs_meta, view, base_algo, base_urgency)
    current_price = float(view_day["Close"].iloc[-1])

    live_algo = _build_result(
        name="Live", schedule_df=view[["time", "shares_traded", "price"]],
        arrival_price=arrival_price, order_shares=order_shares, adv_shares=adv_shares,
        vol_ann=vol_ann, speed_factor=sf_asof, period_end_price=current_price,
        schedule_note="Live snapshot, marked to the current bar's price" if not is_final else "Final, full-day",
    )

    bench = _benchmarks_to_date(live_algo, view_day, is_final)

    # Mark-to-market opportunity cost of the unfilled remainder, using the
    # CURRENT price as the mark (already baked into live_algo.opportunity_cost_bps
    # via period_end_price=current_price above) -- surfaced separately since
    # it answers a distinct live-risk question ("what am I on the hook for if
    # I stopped trading right now") from the benchmark table's slippage-so-far.
    mtm_bps = live_algo.opportunity_cost_bps

    reversion = decomposition = pctl = None
    note = ("Reversion, impact decomposition, and a historical cost percentile all need the "
           "completed day's closing price -- available once the session finishes playing.")
    if is_final and comparison is not None and algo_name_for_history is not None:
        reversion = compute_impact_reversion(live_algo, view_day)
        decomposition = compute_impact_decomposition(live_algo, view_day)
        pctl = compute_cost_percentile(comparison, algo_name_for_history, live_algo.total_cost_bps)
        note = "Session complete -- these now reflect the full realized day, same methodology as Agent 6."

    return LiveTCA(
        is_final=is_final, live_algo=live_algo, benchmarks_to_date=bench,
        mark_to_market_unfilled_bps=mtm_bps, reversion=reversion,
        decomposition=decomposition, cost_percentile=pctl, note=note,
    )


# ── Live alert engine (EMS-blotter-style threshold rules) ───────────────────

ALERT_SLIP_MEDIUM_BPS = 25.0
ALERT_SLIP_HIGH_BPS = 50.0
ALERT_BEHIND_PACE_PTS = 10.0     # fill% lags elapsed-time% by more than this


@dataclass
class LiveAlert:
    severity: str      # "HIGH" | "MEDIUM" | "INFO"
    rule: str
    message: str


def build_live_alerts(*, filled_shares: float, order_shares: float,
                      elapsed_frac: float, algo_name: str,
                      last_bar_participation_pct: Optional[float] = None,
                      cap_pct: Optional[float] = None,
                      limit_price: Optional[float] = None,
                      current_price: Optional[float] = None,
                      vpin_label: Optional[str] = None,
                      slip_vs_benchmark_bps: Optional[float] = None,
                      benchmark_name: str = "Arrival",
                      reconsider: bool = False) -> list[LiveAlert]:
    """Threshold rules over the live metrics — the alert blotter a real EMS
    shows next to a working order. Pure function: everything is passed in,
    nothing recomputed, so it is trivially unit-testable and can't disagree
    with the panels above it. Alerts inform the trader; nothing auto-acts
    (same posture as Agent 8)."""
    alerts: list[LiveAlert] = []
    fill_frac = filled_shares / order_shares if order_shares > 0 else 1.0

    # Completion pace — only meaningful for front-participating algos;
    # back-loaded schedules (IS high-urgency is front-loaded; MOC/MOO are
    # auction-timed) legitimately lag the clock.
    if algo_name not in ("MOC", "MOO", "IS") and elapsed_frac > 0.10:
        gap_pts = (elapsed_frac - fill_frac) * 100
        if gap_pts > ALERT_BEHIND_PACE_PTS:
            sev = "HIGH" if gap_pts > 2 * ALERT_BEHIND_PACE_PTS else "MEDIUM"
            alerts.append(LiveAlert(sev, "Completion pace",
                f"Filled {fill_frac:.0%} vs {elapsed_frac:.0%} of the session elapsed "
                f"({gap_pts:.0f} pts behind) — completion risk if volume doesn't improve."))

    if (cap_pct is not None and last_bar_participation_pct is not None
            and last_bar_participation_pct > cap_pct):
        alerts.append(LiveAlert("HIGH", "Participation breach",
            f"Last bar traded {last_bar_participation_pct:.1f}% of bar volume vs the "
            f"{cap_pct:g}% ticket cap — reduce aggression or widen the horizon."))

    if limit_price is not None and current_price is not None and current_price > limit_price:
        alerts.append(LiveAlert("MEDIUM", "Limit through market",
            f"Market ({current_price:.2f}) is trading above the {limit_price:g} buy limit — "
            "fills are paused; completion risk accumulates while price stays through the limit."))

    if vpin_label == "High":
        alerts.append(LiveAlert("MEDIUM", "Order-flow toxicity",
            "Live VPIN is in its High band — contested as a predictor "
            "(Andersen-Bondarenko 2014), but elevated toxicity regimes coincide with "
            "wider spreads and thinner books; consider slowing down."))
    elif vpin_label == "Elevated":
        alerts.append(LiveAlert("INFO", "Order-flow toxicity",
            "Live VPIN is Elevated — monitoring signal only."))

    if slip_vs_benchmark_bps is not None:
        if slip_vs_benchmark_bps > ALERT_SLIP_HIGH_BPS:
            alerts.append(LiveAlert("HIGH", "Benchmark slippage",
                f"Execution is {slip_vs_benchmark_bps:+.1f} bps vs {benchmark_name} "
                f"(> {ALERT_SLIP_HIGH_BPS:g} bps) — intervention review warranted."))
        elif slip_vs_benchmark_bps > ALERT_SLIP_MEDIUM_BPS:
            alerts.append(LiveAlert("MEDIUM", "Benchmark slippage",
                f"Execution is {slip_vs_benchmark_bps:+.1f} bps vs {benchmark_name} "
                f"(> {ALERT_SLIP_MEDIUM_BPS:g} bps)."))

    if reconsider:
        alerts.append(LiveAlert("INFO", "Strategy re-check",
            "Agent 5's rule re-fired against the live regime and would now pick a "
            "different algo — see the Reconsider panel above."))
    return alerts
