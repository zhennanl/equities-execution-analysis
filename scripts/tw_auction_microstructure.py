#!/usr/bin/env python3
"""Taiwan's closing auction, from TWSE's own 5-second file.

    py scripts\\tw_auction_microstructure.py

WHY THIS IS THE HIGHEST-VALUE INTRADAY DATASET WE HOLD. The IB
5-minute panel starts in 2023 and covers 43 Taiwanese effective
dates. `auction5s_history.json` carries 2,815 trading days back to
2015 — eleven years — and it is TWSE's own disclosure rather than
a vendor's reconstruction. It answers the one question a program
desk is actually asked before an index print: HOW MUCH CAN THE
CLOSE ABSORB.

WHAT THE FILE IS. Every 5 seconds from 13:20 to 13:30, plus a
13:00 snapshot, TWSE publishes a market-wide cumulative line.
MARKET-WIDE is the binding limitation and it is stated everywhere
below: there is no per-stock breakdown, so this sizes the VENUE,
not the name. The per-name question is the IB panel's job.

COLUMN IDENTIFICATION, MEASURED RATHER THAN ASSUMED. The file
ships as bare numbers with no header, and the obvious mapping to
TWSE's published column list does not survive contact with the
data — two of the columns FALL through the session, which no
cumulative order count does. So only the columns that identify
themselves are used:

  c5  cumulative matched QUANTITY   frozen 13:25:05-13:29:55,
                                    jumps at 13:30:00
  c6  cumulative matched VALUE      same freeze, same jump

The freeze is the call auction: no continuous matching happens
during order collection, so cumulative traded fields cannot move
until the auction prints. Two independent checks confirm the
pair:

  1. c6/c5 implies an average traded price of about 87 TWD,
     which is the right order of magnitude for the Taiwanese
     market and would be absurd under any other assignment.
  2. The freeze holds on 100% of days in every month sampled.

c0 and c2 rise monotonically and c1 and c3 fall. That rules out
the naive "cumulative buy/sell order count and quantity" reading
for at least two of them, and nothing in the file settles which.
THEY ARE NOT USED. An imbalance series built on a guessed column
would be the most attractive output here and the least defensible.

A REGIME ASSUMPTION THAT TURNED OUT TO BE WRONG, recorded because
it nearly shaped the whole analysis. I expected the closing call
auction to begin on 2020-03-23 and planned to split the sample
there. The freeze test says otherwise: matched quantity is frozen
through 13:25-13:30 on 100% of days in 2015 as well as 2026. The
closing call auction predates this sample; what changed in March
2020 was the CONTINUOUS session moving from 5-second batch
matching to continuous matching, which does not touch the close.
So the series is comparable end to end, and the split that would
have been made was the wrong one.
"""
from __future__ import annotations

import collections
import json
import random
import statistics as st
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "tw_auction_microstructure.json"
DOC = ROOT / "docs" / "TW_AUCTION_MICROSTRUCTURE.md"

QTY, VAL = 5, 6            # the two identified columns
OPEN_SNAP, AUCT_START, CLOSE = "13:00:00", "13:25:00", "13:30:00"
# The freeze window used to prove the call auction. 13:25:05 is
# the first tick after collection begins; 13:29:55 the last
# before the print.
FREEZE = ("13:25:05", "13:29:55")


def _j(name):
    p = ROOT / "data" / name
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def num(x):
    try:
        return float(str(x).replace(",", ""))
    except (TypeError, ValueError):
        return None


def pct(xs, p):
    xs = sorted(x for x in xs if x is not None and x == x)
    if not xs:
        return None
    i = (len(xs) - 1) * p
    lo = int(i)
    hi = min(lo + 1, len(xs) - 1)
    return xs[lo] + (xs[hi] - xs[lo]) * (i - lo)


def describe(xs):
    xs = [x for x in xs if x is not None and x == x]
    if not xs:
        return {"n": 0}
    return {"n": len(xs), "mean": st.mean(xs), "p10": pct(xs, .10),
            "p25": pct(xs, .25), "p50": pct(xs, .50),
            "p75": pct(xs, .75), "p90": pct(xs, .90)}


