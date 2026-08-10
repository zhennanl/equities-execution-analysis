"""The Market Investable Equity Universe, built the rulebook's
way (c-123) — all seven §2.2 screens, each with its data source
or an honest NOT_EVALUATED label.

Bill's proposal, implemented: build the MIEU with the full
screen chain, then put the best float estimate on every
qualified company, then walk §2.3.3 to the 85% rank.

SCREENS (May-2026 GIMI):
  2.2.3 full mkt cap >= $537M          exchange px x shares (PIT)
  2.2.4 float cap >= 50% x $537M       float stack (below)
  2.2.5 liquidity: 12m ATVR >= 15%,    TWSE FMSRFK monthly
        3m ATVR >= 15%, freq >= 80%    turnover / ff;
                                       TPEx = NOT_EVALUATED
  2.2.6 minimum FIF (>= 0.15 proxy)    float stack
  2.2.7 length of trading (>= 3 mo)    listing date, both boards
  2.2.8 foreign room >= 15%            TWSE MI_QFIIS: (FOL -
                                       held)/FOL; no FOL = pass
  2.2.9 financial reporting            NOT_EVALUATED (needs
                                       filing calendars; rarely
                                       binding for seasoned names)

FLOAT STACK (measured accuracy, spec §3c):
  factsheet-implied > Yahoo (2.7%) > TDCC x calibration > 0.55

Usage:  py scripts\\tw_mieu_build.py [YYYYMMDD]
Output: data/tw_mieu_universe.json + console walk summary
"""
import json
import statistics as st
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UNI = ROOT / "data" / "tw_universe_pit.json"
ATVR = ROOT / "data" / "tw_atvr.json"
OUT = ROOT / "data" / "tw_mieu_universe.json"
UA = {"User-Agent": "Mozilla/5.0"}
EU_MIN = 0.537

sys.path.insert(0, str(ROOT / "scripts"))


def listing_dates():
    """Both boards, cached to data/tw_listing_dates.json."""
    p = ROOT / "data" / "tw_listing_dates.json"
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    import requests
    out = {}
    tw = requests.get(
        "https://openapi.twse.com.tw/v1/opendata/t187ap03_L",
        headers=UA, timeout=45).json()
    for r in tw:
        c, d = r.get("公司代號"), r.get("上市日期")
        if c and d and len(d) == 8:
            out[c] = f"{d[:4]}-{d[4:6]}-{d[6:]}"
    tp = requests.get(
        "https://www.tpex.org.tw/openapi/v1/mopsfin_t187ap03_O",
        headers=UA, timeout=45).json()
    for r in tp:
        c = r.get("SecuritiesCompanyCode")
        d = str(r.get("DateOfListing") or "")
        if c and len(d) == 7 and d.isdigit():      # ROC era
            out.setdefault(c, f"{1911 + int(d[:3])}-"
                              f"{d[3:5]}-{d[5:]}")
        elif c and len(d) == 8 and d.isdigit():
            out.setdefault(c, f"{d[:4]}-{d[4:6]}-{d[6:]}")
    p.write_text(json.dumps(out), encoding="utf-8")
    return out


def atvr_stats(code, ff):
    """(atvr_12m, atvr_3m, freq) or None if not evaluated."""
    if not ATVR.exists():
        return None
    m = json.loads(ATVR.read_text(encoding="utf-8"))["months"].get(code)
    if not m or not m.get("rows"):
        return None
    rows = m["rows"]
    tos = [r["turnover_pct"] / 100 for r in rows]
    if not tos or not ff:
        return None
    a12 = 12 * st.median(tos) / ff
    a3 = 12 * st.median(tos[-3:]) / ff
    freq = sum(1 for r in rows if (r.get("value_twd") or 0) > 0
               ) / len(rows)
    return round(a12, 3), round(a3, 3), round(freq, 3)


