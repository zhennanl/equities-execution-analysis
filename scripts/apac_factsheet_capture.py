"""APAC factsheet capture — all 10 review markets (c-62).

Generalizes the Taiwan factsheet capture: fetches each market's
official MSCI index factsheet (current month), parses the
characteristics block, and computes the implied market denominator
(index float cap / coverage) plus the corridor its cutoff must
land in (DEVELOPED markets — Japan, Australia, Hong Kong — are
judged against the DM reference; EMERGING against half of it).

Output: data/apac_factsheet_archive.json (keyed market -> month).
Run monthly with the sentinels.
"""
import datetime as dt
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

BASE = "https://www.msci.com/documents/10199/255599/"
MARKETS = {
    "Taiwan":      ("msci-taiwan-index.pdf", "EM"),
    "Japan":       ("msci-japan-index.pdf", "DM"),
    "Australia":   ("msci-australia-index.pdf", "DM"),
    "HongKong":    ("msci-hong-kong-index.pdf", "DM"),
    "Korea":       ("msci-korea-index.pdf", "EM"),
    "China":       ("msci-china-index.pdf", "EM"),
    "India":       ("msci-india-index-gross-usd.pdf", "EM"),
    "Malaysia":    ("msci-malaysia-index.pdf", "EM"),
    "Indonesia":   ("msci-indonesia-index.pdf", "EM"),
    "Philippines": ("msci-philippines-index.pdf", "EM"),
    # c-86: the three zero-change-in-May markets added for full
    # APAC coverage (13 = 5 DM + 8 EM); slugs probed 200/PDF
    "NewZealand":  ("msci-new-zealand-index.pdf", "DM"),
    "Singapore":   ("msci-singapore-index.pdf", "DM"),
    "Thailand":    ("msci-thailand-index.pdf", "EM"),
}
# Aug-2026 global reference forecast (Q16/Q22): May published
# $15.75B x DM move proxy 1.042
DM_REF = 15.75 * 1.042
EM_REF = DM_REF / 2
OUT = ROOT / "data" / "apac_factsheet_archive.json"
PDF_DIR = ROOT / "data" / "factsheets"


def parse(pdf_bytes):
    txt = subprocess.run(["pdftotext", "-", "-"], input=pdf_bytes,
                         capture_output=True).stdout.decode(
        "utf-8", "ignore").replace("ﬂ", "fl")
    m = re.search(r"([A-Z]{3} \d{1,2}, \d{4})\s*Index Factsheet",
                  txt)
    asof = m.group(1) if m else "unknown"
    mchar = re.search(
        r"Mkt Cap \( USD Millions\).*?Median\n\n"
        r"([\d,]+\.\d{2})\n([\d,]+\.\d{2})\n([\d,]+\.\d{2})\n"
        r"([\d,]+\.\d{2})\n([\d,]+\.\d{2})", txt, re.S)
    chars = ([float(x.replace(",", "")) for x in mchar.groups()]
             if mchar else None)
    if chars is None:
        # small-market layout (c-86, found on NZ): the stream
        # order puts the five stats DIRECTLY after the header
        # (labels typeset elsewhere) — Index/Largest/Smallest/
        # Average/Median in that order
        m2 = re.search(
            r"Mkt Cap \( USD Millions\)\n\n"
            r"([\d,]+\.\d{2})\n([\d,]+\.\d{2})\n"
            r"([\d,]+\.\d{2})\n([\d,]+\.\d{2})\n"
            r"([\d,]+\.\d{2})", txt)
        if m2:
            chars = [float(x.replace(",", ""))
                     for x in m2.groups()]
    ncon = re.search(r"With\s*(\d+)\s*\n?constituents", txt)
    cov = re.search(r"approximately\s+(\d+)%", txt)
    return {"asof": asof,
            "n_constituents": int(ncon.group(1)) if ncon else None,
            "coverage_pct": int(cov.group(1)) if cov else 85,
            "index_float_cap_musd": chars[0] if chars else None,
            "largest_musd": chars[1] if chars else None,
            "smallest_musd": chars[2] if chars else None,
            "median_musd": chars[4] if chars else None}


def main():
    import requests
    PDF_DIR.mkdir(exist_ok=True)
    arch = json.loads(OUT.read_text()) if OUT.exists() else {}
    for mkt, (slug, dmem) in MARKETS.items():
        try:
            r = requests.get(BASE + slug, headers={
                "User-Agent": "Mozilla/5.0"}, timeout=45)
            r.raise_for_status()
            e = parse(r.content)
            tag = (dt.datetime.strptime(e["asof"], "%b %d, %Y")
                   .strftime("%Y-%m") if e["asof"] != "unknown"
                   else dt.date.today().strftime("%Y-%m"))
            (PDF_DIR / f"msci_{mkt.lower()}_{tag}.pdf"
             ).write_bytes(r.content)
            ref = DM_REF if dmem == "DM" else EM_REF
            cov = (e["coverage_pct"] or 85) / 100
            e.update({
                "classification": dmem,
                "implied_denominator_busd":
                round(e["index_float_cap_musd"] / cov / 1000, 0)
                if e["index_float_cap_musd"] else None,
                "cutoff_corridor_busd": [round(0.5 * ref, 2),
                                         round(1.15 * ref, 2)],
                "observed_boundary_smallest_musd":
                e["smallest_musd"]})
            arch.setdefault(mkt, {})[tag] = e
            print(f"{mkt:12s} {e['asof']:12s} n={e['n_constituents']:>4} "
                  f"idx ${e['index_float_cap_musd']/1000:>8,.0f}B "
                  f"-> denom ${e['implied_denominator_busd']:>8,.0f}B "
                  f"| corridor {e['cutoff_corridor_busd']} "
                  f"| smallest ${e['smallest_musd']:,.0f}M")
        except Exception as ex:                # noqa: BLE001
            print(f"{mkt:12s} FAILED: {str(ex)[:60]}")
    tmp = OUT.with_suffix(".tmp")
    tmp.write_text(json.dumps(arch, indent=1))
    tmp.replace(OUT)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
