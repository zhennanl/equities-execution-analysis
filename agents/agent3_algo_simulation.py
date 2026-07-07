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
from agents.order_ticket import constrain_fills, windowed_curve, excluded_algos


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

# Minimum average fill rate (across the comparison window) an algo must clear
# to be eligible for "best algo" / "secondary" selection in Agent 4 / Agent 5.
# Without this, POV/Liquidity-Seeking/Stealth can win purely on favorable
# ex-post opportunity-cost variance from a low, unrepresentative fill (e.g.
# Stealth at 14.5% completion "winning" on a small sample) even though the
# order was barely executed. Algos below the threshold are still shown in the
# comparison table, just excluded from being recommended as primary/secondary
# unless every algo fails to qualify (in which case we fall back to the
# unfiltered global minimum rather than recommending nothing).
FILL_QUALIFY_THRESH = 0.90


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
    excluded: dict = field(default_factory=dict)    # name -> reason (order-ticket exclusions)
    constraint_notes: list = field(default_factory=list)  # active order-ticket constraints


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
        close_w = hist_curve[-w:]
        tv = close_w.sum()
        shares[-w:] = (close_w / tv * order_shares) if tv > 0 else (order_shares / w)
    else:
        close_vol = day["Volume"].values[-w:]
        tv = close_vol.sum()
        shares[-w:] = (close_vol / tv * order_shares) if tv > 0 else (order_shares / w)
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
        open_w = hist_curve[:w]
        tv = open_w.sum()
        shares[:w] = (open_w / tv * order_shares) if tv > 0 else (order_shares / w)
    else:
        open_vol = day["Volume"].values[:w]
        tv = open_vol.sum()
        shares[:w] = (open_vol / tv * order_shares) if tv > 0 else (order_shares / w)
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
                   urgency: str, log=None, ticket=None) -> SimulationResult:
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

    # -- Order-ticket constraints (institutional order parameters) ----------
    # Arrival (decision price) and period-end stay FULL-DAY anchors even when
    # the ticket's window restricts trading to part of the day: slippage vs
    # the decision price then implicitly measures the delay cost of the
    # window, which is the institutionally correct IS treatment.
    ticket_active = ticket is not None and not ticket.is_default()
    s_bar, e_bar, excl = 0, n - 1, {}
    if ticket_active:
        s_bar, e_bar = ticket.window_indices(day.index)
        excl = excluded_algos(ticket, s_bar, e_bar, n)
    if ticket_active and (s_bar, e_bar) != (0, n - 1):
        day_plan = day.iloc[s_bar:e_bar + 1]
        hist_curve_plan = windowed_curve(hist_curve, s_bar, e_bar)
        _log(f"  Order ticket: window bars {s_bar}..{e_bar} of {n}")
    else:
        day_plan, hist_curve_plan = day, hist_curve
    if ticket_active:
        for c in ticket.constraint_summary():
            _log(f"  Order ticket: {c}")

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
                  hist_curve=hist_curve_plan)

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
        if name in excl:
            result.excluded[name] = excl[name]
            _log(f"  {name}: EXCLUDED — {excl[name]}")
            continue
        sched = fn(day=day_plan, **common)
        if ticket_active:
            exempt = (frozenset({len(day_plan) - 1}) if name == "MOC"
                      else frozenset({0}) if name == "MOO" else frozenset())
            adj = constrain_fills(sched["shares_traded"].to_numpy(dtype=float),
                                  sched["price"].to_numpy(dtype=float),
                                  day_plan["Volume"].to_numpy(dtype=float),
                                  cap_frac=ticket.cap_frac,
                                  limit_price=ticket.effective_limit,
                                  exempt=exempt)
            sched = sched.assign(shares_traded=adj, cumulative=np.cumsum(adj))
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

    if ticket_active:
        result.constraint_notes = ticket.constraint_summary()

    _log("Agent 3 complete.")
    return result


# -- Live execution monitor / chained mid-session adjustment ------------------
#
# Generalizes a single "checkpoint and resume" switch into an arbitrary CHAIN
# of interventions -- a trader watching the blotter can act more than once in
# a session, not just at one point -- and attaches per-bar RUNNING metrics
# (cumulative avg execution price vs. two passive market benchmarks: interval
# VWAP-to-date and interval TWAP-to-date) so the app can plot how the
# execution is tracking its benchmark as the (simulated) session unfolds,
# not just report a single end-of-day number. This is what lets the UI show
# "is this algo behaving suboptimally *right now*", which a single final
# total-cost figure cannot.

