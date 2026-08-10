#!/usr/bin/env python3
"""Round two: does the capacity ladder survive its own inputs?

    py scripts\\tw_positioning_round2.py

WHAT ROUND ONE SAID. tw_tracker_playbook.py ranked the three
carried names by `demand_shares / (0.095 x ADV)` — how many
ordinary closing auctions it would take to absorb the index
order. Winbond ranked worst, then Nan Ya PCB, then Nanya Tech.
tw_prepositioning.py separately found no evidence that event
money had already bought them.

WHAT THIS SCRIPT DOES TO THAT. It attacks the ladder with the two
inputs it was silent about, and reports whether the conclusion
holds or breaks:

  1. THE ADV HORIZON. The ladder struck ADV on one horizon and
     never said which. tw_watch_tape.py now measures four (20 /
     60 / 120 / 250 sessions) and the spread is 1.1x to 1.7x
     depending on the name — which means the horizon is a free
     parameter large enough to reorder a three-name ranking. This
     recomputes the ladder on every horizon and asks whether the
     ORDER changes. If it does not, the ranking is robust to a
     choice nobody defended. If it does, the ranking was an
     artefact of that choice and has to be reported as a range.

  2. THE TRACKING-AUM ASSUMPTION. `demand_shares` is
     proportional to a hand-set USD 180bn (traced in c-327 to a
     constant in event_window_analyze.py, not to any external
     source). It cancels in the RATIO between names and does not
     cancel in the LEVEL. So the level is reported as a band and
     the ranking as the durable claim.

WHY JULY MATTERS SO MUCH HERE. TAIEX fell 12.5% between 16 and 30
July and the four names ran 30d realised vol of 75-114%. A 20-day
ADV struck through that window is a crisis-volume number; a
250-day ADV is not. This is exactly the condition under which the
horizon choice stops being cosmetic.

INPUTS, all offline:
  data/tw_watch_tape.json      ADV on four horizons, trend, blocks
  data/aug26_scenarios.json    demand_shares, index weight
  data/tw_tracker_playbook.json  the round-one ranking
  data/tdcc_dispersion.json    OPTIONAL — if the TDCC harvest has
                               been run, the holder-side test is
                               added; if not, the section says so
                               rather than being silently absent.
"""
from __future__ import annotations

import datetime as dt
import json
import pathlib
import statistics as stats

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "tw_positioning_round2.json"
DOC = ROOT / "docs" / "TW_POSITIONING_ROUND2.md"

CLOSE_SHARE = 0.095      # measured; see docs/TW_CASE_STUDY.md
WINDOWS = ("20", "60", "120", "250")


def _j(name, default=None):
    p = ROOT / "data" / name
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() \
        else (default if default is not None else {})


