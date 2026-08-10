"""APAC-wide implied-FIF extraction and float-source comparison
(c-124) — Bill's TW method, repeated for every market.

METHOD (validated on Taiwan, where the implied top-10 float sum
ties the factsheet's own total to $0.01B):
  implied_FIF = factsheet float-adj cap  /  full market cap
Divide MSCI's published number by an independent full cap and
the float assumption pops out. Grading any float source against
these implied FIFs is grading it against MSCI itself.

INPUTS
  data/factsheets/msci_<mkt>_2026-07.pdf   TOP 10 float caps
                                           (as of Jul-31-2026)
  Yahoo fast_info                          full market cap
  Yahoo get_info floatShares/sharesOut     the candidate
                                           universal float src

DATE CAVEAT, stated not hidden: Yahoo caps are CURRENT (~Aug-7)
while the factsheet is Jul-31 — a ~1-week drift enters every
implied FIF. On Taiwan (where we had exact Jul-31 caps) the
method tied exactly; here the drift adds noise of a few percent
in volatile names. The comparison still ranks sources; it just
cannot certify 1-2% differences.

Stages (each resumable):
  parse    factsheets -> data/apac_factsheet_top10.json
  map      names -> local tickers -> Yahoo symbols
  harvest  Yahoo caps + floats (resumable cache)
  report   the comparison table -> data/apac_fif_compare.json

Usage: py scripts\\apac_fif_compare.py all
       py scripts\\apac_fif_compare.py harvest   (resume)
       py scripts\\apac_fif_compare.py report
"""
import json
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
FS = ROOT / "data" / "apac_factsheet_top10.json"
CACHE = ROOT / "data" / "apac_fif_yahoo_cache.json"
OUT = ROOT / "data" / "apac_fif_compare.json"

MKTS = {"australia": "Australia", "china": "China",
        "hongkong": "HongKong", "india": "India",
        "indonesia": "Indonesia", "japan": "Japan",
        "korea": "Korea", "malaysia": "Malaysia",
        "newzealand": "NewZealand", "philippines": "Philippines",
        "singapore": "Singapore", "taiwan": "Taiwan",
        "thailand": "Thailand"}
SUFFIX = {"Japan": ".T", "Korea": ".KS", "HongKong": ".HK",
          "Australia": ".AX", "India": ".NS", "Malaysia": ".KL",
          "Indonesia": ".JK", "Philippines": ".PS",
          "Singapore": ".SI", "Thailand": ".BK",
          "NewZealand": ".NZ", "Taiwan": ".TW"}
# hand overrides where name->ticker matching is unreliable
# (c-124b: the unmatched set is mostly mega-caps whose MSCI
# names differ too much from the member-list names)
OVERRIDES = {
    ("Korea", "SAMSUNG ELECTRONICS PREF"): "005935.KS",
    ("Korea", "SAMSUNG ELECTRONICS CO"): "005930.KS",
    ("Korea", "SAMSUNG ELECTRO-MECH. CO"): "009150.KS",
    ("Korea", "HANA FINANCIAL HOLDINGS"): "086790.KS",
    ("India", "HDFC BANK"): "HDFCBANK.NS",
    ("India", "ICICI BANK"): "ICICIBANK.NS",
    ("Australia", "CSL"): "CSL.AX",
    ("Australia", "BHP GROUP (AU)"): "BHP.AX",
    ("China", "TENCENT HOLDINGS LI (CN)"): "0700.HK",
    ("China", "ALIBABA GRP HLDG (HK)"): "9988.HK",
    ("China", "CHINA CONSTRUCTION BK H"): "0939.HK",
    ("China", "ICBC H"): "1398.HK",
    ("China", "PDD HOLDINGS A ADR"): "PDD",
    ("China", "PING AN INSURANCE H"): "2318.HK",
    ("China", "BANK OF CHINA H"): "3988.HK",
    ("HongKong", "HONGKONG EXCH & CLEARING"): "0388.HK",
    ("HongKong", "LINK REIT"): "0823.HK",
    # Jardine Matheson: MSCI's HK index holds the SGX (USD) line
    ("HongKong", "JARDINE MATHESON (USD)"): "J36.SI",
    ("Japan", "SUMITOMO MITSUI FINL GRP"): "8316.T",
    ("Japan", "SOFTBANK GROUP CORP"): "9984.T",
    ("Japan", "RECRUIT HOLDINGS CO"): "6098.T",
    ("Indonesia", "TELKOM INDONESIA"): "TLKM.JK",
    ("NewZealand", "AUCKLAND INTL AIRPORT"): "AIA.NZ",
    ("Philippines", "ICTSI INTL CONTAINER"): "ICT.PS",
    ("Singapore", "OCBC BANK"): "O39.SI",
    ("Singapore", "SEA A ADR"): "SE",
    ("Singapore", "SINGAPORE TECH ENGR"): "S63.SI",
    ("Thailand", "PTT"): "PTT.BK",
    ("Thailand", "BANGKOK DUSIT MED. SVCS"): "BDMS.BK",
    ("Thailand", "SIAM CEMENT"): "SCC.BK",
    ("Taiwan", "TAIWAN SEMICONDUCTOR MFG"): "2330.TW",
    ("Taiwan", "HON HAI PRECISION IND CO"): "2317.TW",
    ("Taiwan", "UNITED MICROELECTRONICS"): "2303.TW",
    # Bursa's Yahoo symbols are NUMERIC stock codes, not the
    # exchange mnemonics the census stored
    ("Malaysia", "PUBLIC BANK"): "1295.KL",
    ("Malaysia", "MALAYAN BANKING"): "1155.KL",
    ("Malaysia", "CIMB GROUP HOLDINGS"): "1023.KL",
    ("Malaysia", "TENAGA NASIONAL"): "5347.KL",
    ("Malaysia", "PRESS METAL ALUMINIUM"): "8869.KL",
    ("Malaysia", "GAMUDA"): "5398.KL",
    ("Malaysia", "AMMB HOLDINGS"): "1015.KL",
    ("Malaysia", "RHB BANK"): "1066.KL",
    ("Malaysia", "IHH HEALTHCARE"): "5225.KL",
    ("Malaysia", "SUNWAY"): "5211.KL",
}


