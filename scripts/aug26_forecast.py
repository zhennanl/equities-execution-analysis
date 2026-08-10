#!/usr/bin/env python3
"""Aug-2026 Taiwan: current positioning in the called names, and the
historical ADD-event template measured on foreign flow.

    py scripts/aug26_forecast.py

WHAT THIS IS FOR. The case study measured what a Taiwan index event looks
like on average. This asks the forward question: where are the four names
we called ALREADY, with the announcement days away, and what does the
historical template say happens next.

WHY FOREIGN FLOW IS IN HERE NOW. The case study reported foreign net buy
as unavailable — that was wrong. It checked twse_institutional.json (22
days) and never found t86_history.json, which holds 2,815 non-empty
sessions from 2015 and, importantly, stores the source field count per
row and parses per layout. Spot-checking 112,600 rows against the correct
per-layout offsets returns zero mismatches, so the series is sound.

THE MEASUREMENT THAT MATTERS. Flow is expressed in DAYS OF ADV, never in
shares. A share count is not comparable across names, and the whole point
is to compare a NT$500 stock with a NT$40 one.

WHAT THIS CANNOT DO. It cannot tell you whether these four names are
actually in the list — that is the call, and the call carries its own
probability. Every number here is conditional on the name being added.
"""
from __future__ import annotations

import json
import statistics as st
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CALL = ROOT / "data" / "aug26_tw_call_v2.json"
OUT = ROOT / "data" / "aug26_forecast.json"

LOOK = 20            # sessions of "recent" positioning
PRE, POST = 20, 20   # event-study window either side


def _j(name):
    p = ROOT / "data" / name
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def px_series(code, cache):
    """[(date, close, volume)] ascending, missing bars dropped."""
    rows = cache.get(f"px|{code}") or []
    out = []
    for r in rows:
        c, v = r.get("close"), r.get("Trading_Volume")
        if c and v is not None:
            out.append((r["date"], float(c), float(v)))
    return sorted(out)


def t86_by_code():
    """{code: {YYYYMMDD: foreign_net_shares}} — 'f' is the foreign net,
    already parsed against the right layout for its era."""
    raw = _j("t86_history.json") or {}
    out = {}
    for day, rows in raw.items():
        for code, r in (rows or {}).items():
            f = r.get("f")
            if f is not None:
                out.setdefault(code, {})[day] = float(f)
    return out


def sbl_by_code():
    """{code: {YYYYMMDD: balance}} — element [1] is the balance, [0] is
    the day's new lending. Same convention as tw_case_study."""
    raw = _j("sbl_history.json") or {}
    out = {}
    for day, rows in (raw or {}).items():
        for code, v in (rows or {}).items():
            try:
                bal = float(v[1]) if isinstance(v, (list, tuple)) else float(v)
            except (TypeError, ValueError, IndexError):
                continue
            out.setdefault(code, {})[day] = bal
    return out


def pct(xs, p):
    xs = sorted(x for x in xs if x is not None)
    if not xs:
        return None
    i = (len(xs) - 1) * p
    lo = int(i)
    hi = min(lo + 1, len(xs) - 1)
    return xs[lo] + (xs[hi] - xs[lo]) * (i - lo)


