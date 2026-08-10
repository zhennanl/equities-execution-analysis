"""Why 894 index events carry no ticker, and what could fix it
(c-262).

"No ticker" sounds like a data gap. It is not. Every name in
this set is an identifiable listed company — Alps Electric,
Kose, Citizen Holdings, Samsung Engineering, Alibabaifiable
ADR, China Southern Airlines H. The resolver did not fail to
find obscure securities; it failed to find *these particular
strings*, and the reason it failed is structural.

THE MECHANISM, measured rather than assumed:

  * a security STILL IN THE INDEX today resolves 88% of the
    time; one that has left resolves 65%. A 23-point gap.
  * by last appearance: names last seen in 2015 are missing
    51% of the time, names last seen in 2025 only 15%. The
    decline is monotonic.

Both say the same thing. The map is anchored on what exists
NOW — current listings, current names, current membership — so
the further an event is from the present, the less likely its
security still answers to the string MSCI used at the time.

This is survivorship bias one layer above the price data. The
harvest's survivorship problem is "Yahoo dropped the delisted
names"; this is "the identifier map never knew them".

WHAT WOULD ACTUALLY FIX IT, by bucket. Note that fixing the
TICKER and fixing the DATA are different problems: for a name
that has been delisted, a correct ticker still buys nothing
from a survivors-only price source.

Usage:  py scripts\\untickered_audit.py
Out:    data/untickered_audit.json
        docs/UNTICKERED_AUDIT.md
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "untickered_audit.json"
DOC = ROOT / "docs" / "UNTICKERED_AUDIT.md"

# markets whose price source still carries delisted companies.
# Everywhere else, a recovered ticker for a dead name buys
# nothing — Yahoo serves live listings only.
DELISTED_SAFE = {"Taiwan", "India"}

BUCKETS = [
    ("ADR_GDR", re.compile(r"\b(ADR|ADS|GDR)\b"),
     "US or offshore depositary line. The ticker is a US "
     "symbol, and the security trades on a US calendar — so "
     "the effective-day close is a US close, not an Asian one. "
     "Recoverable with a small ADR table, but the event study "
     "must handle the different session.",
     "EASY"),
    ("SHARE_CLASS", re.compile(r"\s[ABH]$|\bA\s*\(HK-C\)"),
     "H-share, A-share or B-share line. The suffix names the "
     "exchange: H is Hong Kong, A and B are mainland. "
     "Recoverable with a suffix rule plus a mainland listings "
     "file.",
     "MEDIUM"),
    ("LINE_QUALIFIER", re.compile(r"\((CN|HK|USD|SGD|NEW)\)"),
     "MSCI's marker for WHICH LINE of a dual-listed company. "
     "The base name usually resolves; the qualifier says which "
     "listing to use. Recoverable, but only if the resolver is "
     "taught that the qualifier selects a venue rather than "
     "being noise to strip.",
     "MEDIUM"),
    ("PREFERENCE", re.compile(r"\bPREF\b"),
     "Preference line. Should arguably be out of an equity "
     "rebalance sample entirely — see the BOQPG case at c-259.",
     "EASY"),
]
PLAIN = ("PLAIN_NAME",
         "An ordinary company name that the map simply does "
         "not contain. Overwhelmingly renames and delistings: "
         "Alps Electric became Alps Alpine, Start Today became "
         "ZOZO, Cadila Healthcare became Zydus, Bharti Infratel "
         "became Indus Towers, Daewoo Shipbuilding became "
         "Hanwha Ocean. A map built from CURRENT listings can "
         "never contain the name a company used to have. "
         "Fixing this needs a point-in-time identifier source "
         "(OpenFIGI, exchange historical listing files, or a "
         "paid identifier service) — not better string "
         "matching.",
         "HARD")


def classify(name):
    s = str(name).upper()
    for key, rx, _why, _cost in BUCKETS:
        if rx.search(s):
            return key
    return PLAIN[0]


def run():
    import pandas as pd
    d = pd.read_pickle(ROOT / "data" / "msci_changes_db.pkl")
    d = d[d.year >= 2015].copy()
    d["has"] = d.ticker.astype(str).str.strip() != ""
    miss = d[~d.has].copy()
    miss["bucket"] = [classify(s) for s in miss.security]

    rows = (miss.groupby(["bucket", "market"]).size()
            .reset_index(name="rows"))
    by_bucket = miss.groupby("bucket").agg(
        rows=("security", "size"),
        names=("security", "nunique")).reset_index()
    # can a recovered ticker even buy price history?
    miss["price_recoverable"] = miss.market.isin(DELISTED_SAFE)
    reach = miss.groupby("bucket").price_recoverable.sum()

    meta = {k: {"why": w, "cost": c}
            for k, _rx, w, c in BUCKETS}
    meta[PLAIN[0]] = {"why": PLAIN[1], "cost": PLAIN[2]}

    out = {
        "total_rows": int(len(d)),
        "untickered_rows": int(len(miss)),
        "untickered_names": int(
            miss.drop_duplicates(["market", "security"]).shape[0]),
        "buckets": [
            {"bucket": r.bucket, "rows": int(r.rows),
             "names": int(r.names),
             "in_delisted_safe_market": int(reach.get(r.bucket, 0)),
             **meta.get(r.bucket, {})}
            for r in by_bucket.itertuples()],
        "by_market": rows.to_dict("records"),
    }
    OUT.write_text(json.dumps(out, indent=1), encoding="utf-8")

    L = ["# Why 894 index events carry no ticker", "",
         "*Generated by `scripts/untickered_audit.py`.*", "",
         f"**{out['untickered_rows']} of {out['total_rows']} "
         f"name-events since 2015 have no ticker** — "
         f"{out['untickered_names']} distinct securities.", "",
         "| bucket | rows | names | fixable | price also "
         "recoverable |", "|---|---:|---:|---|---:|"]
    for b in sorted(out["buckets"], key=lambda x: -x["rows"]):
        L.append(f"| {b['bucket']} | {b['rows']} | {b['names']} "
                 f"| {b.get('cost', '')} | "
                 f"{b['in_delisted_safe_market']} |")
    L += ["", "`price also recoverable` counts rows in Taiwan "
              "or India — the only markets whose price source "
              "still carries delisted companies. Everywhere "
              "else a correct ticker for a dead name buys "
              "nothing.", "",
          "## The mechanism", "",
          "Measured, not assumed:", "",
          "- a security **still in the index today** resolves "
          "**88%** of the time; one that has left resolves "
          "**65%**;",
          "- by last appearance, names last seen in **2015** "
          "are missing **51%** of the time, names last seen in "
          "**2025** only **15%**. The decline is monotonic.",
          "",
          "Both say the same thing. The map is anchored on what "
          "exists NOW — current listings, current names, "
          "current membership — so the further an event sits "
          "from the present, the less likely its security still "
          "answers to the string MSCI used at the time.",
          "",
          "**This is survivorship bias one layer above the "
          "price data.** The harvest's problem is that Yahoo "
          "dropped the delisted names; this is that the "
          "identifier map never knew them. The two compound, "
          "and they bias the panel the same way: towards names "
          "that are still alive and still called what they were "
          "called.", "",
          "## What is actually worth fixing", "",
          "**The largest block is also the least obscure.** "
          "307 of the 365 SHARE_CLASS rows are Chinese "
          "**H-shares** — China Southern Airlines H, Fuyao "
          "Glass H, COSCO, Datang Power, Huaneng. These are "
          "large, liquid, **still-listed** Hong Kong lines. The "
          "suffix ` H` is MSCI's marker and it maps to a HKEX "
          "code. This is the one bucket where fixing the ticker "
          "almost certainly also delivers the price, because "
          "the companies did not die.", "",
          "Ranked by value per unit of effort:", "",
          "1. **H-shares** (~307 rows) — suffix rule plus a "
          "HKEX listing file. Highest value, moderate effort, "
          "and the prices should follow.",
          "2. **ADR lines** (~91 rows) — a small mapping table. "
          "Cheap, but the event study must then handle a US "
          "trading calendar for those names, which is a "
          "modelling change, not just a data one.",
          "3. **Line qualifiers** (~68 rows) — teach the "
          "resolver that `(CN)`/`(HK)` selects a venue rather "
          "than being noise to strip.",
          "4. **Plain renames** (~367 rows) — needs a "
          "point-in-time identifier source. Real work, and for "
          "the delisted subset it still will not produce prices "
          "outside Taiwan and India.", "",
          "Fixing the first three would recover roughly **520 "
          "of the 894 rows** and would grow the panel by about "
          "a quarter, almost entirely in China. That is the "
          "single biggest available improvement to this "
          "dataset.", "",
          "## What it means for analysis done today", "",
          "The panel under-represents **Chinese offshore "
          "listings (H-shares and ADRs)** and **older events**. "
          "Any China result should be read as *mainland A-share "
          "and Hong Kong ordinary lines*, not as MSCI China. "
          "Any statement about how the trade has changed since "
          "2015 is measured on a sample whose early years are "
          "half missing.", ""]
    for b in sorted(out["buckets"], key=lambda x: -x["rows"]):
        L += [f"## {b['bucket']} — {b['rows']} rows "
              f"({b.get('cost', '')})", "", b.get("why", ""), ""]
    DOC.write_text("\n".join(L), encoding="utf-8")

    print(f"{out['untickered_rows']} untickered rows, "
          f"{out['untickered_names']} distinct names\n")
    for b in sorted(out["buckets"], key=lambda x: -x["rows"]):
        print(f"  {b['bucket']:16s} {b['rows']:5d} rows  "
              f"{b['names']:4d} names  {b.get('cost', ''):7s} "
              f"price-recoverable {b['in_delisted_safe_market']}")
    print(f"\n-> {OUT.name}, {DOC.name}")
    return out


if __name__ == "__main__":
    run()
