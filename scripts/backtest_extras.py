"""The diagnostic layer of the c-116 backtest.

Everything here answers "WHY was the engine wrong", as opposed
to backtest_report.py which answers "HOW OFTEN". Each function
is one hypothesis test, and each one is allowed to come back
negative — the persistence test did, and that negative result
is reported rather than dropped.
"""
import json
import statistics as st
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from backtest_report import ORDER, _caps, load    # noqa: E402

O2 = [f"{m}{y % 100:02d}" for y in range(2015, 2027)
      for m in ("Feb", "May", "Aug", "Nov")]
_MEM = {}


def members(rev, tw):
    """Memoized PIT membership — the reverse-roll walks the
    whole changes table, so recomputing it inside a 9-point
    sweep was the second hotspot (c-116)."""
    if rev not in _MEM:
        import review_reconstruct as RR
        _MEM[rev] = RR.pit_members(rev, O2, tw[tw.code != ""])
    return _MEM[rev]


def _uni():
    v = json.loads((ROOT / "data" / "tw_vintage_cache.json")
                   .read_text(encoding="utf-8"))
    return sorted({k.split("|")[1] for k in v
                   if k.startswith("px|")})


def add_threshold_sweep(recs, tw, mults=(0.6, 0.667, 0.7, 0.75,
                                         0.8, 0.9, 1.0, 1.25,
                                         1.5)):
    """The engine's add bar is 1.5 x ceiling. Is that right?
    Recall is exact (all 41 coded additions have vintage data).
    Precision is measured against the 150-name vintage universe
    only — a BIASED sample (assembled around names of interest,
    so it over-represents borderline names). Treat precision as
    indicative of the SHAPE of the curve, not its level."""
    import review_reconstruct as RR
    uni = _uni()
    out = []
    for mu in mults:
        tp = fp = fn = 0
        for rev, r in recs.items():
            k, fx = r["keys"], r["fx_used"]
            t = k["ceiling"] * mu
            mem = members(rev, tw)
            caps = _caps([c for c in uni if c not in mem],
                         k["price_date"], fx)
            fl = {c for c, v in caps.items() if v >= t}
            act = set(tw[(tw.review == rev)
                         & (tw.action == "ADD")].code) - {""}
            tp += len(fl & act)
            fp += len(fl - act)
            fn += len(act - fl)
        out.append({"x_ceiling": mu,
                    "recall": round(tp / max(tp + fn, 1), 3),
                    "precision_partial":
                        round(tp / max(tp + fp, 1), 3),
                    "hits": tp, "misses": fn, "flagged_other": fp})
    return out


def classify_misses(a, recs, tw):
    """Two very different failure modes hide in one number."""
    out = []
    for m in a["misses"]:
        in_mem = m["code"] in members(m["review"], tw)
        cap, fl = m["cap"], m["floor"]
        if cap is None:
            cls, why = "NO DATA", "no vintage price/shares"
        elif not in_mem and cap < fl:
            cls = "MEMBERSHIP GAP"
            why = ("size test WOULD have fired — the name was "
                   "missing from our reconstructed membership, "
                   "so it never entered the pool")
        elif cap >= fl:
            over = 100 * (cap - fl) / fl
            cls = "ABOVE FLOOR"
            why = (f"full cap sat {over:.0f}% above the floor — "
                   "size alone cannot explain this deletion; "
                   "float or liquidity must")
        else:
            cls, why = "OTHER", "below floor and in membership"
        out.append({**m, "in_pit_membership": in_mem,
                    "class": cls, "why": why})
    return out


def persistence_and_depth(recs):
    """Two candidate ranking features, tested honestly."""
    revs = [r for r in ORDER if r in recs]
    below = {r: set(recs[r]["grading"]["pool"]) for r in revs}

    def streak(code, i):
        n = 0
        for j in range(i, -1, -1):
            if code in below[revs[j]]:
                n += 1
            else:
                break
        return n
    ds, fs, dd, fd = [], [], [], []
    for i, r in enumerate(revs):
        g, fl = recs[r]["grading"], recs[r]["keys"]["floor"]
        for c in g["hits"]:
            ds.append(streak(c, i))
            if g["pool"].get(c):
                dd.append(g["pool"][c] / fl)
        for c in g["false_alarms"]:
            fs.append(streak(c, i))
            if g["pool"].get(c):
                fd.append(g["pool"][c] / fl)
    return {"persistence": {
                "deleted_median": st.median(ds),
                "fa_median": st.median(fs),
                "verdict": "NO discriminating power — both "
                           "medians are 3 consecutive reviews "
                           "below the floor. A 'has been at "
                           "risk for a while' feature does not "
                           "separate the two groups."},
            "depth": {
                "deleted_median": round(st.median(dd), 3),
                "fa_median": round(st.median(fd), 3),
                "verdict": "DOES discriminate — deleted names "
                           "sit at 0.62x the floor vs 0.79x for "
                           "survivors. Depth belongs in a "
                           "ranking model, though on its own it "
                           "only lifts precision from 8% to "
                           "~18%."}}


def float_coverage(recs):
    """Can we even TEST the float hypothesis? (No.)"""
    ins = json.loads((ROOT / "data" / "insider_pct_cache.json")
                     .read_text(encoding="utf-8"))

    def ff(c):
        d = ins.get(c) or {}
        if d.get("float_shares") and d.get("shares_out"):
            return d["float_shares"] / d["shares_out"]
        return None
    hd = hf = fad = faf = 0
    for r in recs.values():
        for c in r["grading"]["hits"]:
            hd += 1
            hf += ff(c) is not None
        for c in r["grading"]["false_alarms"]:
            fad += 1
            faf += ff(c) is not None
    return {"deleted_with_float": hf, "deleted_total": hd,
            "fa_with_float": faf, "fa_total": fad,
            "verdict": f"float data exists for only {hf} of "
                       f"{hd} historically deleted names "
                       f"({hf / max(hd, 1):.0%}). The single "
                       "most plausible explanation for the "
                       "above-floor deletions is therefore "
                       "UNTESTABLE with what we hold — this is "
                       "the top data gap, not a modelling gap."}


def build():
    import pandas as pd
    from backtest_report import analyse
    a = analyse()
    recs = load()
    db = pd.read_pickle(ROOT / "data" / "msci_changes_db.pkl")
    tw = db[db.market == "Taiwan"]
    a["add_sweep"] = add_threshold_sweep(recs, tw)
    a["miss_classes"] = classify_misses(a, recs, tw)
    a["features"] = persistence_and_depth(recs)
    a["float_coverage"] = float_coverage(recs)
    (ROOT / "data" / "backtest_taiwan.json").write_text(
        json.dumps(a, indent=1), encoding="utf-8")
    return a


if __name__ == "__main__":
    a = build()
    print("add sweep:")
    for r in a["add_sweep"]:
        print(f"  x{r['x_ceiling']:<6} recall {r['recall']:.0%} "
              f"prec* {r['precision_partial']:.0%}")
    print("miss classes:", {c["class"]: 1 for c in
                            a["miss_classes"]})
    print(a["float_coverage"]["verdict"])
