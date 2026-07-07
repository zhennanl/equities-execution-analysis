"""
Agent 9: Market Microstructure & Order-Flow Toxicity

VPIN DISCLOSURE (see docs/EXECUTION_SIMULATOR_RESEARCH.md): VPIN's predictive
validity is academically contested. Andersen & Bondarenko (2014, J. Financial
Markets) show its predictive content is largely a mechanical reflection of
volume and volatility, that it peaked AFTER (not before) the 2010 Flash
Crash, and that results are sensitive to the trade-classification scheme;
Easley, Lopez de Prado & O'Hara's rejoinder defends the toxicity->liquidity
channel. This module therefore treats VPIN as a MONITORING SIGNAL correlated
with stressed conditions — not a validated predictor — and Agent 8 consumes
it as a flag for a human, never an automatic action.

Adds three genuinely institutional-grade liquidity diagnostics that this
platform's free OHLCV-only data feed can actually support:

1. Kyle's Lambda (Kyle 1985) -- price impact per unit of signed order flow,
   the workhorse liquidity/depth metric on every institutional trading
   desk's microstructure dashboard. Estimated here via OLS regression of
   NEXT-bar returns on THIS-bar's Bulk-Volume-Classified (see #2) net order
   flow, pooled across every intraday day Agent 1 fetched (bar-to-bar
   within a day only -- overnight gaps are excluded).

   Deliberately lagged, not contemporaneous: Bulk Volume Classification
   assigns a bar's buy/sell split from that SAME bar's own price change
   (see _bulk_volume_classify). Regressing that bar's return on order flow
   derived from the bar's own price change would be close to tautological
   -- BVC's buy fraction is a monotonic function of the bar's realized
   return, so a contemporaneous regression mechanically inflates R^2
   without saying anything about genuine price impact. Using bar t's
   classified flow to predict bar t+1's return breaks that circularity:
   the predictor is fully determined before the response is observed, the
   same logic already applied elsewhere in this codebase to eliminate
   look-ahead bias in the VWAP/MOC/MOO schedules (see agent3's module
   docstring). This also better matches how a real desk would use the
   number -- "does the flow I'm seeing right now forecast where the price
   goes next" -- rather than an unobservable instantaneous coefficient.
   Higher lambda = lower depth = order flow moves the price more.

2. VPIN -- Volume-Synchronized Probability of Informed Trading (Easley,
   Lopez de Prado & O'Hara, "Flow Toxicity and Liquidity in a High
   Frequency World", J. Finance / Review of Financial Studies; bulk-volume
   classification method from Easley, Lopez de Prado & O'Hara (2012),
   "Bulk Classification of Trading Activity"). VPIN reached historically
   elevated levels in the hour before the May 6, 2010 Flash Crash and is
   used by exchanges/regulators (a Lawrence Berkeley National Laboratory
   study for the SEC called it "the strongest early warning signal known
   to us at this time"). It measures order-flow "toxicity" -- how
   one-sided volume is -- as an adverse-selection proxy for market makers.

   Data caveat -- this is a TIME-BAR approximation, not canonical VPIN:
   the original method buckets by EQUAL VOLUME using tick-level trade
   prints; this platform only has 5-min OHLCV bars (no tick data, no
   sub-bar trade prints), so volume buckets aren't constructible. Each
   5-min bar is used as one bucket instead. This is disclosed explicitly
   rather than presented as a canonical reading -- consistent with every
   other proxy metric in this codebase (Corwin-Schultz spread, MOC/MOO
   auction approximations, etc.).

3. Almgren et al. (2005) calibrated impact cross-check -- "Direct
   Estimation of Equity Market Impact" (Almgren, Thum, Hauptmann & Li,
   Citigroup Global Quantitative Research) fit permanent impact I and
   temporary impact K = J - I/2 from ~29,500 real Citigroup institutional
   equity orders (Dec 2001 - Jun 2003):

     I = gamma * sigma * (X/V) * (Theta/V)^delta      gamma = 0.314, delta = 0.25
     K = eta   * sigma * |X/(V*T)|^beta * sgn(X)       eta   = 0.142, beta  = 0.60

   sigma = daily volatility, X = signed order size (shares), V = ADV,
   T = fraction of a trading day over which the order executes,
   Theta = shares outstanding (the "turnover" liquidity factor -- omitted,
   i.e. (Theta/V)^delta set to 1, when shares outstanding can't be fetched
   for free). This is reported alongside Agent 3's independent eta=0.3
   square-root model as a literature-anchored cross-check, not a
   replacement for it -- the two models disagreeing materially is itself
   informative (Agent 3's model uses beta=0.5, the classical square-root
   law; Almgren et al. found and rejected beta=0.5 in favor of beta=0.6
   at the 95% confidence level on their institutional sample, so some
   divergence at large order sizes is expected and not a bug).
"""

