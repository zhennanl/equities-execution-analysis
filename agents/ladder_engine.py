"""Ladder shadow engine — the book's true mechanism (session 9i c-35).

Replaces the boundary-shorthand with the validated full-member
ladder: confirmed constituents (3-fund pipeline) + current caps ->
GMSR walk -> delete pool (buffer band, GIMI §3.1.5.1) + add
candidates (dual hurdle §3.1.2.3 + foreign room §3.1.2.6).

SHADOW MODE for Aug-2026: runs ALONGSIDE the locked engine, output
published pre-announcement next to the legacy call so Aug-12 grades
BOTH. Validated pedigree: this ladder graded May-26 deletions as
the exact bottom-7 (zero false calls) and Nov-25 7/7 —
data/delete_pool_validation.json.

Usage: python -m agents.ladder_engine   (writes
data/ladder_aug26_tw.json)
"""
import json
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FX = 32.5
BUFFER_EDGE = 1.15          # pool cutoff: generous buffer-band edge
API = "https://api.finmindtrade.com/api/v4/data"


def _current_caps(codes):
    """Current cap + foreign room per code: vintage cache first
    (fresh through 2026-08), FinMind top-up for the rest."""
    import pandas as pd
    import requests
    cache = json.loads((ROOT / "data" / "tw_vintage_cache.json")
                       .read_text())
    out, missing = {}, []
    for c in codes:
        if f"px|{c}" in cache and f"sh|{c}" in cache:
            px = pd.DataFrame(cache[f"px|{c}"])
            sh = pd.DataFrame(cache[f"sh|{c}"])
            room = None
            last = sh.iloc[-1]
            if "ForeignInvestmentSharesRatio" in sh.columns:
                lim = last.get("ForeignInvestmentUpperLimitRatio",
                               100.0) or 100.0
                held = last["ForeignInvestmentSharesRatio"] or 0.0
                room = max(lim - held, 0.0) / 100.0
            out[c] = {"cap_usd": float(px["close"].iloc[-1])
                      * float(last["NumberOfSharesIssued"]) / FX,
                      "asof": str(px["date"].iloc[-1]),
                      "foreign_room_frac": room,
                      "src": "vintage cache"}
        else:
            missing.append(c)
    live = ROOT / "data" / "ladder_livecap_cache.json"
    lc = json.loads(live.read_text()) if live.exists() else {}
    for c in list(missing):
        if c in lc:
            out[c] = lc[c]
            missing.remove(c)
    for c in missing:
        try:
            r = requests.get(API, params={
                "dataset": "TaiwanStockShareholding", "data_id": c,
                "start_date": "2026-07-20", "end_date": "2026-08-05"},
                timeout=30).json()["data"]
            p = requests.get(API, params={
                "dataset": "TaiwanStockPrice", "data_id": c,
                "start_date": "2026-07-20", "end_date": "2026-08-05"},
                timeout=30).json()["data"]
            if not r or not p:
                continue
            lim = r[-1].get("ForeignInvestmentUpperLimitRatio",
                            100.0) or 100.0
            held = r[-1].get("ForeignInvestmentSharesRatio") or 0.0
            out[c] = {"cap_usd": p[-1]["close"]
                      * r[-1]["NumberOfSharesIssued"] / FX,
                      "asof": p[-1]["date"],
                      "foreign_room_frac": max(lim - held, 0) / 100.0,
                      "src": "FinMind live"}
            lc[c] = out[c]
            tmp = live.with_suffix(".tmp")
            tmp.write_text(json.dumps(lc))
            tmp.replace(live)
            time.sleep(0.6)
        except Exception:                      # noqa: BLE001
            continue
    return out


def build_ladder(market="Taiwan"):
    src = json.loads((ROOT / "data" / "tw_membership_sources.json")
                     .read_text())
    ewt = set(json.loads((ROOT / "data" / "ewt_members.json")
                         .read_text())["codes"])
    confirmed = set(src["eem_tw_codes"]) & ewt \
        & set(src["yuanta_006203_codes"])
    likely = (set(src["eem_tw_codes"]) | ewt
              | set(src["yuanta_006203_codes"])) - confirmed
    members = confirmed | likely               # inclusive by design
    caps = _current_caps(sorted(members))
    rows = [{"code": c,
             "tier": "CONFIRMED" if c in confirmed else "LIKELY",
             **caps[c]} for c in members if c in caps]
    rows.sort(key=lambda r: r["cap_usd"])
    # GMSR walk on this ladder via the engine (count = len(members))
    import pandas as pd
    from agents.review_engine import screen_market
    uni = pd.DataFrame({
        "ticker": [r["code"] for r in rows],
        "full_mktcap_usd": [r["cap_usd"] for r in rows],
        "free_float_frac": 0.7, "adv_usd": 1e7, "atvr": 1.0,
        "member": 1})
    s = screen_market(uni, review="QIR",
                      member_count=len(rows), tail_hi=10e9,
                      tail_n=400)
    gmsr = s["gmsr"]
    pool = [dict(r, x_gmsr=round(r["cap_usd"] / gmsr, 2))
            for r in rows if r["cap_usd"] < BUFFER_EDGE * gmsr]
    return {"market": market, "generated": time.strftime("%Y-%m-%d"),
            "n_members_priced": len(rows),
            "coverage": f"{len(rows)}/{len(members)} members priced",
            "gmsr_usd_b": round(gmsr / 1e9, 2),
            "pool_cutoff": f"< {BUFFER_EDGE}x GMSR "
                           f"(${BUFFER_EDGE * gmsr / 1e9:.2f}B)",
            "delete_pool": pool,
            "note": "SHADOW engine (book-mechanism ladder, "
                    "validated May-26 exact bottom-7 + Nov-25 7/7); "
                    "legacy engine remains the locked Aug-26 call. "
                    "GMSR CAVEAT (stated, not hidden): this walk "
                    "runs on members + modeled tail with default "
                    "0.7 floats and NO real non-member caps, so its "
                    "GMSR sits ABOVE the boundary frame's ($6.5B vs "
                    "$4.8B) — errs INCLUSIVE, widening the pool "
                    "(the safe direction for a pool; wrong "
                    "direction for calls, which is why this stays "
                    "shadow). Reconciliation queued: walk on the "
                    "union universe with real floats.",
            "ladder_bottom": [dict(r, x_gmsr=round(
                r["cap_usd"] / gmsr, 2)) for r in rows[:15]]}


if __name__ == "__main__":
    out = build_ladder()
    p = ROOT / "data" / "ladder_aug26_tw.json"
    p.write_text(json.dumps(out, indent=1))
    print(f"members priced: {out['n_members_priced']} | GMSR "
          f"${out['gmsr_usd_b']}B | pool: {len(out['delete_pool'])}")
    for r in out["ladder_bottom"]:
        mark = " <— POOL" if r in out["delete_pool"] else ""
        print(f"  {r['code']:6s} ${r['cap_usd']/1e9:6.2f}B "
              f"x={r['x_gmsr']:5.2f} {r['tier']:9s} "
              f"[{r['src']}]{mark}")
    print("wrote", p)
