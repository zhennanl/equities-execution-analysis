"""CONDITIONAL event-window study — Taiwan (c-132).

The upgrade Bill asked for: not "what happens on average" but
"GIVEN what I can observe by day t, what happens next, and
which MECHANISM is driving it".

Taiwan lets us attribute because three flows carry different
fingerprints, per stock per day:
    t86 foreign net buy   -> institutions / index arbs / HFs
    margin balance        -> RETAIL leverage (the TW retail
                             instrument of choice)
    SBL borrow balance    -> shorts (build = positioning,
                             fall = covering)

THE ANALYSES
  A. Early-strength attribution (Bill's question): ADDs
     bucketed by day1-3 return tercile x dominant early flow
     (foreign-led / retail-led / flowless). For each cell:
     what happened AFTER (day3->E-1, eff day, revert). If
     early strength + foreign flow -> continuation, that IS
     the pre-positioning signature; retail-led or flowless
     early pops behave differently.
  B. "Has the trade already happened?" — conditional path
     table: day1-5 return quartile -> remaining drift, eff
     day, reversion. The single most-asked desk question.
  C. DEL borrow conditionals: borrow-build tercile (window)
     -> eff day + revert (does a crowded short squeeze the
     close and bounce after?). Same for PRE-announcement
     borrow build.
  D. Liquidity conditioning: ADV-dollar bucket -> drift /
     eff-day / reversion (do small names drift more and
     revert more?).
  E. Risk shape, not just terminal alpha: per-window MAE/MFE
     of the day-1-entry add-long (what drawdown must the pod
     survive to collect the drift?).
  F. Crowdedness of the REVIEW (names per event) -> per-name
     drift (is arb capital diluted across big reviews?).

Flow attribution is 2015+ (flow caches start 2015-01);
price-path conditionals use all windows. Every cell carries n.
Attribution is CORRELATIONAL — stated, not hidden.

Usage:  py scripts\\event_conditional_study.py
Output: data/event_conditional_tw.json + console tables
"""
import json
import statistics as st
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "event_conditional_tw.json"


def _num(x):
    try:
        return float(str(x).replace(",", ""))
    except (ValueError, TypeError):
        return None


def med(xs):
    xs = [x for x in xs if x is not None]
    return round(st.median(xs), 4) if xs else None


def _series(v, t86, sbl, margin):
    """Per-window day-indexed arrays + flow series."""
    px = v["px"]
    dts = [r["d"] for r in px]
    close = [r["c"] for r in px]
    vol = [r["v"] for r in px]
    i0 = None
    for i, d in enumerate(dts):
        if d <= v["ann"]:
            i0 = i
    ie = None
    for i, d in enumerate(dts):
        if d <= v["eff"]:
            ie = i
    if i0 is None or ie is None or ie <= i0 + 4 \
            or len(px) < ie + 2:
        return None
    keys = [d.replace("-", "") for d in dts]
    code = v["code"]
    fnet = [(t86.get(k, {}).get(code) or {}).get("f")
            for k in keys]
    bor = [(sbl.get(k, {}).get(code) or [None, None])[1]
           for k in keys]

    def mar(k):
        r = (margin.get(k, {}).get(code) or {}).get("raw")
        return _num(r[5]) if r and len(r) > 5 else None
    marg = [mar(k) for k in keys]
    adv_sh = st.median([q for q in vol[max(0, i0 - 20):i0]
                        if q] or [1])
    adv_usd = adv_sh * close[i0] / 31.5 / 1e6   # $M, rough fx

    def ret(a, b):
        return close[b] / close[a] - 1
    n3 = min(i0 + 3, ie - 1)
    n5 = min(i0 + 5, ie - 1)
    ser = {
        "rev": v["rev"], "code": code, "action": v["action"],
        "year": int(v["ann"][:4]),
        "r_early3": ret(i0, n3),
        "r_early5": ret(i0, n5),
        "r_late": ret(n3, ie - 1),
        "eff_day": ret(ie - 1, ie),
        "revert5": ret(ie, min(ie + 5, len(close) - 1)),
        "total": ret(i0, ie - 1),
        "adv_usd_m": adv_usd,
    }
    # flows over day1..3 (normalized by ADV shares)
    f3 = [f for f in fnet[i0 + 1:n3 + 1] if f is not None]
    ser["f_early_adv"] = (sum(f3) / (3 * adv_sh)
                          if f3 and adv_sh else None)
    m0, m3 = marg[i0], next((m for m in marg[n3::-1] if m),
                            None)
    m3 = marg[n3] if marg[n3] else m3
    ser["margin_chg_adv"] = ((m3 - m0) / (3 * adv_sh)
                             if m0 and m3 and adv_sh else None)
    b0 = bor[i0] or next((b for b in bor[:i0][::-1] if b), None)
    be = next((b for b in bor[ie::-1] if b), None)
    bp = next((b for b in bor[max(0, i0 - 25):i0] if b), None)
    ser["borrow_win_bld"] = (be / b0 if be and b0 else None)
    ser["borrow_pre_bld"] = (b0 / bp if b0 and bp else None)
    # MAE/MFE for a day-1-close entry, held to E-1
    if v["action"] == "ADD":
        entry = close[min(i0 + 1, ie - 1)]
        path = [c / entry - 1 for c in close[i0 + 1:ie]]
        ser["mae"] = round(min(path), 4) if path else None
        ser["mfe"] = round(max(path), 4) if path else None
    return ser


