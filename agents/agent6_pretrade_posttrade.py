"""
Agent 6: Pre-Trade / Post-Trade Analytics
Bridges the gap between "which algo is cheapest on average" (Agent 4) and
what an execution desk actually needs at two distinct decision points:
before the order is worked, and after it fills.

Pre-trade (build_pretrade_estimate) — answers "what should this order cost,
and can the market even absorb it":
  1. Spread cost estimate — Corwin & Schultz (2012) high-low estimator.
     The platform only ever ingests OHLCV bars (no order book / NBBO feed is
     free at intraday granularity — see agent3's module docstring for the
     research behind that constraint), so quoted spread has been completely
     invisible until now. Corwin-Schultz recovers an estimate of the
     bid-ask spread from consecutive-day high/low ranges alone, by
     exploiting the fact that the high-low ratio reflects both volatility
     and spread, but volatility scales with the square root of the
     time-window while spread doesn't — so a 2-day and two 1-day estimates
     can be combined to isolate the spread component.
  2. Capacity table — days required to complete the order at a range of
     participation rates, given ADV.
  3. Expected cost range — empirical percentile bands (P10/P50/P90) across
     Agent 4's simulated daily cost distribution when enough days are
     available, falling back to Mean +/- Std otherwise. Reframes Agent 4's
     backward-looking scorecard as a forward-looking Low/Expected/High
     estimate.
  4. Almgren et al. (2005) calibrated cross-check — an independent,
     literature-fitted permanent/temporary impact estimate (see Agent 9),
     shown alongside the simulation's own eta=0.3 square-root model.

Post-trade (build_posttrade_tca) — answers "how did the fill actually do":
  1. Multi-benchmark comparison — the app previously only ever measured
     slippage vs. arrival price. Real TCA reports also benchmark against
     full-day VWAP, full-day TWAP, and the close, since different mandates
     care about different benchmarks (a VWAP-mandated fund cares about the
     VWAP benchmark, not arrival).
  2. Impact-reversion check — compares price at the algo's last fill to the
     day's closing price. This is a *rough* diagnostic, not a clean causal
     estimate: there is no control group to isolate impact we caused from
     ordinary intraday drift or news. It is presented as directional
     evidence only, and documented as such.
  3. Cost percentile — where the realized cost for the executed algo ranks
     within its own historical daily-cost distribution (from Agent 4), so
     "47.3 bps" gets a "was this a good day or a bad day" answer.
  4. Impact decomposition — Almgren et al. (2005)'s permanent/temporary
     (I/J/K) split applied to the realized fill, using arrival, average
     execution, and day-end prices already computed elsewhere in this
     module.
"""

import numpy as np
import pandas as pd
from dataclasses import dataclass
from agents.agent1_market_data import MarketData, MARKET_INFO
from agents.explicit_costs import get_explicit_costs, explicit_cost_note
from agents.order_ticket import side_sign
from agents.agent3_algo_simulation import AlgoResult, SimulationResult, _sim_day
from agents.agent4_performance_comparison import PerformanceComparison
from agents.agent9_microstructure import almgren_2005_impact, AlmgrenImpactEstimate

# Minimum number of historical daily-cost observations required before the
# pre-trade Expected Cost Range switches from Mean +/- Std to empirical
# percentiles (P10/P50/P90). Almgren et al. (2005)'s own residual analysis
# found impact-cost residuals to be "extremely fat-tailed" even though a
# Gaussian is a reasonable fit "to the central part" (Section 4.4) -- so a
# symmetric Mean +/- Std band can understate tail risk on either side. With
# too few days, though, empirical percentiles are just as noisy as the mean/
# std they'd replace, so a minimum sample size is enforced before switching.
MIN_DAYS_FOR_PERCENTILE_BAND = 5


# ══════════════════════════════════════════════════════════════════════════
# PRE-TRADE
# ══════════════════════════════════════════════════════════════════════════

# Corwin-Schultz (2012) normalizing constant: 3 - 2*sqrt(2)
_CS_K = 3 - 2 * np.sqrt(2)


