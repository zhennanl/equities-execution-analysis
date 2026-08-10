#!/usr/bin/env python3
"""Taiwan index movers that hit the daily price limit on the print.

    py scripts\\tw_limit_moves.py

WHY THIS IS THE ONE TAIWAN-SPECIFIC RISK WORTH MEASURING. Taiwan
caps a stock's daily move. A tracker that must own the closing
price on the effective date has no recourse if the stock is
LOCKED at the limit: the auction cannot clear where the index
marks, the fill is partial, and the residual is carried into a
session the index no longer pays for. That is a tracking-error
event created by market structure rather than by the trade, and
no APAC market outside Taiwan, Korea and China has it.

THE REGIME CHANGE THAT WOULD HAVE SILENTLY BROKEN THIS. TWSE
widened the daily limit from 7% to 10% on 1 June 2015. Our panel
opens in Feb-2015, so the Feb-15 and May-15 reviews sit under the
OLD limit. A detector hard-coded at 10% does not merely mis-count
them — it reports ZERO limit hits for those reviews and looks
like a clean result.

ONLY "LOCKED" IS MEASURABLE HERE, AND THAT IS A DATA FACT.

    LOCKED    the CLOSE sits at the cap. The closing auction
              could not clear away from the limit, so a
              market-on-close order did not fully fill. Needs
              only the close and the previous close.
    TOUCHED   the high or low reached the cap intraday and the
              stock came back. Needs the day's HIGH and LOW.

Every one of the 165 effective-date bars in this panel is
CLOSE-ONLY — the o/h/l fields are absent on all of them (about
20% of rows overall carry OHLC, and none of those rows is a
print date). So "touched and recovered" is not detectable and is
not reported. Guessing it from the close would invent the one
number a desk would actually act on.

The loss is smaller than it looks: LOCKED is the fill problem.
A name that tested the limit and closed away still printed.

THE TELL A DESK CAN USE. A locked print should show LOWER volume
than an ordinary effective day, not higher — the trade could not
happen. If the volume is missing on the print and appears the
next session, that is the residual being worked, and it is
directly measurable here.
"""
from __future__ import annotations

import json
import statistics as st
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "tw_limit_moves.json"

# TWSE widened the daily limit on 1 June 2015. VERIFIED, not
# recalled: TWSE trading-mechanism page and the price-limit
# literature both date it to 2015-06-01.
LIMIT_CHANGE = "2015-06-01"
LIMIT_OLD, LIMIT_NEW = 0.07, 0.10

# TWSE tick ladder. The exchange rounds the limit price to a
# valid tick, so a cap can sit up to one tick inside the
# arithmetic cap — which is why every comparison below carries a
# one-tick tolerance instead of testing equality.
_TICKS = ((10, 0.01), (50, 0.05), (100, 0.1), (500, 0.5),
          (1000, 1.0))
HORIZ = 20


def limit_for(date):
    return LIMIT_OLD if str(date) < LIMIT_CHANGE else LIMIT_NEW


def tick(price):
    for hi, t in _TICKS:
        if price < hi:
            return t
    return 5.0


def _j(name):
    p = ROOT / "data" / name
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def pct(xs, p):
    xs = sorted(x for x in xs if x is not None and x == x)
    if not xs:
        return None
    i = (len(xs) - 1) * p
    lo = int(i)
    hi = min(lo + 1, len(xs) - 1)
    return xs[lo] + (xs[hi] - xs[lo]) * (i - lo)


def classify(prev_close, bar, date):
    """(locked_up, locked_dn) for one session.

    Measured against the cap implied by the PREVIOUS close, with
    a one-tick tolerance because TWSE rounds the limit price to a
    valid tick — so the real cap can sit just inside the
    arithmetic one and an equality test would miss it.
    """
    lim = limit_for(date)
    tk = tick(prev_close)
    return (bar["c"] >= prev_close * (1 + lim) - tk,
            bar["c"] <= prev_close * (1 - lim) + tk)


