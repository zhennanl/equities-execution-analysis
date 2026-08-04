"""Screening funnel — universe -> conditions -> final candidates.

Session 9i. Decomposes one review screen into the stage-by-stage
funnel a trader can SEE: how ~500 names boil down to a handful of
calls, with every elimination tied to its rule (the same L0-L4
logic as the engine — this file only OBSERVES, it never re-decides).

Stages:
  S0 universe        real named stocks + count-anchored tail
  S1 eligibility     float >= 0.15 AND ATVR floor (L1)
  S2 GMSR ladder     85% coverage walk -> GMSR + thresholds (L2-L3)
  S3 threshold test  non-members >= add bar / members < 0.5x floor
  S4 churn buffers   prior review's changes excluded (L5)
  S5 verification    Feng Tay gate: blocked calls (L7)
  FINAL              committed calls with probabilities (L8)

`funnel_stages` consumes the artifacts of an actual engine run so
the funnel can never drift from the engine.
"""
from __future__ import annotations

import pandas as pd


def funnel_stages(screen: dict, calls: pd.DataFrame,
                  review: str) -> list[dict]:
    from agents.reconstitution import MSCIRules, _screens
    u = screen["assembled"].copy()
    rules = MSCIRules(review=review)
    u["eligible"] = _screens(u, rules.min_float, rules.min_atvr)
    if "is_member" not in u.columns:
        u["is_member"] = u["member"].astype(bool)
    real = u[~u["ticker"].str.startswith("TAIL")]
    n_real, n_tail = len(real), len(u) - len(real)
    elig = u[u["eligible"]]
    inelig = real[~real["eligible"]]
    gmsr, add_thr = screen["gmsr"], screen["add_thr"]
    del_thr = 0.5 * gmsr
    add_cand = screen["adds"]
    del_cand = screen["deletes"]
    watch = screen["watch"]
    readds = screen.get("excluded_readds", [])
    redels = screen.get("excluded_redels", [])
    n_cand = len(add_cand) + len(del_cand)
    if len(calls):
        blocked = calls[calls["call"] == "BLOCKED"]
        live = calls[calls["call"] != "BLOCKED"]
    else:
        blocked = live = calls
    stages = [
        {"stage": "S0 universe", "n": len(u),
         "rule": "count-anchored: real named stocks + synthetic tail "
                 "pinned to the published constituent count (L0)",
         "detail": f"{n_real} real named + {n_tail} tail; "
                   f"{int(u['is_member'].sum())} members"},
        {"stage": "S1 eligible", "n": len(elig),
         "rule": "free float >= 0.15 AND ATVR liquidity floor (L1)",
         "detail": f"eliminated {len(u) - len(elig)}"
                   + (f"; ineligible real names: "
                      f"{', '.join(inelig['ticker'].head(6))}"
                      if len(inelig) else "")},
        {"stage": "S2 thresholds", "n": len(elig),
         "rule": "ladder to 85% coverage -> GMSR; add bar = "
                 f"{'1.8x (QIR)' if review == 'QIR' else '1.15x'}; "
                 "deletion floor = 0.5x (L2-L3)",
         "detail": f"GMSR ${gmsr/1e9:.1f}B | add >= "
                   f"${add_thr/1e9:.1f}B | floor ${del_thr/1e9:.1f}B"},
        {"stage": "S3 candidates", "n": n_cand,
         "rule": "non-members above the add bar; members below the "
                 "floor or failing screens (L3-L4)",
         "detail": f"{len(add_cand)} add / {len(del_cand)} delete; "
                   f"{len(watch)} in the ±15% watch band"},
        {"stage": "S4 churn-buffered", "n": n_cand - len(readds)
         - len(redels),
         "rule": "prior review's changes excluded from opposite-side "
                 "candidacy (L5)",
         "detail": (f"excluded re-adds {readds}, re-dels {redels}"
                    if readds or redels else "nothing to exclude")},
        {"stage": "S5 verified", "n": len(live),
         "rule": "no call ships on unverified membership — the "
                 "Feng Tay gate (L7)",
         "detail": f"{len(blocked)} blocked"
                   + (": " + ", ".join(blocked["ticker"])
                      if len(blocked) else "")},
        {"stage": "FINAL calls", "n": len(live),
         "rule": "Laplace-shrunk probabilities from the graded "
                 "record (L8)",
         "detail": ("; ".join(f"{r['call']} {r['ticker']} "
                              f"p={r['p_correct']}"
                              for _, r in live.iterrows())
                    if len(live) else
                    "0 calls at the OBSERVABLE margin — blind band "
                    "below the named floor is declared, not denied")},
    ]
    for s in stages:
        s["n"] = int(s["n"])
    return stages


def validate_against_key(stages_final: pd.DataFrame,
                         official_adds: set, official_dels: set,
                         universe_names: set) -> dict:
    """Grade a funnel's final calls against an official key. Names
    outside the universe are UNGRADABLE (breadth class), counted
    separately — the funnel is graded only on what it could see."""
    calls_a = set(stages_final.loc[stages_final["call"] == "ADD",
                                   "ticker"])
    calls_d = set(stages_final.loc[stages_final["call"] == "DELETE",
                                   "ticker"])
    vis_a = official_adds & universe_names
    vis_d = official_dels & universe_names
    return {
        "adds_hit": sorted(calls_a & vis_a),
        "adds_missed_visible": sorted(vis_a - calls_a),
        "dels_hit": sorted(calls_d & vis_d),
        "dels_missed_visible": sorted(vis_d - calls_d),
        "false_adds": sorted(calls_a - official_adds),
        "false_dels": sorted(calls_d - official_dels),
        "ungradable_below_floor": sorted(
            (official_adds | official_dels) - universe_names)}
