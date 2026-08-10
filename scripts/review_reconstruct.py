"""Phase 2: the PIT review reconstruction engine (c-110).

For a market + review (Taiwan first), rebuild MSCI's decision
with the data and rules OF THAT DAY:
  - the ACTUAL GMSR + EM range + DISCLOSED price cutoff date
    (edition-mined answer keys, gimi_editions_index.json)
  - PIT full caps: vintage close x shares AT the disclosed
    price date, / that month's FX (fx_twd_history.json)
  - PIT membership: reverse-rolled from today's members using
    the count-validated changes DB (off-cycle exits add known
    noise — 2 cases in TW, labeled)
  - frontiers under the TW corridor-binding convention:
    cutoff = EM-range ceiling (labeled ASSUMPTION; TW's
    crossing sits above the ceiling in every frame we can
    test), floor = 2/3 x ceiling, add bar = 1.5 x ceiling

VERDICTS per actual move: DEL explained if PIT cap < floor;
ADD explained if PIT cap >= bar; NEAR if within 20% of the
frontier; else NOT-EXPLAINED (L4 candidate).
GRADING per review: would OUR rules have called it? pool =
PIT members below floor -> hits / misses / false alarms.

Honesty labels carried in every output: floats current-vintage
(full-cap tests don't need them; half-bar gate SKIPPED
historically), pre-2023 QIRs use prevailing SAIR keys (the
discovered regime), corridor-binding is an assumption.

Usage:
  py scripts\\review_reconstruct.py one May26
  py scripts\\review_reconstruct.py batch     (Feb18 -> May26)
Output: data/reconstruct/TW_<review>.json + summary
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RDIR = ROOT / "data" / "reconstruct"

MON = {"January": 1, "February": 2, "March": 3, "April": 4,
       "May": 5, "June": 6, "July": 7, "August": 8,
       "September": 9, "October": 10, "November": 11,
       "December": 12}
_PRICE2REV = {4: "May", 7: "Aug", 10: "Nov", 1: "Feb"}


def _j(name):
    return json.loads((ROOT / "data" / name).read_text(encoding="utf-8"))


def answer_keys():
    """review label -> {gmsr, ceiling, floor, bar, price_date,
    source}. Pre-2023 QIRs inherit the prevailing SAIR key."""
    idx = _j("gimi_editions_index.json")["editions"]
    keys = {}
    for ed, g in idx.items():
        if not (g.get("gmsr_dm") and g.get("data_date")):
            continue
        m = re.match(r"([A-Z][a-z]+) (\d{1,2}) (\d{4})",
                     g["data_date"])
        if not m:
            continue
        mon, day, yr = m.group(1), int(m.group(2)), int(m.group(3))
        pm = MON[mon]
        rev_mon = _PRICE2REV.get(pm)
        if not rev_mon:
            continue
        ry = yr + (1 if pm == 1 and rev_mon == "Feb" else 0)
        rev = f"{rev_mon}{ry % 100:02d}"
        ceil = g["em_range"][1]
        rec = {"gmsr_dm": g["gmsr_dm"], "em_range": g["em_range"],
               "ceiling": ceil, "floor": round(2 / 3 * ceil, 3),
               "bar": round(1.5 * ceil, 3),
               "price_date": f"{yr}-{pm:02d}-{day:02d}",
               "source": ed}
        if rev in keys and keys[rev]["gmsr_dm"] != rec["gmsr_dm"]:
            raise SystemExit(f"HALT: conflicting keys for {rev}")
        keys[rev] = rec
    # pre-2023 QIRs inherit prevailing SAIR (the regime)
    order = [f"{m}{y % 100:02d}" for y in range(2018, 2027)
             for m in ("Feb", "May", "Aug", "Nov")]
    prev = None
    for rev in order:
        if rev in keys:
            prev = rev
        elif prev and int("20" + rev[-2:]) < 2023 \
                and rev[:3] in ("Feb", "Aug"):
            keys[rev] = {**keys[prev],
                         "source": f"prevailing {prev} "
                         "(pre-2023 QIR regime)",
                         "price_date": keys[prev]["price_date"]}
    return keys


def _fx(date):
    fx = _j("fx_twd_history.json")
    ym = date[:7]
    return fx.get(ym) or fx[min(fx, key=lambda k:
                                abs(int(k[:4]) * 12 + int(k[5:7])
                                    - int(ym[:4]) * 12
                                    - int(ym[5:7])))]


def pit_members(review, order, changes):
    """Reverse-roll today's TW members to just BEFORE the
    review: undo every change at or after it."""
    mem = set(_j("apac_members.json")["markets"]["Taiwan"]
              ["standard_members"])
    idx = order.index(review)
    later = [r for r in order[idx:]]
    for _, row in changes.iterrows():
        if row.review in later and row.code:
            if row.action == "ADD":
                mem.discard(row.code)
            else:
                mem.add(row.code)
    return mem


def reconstruct(review):
    import pandas as pd
    keys = answer_keys()
    if review not in keys:
        return {"review": review, "error": "no answer key "
                "(2015-17 hole or out of scope)"}
    k = keys[review]
    fx = _fx(k["price_date"])
    vint = _j("tw_vintage_cache.json")
    df = pd.read_pickle(ROOT / "data" / "msci_changes_db.pkl")
    tw = df[(df.market == "Taiwan")]
    order = [f"{m}{y % 100:02d}" for y in range(2015, 2027)
             for m in ("Feb", "May", "Aug", "Nov")]

    def cap_at(code, date):
        px = vint.get(f"px|{code}")
        sh = vint.get(f"sh|{code}")
        if not (px and sh):
            return None
        p = next((r["close"] for r in reversed(px)
                  if r["date"] <= date), None)
        s = next((r["NumberOfSharesIssued"] for r in reversed(sh)
                  if r["date"] <= date), None)
        return p * s / fx / 1e9 if p and s else None

    moves = tw[tw.review == review]
    verdicts = []
    for _, r in moves.iterrows():
        cap = cap_at(r.code, k["price_date"]) if r.code else None
        if cap is None:
            v = "NO PIT DATA (code unresolved or off-cache)"
        elif r.action == "DEL":
            m = (cap - k["floor"]) / k["floor"]
            v = (f"EXPLAINED: {cap:.2f}B is {-m:.0%} below the "
                 f"{k['floor']}B floor" if cap < k["floor"] else
                 f"NEAR-MISS: {cap:.2f}B is {m:.0%} ABOVE the "
                 f"floor" if m < 0.2 else
                 f"NOT-EXPLAINED: {cap:.2f}B well above floor")
        else:
            m = (cap - k["bar"]) / k["bar"]
            v = (f"EXPLAINED: {cap:.2f}B clears the {k['bar']}B "
                 f"bar by {m:.0%}" if cap >= k["bar"] else
                 f"NEAR-MISS: {cap:.2f}B is {-m:.0%} below the "
                 f"bar" if -m < 0.2 else
                 f"NOT-EXPLAINED: {cap:.2f}B well below bar")
        verdicts.append({"code": r.code, "security": r.security,
                         "action": r.action,
                         "pit_cap_busd": round(cap, 2)
                         if cap else None, "verdict": v})
    # grading: our pool vs actual dels
    mem = pit_members(review, order, tw[tw.code != ""])
    pool = {}
    for c in mem:
        cap = cap_at(c, k["price_date"])
        if cap is not None and cap < k["floor"]:
            pool[c] = round(cap, 2)
    actual_dels = set(moves[moves.action == "DEL"].code) - {""}
    hits = sorted(pool.keys() & actual_dels)
    misses = sorted(actual_dels - pool.keys())
    false_alarms = sorted(pool.keys() - actual_dels)
    out = {"market": "Taiwan", "review": review, "keys": k,
           "fx_used": fx,
           "labels": ["floats current-vintage (full-cap tests "
                      "only; half-bar skipped)",
                      "cutoff = EM ceiling (TW corridor-binding "
                      "assumption)",
                      "membership reverse-rolled (2 known "
                      "off-cycle noise cases)"],
           "verdicts": verdicts,
           "grading": {"pool": pool, "hits": hits,
                       "misses": misses,
                       "false_alarms": false_alarms}}
    RDIR.mkdir(exist_ok=True)
    (RDIR / f"TW_{review}.json").write_text(
        json.dumps(out, indent=1), encoding="utf-8")
    return out


def batch():
    order = [f"{m}{y % 100:02d}" for y in range(2018, 2027)
             for m in ("Feb", "May", "Aug", "Nov")]
    order = order[:order.index("Aug26")]
    summ = []
    for rev in order:
        o = reconstruct(rev)
        if "error" in o:
            summ.append({"review": rev, "note": o["error"]})
            continue
        g = o["grading"]
        expl = sum(1 for v in o["verdicts"]
                   if v["verdict"].startswith("EXPLAINED"))
        summ.append({"review": rev,
                     "moves": len(o["verdicts"]),
                     "explained": expl,
                     "del_hits": len(g["hits"]),
                     "del_misses": len(g["misses"]),
                     "false_alarms": len(g["false_alarms"])})
        print(f"{rev}: {len(o['verdicts'])} moves, {expl} "
              f"explained | dels {len(g['hits'])}H/"
              f"{len(g['misses'])}M/{len(g['false_alarms'])}FA")
    (ROOT / "data" / "reconstruct_summary.json").write_text(
        json.dumps(summ, indent=1), encoding="utf-8")
    print("summary written")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "batch"
    if cmd == "one":
        print(json.dumps(reconstruct(sys.argv[2]), indent=1))
    else:
        batch()
