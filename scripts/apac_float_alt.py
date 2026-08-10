"""Alternative float sources for the bot-blocked markets
(c-125) — RUN ON BILL'S TERMINAL.

The sandbox gets 403s because these sites block datacenter IPs
and bare clients. A residential IP with the right session
ritual passes. Each market below encodes its specific unlock:

  THAILAND  set.or.th — needs a browser-like session: land on
            the quote page first (collects cookies), then call
            the JSON api with Referer + the cookies. Serves
            '% Free Float' AND foreign limit/room per stock.
  INDIA     nseindia.com — the classic warm-up: GET the
            homepage with full browser headers, KEEP the
            session, then hit the api. FPI headroom comes from
            NSDL's company-wise limit tables.
  INDONESIA idx.co.id — Cloudflare; plain requests fails even
            residentially. `pip install cloudscraper` and it
            passes. The securities list includes free float.
  KOREA     data.krx.co.kr — POST getJsonData with a Referer
            from the stats page; the floating-stock ratio
            sits in the MDCSTAT screens. If LOGOUT persists,
            fall back to Naver Finance per-name pages.

If any source still refuses: MANUAL FALLBACK — open the quoted
URL in a browser, copy the float/limit numbers into
data/<mkt>_float_manual.json as {"SYMBOL": 0.xx} and the
`grade` step picks them up. Ten names per market is minutes of
work and unblocks the grading.

Usage (Bill's terminal):
  py scripts\\apac_float_alt.py th
  py scripts\\apac_float_alt.py in
  py scripts\\apac_float_alt.py id
  py scripts\\apac_float_alt.py kr
  py scripts\\apac_float_alt.py grade     (score vs implied FIF)
"""
import json
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FS = ROOT / "data" / "apac_factsheet_top10.json"
CMP = ROOT / "data" / "apac_fif_compare.json"

BROWSER_HDRS = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) "
                   "Chrome/126.0 Safari/537.36"),
    "Accept": ("text/html,application/xhtml+xml,application/"
               "xml;q=0.9,*/*;q=0.8"),
    "Accept-Language": "en-US,en;q=0.9"}

TH_SYMS = {"DELTA ELECTRONICS THAI": "DELTA", "PTT": "PTT",
           "AIRPORTS OF THAILAND": "AOT", "CP ALL": "CPALL",
           "GULF DEVELOPMENT": "GULF",
           "ADVANCED INFO SERVICE": "ADVANC",
           "BANGKOK DUSIT MED. SVCS": "BDMS",
           "KASIKORNBANK": "KBANK", "SIAM CEMENT": "SCC",
           "KRUNG THAI BANK": "KTB", "TRUE CORP NEW": "TRUE",
           "SCB X": "SCB"}
IN_SYMS = {"HDFC BANK": "HDFCBANK", "ICICI BANK": "ICICIBANK",
           "RELIANCE INDUSTRIES": "RELIANCE",
           "BHARTI AIRTEL": "BHARTIARTL", "INFOSYS": "INFY",
           "MAHINDRA & MAHINDRA": "M&M",
           "BAJAJ FINANCE": "BAJFINANCE", "AXIS BANK": "AXISBANK",
           "LARSEN & TOUBRO": "LT",
           "KOTAK MAHINDRA BANK": "KOTAKBANK"}


def th():
    """SET: session warm-up then the stock JSON api."""
    import requests
    s = requests.Session()
    s.headers.update(BROWSER_HDRS)
    out = {}
    for nm, sym in TH_SYMS.items():
        try:
            s.get(f"https://www.set.or.th/en/market/product/"
                  f"stock/quote/{sym}/price", timeout=25)
            r = s.get(
                f"https://www.set.or.th/api/set/stock/{sym}"
                f"/profile?lang=en",
                headers={"Referer":
                         f"https://www.set.or.th/en/market/"
                         f"product/stock/quote/{sym}/price"},
                timeout=25)
            j = r.json()
            out[sym] = {
                "free_float_pct": j.get("percentFreeFloat"),
                "foreign_limit_pct": j.get("percentForeignLimit")
                or j.get("foreignLimit"),
                "foreign_room_pct": j.get("foreignRoom"),
                "raw_keys": sorted(j)[:20]}
            print(sym, out[sym]["free_float_pct"],
                  out[sym]["foreign_limit_pct"], flush=True)
        except Exception as e:                     # noqa: BLE001
            print(sym, "FAIL", type(e).__name__, flush=True)
        time.sleep(2.0)
    (ROOT / "data" / "th_set_float.json").write_text(
        json.dumps(out, indent=1), encoding="utf-8")
    print("-> data/th_set_float.json")