def parse():
    """TOP 10 CONSTITUENTS blocks from every factsheet."""
    out = {}
    for slug, mkt in MKTS.items():
        p = ROOT / "data" / "factsheets" / f"msci_{slug}_2026-07.pdf"
        if not p.exists():
            continue
        txt = subprocess.run(
            ["pdftotext", "-layout", str(p), "-"],
            capture_output=True, text=True).stdout
        m = re.search(r"TOP \d+ CONSTITUENTS(.*?)\bTotal\b",
                      txt, re.S)
        if not m:
            print(f"{mkt}: TOP-N block not found")
            continue
        rows = []
        for ln in m.group(1).splitlines():
            # -layout interleaves the left column (INDEX
            # CHARACTERISTICS) into these lines, so take the
            # LAST name+cap+weight match on each line and then
            # keep only the text after the final wide gap —
            # that is the right-hand column's name.
            hits = list(re.finditer(
                r"([A-Za-z][A-Za-z0-9 .&()'\-/]+?)\s{2,}"
                r"([\d,]+\.\d\d)\s+(\d+\.\d\d)(?:\s|$)", ln))
            if not hits:
                continue
            mm = hits[-1]
            nm = re.split(r"\s{3,}", mm.group(1).strip())[-1]
            if nm.upper() in ("CONSTITUENTS", "INDEX",
                              "LARGEST", "SMALLEST", "AVERAGE",
                              "MEDIAN") or len(nm) < 3:
                continue
            rows.append({
                "name": nm,
                "float_cap_usd_b":
                    float(mm.group(2).replace(",", "")),
                "weight_pct": float(mm.group(3))})
        expect = 5 if mkt == "NewZealand" else 10
        if len(rows) != expect:
            print(f"{mkt}: parsed {len(rows)} rows "
                  f"(expect {expect})")
        out[mkt] = rows
    FS.write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(f"parsed {len(out)} markets -> {FS.name}")
    return out


def _symbols(mkt, rows):
    """Map factsheet names to Yahoo symbols via the member
    lists (ticker -> name) with prefix matching."""
    from ticker_backfill import prefix_match, norm
    mem = json.loads((ROOT / "data" / "apac_members.json")
                     .read_text(encoding="utf-8"))["markets"].get(mkt, {})
    names = {n: t for t, n in (mem.get("names") or {}).items()
             if n}
    out = []
    for r in rows:
        ov = OVERRIDES.get((mkt, r["name"]))
        if ov:
            out.append((r, ov, "override"))
            continue
        t = None
        nn = norm(r["name"])
        # exact then prefix in both directions
        for cand_n, cand_t in names.items():
            if norm(cand_n) == nn:
                t = cand_t
                break
        if not t:
            t = prefix_match(r["name"], names)
        if not t:
            hits = [tt for n2, tt in names.items()
                    if prefix_match(n2, {r["name"]: tt})]
            t = hits[0] if len(hits) == 1 else None
        if not t:
            out.append((r, None, "UNMATCHED"))
            continue
        s = str(t)
        if mkt == "China":
            sym = (f"{int(s):04d}.HK" if s.isdigit()
                   and len(s) <= 5 else
                   f"{s}.SS" if s.startswith(("6",)) else
                   f"{s}.SZ")
        elif mkt == "HongKong" and s.isdigit():
            sym = f"{int(s):04d}.HK"
        elif mkt == "Korea" and s.isdigit():
            sym = f"{int(s):06d}.KS"
        elif mkt == "Thailand":
            # THD census stores the NVDR line (CPALL.R); the
            # tradeable Yahoo symbol is the local line .BK
            sym = f"{s.split('.')[0]}.BK"
        else:
            sym = f"{s}{SUFFIX.get(mkt, '')}" if "." not in s \
                else s
        out.append((r, sym, "member-match"))
    return out