_ALGO_FUNCS = {
    "VWAP": _sim_vwap, "TWAP": _sim_twap, "POV": _sim_pov, "IS": _sim_is,
    "MOC": _sim_moc, "MOO": _sim_moo, "LIQ": _sim_liquidity_seeking, "STEALTH": _sim_stealth,
}


def _running_benchmark_curves(day: pd.DataFrame):
    """
    Interval (expanding-window) VWAP and TWAP computed from the day's own
    realized OHLCV -- a passive market benchmark independent of our simulated
    order's own fills, exactly the "how am I doing vs. VWAP-to-date" number a
    real intraday TCA dashboard shows. Returns (vwap_to_date, twap_to_date),
    each a length-n array aligned to `day`'s bar index.
    """
    closes  = day["Close"].values.astype(float)
    volumes = day["Volume"].values.astype(float)
    cum_vol      = np.cumsum(volumes)
    cum_notional = np.cumsum(closes * volumes)
    with np.errstate(divide="ignore", invalid="ignore"):
        vwap_to_date = np.where(cum_vol > 0, cum_notional / cum_vol, closes[0])
    twap_to_date = np.cumsum(closes) / np.arange(1, len(closes) + 1)
    return vwap_to_date, twap_to_date


def _attach_running_metrics(combined: pd.DataFrame, day: pd.DataFrame,
                            arrival_price: float) -> pd.DataFrame:
    """
    Adds, per bar of the combined (possibly multi-leg) schedule: the
    cumulative fill-weighted execution price so far, and running slippage
    (bps) vs. arrival and vs. interval-VWAP-to-date. Zero before the first
    fill (nothing to compare yet) rather than NaN, so charts don't break.
    """
    vwap_to_date, twap_to_date = _running_benchmark_curves(day)
    bench_df = pd.DataFrame({
        "time": day.index, "vwap_to_date": vwap_to_date, "twap_to_date": twap_to_date,
    })
    out = combined.merge(bench_df, on="time", how="left")
    cum_shares   = out["shares_traded"].cumsum()
    cum_notional = (out["shares_traded"] * out["price"]).cumsum()
    with np.errstate(divide="ignore", invalid="ignore"):
        cum_avg_price = np.where(cum_shares > 0, cum_notional / cum_shares, arrival_price)
    out["cum_avg_price"] = cum_avg_price
    out["running_slip_vs_arrival_bps"] = np.where(
        cum_shares > 0, (cum_avg_price - arrival_price) / arrival_price * 10_000, 0.0)
    out["running_slip_vs_vwap_bps"] = np.where(
        (cum_shares > 0) & (out["vwap_to_date"] > 0),
        (cum_avg_price - out["vwap_to_date"]) / out["vwap_to_date"] * 10_000, 0.0)
    return out


