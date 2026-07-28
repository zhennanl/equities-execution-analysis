#!/usr/bin/env python3
"""Convert iShares country-ETF holdings CSVs into VALIDATED membership
universes for the QIR screener — the NO-CALL -> call conversion path
for the 8 uncovered markets.

The sandbox cannot fetch these CSVs (anti-bot), but a browser can, in
seconds each. Download 'Detailed Holdings and Analytics' for:
    MCHI (China), INDA (India), EWS (Singapore), EWH (Hong Kong),
    THD (Thailand), EWM (Malaysia), EIDO (Indonesia), EPHE (Philippines)
into data/holdings/<TICKER>.csv, then:

    python scripts/ingest_holdings.py            # parse + report all
    python scripts/ingest_holdings.py MCHI       # one market

Output per market: validated member list + weights, bottom-decile
DELETION WATCH ZONE (smallest float-cap members = the at-risk cohort),
and a universe skeleton json the QIR screener consumes after boundary
caps are fetched (run_qir_aug2026-style chunked yfinance pass).

Method note (honest): holdings weights are float-cap-proportional, so
weight rank IS the deletion-relevance rank; the ADD side still needs
non-member candidates (weight files cannot contain them) — adds stay
NO-CALL until a candidate list is added per market.
"""
import csv
import io
import json
import sys
from pathlib import Path

HOLDINGS_DIR = Path("data/holdings")
OUT = Path("data/holdings_universes.json")

MARKETS = {"MCHI": "China", "INDA": "India", "EWS": "Singapore",
           "EWH": "Hong Kong", "THD": "Thailand", "EWM": "Malaysia",
           "EIDO": "Indonesia", "EPHE": "Philippines"}


def parse_ishares_csv(text: str) -> list[dict]:
    """iShares CSVs carry preamble lines before the header row; find the
    header (starts with 'Ticker'), read equity rows."""
    lines = text.splitlines()
    start = next((i for i, l in enumerate(lines)
                  if l.startswith("Ticker")), None)
    if start is None:
        return []
    rows = []
    for r in csv.DictReader(io.StringIO("\n".join(lines[start:]))):
        if (r.get("Asset Class") or "").strip() != "Equity":
            continue
        try:
            w = float((r.get("Weight (%)") or "0").replace(",", ""))
        except ValueError:
            continue
        rows.append({"ticker": (r.get("Ticker") or "").strip(),
                     "name": (r.get("Name") or "").strip(),
                     "weight_pct": w,
                     "exchange": (r.get("Exchange") or "").strip(),
                     "location": (r.get("Location") or "").strip()})
    return sorted(rows, key=lambda x: -x["weight_pct"])


def report(etf: str) -> dict | None:
    p = HOLDINGS_DIR / f"{etf}.csv"
    if not p.exists():
        print(f"{etf} ({MARKETS[etf]}): file missing -> still NO-CALL")
        return None
    rows = parse_ishares_csv(p.read_text(encoding="utf-8-sig",
                                         errors="replace"))
    if not rows:
        print(f"{etf}: parse failed — check format")
        return None
    n = len(rows)
    decile = max(3, n // 10)
    watch = rows[-decile:]
    print(f"\n===== {MARKETS[etf]} ({etf}): {n} members (validated "
          "membership from fund holdings) =====")
    print(f"DELETION WATCH ZONE (bottom {decile} by weight — "
          "float-cap rank):")
    for r in watch:
        print(f"  {r['ticker']:8s} {r['name'][:36]:36s} "
              f"{r['weight_pct']:.3f}%")
    print("ADD side: NO-CALL until a non-member candidate list is "
          "built for this market.")
    return {"market": MARKETS[etf], "n_members": n,
            "members": rows, "watch_zone": watch}


def main():
    targets = [a for a in sys.argv[1:] if a in MARKETS] or list(MARKETS)
    out = {}
    for etf in targets:
        r = report(etf)
        if r:
            out[etf] = r
    if out:
        OUT.write_text(json.dumps(out))
        print(f"\nuniverse skeletons -> {OUT} (feed to QIR screener "
              "after a boundary-cap yfinance pass)")


if __name__ == "__main__":
    main()
