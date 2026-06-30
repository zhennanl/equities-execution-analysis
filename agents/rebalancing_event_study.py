"""
Index Rebalancing Event Study
Computes Cumulative Abnormal Returns (CAR) and Abnormal Volume around
an index constituent change date using yfinance public data.

Methodology:
  Estimation window : [T-70, T-11] trading days  (~60 obs)
  Event window      : [T-n, T+n] where n = user-specified days
  Market model      : R_stock = alpha + beta * R_index  (OLS on estimation window)
  AR_t              : R_stock_t - (alpha + beta * R_index_t)
  CAR               : cumsum(AR)
  Abnormal Volume   : Volume_t / mean(Volume in estimation window)
"""

import time
import numpy as np
import pandas as pd
import yfinance as yf
from dataclasses import dataclass
from agents.agent1_market_data import build_ticker

INDEX_PROXIES = {
    # Taiwan
    "MSCI Taiwan / TAIEX":      "^TWII",
    # Hong Kong
    "Hang Seng Index":          "^HSI",
    "Hang Seng China Ent.":     "^HSCE",
    # Japan
    "Nikkei 225":               "^N225",
    "TOPIX":                    "^N300",
    # Korea
    "KOSPI / KOSPI 200":        "^KS11",
    # Singapore
    "Straits Times Index":      "^STI",
    # China-A
    "Shanghai Composite":       "000001.SS",
    "Shenzhen Component":       "399001.SZ",
    "CSI 300":                  "000300.SS",
    # India
    "NIFTY 50":                 "^NSEI",
    "BSE SENSEX":               "^BSESN",
    # Australia
    "S&P/ASX 200":              "^AXJO",
    # Thailand
    "SET Index":                "^SET.BK",
    # Indonesia
    "IDX Composite":            "^JKSE",
    # Malaysia
    "FTSE Bursa Malaysia KLCI": "^KLSE",
    # Vietnam (no direct yfinance proxy; use US-listed ETF as rough benchmark)
    "VanEck Vietnam ETF (VNM)": "VNM",
    # US benchmarks (for US-listed stocks)
    "S&P 500":                  "^GSPC",
    "NASDAQ 100":               "^NDX",
}


@dataclass
class EventStudyResult:
    ticker: str
    index_name: str
    T: pd.Timestamp                  # effective rebalancing date (nearest trading day)
    rel_days: np.ndarray             # relative day index (-n … +n)
    car: np.ndarray                  # cumulative abnormal return (decimal)
    ar: np.ndarray                   # per-day abnormal return
    ab_vol: np.ndarray               # abnormal volume ratio
    norm_price: np.ndarray           # price indexed to 100 at T
    alpha: float
    beta: float
    summary: pd.DataFrame            # CAR at key days: -5, -1, 0, +1, +5, +n


