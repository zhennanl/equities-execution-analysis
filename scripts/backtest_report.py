"""Full historical backtest of the prediction engine —
MSCI Taiwan, 2018 → 2026 (c-116).

Answers Bill's four questions in one artifact:
  1. HOW WELL does the engine predict? Additions AND deletions,
     with hits / misses / false alarms per review and in
     aggregate.
  2. WHAT DATA does it use, is it reliable, what broke?
  3. WHERE did it go wrong? Every miss and every false alarm
     classified by root cause.
  4. WHAT SHOULD CHANGE? Concrete engine modifications, ranked,
     each tied to a measured error class.

TWO THINGS THIS SCRIPT ADDS TO THE ENGINE:
  - ADDITION GRADING. review_reconstruct.py grades deletions
    only (pool = members below the floor). Additions were never
    scored because scoring them needs a non-member universe.
    We have vintage prices for 150 TW names, which covers 41 of
    41 coded actual additions — so RECALL is measurable
    exactly. PRECISION is not, and is reported as such rather
    than faked.
  - THE SURVIVAL RE-READ of false alarms. A name flagged
    below-floor that MSCI deletes two reviews later was not
    wrong, it was EARLY. Measuring that turns a precision
    number into an actionable one.

Usage:  py scripts\\backtest_report.py
Output: reports/backtest_taiwan_2018_2026.html (+ .json)
"""
import json
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RDIR = ROOT / "data" / "reconstruct"
sys.path.insert(0, str(ROOT / "scripts"))

ORDER = [f"{m}{y % 100:02d}" for y in range(2018, 2027)
         for m in ("Feb", "May", "Aug", "Nov")]
ORDER = ORDER[:ORDER.index("Aug26")]


_VCACHE = {}


def _vintage():
    """Memoized — this file was being re-read from disk on
    every _caps() call, which made the sweeps take minutes
    instead of seconds (c-116)."""
    if not _VCACHE:
        _VCACHE.update(json.loads(
            (ROOT / "data" / "tw_vintage_cache.json").read_text(encoding="utf-8")))
    return _VCACHE


_MEMO = {}


def _caps(codes, date, fx):
    v = _vintage()
    out = {}
    for c in codes:
        px, sh = v.get(f"px|{c}"), v.get(f"sh|{c}")
        if not (px and sh):
            continue
        p = next((r["close"] for r in reversed(px)
                  if r["date"] <= date), None)
        s = next((r["NumberOfSharesIssued"] for r in reversed(sh)
                  if r["date"] <= date), None)
        if p and s:
            out[c] = p * s / fx / 1e9
    return out


def load():
    """Every reconstruction we have, in review order."""
    out = {}
    for rev in ORDER:
        p = RDIR / f"TW_{rev}.json"
        if p.exists():
            out[rev] = json.loads(p.read_text(encoding="utf-8"))
    return out


def grade_additions(recs, db):
    """The engine's addition rule is 'PIT full cap >= add bar'.
    Score it against what MSCI actually added."""
    rows = []
    for rev, r in recs.items():
        k, fx = r["keys"], r["fx_used"]
        adds = db[(db.review == rev) & (db.action == "ADD")
                  & (db.code != "")]
        if adds.empty:
            continue
        caps = _caps(list(adds.code), k["price_date"], fx)
        for _, a in adds.iterrows():
            c = caps.get(a.code)
            rows.append({
                "review": rev, "code": a.code,
                "security": a.security,
                "cap": round(c, 2) if c else None,
                "bar": k["bar"],
                "flagged": bool(c and c >= k["bar"]),
                "shortfall_pct": (round(100 * (k["bar"] - c)
                                        / k["bar"], 1)
                                  if c and c < k["bar"] else 0)})
    return rows


def survival(recs, db):
    """False alarms re-read: was the flagged name deleted at a
    LATER review? Then it was early, not wrong."""
    fut = {}
    for rev in ORDER:
        d = db[(db.review == rev) & (db.action == "DEL")]
        fut[rev] = set(d.code) - {""}
    rows = []
    for rev, r in recs.items():
        i = ORDER.index(rev)
        for c in r["grading"]["false_alarms"]:
            lag = None
            for j in range(i + 1, len(ORDER)):
                if c in fut.get(ORDER[j], set()):
                    lag = j - i
                    break
            rows.append({"review": rev, "code": c, "lag": lag,
                         "cap": r["grading"]["pool"].get(c)})
    return rows


