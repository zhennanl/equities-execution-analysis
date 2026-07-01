"""
Agent 1: Market Data Agent
Fetches intraday and daily OHLCV data from yfinance.
Computes ADV, realized volatility, and intraday volume profile.
"""

import time
import yfinance as yf
import pandas as pd
import numpy as np
from dataclasses import dataclass

# Suffix, market open/close (local time, 24h), expected 5-min bars per session
# Bars measured empirically from yfinance output; used for vol normalisation
# and "data completeness" checks in downstream agents.
#
# China-A has a lunch break (09:30-11:30, 13:00-15:00) → 49 bars
# Vietnam HOSE has a lunch break  (09:15-11:30, 13:00-14:45) → 46 bars
# Thailand SET has a lunch break  (10:00-12:30, 14:00-16:30) → 61 bars
# Indonesia IDX has a lunch break (09:00-12:00, 13:30-16:00) → 67 bars (Mon-Thu)
# Hong Kong HKEX has a lunch break (09:30-12:00, 13:00-16:00) → ~67 bars — not
#   previously documented; "bars": 78 assumed a continuous session and
#   overstated realized_vol_ann's annualization factor by ~8% (sqrt(78/67)).
#   Fixed after live yfinance verification.
# Japan TSE has a lunch break (09:00-11:30, 12:30-15:30) → ~65 bars — likewise
#   not previously documented; "bars": 78 overstated annualized vol by ~10%
#   (sqrt(78/65)). Fixed after live yfinance verification.
# Korea KRX: yfinance's intraday feed consistently ends ~30 min before the
#   official 15:30 close (last bar ~14:55) → ~72 bars, not 78. Whatever the
#   cause, this is what the data source actually delivers, so it's what the
#   vol/impact model should assume. Fixed after live yfinance verification.
MARKET_INFO = {
    # ── Core ──────────────────────────────────────────────────────────────
    "Taiwan (TWSE)":        {"suffix": ".TW", "open": "09:00", "close": "13:30", "bars": 54},
    "Hong Kong (HKEX)":     {"suffix": ".HK", "open": "09:30", "close": "16:00", "bars": 67},
    "Japan (TSE)":          {"suffix": ".T",  "open": "09:00", "close": "15:30", "bars": 65},
    "Korea (KRX)":          {"suffix": ".KS", "open": "09:00", "close": "15:30", "bars": 72},
    "US":                   {"suffix": "",    "open": "09:30", "close": "16:00", "bars": 78},
    # ── Extended Asia ─────────────────────────────────────────────────────
    "Singapore (SGX)":      {"suffix": ".SI", "open": "09:00", "close": "17:00", "bars": 85},
    "China-A Shanghai":     {"suffix": ".SS", "open": "09:30", "close": "15:00", "bars": 49},
    "China-A Shenzhen":     {"suffix": ".SZ", "open": "09:30", "close": "15:00", "bars": 49},
    "India (NSE)":          {"suffix": ".NS", "open": "09:15", "close": "15:30", "bars": 75},
    "Australia (ASX)":      {"suffix": ".AX", "open": "10:00", "close": "16:00", "bars": 73},
    "Thailand (SET)":       {"suffix": ".BK", "open": "10:00", "close": "16:30", "bars": 61},
    "Indonesia (IDX)":      {"suffix": ".JK", "open": "09:00", "close": "16:15", "bars": 67},
    "Malaysia (KLSE)":      {"suffix": ".KL", "open": "09:00", "close": "17:00", "bars": 71},
    "Vietnam (HOSE)":       {"suffix": ".VN", "open": "09:15", "close": "14:45", "bars": 46},
}

@dataclass
class MarketData:
    ticker: str
    market: str
    intraday: pd.DataFrame
    daily: pd.DataFrame
    adv_shares: float
    adv_usd: float
    current_price: float
    realized_vol_ann: float
    vol_profile: pd.DataFrame
    shares_outstanding: float = None   # best-effort; None if unavailable (see fetch_market_data)

