"""
Agent 4: Performance Comparison
1. Multi-day simulation: repeats Agent 3 logic (VWAP, TWAP, POV, IS, MOC, MOO,
   Liquidity-Seeking, Stealth) across all available intraday days
2. Order-size sensitivity: total cost matrix across all algos x order sizes,
   computed by actually re-simulating each size on each day (not a formula
   shortcut) so fill-rate degradation and Perold opportunity cost show up
   correctly at larger sizes for POV/Liquidity-Seeking/Stealth
3. Selects best algorithm by average total cost among algos that averaged at
   least FILL_QUALIFY_THRESH completion (falls back to the unfiltered
   minimum only if none qualify) -- otherwise a thinly-filled algo can look
   "best" purely on favorable ex-post opportunity-cost variance; counts
   daily wins under the same fill-qualified rule
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
from agents.order_ticket import constrain_fills, windowed_curve, excluded_algos
from agents.agent3_algo_simulation import (
    IMPACT_ETA, SPEED_FACTORS, POV_RATES, IS_KAPPA_T,
    LIQ_BASE_RATE, LIQ_TILT_K, LIQ_ROLL_BARS, STEALTH_CAP,
    MOC_WINDOW_PCT, MOO_WINDOW_PCT, FILL_QUALIFY_THRESH,
    _historical_volume_weights, _ac_trajectory_weights, ac_efficient_frontier,
)


@dataclass
class PerformanceComparison:
    daily_costs: pd.DataFrame     # index=date, cols=algo names (total cost bps, incl. opportunity cost)
    daily_slips: pd.DataFrame     # same structure, slippage only
    daily_impact: pd.DataFrame    # same structure, market impact (bps) only
    daily_opp: pd.DataFrame       # same structure, Perold opportunity cost (bps) only
    daily_fills: pd.DataFrame     # same structure, fill fraction (0-1)
    summary: pd.DataFrame         # mean, std, min, max, avg fill, win-days per algo
    sensitivity: pd.DataFrame     # index=algo, cols=order pct labels (re-simulated, not a formula shortcut)
    best_algo: str
    win_counts: dict
    ac_frontier: pd.DataFrame     # Almgren-Chriss kappa*T grid: front-loading % vs risk proxy


def _build_valid_days(market_data: MarketData) -> list:
    """
    Shared "which historical days are usable, and what's their leave-one-out
    historical volume curve" pre-pass -- factored out so agent10's hypothesis
    tests can re-simulate a different urgency/order-size config across
    EXACTLY the same day set Agent 4 used (paired-sample requirement: both
    arms of a hypothesis test must be compared on the same historical days),
    without duplicating this logic.
    """
    bars_expected = MARKET_INFO[market_data.market]["bars"]
    intraday = market_data.intraday
    valid_days = []
    for d in sorted(intraday.index.normalize().unique()):
        day = intraday[intraday.index.normalize() == d]
        if len(day) < int(bars_expected * 0.5):
            continue
        hist_curve, _n_hist = _historical_volume_weights(intraday, d, len(day))
        valid_days.append((d, day, hist_curve))
    return valid_days


def _sim_day_all(day: pd.DataFrame, order_shares: float, urgency: str,
                 adv_shares: float, vol_ann: float, hist_curve=None,
                 ticket=None) -> dict:
    """
    Simulate all 8 algos on a single day's bar data.
    Returns {algo_name: (slippage_bps, market_impact_bps, opportunity_cost_bps,
    total_cost_bps, fill_frac)}. total_cost_bps is slippage + market impact +
    Perold (1988) opportunity cost on any unfilled shares (priced against the
    day's period-end close vs arrival) -- the three components are also
    returned individually so callers (Agent 4's tables, Agent 10's hypothesis
    tests) can test/report on any one of them, not just the combined total.
    fill_frac is the fraction of order_shares actually completed on this day,
    used by compare_performance() to gate "best algo" selection on
    FILL_QUALIFY_THRESH so a thinly-filled algo can't win purely on favorable
    ex-post opportunity-cost variance.

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
    # Full-day anchors (decision price / period end) even under a ticket
    # window — slippage vs decision price then includes the window's delay
    # cost (institutionally correct IS treatment).
    arrival = float(day["Open"].iloc[0]) if "Open" in day.columns else float(closes[0])
    period_end = float(closes[-1])
    sigma_d = vol_ann / np.sqrt(252)

    ticket_active = ticket is not None and not ticket.is_default()
    if ticket_active:
        s_bar, e_bar = ticket.window_indices(day.index)
        if (s_bar, e_bar) != (0, n - 1):
            if hist_curve is not None and len(hist_curve) == n:
                hist_curve = windowed_curve(hist_curve, s_bar, e_bar)
            closes  = closes[s_bar:e_bar + 1]
            volumes = volumes[s_bar:e_bar + 1]
            n = len(closes)

    def _constrain(shares, exempt=frozenset()):
        if not ticket_active:
            return shares
        return constrain_fills(shares, closes, volumes,
                               cap_frac=ticket.cap_frac,
                               limit_price=ticket.effective_limit,
                               exempt=exempt)

    def _cost(shares, sf):
        filled = shares.sum()
        fill_frac = 1.0 if order_shares <= 0 else min(1.0, filled / order_shares)
        if filled <= 0:
            return 0.0, 0.0, 0.0, 0.0, round(fill_frac, 4)
        avg_px   = (shares * closes).sum() / filled
        slip     = (avg_px - arrival) / arrival * 10_000
        mi       = IMPACT_ETA * sigma_d * np.sqrt(order_shares / adv_shares) * sf * 10_000
        unfilled = max(0.0, order_shares - filled)
        opp      = ((unfilled / order_shares) * (period_end - arrival) / arrival * 10_000
                    if order_shares > 0 else 0.0)
        return round(slip, 2), round(mi, 2), round(opp, 2), round(slip + mi + opp, 2), round(fill_frac, 4)

    # VWAP
    if hist_curve is not None and len(hist_curve) == n:
        vwap_w = hist_curve * order_shares
    else:
        tv = volumes.sum()
        vwap_w = volumes / tv * order_shares if tv > 0 else np.full(n, order_shares / n)
    vwap_res = _cost(_constrain(vwap_w), SPEED_FACTORS["VWAP"])

    # TWAP
    twap_w = np.full(n, order_shares / n)
    twap_res = _cost(_constrain(twap_w), SPEED_FACTORS["TWAP"])

    # POV
    rate = POV_RATES[urgency]
    rem = order_shares
    pov_w = np.zeros(n)
    for i in range(n):
        if rem <= 0: break
        traded = min(rem, volumes[i] * rate)
        pov_w[i] = traded
        rem -= traded
    pov_res = _cost(_constrain(pov_w), SPEED_FACTORS["POV"])

    # IS -- Almgren-Chriss trajectory (replaces the old ad hoc exponential decay)
    is_w = _ac_trajectory_weights(n, IS_KAPPA_T[urgency]) * order_shares
    is_res = _cost(_constrain(is_w), SPEED_FACTORS["IS"][urgency])

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
    moc_res = _cost(_constrain(moc_w, exempt=frozenset({n - 1})), SPEED_FACTORS["MOC"])

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
    moo_res = _cost(_constrain(moo_w, exempt=frozenset({0})), SPEED_FACTORS["MOO"])

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
    liq_res = _cost(_constrain(liq_w), SPEED_FACTORS["LIQ"][urgency])

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
    stealth_res = _cost(_constrain(stealth_w), SPEED_FACTORS["STEALTH"][urgency])

    return {
        "VWAP": vwap_res, "TWAP": twap_res, "POV": pov_res, "IS": is_res,
        "MOC": moc_res, "MOO": moo_res, "LIQ": liq_res, "STEALTH": stealth_res,
    }


def compare_performance(market_data: MarketData, order_pct_adv: float,
                        urgency: str, log=None, ticket=None) -> PerformanceComparison:
    def _log(msg):
        if log: log(msg)

    order_shares  = market_data.adv_shares * (order_pct_adv / 100)
    bars_expected = MARKET_INFO[market_data.market]["bars"]
    intraday      = market_data.intraday
    adv_shares    = market_data.adv_shares
    vol_ann       = market_data.realized_vol_ann

    algos = ["VWAP", "TWAP", "POV", "IS", "MOC", "MOO", "LIQ", "STEALTH"]
    cost_rows, slip_rows, impact_rows, opp_rows = [], [], [], []
    win_counts = {a: 0 for a in algos}

    # -- Pre-compute each valid day + its leave-one-out historical curve ------
    valid_days = _build_valid_days(market_data)

    # Order-ticket exclusions (auction gating / execution window) apply
    # uniformly across all days, so filter the algo set once up front.
    if ticket is not None and not ticket.is_default() and valid_days:
        _d0, _day0, _hc0 = valid_days[0]
        _s0, _e0 = ticket.window_indices(_day0.index)
        _excl = excluded_algos(ticket, _s0, _e0, len(_day0))
        if _excl:
            algos = [a2 for a2 in algos if a2 not in _excl]
            win_counts = {a2: 0 for a2 in algos}

    # -- Multi-day loop at the requested order size ---------------------------
    # Tuple layout from _sim_day_all: (slip, mi, opp, total, fill)
    fill_rows = []
    for d, day, hist_curve in valid_days:
        res = _sim_day_all(day, order_shares, urgency, adv_shares, vol_ann, hist_curve=hist_curve, ticket=ticket)
        if res is None:
            continue
        cost_row   = {"date": d.date(), **{a: res[a][3] for a in algos}}
        slip_row   = {"date": d.date(), **{a: res[a][0] for a in algos}}
        impact_row = {"date": d.date(), **{a: res[a][1] for a in algos}}
        opp_row    = {"date": d.date(), **{a: res[a][2] for a in algos}}
        fill_row   = {"date": d.date(), **{a: res[a][4] for a in algos}}
        cost_rows.append(cost_row)
        slip_rows.append(slip_row)
        impact_rows.append(impact_row)
        opp_rows.append(opp_row)
        fill_rows.append(fill_row)

        # Fill-qualified "best day" -- an algo that barely filled shouldn't win
        # a day purely on favorable ex-post opportunity-cost variance. Fall
        # back to the unfiltered minimum only if nothing qualifies that day.
        qualifying_today = [a for a in algos if res[a][4] >= FILL_QUALIFY_THRESH]
        pool_today = qualifying_today if qualifying_today else algos
        best_day = min(pool_today, key=lambda a: res[a][3])
        win_counts[best_day] += 1
        _log(f"  {d.date()}: best={best_day} ({res[best_day][3]:.1f} bps, fill {res[best_day][4]:.0%})")

    daily_costs  = pd.DataFrame(cost_rows).set_index("date")
    daily_slips  = pd.DataFrame(slip_rows).set_index("date")
    daily_impact = pd.DataFrame(impact_rows).set_index("date")
    daily_opp    = pd.DataFrame(opp_rows).set_index("date")
    daily_fills  = pd.DataFrame(fill_rows).set_index("date")
    avg_fill = daily_fills.mean()

    summary = pd.DataFrame({
        "Mean (bps)": daily_costs.mean(),
        "Std (bps)":  daily_costs.std().fillna(0),
        "Min (bps)":  daily_costs.min(),
        "Max (bps)":  daily_costs.max(),
        "Avg Fill":   avg_fill,
        "Win Days":   pd.Series(win_counts),
    })
    bps_cols = ["Mean (bps)", "Std (bps)", "Min (bps)", "Max (bps)"]
    summary[bps_cols] = summary[bps_cols].round(1)
    summary["Avg Fill"] = summary["Avg Fill"].round(3)

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
            res = _sim_day_all(day, q, urgency, adv_shares, vol_ann, hist_curve=hist_curve, ticket=ticket)
            if res is None:
                continue
            for a in algos:
                per_algo_costs[a].append(res[a][3])
        for a in algos:
            vals = per_algo_costs[a]
            sens_rows[a][f"{pct}% ADV"] = round(float(np.mean(vals)), 1) if vals else None

    sensitivity = pd.DataFrame(sens_rows).T

    ac_frontier = ac_efficient_frontier(bars_expected)

    # Fill-qualified "best algo" -- same rationale as best_day above, applied
    # across the whole window. Falls back to the unfiltered global minimum
    # only if no algo averages >= FILL_QUALIFY_THRESH completion.
    qualifying = [a for a in algos if avg_fill[a] >= FILL_QUALIFY_THRESH]
    pool = qualifying if qualifying else algos
    best_algo = summary.loc[pool, "Mean (bps)"].idxmin()
    _log(
        f"Best algo: {best_algo}  avg {summary.loc[best_algo, 'Mean (bps)']:.1f} bps "
        f"(avg fill {summary.loc[best_algo, 'Avg Fill']:.0%})"
    )
    _log("Agent 4 complete.")

    return PerformanceComparison(
        daily_costs=daily_costs,
        daily_slips=daily_slips,
        daily_impact=daily_impact,
        daily_opp=daily_opp,
        daily_fills=daily_fills,
        summary=summary,
        sensitivity=sensitivity,
        best_algo=best_algo,
        win_counts=win_counts,
        ac_frontier=ac_frontier,
    )
