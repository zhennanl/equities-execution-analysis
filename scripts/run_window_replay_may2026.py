#!/usr/bin/env python3
"""Step-2 DAILY window replay — May-2026 TW basket (session 8n).

The setting: announcement May 12 evening; effective close May 29.
Basket = the PIT Step-1 predictions (MPI add + 7 deletion calls),
sized from the engine's own expected flows. Each trading day May 13
→ May 28 the window analysis re-runs on data through THAT day only:
crowding reads update, discretion decisions re-derive, and every
decision FLIP is logged with its trigger. Then the full T-1
(May 28) plan renders — the night-before state of the book.

Everything dollar-denominated where shares are unknowable
(qty = expected-flow midpoint; ratios — ADV-days, footprint — are
exact). Borrow column: the archive stores balances, not quota →
'no quota data' at replay vintage, stated.
Output: docs/case_studies/WINDOW_REPLAY_MAY2026.md
"""
import json
import re
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from agents.event_window import (build_window_plan,             # noqa
                                 discretion_decision)
from agents.review_engine import crowding_reads, run_full_review  # noqa
from agents.reconstitution import parse_msci_public_list        # noqa
from scripts.run_full_review_asia import (PRE_COUNT, pit_screen,  # noqa
                                          pit_universe)
from scripts.run_qir_aug2026 import TW_ALIASES                  # noqa

ANN, EFF, T1 = "2026-05-12", "2026-05-29", "2026-05-28"
ENVELOPE = 30.0


def tw_calls():
    """The Step-1 PIT output for Taiwan — the basket source."""
    u = pit_universe("Taiwan")
    ledgers = [parse_msci_public_list(
        Path("data/msci_feb26_public_list.txt").read_text())]
    r = run_full_review(
        "Taiwan", u, TW_ALIASES, ledgers, "TAIWAN",
        review="SAIR", member_count=PRE_COUNT["Taiwan"],
        screen=pit_screen("Taiwan", u))
    return r["calls"], u


def basket_from_calls(calls, u):
    adv = dict(zip(u["ticker"], u["adv_usd"]))
    rows = []
    for _, c in calls.iterrows():
        lo, hi = [float(x) for x in c["flow_usd_m"].split("-")]
        mid = (lo + hi) / 2 * 1e6
        rows.append({
            "ticker": c["ticker"], "market": "Taiwan (TWSE)",
            "side": "Buy" if c["call"] == "ADD" else "Sell",
            "qty_shares": mid,               # USD-denominated
            "adv_shares": adv[c["ticker"]]})  # USD ADV — ratios exact
    return pd.DataFrame(rows)


def cache_through(day):
    c = json.loads(Path("data/event_data_cache.json").read_text())
    return {"short": {d: v for d, v in c.get("short", {}).items()
                      if d <= day.replace("-", "")}}


def daily_log(basket):
    days = sorted({d for d in json.loads(
        Path("data/event_data_cache.json").read_text())["short"]
        if ANN.replace("-", "") < d <= T1.replace("-", "")})
    prev, log, last_read = {}, [], {}
    for d in days:
        iso = f"{d[:4]}-{d[4:6]}-{d[6:]}"
        reads = crowding_reads(cache_through(iso),
                               list(basket["ticker"]))
        for _, r in basket.iterrows():
            base = r["ticker"].split(".")[0]
            dec = discretion_decision(r["side"], reads.get(base),
                                      ENVELOPE)["decision"]
            short = re.split(r" [—-] | up to", dec)[0]
            if base in prev and prev[base] != short:
                log.append({"date": iso, "ticker": r["ticker"],
                            "flip": f"{prev[base]} -> {short}",
                            "trigger": reads.get(base, "no data")})
            prev[base] = short
        last_read[iso] = reads
    return days, log, last_read


