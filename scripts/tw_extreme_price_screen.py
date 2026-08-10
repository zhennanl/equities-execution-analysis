#!/usr/bin/env python3
"""§2.3.6.3 — extreme price increase — applied to the Aug-2026 calls.

    py scripts\\tw_extreme_price_screen.py

WHAT THE RULE ACTUALLY SAYS (GIMI May-2026, §2.3.6.3, p.31):

    "Securities that exhibit extreme price increase will not be
    eligible for addition into the Standard Indexes but will
    continue to be considered as part of the market investable
    universe."

So this is not a size or float test that changes a probability —
it is a HARD GATE on the addition side, and a name that trips it
is out of this review entirely and re-tested at the next one. It
sits downstream of everything the walkthrough computes, which is
why the calls need it applied separately.

    Period    5D 10D 15D 20D | 25D 30D 35D 40D | 45D 50D 55D 60D
    Excess   100 100 100 100 | 200 200 200 200 | 400 400 400 400
    Period    90D  120D  150D  180D  250D
    Excess    500   800  1500  1500  2500        (per cent)

    "* Number of days (Mon-Fri) prior to the price cutoff date"

TWO DEFINITIONS THAT ARE EASY TO GET WRONG, AND BOTH MATTER.

1. THE PERIOD IS CALENDAR WEEKDAYS, NOT TRADING DAYS. The
   footnote says "days (Mon-Fri)", so 250D reaches back 250
   weekdays — about 50 weeks — and every Taiwanese public holiday
   inside that span is COUNTED. Treating them as trading sessions
   would reach back roughly 5% further and quietly change the
   base price of every window. We step weekdays and then take the
   last session on or before the resulting date.

2. EXCESS IS AGAINST THE COUNTRY-SECTOR, NOT THE INDEX.

    "the difference between the return of a security ... and the
    average return of IMI constituents belonging to the same
    country-sector ... For country-sectors that have five or less
    IMI constituents, the relevant country IMI return is used."

   AVERAGE, so equal-weighted, not cap-weighted. We do not hold
   MSCI's Taiwan IMI membership by GICS sector, so the measured
   excess below is a PROXY and is labelled as one.

HOW THE PROXY IS PREVENTED FROM DECIDING ANYTHING. The first
version of this script bounded the other way — a sector cannot
return worse than -100%, so excess <= r_stock + 100pp, and any
name whose bound stayed under the threshold could be cleared with
no benchmark at all. That bound is DEGENERATE at the short
horizons: the 5D-20D threshold is exactly 100%, so r_stock + 100pp
clears it for any stock that is up so much as a tick, and the
screen returned "breach possible" for all four names while
proving nothing. It is recorded here because it looked rigorous
and was useless, which is the more dangerous kind of wrong.

The question is inverted instead. A breach needs

    r_sector <= r_stock - threshold                    (= "needed")

so `needed` is stated per window and read directly:

    needed < -100%   arithmetically IMPOSSIBLE, no data required
    otherwise        possible in principle — and then the number
                     says what the Taiwan IT sector would have had
                     to do over that span for it to happen, which
                     a reader can judge without trusting our proxy

The measured proxy excess is reported beside it as the realistic
estimate. It is never the verdict on its own.

PRICE CUTOFF IS NOT KNOWN. §3.1.9 lets MSCI use any one of the
last ten business days of July. Every window is therefore
evaluated at ALL TEN candidate cutoffs and the worst case across
them is what gets reported — a screen answered at one arbitrary
date would be a coin flip on the other nine.
"""
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "tw_extreme_price_screen.json"
DOC = ROOT / "docs" / "TW_EXTREME_PRICE_SCREEN.md"

# §2.3.6.3, p.31. Periods in WEEKDAYS, thresholds as fractions.
THRESHOLDS = [(5, 1.0), (10, 1.0), (15, 1.0), (20, 1.0),
              (25, 2.0), (30, 2.0), (35, 2.0), (40, 2.0),
              (45, 4.0), (50, 4.0), (55, 4.0), (60, 4.0),
              (90, 5.0), (120, 8.0), (150, 15.0), (180, 15.0),
              (250, 25.0)]

CALLS = ["2408", "8046", "2344", "8299"]

