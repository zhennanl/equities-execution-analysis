"""Full Taiwan universe, point-in-time, from exchange bulk feeds
(c-120).

WHY THIS EXISTS: the c-116 backtest found that our 148-name
universe was missing ~11% of the market's float mass, which
made every 85%-coverage cutoff wrong before float accuracy even
mattered. Fixing it does NOT need per-name scraping — Taiwan
publishes everything in bulk, dated.

FOUR SOURCES, all free, all dated, ~4 calls per date:

  1. TWSE  /rwd/zh/afterTrading/MI_INDEX?date=&type=ALL
     every listed security's close ON THAT DATE (table
     '每日收盤行情(全部)', ~30k rows incl. warrants/ETFs/bonds).

  2. TWSE  /rwd/zh/fund/MI_QFIIS?date=&selectType=ALLBUT0999
     per security AT THAT DATE: 發行股數 (shares outstanding —
     so shares are POINT-IN-TIME, not today's), 全體外資及陸資
     持股比率 (foreign holding %), and 法令投資上限比率 (the
     Foreign Ownership Limit, needed for GIMI §2.3.6.2).

  3. TPEx  /www/zh-tw/afterTrading/otc?date=YYYY/MM/DD&type=EW
     TPEx closes AND 發行股數 in the same response.

  4. TDCC  opendata.tdcc.com.tw/getOD.ashx?id=1-5
     shareholding dispersion for ~4,000 securities. Bracket 15
     = holders above 1,000,000 shares; bracket 17 = total.
     Only the LATEST week is served, so the float proxy carries
     a small date offset from the price date — labelled, not
     hidden.

FLOAT PROXY (v1 recipe, carried over from tw_float_tdcc.json):
    float = 1 - max(bracket15_share - foreign_share, 0)
Rationale: bracket 15 lumps strategic holders WITH foreign
institutions; foreign holdings are float, so they are added
back. Known residual: domestic funds and insurers sitting in
bracket 15 are wrongly treated as strategic. This is a PROXY
for MSCI's FIF, not MSCI's FIF — MSCI classifies holders by
investor type (Appendix VI) using rules published separately.

PRICE DATE: GIMI §3.1.9 lets MSCI use any one of the last 10
business days of July for the August review. All ten are
harvested so downstream work carries a date-uncertainty band
rather than a point guess.

Usage:
  py scripts\\tw_universe_pit.py harvest        (all 10 dates)
  py scripts\\tw_universe_pit.py harvest 20260720
Output: data/tw_universe_pit.json
"""
import csv
import io
import json
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "tw_universe_pit.json"
UA = {"User-Agent": "Mozilla/5.0"}

# last 10 business days of July 2026 (GIMI §3.1.9 window for
# the August review). Non-trading days simply return no data.
WINDOW = ["20260720", "20260721", "20260722", "20260723",
          "20260724", "20260727", "20260728", "20260729",
          "20260730", "20260731"]


def _num(s):
    try:
        return float(str(s).replace(",", "").strip())
    except (ValueError, AttributeError):
        return None


def twse_prices(date):
    """{code: close} for every 4-digit TWSE common stock."""
    import requests
    u = ("https://www.twse.com.tw/rwd/zh/afterTrading/MI_INDEX"
         f"?date={date}&type=ALL&response=json")
    j = requests.get(u, headers=UA, timeout=60).json()
    if j.get("stat") != "OK":
        return {}
    tb = [t for t in j.get("tables", [])
          if t.get("fields") and t["fields"][0] == "證券代號"]
    if not tb:
        return {}
    out = {}
    for r in tb[0]["data"]:
        c = r[0].strip()
        # 4-digit, not starting 00 (that range is ETFs/funds)
        if re.fullmatch(r"\d{4}", c) and not c.startswith("00"):
            p = _num(r[8])
            if p:
                out[c] = p
    return out


def twse_shares_foreign(date):
    """{code: (shares, foreign_pct, FOL_pct)} at that date."""
    import requests
    u = ("https://www.twse.com.tw/rwd/zh/fund/MI_QFIIS"
         f"?date={date}&selectType=ALLBUT0999&response=json")
    j = requests.get(u, headers=UA, timeout=60).json()
    out = {}
    for r in j.get("data", []):
        c = str(r[0]).strip()
        if not (re.fullmatch(r"\d{4}", c)
                and not c.startswith("00")):
            continue
        sh, fp, fol = _num(r[3]), _num(r[7]), _num(r[8])
        if sh:
            out[c] = (sh, (fp or 0) / 100,
                      (fol / 100) if fol else None)
    return out


def tpex(date):
    """{code: (close, shares)} — TPEx serves both together."""
    import requests
    d = f"{date[:4]}%2F{date[4:6]}%2F{date[6:]}"
    u = ("https://www.tpex.org.tw/www/zh-tw/afterTrading/otc"
         f"?date={d}&type=EW&id=&response=json")
    j = requests.get(u, headers=UA, timeout=60).json()
    out = {}
    for t in j.get("tables", []):
        f = t.get("fields") or []
        if not f or "代號" not in f[0]:
            continue
        try:
            ci, si = 2, f.index([x for x in f
                                 if "發行股數" in x][0])
        except (ValueError, IndexError):
            continue
        for r in t["data"]:
            c = str(r[0]).strip()
            if not (re.fullmatch(r"\d{4}", c)
                    and not c.startswith("00")):
                continue
            p, sh = _num(r[ci]), _num(r[si])
            if p and sh:
                out[c] = (p, sh)
    return out


