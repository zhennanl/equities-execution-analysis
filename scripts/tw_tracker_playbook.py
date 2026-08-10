#!/usr/bin/env python3
"""The passive tracker's three questions, answered per name.

    py scripts\\tw_tracker_playbook.py

WHY THIS EXISTS. The question bank's §0.1 splits clients by what
they need, and for the passive tracker the whole event reduces to
three moments and one currency — tracking error. The pages built
so far answer those questions in AGGREGATE (medians across 52
additions) and leave the reader to do the per-name arithmetic.
This does the arithmetic.

THE NUMBER THIS FILE ADDS, AND IT IS THE ONE A TRACKER ASKS
FIRST. Not "how many days of ADV do I have to buy" — the whole
order does not go through the session, it goes through the close.
The question is:

    HOW MANY TIMES THIS NAME'S OWN NORMAL CLOSING AUCTION
    IS MY ORDER?

An index mover puts about 79% of its effective-day volume through
Taiwan's 13:25-13:30 call (n=43, IB panel), against 9.5% on an
ordinary day. So a name's ordinary close absorbs roughly

    0.095 x ADV shares

and the tracker's requirement, in units of that, is

    demand_shares / (0.095 x ADV)

which is a plain multiple with no index jargon in it. Ten times
the normal close is a different conversation from one times.

THREE THINGS THIS IS NOT.

 1. NOT a price forecast. The addition study's out-of-sample test
    found nothing that predicts direction, so nothing here tries.
    Every number below is a QUANTITY or a monitoring threshold.
 2. NOT a claim that the close will hold that multiple. The
    9.5% is the ordinary-day share; on the effective day the same
    close swells — market-wide it runs about 5x its normal share.
    The multiple is the SIZE OF THE ASK, not a prediction of
    slippage, and the page says so.
 3. NOT per-name auction data. Taiwan's 5-second file is
    market-wide. The 9.5% is a median across 43 index-mover
    windows in the IB panel, applied to every name alike, and a
    quiet name's own close may be thinner than that.

THE MONITORING SIDE. For each of the three phases the question
bank names — before the announcement, announcement to effective,
and the effective date — this emits the metric to watch, the
historical reference level it should be compared against, and a
threshold with the reasoning attached. Thresholds are proposed,
not authoritative: they are placed at the historical quartiles so
"unusual" means "outside three quarters of the sample" rather
than a number somebody liked.
"""
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "tw_tracker_playbook.json"
DOC = ROOT / "docs" / "TW_TRACKER_PLAYBOOK.md"


