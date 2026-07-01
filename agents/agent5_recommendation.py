"""
Agent 5: Recommendation Memo (rule-based, no API key required)
Combines regime, simulation, and multi-day comparison to produce a
structured execution recommendation.

Design note — rule-based + data-driven, not RL: a 2025 industry survey of
execution-algorithm research found hybrid RL-plus-domain-knowledge approaches
growing from 15% to 42% adoption while pure RL fell from 85% to 58%, with
implementation quality and domain knowledge mattering more than algorithm
sophistication. This agent's fixed rules layered on top of Agent 4's
data-driven "best average cost" comparison is structurally that same hybrid
pattern. A full reinforcement-learning execution agent would need historical
fill/reward data this yfinance-only pipeline doesn't have, so it's treated as
future work rather than built here.
"""

from dataclasses import dataclass, field
from agents.agent1_market_data import MarketData
from agents.agent2_market_regime import RegimeAssessment
from agents.agent3_algo_simulation import SimulationResult
from agents.agent4_performance_comparison import PerformanceComparison


@dataclass
class RecommendationMemo:
    primary_algo: str
    secondary_algo: str
    risk_flags: list
    memo_text: str


# ── Rule-based algorithm selection ────────────────────────────────────────────

def _select_algos(regime: RegimeAssessment, comparison: PerformanceComparison,
                  urgency: str) -> tuple:
    """
    Priority order:
      1. Extremely Trending + Medium/High urgency → IS (speed needed)
      2. High urgency → IS
      3. Tight/Normal vol + U-Shaped volume + Low urgency → VWAP
      4. Uniform volume + Low/Medium urgency → TWAP
      5. Mean-Reverting + Low urgency → TWAP (patience rewarded)
      6. Trending returns + High urgency → IS
      7. Default → lowest average cost from comparison
    """
    vol    = regime.vol_label
    volume = regime.volume_label
    trend  = regime.trend_label

    primary = comparison.best_algo   # start with data-driven pick

    if vol == "Extremely Trending" and urgency in ("Medium", "High"):
        primary = "IS"
    elif urgency == "High":
        primary = "IS"
    elif vol in ("Tight", "Normal") and volume == "U-Shaped" and urgency == "Low":
        primary = "VWAP"
    elif volume == "Uniform" and urgency in ("Low", "Medium"):
        primary = "TWAP"
    elif trend == "Mean-Reverting" and urgency == "Low":
        primary = "TWAP"
    elif trend == "Trending" and urgency == "High":
        primary = "IS"

    ranked    = comparison.summary["Mean (bps)"].sort_values().index.tolist()
    secondary = next(a for a in ranked if a != primary)

    return primary, secondary


# ── Risk flags ────────────────────────────────────────────────────────────────

def _build_flags(regime: RegimeAssessment, sim: SimulationResult,
                 order_pct_adv: float, urgency: str, primary: str = None) -> list:
    flags = []
    if regime.vol_label in ("Trending", "Extremely Trending"):
        flags.append(
            f"Elevated intraday range ({regime.vol_ratio:.2f}× 20-day median) increases market "
            f"impact. Consider reducing order size or splitting across sessions."
        )
    if order_pct_adv >= 15:
        flags.append(
            f"Large order ({order_pct_adv}% ADV) — price impact likely to be material "
            f"regardless of algorithm choice."
        )
    pov_fill = sim.algos["POV"].completion_pct
    if pov_fill < 1.0:
        flags.append(
            f"POV fill rate {pov_fill:.0%} on simulation day — insufficient liquidity "
            f"to complete the order at current urgency ({urgency}). Avoid POV or increase rate."
        )
    stealth = sim.algos.get("STEALTH")
    if stealth and stealth.completion_pct < 1.0:
        flags.append(
            f"Stealth fill rate {stealth.completion_pct:.0%} on simulation day — the low-footprint "
            f"participation cap is too restrictive for this order size. Raise urgency or accept a "
            f"multi-day execution horizon."
        )
    if regime.trend_label == "Trending" and urgency == "Low":
        flags.append(
            "Positive return autocorrelation with Low urgency — intraday momentum may "
            "widen cost if execution is too slow. Consider upgrading to Medium urgency."
        )
    primary_result = sim.algos.get(primary) if primary else None
    if primary_result and primary_result.completion_pct < 0.999 and abs(primary_result.opportunity_cost_bps) >= 5:
        direction = "cost" if primary_result.opportunity_cost_bps > 0 else "benefit"
        flags.append(
            f"{primary} left {1 - primary_result.completion_pct:.0%} of the order unfilled on the "
            f"simulation day. Perold (1988) opportunity cost on the unfilled portion — priced against "
            f"the day's period-end close versus arrival — was {primary_result.opportunity_cost_bps:+.1f} bps "
            f"(a {direction} relative to a fully-filled paper portfolio, already reflected in the total "
            f"cost above)."
        )
    if not flags:
        flags.append("No material risk flags. Conditions are within normal parameters.")
    return flags


# ── Memo text assembly ────────────────────────────────────────────────────────

