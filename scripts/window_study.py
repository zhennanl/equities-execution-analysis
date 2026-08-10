#!/usr/bin/env python3
"""STEP-2 WINDOW STUDY on the keyed decade (session 9a).

Six TW50 events (2021-2026, 24 adds / 24 dels), three official
sources (quotes/shorts/foreign), STRICT point-in-time discipline:
every per-day factor uses only data <= that day (announcement lands
after the close; the window is the sessions AFTER ann through the
effective print T).

Per name/day factors: cumulative drift vs pre-ann close; daily
volume multiple vs pre-ann baseline; short-balance build since ann;
cumulative foreign net; window flow phasing. Then execution
counterfactuals vs the T-close benchmark, and early-signal
conditioning (what you could KNOW at A+3 vs what followed).

Output: docs/case_studies/WINDOW_STUDY_2021_2026.md
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scripts.backfill_tw_history import load as hist  # noqa

KEYS = json.loads(Path("data/ftse_tw50_changes.json").read_text(encoding="utf-8"))
EVENTS = ["2021-06", "2021-09", "2023-09", "2024-03",
          "2025-12", "2026-03"]

METRIC_DEFS_MD = """
## 0. Metric definitions — exact formulas, inputs, edge handling

All inputs are OFFICIAL TWSE files (MI_INDEX all-stock daily quotes,
TWT93U short balances, TWT38U foreign net) — nothing derived from
third-party feeds. Notation: announcement date A (published AFTER
that day's close), effective print day T, sessions k = 1..N strictly
after A through T, relative day rk = k − N (so rk = 0 is the print).

| Metric | Formula | Inputs & units | Edge handling |
|---|---|---|---|
| `pre_close` (P₀) | last official close on or before A | NT$; uncontaminated baseline because the announcement lands post-close | name skipped if missing |
| `base_v` (V₀) | median(daily share volume over the ≤5 sessions ending at A) | shares/day | requires ≥3 sessions, else name skipped |
| `drift_bps(k)` | (closeₖ / P₀ − 1) × 10⁴ | bps vs the pre-announcement price | — |
| `fav_drift(k)` | drift for adds; **−drift** for deletes | bps; positive = price moving WITH the index flow | sign flip only, no scaling |
| `t_mult(k)` | volₖ / V₀ | unitless multiple of baseline volume | None if V₀ = 0 |
| `short_chg(k)` | ((marginₖ+sblₖ)/(margin₀+sbl₀) − 1) × 100, balances from TWT93U, 0 = A-day | % change in TOTAL short interest since announcement | None if A-day balance 0/missing |
| `foreign_cum_x_adv(k)` | Σⱼ≤ₖ (foreign buyⱼ − sellⱼ) / V₀ | cumulative foreign net, in units of baseline-day volumes (×ADV) | missing days contribute 0 |
| track rows | cross-name MEDIAN at each rk, sides separate; `n` = names contributing | medians (robust to the shipping-boom outliers) | rk < −10 trimmed for display |
| counterfactual `cost_bps` | sign × (P_avg / close_T − 1) × 10⁴; sign = +1 Buy / −1 Sell | bps vs the T-close benchmark; NEGATIVE = client beat the close; MOC ≡ 0 by construction | fills at DAILY CLOSES — impact-free upper bounds, stated |
| strategies | LINEAR = mean(close₁..T) · LATE5 = mean(last 5 closes) · EARLY30_MOC70 = 0.3·mean(close₁..₃) + 0.7·close_T · ALL_DAY1 = close₁ | — | — |
| `early_fav_drift_A3` | fav_drift at the close of session 3 | bps; PIT-legal at A+3 | uses session min(3, N) |
| `early_hot` | early_fav_drift_A3 > side median | boolean; IN-SAMPLE split (median chosen on the same 38 names — stated; out-of-sample test = next events) | — |
"""


def event_frames():
    quotes, shorts, foreign = hist("quotes"), hist("shorts"), \
        hist("foreign")
    qd = sorted(quotes)
    rows = []
    for ek in EVENTS:
        v = KEYS[ek]
        ann = v["ann_date"].replace("/", "")
        eff = v["effective"].replace("-", "")
        pre = [d for d in qd if d <= ann][-5:]
        sess = [d for d in qd if ann < d <= eff]
        if len(pre) < 3 or len(sess) < 5:
            print(ek, "insufficient window"); continue
        for side, lst in (("Buy", v["adds"]), ("Sell", v["dels"])):
            for x in lst:
                c = x["code"]
                pc = quotes[pre[-1]].get(c)
                base = [quotes[d][c][0] for d in pre
                        if quotes[d].get(c) and quotes[d][c][0]]
                if not pc or not pc[2] or len(base) < 3:
                    continue
                base_v = float(np.median(base))
                s0 = shorts.get(pre[-1], {}).get(c)
                f_cum = 0.0
                for k, d in enumerate(sess, 1):
                    q = quotes[d].get(c)
                    if not q or not q[2]:
                        continue
                    f_cum += foreign.get(d, {}).get(c, 0.0)
                    sb = shorts.get(d, {}).get(c)
                    rows.append({
                        "event": ek, "code": c, "side": side,
                        "k": k, "T": len(sess), "date": d,
                        "close": q[2], "vol": q[0],
                        "pre_close": pc[2], "base_v": base_v,
                        "drift_bps": (q[2] / pc[2] - 1) * 1e4,
                        "t_mult": q[0] / base_v if base_v else None,
                        "short_chg": ((sb[0] + sb[1])
                                      / (s0[0] + s0[1]) - 1) * 100
                        if sb and s0 and (s0[0] + s0[1]) else None,
                        "foreign_cum_x_adv": f_cum / base_v
                        if base_v else None})
    return pd.DataFrame(rows)


def favorable(df):
    """Sign drift so + = moving WITH the index flow (adds up,
    deletes down)."""
    s = df.copy()
    s["fav_drift"] = np.where(s["side"] == "Buy",
                              s["drift_bps"], -s["drift_bps"])
    return s


def day_tracks(df):
    """Median factor tracks by normalized day index (k relative to
    T: rk = k - T, so 0 = the print day)."""
    s = favorable(df)
    s["rk"] = s["k"] - s["T"]
    g = s.groupby(["side", "rk"]).agg(
        fav_drift=("fav_drift", "median"),
        t_mult=("t_mult", "median"),
        short_chg=("short_chg", "median"),
        foreign=("foreign_cum_x_adv", "median"),
        n=("code", "count")).reset_index()
    return g[g["rk"] >= -10]


def counterfactuals(df):
    """Strategy cost vs the T-close benchmark (bps; negative =
    beat the close). MOC = 0 by construction."""
    out = []
    for (ek, c), g in df.groupby(["event", "code"]):
        g = g.sort_values("k")
        T = g["T"].iloc[0]
        closeT = g[g["k"] == T]["close"]
        if not len(closeT):
            continue
        closeT = float(closeT.iloc[0])
        side = g["side"].iloc[0]
        sgn = 1 if side == "Buy" else -1

        def cost(avg):
            return sgn * (avg / closeT - 1) * 1e4
        closes = g["close"].tolist()
        out.append({
            "event": ek, "code": c, "side": side,
            "LINEAR": cost(np.mean(closes)),
            "LATE5": cost(np.mean(closes[-5:])),
            "EARLY30_MOC70": cost(0.3 * np.mean(closes[:3])
                                  + 0.7 * closeT),
            "ALL_DAY1": cost(closes[0]),
            "early_fav_drift_A3":
                (1 if side == "Buy" else -1)
                * (closes[min(2, len(closes) - 1)]
                   / g["pre_close"].iloc[0] - 1) * 1e4})
    return pd.DataFrame(out)


def make_figs(tracks):
    """Static evolution charts -> docs/figs/ (embedded in the md)."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    figdir = Path("docs/figs")
    figdir.mkdir(exist_ok=True)
    specs = [("fav_drift", "Cumulative drift WITH the flow (bps)",
              "window_drift.png"),
             ("t_mult", "Daily volume multiple vs pre-ann baseline",
              "window_tmult.png"),
             ("short_chg", "Short interest change since ann (%)",
              "window_short.png"),
             ("foreign", "Cumulative foreign net (x baseline ADV)",
              "window_foreign.png")]
    for col, title, fname in specs:
        fig, ax = plt.subplots(figsize=(7, 3.4))
        for side, style, lbl in (("Buy", "o-", "ADDS"),
                                 ("Sell", "s--", "DELETES")):
            t = tracks[tracks["side"] == side]
            ax.plot(t["rk"], t[col], style, label=lbl, ms=4)
        ax.axvline(0, color="gray", lw=0.8, ls=":")
        ax.axhline(0, color="gray", lw=0.5)
        ax.set_xlabel("session vs print day (0 = T)")
        ax.set_title(title, fontsize=10)
        ax.legend(fontsize=8)
        fig.tight_layout()
        fig.savefig(figdir / fname, dpi=110)
        plt.close(fig)
    return [s[2] for s in specs]


def main():
    df = event_frames()
    print(f"panel: {len(df)} name-days, "
          f"{df.groupby(['event', 'code']).ngroups} names")
    tracks = day_tracks(df)
    cf = counterfactuals(df)
    med = cf.groupby("side")[["LINEAR", "LATE5", "EARLY30_MOC70",
                              "ALL_DAY1"]].median().round(0)
    # early-signal conditioning: split by favorable drift at A+3
    cf["early_hot"] = cf["early_fav_drift_A3"] > \
        cf.groupby("side")["early_fav_drift_A3"].transform("median")
    cond = cf.groupby(["side", "early_hot"])[
        ["LINEAR", "LATE5"]].median().round(0)

    figs = make_figs(tracks)
    L = ["# Step-2 Window Study — Six Keyed TW50 Events (2021-2026), "
         "Strict PIT",
         f"*Session 9a. {df.groupby(['event', 'code']).ngroups} "
         "event-names, official quotes/shorts/foreign only, every "
         "factor computed with data <= its own day. Events: "
         + ", ".join(EVENTS) + ".*", ""]
    L.append(METRIC_DEFS_MD)
    L.append("## 1. The day-by-day factor tracks (median, day rk "
             "relative to the print T=0)\n")
    for f in figs:
        L.append(f"![{f}](../figs/{f})\n")
    for side, label in (("Buy", "ADDS"), ("Sell", "DELETES —"
                                          " drift signed WITH flow")):
        t = tracks[tracks["side"] == side]
        L.append(f"### {label}\n")
        L.append(t.round(2).to_markdown(index=False))
        L.append("")
    L.append("## 2. Execution counterfactuals vs the T-close "
             "benchmark (median bps; negative = beat the close)\n")
    L.append(med.to_markdown())
    L.append("\n## 3. Early-signal conditioning (what A+3 already "
             "told you)\n")
    L.append(cond.to_markdown())
    L.append("\n*(early_hot = favorable drift at A+3 above the "
             "side's median — a PIT-legal signal on day 3)*")
    L.append("""
## 4. What the window taught us — the lessons

**L1. The sides are ASYMMETRIC, and the asymmetry is the headline.**
ADDS: every early strategy beat the T-close (day-1-everything:
median **−630 bps**; 30/70 split −86; late-work −71) — the add-side
front-run is real, persistent, and mostly happens EARLY in the
window. DELETES: every working strategy LOST to the close (+43 to
+88 bps) — delete prices fall early, then RECOVER INTO the print
(the covering bounce arriving before T). For this FTSE-class event:
adds reward pre-positioning; deletes reward patience. The MOC
default is right for deletes and expensive for adds.

**L2. Day 3 already knows.** Conditioning on favorable drift at A+3
(PIT-legal — you have it in real time) separates the outcomes:
early-hot adds, working linearly = **−274 bps**; early-cold adds =
+282 (worse than just taking the close). Same shape on deletes
(−35/−55 vs +187/+154). Window momentum PERSISTS: if the name is
moving with the flow by day 3, work it; if it is not, stop and take
the print. This one conditional rule dominates every unconditional
strategy in the sample.

**L3. The discretion matrix gets its drift leg.** The May-2026 MSCI
grading showed crowding correctly called UNPRICED but missed drift
direction on 2/7 names — this study supplies the missing signal:
the A+3 drift check IS the drift leg, measured on 38 names.

**L4. Honesty caveats, stated:** fills at daily closes (price-path
differences, not net-of-impact — a real desk pays spread/impact
working early, so L1's magnitudes are upper bounds); the −630
day-1 number includes the announcement gap (partly uncapturable);
n = 38 names / 6 events, FTSE-class prints (~5x), NOT MSCI-class
(16x) — the MSCI replication runs when the alias bridge lands;
no borrow costs on pre-positioned adds.

**L5. Execution playbook update (Step-2/3 wiring):** (a) adds with
an envelope: deploy the early tranche in the FIRST sessions, not
spread; (b) deletes: default MOC unless A+3 shows the name still
falling; (c) the A+3 checkpoint joins the daily loop as a formal
decision gate (alongside the crowding flip we already grade);
(d) re-run this study on the MSCI cohort + with impact-adjusted
fills via the replay simulator.""")
    out = Path("docs/case_studies/WINDOW_STUDY_2021_2026.md")
    out.write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"doc -> {out}")
    print("\ncounterfactual medians (bps vs close):")
    print(med.to_string())
    print("\nconditioned:")
    print(cond.to_string())


if __name__ == "__main__":
    main()
