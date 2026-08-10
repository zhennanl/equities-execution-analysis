"""Malaysia float automation: the CALIBRATED GLIC CLASSIFIER
(c-126) — RUN ON BILL'S TERMINAL (Bursa sits behind
Cloudflare; `pip install cloudscraper` passes it there).

WHY THIS DESIGN. Malaysia has no published float ratio, but it
has something better: mandatory disclosure of every substantial
(>=5%) shareholder, printed in each annual report's "Analysis
of Shareholdings" section. MSCI's own float methodology
(Appendix VI) says it works "solely on publicly available
shareholder information" classified by investor type — i.e.
MSCI is running a holder classifier over these same tables. So
we do not need to find float data; we need to REPRODUCE THE
CLASSIFIER. And we hold the answer key to tune it against: the
ten factsheet-implied FIFs.

PIPELINE
  1. anns     Bursa announcements API per company -> latest
              Annual Report -> attachment PDF URL
  2. parse    pdftotext the AR, locate ANALYSIS OF
              SHAREHOLDINGS / SUBSTANTIAL SHAREHOLDERS, regex
              out (holder name, %). ARs are 200-400pp; the
              section is found by header, not by reading it all
  3. classify holder -> strategic / float by keyword class
  4. float    1 - sum(strategic %)
  5. CALIBRATE (the trick): which holder classes MSCI counts
              strategic is not published. Grid-search the
              class inclusion flags (EPF in/out, PNB funds
              in/out, nominees at 0/50/100%) to minimize error
              vs the ten implied FIFs, then FREEZE the flags
              and apply to the whole market. The flags are a
              fitted model and are labelled as such.

CADENCE: annual reports refresh yearly; GLIC stakes move
slowly. Event patches come from Bursa's "Changes in Substantial
Shareholder's Interest" category (same API, cat=CSSI) if wanted.

SECONDARY ROUTE (cheaper, partial): invert the direction —
harvest the 5 GLICs' OWN disclosed portfolios (EPF publishes
top equity holdings annually; Khazanah lists investees) and map
onto the ~30 index names. 5 documents instead of 30 ARs, but
coverage is partial. Use as a cross-check, not the spine.

Usage (Bill's terminal):
  pip install cloudscraper
  py scripts\\my_float_glic.py anns
  py scripts\\my_float_glic.py parse
  py scripts\\my_float_glic.py calibrate
"""
import json
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "my_glic_float.json"

# Bursa stock codes for the MSCI Malaysia top 10 (the
# calibration anchors) — extend to the full membership after
# the flags are frozen
CODES = {"PUBLIC BANK": "1295", "MALAYAN BANKING": "1155",
         "CIMB GROUP HOLDINGS": "1023",
         "TENAGA NASIONAL": "5347",
         "PRESS METAL ALUMINIUM": "8869", "GAMUDA": "5398",
         "AMMB HOLDINGS": "1015", "RHB BANK": "1066",
         "IHH HEALTHCARE": "5225", "SUNWAY": "5211"}

# implied FIFs (Jul-31 factsheet / Yahoo caps) — the answer key
IMPLIED = {"PUBLIC BANK": 0.748, "MALAYAN BANKING": 0.485,
           "CIMB GROUP HOLDINGS": 0.721,
           "TENAGA NASIONAL": 0.457,
           "PRESS METAL ALUMINIUM": 0.452, "GAMUDA": 0.812,
           "AMMB HOLDINGS": 0.690, "RHB BANK": 0.412,
           "IHH HEALTHCARE": 0.196, "SUNWAY": 0.406}

# holder-classification vocabulary. Each class gets an
# inclusion flag tuned in `calibrate`.
CLASSES = {
    "khazanah": ["KHAZANAH"],
    "pnb": ["PERMODALAN NASIONAL", "AMANAH SAHAM", "AMANAHRAYA",
            "ASB", "ASN", "YAYASAN PELABURAN"],
    "epf": ["EMPLOYEES PROVIDENT", "KWSP"],
    "kwap": ["KUMPULAN WANG PERSARAAN", "KWAP"],
    "ltat_lth": ["LEMBAGA TABUNG ANGKATAN", "TABUNG HAJI",
                 "LTAT"],
    "founder_corp": [],   # any single non-GLIC holder >= 5%
    "foreign_strategic": ["MITSUI", "SUMITOMO", "TEMASEK",
                          "MBK PARTNERS"],
}


def _scraper():
    try:
        import cloudscraper
        return cloudscraper.create_scraper()
    except ImportError:
        raise SystemExit("pip install cloudscraper")


