"""Taiwan MSCI ex-post review 2015-2026 + official re-grade + drivers.

Session 9i. Four jobs:
  export   : full APAC change list 2015-2026 from official ledgers ->
             docs/MSCI_APAC_CHANGES_2015_2026.md (TW per-review table
             with Aug-QIR base rates)
  fetch    : STOCK_DAY months for the 2025-26 TW change cohort
             (curated code map below, each alias PRINT-VERIFIED)
  classify : mechanical driver classification per change:
             ret_3m into announcement + print check ->
             DECLINE / DRIFT / STALE (deletes),
             MOMENTUM / STEADY (adds); TPEx names = NO-DATA (stated)
  boundary : Aug-2026 TW distances to the 0.5x floor and 1.8x add
             bar at REFRESHED caps — the honest answer to "I don't
             believe zero calls"

The official-key RE-GRADE (in the doc): the 2025 backtest used
detector-reconstructed keys; the MSCI archive (solved later, 9a)
holds the official lists. Corrections are stated, not smoothed over.

Usage: python scripts/tw_expost_msci.py [export|fetch|classify|boundary]
"""
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SD = ROOT / "data" / "tw_history" / "stock_day.json"
DOC = ROOT / "docs" / "MSCI_APAC_CHANGES_2015_2026.md"

# Curated TW alias map, 2025-26 cohort (each verified by event print
# or rejected to NO-DATA). TPEx listings marked — STOCK_DAY is TWSE.
CODES = {
    "CALIWAY BIOPHARMA": "6919", "KING SLIDE WORKS CO": "2059",
    "POU CHEN CORP": "9904", "RUENTEX DEVELOPMENT CO": "9945",
    "ASPEED TECHNOLOGY": None,          # 5274 TPEx — no STOCK_DAY
    "BIZLINK HOLDING": "3665", "CHROMA ATE": "2360",
    "GOLD CIRCUIT ELECTRONICS": "2368",
    "KING YUAN ELECTRONICS CO": "2449",
    "TECO ELECTRIC & MACH": "1504", "ACER": "2353",
    "AUO CORP": "2409", "MICRO-STAR INTERNATIONAL": "2377",
    "SILERGY CORP": "6415", "SYNNEX TECHNOLOGY INTL": "2347",
    "VOLTRONIC POWER TECH": "6409", "WPG HOLDINGS CO": "3702",
    "MPI CORP": None,                   # 6223 TPEx
    "ASIA CEMENT CORP": "1102", "CATCHER TECH CO": "2474",
    "CHINA AIRLINES": "2610", "COMPAL ELECTRONICS": "2324",
    "FAR EASTERN NEW CENTURY": "1402",
    "TAIWAN HIGH SPEED RAIL": "2633",
    "CHENG SHIN RUBBER IND": "2105", "ECLAT TEXTILE CO": "1476",
    "FENG TAY ENTERPRISE CO": "9910", "NIEN MADE ENTERPRISE": "8464",
}

# 2025-26 TW events: (season, ann_date, eff_date, adds, dels)
EVENTS = [
    ("Aug25", "2025-08-07", "2025-08-28",
     ["CALIWAY BIOPHARMA", "KING SLIDE WORKS CO"],
     ["POU CHEN CORP", "RUENTEX DEVELOPMENT CO"]),
    ("Nov25", "2025-11-06", "2025-11-27",
     ["ASPEED TECHNOLOGY", "BIZLINK HOLDING", "CHROMA ATE",
      "GOLD CIRCUIT ELECTRONICS", "KING YUAN ELECTRONICS CO",
      "TECO ELECTRIC & MACH"],
     ["ACER", "AUO CORP", "MICRO-STAR INTERNATIONAL", "SILERGY CORP",
      "SYNNEX TECHNOLOGY INTL", "VOLTRONIC POWER TECH",
      "WPG HOLDINGS CO"]),
    ("Feb26", "2026-02-10", "2026-02-26",
     [],
     ["CHENG SHIN RUBBER IND", "ECLAT TEXTILE CO",
      "FENG TAY ENTERPRISE CO", "NIEN MADE ENTERPRISE"]),
    ("May26", "2026-05-12", "2026-05-29",
     ["MPI CORP"],
     ["ASIA CEMENT CORP", "CATCHER TECH CO", "CHINA AIRLINES",
      "COMPAL ELECTRONICS", "FAR EASTERN NEW CENTURY",
      "TAIWAN HIGH SPEED RAIL", "TECO ELECTRIC & MACH"]),
]