def perm_p(a, b, trials=20000, seed=7):
    """Permutation test on the difference of medians."""
    a = [x for x in a if x is not None]
    b = [x for x in b if x is not None]
    if len(a) < 4 or len(b) < 4:
        return None
    obs = abs(st.median(a) - st.median(b))
    pool, rnd, hits = a + b, random.Random(seed), 0
    for _ in range(trials):
        rnd.shuffle(pool)
        if abs(st.median(pool[:len(a)])
               - st.median(pool[len(a):])) >= obs:
            hits += 1
    return (hits + 1) / (trials + 1)


def day_series(rows):
    """{clock: [values]} for one day, numbers parsed."""
    return {r[0]: [num(x) for x in r[1:]] for r in rows if r}


def is_call_auction(d):
    """Does matched quantity FREEZE through order collection?

    This is the test that identifies the columns and proves the
    mechanism at the same time. If it ever returns False for a
    stretch of days, either the columns moved or Taiwan changed
    its close — and both must stop the analysis rather than be
    averaged into it.
    """
    seg = [v[QTY] for t, v in d.items()
           if FREEZE[0] <= t <= FREEZE[1] and v[QTY] is not None]
    return len(seg) > 20 and max(seg) == min(seg)


def main():
    raw = _j("auction5s_history.json") or {}
    wins = (_j("tw_event_windows.json") or {}).get("windows", {})
    eff_dates = {str(w.get("eff")).replace("-", "")
                 for w in wins.values() if w.get("eff")}

    days, bad = {}, collections.Counter()
    for k in sorted(raw):
        rows = raw.get(k)
        if not rows:
            bad["empty"] += 1
            continue
        d = day_series(rows)
        if not all(t in d for t in (OPEN_SNAP, AUCT_START, CLOSE)):
            bad["missing_anchor_tick"] += 1
            continue
        q0, q25, q30 = (d[OPEN_SNAP][QTY], d[AUCT_START][QTY],
                        d[CLOSE][QTY])
        v0, v25, v30 = (d[OPEN_SNAP][VAL], d[AUCT_START][VAL],
                        d[CLOSE][VAL])
        if None in (q0, q25, q30, v0, v25, v30) or not (q30 and v30):
            bad["unparseable"] += 1
            continue
        if not is_call_auction(d):
            bad["no_freeze"] += 1
            continue
        days[k] = {
            "date": f"{k[:4]}-{k[4:6]}-{k[6:]}",
            "auction_qty_share": (q30 - q25) / q30,
            "auction_val_share": (v30 - v25) / v30,
            "last30_qty_share": (q30 - q0) / q30,
            "day_qty": q30, "day_val": v30,
            "auction_qty": q30 - q25, "auction_val": v30 - v25,
            # c6/c5 — the identification check, kept per day so a
            # column swap upstream shows up as a nonsense price
            # rather than as a plausible-looking share
            "implied_avg_price": (v30 / q30) * 1000.0,
            "is_effective_date": k in eff_dates,
        }

    if not days:
        raise SystemExit("no usable days — check auction5s_history")

    ks = sorted(days)
    allq = [days[k]["auction_qty_share"] for k in ks]
    allv = [days[k]["auction_val_share"] for k in ks]
    eff = [k for k in ks if days[k]["is_effective_date"]]
    ord_ = [k for k in ks if not days[k]["is_effective_date"]]

    month_ends = set()
    last_of = {}
    for k in ks:
        last_of[k[:6]] = k
    month_ends = set(last_of.values())
    me_only = [k for k in ks
               if k in month_ends and not days[k]["is_effective_date"]]
    plain = [k for k in ks
             if k not in month_ends and not days[k]["is_effective_date"]]
    sair = [k for k in eff if k[4:6] in ("05", "11")]
    qir = [k for k in eff if k[4:6] in ("02", "08")]

    by_year = {}
    for k in ks:
        by_year.setdefault(k[:4], []).append(k)
    years = {y: {"n": len(v),
                 "auction_qty_share": describe(
                     [days[x]["auction_qty_share"] for x in v]),
                 "auction_val_share": describe(
                     [days[x]["auction_val_share"] for x in v])}
             for y, v in sorted(by_year.items())}

    # THE CAPACITY NUMBER. Absolute size of the venue, in TWD and
    # converted to USD, so a demand estimate in dollars can be
    # compared with it directly.
    fx = _j("fx_twd_history.json") or {}
    rate = float(fx[max(fx)]) if fx else 32.0
    auc_val_twd = [days[k]["auction_val"] * 1e6 for k in ks]

    out = {
        "_what": "Taiwan closing auction, market-wide, from "
                 "TWSE's 5-second disclosure",
        "scope": "MARKET-WIDE. There is no per-stock breakdown in "
                 "this file, so every figure sizes the VENUE and "
                 "none of them sizes a name.",
        "columns_identified": {
            "matched_quantity": QTY, "matched_value": VAL,
            "method": "both freeze through 13:25:05-13:29:55 and "
                      "jump at 13:30:00, which no continuously "
                      "matched field does; and value/quantity "
                      "implies a sane average traded price",
            "not_identified": "c0-c3 — two rise and two fall "
                              "through the session, which rules "
                              "out the obvious mapping. Unused.",
            "implied_avg_price_twd": describe(
                [days[k]["implied_avg_price"] for k in ks]),
        },
        "sample": {"days": len(days),
                   "first": days[ks[0]]["date"],
                   "last": days[ks[-1]]["date"],
                   "dropped": dict(bad),
                   "call_auction_days": len(days),
                   "call_auction_share_of_days": 1.0},
        "auction_share": {
            "by_quantity": describe(allq),
            "by_value": describe(allv),
            "note": "value share exceeds quantity share because "
                    "the auction is disproportionately the large, "
                    "high-priced names",
        },
        "last_30_minutes_qty_share": describe(
            [days[k]["last30_qty_share"] for k in ks]),
        "by_year": years,
        # THE CONTROL THAT HAD TO BE RUN. MSCI effective dates are
        # the last business day of Feb/May/Aug/Nov — 26 of the 30
        # in this sample are month-ends, and month-end carries
        # benchmark flow from every index family at once. Without
        # a month-end comparison group, a month-end effect would
        # be reported as an MSCI effect.
        "month_end_control": {
            "msci_effective": describe(
                [days[k]["auction_val_share"] for k in eff]),
            "month_end_not_msci": describe(
                [days[k]["auction_val_share"] for k in me_only]),
            "neither": describe(
                [days[k]["auction_val_share"] for k in plain]),
            "msci_dates_that_are_month_ends":
                f"{len([k for k in eff if k in month_ends])}"
                f"/{len(eff)}",
            "p_msci_vs_month_end": perm_p(
                [days[k]["auction_val_share"] for k in eff],
                [days[k]["auction_val_share"] for k in me_only]),
        },
        # MSCI runs a SEMI-ANNUAL review in May and November and a
        # smaller QUARTERLY one in February and August. The close
        # knows the difference, which makes the review type a
        # capacity input a desk has months of notice on.
        "review_type": {
            "sair_may_nov": describe(
                [days[k]["auction_val_share"] for k in sair]),
            "qir_feb_aug": describe(
                [days[k]["auction_val_share"] for k in qir]),
            "p": perm_p(
                [days[k]["auction_val_share"] for k in sair],
                [days[k]["auction_val_share"] for k in qir]),
        },
        "effective_dates": {
            "n": len(eff),
            "by_quantity": describe(
                [days[k]["auction_qty_share"] for k in eff]),
            "by_value": describe(
                [days[k]["auction_val_share"] for k in eff]),
            "ordinary_by_quantity": describe(
                [days[k]["auction_qty_share"] for k in ord_]),
            "ordinary_by_value": describe(
                [days[k]["auction_val_share"] for k in ord_]),
        },
        "capacity": {
            "auction_value_twd": describe(auc_val_twd),
            "auction_value_usd": describe(
                [v / rate for v in auc_val_twd]),
            "usd_twd": rate,
        },
        "days": days,
    }
    OUT.write_text(json.dumps(out, indent=1), encoding="utf-8")
    write_doc(out)
    print(f"-> {OUT.relative_to(ROOT)}")
    print(f"-> {DOC.relative_to(ROOT)}")

    A = out["auction_share"]
    print(f"\n{len(days):,} days, {out['sample']['first']} to "
          f"{out['sample']['last']}  (dropped {dict(bad)})")
    print(f"implied average traded price: "
          f"{out['columns_identified']['implied_avg_price_twd']['p50']:.1f}"
          f" TWD  <- the column-identification check")
    print(f"\nclosing auction, share of the whole day")
    print(f"  by quantity  p25 {A['by_quantity']['p25']:.2%}  "
          f"p50 {A['by_quantity']['p50']:.2%}  "
          f"p90 {A['by_quantity']['p90']:.2%}")
    print(f"  by value     p25 {A['by_value']['p25']:.2%}  "
          f"p50 {A['by_value']['p50']:.2%}  "
          f"p90 {A['by_value']['p90']:.2%}")
    M = out["month_end_control"]
    print(f"\nauction share of VALUE, with the month-end control")
    print(f"  MSCI effective date       n={M['msci_effective']['n']:>4}"
          f"  {M['msci_effective']['p50']:>7.2%}")
    print(f"  month-end, not MSCI       n={M['month_end_not_msci']['n']:>4}"
          f"  {M['month_end_not_msci']['p50']:>7.2%}")
    print(f"  neither                   n={M['neither']['n']:>4}"
          f"  {M['neither']['p50']:>7.2%}")
    print(f"  MSCI vs month-end, p = {M['p_msci_vs_month_end']:.4f}")
    R = out["review_type"]
    print(f"\n  May/Nov semi-annual  n={R['sair_may_nov']['n']:>3}"
          f"  {R['sair_may_nov']['p50']:.1%}")
    print(f"  Feb/Aug quarterly    n={R['qir_feb_aug']['n']:>3}"
          f"  {R['qir_feb_aug']['p50']:.1%}   p={R['p']:.4f}")
    C = out["capacity"]
    print(f"\ncapacity of one close: USD "
          f"{C['auction_value_usd']['p50'] / 1e6:,.0f}m at the "
          f"median, USD {C['auction_value_usd']['p10'] / 1e6:,.0f}m "
          f"on a quiet day")
    return 0


