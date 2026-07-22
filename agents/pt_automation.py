"""Desk automations — the concrete answers to "what would you automate if
you joined the desk?", each implemented, not just proposed.

A1  preopen_pack        T-1/pre-open basket pack: lot-normalized shares,
                        compliance pre-flight, %ADV + capacity RAG, explicit
                        costs, settlement dates, side/notional imbalance,
                        auction cutoffs — one text pack to the sales trader
                        before the open.
A2  alert_scan          intraday alerting on STATE TRANSITIONS (limit level
                        escalations, cutoff T-15 with residual, run-rate
                        collapse) — fires once per transition, not every
                        refresh; acknowledgments append to a JSON log with
                        the rules version (audit trail by-product).
A3  eod_client_summary  end-of-day client email draft: per-market fills,
                        residual roll plan, notable events, settlement
                        calendar — dealer edits 10%, sales trader sends.
A4  classify_breaks     recon break classifier: auto-clears within
                        tolerance, classes the rest (QTY/PRICE/MISSING) with
                        a suggested action — humans keep the ambiguous tail.
A5  event_radar         index-event radar over the basket: names inside a
                        provider review window (offline cadence rules from
                        Agent 12), with observed event-day volume multiples
                        from the event library when available.
A6  rules_version       (in pt_dealer) versioned rule tables stamped into
                        every audit artifact.

Everything is offline and injectable — same testability contract as the
rest of the platform.
"""
from __future__ import annotations

import datetime as _dt
import json
from pathlib import Path

import numpy as np
import pandas as pd

from agents.explicit_costs import get_explicit_costs
from agents.program_trading import lot_check, short_check, settlement_date
from agents.pt_dealer import (attention_queue, auction_countdown,
                              limit_proximity, rules_version)

DEFAULT_ALERT_LOG = (Path(__file__).resolve().parent.parent / "data"
                     / "alert_log.json")
CAP_RATE = 0.15                      # participation for capacity days
RUNRATE_ALERT = 0.6
CUTOFF_ALERT_MIN = 15.0


# ── A1: pre-open basket pack ───────────────────────────────────────────────

def preopen_pack(basket: pd.DataFrame, trade_date: _dt.date = None,
                 now_utc: _dt.datetime = None) -> dict:
    """Basket columns: ticker, market, side, shares, prev_close
    [, adv_shares, locate_confirmed]. Works from the client file + T-1
    reference data — no live fetch needed pre-open."""
    trade_date = trade_date or _dt.date.today()
    rows, notional_by_side = [], {"Buy": 0.0, "Sell": 0.0}
    for _, r in basket.iterrows():
        mkt, side = r["market"], str(r["side"]).capitalize()
        shares = float(r.get("shares", 0) or 0)
        lc = lot_check(mkt, shares)
        sc = short_check(mkt, side, bool(r.get("locate_confirmed", False)))
        adv = float(r.get("adv_shares", np.nan))
        pct = shares / adv * 100 if adv and np.isfinite(adv) and adv > 0 else np.nan
        days = (shares / (adv * CAP_RATE)
                if adv and np.isfinite(adv) and adv > 0 else np.nan)
        rag = ("n/a" if not np.isfinite(days) else
               "GREEN" if days <= 1 else "RED" if days > 3 else "AMBER")
        notional = shares * float(r.get("prev_close", 0) or 0)
        notional_by_side[side] = notional_by_side.get(side, 0.0) + notional
        rows.append({"ticker": r["ticker"], "market": mkt, "side": side,
                     "shares": shares, "lot_rounded": lc["rounded"],
                     "odd_lot": lc["odd"], "pct_adv": None if pd.isna(pct)
                     else round(pct, 1), "capacity_days": None
                     if pd.isna(days) else round(days, 2), "flag": rag,
                     "explicit_bps": get_explicit_costs(mkt).total_bps(side),
                     "settles": str(settlement_date(mkt, trade_date)),
                     "short": sc["level"] if sc["level"] != "none" else "",
                     "notes": " | ".join(n for n in (
                         lc["note"] if not lc["ok"] else "",
                         sc["note"] if sc["level"] in ("WARN", "BLOCK")
                         else "") if n)})
    per_name = pd.DataFrame(rows)
    buy_n, sell_n = notional_by_side.get("Buy", 0), notional_by_side.get("Sell", 0)
    gross = buy_n + sell_n
    imb = (buy_n - sell_n) / gross if gross > 0 else 0.0
    cuts = auction_countdown(basket["market"].unique(), now_utc)
    pack = {"trade_date": str(trade_date), "n_names": int(len(basket)),
            "markets": sorted(basket["market"].unique().tolist()),
            "gross_notional": round(gross, 0),
            "net_imbalance_frac": round(float(imb), 3),
            "n_blocked_shorts": int((per_name["short"] == "BLOCK").sum()),
            "n_odd_lots": int((per_name["odd_lot"] > 0).sum()),
            "per_name": per_name, "auction_cutoffs": cuts,
            "rules_version": rules_version()}
    pack["text"] = _preopen_text(pack)
    return pack