def _months_needed():
    out = set()
    for _, ann, eff, adds, dels in EVENTS:
        for nm in adds + dels:
            c = CODES.get(nm)
            if not c:
                continue
            a = pd.Timestamp(ann)
            for k in range(4, -1, -1):
                out.add((c, (a - pd.DateOffset(months=k))
                         .strftime("%Y%m")))
            out.add((c, pd.Timestamp(eff).strftime("%Y%m")))
    return sorted(out)


def fetch():
    from scripts.twap_vwap_moc_study import fetch_month
    cache = json.loads(SD.read_text()) if SD.exists() else {}
    todo = [(c, m) for c, m in _months_needed()
            if m not in cache.get(c, {})]
    print(f"{len(todo)} code-months missing")
    import time
    for c, m in todo:
        time.sleep(1.2)
        try:
            cache.setdefault(c, {})[m] = fetch_month(c, m)
        except Exception as e:                        # noqa: BLE001
            print(" ", c, m, str(e)[:40])
        SD.write_text(json.dumps(cache))
    print("done")


def _px(cache, code, upto, back=0):
    rows = [r for m in sorted(cache.get(code, {}))
            for r in cache[code][m] if r[0] <= upto]
    return rows[-1 - back] if len(rows) > back else None


def classify():
    cache = json.loads(SD.read_text())
    rows = []
    for season, ann, eff, adds, dels in EVENTS:
        a3 = (pd.Timestamp(ann) - pd.DateOffset(months=3)
              ).strftime("%Y-%m-%d")
        for side, names in (("ADD", adds), ("DELETE", dels)):
            for nm in names:
                c = CODES.get(nm)
                if not c:
                    rows.append({"season": season, "name": nm,
                                 "side": side, "code": "TPEx",
                                 "ret_3m_pct": None,
                                 "driver": "NO-DATA (TPEx listing)"})
                    continue
                now = _px(cache, c, ann)
                then = _px(cache, c, a3)
                t_day = _px(cache, c, eff)
                if not (now and then):
                    rows.append({"season": season, "name": nm,
                                 "side": side, "code": c,
                                 "ret_3m_pct": None,
                                 "driver": "NO-DATA"})
                    continue
                r3 = (now[6] / then[6] - 1) * 100
                if side == "DELETE":
                    drv = ("DECLINE (cap fell to floor)" if r3 < -15
                           else "DRIFT (slow bleed)" if r3 < -3
                           else "STALE (flat: migration/FF cut)")
                else:
                    drv = ("MOMENTUM (re-rating into threshold)"
                           if r3 > 20 else "STEADY (size growth)")
                rows.append({"season": season, "name": nm,
                             "side": side, "code": c,
                             "ret_3m_pct": round(r3, 1),
                             "eff_close": t_day[6] if t_day else None,
                             "driver": drv})
    df = pd.DataFrame(rows)
    print(df.to_string(index=False))
    mix = df[df["ret_3m_pct"].notna()].groupby(
        ["side", "driver"])["name"].count()
    print("\ndriver mix:\n", mix.to_string())
    return df