def estimate_spread_corwin_schultz(daily: pd.DataFrame, window: int = 20) -> dict:
    """
    Corwin & Schultz (2012, Journal of Finance 67(2)) high-low bid-ask
    spread estimator. Uses only daily High/Low (no order book needed).

    For each pair of consecutive trading days (t, t+1):
      beta  = [ln(H_t/L_t)]^2 + [ln(H_t+1/L_t+1)]^2
      gamma = [ln(max(H_t,H_t+1) / min(L_t,L_t+1))]^2
      alpha = (sqrt(2*beta) - sqrt(beta)) / K  -  sqrt(gamma / K)     K = 3-2*sqrt(2)
      spread = 2*(e^alpha - 1) / (1 + e^alpha)

    Negative alpha (implying a negative spread) is floored at zero, standard
    practice in the spread-estimation literature since a spread can't be
    negative — negative estimates just mean the true spread is too small
    for this estimator to resolve on that pair of days.

    Known limitation — trending/volatile periods bias this estimator
    upward: the derivation assumes each day's price path is a
    driftless random walk, so the 2-day high-low range should scale by
    exactly sqrt(2) relative to the two 1-day ranges. A real 2-day
    *directional* move (e.g. a sharp selloff spanning both days) breaks
    that assumption and inflates gamma relative to beta, which the model
    misreads as spread rather than trend. In practice this means single-name,
    short-window estimates can come out economically implausible (tens to
    over 100 bps on a liquid large-cap) during volatile stretches — this is
    a documented weakness of high-low range estimators generally, not unique
    to this implementation. To manage it: (1) the *median* of the window's
    daily-pair estimates is reported as the headline number (materially more
    robust to a handful of trend-driven outlier days than the mean), with
    the mean also returned for comparison; (2) `reliability` flags "Low"
    when the two disagree substantially or when a large share of the window
    had to be floored at zero, so the caller can decide whether to trust the
    point estimate or treat it as order-of-magnitude only.

    Returns spread_bps (median-based quoted spread) and half_spread_bps
    (~the one-way crossing cost a single marketable order pays), computed
    over the most recent `window` daily-pair estimates.
    """
    hi = daily["High"].values
    lo = daily["Low"].values
    n = len(hi)
    if n < window + 2:
        return {"spread_bps": None, "half_spread_bps": None, "n_obs": 0,
                "spread_mean_bps": None, "reliability": "N/A",
                "note": f"Need >= {window + 2} daily bars for a stable estimate; have {n}."}

    alphas = []
    for t in range(n - 1):
        if lo[t] <= 0 or lo[t + 1] <= 0:
            continue
        h2 = max(hi[t], hi[t + 1])
        l2 = min(lo[t], lo[t + 1])
        if l2 <= 0:
            continue
        beta  = np.log(hi[t] / lo[t]) ** 2 + np.log(hi[t + 1] / lo[t + 1]) ** 2
        gamma = np.log(h2 / l2) ** 2
        alpha = (np.sqrt(2 * beta) - np.sqrt(beta)) / _CS_K - np.sqrt(gamma / _CS_K)
        alphas.append(alpha)

    if not alphas:
        return {"spread_bps": None, "half_spread_bps": None, "n_obs": 0,
                "spread_mean_bps": None, "reliability": "N/A",
                "note": "Estimator could not be computed (zero/invalid low prices in window)."}

    alphas = np.array(alphas)
    raw_spreads = 2 * (np.exp(alphas) - 1) / (1 + np.exp(alphas))
    spreads = np.clip(raw_spreads, 0, None)   # floor negative estimates at 0

    recent     = spreads[-window:] if len(spreads) >= window else spreads
    raw_recent = raw_spreads[-window:] if len(raw_spreads) >= window else raw_spreads

    median_frac = float(np.median(recent))
    mean_frac   = float(np.mean(recent))
    frac_floored = float((raw_recent < 0).mean())

    median_bps = median_frac * 10_000

    reliability = "Normal"
    if frac_floored > 0.30:
        reliability = ("Low — over 30% of the window's daily-pair estimates were negative (floored at "
                       "zero), indicating a choppy/noisy read.")
    elif mean_frac > 0 and abs(mean_frac - median_frac) / mean_frac > 0.30:
        reliability = ("Low — mean and median estimates diverge materially, consistent with one or more "
                       "trending/volatile day-pairs skewing the average upward; treat the median as the "
                       "more robust read and the whole figure as order-of-magnitude only.")
    elif median_bps > 50:
        # Even when the window is internally consistent (no outlier days skewing mean vs
        # median, few floored observations), a median well above typical quoted spreads for
        # liquid large/mid-cap names (usually low single-digit to a few tens of bps) is a sign
        # the *whole* window had sustained trending/volatile price action, which biases every
        # observation in the same direction rather than producing a few outliers -- exactly
        # the case that the mean-vs-median and floor-fraction checks above can't catch.
        reliability = ("Low — median estimate is well above typical quoted spreads for liquid "
                       "names; sustained volatility/trending price action across the window "
                       "likely inflated every observation rather than just a few outlier days. "
                       "Treat as order-of-magnitude only and cross-check against the security's "
                       "known liquidity tier.")

    return {
        "spread_bps": round(median_frac * 10_000, 2),
        "half_spread_bps": round(median_frac * 10_000 / 2, 2),
        "spread_mean_bps": round(mean_frac * 10_000, 2),
        "n_obs": len(recent),
        "reliability": reliability,
        "note": "",
    }