def _preopen_text(p: dict) -> str:
    L = ["=" * 66, f"PRE-OPEN BASKET PACK — {p['trade_date']}  "
         f"(rules {p['rules_version']})", "=" * 66,
         f"{p['n_names']} names | {len(p['markets'])} markets | gross "
         f"~{p['gross_notional']:,.0f} | net imbalance "
         f"{p['net_imbalance_frac']:+.1%} "
         + ("(buy-heavy)" if p["net_imbalance_frac"] > 0.1 else
            "(sell-heavy)" if p["net_imbalance_frac"] < -0.1 else "(balanced)")]
    if p["n_blocked_shorts"]:
        L.append(f"⛔ {p['n_blocked_shorts']} short(s) BLOCKED — resolve "
                 "before the open (swap/synthetic or drop).")
    if p["n_odd_lots"]:
        L.append(f"⚠️ {p['n_odd_lots']} name(s) need lot rounding — "
                 "rounded shares in the table; route odd lots separately.")
    hard = p["per_name"][p["per_name"]["flag"].isin(["RED", "AMBER"])]
    if len(hard):
        L.append(f"Hardest names ({len(hard)}): "
                 + ", ".join(f"{r.ticker} ({r.capacity_days}d)"
                             for r in hard.itertuples()))
    L.append("-" * 66)
    L.append("Close-auction cutoffs (local): "
             + "; ".join(f"{r['Market']} {r['Cutoff (local)']}"
                         for _, r in p["auction_cutoffs"].iterrows()))
    L.append("Static rule tables — verify against today's exchange notices.")
    return "\n".join(L)


# ── A2: intraday alert engine (transition-based) ───────────────────────────

def alert_scan(basket: pd.DataFrame, prev_state: dict = None,
               now_utc: _dt.datetime = None):
    """Returns (alerts list, new_state). Fires only on TRANSITIONS so a
    30-second refresh loop doesn't re-page the dealer for the same
    condition. State keys per ticker: limit level, cutoff-alerted flag,
    runrate-alerted flag."""
    now_utc = now_utc or _dt.datetime.now(_dt.timezone.utc).replace(tzinfo=None)
    prev_state = prev_state or {}
    cuts = {r["Market"]: r["Mins to cutoff"]
            for _, r in auction_countdown(basket["market"].unique(),
                                          now_utc).iterrows()}
    alerts, state = [], {}
    order = {"none": 0, "n/a": 0, "WATCH": 1, "ALERT": 2, "LOCKED": 3}
    for _, r in basket.iterrows():
        t = r["ticker"]
        ps = prev_state.get(t, {})
        lp = limit_proximity(r["market"], r["prev_close"], r["last_price"])
        lvl = lp["level"]
        if order.get(lvl, 0) > order.get(ps.get("limit", "none"), 0) \
                and lvl in ("WATCH", "ALERT", "LOCKED"):
            alerts.append(_alert(t, r["market"], "LIMIT", lvl, now_utc,
                                 f"{lvl}: {lp['used_frac']:.0%} of "
                                 f"±{lp['band_pct']}% band ({lp['side']})"))
        mins = cuts.get(r["market"], np.inf)
        residual = 1.0 - float(r["filled_frac"])
        cut_hit = 0 <= mins < CUTOFF_ALERT_MIN and residual > 0.05
        if cut_hit and not ps.get("cutoff_alerted"):
            alerts.append(_alert(t, r["market"], "CUTOFF", "ALERT", now_utc,
                                 f"close cutoff in {mins:.0f}m with "
                                 f"{residual:.0%} unfilled — submit MOC or "
                                 "accept residual"))
        rr = float(r.get("runrate_ratio", 1.0))
        rr_hit = rr < RUNRATE_ALERT
        if rr_hit and not ps.get("runrate_alerted"):
            alerts.append(_alert(t, r["market"], "LIQUIDITY", "WARN", now_utc,
                                 f"tape at {rr:.0%} of expected volume — "
                                 "schedule at risk"))
        state[t] = {"limit": lvl if lvl in ("WATCH", "ALERT", "LOCKED")
                    else "none",
                    "cutoff_alerted": bool(cut_hit or ps.get("cutoff_alerted")),
                    "runrate_alerted": bool(rr_hit or ps.get("runrate_alerted"))}
    return alerts, state


