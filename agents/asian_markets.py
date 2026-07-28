"""
Asian-market execution specifics (see docs/MICROSTRUCTURE_RESEARCH_IMPROVEMENTS.md).

Two features a desk trading Asia must price and that US-centric tools miss:

  * Daily PRICE LIMITS — statutory bands (China ±10%, Korea ±30%, Taiwan ±10%,
    Vietnam ±7%, Thailand ±30%, Indonesia stylised ±25%). A limit-up/down
    "locked" market caps fills; a limit order set beyond the band can never
    execute. `price_limit_flag()` warns pre-trade.
  * CLOSING-AUCTION concentration — closing auctions can be ~20% of daily volume
    (larger in passive-heavy names); Asia has grown its closing/opening call
    auctions (HK CAS 2016; China call auctions). `closing_auction_concentration()`
    measures how much of the day prints in the closing window — where a large
    Asian order often should sit.

Bands are the published statutory rates (stylised, not a live exchange rule
engine); the auction proxy is the historical volume curve's closing window.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

# Daily price-limit band (% up/down from the prior reference). None = no daily
# limit (or per-stock/variable rules we don't stylise). Keyed by MARKET_INFO name.
PRICE_LIMIT_PCT: dict[str, float | None] = {
    "China-A Shanghai": 10.0,     # main board ±10% (ST ±5%, STAR/ChiNext ±20%)
    "China-A Shenzhen": 10.0,
    "Korea (KRX)":      30.0,
    "Taiwan (TWSE)":    10.0,
    "Vietnam (HOSE)":   7.0,
    "Thailand (SET)":   30.0,
    "Indonesia (IDX)":  25.0,      # tiered auto-rejection, stylised
    "Japan (TSE)":      None,      # variable yen-denominated bands (not a flat %)
    "India (NSE)":      None,      # per-security circuit filters + index breakers
    "US":               None,
    "UK (LSE)":         None,
    "Hong Kong (HKEX)": None,      # no continuous limit (CAS has a ±ref band)
    "Australia (ASX)":  None,
    "Singapore (SGX)":  None,
    "Malaysia (KLSE)":  30.0,     # static ±30% (8g correction)
}

# closing-window = last this fraction of the session's bars (the MOC/auction zone)
CLOSE_WINDOW_FRAC = 0.10
AUCTION_CONCENTRATION_WARN = 15.0   # % of daily volume in the closing window


def price_limit_pct(market: str) -> float | None:
    return PRICE_LIMIT_PCT.get(market, None)


def price_limit_flag(market: str, limit_price: float | None, last_price: float | None,
                     side: str = "Buy") -> dict:
    """Pre-trade price-limit check. Returns a finding dict; `severity` is None
    when there is nothing to flag."""
    band = price_limit_pct(market)
    if band is None or not last_price or last_price <= 0:
        return {"severity": None, "band_pct": band, "message": ""}
    up = last_price * (1 + band / 100.0)
    down = last_price * (1 - band / 100.0)
    msg_band = (f"{market} has a daily price limit of ±{band:g}% "
                f"(band ~{down:.2f} … {up:.2f} vs last {last_price:.2f}).")

    # a limit order set beyond the band can never fill
    if limit_price is not None:
        if side == "Buy" and limit_price > up:
            return {"severity": "BLOCK", "band_pct": band,
                    "message": f"Buy limit {limit_price:g} is above the upper price limit "
                               f"{up:.2f} — it can never execute today. {msg_band}"}
        if side == "Sell" and limit_price < down:
            return {"severity": "BLOCK", "band_pct": band,
                    "message": f"Sell limit {limit_price:g} is below the lower price limit "
                               f"{down:.2f} — it can never execute today. {msg_band}"}
        # near-the-band warning (within 10% of the band width of the limit)
        near_up = side == "Buy" and limit_price > last_price and (up - limit_price) / (up - last_price + 1e-9) < 0.1
        near_dn = side == "Sell" and limit_price < last_price and (limit_price - down) / (last_price - down + 1e-9) < 0.1
        if near_up or near_dn:
            return {"severity": "WARN", "band_pct": band,
                    "message": f"Limit {limit_price:g} sits very close to the daily price "
                               f"limit — completion risk if the market locks limit-{'up' if side=='Buy' else 'down'}. {msg_band}"}
    return {"severity": "INFO", "band_pct": band,
            "message": msg_band + " Size into the band raises the risk of a locked "
                       "(limit-up/down) market that halts fills."}


def closing_auction_concentration(intraday: pd.DataFrame,
                                  close_window_frac: float = CLOSE_WINDOW_FRAC) -> dict:
    """Average share of daily volume printing in the closing window (last
    `close_window_frac` of each session's bars) — the closing-auction proxy."""
    if "Volume" not in intraday.columns or len(intraday) == 0:
        return {"close_share_pct": None, "concentrated": None, "note": "No volume data."}
    df = intraday.copy()
    df["_date"] = df.index.normalize()
    shares = []
    for _, day in df.groupby("_date"):
        n = len(day)
        tv = float(day["Volume"].sum())
        if n < 3 or tv <= 0:
            continue
        w = max(1, int(round(n * close_window_frac)))
        shares.append(float(day["Volume"].iloc[-w:].sum()) / tv)
    if not shares:
        return {"close_share_pct": None, "concentrated": None, "note": "Insufficient history."}
    share_pct = float(np.mean(shares) * 100)
    return {"close_share_pct": round(share_pct, 1),
            "concentrated": bool(share_pct > AUCTION_CONCENTRATION_WARN),
            "n_days": len(shares),
            "note": ("High closing-auction concentration — a large order can often "
                     "source size in the close with less continuous-session impact."
                     if share_pct > AUCTION_CONCENTRATION_WARN else "")}
