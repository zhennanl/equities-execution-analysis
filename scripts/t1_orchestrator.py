"""T+1 unattended post-event orchestrator (c-40, STEP34 build #5).

The data-arrival gate + the pack, one command, zero attendance:
  1. ARRIVAL CHECK — refuses to grade on partial data: official
     T-day rows present for every name, IB/vintage T+1 closes
     available
  2. if ready and the pack is missing or older than its inputs:
     build_pack (incl. playbook strategy + archetype grading) +
     TCA letter drafts + one status line

Scheduled at T+1 08:00 the desk wakes up to a graded event or an
explicit list of what has not arrived — never a silent partial.

Usage: python scripts/t1_orchestrator.py may26
       python scripts/t1_orchestrator.py aug26   (after Sep-01)
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

EVENTS = {
    "may26": {"event": "MSCI 2026-05 SAIR TW", "provider": "MSCI",
              "ann": "2026-05-12", "t_day": "2026-05-29",
              "names": {c: "Sell" for c in
                        ["1102", "1402", "1504", "2324", "2474",
                         "2610", "2633"]}},
    # aug26 filled by the announcement-day agent after Aug-12
}


def arrival_check(cfg):
    from agents.post_event import _next_close_vintage, _stock_day
    missing = []
    for code in cfg["names"]:
        days = _stock_day(code)
        if not any(r[0] == cfg["t_day"] for r in days):
            missing.append(f"{code}: no official T-day row")
        elif not ([r for r in days if r[0] > cfg["t_day"]]
                  or _next_close_vintage(code, cfg["t_day"])):
            missing.append(f"{code}: no T+1 close yet")
    return missing


def main(tag):
    cfg = EVENTS.get(tag)
    if not cfg:
        print(f"[BLOCKED ] {tag}: no event config (announcement "
              "agent fills it post-announcement)")
        return 2
    missing = arrival_check(cfg)
    if missing:
        print(f"[WAITING ] {tag}: " + "; ".join(missing))
        return 1
    from agents.post_event import (build_pack, render_tca_letters)
    out = ROOT / "data" / f"post_event_{tag}.json"
    pack = build_pack(cfg["event"], cfg["provider"], cfg["ann"],
                      cfg["t_day"], cfg["names"], event_tag=tag)
    out.write_text(json.dumps(pack, indent=1), encoding="utf-8")
    (ROOT / "docs" / "case_studies" /
     f"TCA_LETTERS_{tag.upper()}_TW.md").write_text(
        render_tca_letters(pack), encoding="utf-8")
    graded = sum(1 for r in pack["names"] if "note" not in r)
    print(f"[GRADED  ] {tag}: {graded}/{len(pack['names'])} names "
          f"packed -> {out.name} + TCA drafts")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "may26"))