def estimate_spread_abdi_ranaldo(daily: pd.DataFrame, window: int = 20) -> dict:
    """Abdi & Ranaldo (2017, Review of Financial Studies) close-high-low
    bid-ask spread estimator — the modern cross-check to Corwin-Schultz.

    For each pair of consecutive days (t, t+1), with eta_t = (ln H_t + ln L_t)/2
    (the day's mid-range) and c_t = ln C_t:

        s2_t   = 4 * (c_t - eta_t) * (c_t - eta_{t+1})
        spread = sqrt(max(s2_t, 0))

    Uses more of the daily bar than the high-low estimator and is independent
    of the trade direction of closing prices; comparisons find it generally
    more accurate across liquidity regimes (CS has lower small-sample
    variance). Same conventions as the CS function: negative per-pair
    estimates floored at zero, median of the window's per-pair estimates as
    the headline, mean returned for comparison.
    """
    need = {"High", "Low", "Close"}
    if not need.issubset(daily.columns):
        return {"spread_bps": None, "half_spread_bps": None, "n_obs": 0,
                "spread_mean_bps": None, "note": "Daily High/Low/Close unavailable."}
    d = daily.tail(window + 2)
    n = len(d)
    if n < window // 2 + 2:
        return {"spread_bps": None, "half_spread_bps": None, "n_obs": 0,
                "spread_mean_bps": None,
                "note": f"Need >= {window // 2 + 2} daily bars; have {n}."}
    hi = np.log(d["High"].astype(float).values)
    lo = np.log(d["Low"].astype(float).values)
    c = np.log(d["Close"].astype(float).values)
    eta = (hi + lo) / 2.0
    ests = []
    for t in range(n - 1):
        if not (np.isfinite(eta[t]) and np.isfinite(eta[t + 1]) and np.isfinite(c[t])):
            continue
        s2 = 4.0 * (c[t] - eta[t]) * (c[t] - eta[t + 1])
        ests.append(np.sqrt(max(s2, 0.0)))
    if not ests:
        return {"spread_bps": None, "half_spread_bps": None, "n_obs": 0,
                "spread_mean_bps": None, "note": "No valid day-pairs."}
    med = float(np.median(ests))
    return {"spread_bps": round(med * 10_000, 2),
            "half_spread_bps": round(med * 10_000 / 2, 2),
            "spread_mean_bps": round(float(np.mean(ests)) * 10_000, 2),
            "n_obs": len(ests), "note": ""}


def capacity_table(order_shares: float, adv_shares: float,
                   rates=(0.05, 0.10, 0.15, 0.20, 0.25)) -> pd.DataFrame:
    """Days required to complete the order at each participation rate."""
    rows = []
    for r in rates:
        days = (order_shares / (adv_shares * r)) if adv_shares > 0 else float("inf")
        rows.append({"Participation Rate": f"{r:.0%}", "Days to Complete": round(days, 2)})
    return pd.DataFrame(rows).set_index("Participation Rate")


_URGENCY_RATE = {"Low": 0.10, "Medium": 0.15, "High": 0.20}


@dataclass
class PreTradeEstimate:
    spread_bps: float
    spread_mean_bps: float
    half_spread_bps: float
    spread_n_obs: int
    spread_reliability: str
    spread_note: str
    capacity: pd.DataFrame
    expected_cost_range: pd.DataFrame    # per algo: Low / Expected / High (bps), Avg Fill
    cost_range_method: str               # "Empirical percentile (P10/P50/P90)" | "Mean +/- Std"
    days_at_chosen_urgency: float
    almgren: AlmgrenImpactEstimate       # Almgren et al. (2005) calibrated cross-check (Agent 9)
    notes: list
    spread_ar_bps: float = None          # Abdi-Ranaldo (2017) cross-check estimate
    explicit_cost_bps: float = None      # commissions + fees + taxes (buy side)
    spread_blend_note: str = ""          # how the two estimators were combined


