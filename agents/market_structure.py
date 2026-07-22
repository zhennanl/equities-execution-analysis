"""Market-structure fingerprint & drift tracker — measure the structure,
describe it in words, and track its development over time.

HOW WE CHARACTERIZE A MARKET'S MICROSTRUCTURE (the measurement framework):

    Liquidity WHERE   close-auction share; U-shape coefficient (open+close
                      vs midday volume); lunch dip (where sessions break).
    Liquidity COST    Roll effective-spread proxy (bps); Amihud illiquidity
                      (bps of move per $1M traded).
    PRICE FORMATION   variance ratio (5-min RV vs daily-scaled — >1 means
                      intraday noise/bounce, <1 means quiet tape between
                      sessions); intraday return autocorrelation (bounce vs
                      momentum); overnight/intraday variance split (how
                      much price discovery happens while the market is
                      CLOSED — high in gap-prone, limit-banded markets).
    CONSTRAINTS       from MARKET_REG/LIMIT_BANDS: bands, lot sizes,
                      short regime, settlement — the rules half of
                      structure that bars alone can't see.

The FINGERPRINT is the quantitative half computed from any MarketData; the
NOTES table is the qualitative half (2026 state, sourced); DRIFT compares
two dated fingerprints and flags what changed beyond thresholds — the
"track the development" automation: snapshot quarterly, diff, and the
flagged deltas are your market-structure briefing.
"""
from __future__ import annotations

import datetime as _dt
import json
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

from agents.microstructure_analytics import roll_spread

DEFAULT_STRUCTURE_PATH = (Path(__file__).resolve().parent.parent / "data"
                          / "structure_library.json")

DRIFT_THRESHOLDS = {          # |delta| that makes a metric "developed"
    "close_share": 0.03,      # +/-3pp of day volume
    "u_shape": 0.25,
    "roll_spread_bps": None,  # relative: 30%
    "variance_ratio": 0.15,
    "autocorr_1": 0.10,
    "overnight_var_share": 0.10,
    "amihud_bps_per_musd": None,   # relative: 50%
}


@dataclass
class StructureFingerprint:
    available: bool
    reason: str = ""
    market: str = ""
    ticker: str = ""
    as_of: str = ""
    close_share: float = None          # last-bar share of day volume
    u_shape: float = None              # (first+last)/2 / midday avg volume
    lunch_dip: float = None            # midday trough vs day mean (None if no lunch)
    roll_spread_bps: float = None
    variance_ratio: float = None       # 5m-RV-based daily var / close-close var
    autocorr_1: float = None           # 5m return lag-1 autocorr
    overnight_var_share: float = None  # overnight var / (overnight + intraday)
    amihud_bps_per_musd: float = None
    words: str = ""


