"""Step-2 window planner — announcement -> effective day (session 8g).

Implements the two AI-implementable workstreams of lifecycle Step 2
(docs/INDEX_REBALANCE_TRADE_LIFECYCLE.md):

    2.2 Liquidity & risk analysis per name  -> liquidity_risk_sheet()
    2.3 Execution planning & discretion     -> start_schedule() +
                                               discretion_decision() +
                                               build_window_plan()

Design rules carried over from the rest of the project: every output
is deterministic and every decision ships WITH its documented
rationale (the best-ex evidence is a BY-PRODUCT of deciding, not
paperwork after it). Data honesty: borrow utilization only where SBL
quota data exists (TWT93U); halt risk is a stated proxy; T-multiples
come from the measured event library, never guessed.
"""
from __future__ import annotations

import math
import re

import numpy as np
import pandas as pd

# Bucket thresholds — same convention as review_engine.build_calls.
BUCKET_MOC_MAX = 1.0        # < 1 ADV-day  -> MOC
BUCKET_WORK_MAX = 3.0       # < 3 ADV-days -> WORK+MOC

# Measured T-day auction share of event-day volume (event library,
# TW MSCI events): the close prints roughly a third of the day.
DEFAULT_AUCTION_SHARE = 0.30

# SBL quota utilization above this = borrow constrained.
BORROW_TIGHT_UTIL = 0.80


def bucket(adv_days: float) -> str:
    return ("MOC" if adv_days < BUCKET_MOC_MAX else
            "WORK+MOC" if adv_days < BUCKET_WORK_MAX else "MULTI-DAY")


def sbl_utilization(twt93u: pd.DataFrame) -> dict[str, float]:
    """Borrow-capacity read from a TWT93U day frame. The file's quota
    column is the REMAINING next-day SBL sell quota, so the honest
    capacity proxy is balance / (balance + remaining quota) — the
    fraction of implied SBL capacity already in use. Taiwan only —
    the one market whose public file carries quota. Returns
    {ticker: utilization 0..1}."""
    out = {}
    for _, r in twt93u.iterrows():
        q, b = r.get("sbl_quota"), r.get("sbl_bal")
        if (q is not None and b is not None and not np.isnan(q)
                and not np.isnan(b) and (q + b) > 0):
            out[str(r["ticker"])] = round(float(b) / float(b + q), 3)
    return out


def liquidity_risk_sheet(basket: pd.DataFrame,
                         t_mult_med: float, t_mult_max: float,
                         auction_share: float = DEFAULT_AUCTION_SHARE,
                         sbl_util: dict[str, float] | None = None,
                         halt_names: set[str] | None = None
                         ) -> pd.DataFrame:
    """2.2 — the per-name liquidity & risk table.

    basket columns: ticker, market, side (Buy/Sell), qty_shares,
    adv_shares. Band % comes from asian_markets.price_limit_pct.
    Outputs, per line: ADV-days, expected T-day volume (median and
    max multiples), expected auction volume, the order's auction
    footprint %, limit-band risk, borrow status (where quota data
    exists), halt proxy, and the bucket that drives everything
    downstream."""
    from agents.asian_markets import price_limit_pct
    rows = []
    for _, r in basket.iterrows():
        adv_days = (r["qty_shares"] / r["adv_shares"]
                    if r["adv_shares"] else np.nan)
        exp_t_vol = r["adv_shares"] * t_mult_med
        exp_auct = exp_t_vol * auction_share
        foot = 100 * r["qty_shares"] / exp_auct if exp_auct else np.nan
        band = price_limit_pct(r["market"])
        limit_risk = ("-" if band is None else
                      f"LOCK RISK (±{band:.0f}%)" if band <= 10 else
                      f"WATCH (±{band:.0f}%)")
        base = str(r["ticker"]).split(".")[0]
        util = (sbl_util or {}).get(base)
        borrow = ("no quota data" if util is None else
                  f"TIGHT ({util:.0%} of implied capacity)"
                  if util >= BORROW_TIGHT_UTIL else f"ok ({util:.0%})")
        halted = base in (halt_names or set())
        rows.append({
            "ticker": r["ticker"], "market": r["market"],
            "side": r["side"], "adv_days": round(adv_days, 2),
            "exp_t_vol_mult": f"{t_mult_med:.0f}x (max {t_mult_max:.0f}x)",
            "auction_footprint_pct": round(foot, 1),
            "band_pct": band if band is not None else np.nan,
            "limit_risk": limit_risk,
            "borrow": borrow,
            "halt_flag": ("HALT/SUSPENSION WATCH" if halted else "-"),
            "bucket": bucket(adv_days),
        })
    return pd.DataFrame(rows)


