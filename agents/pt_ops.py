"""PT desk operations automations, round 2 — the four JD gaps left after
the 6h/6i cockpit work (session 6m):

A8  normalize_client_file   client basket files arrive in every convention
                            there is (Bloomberg "2330 TT", local codes,
                            B/S/1/2 sides, notional instead of shares).
                            Normalize to the platform contract with an
                            explicit ISSUES list — never silently guess.
A9  holiday calendar        settlement math and residual roll plans that
                            know Asia's holiday clusters (CNY, Golden
                            Week, National Day). Static 2026 table,
                            clearly approximate — production wires an
                            exchange calendar feed. Plus restricted-
                            currency FX notes (TWD/KRW/INR onshore).
A10 crossing_report         same name, opposite sides, different clients
                            -> internal crossing opportunity that saves
                            both clients the spread — WITH the per-market
                            legality/mechanism note (China-A: exchange
                            only; Japan: ToSTNeT; HK: direct business
                            reporting; TW: block rules).
A11 exposure_schedule       two-sided baskets: schedule waves so sell
                            proceeds fund buys — minimize the running net
                            exposure a naive pro-rata schedule leaves.

Same contracts as everything else: offline, injectable, tested, disclosed.
"""
from __future__ import annotations

import datetime as _dt
import re
from dataclasses import dataclass

import numpy as np
import pandas as pd

from agents.program_trading import MARKET_REG

# ── A8: client file normalizer ─────────────────────────────────────────────

# Bloomberg-style suffix -> (platform market, yahoo suffix, zero-pad width)
_BBG = {"TT": ("Taiwan (TWSE)", ".TW", 0), "HK": ("Hong Kong (HKEX)", ".HK", 4),
        "JT": ("Japan (TSE)", ".T", 0), "JP": ("Japan (TSE)", ".T", 0),
        "KS": ("Korea (KRX)", ".KS", 6), "CH": ("China-A Shanghai", ".SS", 6),
        "C1": ("China-A Shenzhen", ".SZ", 6), "SP": ("Singapore (SGX)", ".SI", 0),
        "IN": ("India (NSE)", ".NS", 0), "AU": ("Australia (ASX)", ".AX", 0),
        "US": ("US", "", 0), "UN": ("US", "", 0), "UW": ("US", "", 0)}
_SIDES = {"B": "Buy", "BUY": "Buy", "1": "Buy", "COVER": "Buy",
          "S": "Sell", "SELL": "Sell", "2": "Sell", "SHORT": "Sell",
          "SL": "Sell"}


def _norm_ticker(raw: str):
    """'2330 TT' -> ('2330.TW', 'Taiwan (TWSE)'); '700 HK' -> '0700.HK';
    already-suffixed Yahoo codes pass through. Returns (ticker, market|None)."""
    t = str(raw).strip().upper()
    m = re.fullmatch(r"([A-Z0-9]+)\s+([A-Z0-9]{2})(?:\s+EQUITY)?", t)
    if m and m.group(2) in _BBG:
        code, (mkt, suf, pad) = m.group(1), _BBG[m.group(2)]
        if pad and code.isdigit():
            code = code.zfill(pad)
        return code + suf, mkt
    return t, None       # assume already platform/Yahoo format; market unknown