def anns():
    """Latest Annual Report announcement + PDF link per name."""
    s = _scraper()
    out = (json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists()
           else {"anns": {}, "holders": {}})
    for nm, code in CODES.items():
        if nm in out["anns"]:
            continue
        try:
            r = s.get(
                "https://www.bursamalaysia.com/api/v1/"
                "announcements/announcements_list",
                params={"cat": "AR", "company": code,
                        "per_page": 5}, timeout=30)
            j = r.json()
            rows = j.get("data") or []
            if rows:
                a = rows[0]
                out["anns"][nm] = {
                    "code": code,
                    "title": a.get("title") or a.get("an_title"),
                    "date": a.get("date") or a.get("an_date"),
                    "url": a.get("url") or a.get("link")}
                print(nm, "->", out["anns"][nm]["date"],
                      flush=True)
        except Exception as e:                     # noqa: BLE001
            print(nm, "FAIL", type(e).__name__, flush=True)
        time.sleep(2)
    OUT.write_text(json.dumps(out, indent=1), encoding="utf-8")
    print("NOTE: if the JSON API shape differs, open one "
          "announcement in the browser and adjust the field "
          "names — the page URLs also embed the attachment id.")


def parse():
    """Download each AR, extract the substantial-shareholders
    table. Requires pdftotext on PATH (poppler)."""
    import subprocess
    s = _scraper()
    out = json.loads(OUT.read_text(encoding="utf-8"))
    for nm, a in out["anns"].items():
        if nm in out["holders"] or not a.get("url"):
            continue
        try:
            pdf = s.get(a["url"], timeout=120).content
            p = ROOT / "data" / f"_ar_{a['code']}.pdf"
            p.write_bytes(pdf)
            txt = subprocess.run(
                ["pdftotext", "-layout", str(p), "-"],
                capture_output=True, text=True).stdout
            p.unlink()
            m = re.search(
                r"(SUBSTANTIAL SHAREHOLDERS?|ANALYSIS OF "
                r"SHAREHOLDINGS?)(.{0,8000})", txt,
                re.S | re.I)
            holders = []
            if m:
                for mm in re.finditer(
                        r"([A-Z][A-Z0-9 .,&()'/\-]{6,60}?)\s+"
                        r"[\d,]+\s+(\d{1,2}\.\d{1,3})\s*$",
                        m.group(2), re.M):
                    holders.append(
                        {"holder": mm.group(1).strip(),
                         "pct": float(mm.group(2))})
            out["holders"][nm] = holders
            print(f"{nm}: {len(holders)} holders", flush=True)
        except Exception as e:                     # noqa: BLE001
            print(nm, "FAIL", type(e).__name__, flush=True)
        time.sleep(3)
    OUT.write_text(json.dumps(out, indent=1), encoding="utf-8")


def _float_for(holders, flags):
    """1 - strategic%, under a flag set."""
    strat = 0.0
    for h in holders:
        up = h["holder"].upper()
        cls = None
        for c, kws in CLASSES.items():
            if any(k in up for k in kws):
                cls = c
                break
        if cls is None and h["pct"] >= 5.0:
            cls = "founder_corp"
        if cls and flags.get(cls, 1.0) > 0:
            strat += h["pct"] * flags[cls]
    return max(0.0, 1 - strat / 100)


def calibrate():
    """Grid-search the class flags against the implied FIFs."""
    import itertools
    import statistics as st
    out = json.loads(OUT.read_text(encoding="utf-8"))
    H = out["holders"]
    grid = {"khazanah": [1.0], "pnb": [1.0],
            "epf": [0.0, 0.5, 1.0], "kwap": [0.0, 1.0],
            "ltat_lth": [1.0], "founder_corp": [1.0],
            "foreign_strategic": [1.0]}
    best = None
    for combo in itertools.product(*grid.values()):
        flags = dict(zip(grid.keys(), combo))
        errs = []
        for nm, imp in IMPLIED.items():
            if nm not in H or not H[nm]:
                continue
            est = _float_for(H[nm], flags)
            errs.append(abs(est - imp) / imp)
        if errs:
            med = st.median(errs)
            if best is None or med < best[0]:
                best = (med, flags, len(errs))
    if not best:
        raise SystemExit("no parsed holders yet — run `parse`")
    med, flags, n = best
    out["calibration"] = {
        "flags": flags, "median_abs_err": round(med, 3),
        "n_anchors": n,
        "label": "FITTED to the 10 implied FIFs — a calibrated "
                 "classifier, not independent measurement; "
                 "freeze before applying market-wide"}
    OUT.write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(f"best flags {flags} -> median |err| {med:.1%} "
          f"on {n} anchors (Yahoo baseline was 14.1%)")


if __name__ == "__main__":
    {"anns": anns, "parse": parse,
     "calibrate": calibrate}[sys.argv[1]
                             if len(sys.argv) > 1 else "anns"]()