import math
import numpy as np
import pandas as pd
from dataclasses import dataclass
from typing import Optional

# Almgren, Thum, Hauptmann & Li (2005), "Direct Estimation of Equity Market
# Impact" -- fitted coefficients (Section 4.3), all dimensionless, applied to
# I/sigma and (J - I/2)/sigma:
ALMGREN_GAMMA = 0.314   # permanent-impact coefficient (t=7.7 in the original fit)
ALMGREN_ETA   = 0.142   # temporary-impact coefficient  (t=23  in the original fit)
ALMGREN_ALPHA = 1.0     # permanent-impact exponent on X/V (linear; can't be rejected, ch4.2)
ALMGREN_BETA  = 0.60    # temporary-impact exponent on X/(V*T) (3/5 power law, rejects sqrt-law's 0.5 at 95% CI)
ALMGREN_DELTA = 0.25    # turnover liquidity-factor exponent on (Theta/V)

# VPIN: number of bars per "bucket" window (a true implementation uses equal-
# volume buckets from tick data; we approximate with a rolling window of bars
# -- 50 buckets/day is the window size most commonly cited in the VPIN
# literature for liquid US equities, so we use it here as the rolling window
# length, capped to whatever the session actually has).
VPIN_WINDOW_BARS = 50

# Kyle's lambda / VPIN: minimum bar-return observations required before we'll
# report a regression or toxicity score rather than "insufficient data".
MIN_OBS_KYLE  = 30
MIN_OBS_VPIN  = 10


def _normal_cdf(x: np.ndarray) -> np.ndarray:
    """Standard normal CDF via math.erf -- avoids adding a scipy dependency
    for a single function. Vectorized with np.vectorize since erf isn't
    natively vectorized in the stdlib."""
    erf_vec = np.vectorize(math.erf)
    return 0.5 * (1.0 + erf_vec(x / math.sqrt(2.0)))


def _bulk_volume_classify(bars: pd.DataFrame) -> pd.DataFrame:
    """
    Bulk Volume Classification (Easley, Lopez de Prado & O'Hara 2012):
    within each bar, the fraction of that bar's volume classified as
    buyer-initiated is Z(dP / sigma_dP), where dP is the bar's price change,
    sigma_dP is the standard deviation of price changes across the sample,
    and Z is the standard normal CDF. This classifies volume WITHOUT needing
    tick-level trade prints or a quote midpoint -- the entire point of BVC
    versus the older tick-rule/Lee-Ready methods, and why it's usable here.

    Returns a copy of `bars` with added columns: dP, buy_vol, sell_vol.
    """
    out = bars.copy()
    out["dP"] = out["Close"].diff()
    sigma_dp = out["dP"].std()
    if not sigma_dp or sigma_dp <= 0 or np.isnan(sigma_dp):
        out["buy_vol"] = out["Volume"] * 0.5
        out["sell_vol"] = out["Volume"] * 0.5
        return out
    z = _normal_cdf((out["dP"] / sigma_dp).fillna(0.0).values)
    out["buy_vol"] = out["Volume"].values * z
    out["sell_vol"] = out["Volume"].values * (1 - z)
    return out


@dataclass
class KyleLambdaEstimate:
    available: bool
    reason: str
    lambda_bps_per_pct_adv: float   # price move (bps) per 1% of ADV net signed order flow
    t_stat: float
    r_squared: float
    n_obs: int
    note: str


