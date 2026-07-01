"""
Agent 4: Performance Comparison
1. Multi-day simulation: repeats Agent 3 logic (VWAP, TWAP, POV, IS, MOC, MOO,
   Liquidity-Seeking, Stealth) across all available intraday days
2. Order-size sensitivity: total cost matrix across all algos x order sizes,
   computed by actually re-simulating each size on each day (not a formula
   shortcut) so fill-rate degradation and Perold opportunity cost show up
   correctly at larger sizes for POV/Liquidity-Seeking/Stealth
3. Selects best algorithm by average total cost; counts daily wins
4. Reports the Almgren-Chriss cost/risk efficient frontier (ac_frontier) so
   the urgency-to-front-loading mapping used by IS can be shown, not just
   asserted

See agent3_algo_simulation.py's module docstring for the square-root-law,
look-ahead-bias, Perold opportunity-cost, and Almgren-Chriss background this
module inherits.
"""

import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from agents.agent1_market_data import MarketData, MARKET_INFO
from agents.agent3_algo_simulation import (
    IMPACT_ETA, SPEED_FACTORS, POV_RATES, IS_KAPPA_T,
    LIQ_BASE_RATE, LIQ_TILT_K, LIQ_ROLL_BARS, STEALTH_CAP,
    MOC_WINDOW_PCT, MOO_WINDOW_PCT,
    _historical_volume_weights, _ac_trajectory_weights, ac_efficient_frontier,
)


@dataclass
class PerformanceComparison:
    daily_costs: pd.DataFrame     # index=date, cols=algo names (total cost bps, incl. opportunity cost)
    daily_slips: pd.DataFrame     # same structure, slippage only
    summary: pd.DataFrame         # mean, std, min, max, win-days per algo
    sensitivity: pd.DataFrame     # index=algo, cols=order pct labels (re-simulated, not a formula shortcut)
    best_algo: str
    win_counts: dict
    ac_frontier: pd.DataFrame     # Almgren-Chriss kappa*T grid: front-loading % vs risk proxy


def _sim_day_all(day: pd.DataFrame, order_shares: float, urgency: str,
                 adv_shares: float, vol_ann: float, hist_curve=None) -> dict:
    """
    Simulate all 8 algos on a single day's bar data.
    Returns {algo_name: (slippage_bps, total_cost_bps)}. total_cost_bps is
    slippage + market impact + Perold (1988) opportunity cost on any unfilled
    shares (priced against the day's period-end close vs arrival).

    hist_curve, if provided, is the leave-one-out historical volume-share
    curve from _historical_volume_weights() -- used to schedule VWAP/MOC/MOO
    instead of this day's own realized volume (look-ahead-bias fix). POV /
    Liquidity-Seeking / Stealth react bar-by-bar to realized volume as it
    prints, which is causal, so they don't use hist_curve.
    """
    n = len(day)
    if n < 3:
        return None

    closes  = day["Close"].values
    volumes = day["Volume"].values
    arrival = float(day["Open"].iloc[0]) if "Open" in day.columns else float(closes[0])
    period_end = float(closes[-1])
    sigma_d = vol_ann / np.sqrt(252)

    def _cost(shares, sf):
        filled = shares.sum()
        if filled <= 0:
            return 0.0, 0.0
        avg_px   = (shares * closes).sum() / filled
        slip     = (avg_px - arrival) / arrival * 10_000
        mi       = IMPACT_ETA * sigma_d * np.sqrt(order_shares / adv_shares) * sf * 10_000
        unfilled = max(0.0, order_shares - filled)
        opp      = ((unfilled / order_shares) * (period_end - arrival) / arrival * 10_000
                    if order_shares > 0 else 0.0)
        return round(slip, 2), round(slip + mi + opp, 2)

    # VWAP
    if hist_curve is not None and len(hist_curve) == n:
        vwap_w = hist_curve * order_shares
    else:
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

    # IS -- Almgren-Chriss trajectory (replaces the old ad hoc exponential decay)
    is_w = _ac_trajectory_weights(n, IS_KAPPA_T[urgency]) * order_shares
    is_slip, is_tot = _cost(is_w, SPEED_FACTORS["IS"][urgency])

    # MOC -- concentrate into the closing window, historical shape when available
    w_close = max(1, int(round(n * MOC_WINDOW_PCT)))
    moc_w = np.zeros(n)
    if hist_curve is not None and len(hist_curve) == n:
        close_w = hist_curve[-w_close:]
        tv_c = close_w.sum()
        moc_w[-w_close:] = (close_w / tv_c * order_shares) if tv_c > 0 else (order_shares / w_close)
    else:
        close_vol = volumes[-w_close:]
        tv_c = close_vol.sum()
        moc_w[-w_close:] = (close_vol / tv_c * order_shares) if tv_c > 0 else (order_shares / w_close)
    moc_slip, moc_tot = _cost(moc_w, SPEED_FACTORS["MOC"])

    # MOO -- concentrate into the opening window, historical shape when available
    w_open = max(1, int(round(n * MOO_WINDOW_PCT)))
    moo_w = np.zeros(n)
    if hist_curve is not None and len(hist_curve) == n:
        open_w = hist_curve[:w_open]
        tv_o = open_w.sum()
        moo_w[:w_open] = (open_w / tv_o * order_shares) if tv_o > 0 else (order_shares / w_open)
    else:
        open_vol = volumes[:w_open]
        tv_o = open_vol.sum()
        moo_w[:w_open] = (open_vol / tv_o * order_shares) if tv_o > 0 else (order_shares / w_open)
    moo_slip, moo_tot = _cost(moo_w, SPEED_FACTORS["MOO"])

    # Liquidity-Seeking -- participation tilted by short-term price favorability
    base_rate = LIQ_BASE_RATE[urgency]
    remaining = order_shares
    liq_w = np.zeros(n)
    for i in range(n):
        if remaining <= 0:
            break
        lo = max(0, i - LIQ_ROLL_BARS)
        window = closes[lo:i + 1]
        mean = window.mean()
        std = window.std()
        std = std if std > 1e-9 else 1e-9
        z = (mean - closes[i]) / std
        mult = float(np.clip(1 + LIQ_TILT_K * z, 0.2, 2.5))
        traded = min(remaining, volumes[i] * base_rate * mult)
        liq_w[i] = traded
        remaining -= traded
    liq_slip, liq_tot = _cost(liq_w, SPEED_FACTORS["LIQ"][urgency])

    # Stealth -- capped, randomized, near-equal participation (iceberg-style)
    cap_rate = STEALTH_CAP[urgency]
    target = order_shares / n
    seed = abs(hash((str(day.index[0]), round(order_shares, 2), n))) % (2**32)
    rng = np.random.RandomState(seed)
    remaining = order_shares
    stealth_w = np.zeros(n)
    carry = 0.0
    for i in range(n):
        if remaining <= 0:
            break
        jitter = rng.uniform(0.7, 1.3)
        want = target * jitter + carry
        cap = volumes[i] * cap_rate
        traded = min(remaining, want, cap)
        stealth_w[i] = traded
        carry = max(0.0, want - traded)
        remaining -= traded
    stealth_slip, stealth_tot = _cost(stealth_w, SPEED_FACTORS["STEALTH"][urgency])

    return {
        "VWAP":    (vwap_slip,    vwap_tot),
        "TWAP":    (twap_slip,    twap_tot),
        "POV":     (pov_slip,     pov_tot),
        "IS":      (is_slip,      is_tot),
        "MOC":     (moc_slip,     moc_tot),
        "MOO":     (moo_slip,     moo_tot),
        "LIQ":     (liq_slip,     liq_tot),
        "STEALTH": (stealth_slip, stealth_tot),
    }


