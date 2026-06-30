"""
Agent 2: Market Regime Assessment Agent
Classifies current market conditions across three dimensions:
  1. Intraday volatility (range vs 20-day median)
  2. Volume pattern (U-shaped vs uniform intraday distribution)
  3. Price trend (lag-1 return autocorrelation)
"""

import numpy as np
import pandas as pd
from dataclasses import dataclass
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
    autocorr: float       # lag-1 autocorrelation of 5-min returns

    summary: str          # one-line description for display


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


def _classify_trend(intraday: pd.DataFrame):
    """
    Lag-1 autocorrelation of 5-min returns for the most recent trading day.

      autocorr > +0.10  → Trending      (positive momentum, returns persist)
      autocorr < -0.10  → Mean-Reverting (returns reverse — common in equities)
      -0.10 to +0.10    → Neutral
    """
    last_date = intraday.index.normalize().max()
    today = intraday[intraday.index.normalize() == last_date]

    rets = today["Close"].pct_change().dropna()
    if len(rets) < 10:
        return "Neutral", 0.0

    ac = float(rets.autocorr(lag=1))
    if np.isnan(ac):
        return "Neutral", 0.0

    if ac > 0.10:
        label = "Trending"
    elif ac < -0.10:
        label = "Mean-Reverting"
    else:
        label = "Neutral"

    return label, round(ac, 4)


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

    trend_label, autocorr = _classify_trend(market_data.intraday)
    _log(f"  Trend: {trend_label}  (lag-1 autocorr {autocorr:+.3f})")

    summary = f"{vol_label} · {volume_label} volume · {trend_label} returns"
    _log("Agent 2 complete.")

    return RegimeAssessment(
        vol_label=vol_label,
        vol_ratio=vol_ratio,
        volume_label=volume_label,
        u_shape_score=u_score,
        trend_label=trend_label,
        autocorr=autocorr,
        summary=summary,
    )
