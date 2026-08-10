"""The Taiwan window analysis, run for EVERY APAC market
(c-152).

Bill's ask: the agent produced a full announcement->effective
study for Taiwan (tracker / hedge-fund / desk personas plus
the conditional tables). Run the same thing market by market.

WHAT TRANSFERS, AND WHAT DOESN'T — stated before the numbers:
  PRICE/VOLUME metrics transfer everywhere: gap1, drift,
  eff_day, revert5, total_alpha, capture, volume multiples,
  hit rates, era splits. Those are computed here for all 11
  markets with harvested windows.
  FLOW metrics do NOT: the Taiwan conditionals (accumulation
  vs froth, borrow-crowding, excess-vs-sector-tide) need
  foreign-net and stock-borrow series that exist only for
  Taiwan today (ASIC shorts for AU, KR/TH pending). Those
  sections are emitted as NEEDS with the named harvester
  rather than silently skipped.

SURVIVORSHIP is carried per market, not averaged away. Only
Taiwan and India are delisted-safe (exchange day-files);
the other nine are Yahoo survivors, so their DELETION stats
are biased toward names that lived. Every deletion figure
from a survivor market is labelled.

Run: py scripts\\apac_persona_study.py
Out: data/apac_persona_study.json + console table
"""
import json
import statistics as stx
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "apac_persona_study.json"
WIN = ROOT / "data" / "apac_event_windows"
DELISTED_SAFE = {"Taiwan", "India"}
FLOWS = {"Taiwan": "t86 foreign net + SBL borrow + margin",
         "Australia": "ASIC daily shorts only",
         "Korea": "pending (kr_flow_harvest.py)",
         "Thailand": "pending (th_nvdr_harvest.py)"}


def med(xs):
    xs = [x for x in xs if x is not None]
    return round(stx.median(xs), 4) if xs else None


def frac(xs, cond):
    xs = [x for x in xs if x is not None]
    return round(sum(1 for x in xs if cond(x)) / len(xs), 3) \
        if xs else None


def metrics(w):
    """Per-window price metrics — the same definitions the
    Taiwan study used, so the numbers are comparable."""
    px = w.get("px") or []
    if len(px) < 12:
        return None
    dts = [r["d"] for r in px]
    cl = [r["c"] for r in px]
    vol = [r.get("v") for r in px]
    i0 = max((i for i, d in enumerate(dts) if d <= w["ann"]),
             default=None)
    ie = max((i for i, d in enumerate(dts) if d <= w["eff"]),
             default=None)
    if i0 is None or ie is None or ie <= i0 + 2 \
            or len(cl) < ie + 2:
        return None
    adv = stx.median([q for q in vol[max(0, i0 - 20):i0] if q]
                     or [0]) or None
    gap1 = cl[i0 + 1] / cl[i0] - 1
    drift = cl[ie - 1] / cl[i0 + 1] - 1
    eff = cl[ie] / cl[ie - 1] - 1
    tot = cl[ie - 1] / cl[i0] - 1
    rev5 = cl[min(ie + 5, len(cl) - 1)] / cl[ie] - 1
    pre = (cl[i0] / cl[max(0, i0 - 10)] - 1) if i0 >= 10 \
        else None
    return {"action": w["action"], "year": int(w["ann"][:4]),
            "gap1": gap1, "drift": drift, "eff_day": eff,
            "total_alpha": tot, "revert5": rev5,
            "pre_drift": pre,
            "capture": (drift / (gap1 + drift)
                        if (gap1 + drift) else None),
            "vol_mult_eff": ((vol[ie] / adv)
                             if adv and vol[ie] else None)}