def build_pretrade_estimate(market_data: MarketData, comparison: PerformanceComparison,
                            order_shares: float, order_pct_adv: float,
                            urgency: str, ticket=None) -> PreTradeEstimate:
    side = ticket.side if ticket is not None else "Buy"
    sp  = estimate_spread_corwin_schultz(market_data.daily)
    ar  = estimate_spread_abdi_ranaldo(market_data.daily)
    cap = capacity_table(order_shares, market_data.adv_shares)

    rate = _URGENCY_RATE[urgency]
    # Order-ticket participation cap binds the capacity assumption when it is
    # tighter than the urgency-implied rate.
    if ticket is not None and getattr(ticket, "cap_frac", None):
        rate = min(rate, ticket.cap_frac)
    days_chosen = (order_shares / (market_data.adv_shares * rate)) if market_data.adv_shares > 0 else float("inf")

    n_days = len(comparison.daily_costs)
    if n_days >= MIN_DAYS_FOR_PERCENTILE_BAND:
        pctl = comparison.daily_costs.quantile([0.10, 0.50, 0.90])
        rng = pd.DataFrame({
            "Low (bps)":      pctl.loc[0.10],
            "Expected (bps)": pctl.loc[0.50],
            "High (bps)":     pctl.loc[0.90],
            "Avg Fill":       comparison.summary["Avg Fill"],
        })
        cost_range_method = f"Empirical percentile (P10/P50/P90) across {n_days} simulated days"
    else:
        rng = comparison.summary.copy()
        rng["Low (bps)"]      = rng["Mean (bps)"] - rng["Std (bps)"]
        rng["Expected (bps)"] = rng["Mean (bps)"]
        rng["High (bps)"]     = rng["Mean (bps)"] + rng["Std (bps)"]
        cost_range_method = (f"Mean +/- Std (only {n_days} simulated days available -- "
                             f"need >= {MIN_DAYS_FOR_PERCENTILE_BAND} for empirical percentiles)")

    expected_range = rng[["Low (bps)", "Expected (bps)", "High (bps)", "Avg Fill"]].round(
        {"Low (bps)": 1, "Expected (bps)": 1, "High (bps)": 1, "Avg Fill": 3}
    )

    almgren = almgren_2005_impact(
        order_shares, market_data.adv_shares, market_data.realized_vol_ann, rate,
        getattr(market_data, "shares_outstanding", None)
    )

    notes = []
    if sp["spread_bps"] is not None:
        notes.append(
            f"Estimated quoted spread ~{sp['spread_bps']:.1f} bps median (Corwin-Schultz, {sp['n_obs']} "
            f"recent daily-pair observations, mean {sp['spread_mean_bps']:.1f} bps) — a single marketable "
            f"order typically pays roughly half the median as crossing cost (~{sp['half_spread_bps']:.1f} "
            f"bps), on top of the market-impact and opportunity-cost terms already modeled below."
        )
        if sp["reliability"] != "Normal":
            notes.append(f"⚠️ Spread estimate reliability: {sp['reliability']}")
    else:
        notes.append(f"Spread estimate unavailable: {sp['note']}")

    if days_chosen > 1.05:
        notes.append(
            f"At the {urgency}-urgency participation rate ({rate:.0%} of ADV), this order needs "
            f"~{days_chosen:.1f} trading days to complete without exceeding a prudent participation "
            f"cap — consider a multi-day schedule rather than forcing single-day completion."
        )

    if order_pct_adv >= 20:
        notes.append(
            f"Order size ({order_pct_adv}% ADV) is large relative to the historical window used for "
            f"the Expected column — realized cost at this size may exceed the historical average if "
            f"the fetch window rarely saw participation this high (check the Order Size Sensitivity "
            f"table for the re-simulated cost at this specific size)."
        )

    if almgren.available:
        notes.append(
            f"Almgren et al. (2005) calibrated cross-check: ~{almgren.permanent_impact_bps:.1f} bps "
            f"permanent + {almgren.temporary_impact_bps:.1f} bps temporary ≈ "
            f"{almgren.realized_impact_bps:.1f} bps total expected impact, from coefficients fit to "
            f"~29,500 real institutional orders (independent of the eta=0.3 square-root model used "
            f"in the simulation above — see Agent 9). {almgren.note}"
        )

    # ── Explicit costs (commissions/fees/taxes — deterministic, pre-known) ─
    _exp = get_explicit_costs(market_data.market)
    notes.append("💰 " + explicit_cost_note(market_data.market, side))

    # ── Estimator blend: Corwin-Schultz x Abdi-Ranaldo x EDGE ─────────────
    # Three independent daily-bar estimators; the blended half-spread is the
    # MEDIAN of whichever resolve (robust to one estimator degenerating on a
    # given sample) and is what downstream consumers (Agent 13 routing)
    # receive. EDGE (Ardia-Guidotti-Kroencke JFE 2024) folded into the blend
    # 2026-07-08 — previously display-only in the Microstructure section;
    # this SHIFTS displayed pre-trade spread numbers (documented in
    # docs/MICROSTRUCTURE_RESEARCH_IMPROVEMENTS.md and the session summary).
    # Disagreement is itself information: > 2x spread between the highest and
    # lowest resolving estimator downgrades the reliability read.
    from agents.microstructure_analytics import estimate_spread_edge
    eg = estimate_spread_edge(market_data.daily)
    _halves = {"Corwin-Schultz": sp["half_spread_bps"],
               "Abdi-Ranaldo": ar["half_spread_bps"],
               "EDGE": eg["half_spread_bps"]}
    _live = {k: v for k, v in _halves.items() if v is not None}
    blended_half = sp["half_spread_bps"]
    blend_note = "Corwin-Schultz only (other estimators unavailable)."
    if len(_live) >= 2:
        blended_half = round(float(np.median(list(_live.values()))), 2)
        _fulls = [2 * v for v in _live.values()]
        ratio = max(_fulls) / max(min(_fulls), 0.01)
        agree = "agree within 2x" if ratio <= 2.0 else f"DISAGREE ({ratio:.1f}x apart)"
        blend_note = (", ".join(f"{k} {2 * v:.1f} bps" for k, v in _live.items())
                      + f" — {len(_live)} estimators {agree}; blended (median) half-spread "
                        f"{blended_half:.1f} bps feeds venue routing.")
        notes.append(f"Spread cross-check: {blend_note}")
        if ratio > 2.0:
            notes.append("⚠️ Spread estimators disagree by more than 2x — treat the level as "
                         "order-of-magnitude only (all are daily-bar approximations; the "
                         "routing input remains capped).")
    elif len(_live) == 1:
        blended_half = list(_live.values())[0]
        blend_note = f"{list(_live.keys())[0]} only (other estimators unavailable)."
    elif ar["half_spread_bps"] is None and sp["half_spread_bps"] is not None:
        notes.append("Spread cross-check: Abdi-Ranaldo estimator unavailable "
                     f"({ar['note']}) — Corwin-Schultz stands alone.")

    return PreTradeEstimate(
        spread_bps=sp["spread_bps"],
        spread_mean_bps=sp["spread_mean_bps"],
        half_spread_bps=blended_half,
        spread_n_obs=sp["n_obs"],
        spread_reliability=sp["reliability"],
        spread_note=sp["note"],
        capacity=cap,
        expected_cost_range=expected_range,
        cost_range_method=cost_range_method,
        days_at_chosen_urgency=round(days_chosen, 2),
        almgren=almgren,
        notes=notes,
        spread_ar_bps=ar["spread_bps"],
        explicit_cost_bps=_exp.total_bps(side),
        spread_blend_note=blend_note,
    )