def build(date="20260420"):
    from tw_walk_display import float_stack
    u = json.loads(UNI.read_text(encoding="utf-8"))
    if date not in u["dates"]:
        raise SystemExit(f"{date} not harvested")
    rows = u["dates"][date]["rows"]
    ff, cal = float_stack(u, date)
    ld = listing_dates()
    pd_iso = f"{date[:4]}-{date[4:6]}-{date[6:]}"
    uni, audit = {}, {"listed": len(rows)}
    drops = {k: 0 for k in ("size", "float_cap", "liquidity",
                            "fif", "trading_age", "foreign_room")}
    not_eval = {"liquidity_tpex": 0, "liquidity_no_data": 0,
                "financial_reporting": "NOT_EVALUATED (all)"}
    for c, r in rows.items():
        cap = r.get("cap_usd_b") or 0
        f, src = ff[c]
        fcap = cap * f
        # 2.2.3
        if cap < EU_MIN:
            drops["size"] += 1
            continue
        # 2.2.4
        if fcap < 0.5 * EU_MIN:
            drops["float_cap"] += 1
            continue
        # 2.2.6 (proxy: MSCI global minimum FIF)
        if f < 0.15:
            drops["fif"] += 1
            continue
        # 2.2.7 — listed >= 3 months before the price date
        lday = ld.get(c)
        if lday and lday > pd_iso[:8] + "01":
            pass
        if lday:
            yy, mm = int(lday[:4]), int(lday[5:7])
            py, pm = int(date[:4]), int(date[4:6])
            if (py - yy) * 12 + (pm - mm) < 3:
                drops["trading_age"] += 1
                continue
        # 2.2.8 — foreign room where an FOL exists
        fol, held = r.get("fol"), r.get("foreign") or 0
        if fol and fol < 1.0:
            room = (fol - held) / fol
            if room < 0.15:
                drops["foreign_room"] += 1
                continue
        # 2.2.5 — where evaluable
        a = atvr_stats(c, f)
        if a is None:
            if r["mkt"] == "tpex":
                not_eval["liquidity_tpex"] += 1
            else:
                not_eval["liquidity_no_data"] += 1
        else:
            a12, a3, freq = a
            if a12 < 0.15 or a3 < 0.15 or freq < 0.80:
                drops["liquidity"] += 1
                continue
        uni[c] = {"cap": cap, "ff": f, "src": src,
                  "fcap": round(fcap, 4), "mkt": r["mkt"],
                  "atvr": a}
    # ---- the walk (§2.3.3) ------------------------------
    srt = sorted(uni.items(), key=lambda x: -x[1]["cap"])
    tot = sum(v["fcap"] for _, v in srt)
    run, cross = 0.0, None
    for i, (c, v) in enumerate(srt, 1):
        run += v["fcap"]
        if cross is None and run >= 0.85 * tot:
            cross = {"rank": i, "code": c,
                     "cutoff_usd_b": round(v["cap"], 3)}
    out = {"date": date, "fx": u["dates"][date]["fx"],
           "float_calibration": cal,
           "screens_dropped": drops,
           "not_evaluated": not_eval,
           "mieu_n": len(uni),
           "universe_float_usd_b": round(tot, 1),
           "crossing": cross,
           "universe": {c: v for c, v in srt}}
    OUT.write_text(json.dumps(out), encoding="utf-8")
    print(f"date {date} | listed {audit['listed']:,}")
    print("dropped:", {k: v for k, v in drops.items() if v})
    print("not evaluated:", not_eval)
    print(f"MIEU: {len(uni)} companies | float ${tot:,.0f}B")
    if cross:
        print(f"85% crossing: rank {cross['rank']} = "
              f"{cross['code']} at ${cross['cutoff_usd_b']}B")
        print("TARGET (May-26): rank 77, $5.19B, "
              "universe float $3,537-3,979B")
    print(f"-> {OUT.name}")
    return out


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else "20260420")
