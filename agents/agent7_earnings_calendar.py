"""
Agent 7: Earnings Calendar Check
Flags overnight gap risk when a scheduled earnings release falls inside the
order's likely execution horizon (single simulated day plus, for multi-day
schedules, the capacity-table horizon computed by Agent 6).

Data source: yfinance's Ticker.get_earnings_dates() -- free, and (unlike the
intraday 5-day cap or the 60-day daily cap) works reasonably across all 14
supported markets including Asian names, confirmed via live spot-checks
(AAPL, 2330.TW, 0700.HK, 7203.T, 005930.KS, D05.SI, 600519.SS, RELIANCE.NS,
BHP.AX, PTT.BK all returned usable rows). Coverage and update lag vary by
market -- this is disclosed in the flag's `available`/`reason` fields rather
than assumed reliable, consistent with the caveats already documented for
every other data source in this app (spread estimator, event study, etc.).

This is a genuinely new capability, not a re-framing of an existing one: the
platform previously had zero visibility into scheduled corporate events, so
"the market looks calm" (Agent 2's regime read) and "the market IS calm
through the horizon we're about to trade in" were conflated. An order sized
and scheduled purely on trailing volatility can walk straight into an
earnings-day gap that trailing data has no way to anticipate.
"""

import numpy as np
import pandas as pd
import yfinance as yf
from dataclasses import dataclass

# Flag as "near-term risk" if the nearest future earnings date falls within
# this many trading days of today.
NEAR_TERM_TRADING_DAYS = 5


@dataclass
class EarningsFlag:
    available: bool
    reason: str
    ticker: str
    next_earnings_date: object          # pd.Timestamp or None
    trading_days_until: int             # approximate (calendar business days, no holiday calendar)
    is_near_term: bool
    risk_note: str


def check_earnings_calendar(ticker: str, log=None) -> EarningsFlag:
    def _log(msg):
        if log:
            log(msg)

    try:
        tk = yf.Ticker(ticker)
        ed = tk.get_earnings_dates(limit=12)
    except Exception as e:
        _log(f"Earnings calendar unavailable for {ticker}: {e}")
        return EarningsFlag(False, f"Could not fetch earnings calendar: {e}", ticker, None, 0, False, "")

    if ed is None or ed.empty:
        return EarningsFlag(False, "No earnings-date data returned for this ticker.", ticker, None, 0, False, "")

    # get_earnings_dates() mixes past and future rows (not guaranteed sorted
    # or future-only) -- normalize to UTC and keep only rows at/after now.
    idx_utc = ed.index.tz_convert("UTC") if ed.index.tz is not None else ed.index.tz_localize("UTC")
    now_utc = pd.Timestamp.now(tz="UTC")
    future_mask = idx_utc >= now_utc
    if not future_mask.any():
        return EarningsFlag(False, "No upcoming earnings date found (only historical rows on file).",
                            ticker, None, 0, False, "")

    next_date = idx_utc[future_mask].min()

    # Approximate trading days until (business-day count, no holiday calendar --
    # consistent in precision with the rest of the app's day-count math, e.g.
    # Agent 6's capacity table).
    today = pd.Timestamp.now(tz="UTC").normalize()
    bdays = pd.bdate_range(start=today, end=next_date.normalize())
    trading_days_until = max(0, len(bdays) - 1)

    is_near_term = trading_days_until <= NEAR_TERM_TRADING_DAYS
    if is_near_term:
        risk_note = (
            f"Earnings scheduled in ~{trading_days_until} trading day(s) ({next_date.date()}) -- "
            f"an order worked over more than {trading_days_until} day(s), or held past the print, "
            f"carries overnight gap risk this platform's trailing-volatility models cannot see. "
            f"Consider raising urgency to complete before the print, or explicitly accepting "
            f"the gap risk if holding through it."
        )
    else:
        risk_note = f"Next earnings ~{trading_days_until} trading days out ({next_date.date()}) -- outside the near-term window."

    _log(f"Earnings check: next print {next_date.date()} (~{trading_days_until} trading days), near_term={is_near_term}")

    return EarningsFlag(
        available=True,
        reason="",
        ticker=ticker,
        next_earnings_date=next_date,
        trading_days_until=trading_days_until,
        is_near_term=is_near_term,
        risk_note=risk_note,
    )