def structure_fingerprint(md) -> StructureFingerprint:
    """Compute the quantitative fingerprint from a MarketData object
    (any source: yfinance, kdb+, tick file)."""
    intra, daily = md.intraday, md.daily
    if intra is None or len(intra) < 60 or daily is None or len(daily) < 25:
        return StructureFingerprint(False, reason="need >=60 intraday bars "
                                    "and >=25 daily rows")
    days = intra.groupby(intra.index.normalize())
    close_shares, u_shapes, dips = [], [], []
    ac, rv5 = [], []
    for _, d in days:
        v = d["Volume"].to_numpy(dtype=float)
        if len(v) < 10 or v.sum() <= 0:
            continue
        close_shares.append(v[-1] / v.sum())
        k = max(2, len(v) // 6)
        mid = v[k:-k]
        u_shapes.append(((v[:k].mean() + v[-k:].mean()) / 2)
                        / max(mid.mean(), 1.0))
        dips.append(mid.min() / max(v.mean(), 1.0))
        r = d["Close"].pct_change().dropna().to_numpy()
        if len(r) > 5 and r.std() > 0:
            ac.append(float(pd.Series(r).autocorr(lag=1)))
            rv5.append(float(np.sum(r ** 2)))
    if not close_shares:
        return StructureFingerprint(False, reason="no usable intraday days")
    cc = daily["Close"].pct_change().dropna()
    var_daily = float(cc.var()) or 1e-12
    vr = float(np.mean(rv5) / var_daily) if rv5 else None
    on = (np.log(daily["Open"] / daily["Close"].shift())).dropna()
    io = (np.log(daily["Close"] / daily["Open"])).dropna()
    ov = float(on.var() / max(on.var() + io.var(), 1e-12))
    dollar = (daily["Close"] * daily["Volume"]).replace(0, np.nan)
    ami = float((daily["Close"].pct_change().abs() / (dollar / 1e6))
                .dropna().mean() * 1e4)
    rs = roll_spread(daily)
    fp = StructureFingerprint(
        True, market=md.market, ticker=md.ticker,
        as_of=str(_dt.date.today()),
        close_share=round(float(np.mean(close_shares)), 4),
        u_shape=round(float(np.mean(u_shapes)), 2),
        lunch_dip=round(float(np.mean(dips)), 2),
        roll_spread_bps=(round(rs["spread_bps"], 1)
                         if rs.get("available") else None),
        variance_ratio=None if vr is None else round(vr, 2),
        autocorr_1=round(float(np.mean(ac)), 3) if ac else None,
        overnight_var_share=round(ov, 3),
        amihud_bps_per_musd=round(ami, 2))
    fp.words = describe_fingerprint(fp)
    return fp


def describe_fingerprint(fp: StructureFingerprint) -> str:
    """The words: turn the numbers into the sentence a dealer would say."""
    if not fp.available:
        return fp.reason
    L = []
    cs = fp.close_share
    L.append(f"{cs:.0%} of volume prints in the closing bar — "
             + ("auction-dominated: benchmark risk lives at the close"
                if cs >= 0.12 else
                "meaningful close concentration" if cs >= 0.07 else
                "volume is spread through the day"))
    L.append(f"U-shape {fp.u_shape:.1f}x "
             + ("(strong open/close humps — schedule around the belly)"
                if fp.u_shape >= 1.8 else "(mild intraday curve)"))
    if fp.autocorr_1 is not None:
        L.append(f"5-min autocorr {fp.autocorr_1:+.2f} "
                 + ("— bounce-dominated, patient limit orders get paid"
                    if fp.autocorr_1 < -0.05 else
                    "— momentum tape, hesitation costs" if fp.autocorr_1 > 0.05
                    else "— roughly efficient at 5-min"))
    L.append(f"overnight variance share {fp.overnight_var_share:.0%} "
             + ("— discovery happens while you sleep; opens gap"
                if fp.overnight_var_share >= 0.45 else
                "— most discovery is intraday"))
    if fp.roll_spread_bps is not None:
        L.append(f"Roll effective spread ~{fp.roll_spread_bps:.0f} bps")
    L.append(f"Amihud {fp.amihud_bps_per_musd:.1f} bps/$1M "
             + ("— thin: size moves price" if fp.amihud_bps_per_musd > 5
                else "— deep"))
    return "; ".join(L) + "."


# ── snapshot library + drift (the tracking automation) ─────────────────────

def record_fingerprint(fp: StructureFingerprint,
                       path: Path = DEFAULT_STRUCTURE_PATH) -> dict:
    row = {k: v for k, v in fp.__dict__.items() if k != "words"}
    path = Path(path)
    lib = []
    if path.exists():
        try:
            lib = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            lib = []
    lib.append(row)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(lib, indent=1), encoding="utf-8")
    return row


def structure_drift(old: StructureFingerprint | dict,
                    new: StructureFingerprint | dict) -> list:
    """Compare two dated fingerprints; return the human-readable list of
    metrics that moved beyond thresholds — the quarterly 'what changed in
    this market's structure' briefing."""
    o = old if isinstance(old, dict) else old.__dict__
    n = new if isinstance(new, dict) else new.__dict__
    out = []
    for k, thr in DRIFT_THRESHOLDS.items():
        a, b = o.get(k), n.get(k)
        if a is None or b is None:
            continue
        if thr is None:                      # relative threshold
            if a != 0 and abs(b - a) / abs(a) > (0.30 if "roll" in k else 0.50):
                out.append(f"{k}: {a} -> {b} "
                           f"({(b - a) / abs(a):+.0%}) — investigate")
        elif abs(b - a) > thr:
            out.append(f"{k}: {a} -> {b} (Δ{b - a:+.3f}) — structural move")
    return out


