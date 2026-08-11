#!/usr/bin/env python3
"""Volume-revealed tracking AUM — the close's own testimony.

    py scripts\\tw_volume_revealed_aum.py

THE IDEA (c-375, Bill; the Chinco-Sammon logic). Fund registers
only see money with a ticker. But every indexed dollar — ETF,
mandate, internal indexing — must TRADE the effective-day close,
so the close's excess volume reveals the money the registers
cannot: for one event,

    revealed AUM = excess close dollars / delta-w

where excess close dollars is what the closing auction printed
on the effective day OVER the same stock's normal close, and
delta-w is the weight the name gained or lost. This is the
project's Method D (flow-revealed) rebuilt on AUCTION VOLUME
instead of T86 foreign net — which removes Method D's dominant
defect, because auction volume does not net buyers against
sellers the way T86 nets foreign accounts.

WHAT LIMITS THE SAMPLE, STATED BEFORE THE NUMBER. Delta-w needs
the name's float cap at its event, and public float history does
not exist (the licence limitation). So the study runs on the
recent events whose float inputs are ON DISK — members of the
current index with a MOPS-verified cap and a Yahoo float factor
— and names every event it skips. Three approximations, each
declared in the output: the cap is struck at the MOPS as-of date
rather than the event date (price drift between the two is the
dominant error); the float factor is today's; the index float
value (USD 3,183bn, MSCI Taiwan factsheet Jul-2026) is today's.

WHY BOTH DIRECTIONS COUNT. An addition's trackers buy delta-w x
AUM in the close; a deletion's sell the same. Volume is
unsigned, so both sides run through one formula and the sides
are reported separately as a check on each other.

WHAT THE NUMBER MEANS. Each event yields one revealed-AUM
reading; the distribution across events is the estimate. Read it
against the two anchors already on the page: the USD 60bn
bottom-up floor (registers + fee inversion) and Method D's T86
median of ~180bn with a 13x IQR. A volume-revealed median
between those two, with a tighter spread, is exactly what the
Chinco-Sammon mechanism predicts: more than the registers,
cleaner than netted flow.
"""
from __future__ import annotations

import datetime as dt
import json
import pathlib
import statistics as stats

ROOT = pathlib.Path(__file__).resolve().parents[1]
STUDY = ROOT / "data" / "tw_addition_study.json"
IB = ROOT / "data" / "ib_5m_analysis.json"
MOPS = ROOT / "data" / "tw_float_mops_v2.json"
YAHOO = ROOT / "data" / "tw_float_yahoo.json"
SCN = ROOT / "data" / "aug26_scenarios.json"
FS = ROOT / "data" / "msci_factsheet_archive.json"
OUT = ROOT / "data" / "tw_volume_revealed_aum.json"

RECENT = ("Aug25", "Nov25", "Feb26", "May26")


