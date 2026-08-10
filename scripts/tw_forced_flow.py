#!/usr/bin/env python3
"""The institutional framing, applied to what this project holds.

    py scripts\\tw_forced_flow.py

WHY THIS FILE EXISTS. c-354, Bill brought a write-up of how a
multi-manager platform runs index rebalancing as a book — the
one where two Millennium teams reportedly made about USD 3.7bn
in a single month, more than half the firm's pre-fee profit that
month. The framing in it is worth adopting whether or not the
data to run it is available, because it names the trade
precisely:

    FORCED DEMAND IS NOT FUNDAMENTAL DEMAND. A tracker buys a
    new constituent because its benchmark now contains it, not
    because it has a view. That flow is price-insensitive and
    its arrival date is published in advance.

and it reduces to two equations:

    Expected Flow  =  P(index add) x  delta-weight  x  AUM
    Alpha          =  Expected Flow / Available Liquidity

────────────────────────────────────────────────────────────────
WHAT THIS PROJECT ALREADY HAS, TERM BY TERM

  P(index add)   scripts/aug26_scenarios.py — a registered
                 probability per candidate, from base rates on
                 124 historical Taiwan events with haircuts for
                 float error and member-count flex.

  delta-weight   free-float market cap over the index's own
                 free-float value. Estimated, not licensed —
                 see the limitation on the opening page.

  AUM            scripts/tw_mandate_size.py — USD 60bn, built
                 bottom-up from named ETFs plus a floor on
                 non-ETF indexed mandates inverted out of MSCI's
                 own reported fee revenue.

  liquidity      ADV per name, and better: the closing auction's
                 own capacity, because on an effective day 79%
                 of the volume prints in one five-minute call.
                 A day's ADV is the wrong denominator when the
                 forced flow does not arrive across the day.

So all four terms exist. This file assembles them and prints the
two numbers the framework asks for.

────────────────────────────────────────────────────────────────
THE ONE PLACE THE SITE AND THE FRAMEWORK DIFFER, AND IT IS NOT
AN OVERSIGHT

The Taiwan Case Study reports demand CONDITIONAL on the addition
happening — weight x AUM, with no probability multiplier. This
file reports the probability-weighted version as well. Both are
correct and they answer different questions:

    CONDITIONAL (the page)   "If MSCI adds it, how much do I have
                             to get done, and where?" That is the
                             execution question, and a dealer
                             sizing the order does not discount
                             it by 62% — on the day, either the
                             order is there in full or it is not
                             there at all.

    EXPECTED (this file)     "What is this worth to position for
                             BEFORE the announcement?" That is
                             the portfolio question, and it must
                             be discounted, because 38% of the
                             time the flow never arrives.

Keeping both is the point. Collapsing them would make the page
wrong for one audience or the other.

────────────────────────────────────────────────────────────────
WHAT CANNOT BE REPLICATED HERE, STATED PLAINLY

  1. THE AUM IS A FLOOR, AND MISSES A WHOLE POOL. The write-up
     lists four pools of forced buyers: index ETFs, index mutual
     funds, institutional passive mandates, and BENCHMARK-AWARE
     ACTIVE FUNDS. A manager benchmarked to an index who holds
     none of a new 1% constituent is running a -1% active bet by
     doing nothing, so some of that money buys too. This project
     counts the first three and cannot see the fourth at all.

  2. THE HISTORICAL TEST CONDITIONED ON THE WRONG VARIABLE.
     scripts/tw_addition_study.py ran an out-of-sample test on
     six candidate features — announcement gap, ADV, prior
     drift, pre-event volatility and so on — and found nothing
     that survives. NONE OF THEM IS THE FRAMEWORK'S RATIO.
     Expected flow over liquidity was never testable
     historically, because per-event index weights need a
     point-in-time float stack for every review back to 2015 and
     this project only reconstructed the recent ones.

     That is the single most valuable thing to build next, and
     it is a data problem rather than a method problem. The
     nearest things already tested are suggestive: `adv ->
     eff_day` and `n_same_review -> drift` both came back
     nominally significant, and both are crude proxies for the
     same ratio — one is the denominator, the other is how many
     names are competing for the same liquidity that day.

  3. NO CROSS-SECTION. A platform runs this across every index
     and every region, so it can diversify a per-event edge that
     is individually noisy. One market and 124 events cannot.

WHAT WOULD CHANGE WITH INSTITUTIONAL DATA, in order of value:

  a. Licensed index files — real free float and the published
     constituent list. Removes the estimation band from
     delta-weight and from P(add).
  b. eVestment or similar mandate data — turns the AUM floor
     into a range with a defensible middle, and reaches the
     institutional passive pool directly instead of inverting
     fee revenue.
  c. Holdings data on benchmark-aware active funds — the fourth
     pool, currently invisible.
  d. A borrow book — shows crowding while it forms rather than
     a week later, which is what tells you whether the forced
     flow is already being front-run.
"""
from __future__ import annotations

