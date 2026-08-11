#!/usr/bin/env python3
"""Is anyone positioned for the Caliway deletion? The borrow says.

    py scripts\\tw_deletion_borrow.py

THE QUESTION, c-368 (Bill): the August call carries one border
deletion — Caliway (6919), 1.03x the floor, P(delete) 39%. A
hedge fund positioned for that trade is SHORT into the effective
day, expecting to cover into the trackers' forced selling. A
short needs a borrow, and TWSE publishes every listed name's
securities-lending balance daily (TWT93U). So the trade's
footprint, if it exists, is a RISING SBL balance into the review.

WHAT THIS MEASURES, AND WHAT IT CANNOT.

  * The SBL balance is shares out on loan — the stock of open
    borrow, not the day's shorting. It moves when new borrow is
    taken or returned.
  * It UNDERCOUNTS total short exposure: margin-account shorting
    (a different file) and any synthetic short via swaps or
    single-stock futures never touch the SBL balance. A flat
    balance therefore does not prove nobody is positioned — it
    proves the POSITIONING IS NOT VISIBLE in the one public
    channel that would show it.
  * Direction matters more than level: the level reflects
    long-standing lending programmes; the CHANGE into the review
    is the event signal.

READING (drafted for the page, numbers regenerate):
latest balance vs the trailing year's range, and the change over
the last 20 sessions. No verdict is rendered — the observation
is stated and the reader sizes it.
"""
from __future__ import annotations

import datetime as dt
import json
import pathlib
import statistics as stats

ROOT = pathlib.Path(__file__).resolve().parents[1]
SBL = ROOT / "data" / "sbl_history.json"
QUOTES = ROOT / "data" / "tw_history" / "quotes.json"
PROB = ROOT / "data" / "tw_add_probability.json"
OUT = ROOT / "data" / "tw_deletion_borrow.json"

CODE = "6919"
NAME = "Caliway Biopharmaceutical"
CHART_SESSIONS = 120     # what the page draws
CHANGE_SESSIONS = 20     # the "into the review" window
YEAR_SESSIONS = 250      # the percentile yardstick


def main():
    if not SBL.exists():
        raise SystemExit("missing sbl_history.json")
    sbl = json.loads(SBL.read_text(encoding="utf-8"))
    series = []
    for d in sorted(sbl):
        v = sbl[d].get(CODE)
        if v and v[1] is not None:
            series.append((d, float(v[1])))
    # c-370, Bill asked why the chart was flat at zero from
    # early 2025: those are REAL zeros on sparsely covered days —
    # Caliway had no securities lending at all until 2026-03-11
    # (first loan: 2,000 shares). The chart and the yardstick
    # therefore start where the LENDING HISTORY starts, and the
    # start date is recorded so the page can say it.
    first_nz = next((i for i, (_d, b) in enumerate(series)
                     if b and b > 0), None)
    if first_nz is None:
        raise SystemExit(f"{CODE} has no SBL lending history")
    lending_began = series[first_nz][0]
    series = series[first_nz:]
    if len(series) < 40:
        raise SystemExit(f"only {len(series)} sessions since "
                         f"lending began for {CODE}")

    bal = [b for _d, b in series]
    latest_d, latest = series[-1]
    yr = bal[-min(YEAR_SESSIONS, len(bal)):]
    below = sum(1 for b in yr if b <= latest)
    pctl = below / len(yr)
    chg = latest - bal[-1 - CHANGE_SESSIONS]
    chg_pct = chg / bal[-1 - CHANGE_SESSIONS] if \
        bal[-1 - CHANGE_SESSIONS] else None

    # scale: the name's ADV from the quotes harvest (volume is
    # field 0). The quotes file may trail the SBL file; the ADV
    # window is the last 60 covered quote sessions, stamped.
    adv, adv_to = None, None
    if QUOTES.exists():
        q = json.loads(QUOTES.read_text(encoding="utf-8"))
        vols = [(d, q[d][CODE][0]) for d in sorted(q)
                if CODE in q[d] and q[d][CODE][0]]
        if len(vols) >= 30:
            vols = vols[-60:]
            adv = stats.median(v for _d, v in vols)
            adv_to = vols[-1][0]

    pdel = None
    if PROB.exists():
        pr = json.loads(PROB.read_text(encoding="utf-8"))
        for r in pr.get("border_deletions", []):
            if r["code"] == CODE:
                pdel = r["p_delete"]

    out = {
        "_what": "SBL borrow balance in the border deletion "
                 "candidate — the public footprint a "
                 "pre-positioned short would leave",
        "generated": dt.datetime.now().isoformat(timespec="seconds"),
        "code": CODE, "name": NAME,
        "p_delete": pdel,
        "lending_began": lending_began,
        "peak_balance_shares": max(bal),
        "latest": {"date": latest_d, "balance_shares": latest,
                   "pctl_vs_lending_era": round(pctl, 3),
                   "era_sessions": len(yr),
                   "balance_x_adv": (round(latest / adv, 3)
                                     if adv else None)},
        "change": {"sessions": CHANGE_SESSIONS,
                   "shares": chg,
                   "pct": round(chg_pct, 4) if chg_pct is not None
                   else None},
        "adv": {"shares": adv, "to": adv_to,
                "source": "tw_history/quotes.json, median of "
                          "last 60 covered sessions"},
        "series": [{"d": d, "bal": b}
                   for d, b in series[-CHART_SESSIONS:]],
        "caveats": [
            "SBL balance only — margin-account shorts and "
            "synthetic shorts (swaps, futures) are invisible "
            "here, so a flat balance does not prove absence of "
            "positioning",
            "the balance is a stock of open borrow; the change "
            "into the review is the event signal, the level is "
            "mostly lending-programme history"],
    }
    OUT.write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(f"{CODE} {NAME}: balance {latest / 1e6:.2f}m sh "
          f"({pctl:.0%} of trailing yr) "
          f"chg {CHANGE_SESSIONS}s {chg / 1e6:+.2f}m "
          f"({(chg_pct or 0):+.1%})  "
          f"x ADV {(latest / adv if adv else float('nan')):.2f}")
    print(f"wrote {OUT.name}")


if __name__ == "__main__":
    main()