def start_schedule(sheet: pd.DataFrame, eff_date: str,
                   participation_cap: float = 0.25,
                   today: str | None = None) -> pd.DataFrame:
    """2.3a — WHEN to start each MULTI-DAY name: working days needed
    = ceil(ADV-days / participation cap) with the final day being the
    auction leg on T; start date = effective date minus (days-1)
    business days. A start date at or before 'today' flags LATE
    START — the escalation trigger, not a silent slip."""
    eff = pd.Timestamp(eff_date)
    now = pd.Timestamp(today) if today else pd.Timestamp.today()
    rows = []
    for _, r in sheet.iterrows():
        if r["bucket"] != "MULTI-DAY":
            rows.append({"ticker": r["ticker"], "bucket": r["bucket"],
                         "days_needed": 1, "start_date": "T",
                         "status": "auction-window name"})
            continue
        days = math.ceil(r["adv_days"] / participation_cap)
        start = eff - pd.tseries.offsets.BusinessDay(days - 1)
        late = start.normalize() <= now.normalize()
        rows.append({
            "ticker": r["ticker"], "bucket": r["bucket"],
            "days_needed": days,
            "start_date": str(start.date()),
            "status": ("LATE START — escalate: cap must rise or "
                       "completion slips past T" if late
                       else f"start {str(start.date())} at "
                            f"{participation_cap:.0%} participation"),
        })
    return pd.DataFrame(rows)


def _parse_crowding(label: str | None) -> tuple[str, bool]:
    """'HIGH (+53%/30obs); EXITING (-43% off peak)' -> ('HIGH', True).
    None/no data -> ('NO DATA', False)."""
    if not label:
        return "NO DATA", False
    m = re.match(r"(HIGH|MED|LOW)", label)
    return (m.group(1) if m else "NO DATA"), "EXITING" in label


def discretion_decision(side: str, crowding_label: str | None,
                        envelope_pct: float) -> dict:
    """2.3b — pre-position vs wait, decided BY the crowding read, with
    the best-ex rationale written as a by-product.

    The logic (from the measured event studies):
    - Crowded DELETE: the street already sold it — pressure is part-
      spent and the covering bounce is bigger. WORK it ahead within
      the envelope; don't donate the close to the covering crowd.
    - Uncrowded DELETE: pressure arrives AT the print. Wait; take the
      benchmark close (front-running a clean close adds impact and
      tracking for nothing).
    - Crowded ADD: the jump is already partly priced (CONSENSUS).
      Work into the close; pre-positioning now pays the crowd's mark.
    - Uncrowded ADD (UNPRICED): the close will jump — pre-position
      within the envelope to capture part of the move for the client.
    - EXITING tag flips the crowded read toward its uncrowded logic —
      the crowd is leaving before T (stock, not flow).
    - No envelope -> MOC only, whatever the color: discretion was not
      granted, so none is exercised (that IS best-ex here).
    """
    band, exiting = _parse_crowding(crowding_label)
    ev = f"evidence: crowding read '{crowding_label or 'no data'}'"
    if envelope_pct <= 0:
        return {"decision": "MOC ONLY",
                "rationale": "no discretion envelope granted — "
                             "benchmark print is the mandate; " + ev}
    eff_band = band
    if exiting and band in ("HIGH", "MED"):
        eff_band = "LOW"
        ev += " — EXITING tag: crowd leaving pre-T, treated as uncrowded"
    if side == "Sell":
        if eff_band == "HIGH":
            d = (f"WORK AHEAD up to {envelope_pct:.0f}% of order "
                 "pre-close")
            why = ("crowded delete: street pre-sold, pressure part-"
                   "spent, covering bounce enlarged — working ahead "
                   "beats donating the close to the covering crowd")
        elif eff_band == "MED":
            d = (f"WORK AHEAD up to {envelope_pct / 2:.0f}% "
                 "(half envelope)")
            why = "moderate crowding: split the difference, keep optionality"
        else:
            d = "WAIT — MOC the full order"
            why = ("uncrowded/unknown delete: pressure arrives at the "
                   "print; pre-trading a clean close adds impact and "
                   "tracking for nothing")
    else:  # Buy / add
        if eff_band == "HIGH":
            d = "WORK INTO CLOSE — no pre-positioning"
            why = ("crowded add: jump already partly priced "
                   "(consensus); pre-positioning pays the crowd's mark")
        elif eff_band == "MED":
            d = (f"PRE-POSITION up to {envelope_pct / 2:.0f}% "
                 "(half envelope)")
            why = "partial positioning seen: capture part of the jump, capped"
        else:
            d = (f"PRE-POSITION up to {envelope_pct:.0f}% within "
                 "envelope")
            why = ("uncrowded add (unpriced): the close will jump; the "
                   "envelope exists to capture part of that move")
    return {"decision": d, "rationale": f"{why}; {ev}"}