def _build_memo(market_data: MarketData, regime: RegimeAssessment,
                comparison: PerformanceComparison, primary: str, secondary: str,
                flags: list, order_pct_adv: float, urgency: str) -> str:

    order_shares   = market_data.adv_shares * (order_pct_adv / 100)
    order_notional = order_shares * market_data.current_price
    n_days         = len(comparison.daily_costs)
    wins           = comparison.win_counts[primary]
    mean_cost      = comparison.summary.loc[primary, "Mean (bps)"]
    sec_cost       = comparison.summary.loc[secondary, "Mean (bps)"]

    # Regime-specific rationale sentences
    vol_line = {
        "Tight":              "Compressed intraday range suggests muted price impact — execution conditions are favourable.",
        "Normal":             "Intraday range is in line with recent history. Standard execution conditions apply.",
        "Trending":           "Wide intraday range signals elevated volatility. Speed-precision trade-off is elevated today.",
        "Extremely Trending": "Exceptional intraday range — execution risk is elevated. Prioritise speed over slippage.",
    }.get(regime.vol_label, "")

    vol_line2 = {
        "U-Shaped":    "Volume is concentrated at open and close — VWAP benefits from trading with this natural flow.",
        "Uniform":     "Volume is evenly distributed across the session — TWAP minimises timing risk effectively.",
        "Midday-Heavy": "Unusual midday concentration — careful timing review is warranted before execution.",
    }.get(regime.volume_label, "")

    trend_line = {
        "Trending":       "Positive return autocorrelation indicates intraday momentum — front-loading may reduce cost.",
        "Mean-Reverting": "Negative autocorrelation is typical equity microstructure — patient algos perform well.",
        "Neutral":        "No dominant directional bias in intraday returns — standard scheduling applies.",
    }.get(regime.trend_label, "")

    algo_rationale = {
        "VWAP":    f"tracks the natural volume curve, aligning execution with open/close liquidity and minimising market footprint.",
        "TWAP":    f"spreads the order evenly over the session, avoiding timing bias and minimising impact at a low participation rate.",
        "IS":      f"trades an Almgren-Chriss (2000) optimal front-loaded trajectory, balancing impact against timing risk under elevated urgency.",
        "POV":     f"maintains a consistent participation rate with market volume, adapting to real-time liquidity.",
        "MOC":     f"holds back size until the closing window, concentrating execution into the close where auction liquidity is assumed to absorb it efficiently.",
        "MOO":     f"concentrates execution into the opening window, prioritising early completion at the cost of higher opening-print adverse-selection risk.",
        "LIQ":     f"opportunistically increases participation when price dips favourably versus its recent short-term mean, seeking liquidity while minimising footprint.",
        "STEALTH": f"caps participation per bar and randomises child-order size to avoid signalling — trading completion speed for minimal footprint.",
    }.get(primary, "delivered the lowest average total cost across the simulation window.")

    lines = [
        "**EXECUTION RECOMMENDATION MEMO**",
        "",
        f"**Ticker:** {market_data.ticker}  |  **Market:** {market_data.market}",
        f"**Order:** {order_pct_adv}% ADV · {order_shares:,.0f} shares · ${order_notional/1e6:.2f}M notional",
        f"**Urgency:** {urgency}",
        "",
        "---",
        "",
        "**MARKET CONDITIONS**",
        f"- Range: **{regime.vol_label}** ({regime.vol_ratio:.2f}× 20-day median) — {vol_line}",
        f"- Volume: **{regime.volume_label}** (U-score {regime.u_shape_score:.2f}) — {vol_line2}",
        f"- Trend: **{regime.trend_label}** (lag-1 autocorr {regime.autocorr:+.3f}) — {trend_line}",
        "",
        "---",
        "",
        f"**PRIMARY RECOMMENDATION: {primary}** — estimated {mean_cost:.1f} bps avg total cost",
        "",
        f"{primary} {algo_rationale} "
        f"Across {n_days} simulated trading days, it averaged **{mean_cost:.1f} bps** and ranked best "
        f"on **{wins}/{n_days} days**.",
        "",
        f"**Secondary / Fallback: {secondary}** ({sec_cost:.1f} bps avg) — recommended if intraday "
        f"liquidity conditions deviate materially from the simulation day.",
        "",
        "---",
        "",
        "**RISK FLAGS**",
    ]
    for flag in flags:
        lines.append(f"- {flag}")

    lines += [
        "",
        "---",
        "",
        "*Simulated using public OHLCV data (Yahoo Finance). Market impact estimated via the "
        "square-root model (η = 0.3, speed-adjusted per algorithm) — one of the more robust "
        "empirical findings in market microstructure. Total cost includes Perold (1988) opportunity "
        "cost on any unfilled shares. Results are for research and educational purposes only and "
        "do not constitute investment advice.*",
    ]

    return "\n".join(lines)


# ── Main entry point ──────────────────────────────────────────────────────────

def generate_memo(market_data: MarketData, regime: RegimeAssessment,
                  sim: SimulationResult, comparison: PerformanceComparison,
                  urgency: str, order_pct_adv: float, log=None) -> RecommendationMemo:

    def _log(msg):
        if log: log(msg)

    primary, secondary = _select_algos(regime, comparison, urgency)
    flags    = _build_flags(regime, sim, order_pct_adv, urgency, primary=primary)
    memo_txt = _build_memo(market_data, regime, comparison, primary, secondary,
                           flags, order_pct_adv, urgency)

    _log(f"Primary: {primary}  Secondary: {secondary}")
    _log("Agent 5 complete.")

    return RecommendationMemo(
        primary_algo=primary,
        secondary_algo=secondary,
        risk_flags=flags,
        memo_text=memo_txt,
    )
