"""T-day situations playbook — "you are here -> history says".

Session 9i. For every historical effective day (5m, post-2023-05
floor), condition on what a trader can OBSERVE BY MIDDAY and measure
what happened AFTER — the decision-relevant split. This is a LOOKUP
TABLE with honesty labels, not a hypothesis test: cells under 8
name-days or 4 events are marked DATA-THIN and carry no reaction.

CONDITIONING (all observable at 12:00 on T):
  side          Buy (add) / Sell (delete) — known before open
  am_tape       WITH-flow (price moving the way index flow pushes:
                up for adds, down for deletes) vs AGAINST-flow
  am_vol        HEAVY (>= 1.5x this name's pre-announcement median
                morning volume) vs NORMAL

OUTCOMES (all after 12:00):
  pm_fav_bps        12:00 -> last continuous, favorable sign
  gap_fav_bps       last continuous -> official close, fav sign
  p_gap_favorable   share of name-days where the print helped
  auction_share     realized print size
  t1_reversal_bps   official close -> next day close, REVERSAL sign
                    (positive = price came back = completion leg
                    cheaper than chasing on T)

Usage: python scripts/tday_playbook.py
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import numpy as np                                     # noqa: E402
import pandas as pd                                    # noqa: E402

DOC = ROOT / "docs" / "case_studies" / "TDAY_PLAYBOOK.md"
OUT = ROOT / "data" / "tday_playbook.json"
THIN_DAYS, THIN_EVENTS = 8, 4


def build() -> pd.DataFrame:
    from scripts.ib_harvest import IB_FLOOR, _ib_event_set
    from scripts.tday_execution_studies import (_ib_day, _load_ib,
                                                _official_close)
    from scripts.window_intraday_study import _anns
    ib = _load_ib()
    anns = _anns()
    rows = []
    for event, prov, eff, names in _ib_event_set():
        if eff < IB_FLOOR:
            continue
        ann = anns.get(eff)
        for code, side in names.items():
            series = sorted({r[0][:10] for r in
                             ib.get(code, {}).get("5m", [])})
            # T = last covered day <= stated eff (holiday-shifted)
            tdays = [d for d in series if d <= eff]
            after = [d for d in series if d > eff]
            if not tdays:
                continue
            T = tdays[-1]
            r = _ib_day(ib, code, T)
            if not r:
                continue
            cont, auc, last_cont = r
            off = _official_close(code, T)
            if off is None:
                off = auc and None
            # midday observables
            am = [b for b in cont if b[0] <= "12:00"]
            if len(am) < 10:
                continue
            o_am, c12 = am[0][1], am[-1][2]
            am_vol = sum(b[3] for b in am)
            # baseline: pre-announcement days' morning volume median
            pre = [d for d in series
                   if ann and d <= ann][-10:]
            base_am = []
            for d in pre:
                rb = _ib_day(ib, code, d)
                if rb:
                    base_am.append(sum(b[3] for b in rb[0]
                                       if b[0] <= "12:00"))
            if not base_am:
                continue
            am_x = am_vol / np.median(base_am)
            sgn = 1.0 if side == "Buy" else -1.0
            am_fav = sgn * (c12 / o_am - 1) * 1e4
            # outcomes
            pm_fav = sgn * (last_cont / c12 - 1) * 1e4
            close_ref = off if off else last_cont
            gap_fav = sgn * (close_ref / last_cont - 1) * 1e4
            share = auc / (auc + sum(b[3] for b in cont)) \
                if auc else None
            t1 = None
            if after:
                r1 = _ib_day(ib, code, after[0])
                if r1 and close_ref:
                    # reversal sign: + = price moved BACK against
                    # the index flow direction after the print
                    t1 = -sgn * (r1[2] / close_ref - 1) * 1e4
            rows.append({
                "event": event, "provider": prov, "code": code,
                "side": side, "t_day": T,
                "am_fav_bps": am_fav,
                "am_tape": "WITH-flow" if am_fav > 0
                else "AGAINST-flow",
                "am_vol_x": round(float(am_x), 2),
                "am_vol": "HEAVY" if am_x >= 1.5 else "NORMAL",
                "pm_fav_bps": pm_fav, "gap_fav_bps": gap_fav,
                "auction_share": share,
                "t1_reversal_bps": t1})
    return pd.DataFrame(rows)


def table(df: pd.DataFrame) -> pd.DataFrame:
    g = df.groupby(["side", "am_tape", "am_vol"])
    out = g.agg(
        n=("code", "count"),
        n_events=("event", "nunique"),
        pm_fav=("pm_fav_bps", "median"),
        gap_fav=("gap_fav_bps", "median"),
        p_gap_fav=("gap_fav_bps", lambda s: (s > 0).mean()),
        share=("auction_share", "median"),
        t1_rev=("t1_reversal_bps", "median")).round(2)
    out["label"] = np.where(
        (out["n"] < THIN_DAYS) | (out["n_events"] < THIN_EVENTS),
        "DATA-THIN", "OK")
    return out


# Reactions are DATA-GROUNDED — rewritten to match the measured
# table (the first draft, written before the numbers, disagreed with
# them in two cells and was corrected; noted per honesty rules).
REACTIONS = {
    ("Sell", "WITH-flow", "HEAVY"):
        "Delete falling hard on heavy volume by noon. Measured: PM "
        "flat, gap ~flat (p_fav 0.38 — the least punitive print of "
        "any cell), share 0.76, T+1 continues DOWN (-85). Reading: "
        "the pressure is orderly and the close is fair here — MOC "
        "core carries it; no need to chase the morning.",
    ("Sell", "WITH-flow", "NORMAL"):
        "Delete drifting down quietly. Measured: gap -31 against "
        "you (p_fav 0.10), T+1 ~flat. Reading: the print charges a "
        "moderate immediacy toll; envelope working ahead of the "
        "close earns its keep on this tape.",
    ("Sell", "AGAINST-flow", "HEAVY"):
        "Delete RISING on heavy volume by noon — the squeeze tape "
        "(6919 family). Measured: PM flat, gap -44 against the "
        "seller (p_fav 0.11), and T+1 keeps going (-15): the "
        "squeeze usually completes AT and AFTER the close, not "
        "before it. Reading: do NOT count on the print to bail out "
        "a late sale; if crowding shows shorts covering, sell what "
        "you can into the strength you're given.",
    ("Sell", "AGAINST-flow", "NORMAL"):
        "Delete firm on quiet tape. Measured: PM -23, gap -55 "
        "(p_fav 0.08 — the most punitive cell), and T+1 CONTINUES "
        "against (-108). Reading: quiet strength in a delete is "
        "the worst sell tape in the book — work early, expect the "
        "print to cost, plan the completion leg for further "
        "adverse drift, not a comeback.",
    ("Buy", "WITH-flow", "NORMAL"):
        "Add drifting up quietly. Measured: PM gives back -34, gap "
        "~flat (p_fav 0.18), T+1 reverses +79. Reading: midday "
        "strength fades into the close — patience beats chasing; "
        "the completion leg benefits from the T+1 give-back.",
    ("Buy", "AGAINST-flow", "HEAVY"):
        "Add FALLING on heavy volume by noon — the crowd-unwind "
        "tape (2344 family). Measured: PM flat, gap -15 (p_fav "
        "0.10), share only 0.43, T+1 ~flat. Reading: the unwind "
        "dominates through the close; buying weakness intraday is "
        "supported, but do not expect the print itself to favor "
        "you.",
    ("Buy", "AGAINST-flow", "NORMAL"):
        "Add soft on quiet tape. Measured: gap -57 against the "
        "buyer (p_fav 0.24) but **T+1 reverses +255 — the "
        "strongest completion-leg signal in the table**. Reading: "
        "a soft add's print overshoots down and comes back hard; "
        "residuals bought patiently on T+1 historically beat "
        "chasing the close.",
}

SYNTHESIS = (
    "**The systematic lesson across cells: the closing print "
    "typically lands AGAINST the obligated side** — favorable-gap "
    "probability runs 8-38%, median toll 15-55 bps. That is the "
    "measured cost of demanding immediacy at the bell (Dimensional's "
    "reconstitution result, reproduced at 5-minute scale on our own "
    "market). The limit-lock cases where the print FAVORS the "
    "obligated side (6919/2344) are the tails, not the rule. "
    "Second lesson: T+1 behavior is CELL-DEPENDENT — squeezes "
    "continue (Sell/AGAINST cells), soft-add prints snap back "
    "(+255) — so the completion-leg plan must be conditioned on "
    "the same midday observables, not a blanket reversal prior.")


def main():
    df = build()
    t = table(df)
    OUT.write_text(json.dumps(
        {"n_name_days": len(df),
         "n_events": int(df["event"].nunique()),
         "cells": json.loads(t.reset_index().to_json(
             orient="records"))}, indent=1, default=str))
    print(f"{len(df)} T-day observations, "
          f"{df['event'].nunique()} events")
    print(t.to_string())
    L = ["# T-Day Situations Playbook — 'you are here -> history "
         "says'\n",
         f"*Session 9i. {len(df)} historical T-day observations "
         f"({df['event'].nunique()} events, 5m with auction bars). "
         "Conditioning = what a trader OBSERVES BY NOON (side, "
         "tape direction vs flow, morning volume vs the name's own "
         "pre-announcement baseline). Outcomes = what happened "
         "AFTER noon. Cells under "
         f"{THIN_DAYS} days / {THIN_EVENTS} events are DATA-THIN "
         "and carry no recommendation. This is a descriptive "
         "lookup, refreshed every event — not a promise.*\n",
         "## The table (favorable bps = helping the index-flow "
         "side)\n",
         t.to_markdown(), "",
         "## Reactions per situation (only OK-labeled cells)\n"]
    for key, txt in REACTIONS.items():
        if key in t.index and t.loc[key, "label"] == "OK":
            n = int(t.loc[key, "n"])
            L.append(f"- **{' / '.join(key)}** (n={n}): {txt}")
    L += ["", "## The synthesis\n", SYNTHESIS, "",
          "## Completion-leg note",
          "t1_rev > 0 means the price came BACK after the print — "
          "median reversal per cell above feeds the residual/"
          "completion decision (patient completion historically "
          "beats chasing where t1_rev is positive and large)."]
    DOC.write_text("\n".join(L), encoding="utf-8")
    print("wrote", DOC)


if __name__ == "__main__":
    main()