def _raise_friendly(exc, ticker):
    msg = str(exc)
    if "429" in msg or "Too Many Requests" in msg or "rate limit" in msg.lower():
        raise RuntimeError(
            f"Yahoo Finance is temporarily rate-limiting requests for '{ticker}'. "
            "Please wait 30 seconds and try again."
        )
    raise RuntimeError(f"Failed to fetch data for '{ticker}': {msg}")

def build_ticker(base, market):
    suffix = MARKET_INFO[market]["suffix"]
    base = base.strip().upper()
    if not base.endswith(suffix):
        return base + suffix
    return base

def fetch_market_data(ticker_base, market, log=None):
    def _log(msg):
        if log:
            log(msg)

    ticker = build_ticker(ticker_base, market)
    _log(f"Fetching data for **{ticker}** ({market})...")
    stock = yf.Ticker(ticker)

    # Intraday 5-min bars
    try:
        intraday = stock.history(period="5d", interval="5m")
    except Exception as e:
        _raise_friendly(e, ticker)

    if intraday.empty:
        raise ValueError(
            f"No intraday data returned for '{ticker}'. "
            "Check the ticker symbol and market selection."
        )
    intraday = intraday[["Open", "High", "Low", "Close", "Volume"]].copy()
    intraday.index = pd.to_datetime(intraday.index)
    _log(f"Intraday: {len(intraday)} bars across {intraday.index.normalize().nunique()} days")

    time.sleep(0.3)  # burst-rate protection

    # Daily bars (60 days for ADV)
    try:
        daily = stock.history(period="60d", interval="1d")
    except Exception as e:
        _raise_friendly(e, ticker)

    if daily.empty:
        raise ValueError(f"No daily data returned for '{ticker}'.")
    daily = daily[["Open", "High", "Low", "Close", "Volume"]].copy()
    _log(f"Daily: {len(daily)} trading days")

    # ADV
    adv_shares = float(daily["Volume"].mean())
    current_price = float(daily["Close"].iloc[-1])
    adv_usd = adv_shares * current_price
    _log(f"ADV: {adv_shares:,.0f} shares (~${adv_usd / 1e6:.1f}M notional)")

    # Realized volatility (annualized)
    intraday["returns"] = intraday["Close"].pct_change()
    bars_per_day = MARKET_INFO[market]["bars"]
    realized_vol_ann = float(intraday["returns"].std() * np.sqrt(bars_per_day * 252))
    _log(f"Realized vol (annualized): {realized_vol_ann:.1%}")

    # Intraday volume profile
    intraday["time_str"] = intraday.index.strftime("%H:%M")
    vol_profile = (
        intraday.groupby("time_str")["Volume"]
        .mean()
        .reset_index()
        .rename(columns={"time_str": "time", "Volume": "avg_volume"})
    )
    vol_profile["volume_pct"] = vol_profile["avg_volume"] / vol_profile["avg_volume"].sum()
    _log(f"Volume profile: {len(vol_profile)} time buckets")

    # Shares outstanding -- best-effort only. Used by Agent 9's Almgren et al.
    # (2005) turnover liquidity factor; NOT required for anything else in the
    # pipeline, so failure here must never block the fetch. `.info` is a
    # heavier/slower call than `.history()` and more prone to rate-limiting,
    # so this is wrapped in its own try/except and simply left as None (Agent
    # 9 already handles None by omitting the liquidity factor) rather than
    # retried or raised.
    shares_outstanding = None
    try:
        info = stock.info
        shares_outstanding = info.get("sharesOutstanding")
        if shares_outstanding:
            _log(f"Shares outstanding: {shares_outstanding:,.0f}")
    except Exception as e:
        _log(f"Shares outstanding unavailable (non-blocking): {e}")

    _log("Agent 1 complete.")

    return MarketData(
        ticker=ticker,
        market=market,
        intraday=intraday,
        daily=daily,
        adv_shares=adv_shares,
        adv_usd=adv_usd,
        current_price=current_price,
        realized_vol_ann=realized_vol_ann,
        vol_profile=vol_profile,
        shares_outstanding=shares_outstanding,
    )
