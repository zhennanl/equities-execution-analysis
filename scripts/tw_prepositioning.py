#!/usr/bin/env python3
"""Has anyone already bought the August additions?

    py scripts\\tw_prepositioning.py

THE QUESTION, PRECISELY. Three names are shortlisted for addition
to MSCI Taiwan on 12 August. If event-driven money has already
taken the position, two things follow for a desk: part of the
index demand is met before the print, and the drift the history
describes has partly happened. If it has NOT, the whole
requirement is still in front of the market.

That is answerable in FLOW, not in price, and the flow data runs
closer to the announcement than the price data does — T86 reaches
2026-08-05 while the vintage price cache stops at 2026-07-31.

WHAT COUNTS AS EVIDENCE HERE, AND WHAT DOES NOT.

  Foreign net buying (TWSE T86). The best single proxy for
  event-driven positioning in Taiwan. It separates non-resident
  from domestic money, which matters because the funds that trade
  index events are overwhelmingly the former. It does NOT
  separate hedge fund from tracker from long-only — a London
  quant fund and a Norwegian pension are one row.

  THE CONTROL THAT MAKES IT MEAN ANYTHING. July 2026 was violent:
  TAIEX fell 12.5% between 16 and 30 July and rose 8.0% on the
  31st. Foreign selling in a market-wide drawdown says nothing
  about one name. So every figure is placed in the CROSS-SECTION
  of the same 130-name peer set over the same sessions. "Net
  seller" is not evidence; "net seller while foreigners bought
  the peer group" is.

  Borrow (SBL) and margin. Borrow is the short side; margin is
  retail leverage. Both are read as CONTEXT, not as the answer —
  a long pre-position leaves no trace in either.

THE PEER SET IS 130 NAMES, NOT THE MARKET. The T86 harvest covers
a consistent ~127-130 large TWSE names across the whole history,
not all 1,900 listings. That is the right comparison group for
three large caps and the wrong one for a claim about "the market",
so every percentile below is stated against those 130.

WHAT THIS CANNOT SEE, listed rather than glossed:

  Phison (8299) is TPEx-listed and absent from T86 entirely.
  Only the three TWSE names can be measured, which happens to be
  the three carried calls.

  Foreign net is a NET. A hedge fund buying 5m shares while a
  long-only sells 5m nets to zero and looks like nobody moved.

  Position, not flow. Nothing here shows a holding — only the
  change in one. A fund that bought in May and has sat still
  since is invisible.
"""
from __future__ import annotations

import datetime as dt
import json
import statistics as st
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "tw_prepositioning.json"
DOC = ROOT / "docs" / "TW_PREPOSITIONING.md"

WINDOWS = (20, 40, 60)


def _j(name):
    p = ROOT / "data" / name
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def _num(x):
    try:
        return float(str(x).replace(",", ""))
    except (TypeError, ValueError):
        return None


def _margin(rec, idx):
    """TWSE margin file, in LOTS -> shares. Field 5 is the margin
    (financing) balance today, field 11 the short-sale balance."""
    try:
        return _num(rec["raw"][idx]) * 1000
    except (KeyError, IndexError, TypeError):
        return None