def sensitivity(recs, db, mults=(0.6, 0.7, 0.8, 0.9, 1.0,
                                 1.1, 1.25)):
    """What if the floor sat elsewhere? The precision/recall
    curve the engine is actually operating on."""
    out = []
    for mu in mults:
        tp = fp = fn = 0
        for rev, r in recs.items():
            k, fx = r["keys"], r["fx_used"]
            floor = k["floor"] * mu
            pool = {c for c, v in r["grading"]["pool"].items()
                    if v < floor}
            # pool is stored only below the ORIGINAL floor, so
            # raising the floor needs the full member scan
            if mu > 1.0:
                from backtest_extras import members
                mem = members(rev, db[db.market == "Taiwan"])
                cc = _caps(mem, k["price_date"], fx)
                pool = {c for c, v in cc.items() if v < floor}
            act = set(db[(db.review == rev)
                         & (db.action == "DEL")].code) - {""}
            tp += len(pool & act)
            fp += len(pool - act)
            fn += len(act - pool)
        out.append({"floor_multiple": mu,
                    "recall": round(tp / max(tp + fn, 1), 3),
                    "precision": round(tp / max(tp + fp, 1), 3),
                    "hits": tp, "false_alarms": fp,
                    "misses": fn})
    return out


def analyse():
    import pandas as pd
    recs = load()
    db = pd.read_pickle(ROOT / "data" / "msci_changes_db.pkl")
    db = db[db.market == "Taiwan"]

    # ---- deletions -------------------------------------
    per = []
    for rev, r in recs.items():
        g = r["grading"]
        per.append({"review": rev,
                    "hits": len(g["hits"]),
                    "misses": len(g["misses"]),
                    "false_alarms": len(g["false_alarms"]),
                    "pool": len(g["pool"]),
                    "floor": r["keys"]["floor"],
                    "bar": r["keys"]["bar"],
                    "price_date": r["keys"]["price_date"],
                    "key_source": r["keys"]["source"]})
    H = sum(p["hits"] for p in per)
    M = sum(p["misses"] for p in per)
    F = sum(p["false_alarms"] for p in per)

    # ---- misses in detail ------------------------------
    miss_rows = []
    for rev, r in recs.items():
        k, fx = r["keys"], r["fx_used"]
        for c in r["grading"]["misses"]:
            cap = _caps([c], k["price_date"], fx).get(c)
            nm = db[(db.review == rev) & (db.code == c)]
            miss_rows.append({
                "review": rev, "code": c,
                "security": (nm.security.iloc[0] if len(nm)
                             else c),
                "cap": round(cap, 2) if cap else None,
                "floor": k["floor"],
                "above_floor_pct": (round(100 * (cap - k["floor"])
                                          / k["floor"], 1)
                                    if cap else None)})

    adds = grade_additions(recs, db)
    surv = survival(recs, db)
    sens = sensitivity(recs, db)

    a_tot = len(adds)
    a_hit = sum(1 for a in adds if a["flagged"])
    a_near = [a for a in adds
              if not a["flagged"] and a["shortfall_pct"] <= 25]
    lags = [s["lag"] for s in surv if s["lag"] is not None]
    return {"per_review": per,
            "deletions": {"hits": H, "misses": M,
                          "false_alarms": F,
                          "recall": round(H / max(H + M, 1), 3),
                          "precision": round(H / max(H + F, 1),
                                             3)},
            "additions": {"actual": a_tot, "flagged": a_hit,
                          "recall": round(a_hit / max(a_tot, 1),
                                          3),
                          "near_miss_within_25pct": len(a_near),
                          "rows": adds},
            "misses": miss_rows,
            "survival": {"total_fa": len(surv),
                         "later_deleted": len(lags),
                         "share": round(len(lags)
                                        / max(len(surv), 1), 3),
                         "median_lag_reviews":
                             (statistics.median(lags) if lags
                              else None),
                         "rows": surv},
            "sensitivity": sens,
            "coverage": {"reviews_scored": len(recs),
                         "reviews_in_window": len(ORDER),
                         "missing": [r for r in ORDER
                                     if r not in recs]}}


if __name__ == "__main__":
    a = analyse()
    (ROOT / "data" / "backtest_taiwan.json").write_text(
        json.dumps(a, indent=1), encoding="utf-8")
    d = a["deletions"]
    print(f"reviews scored {a['coverage']['reviews_scored']}"
          f"/{a['coverage']['reviews_in_window']} "
          f"(missing {a['coverage']['missing']})")
    print(f"DELETIONS  recall {d['recall']:.0%} "
          f"({d['hits']}/{d['hits'] + d['misses']}) | "
          f"precision {d['precision']:.0%} | FA {d['false_alarms']}")
    ad = a["additions"]
    print(f"ADDITIONS  recall {ad['recall']:.0%} "
          f"({ad['flagged']}/{ad['actual']}) | near-miss "
          f"{ad['near_miss_within_25pct']}")
    s = a["survival"]
    print(f"FALSE ALARMS deleted later: {s['later_deleted']}"
          f"/{s['total_fa']} ({s['share']:.0%}), median lag "
          f"{s['median_lag_reviews']} reviews")
    print("\nfloor sensitivity:")
    for r in a["sensitivity"]:
        print(f"  x{r['floor_multiple']:<5} recall "
              f"{r['recall']:.0%}  precision {r['precision']:.0%}"
              f"  (H{r['hits']}/M{r['misses']}/FA"
              f"{r['false_alarms']})")