def normalize_client_file(df: pd.DataFrame,
                          prev_close: dict = None) -> dict:
    """Normalize a client basket file. Recognized columns (case-insensitive,
    first match wins): ticker/symbol/security; side/direction/bs;
    shares/quantity/qty; notional/value/usd. Duplicate (ticker, side) lines
    are aggregated. Everything questionable lands in `issues` — the file is
    never silently 'fixed'."""
    cols = {c.lower(): c for c in df.columns}

    def pick(*names):
        for n in names:
            if n in cols:
                return cols[n]
        return None
    c_t = pick("ticker", "symbol", "security", "stock")
    c_s = pick("side", "direction", "bs", "b/s")
    c_q = pick("shares", "quantity", "qty")
    c_n = pick("notional", "value", "notional_usd", "usd")
    issues, rows = [], []
    if c_t is None or c_s is None:
        return {"ok": False, "issues": ["cannot find ticker and/or side "
                                        f"columns in {list(df.columns)}"],
                "basket": pd.DataFrame()}
    for i, r in df.iterrows():
        tkr, mkt = _norm_ticker(r[c_t])
        side = _SIDES.get(str(r[c_s]).strip().upper())
        if side is None:
            issues.append(f"row {i}: unrecognized side '{r[c_s]}' — SKIPPED")
            continue
        shares = pd.to_numeric(r[c_q], errors="coerce") if c_q else np.nan
        if pd.isna(shares) and c_n is not None:
            notional = pd.to_numeric(r[c_n], errors="coerce")
            px = (prev_close or {}).get(tkr)
            if pd.notna(notional) and px:
                shares = float(notional) / float(px)
                issues.append(f"row {i}: {tkr} converted from notional at "
                              f"prev close {px} — verify")
            else:
                issues.append(f"row {i}: {tkr} has notional but no prev "
                              "close supplied — SKIPPED")
                continue
        if pd.isna(shares) or shares <= 0:
            issues.append(f"row {i}: {tkr} no usable shares/notional — SKIPPED")
            continue
        if mkt is None:
            issues.append(f"row {i}: '{r[c_t]}' not a recognized convention "
                          "— passed through as-is, ASSIGN market manually")
        rows.append({"ticker": tkr, "market": mkt, "side": side,
                     "shares": float(shares)})
    out = pd.DataFrame(rows)
    if len(out):
        n0 = len(out)
        out = (out.groupby(["ticker", "side"], as_index=False)
               .agg({"market": "first", "shares": "sum"}))
        if len(out) < n0:
            issues.append(f"{n0 - len(out)} duplicate (ticker, side) line(s) "
                          "aggregated")
        both = set(out[out.side == "Buy"].ticker) & set(out[out.side == "Sell"].ticker)
        if both:
            issues.append(f"BOTH-SIDES flag: {sorted(both)} appear as buy AND "
                          "sell — confirm with the client before netting")
    return {"ok": True, "basket": out, "issues": issues,
            "n_in": int(len(df)), "n_out": int(len(out))}


# ── A9: holiday-aware settlement + closures + FX notes ────────────────────

# Major 2026 closures, APPROXIMATE — verify against exchange calendars.
HOLIDAYS_2026: dict[str, list] = {
    "China-A Shanghai": ["2026-01-01", "2026-02-16", "2026-02-17", "2026-02-18",
                         "2026-02-19", "2026-02-20", "2026-04-06", "2026-05-01",
                         "2026-06-19", "2026-10-01", "2026-10-02", "2026-10-05",
                         "2026-10-06", "2026-10-07"],
    "China-A Shenzhen": ["2026-01-01", "2026-02-16", "2026-02-17", "2026-02-18",
                         "2026-02-19", "2026-02-20", "2026-04-06", "2026-05-01",
                         "2026-06-19", "2026-10-01", "2026-10-02", "2026-10-05",
                         "2026-10-06", "2026-10-07"],
    "Hong Kong (HKEX)": ["2026-01-01", "2026-02-17", "2026-02-18", "2026-02-19",
                         "2026-04-03", "2026-04-06", "2026-04-07", "2026-05-01",
                         "2026-05-25", "2026-07-01", "2026-10-01", "2026-10-26",
                         "2026-12-25"],
    "Taiwan (TWSE)":    ["2026-01-01", "2026-02-13", "2026-02-16", "2026-02-17",
                         "2026-02-18", "2026-02-19", "2026-02-20", "2026-02-27",
                         "2026-04-03", "2026-04-06", "2026-05-01", "2026-06-19",
                         "2026-09-25", "2026-10-09"],
    "Japan (TSE)":      ["2026-01-01", "2026-01-02", "2026-01-12", "2026-02-11",
                         "2026-02-23", "2026-03-20", "2026-04-29", "2026-05-04",
                         "2026-05-05", "2026-05-06", "2026-07-20", "2026-08-11",
                         "2026-09-21", "2026-09-22", "2026-10-12", "2026-11-03",
                         "2026-11-23", "2026-12-31"],
    "Korea (KRX)":      ["2026-01-01", "2026-02-16", "2026-02-17", "2026-02-18",
                         "2026-03-02", "2026-05-01", "2026-05-05", "2026-05-25",
                         "2026-06-06", "2026-08-17", "2026-09-24", "2026-09-25",
                         "2026-10-05", "2026-10-09", "2026-12-25", "2026-12-31"],
    "Singapore (SGX)":  ["2026-01-01", "2026-02-17", "2026-02-18", "2026-04-03",
                         "2026-05-01", "2026-05-27", "2026-06-16", "2026-08-10",
                         "2026-11-10", "2026-12-25"],
}