def main():
    wins = (_j("tw_event_windows.json") or {}).get("windows", {})
    twii = {k: float(v) for k, v in
            (_j("twii_daily.json") or {}).items()}
    rows, checked = [], 0

    for key, w in wins.items():
        px = w.get("px") or []
        eff = w.get("eff")
        if not px or not eff:
            continue
        bars = sorted(px, key=lambda r: r["d"])
        dates = [r["d"] for r in bars]
        if eff not in dates:
            continue
        i = dates.index(eff)
        if i < 21 or i + 1 >= len(bars):
            continue
        checked += 1

        prev, day = bars[i - 1], bars[i]
        if not prev["c"]:
            continue
        lu, ld = classify(prev["c"], day, eff)

        # ADV from the 20 sessions ENDING BEFORE the announcement
        # reaction, same denominator the rest of the project uses
        ann = w.get("ann") or ""
        ai = next((n for n, d in enumerate(dates) if d >= ann), i)
        base = [r["v"] for r in bars[max(0, ai - 20):ai] if r["v"]]
        adv = st.mean(base) if base else None

        def ex(a, b):
            """excess return over TAIEX between two bar indices"""
            if a < 0 or b >= len(bars):
                return None
            p0, p1 = bars[a]["c"], bars[b]["c"]
            m0 = twii.get(dates[a])
            m1 = twii.get(dates[b])
            if not (p0 and p1):
                return None
            r = p1 / p0 - 1
            if m0 and m1:
                r -= (m1 / m0 - 1)
            return r

        path = {n: ex(i, i + n) for n in range(1, HORIZ + 1)
                if i + n < len(bars)}
        nxt = bars[i + 1]
        rows.append({
            "key": key, "code": w["code"], "rev": w["rev"],
            "action": w["action"], "eff": eff,
            "limit_pct": limit_for(eff),
            "locked_up": lu, "locked_dn": ld,
            "eff_day_ret": day["c"] / prev["c"] - 1,
            "eff_excess": ex(i - 1, i),
            "eff_x_adv": (day["v"] / adv) if adv else None,
            "next_x_adv": (nxt["v"] / adv) if adv else None,
            "next_open_gap": (nxt["o"] / day["c"] - 1
                              if day["c"] and nxt.get("o") else None),
            "path": {str(n): v for n, v in path.items()
                     if v is not None},
        })

    def grp(sel):
        return [r for r in rows if sel(r)]

    def summarise(rs):
        if not rs:
            return {"n": 0}
        out = {"n": len(rs)}
        for f in ("eff_excess", "eff_x_adv", "next_x_adv",
                  "next_open_gap"):
            xs = [r[f] for r in rs if r.get(f) is not None]
            out[f] = {"n": len(xs), "p25": pct(xs, .25),
                      "p50": pct(xs, .5), "p75": pct(xs, .75)}
        out["path"] = {}
        for n in range(1, HORIZ + 1):
            xs = [r["path"][str(n)] for r in rs
                  if str(n) in r["path"]]
            if xs:
                out["path"][str(n)] = {
                    "n": len(xs), "p25": pct(xs, .25),
                    "p50": pct(xs, .5), "p75": pct(xs, .75)}
        return out

    locked = grp(lambda r: r["locked_up"] or r["locked_dn"])
    clear = grp(lambda r: not (r["locked_up"] or r["locked_dn"]))
    # NEAR is not "touched" — it is a close within 2pp of the cap,
    # computable from the close alone. It exists to answer "how
    # close did the rest get?" without pretending to see intraday.
    near = grp(lambda r: not (r["locked_up"] or r["locked_dn"])
               and abs(r["eff_day_ret"]) >= r["limit_pct"] - 0.02)

    # ---- THE SPLIT THAT REFRAMES EVERYTHING -------------------
    # Eight locked prints is not eight independent observations.
    # Six of them share ONE DATE, 2011-11-30, when a nine-name
    # deletion review printed and six of the nine closed at the
    # floor. TAIEX moved -1.21% that session, so this was the
    # deletion basket exhausting the book, not a market crash —
    # and it is one episode, not six.
    #
    # And seven of the eight happened under the OLD 7% limit.
    # Splitting on the regime is the single most useful cut in
    # this file: it turns "4.8% of prints lock" into a number
    # that is no longer true of the market a desk trades today.
    old_era = [r for r in rows if r["limit_pct"] == LIMIT_OLD]
    new_era = [r for r in rows if r["limit_pct"] == LIMIT_NEW]
    ol = [r for r in old_era if r["locked_up"] or r["locked_dn"]]
    nl = [r for r in new_era if r["locked_up"] or r["locked_dn"]]
    episodes = sorted({r["eff"] for r in locked})

    res = {
        "_what": "Taiwan index movers at the daily price limit "
                 "on the effective date",
        "_limit_regime": {"before": f"{LIMIT_OLD:.0%} until "
                                    f"{LIMIT_CHANGE}",
                          "after": f"{LIMIT_NEW:.0%} from "
                                   f"{LIMIT_CHANGE}"},
        "_not_measurable": "intraday touch-and-recover: every "
                           "effective-date bar in this panel is "
                           "close-only",
        "sample": {"windows_checked": checked,
                   "locked": len(locked), "near": len(near),
                   "clear": len(clear),
                   "locked_episodes": len(episodes),
                   "locked_dates": episodes},
        "by_regime": {
            "limit_7pct": {"prints": len(old_era),
                           "locked": len(ol),
                           "rate": len(ol) / len(old_era)
                           if old_era else None},
            "limit_10pct": {"prints": len(new_era),
                            "locked": len(nl),
                            "rate": len(nl) / len(new_era)
                            if new_era else None}},
        "locked": summarise(locked),
        "near_the_limit": summarise(near),
        "clear": summarise(clear),
        "locked_up": summarise(grp(lambda r: r["locked_up"])),
        "locked_dn": summarise(grp(lambda r: r["locked_dn"])),
        "events": rows,
    }
    OUT.write_text(json.dumps(res, indent=1), encoding="utf-8")

    print(f"windows with a dated print: {checked}")
    print(f"  LOCKED at the limit on the print : {len(locked)}"
          f"  ({len(locked) / max(checked, 1):.1%})")
    print(f"  closed within 2pp of the limit   : {len(near)}")
    print(f"  clear                            : {len(clear)}")
    print(f"\n  {'group':<16}{'n':>4}{'eff excess':>12}"
          f"{'eff xADV':>10}{'next xADV':>11}{'gap':>9}")
    for lab, g in (("locked", locked), ("near (<2pp)", near),
                   ("clear", clear)):
        s = summarise(g)
        if not s["n"]:
            continue
        def f(field, fmt, w):
            # every cell None-safe: the open is absent from these
            # bars, so next_open_gap has no median and printing it
            # blind raised TypeError on the first run.
            v = (s.get(field) or {}).get("p50")
            return (format(v, fmt) if v is not None
                    else "—").rjust(w)
        print(f"  {lab:<16}{s['n']:>4}"
              + f("eff_excess", ".2%", 11)
              + f("eff_x_adv", ".1f", 9)
              + f("next_x_adv", ".1f", 10)
              + f("next_open_gap", ".2%", 9))
    print(f"\n  path after the print (median excess over TAIEX)")
    print(f"  {'group':<16}" + "".join(f"{'+' + str(n):>9}"
                                       for n in (1, 5, 10, 20)))
    for lab, g in (("locked", locked), ("near (<2pp)", near),
                   ("clear", clear)):
        s = summarise(g)
        if not s["n"]:
            continue
        cells = ""
        for n in (1, 5, 10, 20):
            v = s["path"].get(str(n))
            cells += (f"{v['p50']:>8.2%} " if v and
                      v.get("p50") is not None else "       — ")
        print(f"  {lab:<16}{cells}")
    ups = [r for r in rows if r["locked_up"]]
    dns = [r for r in rows if r["locked_dn"]]
    print(f"\n  locked UP {len(ups)}  |  locked DOWN {len(dns)}")
    by_side = {}
    for r in locked:
        by_side[r["action"]] = by_side.get(r["action"], 0) + 1
    print(f"  locked by side: {by_side}")
    print(f"\n  BY LIMIT REGIME")
    print(f"     7% (to 2015-05-31) : {len(ol)}/{len(old_era)}"
          f" prints locked"
          + (f"  = {len(ol) / len(old_era):.1%}" if old_era else ""))
    print(f"    10% (from 2015-06)  : {len(nl)}/{len(new_era)}"
          f" prints locked"
          + (f"  = {len(nl) / len(new_era):.1%}" if new_era else ""))
    print(f"\n  the {len(locked)} locked prints fall on "
          f"{len(episodes)} DATES: {', '.join(episodes)}")
    print(f"\n-> {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
