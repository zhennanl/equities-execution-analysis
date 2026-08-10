#!/usr/bin/env python3
"""Step-2 window-plan DEMO on live data (session 8g).

Basket = boundary names from the Aug-2026 Asia pack appendix that have
LIVE crowding reads (TW/HK/CN-H/JP). Order QUANTITIES are hypothetical
client sizes chosen to span the three buckets — every other column is
live: crowding from the multi-market archive, T-multiples from the
measured event library, SBL borrow utilization from today's TWT93U,
bands from the market table. Output:
docs/case_studies/EVENT_WINDOW_PLAN_DEMO_AUG2026.md
"""
import datetime as dt
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from agents.event_data import fetch_twse_short_balance          # noqa
from agents.event_window import (build_window_plan,             # noqa
                                 render_window_plan,
                                 sbl_utilization)
from agents.pitch_pack import expected_t_multiples              # noqa
from agents.review_engine import crowding_reads                 # noqa
from scripts.run_full_review_asia import market_short_caches    # noqa

# side: boundary members = deletion-watch (Sell), boundary non-members
# = add-watch (Buy). ADV in shares, qty spans the buckets.
BASKET = pd.DataFrame([
    # ticker            market            side   qty          adv
    ["1101.TW", "Taiwan (TWSE)",  "Sell",  2_500_000, 18_000_000],
    ["2207.TW", "Taiwan (TWSE)",  "Sell",  3_600_000,  1_800_000],
    ["1326.TW", "Taiwan (TWSE)",  "Sell", 12_000_000,  9_000_000],
    ["2002.TW", "Taiwan (TWSE)",  "Sell", 55_000_000,  9_500_000],
    ["0027.HK", "Hong Kong (HKEX)", "Sell", 9_000_000, 21_000_000],
    ["9995.HK", "Hong Kong (HKEX)", "Buy",  3_000_000,  1_400_000],
    ["4004.T",  "Japan (TSE)",    "Buy",   5_200_000,  2_600_000],
], columns=["ticker", "market", "side", "qty_shares", "adv_shares"])

ENVELOPES = {"1101.TW": 30.0, "2207.TW": 30.0, "1326.TW": 30.0,
             "2002.TW": 30.0, "9995.HK": 25.0, "4004.T": 25.0}
             # 0027.HK deliberately WITHOUT an envelope -> MOC ONLY


def main():
    caches = market_short_caches()
    crowding = {}
    for mkt, cache in caches.items():
        crowding.update(crowding_reads(
            cache, list(BASKET["ticker"])))
    event_cache = json.loads(
        Path("data/event_flow_study.json").read_text(encoding="utf-8"))
    tm = expected_t_multiples(event_cache, "MSCI", "Sell")
    med, mx = tm.get("median", 16.0), tm.get("max", 38.0)
    # live borrow read: latest TWT93U day
    sbl = {}
    d = dt.date.today()
    for _ in range(5):
        d -= dt.timedelta(days=1)
        if d.weekday() >= 5:
            continue
        df = fetch_twse_short_balance(d.strftime("%Y%m%d"))
        if not df.empty:
            sbl = sbl_utilization(df)
            break
    plan = build_window_plan(
        BASKET, "2026-09-01", med, mx, crowding_map=crowding,
        envelopes=ENVELOPES, sbl_util=sbl, today="2026-07-28")
    notes = (
        "DEMO basket: quantities hypothetical (span the buckets); "
        "names/sides = live boundary reads from AUG2026_QIR_ASIA_PACK "
        "appendix. T-multiple = measured MSCI-Sell library (median "
        f"{med:.0f}x, max {mx:.0f}x) applied to all lines for the "
        "demo — per-side/per-provider in production. Borrow "
        "utilization live TWT93U (Taiwan only — the one public quota "
        "file); HK/JP lines honestly show 'no quota data'. Auction "
        "footprint uses the measured ~30% close share of T-day "
        "volume. 0027.HK has NO envelope on purpose — the plan shows "
        "discretion is not exercised where it was not granted.")
    md = render_window_plan(
        plan, "Step-2 Window Plan — DEMO basket, Aug-2026 QIR "
        "(eff Sep 1)", "2026-07-28", notes=notes)
    out = Path("docs/case_studies/EVENT_WINDOW_PLAN_DEMO_AUG2026.md")
    out.write_text(md, encoding="utf-8")
    print(f"plan -> {out}")
    print(plan["sheet"][["ticker", "adv_days", "bucket",
                         "auction_footprint_pct", "borrow"]])
    print(plan["decisions"][["ticker", "decision"]])


if __name__ == "__main__":
    main()
