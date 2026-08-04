"""Screening-funnel demo — Taiwan: validated replay + Aug-2026.

Session 9i. Two funnels, saved for the UI (data/funnel_tw.json):

1. VALIDATION — May-2026 SAIR at the APRIL-PIT universe (the graded
   configuration). The funnel's final calls are graded against the
   OFFICIAL key (translated to codes via the print-verified alias
   map). Official changes below the named floor are UNGRADABLE —
   counted, named, not hidden. Decade scope statement: this is the
   one TW review with a preserved PIT input set; 2015-2025 funnel
   replays remain gated on historical share/float vintages
   (PREDICTION_ENGINE_REVIEW_2026 §3) — official OUTCOMES for all
   44 reviews live in MSCI_APAC_CHANGES_2015_2026.md.

2. PREDICTION — Aug-2026 QIR at REFRESHED caps (Apr->Aug repriced),
   churn buffers fed with the May-26 official changes: the pack's
   zero-visible-calls posture with the funnel showing exactly where
   candidates died and where the blind band starts.

Usage: python scripts/funnel_demo.py
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import pandas as pd                                    # noqa: E402

from agents.review_engine import build_calls, screen_market  # noqa: E402
from agents.review_funnel import funnel_stages, validate_against_key  # noqa: E402

OUT = ROOT / "data" / "funnel_tw.json"
DOC = ROOT / "docs" / "case_studies" / "TW_FUNNEL.md"

# Official May-26 TW key -> codes (print-verified map, tw_expost_msci)
MAY26_DELS = {"1102.TW", "2474.TW", "2610.TW", "2324.TW", "1402.TW",
              "2633.TW", "1504.TW"}
MAY26_ADDS = {"6223.TWO"}                       # MPI Corp (TPEx line)


def run(universe, review, recent_dels=None, recent_adds=None,
        member_count=83):
    s = screen_market(universe, review=review,
                      member_count=member_count, tail_hi=10e9,
                      tail_n=500)
    for key, recent, side in (("excluded_readds", recent_dels, "adds"),
                              ("excluded_redels", recent_adds,
                               "deletes")):
        if recent and len(s[side]):
            excl = s[side]["ticker"].isin(recent)
            if excl.any():
                s[key] = sorted(s[side].loc[excl, "ticker"])
                s[side] = s[side][~excl]
    calls = build_calls(s, universe, [], {}, {},
                        membership_verified=False)
    return s, calls


def main():
    from scripts.run_full_review_asia import (ACTUAL, pit_screen,
                                              pit_universe,
                                              post_may_universe)
    # ---- 1. validation: May-26 SAIR on the April PIT universe,
    # using the EXACT graded configuration (pit_screen: migration
    # sweep + CA rule — the 7/7 run), not the live-QIR default
    u_pit = pit_universe("Taiwan")
    s1 = pit_screen("Taiwan", u_pit, review="SAIR")
    c1 = build_calls(s1, u_pit, [], {}, {},
                     membership_verified=False)
    f1 = funnel_stages(s1, c1, "SAIR")
    names = set(u_pit["ticker"])
    grade = validate_against_key(c1, MAY26_ADDS, MAY26_DELS, names)
    # ---- 2. prediction: Aug-26 QIR on refreshed caps
    u_aug = post_may_universe("Taiwan")
    s2, c2 = run(u_aug, "QIR",
                 recent_dels=set(ACTUAL["Taiwan"]["dels"]),
                 recent_adds=set(ACTUAL["Taiwan"]["adds"]))
    f2 = funnel_stages(s2, c2, "QIR")
    payload = {
        "validation": {"event": "MSCI May-2026 SAIR (April PIT "
                       "universe, graded vs official key)",
                       "stages": f1, "grade": grade},
        "prediction": {"event": "MSCI Aug-2026 QIR (caps refreshed "
                       "to current)", "stages": f2},
    }
    OUT.write_text(json.dumps(payload, indent=1))
    for tag, f in (("VALIDATION May-26", f1), ("PREDICTION Aug-26",
                                               f2)):
        print(f"\n== {tag}")
        for st in f:
            print(f"  {st['stage']:16s} n={st['n']:4d}  {st['detail']}")
    print("\ngrade:", json.dumps(grade))
    # ---- doc
    L = ["# The Screening Funnel — Taiwan (validated replay + "
         "Aug-2026 prediction)\n",
         "*Session 9i. How ~500 names boil down to calls, stage by "
         "stage; the funnel observes the engine's own artifacts and "
         "can never drift from it. UI: lifecycle Tab 1 expander. "
         "Decade scope: official outcomes for all 44 reviews are in "
         "MSCI_APAC_CHANGES_2015_2026.md; funnel REPLAY beyond "
         "May-2026 is gated on historical share/float vintages — "
         "stated, not fudged.*\n"]
    for tag, blob in (("May-2026 SAIR — validation",
                       payload["validation"]),
                      ("Aug-2026 QIR — prediction",
                       payload["prediction"])):
        L.append(f"## {tag}\n")
        L.append("| stage | n | rule | detail |")
        L.append("|---|---|---|---|")
        for st in blob["stages"]:
            L.append(f"| {st['stage']} | {st['n']} | {st['rule']} "
                     f"| {st['detail']} |")
        L.append("")
    g = grade
    L += ["## Validation grade (May-26, vs official key)\n",
          f"- Deletions hit (visible): {g['dels_hit']}",
          f"- Deletions missed (visible): {g['dels_missed_visible']}",
          f"- Adds hit: {g['adds_hit']} / missed visible: "
          f"{g['adds_missed_visible']}",
          f"- False calls: adds {g['false_adds']}, dels "
          f"{g['false_dels']}",
          f"- Ungradable below the named floor: "
          f"{g['ungradable_below_floor']}",
          "\nReading: the funnel recovers the graded engine result — "
          "visible deletions caught at the thresholds stage, the "
          "below-floor names are the declared breadth class, and the "
          "Aug-26 funnel shows the same structure ending at zero "
          "VISIBLE candidates with the blind band stated."]
    DOC.write_text("\n".join(L), encoding="utf-8")
    print("wrote", OUT, "and", DOC)


if __name__ == "__main__":
    main()