# ── the qualitative half: each market in words, 2026 ──────────────────────

MARKET_STRUCTURE_NOTES = {
    "Japan (TSE)":
        "Deep, quote-driven continuous market with special-quote renewals "
        "instead of hard halts. Closing auction at 15:30 since the Nov-2024 "
        "close reform (session extended, closing auction introduced). "
        "Off-exchange: ToSTNeT + PTS venues (Japannext/Cboe/ODX ~10% "
        "combined) — fragmentation real but primary-dominated. Tick-size "
        "program by price tier; T+2; shorts covered-only with the -10% "
        "uptick trigger. Lunch break splits the day; overnight gap risk "
        "material.",
    "Hong Kong (HKEX)":
        "Single lit venue, no static price band — VCM cooling-offs per "
        "stock instead. CAS closing auction 16:00-16:10 with no-cancel and "
        "random-close phases. Per-stock board lots; stamp duty makes it "
        "structurally expensive; short selling on the designated list with "
        "tick rule and weekly SFC position disclosure. 2026 theme: "
        "HKD-RMB dual counters (RMB stamp duty now payable in RMB) staging "
        "toward Southbound RMB trading; Connect flow a dominant liquidity "
        "driver.",
    "China-A Shanghai":
        "Retail-heavy order-driven market inside ±10% daily bands (±20% "
        "STAR), T+1 stock settlement (no same-day turnaround), effectively "
        "no shorting. Close = brief 14:57-15:00 call. Off-exchange crossing "
        "prohibited. 2025-26 regime shift: program-trading rules effective "
        "Jul-2025 (order-rate thresholds define HFT; reporting + fees) — "
        "quant flow slowing, front-loaded morning liquidity, Connect the "
        "foreign rail with SPSA pre-checks.",
    "China-A Shenzhen":
        "As Shanghai but ChiNext ±20% bands and a younger, even more "
        "retail-tilted name mix; same T+1/no-short/program-trading regime.",
    "Taiwan (TWSE)":
        "Continuous since 2020 (was batch-call), ±10% daily limits that DO "
        "lock (queue-vs-retreat is a daily dealer decision), 1000-share "
        "board lots with a separate odd-lot session, close call auction "
        "13:25-13:30. Foreign investors dominate value traded; FINI "
        "framework, SBL-quota shorts, excellent free daily margin/SBL/"
        "foreign-ownership disclosure. TWD is a restricted currency — "
        "funding is part of microstructure here.",
    "Korea (KRX)":
        "±30% bands with per-stock VIs and index sidecars. The 2026 story "
        "is fragmentation: Nextrade (Mar-2025, first ATS in 70 years) took "
        "~10-15% share then stalled near 10% under the 15% volume cap — "
        "first real SOR decision in Korea, extended hours pulling some "
        "discovery off the primary close. Shorts resumed Mar-2025 under "
        "tightened rules (registration, systems audits). Retail share "
        "high; KOSDAQ especially.",
    "Singapore (SGX)":
        "Small, institutional, MM/liquidity-provider supported; no lunch "
        "break; per-stock CB (±10% vs 5-min reference); 100-share lots. "
        "Liquidity thin outside index names — a capacity market, not a "
        "speed market.",
    "India (NSE)":
        "Order-driven, deep retail + derivatives-led (index options volume "
        "world-leading); T+1 settled with optional T+0 for the top-500 "
        "(2026) — settlement innovation is the structural story, plus "
        "periodic F&O curbs. Stock bands 2-20% (no static band for F&O "
        "names); FPI limits bind in places. Closing session mechanics "
        "changing toward auction-based (watch item).",
    "Australia (ASX)":
        "Primary + Cboe AU competition, staggered opening auction by "
        "alphabet, CSPA close ~16:10 (huge index/EOD concentration), no "
        "price bands (anomalous-order controls), covered shorts with ASIC "
        "reporting. CHESS replacement (again) the perennial settlement "
        "watch item.",
    "US":
        "The fragmentation extreme for contrast: 16+ exchanges + ~40 ATSs, "
        "LULD bands + MWCB, Reg NMS routing, T+1 since May-2024, "
        "closing auctions at NYSE/Nasdaq are the world's largest prints. "
        "Everything the Asia books do differently is visible against this "
        "baseline.",
}
