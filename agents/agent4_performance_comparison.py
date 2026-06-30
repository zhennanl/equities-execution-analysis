"""
Agent 4: Performance Comparison
1. Multi-day simulation: repeats Agent 3 logic across all available intraday days
2. Order-size sensitivity: total cost matrix across all algos × order sizes
3. Selects best algorithm by average total cost; counts daily wins
"""

import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from agents.agent1_market_data import MarketData, MARKET_INFO
from agents.agent3_algo_simulation import IMPACT_ETA, SPEED_FACTORS, POV_RATES, IS_LAMBDA


@dataclass
class PerformanceComparison:
    daily_costs: pd.DataFrame     # index=date, cols=VWAP/TWAP/POV/IS (total cost bps)
    daily_slips: pd.DataFrame     # same structure, slippage only
    summary: pd.DataFrame         # mean, std, min, max, win-days per algo
    sensitivity: pd.DataFrame     # index=algo, cols=order pct labels
    best_algo: str
    win_counts: dict


def _sim_day_all(day: pd.DataFrame, order_shares: float, urgency: str,
                 adv_shares: float, vol_ann: float) -> dict:
    """
    Simulate all 4 algos on a single day's bar data.
    Returns {algo_name: (slippage_bps, total_cost_bps)}.
    """
    n = len(day)
    if n < 3:
        return None

    closes  = day["Close"].values
    volumes = day["Volume"].values
    arrival = float(day["Open"].iloc[0]) if "Open" in day.columns else float(closes[0])
    sigma_d = vol_ann / np.sqrt(252)

    def _cost(shares, sf):
        filled = shares.sum()
        if filled <= 0:
            return 0.0, 0.0
        avg_px   = (shares * closes).sum() / filled
        slip     = (avg_px - arrival) / arrival * 10_000
        mi       = IMPACT_ETA * sigma_d * np.sqrt(order_shares / adv_shares) * sf * 10_000
        return round(slip, 2), round(slip + mi, 2)

    # VWAP
    tv = volumes.sum()
    vwap_w = volumes / tv * order_shares if tv > 0 else np.full(n, order_shares / n)
    vwap_slip, vwap_tot = _cost(vwap_w, SPEED_FACTORS["VWAP"])

    # TWAP
    twap_w = np.full(n, order_shares / n)
    twap_slip, twap_tot = _cost(twap_w, SPEED_FACTORS["TWAP"])

    # POV
    rate = POV_RATES[urgency]
    rem = order_shares
    pov_w = np.zeros(n)
    for i in range(n):
        if rem <= 0: break
        traded = min(rem, volumes[i] * rate)
        pov_w[i] = traded
        rem -= traded
    pov_slip, pov_tot = _cost(pov_w, SPEED_FACTORS["POV"])

    # IS
    lam = IS_LAMBDA[urgency]
    rw = np.exp(-lam * np.arange(n) / n)
    is_w = rw / rw.sum() * order_shares
    is_slip, is_tot = _cost(is_w, SPEED_FACTORS["IS"][urgency])

    return {
        "VWAP": (vwap_slip, vwap_tot),
        "TWAP": (twap_slip, twap_tot),
        "POV":  (pov_slip,  pov_tot),
        "IS":   (is_slip,   is_tot),
    }


def compare_performance(market_data: MarketData, order_pct_adv: float,
                        urgency: str, log=None) -> PerformanceComparison:
    def _log(msg):
        if log: log(msg)

    order_shares  = market_data.adv_shares * (order_pct_adv / 100)
    bars_expected = MARKET_INFO[market_data.market]["bars"]
    intraday      = market_data.intraday

    algos = ["VWAP", "TWAP", "POV", "IS"]
    cost_rows, slip_rows = [], []
    win_counts = {a: 0 for a in algos}

    # ── Multi-day loop ────────────────────────────────────────────────────────
    for d in sorted(intraday.index.normalize().unique()):
        day = intraday[intraday.index.normalize() == d]
        if len(day) < int(bars_expected * 0.5):
            continue
        res = _sim_day_all(day, order_shares, urgency,
                           market_data.adv_shares, market_data.realized_vol_ann)
        if res is None:
            continue
        cost_row = {"date": d.date(), **{a: res[a][1] for a in algos}}
        slip_row = {"date": d.date(), **{a: res[a][0] for a in algos}}
        cost_rows.append(cost_row)
        slip_rows.append(slip_row)

        best_day = min(algos, key=lambda a: res[a][1])
        win_counts[best_day] += 1
        _log(f"  {d.date()}: best={best_day} ({res[best_day][1]:.1f} bps)")

    daily_costs = pd.DataFrame(cost_rows).set_index("date")
    daily_slips = pd.DataFrame(slip_rows).set_index("date")

    summary = pd.DataFrame({
        "Mean (bps)": daily_costs.mean(),
        "Std (bps)":  daily_costs.std().fillna(0),
        "Min (bps)":  daily_costs.min(),
        "Max (bps)":  daily_costs.max(),
        "Win Days":   pd.Series(win_counts),
    }).round(1)

    # ── Order-size sensitivity ────────────────────────────────────────────────
    pct_range  = [1, 5, 10, 15, 20, 25]
    sigma_d    = market_data.realized_vol_ann / np.sqrt(252)
    mean_slips = daily_slips.mean().to_dict()

    sens_rows = {}
    for algo in algos:
        sf  = SPEED_FACTORS[algo] if algo != "IS" else SPEED_FACTORS["IS"][urgency]
        row = {}
        for pct in pct_range:
            q  = market_data.adv_shares * (pct / 100)
            mi = IMPACT_ETA * sigma_d * np.sqrt(q / market_data.adv_shares) * sf * 10_000
            row[f"{pct}% ADV"] = round(mean_slips.get(algo, 0.0) + mi, 1)
        sens_rows[algo] = row

    sensitivity = pd.DataFrame(sens_rows).T

    best_algo = summary["Mean (bps)"].idxmin()
    _log(f"Best algo: {best_algo}  avg {summary.loc[best_algo, 'Mean (bps)']:.1f} bps")
    _log("Agent 4 complete.")

    return PerformanceComparison(
        daily_costs=daily_costs,
        daily_slips=daily_slips,
        summary=summary,
        sensitivity=sensitivity,
        best_algo=best_algo,
        win_counts=win_counts,
    )
