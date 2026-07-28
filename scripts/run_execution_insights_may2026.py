#!/usr/bin/env python3
"""Step-4 execution-insights DEMO on the REAL May-2026 TW deletions
(session 8i). Real: crowding bands (short archive truncated to the
pre-announcement date — exactly what Step 2 would have seen), the
realized paths (ann->T drift, T-day move, T+1..T+5 reversal, T-day
volume multiple from yfinance). Hypothetical, labeled: fills and
pre-trade estimates (we did not execute; the TCA table demonstrates
the reconciliation mechanics).
Output: docs/case_studies/EXECUTION_INSIGHTS_DEMO_MAY2026.md
"""
import json
import sys
from pathlib import Path

import pandas as pd
import yfinance as yf

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from agents.event_window import discretion_decision            # noqa
from agents.execution_insights import (discretion_counterfactual,  # noqa
                                       render_debrief,
                                       reversal_grade,
                                       tca_vs_estimate,
                                       update_priors)
from agents.review_engine import crowding_reads                # noqa

DELS = ["2324.TW", "1504.TW", "2610.TW", "2474.TW", "1102.TW",
        "1402.TW", "2633.TW"]
ANN, EFF = "2026-05-12", "2026-05-29"          # announce / eff close


def truncated_cache(upto: str) -> dict:
    c = json.loads(Path("data/event_data_cache.json").read_text())
    return {"short": {d: v for d, v in c.get("short", {}).items()
                      if d <= upto}}


def realized_paths():
    rows = []
    for t in DELS:
        h = yf.Ticker(t).history(start="2026-04-20", end="2026-06-10",
                                 interval="1d")
        h.index = pd.to_datetime(h.index).tz_localize(None)
        c = h["Close"]

        def px(d):
            s = c[c.index <= pd.Timestamp(d)]
            return float(s.iloc[-1]) if len(s) else None
        ann_px, eff_px = px(ANN), px(EFF)
        prev = float(c[c.index < pd.Timestamp(EFF)].iloc[-1])
        post = px("2026-06-05")
        vol_t = float(h.loc[h.index == pd.Timestamp(EFF),
                            "Volume"].iloc[0])
        adv = float(h[h.index < pd.Timestamp(ANN)]["Volume"].mean())
        rows.append({
            "ticker": t,
            "drift_bps": (eff_px / ann_px - 1) * 1e4,
            "t_move_bps": (eff_px / prev - 1) * 1e4,
            "reversal_bps": (post / eff_px - 1) * 1e4,
            "t_mult": vol_t / adv if adv else None,
            "eff_close": eff_px})
    return pd.DataFrame(rows)


def main():
    crowd = crowding_reads(truncated_cache("20260512"),
                           DELS)          # pre-announcement read
    paths = realized_paths()
    # --- 4.4a discretion: what Step 2 would have decided, graded
    dec_rows = []
    for _, r in paths.iterrows():
        base = r["ticker"].split(".")[0]
        d = discretion_decision("Sell", crowd.get(base), 30.0)
        worked = 0.3 if d["decision"].startswith("WORK") else 0.0
        dec_rows.append({"ticker": r["ticker"], "side": "Sell",
                         "decision": d["decision"],
                         "worked_frac": worked,
                         "pre_close_drift_bps": r["drift_bps"]})
    cf = discretion_counterfactual(pd.DataFrame(dec_rows))
    # --- 4.4b reversal vs crowding band
    rev_rows = []
    for _, r in paths.iterrows():
        base = r["ticker"].split(".")[0]
        band = crowd.get(base, "NO DATA").split(" ")[0]
        rev_rows.append({"ticker": r["ticker"],
                         "crowding_band": band,
                         "t_move_bps": round(r["t_move_bps"], 0),
                         "post_reversal_bps": round(
                             r["reversal_bps"], 0)})
    rev = reversal_grade(pd.DataFrame(rev_rows))
    # --- 4.2 TCA (hypothetical fills, labeled)
    tca_rows = []
    for _, r in paths.iterrows():
        tca_rows.append({
            "ticker": r["ticker"], "side": "Sell",
            "qty_shares": 1_000_000,
            "avg_px": r["eff_close"] * (1 - 8e-4),   # DEMO: -8 bps
            "close_px": r["eff_close"],
            "est_cost_bps": 12.0})                   # DEMO estimate
    tca = tca_vs_estimate(pd.DataFrame(tca_rows))
    # --- 4.5 priors (in-memory copy — demo does NOT persist)
    cache = json.loads(Path("data/event_flow_study.json").read_text())
    realized = [{"provider": "MSCI", "side": "Sell",
                 "t_mult": round(float(r["t_mult"]), 1),
                 "auction_share": None,
                 "reversal_frac": round(abs(r["reversal_bps"])
                                        / abs(r["t_move_bps"]), 2)
                 if r["t_move_bps"] else None}
                for _, r in paths.iterrows()]
    priors = update_priors(dict(cache), realized)
    notes = (
        "REAL: crowding bands from the short archive truncated to "
        "May 12 (the pre-announcement read Step 2 would have had); "
        "drift/T-move/reversal/T-multiples from realized prices. "
        "HYPOTHETICAL, labeled: fills (uniform -8 bps vs close) and "
        "the 12 bps pre-trade estimate — we did not execute; the "
        "table demonstrates the reconciliation. auction_share=None "
        "for May names (outside the 60-day 5m window — the "
        "derivation runs live from Aug). Priors table is an "
        "in-memory copy; the real library updates only with graded "
        "events.")
    md = render_debrief(
        tca, cf, rev, priors,
        "Execution Insights — May-2026 TW Deletions (Step-4 DEMO)",
        "2026-07-28", notes=notes)
    out = Path("docs/case_studies/EXECUTION_INSIGHTS_DEMO_MAY2026.md")
    out.write_text(md, encoding="utf-8")
    print(f"debrief -> {out}")
    print(cf[["ticker", "decision", "cf_gain_bps", "verdict"]])
    print(rev[["ticker", "crowding_band", "grade"]])
    print("reversal hit rate:", rev.attrs.get("hit_rate"))


if __name__ == "__main__":
    main()