import datetime as dt
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCN = ROOT / "data" / "aug26_scenarios.json"
PB = ROOT / "data" / "tw_tracker_playbook.json"
MAND = ROOT / "data" / "tw_mandate_size.json"
STUDY = ROOT / "data" / "tw_addition_study.json"
OUT = ROOT / "data" / "tw_forced_flow.json"
DOC = ROOT / "docs" / "INSTITUTIONAL_FRAMEWORK.md"


def main():
    for p in (SCN, PB, MAND):
        if not p.exists():
            raise SystemExit(f"missing {p.name} — run its script first")
    scn = json.loads(SCN.read_text(encoding="utf-8"))
    pb = json.loads(PB.read_text(encoding="utf-8"))
    md = json.loads(MAND.read_text(encoding="utf-8"))
    study = (json.loads(STUDY.read_text(encoding="utf-8"))
             if STUDY.exists() else {})

    aum = md["taiwan"]["estimate_always_buys_usd_b"]
    A = scn["assumptions"]
    close_share = pb["capacity_model"]["ordinary_close_share"]
    eff_share = pb["capacity_model"]["effective_day_close_share"]

    rows = []
    for code, r in sorted(
            (kv for kv in pb["names"].items()
             if kv[1].get("capacity_rank")),
            key=lambda kv: kv[1]["capacity_rank"]):
        s = scn["names"][code]
        p = s["prob_of_addition"]
        w = r["index_weight_pct"]
        usd_m = w / 100 * aum * 1000
        shares = usd_m * 1e6 * A["usd_twd"] / s["last_close_twd"]
        adv_x = shares / r["adv_shares"]
        rows.append({
            "code": code, "name": r["name"],
            "p_add": p,
            "delta_weight_pct": w,
            "forced_flow_usd_m": round(usd_m, 1),
            "forced_flow_shares_m": round(shares / 1e6, 2),
            # THE FRAMEWORK'S TWO RATIOS.
            # `alpha_ratio_day` is flow over a whole day's
            # liquidity — the number the write-up uses.
            # `alpha_ratio_close` divides by the liquidity that
            # is ACTUALLY there when the flow arrives, which on
            # an effective day is one auction, not a session.
            # It is ~10x larger and it is the honest denominator
            # for a trade that prints in the close.
            "alpha_ratio_day": round(adv_x, 4),
            "alpha_ratio_close": round(
                shares / (close_share * r["adv_shares"]), 3),
            "expected_flow_usd_m": round(p * usd_m, 1),
            "expected_alpha_ratio_day": round(p * adv_x, 4),
        })

    oos = (study.get("out_of_sample") or {}).get("rules") or []
    o = {
        "_what": "P(add) x delta-weight x AUM, over the liquidity "
                 "that is actually there when the flow arrives",
        "generated": dt.datetime.now().isoformat(timespec="seconds"),
        "inputs": {
            "tracking_aum_usd_b": aum,
            "aum_basis": "scripts/tw_mandate_size.py — named ETFs "
                         "plus a floor on non-ETF indexed "
                         "mandates from MSCI's reported fee "
                         "revenue",
            "index_float_value_usd_b":
                A["index_float_value_usd_b"],
            "usd_twd": A["usd_twd"],
            "ordinary_close_share": close_share,
            "effective_day_close_share": eff_share,
        },
        "names": rows,
        "pools_of_forced_demand": [
            {"pool": "index ETFs", "counted": True,
             "where": "tw_tracking_aum.py, fund by fund"},
            {"pool": "index mutual funds", "counted": True,
             "where": "inside the non-ETF indexed floor"},
            {"pool": "institutional passive mandates",
             "counted": True,
             "where": "inverted from MSCI's non-ETF fee revenue"},
            {"pool": "benchmark-aware active funds",
             "counted": False,
             "where": "not visible without holdings data — a "
                      "manager holding none of a new 1% "
                      "constituent is running a -1% active bet "
                      "by standing still, so some of this money "
                      "buys too"},
        ],
        "out_of_sample_features_tested":
            sorted({r["feature"] for r in oos}),
        "gap": "None of the tested features is expected forced "
               "flow over liquidity. Per-event index weights "
               "need a point-in-time float stack for every "
               "review, which exists only for recent ones.",
    }
    OUT.write_text(json.dumps(o, indent=1), encoding="utf-8")

    d = ["# Index Rebalancing, the Institutional Framing", "",
         f"Generated {o['generated']} by "
         "`scripts/tw_forced_flow.py`. Every figure below comes "
         "from the JSON that script writes; nothing here is "
         "typed.", "",
         "## The framework", "",
         "Forced demand is not fundamental demand. A tracker "
         "buys a new constituent because its benchmark contains "
         "it, not because it has a view — the flow is "
         "price-insensitive and its date is published in "
         "advance. That reduces to:", "",
         "```",
         "Expected Flow = P(index add) x delta-weight x AUM",
         "Alpha         = Expected Flow / Available Liquidity",
         "```", "",
         "## Applied to the August 2026 candidates", "",
         f"AUM is **USD {aum:.0f}bn** \u2014 the sourced floor from "
         "`scripts/tw_mandate_size.py`, not the USD 180bn "
         "constant this project inherited. Weights are estimated "
         "free-float caps over the index's own free-float value, "
         f"USD {A['index_float_value_usd_b']:,.0f}bn.", "",
         "| Name | P(add) | Weight | Forced flow | x ADV | "
         "x one close | Expected x ADV |",
         "| --- | ---: | ---: | ---: | ---: | ---: | ---: |"]
    for r in rows:
        d.append(
            f"| {r['name'][:26]} ({r['code']}) | "
            f"{r['p_add']:.0%} | {r['delta_weight_pct']:.3f}% | "
            f"USD {r['forced_flow_usd_m']:,.0f}m | "
            f"{r['alpha_ratio_day']:.0%} | "
            f"{r['alpha_ratio_close']:.1f}x | "
            f"{r['expected_alpha_ratio_day']:.0%} |")
    d += ["",
          "The **x ADV** column is the framework's ratio against "
          "a whole day's liquidity. The **x one close** column "
          "divides by the liquidity that is actually there when "
          "the flow arrives — on an effective day "
          f"{eff_share:.0%} of volume prints in the closing "
          "auction, and an ordinary close in these names takes "
          f"only {close_share:.1%} of the day. That is the "
          "denominator a dealer should use, and it is about ten "
          "times smaller than a session.", "",
          "**Expected x ADV** applies the probability. The site "
          "itself reports the conditional figure instead, "
          "because a desk sizing the order on the effective day "
          "does not discount it — either the order is there in "
          "full or it is not there at all. The expected version "
          "is the number for positioning BEFORE the "
          "announcement.", "",
          "## The four pools of forced demand", "",
          "| Pool | Counted here? | Where |",
          "| --- | --- | --- |"]
    for p_ in o["pools_of_forced_demand"]:
        d.append(f"| {p_['pool']} | "
                 f"{'yes' if p_['counted'] else '**no**'} | "
                 f"{p_['where']} |")
    d += ["",
          "## What cannot be replicated without institutional "
          "data", "",
          "1. **The fourth pool is invisible.** Benchmark-aware "
          "active managers buy too, and holdings data is the "
          "only way to size that.",
          "2. **The historical test conditioned on the wrong "
          "variable.** The out-of-sample work tested "
          + ", ".join(f"`{f}`" for f in
                      o["out_of_sample_features_tested"])
          + " — none of which is flow over liquidity. Building "
            "that feature needs a point-in-time float stack for "
            "every review back to 2015.",
          "3. **No cross-section.** A platform diversifies a "
          "noisy per-event edge across every index and region. "
          "One market cannot.", "",
          "## What would change with access, in order of value",
          "", "1. Licensed index files — real free float and the "
          "published constituent list. Removes the estimation "
          "band from both the weight and P(add).",
          "2. Mandate data — turns the AUM floor into a range "
          "with a defensible middle.",
          "3. Holdings data on benchmark-aware active funds — "
          "the fourth pool.",
          "4. A borrow book — crowding while it forms, not a "
          "week later.", ""]
    DOC.write_text("\n".join(d), encoding="utf-8")

    print(f"tracking AUM      USD {aum:.0f}bn")
    for r in rows:
        print(f"{r['code']} {r['name'][:22]:24} "
              f"P={r['p_add']:.0%}  w={r['delta_weight_pct']:.3f}%  "
              f"flow=USD {r['forced_flow_usd_m']:6.0f}m  "
              f"{r['alpha_ratio_day']:6.1%} ADV  "
              f"{r['alpha_ratio_close']:5.1f}x close  "
              f"E={r['expected_alpha_ratio_day']:.1%} ADV")
    print(f"features tested out of sample: "
          f"{o['out_of_sample_features_tested']}")
    print(f"wrote {OUT.name}, {DOC.name}")


if __name__ == "__main__":
    main()
