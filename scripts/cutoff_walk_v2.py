"""Cutoff walk v2 — the CORRECTED Taiwan 85% walk, real names
only (c-79).

Fixes vs the old calculation (Q23):
  1. DENOMINATOR: the old walk used the bottom-up $4,197B frame
     (150 tracked + a MODELED 400-name body) — later shown
     +11.4% high vs the factsheet-implied $3,745B. This walk
     replaces the modeled body with REAL census names (fund
     shares x last close from mieu_cache) and reports every
     frame side by side.
  2. RANK vs ACCUMULATE bases stated exactly (the old text
     muddied them): companies are RANKED by FULL market cap
     descending; coverage ACCUMULATES free-float-adjusted cap;
     the walk stops when cumulative float value crosses 85% of
     the float total; the CUTOFF is expressed as the crossing
     company's FULL cap. (GIMI segmentation convention — rank
     full, accumulate float, express full.)
  3. SCREENS applied before the walk (the old body skipped
     them): min size ~US$0.2B full cap, float >= 0.15, ATVR
     12m >= 15% where tape data allows.

Float sources, tiered and labeled: MSCI implied FIFs (members'
top-10) > v2 named-insider (members) > default 0.55 with a
[0.4, 0.7] sensitivity band (non-member census names — the
floats census phase upgrades these when run).

Usage: py scripts\\cutoff_walk_v2.py
Output: data/cutoff_walk_v2.json + printed summary
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

TWD = 29.5                      # TWD/USD (state; sensitivity small)
MIN_SIZE_USD = 0.2e9
DEFAULT_FF = 0.55
FF_BAND = (0.40, 0.70)
EM_REF = (15.75 * 1.042) / 2    # Q22/Q23 chain, unchanged
CORRIDOR = (0.5 * EM_REF, 1.15 * EM_REF)
IMPLIED_D = 3745.0              # factsheet-inverted, $B


TOP10_CODES = {"TAIWAN SEMICONDUCTOR MFG": "2330",
               "MEDIATEK": "2454", "HON HAI PRECISION IND":
               "2317", "DELTA ELECTRONICS": "2308",
               "QUANTA COMPUTER": "2382",
               "FUBON FINANCIAL HOLDINGS": "2881",
               "CTBC FINANCIAL HOLDING": "2891",
               "CATHAY FINANCIAL HOLDING": "2882",
               "UNITED MICROELECTRONICS": "2303",
               "E.SUN FINANCIAL HOLDING": "2884"}


def member_floats(fund, tape):
    """Member FIFs, tiered: (1) top-10 implied IN-FRAME — the
    factsheet's float cap / OUR census full cap, so head floats
    carry MSCI's own factors at our prices; (2) v2 named-insider
    floats for the rest (validated 0.022; known blind spot:
    board-seatless government stakes -> the top-10 override
    exists precisely for that)."""
    out = {}
    p = ROOT / "data" / "tw_float_mops_v2.json"
    if p.exists():
        for r in json.loads(p.read_text())["rows"]:
            out[r["code"]] = (min(float(r["float_v2"]), 1.0),
                              "v2_insiders")
    p = ROOT / "data" / "msci_factsheet_archive.json"
    if p.exists():
        arch = json.loads(p.read_text())
        latest = arch[sorted(arch)[-1]]
        for row in latest.get("top10", []):
            code = TOP10_CODES.get(row["name"])
            f, t = fund.get(code), tape.get(code)
            if code and f and f.get("shares") and t \
                    and t.get("close"):
                full_b = f["shares"] * t["close"] / TWD / 1e9
                fif = min(row["float_cap_busd"] / full_b, 1.0)
                out[code] = (fif, "msci_implied_inframe")
    return out


def build(default_ff=DEFAULT_FF):
    c = json.loads((ROOT / "data" / "mieu_cache.json").read_text())
    fund, tape = c["fund"], c["tape"]
    ffs = member_floats(fund, tape)
    rows, excl = [], {"no_data": 0, "min_size": 0, "atvr": 0,
                      "low_float": 0}
    for code, f in fund.items():
        t = tape.get(code)
        if not (f and f.get("shares") and t and t.get("close")):
            excl["no_data"] += 1
            continue
        cap = f["shares"] * t["close"] / TWD          # USD full
        if cap < MIN_SIZE_USD:
            excl["min_size"] += 1
            continue
        ff, src = ffs.get(code, (default_ff, "default"))
        if ff < 0.15:
            excl["low_float"] += 1
            continue
        atvr = (t["val_12m"] / TWD) / (cap * ff) \
            if cap * ff else 0.0
        if t.get("days", 0) >= 200 and atvr < 0.15:
            excl["atvr"] += 1
            continue
        rows.append({"code": code, "cap_b": cap / 1e9,
                     "ff": ff, "ff_src": src,
                     "float_b": cap * ff / 1e9})
    # THE WALK: rank FULL cap desc, accumulate FLOAT value
    rows.sort(key=lambda r: -r["cap_b"])
    D = sum(r["float_b"] for r in rows)
    target = 0.85 * D
    cum, cross = 0.0, None
    for i, r in enumerate(rows):
        cum += r["float_b"]
        if cross is None and cum >= target:
            cross = i
    res = {"n_pass": len(rows), "excluded": excl,
           "denominator_busd": round(D, 1),
           "gap_vs_implied_pct": round((D - IMPLIED_D)
                                       / IMPLIED_D * 100, 1),
           "target_busd": round(target, 1),
           "cross_rank": cross + 1,
           "cross_code": rows[cross]["code"],
           "cutoff_full_cap_busd": round(rows[cross]["cap_b"], 2),
           "corridor_busd": [round(x, 2) for x in CORRIDOR],
           "in_corridor": CORRIDOR[0] <= rows[cross]["cap_b"]
           <= CORRIDOR[1],
           "default_ff_share_pct": round(sum(
               r["float_b"] for r in rows
               if r["ff_src"] == "default") / D * 100, 1)}
    return res, rows


if __name__ == "__main__":
    base, rows = build()
    lo, _ = build(default_ff=FF_BAND[0])
    hi, _ = build(default_ff=FF_BAND[1])
    out = {"desc": "corrected walk: rank FULL cap / accumulate "
           "FLOAT / cutoff in FULL cap; real census names, "
           "screens applied; coverage partial until census "
           "completes", "base": base,
           "band": {"default_ff_0.40":
                    {k: lo[k] for k in ("denominator_busd",
                     "cutoff_full_cap_busd", "cross_rank")},
                    "default_ff_0.70":
                    {k: hi[k] for k in ("denominator_busd",
                     "cutoff_full_cap_busd", "cross_rank")}},
           "frames": {"census_walk": base["denominator_busd"],
                      "factsheet_implied": IMPLIED_D},
           "census_coverage": f"{base['n_pass']} pass of "
           f"{base['n_pass'] + sum(base['excluded'].values())} "
           "cached (2,146 target)"}
    (ROOT / "data" / "cutoff_walk_v2.json").write_text(
        json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))