FX_SYMS = {"JPY": "JPY=X", "KRW": "KRW=X", "HKD": "HKD=X",
           "AUD": "AUDUSD=X", "INR": "INR=X", "MYR": "MYR=X",
           "IDR": "IDR=X", "PHP": "PHP=X", "SGD": "SGD=X",
           "THB": "THB=X", "NZD": "NZDUSD=X", "TWD": "TWD=X",
           "CNY": "CNY=X"}


def _fx_rates(cache):
    """local-per-USD for each currency (AUD/NZD quoted USD-per,
    inverted)."""
    import yfinance as yf
    fx = cache.setdefault("_fx", {})
    for ccy, sym in FX_SYMS.items():
        if ccy in fx:
            continue
        try:
            p = yf.Ticker(sym).fast_info["lastPrice"]
            fx[ccy] = (round(1 / p, 6)
                       if sym.endswith("USD=X") else round(p, 6))
        except Exception:                          # noqa: BLE001
            pass
        time.sleep(0.4)
    fx["USD"] = 1.0
    return fx


def harvest():
    import yfinance as yf
    fs = json.loads(FS.read_text(encoding="utf-8"))
    cache = (json.loads(CACHE.read_text(encoding="utf-8"))
             if CACHE.exists() else {})
    _fx_rates(cache)
    CACHE.write_text(json.dumps(cache), encoding="utf-8")
    jobs = []
    for mkt, rows in fs.items():
        for r, sym, how in _symbols(mkt, rows):
            if sym and sym not in cache:
                jobs.append(sym)
    print(f"{len(jobs)} symbols to fetch", flush=True)
    for i, sym in enumerate(jobs):
        rec = {}
        try:
            t = yf.Ticker(sym)
            info = t.get_info()
            rec = {"cap": info.get("marketCap"),
                   "float_shares": info.get("floatShares"),
                   "shares_out": info.get("sharesOutstanding"),
                   "ccy": info.get("currency")}
        except Exception as e:                     # noqa: BLE001
            rec = {"error": type(e).__name__}
        cache[sym] = rec
        CACHE.write_text(json.dumps(cache), encoding="utf-8")
        if (i + 1) % 10 == 0:
            ok = sum(1 for v in cache.values() if v.get("cap"))
            print(f"  {i + 1}/{len(jobs)} (with cap {ok})",
                  flush=True)
        time.sleep(0.6)
    print("harvest done", flush=True)


def report():
    import statistics as st
    fs = json.loads(FS.read_text(encoding="utf-8"))
    cache = (json.loads(CACHE.read_text(encoding="utf-8"))
             if CACHE.exists() else {})
    fx = cache.get("_fx", {"USD": 1.0})
    res = {"method": "implied FIF = factsheet float cap (USD) / "
                     "Yahoo full cap converted to USD; yahoo "
                     "float = floatShares/sharesOut",
           "date_caveat": "factsheet Jul-31 vs Yahoo current "
                          "(~1wk drift in implied FIFs)",
           "fx_used": fx, "markets": {}, "summary": {}}
    import statistics as st
    for mkt, rows in fs.items():
        comp, errs = [], []
        for r, sym, how in _symbols(mkt, rows):
            c = cache.get(sym or "", {})
            cap, fsh, so = (c.get("cap"), c.get("float_shares"),
                            c.get("shares_out"))
            ccy = c.get("ccy")
            cap_usd = (cap / fx[ccy] / 1e9
                       if cap and fx.get(ccy) else None)
            imp = (round(min(1.05, r["float_cap_usd_b"]
                             / cap_usd), 3)
                   if cap_usd else None)
            yff = (round(min(1.0, fsh / so), 3)
                   if fsh and so else None)
            err = (round((yff - imp) / imp, 3)
                   if yff and imp else None)
            if err is not None:
                errs.append(abs(err))
            comp.append({"name": r["name"], "symbol": sym,
                         "match": how,
                         "float_cap_usd_b": r["float_cap_usd_b"],
                         "cap_usd_b": (round(cap_usd, 2)
                                       if cap_usd else None),
                         "implied_fif": imp, "yahoo_ff": yff,
                         "yahoo_err": err})
        res["markets"][mkt] = comp
        res["summary"][mkt] = {
            "n_scored": len(errs),
            "yahoo_median_abs_err":
                (round(st.median(errs), 3) if errs else None)}
    OUT.write_text(json.dumps(res, indent=1), encoding="utf-8")
    print(f"{'market':12} {'scored':>7} {'yahoo median |err|':>19}")
    for m, s in sorted(res["summary"].items()):
        e = s["yahoo_median_abs_err"]
        print(f"{m:12} {s['n_scored']:>7} "
              f"{(f'{e:.1%}' if e is not None else 'n/a'):>19}")
    print(f"-> {OUT.name}")
    return res


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "all"
    if cmd in ("parse", "all"):
        parse()
    if cmd in ("harvest", "all"):
        harvest()
    if cmd in ("report", "all"):
        report()