def main():
    cache = _j("tw_vintage_cache.json") or {}
    twii = {k: float(v) for k, v in (_j("twii_daily.json") or {}).items()}
    call = json.loads(CALL.read_text(encoding="utf-8"))
    t86, sbl = t86_by_code(), sbl_by_code()

    # TAIEX keyed YYYY-MM-DD; flows keyed YYYYMMDD
    tw_dates = sorted(twii)
    out = {"_what": "Aug-2026 Taiwan forecast inputs",
           "review": call["review"], "declared": call["declared"],
           "names": {}, "history": {}}

    print(f"data currency: TAIEX -> {tw_dates[-1]}   "
          f"T86 -> {max(max(v) for v in t86.values())}   "
          f"SBL -> {max(max(v) for v in sbl.values())}")

    # ---- A. where the called names are RIGHT NOW -----------------------
    print("\nA. CURRENT POSITIONING (last "
          f"{LOOK} sessions, to each series' end)")
    print(f"  {'code':<6}{'excess':>9}{'vol/ADV':>9}"
          f"{'foreign':>10}{'borrow':>9}   note")
    for c in call["calls"]:
        code = str(c["code"])
        s = px_series(code, cache)
        rec = {"action": c["action"], "prob": c.get("prob"),
               "zone": c.get("zone")}
        if len(s) < LOOK + 60:
            out["names"][code] = {**rec, "available": False}
            print(f"  {code:<6}{'—':>9}{'—':>9}{'—':>10}{'—':>9}"
                  f"   no price history")
            continue
        win = s[-LOOK:]
        adv = st.mean(v for _d, _c, v in s[-LOOK - 60:-LOOK])
        # excess over TAIEX across the same span
        d0, d1 = win[0][0], win[-1][0]
        stock = win[-1][1] / win[0][1] - 1
        i0 = max([d for d in tw_dates if d <= d0], default=None)
        i1 = max([d for d in tw_dates if d <= d1], default=None)
        mkt = (twii[i1] / twii[i0] - 1) if i0 and i1 else 0.0
        excess = stock - mkt
        volx = st.mean(v for _d, _c, v in win) / adv if adv else None

        keys = [d.replace("-", "") for d, _c, _v in win]
        fser = t86.get(code, {})
        fnet = sum(fser.get(k, 0.0) for k in keys)
        f_adv = fnet / adv if adv else None
        bser = sbl.get(code, {})
        bk = [k for k in keys if k in bser]
        b_adv = ((bser[bk[-1]] - bser[bk[0]]) / adv
                 if len(bk) >= 2 and adv else None)

        rec.update({"available": True, "from": d0, "to": d1,
                    "excess_20d": excess, "vol_x_adv": volx,
                    "foreign_net_days_adv": f_adv,
                    "borrow_build_days_adv": b_adv,
                    "adv_shares": adv,
                    "in_t86": bool(fser), "in_sbl": bool(bser)})
        out["names"][code] = rec
        note = "" if fser else "not in T86 (TPEx-listed?)"
        print(f"  {code:<6}{excess:>+8.1%}{volx:>9.2f}"
              f"{(f'{f_adv:+.2f}' if f_adv is not None else '—'):>10}"
              f"{(f'{b_adv:+.2f}' if b_adv is not None else '—'):>9}"
              f"   {note}")

    # ---- B. the historical ADD template, on foreign flow ---------------
    # For every registry-dated Taiwan ADD, how much did foreigners buy
    # BEFORE the announcement, BETWEEN announcement and print, and ON the
    # print — each in days of that name's own pre-announcement ADV.
    wins = (_j("tw_event_windows.json") or {}).get("windows", {})
    legs = {"pre": [], "ann_to_eff": [], "eff_day": [], "post5": []}
    n_used = 0
    for v in wins.values():
        if v.get("action") != "ADD" or v.get("ann_src") != "registry":
            continue
        code = str(v["code"])
        s = px_series(code, cache)
        fser = t86.get(code)
        if not s or not fser or not v.get("eff"):
            continue
        dates = [d for d, _c, _v in s]
        if v["ann"] not in dates or v["eff"] not in dates:
            continue
        ia, ie = dates.index(v["ann"]), dates.index(v["eff"])
        if ia - PRE < 0 or ie + 5 >= len(dates):
            continue
        adv = st.mean(x[2] for x in s[ia - PRE - 40:ia - PRE]) \
            if ia - PRE - 40 >= 0 else st.mean(x[2] for x in s[:ia])
        if not adv:
            continue

        def flow(lo, hi):
            return sum(fser.get(dates[i].replace("-", ""), 0.0)
                       for i in range(lo, hi)) / adv

        legs["pre"].append(flow(ia - PRE, ia))
        legs["ann_to_eff"].append(flow(ia + 1, ie))
        legs["eff_day"].append(flow(ie, ie + 1))
        legs["post5"].append(flow(ie + 1, ie + 6))
        n_used += 1

    print(f"\nB. FOREIGN NET BUY AROUND PAST TAIWAN ADDITIONS  (n={n_used}, "
          f"days of ADV)")
    print(f"  {'leg':<14}{'p25':>8}{'median':>9}{'p75':>8}"
          f"{'% buying':>10}")
    for k, label in (("pre", f"pre-ann ({PRE}d)"),
                     ("ann_to_eff", "ann -> eff"),
                     ("eff_day", "effective day"),
                     ("post5", "+1..+5")):
        xs = legs[k]
        if not xs:
            continue
        share = sum(1 for x in xs if x > 0) / len(xs)
        out["history"][k] = {"n": len(xs), "p25": pct(xs, .25),
                             "p50": pct(xs, .5), "p75": pct(xs, .75),
                             "share_buying": share}
        print(f"  {label:<14}{pct(xs,.25):>+8.2f}{pct(xs,.5):>+9.2f}"
              f"{pct(xs,.75):>+8.2f}{share:>9.0%}")

    out["history"]["_n_events"] = n_used
    OUT.write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(f"\n-> {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
