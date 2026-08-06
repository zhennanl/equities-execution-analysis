"""Step-2 historical liquidity panel — every MSCI TW event 2015+
(c-56).

Extends the May-2026 single-event validation (STEP2_LIQUIDITY_
MODEL.md) to the FULL history: for every name in every MSCI TW
review change since 2015, compute the PIT-at-T-1 window features
and the realized T-day/after outcomes, entirely from the held
vintage cache (daily: prices, volumes, foreign holding — no new
fetching). 5-minute legs (auction-share migration etc.) exist for
2023-05+ events via the IB harvest and are analyzed separately in
tday_execution_studies; this panel is the DAILY spine.

Features (frozen at T-1, announcement -> day before effective):
  completion   cum max(vol - baseline, 0) over the window
               / (class-prior multiple x baseline ADV)
  foreign_pp   foreign-holding percentage-point change ann -> T-1
  wrongway     foreign direction INCONSISTENT with the side
Outcomes:
  t_mult       T-day volume / baseline ADV
  rev3_pct     close(T+3) vs close(T), %  (the unwind)
  fav3_pct     rev3 signed FAVORABLE to a T+1 liquidity taker
               (deletes: bounce positive; adds: fade positive)

Evaluation: the DECLARED scenario thresholds (0.3/0.7/1.2 —
declared before the May demo, never tuned) are graded per bucket,
event-clustered. Output: data/liquidity_panel_tw.json.

Usage: python scripts/liquidity_panel.py
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import numpy as np                                     # noqa: E402
import pandas as pd                                    # noqa: E402

PRIOR = {"del": 16.0, "add": 8.0}
SCEN = [(0.3, "UNDERSUPPLIED"), (0.7, "BUILDING"),
        (1.2, "WELL-SUPPLIED"), (9e9, "OVERCROWDED")]


def _series(cache, code):
    px = cache.get(f"px|{code}")
    sh = cache.get(f"sh|{code}")
    if not px:
        return None, None
    p = pd.DataFrame(px).set_index("date").sort_index()
    s = (pd.DataFrame(sh).set_index("date").sort_index()
         if sh else None)
    return p, s


def name_event(cache, code, side, ann, eff):
    px, sh = _series(cache, code)
    if px is None:
        return None
    pre = px[px.index < ann]
    if len(pre) < 40:
        return None
    base = float(pre["Trading_Volume"].tail(60).median())
    if not base:
        return None
    win = px[(px.index >= ann) & (px.index < eff)]
    if len(win) < 3:
        return None
    exp_flow = PRIOR[side] * base
    cum = float((win["Trading_Volume"] - base).clip(lower=0).sum())
    completion = cum / exp_flow
    f_pp, wrong = None, None
    if sh is not None and "ForeignInvestmentSharesRatio" in sh:
        w = sh[(sh.index >= ann) & (sh.index < eff)][
            "ForeignInvestmentSharesRatio"].dropna()
        if len(w) > 1:
            f_pp = float(w.iloc[-1] - w.iloc[0])
            wrong = (f_pp > 0.5) if side == "del" \
                else (f_pp < -0.5)
    t_rows = px[px.index >= eff]
    if not len(t_rows):
        return None
    t_day = t_rows.index[0]
    t_mult = float(t_rows["Trading_Volume"].iloc[0]) / base
    after = px[px.index > t_day]
    rev3 = (float(after["close"].iloc[min(2, len(after) - 1)]
                  / t_rows["close"].iloc[0] - 1) * 100
            if len(after) else None)
    fav3 = (rev3 if side == "del" else -rev3) \
        if rev3 is not None else None
    scen = next(s for lim, s in SCEN if completion < lim)
    return {"code": code, "side": side,
            "completion": round(completion, 2),
            "foreign_pp": round(f_pp, 2) if f_pp is not None
            else None,
            "wrongway": wrong, "scenario": scen,
            "t_mult": round(t_mult, 1),
            "rev3_pct": round(rev3, 1) if rev3 is not None
            else None,
            "fav3_pct": round(fav3, 1) if fav3 is not None
            else None}


def main():
    cache = json.loads((ROOT / "data" / "tw_vintage_cache.json")
                       .read_text())
    events = json.loads((ROOT / "data" / "msci_tw_events.json")
                        .read_text())
    panel, skipped = [], []
    for season, ev in sorted(events.items(),
                             key=lambda kv: kv[1]["ann"]):
        for side, key in (("add", "adds"), ("del", "dels")):
            for code in ev[key]:
                r = name_event(cache, code, side, ev["ann"],
                               ev["eff"])
                if r:
                    panel.append({"season": season, **r})
                else:
                    skipped.append(f"{season}:{code}")
    df = pd.DataFrame(panel)
    # ---- evaluation of the DECLARED thresholds, event-clustered
    def clus(sub, col):
        by_ev = sub.groupby("season")[col].mean()
        return (round(float(by_ev.mean()), 1), len(by_ev))
    buckets = {}
    for scen in ("UNDERSUPPLIED", "BUILDING", "WELL-SUPPLIED",
                 "OVERCROWDED"):
        sub = df[df["scenario"] == scen].dropna(
            subset=["fav3_pct"])
        if not len(sub):
            continue
        m_abs, nev = clus(sub.assign(
            a=sub["rev3_pct"].abs()), "a")
        m_fav, _ = clus(sub, "fav3_pct")
        m_t, _ = clus(sub, "t_mult")
        buckets[scen] = {"n_names": int(len(sub)),
                         "n_events": nev,
                         "mean_abs_rev3_pct": m_abs,
                         "mean_fav3_pct": m_fav,
                         "mean_t_mult": m_t}
    # correlation completion vs |reversal|, event-clustered means
    ev_means = df.dropna(subset=["rev3_pct"]).groupby("season") \
        .agg(c=("completion", "mean"),
             r=("rev3_pct", lambda s: s.abs().mean()))
    corr = (float(np.corrcoef(ev_means["c"], ev_means["r"])[0, 1])
            if len(ev_means) > 3 else None)
    # wrongway flag performance
    ww = df.dropna(subset=["fav3_pct", "wrongway"])
    ww_stats = {
        "wrongway_true_mean_abs_rev3": round(float(
            ww[ww["wrongway"]]["rev3_pct"].abs().mean()), 1)
        if len(ww[ww["wrongway"]]) else None,
        "wrongway_false_mean_abs_rev3": round(float(
            ww[~ww["wrongway"]]["rev3_pct"].abs().mean()), 1)
        if len(ww[~ww["wrongway"]]) else None,
        "n_true": int(ww["wrongway"].sum()),
        "n_false": int((~ww["wrongway"]).sum())}
    out = {"n_name_events": len(df),
           "n_events": df["season"].nunique(),
           "skipped": skipped,
           "declared_thresholds": "0.3/0.7/1.2 (pre-May-26 demo, "
                                  "NEVER tuned; this is their "
                                  "first full-history evaluation)",
           "buckets": buckets,
           "completion_vs_absrev3_corr_eventlevel":
           round(corr, 3) if corr is not None else None,
           "wrongway_flag": ww_stats,
           "panel": panel}
    (ROOT / "data" / "liquidity_panel_tw.json").write_text(
        json.dumps(out, indent=1))
    print(f"panel: {len(df)} name-events across "
          f"{df['season'].nunique()} events "
          f"(skipped {len(skipped)})")
    for k, v in buckets.items():
        print(f"  {k:14s} n={v['n_names']:3d}/{v['n_events']:2d}ev "
              f"|rev3| {v['mean_abs_rev3_pct']:5.1f}% "
              f"fav3 {v['mean_fav3_pct']:+5.1f}% "
              f"t_mult {v['mean_t_mult']}")
    print("event-level corr(completion, |rev3|):", corr)
    print("wrongway:", ww_stats)


if __name__ == "__main__":
    main()
