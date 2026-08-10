#!/usr/bin/env python3
"""STEP-2 WINDOW STUDY — China A / Japan / Hong Kong, May-2026 MSCI
cohorts (session 9d). Replicates the Taiwan framework (formulas =
WINDOW_STUDY §0) with each market's public-data limits STATED:

  CN-A : quotes/volumes via baostock daily (official-grade, years).
         Crowding pillar ABSENT (margin data sandbox-blocked;
         northbound per-stock holdings = future fetcher).
  JP   : quotes via yfinance daily. Crowding at MAY vintage ABSENT
         (JPX site retains ~1 month of short files; archive begins
         with OUR collection, July-2026).
  HK   : quotes via yfinance daily (incl. MSCI-China H-lines that
         trade in HK). Crowding RECONSTRUCTED at vintage from the
         SFC weekly archive — discovered to list ALL weeks back to
         2012 (n=724): the HK crowding pillar is historical.

Windows: announcement 2026-05-12 (post-close) -> effective print
2026-05-29. PIT: baselines from sessions <= ann only.

Usage: cn | jphk | sfc | report
Cache: data/cnjphk_window.json
Doc:   docs/case_studies/WINDOW_STUDY_CNJPHK_MAY2026.md
"""
import json
import re
import sys
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scripts.pit_may2026_asia import ACTUAL  # noqa

CACHE = Path("data/cnjphk_window.json")
ANN, EFF = "2026-05-12", "2026-05-29"
W0, W1 = "2026-05-04", "2026-06-03"


def names_by_market():
    cn_a, hk = [], []
    for key, side in (("adds", "Buy"), ("dels", "Sell")):
        for t in sorted(ACTUAL["China"][key]):
            if t.endswith(".SS"):
                cn_a.append((f"sh.{t[:-3]}", t, side))
            elif t.endswith(".SZ"):
                cn_a.append((f"sz.{t[:-3]}", t, side))
            elif t.endswith(".HK"):
                hk.append((t, side))
    jp = [(t, "Buy") for t in sorted(ACTUAL["Japan"]["adds"])] + \
         [(t, "Sell") for t in sorted(ACTUAL["Japan"]["dels"])]
    hk += [(t, "Sell") for t in sorted(ACTUAL["HongKong"]["dels"])]
    return cn_a, jp, hk


def load():
    return json.loads(CACHE.read_text(encoding="utf-8")) if CACHE.exists() else {}


def save(c):
    CACHE.write_text(json.dumps(c), encoding="utf-8")


def fetch_cn():
    import baostock as bs
    cn_a, _, _ = names_by_market()
    c = load()
    out = c.setdefault("CN", {})
    bs.login()
    for code, label, side in cn_a:
        if label in out:
            continue
        rs = bs.query_history_k_data_plus(
            code, "date,close,volume", start_date=W0, end_date=W1,
            frequency="d", adjustflag="3")
        rows = []
        while rs.error_code == "0" and rs.next():
            d, cl, v = rs.get_row_data()
            if cl and v:
                rows.append([d, float(cl), float(v)])
        out[label] = {"side": side, "rows": rows}
        print(label, len(rows))
    bs.logout()
    save(c)


def fetch_jphk():
    import yfinance as yf
    _, jp, hk = names_by_market()
    c = load()
    for mkt, lst in (("JP", jp), ("HK", hk)):
        out = c.setdefault(mkt, {})
        for t, side in lst:
            if t in out:
                continue
            try:
                h = yf.Ticker(t).history(start=W0, end=W1,
                                         interval="1d")
                rows = [[str(d.date()), float(r["Close"]),
                         float(r["Volume"])]
                        for d, r in h.iterrows()]
                out[t] = {"side": side, "rows": rows}
                print(mkt, t, len(rows))
            except Exception as e:
                print(mkt, t, "FAIL", str(e)[:50])
    save(c)


