"""Program Trading Desk — Asia cross-market basket execution support.

Maps the program-trader job onto the platform (see SESSION_SUMMARY 2026-07-08
session 5j): basket pre-trade across markets, session/time-zone coordination,
market-microstructure regulation reference (lot sizes, short-sale regimes,
circuit breakers), T+n settlement dates, and a simulated fills-vs-blotter
reconciliation. Everything is desk-reference quality with honesty labels:
session times and regulatory notes are STYLIZED (no holiday calendars, DST
approximated, per-stock board lots vary) — verify against the exchange
notice before trading. All functions are pure and offline-testable; the
program pre-trade takes an injectable fetcher (same pattern as basket mode).
"""

from __future__ import annotations

import datetime as _dt
from dataclasses import dataclass
from typing import Callable, Optional

import numpy as np
import pandas as pd

from agents.agent1_market_data import MARKET_INFO
from agents.explicit_costs import get_explicit_costs

# ── Per-market desk reference (stylized; one line each, verify vs exchange) ──
# utc_offset: standard offsets; US/UK/AU DST is approximated (disclosed).
# lunch: (start, end) local, or None. settle: business days after trade date.
# lot: typical board lot ("varies" markets flagged). short: regime note.
# cb: circuit-breaker / price-band note.
MARKET_REG: dict[str, dict] = {
    "Japan (TSE)":       dict(utc=9,    lunch=("11:30", "12:30"), settle=2, lot=100,
        short="Covered only; uptick ('price-test') rule triggers on -10% days; flagging + reporting required.",
        cb="Per-stock daily price limits + special quotes; no market-wide halt."),
    "Hong Kong (HKEX)":  dict(utc=8,    lunch=("12:00", "13:00"), settle=2, lot=None,
        short="Designated-securities list only; naked shorting banned; tick rule on covered shorts.",
        cb="VCM: per-stock ±10% vs 5-min-ago triggers 5-min cooling-off; CAS auction 16:00-16:10."),
    "China-A Shanghai":  dict(utc=8,    lunch=("11:30", "13:00"), settle=1, lot=100,
        short="Effectively restricted: margin-trading list only via brokers; practical institutional shorting minimal.",
        cb="±10% daily price limit (±5% ST names, ±20% STAR); T+1 stock settlement, no same-day turnaround."),
    "China-A Shenzhen":  dict(utc=8,    lunch=("11:30", "13:00"), settle=1, lot=100,
        short="Same as Shanghai: margin-list only, minimal practical shorting.",
        cb="±10% daily limit (±20% ChiNext); T+1, no same-day turnaround."),
    "Taiwan (TWSE)":     dict(utc=8,    lunch=None,               settle=2, lot=1000,
        short="SBL quota system; uptick restrictions; borrow must be pre-arranged (locates slow).",
        cb="±10% daily price limit; intraday volatility interruption."),
    "Korea (KRX)":       dict(utc=9,    lunch=None,               settle=2, lot=1,
        short="Resumed Mar-2025 after full ban with tightened rules: covered only, position reporting, institutional systems audits.",
        cb="±30% daily limit; VI per stock; sidecar/market CB on KOSPI futures moves."),
    "Singapore (SGX)":   dict(utc=8,    lunch=None,               settle=2, lot=100,
        short="Covered shorting allowed; daily short-sell reporting; MAS position disclosures.",
        cb="Per-stock circuit breaker ±10% around 5-min reference."),
    "India (NSE)":       dict(utc=5.5,  lunch=None,               settle=1, lot=1,
        short="Institutional: SLB-covered only, disclosed upfront; intraday naked prohibited for institutions.",
        cb="Stock bands 2-20%; market-wide 10/15/20% index halts; T+1 settled."),
    "Thailand (SET)":    dict(utc=7,    lunch=("12:30", "14:30"), settle=2, lot=100,
        short="Uptick rule; eligible-securities list; regulator tightened after 2024 naked-short scandals.",
        cb="±30% ceiling/floor; market-wide CB at index -8/-15/-20%."),
    "Indonesia (IDX)":   dict(utc=7,    lunch=("11:30", "13:30"), settle=2, lot=100,
        short="Restricted eligible list; margin/short rules per OJK; practically limited.",
        cb="Asymmetric auto-rejection bands (ARA/ARB) by price tier; market-wide halts."),
    "Malaysia (KLSE)":   dict(utc=8,    lunch=("12:30", "14:30"), settle=2, lot=100,
        short="Regulated (RSS) on approved securities only, with gross short position limits.",
        cb="±30 static / dynamic limits; market-wide CB on KLCI."),
    "Vietnam (HOSE)":    dict(utc=7,    lunch=("11:30", "13:00"), settle=2, lot=100,
        short="No institutional shorting in practice (covered SBL pilot exists on paper only).",
        cb="±7% daily band (HOSE); ATC close 14:30-14:45; foreign-ownership room binds."),
    "Australia (ASX)":   dict(utc=10,   lunch=None,               settle=2, lot=1,
        short="Covered only; ASIC daily short-sale + position reporting.",
        cb="Anomalous-order thresholds; staggered opening auction; CSPA close ~16:00-16:10 (DST approx.)."),
    "US":                dict(utc=-5,   lunch=None,               settle=1, lot=1,
        short="Reg SHO: locate required; Rule 201 uptick triggers on -10% days.",
        cb="LULD per-stock bands + market-wide 7/13/20%% S&P halts; T+1 since May-2024 (DST approx.)."),
    "UK (LSE)":          dict(utc=0,    lunch=None,               settle=2, lot=1,
        short="Covered; UK SSR net-short disclosure to FCA above thresholds.",
        cb="Per-stock dynamic/static circuit breakers on the order book (DST approx.)."),
}