FX_NOTES = [
    {"Market": "Taiwan (TWSE)", "Ccy": "TWD",
     "Note": "Restricted — onshore FX only (or NDF); confirm onshore cutoff "
             "same-day; FINI pre-funding considerations."},
    {"Market": "Korea (KRX)", "Ccy": "KRW",
     "Note": "Restricted — onshore deliverable (extended won hours since "
             "2024) or NDF; registration (IRC) required."},
    {"Market": "India (NSE)", "Ccy": "INR",
     "Note": "Restricted — onshore via custodian, T+1 funding pressure; NDF "
             "offshore."},
    {"Market": "China-A Shanghai", "Ccy": "CNY/CNH",
     "Note": "Connect trades settle CNH; onshore CNY via QFI only."},
    {"Market": "Japan (TSE)", "Ccy": "JPY", "Note": "Deliverable, deep."},
    {"Market": "Hong Kong (HKEX)", "Ccy": "HKD", "Note": "Deliverable, pegged."},
]


def _holidays(market: str) -> set:
    return {pd.Timestamp(d).date() for d in HOLIDAYS_2026.get(market, [])}


def settlement_date_holiday_aware(market: str, trade_date: _dt.date) -> dict:
    """T+n skipping weekends AND known exchange holidays; reports which
    holidays pushed the date vs the naive calc."""
    n = MARKET_REG.get(market, {}).get("settle", 2)
    hols = _holidays(market)
    d, skipped = trade_date, []
    k = n
    while k > 0:
        d += _dt.timedelta(days=1)
        if d.weekday() >= 5:
            continue
        if d in hols:
            skipped.append(str(d))
            continue
        k -= 1
    return {"settles": d, "holidays_skipped": skipped,
            "note": ("" if not skipped else
                     f"pushed past {len(skipped)} holiday(s): "
                     f"{', '.join(skipped)} — fund accordingly. ")
            + "2026 approximate calendar — verify."}


def closure_warnings(markets, today: _dt.date, horizon: int = 5) -> list:
    """Which of the program's markets are closed within the next `horizon`
    calendar days — residual roll plans and settlement chains break here."""
    out = []
    for m in sorted(set(markets)):
        hols = _holidays(m)
        for k in range(horizon + 1):
            d = today + _dt.timedelta(days=k)
            if d in hols:
                when = ("TODAY" if k == 0 else "tomorrow" if k == 1
                        else f"in {k}d")
                out.append(f"{m} closed {when} ({d}) — residuals roll "
                           "further; settlement chain shifts.")
    return out


# ── A10: crossing / internal netting detector ──────────────────────────────

CROSSING_RULES = {
    "Japan (TSE)": "ToSTNeT off-auction crossing available — standard route.",
    "Hong Kong (HKEX)": "Direct-business (off-exchange) cross permitted; "
                        "report to HKEX within 15 min.",
    "Taiwan (TWSE)": "Exchange-centric: use block-trade session / "
                     "after-hours fixed-price; no free OTC cross.",
    "China-A Shanghai": "NO off-exchange crossing — exchange block platform "
                        "only, size/price constraints.",
    "China-A Shenzhen": "NO off-exchange crossing — exchange block platform "
                        "only.",
    "Korea (KRX)": "KRX block-deal mechanism; pre-arranged crosses must go "
                   "through it.",
    "Singapore (SGX)": "Married deals permitted with reporting.",
    "US": "Broker cross permitted (ATS/internalization) with trade "
          "reporting; Reg NMS applies.",
    "Australia (ASX)": "Block special-crossing thresholds by liquidity tier.",
}


