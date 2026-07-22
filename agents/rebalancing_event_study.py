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

Execution-cost extensions (all built on the CAR/volume outputs above, plus one
optional intraday fetch — no paid data required; see each function's docstring
for what it approximates and its limitations):
  1. Closing auction concentration  — analyze_closing_concentration()
  2. Post-event reversal            — compute_reversal()
  3. Pre-announcement vs pre-effective drift decomposition — compute_drift_decomposition()
  4. Flow-to-trade estimator        — estimate_flow_to_trade()
  5. Event-day impact (eta) calibration — calibrate_event_day_eta()
  6. Basket/crowding caveat          — basket_crowding_note()
  7. Objective-aware recommendation — recommend_rebalance_execution()
  build_execution_insights() ties 1-7 together for a single call from the UI.
"""

import time
import numpy as np
import pandas as pd
import yfinance as yf
from dataclasses import dataclass
from agents.agent1_market_data import build_ticker, MARKET_INFO
from agents.agent3_algo_simulation import IMPACT_ETA

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
    # UK
    "FTSE 100":                 "^FTSE",
    "FTSE 250":                 "^FTMC",
    # US benchmarks (for US-listed stocks)
    "S&P 500":                  "^GSPC",
    "NASDAQ 100":               "^NDX",
}

# Reversal classification thresholds (fraction of pre-event run-up given back)
MIN_RUNUP_PCT               = 0.10   # below this, run-up is too small to classify reversal
REVERSAL_TRANSIENT_THRESH   = 0.50
REVERSAL_PARTIAL_THRESH     = 0.15
REVERSAL_MOMENTUM_THRESH    = -0.15

# yfinance retains ~60 days of 5-min intraday history
INTRADAY_LOOKBACK_CAP_DAYS = 59


@dataclass
class EventStudyResult:
    ticker: str
    index_name: str
    T: pd.Timestamp                  # effective rebalancing date (nearest trading day)
    rel_days: np.ndarray             # relative day index (-n ... +n)
    car: np.ndarray                  # cumulative abnormal return (decimal)
    ar: np.ndarray                   # per-day abnormal return
    ab_vol: np.ndarray               # abnormal volume ratio
    norm_price: np.ndarray           # price indexed to 100 at T
    alpha: float
    beta: float
    summary: pd.DataFrame            # CAR at key days: -5, -1, 0, +1, +5, +n
    event_dates: np.ndarray          # trading-day timestamps aligned to rel_days/car/ar/ab_vol
    price_at_T: float                # raw (non-indexed) close price at T
    est_sigma_daily: float           # daily return std-dev over the estimation window
    est_avg_volume: float            # mean daily volume over the estimation window (ADV proxy)
    ar_tstat: np.ndarray = None      # per-day AR t-stats (Brown-Warner single-firm, forecast-error corrected)
    car_sigma: np.ndarray = None     # cumulative CAR standard error per event day
    liquidity_shift: "LiquidityShift" = None   # pre vs post-event beta/spread/illiquidity


def event_inference(AR: np.ndarray, resid: np.ndarray,
                    index_ret_est: np.ndarray, index_ret_ev: np.ndarray):
    """Single-firm event-study inference (Brown-Warner 1985 / Patell-style
    forecast-error correction, one firm so no cross-sectional aggregation):

      var(AR_t) = s^2 * ( 1 + 1/L + (Rm_t - Rm_bar)^2 / SSRm )

    where s^2 is the estimation-window residual variance (ddof=2), L the
    estimation length, Rm_bar / SSRm the estimation-window market-return mean
    and centered sum of squares. CAR sigma is the sqrt of the running sum of
    var(AR_t) (residuals assumed serially uncorrelated — the market model's
    own assumption). Returns (ar_tstat, car_sigma), both event-window arrays.
    Event-induced variance (BMP critique) makes these ANTI-conservative on
    the event days themselves — display bands, don't hard-test."""
    L = len(resid)
    if L < 10:
        return None, None
    s2 = float(np.sum(resid ** 2) / (L - 2))
    rm_bar = float(np.mean(index_ret_est))
    ssrm = float(np.sum((index_ret_est - rm_bar) ** 2))
    if s2 <= 0 or ssrm <= 0:
        return None, None
    var_t = s2 * (1.0 + 1.0 / L + (index_ret_ev - rm_bar) ** 2 / ssrm)
    ar_t = AR / np.sqrt(var_t)
    car_sigma = np.sqrt(np.cumsum(var_t))
    return ar_t, car_sigma


