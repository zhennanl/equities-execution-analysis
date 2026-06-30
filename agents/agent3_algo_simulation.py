"""
Agent 3: Algorithm Simulation Agent
Simulates VWAP, TWAP, POV, and Implementation Shortfall on a synthetic
buy order using real intraday price/volume data from Agent 1.

Metrics per algorithm:
  - Slippage (bps):        (avg_exec_price - arrival_price) / arrival_price * 10000
  - Market impact (bps):   Square root model — sigma_daily * sqrt(Q/ADV) * eta * speed_factor
  - Total cost (bps):      Slippage + Market Impact
  - Completion (%):        For POV, may not fill 100% if liquidity is thin
"""

import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from agents.agent1_market_data import MarketData, MARKET_INFO


# Market impact coefficient (empirical, typical range 0.2–0.5)
IMPACT_ETA = 0.3

# Speed factors scale market impact per algo (relative to neutral baseline)
SPEED_FACTORS = {
    "TWAP": 0.85,   # most passive — spread evenly over time
    "VWAP": 0.90,   # follows volume curve — slightly passive
    "POV":  1.00,   # neutral — depends on participation rate
    "IS":   {"Low": 1.20, "Medium": 1.55, "High": 2.00},  # front-loaded = higher impact
}

POV_RATES    = {"Low": 0.10, "Medium": 0.15, "High": 0.20}
IS_LAMBDA    = {"Low": 0.5,  "Medium": 1.2,  "High": 2.5}


@dataclass
class AlgoResult:
    name: str
    arrival_price: float
    avg_exec_price: float
    slippage_bps: float
    market_impact_bps: float
    total_cost_bps: float
    completion_pct: float          # 1.0 for VWAP/TWAP/IS; may be < 1.0 for POV
    schedule: pd.DataFrame         # columns: time, shares_traded, price, cumulative


@dataclass
class SimulationResult:
    ticker: str
    order_shares: float
    order_pct_adv: float
    urgency: str
    arrival_price: float
    algos: dict = field(default_factory=dict)   # name → AlgoResult


# ── Helpers ────────────────────────────────────────────────────────────────────

def _sim_day(intraday: pd.DataFrame, bars_expected: int) -> pd.DataFrame:
    """Return the most recent day with ≥80% of expected bars (most complete day)."""
    dates = sorted(intraday.index.normalize().unique())
    for d in reversed(dates):
        day = intraday[intraday.index.normalize() == d]
        if len(day) >= int(bars_expected * 0.8):
            return day.copy()
    return intraday[intraday.index.normalize() == dates[-1]].copy()


def _build_result(name, schedule_df, arrival_price, order_shares,
                  adv_shares, vol_ann, speed_factor):
    filled = schedule_df["shares_traded"].sum()
    if filled == 0:
        avg_px = arrival_price
    else:
        avg_px = (schedule_df["shares_traded"] * schedule_df["price"]).sum() / filled

    slippage_bps   = (avg_px - arrival_price) / arrival_price * 10_000
    sigma_daily    = vol_ann / np.sqrt(252)
    mi_bps         = IMPACT_ETA * sigma_daily * np.sqrt(order_shares / adv_shares) * speed_factor * 10_000
    total_bps      = slippage_bps + mi_bps
    completion_pct = min(filled / order_shares, 1.0)

    return AlgoResult(
        name=name,
        arrival_price=arrival_price,
        avg_exec_price=avg_px,
        slippage_bps=round(slippage_bps, 2),
        market_impact_bps=round(mi_bps, 2),
        total_cost_bps=round(total_bps, 2),
        completion_pct=round(completion_pct, 4),
        schedule=schedule_df,
    )


# ── Algorithm schedules ────────────────────────────────────────────────────────

def _sim_vwap(day: pd.DataFrame, order_shares: float, **kw) -> pd.DataFrame:
    total_vol = day["Volume"].sum()
    if total_vol == 0:
        shares = np.ones(len(day)) * order_shares / len(day)
    else:
        shares = (day["Volume"] / total_vol * order_shares).values
    cumulative = np.cumsum(shares)
    return pd.DataFrame({
        "time": day.index,
        "shares_traded": shares,
        "price": day["Close"].values,
        "cumulative": cumulative,
    })


