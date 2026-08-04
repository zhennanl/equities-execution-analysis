#!/usr/bin/env python3
"""MSCI press-release archive downloader (session 8v).

DISCOVERY (probed): app2.msci.com/eqb/pressreleases/archive/ serves
review press releases 2005-2025 with near-uniform naming
MSCI_{Feb|May|Aug|Nov}{YY}_QIRPR.pdf (May18 = SAIRPR, the one
exception known to the Wayback CDX). These PRs carry the appendix
change tables our ledger parser reads — the ANSWER KEYS for the
retrospective program, back to 2015 and beyond.

Usage: fetch [start_yy end_yy] | extract | check
Files: data/msci_archive/*.pdf + .txt
"""
import subprocess
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

DIR = Path("data/msci_archive")
DIR.mkdir(exist_ok=True)
BASE = "https://app2.msci.com/eqb/pressreleases/archive/"
SEASONS = ["Feb", "May", "Aug", "Nov"]


def names_for(y0, y1):
    out = []
    for yy in range(y0, y1 + 1):
        for s in SEASONS:
            n = f"MSCI_{s}{yy:02d}_QIRPR.pdf"
            if (s, yy) == ("May", 18):
                n = "MSCI_May18_SAIRPR.pdf"
            out.append(n)
    return out


# THE FULL LISTS (session 8v discovery via Wayback CDX): Standard-
# index public lists live at msci.com/eqb/gimi/stdindex/ with
# uniform naming back to 2003 — the complete per-country change
# tables our ledger parser reads natively.
LIST_BASE = "https://www.msci.com/eqb/gimi/stdindex/"


def list_names_for(y0, y1):
    return [f"MSCI_{s}{yy:02d}_STPublicList.pdf"
            for yy in range(y0, y1 + 1) for s in SEASONS]


def fetch(y0=15, y1=25, max_files=12, lists=False):
    got = 0
    names = list_names_for(y0, y1) if lists else names_for(y0, y1)
    base = LIST_BASE if lists else BASE
    for n in names:
        p = DIR / n
        if p.exists() or got >= max_files:
            continue
        try:
            req = urllib.request.Request(
                base + n, headers={"User-Agent": "Mozilla/5.0"})
            b = urllib.request.urlopen(req, timeout=20).read()
            if b[:4] == b"%PDF":
                p.write_bytes(b)
                got += 1
                print(n, f"{len(b) // 1024}KB")
        except Exception as e:
            print(n, "MISS", str(e)[:40])
    have = len(list(DIR.glob("*.pdf")))
    print(f"archive: {have} PDFs")


def extract():
    for p in sorted(DIR.glob("*.pdf")):
        t = p.with_suffix(".txt")
        if not t.exists():
            subprocess.run(["pdftotext", "-layout", str(p), str(t)],
                           check=False)
    print("txt files:", len(list(DIR.glob("*.txt"))))


def check():
    from agents.reconstitution import parse_msci_public_list
    rows = []
    for t in sorted(DIR.glob("*.txt")):
        txt = t.read_text(errors="ignore")
        try:
            led = parse_msci_public_list(txt)
        except Exception:
            led = {}
        tw = led.get("TAIWAN", {})
        rows.append((t.stem, len(led),
                     len(tw.get("adds", [])),
                     len(tw.get("deletes", []))))
    for r in rows:
        print(f"{r[0]:24s} countries {r[1]:3d}  "
              f"TW +{r[2]} -{r[3]}")


if __name__ == "__main__":
    m = sys.argv[1] if len(sys.argv) > 1 else "fetch"
    if m == "fetch":
        y0 = int(sys.argv[2]) if len(sys.argv) > 2 else 15
        y1 = int(sys.argv[3]) if len(sys.argv) > 3 else 25
        fetch(y0, y1)
    elif m == "lists":
        y0 = int(sys.argv[2]) if len(sys.argv) > 2 else 15
        y1 = int(sys.argv[3]) if len(sys.argv) > 3 else 25
        fetch(y0, y1, lists=True)
    elif m == "extract":
        extract()
    elif m == "check":
        check()
