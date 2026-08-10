"""Step-1 universe-assembly workbench — Taiwan (session 9i c-29).

User request: show CLEAR NUMBERS for engine Step 1 on the website —
per name: local cap, FX, price-refresh ratio, USD cap, free-float
estimate, float-adjusted cap, ADV/ATVR — and how those numbers feed
the add/delete decision (full cap vs hurdles; float-adjusted cap in
the coverage walk). Saves data/universe_workbench_tw.json for the UI.

Usage: python scripts/universe_workbench.py
"""
import datetime as dt
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main():
    from agents.review_engine import screen_market
    from scripts.pit_may2026_asia import ACTUAL, FX, UNIVERSES
    from scripts.run_full_review_asia import (cap_refresh,
                                              post_may_universe)
    cache = json.loads(
        (ROOT / "data" / "pit_may26_asia_cache.json").read_text(encoding="utf-8"))
    ratios = cap_refresh()
    fx = FX["Taiwan"]
    u = post_may_universe("Taiwan")
    # c-33c: 77 = post-May count (83 - 7 + 1), three-fund unanimous
    s = screen_market(u, review="QIR", member_count=77,
                      tail_hi=10e9, tail_n=500)
    gmsr, add_thr = s["gmsr"], s["add_thr"]
    floor = 0.5 * gmsr
    act = ACTUAL["Taiwan"]
    rows = []
    for t, mem_pre in UNIVERSES["Taiwan"]:
        c = cache.get(t, {})
        if "cap_pit" not in c:
            continue
        mem = 0 if t in act["dels"] else (
            1 if t in act["adds"] else mem_pre)
        ratio = ratios.get(t, 1.0)
        cap_usd = c["cap_pit"] / fx * ratio
        ff = min(c.get("ff", 0.7), 1.0)
        adv_usd = (c.get("adv_loc") or 0) / fx
        x = cap_usd / (floor if mem else add_thr)
        if mem:
            bucket = ("DELETE candidate" if x < 1 else
                      "WATCH (within 15% of the floor)" if x < 1.15
                      else "member — safe")
        else:
            bucket = ("ADD candidate" if x >= 1 else
                      "WATCH (within 15% of the add bar)"
                      if x >= 0.85 else "non-member — not close")
        rows.append({
            "ticker": t, "member": bool(mem),
            "cap_twd_b_apr30": round(c["cap_pit"] / 1e9, 1),
            "price_ratio_since_apr": round(ratio, 3),
            "cap_usd_b_now": round(cap_usd / 1e9, 2),
            "free_float_est": round(ff, 3),
            "float_adj_cap_usd_b": round(cap_usd * ff / 1e9, 2),
            "adv_usd_m": round(adv_usd / 1e6, 1),
            "vs_threshold": round(x, 2),
            "decision_bucket": bucket})
    out = {
        "asof": dt.date.today().isoformat(),
        "market": "Taiwan", "fx_twd_usd": fx,
        "review": "Aug-2026 QIR",
        "thresholds": {"gmsr_usd_b": round(gmsr / 1e9, 2),
                       "add_bar_usd_b": round(add_thr / 1e9, 2),
                       "floor_usd_b": round(floor / 1e9, 2)},
        "formulas": {
            "cap_usd": "cap_TWD(Apr-30, price x shares via "
                       "yfinance) / 32.5 FX x current-price ratio",
            "free_float": "estimated from holder filings "
                          "(yfinance), capped at 1.0 — MSCI's own "
                          "floats are licensed; stated miss source",
            "coverage_walk": "uses FLOAT-ADJUSTED cap (ff x cap) "
                             "to find 85% coverage -> GMSR",
            "hurdles": "use FULL cap: add >= 1.8x GMSR (QIR) / "
                       "1.15x (SAIR); deletion floor 0.5x GMSR"},
        "rows": sorted(rows, key=lambda r: -r["cap_usd_b_now"])}
    p = ROOT / "data" / "universe_workbench_tw.json"
    p.write_text(json.dumps(out, indent=1), encoding="utf-8")
    print("wrote", p)
    for r in out["rows"]:
        print(f"  {r['ticker']:9s} mem={int(r['member'])} "
              f"cap=${r['cap_usd_b_now']:7.2f}B ff="
              f"{r['free_float_est']:.2f} x={r['vs_threshold']:6.2f} "
              f"{r['decision_bucket']}")
    print("thresholds:", out["thresholds"])


if __name__ == "__main__":
    main()
