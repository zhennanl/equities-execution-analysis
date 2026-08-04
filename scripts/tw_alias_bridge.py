"""Taiwan alias bridge — MSCI English names -> TWSE codes, 2015-2026.

Session 9i. The pre-2025 MSCI TW unlock: MSCI STPublicLists carry
English names only; this bridge maps them to stock codes using the
TWSE ISIN registry's ENGLISH page (isin.twse.com.tw/isin/
e_C_public.jsp?strMode=2 — code + English security name, live
official source) with the decade bridge's token matcher + the
project's ~35 print-verified seed aliases.

Honesty notes (same class as the CN/JP/HK bridge):
  * The ISIN page lists CURRENT equities — names delisted since
    their event cannot match (survivorship in COVERAGE; unmatched
    names are ledgered, never guessed).
  * Bridge-matched aliases are tagged UNVERIFIED until an event
    print confirms them (the HONPRECISION technique); the IB/STOCK_
    DAY fetch validates opportunistically.
  * Effective dates: parsed from the archive press releases
    (window_study_decade._pr_dates); announcement likewise.

Output: data/msci_tw_events.json
  {season: {ann, eff, adds: {code: name}, dels: {code: name},
            unmatched: [names]}}
Usage: python scripts/tw_alias_bridge.py [build|report]
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

OUT = ROOT / "data" / "msci_tw_events.json"

# Print-verified seeds (tw_expost_msci CODES + registry + FEB map)
SEEDS = {
    "CALIWAY BIOPHARMA": "6919", "KING SLIDE WORKS CO": "2059",
    "POU CHEN CORP": "9904", "RUENTEX DEVELOPMENT CO": "9945",
    "BIZLINK HOLDING": "3665", "CHROMA ATE": "2360",
    "GOLD CIRCUIT ELECTRONICS": "2368",
    "KING YUAN ELECTRONICS CO": "2449",
    "TECO ELECTRIC & MACH": "1504", "ACER": "2353",
    "AUO CORP": "2409", "MICRO-STAR INTERNATIONAL": "2377",
    "SILERGY CORP": "6415", "SYNNEX TECHNOLOGY INTL": "2347",
    "VOLTRONIC POWER TECH": "6409", "WPG HOLDINGS CO": "3702",
    "ASIA CEMENT CORP": "1102", "CATCHER TECH CO": "2474",
    "CHINA AIRLINES": "2610", "COMPAL ELECTRONICS": "2324",
    "FAR EASTERN NEW CENTURY": "1402",
    "TAIWAN HIGH SPEED RAIL": "2633",
    "CHENG SHIN RUBBER IND": "2105", "ECLAT TEXTILE CO": "1476",
    "FENG TAY ENTERPRISE CO": "9910", "NIEN MADE ENTERPRISE": "8464",
    "NIEN MADE ENTERPRISE CO": "8464", "WAN HAI LINES": "2615",
    "YANG MING MARINE TRANSP": "2609", "EVA AIRWAYS CORP": "2618",
    "UNIMICRON TECHNOLOGY": "3037", "NANYA TECHNOLOGY": "2408",
    "WALSIN LIHWA CORP": "1605", "WISTRON CORP": "3231",
    "MOMO.COM": "8454", "GIGABYTE TECHNOLOGY CO": "2376",
    "WIN SEMICONDUCTORS": "3105",       # TPEx — flagged downstream
    "ASMEDIA TECHNOLOGY": "5269",
}


def _containment(nm, cands):
    """The ISIN English master uses ABBREVIATED names (ACCTON, GIANT)
    — accept when exactly ONE master entry's tokens are all contained
    in the MSCI name's tokens, with a length guard against 2-letter
    stubs (YL-class false positives)."""
    from scripts.window_study_decade import _toks
    mt = set(_toks(nm))
    hits = []
    for code, ctoks in cands:
        if not ctoks:
            continue
        if all(len(t) >= 4 for t in ctoks) \
                and all(t in mt for t in ctoks):
            hits.append(code)
    return hits[0] if len(hits) == 1 else None


# Acronym / delisted / TPEx names the containment pass cannot reach.
# Domain-knowledge seeds, tagged UNVERIFIED-SEED until an event print
# confirms them (delisted codes noted — data may end pre-2026).
SEEDS_EXTRA = {
    "FORMOSA PETROCHEMICAL CO": "6505",   # master 'FPCC' acronym
    "FAR EAST DEPT STORES": "2903",
    "FARGLORY LAND DEV": "5522",
    "FORMOSA INTL HOTELS": "2707",
    "FORMOSA TAFFETA CO": "1434",
    "EPISTAR CORP": "2448",               # delisted 2021 (Ennostar)
    "E INK HOLDINGS": "8069",             # TPEx
    "EMEMORY TECHNOLOGY": "3529",         # TPEx
    "ASPEED TECHNOLOGY": "5274",          # TPEx
    "CHINA MOTOR CORP": "2204",
    "CHICONY ELECTRONICS CO": "2385",
    "ASIA VITAL COMPONENTS": "3017",
    "ELITE MATERIAL CO": "2383",
    "FORTUNE ELECTRIC CO": "1519",
    "CASETEK HOLDINGS": "5264",           # delisted 2019
    "ASIA PACIFIC TELECOM CO": "3682",    # merged/delisted 2022
    "ECLAT TEXTILE COMPANY": "1476",
    # batch 2 (acronym-mastered / TPEx / delisted). TPEx marked —
    # TWSE data layers exclude them; IB TPEX fallback may serve.
    "FOXCONN TECHNOLOGY CO": "2354",
    "GENERAL INTERFACE SOLN": "6456",
    "GLOBAL UNICHIP CORP": "3443",        # master 'GUC'
    "INTL GAMES SYSTEM C": "3293",        # TPEx
    "MERIDA INDUSTRY CO": "9914",
    "MPI CORP": "6223",                   # TPEx
    "NAN YA PRINTED CIRCUIT": "8046",
    "OBI PHARMA": "4174",                 # TPEx
    "ONENESS BIOTECH": "4743",            # TPEx
    "PARADE TECHNOLOGIES": "4966",        # TPEx
    "PHARMAESSENTIA": "6446",
    "PHISON ELECTRONICS CORP": "8299",    # TPEx
    "POWERCHIP SEMICONDUCTOR": "6770",
    "RADIANT OPTO-ELECTRONICS": "6176",
    "RUENTEX INDUSTRIES": "2915",         # master 'RUENTEX IND.LTD'
    "SCINOPHARM TAIWAN": "1789",
    "SHANGHAI COMM & SAV BANK": "5876",
    "SIMPLO TECHNOLOGY CO": "6121",       # TPEx
    "STANDARD FOODS CORP": "1227",
    "TAIMED BIOLOGICS": "4147",           # TPEx
    "TATUNG": "2371",
    "TPK HOLDING CO": "3673",
    "TRANSCEND INFORMATION": "2451",
    "U-MING MARINE TRANSPORT": "2606",
    "WALSIN TECHNOLOGY CORP": "2492",
    "WIWYNN CORPORATION": "6669",
    "YAGEO CORP": "2327",
    "YULON MOTOR CO": "2201",
    "KINSUS INTERCONNECT TECH": "3189",
    "TAIWAN GLASS INDL CORP": "1802",
    "TAIWAN FERTILIZER CO": "1722",
    "HIGHWEALTH CONSTRUCTION": "2542",
    "CLEVO COMPANY": "2362",
    "TAIWAN BUSINESS BANK": "2834",
    "MACRONIX INTERNATIONAL": "2337",
    "AIRTAC INTERNATIONAL": "1590",
    "ACCTON TECHNOLOGY CORP": "2345",
    "ALCHIP TECHNOLOGIES": "3661",
    "GIANT MANUFACTURING CO.": "9921",
    "CHINA STEEL CHEM": "1723",
    "WINBOND ELECTRONICS CORP": "2344",
    # HONPRECISION deliberately NOT seeded: the 2354 alias was
    # REJECTED by its own non-print (Feb-2026 record) — needs a
    # fresh investigation, not a guess.
}


def fetch_master():
    """TWSE ISIN English page -> {code: english_name} (equities).
    Disk-cached — the ISIN server throttles repeat hits."""
    import requests
    cache = ROOT / "data" / "tw_isin_master.json"
    if cache.exists():
        return json.loads(cache.read_text(encoding="utf-8"))
    r = requests.get("https://isin.twse.com.tw/isin/e_C_public.jsp"
                     "?strMode=2", timeout=40,
                     headers={"User-Agent": "Mozilla/5.0"})
    r.encoding = "big5"     # page mixes; names are ASCII anyway
    rows = re.findall(r"<td[^>]*>([0-9]{4,6})　([^<]+)</td>",
                      r.text)
    if not rows:            # fallback: plain-space separator
        rows = re.findall(r"<td[^>]*>([0-9]{4,6})\s+([A-Z][^<]+)</td>",
                          r.text)
    out = {c: n.strip() for c, n in rows if len(c) == 4}
    cache.write_text(json.dumps(out, ensure_ascii=False))
    return out


def tw_names():
    """All TAIWAN adds/dels 2015-2026 from official ledgers."""
    from scripts.tw_expost_msci import _rows_2026
    from scripts.msci_key_stats import ledgers
    out = []
    for r in ledgers() + _rows_2026():
        if r["market"] != "TAIWAN":
            continue
        out.append((r["season"], r.get("rtype", ""),
                    r["adds"], r["dels"]))
    return out


def build():
    from scripts.window_study_decade import _pr_dates, _toks, _match
    master = fetch_master()
    cands = [(c, _toks(n)) for c, n in master.items()]
    print(f"English master: {len(master)} listed equities")
    events, all_unmatched = {}, set()
    for season, _, adds, dels in tw_names():
        if not (adds or dels):
            continue
        if season in ("Feb26", "May26"):
            ann, eff = {"Feb26": ("2026-02-10", "2026-02-26"),
                        "May26": ("2026-05-12", "2026-05-29")}[season]
        else:
            ann, eff = _pr_dates(season)
        if not eff and ann:      # MSCI rule: close of month's last bday
            import pandas as pd
            eff = (pd.Timestamp(ann) + pd.offsets.BMonthEnd(0)
                   ).strftime("%Y-%m-%d")
        ev = {"ann": ann, "eff": eff, "adds": {}, "dels": {},
              "unmatched": []}
        for side, names in (("adds", adds), ("dels", dels)):
            for nm in names:
                code = SEEDS.get(nm.strip()) or SEEDS_EXTRA.get(nm.strip())
                if not code:
                    code, _sc = _match(_toks(nm), cands)
                if not code:
                    code = _containment(nm, cands)
                if code:
                    ev[side][code] = nm
                else:
                    ev["unmatched"].append(nm)
                    all_unmatched.add(nm)
        events[season] = ev
    OUT.write_text(json.dumps(events, ensure_ascii=False, indent=1))
    n_ev = sum(1 for e in events.values() if e["adds"] or e["dels"])
    n_named = sum(len(e["adds"]) + len(e["dels"])
                  for e in events.values())
    n_un = sum(len(e["unmatched"]) for e in events.values())
    print(f"{n_ev} events with matched codes; {n_named} name-matches,"
          f" {n_un} unmatched occurrences "
          f"({len(all_unmatched)} unique)")
    if all_unmatched:
        print("unmatched:", sorted(all_unmatched)[:20])
    return events


def report():
    ev = json.loads(OUT.read_text(encoding="utf-8"))
    for season in sorted(ev, key=lambda s: (s[-2:], s[:3])):
        e = ev[season]
        if e["adds"] or e["dels"]:
            print(f"{season:6s} ann {e['ann']} eff {e['eff']} "
                  f"+{list(e['adds'])} -{list(e['dels'])}"
                  + (f" ?{e['unmatched']}" if e["unmatched"] else ""))


if __name__ == "__main__":
    {"build": build, "report": report}[
        sys.argv[1] if len(sys.argv) > 1 else "build"]()
