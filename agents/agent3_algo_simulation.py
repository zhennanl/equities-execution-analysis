"""
Agent 3: Algorithm Simulation Agent
Simulates VWAP, TWAP, POV, Implementation Shortfall, Market-on-Close,
Market-on-Open, Liquidity-Seeking, and Stealth on a synthetic buy order
using real intraday price/volume data from Agent 1.

Metrics per algorithm:
  - Slippage (bps):          (avg_exec_price - arrival_price) / arrival_price * 10000
  - Market impact (bps):     Square-root model — sigma_daily * sqrt(Q/ADV) * eta * speed_factor.
                              The square-root law is one of the more robust empirical findings in
                              market microstructure — recent work on a full Tokyo Stock Exchange
                              census (Bacry/Bouchaud-style studies) finds the same exponent across
                              stocks, traders, options, and even crypto, rejecting the leading
                              "non-universal" alternative models. That's the justification for
                              using sqrt(Q/ADV) here rather than a linear impact model.
  - Opportunity cost (bps):  Perold's (1988) Implementation Shortfall framework prices the
                              unfilled portion of an order against the period-end price relative
                              to arrival — a buy order that never completes "missed" any run-up
                              (positive cost) or was spared any decline (negative cost) versus a
                              hypothetical fully-filled paper portfolio. POV, Liquidity-Seeking and
                              Stealth can all complete under 100%; without this term their partial
                              fills look artificially cheap because the unfilled shares simply
                              vanish from the average instead of being charged for non-participation.
  - Total cost (bps):        Slippage + Market Impact + Opportunity Cost.
  - Completion (%):          For POV/Liquidity-Seeking/Stealth, may not fill 100% if liquidity or
                              the participation cap is limiting.

Data caveat — MOC / MOO / Liquidity-Seeking / Stealth:
  All four are approximations built on 5-min OHLCV bars only (no order book,
  no dark-pool prints, no auction-specific depth are available for free at
  intraday granularity across the 14 supported markets — confirmed via
  research into Databento, IBKR TWS, Moomoo L2, and FINRA OTC Transparency,
  none of which offer free historical intraday microstructure data for this
  use case). Slippage for every algorithm, including MOC/MOO, is still
  measured against the session arrival (open) price so results stay
  comparable — real MOC/MOO desks would benchmark against the closing/
  opening auction print instead.

Look-ahead bias fix (VWAP / MOC / MOO):
  The original implementation built each of these schedules from the exact
  intraday day being simulated — e.g. VWAP allocated shares in proportion to
  that day's own realized volume curve, something a real-time algorithm
  cannot see in advance. _historical_volume_weights() now builds the schedule
  from the OTHER days available in Agent 1's fetch window instead (a rolling
  historical curve in spirit, given yfinance's 5-day intraday cap), and prices
  fills against the real day's prices. POV / Liquidity-Seeking / Stealth are
  unaffected: they already react bar-by-bar to realized volume as it prints,
  which is causal (no future information), not a forecast.

Implementation Shortfall trajectory:
  IS now uses the actual Almgren & Chriss (2000) closed-form optimal
  trajectory (a sinh-weighted front-loaded schedule controlled by a
  dimensionless risk-aversion product kappa*T) instead of an ad hoc
  exponential decay — see _ac_trajectory_weights() and ac_efficient_frontier().

Future work — reinforcement learning: a 2025 industry survey found hybrid
RL-plus-domain-knowledge approaches overtaking pure RL in adoption (15%->42%
vs 85%->58%, 2020-2025), with implementation quality and domain knowledge
mattering more than algorithm sophistication. This module's rule-based
schedules layered under Agent 4's data-driven comparison and Agent 5's
rule-based selection is structurally that same hybrid pattern. A full RL
execution agent would need historical fill/reward data this yfinance-only
pipeline doesn't have, so it's noted here as a direction rather than built.
"""

import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from agents.agent1_market_data import MarketData, MARKET_INFO


