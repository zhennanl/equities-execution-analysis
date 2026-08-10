#!/usr/bin/env python3
"""Bring the Taiwan series current, and cover the TPEx names.

    py scripts\\tw_live_topup.py status            # no network
    py scripts\\tw_live_topup.py prices            # top up px|/sh|
    py scripts\\tw_live_topup.py flows             # called names
    py scripts\\tw_live_topup.py flows --codes 2330,6223
    py scripts\\tw_live_topup.py calibrate         # lending units

WHY THIS EXISTS. Two holes showed up while forecasting the Aug-2026
review, and both mattered more than they looked.

1. THE PRICE SERIES WAS FIVE SESSIONS STALE. tw_vintage_harvest.py has
   `END = "2026-08-01"` baked in, and its fetch() skips any series
   already in the cache — so it can bootstrap a name and can never top
   one up. The blind window was 1-7 August, i.e. precisely the run-up to
   the announcement. It was not academic: 8299 went 1,640 -> 2,020
   (+23%) inside it, which inverts the positioning read taken on data to
   31 July.

2. TPEx NAMES HAVE NO FLOW COVERAGE. t86_history.json is TWSE-only, so
   8299 — the name our own call is least sure of — had no institutional
   flow and no borrow. Same for any future TPEx candidate; MPI (6223)
   was added in May-2026 and is TPEx too.

WHY FINMIND FOR FLOWS RATHER THAN THE EXCHANGE FEEDS. The T86 endpoint
returns positional columns whose layout has changed three times, and
reading a historical day with today's offsets silently returns
foreign+trust as "foreign" (see agents/investor_flow._T86_LAYOUTS).
FinMind's institutional dataset is LONG-FORMAT AND NAMED — one row per
(date, investor type) with an explicit `name` field — so there is no
column to guess at, and it covers TPEx and TWSE through the same call.
That makes it the safer source for this job even though it is a
third-party mirror rather than the exchange itself.

THE ONE THING NOT TAKEN ON TRUST. The securities-lending dataset is
transaction-level new lending (議借), NOT an outstanding balance, and it
does not state whether `volume` is shares or lots. `calibrate` answers
that empirically by comparing it against the balances already in
sbl_history.json for names that appear in both, instead of assuming.
Until it is run, lending is stored raw and labelled unverified.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import statistics as st
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

API = "https://api.finmindtrade.com/api/v4/data"
CACHE = ROOT / "data" / "tw_vintage_cache.json"
FLOWS = ROOT / "data" / "tw_flows.json"
CALL = ROOT / "data" / "aug26_tw_call_v2.json"
PACE_S = 1.2

# FinMind's investor labels. Foreign = the main foreign book PLUS the
# foreign dealers' own account, which is the same definition T86 uses in
# its modern layout (columns [3] + [6]) — kept identical so the two
# sources can be compared without a convention mismatch.
FOREIGN = ("Foreign_Investor", "Foreign_Dealer_Self")
TRUST = ("Investment_Trust",)
DEALER = ("Dealer_self", "Dealer_Hedging")


def _j(p, default=None):
    return (json.loads(p.read_text(encoding="utf-8"))
            if p.exists() else default)


def _save(path, obj):
    """Atomic: a killed run must never leave a truncated cache."""
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj), encoding="utf-8")
    tmp.replace(path)


def _get(dataset, data_id, start, end):
    import requests
    params = {"dataset": dataset, "data_id": data_id,
              "start_date": start, "end_date": end}
    tok = os.environ.get("FINMIND_TOKEN")
    if tok:
        params["token"] = tok
    r = requests.get(API, params=params, timeout=60)
    r.raise_for_status()
    j = r.json()
    if j.get("status") != 200:
        raise RuntimeError(f"{dataset}/{data_id}: {j.get('msg')}")
    return j.get("data") or []


def called_codes():
    c = _j(CALL)
    return [str(x["code"]) for x in c["calls"]] if c else []


def _merge_by_date(old, new):
    """Union on date, NEW WINS on a collision.

    A same-date collision is normally a restated row, and the later
    fetch is the better copy. Returns (merged, n_added) so the caller
    can report movement rather than claim it.
    """
    by = {str(r["date"]): r for r in old}
    before = set(by)
    for r in new:
        by[str(r["date"])] = r
    return ([by[k] for k in sorted(by)], len(set(by) - before))


# ── status ───────────────────────────────────────────────────────────

def cmd_status(_a):
    cache = _j(CACHE, {})
    codes = called_codes()
    print(f"today {dt.date.today().isoformat()}\n")
    twii = _j(ROOT / "data" / "twii_daily.json", {})
    if twii:
        print(f"  TAIEX          -> {max(twii)}")
    for name, path in (("t86_history", "t86_history.json"),
                       ("sbl_history", "sbl_history.json")):
        d = _j(ROOT / "data" / path, {})
        ne = [k for k, v in d.items() if v]
        if ne:
            print(f"  {name:<14} -> {max(ne)}  ({len(ne)} non-empty days)")
    fl = _j(FLOWS, {})
    print()
    print(f"  {'code':<7}{'px last':<13}{'sh last':<13}"
          f"{'inst last':<13}{'lend last':<12}")
    for c in codes:
        px = cache.get(f"px|{c}") or []
        sh = cache.get(f"sh|{c}") or []
        f = (fl.get("codes") or {}).get(c) or {}
        inst, lend = f.get("inst") or {}, f.get("lend") or {}
        print(f"  {c:<7}"
              f"{(px[-1]['date'] if px else '—'):<13}"
              f"{(sh[-1]['date'] if sh else '—'):<13}"
              f"{(max(inst) if inst else '—'):<13}"
              f"{(max(lend) if lend else '—'):<12}")
    print("\n(no network touched)")
    return 0


# ── prices ───────────────────────────────────────────────────────────

def cmd_prices(a):
    cache = _j(CACHE, {})
    end = a.to or dt.date.today().isoformat()
    codes = a.codes.split(",") if a.codes else called_codes()
    if a.all:
        codes = sorted({k.split("|", 1)[1] for k in cache
                        if k.startswith(("px|", "sh|"))})
    print(f"topping up {len(codes)} names to {end}\n")
    moved = 0
    for i, code in enumerate(codes, 1):
        for tag, ds, keep in (
                ("px", "TaiwanStockPrice",
                 ("date", "close", "Trading_Volume")),
                ("sh", "TaiwanStockShareholding",
                 ("date", "NumberOfSharesIssued",
                  "ForeignInvestmentSharesRatio",
                  "ForeignInvestmentUpperLimitRatio"))):
            if a.prices_only and tag == "sh":
                continue
            key = f"{tag}|{code}"
            old = cache.get(key) or []
            if not old:
                print(f"  {key}: not bootstrapped — run "
                      f"tw_vintage_harvest.py fetch first")
                continue
            last = max(str(r["date"]) for r in old)
            if last >= end:
                continue
            # re-fetch from the last stored day, not the day after: the
            # final bar can be revised, and _merge_by_date lets the new
            # copy win
            try:
                rows = _get(ds, code, last, end)
            except Exception as ex:                      # noqa: BLE001
                print(f"  {key}: FAIL {ex}")
                time.sleep(PACE_S)
                continue
            slim = [{k: r.get(k) for k in keep} for r in rows
                    if r.get("date")]
            cache[key], added = _merge_by_date(old, slim)
            if added:
                moved += 1
                print(f"  {key}: {last} -> "
                      f"{max(str(r['date']) for r in cache[key])} "
                      f"(+{added})")
            time.sleep(PACE_S)
        if i % 5 == 0:
            _save(CACHE, cache)
    _save(CACHE, cache)
    print(f"\n{moved} series advanced -> {CACHE.relative_to(ROOT)}")
    return 0


# ── flows ────────────────────────────────────────────────────────────

def _net(rows):
    """Long-format institutional rows -> {date: {foreign,trust,dealer}}.

    Keyed on the NAME field, so an added or reordered investor category
    cannot silently land in the wrong bucket. Unknown labels are
    collected and reported rather than dropped in silence.
    """
    out, unknown = {}, set()
    for r in rows:
        d, nm = str(r.get("date")), r.get("name")
        net = float(r.get("buy") or 0) - float(r.get("sell") or 0)
        slot = ("foreign" if nm in FOREIGN else
                "trust" if nm in TRUST else
                "dealer" if nm in DEALER else None)
        if slot is None:
            unknown.add(nm)
            continue
        out.setdefault(d, {"foreign": 0.0, "trust": 0.0,
                           "dealer": 0.0})[slot] += net
    return out, unknown


def cmd_flows(a):
    fl = _j(FLOWS, {"_what": "TWSE+TPEx per-name flows (FinMind)",
                    "_source": API,
                    "_lending_units": "UNVERIFIED — run `calibrate`",
                    "codes": {}})
    codes = a.codes.split(",") if a.codes else called_codes()
    start = a.start or "2026-01-01"
    end = a.to or dt.date.today().isoformat()
    print(f"flows for {len(codes)} names, {start} -> {end}\n")
    all_unknown = set()
    for code in codes:
        rec = fl["codes"].setdefault(code, {"inst": {}, "lend": {}})
        try:
            inst, unknown = _net(_get(
                "TaiwanStockInstitutionalInvestorsBuySell",
                code, start, end))
            all_unknown |= unknown
            rec["inst"].update(inst)
        except Exception as ex:                          # noqa: BLE001
            print(f"  {code} inst: FAIL {ex}")
            inst = {}
        time.sleep(PACE_S)
        try:
            lend = {}
            for r in _get("TaiwanStockSecuritiesLending",
                          code, start, end):
                lend[str(r["date"])] = (lend.get(str(r["date"]), 0.0)
                                        + float(r.get("volume") or 0))
            rec["lend"].update(lend)
        except Exception as ex:                          # noqa: BLE001
            print(f"  {code} lend: FAIL {ex}")
            lend = {}
        print(f"  {code}: inst {len(inst)} days"
              f"{' -> ' + max(inst) if inst else ''}"
              f" | lend {len(lend)} days")
        time.sleep(PACE_S)
        _save(FLOWS, fl)
    if all_unknown:
        print(f"\n!! unrecognised investor labels, NOT counted: "
              f"{sorted(all_unknown)}\n   add them to FOREIGN/TRUST/"
              f"DEALER before trusting these nets")
    _save(FLOWS, fl)
    print(f"\n-> {FLOWS.relative_to(ROOT)}")
    return 0


# ── calibrate ────────────────────────────────────────────────────────

def cmd_calibrate(_a):
    """Are FinMind lending volumes shares or lots?

    Decided against sbl_history.json, which is in shares. Both series
    describe new lending, so on days where our balance RISES the rise
    should be of the same order as FinMind's volume — same order if
    shares, ~1000x apart if lots.
    """
    fl = _j(FLOWS, {})
    sbl = _j(ROOT / "data" / "sbl_history.json", {})
    if not fl.get("codes"):
        print("no flows yet — run `flows` first")
        return 1
    ratios = []
    for code, rec in fl["codes"].items():
        lend = rec.get("lend") or {}
        bal = {d: v for d, v in
               ((k, (sbl.get(k) or {}).get(code)) for k in sbl)
               if v is not None}
        if len(bal) < 5 or not lend:
            continue
        days = sorted(bal)
        for prev, cur in zip(days, days[1:]):
            iso = f"{cur[:4]}-{cur[4:6]}-{cur[6:]}"
            v = lend.get(iso)
            try:
                rise = float(bal[cur][1]) - float(bal[prev][1])
            except (TypeError, ValueError, IndexError):
                continue
            if v and rise > 0:
                ratios.append(rise / v)
    if not ratios:
        print("no overlapping days — the called names are TPEx or "
              "absent from sbl_history; try `flows --codes 2330,2408`")
        return 1
    med = st.median(ratios)
    unit = ("SHARES (1x)" if 0.2 < med < 5
            else "LOTS (~1000 shares)" if 200 < med < 5000
            else f"UNCLEAR — median ratio {med:.1f}")
    print(f"n={len(ratios)} overlapping days")
    print(f"median (SBL balance rise) / (FinMind volume) = {med:.1f}")
    print(f"-> FinMind lending `volume` looks like {unit}")
    fl["_lending_units"] = unit
    fl["_lending_calibration"] = {"n": len(ratios), "median_ratio": med}
    _save(FLOWS, fl)
    return 0


def main():
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd")
    sub.add_parser("status")
    p = sub.add_parser("prices")
    p.add_argument("--codes")
    p.add_argument("--to")
    p.add_argument("--all", action="store_true")
    p.add_argument("--prices-only", action="store_true")
    f = sub.add_parser("flows")
    f.add_argument("--codes")
    f.add_argument("--start")
    f.add_argument("--to")
    sub.add_parser("calibrate")
    a = ap.parse_args()
    return {"status": cmd_status, "prices": cmd_prices,
            "flows": cmd_flows, "calibrate": cmd_calibrate}.get(
                a.cmd, cmd_status)(a)


if __name__ == "__main__":
    raise SystemExit(main())