def boundary():
    sys.path.insert(0, str(ROOT))
    from agents.review_engine import screen_market
    from scripts.run_full_review_asia import COUNT, post_may_universe
    u = post_may_universe("Taiwan")
    s = screen_market(u, review="QIR", member_count=COUNT["Taiwan"],
                      tail_hi=10e9, tail_n=500)
    g = s["gmsr"]
    real = u[~u["ticker"].str.startswith("TAIL")] \
        if u["ticker"].str.startswith("TAIL").any() else u
    real = real.assign(x_gmsr=real["full_mktcap_usd"] / g)
    mem = real[real["member"] == 1].nsmallest(6, "x_gmsr")
    non = real[real["member"] == 0].nlargest(6, "x_gmsr")
    print(f"GMSR ${g/1e9:.1f}B | floor 0.5x | QIR add bar 1.8x")
    print("\nMembers nearest the 0.5x floor (refreshed caps):")
    print(mem[["ticker", "x_gmsr"]].round(2).to_string(index=False))
    print("\nNon-members nearest the 1.8x add bar:")
    print(non[["ticker", "x_gmsr"]].round(2).to_string(index=False))
    return g, mem, non


def _rows_2026():
    """Feb-26 + May-26 official lists (held locally, outside the
    2015-2025 archive) in the same row shape as ledgers()."""
    from agents.reconstitution import parse_msci_public_list
    from scripts.msci_key_stats import APAC
    out = []
    for season, rtype, f in (("Feb26", "QIR",
                              "data/msci_feb26_public_list.txt"),
                             ("May26", "SAIR",
                              "data/msci_may26_public_list.txt")):
        led = parse_msci_public_list(
            (ROOT / f).read_text(errors="ignore"))
        for c in APAC:
            d = led.get(c, {})
            out.append({"season": season, "rtype": rtype, "market": c,
                        "adds": d.get("adds", []),
                        "dels": d.get("deletes", [])})
    return out


def export():
    from scripts.msci_key_stats import ledgers
    rows = ledgers() + _rows_2026()
    seasons = []                      # chronological order, deduped
    for r in rows:
        if r["season"] not in seasons:
            seasons.append(r["season"])
    n_seasons = len(seasons)
    L = ["# MSCI APAC Index Changes 2015 - May 2026 — the official "
         "record, every review\n",
         f"*Session 9i. Source: {n_seasons} quarterly official "
         "lists (44 archive STPublicLists 2015-2025 + the held "
         "Feb/May-2026 lists). EVERY review is shown per market — "
         "no-change quarters included, because a quiet review is a "
         "data point too (the decade base rates in "
         "msci_decade_stats.json are built on exactly this). Names "
         "as published by MSCI. TW ex-post analysis: "
         "TAIWAN_MARKET_ANALYSIS.md §6.*\n"]
    for mkt in ("TAIWAN", "CHINA", "JAPAN", "HONG KONG", "KOREA",
                "INDIA", "MALAYSIA", "INDONESIA", "THAILAND",
                "PHILIPPINES", "SINGAPORE", "AUSTRALIA",
                "NEW ZEALAND"):
        sec = {r["season"]: r for r in rows if r["market"] == mkt}
        n_chg = sum(1 for r in sec.values()
                    if r["adds"] or r["dels"])
        L.append(f"## {mkt} — {n_chg} of {n_seasons} reviews with "
                 "changes\n")
        for season in seasons:
            r = sec.get(season)
            if r is None:
                continue
            tag = f"- **{season} {r['rtype']}**"
            if not (r["adds"] or r["dels"]):
                L.append(f"{tag} — no change")
                continue
            L.append(f"{tag} +{len(r['adds'])}/-{len(r['dels'])}: "
                     + ("ADD " + ", ".join(r["adds"]) + " " if
                        r["adds"] else "")
                     + ("DEL " + ", ".join(r["dels"]) if r["dels"]
                        else ""))
        L.append("")
    DOC.write_text("\n".join(L), encoding="utf-8")
    print(f"wrote {DOC} ({n_seasons} reviews per market)")


if __name__ == "__main__":
    {"export": export, "fetch": fetch, "classify": classify,
     "boundary": boundary}[sys.argv[1] if len(sys.argv) > 1
                           else "export"]()
