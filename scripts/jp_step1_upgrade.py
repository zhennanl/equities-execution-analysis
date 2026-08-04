"""JP Step-1 upgrade — from daily data ALREADY HELD (no new source).

Session 9i. The prediction engine needs DAILY data; the decade
window study already harvested 182 JP name-windows (yfinance daily,
2015-2025). This script converts them into Step-1 assets:

  1. PRINT-VERIFICATION of the JP alias bridge (t_mult at T vs the
     name's own pre-announcement baseline; >=2 verified, 1.2-2
     print-weak, <1.2 no-material-print — the honest categories
     from the CN work; survivorship stated: delisted names absent
     from yfinance).
  2. JP CLASS T-MULTIPLE PRIORS per side (median/max/n on verified
     names) — replacing the silent use of TAIWAN-measured priors in
     the JP pack section (an honesty gap: the pack showed TW's 16x
     under every market).
  3. data/jp_event_priors.json consumed by the Asia runner.

Source alternatives documented (not needed for this step):
J-Quants free tier = official JPX dailies (signup; the upgrade
path); IB TSE L1 (JPY 3,000/mo) = INTRADAY only — deferred.

Usage: python scripts/jp_step1_upgrade.py
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import numpy as np                                     # noqa: E402
import pandas as pd                                    # noqa: E402

OUT = ROOT / "data" / "jp_event_priors.json"
DOC = ROOT / "docs" / "case_studies" / "JP_STEP1_UPGRADE.md"


def main():
    from scripts.window_study_decade import events as decade_events
    d = json.loads((ROOT / "data" / "decade_windows.json")
                   .read_text())
    evs = {e["season"]: e for e in decade_events()}
    rows = []
    for key, v in d.items():
        season, code = key.split("|")
        if not code.endswith(".T"):
            continue
        ev = evs.get(season)
        if not ev or len(v.get("rows", [])) < 8:
            continue
        df = pd.DataFrame(v["rows"], columns=["date", "close",
                                              "vol"])
        df = df[df["date"] <= ev["eff"]]
        pre = df[df["date"] <= ev["ann"]]
        win = df[df["date"] > ev["ann"]]
        if len(pre) < 3 or len(win) < 3:
            continue
        base = pre["vol"].median()
        t = win.iloc[-1]
        tm = t["vol"] / base if base else 0
        cat = ("VERIFIED" if tm >= 2 else
               "PRINT-WEAK" if tm >= 1.2 else "NO-MATERIAL-PRINT")
        rows.append({"season": season, "code": code,
                     "side": v["side"], "t_mult": round(tm, 1),
                     "category": cat})
    df = pd.DataFrame(rows)
    ver = df[df["category"] == "VERIFIED"]
    priors = {}
    for side, g in ver.groupby("side"):
        priors[side] = {"median": round(float(g["t_mult"].median()),
                                        1),
                        "max": round(float(g["t_mult"].max()), 1),
                        "n": int(len(g)),
                        "basis": "JP decade name-events, "
                                 "print-verified, daily yfinance"}
    out = {"priors": priors,
           "verification": {
               "n_total": len(df),
               "verified": int((df["category"] == "VERIFIED").sum()),
               "print_weak": int((df["category"] ==
                                  "PRINT-WEAK").sum()),
               "no_material": int((df["category"] ==
                                   "NO-MATERIAL-PRINT").sum())},
           "note": "survivorship: delisted JP names absent from "
                   "yfinance — verification covers survivors only, "
                   "stated"}
    OUT.write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))
    agg = df.groupby(["side", "category"])["code"].count()
    L = ["# JP Step-1 Upgrade — from daily data already held\n",
         f"*Session 9i. {len(df)} JP name-events (29 seasons, "
         "2015-2025, yfinance daily from the decade harvest). No "
         "new data source required: prediction runs on dailies. "
         "J-Quants free tier documented as the official upgrade "
         "path; IB TSE (JPY 3,000/mo) gates INTRADAY only — "
         "deferred by choice.*\n",
         "## Alias verification (survivorship stated)\n",
         agg.to_frame("n").to_markdown(), "",
         "## JP class T-multiple priors (print-verified names)\n",
         f"```json\n{json.dumps(priors, indent=1)}\n```\n",
         "Wired into the Asia pack: the Japan section now shows "
         "JP-measured priors instead of silently reusing Taiwan's "
         "16x (an honesty gap this closes)."]
    DOC.write_text("\n".join(L), encoding="utf-8")
    print("wrote", DOC)


if __name__ == "__main__":
    main()