@dataclass
class LiquidityShift:
    """Pre vs post-event liquidity & systematic-risk shift (research memo
    stream H: Hegde-McDermott 2003 liquidity; Barberis-Shleifer-Wurgler 2005
    comovement). Pre = estimation window; post = T+1 onward (needs >= 8 days)."""
    available: bool
    reason: str = ""
    beta_pre: float = None
    beta_post: float = None
    edge_pre_bps: float = None
    edge_post_bps: float = None
    amihud_pre: float = None          # bps impact per $1M notional
    amihud_post: float = None
    n_post_days: int = 0
    note: str = ""


def compute_liquidity_shift(stock_raw: pd.DataFrame, combined: pd.DataFrame,
                            est_start: int, est_end: int, T_idx: int,
                            alpha: float, beta: float) -> LiquidityShift:
    """stock_raw: raw daily OHLCV (naive dates); combined: aligned stock/index
    closes used by the study; windows are combined-frame positions."""
    from agents.microstructure_analytics import estimate_spread_edge, amihud_illiquidity
    post = combined.iloc[T_idx + 1:]
    n_post = len(post)
    if n_post < 8:
        return LiquidityShift(False, f"Only {n_post} post-event days (need >= 8) — rerun later.")
    sr = post["stock"].pct_change().dropna()
    ir = post["index"].pct_change().dropna()
    both = pd.concat([sr, ir], axis=1).dropna()
    if len(both) < 6:
        return LiquidityShift(False, "Too few overlapping post-event returns.")
    X = np.column_stack([np.ones(len(both)), both["index"].values])
    beta_post = float(np.linalg.lstsq(X, both["stock"].values, rcond=None)[0][1])

    est_dates = combined.index[est_start:est_end]
    post_dates = post.index
    pre_ohlc = stock_raw.loc[stock_raw.index.isin(est_dates)]
    post_ohlc = stock_raw.loc[stock_raw.index.isin(post_dates)]

    e_pre = estimate_spread_edge(pre_ohlc)
    e_post = estimate_spread_edge(post_ohlc)
    a_pre = amihud_illiquidity(pre_ohlc)
    a_post = amihud_illiquidity(post_ohlc)

    bits = [f"beta {beta:.2f} -> {beta_post:.2f} ({n_post} post days)"]
    if e_pre.get("spread_bps") and e_post.get("spread_bps"):
        bits.append(f"EDGE spread {e_pre['spread_bps']:.1f} -> {e_post['spread_bps']:.1f} bps")
    if a_pre.get("impact_bps_per_1m") is not None and a_post.get("impact_bps_per_1m") is not None:
        bits.append(f"Amihud {a_pre['impact_bps_per_1m']:.2f} -> {a_post['impact_bps_per_1m']:.2f} bps/$1M")
    note = ("Post-event window is short and overlaps the reversal — read as an early "
            "indication, not a settled regime. Practical uses: update hedge ratios off "
            "the post beta; falling spread/illiquidity makes post-effective completion "
            "cheaper than pre-event estimates assumed. " + " · ".join(bits))
    return LiquidityShift(
        available=True, beta_pre=round(float(beta), 3), beta_post=round(beta_post, 3),
        edge_pre_bps=e_pre.get("spread_bps"), edge_post_bps=e_post.get("spread_bps"),
        amihud_pre=a_pre.get("impact_bps_per_1m"), amihud_post=a_post.get("impact_bps_per_1m"),
        n_post_days=n_post, note=note)