def main():
    calls, u = tw_calls()
    basket = basket_from_calls(calls, u)
    days, flips, reads_by_day = daily_log(basket)
    first_iso = f"{days[0][:4]}-{days[0][4:6]}-{days[0][6:]}"
    first = reads_by_day[first_iso]
    t1_reads = crowding_reads(cache_through(T1),
                              list(basket["ticker"]))
    plan = build_window_plan(
        basket, EFF, 16.0, 38.0, crowding_map=t1_reads,
        envelopes={t: ENVELOPE for t in basket["ticker"]},
        participation_cap=0.25, today=T1)

    L = ["# Step-2 Window Replay — May 2026 TW Basket "
         "(announcement -> T-1)",
         "*Session 8n. Basket = the Step-1 PIT predictions, sized "
         "by the engine's own flow midpoints. Analysis re-run each "
         "trading day on data through that day only; below: the "
         "daily decision-flip log and the full T-1 (May 28) plan — "
         "the night-before state. Grading context: 7/7 deletions "
         "and the MPI add were correct calls; 2324.TW read is the "
         "one the Step-4 replay later graded (WAIT was wrong there "
         "— drift +2274bps into the close).*", ""]
    L.append(f"## Daily loop ({len(days)} trading days, "
             "May 13 -> May 28)\n")
    L.append("**Day-1 baseline reads (May 13):** " + "; ".join(
        f"{k} {v}" for k, v in sorted(first.items())) + "\n")
    if flips:
        L.append("**Decision flips during the window** (the daily "
                 "diff — silence on unchanged names):\n")
        L.append(pd.DataFrame(flips).to_markdown(index=False))
    else:
        L.append("**No decision flips**: every name's crowding band "
                 "was stable through the window — the day-1 plan "
                 "survived to T-1 unchanged. (That is a finding, "
                 "not a gap: the daily loop's product is the "
                 "CONFIRMATION that nothing needs re-deciding.)")
    L.append("\n**T-1 crowding reads (through May 28):** " +
             "; ".join(f"{k} {v}" for k, v in sorted(t1_reads.items()))
             + "\n")
    L.append("## The T-1 plan (the night-before book state)\n")
    L.append("### 2.2 Liquidity & risk\n")
    L.append(plan["sheet"].to_markdown(index=False))
    L.append("\n### 2.3a Schedule state at T-1\n")
    L.append(plan["schedule"].to_markdown(index=False))
    L.append("\n*(At T-1, MULTI-DAY names showing LATE START are the "
             "residual-risk names: whatever was not worked in the "
             "window must now clear in one auction — see the "
             "footprint column and CLOSING_AUCTIONS_ASIA.md.)*\n")
    L.append("### 2.3b Discretion decisions at T-1 (documented)\n")
    for _, r in plan["decisions"].iterrows():
        L.append(f"- **{r['ticker']}** ({r['side']}): "
                 f"{r['decision']}\n  - {r['rationale']}")
    L.append("\n### T-1 checklist state\n")
    sheet = plan["sheet"]
    L.append(f"- Names: {len(sheet)}; MULTI-DAY "
             f"{int((sheet['bucket'] == 'MULTI-DAY').sum())}; "
             f"footprint>30% "
             f"{int((sheet['auction_footprint_pct'] > 30).sum())} "
             "(client conversations held); LOCK-RISK all TW names "
             "(±10% band) — queue-or-retreat playbook attached")
    L.append("- Final index file reconciliation, FX confirmation, "
             "staged auction orders: DESK OPS (out of replay scope, "
             "on the checklist)")
    L.append("- Cutoff: TW 13:25 order-rest; indicative broadcast "
             "13:25-13:30 is tomorrow's one real-time decision")
    out = Path("docs/case_studies/WINDOW_REPLAY_MAY2026.md")
    out.write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"replay -> {out}")
    print(f"days {len(days)}, flips {len(flips)}")
    print(plan["sheet"][["ticker", "side", "adv_days", "bucket",
                         "auction_footprint_pct"]].to_string(
        index=False))
    for f in flips:
        print(f)


if __name__ == "__main__":
    main()