def tdcc():
    """{code: (bracket15_share, total_shares, asof)} — the
    float proxy input. Latest week only."""
    import requests
    r = requests.get(
        "https://opendata.tdcc.com.tw/getOD.ashx?id=1-5",
        headers=UA, timeout=90)
    rows = list(csv.reader(io.StringIO(r.text)))
    agg, asof = {}, None
    for x in rows[1:]:
        if len(x) < 6:
            continue
        asof = asof or x[0].strip()
        c, lvl, sh = x[1].strip(), x[2].strip(), _num(x[4])
        if sh is None:
            continue
        d = agg.setdefault(c, {})
        d[lvl] = sh
    out = {}
    for c, d in agg.items():
        tot = d.get("17")
        b15 = d.get("15")
        if tot and b15 is not None and tot > 0:
            out[c] = (b15 / tot, tot, asof)
    return out


def _fx(date):
    fx = json.loads((ROOT / "data" / "fx_twd_history.json")
                    .read_text(encoding="utf-8"))
    ym = f"{date[:4]}-{date[4:6]}"
    if ym in fx:
        return fx[ym], ym
    k = max(fx)
    return fx[k], k + " (nearest available)"


def _retry(fn, d, tries=3):
    """TWSE throttles bulk pulls; back off rather than hang."""
    for i in range(tries):
        try:
            return fn(d)
        except Exception as e:                    # noqa: BLE001
            if i == tries - 1:
                print(f"   {fn.__name__} failed: "
                      f"{type(e).__name__}", flush=True)
                return {}
            time.sleep(5 * (i + 1))
    return {}


def harvest(dates=None):
    """RESUMABLE (c-120): each date is written as soon as it
    lands, so a throttled or interrupted run resumes instead of
    starting over."""
    dates = dates or WINDOW
    out = (json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists()
           else {"source": "TWSE MI_INDEX + MI_QFIIS, TPEx otc, "
                           "TDCC opendata 1-5",
                 "float_recipe":
                     "1 - max(TDCC bracket-15 share - foreign "
                     "holding share, 0); a PROXY for MSCI FIF, "
                     "not FIF",
                 "tdcc_date_offset_note":
                     "TDCC serves only the latest week, so the "
                     "float proxy post-dates the price date by "
                     "up to ~2 weeks. Float moves slowly; "
                     "labelled, not hidden.",
                 "dates": {}})
    todo = [d for d in dates if d not in out["dates"]]
    if not todo:
        print("all dates already harvested")
        return out
    td = tdcc()
    asof_tdcc = next(iter(td.values()))[2] if td else "?"
    out["tdcc_asof"] = asof_tdcc
    print(f"TDCC dispersion: {len(td)} securities, as of "
          f"{asof_tdcc} | {len(todo)} dates to fetch", flush=True)
    for d in todo:
        px = _retry(twse_prices, d)
        sf = _retry(twse_shares_foreign, d)
        tp = _retry(tpex, d)
        if not px and not tp:
            print(f"{d}: no data (non-trading day)", flush=True)
            out["dates"][d] = {"n": 0, "note": "no data",
                               "rows": {}}
            OUT.write_text(json.dumps(out), encoding="utf-8")
            continue
        fx, fxsrc = _fx(d)
        rows = {}
        for c, p in px.items():
            s = sf.get(c)
            if not s:
                continue
            rows[c] = {"mkt": "twse", "close": p,
                       "shares": s[0], "foreign": s[1],
                       "fol": s[2]}
        for c, (p, sh) in tp.items():
            rows.setdefault(c, {"mkt": "tpex", "close": p,
                                "shares": sh,
                                "foreign": (sf.get(c) or
                                            (None, 0, None))[1],
                                "fol": None})
        for c, r in rows.items():
            t = td.get(c)
            b15 = t[0] if t else None
            r["b15"] = b15
            if b15 is None:
                r["ff"] = None
                r["ff_src"] = "no TDCC"
            else:
                r["ff"] = round(
                    1 - max(b15 - (r["foreign"] or 0), 0), 4)
                r["ff_src"] = "tdcc-b15 less foreign"
            r["cap_usd_b"] = round(
                r["close"] * r["shares"] / fx / 1e9, 4)
            r["ffcap_usd_b"] = (round(r["cap_usd_b"] * r["ff"], 4)
                                if r["ff"] is not None else None)
        have = sum(1 for r in rows.values() if r["ff"] is not None)
        out["dates"][d] = {"fx": fx, "fx_src": fxsrc,
                           "n": len(rows), "n_with_float": have,
                           "rows": rows}
        tot = sum(r["ffcap_usd_b"] for r in rows.values()
                  if r["ffcap_usd_b"])
        print(f"{d}: {len(rows):5d} companies "
              f"({sum(1 for r in rows.values() if r['mkt'] == 'twse')} "
              f"TWSE / "
              f"{sum(1 for r in rows.values() if r['mkt'] == 'tpex')} "
              f"TPEx) | float data {have} | FX {fx} | "
              f"aggregate float cap ${tot:,.0f}B", flush=True)
        OUT.write_text(json.dumps(out), encoding="utf-8")      # incremental save
        time.sleep(1.2)
    OUT.write_text(json.dumps(out), encoding="utf-8")
    print(f"\n-> {OUT.name} ({OUT.stat().st_size / 1e6:.1f} MB, "
          f"{len(out['dates'])} dates)")
    return out


if __name__ == "__main__":
    a = sys.argv[1:]
    if a and a[0] == "harvest":
        harvest(a[1:] or None)
    else:
        harvest()