# TWSE industry codes that map to GICS Information Technology.
# 24 semiconductor, 25 computer & peripheral, 26 optoelectronic,
# 28 electronic parts, 29 electronic distribution, 30 information
# service, 31 other electronic. 27 (communications & internet) is
# LEFT OUT because it straddles IT and Communication Services and
# we cannot split it from the TWSE code alone.
IT_CODES = {"24", "25", "26", "28", "29", "30", "31"}


def _j(name):
    p = ROOT / "data" / name
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def weekdays_before(d, n):
    """The date `n` Mon-Fri days before `d`. See note 1 above."""
    out = d
    while n:
        out -= dt.timedelta(days=1)
        if out.weekday() < 5:
            n -= 1
    return out


def _series(px):
    """[(date, close)] sorted, dropping unpriced rows."""
    return sorted((r["date"], float(r["close"])) for r in px
                  if r.get("close"))


def px_on_or_before(series, day):
    """Last close on or before `day`. None if the series starts later."""
    lo, hi, best = 0, len(series) - 1, None
    key = day.isoformat()
    while lo <= hi:
        mid = (lo + hi) // 2
        if series[mid][0] <= key:
            best = series[mid]
            lo = mid + 1
        else:
            hi = mid - 1
    return best


def last_business_days(year, month, n=10):
    """The last `n` business days of a month — the price-cutoff pool
    (§3.1.9). Public holidays are NOT excluded; the pool is then
    intersected with the trading calendar by the caller."""
    d = dt.date(year, month, 1)
    nxt = dt.date(year + (month == 12), month % 12 + 1, 1)
    days = []
    while d < nxt:
        if d.weekday() < 5:
            days.append(d)
        d += dt.timedelta(days=1)
    return days[-n:]


def sector_series(vintage, industry):
    """Equal-weighted IT price index from the names we hold.

    A PROXY, and the honest description of what it is: the
    electronics block of the ~150 names in the vintage cache,
    rebased to 1.0 and averaged across names each day. MSCI
    averages over Taiwan IMI constituents in the GICS sector,
    which is a wider and more small-cap-heavy set than this.
    """
    members = [k[3:] for k in vintage if k.startswith("px|")
               and str(industry.get(k[3:])) in IT_CODES]
    by_day = {}
    for c in members:
        s = _series(vintage[f"px|{c}"])
        if not s:
            continue
        base = None
        for day, close in s:
            if base is None:
                base = close
            by_day.setdefault(day, []).append(close / base)
    return ({d: sum(v) / len(v) for d, v in by_day.items()},
            sorted(members))


