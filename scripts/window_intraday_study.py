"""Window intraday study — ann->eff period at 5m resolution.

Session 9i. Builds the per-name-per-WINDOW-DAY intraday panel from
the IB harvest (24 events post the 2023-05 floor; full ann->eff
coverage audited, CNY-aware) and evaluates the registry-v2
hypotheses H9/H10 with the same event-clustered verdict machinery
as run 1. Registry was LOCKED before this file ran.

Panel columns per name-day:
  k, rk               day index from announcement / to T
  day_auction_share   day's 13:25+ volume / day total (DIRECT)
  pm_vol_share        13:00-13:25 cont volume / cont volume
  am_fav_bps, pm_fav_bps   favorable drift split at the 12:00 bar
  day_vol_x_base      day volume / pre-announcement baseline median
Usage: python scripts/window_intraday_study.py
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import numpy as np                                     # noqa: E402
import pandas as pd                                    # noqa: E402

DOC = ROOT / "docs" / "case_studies" / "WINDOW_INTRADAY_STUDY.md"
OUT = ROOT / "data" / "window_intraday.json"


def _anns():
    anns = {}
    keys = json.loads((ROOT / "data" / "ftse_tw50_changes.json")
                      .read_text(encoding="utf-8"))
    for v in keys.values():
        if v.get("effective"):
            anns[v["effective"]] = v["ann_date"].replace("/", "-")
    from agents.time_machine import MSCI_TW
    for v in MSCI_TW.values():
        anns[v["effective"]] = v["ann_date"].replace("/", "-")
    bridge = json.loads((ROOT / "data" / "msci_tw_events.json")
                        .read_text(encoding="utf-8"))
    for v in bridge.values():
        if v.get("eff"):
            anns.setdefault(v["eff"], v["ann"])
    return anns


def panel() -> pd.DataFrame:
    from scripts.ib_harvest import IB_FLOOR, _ib_event_set
    from scripts.tday_execution_studies import _ib_day, _load_ib
    ib = _load_ib()
    anns = _anns()
    rows = []
    for event, prov, eff, names in _ib_event_set():
        if eff < IB_FLOOR:
            continue
        ann = anns.get(eff)
        if not ann:
            continue
        for code, side in names.items():
            series = sorted({r[0][:10] for r in
                             ib.get(code, {}).get("5m", [])})
            wdays = [d for d in series if ann < d <= eff]
            pre = [d for d in series if d <= ann]
            if len(wdays) < 5 or len(pre) < 5:
                continue
            base_vols = []
            for d in pre[-10:]:
                r = _ib_day(ib, code, d)
                if r:
                    base_vols.append(sum(x[3] for x in r[0]) + r[1])
            base = float(np.median(base_vols)) if base_vols else None
            sgn = 1.0 if side == "Buy" else -1.0
            T = len(wdays)
            for k, d in enumerate(wdays, start=1):
                r = _ib_day(ib, code, d)
                if not r:
                    continue
                cont, auc, last = r
                cv = sum(x[3] for x in cont)
                tot = cv + auc
                if not tot:
                    continue
                o_am = cont[0][1]
                c12 = next((x[2] for x in reversed(cont)
                            if x[0] <= "12:00"), None)
                if not (o_am and c12):
                    continue
                rows.append({
                    "event": event, "provider": prov, "code": code,
                    "side": side, "k": k, "rk": k - T,
                    "day_auction_share": auc / tot,
                    "pm_vol_share": sum(x[3] for x in cont
                                        if x[0] >= "13:00") / cv
                    if cv else None,
                    "am_fav_bps": sgn * (c12 / o_am - 1) * 1e4,
                    "pm_fav_bps": sgn * (last / c12 - 1) * 1e4,
                    "day_vol_x_base": tot / base if base else None})
    return pd.DataFrame(rows)


def _late_minus_early(df, col):
    """Per name-event: mean(col | rk>=-3) - mean(col | k<=3); then
    event-clustered effects (mean of name effects per event)."""
    effects = []
    for event, g in df.groupby("event"):
        diffs = []
        for code, gg in g.groupby("code"):
            late = gg[gg["rk"] >= -3][col].mean()
            early = gg[gg["k"] <= 3][col].mean()
            if pd.notna(late) and pd.notna(early):
                diffs.append(late - early)
        if diffs:
            effects.append(float(np.mean(diffs)))
    return effects


def main():
    from agents.variable_lab import _verdict
    df = panel()
    print(f"panel: {len(df)} name-days, "
          f"{df['event'].nunique()} events, "
          f"{df.groupby(['event', 'code']).ngroups} name-windows")
    res = {}
    # H9: deletes' day auction share, late minus early (share units:
    # scale x1000 to reuse the bps verdict machinery at the locked
    # 0.05-share threshold -> 50)
    dels = df[df["side"] == "Sell"]
    e9 = [x * 1000 for x in _late_minus_early(dels,
                                              "day_auction_share")]
    v9, s9 = _verdict(e9)
    res["H9"] = {"verdict": v9, **s9,
                 "effect_share": round(s9.get("mean_bps", 0) / 1000,
                                       3) if "mean_bps" in s9 else None}
    # H10: PM fav drift, late minus early (bps native)
    e10 = _late_minus_early(df, "pm_fav_bps")
    v10, s10 = _verdict(e10)
    res["H10"] = {"verdict": v10, **s10}
    # descriptive: medians by class and window third
    df["phase"] = np.where(df["k"] <= 3, "early",
                           np.where(df["rk"] >= -3, "late", "mid"))
    desc = df.groupby(["provider", "side", "phase"]).agg(
        n=("code", "count"),
        auc_share=("day_auction_share", "median"),
        pm_vol=("pm_vol_share", "median"),
        am_fav=("am_fav_bps", "median"),
        pm_fav=("pm_fav_bps", "median"),
        vol_x=("day_vol_x_base", "median")).round(3)
    OUT.write_text(json.dumps(
        {"n_name_days": len(df),
         "n_events": int(df["event"].nunique()), "H9": res["H9"],
         "H10": res["H10"],
         "desc": json.loads(desc.to_json())}, indent=1,
        default=str), encoding="utf-8")
    print("H9:", json.dumps(res["H9"]))
    print("H10:", json.dumps(res["H10"]))
    print(desc.to_string())
    L = ["# Window Intraday Study — ann->eff at 5m (24 events, "
         "post-2023-05 floor)\n",
         f"*Session 9i. {len(df)} name-days across "
         f"{df['event'].nunique()} events; registry-v2 H9/H10 "
         "evaluated with the locked criteria (event-clustered, "
         "LOO). Full ann->eff coverage audited (CNY-aware); TPEx "
         "gap excluded.*\n",
         "## Verdicts\n",
         f"- **H9** (deletes' window-day auction share rises toward "
         f"T): **{res['H9']['verdict']}** — "
         f"{json.dumps({k: v for k, v in res['H9'].items() if k != 'verdict'})}",
         f"- **H10** (PM drift concentration grows toward T): "
         f"**{res['H10']['verdict']}** — "
         f"{json.dumps({k: v for k, v in res['H10'].items() if k != 'verdict'})}",
         "", "## Descriptive medians (class x window phase)\n",
         desc.to_markdown()]
    DOC.write_text("\n".join(L), encoding="utf-8")
    print("wrote", DOC)


if __name__ == "__main__":
    main()