# Market impact coefficient (empirical, typical range 0.2-0.5 across the
# square-root-law literature)
IMPACT_ETA = 0.3

# Speed factors scale market impact per algo (relative to neutral baseline)
SPEED_FACTORS = {
    "TWAP":    0.85,   # most passive — spread evenly over time
    "VWAP":    0.90,   # follows volume curve — slightly passive
    "POV":     1.00,   # neutral — depends on participation rate
    "IS":      {"Low": 1.20, "Medium": 1.55, "High": 2.00},  # front-loaded = higher impact
    "MOC":     0.80,   # concentrated in the close — closing auction assumed to absorb size well
    "MOO":     1.05,   # concentrated in the open — opening print carries more adverse-selection risk
    "LIQ":     {"Low": 0.70, "Medium": 0.85, "High": 1.05},  # opportunistic — lower footprint, scales with urgency
    "STEALTH": {"Low": 0.55, "Medium": 0.65, "High": 0.80},  # capped participation — designed for minimal footprint
}

POV_RATES     = {"Low": 0.10, "Medium": 0.15, "High": 0.20}

# Implementation Shortfall: dimensionless Almgren-Chriss risk-aversion product
# kappa*T. kappa*T -> 0 collapses to a uniform (TWAP-like) schedule; larger
# values front-load execution more aggressively. See _ac_trajectory_weights().
IS_KAPPA_T    = {"Low": 0.3, "Medium": 1.5, "High": 4.0}

# Liquidity-Seeking: base participation rate tilted by short-term price favorability
LIQ_BASE_RATE = {"Low": 0.08, "Medium": 0.12, "High": 0.18}
LIQ_TILT_K    = 0.6     # sensitivity of participation to price-vs-recent-mean z-score
LIQ_ROLL_BARS = 6       # rolling window (bars) used to gauge "favorable" price

# Stealth: hard participation cap per bar + randomized child-order sizing
STEALTH_CAP   = {"Low": 0.03, "Medium": 0.05, "High": 0.08}

# MOC / MOO: fraction of the session's bars treated as the "closing"/"opening" window
MOC_WINDOW_PCT = 0.15
MOO_WINDOW_PCT = 0.15

# Minimum number of "other" days required in Agent 1's intraday fetch before
# we'll build a historical volume-share curve; below this we fall back to the
# day's own realized volume (the pre-fix behavior) and flag it as such.
MIN_HISTORY_DAYS = 2


def _speed_factor(name: str, urgency: str) -> float:
    """Look up an algo's speed factor, resolving urgency-dependent dict entries."""
    sf = SPEED_FACTORS[name]
    return sf[urgency] if isinstance(sf, dict) else sf


@dataclass
class AlgoResult:
    name: str
    arrival_price: float
    avg_exec_price: float
    slippage_bps: float
    market_impact_bps: float
    opportunity_cost_bps: float    # Perold (1988): cost of unfilled shares vs period-end price
    total_cost_bps: float          # slippage + market impact + opportunity cost
    completion_pct: float          # 1.0 for VWAP/TWAP/IS/MOC/MOO; may be < 1.0 for POV/LIQ/STEALTH
    unfilled_shares: float
    schedule_note: str             # data-source caveat: historical curve / same-day fallback / causal / N/A
    schedule: pd.DataFrame          # columns: time, shares_traded, price, cumulative


@dataclass
class SimulationResult:
    ticker: str
    order_shares: float
    order_pct_adv: float
    urgency: str
    arrival_price: float
    algos: dict = field(default_factory=dict)   # name -> AlgoResult


# -- Helpers ----------------------------------------------------------------

def _sim_day(intraday: pd.DataFrame, bars_expected: int) -> pd.DataFrame:
    """Return the most recent day with >=80% of expected bars (most complete day)."""
    dates = sorted(intraday.index.normalize().unique())
    for d in reversed(dates):
        day = intraday[intraday.index.normalize() == d]
        if len(day) >= int(bars_expected * 0.8):
            return day.copy()
    return intraday[intraday.index.normalize() == dates[-1]].copy()