def _j(name):
    p = ROOT / "data" / name
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def main():
    scn = _j("aug26_scenarios.json")
    study = _j("tw_addition_study.json")
    intr = _j("ib_5m_analysis.json")
    auc = _j("tw_auction_microstructure.json")
    if not (scn and study and intr):
        raise SystemExit("run aug26_scenarios.py, "
                         "tw_addition_study.py and "
                         "ib_5m_analysis.py first")

    TW = intr["markets"]["Taiwan"]
    ord_close = TW["close_share_ctrl"]["p50"]
    eff_close = TW["close_share_eff"]["p50"]
    A = study["anatomy"]["ADD"]
    FA = study["foreign_flow"]["ADD"]
    ACC = study["drift_accrual"]["ADD"]
    SCH = study["schedules"]["ADD"]

    names = {}
    for code, r in scn["names"].items():
        # c-325: a name whose addition verdict flips inside the
        # ±5% band on the cutoff is REPORTED but not carried, and
        # the capacity ladder is a sizing tool — sizing from a
        # name you are not standing behind is the wrong default.
        # The record is kept so the chart can show it on request.
        adv = r["adv_shares"]
        demand = r["demand_shares"]
        # the name's ordinary close, in shares
        close_shares = ord_close * adv
        names[code] = {
            "carried": bool(r.get("carried")),
            "name": r["name"],
            "adv_shares": adv,
            "demand_shares": demand,
            "demand_adv_days": r["demand_adv_days"],
            "ordinary_close_shares": close_shares,
            # THE HEADLINE
            "order_in_normal_closes": (demand / close_shares
                                       if close_shares else None),
            # and the same thing if the close swells as it
            # historically does on an effective date
            "order_in_effective_day_closes": (
                demand / (eff_close * adv) if adv else None),
            "expected_print_x_adv": r["expected_print_x_adv"],
            "pre_ann_excess_25d": r["pre_ann_excess_25d"],
            "pre_ann_percentile": r["pre_ann_percentile"],
            "prob_of_addition": r["prob_of_addition"],
            "index_weight_pct": r["index_weight_pct"],
        }
    # RANK THE CARRIED NAMES 1..N. c-325: the rank used to be
    # assigned over ALL names and the page then filtered one out,
    # which left the chart numbered 2, 3, 4 — a rank with a hole
    # in it reads as a missing row rather than as a name that was
    # deliberately excluded. Rank after filtering, not before.
    ranked = sorted([kv for kv in names.items() if kv[1]["carried"]],
                    key=lambda kv: -(kv[1]["order_in_normal_closes"]
                                     or 0))
    for i, (code, r) in enumerate(ranked, 1):
        r["capacity_rank"] = i
    for code, r in names.items():
        r.setdefault("capacity_rank", None)

    # ── the three phases ────────────────────────────────────────
    watch = [
        {"phase": "1 · Now, before the announcement "
                  "(to 12 Aug)",
         "question": "Is the market already positioned for this?",
         "metric": "25-session excess return over TAIEX, and "
                   "foreign net buying in days of ADV",
         "reference": f"a typical Taiwanese addition arrives "
                      f"having risen {A['pre_drift']['p50']:+.1%} "
                      f"(positive "
                      f"{A['pre_drift']['right_sign_share']:.0%} "
                      f"of the time) and having drawn "
                      f"{FA['pre']['p50']:+.2f} ADV days of "
                      f"foreign buying",
         "threshold": f"below {A['pre_drift']['p25']:+.1%} is the "
                      f"bottom quartile of the sample",
         "reading": "these four sit at the 2nd to 15th percentile "
                    "— the anticipation that normally precedes an "
                    "addition has not happened. That is the one "
                    "genuinely unusual feature of this review and "
                    "it cuts both ways: less pre-positioning to "
                    "unwind, and less confirmation that the "
                    "market agrees with the call.",
         "why_it_matters": "a name the market has already bought "
                           "is a name whose index demand is "
                           "partly met before the print"},
        {"phase": "2 · Announcement to effective (12–31 Aug)",
         "question": "Is the flow arriving, and on schedule?",
         "metric": "cumulative foreign net buying in ADV days, "
                   "against the drift accrual path",
         "reference": f"the median addition draws "
                      f"{FA['ann_to_eff']['p50']:+.2f} ADV days "
                      f"over this leg and "
                      f"{FA['cumulative_to_effective']['p50']:+.2f}"
                      f" cumulatively from 20 sessions before the "
                      f"announcement; half the drift has accrued "
                      f"by session {ACC['sessions_to_half']} of "
                      f"about thirteen",
         "threshold": f"foreign buying under "
                      f"{FA['ann_to_eff']['p25']:+.2f} ADV days by "
                      f"the halfway point is the bottom quartile",
         "reading": "the drift accrues close to linearly, so no "
                    "date is special and there is nothing to wait "
                    "for. What IS informative is the flow: if the "
                    "shares are not moving, the demand is still "
                    "ahead of you and the close carries it.",
         "why_it_matters": "the flow that has already arrived is "
                           "flow that will not compete with you "
                           "in the auction"},
        {"phase": "3 · The effective date (31 Aug)",
         "question": "Did the close absorb it, and at what price?",
         "metric": "effective-day volume as a multiple of ADV, "
                   "and the close against the day's own VWAP",
         "reference": f"the median addition prints "
                      f"{A['vol_mult_eff']['p50']:.1f}x ADV "
                      f"(p90 {A['vol_mult_eff']['p90']:.1f}x), and "
                      f"across markets the close lands within a "
                      f"third of a percent of the day's VWAP",
         "threshold": f"a print under {A['vol_mult_eff']['p25']:.1f}"
                      f"x ADV means the flow did not arrive; over "
                      f"{A['vol_mult_eff']['p90']:.1f}x means it "
                      f"arrived with company",
         "reading": "the close is the benchmark, so executing in "
                    "it is zero tracking error by definition. The "
                    "measured dislocation is small — which is an "
                    "argument FOR the close and against working "
                    "the session.",
         "why_it_matters": "for a tracker the effective close is "
                           "not an execution choice, it is the "
                           "benchmark; every alternative buys P&L "
                           "with tracking error"},
    ]

    out = {
        "_what": "the passive tracker's three questions, per name, "
                 "for the Aug-2026 MSCI Taiwan additions",
        "generated": dt.date.today().isoformat(),
        "conditional_on": "MSCI adding the name; the probability "
                          "of that is carried separately",
        "capacity_model": {
            "ordinary_close_share": ord_close,
            "effective_day_close_share": eff_close,
            "source": f"IB 5-minute panel, Taiwan, n={TW['n']} "
                      f"index-mover windows",
            "market_wide_auction_share_of_value":
                (auc or {}).get("auction_share", {})
                .get("by_value", {}).get("p50"),
            "limits": [
                "the closing-bar share is a MEDIAN across 43 "
                "index-mover windows and is applied to every name "
                "alike; a quiet name's own close may be thinner",
                "Taiwan's 5-second auction file is market-wide, so "
                "there is no per-name auction series to check this "
                "against",
                "the multiple is the SIZE OF THE ASK, not a "
                "slippage forecast — nothing here predicts price",
            ]},
        "schedule_reference": {
            "eff_close": SCH["eff_close"],
            "last_four": SCH["last_four"],
            "ann_plus_1": SCH["ann_plus_1"]},
        "watchlist": watch,
        "names": names,
    }
    OUT.write_text(json.dumps(out, indent=1), encoding="utf-8")
    write_doc(out)
    print(f"-> {OUT.relative_to(ROOT)}")
    print(f"-> {DOC.relative_to(ROOT)}")
    print(f"\nordinary close absorbs {ord_close:.1%} of a Taiwan "
          f"name's day; on an effective date {eff_close:.0%}\n")
    print(f"{'':4}{'name':<28}{'demand':>12}{'ADV days':>10}"
          f"{'x normal close':>16}")
    for code, r in ranked:
        print(f"{r['capacity_rank']:<4}{str(r['name'])[:26]:<28}"
              f"{r['demand_shares'] / 1e6:>10.1f}m"
              f"{r['demand_adv_days']:>10.2f}"
              f"{r['order_in_normal_closes']:>15.1f}x")
    return 0