def study(market, rows):
    adds = [r for r in rows if r["action"] == "ADD"]
    dels = [r for r in rows if r["action"] == "DEL"]
    safe = market in DELISTED_SAFE

    def era(r):
        y = r["year"]
        # c-188: the 2010-14 bucket is gone with the 2015 floor
        return ("2015-18" if y <= 2018 else "2019-22"
                if y <= 2022 else "2023-26")
    out = {
        "market": market, "n": len(rows),
        "n_add": len(adds), "n_del": len(dels),
        "survivorship": ("DELISTED-SAFE" if safe else
                         "SURVIVORS ONLY — deletion stats "
                         "biased toward names that lived"),
        "flows": FLOWS.get(market, "none harvested"),
        # ---- TRACKER ----------------------------------
        "P1_close_cost": {
            "ADD_eff_day": med([r["eff_day"] for r in adds]),
            "DEL_eff_day": med([r["eff_day"] for r in dels])},
        "P2_early_cost": {
            "ADD_drift": med([r["drift"] for r in adds]),
            "ADD_gap1": med([r["gap1"] for r in adds])},
        "P3_close_reverts": {
            "ADD_revert5": med([r["revert5"] for r in adds]),
            "ADD_frac_reverting": frac(
                [r["revert5"] for r in adds], lambda x: x < 0),
            "DEL_revert5": med([r["revert5"] for r in dels])},
        "P4_close_capacity": {
            "eff_day_vol_x_ADV": med([r["vol_mult_eff"]
                                      for r in rows])},
        # ---- HEDGE FUND -------------------------------
        "H1_alpha": {
            "ADD_total": med([r["total_alpha"] for r in adds]),
            "DEL_total": med([r["total_alpha"] for r in dels]),
            "ADD_by_era": {e: med([r["total_alpha"]
                                   for r in adds
                                   if era(r) == e])
                           for e in ("2015-18", "2019-22",
                                     "2023-26")}},
        "H2_entry_timing": {
            "ADD_capture": med([r["capture"] for r in adds])},
        "H4_reversal": {
            "short_ADD_edge": med([-r["revert5"]
                                   for r in adds]),
            "short_ADD_hit": frac([r["revert5"] for r in adds],
                                  lambda x: x < 0)},
        "H5_front_running": {
            "ADD_pre_drift": med([r["pre_drift"]
                                  for r in adds]),
            "DEL_pre_drift": med([r["pre_drift"]
                                  for r in dels])},
        "H6_hit_rates": {
            "ADD_alpha_hit": frac([r["total_alpha"]
                                   for r in adds],
                                  lambda x: x > 0),
            "DEL_alpha_hit": frac([r["total_alpha"]
                                   for r in dels],
                                  lambda x: x < 0)},
        # ---- WHAT CANNOT BE RUN HERE -------------------
        "conditionals_NEEDS": (
            "accumulation-vs-froth, borrow crowding and "
            "excess-vs-sector-tide need per-name flow series. "
            f"This market has: {FLOWS.get(market, 'none')}."
            if market != "Taiwan" else "RUN — see "
            "event_conditional_tw.json / strategist_tw.json")}
    return out


def main():
    res = {"generated": "2026-08-08",
           "method": "same metric definitions as the Taiwan "
                     "study, so markets are comparable",
           "markets": {}}
    files = sorted(WIN.glob("*.json"))
    tw = ROOT / "data" / "tw_event_windows.json"
    srcs = [("Taiwan", tw)] + [(f.stem, f) for f in files
                               if f.stem != "Taiwan"]
    for name, path in srcs:
        if not path.exists():
            continue
        w = json.loads(path.read_text(encoding="utf-8"))["windows"]
        ws = list(w.values()) if isinstance(w, dict) else w
        rows = [m for m in (metrics(x) for x in ws) if m]
        if len(rows) < 5:
            res["markets"][name] = {
                "market": name, "status": "INSUFFICIENT",
                "n_windows_with_prices": len(rows),
                "need": "more harvested windows"}
            print(f"{name:12} INSUFFICIENT ({len(rows)})")
            continue
        s = study(name, rows)
        res["markets"][name] = s
        print(f"{name:12} n={s['n']:4} (A{s['n_add']}/"
              f"D{s['n_del']}) | ADD alpha "
              f"{(s['H1_alpha']['ADD_total'] or 0):+.2%} | "
              f"eff-day {(s['P1_close_cost']['ADD_eff_day'] or 0):+.2%}"
              f" | revert5 {(s['P3_close_reverts']['ADD_revert5'] or 0):+.2%}"
              f" | vol {s['P4_close_capacity']['eff_day_vol_x_ADV']}x"
              f" | {'safe' if name in DELISTED_SAFE else 'surv'}")
    OUT.write_text(json.dumps(res, indent=1), encoding="utf-8")
    print(f"\n-> {OUT.name}")


if __name__ == "__main__":
    main()