def estimate_kyle_lambda(intraday: pd.DataFrame, adv_shares: float) -> KyleLambdaEstimate:
    """
    Kyle (1985) lambda: regresses NEXT-bar returns on THIS-bar's Bulk-
    Volume-Classified net order flow (buy_vol - sell_vol), pooled across
    every day in Agent 1's intraday fetch window. Per-day pairing drops the
    first bar (its own BVC split is degenerate -- no prior close to diff
    against, see _bulk_volume_classify) and the last bar (no next-bar
    return to pair it with) so no pair spans an overnight gap or leaks
    information. See module docstring for why the response is lagged by
    one bar rather than contemporaneous with the order-flow predictor.

    Order flow is normalized by ADV so lambda is comparable across tickers
    of very different liquidity: it is reported as the return (in bps)
    associated with a net order-flow imbalance equal to 1% of average
    daily volume, observed one bar later.

    This is in the same spirit as the regression approach used by Breen,
    Hodrick & Korajczyk (2002) and cited in Almgren et al. (2005) Section 1
    -- "regress net market movement ... against the net buy-sell imbalance"
    -- adapted to (a) BVC-classified order flow, since this platform has no
    tick-level trade classification, and (b) a one-bar lag, to keep that
    substitution from being circular.
    """
    if adv_shares <= 0 or intraday.empty:
        return KyleLambdaEstimate(False, "No ADV or intraday data available.", 0.0, 0.0, 0.0, 0, "")

    rows = []
    for d in sorted(intraday.index.normalize().unique()):
        day = intraday[intraday.index.normalize() == d]
        if len(day) < 4:
            continue
        bvc = _bulk_volume_classify(day)
        ofi = (bvc["buy_vol"] - bvc["sell_vol"]) / adv_shares * 100          # % of ADV, this bar
        ret_fwd = day["Close"].pct_change().shift(-1) * 10_000               # bps, NEXT bar's return
        df = pd.DataFrame({"ret_fwd": ret_fwd.values, "ofi": ofi.values}).iloc[1:-1]
        rows.append(df)

    if not rows:
        return KyleLambdaEstimate(False, "No valid intraday days found.", 0.0, 0.0, 0.0, 0, "")

    pooled = pd.concat(rows, ignore_index=True).dropna()
    n = len(pooled)
    if n < MIN_OBS_KYLE:
        return KyleLambdaEstimate(
            False, f"Only {n} bar-to-bar observations available (need >= {MIN_OBS_KYLE}).",
            0.0, 0.0, 0.0, n, ""
        )

    x = pooled["ofi"].values
    y = pooled["ret_fwd"].values
    x_mean, y_mean = x.mean(), y.mean()
    sxx = np.sum((x - x_mean) ** 2)
    if sxx <= 0:
        return KyleLambdaEstimate(False, "No variation in order flow to regress against.", 0.0, 0.0, 0.0, n, "")

    slope = np.sum((x - x_mean) * (y - y_mean)) / sxx
    intercept = y_mean - slope * x_mean
    y_hat = intercept + slope * x
    resid = y - y_hat
    sse = np.sum(resid ** 2)
    sst = np.sum((y - y_mean) ** 2)
    r2 = 1 - sse / sst if sst > 0 else 0.0

    dof = n - 2
    se_slope = math.sqrt(sse / dof / sxx) if dof > 0 and sxx > 0 else float("nan")
    t_stat = slope / se_slope if se_slope and not np.isnan(se_slope) and se_slope > 0 else 0.0

    sig_note = ("Statistically significant at ~95% (|t|>=2)." if abs(t_stat) >= 2 else
                "Not statistically significant at ~95% -- treat as a noisy/order-of-magnitude read.")
    if slope > 0:
        sign_note = ("Positive: net buy pressure of 1% of ADV this bar is followed by HIGHER "
                     "returns next bar -- consistent with genuine, partly-persistent price impact "
                     "(depth is limited; size moves the price and it doesn't fully bounce back).")
    else:
        sign_note = ("Negative: net buy pressure of 1% of ADV this bar is followed by LOWER "
                     "returns next bar -- consistent with short-horizon mean-reversion of intraday "
                     "price pressure (a bid-ask-bounce-like effect at 5-min granularity) rather than "
                     "persistent impact. This still matters for execution: it suggests part of any "
                     "impact this order causes may unwind on the next bar rather than sticking.")
    note = f"{sign_note} {sig_note}"

    return KyleLambdaEstimate(
        available=True, reason="",
        lambda_bps_per_pct_adv=round(float(slope), 3),
        t_stat=round(float(t_stat), 2),
        r_squared=round(float(r2), 4),
        n_obs=n,
        note=note,
    )


