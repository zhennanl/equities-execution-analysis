"""APAC constituent pipeline — the TW method, all review markets
(session 9i c-34).

For every APAC market in the MSCI review, membership is observed
from free public fund holdings, two independent angles:
  PRIMARY  single-country iShares MSCI ETF (25/50-capped variant —
           capping changes weights, NOT membership)
  CROSS    the composite subset: EEM (EM Standard) or EFA (EAFE
           Standard DM) filtered to the market's Location — the
           building-block principle makes this a second observation
           of the SAME country membership

Saves data/apac_members.json: per market, anchor codes, composite
codes, consistency diff, counts. Tickers stored as published
(numeric for JP/TW/KR/HK/CN-lines, alpha for AU/IN/MY/ID/PH).

Usage: python scripts/apac_members_harvest.py
"""
import csv
import io
import json
import sys
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "apac_members.json"
UA = {"User-Agent": "Mozilla/5.0"}
BASE = "https://www.ishares.com/us/products/{pid}/{slug}/latest-holdings.csv"

# market: (fund, product_id, slug, composite, Location value)
MARKETS = {
    "Japan":       ("EWJ",  239665, "ishares-msci-japan-etf",
                    "EFA", "Japan"),
    "Australia":   ("EWA",  239607, "ishares-msci-australia-etf",
                    "EFA", "Australia"),
    "HongKong":    ("EWH",  239657, "ishares-msci-hong-kong-etf",
                    "EFA", "Hong Kong"),
    "Korea":       ("EWY",  239681, "ishares-msci-south-korea-etf",
                    "EEM", "Korea (South)"),
    "Taiwan":      ("EWT",  239686, "ishares-msci-taiwan-etf",
                    "EEM", "Taiwan"),
    "China":       ("MCHI", 239619, "ishares-msci-china-etf",
                    "EEM", "China"),
    "India":       ("INDA", 239659, "ishares-msci-india-etf",
                    "EEM", "India"),
    "Malaysia":    ("EWM",  239669, "ishares-msci-malaysia-etf",
                    "EEM", "Malaysia"),
    # NOTE: EIDO/EPHE track IMI variants (Standard + Small Cap) —
    # their anchors are SUPERSETS; the EEM subset is the Standard
    # membership for these two markets (primary source flipped).
    "Indonesia":   ("EIDO", 239661, "ishares-msci-indonesia-etf",
                    "EEM", "Indonesia"),
    "Philippines": ("EPHE", 239675, "ishares-msci-philippines-etf",
                    "EEM", "Philippines"),
    # c-95: full-region completion. ENZL and THD track IMI
    # variants (like EIDO/EPHE) -> Standard = composite subset;
    # EWS tracks the 25/50 Standard family (like EWT).
    "NewZealand":  ("ENZL", 239672, "ishares-msci-new-zealand-etf",
                    "EFA", "New Zealand"),
    "Singapore":   ("EWS",  239678, "ishares-msci-singapore-etf",
                    "EFA", "Singapore"),
    "Thailand":    ("THD",  239688, "ishares-msci-thailand-etf",
                    "EEM", "Thailand"),
}
IMI_ANCHORS = {"Indonesia", "Philippines", "NewZealand",
               "Thailand"}                   # anchor = IMI superset
COMPOSITES = {"EEM": (239637, "ishares-msci-emerging-markets-etf"),
              "EFA": (239623, "ishares-msci-eafe-etf")}


def _fetch_csv(pid, slug):
    r = requests.get(BASE.format(pid=pid, slug=slug), headers=UA,
                     timeout=45)
    r.raise_for_status()
    return list(csv.reader(io.StringIO(r.text)))


def _equity_rows(rows, location=None):
    hdr_i = next(i for i, r in enumerate(rows)
                 if r and r[0] == "Ticker")
    cols = rows[hdr_i]
    ai, li = cols.index("Asset Class"), cols.index("Location")
    ni = cols.index("Name")
    out = {}
    for r in rows[hdr_i + 1:]:
        if len(r) <= max(ai, li, ni) or r[ai] != "Equity":
            continue
        if location and r[li] != location:
            continue
        t = (r[0] or "").strip()
        if t and t not in ("-", "--"):
            out[t] = r[ni]
    asof = rows[1][1] if len(rows) > 1 and len(rows[1]) > 1 else "?"
    return out, asof


def main():
    comp_cache = {}
    for tag, (pid, slug) in COMPOSITES.items():
        comp_cache[tag] = _fetch_csv(pid, slug)
        time.sleep(1)
    out = {"generated": time.strftime("%Y-%m-%d"),
           "method": "single-country iShares anchor + composite "
                     "(EEM/EFA) subset cross-check; see "
                     "docs/CONSTITUENT_PIPELINE_FRAMEWORK.md",
           "markets": {}}
    for mkt, (fund, pid, slug, comp, loc) in MARKETS.items():
        try:
            rows = _fetch_csv(pid, slug)
            anchor, asof = _equity_rows(rows)
        except Exception as ex:                # noqa: BLE001
            out["markets"][mkt] = {"error": str(ex)}
            continue
        cross, casof = _equity_rows(comp_cache[comp], location=loc)
        a, c = set(anchor), set(cross)
        out["markets"][mkt] = {
            "fund": fund, "asof": asof,
            "anchor_variant": ("IMI (superset — Standard = "
                               "composite subset)"
                               if mkt in IMI_ANCHORS
                               else "Standard 25/50"),
            "standard_members": sorted(
                c if mkt in IMI_ANCHORS else a | c),
            "composite": comp, "composite_asof": casof,
            "n_anchor": len(a), "n_composite": len(c),
            "confirmed_both": sorted(a & c),
            "anchor_only": sorted(a - c),
            "composite_only": sorted(c - a),
            "names": {t: anchor.get(t) or cross.get(t)
                      for t in sorted(a | c)}}
        m = out["markets"][mkt]
        print(f"{mkt:12s} {fund}: anchor {m['n_anchor']:4d} | "
              f"{comp}-subset {m['n_composite']:4d} | confirmed "
              f"{len(m['confirmed_both']):4d} | anchor-only "
              f"{len(m['anchor_only'])} | comp-only "
              f"{len(m['composite_only'])}")
        time.sleep(1)
    OUT.write_text(json.dumps(out, indent=1))
    print("wrote", OUT)


if __name__ == "__main__":
    main()