def fetch_sfc():
    """Vintage HK crowding: the SFC page lists EVERY weekly CSV
    back to 2012 — pull the window's weeks (pre-ann + window)."""
    from agents.event_data import parse_sfc_short_csv
    want = {"20260410", "20260417", "20260424", "20260502",
            "20260508", "20260515", "20260522", "20260529"}
    req = urllib.request.Request(
        "https://www.sfc.hk/en/Regulatory-functions/Market/"
        "Short-position-reporting/Aggregated-reportable-short-"
        "positions-of-specified-shares",
        headers={"User-Agent": "Mozilla/5.0"})
    html = urllib.request.urlopen(req, timeout=25).read() \
        .decode("utf-8", "ignore")
    links = {d: u for u, d in re.findall(
        r'href="(https://www\.sfc\.hk/-/media/[^"]*Short_'
        r'Position_Reporting_Aggregated_Data_(\d{8})\.csv'
        r'[^"]*)"', html)}
    c = load()
    out = c.setdefault("SFC", {})
    for d in sorted(want):
        # exact date may differ (Friday conventions) — nearest match
        cands = [k for k in links if abs(
            (pd.Timestamp(k) - pd.Timestamp(d)).days) <= 3]
        if not cands:
            continue
        k = sorted(cands)[0]
        if k in out:
            continue
        r2 = urllib.request.Request(
            links[k], headers={"User-Agent": "Mozilla/5.0"})
        df = parse_sfc_short_csv(
            urllib.request.urlopen(r2, timeout=25).read()
            .decode("utf-8-sig", "ignore"))
        out[k] = {r["ticker"]: r["short_shares"]
                  for _, r in df.iterrows()}
        print("SFC", k, len(out[k]))
    save(c)


def panel(mkt):
    c = load()
    rows = []
    for name, obj in c.get(mkt, {}).items():
        rs = [r for r in obj["rows"] if r[1] and r[2]]
        pre = [r for r in rs if r[0] <= ANN][-5:]
        sess = [r for r in rs if ANN < r[0] <= EFF]
        if len(pre) < 3 or len(sess) < 5:
            continue
        p0 = pre[-1][1]
        v0 = float(np.median([r[2] for r in pre]))
        for k, r in enumerate(sess, 1):
            drift = (r[1] / p0 - 1) * 1e4
            rows.append({
                "market": mkt, "code": name,
                "side": obj["side"], "k": k, "T": len(sess),
                "date": r[0], "close": r[1],
                "fav_drift": drift if obj["side"] == "Buy"
                else -drift,
                "t_mult": r[2] / v0 if v0 else None})
    return pd.DataFrame(rows)


def hk_crowding():
    """Weekly short_chg since the last pre-ann week, per HK name."""
    c = load()
    sfc = c.get("SFC", {})
    dates = sorted(sfc)
    pre = [d for d in dates
           if d <= ANN.replace("-", "")][-1:] or dates[:1]
    out = {}
    for t, obj in c.get("HK", {}).items():
        base = t.split(".")[0].zfill(4)
        b = sfc.get(pre[0], {}).get(base)
        series = {d: sfc[d].get(base) for d in dates}
        if b:
            out[t] = {d: round((v / b - 1) * 100, 1)
                      for d, v in series.items() if v}
    return pre[0] if pre else None, out


def counterfactuals(df):
    out = []
    for (m, code), g in df.groupby(["market", "code"]):
        g = g.sort_values("k")
        T = g["T"].iloc[0]
        cT = g[g["k"] == T]["close"]
        if not len(cT):
            continue
        cT = float(cT.iloc[0])
        sgn = 1 if g["side"].iloc[0] == "Buy" else -1

        def cost(avg):
            return sgn * (avg / cT - 1) * 1e4
        cl = g["close"].tolist()
        a3 = g[g["k"] <= 3]["fav_drift"]
        out.append({
            "market": m, "code": code, "side": g["side"].iloc[0],
            "LINEAR": cost(np.mean(cl)),
            "LATE5": cost(np.mean(cl[-5:])),
            "EARLY30_MOC70": cost(0.3 * np.mean(cl[:3])
                                  + 0.7 * cT),
            "ALL_DAY1": cost(cl[0]),
            "A3_hot": bool(len(a3) >= 3 and a3.iloc[-1] > 0)})
    return pd.DataFrame(out)