def main():
    tape = _j("tw_watch_tape.json")
    scen = _j("aug26_scenarios.json")
    play = _j("tw_tracker_playbook.json")
    tdcc = _j("tdcc_dispersion.json")

    names = {r["code"]: r for r in tape.get("names", [])
             if not r.get("_no_data")}
    sc = scen.get("names") or {}
    carried = [c for c in names if sc.get(c, {}).get("carried")]

    o = {"_what": "round-two stress of the capacity ladder",
         "generated": dt.datetime.now().isoformat(timespec="seconds"),
         "close_share": CLOSE_SHARE,
         "coverage": tape.get("coverage", {}),
         "carried": sorted(carried),
         "ladder_by_horizon": {}, "rank_by_horizon": {},
         "per_name": {}, "tdcc": {}}

    # ── 1 · the ladder on every horizon ────────────────────────
    for w in WINDOWS:
        row = {}
        for c in carried:
            adv = names[c]["adv"][w]["shares"]
            dem = sc[c].get("demand_shares")
            if adv and dem:
                row[c] = dem / (CLOSE_SHARE * adv)
        o["ladder_by_horizon"][w] = row
        o["rank_by_horizon"][w] = [k for k, _ in sorted(
            row.items(), key=lambda kv: -kv[1])]

    orders = {tuple(v) for v in o["rank_by_horizon"].values() if v}
    o["rank_is_stable"] = len(orders) == 1
    o["distinct_orders"] = [list(x) for x in orders]

    # ── 2 · per-name summary ───────────────────────────────────
    for c in sorted(names):
        r, s = names[c], sc.get(c, {})
        vals = [o["ladder_by_horizon"][w].get(c) for w in WINDOWS]
        vals = [v for v in vals if v]
        o["per_name"][c] = {
            "name": r["name"], "board": r["board"],
            "carried": bool(s.get("carried")),
            "last_close": r["last_close"], "last_date": r["last_date"],
            "ret_20d": r.get("ret_20d"), "ret_30d": r.get("ret_30d"),
            "vol_30d": r.get("vol_30d"),
            "drawdown_from_30d_high": r.get("drawdown_from_30d_high"),
            "adv_spread": r.get("adv_spread"),
            "closes_lo": min(vals) if vals else None,
            "closes_hi": max(vals) if vals else None,
            "closes_round1": (play.get("names", {})
                              .get(c, {}).get("order_in_normal_closes")),
            "peer_pctile": r.get("peer_pctile"),
            "turnover_ratio": r.get("turnover_ratio"),
            "foreign_net_5d_of_adv": r.get("foreign_net_5d_of_adv"),
            "foreign_net_20d_of_adv": r.get("foreign_net_20d_of_adv"),
            "foreign_net_60d_of_adv": r.get("foreign_net_60d_of_adv"),
            "blocks_30d_n": len(r.get("blocks_30d") or []),
            "blocks_30d_of_adv": r.get("blocks_30d_of_adv"),
            "sbl_build_20d_of_adv": r.get("sbl_build_20d_of_adv"),
        }

    # ── 3 · the holder-side test, if the harvest has been run ──
    real = {c: {d: v for d, v in wk.items() if v}
            for c, wk in tdcc.items()
            if not c.startswith("_") and isinstance(wk, dict)}
    real = {c: v for c, v in real.items() if v}
    if not real:
        o["tdcc"] = {"_status": "NOT HARVESTED — run "
                                "scripts/tdcc_dispersion_harvest.py"}
    else:
        for c, wk in real.items():
            ds = sorted(wk)
            b15 = [wk[d]["b15_pct"] for d in ds
                   if wk[d].get("b15_pct") is not None]
            if len(b15) < 12:
                o["tdcc"][c] = {"weeks": len(b15),
                                "_status": "too few weeks"}
                continue
            # c-333 THE CALIBRATION THAT MAKES THIS READABLE.
            # Bracket-15 share moves 1-2pp a week on its own in
            # these names, so a raw "+2.7pp over eight weeks" is
            # not evidence of anything until it is placed against
            # that noise. The comparison is the standard
            # deviation of WEEKLY CHANGES over the whole year,
            # scaled to the eight-week horizon by sqrt(8) — the
            # random-walk scaling, which is the null this is
            # being tested against.
            diffs = [b15[i] - b15[i - 1] for i in range(1, len(b15))]
            sd_w = stats.pstdev(diffs) if len(diffs) > 2 else None
            chg8 = b15[-1] - b15[-9]
            base = stats.median(b15[:-8])
            z8 = (chg8 / (sd_w * (8 ** .5))) if sd_w else None
            o["tdcc"][c] = {
                "weeks": len(b15), "first": ds[0], "last": ds[-1],
                "b15_first": b15[0], "b15_last": b15[-1],
                "b15_min": min(b15), "b15_max": max(b15),
                "b15_8w_change": chg8,
                "b15_vs_year_median": b15[-1] - base,
                "weekly_sd_pp": sd_w,
                "z_8w": z8,
                "verdict": ("no signal" if z8 is None or abs(z8) < 1
                            else "suggestive" if abs(z8) < 2
                            else "notable"),
                "holders_first": wk[ds[0]].get("total_holders"),
                "holders_last": wk[ds[-1]].get("total_holders"),
                "shares_first": wk[ds[0]].get("total_shares"),
                "shares_last": wk[ds[-1]].get("total_shares")}
            # A share count that moved is a corporate action, and
            # it changes what a percentage MEANS — the denominator
            # is not the same security week to week.
            sf = o["tdcc"][c]["shares_first"]
            sl = o["tdcc"][c]["shares_last"]
            if sf and sl:
                o["tdcc"][c]["shares_change"] = sl / sf - 1

    OUT.write_text(json.dumps(o, indent=1), encoding="utf-8")
    write_doc(o)
    print(f"wrote {OUT.name} and {DOC.name}")
    print("rank stable across ADV horizons:", o["rank_is_stable"])
    for w in WINDOWS:
        print(f"  {w:>4}d ADV -> " + ", ".join(
            f"{c} {o['ladder_by_horizon'][w][c]:.1f}"
            for c in o["rank_by_horizon"][w]))
    return o


