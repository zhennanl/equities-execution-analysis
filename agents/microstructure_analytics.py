"""
Research-grounded microstructure analytics (see docs/MICROSTRUCTURE_RESEARCH_IMPROVEMENTS.md).

  * edge_spread            — EDGE effective-spread estimator, Ardia, Guidotti &
                             Kroencke (JFE 2024). A faithful reimplementation of
                             the authors' reference algorithm (MIT-licensed,
                             https://github.com/eguidotti/bidask), the modern,
                             more-efficient cross-check to Corwin-Schultz (2012)
                             and Abdi-Ranaldo (2017).
  * amihud_illiquidity     — Amihud (2002) ILLIQ = mean(|return| / dollar volume),
                             the daily price-response-per-dollar proxy, computable
                             wherever OHLCV exists (valuable across Asia).
  * intraday_seasonality   — open/midday/close volume buckets + U-shape ratio,
                             the seasonality a desk schedules around.
  * acf, ljung_box         — autocorrelation function and the Ljung-Box test for
                             serial dependence (the JD's "time series analysis").

All inputs are free OHLCV / bar data; every estimator is spread/impact from
ranges and volume, not a quoted order book.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats as _stats


# ══════════════════════════════════════════════════════════════════════════
# EDGE effective-spread estimator (Ardia, Guidotti & Kroencke, JFE 2024)
# ══════════════════════════════════════════════════════════════════════════

def edge_spread(open_, high, low, close, sign: bool = False) -> float:
    """Effective bid-ask spread from OHLC prices (fraction; 0.01 = 1%).

    Faithful reimplementation of the authors' reference `edge()` (JFE 2024,
    github.com/eguidotti/bidask, MIT). Requires >= 3 observations; returns NaN
    otherwise. Estimates the root-mean-square effective spread over the sample.
    """
    o = np.log(np.asarray(open_, dtype=float))
    h = np.log(np.asarray(high, dtype=float))
    l = np.log(np.asarray(low, dtype=float))
    c = np.log(np.asarray(close, dtype=float))
    nobs = len(o)
    if nobs < 3 or len(h) != nobs or len(l) != nobs or len(c) != nobs:
        return float("nan")
    m = (h + l) / 2.0

    h1, l1, c1, m1 = h[:-1], l[:-1], c[:-1], m[:-1]
    o, h, l, c, m = o[1:], h[1:], l[1:], c[1:], m[1:]

    r1 = m - o
    r2 = o - m1
    r3 = m - c1
    r4 = c1 - m1
    r5 = o - c1

    tau = np.where(np.isnan(h) | np.isnan(l) | np.isnan(c1), np.nan, ((h != l) | (l != c1)).astype(float))
    po1 = tau * np.where(np.isnan(o) | np.isnan(h), np.nan, (o != h).astype(float))
    po2 = tau * np.where(np.isnan(o) | np.isnan(l), np.nan, (o != l).astype(float))
    pc1 = tau * np.where(np.isnan(c1) | np.isnan(h1), np.nan, (c1 != h1).astype(float))
    pc2 = tau * np.where(np.isnan(c1) | np.isnan(l1), np.nan, (c1 != l1).astype(float))

    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        pt = np.nanmean(tau)
        po = np.nanmean(po1) + np.nanmean(po2)
        pc = np.nanmean(pc1) + np.nanmean(pc2)
        if np.nansum(tau) < 2 or po == 0 or pc == 0:
            return float("nan")
        d1 = r1 - np.nanmean(r1) / pt * tau
        d3 = r3 - np.nanmean(r3) / pt * tau
        d5 = r5 - np.nanmean(r5) / pt * tau
        x1 = -4.0 / po * d1 * r2 + -4.0 / pc * d3 * r4
        x2 = -4.0 / po * d1 * r5 + -4.0 / pc * d5 * r4
        e1 = np.nanmean(x1)
        e2 = np.nanmean(x2)
        v1 = np.nanmean(x1 ** 2) - e1 ** 2
        v2 = np.nanmean(x2 ** 2) - e2 ** 2

    vt = v1 + v2
    s2 = (v2 * e1 + v1 * e2) / vt if vt > 0 else (e1 + e2) / 2.0
    s = np.sqrt(np.abs(s2))
    if sign:
        s *= np.sign(s2)
    return float(s)


def estimate_spread_edge(daily: pd.DataFrame) -> dict:
    """EDGE spread on a daily OHLC frame, returned in the same shape as the
    Corwin-Schultz / Abdi-Ranaldo estimators (spread_bps + half_spread_bps)."""
    need = {"Open", "High", "Low", "Close"}
    if not need.issubset(daily.columns) or len(daily) < 3:
        return {"spread_bps": None, "half_spread_bps": None, "n_obs": 0,
                "note": "Need >= 3 OHLC bars for EDGE."}
    s = edge_spread(daily["Open"].values, daily["High"].values,
                    daily["Low"].values, daily["Close"].values)
    if not np.isfinite(s):
        return {"spread_bps": None, "half_spread_bps": None, "n_obs": len(daily),
                "note": "EDGE estimator returned NaN (degenerate OHLC in window)."}
    return {"spread_bps": round(s * 10_000, 2),
            "half_spread_bps": round(s * 10_000 / 2, 2),
            "n_obs": len(daily), "note": ""}


# ══════════════════════════════════════════════════════════════════════════
# Amihud (2002) illiquidity
# ══════════════════════════════════════════════════════════════════════════

def amihud_illiquidity(daily: pd.DataFrame, scale: float = 1e6) -> dict:
    """ILLIQ = mean(|daily return| / daily dollar volume). Higher = more illiquid
    (bigger price move per dollar traded). Reported scaled (×`scale`) since the
    raw figure is tiny for liquid names, plus bps-impact-per-$1M notional."""
    if not {"Close", "Volume"}.issubset(daily.columns) or len(daily) < 2:
        return {"illiq_scaled": None, "impact_bps_per_1m": None, "n_obs": 0,
                "note": "Need Close + Volume with >= 2 rows."}
    px = daily["Close"].astype(float).values
    vol = daily["Volume"].astype(float).values
    ret = np.abs(np.diff(px) / px[:-1])
    dollar_vol = (px[1:] * vol[1:])
    ok = dollar_vol > 0
    if ok.sum() == 0:
        return {"illiq_scaled": None, "impact_bps_per_1m": None, "n_obs": 0,
                "note": "No positive dollar-volume days."}
    illiq = float(np.mean(ret[ok] / dollar_vol[ok]))
    return {"illiq_scaled": round(illiq * scale, 4),
            "impact_bps_per_1m": round(illiq * 1e6 * 10_000, 3),   # bps move per $1M
            "n_obs": int(ok.sum()), "note": ""}


# ══════════════════════════════════════════════════════════════════════════
# Intraday seasonality (U-shape), session/lunch-break aware
# ══════════════════════════════════════════════════════════════════════════

def intraday_seasonality(intraday: pd.DataFrame, n_buckets: int = 3) -> dict:
    """Average share of daily volume by intraday position, bucketed open/midday/
    close (thirds of the session by bar index, so it is lunch-break-robust). A
    U-shape ratio > 1 means the open+close carry more than the midday."""
    if "Volume" not in intraday.columns or len(intraday) == 0:
        return {"buckets": None, "u_shape_ratio": None, "note": "No volume data."}
    df = intraday.copy()
    df["_date"] = df.index.normalize()
    shares = []
    for _, day in df.groupby("_date"):
        tv = float(day["Volume"].sum())
        if tv <= 0 or len(day) < n_buckets:
            continue
        v = day["Volume"].astype(float).values / tv
        idx = np.linspace(0, n_buckets, len(v) + 1)[1:] - 1e-9
        bucket_share = [float(v[(idx >= b) & (idx < b + 1)].sum()) for b in range(n_buckets)]
        shares.append(bucket_share)
    if not shares:
        return {"buckets": None, "u_shape_ratio": None, "note": "Insufficient intraday history."}
    mean_share = np.mean(shares, axis=0)
    labels = (["open", "midday", "close"] if n_buckets == 3
              else [f"bucket_{i+1}" for i in range(n_buckets)])
    buckets = {labels[i]: round(float(mean_share[i]) * 100, 1) for i in range(n_buckets)}
    if n_buckets == 3 and mean_share[1] > 0:
        u_ratio = float((mean_share[0] + mean_share[2]) / (2 * mean_share[1]))
    else:
        u_ratio = float("nan")
    return {"buckets": buckets, "u_shape_ratio": round(u_ratio, 2) if np.isfinite(u_ratio) else None,
            "n_days": len(shares), "note": ""}


# ══════════════════════════════════════════════════════════════════════════
# Time-series tools — ACF + Ljung-Box (the JD's "time series analysis")
# ══════════════════════════════════════════════════════════════════════════

def acf(x, nlags: int = 10) -> np.ndarray:
    """Sample autocorrelation function rho_0..rho_nlags (rho_0 == 1)."""
    x = np.asarray(x, dtype=float)
    x = x[~np.isnan(x)]
    n = len(x)
    x = x - x.mean()
    denom = float(x @ x)
    if denom == 0:
        return np.concatenate([[1.0], np.zeros(nlags)])
    out = [1.0]
    for k in range(1, nlags + 1):
        out.append(float((x[k:] @ x[:-k]) / denom))
    return np.array(out)


def ljung_box(x, lags: int = 10) -> dict:
    """Ljung-Box Q-test for autocorrelation up to `lags`. Low p => serial
    dependence present (not white noise)."""
    x = np.asarray(x, dtype=float)
    x = x[~np.isnan(x)]
    n = len(x)
    if n <= lags + 1:
        return {"lb_stat": None, "p_value": None, "lags": lags,
                "autocorrelated": None, "note": "Not enough observations."}
    r = acf(x, lags)[1:]
    k = np.arange(1, lags + 1)
    q = n * (n + 2) * np.sum(r ** 2 / (n - k))
    p = float(_stats.chi2.sf(q, lags))
    return {"lb_stat": round(float(q), 3), "p_value": round(p, 4), "lags": lags,
            "autocorrelated": bool(p < 0.05), "note": ""}


# ──────────────────────────────────────────────────────────────────────────
# Roll (1984) implied spread — 4th spread cross-check (added 2026-07-08)
# ──────────────────────────────────────────────────────────────────────────

def roll_spread(daily: pd.DataFrame) -> dict:
    """Roll (1984): bid-ask bounce makes successive price CHANGES negatively
    autocorrelated; the implied effective spread is 2*sqrt(-cov(dP_t, dP_{t-1})).
    Returned in bps of the mean close, same dict shape as the other estimators.
    When the serial covariance is positive (trending/informed flow dominates
    the bounce) the estimator is undefined — reported as unavailable rather
    than clamped, which is itself diagnostic."""
    if "Close" not in daily.columns or len(daily) < 10:
        return {"spread_bps": None, "half_spread_bps": None, "n_obs": 0,
                "note": "Need >= 10 closes for Roll."}
    px = daily["Close"].astype(float).values
    dp = np.diff(px)
    if len(dp) < 5:
        return {"spread_bps": None, "half_spread_bps": None, "n_obs": len(px),
                "note": "Too few price changes."}
    cov = float(np.cov(dp[1:], dp[:-1])[0, 1])
    # eps guard: a pure trend gives cov ~ -1e-29 (numerical zero) — that is
    # "no bounce detectable", not a zero-spread reading.
    if cov >= -1e-10:
        return {"spread_bps": None, "half_spread_bps": None, "n_obs": len(px),
                "note": "Serial covariance of price changes is non-negative — "
                        "bounce swamped by trend/information; Roll undefined "
                        "(common on trending samples, itself informative)."}
    spread = 2.0 * np.sqrt(-cov)
    mid = float(np.mean(px))
    bps = spread / mid * 10_000
    return {"spread_bps": round(bps, 2), "half_spread_bps": round(bps / 2, 2),
            "n_obs": len(px), "note": "Roll (1984) serial-covariance estimator."}


# ──────────────────────────────────────────────────────────────────────────
# Post-fill markout curve — fill quality / adverse selection (added 2026-07-08)
# ──────────────────────────────────────────────────────────────────────────

MARKOUT_HORIZONS_BARS = (1, 2, 3, 6, 12)     # x 5-min bars = 5/10/15/30/60 min


def compute_markout_curve(schedule: pd.DataFrame, day: pd.DataFrame, side: str,
                          horizons: tuple = MARKOUT_HORIZONS_BARS) -> dict:
    """Share-weighted post-fill markouts: for every child slice, the signed
    move from its fill price to the bar close h bars later,
        markout_h = sign(side) * (P_{i+h} - fill_i) / fill_i * 1e4,
    averaged across slices weighted by shares. Positive = price kept moving
    AGAINST the order after fills (impact persists / order behind the market);
    negative = temporary impact reverted after fills. The standard TCA fill-
    quality curve, computed on 5-minute bars (bar close as the mid proxy —
    disclosed; tick-level markouts need tick data).

    Returns {"available", "curve": DataFrame[horizon_min, markout_bps, n_slices],
             "note"}."""
    from agents.order_ticket import side_sign
    if schedule is None or len(schedule) == 0 or "shares_traded" not in schedule:
        return {"available": False, "reason": "No schedule.", "curve": None, "note": ""}
    fills = schedule[schedule["shares_traded"] > 0]
    if len(fills) == 0:
        return {"available": False, "reason": "No filled slices.", "curve": None, "note": ""}

    closes = day["Close"].astype(float).values
    n = len(closes)
    # map each fill to its BAR position via the schedule's 'time' column —
    # sparse schedules (LIQ/STEALTH auction-window algos) don't have
    # one-row-per-bar, so positional indexing would misalign.
    bar_pos = {t: i for i, t in enumerate(day.index)}
    sgn = side_sign(side)

    rows = []
    for h in horizons:
        num, den, cnt = 0.0, 0.0, 0
        for _, r in fills.iterrows():
            i = bar_pos.get(r["time"])
            if i is None or i + h >= n:
                continue
            mo = sgn * (closes[i + h] - float(r["price"])) / float(r["price"]) * 10_000
            q = float(r["shares_traded"])
            num += mo * q
            den += q
            cnt += 1
        if den > 0:
            rows.append({"horizon_min": h * 5, "markout_bps": round(num / den, 2),
                         "n_slices": cnt})
    if not rows:
        return {"available": False,
                "reason": "No slice has enough post-fill bars (fills too close to the close).",
                "curve": None, "note": ""}
    curve = pd.DataFrame(rows)
    last = curve.iloc[-1]["markout_bps"]
    first = curve.iloc[0]["markout_bps"]
    if last > max(first, 0):
        note = ("Rising markouts: the price kept moving against the order after fills — "
                "impact looks persistent / the order was behind the market; slowing down "
                "would not have obviously helped.")
    elif last < min(first, 0):
        note = ("Falling/negative markouts: post-fill reversion — part of the paid impact "
                "was temporary liquidity concession; a slower schedule or more passive "
                "tactics could have recaptured some of it.")
    else:
        note = "Flat markouts: little post-fill drift either way at these horizons."
    return {"available": True, "reason": "", "curve": curve, "note": note}