@dataclass
class VPINEstimate:
    available: bool
    reason: str
    vpin_score: float        # 0-1, higher = more one-sided/toxic order flow
    label: str               # "Low" | "Normal" | "Elevated" | "High"
    n_bars: int
    window_bars: int
    note: str


def compute_vpin(intraday: pd.DataFrame) -> VPINEstimate:
    """
    Time-bar approximation of VPIN (see module docstring for the canonical-
    vs-approximated distinction). Uses the most recently completed session
    with the largest bar count in Agent 1's fetch window, classifies each
    bar's volume via Bulk Volume Classification, and computes:

        VPIN = mean_over_window( |buy_vol - sell_vol| / total_vol )

    over the trailing min(VPIN_WINDOW_BARS, bars available) bars. This is
    the standard VPIN formula (Easley/Lopez de Prado/O'Hara) with volume
    buckets substituted by fixed-count time bars -- so it is comparable in
    spirit (a 0-1 order-flow-imbalance score) but not numerically identical
    to a tick-data VPIN reading, and is labeled as such throughout the UI.

    Since there is no cross-sectional universe here to derive a proper
    percentile rank (real VPIN deployments compare a stock's VPIN to its own
    trailing history or to a peer universe), the label buckets are fixed,
    literature-informed thresholds rather than a percentile: scores are
    typically well below 0.3 in calm conditions and can approach or exceed
    0.6-0.7 in the kind of toxic, one-sided flow VPIN was designed to catch
    (e.g. the pre-Flash-Crash reading). Treat the label as directional, not
    a calibrated probability.
    """
    if intraday.empty:
        return VPINEstimate(False, "No intraday data available.", 0.0, "N/A", 0, 0, "")

    dates = sorted(intraday.index.normalize().unique())
    best_day = max(dates, key=lambda d: len(intraday[intraday.index.normalize() == d]))
    day = intraday[intraday.index.normalize() == best_day]

    if len(day) < MIN_OBS_VPIN:
        return VPINEstimate(False, f"Only {len(day)} bars in the most complete session "
                            f"(need >= {MIN_OBS_VPIN}).", 0.0, "N/A", len(day), 0, "")

    bvc = _bulk_volume_classify(day)
    window = min(VPIN_WINDOW_BARS, len(bvc))
    recent = bvc.iloc[-window:]
    total_vol = recent["Volume"].sum()
    if total_vol <= 0:
        return VPINEstimate(False, "Zero volume in the VPIN window.", 0.0, "N/A", len(day), window, "")

    imbalance = (recent["buy_vol"] - recent["sell_vol"]).abs()
    vpin = float(imbalance.sum() / total_vol) if total_vol > 0 else 0.0
    vpin = min(1.0, max(0.0, vpin))

    if vpin >= 0.6:
        label = "High"
        note = ("Highly one-sided order flow over the trailing window -- comparable in magnitude "
                "to pre-stress readings documented in the VPIN literature (e.g. ahead of the May "
                "2010 Flash Crash). Treat as a signal to reduce urgency/size or widen participation "
                "caps rather than as a precise crash probability.")
    elif vpin >= 0.4:
        label = "Elevated"
        note = "Order flow is moderately one-sided -- consistent with directional pressure building."
    elif vpin >= 0.25:
        label = "Normal"
        note = "Order flow imbalance is within a typical range."
    else:
        label = "Low"
        note = "Order flow is close to balanced buy/sell pressure."

    return VPINEstimate(
        available=True, reason="", vpin_score=round(vpin, 4), label=label,
        n_bars=len(day), window_bars=window, note=note,
    )


@dataclass
class AlmgrenImpactEstimate:
    available: bool
    reason: str
    permanent_impact_bps: float
    temporary_impact_bps: float
    realized_impact_bps: float     # J = I/2 + K (total expected cost per the calibrated model)
    liquidity_factor_applied: bool
    note: str