def simulate_with_interventions(market_data: MarketData, order_shares: float,
                                base_algo: str, base_urgency: str,
                                interventions: list, log=None) -> dict:
    """
    Models a buy-side trader monitoring execution intraday (as on a GSET-style
    blotter) and intervening -- possibly more than once -- the way a real desk
    would if the fill/slippage-so-far no longer matched conditions.

    `interventions` is a list of {"checkpoint_time", "algo", "urgency"} dicts
    (any order; sorted here by checkpoint_time). An empty list degenerates
    to a plain single-algo/urgency run of `base_algo`/`base_urgency` for the
    whole day. Each leg is simulated fresh, sized to only the shares still
    unfilled entering that leg, over only the bars in that leg's window --
    everything BEFORE a given checkpoint is never re-simulated once computed
    (each leg is computed once, in order), matching what "already happened
    under the plan so far" means for a real trader. Legs are stitched into
    one blended AlgoResult via the existing _build_result() cost math, using
    a fill-weighted blend of every leg's speed factor for the market-impact
    term (a reasonable approximation for a single sqrt-law total-size impact
    estimate split across several different aggressiveness regimes).

    This is backtest-style ("what if I had intervened at these points on this
    historical day"), not a live feed -- the underlying prices are the same
    historical bars simulate_algos() already used, replayed rather than new
    data arriving in real time.

    Returns a dict with:
      schedule       -- combined per-bar DataFrame (time, shares_traded, price,
                         cumulative, cum_avg_price, running_slip_vs_arrival_bps,
                         running_slip_vs_vwap_bps) -- one row per bar of the day
      legs           -- list of {start_time, end_time, algo, urgency, filled_shares}
      blended        -- AlgoResult for the full (all interventions applied) day
      day            -- the simulated day's OHLCV (for chart axis reuse)
      arrival_price, period_end_price
    """
    def _log(msg):
        if log: log(msg)

    bars_expected = MARKET_INFO[market_data.market]["bars"]
    day = _sim_day(market_data.intraday, bars_expected)
    n = len(day)
    sim_date = day.index[0].normalize()
    arrival_price = float(day["Open"].iloc[0]) if "Open" in day.columns else float(day["Close"].iloc[0])
    period_end_price = float(day["Close"].iloc[-1])

    hist_curve_full, _ = _historical_volume_weights(market_data.intraday, sim_date, n)

    ivs = sorted(interventions, key=lambda x: pd.Timestamp(x["checkpoint_time"]))
    boundaries = ([day.index[0] - pd.Timedelta(seconds=1)]
                 + [pd.Timestamp(iv["checkpoint_time"]) for iv in ivs]
                 + [day.index[-1]])
    leg_configs = [(base_algo, base_urgency)] + [(iv["algo"], iv["urgency"]) for iv in ivs]

    remaining_shares = order_shares
    frames, legs_meta = [], []
    sf_weighted_sum = 0.0

    for i, (algo, urg) in enumerate(leg_configs):
        seg_start, seg_end = boundaries[i], boundaries[i + 1]
        seg_day = day[(day.index > seg_start) & (day.index <= seg_end)]
        if len(seg_day) == 0 or remaining_shares <= 0:
            legs_meta.append({"start_time": seg_start, "end_time": seg_end, "algo": algo,
                              "urgency": urg, "filled_shares": 0.0})
            continue

        hist_seg = None
        if hist_curve_full is not None:
            mask = np.asarray((day.index > seg_start) & (day.index <= seg_end))
            sliced = hist_curve_full[mask]
            tot = sliced.sum()
            hist_seg = sliced / tot if tot > 0 else None

        fn = _ALGO_FUNCS[algo]
        seg_sched = fn(day=seg_day, order_shares=remaining_shares, urgency=urg, hist_curve=hist_seg)
        seg_filled = float(seg_sched["shares_traded"].sum())
        remaining_shares = max(0.0, remaining_shares - seg_filled)
        sf_weighted_sum += seg_filled * _speed_factor(algo, urg)

        frames.append(seg_sched[["time", "shares_traded", "price"]])
        legs_meta.append({"start_time": seg_start, "end_time": seg_end, "algo": algo,
                          "urgency": urg, "filled_shares": seg_filled})

    if frames:
        combined = pd.concat(frames, ignore_index=True)
    else:
        combined = pd.DataFrame(columns=["time", "shares_traded", "price"])
    combined["cumulative"] = combined["shares_traded"].cumsum() if len(combined) else []

    total_filled = order_shares - remaining_shares
    sf_blend = (sf_weighted_sum / total_filled) if total_filled > 0 else _speed_factor(base_algo, base_urgency)

    label = base_algo + "".join(f"→{iv['algo']}" for iv in ivs)
    note_parts = [f"Base: {base_algo} ({base_urgency})"]
    for iv in ivs:
        note_parts.append(f"switch @ {pd.Timestamp(iv['checkpoint_time']).strftime('%H:%M')} "
                          f"-> {iv['algo']} ({iv['urgency']})")
    note = "; ".join(note_parts)

    blended = _build_result(label, combined, arrival_price, order_shares,
                            market_data.adv_shares, market_data.realized_vol_ann,
                            sf_blend, period_end_price, schedule_note=note)

    combined = _attach_running_metrics(combined, day, arrival_price)

    _log(f"Interventions ({len(ivs)}): filled {total_filled:,.0f}/{order_shares:,.0f} sh; "
         f"blended total cost {blended.total_cost_bps:.1f} bps")

    return {
        "schedule": combined,
        "legs": legs_meta,
        "blended": blended,
        "day": day,
        "arrival_price": arrival_price,
        "period_end_price": period_end_price,
    }