# ══════════════════════════════════════════════════════════════════════════
# POST-TRADE
# ══════════════════════════════════════════════════════════════════════════

def _full_day_vwap(day: pd.DataFrame) -> float:
    vol = day["Volume"].values
    # typical price per bar — consistent with the continuous-fill convention
    if {"High", "Low", "Close"}.issubset(day.columns):
        px = (day["High"].values + day["Low"].values + day["Close"].values) / 3.0
    else:
        px = day["Close"].values
    tv  = vol.sum()
    return float((px * vol).sum() / tv) if tv > 0 else float(px.mean())


@dataclass
class BenchmarkComparison:
    table: pd.DataFrame   # index=benchmark name, cols=Benchmark Price, Slippage vs Benchmark (bps)


def compute_benchmark_comparison(algo: AlgoResult, day: pd.DataFrame, side: str = "Buy") -> BenchmarkComparison:
    """
    Benchmarks the algo's realized average execution price against the four
    standard TCA reference points: Arrival (session open), full-day VWAP,
    full-day TWAP (simple average of bar closes), and the close. Different
    mandates care about different benchmarks — a VWAP-tracking fund cares
    about the VWAP row, not Arrival, which is all the simulator measured
    against previously. Slippage (bps) = (avg_exec - benchmark)/benchmark *
    10000 for a buy order — positive means the algo paid more than that
    benchmark.
    """
    avg_px  = algo.avg_exec_price
    arrival = algo.arrival_price
    close   = float(day["Close"].iloc[-1])
    vwap    = _full_day_vwap(day)
    twap    = float(day["Close"].mean())

    rows = []
    sgn = side_sign(side)
    for name, bench in [("Arrival (Open)", arrival), ("Full-Day VWAP", vwap),
                        ("Full-Day TWAP", twap), ("Close", close)]:
        slip = sgn * (avg_px - bench) / bench * 10_000 if bench > 0 else 0.0
        rows.append({
            "Benchmark": name,
            "Benchmark Price": round(bench, 4),
            "Slippage vs Benchmark (bps)": round(slip, 2),
        })
    return BenchmarkComparison(table=pd.DataFrame(rows).set_index("Benchmark"))


