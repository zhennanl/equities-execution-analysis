"""The ANALOG MATCHER (c-136) — Bill's idea, implemented.

"I have a tech add, +5% at day 7 since announcement. Find the
similar historical cases and show me what happened next."

ASSESSMENT OF THE IDEA (requested): it is sound, and it is the
right formalization — what Bill describes is the EMPIRICAL
CONDITIONAL DISTRIBUTION, the nonparametric cousin of the
tercile tables, and how experienced desks actually reason
("this smells like Chroma in Nov-25"). Three honest hazards,
each handled:
  1. CURSE OF DIMENSIONALITY: 100 adds cannot support matching
     on five features. We match on at most action + day-offset
     (exact, by construction) + cum-return distance + optional
     sector — and SHOW N so thin matches are self-evident.
  2. SMALL-N OVERCONFIDENCE: output is the analog LIST first,
     distribution second. Eyeballing 8 named cases resists
     false precision better than a median of 8 does.
  3. REGIME LEAKAGE: analogs carry their year; the caller sees
     if all matches come from one era.

Usage:
  from analog_matcher import analogs
  analogs(action="ADD", day=7, cum_ret=0.05, sector="TECH")
  py scripts\\analog_matcher.py ADD 7 0.05 TECH
Returns: matched cases with what-happened-next + the
conditional distribution.
"""
import json
import statistics as st
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SECTOR_GROUP = {
    "24": "TECH", "25": "TECH", "26": "TECH", "27": "TECH",
    "28": "TECH", "29": "TECH", "30": "TECH", "31": "TECH",
    "05": "TECH", "17": "FINANCIAL", "15": "SHIPPING",
    "22": "HEALTHCARE"}

_CACHE = {}


def _library():
    """Every historical window, resampled onto day-offset
    space: cum returns at each day t, plus the outcomes."""
    if _CACHE:
        return _CACHE["lib"]
    W = json.loads((ROOT / "data" / "tw_event_windows.json")
                   .read_text(encoding="utf-8"))["windows"]
    # c-188: 2015 floor — see scripts/study_window.py
    import sys as _sys
    _sys.path.insert(0, str(ROOT / 'scripts'))
    from study_window import filter_windows
    W = filter_windows(W)
    ind = json.loads((ROOT / "data" / "tw_industry_map.json")
                     .read_text(encoding="utf-8"))
    lib = []
    for v in W.values():
        px = v["px"]
        if len(px) < 12:
            continue
        dts = [r["d"] for r in px]
        cl = [r["c"] for r in px]
        vol = [r["v"] for r in px]
        i0 = max((i for i, d in enumerate(dts)
                  if d <= v["ann"]), default=None)
        ie = max((i for i, d in enumerate(dts)
                  if d <= v["eff"]), default=None)
        if i0 is None or ie is None or ie <= i0 + 3 \
                or len(px) < ie + 2:
            continue
        adv = st.median([q for q in vol[max(0, i0 - 20):i0]
                         if q] or [1])
        lib.append({
            "rev": v["rev"], "code": v["code"],
            "name": v["name"], "action": v["action"],
            "year": int(v["ann"][:4]),
            "sector": SECTOR_GROUP.get(
                ind.get(v["code"], ""), "OTHER"),
            "n_days_to_eff": ie - i0,
            "cum_at": {t: cl[min(i0 + t, ie - 1)] / cl[i0] - 1
                       for t in range(1, 15)},
            "then_to_Eminus1": None,      # filled per query
            "eff_day": cl[ie] / cl[ie - 1] - 1,
            "close_vs_ann": cl[ie] / cl[i0] - 1,
            "revert5": cl[min(ie + 5, len(cl) - 1)]
            / cl[ie] - 1,
            "vol_eff_x": (vol[ie] / adv
                          if adv and vol[ie] else None),
            "_cl": cl, "_i0": i0, "_ie": ie})
    _CACHE["lib"] = lib
    return lib


def analogs(action="ADD", day=7, cum_ret=0.05, sector=None,
            k=8):
    lib = _library()
    cands = []
    for r in lib:
        if r["action"] != action:
            continue
        if sector and r["sector"] != sector:
            continue
        if r["n_days_to_eff"] <= day:
            continue                      # eff already passed
        c = r["cum_at"].get(day)
        if c is None:
            continue
        cands.append((abs(c - cum_ret), c, r))
    cands.sort(key=lambda x: x[0])
    out = []
    for dist, c, r in cands[:k]:
        cl, i0, ie = r["_cl"], r["_i0"], r["_ie"]
        out.append({
            "rev": r["rev"], "code": r["code"],
            "name": r["name"], "year": r["year"],
            "sector": r["sector"],
            "cum_at_day": round(c, 4),
            "then_to_Eminus1":
                round(cl[ie - 1] / cl[min(i0 + day, ie - 1)]
                      - 1, 4),
            "eff_day": round(r["eff_day"], 4),
            "revert5": round(r["revert5"], 4),
            "vol_eff_x": (round(r["vol_eff_x"], 1)
                          if r["vol_eff_x"] else None)})
    def med(key):
        xs = [o[key] for o in out if o[key] is not None]
        return round(st.median(xs), 4) if xs else None
    dist = {"n": len(out),
            "n_candidates": len(cands),
            "then_to_Eminus1_med": med("then_to_Eminus1"),
            "eff_day_med": med("eff_day"),
            "revert5_med": med("revert5"),
            "years": sorted({o["year"] for o in out})}
    return {"query": {"action": action, "day": day,
                      "cum_ret": cum_ret, "sector": sector},
            "analogs": out, "distribution": dist}


if __name__ == "__main__":
    a = sys.argv[1:]
    res = analogs(a[0] if a else "ADD",
                  int(a[1]) if len(a) > 1 else 7,
                  float(a[2]) if len(a) > 2 else 0.05,
                  a[3] if len(a) > 3 else None)
    print(json.dumps(res, indent=1))