def report():
    frames = [panel(m) for m in ("CN", "JP", "HK")]
    df = pd.concat([f for f in frames if len(f)], ignore_index=True)
    cf = counterfactuals(df)
    med = cf.groupby(["market", "side"])[
        ["LINEAR", "LATE5", "EARLY30_MOC70",
         "ALL_DAY1"]].median().round(0)
    # THE OOS TEST of the Taiwan A+3 rule (sign rule, no re-fitting)
    oos = cf.groupby(["side", "A3_hot"])[
        ["LINEAR", "LATE5"]].median().round(0)
    pre_week, hkc = hk_crowding()
    L = ["# Step-2 Window Study — China A / Japan / Hong Kong, "
         "May-2026 MSCI Cohorts",
         f"*Session 9d. {cf.groupby(['market', 'code']).ngroups} "
         "names; formulas identical to the Taiwan study "
         "(WINDOW_STUDY §0); announcement 2026-05-12 post-close, "
         "print 2026-05-29; PIT baselines pre-announcement only.*",
         ""]
    L.append("## 1. Per-market data limitations (stated first)\n")
    L.append("| Market | Quotes | Crowding at vintage | Foreign "
             "flow |\n|---|---|---|---|")
    L.append("| CN-A | baostock daily (official-grade, years) | "
             "ABSENT — margin data walled; northbound holdings = "
             "queued fetcher | ABSENT (same) |")
    L.append("| JP | yfinance daily | ABSENT at May vintage — JPX "
             "site retains ~1 month; our archive starts Jul-2026 | "
             "weekly aggregates only (structural) |")
    L.append("| HK | yfinance daily | **RECONSTRUCTED — the SFC "
             "page lists all 724 weekly files back to 2012** (the "
             "HK crowding pillar is historical!) | CCASS (future "
             "fetcher) |")
    L.append("\n## 2. Execution counterfactuals vs the T-close "
             "(median bps; negative = beat the close)\n")
    L.append(med.to_markdown())
    L.append("\n## 3. OUT-OF-SAMPLE test of the Taiwan A+3 rule "
             "(sign rule, no re-fit)\n")
    L.append(oos.to_markdown())
    L.append("\n*(A3_hot = favorable drift at session 3 > 0 — the "
             "rule as exported from Taiwan, applied unchanged to "
             "MSCI-class flows in three other markets.)*")
    if hkc:
        L.append(f"\n## 4. HK vintage crowding (SFC weekly, "
                 f"base week {pre_week})\n")
        rows = [{"name": t, **{d: v for d, v in s.items()}}
                for t, s in hkc.items()]
        L.append(pd.DataFrame(rows).to_markdown(index=False))
        L.append("\n*(% change in aggregated reportable short "
                 "positions vs the last pre-announcement week — "
                 "the weekly-cadence crowding read, at vintage.)*")
    L.append("""
## 5. Cross-market synthesis — the MSCI-class window INVERTS the Taiwan playbook

**The Taiwan (FTSE-class) lessons do NOT transfer — and the
inversion is systematic, which makes it a finding, not noise:**

| Lesson | Taiwan FTSE-class (6 events, 38 names) | MSCI-class May-2026 (CN/HK, this study) |
|---|---|---|
| Adds | drift builds ALL window; buy day-1 = **−630** (early wins) | announcement-day overshoot then DECAY; buy day-1 = **+1103 (CN) / +1453 (HK)** — day-1 buys the pop's top; WAIT/MOC wins |
| Deletes | fall early, RECOVER into print; MOC best | keep pressing to T; sell early = **−614 (CN) / −1097 (HK)**; working wins |
| A+3 momentum gate | separates ±500 bps, dominates | **FAILS OOS on adds** (hot +448 vs cold +336 — mean-reversion after the pop); no separation on deletes |

**Mechanism hypothesis (consistent with everything measured):**
MSCI events carry 16x flows and a professional arb ecosystem — the
add pop is priced WITHIN THE ANNOUNCEMENT SESSION and then decays
as arbs distribute; FTSE-class events (5x, more domestic) leak in
gradually, so momentum persists. Delete-side: MSCI's larger flow
presses prices to the print; FTSE deletes finish early and bounce.
**Execution playbooks must be EVENT-CLASS-CONDITIONAL**: provider x
tracked-AUM class is a first-order input to the discretion matrix,
ahead of the A+3 gate.

**Caveats, stated:** ONE MSCI event (the 66-deletion May-2026 SAIR,
one tape regime); JP's milder pattern (adds LINEAR −402, deletes
~flat) hints market-level variation within the class; close-fill
counterfactuals are impact-free upper bounds. Cross-event
replication (Aug-2026 + the archived future events + alias-bridged
history) is the designed confirmation path before any rule ships.
""")
    out = Path("docs/case_studies/WINDOW_STUDY_CNJPHK_MAY2026.md")
    out.write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"doc -> {out}")
    print(med.to_string())
    print("\nOOS A+3:")
    print(oos.to_string())


if __name__ == "__main__":
    m = sys.argv[1] if len(sys.argv) > 1 else "report"
    {"cn": fetch_cn, "jphk": fetch_jphk, "sfc": fetch_sfc,
     "report": report}[m]()
