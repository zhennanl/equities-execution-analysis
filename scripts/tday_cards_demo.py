"""Generate T-day forecast cards for the Aug-2026 TW shortlist.

Usage: python scripts/tday_cards_demo.py
Writes docs/case_studies/TDAY_CARDS_AUG2026_TW.md + data/tday_cards_
aug26.json (UI).
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from agents.review_engine import (crowding_reads, screen_market,  # noqa: E402
                                  shortlist_candidates)
from agents.tday_cards import build_cards, render_cards_md  # noqa: E402

DOC = ROOT / "docs" / "case_studies" / "TDAY_CARDS_AUG2026_TW.md"
OUT = ROOT / "data" / "tday_cards_aug26.json"


def main():
    from scripts.run_full_review_asia import (ACTUAL, COUNT,
                                              market_short_caches,
                                              post_may_universe)
    u = post_may_universe("Taiwan")
    s = screen_market(u, review="QIR", member_count=COUNT["Taiwan"],
                      tail_hi=10e9, tail_n=500)
    sl = shortlist_candidates(
        s, u, "QIR", "Taiwan",
        recent_deletions=set(ACTUAL["Taiwan"]["dels"]))
    codes = [t.split(".")[0] for t in sl["ticker"]
             if not t.startswith("BELOW")]
    try:
        crowd = crowding_reads(
            market_short_caches().get("Taiwan"), codes)
    except Exception:                                  # noqa: BLE001
        crowd = {}
    cards = build_cards(sl, u, crowding_map=crowd)
    md = render_cards_md(cards, "MSCI Aug-2026 QIR Taiwan shortlist "
                         "(ann Aug-11/12, print Aug-31)",
                         "2026-08-04")
    DOC.write_text(md, encoding="utf-8")
    OUT.write_text(json.dumps(
        {"event": "MSCI Aug-2026 QIR Taiwan", "cards": cards},
        indent=1, default=str))
    print(f"{len(cards)} cards -> {DOC}")
    for c in cards:
        if "note" in c:
            print(f"  {c['side']:6s} {c['ticker']:28s} "
                  f"p={c['p_convert']}")
        else:
            print(f"  {c['side']:6s} {c['ticker']:10s} "
                  f"p={c['p_convert']:.3f} flow "
                  f"${c['flow_if_converts_usd_m'][0]}-"
                  f"{c['flow_if_converts_usd_m'][1]}M "
                  f"{c['bucket']}")


if __name__ == "__main__":
    main()