def in_():
    """NSE warm-up session; free float via securityInfo, FPI
    limits are on NSDL (manual URL printed).

    c-126 fixes after the first live run failed with
    JSONDecodeError on every symbol:
      - NSE serves Content-Encoding: br. Without the `brotli`
        package requests cannot decode it and .json() dies.
        We now request gzip/deflate ONLY, so brotli is never
        negotiated (installing `pip install brotli` also
        works).
      - the api wants a PER-SYMBOL Referer (its own get-quotes
        page), and the session must touch that page first.
      - 'M&M' must be URL-encoded (the & truncated the query).
    """
    import urllib.parse

    import requests
    s = requests.Session()
    s.headers.update({**BROWSER_HDRS,
                      "Accept": "*/*",
                      "Accept-Encoding": "gzip, deflate"})
    s.get("https://www.nseindia.com", timeout=25)
    time.sleep(1.5)
    out = {}
    for nm, sym in IN_SYMS.items():
        q = urllib.parse.quote(sym, safe="")
        ref = ("https://www.nseindia.com/get-quotes/equity"
               f"?symbol={q}")
        try:
            s.get(ref, timeout=25)          # per-symbol warm-up
            time.sleep(0.8)
            r = s.get("https://www.nseindia.com/api/"
                      f"quote-equity?symbol={q}",
                      headers={"Referer": ref,
                               "X-Requested-With":
                                   "XMLHttpRequest"},
                      timeout=25)
            ct = r.headers.get("content-type", "")
            if "json" not in ct:
                print(f"{sym} BLOCKED (got {ct[:30]!r}, "
                      f"status {r.status_code}) — NSE served a "
                      "challenge page, not data", flush=True)
                time.sleep(4)
                continue
            j = r.json()
            sec = j.get("securityInfo", {})
            out[sym] = {"faceValue": sec.get("faceValue"),
                        "issuedSize": sec.get("issuedSize"),
                        "keys": sorted(j)}
            print(sym, "ok", flush=True)
        except Exception as e:                     # noqa: BLE001
            print(sym, "FAIL", type(e).__name__, flush=True)
        time.sleep(2.5)
    (ROOT / "data" / "in_nse_probe.json").write_text(
        json.dumps(out, indent=1), encoding="utf-8")
    print("-> data/in_nse_probe.json")
    print("\nFPI headroom (the input that actually binds): "
          "download the company-wise FPI limit table from "
          "https://www.fpi.nsdl.co.in/web/Reports/Latest.aspx "
          "and save as data/in_fpi_limits.csv — the grade step "
          "reads it if present.")


def id_():
    """IDX behind Cloudflare -> cloudscraper."""
    try:
        import cloudscraper
    except ImportError:
        raise SystemExit("pip install cloudscraper")
    s = cloudscraper.create_scraper()
    r = s.get("https://www.idx.co.id/primary/StockData/"
              "GetSecuritiesStock?start=0&length=1000&code=",
              timeout=40)
    j = r.json()
    rows = j.get("data", j if isinstance(j, list) else [])
    out = {}
    for x in rows:
        code = x.get("Code") or x.get("code")
        if code:
            out[code] = x
    (ROOT / "data" / "id_idx_stocklist.json").write_text(
        json.dumps(out, indent=1), encoding="utf-8")
    print(f"{len(out)} securities -> data/id_idx_stocklist.json "
          "(inspect a row for the float field name, then tell "
          "the grade step)")


def kr():
    """KRX floating-stock ratio; try the JSON gateway, print
    the fallback if it still says LOGOUT."""
    import requests
    s = requests.Session()
    s.headers.update({**BROWSER_HDRS,
                      "Referer": "http://data.krx.co.kr/contents"
                      "/MDC/MDI/mdiLoader/index.cmd"})
    s.get("http://data.krx.co.kr/contents/MDC/MDI/mdiLoader/"
          "index.cmd?menuId=MDC0201020103", timeout=25)
    r = s.post("http://data.krx.co.kr/comm/bldAttendant/"
               "getJsonData.cmd",
               data={"bld": "dbms/MDC/STAT/standard/MDCSTAT03501",
                     "locale": "en", "mktId": "STK",
                     "trdDd": time.strftime("%Y%m%d"),
                     "share": "1", "money": "1"},
               timeout=25)
    print("KRX:", r.status_code, r.text[:200])
    if "LOGOUT" in r.text:
        print("\nStill session-gated. FALLBACK: Naver Finance "
              "shows 유동주식비율 per stock — or fill "
              "data/kr_float_manual.json by hand for the 10 "
              "names.")


def grade():
    """Merge whatever landed into the implied-FIF comparison."""
    import statistics as st
    fs = json.loads(FS.read_text(encoding="utf-8"))
    cmp_ = json.loads(CMP.read_text(encoding="utf-8"))
    # Thailand
    p = ROOT / "data" / "th_set_float.json"
    if p.exists():
        th_ = json.loads(p.read_text(encoding="utf-8"))
        name2sym = TH_SYMS
        rows = []
        for r in fs["Thailand"]:
            sym = name2sym.get(r["name"])
            v = (th_.get(sym) or {})
            f = v.get("free_float_pct")
            fol = v.get("foreign_limit_pct")
            comp = next((c for c in cmp_["markets"]["Thailand"]
                         if c["name"] == r["name"]), {})
            imp = comp.get("implied_fif")
            if f and imp:
                est = f / 100
                if fol:
                    est = min(est, fol / 100)
                rows.append({"name": r["name"], "implied": imp,
                             "set_min_float_fol": round(est, 3),
                             "err": round((est - imp) / imp, 3)})
        if rows:
            med = st.median(abs(x["err"]) for x in rows)
            cmp_.setdefault("alternative_scored", {})[
                "Thailand"] = {"rows": rows,
                               "median_abs_err": round(med, 3)}
            print(f"Thailand min(SET float, FOL) vs implied: "
                  f"median |err| {med:.1%}")
            for x in rows:
                print(f"  {x['name'][:24]:24} implied "
                      f"{x['implied']:.3f} est "
                      f"{x['set_min_float_fol']:.3f} "
                      f"{x['err']:+.0%}")
    CMP.write_text(json.dumps(cmp_, indent=1), encoding="utf-8")
    print(f"-> {CMP.name}")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "grade"
    {"th": th, "in": in_, "id": id_, "kr": kr,
     "grade": grade}[cmd]()
