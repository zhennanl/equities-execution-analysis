"""Positioning check for index-rebalance names — who is already in the
trade, estimated three ways:

1. price/volume FOOTPRINT (free, any market): infer pre-positioning from
   our own event study — excess abnormal volume between announcement and
   effective, in ADV units, with CAR drift as direction confirmation. This
   is the estimate a desk can always compute; it cannot identify WHO holds.
2. official SHORT/BORROW disclosures (free, per-market regimes): Japan
   0.2% position disclosures (same-day), Korea net-short register
   (0.01%/KRW1bn), HK SFC weekly aggregated short positions, Taiwan daily
   margin & SBL balances, US FINRA bi-monthly short interest + SEC FTD.
   `short_interest_snapshot` pulls the yfinance fields for US-listed names;
   the per-market source map is in PUBLIC_POSITIONING_SOURCES.
3. what BROKERS additionally see (not public, documented for honesty):
   own client flow by segment, prime-brokerage securities-lending book,
   internal crossing interest, paid vendors (S&P Global Securities
   Finance, EPFR fund flows), exchange member-level data.

The footprint heuristic is disclosed everywhere: excess volume x an
assumed arbitrageur participation share. It bounds the position; it does
not name the holder.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

ARB_PARTICIPATION = 0.5      # assumed share of excess volume that is
                             # event-driven accumulation (disclosed heuristic)
HEAVY_ADV_DAYS = 3.0
MODERATE_ADV_DAYS = 1.0
DRIFT_CONFIRM = 0.02         # |CAR drift| >= 2% corroborates the footprint


@dataclass
class PositioningFootprint:
    available: bool
    reason: str = ""
    window: str = ""
    excess_adv_days: float = 0.0        # cumulative abnormal volume above 1x, in ADV days
    est_prepositioned_shares: float = 0.0
    est_prepositioned_pct_adv: float = 0.0
    car_drift: float = 0.0              # CAR change over the window (direction hint)
    verdict: str = ""                   # HEAVY / MODERATE / LIGHT
    detail: str = ""
    caveats: list = field(default_factory=list)


def positioning_footprint(es, announcement_rel: int = None,
                          arb_participation: float = ARB_PARTICIPATION
                          ) -> PositioningFootprint:
    """Estimate pre-positioning from the event-study window.

    `announcement_rel`: relative day of the announcement (negative, e.g. -6);
    defaults to the start of the pre-effective window. Window runs to T-1 —
    positioning is what accumulated BEFORE the effective print."""
    rel = np.asarray(es.rel_days)
    ab = np.asarray(es.ab_vol, dtype=float)
    car = np.asarray(es.car, dtype=float)
    pre = rel < 0
    if pre.sum() < 3:
        return PositioningFootprint(False, reason="fewer than 3 pre-effective "
                                    "days in the event window")
    start = int(announcement_rel) if announcement_rel is not None else int(rel[pre][0])
    m = (rel >= start) & (rel < 0)
    if m.sum() < 1:
        return PositioningFootprint(False, reason="empty announcement->T-1 window")
    excess = np.clip(ab[m] - 1.0, 0.0, None).sum()
    adv = float(getattr(es, "est_avg_volume", 0.0) or 0.0)
    shares = excess * adv * arb_participation
    drift = float(car[m][-1] - car[m][0]) if m.sum() > 1 else 0.0
    confirmed = abs(drift) >= DRIFT_CONFIRM
    if excess >= HEAVY_ADV_DAYS and confirmed:
        verdict = "HEAVY"
    elif excess >= MODERATE_ADV_DAYS:
        verdict = "MODERATE"
    else:
        verdict = "LIGHT"
    detail = (f"Window T{start:+d}..T-1: {excess:.1f} ADV-days of excess "
              f"volume -> est. ~{shares:,.0f} sh pre-positioned "
              f"(~{excess * arb_participation:.1f}x ADV) at "
              f"{arb_participation:.0%} assumed event-driven share; CAR "
              f"drift {drift:+.1%} "
              + ("corroborates accumulation." if confirmed else
                 "does NOT corroborate — excess volume may be two-sided."))
    return PositioningFootprint(
        True, window=f"T{start:+d}..T-1", excess_adv_days=round(float(excess), 2),
        est_prepositioned_shares=round(float(shares), 0),
        est_prepositioned_pct_adv=round(float(excess * arb_participation), 2),
        car_drift=round(drift, 4), verdict=verdict, detail=detail,
        caveats=["Footprint bounds the position; it cannot identify holders "
                 "or split indexers vs arbitrageurs.",
                 f"Assumed event-driven share of excess volume: "
                 f"{arb_participation:.0%} (parameter).",
                 "For the SHORT side use the official per-market disclosures "
                 "(see source table) — price/volume alone cannot see borrow."])


# ── official public sources per market ─────────────────────────────────────

PUBLIC_POSITIONING_SOURCES = [
    {"Market": "Japan (TSE)", "Dataset": "Outstanding short positions >=0.2% (per holder, per stock)",
     "Cadence": "daily (same-day publication)", "Access": "free — JPX website CSV"},
    {"Market": "Japan (TSE)", "Dataset": "Trading by investor type (foreign/individual/prop net flows)",
     "Cadence": "weekly", "Access": "free — JPX"},
    {"Market": "Taiwan (TWSE)", "Dataset": "Margin purchase / short sale balances + SBL short balance per stock",
     "Cadence": "daily", "Access": "free — TWSE open data"},
    {"Market": "Taiwan (TWSE)", "Dataset": "Foreign ownership % per stock",
     "Cadence": "daily", "Access": "free — TWSE/TDCC"},
    {"Market": "Korea (KRX)", "Dataset": "Net short position register (>=0.01% or KRW 1bn) + short-sale balance",
     "Cadence": "daily (T+2/T+3 publication)", "Access": "free — KRX/FSS"},
    {"Market": "Hong Kong (HKEX)", "Dataset": "SFC aggregated reportable short positions (Friday snapshot)",
     "Cadence": "weekly", "Access": "free — SFC website"},
    {"Market": "Hong Kong (HKEX)", "Dataset": "Daily short-selling turnover per stock",
     "Cadence": "daily", "Access": "free — HKEX"},
    {"Market": "US", "Dataset": "FINRA equity short interest (all listed names)",
     "Cadence": "twice monthly (settlement-date, ~T+9 publication)", "Access": "free — FINRA data"},
    {"Market": "US", "Dataset": "SEC Reg SHO fails-to-deliver",
     "Cadence": "twice monthly", "Access": "free — SEC"},
    {"Market": "US", "Dataset": "13F institutional holdings",
     "Cadence": "quarterly (45-day lag — too slow for events; shows the passive base)",
     "Access": "free — SEC EDGAR"},
    {"Market": "US / global ETFs", "Dataset": "ETF shares outstanding (creation/redemption flow)",
     "Cadence": "daily", "Access": "free — issuer sites / yfinance"},
    {"Market": "EU/UK", "Dataset": "Net short position registers (>=0.5% public)",
     "Cadence": "daily", "Access": "free — ESMA/FCA registers"},
    {"Market": "(brokers only)", "Dataset": "Own client flow, PB securities-lending book, crossing interest, "
     "paid vendors (S&P Global Securities Finance, EPFR)",
     "Cadence": "real-time/daily", "Access": "NOT public — listed for honesty"},
]


def positioning_sources_table() -> pd.DataFrame:
    return pd.DataFrame(PUBLIC_POSITIONING_SOURCES)


# ── US short-interest snapshot (yfinance; injectable for tests) ────────────

def short_interest_snapshot(ticker: str, info_fn=None) -> dict:
    """yfinance .info short-interest fields for US-listed names — the
    bi-monthly FINRA number surfaced through a free API. `info_fn`
    injectable (tests / other vendors)."""
    if info_fn is None:                                    # pragma: no cover
        def info_fn(t):
            import yfinance as yf
            return yf.Ticker(t).info
    try:
        info = info_fn(ticker)
    except Exception as e:
        return {"available": False, "reason": f"info fetch failed: {e}"}
    ss = info.get("sharesShort")
    if not ss:
        return {"available": False,
                "reason": "no short-interest fields (non-US listing? use the "
                          "per-market official sources instead — see table)"}
    prior = info.get("sharesShortPriorMonth")
    chg = (ss - prior) / prior if prior else None
    signal = ("" if chg is None else
              "shorts BUILDING into the event" if chg > 0.10 else
              "shorts COVERING" if chg < -0.10 else "short base flat")
    return {"available": True, "shares_short": ss,
            "prior_month": prior,
            "chg_mom": None if chg is None else round(chg, 3),
            "days_to_cover": info.get("shortRatio"),
            "pct_of_float": info.get("shortPercentOfFloat"),
            "signal": signal,
            "note": "FINRA bi-monthly settlement-date data (~T+9 lag) — a "
                    "positioning LEVEL, not today\'s flow."}