def write_doc(o):
    P = o["per_name"]
    L = ["# Round two — stressing the capacity ladder", "",
         f"Generated {o['generated']}. Prices to "
         f"{o['coverage'].get('vintage_last')}"
         + ("" if o["coverage"].get("refreshed")
            else " (**live refresh not run**)") + ".", "",
         "## 1 · Does the ranking survive the ADV horizon?", "",
         "The ladder divides index demand by "
         f"`{o['close_share']:.3f} x ADV` — the share of a day's "
         "volume that an ordinary Taiwanese closing auction takes. "
         "ADV was struck on one horizon and the horizon was never "
         "named. Here it is struck on four.", "",
         # c-328: first-word labels turned "Nan Ya PCB" into
         # "Nan". Two words, which separates Nanya from Nan Ya.
         "| ADV horizon | " + " | ".join(
             f"{' '.join(P[c]['name'].split()[:2])} ({c})"
             for c in o["carried"]) + " | order |",
         "|---|" + "---|" * (len(o["carried"]) + 1)]
    for w in ("20", "60", "120", "250"):
        row = o["ladder_by_horizon"][w]
        L.append(f"| {w}d | " + " | ".join(
            f"{row.get(c, float('nan')):.1f}" for c in o["carried"])
            + " | " + " > ".join(o["rank_by_horizon"][w]) + " |")
    L += ["", "*Cells are closing auctions of ordinary liquidity "
              "the order would consume.*", ""]
    if o["rank_is_stable"]:
        L += ["**The ranking holds on every horizon.** The order is "
              f"`{' > '.join(o['rank_by_horizon']['20'])}` whether "
              "ADV is struck over 20 sessions or 250. That matters "
              "because the LEVEL is not robust — it moves by up to "
              f"{max((P[c]['adv_spread'] or 1) for c in o['carried']):.1f}x "
              "with the horizon — so the defensible claim is the "
              "ORDER, and the level belongs in a range.", ""]
    else:
        L += ["**The ranking does NOT hold.** Different horizons "
              "give different orders: "
              + "; ".join(" > ".join(x) for x in o["distinct_orders"])
              + ". Round one's single ranking was an artefact of an "
              "undeclared horizon choice and should be withdrawn in "
              "favour of the range below.", ""]
    L += ["## 2 · The names, as they stand", ""]
    for c in sorted(P):
        r = P[c]
        L += [f"### {c} {r['name']}"
              + ("" if r["carried"] else "  *(not carried)*"), "",
              f"- last close **{r['last_close']}** ({r['last_date']}), "
              f"20d {(r['ret_20d'] or 0):+.1%}, 30d "
              f"{(r['ret_30d'] or 0):+.1%}, "
              f"{(r['drawdown_from_30d_high'] or 0):+.1%} off the "
              f"30d high, 30d vol {(r['vol_30d'] or 0):.0%}"]
        if r["closes_lo"]:
            L.append(f"- order size **{r['closes_lo']:.1f} to "
                     f"{r['closes_hi']:.1f} ordinary closes** "
                     f"depending on ADV horizon"
                     + (f" (round one said {r['closes_round1']:.1f})"
                        if r["closes_round1"] else ""))
        if r["peer_pctile"] is not None:
            L.append(f"- trading at {r['turnover_ratio']:.2f}x its own "
                     f"median volume — {r['peer_pctile']:.0%} of the "
                     f"market that session")
        fn = [(n, r[f"foreign_net_{n}d_of_adv"]) for n in (5, 20, 60)
              if r.get(f"foreign_net_{n}d_of_adv") is not None]
        if fn:
            L.append("- foreign net, in days of 20d ADV: " + ", ".join(
                f"{n}d {v:+.2f}" for n, v in fn))
        if r["blocks_30d_n"]:
            L.append(f"- {r['blocks_30d_n']} block prints in 30 "
                     f"sessions ({(r['blocks_30d_of_adv'] or 0):.2f} "
                     f"days of ADV)")
        if r["sbl_build_20d_of_adv"] is not None:
            L.append(f"- borrow 20d change "
                     f"{r['sbl_build_20d_of_adv']:+.2f} days of ADV")
        L.append("")
    L += ["## 3 · The holder-side test (TDCC)", ""]
    if o["tdcc"].get("_status"):
        L += ["**" + o["tdcc"]["_status"] + ".** Every positioning "
              "read above is a FLOW read, and flow cannot see a fund "
              "that bought in May and has sat still since. TDCC's "
              "weekly custody census is the only free instrument "
              "that can. Until it is harvested this section is a "
              "known blind spot, not an absence of evidence.", ""]
    else:
        L += ["Bracket 15 is holdings above 1,000,000 shares — "
              "where non-resident institutions, government funds "
              "and the ETF trusts sit. A passive pre-position "
              "shows up as a RISING bracket-15 share.", "",
              "**Read the change against the noise, not against "
              "zero.** These shares move 1-2pp week to week on "
              "their own, so `z` places the eight-week change "
              "against that weekly volatility scaled by sqrt(8). "
              "Below 1 is indistinguishable from drift.", "",
              "| code | weeks | b15 now | range | 8-week change | "
              "weekly SD | z | read |",
              "|---|---|---|---|---|---|---|---|"]
        for c, t in sorted(o["tdcc"].items()):
            if t.get("_status"):
                L.append(f"| {c} | {t.get('weeks', 0)} | — | — | — "
                         f"| — | — | {t['_status']} |")
                continue
            L.append(f"| {c} | {t['weeks']} | {t['b15_last']:.2f}% | "
                     f"{t['b15_min']:.1f}–{t['b15_max']:.1f}% | "
                     f"{t['b15_8w_change']:+.2f}pp | "
                     f"{t['weekly_sd_pp']:.2f}pp | "
                     f"{t['z_8w']:+.2f} | {t['verdict']} |")
        L += ["", "### Holders, and the denominator", "",
              "| code | holders first → last | change | custody "
              "shares first → last | change |", "|---|---|---|---|---|"]
        for c, t in sorted(o["tdcc"].items()):
            if t.get("_status"):
                continue
            hf, hl = t["holders_first"], t["holders_last"]
            sf, sl = t["shares_first"], t["shares_last"]
            L.append(f"| {c} | {hf:,.0f} → {hl:,.0f} | "
                     f"{hl / hf - 1:+.0%} | {sf:,.0f} → {sl:,.0f} | "
                     f"{t.get('shares_change', 0):+.1%} |")
        L += ["", "*A moving custody total is a corporate action, "
                  "and it changes what the percentage means — the "
                  "denominator is not the same security week to "
                  "week.*", "",
              "*TDCC retains one year, so this cannot reach the "
              "May-2026 review — only the August one.*", ""]
    L += ["## What is still missing", "",
          "- **Broker-branch (券商分點).** The single most direct "
          "positioning source in Taiwan, and unreachable: TWSE "
          "publishes per-branch, per-stock buy/sell only via "
          "bsr.twse.com.tw, CAPTCHA-gated and latest-session-only. "
          "Vendor purchase or manual daily capture; not a harvest.",
          "- **The USD 180bn tracking-AUM assumption**, which sets "
          "the LEVEL of every demand number above and is a hand-set "
          "constant with no external source. It cancels in the "
          "ranking and does not cancel in the level.",
          "- **Per-name auction share.** The 9.5% is a market-wide "
          "median applied to every name; TWSE per-stock intraday "
          "does not reach back far enough to measure it per name.",
          ""]
    DOC.write_text("\n".join(L), encoding="utf-8")


if __name__ == "__main__":
    main()