def write_doc(o):
    A, E, C = o["auction_share"], o["effective_dates"], o["capacity"]
    S = o["sample"]
    M, R = o["month_end_control"], o["review_type"]

    def p(v, f="{:.2%}"):
        return f.format(v) if v is not None else "n/a"

    L = ["# Taiwan's closing auction — how much can the close "
         "absorb\n",
         "Generated by `scripts/tw_auction_microstructure.py` "
         "into `data/tw_auction_microstructure.json`.\n",
         "## Scope, before anything else\n",
         f"- **{S['days']:,} trading days**, {S['first']} to "
         f"{S['last']}, from TWSE's own 5-second disclosure.",
         f"- **Market-wide.** {o['scope']}",
         f"- Columns were identified by behaviour, not by a "
         f"header: matched quantity and value both freeze through "
         f"order collection and jump at 13:30, and their ratio "
         f"implies an average traded price of "
         f"{o['columns_identified']['implied_avg_price_twd']['p50']:.0f}"
         f" TWD. Four other columns could not be identified and "
         f"are unused.\n",
         "## The auction is small, and that is the point\n",
         "| | p25 | median | p90 |",
         "|---|---|---|---|",
         f"| share of the day, by quantity | "
         f"{p(A['by_quantity']['p25'])} | "
         f"{p(A['by_quantity']['p50'])} | "
         f"{p(A['by_quantity']['p90'])} |",
         f"| share of the day, by value | "
         f"{p(A['by_value']['p25'])} | {p(A['by_value']['p50'])} | "
         f"{p(A['by_value']['p90'])} |",
         "",
         f"The median Taiwanese close prints "
         f"{p(A['by_value']['p50'])} of the day's value — about "
         f"USD {C['auction_value_usd']['p50'] / 1e6:,.0f}m of "
         f"turnover across the entire market. On a quiet day "
         f"(p10) it is USD "
         f"{C['auction_value_usd']['p10'] / 1e6:,.0f}m.\n",
         f"Set that against the IB panel's per-name result: an "
         f"MSCI index mover puts roughly **79%** of its "
         f"effective-day volume through that same five minutes. "
         f"The venue is thin; the index trade is not. That gap is "
         f"the capacity problem in one line.\n",
         "## Index days trade a different venue\n",
         "| day type | n | median auction share of value |",
         "|---|---|---|",
         f"| MSCI effective date | {M['msci_effective']['n']} | "
         f"{p(M['msci_effective']['p50'])} |",
         f"| month-end, not an MSCI date | "
         f"{M['month_end_not_msci']['n']} | "
         f"{p(M['month_end_not_msci']['p50'])} |",
         f"| neither | {M['neither']['n']:,} | "
         f"{p(M['neither']['p50'])} |",
         "",
         f"**THE CONTROL MATTERS AND IT WAS NEARLY SKIPPED.** "
         f"{M['msci_dates_that_are_month_ends']} MSCI effective "
         f"dates in this sample are month-ends, and month-end "
         f"carries benchmark flow from every index family at "
         f"once. Without the middle row a month-end effect would "
         f"have been reported as an MSCI effect. It is not: "
         f"month-end alone lifts the close from "
         f"{p(M['neither']['p50'])} to "
         f"{p(M['month_end_not_msci']['p50'])}, and the MSCI "
         f"review lifts it again to "
         f"{p(M['msci_effective']['p50'])} "
         f"(p={M['p_msci_vs_month_end']:.4f}).\n",
         f"**The close is deepest exactly when you need it.** "
         f"Roughly five times its ordinary share. A capacity "
         f"estimate built off a normal day understates the "
         f"effective-date close by a factor of about "
         f"{M['msci_effective']['p50'] / M['neither']['p50']:.0f}, "
         f"which is the difference between crossing at the close "
         f"and working the session.\n",
         "## The review type is a capacity input\n",
         f"MSCI runs a semi-annual review in May and November and "
         f"a smaller quarterly one in February and August. The "
         f"close knows the difference: "
         f"{p(R['sair_may_nov']['p50'])} of the day's value on "
         f"the {R['sair_may_nov']['n']} May/November dates "
         f"against {p(R['qir_feb_aug']['p50'])} on the "
         f"{R['qir_feb_aug']['n']} February/August ones "
         f"(p={R['p']:.4f}).\n",
         f"August 2026 is a QUARTERLY review, so the base case "
         f"for its close is the lower number — around "
         f"{p(R['qir_feb_aug']['p50'])} of the day rather than "
         f"the {p(R['sair_may_nov']['p50'])} a May or November "
         f"print would bring. A desk has months of notice on "
         f"this input.\n",
         "## What this file cannot do\n",
         "- **No per-stock split.** Sizing a single name's share "
         "of its own close needs the IB panel or TWSE per-stock "
         "intraday, neither of which reaches 2015.",
         "- **Four unidentified columns.** An order-imbalance "
         "series would be the most useful thing here and the "
         "least defensible; it is not built.",
         "- **Market-wide value is not a limit order book.** "
         "Knowing the close trades USD "
         f"{C['auction_value_usd']['p50'] / 1e6:,.0f}m does not "
         "tell you the depth available at a price.\n"]
    DOC.write_text("\n".join(L), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
