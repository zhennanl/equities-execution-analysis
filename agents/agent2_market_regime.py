"""
Agent 2: Market Regime Assessment Agent
Classifies current market conditions across three dimensions:
  1. Intraday volatility (range vs 20-day median)
  2. Volume pattern (U-shaped vs uniform intraday distribution)
  3. Price trend (Lo-MacKinlay (1988) variance ratio test, with lag-1
     autocorrelation retained as a simpler supporting statistic)
"""

import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from agents.agent1_market_data import MarketData


@dataclass
class RegimeAssessment:
    # Dimension 1: Volatility
    vol_label: str        # "Tight" | "Normal" | "Trending" | "Extremely Trending"
    vol_ratio: float      # today_range / 20d_median_range

    # Dimension 2: Volume pattern
    volume_label: str     # "U-Shaped" | "Uniform" | "Midday-Heavy"
    u_shape_score: float  # avg(open_vol, close_vol) / midday_vol

    # Dimension 3: Price trend
    trend_label: str      # "Trending" | "Mean-Reverting" | "Neutral"
    autocorr: float       # lag-1 autocorrelation of 5-min returns (legacy/supporting stat)

    summary: str          # one-line description for display

    # Variance-ratio test detail (Lo-MacKinlay 1988) -- defaulted so existing
    # callers constructing RegimeAssessment positionally still work
    vr_available: bool = False
    vr_q: int = 0                  # primary aggregation horizon used for the headline label
    vr_ratio: float = 1.0          # VR(q): >1 momentum, <1 mean-reversion, =1 random walk
    vr_zstat: float = 0.0          # heteroskedasticity-robust z*-statistic at q
    vr_significant: bool = False   # |z*| >= 1.96 (~95%)
    vr_detail: list = field(default_factory=list)  # [{q, vr, z_homo, z_robust}, ...] full grid


def _classify_volatility(daily: pd.DataFrame):
    """
    Range-based volatility regime.

    ratio = today's (High-Low) / median of prior 20 days' (High-Low)

    Mutually exclusive thresholds:
      ratio > 1.50           → Extremely Trending
      1.20 < ratio <= 1.50   → Trending
      0.80 <= ratio <= 1.20  → Normal
      ratio < 0.80           → Tight
    """
    ranges = daily["High"] - daily["Low"]
    if len(ranges) < 3:
        return "Normal", 1.0

    median_range = float(ranges.iloc[:-1].tail(20).median())
    today_range = float(ranges.iloc[-1])

    if median_range <= 0:
        return "Normal", 1.0

    ratio = today_range / median_range

    if ratio > 1.50:
        label = "Extremely Trending"
    elif ratio > 1.20:
        label = "Trending"
    elif ratio >= 0.80:
        label = "Normal"
    else:
        label = "Tight"

    return label, round(ratio, 3)