@dataclass
class ImpactReversion:
    available: bool
    reason: str
    price_at_last_fill: float
    price_at_day_end: float
    reversion_bps: float
    interpretation: str


def compute_impact_reversion(algo: AlgoResult, day: pd.DataFrame, side: str = "Buy") -> ImpactReversion:
    """
    Rough post-trade impact-decay check: compares price at the algo's last
    fill to the day's closing price. For a buy order, price falling back
    after the last fill (negative reversion_bps) is *consistent with* at
    least part of the impact we caused being temporary; price continuing to
    rise is consistent with either genuinely permanent impact or broader
    momentum/news dominating. This is a directional diagnostic only — there
    is no control group (a counterfactual "what would price have done
    without our order") to cleanly isolate our impact from ordinary
    intraday drift, so it should not be read as a precise measurement.
    """
    sched = algo.schedule
    filled_mask = sched["shares_traded"] > 0
    if not filled_mask.any():
        return ImpactReversion(False, "No shares were filled on the simulated day.", 0.0, 0.0, 0.0, "N/A")

    last_fill_pos = np.where(filled_mask.values)[0][-1]
    if last_fill_pos == len(sched) - 1:
        price_at_last_fill = float(sched["price"].iloc[last_fill_pos])
        price_at_day_end = float(day["Close"].iloc[-1])
        return ImpactReversion(
            False,
            "Last fill occurred in the day's final bar — no post-fill window remains to observe reversion.",
            price_at_last_fill, price_at_day_end, 0.0, "N/A",
        )

    price_at_last_fill = float(sched["price"].iloc[last_fill_pos])
    price_at_day_end   = float(day["Close"].iloc[-1])
    # signed so negative = favorable reversion (temporary impact) for either side
    reversion_bps = side_sign(side) * (price_at_day_end - price_at_last_fill) / price_at_last_fill * 10_000

    if reversion_bps < -5:
        interp = ("Price gave back ground after our last fill — consistent with at least "
                 "partial temporary impact.")
    elif reversion_bps > 5:
        interp = ("Price continued rising after our last fill — consistent with either largely "
                 "permanent impact or broader momentum/news dominating (this diagnostic can't "
                 "separate the two).")
    else:
        interp = "Price was roughly flat after our last fill — no strong reversion or continuation signal."

    return ImpactReversion(True, "", price_at_last_fill, price_at_day_end, round(reversion_bps, 2), interp)


@dataclass
class ImpactDecomposition:
    available: bool
    reason: str
    permanent_impact_bps: float    # I  = (Spost - S0) / S0
    realized_impact_bps: float     # J  = (Sbar  - S0) / S0  (== algo.slippage_bps)
    temporary_impact_bps: float    # K  = J - I/2
    note: str