def build_window_plan(basket: pd.DataFrame, eff_date: str,
                      t_mult_med: float, t_mult_max: float,
                      crowding_map: dict[str, str] | None = None,
                      envelopes: dict[str, float] | None = None,
                      sbl_util: dict[str, float] | None = None,
                      halt_names: set[str] | None = None,
                      participation_cap: float = 0.25,
                      today: str | None = None) -> dict:
    """2.2 + 2.3 in one pass: the sheet, the start schedule, and a
    documented discretion decision per name. envelopes: {ticker: %
    of order the client allows worked away from the close}; missing
    ticker = no envelope."""
    sheet = liquidity_risk_sheet(basket, t_mult_med, t_mult_max,
                                 sbl_util=sbl_util,
                                 halt_names=halt_names)
    sched = start_schedule(sheet, eff_date,
                           participation_cap=participation_cap,
                           today=today)
    decisions = []
    for _, r in sheet.iterrows():
        base = str(r["ticker"]).split(".")[0]
        dec = discretion_decision(
            r["side"], (crowding_map or {}).get(base),
            (envelopes or {}).get(r["ticker"], 0.0))
        decisions.append({"ticker": r["ticker"], "side": r["side"],
                          **dec})
    return {"sheet": sheet, "schedule": sched,
            "decisions": pd.DataFrame(decisions),
            "eff_date": eff_date}


def indicative_read(expected_mult: float, indicative_mult: float,
                    side: str = "Sell",
                    envelope_remaining_pct: float = 0.0) -> dict:
    """Step-3 close-sequence rule (3.3): indicative auction volume vs
    the expected T-multiple -> framed recommendation for the day's
    one real-time decision. Deterministic; the dealer decides."""
    if expected_mult <= 0:
        return {"read": "NO EXPECTATION", "action": "hold plan",
                "rationale": "no measured multiple to compare against"}
    ratio = indicative_mult / expected_mult
    if ratio < 0.6:
        read = f"THIN ({indicative_mult:.0f}x vs {expected_mult:.0f}x expected)"
        action = ("retreat: hold back up to "
                  f"{envelope_remaining_pct:.0f}% for the T+1 plan"
                  if envelope_remaining_pct > 0 else
                  "no envelope left — take the print, flag violence "
                  "risk to client")
        why = ("crowd did not show; the print will be violent — "
               "footprint in a thin auction is expensive")
    elif ratio > 1.3:
        read = f"RICH ({indicative_mult:.0f}x vs {expected_mult:.0f}x)"
        action = "size UP into the close within envelope"
        why = ("the crowd showed up; liquidity is at the print — "
               "this is the cheapest moment to complete")
    else:
        read = f"IN LINE ({indicative_mult:.0f}x vs {expected_mult:.0f}x)"
        action = "execute the plan unchanged"
        why = "auction confirming the T-multiple assumption"
    return {"read": read, "action": action, "rationale": why,
            "ratio": round(ratio, 2)}


def render_window_plan(plan: dict, title: str, as_of: str,
                       notes: str = "") -> str:
    L = [f"# {title}", f"*Generated {as_of} by agents/event_window.py "
         "— lifecycle Step 2 workstreams 2.2 + 2.3. Deterministic; "
         "every discretion decision ships with its best-ex "
         f"rationale. Effective date {plan['eff_date']}.*", ""]
    L.append("## 2.2 Liquidity & risk per name\n")
    L.append(plan["sheet"].to_markdown(index=False))
    L.append("\n## 2.3a Start schedule (multi-day names)\n")
    L.append(plan["schedule"].to_markdown(index=False))
    L.append("\n## 2.3b Discretion decisions (documented)\n")
    for _, r in plan["decisions"].iterrows():
        L.append(f"- **{r['ticker']}** ({r['side']}): "
                 f"{r['decision']}\n  - {r['rationale']}")
    if notes:
        L.append(f"\n## Notes\n\n{notes}")
    return "\n".join(L) + "\n"