def _parse_hm(s: str) -> _dt.time:
    h, m = s.split(":")
    return _dt.time(int(h), int(m))


def market_status(market: str, now_utc: _dt.datetime) -> dict:
    """Session state for one market at a UTC instant: local time, phase
    (Pre-open / Open / Lunch / Closed), and minutes to the close."""
    info, reg = MARKET_INFO.get(market), MARKET_REG.get(market)
    if info is None or reg is None:
        return {"market": market, "phase": "unknown", "local_time": "", "mins_to_close": None}
    local = now_utc + _dt.timedelta(hours=reg["utc"])
    t = local.time()
    o, c = _parse_hm(info["open"]), _parse_hm(info["close"])
    phase = "Closed"
    if o <= t <= c:
        phase = "Open"
        if reg["lunch"]:
            ls, le = _parse_hm(reg["lunch"][0]), _parse_hm(reg["lunch"][1])
            if ls <= t < le:
                phase = "Lunch"
    elif t < o:
        phase = "Pre-open"
    mins = None
    if phase in ("Open", "Lunch"):
        mins = int((_dt.datetime.combine(local.date(), c) - local.replace(tzinfo=None)).total_seconds() // 60)
    return {"market": market, "local_time": local.strftime("%H:%M"),
            "phase": phase, "mins_to_close": mins,
            "close_utc": (_dt.datetime.combine(now_utc.date(), c)
                          - _dt.timedelta(hours=reg["utc"])).strftime("%H:%M")}


def market_status_board(now_utc: Optional[_dt.datetime] = None) -> pd.DataFrame:
    now_utc = now_utc or _dt.datetime.now(_dt.timezone.utc).replace(tzinfo=None)
    rows = [market_status(m, now_utc) for m in MARKET_REG]
    df = pd.DataFrame(rows)
    order = {"Open": 0, "Lunch": 1, "Pre-open": 2, "Closed": 3}
    return df.sort_values(["phase", "close_utc"],
                          key=lambda s: s.map(order) if s.name == "phase" else s
                          ).reset_index(drop=True)


def regulation_reference() -> pd.DataFrame:
    rows = []
    for m, r in MARKET_REG.items():
        ec = get_explicit_costs(m)
        rows.append({"Market": m,
                     "Board lot": r["lot"] if r["lot"] else "varies per stock",
                     "Settlement": f"T+{r['settle']}",
                     "Short-sale regime": r["short"],
                     "Circuit breakers / bands": r["cb"],
                     "Explicit costs (Buy, bps)": ec.total_bps("Buy"),
                     "Explicit costs (Sell, bps)": ec.total_bps("Sell")})
    return pd.DataFrame(rows)


def lot_check(market: str, shares: float) -> dict:
    """Board-lot compliance: rounds DOWN to the lot and flags the remainder."""
    lot = MARKET_REG.get(market, {}).get("lot")
    if not lot or lot <= 1:
        return {"ok": True, "lot": lot or 1, "rounded": float(shares), "odd": 0.0,
                "note": "No board-lot constraint (or per-stock — verify)." if lot is None
                        else "Lot of 1 — no rounding."}
    rounded = float(int(shares // lot) * lot)
    odd = float(shares - rounded)
    return {"ok": odd == 0.0, "lot": lot, "rounded": rounded, "odd": odd,
            "note": ("OK" if odd == 0 else
                     f"{odd:,.0f} odd-lot shares — route via odd-lot facility or round to {rounded:,.0f}.")}


def short_check(market: str, side: str, locate_confirmed: bool = False) -> dict:
    reg = MARKET_REG.get(market, {})
    if side != "Sell":
        return {"level": "none", "note": ""}
    note = reg.get("short", "Verify local short-sale rules.")
    hard = market.startswith("China-A") or market == "Vietnam (HOSE)"
    if hard:
        return {"level": "BLOCK", "note": f"Short sale effectively unavailable: {note}"}
    if not locate_confirmed:
        return {"level": "WARN", "note": f"Locate/borrow not confirmed. {note}"}
    return {"level": "ok", "note": note}


def settlement_date(market: str, trade_date: _dt.date) -> _dt.date:
    """T+n business-day settlement (weekends only — no holiday calendar,
    disclosed)."""
    n = MARKET_REG.get(market, {}).get("settle", 2)
    d = trade_date
    while n > 0:
        d += _dt.timedelta(days=1)
        if d.weekday() < 5:
            n -= 1
    return d


def wave_plan(markets: list[str], now_utc: Optional[_dt.datetime] = None) -> pd.DataFrame:
    """Cross-market execution waves: order the program's markets by closing
    time in UTC — the desk works the earliest close first (Tokyo/Taipei before
    HK/China before India before Europe/US)."""
    now_utc = now_utc or _dt.datetime.now(_dt.timezone.utc).replace(tzinfo=None)
    rows = []
    for m in sorted(set(markets)):
        st = market_status(m, now_utc)
        rows.append({"Market": m, "Close (UTC)": st.get("close_utc", ""),
                     "Phase now": st["phase"],
                     "Mins to close": st["mins_to_close"]})
    df = pd.DataFrame(rows).sort_values("Close (UTC)").reset_index(drop=True)
    df.insert(0, "Wave", range(1, len(df) + 1))
    return df


# ── Program pre-trade blotter ──────────────────────────────────────────────

_CAP_RATE = 0.15          # Medium-urgency participation for capacity days


def run_program_pretrade(program: pd.DataFrame, fetch_fn: Callable = None,
                         trade_date: Optional[_dt.date] = None,
                         log: Callable = None) -> pd.DataFrame:
    """Program CSV columns: ticker, market, side [, shares]. Per name:
    price/ADV via fetch_fn (injectable; defaults to agent1), % ADV, capacity
    days at 15% participation, lot check, short check, explicit costs,
    settlement date, capacity RAG (GREEN <=1d / AMBER / RED >3d). Failures
    degrade per name."""
    if fetch_fn is None:
        from agents.agent1_market_data import fetch_market_data as fetch_fn
    trade_date = trade_date or _dt.date.today()
    rows = []
    for _, r in program.iterrows():
        tkr, mkt = str(r["ticker"]).strip(), str(r["market"]).strip()
        side = str(r.get("side", "Buy")).strip().capitalize() or "Buy"
        try:
            md = fetch_fn(tkr, mkt)
            shares = (float(r["shares"]) if "shares" in program.columns and pd.notna(r.get("shares"))
                      else 0.05 * md.adv_shares)
            pct = shares / md.adv_shares * 100 if md.adv_shares else float("nan")
            days = shares / (md.adv_shares * _CAP_RATE) if md.adv_shares else float("inf")
            rag = "GREEN" if days <= 1.0 else ("RED" if days > 3.0 else "AMBER")
            lc = lot_check(mkt, shares)
            sc = short_check(mkt, side, bool(r.get("locate", False)))
            notes = []
            if not lc["ok"]:
                notes.append(lc["note"])
            if sc["level"] in ("WARN", "BLOCK"):
                notes.append(f"[{sc['level']}] {sc['note']}")
            rows.append({"Ticker": md.ticker, "Market": mkt, "Side": side,
                         "Shares": round(shares, 0), "% ADV": round(pct, 1),
                         "Capacity (days)": round(days, 2), "Flag": rag,
                         "Lot-rounded": lc["rounded"],
                         "Explicit (bps)": get_explicit_costs(mkt).total_bps(side),
                         "Settles": str(settlement_date(mkt, trade_date)),
                         "Notes": " | ".join(notes), "Error": ""})
        except Exception as e:
            rows.append({"Ticker": tkr, "Market": mkt, "Side": side, "Shares": None,
                         "% ADV": None, "Capacity (days)": None, "Flag": "n/a",
                         "Lot-rounded": None, "Explicit (bps)": None, "Settles": "",
                         "Notes": "", "Error": f"{type(e).__name__}: {e}"})
        if log:
            log(f"{tkr}: done")
    df = pd.DataFrame(rows)
    sev = {"n/a": -1, "RED": 0, "AMBER": 1, "GREEN": 2}
    df["_s"] = df["Flag"].map(sev)
    return df.sort_values(["_s", "% ADV"], ascending=[True, False]).drop(columns="_s").reset_index(drop=True)


def program_recon(blotter: pd.DataFrame) -> str:
    """Simulated end-of-day reconciliation: shares and (price-proxy) cash
    tie-out per name plus program totals — the ops-support artifact, generated
    rather than hand-built. Real recon runs against custodian confirms; this
    demonstrates the record-keeping discipline on simulated fills."""
    ok = blotter[blotter["Error"] == ""] if "Error" in blotter.columns else blotter
    lines = ["=" * 70,
             f"PROGRAM RECONCILIATION — {_dt.date.today()} — {len(ok)} name(s)",
             "=" * 70]
    tot = 0.0
    for _, r in ok.iterrows():
        sh = r.get("Shares") or 0
        lot_sh = r.get("Lot-rounded") if r.get("Lot-rounded") is not None else sh
        diff = (sh or 0) - (lot_sh or 0)
        tot += sh or 0
        lines.append(f"{str(r['Ticker']):<12} {r['Side']:<4} ordered {sh:>14,.0f}  "
                     f"lot-executable {lot_sh:>14,.0f}  odd-lot {diff:>10,.0f}  "
                     f"settles {r.get('Settles', '')}")
    lines += ["-" * 70,
              f"TOTAL ordered shares: {tot:,.0f}. Discrepancy rule: any odd-lot",
              "residual above must be routed to the odd-lot facility or rounded",
              "with the client BEFORE settlement date; unresolved breaks escalate",
              "to ops. (Simulated tie-out — real recon runs vs custodian confirms.)",
              "=" * 70]
    return "\n".join(lines)
