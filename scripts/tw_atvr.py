"""ATVR inputs for the §2.2.5 liquidity screen (c-123).

MSCI's EM Minimum Liquidity Requirement (§2.2.5) wants, per
security: 15% 12-month ATVR, 15% 3-month ATVR, and 80% monthly
frequency of trading. ATVR is the ANNUALIZED TRADED VALUE
RATIO, computed by MSCI from monthly medians of traded value
over FLOAT-adjusted capitalization.

DATA: TWSE FMSRFK serves, in ONE call per stock per YEAR:
monthly traded value, share volume, and — the shortcut — the
monthly TURNOVER on total shares (週轉率%). Our ATVR estimate:

    atvr_12m = 12 x median(monthly turnover%) / ff

dividing by float because MSCI's ratio is on float cap while
TWSE's turnover is on total shares. Two calls per stock cover
the trailing 12 months (calendar years Y and Y-1).

TPEx: no per-stock monthly endpoint found (probed
perMonth/stkMonthly/monthlyTrading/openapi catalogue —
registered gap). TPEx names are labeled NOT_EVALUATED by the
screen, never silently passed or failed.

Usage:  py scripts\\tw_atvr.py run [--limit N]
Resumable: data/tw_atvr.json
"""
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UNI = ROOT / "data" / "tw_universe_pit.json"
OUT = ROOT / "data" / "tw_atvr.json"
UA = {"User-Agent": "Mozilla/5.0"}
ASOF = "20260731"       # trailing-12m window ends here
CAND_MIN_CAP = 0.40     # harvest a margin below the $0.537B screen


def _num(s):
    try:
        return float(str(s).replace(",", "").strip())
    except (ValueError, AttributeError):
        return None


def candidates():
    u = json.loads(UNI.read_text(encoding="utf-8"))
    codes = set()
    for d in ("20260420", "20260720"):
        for c, r in u["dates"].get(d, {}).get("rows", {}).items():
            if (r.get("cap_usd_b") or 0) >= CAND_MIN_CAP:
                codes.add((c, r["mkt"]))
    return sorted(codes)


def fetch_year(code, year):
    """FMSRFK: one call = one calendar year of monthly rows."""
    import requests
    u = ("https://www.twse.com.tw/rwd/zh/afterTrading/FMSRFK"
         f"?date={year}0731&stockNo={code}&response=json")
    j = requests.get(u, headers=UA, timeout=30).json()
    if j.get("stat") != "OK" or not j.get("data"):
        return []
    out = []
    for r in j["data"]:
        # fields: 年度,月份,最高,最低,均價,筆數,成交金額,成交股數,週轉率%
        yy, mm, to = r[0], r[1], _num(r[8])
        val = _num(r[6])
        if to is not None:
            out.append({"ym": f"{1911 + int(yy)}-{int(mm):02d}",
                        "turnover_pct": to,
                        "value_twd": val})
    return out


def run(limit=None):
    cache = (json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists()
             else {"asof": ASOF, "months": {}})
    cand = candidates()
    todo = [(c, m) for c, m in cand
            if c not in cache["months"] and m == "twse"]
    tpex = [c for c, m in cand if m == "tpex"]
    for c in tpex:
        cache["months"].setdefault(
            c, {"note": "TPEX — no monthly endpoint, "
                        "NOT_EVALUATED"})
    if limit:
        todo = todo[:int(limit)]
    print(f"{len(todo)} TWSE names to fetch "
          f"({len(tpex)} TPEx marked NOT_EVALUATED)", flush=True)
    fails = 0
    for i, (c, _) in enumerate(todo):
        rows = []
        for yr in (2025, 2026):
            try:
                rows += fetch_year(c, yr)
            except Exception as e:                 # noqa: BLE001
                fails += 1
                print(f"  {c}/{yr}: {type(e).__name__}",
                      flush=True)
            # c-123: TWSE throttles sustained pulls — pace at
            # 2.5s (0.8s starved every request into a 30s
            # timeout; ~fresh single calls succeeded, which is
            # the burst-limiter signature)
            time.sleep(2.5)
        # trailing 12 months ending ASOF
        end = f"{ASOF[:4]}-{ASOF[4:6]}"
        keep = sorted([r for r in rows if r["ym"] <= end],
                      key=lambda r: r["ym"])[-12:]
        cache["months"][c] = {"rows": keep}
        OUT.write_text(json.dumps(cache), encoding="utf-8")      # save every name
        if (i + 1) % 10 == 0:
            print(f"  {i + 1}/{len(todo)} "
                  f"(fails {fails})", flush=True)
    OUT.write_text(json.dumps(cache), encoding="utf-8")
    got = sum(1 for v in cache["months"].values()
              if v.get("rows"))
    print(f"done: {got} names with monthly data -> {OUT.name}",
          flush=True)


if __name__ == "__main__":
    a = sys.argv[1:]
    lim = a[a.index("--limit") + 1] if "--limit" in a else None
    run(lim)