def _historical_volume_weights(intraday: pd.DataFrame, sim_date, n_bars: int):
    """
    Build a bar-by-bar historical volume-share curve (length n_bars, sums to 1)
    from every OTHER day present in `intraday`, matched by time-of-day. This is
    the schedule a real VWAP/MOC/MOO algo has to use, since it cannot see the
    current day's own future volume — using the day's own realized volume to
    build its own schedule (the original implementation) is a look-ahead bias.

    In a live deployment this would be a rolling N-day trailing average; since
    Agent 1 only fetches a 5-day intraday window from yfinance, we use every
    other day available in that window (before AND after the simulated day) as
    the closest practical proxy. This still removes the core bug — using a
    day's own future bars to schedule that same day — even though it isn't a
    strictly trailing-only window.

    Returns (weights, n_history_days). weights is None if fewer than
    MIN_HISTORY_DAYS other days are available; caller should then fall back to
    the day's own realized volume and flag it as such.
    """
    sim_norm = pd.Timestamp(sim_date).normalize()
    other = intraday[intraday.index.normalize() != sim_norm]
    n_history_days = other.index.normalize().nunique() if len(other) else 0
    if n_history_days < MIN_HISTORY_DAYS:
        return None, n_history_days

    other = other.copy()
    other["_t"] = other.index.strftime("%H:%M")
    curve = other.groupby("_t")["Volume"].mean().sort_index()
    if len(curve) < n_bars:
        return None, n_history_days

    weights = curve.iloc[:n_bars].values.astype(float)
    total = weights.sum()
    if total <= 0:
        return None, n_history_days
    return weights / total, n_history_days


def _ac_trajectory_weights(n: int, kappa_T: float) -> np.ndarray:
    """
    Discrete Almgren & Chriss (2000) optimal-execution trajectory, parameterized
    by the dimensionless product kappa*T (risk-aversion intensity over the
    trading horizon). With x_j the *remaining* position after bar j:
        x_j / X = sinh(kappa*(T - t_j)) / sinh(kappa*T)
    Shares traded in bar j = x_(j-1) - x_j. As kappa*T -> 0 this collapses to a
    uniform (TWAP-like) schedule — the correct zero-risk-aversion limit under a
    linear temporary-impact cost, since trajectory shape doesn't affect
    expected cost when there's no variance to hedge against. Larger kappa*T
    front-loads execution more aggressively, approaching immediate liquidation.

    We parameterize directly by kappa*T rather than deriving kappa from a
    separately-fit temporary-impact coefficient, risk-aversion lambda, and
    volatility — only that product determines the trajectory's shape, which
    keeps the model tractable without inventing an extra, uncalibrated constant
    on top of the square-root law already used for cost magnitude.
    """
    if kappa_T < 1e-6:
        return np.full(n, 1.0 / n)
    t = np.linspace(0.0, 1.0, n + 1)
    remaining = np.sinh(kappa_T * (1 - t)) / np.sinh(kappa_T)
    traded = -np.diff(remaining)
    traded = np.clip(traded, 0, None)
    total = traded.sum()
    return traded / total if total > 0 else np.full(n, 1.0 / n)