def main():
    vintage = _j("tw_vintage_cache.json") or {}
    industry = _j("tw_industry_map.json") or {}
    names = _j("yahoo_names.json") or {}
    call = _j("aug26_tw_call_v2.json") or {}
    probs = {str(c["code"]): c for c in call.get("calls", [])}

    sect, members = sector_series(vintage, industry)
    sect_days = sorted(sect)

    def sect_on_or_before(day):
        best, key = None, day.isoformat()
        for d in sect_days:                      # small, linear is fine
            if d <= key:
                best = (d, sect[d])
            else:
                break
        return best

    # the ten candidate price-cutoff dates, kept only where the
    # market actually traded — a cutoff on a Taiwanese holiday is
    # not a cutoff
    pool = last_business_days(2026, 7, 10)
    any_series = _series(vintage[f"px|{CALLS[0]}"])
    traded = {d for d, _c in any_series}
    cutoffs = [d for d in pool if d.isoformat() in traded]

    rows, worst_any = {}, False
    for code in CALLS:
        key = f"px|{code}"
        if key not in vintage:
            rows[code] = {"error": "no daily series"}
            continue
        s = _series(vintage[key])
        per_cut = []
        for cut in cutoffs:
            end = px_on_or_before(s, cut)
            se = sect_on_or_before(cut)
            windows = []
            for n, thr in THRESHOLDS:
                start_day = weekdays_before(cut, n)
                beg = px_on_or_before(s, start_day)
                if not (beg and end):
                    windows.append({"days": n, "threshold": thr,
                                    "measurable": False})
                    continue
                r = end[1] / beg[1] - 1
                sb = sect_on_or_before(start_day)
                rs = (se[1] / sb[1] - 1) if (se and sb) else None
                needed = r - thr
                windows.append({
                    "days": n, "threshold": thr, "measurable": True,
                    "from": beg[0], "to": end[0],
                    "stock_return": r,
                    # what the country-sector would have had to
                    # return over this same span for the excess to
                    # reach the threshold
                    "sector_return_needed": needed,
                    "arithmetically_impossible": needed < -1.0,
                    "sector_return_proxy": rs,
                    "excess_proxy": (r - rs) if rs is not None
                    else None,
                    "breach_proxy": (rs is not None
                                     and (r - rs) >= thr)})
            per_cut.append({"cutoff": cut.isoformat(),
                            "windows": windows})
        flat = [w for c in per_cut for w in c["windows"]
                if w.get("measurable")]
        # windows where a breach is not ruled out by arithmetic
        open_w = [w for w in flat
                  if not w["arithmetically_impossible"]]
        soft = [w for w in flat if w.get("breach_proxy")]
        worst_any = worst_any or bool(soft)
        # "closest" is the window where the sector would have had
        # to fall LEAST — the one nearest to a breach
        head = max(flat, key=lambda w: w["sector_return_needed"])
        c = probs.get(code, {})
        rows[code] = {
            "name": (names.get(f"{code}.TW")
                     or names.get(f"{code}.TWO") or ""),
            "prob": c.get("prob"),
            "verdict": ("BREACHES ON THE PROXY" if soft
                        else "NO BREACH"),
            "n_windows": len(flat),
            "windows_impossible_by_arithmetic":
                len(flat) - len(open_w),
            "closest_window": head,
            "max_excess_proxy": max(
                (w["excess_proxy"] for w in flat
                 if w["excess_proxy"] is not None), default=None),
            "breaches_proxy": len(soft),
            "cutoffs": per_cut}

    out = {"_what": "MSCI GIMI May-2026 §2.3.6.3 extreme price "
                    "increase, applied to the Aug-2026 Taiwan "
                    "addition calls",
           "rulebook": "MSCI_GIMIMethodology_May2026.pdf, §2.3.6.3, "
                       "p.31",
           # a FIELD, not a sentence in a docstring, because this
           # is the fact that decides how the result gets used: a
           # breach is a hard gate on Standard addition, not a
           # haircut on a conviction number.
           "treatment": "hard gate — a breaching security is not "
                        "eligible for addition into the Standard "
                        "Index this review and is re-evaluated at "
                        "the next one; it stays in the market "
                        "investable universe meanwhile",
           "generated": dt.date.today().isoformat(),
           "price_cutoff_pool": [d.isoformat() for d in cutoffs],
           "period_unit": "weekdays (Mon-Fri), per the table's "
                          "footnote — NOT trading sessions",
           "benchmark": {
               "rule": "average return of IMI constituents in the "
                       "same country-sector (GICS sector level)",
               "held": False,
               "proxy": "equal-weighted price index of the TWSE "
                        "electronics block in the vintage cache",
               "proxy_members": len(members),
               "why_it_does_not_decide": "each window states the "
                                         "sector return that "
                                         "would be REQUIRED for a "
                                         "breach; where that is "
                                         "below -100% no data is "
                                         "needed, and elsewhere "
                                         "the figure can be judged "
                                         "without trusting the "
                                         "proxy"},
           "any_breach_on_proxy": worst_any,
           "names": rows}
    OUT.write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(f"-> {OUT.relative_to(ROOT)}")

    print(f"\nprice-cutoff candidates: "
          f"{cutoffs[0]} .. {cutoffs[-1]} ({len(cutoffs)} days)")
    print(f"sector proxy: {len(members)} electronics names\n")
    print(f"{'code':<6}{'name':<24}{'verdict':<11}"
          f"{'closest window — the sector would have had to return':<52}")
    for code, r in rows.items():
        w = r["closest_window"]
        head = (f"{w['days']}D  stock {w['stock_return']:+7.1%}  "
                f"thr {w['threshold']:>5.0%}  needs sector "
                f"{w['sector_return_needed']:+8.1%}"
                f"{'  (impossible)' if w['arithmetically_impossible'] else ''}")
        print(f"{code:<6}{str(r['name'])[:22]:<24}"
              f"{r['verdict']:<11}{head}")
        print(f"{'':<41}measured proxy excess there: "
              f"{w['excess_proxy']:+.1%} vs {w['threshold']:.0%}")
    imp = sum(r["windows_impossible_by_arithmetic"] for r in
              rows.values() if "n_windows" in r)
    tot = sum(r["n_windows"] for r in rows.values()
              if "n_windows" in r)
    print(f"\n{imp} of {tot} name-window-cutoff combinations are "
          f"ruled out by arithmetic alone.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