def _alert(ticker, market, kind, severity, now_utc, message) -> dict:
    return {"ts_utc": now_utc.isoformat(timespec="seconds"), "ticker": ticker,
            "market": market, "kind": kind, "severity": severity,
            "message": message, "acknowledged_by": "",
            "rules_version": rules_version()}


def acknowledge(alerts: list, who: str, note: str = "",
                path: Path = DEFAULT_ALERT_LOG) -> int:
    """Acknowledged alerts land in the audit trail — the acknowledgment IS
    the record that the dealer saw it."""
    for a in alerts:
        a["acknowledged_by"] = who
        a["ack_note"] = note
    path = Path(path)
    log = []
    if path.exists():
        try:
            log = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            log = []
    log.extend(alerts)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(log, indent=1), encoding="utf-8")
    return len(alerts)


# ── A3: EOD client summary draft ───────────────────────────────────────────

def eod_client_summary(basket: pd.DataFrame, program_id: str,
                       trade_date: _dt.date = None,
                       events: list = None) -> str:
    """Email-style draft. Basket may carry slippage_bps (realized vs agreed
    benchmark) — reported when present, never invented."""
    trade_date = trade_date or _dt.date.today()
    L = [f"Subject: {program_id} — execution summary {trade_date}", "",
         "Hi team,", "",
         f"Summary for today's program ({len(basket)} names, "
         f"{basket['market'].nunique()} markets):", ""]
    for mkt, g in basket.groupby("market"):
        filled = (g["filled_frac"] * g["shares"]).sum() / g["shares"].sum()
        line = f"• {mkt}: {filled:.0%} complete across {len(g)} name(s)"
        if "slippage_bps" in g.columns and g["slippage_bps"].notna().any():
            line += (f", avg slippage {g['slippage_bps'].mean():+.1f} bps "
                     "vs agreed benchmark")
        resid = g[g["filled_frac"] < 0.995]
        if len(resid):
            nxt = trade_date + _dt.timedelta(days=1)
            while nxt.weekday() >= 5:
                nxt += _dt.timedelta(days=1)
            line += (f". Residuals on {len(resid)} name(s) roll to {nxt} "
                     "opening rotation")
        line += f". Settles {settlement_date(mkt, trade_date)}."
        L.append(line)
    notable = []
    for _, r in basket.iterrows():
        lp = limit_proximity(r["market"], r["prev_close"], r["last_price"])
        if lp["level"] in ("ALERT", "LOCKED"):
            notable.append(f"{r['ticker']} traded to {lp['used_frac']:.0%} "
                           f"of its daily band ({lp['side']})")
        sc = short_check(r["market"], r["side"],
                         bool(r.get("locate_confirmed", False)))
        if sc["level"] == "BLOCK":
            notable.append(f"{r['ticker']} sell not executed — short "
                           "unavailable in this market (flagged pre-open)")
    for e in (events or []):
        notable.append(str(e))
    if notable:
        L += ["", "Notable:"] + [f"  - {n}" for n in notable]
    L += ["", "Full audit pack attached (timestamped compliance checks, "
          f"rules {rules_version()}).", "", "Best,", "PT Desk"]
    return "\n".join(L)


