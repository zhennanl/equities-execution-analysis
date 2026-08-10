"""Phase 1 of the Review Study roadmap: GIMI edition harvest +
mining (c-105).

Downloads every GIMI methodology edition (2018+ naming era; the
2015-17 older-naming editions are a REGISTERED GAP), extracts
from each worked example (§2.3.2.1):
  - the DM Standard Global Minimum Size Reference ("USD X
    billion ... 85%")
  - the disclosed data date ("based on ... data" / "as of the
    close of <date>") — i.e., THAT review's chosen Price Cutoff
    Date, revealed ex post (the Q60 discovery)
  - the DM/EM Standard ranges where printed

VALIDATION GATES (the build STOPS on surprise):
  G1  May2026 edition must yield GMSR 15.75 and data date
      2026-04-20 (both known independently).
  G2  Dec2022 edition must yield a GMSR in [10, 20] (sanity
      vs the known ~13-16B era) and a date inside the last 10
      business days of a review's price month.
  G3  Across editions, GMSR must stay within [8, 25] and move
      < 35% between consecutive editions (else: naming-era
      mismatch or parse drift — STOP and report).

Output: data/gimi_editions_index.json
Usage:  py scripts\\gimi_editions.py harvest [--limit N]
        py scripts\\gimi_editions.py mine
"""
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EDIR = ROOT / "data" / "gimi_editions"
BASE = "https://www.msci.com/eqb/methodology/meth_docs/"
OUT = ROOT / "data" / "gimi_editions_index.json"


def _editions():
    probe = json.loads((ROOT / "data" /
                        "gimi_edition_probe.json").read_text(encoding="utf-8"))
    return sorted(k for k, v in probe.items() if v == 200)


def harvest(limit=None):
    import requests
    EDIR.mkdir(exist_ok=True)
    todo = [e for e in _editions()
            if not (EDIR / e.replace(".pdf", ".txt")).exists()]
    if limit:
        todo = todo[:int(limit)]
    print(f"{len(todo)} editions to fetch")
    for fn in todo:
        r = requests.get(BASE + fn, timeout=60, headers={
            "User-Agent": "Mozilla/5.0"})
        if r.status_code == 200 and r.content[:4] == b"%PDF":
            p = EDIR / fn
            p.write_bytes(r.content)
            subprocess.run(["pdftotext", "-layout", str(p),
                            str(p.with_suffix(".txt"))])
            p.unlink()          # keep txt only (PDFs are ~2MB)
            print("  ok", fn)
        else:
            print("  MISS", fn, r.status_code)


def _mine_one(txt):
    """Extract (gmsr_dm, data_date, em_range) from an edition's
    text; returns dict with None where not found."""
    out = {"gmsr_dm": None, "data_date": None,
           "em_range": None}
    m = re.search(
        r"85\s*%\s+cumulative free float[^.]*?is\s+USD\s+"
        r"([\d.]+)\s+billion", txt, re.S | re.I)
    if not m:
        m = re.search(
            r"USD\s+([\d.]+)\s+billion[^.]{0,200}?85%",
            txt, re.S)
    if m:
        out["gmsr_dm"] = float(m.group(1))
    d = re.search(r"[Dd]ata as of (?:the close of\s+)?"
                  r"([A-Z][a-z]+ \d{1,2},? \d{4})", txt)
    if not d:
        d = re.search(r"based on ([A-Z][a-z]+ \d{1,2},? \d{4}) "
                      r"data", txt)
    if d:
        out["data_date"] = d.group(1).replace(",", "")
    r2 = re.search(r"EM range[^.]*?USD\s+([\d.]+)\s+billion to "
                   r"USD\s+([\d.]+)\s+billion", txt, re.I)
    if not r2:
        r2 = re.search(r"USD\s+([\d.]+)\s+billion to USD\s+"
                       r"([\d.]+)\s+billion for the\s+EM",
                       txt, re.I)
    if r2:
        out["em_range"] = [float(r2.group(1)),
                           float(r2.group(2))]
    return out


def mine():
    idx = {}
    for t in sorted(EDIR.glob("*.txt")):
        ed = t.stem.replace("MSCI_GIMIMethodology_", "")
        idx[ed] = _mine_one(t.read_text(encoding="utf-8",
                                        errors="ignore"))
        g = idx[ed]
        print(f"{ed:8s} GMSR {g['gmsr_dm']} | date "
              f"{g['data_date']} | EM range {g['em_range']}")
    # ---- gates ----
    halted = None
    m26 = idx.get("May2026", {})
    if not (m26.get("gmsr_dm") == 15.75
            and m26.get("data_date") == "April 20 2026"):
        halted = (f"G1 FAILED: May2026 mined as {m26} — "
                  "expected GMSR 15.75 / April 20 2026")
    if not halted:
        # G3 (corrected c-106 after the first halt taught us the
        # GMSR tripled from its 2020 low): band [4, 25] + the
        # STRONGER check — the printed EM range must equal
        # GMSR x [0.25, 0.575] within rounding
        for e, g in sorted(idx.items()):
            v = g["gmsr_dm"]
            if v is None:
                continue
            if not (4 <= v <= 25):
                halted = f"G3 FAILED: {e} GMSR {v} outside [4,25]"
                break
            r = g.get("em_range")
            if r and (abs(r[0] - 0.25 * v) > 0.02 * v
                      or abs(r[1] - 0.575 * v) > 0.02 * v):
                halted = (f"G3b FAILED: {e} EM range {r} != "
                          f"GMSR {v} x [0.25, 0.575]")
                break
    out = {"editions": idx, "n": len(idx),
           "mined_gmsr": sum(1 for g in idx.values()
                             if g["gmsr_dm"]),
           "mined_date": sum(1 for g in idx.values()
                             if g["data_date"]),
           "gap": "2015-2017 editions (older naming) not yet "
                  "harvested — registered",
           "halted": halted}
    OUT.write_text(json.dumps(out, indent=1), encoding="utf-8")
    if halted:
        print("\n*** BUILD HALTED:", halted)
        sys.exit(2)
    print(f"\nindex written: {out['mined_gmsr']}/{out['n']} "
          f"GMSRs, {out['mined_date']}/{out['n']} dates")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "mine"
    lim = (sys.argv[sys.argv.index("--limit") + 1]
           if "--limit" in sys.argv else None)
    if cmd == "harvest":
        harvest(lim)
    else:
        mine()