def run_event_study(ticker_base: str, market: str, rebal_date,
                    event_window: int, index_name: str, log=None) -> EventStudyResult:
    """
    Parameters
    ----------
    ticker_base   : raw ticker (e.g. "2330")
    market        : market key
    rebal_date    : datetime.date -- index effective rebalancing date
    event_window  : days on each side of T (e.g. 10 -> T-10 to T+10)
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

    # Abnormal returns in event window. Returns are computed with one extra
    # leading trading day so the first event-window day gets a REAL return --
    # a bare pct_change().fillna(0) would set day-1 returns to zero and inject
    # a spurious AR of -alpha (which then shifts the entire CAR curve).
    ext_start = max(0, ev_start - 1)
    event_ext = combined.iloc[ext_start:ev_end]
    stock_ret_ev = event_ext["stock"].pct_change()
    index_ret_ev = event_ext["index"].pct_change()
    if ext_start < ev_start:            # drop the leading helper day
        stock_ret_ev = stock_ret_ev.iloc[1:]
        index_ret_ev = index_ret_ev.iloc[1:]
    stock_ret_ev = stock_ret_ev.fillna(0)
    index_ret_ev = index_ret_ev.fillna(0)
    AR  = stock_ret_ev.values - (alpha + beta * index_ret_ev.values)
    if ext_start == ev_start:           # no earlier data: neutralize day 1
        AR[0] = 0.0
    CAR = np.cumsum(AR)

    # Relative day index (T = 0)
    rel_days = np.arange(ev_start - T_idx, ev_end - T_idx)

    # Abnormal volume
    est_vol   = stock_vol.reindex(estimation.index).fillna(0)
    avg_vol   = est_vol.mean()
    ev_vol    = stock_vol.reindex(event.index).fillna(0)
    ab_vol    = (ev_vol / avg_vol).values if avg_vol > 0 else np.ones(len(event))

    # Normalized price (T=0 -> 100)
    _close_tz = stock_raw["Close"].copy()
    _close_tz.index = pd.to_datetime([d.date() for d in _close_tz.index])
    ev_price  = _close_tz.reindex(event.index).ffill()
    T_price   = float(ev_price.reindex([T_trading]).iloc[0]) if T_trading in ev_price.index else float(ev_price.iloc[0])
    norm_price = (ev_price / T_price * 100).values if T_price > 0 else np.full(len(event), 100.0)

    # Inference: estimation-window residuals -> AR t-stats + CAR sigma bands
    resid = common_est["stock"].values - (alpha + beta * common_est["index"].values)
    ar_tstat, car_sigma = event_inference(AR, resid,
                                          common_est["index"].values,
                                          index_ret_ev.values)

    _close_for_shift = stock_raw.copy()
    _close_for_shift.index = pd.to_datetime([d.date() for d in _close_for_shift.index])
    liq_shift = compute_liquidity_shift(_close_for_shift, combined,
                                        est_start, est_end, T_idx, alpha, beta)

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
                "CAR t": round(float(CAR[pos] / car_sigma[pos]), 2)
                          if car_sigma is not None and car_sigma[pos] > 0 else None,
                "Ab. Volume (x)": round(float(ab_vol[pos]), 2) if pos < len(ab_vol) else None,
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
        event_dates=event.index.values,
        price_at_T=float(T_price),
        est_sigma_daily=float(stock_ret_est.std()),
        est_avg_volume=float(avg_vol),
        ar_tstat=ar_tstat,
        car_sigma=car_sigma,
        liquidity_shift=liq_shift,
    )


# ==============================================================================
# Execution-cost extensions
# ==============================================================================

# -- 1. Closing auction concentration -----------------------------------------

@dataclass
class ClosingConcentration:
    available: bool
    reason: str = ""
    t_last_window_pct: float = None          # % of T's daily volume in the final ~5% of bars
    baseline_last_window_pct: float = None    # same metric averaged over comparison days
    concentration_multiple_window: float = None
    t_last_bar_pct: float = None              # % of T's daily volume in the single final bar
    baseline_last_bar_pct: float = None
    concentration_multiple_bar: float = None
    n_baseline_days: int = None


def analyze_closing_concentration(ticker: str, T_trading: pd.Timestamp, bars_expected: int,
                                  log=None) -> ClosingConcentration:
    """
    Measures how much of T's daily volume is concentrated into the final bars of
    the session (approximating closing-auction participation) versus a baseline
    of nearby non-event trading days. Real reconstitution days have shown 10-75x
    normal closing-window volume in US markets -- this tells you, for this name,
    how much size the close realistically absorbed.

    Limitation: yfinance only retains ~60 days of 5-min intraday history, so this
    is only computable for rebalancing dates within roughly the last two months.
    """
    def _log(msg):
        if log: log(msg)

    today  = pd.Timestamp.now().normalize()
    cutoff = today - pd.Timedelta(days=INTRADAY_LOOKBACK_CAP_DAYS)
    if T_trading < cutoff:
        return ClosingConcentration(
            available=False,
            reason=(f"yfinance only retains ~{INTRADAY_LOOKBACK_CAP_DAYS} days of 5-min intraday "
                    f"history; T ({T_trading.date()}) is outside that window. Closing-auction "
                    f"concentration can only be measured for recent rebalancing dates."),
        )

    start = max(cutoff, T_trading - pd.Timedelta(days=20)).strftime("%Y-%m-%d")
    end   = (T_trading + pd.Timedelta(days=2)).strftime("%Y-%m-%d")
    _log(f"Fetching 5-min intraday for {ticker} from {start} to {end}...")
    try:
        intraday = yf.Ticker(ticker).history(start=start, end=end, interval="5m")
    except Exception as e:
        return ClosingConcentration(available=False, reason=f"Intraday fetch failed: {e}")

    if intraday.empty:
        return ClosingConcentration(available=False, reason="No intraday data returned for this window.")

    dates = pd.to_datetime([d.date() for d in intraday.index])
    intraday = intraday.copy()
    intraday["_date"] = dates

    last_window_n = max(1, int(round(bars_expected * 0.05)))  # ~last 5% of the session
    min_bars       = max(5, int(bars_expected * 0.3))          # skip holiday-truncated sessions

    rows = []
    for d, day_df in intraday.groupby("_date"):
        day_df = day_df.sort_index()
        total_vol = day_df["Volume"].sum()
        if total_vol <= 0 or len(day_df) < min_bars:
            continue
        last_window_vol = day_df["Volume"].iloc[-last_window_n:].sum()
        last_bar_vol     = day_df["Volume"].iloc[-1:].sum()
        rows.append({
            "date": d,
            "last_window_pct": last_window_vol / total_vol,
            "last_bar_pct":    last_bar_vol / total_vol,
        })

    if not rows:
        return ClosingConcentration(available=False, reason="No complete trading sessions found in the fetched intraday window.")

    day_stats = pd.DataFrame(rows).set_index("date")
    T_date = pd.Timestamp(T_trading.date())
    if T_date not in day_stats.index:
        return ClosingConcentration(
            available=False,
            reason=f"Intraday session for T ({T_trading.date()}) was not returned by yfinance (holiday/listing gap?).",
        )

    baseline = day_stats.drop(index=T_date, errors="ignore")
    if len(baseline) == 0:
        return ClosingConcentration(available=False, reason="No non-event comparison days available in the fetched intraday window.")

    t_row = day_stats.loc[T_date]
    baseline_last_window_pct = float(baseline["last_window_pct"].mean())
    baseline_last_bar_pct    = float(baseline["last_bar_pct"].mean())
    t_last_window_pct = float(t_row["last_window_pct"])
    t_last_bar_pct    = float(t_row["last_bar_pct"])

    conc_mult_window = (t_last_window_pct / baseline_last_window_pct) if baseline_last_window_pct > 0 else None
    conc_mult_bar    = (t_last_bar_pct / baseline_last_bar_pct) if baseline_last_bar_pct > 0 else None

    return ClosingConcentration(
        available=True,
        t_last_window_pct=round(t_last_window_pct * 100, 1),
        baseline_last_window_pct=round(baseline_last_window_pct * 100, 1),
        concentration_multiple_window=round(conc_mult_window, 1) if conc_mult_window is not None else None,
        t_last_bar_pct=round(t_last_bar_pct * 100, 1),
        baseline_last_bar_pct=round(baseline_last_bar_pct * 100, 1),
        concentration_multiple_bar=round(conc_mult_bar, 1) if conc_mult_bar is not None else None,
        n_baseline_days=len(baseline),
    )


# -- 2. Post-event reversal ----------------------------------------------------

@dataclass
class ReversalMetrics:
    available: bool
    reason: str = ""
    pre_event_runup_pct: float = None        # CAR from T-k to T (k = min(5, event_window))
    post_event_move_5d_pct: float = None      # CAR from T to T+k
    reversal_fraction_5d: float = None        # fraction of run-up given back within 5 days
    post_event_move_full_pct: float = None    # CAR from T to T+event_window
    reversal_fraction_full: float = None
    classification: str = ""


def compute_reversal(car: np.ndarray, rel_days: np.ndarray) -> ReversalMetrics:
    """
    Compares the pre-event run-up (T-k to T) against the post-event move (T to
    T+k). A large positive reversal fraction (price gives back most of the
    run-up) indicates transient, liquidity-driven price pressure -- favorable
    for a cost-minimizing trader to wait out. Little or no reversal indicates a
    permanent re-rating, where waiting doesn't help.
    """
    if len(rel_days) == 0:
        return ReversalMetrics(available=False, reason="Empty event window.")

    event_window = int(rel_days.max())

    def pos(day):
        idx = np.where(rel_days == day)[0]
        return int(idx[0]) if len(idx) else None

    p0 = pos(0)
    if p0 is None:
        return ReversalMetrics(available=False, reason="T (day 0) not found in event window.")

    k5 = min(5, event_window) if event_window > 0 else 0
    p_minus_k5  = pos(-k5) if k5 > 0 else p0
    p_plus_k5   = pos(k5) if k5 > 0 else p0
    p_plus_full = pos(event_window) if event_window > 0 else p0

    car0 = car[p0]
    pre_event_runup_pct = (car0 - car[p_minus_k5]) * 100 if p_minus_k5 is not None else None
    post_event_5d_pct   = (car[p_plus_k5] - car0) * 100 if p_plus_k5 is not None else None
    post_event_full_pct = (car[p_plus_full] - car0) * 100 if p_plus_full is not None else None

    reversal_fraction_5d = None
    reversal_fraction_full = None
    if pre_event_runup_pct is not None and abs(pre_event_runup_pct) >= MIN_RUNUP_PCT:
        if post_event_5d_pct is not None:
            reversal_fraction_5d = -post_event_5d_pct / pre_event_runup_pct
        if post_event_full_pct is not None:
            reversal_fraction_full = -post_event_full_pct / pre_event_runup_pct

    if pre_event_runup_pct is None or abs(pre_event_runup_pct) < MIN_RUNUP_PCT:
        classification = "Indeterminate -- minimal pre-event move to test for reversal"
    elif reversal_fraction_5d is None:
        classification = "Indeterminate"
    elif reversal_fraction_5d >= REVERSAL_TRANSIENT_THRESH:
        classification = "Transient -- mostly reverses"
    elif reversal_fraction_5d >= REVERSAL_PARTIAL_THRESH:
        classification = "Partial reversal"
    elif reversal_fraction_5d > REVERSAL_MOMENTUM_THRESH:
        classification = "Permanent -- limited reversal"
    else:
        classification = "Momentum continuation"

    return ReversalMetrics(
        available=True,
        pre_event_runup_pct=round(pre_event_runup_pct, 2) if pre_event_runup_pct is not None else None,
        post_event_move_5d_pct=round(post_event_5d_pct, 2) if post_event_5d_pct is not None else None,
        reversal_fraction_5d=round(reversal_fraction_5d, 3) if reversal_fraction_5d is not None else None,
        post_event_move_full_pct=round(post_event_full_pct, 2) if post_event_full_pct is not None else None,
        reversal_fraction_full=round(reversal_fraction_full, 3) if reversal_fraction_full is not None else None,
        classification=classification,
    )


# -- 3. Pre-announcement vs pre-effective drift decomposition -----------------

@dataclass
class DriftDecomposition:
    available: bool
    reason: str = ""
    pre_announcement_car_pct: float = None
    announcement_to_effective_car_pct: float = None
    pct_of_pre_event_move_after_announcement: float = None


def compute_drift_decomposition(car: np.ndarray, event_dates: np.ndarray,
                                T_trading: pd.Timestamp, announcement_date) -> DriftDecomposition:
    """
    Splits the pre-effective drift into a pre-announcement window (should be
    ~flat -- the market doesn't yet know) and an announcement-to-effective
    window (anticipatory arbitrage/front-running drift). A high
    pct_of_pre_event_move_after_announcement confirms the run-up is compressed
    into the days right before T -- evidence for trading ahead of the crowd
    rather than waiting, if a cost-minimizing strategy is chosen.
    """
    if announcement_date is None:
        return DriftDecomposition(available=False, reason="No announcement date supplied.")

    ev_dates = pd.DatetimeIndex(event_dates)
    if len(ev_dates) == 0:
        return DriftDecomposition(available=False, reason="Empty event window.")

    ann_ts = pd.Timestamp(announcement_date)
    if ann_ts < ev_dates[0]:
        return DriftDecomposition(
            available=False,
            reason="Announcement date falls before the start of the event window -- widen the event window to include it.",
        )
    if ann_ts >= T_trading:
        return DriftDecomposition(available=False, reason="Announcement date must be before the effective (T) date.")

    if T_trading not in ev_dates:
        return DriftDecomposition(available=False, reason="T not found in event window.")

    pos_ann = int(np.searchsorted(ev_dates.values, ann_ts.to_datetime64(), side="left"))
    pos_T   = int(np.where(ev_dates == T_trading)[0][0])
    if pos_ann >= len(car) or pos_T >= len(car):
        return DriftDecomposition(available=False, reason="Could not locate announcement/T positions within the event window.")

    car0 = car[0]
    pre_announcement_car_pct          = (car[pos_ann] - car0) * 100
    announcement_to_effective_car_pct = (car[pos_T] - car[pos_ann]) * 100
    total_pre_event_car_pct           = pre_announcement_car_pct + announcement_to_effective_car_pct

    pct_after_announcement = None
    if abs(total_pre_event_car_pct) >= MIN_RUNUP_PCT:
        pct_after_announcement = announcement_to_effective_car_pct / total_pre_event_car_pct * 100

    return DriftDecomposition(
        available=True,
        pre_announcement_car_pct=round(pre_announcement_car_pct, 2),
        announcement_to_effective_car_pct=round(announcement_to_effective_car_pct, 2),
        pct_of_pre_event_move_after_announcement=round(pct_after_announcement, 1) if pct_after_announcement is not None else None,
    )


# -- 4. Flow-to-trade estimator ------------------------------------------------

@dataclass
class FlowToTrade:
    notional_usd: float
    shares: float
    flow_pct_adv: float = None


def estimate_flow_to_trade(weight_change_pct: float, tracked_aum_usd: float,
                           stock_price: float, adv_shares: float = None) -> FlowToTrade:
    """
    Estimates the passive shares that must trade from an index weight change:
      notional = tracked_aum_usd * (weight_change_pct / 100)
      shares   = notional / stock_price
    This is the mechanical flow driving price impact -- a materially better-
    grounded order-size input for a rebalance trade than a generic %-of-ADV
    guess, since it's tied to actual passive ownership change rather than the
    stock's regular trading pattern.
    """
    notional = tracked_aum_usd * (weight_change_pct / 100.0)
    shares   = notional / stock_price if stock_price > 0 else 0.0
    flow_pct_adv = (shares / adv_shares * 100.0) if adv_shares and adv_shares > 0 else None
    return FlowToTrade(
        notional_usd=round(notional, 2),
        shares=round(shares, 0),
        flow_pct_adv=round(flow_pct_adv, 2) if flow_pct_adv is not None else None,
    )


# -- 5. Event-day impact (eta) calibration -------------------------------------

@dataclass
class EtaCalibration:
    available: bool
    reason: str = ""
    shock_car_pct: float = None
    implied_eta: float = None
    baseline_eta: float = IMPACT_ETA


def calibrate_event_day_eta(car: np.ndarray, rel_days: np.ndarray, flow_pct_adv,
                            sigma_daily, baseline_eta: float = IMPACT_ETA) -> EtaCalibration:
    """
    Backs out an implied market-impact coefficient (eta in the square-root model
    impact = eta * sigma_daily * sqrt(Q/ADV)) from this single event, using the
    [T-1, T+1] CAR window as the observed price shock and the flow-to-trade
    estimate as Q/ADV. Index inclusion is a classic natural experiment for
    calibrating price-impact models, since the trade is large and exogenous to
    firm fundamentals -- but this is a single-event estimate, not a true
    cross-sectional regression (that would need a library of past events for
    the same index, run one at a time through this tool and aggregated
    separately).
    """
    def pos(day):
        idx = np.where(rel_days == day)[0]
        return int(idx[0]) if len(idx) else None

    p_minus1, p_plus1 = pos(-1), pos(1)
    if p_minus1 is None or p_plus1 is None:
        return EtaCalibration(available=False, reason="Event window doesn't extend to T-1/T+1.", baseline_eta=baseline_eta)
    if flow_pct_adv is None or flow_pct_adv <= 0:
        return EtaCalibration(
            available=False,
            reason="Flow-to-trade not supplied -- enter weight change % and tracked AUM to calibrate.",
            baseline_eta=baseline_eta,
        )
    if not sigma_daily or sigma_daily <= 0:
        return EtaCalibration(available=False, reason="Insufficient estimation-window data to compute daily volatility.", baseline_eta=baseline_eta)

    shock_car = car[p_plus1] - car[p_minus1]
    denom = sigma_daily * np.sqrt(flow_pct_adv / 100.0)
    if denom <= 0:
        return EtaCalibration(available=False, reason="Could not solve for implied eta (zero denominator).", baseline_eta=baseline_eta)

    implied_eta = abs(shock_car) / denom

    return EtaCalibration(
        available=True,
        shock_car_pct=round(shock_car * 100, 2),
        implied_eta=round(float(implied_eta), 2),
        baseline_eta=baseline_eta,
    )


# -- 6. Basket / crowding caveat ------------------------------------------------

def basket_crowding_note(index_name: str) -> str:
    """
    Full reconstitutions move many names at once; every fund tracking the same
    benchmark trades the same basket in the same auction simultaneously. That
    correlated flow can push realized impact above a single-name model's
    prediction. This tool only analyzes one ticker at a time, so treat its
    cost estimates as a per-name floor, not a full accounting of crowding.
    """
    return (
        f"This analysis models {index_name} single-name price/volume impact only. Full index "
        "reconstitutions move dozens of names simultaneously, and every fund tracking the same "
        "benchmark trades the same basket in the same auction at once -- correlated flow that can "
        "push realized impact above what a single-name square-root model implies. Treat the cost "
        "estimates here as a per-name floor, not a full accounting of basket-level crowding."
    )


# -- 7. Objective-aware execution recommendation -------------------------------

@dataclass
class RebalanceRecommendation:
    objective: str
    recommended_algo: str
    rationale: str
    notes: list


def recommend_rebalance_execution(objective: str, concentration: ClosingConcentration,
                                  reversal: ReversalMetrics, drift: DriftDecomposition,
                                  flow: FlowToTrade, eta_calib: EtaCalibration,
                                  crowding_note: str) -> RebalanceRecommendation:
    """
    Rule-based pick between the algorithms already implemented in Agent 3
    (MOC, MOO, TWAP, POV, IS, Liquidity-Seeking, Stealth), conditioned on the
    investor's objective and the measured event characteristics above.
    """
    notes = []

    if objective == "Index Tracker":
        algo = "MOC"
        rationale = (
            "Index-tracking mandates must transact at (or near) the closing print the index itself "
            "uses to reprice, to avoid tracking error versus the benchmark -- Market-on-Close is "
            "effectively the only algorithm consistent with that constraint, regardless of cost."
        )
        if concentration.available and concentration.concentration_multiple_window is not None:
            if concentration.concentration_multiple_window < 3:
                notes.append(
                    f"Closing-window volume concentration on T was only "
                    f"{concentration.concentration_multiple_window:.1f}x the normal-day baseline -- "
                    f"thinner than the 10-75x seen in major reconstitutions. The auction may not "
                    f"absorb size as cleanly as assumed; consider pre-positioning part of the order "
                    f"in T-1/T-2."
                )
        elif not concentration.available:
            notes.append(f"Closing-window concentration could not be measured ({concentration.reason}) "
                        f"-- proceed with standard MOC sizing assumptions.")
    else:  # Cost-Minimizing
        if (reversal.available and reversal.reversal_fraction_5d is not None
                and reversal.classification in ("Transient -- mostly reverses", "Partial reversal")
                and reversal.reversal_fraction_5d >= 0.30):
            algo = "STEALTH"
            rationale = (
                f"Post-event reversal reclaims an estimated {reversal.reversal_fraction_5d:.0%} of the "
                f"pre-event move within 5 days ({reversal.classification.lower()}) -- consistent with "
                f"transient, liquidity-driven price pressure rather than a permanent re-rating. A "
                f"cost-minimizing trader is better off avoiding the crowd at the close and spreading "
                f"execution after T with a low-footprint strategy to capture part of the reversal."
            )
        elif (drift.available and drift.pct_of_pre_event_move_after_announcement is not None
              and drift.pct_of_pre_event_move_after_announcement >= 60):
            algo = "LIQ"
            rationale = (
                f"An estimated {drift.pct_of_pre_event_move_after_announcement:.0f}% of the pre-event "
                f"run-up occurred after the announcement date -- the anticipatory drift is compressed "
                f"into the days right before T rather than spread evenly. Liquidity-Seeking lets "
                f"execution opportunistically pick up size on favorable dips ahead of the crowd, "
                f"rather than paying the full concentrated impact at the close."
            )
        else:
            algo = "IS"
            rationale = (
                "No strong reversal or pre-effective drift-compression signal was detected -- treat "
                "this as a standard cost-minimizing execution problem and use Implementation "
                "Shortfall, balancing impact against timing risk at the desk's normal urgency setting."
            )
        if not reversal.available:
            notes.append(f"Reversal could not be measured ({reversal.reason}).")
        if not drift.available:
            notes.append(f"Drift decomposition unavailable ({drift.reason}).")

    if flow is not None:
        if flow.flow_pct_adv is not None:
            notes.append(
                f"Estimated passive flow-to-trade: {flow.shares:,.0f} shares "
                f"(${flow.notional_usd/1e6:.1f}M, {flow.flow_pct_adv:.1f}% of estimation-window ADV)."
            )
        else:
            notes.append(
                f"Estimated passive flow-to-trade: {flow.shares:,.0f} shares (${flow.notional_usd/1e6:.1f}M)."
            )

    if eta_calib.available and eta_calib.implied_eta is not None and eta_calib.baseline_eta:
        ratio = eta_calib.implied_eta / eta_calib.baseline_eta
        if ratio >= 1.5:
            notes.append(
                f"Implied event-day impact coefficient (eta~={eta_calib.implied_eta:.2f}) runs "
                f"{ratio:.1f}x the standard eta={eta_calib.baseline_eta:.2f} used elsewhere in this "
                f"tool -- treat standard market-impact estimates as conservative (too low) for this event."
            )
    elif not eta_calib.available:
        notes.append(f"Event-day eta calibration unavailable ({eta_calib.reason}).")

    notes.append(crowding_note)

    return RebalanceRecommendation(
        objective=objective,
        recommended_algo=algo,
        rationale=rationale,
        notes=notes,
    )


# -- Orchestrator ---------------------------------------------------------------

@dataclass
class ExecutionInsights:
    concentration: ClosingConcentration
    reversal: ReversalMetrics
    drift: DriftDecomposition
    flow: FlowToTrade
    eta_calib: EtaCalibration
    crowding_note: str
    recommendation: RebalanceRecommendation


def build_execution_insights(es: EventStudyResult, market: str, objective: str = "Cost-Minimizing",
                             announcement_date=None, weight_change_pct=None,
                             tracked_aum_usd=None, log=None) -> ExecutionInsights:
    """Single entry point tying together all seven execution-cost extensions."""
    def _log(msg):
        if log: log(msg)

    bars_expected = MARKET_INFO.get(market, {}).get("bars", 78)

    concentration = analyze_closing_concentration(es.ticker, es.T, bars_expected, log=log)
    reversal      = compute_reversal(es.car, es.rel_days)
    drift         = compute_drift_decomposition(es.car, es.event_dates, es.T, announcement_date)

    flow = None
    if weight_change_pct is not None and tracked_aum_usd is not None and weight_change_pct > 0 and tracked_aum_usd > 0:
        flow = estimate_flow_to_trade(weight_change_pct, tracked_aum_usd, es.price_at_T, es.est_avg_volume)

    flow_pct_adv = flow.flow_pct_adv if flow is not None else None
    eta_calib = calibrate_event_day_eta(es.car, es.rel_days, flow_pct_adv, es.est_sigma_daily)

    crowding = basket_crowding_note(es.index_name)

    recommendation = recommend_rebalance_execution(
        objective, concentration, reversal, drift, flow, eta_calib, crowding
    )

    _log("Execution insights complete.")

    return ExecutionInsights(
        concentration=concentration,
        reversal=reversal,
        drift=drift,
        flow=flow,
        eta_calib=eta_calib,
        crowding_note=crowding,
        recommendation=recommendation,
    )