def main():
    for p in (STUDY, IB, MOPS, YAHOO, SCN, FS):
        if not p.exists():
            raise SystemExit(f"missing {p.name}")
    study = json.loads(STUDY.read_text(encoding="utf-8"))
    ib = json.loads(IB.read_text(encoding="utf-8"))
    mops = {str(r["code"]): r for r in
            json.loads(MOPS.read_text(encoding="utf-8"))["rows"]}
    yahoo = json.loads(YAHOO.read_text(encoding="utf-8"))
    A = json.loads(SCN.read_text(encoding="utf-8"))["assumptions"]
    fs = json.loads(FS.read_text(encoding="utf-8"))
    fs_month = sorted(fs)[-1]
    idx_float = fs[fs_month]["index_float_cap_musd"] / 1000.0

    intr = {(str(e["code"]), e["rev"]): e
            for e in ib["events"] if e["market"] == "Taiwan"}

    rows, skipped = [], []
    for e in study["events"]:
        if e["rev"] not in RECENT:
            continue
        code = str(e["code"])
        key = (code, e["rev"])
        i = intr.get(key)
        if not (i and e.get("adv") and e.get("vol_mult_eff")
                and e.get("price_level")):
            skipped.append({"key": e["key"],
                            "why": "no intraday close share or "
                                   "study volume fields"})
            continue
        cap = (mops.get(code) or {}).get("cap_usd_b")
        fif = yahoo.get(code)
        if not (cap and fif):
            skipped.append({"key": e["key"],
                            "why": "no on-disk float cap "
                                   "(MOPS+Yahoo cover current "
                                   "members only)"})
            continue
        # excess close volume, in shares then USD at the
        # event's own price
        eff_day_sh = e["vol_mult_eff"] * e["adv"]
        eff_close_sh = eff_day_sh * i["close_share"]
        normal_close_sh = e["adv"] * i["close_share_control"]
        excess_sh = eff_close_sh - normal_close_sh
        if excess_sh <= 0:
            skipped.append({"key": e["key"],
                            "why": "no excess close volume"})
            continue
        excess_usd_m = (excess_sh * e["price_level"]
                        / A["usd_twd"] / 1e6)
        dw = cap * fif / idx_float
        rows.append({
            "key": e["key"], "code": code, "rev": e["rev"],
            "action": e["action"],
            "excess_close_usd_m": round(excess_usd_m, 1),
            "float_cap_usd_b": round(cap * fif, 2),
            "delta_w_pct": round(dw * 100, 4),
            "revealed_aum_usd_b": round(
                excess_usd_m / 1000 / dw, 1),
        })

    vals = [r["revealed_aum_usd_b"] for r in rows]
    med = stats.median(vals) if vals else None
    q = (sorted(vals) if vals else [])

    def pct(p):
        if not q:
            return None
        i = (len(q) - 1) * p
        lo, hi = int(i), min(int(i) + 1, len(q) - 1)
        return round(q[lo] + (q[hi] - q[lo]) * (i - lo), 1)

    out = {
        "_what": "tracking AUM revealed by excess effective-day "
                 "close volume, per event — registers cannot "
                 "see internal indexing; the close can",
        "generated": dt.datetime.now().isoformat(timespec="seconds"),
        "method": {
            "formula": "excess close $ / delta-w, delta-w = "
                       "float cap / index float value",
            "index_float_usd_b": idx_float,
            "index_float_asof": fs_month,
            "usd_twd": A["usd_twd"],
            "approximations": [
                "float cap struck at the MOPS as-of date, not "
                "the event date — price drift between the two "
                "is the dominant error",
                "float factor is today's (Yahoo); no public "
                "float history exists",
                "index float value is today's factsheet",
                "the close-only definition EXCLUDES tracker "
                "volume worked outside the auction, so the "
                "reading errs low"],
        },
        "coverage": {"events_used": len(rows),
                     "events_skipped": len(skipped),
                     "skipped": skipped},
        "revealed_aum_usd_b": {
            "median": med, "p25": pct(.25), "p75": pct(.75),
            "by_side": {
                s: (round(stats.median(
                    [r["revealed_aum_usd_b"] for r in rows
                     if r["action"] == s]), 1)
                    if any(r["action"] == s for r in rows)
                    else None)
                for s in ("ADD", "DEL")}},
        "anchors": {"bottom_up_floor_usd_b": 60,
                    "t86_flow_revealed_median_usd_b": 180},
        "events": rows,
    }
    OUT.write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(f"events used {len(rows)} (skipped {len(skipped)})")
    for r in rows:
        print(f"  {r['key']:24} dw={r['delta_w_pct']:.3f}%  "
              f"excess={r['excess_close_usd_m']:8.1f}m  "
              f"-> AUM {r['revealed_aum_usd_b']:7.1f}bn")
    if med is not None:
        print(f"revealed AUM median {med}bn  "
              f"IQR {pct(.25)}-{pct(.75)}bn")
    print(f"wrote {OUT.name}")


if __name__ == "__main__":
    main()