def compute_impact_decomposition(algo: AlgoResult, day: pd.DataFrame, side: str = "Buy") -> ImpactDecomposition:
    """
    Almgren et al. (2005) permanent/realized/temporary impact decomposition
    (see agent9_microstructure's module docstring for the full model),
    applied post-trade using data this platform already has:

      S0    = arrival price (algo.arrival_price)
      Sbar  = average realized execution price (algo.avg_exec_price)
      Spost = price some time after the order finishes, once temporary
              liquidity effects have dissipated -- the original paper uses
              "one half-hour after the last execution"; this single-day
              simulator's natural analogue is the day's closing price
              (same convention already used by compute_impact_reversion
              above for consistency across this module).

      J (realized impact)  = (Sbar  - S0) / S0 * 10000   [ == slippage_bps ]
      I (permanent impact)  = (Spost - S0) / S0 * 10000
      K (temporary impact)  = J - I/2

    This is NOT the same thing as compute_impact_reversion above (which
    compares price at last fill to day-end, a reversion diagnostic) --
    this decomposition compares the average EXECUTION price itself
    (across the whole schedule, weighted by when shares actually filled)
    against arrival and day-end, splitting total realized cost into a
    piece that persists (I, roughly half-counted per the model, since our
    own trading contributed to moving the permanent level while we were
    still executing) and a piece attributable to the temporary liquidity
    concession from trading (K). Like compute_impact_reversion, this has no
    control group and should be read directionally, not as a precise
    causal estimate.
    """
    if algo.schedule["shares_traded"].sum() <= 0:
        return ImpactDecomposition(False, "No shares were filled on the simulated day.", 0.0, 0.0, 0.0, "")

    s0 = algo.arrival_price
    spost = float(day["Close"].iloc[-1])
    j_bps = algo.slippage_bps                              # already side-signed by Agent 3
    i_bps = side_sign(side) * (spost - s0) / s0 * 10_000 if s0 > 0 else 0.0
    k_bps = j_bps - i_bps / 2

    note = (
        f"Of the {j_bps:+.1f} bps realized impact, ~{i_bps:+.1f} bps looks permanent (price move from "
        f"arrival to day-end) and ~{k_bps:+.1f} bps looks temporary (liquidity concession that priced "
        f"in during execution but isn't reflected in where the stock ultimately settled)."
    )
    return ImpactDecomposition(
        available=True, reason="",
        permanent_impact_bps=round(i_bps, 2),
        realized_impact_bps=round(j_bps, 2),
        temporary_impact_bps=round(k_bps, 2),
        note=note,
    )


@dataclass
class CostPercentile:
    available: bool
    reason: str
    percentile: float
    n_obs: int


def compute_cost_percentile(comparison: PerformanceComparison, algo_name: str,
                            realized_total_cost_bps: float) -> CostPercentile:
    """
    Where the realized cost ranks within the algo's own historical
    daily-cost distribution (from Agent 4's daily_costs). Lower percentile =
    cheaper than usual for this algo on this name.
    """
    if algo_name not in comparison.daily_costs.columns:
        return CostPercentile(False, f"No historical cost distribution available for {algo_name}.", 0.0, 0)
    hist = comparison.daily_costs[algo_name].dropna().values
    if len(hist) == 0:
        return CostPercentile(False, "Historical cost distribution is empty.", 0.0, 0)
    pct = float((hist <= realized_total_cost_bps).mean() * 100)
    return CostPercentile(True, "", round(pct, 1), len(hist))


@dataclass
class ISAttribution:
    """Canonical Perold implementation-shortfall attribution (gap register I-5).

    All components are bps of ORDER notional at the decision price D, signed
    positive = cost for the order's side:
      delay        = filled_frac x (P_first_fill - D) / D      (market moved before we traded)
      trading      = filled_frac x (avg_px - P_first_fill) / D (paid while trading)
      opportunity  = unfilled_frac x (P_end - D) / D           (never-filled shares)
      explicit     = per-market commissions/fees/taxes x filled_frac
    total_is = delay + trading + opportunity + explicit, and reconciles to the
    direct share-weighted shortfall within 0.1 bp BY CONSTRUCTION (exact
    algebraic identity; reconciliation_bps is asserted in tests).

    Convention notes (why this can differ from the dashboard 'Total Cost'):
    the headline total reports slippage UNWEIGHTED by fill fraction plus a
    MODELED sqrt-law impact overlay; this attribution decomposes the REALIZED
    shortfall share-weighted, so on partial fills the two intentionally
    differ, and the modeled impact appears only as a memo (the simulator's
    fills do not embed it)."""
    available: bool
    reason: str = ""
    decision_price: float = None
    first_fill_price: float = None
    delay_bps: float = None
    trading_bps: float = None
    opportunity_bps: float = None
    explicit_bps: float = None
    total_is_bps: float = None
    reconciliation_bps: float = None     # |components - direct| (< 0.1 by identity)
    filled_frac: float = None
    modeled_impact_memo_bps: float = None
    note: str = ""