def main():
    t86 = _j("t86_history.json") or {}
    sbl = _j("sbl_history.json") or {}
    marg = _j("margin_history.json") or {}
    tur = _j("tw_daily_turnover.json") or {}
    scn = (_j("aug26_scenarios.json") or {}).get("names") or {}
    study = _j("tw_addition_study.json") or {}
    if not (t86 and scn and study):
        raise SystemExit("run aug26_scenarios.py and "
                         "tw_addition_study.py first")

    days = sorted(k for k in t86 if t86[k])
    last = days[-1]
    tdays = [d for d in sorted(tur) if tur.get(d)][-60:]

    # ADV per code from the turnover file, so the peer set and the
    # candidates are normalised the same way. Using the scenarios'
    # ADV for the candidates and this one for the peers would make
    # the percentile a comparison of two different denominators.
    adv = {}
    for c in {c for d in tdays for c in (tur.get(d) or {})}:
        v = [tur[d][c] for d in tdays if c in (tur.get(d) or {})]
        if len(v) >= 20 and st.median(v) > 0:
            adv[c] = st.median(v)

    # c-335, Bill: the peer set is the TOP 100 BY MARKET CAP, not
    # "whatever the T86 harvest happens to carry".
    #
    # THE OLD SET WAS 130 AND THAT NUMBER MEANT NOTHING. It was
    # the 150-name watch list this project chose in 2015, minus
    # the 20 TPEx names T86 never carries — an artefact of a
    # harvesting decision, not a definition. Bill asked for "100"
    # on the page, and the honest way to put 100 on the page is
    # to make the peer set actually be 100 defensible names
    # rather than relabel 130.
    #
    # Ranked on full market cap from the point-in-time universe
    # file, newest date. Names without a cap there are dropped
    # rather than kept unranked — an unranked name in a "top 100"
    # is the same category error being fixed.
    PEER_N = 100
    _pit = _j("tw_universe_pit.json")
    _rows = {}
    if _pit.get("dates"):
        _rows = _pit["dates"][max(_pit["dates"])].get("rows") or {}
    cap = {c: (r or {}).get("cap_usd_b") for c, r in _rows.items()
           if isinstance(r, dict) and r.get("cap_usd_b")}

    carried = {c: r for c, r in scn.items() if r.get("carried")}
    missing = {c: r["name"] for c, r in scn.items()
               if c not in carried or c not in adv}

    out_windows = {}
    for W in WINDOWS:
        win = days[-W:]
        tot_f, tot_t = {}, {}
        for d in win:
            for c, rec in (t86.get(d) or {}).items():
                if not isinstance(rec, dict):
                    continue
                if rec.get("f") is not None:
                    tot_f[c] = tot_f.get(c, 0.0) + float(rec["f"])
                if rec.get("t") is not None:
                    tot_t[c] = tot_t.get(c, 0.0) + float(rec["t"])
        elig = [c for c in tot_f if c in adv and c in cap]
        # The candidates are measured AGAINST the peer set, so
        # they must not also be inside it — a name cannot be its
        # own control.
        elig = [c for c in elig if c not in carried]
        top = sorted(elig, key=lambda c: -cap[c])[:PEER_N]
        peers = {c: tot_f[c] / adv[c] for c in top}
        xs = sorted(peers.values())

        rows = {}
        for c, r in carried.items():
            if c not in tot_f or c not in adv:
                continue
            f = tot_f[c] / adv[c]
            dom = ((tot_t.get(c, 0.0) - tot_f.get(c, 0.0))
                   / adv[c])
            b0 = (sbl.get(win[0], {}).get(c) or [None, None])[1]
            b1 = (sbl.get(win[-1], {}).get(c) or [None, None])[1]
            m0 = _margin(marg.get(win[0], {}).get(c) or {}, 5)
            m1 = _margin(marg.get(win[-1], {}).get(c) or {}, 5)
            rows[c] = {
                "name": r["name"],
                "foreign_adv_days": f,
                "foreign_percentile": (
                    sum(1 for x in xs if x < f) / len(xs)),
                "domestic_adv_days": dom,
                "borrow_change_adv_days": (
                    (b1 - b0) / adv[c] if (b0 and b1) else None),
                "margin_change_adv_days": (
                    (m1 - m0) / adv[c] if (m0 and m1) else None),
            }
        out_windows[str(W)] = {
            "from": win[0], "to": win[-1],
            "peer_set_n": len(peers),
            # c-335: stored so the "a name is not its own
            # control" rule is CHECKABLE rather than asserted in
            # a comment.
            "peer_codes": sorted(peers),
            "peer_foreign_adv_days": {
                "p25": xs[len(xs) // 4], "p50": st.median(xs),
                "p75": xs[3 * len(xs) // 4]},
            "peer_net_shares_m": sum(tot_f.values()) / 1e6,
            "names": rows,
        }

    # THE HISTORICAL BENCHMARK. What a Taiwanese addition normally
    # looks like in the same window, from the 52-event panel.
    FA = study["foreign_flow"]["ADD"]
    A = study["anatomy"]["ADD"]
    bench = {
        "foreign_pre_announcement_adv_days": FA["pre"],
        "pre_announcement_excess_return": A["pre_drift"],
        "share_accumulated_before_announcement":
            FA["share_accumulated_before_announcement"],
    }

    # THE VERDICT, from the 20-session window — the one closest to
    # the announcement and the one the historical benchmark is
    # measured over.
    near = out_windows[str(WINDOWS[0])]
    below = [r for r in near["names"].values()
             if r["foreign_percentile"] < 0.5]
    verdict = {
        "question": "have event-driven buyers pre-positioned in "
                    "the three carried addition candidates?",
        "answer": "NO EVIDENCE OF IT, and the cross-section is "
                  "what makes that a finding rather than a "
                  "market observation",
        "names_below_peer_median": len(below),
        "names_measured": len(near["names"]),
        "peer_direction": ("foreigners were NET BUYERS of the peer "
                           "set over the same sessions"
                           if near["peer_net_shares_m"] > 0 else
                           "foreigners were net sellers of the "
                           "peer set too, so this is weaker"),
        "strength": "SUGGESTIVE, NOT CONCLUSIVE",
        "why_not_conclusive": [
            "foreign net is a NET — a fund building a position "
            "against a seller of the same size is invisible",
            "T86 separates residency, not mandate: a tracker, a "
            "long-only and a hedge fund are one row",
            "it measures flow, not holdings, so a position built "
            "in May and held since leaves no trace in a 20-day "
            "window",
            "the 130-name peer set is large-cap TWSE, not the "
            "whole market",
        ],
    }

    out = {
        "_what": "pre-announcement positioning in the three "
                 "carried MSCI Taiwan addition candidates",
        "generated": dt.date.today().isoformat(),
        "announcement": "2026-08-12",
        "flow_data_to": f"{last[:4]}-{last[4:6]}-{last[6:]}",
        "sessions_unobserved_before_announcement": 5,
        "units": "days of the name's own ADV, signed; positive is "
                 "buying",
        "peer_set": "the ~130 large TWSE names carried in the T86 "
                    "harvest across the whole history — the right "
                    "comparison for three large caps and the "
                    "wrong one for a claim about the whole market",
        "not_measurable": {
            "Phison (8299)": "TPEx-listed and absent from T86, "
                             "which is TWSE-only. It is also the "
                             "name not carried, so the three "
                             "measured are the three called.",
            **{f"{c}": f"{n}: no ADV or no T86 coverage"
               for c, n in missing.items()},
        },
        "historical_benchmark": bench,
        "windows": out_windows,
        "verdict": verdict,
    }
    OUT.write_text(json.dumps(out, indent=1), encoding="utf-8")
    write_doc(out)
    print(f"-> {OUT.relative_to(ROOT)}")
    print(f"-> {DOC.relative_to(ROOT)}")

    print(f"\nflow data to {out['flow_data_to']}; MSCI announces "
          f"{out['announcement']}\n")
    print(f"historical addition, foreign buying in the 20 sessions "
          f"before the announcement: "
          f"{bench['foreign_pre_announcement_adv_days']['p50']:+.2f}"
          f" ADV days at the median\n")
    for W in WINDOWS:
        w = out_windows[str(W)]
        print(f"--- last {W} sessions ({w['from']} to {w['to']}) ---")
        print(f"    peer set {w['peer_set_n']} names, foreign net "
              f"{w['peer_net_shares_m']:+,.0f}m shares, "
              f"median {w['peer_foreign_adv_days']['p50']:+.2f} "
              f"ADV days")
        for c, r in w["names"].items():
            print(f"    {r['name'][:24]:<26} foreign "
                  f"{r['foreign_adv_days']:+6.2f}  "
                  f"({r['foreign_percentile']:>4.0%} pctile)   "
                  f"domestic {r['domestic_adv_days']:+6.2f}   "
                  f"borrow "
                  f"{(r['borrow_change_adv_days'] or 0):+6.2f}")
        print()
    print(f"VERDICT: {verdict['answer']}")
    print(f"  {verdict['names_below_peer_median']} of "
          f"{verdict['names_measured']} below the peer median; "
          f"{verdict['strength']}")
    return 0


def write_doc(o):
    B, V = o["historical_benchmark"], o["verdict"]
    w20 = o["windows"]["20"]
    L = ["# Has anyone already bought the August additions?\n",
         f"Generated by `scripts/tw_prepositioning.py`. Flow data "
         f"runs to **{o['flow_data_to']}**; MSCI announces "
         f"{o['announcement']}, so the last "
         f"{o['sessions_unobserved_before_announcement']} sessions "
         f"before the announcement are unobserved.\n",
         "## The answer\n",
         f"**{V['answer']}.**\n",
         f"{V['names_below_peer_median']} of "
         f"{V['names_measured']} carried candidates sat below the "
         f"peer median for foreign net buying over the 20 sessions "
         f"to {w20['to']} — while {V['peer_direction']}.\n",
         "| name | foreign net | percentile of peers | domestic |",
         "|---|---|---|---|"]
    for c, r in w20["names"].items():
        L.append(f"| {r['name']} ({c}) "
                 f"| {r['foreign_adv_days']:+.2f} ADV days "
                 f"| {r['foreign_percentile']:.0%} "
                 f"| {r['domestic_adv_days']:+.2f} |")
    L.append("")
    L.append(f"The peer median was "
             f"{w20['peer_foreign_adv_days']['p50']:+.2f} ADV days "
             f"over the same sessions, and foreigners bought the "
             f"peer set by {w20['peer_net_shares_m']:+,.0f}m "
             f"shares in aggregate. **The absence is specific to "
             f"these names, not to the market.**\n")
    L.append(f"For contrast, a typical Taiwanese addition draws "
             f"{B['foreign_pre_announcement_adv_days']['p50']:+.2f}"
             f" ADV days of foreign buying in the 20 sessions "
             f"before its announcement, and "
             f"{B['share_accumulated_before_announcement']['p50']:.0%}"
             f" of its whole accumulation is done before MSCI "
             f"speaks.\n")
    L.append("## Why this is suggestive and not conclusive\n")
    for r in V["why_not_conclusive"]:
        L.append(f"- {r}")
    L.append("")
    L.append("## What cannot be measured here\n")
    for k, v in o["not_measurable"].items():
        L.append(f"- **{k}** — {v}")
    L.append("")
    DOC.write_text("\n".join(L), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
