"""STEP-2 TIME MACHINE (session 9c) — go back to any keyed index
review, stand on any day inside its announcement -> effective
window, and run the Step-2 analytics using ONLY data <= that day.

PIT enforcement is structural, not cosmetic: `asof_panel` computes
every factor from officially-dated rows and then TRUNCATES the
panel at the as-of date before anything downstream (charts,
decisions) sees it — the future is not merely hidden, it is never
loaded into the view.

Event universe: every keyed TW50 review (data/ftse_tw50_changes
.json) plus the keyed 2026 MSCI TW events. Data: the official
backfill layer (data/tw_history/*). Windows are backfilled ON
DEMAND (threaded) the first time an event is opened.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
KEYS = ROOT / "data" / "ftse_tw50_changes.json"

# Keyed MSCI TW events with codes (from the graded case studies).
MSCI_TW = {
    # session 9i: 2025 events added from the OFFICIAL archive keys +
    # print-verified alias map (tw_expost_msci) — the first measured
    # MSCI TW BUY windows. 5274 (Nov add) is TPEx — excluded, stated.
    "MSCI 2025-08 QIR": {
        "ann_date": "2025/08/07", "effective": "2025-08-28",
        "adds": ["6919", "2059"], "dels": ["9904", "9945"]},
    "MSCI 2025-11 SAIR": {
        "ann_date": "2025/11/06", "effective": "2025-11-27",
        "adds": ["3665", "2360", "2368", "2449", "1504"],
        "dels": ["2353", "2409", "2377", "6415", "2347", "6409",
                 "3702"]},
    "MSCI 2026-02 QIR": {
        "ann_date": "2026/02/10", "effective": "2026-02-26",
        "adds": [], "dels": ["2105", "1476", "9910", "8464"]},
    "MSCI 2026-05 SAIR": {
        "ann_date": "2026/05/12", "effective": "2026-05-29",
        "adds": [],   # 6223 is TPEx — quotes layer is TWSE-only
        "dels": ["1102", "1402", "1504", "2324", "2474", "2610",
                 "2633"]},
}


def list_events() -> pd.DataFrame:
    """All keyed events with window dates and cache status."""
    from scripts.backfill_tw_history import load as hist
    qdates = set(hist("quotes"))
    rows = []
    keys = json.loads(KEYS.read_text())
    for k in sorted(keys):
        v = keys[k]
        if "adds" not in v or k.endswith("-adhoc") \
                or not v.get("effective"):
            continue
        n_chg = len(v["adds"]) + len(v["dels"])
        rows.append({"event": f"FTSE TW50 {k}",
                     "ann": v["ann_date"].replace("/", "-"),
                     "eff": v["effective"], "n_changes": n_chg})
    for name, v in MSCI_TW.items():
        rows.append({"event": name,
                     "ann": v["ann_date"].replace("/", "-"),
                     "eff": v["effective"],
                     "n_changes": len(v["adds"]) + len(v["dels"])})
    df = pd.DataFrame(rows)

    def cached(r):
        a = r["ann"].replace("-", "")
        e = r["eff"].replace("-", "")
        need = pd.bdate_range(r["ann"], r["eff"]).strftime("%Y%m%d")
        have = sum(d in qdates for d in need)
        return f"{have}/{len(need)}"
    df["days_cached"] = df.apply(cached, axis=1)
    return df


def _event_key(event: str):
    if event.startswith("FTSE TW50 "):
        keys = json.loads(KEYS.read_text())
        v = keys[event.replace("FTSE TW50 ", "")]
        adds = [x["code"] for x in v["adds"]]
        dels = [x["code"] for x in v["dels"]]
        return v["ann_date"].replace("/", "-"), v["effective"], \
            adds, dels
    v = MSCI_TW[event]
    return v["ann_date"].replace("/", "-"), v["effective"], \
        v["adds"], v["dels"]


def ensure_window(event: str, pad_pre_days: int = 12) -> dict:
    """Backfill the event's window (quotes/shorts/foreign) if
    missing. Returns per-source cached-date counts."""
    from scripts.backfill_tw_history import backfill, load as hist
    ann, eff, _, _ = _event_key(event)
    d0 = (pd.Timestamp(ann) - pd.Timedelta(days=pad_pre_days)) \
        .strftime("%Y%m%d")
    d1 = (pd.Timestamp(eff) + pd.Timedelta(days=2)) \
        .strftime("%Y%m%d")
    out = {}
    for kind in ("quotes", "shorts", "foreign"):
        backfill(kind, d0, d1, max_days=40)
        out[kind] = len(hist(kind))
    return out


def event_panel(event: str) -> pd.DataFrame:
    """Full per-name/day factor panel for one event (same formulas
    as WINDOW_STUDY §0). Callers truncate via asof_panel."""
    from scripts.backfill_tw_history import load as hist
    quotes, shorts, foreign = hist("quotes"), hist("shorts"), \
        hist("foreign")
    ann, eff, adds, dels = _event_key(event)
    a, e = ann.replace("-", ""), eff.replace("-", "")
    qd = sorted(quotes)
    pre = [d for d in qd if d <= a][-5:]
    sess = [d for d in qd if a < d <= e]
    rows = []
    for side, lst in (("Buy", adds), ("Sell", dels)):
        for c in lst:
            if not pre or not quotes[pre[-1]].get(c):
                continue
            pc = quotes[pre[-1]][c]
            base = [quotes[d][c][0] for d in pre
                    if quotes[d].get(c) and quotes[d][c][0]]
            if not pc[2] or len(base) < 3:
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
                drift = (q[2] / pc[2] - 1) * 1e4
                rows.append({
                    "code": c, "side": side, "k": k,
                    "date": f"{d[:4]}-{d[4:6]}-{d[6:]}",
                    "close": q[2],
                    "drift_bps": round(drift, 1),
                    "fav_drift_bps": round(
                        drift if side == "Buy" else -drift, 1),
                    "t_mult": round(q[0] / base_v, 2)
                    if base_v else None,
                    "short_chg_pct": round(
                        ((sb[0] + sb[1]) / (s0[0] + s0[1]) - 1)
                        * 100, 1)
                    if sb and s0 and (s0[0] + s0[1]) else None,
                    "foreign_cum_x_adv": round(f_cum / base_v, 2)
                    if base_v else None})
    return pd.DataFrame(rows)


def asof_panel(panel: pd.DataFrame, asof: str) -> pd.DataFrame:
    """THE PIT GATE: rows strictly <= asof; nothing after survives."""
    return panel[panel["date"] <= asof].copy()


def asof_step2(panel: pd.DataFrame, asof: str,
               envelope_pct: float = 30.0) -> pd.DataFrame:
    """The Step-2 decision state ON the as-of day, per name:
    latest factor readings, the A+3 momentum gate (window-study
    rule), crowding-style band from the short build, and the
    resulting discretion decision with rationale."""
    from agents.event_window import discretion_decision
    p = asof_panel(panel, asof)
    out = []
    for code, g in p.groupby("code"):
        g = g.sort_values("k")
        last = g.iloc[-1]
        a3 = g[g["k"] <= 3]["fav_drift_bps"]
        a3sig = (float(a3.iloc[-1]) if len(a3) else None)
        sc = last["short_chg_pct"]
        band = ("HIGH" if sc is not None and sc >= 25 else
                "MED" if sc is not None and sc >= 5 else
                "LOW" if sc is not None else None)
        label = (f"{band} ({sc:+.0f}%/since-ann)"
                 if band else None)
        d = discretion_decision(last["side"], label, envelope_pct)
        # Session 9i: the A+3 momentum gate was formally REJECTED by
        # the variable lab (13 events, winrate 0.38 — the 6-event
        # impression did not survive). The column is retained as
        # DESCRIPTIVE context only and must not drive decisions;
        # cohort-relative momentum (H5, FTSE-only) is the surviving
        # form. See VARIABLE_LAB_LEADERBOARD.md.
        gate = ("descriptive: A+3 hot [H3 REJECTED — context only]"
                if a3sig is not None and a3sig > 0 and len(g) >= 3
                else "descriptive: A+3 cold [H3 REJECTED — context "
                "only]" if a3sig is not None and len(g) >= 3
                else "pre-A+3 — no signal yet")
        out.append({
            "code": code, "side": last["side"],
            "days_elapsed": int(last["k"]),
            "fav_drift_bps": last["fav_drift_bps"],
            "t_mult_today": last["t_mult"],
            "short_build": label or "no data",
            "A3_gate": gate,
            "crowding_decision": d["decision"],
            "rationale": d["rationale"]})
    return pd.DataFrame(out)
