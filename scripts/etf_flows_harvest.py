"""iShares ETF NAV / shares-outstanding HISTORY — the passive
creation/redemption leg, measured directly (c-130).

WHY: daily shares outstanding of the MSCI country trackers
(EWT, EWY, EWJ, INDA, ...) is the cleanest observable of
passive flow: creations into the effective date ARE the
tracker demand, no proxy needed. It also fixes the C1/Piece-B
units problem (AUM assumption -> measured AUM).

THE CATCH (probed 2026-08-08): the historic-data ajax URL is
built by JavaScript on the product page — the static HTML
carries no csv links, and guessed ids return the HTML shell.
ONE MANUAL STEP unlocks everything:

  1. open e.g. https://www.ishares.com/us/products/239686/
     ishares-msci-taiwan-etf in Chrome
  2. DevTools -> Network -> filter 'csv' -> click the chart's
     'Download' / view NAV history
  3. copy the request URL (it looks like
     /us/products/239686/<slug>/<NUMERIC_ID>.ajax?fileType=csv
     &fileName=...&dataType=fund)
  4. paste the NUMERIC_ID into AJAX_ID below — it is the SAME
     id for every fund, so one copy serves all 13.

Usage (terminal, after step 4):
    py scripts\\etf_flows_harvest.py harvest
Output: data/etf_flows.json  {fund: [{date, nav, shares}]}
"""
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "etf_flows.json"
UA = {"User-Agent": "Mozilla/5.0"}

AJAX_ID = "PASTE_ME"        # <- from DevTools, see docstring

FUNDS = {"EWT": (239686, "ishares-msci-taiwan-etf"),
         "EWY": (239681, "ishares-msci-south-korea-etf"),
         "EWJ": (239665, "ishares-msci-japan-etf"),
         "INDA": (239659, "ishares-msci-india-etf"),
         "EWA": (239607, "ishares-msci-australia-etf"),
         "EWH": (239657, "ishares-msci-hong-kong-etf"),
         "EWS": (239678, "ishares-msci-singapore-etf"),
         "EWM": (239669, "ishares-msci-malaysia-etf"),
         "THD": (239688, "ishares-msci-thailand-etf"),
         "EIDO": (239661, "ishares-msci-indonesia-etf"),
         "EPHE": (239675, "ishares-msci-philippines-etf"),
         "ENZL": (239672, "ishares-msci-new-zealand-etf"),
         "MCHI": (239619, "ishares-msci-china-etf")}


def harvest():
    import csv
    import io

    import requests
    if AJAX_ID == "PASTE_ME":
        raise SystemExit(__doc__)
    out = (json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {})
    for fund, (pid, slug) in FUNDS.items():
        if fund in out:
            continue
        u = (f"https://www.ishares.com/us/products/{pid}/{slug}"
             f"/{AJAX_ID}.ajax?fileType=csv&fileName={fund}"
             "&dataType=fund")
        r = requests.get(u, headers=UA, timeout=60)
        if r.status_code != 200 or r.text.lstrip().startswith(
                "<!DOCTYPE"):
            print(f"{fund}: NOT CSV (id wrong or fund page "
                  "differs) — recheck AJAX_ID")
            continue
        rows = []
        rd = csv.reader(io.StringIO(r.text))
        for p in rd:
            # expected: date, nav, shares outstanding, ...
            if len(p) >= 3 and p[0][:2].isdigit():
                try:
                    rows.append({"date": p[0],
                                 "nav": float(p[1].replace(
                                     ",", "")),
                                 "shares": float(p[2].replace(
                                     ",", ""))})
                except ValueError:
                    pass
        out[fund] = rows
        OUT.write_text(json.dumps(out), encoding="utf-8")
        print(f"{fund}: {len(rows)} rows", flush=True)
        time.sleep(2)
    print(f"-> {OUT.name} (inspect one fund's first rows and "
          "adjust the column map if the layout differs)")


if __name__ == "__main__":
    harvest()