def ac_efficient_frontier(n_bars: int, kappa_T_grid=(0.1, 0.3, 0.6, 1.0, 1.5, 2.5, 4.0, 6.0)) -> pd.DataFrame:
    """
    Almgren-Chriss cost/risk trade-off: for a grid of kappa*T values, reports
    how front-loaded the resulting trajectory is versus a timing-risk proxy
    (the variance of the remaining, unhedged position integrated over the
    trading horizon — the same quantity AC's risk term penalizes). Higher
    kappa*T buys lower timing risk at the cost of more front-loaded impact.
    risk_score_norm is normalized to the most patient schedule in the grid.
    """
    tau = 1.0 / n_bars
    rows = []
    for kT in kappa_T_grid:
        w = _ac_trajectory_weights(n_bars, kT)
        remaining_frac = np.clip(1 - np.cumsum(w), 0, None)
        risk = float(np.sum(remaining_frac ** 2) * tau)
        rows.append({
            "kappa_T": kT,
            "pct_in_first_third": round(float(w[:max(1, n_bars // 3)].sum() * 100), 1),
            "risk_score": risk,
        })
    df = pd.DataFrame(rows)
    max_risk = df["risk_score"].max()
    df["risk_score_norm"] = (df["risk_score"] / max_risk) if max_risk > 0 else df["risk_score"]
    return df


def _build_result(name, schedule_df, arrival_price, order_shares,
                  adv_shares, vol_ann, speed_factor, period_end_price,
                  schedule_note=""):
    filled = schedule_df["shares_traded"].sum()
    if filled == 0:
        avg_px = arrival_price
    else:
        avg_px = (schedule_df["shares_traded"] * schedule_df["price"]).sum() / filled

    slippage_bps    = (avg_px - arrival_price) / arrival_price * 10_000
    sigma_daily     = vol_ann / np.sqrt(252)
    mi_bps          = IMPACT_ETA * sigma_daily * np.sqrt(order_shares / adv_shares) * speed_factor * 10_000
    completion_pct  = min(filled / order_shares, 1.0) if order_shares > 0 else 1.0
    unfilled_shares = max(0.0, order_shares - filled)

    # Perold (1988) opportunity cost: unfilled shares are marked against the
    # period-end price relative to arrival.
    opp_cost_bps = (
        (unfilled_shares / order_shares) * (period_end_price - arrival_price) / arrival_price * 10_000
        if order_shares > 0 else 0.0
    )

    total_bps = slippage_bps + mi_bps + opp_cost_bps

    return AlgoResult(
        name=name,
        arrival_price=arrival_price,
        avg_exec_price=avg_px,
        slippage_bps=round(slippage_bps, 2),
        market_impact_bps=round(mi_bps, 2),
        opportunity_cost_bps=round(opp_cost_bps, 2),
        total_cost_bps=round(total_bps, 2),
        completion_pct=round(completion_pct, 4),
        unfilled_shares=round(unfilled_shares, 2),
        schedule_note=schedule_note,
        schedule=schedule_df,
    )


# -- Algorithm schedules ------------------------------------------------------

def _sim_vwap(day: pd.DataFrame, order_shares: float, hist_curve=None, **kw) -> pd.DataFrame:
    n = len(day)
    if hist_curve is not None and len(hist_curve) == n:
        shares = hist_curve * order_shares
    else:
        total_vol = day["Volume"].sum()
        if total_vol == 0:
            shares = np.ones(n) * order_shares / n
        else:
            shares = (day["Volume"] / total_vol * order_shares).values
    return pd.DataFrame({
        "time": day.index,
        "shares_traded": shares,
        "price": day["Close"].values,
        "cumulative": np.cumsum(shares),
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
    n = len(day)
    weights = _ac_trajectory_weights(n, IS_KAPPA_T[urgency])
    shares = weights * order_shares
    return pd.DataFrame({
        "time": day.index,
        "shares_traded": shares,
        "price": day["Close"].values,
        "cumulative": np.cumsum(shares),
    })


def _sim_moc(day: pd.DataFrame, order_shares: float, hist_curve=None, **kw) -> pd.DataFrame:
    """
    Market-on-Close: hold back essentially all size until the closing window
    (last MOC_WINDOW_PCT of bars), then allocate proportional to volume within
    that window — approximating participation concentrated into the close/
    closing auction. Uses the historical volume curve's shape within the
    window when available (see _historical_volume_weights), falling back to
    the day's own realized volume in that window otherwise.
    """
    n = len(day)
    shares = np.zeros(n)
    w = max(1, int(round(n * MOC_WINDOW_PCT)))
    if hist_curve is not None and len(hist_curve) == n:
        window_w = hist_curve[-w:]
        tv = window_w.sum()
        shares[-w:] = (window_w / tv * order_shares) if tv > 0 else (order_shares / w)
    else:
        window_vol = day["Volume"].values[-w:]
        tv = window_vol.sum()
        shares[-w:] = (window_vol / tv * order_shares) if tv > 0 else (order_shares / w)
    return pd.DataFrame({
        "time": day.index,
        "shares_traded": shares,
        "price": day["Close"].values,
        "cumulative": np.cumsum(shares),
    })


def _sim_moo(day: pd.DataFrame, order_shares: float, hist_curve=None, **kw) -> pd.DataFrame:
    """
    Market-on-Open: concentrate essentially all size into the opening window
    (first MOO_WINDOW_PCT of bars), allocated proportional to volume within
    that window — approximating participation in the open/opening auction.
    Uses the historical volume curve's shape within the window when
    available, falling back to the day's own realized volume otherwise.
    """
    n = len(day)
    shares = np.zeros(n)
    w = max(1, int(round(n * MOO_WINDOW_PCT)))
    if hist_curve is not None and len(hist_curve) == n:
        window_w = hist_curve[:w]
        tv = window_w.sum()
        shares[:w] = (window_w / tv * order_shares) if tv > 0 else (order_shares / w)
    else:
        window_vol = day["Volume"].values[:w]
        tv = window_vol.sum()
        shares[:w] = (window_vol / tv * order_shares) if tv > 0 else (order_shares / w)
    return pd.DataFrame({
        "time": day.index,
        "shares_traded": shares,
        "price": day["Close"].values,
        "cumulative": np.cumsum(shares),
    })


def _sim_liquidity_seeking(day: pd.DataFrame, order_shares: float, urgency: str, **kw) -> pd.DataFrame:
    """
    Liquidity-Seeking: opportunistic participation that tilts up when price is
    favorable relative to its recent short-term mean (a dip, for a buy order)
    and tilts down when unfavorable — approximating "seek liquidity based on
    price, minimize footprint" behavior without real order-book/dark-pool data.
    Reacts bar-by-bar to realized volume as it prints (causal), so this isn't
    subject to the look-ahead-bias fix applied to VWAP/MOC/MOO.
    """
    n = len(day)
    closes  = day["Close"].values
    volumes = day["Volume"].values
    base_rate = LIQ_BASE_RATE[urgency]

    remaining = order_shares
    shares = np.zeros(n)
    for i in range(n):
        if remaining <= 0:
            break
        lo = max(0, i - LIQ_ROLL_BARS)
        window = closes[lo:i + 1]
        mean = window.mean()
        std = window.std()
        std = std if std > 1e-9 else 1e-9
        z = (mean - closes[i]) / std       # >0 => price dipped below recent mean => favorable to buy
        mult = float(np.clip(1 + LIQ_TILT_K * z, 0.2, 2.5))
        tradeable = volumes[i] * base_rate * mult
        traded = min(remaining, tradeable)
        shares[i] = traded
        remaining -= traded

    return pd.DataFrame({
        "time": day.index,
        "shares_traded": shares,
        "price": day["Close"].values,
        "cumulative": np.cumsum(shares),
    })


def _sim_stealth(day: pd.DataFrame, order_shares: float, urgency: str, **kw) -> pd.DataFrame:
    """
    Stealth: low-footprint variant of TWAP — near-equal target size per bar,
    randomized child-order sizing (jitter), and a hard per-bar participation
    cap so no single clip is large enough to signal the order. Unfilled
    target carries forward to later bars (iceberg-style), which may leave the
    order incomplete if the cap binds throughout the session. Reacts bar-by-bar
    to realized volume as it prints (causal) — not subject to the look-ahead
    fix applied to VWAP/MOC/MOO.
    """
    n = len(day)
    volumes = day["Volume"].values
    cap_rate = STEALTH_CAP[urgency]
    target = order_shares / n

    seed = abs(hash((str(day.index[0]), round(order_shares, 2), n))) % (2**32)
    rng = np.random.RandomState(seed)

    remaining = order_shares
    shares = np.zeros(n)
    carry = 0.0
    for i in range(n):
        if remaining <= 0:
            break
        jitter = rng.uniform(0.7, 1.3)
        want = target * jitter + carry
        cap = volumes[i] * cap_rate
        traded = min(remaining, want, cap)
        shares[i] = traded
        carry = max(0.0, want - traded)
        remaining -= traded

    return pd.DataFrame({
        "time": day.index,
        "shares_traded": shares,
        "price": day["Close"].values,
        "cumulative": np.cumsum(shares),
    })


# -- Main entry point ---------------------------------------------------------

def simulate_algos(market_data: MarketData, order_pct_adv: float,
                   urgency: str, log=None) -> SimulationResult:
    """
    Run all eight algorithm simulations and return comparable results.

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
    n = len(day)

    arrival_price = float(day["Open"].iloc[0]) if "Open" in day.columns else float(day["Close"].iloc[0])
    period_end_price = float(day["Close"].iloc[-1])
    sim_date = day.index[0].normalize()

    hist_curve, n_hist_days = _historical_volume_weights(market_data.intraday, sim_date, n)
    if hist_curve is not None:
        schedule_note_vol = f"Historical {n_hist_days}-day volume curve (excl. simulated day)"
    else:
        schedule_note_vol = f"Same-day realized volume ({n_hist_days} other day(s) available — insufficient history)"

    _log(f"Simulating on {day.index[0].date()} · {n} bars · arrival={arrival_price:.2f}")
    _log(f"  Volume-based schedules (VWAP/MOC/MOO): {schedule_note_vol}")

    result = SimulationResult(
        ticker=market_data.ticker,
        order_shares=order_shares,
        order_pct_adv=order_pct_adv,
        urgency=urgency,
        arrival_price=arrival_price,
    )

    common = dict(order_shares=order_shares, urgency=urgency,
                  adv_shares=market_data.adv_shares, vol_ann=market_data.realized_vol_ann,
                  hist_curve=hist_curve)

    configs = [
        ("VWAP",    _sim_vwap,              _speed_factor("VWAP", urgency),    schedule_note_vol),
        ("TWAP",    _sim_twap,              _speed_factor("TWAP", urgency),    "Time-based (no volume data needed)"),
        ("POV",     _sim_pov,               _speed_factor("POV", urgency),     "Same-bar realized volume (causal)"),
        ("IS",      _sim_is,                _speed_factor("IS", urgency),      f"Almgren-Chriss trajectory (kappa*T={IS_KAPPA_T[urgency]})"),
        ("MOC",     _sim_moc,               _speed_factor("MOC", urgency),     schedule_note_vol),
        ("MOO",     _sim_moo,               _speed_factor("MOO", urgency),     schedule_note_vol),
        ("LIQ",     _sim_liquidity_seeking, _speed_factor("LIQ", urgency),     "Same-bar realized volume (causal)"),
        ("STEALTH", _sim_stealth,           _speed_factor("STEALTH", urgency), "Same-bar realized volume (causal)"),
    ]

    for name, fn, sf, note in configs:
        sched = fn(day=day, **common)
        algo_result = _build_result(name, sched, arrival_price,
                                    order_shares, market_data.adv_shares,
                                    market_data.realized_vol_ann, sf,
                                    period_end_price, schedule_note=note)
        result.algos[name] = algo_result
        _log(f"  {name}: slip={algo_result.slippage_bps:+.1f} bps  "
             f"MI={algo_result.market_impact_bps:.1f} bps  "
             f"opp={algo_result.opportunity_cost_bps:+.1f} bps  "
             f"total={algo_result.total_cost_bps:.1f} bps  "
             f"fill={algo_result.completion_pct:.0%}")

    _log("Agent 3 complete.")
    return result
