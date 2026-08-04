"""Pre-announcement packs — May-2026 PIT backtest + Aug-2026 live.

Usage: python scripts/pre_announcement_demo.py
Writes docs/case_studies/PREANN_PACK_{MAY,AUG}2026_TW.md +
data/preann_tw.json (grades + headline fields for tests/UI).
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import pandas as pd                                    # noqa: E402

from agents.pre_announcement import (build_pack, grade_pack,  # noqa: E402
                                     render_pack_md)
from agents.review_engine import (build_calls, screen_market,  # noqa: E402
                                  shortlist_candidates)
from scripts.funnel_demo import MAY26_ADDS, MAY26_DELS  # noqa: E402


def tw_short_cache():
    d = json.loads(
        (ROOT / "data" / "event_data_cache.json").read_text())
    return {"short": d.get("short", {})}


def main():
    from scripts.run_full_review_asia import (ACTUAL, COUNT,
                                              pit_screen,
                                              pit_universe,
                                              post_may_universe)
    cache = tw_short_cache()
    out = {}

    # ---------- May-2026 BACKTEST (PIT: April universe, SAIR config,
    # crowding as-of 2026-05-11 — the day before announcement)
    u = pit_universe("Taiwan")
    s = pit_screen("Taiwan", u, review="SAIR")
    calls = build_calls(s, u, [], {}, {}, membership_verified=False)
    cand = calls[calls["call"] != "BLOCKED"][
        ["call", "ticker", "p_correct"]].rename(
        columns={"call": "side", "p_correct": "p"})
    cand["reasoning"] = "L8 engine call (PIT May config)"
    ev = {"name": "MSCI May-2026 SAIR TW", "ann": "2026-05-12",
          "eff": "2026-05-29", "review": "SAIR"}
    pack = build_pack(cand, u, ev, short_cache=cache,
                      crowd_asof="20260511")
    grade = grade_pack(pack, MAY26_ADDS, MAY26_DELS)
    md = render_pack_md(pack, "May-2026 TW (PIT BACKTEST)", grade)
    (ROOT / "docs" / "case_studies" /
     "PREANN_PACK_MAY2026_TW.md").write_text(md, encoding="utf-8")
    out["may"] = {"grade": grade,
                  "n_candidates": int(len(cand)),
                  "crowd_alerts": int(pack["crowding_watch"]
                                      ["alert"].sum())
                  if len(pack["crowding_watch"]) else 0}
    print("MAY grade:", json.dumps(grade))

    # ---------- Aug-2026 LIVE (refreshed caps, QIR, shortlist mode)
    u2 = post_may_universe("Taiwan")
    s2 = screen_market(u2, review="QIR", member_count=COUNT["Taiwan"],
                       tail_hi=10e9, tail_n=500)
    sl = shortlist_candidates(
        s2, u2, "QIR", "Taiwan",
        recent_deletions=set(ACTUAL["Taiwan"]["dels"]))
    ev2 = {"name": "MSCI Aug-2026 QIR TW", "ann": "2026-08-11",
           "eff": "2026-08-31", "review": "QIR"}
    pack2 = build_pack(sl, u2, ev2, short_cache=cache)
    md2 = render_pack_md(pack2, "Aug-2026 TW (LIVE, pre-announcement)")
    (ROOT / "docs" / "case_studies" /
     "PREANN_PACK_AUG2026_TW.md").write_text(md2, encoding="utf-8")
    w2 = pack2["crowding_watch"]
    out["aug"] = {"n_candidates": int(len(sl)),
                  "crowd_alerts": int(w2["alert"].sum())
                  if len(w2) else 0,
                  "crowd_asof": (w2["asof"].iloc[0]
                                 if len(w2) else None)}
    (ROOT / "data" / "preann_tw.json").write_text(
        json.dumps(out, indent=1, default=str))
    print("AUG:", json.dumps(out["aug"], default=str))
    print("packs written")


if __name__ == "__main__":
    main()