def build_is_attribution(algo: AlgoResult, day: pd.DataFrame, side: str,
                         market: str, order_shares: float) -> ISAttribution:
    sgn = side_sign(side)
    D = float(algo.arrival_price)
    if D <= 0 or order_shares <= 0:
        return ISAttribution(False, "Missing decision price or order size.")

    sched = algo.schedule
    filled = float(sched["shares_traded"].sum()) if sched is not None and len(sched) else 0.0
    filled_frac = min(filled / order_shares, 1.0)
    unfilled_frac = max(0.0, 1.0 - filled_frac)
    P_end = float(day["Close"].iloc[-1])

    if filled > 0:
        first_i = int(np.argmax(sched["shares_traded"].values > 0))
        P_first = float(sched["price"].iloc[first_i])
        avg_px = float(algo.avg_exec_price)
        delay = sgn * filled_frac * (P_first - D) / D * 10_000
        trading = sgn * filled_frac * (avg_px - P_first) / D * 10_000
    else:
        P_first, avg_px = None, D
        delay, trading = 0.0, 0.0

    opportunity = sgn * unfilled_frac * (P_end - D) / D * 10_000
    explicit = get_explicit_costs(market).total_bps(side) * filled_frac
    total = delay + trading + opportunity + explicit

    direct = (sgn * filled_frac * (avg_px - D) / D * 10_000
              + sgn * unfilled_frac * (P_end - D) / D * 10_000
              + explicit)
    recon = abs(total - direct)

    note = (f"Filled {filled_frac:.0%} of the order. Delay+trading decompose the "
            f"shortfall on FILLED shares (split at the first fill's bar price); "
            f"opportunity marks unfilled shares at the day close vs decision; "
            f"explicit costs are the {market} schedule scaled by fill fraction. "
            f"Reconciles to the share-weighted shortfall within "
            f"{recon:.4f} bp. The modeled sqrt-law impact "
            f"({algo.market_impact_bps:+.1f} bps) is a memo item, not a component "
            f"— simulated fills do not embed it.")

    return ISAttribution(
        available=True,
        decision_price=round(D, 4),
        first_fill_price=round(P_first, 4) if P_first is not None else None,
        delay_bps=round(delay, 2), trading_bps=round(trading, 2),
        opportunity_bps=round(opportunity, 2), explicit_bps=round(explicit, 2),
        total_is_bps=round(total, 2), reconciliation_bps=round(recon, 6),
        filled_frac=round(filled_frac, 4),
        modeled_impact_memo_bps=algo.market_impact_bps,
        note=note)


@dataclass
class PostTradeTCA:
    algo_name: str
    benchmarks: BenchmarkComparison
    reversion: ImpactReversion
    cost_percentile: CostPercentile
    impact_decomposition: ImpactDecomposition
    notes: list
    is_attribution: ISAttribution = None     # added 2026-07-08 (I-5); default keeps old callers valid


def build_posttrade_tca(market_data: MarketData, sim: SimulationResult,
                        comparison: PerformanceComparison, algo_name: str) -> PostTradeTCA:
    """
    algo_name should be the algo that was actually (simulated to be)
    executed — typically memo.primary_algo from Agent 5.
    """
    bars_expected = MARKET_INFO[market_data.market]["bars"]
    day = _sim_day(market_data.intraday, bars_expected)   # same day Agent 3 simulated on

    algo   = sim.algos[algo_name]
    _side  = getattr(sim, "side", "Buy")
    bench  = compute_benchmark_comparison(algo, day, side=_side)
    rev    = compute_impact_reversion(algo, day, side=_side)
    pctl   = compute_cost_percentile(comparison, algo_name, algo.total_cost_bps)
    decomp = compute_impact_decomposition(algo, day, side=_side)

    notes = []
    if pctl.available:
        notes.append(
            f"Today's realized total cost for {algo_name} ({algo.total_cost_bps:+.1f} bps) sits at the "
            f"{pctl.percentile:.0f}th percentile of its {pctl.n_obs}-day historical distribution "
            f"(lower percentile = cheaper than usual)."
        )
    else:
        notes.append(pctl.reason)
    if rev.available:
        notes.append(rev.interpretation)
    if decomp.available:
        notes.append(decomp.note)

    isa = build_is_attribution(algo, day, _side, market_data.market,
                               float(sim.order_shares))
    if isa.available:
        notes.append(isa.note)

    return PostTradeTCA(algo_name=algo_name, benchmarks=bench, reversion=rev,
                        cost_percentile=pctl, impact_decomposition=decomp, notes=notes,
                        is_attribution=isa)