# ── A4: recon break classifier ─────────────────────────────────────────────

BREAK_ACTIONS = {
    "AUTO_CLEAR": "within tolerance — cleared automatically",
    "QTY_BREAK": "compare fill-by-fill; check partial-fill bust/correct",
    "PRICE_BREAK": "check avg-price calc, fees-in-price convention, FX rate",
    "MISSING_STREET": "street unbooked — chase broker confirm before cutoff",
    "MISSING_OURS": "our side unbooked — check order-management late fills",
}


def classify_breaks(ours: pd.DataFrame, street: pd.DataFrame,
                    qty_tol: float = 0.0, px_tol_bps: float = 1.0):
    """Merge our blotter vs street confirms on (ticker, market); classify
    every discrepancy with a suggested action. Columns: ticker, market,
    shares, avg_price. Returns (breaks_df, summary dict)."""
    m = ours.merge(street, on=["ticker", "market"], how="outer",
                   suffixes=("_ours", "_street"), indicator=True)
    rows = []
    for _, r in m.iterrows():
        if r["_merge"] == "left_only":
            cls = "MISSING_STREET"
        elif r["_merge"] == "right_only":
            cls = "MISSING_OURS"
        else:
            dq = float(r["shares_ours"]) - float(r["shares_street"])
            dpx = (abs(r["avg_price_ours"] - r["avg_price_street"])
                   / r["avg_price_street"] * 1e4)
            if abs(dq) > qty_tol:
                cls = "QTY_BREAK"
            elif dpx > px_tol_bps:
                cls = "PRICE_BREAK"
            else:
                cls = "AUTO_CLEAR"
        rows.append({"ticker": r["ticker"], "market": r["market"],
                     "class": cls, "action": BREAK_ACTIONS[cls],
                     "qty_diff": (None if r["_merge"] != "both" else
                                  float(r["shares_ours"] - r["shares_street"])),
                     "px_diff_bps": (None if r["_merge"] != "both" else
                                     round(float((r["avg_price_ours"]
                                                  - r["avg_price_street"])
                                                 / r["avg_price_street"] * 1e4), 2))})
    df = pd.DataFrame(rows)
    summary = df["class"].value_counts().to_dict()
    summary["needs_human"] = int(len(df[df["class"] != "AUTO_CLEAR"]))
    return df, summary


# ── A5: index-event radar ──────────────────────────────────────────────────

def event_radar(basket: pd.DataFrame, today: _dt.date = None,
                window_before: int = 10, window_after: int = 5) -> pd.DataFrame:
    """Which basket names sit inside a provider review window right now?
    Uses Agent 12's offline cadence rules (approximate dates, disclosed)
    plus the event library's observed close-volume multiples when it has
    enough history. Name-level membership needs the provider's announce-
    ment — this flags the WINDOW, the dealer confirms membership."""
    from agents.agent12_index_calendar import upcoming_reviews
    from agents.trader_view import library_stats
    today = today or _dt.date.today()
    revs = upcoming_reviews(today=today)
    lib = library_stats()
    mult = lib.get("median_t_day_volume_multiple")
    rows = []
    for rv in revs:
        eff = rv.get("effective") or rv.get("effective (approx)")
        if not eff:
            continue
        eff = pd.Timestamp(eff).date()
        d = (eff - today).days
        if -window_after <= d <= window_before:
            rows.append({"provider": rv.get("provider", "?"),
                         "effective": str(eff), "days_to_effective": d,
                         "basket_names_at_risk": int(len(basket)),
                         "observed_close_vol_multiple":
                             (round(mult, 1) if mult else "library empty — "
                              "1.4x disclosed placeholder"),
                         "note": rv.get("event", rv.get("note", ""))})
    df = pd.DataFrame(rows)
    if df.empty:
        return pd.DataFrame([{"provider": "—", "effective": "—",
                              "days_to_effective": "",
                              "basket_names_at_risk": 0,
                              "observed_close_vol_multiple": "",
                              "note": f"No provider review window within "
                                      f"-{window_after}/+{window_before} "
                                      f"days of {today}."}])
    return df.sort_values("days_to_effective").reset_index(drop=True)