def tercile_split(rows, key):
    xs = sorted(r[key] for r in rows if r.get(key) is not None)
    if len(xs) < 9:
        return None
    t1, t2 = xs[len(xs) // 3], xs[2 * len(xs) // 3]
    return (t1, t2,
            [r for r in rows if r.get(key) is not None
             and r[key] <= t1],
            [r for r in rows if r.get(key) is not None
             and t1 < r[key] <= t2],
            [r for r in rows if r.get(key) is not None
             and r[key] > t2])


def main():
    W = json.loads((ROOT / "data" / "tw_event_windows.json")
                   .read_text(encoding="utf-8"))["windows"]
    # c-188: 2015 floor — see scripts/study_window.py
    import sys as _sys
    _sys.path.insert(0, str(ROOT / 'scripts'))
    from study_window import filter_windows
    W = filter_windows(W)
    t86 = json.loads((ROOT / "data" / "t86_history.json")
                     .read_text(encoding="utf-8"))
    sbl = json.loads((ROOT / "data" / "sbl_history.json")
                     .read_text(encoding="utf-8"))
    margin = json.loads((ROOT / "data" / "margin_history.json")
                        .read_text(encoding="utf-8"))
    rows = []
    for v in W.values():
        if not v["px"]:
            continue
        s = _series(v, t86, sbl, margin)
        if s:
            rows.append(s)
    adds = [r for r in rows if r["action"] == "ADD"]
    dels = [r for r in rows if r["action"] == "DEL"]
    out = {"n": {"windows": len(rows), "adds": len(adds),
                 "dels": len(dels)},
           "caveats": ["flow attribution 2015+ only",
                       "attribution is correlational",
                       "margin balance = retail-leverage "
                       "proxy, not all retail"]}

    # ---- A. early-strength attribution (ADDs) ------------
    fl = [r for r in adds if r["year"] >= 2015
          and r.get("f_early_adv") is not None]
    A = {}
    ts = tercile_split(fl, "r_early3")
    if ts:
        t1, t2, lo, mid, hi = ts
        A["early_terciles_cutoffs"] = [round(t1, 4),
                                       round(t2, 4)]
        for name, grp in (("weak_early", lo),
                          ("mid_early", mid),
                          ("strong_early", hi)):
            A[name] = {
                "n": len(grp),
                "r_late_med": med([g["r_late"] for g in grp]),
                "eff_day_med": med([g["eff_day"] for g in grp]),
                "revert5_med": med([g["revert5"]
                                    for g in grp]),
                "f_early_adv_med": med([g["f_early_adv"]
                                        for g in grp]),
                "margin_chg_adv_med": med(
                    [g["margin_chg_adv"] for g in grp])}
        # within STRONG early movers: foreign-led vs not
        fkey = med([g["f_early_adv"] for g in hi]) or 0
        fled = [g for g in hi if (g["f_early_adv"] or 0)
                > fkey]
        rest = [g for g in hi if (g["f_early_adv"] or 0)
                <= fkey]
        A["strong_early_foreign_led"] = {
            "n": len(fled),
            "r_late_med": med([g["r_late"] for g in fled]),
            "revert5_med": med([g["revert5"] for g in fled])}
        A["strong_early_NOT_foreign_led"] = {
            "n": len(rest),
            "r_late_med": med([g["r_late"] for g in rest]),
            "revert5_med": med([g["revert5"] for g in rest]),
            "margin_chg_adv_med": med([g["margin_chg_adv"]
                                       for g in rest])}
    out["A_early_attribution_ADD"] = A

    # ---- B. has the trade happened? (all-era, price only) -
    B = {}
    ts = tercile_split(adds, "r_early5")
    if ts:
        t1, t2, lo, mid, hi = ts
        B["cutoffs_day5"] = [round(t1, 4), round(t2, 4)]
        for name, grp in (("cold_start", lo), ("mid", mid),
                          ("hot_start", hi)):
            B[name] = {"n": len(grp),
                       "remaining_drift_med": med(
                           [g["r_late"] for g in grp]),
                       "eff_day_med": med([g["eff_day"]
                                           for g in grp]),
                       "revert5_med": med([g["revert5"]
                                           for g in grp]),
                       "total_med": med([g["total"]
                                         for g in grp])}
    out["B_hot_start_ADD"] = B

    # ---- C. DEL borrow conditionals ----------------------
    C = {}
    fl = [r for r in dels if r.get("borrow_win_bld") is not None]
    ts = tercile_split(fl, "borrow_win_bld")
    if ts:
        t1, t2, lo, mid, hi = ts
        C["window_build_cutoffs"] = [round(t1, 3),
                                     round(t2, 3)]
        for name, grp in (("light_short", lo),
                          ("mid_short", mid),
                          ("crowded_short", hi)):
            C[name] = {"n": len(grp),
                       "eff_day_med": med([g["eff_day"]
                                           for g in grp]),
                       "revert5_med": med([g["revert5"]
                                           for g in grp]),
                       "total_med": med([g["total"]
                                         for g in grp])}
    fl2 = [r for r in dels
           if r.get("borrow_pre_bld") is not None]
    ts2 = tercile_split(fl2, "borrow_pre_bld")
    if ts2:
        t1, t2, lo, mid, hi = ts2
        C["pre_ann_build"] = {
            "cutoffs": [round(t1, 3), round(t2, 3)],
            "low": {"n": len(lo),
                    "total_med": med([g["total"] for g in lo])},
            "high": {"n": len(hi),
                     "total_med": med([g["total"]
                                       for g in hi]),
                     "revert5_med": med([g["revert5"]
                                         for g in hi])}}
    out["C_del_borrow"] = C

    # ---- D. liquidity buckets ----------------------------
    D = {}
    for name, grp in (("small_<20M", [r for r in adds
                                      if r["adv_usd_m"] < 20]),
                      ("mid_20-60M", [r for r in adds
                                      if 20 <= r["adv_usd_m"]
                                      < 60]),
                      ("large_>60M", [r for r in adds
                                      if r["adv_usd_m"] >= 60])):
        D[name] = {"n": len(grp),
                   "drift_med": med([g["r_late"] +
                                     g["r_early3"]
                                     for g in grp]),
                   "eff_day_med": med([g["eff_day"]
                                       for g in grp]),
                   "revert5_med": med([g["revert5"]
                                       for g in grp])}
    out["D_liquidity_ADD"] = D

    # ---- E. MAE / MFE ------------------------------------
    out["E_risk_shape_ADD"] = {
        "mae_med": med([r["mae"] for r in adds]),
        "mae_p10": (sorted([r["mae"] for r in adds
                            if r["mae"] is not None])[
            max(0, len([r for r in adds
                        if r["mae"] is not None]) // 10)]
            if adds else None),
        "mfe_med": med([r["mfe"] for r in adds]),
        "read": "MAE = worst drawdown a day-1 long endures "
                "before E-1; the pod's stop placement and "
                "sizing input"}

    # ---- F. review-size dilution -------------------------
    from collections import Counter
    per_rev = Counter(r["rev"] for r in rows)
    small_ev = [r for r in adds if per_rev[r["rev"]] <= 3]
    big_ev = [r for r in adds if per_rev[r["rev"]] >= 6]
    out["F_review_size"] = {
        "small_reviews(<=3 names)": {
            "n": len(small_ev),
            "total_med": med([g["total"] for g in small_ev])},
        "big_reviews(>=6 names)": {
            "n": len(big_ev),
            "total_med": med([g["total"] for g in big_ev])}}

    OUT.write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