def compare_performance(market_data: MarketData, order_pct_adv: float,
                        urgency: str, log=None) -> PerformanceComparison:
    def _log(msg):
        if log: log(msg)

    order_shares  = market_data.adv_shares * (order_pct_adv / 100)
    bars_expected = MARKET_INFO[market_data.market]["bars"]
    intraday      = market_data.intraday
    adv_shares    = market_data.adv_shares
    vol_ann       = market_data.realized_vol_ann

    algos = ["VWAP", "TWAP", "POV", "IS", "MOC", "MOO", "LIQ", "STEALTH"]
    cost_rows, slip_rows = [], []
    win_counts = {a: 0 for a in algos}

    # -- Pre-compute each valid day + its leave-one-out historical curve ------
    valid_days = []
    for d in sorted(intraday.index.normalize().unique()):
        day = intraday[intraday.index.normalize() == d]
        if len(day) < int(bars_expected * 0.5):
            continue
        hist_curve, _n_hist = _historical_volume_weights(intraday, d, len(day))
        valid_days.append((d, day, hist_curve))

    # -- Multi-day loop at the requested order size ---------------------------
    for d, day, hist_curve in valid_days:
        res = _sim_day_all(day, order_shares, urgency, adv_shares, vol_ann, hist_curve=hist_curve)
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

    # -- Order-size sensitivity: real re-simulation, not a formula shortcut ---
    # (the previous version added mean-slippage + a formulaic sqrt-impact term
    # and ignored fill-rate degradation and opportunity cost entirely; POV/
    # Liquidity-Seeking/Stealth would have looked artificially cheap at large
    # sizes as a result)
    pct_range = [1, 5, 10, 15, 20, 25]
    sens_rows = {a: {} for a in algos}
    for pct in pct_range:
        q = adv_shares * (pct / 100)
        per_algo_costs = {a: [] for a in algos}
        for d, day, hist_curve in valid_days:
            res = _sim_day_all(day, q, urgency, adv_shares, vol_ann, hist_curve=hist_curve)
            if res is None:
                continue
            for a in algos:
                per_algo_costs[a].append(res[a][1])
        for a in algos:
            vals = per_algo_costs[a]
            sens_rows[a][f"{pct}% ADV"] = round(float(np.mean(vals)), 1) if vals else None

    sensitivity = pd.DataFrame(sens_rows).T

    ac_frontier = ac_efficient_frontier(bars_expected)

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
        ac_frontier=ac_frontier,
    )