def _classify_volume(intraday: pd.DataFrame):
    """
    Intraday volume concentration pattern.

    Splits the most recent day into three segments:
      open  — first 25% of bars
      close — last 25% of bars
      mid   — middle 50%

    U-shape score = avg(open_vol, close_vol) / midday_vol

      score > 1.50   → U-Shaped     (heavy open/close, light midday)
      score >= 0.80  → Uniform      (balanced across the day)
      score < 0.80   → Midday-Heavy (unusual inversion)
    """
    last_date = intraday.index.normalize().max()
    today = intraday[intraday.index.normalize() == last_date]

    n = len(today)
    if n < 6:
        return "Uniform", 1.0

    cut = max(1, n // 4)
    open_vol = float(today["Volume"].iloc[:cut].mean())
    close_vol = float(today["Volume"].iloc[-cut:].mean())
    midday_vol = float(today["Volume"].iloc[cut:-cut].mean())

    if midday_vol <= 0:
        return "Uniform", 1.0

    score = (open_vol + close_vol) / 2 / midday_vol

    if score > 1.50:
        label = "U-Shaped"
    elif score >= 0.80:
        label = "Uniform"
    else:
        label = "Midday-Heavy"

    return label, round(score, 3)


def _classify_trend_legacy_autocorr(rets: pd.Series) -> float:
    """Lag-1 autocorrelation, reported as a supporting stat next to the formal
    variance-ratio test. Guarded (2026-07-08): a zero-variance return window
    made pandas' nancorr emit a divide RuntimeWarning and propagate NaN — now
    silenced at the numpy level and mapped to 0.0 (no detectable persistence),
    which is the correct reading of a flat window."""
    if len(rets) < 10 or float(rets.std()) == 0.0:   # original 10-obs floor kept
        return 0.0
    with np.errstate(invalid="ignore", divide="ignore"):
        ac = rets.autocorr(lag=1)
    return round(float(ac), 4) if np.isfinite(ac) else 0.0


def _variance_ratio(rets: np.ndarray, q: int) -> dict:
    """
    Lo & MacKinlay (1988) variance ratio statistic for a single aggregation
    value q, on one contiguous return series (no overnight gaps):

      VR(q) = Var(q-period overlapping returns, adjusted) / (q * Var(1-period returns))

    Under the random-walk null, VR(q) = 1. VR(q) > 1 indicates positive
    serial correlation (momentum/trending); VR(q) < 1 indicates negative
    serial correlation (mean-reversion) -- a materially more standard and
    robust test for this than a raw lag-1 autocorrelation threshold, since
    it aggregates evidence across a full return-differencing horizon rather
    than a single lag, and ships with a proper asymptotic test statistic
    rather than an arbitrary +/-0.10 cutoff.

    Returns both the homoscedastic z-statistic (assumes iid Gaussian
    returns -- Lo-MacKinlay eq. 8) and the heteroskedasticity-robust z*
    statistic (Lo-MacKinlay eq. 14a/14b), which corrects for the
    conditional heteroskedasticity (volatility clustering) that intraday
    equity returns are well known to exhibit. |z*| >= 1.96 is significant
    at ~95% under the random-walk null.
    """
    nq = len(rets)
    if nq <= q or q < 2:
        return {"q": q, "vr": 1.0, "z_homo": 0.0, "z_robust": 0.0, "available": False}

    mu = rets.mean()
    dev = rets - mu

    # 1-period variance (unbiased)
    var_1 = np.sum(dev ** 2) / (nq - 1)

    # q-period overlapping variance (Lo-MacKinlay's bias-adjusted estimator)
    m = q * (nq - q + 1) * (1 - q / nq)
    cum = np.concatenate([[0.0], np.cumsum(rets)])
    q_rets = cum[q:] - cum[:-q]              # overlapping q-period sums
    var_q = np.sum((q_rets - q * mu) ** 2) / m if m > 0 else np.nan

    if var_1 <= 0 or np.isnan(var_q):
        return {"q": q, "vr": 1.0, "z_homo": 0.0, "z_robust": 0.0, "available": False}

    vr = var_q / (q * var_1)

    # Homoscedastic z-stat (Lo-MacKinlay eq. 8)
    theta1 = 2 * (2 * q - 1) * (q - 1) / (3 * q * nq)
    z_homo = (vr - 1) / np.sqrt(theta1) if theta1 > 0 else 0.0

    # Heteroskedasticity-robust z*-stat (Lo-MacKinlay eq. 14a/14b)
    dev2_sum = np.sum(dev ** 2)
    theta2 = 0.0
    for j in range(1, q):
        num = np.sum((dev[j:] ** 2) * (dev[:-j] ** 2))
        delta_j = (num / (dev2_sum ** 2)) * nq if dev2_sum > 0 else 0.0
        theta2 += (2 * (q - j) / q) ** 2 * delta_j
    z_robust = (vr - 1) / np.sqrt(theta2) if theta2 > 0 else 0.0

    return {"q": q, "vr": round(float(vr), 4), "z_homo": round(float(z_homo), 3),
           "z_robust": round(float(z_robust), 3), "available": True}


def _classify_trend(intraday: pd.DataFrame):
    """
    Price-trend classification via the Lo-MacKinlay (1988) variance ratio
    test on the most recent trading day's 5-min log returns, computed at a
    grid of aggregation horizons q in (2, 4, 8) (i.e. 10-, 20-, and 40-min
    return horizons on 5-min bars). q=4 is used as the headline statistic
    (a middle-of-the-grid horizon, long enough to average out bid-ask-bounce
    -like microstructure noise at q=2 but still short enough to have a
    reasonable sample size on the shortest supported sessions).

      Significant (|z*_robust at q=4| >= 1.96) and VR > 1  → Trending
      Significant and VR < 1                                → Mean-Reverting
      Not significant, or insufficient bars                 → Neutral

    Falls back to "Neutral" with vr_available=False if there are too few
    bars for a q=8 estimate (matches the old function's < 10 observations
    guard, extended since the VR grid needs more bars than a single lag-1
    autocorrelation did).
    """
    last_date = intraday.index.normalize().max()
    today = intraday[intraday.index.normalize() == last_date]

    closes = today["Close"].dropna()
    if len(closes) < 20:
        return "Neutral", 0.0, {"available": False, "q": 0, "vr": 1.0, "z_robust": 0.0}, []

    log_rets = np.log(closes / closes.shift(1)).dropna().values
    autocorr = _classify_trend_legacy_autocorr(pd.Series(log_rets))

    grid = [q for q in (2, 4, 8) if len(log_rets) > q * 3]  # need a handful of non-overlapping windows
    detail = [_variance_ratio(log_rets, q) for q in grid]
    detail = [d for d in detail if d]

    primary = next((d for d in detail if d["q"] == 4 and d["available"]), None)
    if primary is None:
        primary = next((d for d in detail if d["available"]), None)

    if primary is None:
        return "Neutral", autocorr, {"available": False, "q": 0, "vr": 1.0, "z_robust": 0.0}, detail

    significant = abs(primary["z_robust"]) >= 1.96
    if significant and primary["vr"] > 1:
        label = "Trending"
    elif significant and primary["vr"] < 1:
        label = "Mean-Reverting"
    else:
        label = "Neutral"

    return label, autocorr, primary, detail


def assess_regime(market_data: MarketData, log=None) -> RegimeAssessment:
    """Main entry point for Agent 2."""
    def _log(msg):
        if log:
            log(msg)

    _log(f"Assessing regime for {market_data.ticker}...")

    vol_label, vol_ratio = _classify_volatility(market_data.daily)
    _log(f"  Range: {vol_label}  ({vol_ratio:.2f}x 20d median)")

    volume_label, u_score = _classify_volume(market_data.intraday)
    _log(f"  Volume: {volume_label}  (U-score {u_score:.2f})")

    trend_label, autocorr, vr_primary, vr_detail = _classify_trend(market_data.intraday)
    if vr_primary.get("available"):
        _log(f"  Trend: {trend_label}  (VR(q={vr_primary['q']})={vr_primary['vr']:.2f}, "
             f"z*={vr_primary['z_robust']:+.2f}, lag-1 autocorr {autocorr:+.3f})")
    else:
        _log(f"  Trend: {trend_label}  (insufficient bars for a variance-ratio read; "
             f"lag-1 autocorr {autocorr:+.3f})")

    summary = f"{vol_label} · {volume_label} volume · {trend_label} returns"
    _log("Agent 2 complete.")

    return RegimeAssessment(
        vol_label=vol_label,
        vol_ratio=vol_ratio,
        volume_label=volume_label,
        u_shape_score=u_score,
        trend_label=trend_label,
        autocorr=autocorr,
        vr_available=vr_primary.get("available", False),
        vr_q=vr_primary.get("q", 0),
        vr_ratio=vr_primary.get("vr", 1.0),
        vr_zstat=vr_primary.get("z_robust", 0.0),
        vr_significant=abs(vr_primary.get("z_robust", 0.0)) >= 1.96,
        vr_detail=vr_detail,
        summary=summary,
    )
