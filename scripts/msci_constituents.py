"""OFFICIAL MSCI constituents harvester (c-114).

THE FACT-CHECK (Bill's question): MSCI DOES publish full
constituent lists publicly — msci.com/constituents, the
"Index Constituents" tool. It exists because of regulatory
requirements (EU ESMA Guidelines for ETFs/UCITS), NOT as a
courtesy, which is why it carries two hard limits:

  1. DELAYED — the data is published roughly 2 months after
     the quarterly review effective date. Today (Aug 2026) the
     tool serves "As Of 01 Jun 2026" = the MAY-2026 review
     membership. It will NOT show the Aug-2026 review until
     ~Oct-2026. So it can never front-run a live review — for
     the Aug-26 trade our ETF census stays the primary source.
  2. NAMES + WEIGHTS ONLY — no tickers, no shares, no float.
     Joining to a tradeable universe still needs our own
     entity resolution.

What it DOES give us that nothing else does:
  - MSCI's OWN membership, authoritative, at a dated snapshot
    -> the independent check on the iShares-ETF census
  - CLOSING WEIGHTS -> the first real weight data in the
    project (the ETF census has none), which is what makes a
    weight treemap possible and what the reverse-roll needs
    to size historical index composition
  - the ANCHOR for the membership time machine: reverse-roll
    the changes DB from this dated official list backwards.

Endpoint (the tool's own XHR, no auth):
  /c/portal/layout?...&p_p_resource_id=<INDEX_CODE>
INDEX_CODES were read from the tool's own <select> options.
NEW ZEALAND is NOT offered by the tool — a REGISTERED GAP;
NZ keeps the ENZL-census membership only.

Usage:  py scripts\\msci_constituents.py harvest
        py scripts\\msci_constituents.py compare   (vs census)
Output: data/msci_official_constituents.json
"""
import json
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "msci_official_constituents.json"

URL = ("https://www-cdn.msci.com/c/portal/layout?p_l_id=54890583"
       "&p_p_cacheability=cacheLevelPage&p_p_id=indexconstituents"
       "_WAR_indexconstituents_INSTANCE_9uV8ur27dV1U"
       "&p_p_lifecycle=2&p_p_resource_id={code}")

# read from the tool's own dropdown (c-114). These are the
# STANDARD country indexes — the same family our change lists
# cover (not IMI, not 25/50, not capped variants).
INDEX_CODES = {
    "Australia": "903600", "China": "302400",
    "HongKong": "934400", "India": "935600",
    "Indonesia": "105767", "Japan": "939200",
    "Korea": "941000", "Malaysia": "105768",
    "Philippines": "860800", "Singapore": "998100",
    "Taiwan": "915800", "Thailand": "105769"}
NOT_OFFERED = {"NewZealand": "MSCI's public constituents tool "
                             "does not list a NEW ZEALAND "
                             "index (registered gap)"}


def harvest():
    import requests
    out = {"source": "MSCI public Index Constituents tool "
                     "(ESMA-mandated, ~2-month delayed)",
           "harvested": time.strftime("%Y-%m-%d"),
           "vintage_note": "serves the LAST review whose data "
                           "has aged ~2 months — verify the "
                           "'As Of' date on msci.com/constituents",
           "not_offered": NOT_OFFERED, "markets": {}}
    for mkt, code in INDEX_CODES.items():
        r = requests.get(URL.format(code=code), timeout=45,
                         headers={"User-Agent": "Mozilla/5.0"})
        r.raise_for_status()
        cons = r.json().get("constituents", [])
        rows = [{"security": c["security_name"],
                 "weight": float(c["security_weight"])}
                for c in cons]
        tot = sum(x["weight"] for x in rows)
        # GATE: weights must sum to ~100% (rounding tolerance)
        if not (99.0 <= tot <= 101.0):
            raise SystemExit(
                f"HALT: {mkt} weights sum to {tot:.3f}% — not a "
                "complete index (partial payload?)")
        out["markets"][mkt] = {"index_code": code,
                               "n": len(rows),
                               "weight_sum": round(tot, 4),
                               "constituents": rows}
        print(f"{mkt:12s} {len(rows):4d} names | "
              f"sum {tot:.3f}% | top "
              f"{rows[0]['security'][:24]} {rows[0]['weight']:.2f}%")
        time.sleep(0.6)
    OUT.write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(f"\n{len(out['markets'])} markets -> {OUT.name} "
          f"(NZ not offered)")
    return out


def _norm(s):
    s = re.sub(r"[^A-Z0-9 ]", " ", str(s).upper())
    return re.sub(r"\s+", " ", s).strip()


def compare():
    """Official list vs our iShares-ETF census — the
    independent cross-check. Differences are EXPECTED where
    the vintages differ (official is ~2 months delayed) and
    are reported, never silently reconciled."""
    import difflib
    sys.path.insert(0, str(ROOT / "scripts"))
    from ticker_backfill import prefix_match
    off = json.loads(OUT.read_text(encoding="utf-8"))["markets"]
    cen = json.loads((ROOT / "data" / "apac_members.json")
                     .read_text(encoding="utf-8"))["markets"]
    report = {}
    for mkt, o in off.items():
        c = cen.get(mkt, {})
        names = c.get("names") or {}
        cn = {_norm(names.get(t) or t): t
              for t in c.get("standard_members", [])}
        on = [_norm(x["security"]) for x in o["constituents"]]
        matched, miss = set(), []
        for nm in on:
            if nm in cn:
                matched.add(cn[nm])
                continue
            # MSCI abbreviates hard in this tool ('VANGUARD
            # INTL SC' = VANGUARD INTERNATIONAL SEMICONDUCT),
            # so token-PREFIX matching beats ratio-fuzzy here
            pm = prefix_match(nm, cn)
            if not pm:
                # BIDIRECTIONAL: either side can be the shorter
                # form ('TERUMO CORP' official vs 'TERUMO'
                # census, and the reverse) — try the census
                # name as the query too
                hits = [t for c_nm, t in cn.items()
                        if prefix_match(c_nm, {nm: t})]
                pm = hits[0] if len(hits) == 1 else None
            if pm:
                matched.add(pm)
                continue
            g = difflib.get_close_matches(nm, list(cn), n=1,
                                          cutoff=0.72)
            if g:
                matched.add(cn[g[0]])
            else:
                miss.append(nm)
        extra = [f"{t} {names.get(t, '')}".strip()
                 for t in c.get("standard_members", [])
                 if t not in matched]
        report[mkt] = {"official_n": o["n"],
                       "census_n": len(cn),
                       "official_not_in_census": miss,
                       "census_not_in_official": extra}
        flag = "" if not (miss or extra) else "  <-- differs"
        print(f"{mkt:12s} official {o['n']:4d} vs census "
              f"{len(cn):4d} | unmatched {len(miss)}/{len(extra)}"
              f"{flag}")
    p = ROOT / "data" / "constituents_crosscheck.json"
    p.write_text(json.dumps(report, indent=1), encoding="utf-8")
    print(f"\n-> {p.name}")
    return report


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "compare"
    harvest() if cmd == "harvest" else compare()