def crossing_report(blotter: pd.DataFrame,
                    half_spread_bps: float = 5.0) -> dict:
    """Find internal offsetting flow across clients: same ticker, opposite
    sides, different clients -> crossable = min(buy, sell) shares. Both
    clients save ~the half-spread. Columns: client, ticker, market, side,
    shares [, price]."""
    rows = []
    for (tkr, mkt), g in blotter.groupby(["ticker", "market"]):
        b = g[g["side"] == "Buy"]
        s = g[g["side"] == "Sell"]
        if b.empty or s.empty:
            continue
        if set(b["client"]) == set(s["client"]) and len(set(b["client"])) == 1:
            continue                     # same single client both ways — not a cross
        x = float(min(b["shares"].sum(), s["shares"].sum()))
        px = float(g["price"].iloc[0]) if "price" in g.columns else np.nan
        save = (x * px * half_spread_bps / 1e4 * 2
                if np.isfinite(px) else np.nan)   # both sides save half-spread
        rows.append({"ticker": tkr, "market": mkt,
                     "crossable_shares": x,
                     "buy_clients": ",".join(sorted(set(b["client"]))),
                     "sell_clients": ",".join(sorted(set(s["client"]))),
                     "est_spread_saved_usd": (round(save, 0)
                                              if np.isfinite(save) else None),
                     "mechanism": CROSSING_RULES.get(mkt, "verify local rules")})
    df = pd.DataFrame(rows)
    return {"crosses": df, "n": int(len(df)),
            "note": "Client-consent + best-execution obligations apply to "
                    "every cross; mechanism column gives the compliant "
                    "route per market. Agency crosses only — no principal."}


# ── A11: two-sided exposure scheduler ──────────────────────────────────────

def exposure_schedule(basket: pd.DataFrame, n_waves: int = 6,
                      band_frac: float = 0.10,
                      front_load: dict = None) -> dict:
    """Two-sided wave scheduling: urgency vs funding.

    The basket's TERMINAL net (buys - sells) is structural — an FX/funding
    fact no schedule changes. What scheduling controls is the PATH: how far
    the running net strays from the pro-rata structural line. A dealer
    front-loads the urgent side (default: buys at 1.5x pro-rata speed —
    adverse-selection risk sits on the demand side); unconstrained, that
    walks the funding line away from plan. This scheduler throttles
    whichever side runs ahead so the running net stays within
    +/- band_frac x gross of the structural line, and reports what the
    unthrottled front-loaded path would have done.

    Columns: side, shares, price. front_load: per-side speed multiple.
    """
    fl = {"Buy": 1.5, "Sell": 1.0}
    fl.update(front_load or {})
    b = basket.copy()
    b["notional"] = b["shares"] * b["price"]
    buy_n = float(b.loc[b.side == "Buy", "notional"].sum())
    sell_n = float(b.loc[b.side == "Sell", "notional"].sum())
    gross = buy_n + sell_n
    if gross <= 0:
        return {"available": False, "reason": "empty basket"}
    band = band_frac * gross
    terminal = buy_n - sell_n
    per = 1.0 / n_waves

    def run(throttled: bool):
        cum_b = cum_s = 0.0
        rows, max_dev = [], 0.0
        for w in range(1, n_waves + 1):
            target = terminal * w / n_waves          # structural line
            tb = min(buy_n * per * fl["Buy"], buy_n - cum_b)
            ts = min(sell_n * per * fl["Sell"], sell_n - cum_s)
            if throttled:
                # pull the side running ahead back toward the band
                dev = (cum_b + tb) - (cum_s + ts) - target
                if dev > band:
                    tb = max(0.0, tb - (dev - band))
                elif dev < -band:
                    ts = max(0.0, ts - (-dev - band))
            if w == n_waves:                          # completion wave
                tb, ts = buy_n - cum_b, sell_n - cum_s
            cum_b += tb
            cum_s += ts
            dev = cum_b - cum_s - target
            max_dev = max(max_dev, abs(dev))
            rows.append({"wave": w, "buy_notional": round(tb, 0),
                         "sell_notional": round(ts, 0),
                         "cum_net": round(cum_b - cum_s, 0),
                         "dev_from_structural": round(dev, 0)})
        return pd.DataFrame(rows), max_dev

    sched, dev_sched = run(throttled=True)
    _, dev_naive = run(throttled=False)
    return {"available": True, "schedule": sched,
            "gross_notional": round(gross, 0),
            "terminal_net": round(terminal, 0),
            "band_usd": round(band, 0),
            "max_dev_scheduled": round(dev_sched, 0),
            "max_dev_frontloaded": round(dev_naive, 0),
            "note": (f"Terminal net {terminal:+,.0f} is structural (FX/"
                     "funding fact). Scheduling holds the PATH within "
                     f"+/-{band_frac:.0%} of gross around the structural "
                     f"line (max deviation {dev_sched:,.0f} vs "
                     f"{dev_naive:,.0f} if the front-loaded urgency ran "
                     "unthrottled). Completion wave forces both sides "
                     "done; participation/impact caps apply on top.")}
