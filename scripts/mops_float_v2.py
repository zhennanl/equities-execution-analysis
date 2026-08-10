"""Float estimator v2 — NAMED insiders (the MOPS approach) (c-52).

The TDCC v1 failed because size brackets cannot tell a founder
from a fund (Q17). v2 uses the insider-holdings percentage —
directors, officers, controlling holders as NAMED in filings
(MOPS-sourced, served via Yahoo's heldPercentInsiders field, which
IS reachable from this environment while MOPS itself is not):

    float_v2 = 1 - insiders_held_pct     (bounded [0.05, 1.0])

Known residual (stated): government stakes without board seats can
escape the insider table (Taiwan Semiconductor's development-fund
stake), so v2 will over-float a few state-invested names.

Grades 3-way vs MSCI's implied factors (incumbent 0.104, TDCC v1
0.143) + the $739.8B aggregate. Resumable cache.

Usage: python scripts/mops_float_v2.py [--limit N]
"""
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

CACHE = ROOT / "data" / "insider_pct_cache.json"
OUT = ROOT / "data" / "tw_float_mops_v2.json"
FIFS = {"2330": 0.955, "2454": 0.905, "2308": 0.754,
        "3711": 0.750, "2383": 0.805, "2881": 0.603,
        "2891": 0.855, "2345": 0.905}


def members():
    import datetime
    from agents.pit_constituents import ladder_asof
    L = ladder_asof(str(datetime.date.today()))
    return sorted([r for r in L["ladder"] if r["member"]],
                  key=lambda r: -r["cap_usd_b"])


def harvest(limit=None):
    import yfinance as yf
    cache = json.loads(CACHE.read_text(encoding="utf-8")) if CACHE.exists() else {}
    mem = members()
    todo = [r["code"] for r in mem if r["code"] not in cache]
    if limit:
        todo = todo[:int(limit)]
    print(f"{len(todo)} to fetch of {len(mem)} members")
    for i, c in enumerate(todo):
        got = None
        for suf in (".TW", ".TWO"):
            try:
                info = yf.Ticker(c + suf).info
                if info.get("sharesOutstanding"):
                    got = {"insiders": info.get(
                        "heldPercentInsiders"),
                        "float_shares": info.get("floatShares"),
                        "shares_out": info.get(
                            "sharesOutstanding")}
                    break
            except Exception:                  # noqa: BLE001
                continue
        cache[c] = got or {"insiders": None}
        if (i + 1) % 5 == 0 or i == len(todo) - 1:
            tmp = CACHE.with_suffix(".tmp")
            tmp.write_text(json.dumps(cache), encoding="utf-8")
            tmp.replace(CACHE)
        time.sleep(0.4)
    print("cached:", sum(1 for v in cache.values()
                         if v.get("insiders") is not None))


def grade():
    import statistics as st
    cache = json.loads(CACHE.read_text(encoding="utf-8"))
    mem = members()
    tdcc = {r["code"]: r for r in json.loads(
        (ROOT / "data" / "tw_float_tdcc.json").read_text(encoding="utf-8"))["rows"]}
    rows, miss = [], []
    for r in mem:
        c = r["code"]
        v = cache.get(c) or {}
        ins = v.get("insiders")
        if ins is None:
            miss.append(c)
            continue
        f2 = round(min(max(1 - ins, 0.05), 1.0), 3)
        old = tdcc.get(c, {}).get("float_old", 0.7)
        rows.append({"code": c, "company": r["company"][:24],
                     "insiders_pct": round(ins, 4),
                     "float_v2": f2, "float_old": old,
                     "cap_usd_b": r["cap_usd_b"]})
    e2 = [abs(x["float_v2"] - FIFS[x["code"]]) for x in rows
          if x["code"] in FIFS]
    eo = [abs(x["float_old"] - FIFS[x["code"]]) for x in rows
          if x["code"] in FIFS]
    top10 = {r["code"] for r in mem[:10]}
    res2 = sum(x["cap_usd_b"] * x["float_v2"] for x in rows
               if x["code"] not in top10)
    reso = sum(x["cap_usd_b"] * x["float_old"] for x in rows
               if x["code"] not in top10)
    out = {"recipe": "float_v2 = 1 - insiders_held_pct (named "
                     "directors/officers/controlling holders, "
                     "filings-sourced); residual stated: "
                     "board-seatless government stakes escape",
           "n_estimated": len(rows), "missing": miss,
           "rows": rows,
           "grading": {
               "vs_msci_fifs": {c: {"v2": next(
                   (x["float_v2"] for x in rows
                    if x["code"] == c), None), "msci": f}
                   for c, f in FIFS.items()},
               "mean_abs_err_v2": round(st.mean(e2), 3),
               "mean_abs_err_old": round(st.mean(eo), 3),
               "mean_abs_err_tdcc_v1": 0.143,
               "residual67_v2_busd": round(res2, 0),
               "residual67_old_busd": round(reso, 0),
               "residual67_target_busd": 739.8}}
    OUT.write_text(json.dumps(out, indent=1), encoding="utf-8")
    g = out["grading"]
    print(f"v2 mean abs err {g['mean_abs_err_v2']} | incumbent "
          f"{g['mean_abs_err_old']} | TDCC v1 0.143")
    print(f"residual-67: v2 {g['residual67_v2_busd']} | old "
          f"{g['residual67_old_busd']} | target 739.8")
    for c, f in FIFS.items():
        v = g["vs_msci_fifs"][c]["v2"]
        print(f"  {c}: v2 {v} vs MSCI {f}")
    return out


if __name__ == "__main__":
    lim = None
    if "--limit" in sys.argv:
        lim = sys.argv[sys.argv.index("--limit") + 1]
    harvest(lim)
    if not lim:
        grade()