def almgren_2005_impact(order_shares: float, adv_shares: float, vol_ann: float,
                        participation_rate: float, shares_outstanding: Optional[float] = None
                        ) -> AlmgrenImpactEstimate:
    """
    Almgren, Thum, Hauptmann & Li (2005) calibrated impact model -- see
    module docstring for the formula and fitted coefficients. `T` (fraction
    of a trading day over which the order executes) is derived from the
    order size and a participation rate the same way Agent 6's capacity
    table already does (T = (X/V) / participation_rate, capped at 1 day for
    this single-day cross-check since the fitted coefficients were
    estimated on orders completed within one day in the original study).
    """
    if adv_shares <= 0 or order_shares <= 0:
        return AlmgrenImpactEstimate(False, "No order size or ADV to evaluate.", 0.0, 0.0, 0.0, False, "")

    sigma_daily = vol_ann / math.sqrt(252) * 10_000  # bps
    x_over_v = order_shares / adv_shares
    t_frac = min(1.0, x_over_v / participation_rate) if participation_rate > 0 else 1.0
    if t_frac <= 0:
        t_frac = 1e-4

    liquidity_factor = 1.0
    liquidity_applied = False
    if shares_outstanding and shares_outstanding > 0:
        liquidity_factor = (shares_outstanding / adv_shares) ** ALMGREN_DELTA
        liquidity_applied = True

    permanent_bps = ALMGREN_GAMMA * sigma_daily * (x_over_v ** ALMGREN_ALPHA) * liquidity_factor
    temporary_bps = ALMGREN_ETA * sigma_daily * (x_over_v / t_frac) ** ALMGREN_BETA
    realized_bps = permanent_bps / 2 + temporary_bps

    note = (
        f"Permanent (information-driven, persists) + temporary (liquidity-demand, decays) "
        f"impact per Almgren et al. (2005)'s fit to ~29,500 real institutional orders."
        + (" Turnover liquidity factor (shares outstanding / ADV) applied."
           if liquidity_applied else
           " Shares-outstanding unavailable from the free data feed -- turnover liquidity "
           "factor omitted (assumed neutral); estimate is somewhat less precise as a result.")
    )

    return AlmgrenImpactEstimate(
        available=True, reason="",
        permanent_impact_bps=round(permanent_bps, 2),
        temporary_impact_bps=round(temporary_bps, 2),
        realized_impact_bps=round(realized_bps, 2),
        liquidity_factor_applied=liquidity_applied,
        note=note,
    )


@dataclass
class MicrostructureAssessment:
    kyle_lambda: KyleLambdaEstimate
    vpin: VPINEstimate
    almgren_impact: AlmgrenImpactEstimate


def assess_microstructure(market_data, order_shares: float, urgency: str, log=None) -> MicrostructureAssessment:
    """Main entry point for Agent 9."""
    def _log(msg):
        if log:
            log(msg)

    _log(f"Assessing microstructure for {market_data.ticker}...")

    kyle = estimate_kyle_lambda(market_data.intraday, market_data.adv_shares)
    _log(f"  Kyle's lambda: {'available' if kyle.available else 'unavailable'} "
         f"({kyle.lambda_bps_per_pct_adv:+.2f} bps/1%ADV, t={kyle.t_stat:.1f})" if kyle.available else
         f"  Kyle's lambda: unavailable ({kyle.reason})")

    vpin = compute_vpin(market_data.intraday)
    _log(f"  VPIN: {vpin.vpin_score:.3f} ({vpin.label})" if vpin.available else f"  VPIN: unavailable ({vpin.reason})")

    from agents.agent3_algo_simulation import POV_RATES
    rate = POV_RATES.get(urgency, 0.15)
    shares_out = getattr(market_data, "shares_outstanding", None)
    almgren = almgren_2005_impact(order_shares, market_data.adv_shares, market_data.realized_vol_ann,
                                  rate, shares_out)
    _log(f"  Almgren (2005) impact: perm={almgren.permanent_impact_bps:.1f}bps "
         f"temp={almgren.temporary_impact_bps:.1f}bps" if almgren.available else "  Almgren (2005): unavailable")

    _log("Agent 9 complete.")
    return MicrostructureAssessment(kyle_lambda=kyle, vpin=vpin, almgren_impact=almgren)
