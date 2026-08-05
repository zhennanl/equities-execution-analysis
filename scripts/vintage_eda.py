"""Vintage EDA — first exploratory pass on the PIT cache (c-30).

Treats index-review prediction as a supervised problem and asks the
two EDA questions the new data can finally answer:
  1. THE GLIDE PATH: how does market cap evolve over the 12 months
     BEFORE a deletion announcement, vs cutline survivors?
  2. SMART MONEY: does foreign ownership move BEFORE announcements
     (adds vs deletes) — i.e., is anticipation visible in the
     shareholding tape?

Outputs: docs/img/eda_glidepath.png, docs/img/eda_foreign.png and
printed stats. Pure exploration — no thresholds set here (that is
registry business).

Usage: python scripts/vintage_eda.py
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import numpy as np                                     # noqa: E402
import pandas as pd                                    # noqa: E402

CACHE = json.loads((ROOT / "data" / "tw_vintage_cache.json")
                   .read_text())
EVENTS = json.loads((ROOT / "data" / "msci_tw_events.json")
                    .read_text())
IMG = ROOT / "docs" / "img"
LOOKBACK = 250                                # trading days (~12m)
SURVIVORS = ["1101", "1326", "2207", "2002"]  # cutline residents


def series(code):
    px = CACHE.get(f"px|{code}")
    sh = CACHE.get(f"sh|{code}")
    if not px or not sh:
        return None
    p = pd.DataFrame(px).set_index("date")
    s = pd.DataFrame(sh).set_index("date")
    df = p.join(s, how="left").sort_index()
    df["NumberOfSharesIssued"] = \
        df["NumberOfSharesIssued"].ffill().bfill()
    df["ForeignInvestmentSharesRatio"] = \
        df["ForeignInvestmentSharesRatio"].ffill()
    df["cap"] = df["close"] * df["NumberOfSharesIssued"]
    return df


def window(df, ann, col):
    pre = df[df.index < ann].tail(LOOKBACK)
    if len(pre) < 200:
        return None
    v = pre[col].to_numpy(dtype=float)
    if col == "cap":
        v = v / v[0] * 100.0                    # index to 100
    else:
        v = v - v[0]                            # pp change
    # pad to LOOKBACK from the left
    out = np.full(LOOKBACK, np.nan)
    out[-len(v):] = v
    return out


def collect(role):
    rows = []
    for season, ev in EVENTS.items():
        for code in ev["dels" if role == "del" else "adds"]:
            df = series(code)
            if df is None:
                continue
            for col, tag in (("cap", "cap"),
                             ("ForeignInvestmentSharesRatio", "ff")):
                w = window(df, ev["ann"], col)
                if w is not None:
                    rows.append((tag, season, code, w))
    return rows


def survivor_windows():
    rows = []
    for season, ev in EVENTS.items():
        if not ev["dels"]:
            continue
        for code in SURVIVORS:
            if code in ev["dels"] or code in ev["adds"]:
                continue
            df = series(code)
            if df is None:
                continue
            w = window(df, ev["ann"], "cap")
            if w is not None:
                rows.append(("cap", season, code, w))
    return rows


def main():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    IMG.mkdir(exist_ok=True)
    dels = collect("del")
    adds = collect("add")
    surv = survivor_windows()
    x = np.arange(-LOOKBACK, 0)

    def med(rows, tag):
        m = np.array([w for t, _, _, w in rows if t == tag])
        return (np.nanmedian(m, axis=0),
                np.nanpercentile(m, 25, axis=0),
                np.nanpercentile(m, 75, axis=0), len(m))

    # --- chart 1: the glide path
    fig, ax = plt.subplots(figsize=(9, 5))
    for rows, lbl, c in ((dels, "deleted names", "#E45756"),
                         (surv, "cutline survivors", "#4C78A8")):
        mm, lo, hi, n = med(rows, "cap")
        ax.plot(x, mm, color=c, label=f"{lbl} (n={n} windows)")
        ax.fill_between(x, lo, hi, color=c, alpha=0.15)
    ax.axhline(100, color="#888", lw=0.7)
    ax.set_title("The glide path to deletion — median market cap, "
                 "12 months before the announcement (indexed=100)")
    ax.set_xlabel("trading days before announcement")
    ax.set_ylabel("cap index (T-250 = 100)")
    ax.legend()
    fig.tight_layout()
    fig.savefig(IMG / "eda_glidepath.png", dpi=120)
    dm = med(dels, "cap")[0]
    sm = med(surv, "cap")[0]
    print(f"glide path: deleted names median cap {dm[-1]:.0f} at T-1 "
          f"(vs 100 at T-250); survivors {sm[-1]:.0f}")

    # --- chart 2: foreign ownership before the announcement
    fig, ax = plt.subplots(figsize=(9, 5))
    for rows, lbl, c in ((adds, "adds", "#54A24B"),
                         (dels, "deletes", "#E45756")):
        mm, lo, hi, n = med(rows, "ff")
        ax.plot(x, mm, color=c, label=f"{lbl} (n={n} windows)")
        ax.fill_between(x, lo, hi, color=c, alpha=0.15)
    ax.axhline(0, color="#888", lw=0.7)
    ax.set_title("Foreign ownership change over the 12 months before "
                 "the announcement (pp vs T-250)")
    ax.set_xlabel("trading days before announcement")
    ax.set_ylabel("foreign holding, pp change")
    ax.legend()
    fig.tight_layout()
    fig.savefig(IMG / "eda_foreign.png", dpi=120)
    am = med(adds, "ff")[0]
    dm = med(dels, "ff")[0]
    print(f"foreign pp change T-250->T-1: adds {am[-1]:+.2f}, "
          f"deletes {dm[-1]:+.2f}")
    print("wrote", IMG / "eda_glidepath.png", "and eda_foreign.png")


if __name__ == "__main__":
    main()