def write_doc(o):
    C = o["capacity_model"]
    L = ["# The passive tracker's three questions\n",
         "Generated by `scripts/tw_tracker_playbook.py`.\n",
         "## The number a tracker asks first\n",
         "Not days of ADV — the order does not go through the "
         "session, it goes through the close. So:\n",
         "> **How many times this name's own normal closing "
         "auction is my order?**\n",
         f"An MSCI index mover puts about "
         f"{C['effective_day_close_share']:.0%} of its "
         f"effective-day volume through Taiwan's 13:25–13:30 call, "
         f"against {C['ordinary_close_share']:.1%} on an ordinary "
         f"day ({C['source']}). So an ordinary close absorbs "
         f"roughly {C['ordinary_close_share']:.3f} × ADV shares, "
         f"and the requirement in units of that is a plain "
         f"multiple.\n",
         "| | name | index demand | ADV days | × its normal close |",
         "|---|---|---|---|---|"]
    for code, r in sorted(
            [kv for kv in o["names"].items()
             if kv[1].get("capacity_rank")],
            key=lambda kv: kv[1]["capacity_rank"]):
        L.append(f"| {r['capacity_rank']} | {r['name']} ({code}) "
                 f"| {r['demand_shares'] / 1e6:,.1f}m shares "
                 f"| {r['demand_adv_days']:.2f} "
                 f"| **{r['order_in_normal_closes']:.1f}×** |")
    L.append("")
    L.append("Ten times the normal close is a different "
             "conversation from one times, and neither is visible "
             "in a days-of-ADV number.\n")
    L.append("## What this is not\n")
    for lim in C["limits"]:
        L.append(f"- {lim}")
    L.append("")
    L.append("## The three phases\n")
    for w in o["watchlist"]:
        L.append(f"### {w['phase']}\n")
        L.append(f"**{w['question']}**\n")
        L.append(f"- *Metric* — {w['metric']}")
        L.append(f"- *Historical reference* — {w['reference']}")
        L.append(f"- *Proposed threshold* — {w['threshold']}")
        L.append(f"- *Why it matters* — {w['why_it_matters']}")
        L.append(f"\n{w['reading']}\n")
    DOC.write_text("\n".join(L), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
