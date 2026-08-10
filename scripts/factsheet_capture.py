"""MSCI factsheet capture — the ground-truth archive (c-48).

MSCI's factsheet URL always serves the CURRENT month, so history
cannot be fetched — it must be ACCUMULATED. This script, run
monthly (schedule alongside sentinels), saves the raw PDF and
parses the headline numbers into data/msci_factsheet_archive.json:

  - constituent count        (validates the membership pipeline)
  - index float-adj cap      (÷0.85 = MSCI's implied market
                              denominator — validates our walk)
  - largest/smallest/median  (ladder shape; smallest = observed
                              membership floor in float terms)
  - top-10 float-adj caps    (÷ our full caps = MSCI's IMPLIED
                              FLOAT FACTORS — the FIF calibration)

Historical backfill: web.archive.org snapshots of the same URL
(blocked from this environment; harvest manually if needed).

Usage: python scripts/factsheet_capture.py
"""
import datetime as dt
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

URL = ("https://www.msci.com/documents/10199/255599/"
       "msci-taiwan-index.pdf")
PDF_DIR = ROOT / "data" / "factsheets"
OUT = ROOT / "data" / "msci_factsheet_archive.json"


def capture():
    import requests
    PDF_DIR.mkdir(exist_ok=True)
    r = requests.get(URL, headers={"User-Agent": "Mozilla/5.0"},
                     timeout=45)
    r.raise_for_status()
    txt = subprocess.run(["pdftotext", "-", "-"], input=r.content,
                         capture_output=True).stdout.decode(
        "utf-8", "ignore")
    m = re.search(r"([A-Z]{3} \d{1,2}, \d{4})\s*Index Factsheet",
                  txt)
    asof = m.group(1) if m else "unknown"
    tag = (dt.datetime.strptime(asof, "%b %d, %Y")
           .strftime("%Y-%m") if m else
           dt.date.today().strftime("%Y-%m"))
    (PDF_DIR / f"msci_taiwan_{tag}.pdf").write_bytes(r.content)
    # characteristics: the 5 numbers following the
    # "Mkt Cap ( USD Millions)" label block (pdftotext keeps order:
    # Index, Largest, Smallest, Average, Median)
    mchar = re.search(
        r"Mkt Cap \( USD Millions\).*?Median\n\n"
        r"([\d,]+\.\d{2})\n([\d,]+\.\d{2})\n([\d,]+\.\d{2})\n"
        r"([\d,]+\.\d{2})\n([\d,]+\.\d{2})", txt, re.S)
    chars = ([float(x.replace(",", "")) for x in mchar.groups()]
             if mchar else [])
    ncon = re.search(r"With\s*(\d+)\s*\n?constituents",
                     txt.replace("ﬂ", "fl"))
    n = int(ncon.group(1)) if ncon else None
    # top-10: names listed after "TOP 10 CONSTITUENTS", float caps
    # (USD Billions) in the block after "( USD Billions)"
    _t0 = txt.find("TOP 10 CONSTITUENTS") \
        + len("TOP 10 CONSTITUENTS")
    names10 = re.findall(r"^([A-Z][A-Z0-9 &.\-']{5,40})$",
                         txt[_t0:
                             txt.find("Mkt Cap ( USD Millions)")],
                         re.M)[:10]
    capblock = txt[txt.find("( USD Billions)"):]
    caps10 = re.findall(r"^([\d,]+\.\d{2})$", capblock, re.M)[:10]
    wblock = capblock[capblock.find("Wt. (%)"):]
    w10 = re.findall(r"^(\d{1,2}\.\d{2})$", wblock, re.M)[:10]
    top10 = list(zip(names10, caps10,
                     w10 + ["0"] * (10 - len(w10))))
    entry = {"asof": asof, "n_constituents": n,
             "index_float_cap_musd": chars[0] if chars else None,
             "largest_musd": chars[1] if len(chars) > 1 else None,
             "smallest_musd": chars[2] if len(chars) > 2 else None,
             "median_musd": chars[4] if len(chars) > 4 else None,
             "implied_market_denominator_busd":
             round(chars[0] / 0.85 / 1000, 0) if chars else None,
             "top10": [{"name": a.strip(),
                        "float_cap_busd":
                        float(b.replace(",", "")),   # already $B
                        "weight_pct": float(w)}
                       for a, b, w in top10[:10]]}
    # implied float factors vs our current full caps
    try:
        from agents.pit_constituents import _data, ladder_asof
        L = ladder_asof(str(dt.date.today()))
        names = _data()[3]
        by_cap = {r["code"]: r["cap_usd_b"] for r in L["ladder"]}
        for t in entry["top10"]:
            code = next((c for c, nm in names.items()
                         if nm and (nm.upper() in t["name"]
                                    or t["name"] in nm.upper())),
                        None)
            if code and by_cap.get(code):
                t["our_full_cap_busd"] = by_cap[code]
                t["implied_fif"] = round(
                    t["float_cap_busd"] / by_cap[code], 3)
    except Exception:                          # noqa: BLE001
        pass
    arch = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {}
    arch[tag] = entry
    tmp = OUT.with_suffix(".tmp")
    tmp.write_text(json.dumps(arch, indent=1), encoding="utf-8")
    tmp.replace(OUT)
    print(f"{tag} ({asof}): n={n}, index cap "
          f"${chars[0]/1000:,.0f}B -> implied denominator "
          f"${entry['implied_market_denominator_busd']:,.0f}B; "
          f"top10 parsed {len(entry['top10'])}")
    for t in entry["top10"][:5]:
        if "implied_fif" in t:
            print(f"   {t['name'][:28]:28s} MSCI float "
                  f"{t['float_cap_busd']}B / our full "
                  f"{t['our_full_cap_busd']}B -> implied FIF "
                  f"{t['implied_fif']}")


if __name__ == "__main__":
    capture()