def run_event_study(ticker_base: str, market: str, rebal_date,
                    event_window: int, index_name: str, log=None) -> EventStudyResult:
    """
    Parameters
    ----------
    ticker_base   : raw ticker (e.g. "2330")
    market        : market key
    rebal_date    : datetime.date — index effective rebalancing date
    event_window  : days on each side of T (e.g. 10 → T-10 to T+10)
    index_name    : one of INDEX_PROXIES keys
    """
    def _log(msg):
        if log: log(msg)

    ticker       = build_ticker(ticker_base, market)
    index_ticker = INDEX_PROXIES.get(index_name, "^TWII")

    # Fetch a wide window: T-120 calendar days to T+40 calendar days
    T_cal    = pd.Timestamp(rebal_date)
    start    = (T_cal - pd.Timedelta(days=120)).strftime("%Y-%m-%d")
    end      = (T_cal + pd.Timedelta(days=40)).strftime("%Y-%m-%d")

    _log(f"Fetching {ticker} and {index_ticker} from {start} to {end}...")

    stock_raw = yf.Ticker(ticker).history(start=start, end=end)
    time.sleep(0.3)
    index_raw = yf.Ticker(index_ticker).history(start=start, end=end)

    if stock_raw.empty:
        raise ValueError(f"No data returned for '{ticker}'. Check ticker and market.")
    if index_raw.empty:
        raise ValueError(f"No data returned for index proxy '{index_ticker}'.")

    # Align on common trading dates
    stock_close  = stock_raw["Close"].rename("stock")
    stock_vol    = stock_raw["Volume"]
    index_close  = index_raw["Close"].rename("index")

    # Normalize index to strip timezone for join
    stock_close.index = pd.to_datetime([d.date() for d in stock_close.index])
    stock_vol.index   = pd.to_datetime([d.date() for d in stock_vol.index])
    index_close.index = pd.to_datetime([d.date() for d in index_close.index])

    combined = pd.concat([stock_close, index_close], axis=1).dropna()
    if len(combined) < 30:
        raise ValueError("Insufficient overlapping trading data. Check ticker and date.")

    # Find nearest trading day T
    avail = combined.index[combined.index <= T_cal]
    if len(avail) == 0:
        raise ValueError("Rebalancing date precedes all available data.")
    T_trading = avail[-1]
    T_idx     = combined.index.get_loc(T_trading)
    _log(f"T (nearest trading day): {T_trading.date()}, index position {T_idx}")

    # Window bounds (in trading-day index)
    est_start  = max(0, T_idx - 70)
    est_end    = max(0, T_idx - 10)
    ev_start   = max(0, T_idx - event_window)
    ev_end     = min(len(combined), T_idx + event_window + 1)

    if est_end - est_start < 20:
        raise ValueError(
            "Fewer than 20 trading days in estimation window. "
            "Choose an earlier rebalancing date or fetch more history."
        )

    estimation = combined.iloc[est_start:est_end]
    event      = combined.iloc[ev_start:ev_end]

    # OLS: R_stock = alpha + beta * R_index
    stock_ret_est = estimation["stock"].pct_change().dropna()
    index_ret_est = estimation["index"].pct_change().dropna()
    common_est    = pd.concat([stock_ret_est, index_ret_est], axis=1).dropna()

    X = np.column_stack([np.ones(len(common_est)), common_est["index"].values])
    y = common_est["stock"].values
    coeffs, _, _, _ = np.linalg.lstsq(X, y, rcond=None)
    alpha, beta = coeffs
    _log(f"Market model: alpha={alpha:.5f}, beta={beta:.3f}")

    # Abnormal returns in event window
    stock_ret_ev = event["stock"].pct_change().fillna(0)
    index_ret_ev = event["index"].pct_change().fillna(0)
    AR  = stock_ret_ev.values - (alpha + beta * index_ret_ev.values)
    CAR = np.cumsum(AR)

    # Relative day index (T = 0)
    rel_days = np.arange(ev_start - T_idx, ev_end - T_idx)

    # Abnormal volume
    est_vol   = stock_vol.reindex(estimation.index).fillna(0)
    avg_vol   = est_vol.mean()
    ev_vol    = stock_vol.reindex(event.index).fillna(0)
    ab_vol    = (ev_vol / avg_vol).values if avg_vol > 0 else np.ones(len(event))

    # Normalized price (T=0 → 100)
    _close_tz = stock_raw["Close"].copy()
    _close_tz.index = pd.to_datetime([d.date() for d in _close_tz.index])
    ev_price  = _close_tz.reindex(event.index).ffill()
    T_price   = float(ev_price.reindex([T_trading]).iloc[0]) if T_trading in ev_price.index else float(ev_price.iloc[0])
    norm_price = (ev_price / T_price * 100).values if T_price > 0 else np.full(len(event), 100.0)

    # Summary table at key days
    key_days = [-event_window, -5, -1, 0, 1, 5, event_window]
    key_days = sorted(set(d for d in key_days if ev_start - T_idx <= d <= ev_end - T_idx - 1))
    summary_rows = []
    for d in key_days:
        pos = d - (ev_start - T_idx)
        if 0 <= pos < len(CAR):
            summary_rows.append({
                "Day": f"T{d:+d}",
                "CAR (%)": round(CAR[pos] * 100, 2),
                "Ab. Volume (×)": round(float(ab_vol[pos]), 2) if pos < len(ab_vol) else None,
                "Price (idx)": round(float(norm_price[pos]), 1) if pos < len(norm_price) else None,
            })
    summary = pd.DataFrame(summary_rows).set_index("Day")

    _log(f"CAR at T+0: {CAR[T_idx - ev_start]*100:.2f}%")
    _log("Event study complete.")

    return EventStudyResult(
        ticker=ticker,
        index_name=index_name,
        T=T_trading,
        rel_days=rel_days,
        car=CAR,
        ar=AR,
        ab_vol=ab_vol,
        norm_price=norm_price,
        alpha=alpha,
        beta=beta,
        summary=summary,
    )