def _sim_twap(day: pd.DataFrame, order_shares: float, **kw) -> pd.DataFrame:
    n = len(day)
    shares = np.full(n, order_shares / n)
    return pd.DataFrame({
        "time": day.index,
        "shares_traded": shares,
        "price": day["Close"].values,
        "cumulative": np.cumsum(shares),
    })


def _sim_pov(day: pd.DataFrame, order_shares: float, urgency: str, **kw) -> pd.DataFrame:
    rate = POV_RATES[urgency]
    remaining = order_shares
    rows = []
    cumulative = 0.0
    for ts, bar in day.iterrows():
        if remaining <= 0:
            rows.append((ts, 0.0, bar["Close"], cumulative))
            continue
        tradeable = bar["Volume"] * rate
        traded = min(remaining, tradeable)
        remaining -= traded
        cumulative += traded
        rows.append((ts, traded, bar["Close"], cumulative))
    return pd.DataFrame(rows, columns=["time", "shares_traded", "price", "cumulative"])


def _sim_is(day: pd.DataFrame, order_shares: float, urgency: str, **kw) -> pd.DataFrame:
    lam = IS_LAMBDA[urgency]
    n = len(day)
    raw_weights = np.array([np.exp(-lam * i / n) for i in range(n)])
    weights = raw_weights / raw_weights.sum()
    shares = weights * order_shares
    return pd.DataFrame({
        "time": day.index,
        "shares_traded": shares,
        "price": day["Close"].values,
        "cumulative": np.cumsum(shares),
    })


# ── Main entry point ───────────────────────────────────────────────────────────

def simulate_algos(market_data: MarketData, order_pct_adv: float,
                   urgency: str, log=None) -> SimulationResult:
    """
    Run all four algorithm simulations and return comparable results.

    Parameters
    ----------
    market_data   : MarketData from Agent 1
    order_pct_adv : order size as % of ADV (e.g. 5 = 5%)
    urgency       : "Low" | "Medium" | "High"
    log           : optional logging callback
    """
    def _log(msg):
        if log: log(msg)

    order_shares = market_data.adv_shares * (order_pct_adv / 100)
    bars_expected = MARKET_INFO[market_data.market]["bars"]
    day = _sim_day(market_data.intraday, bars_expected)

    arrival_price = float(day["Open"].iloc[0]) if "Open" in day.columns else float(day["Close"].iloc[0])
    _log(f"Simulating on {day.index[0].date()} · {len(day)} bars · arrival={arrival_price:.2f}")

    result = SimulationResult(
        ticker=market_data.ticker,
        order_shares=order_shares,
        order_pct_adv=order_pct_adv,
        urgency=urgency,
        arrival_price=arrival_price,
    )

    common = dict(order_shares=order_shares, urgency=urgency,
                  adv_shares=market_data.adv_shares, vol_ann=market_data.realized_vol_ann)

    configs = [
        ("VWAP", _sim_vwap, SPEED_FACTORS["VWAP"]),
        ("TWAP", _sim_twap, SPEED_FACTORS["TWAP"]),
        ("POV",  _sim_pov,  SPEED_FACTORS["POV"]),
        ("IS",   _sim_is,   SPEED_FACTORS["IS"][urgency]),
    ]

    for name, fn, sf in configs:
        sched = fn(day=day, **common)
        algo_result = _build_result(name, sched, arrival_price,
                                    order_shares, market_data.adv_shares,
                                    market_data.realized_vol_ann, sf)
        result.algos[name] = algo_result
        _log(f"  {name}: slip={algo_result.slippage_bps:+.1f} bps  "
             f"MI={algo_result.market_impact_bps:.1f} bps  "
             f"total={algo_result.total_cost_bps:.1f} bps  "
             f"fill={algo_result.completion_pct:.0%}")

    _log("Agent 3 complete.")
    return result
