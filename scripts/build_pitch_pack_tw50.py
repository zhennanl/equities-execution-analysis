#!/usr/bin/env python3
"""Real example: the pre-event pack CLSA could have sent on 2026-06-01
for the FTSE TW50 June review — built point-in-time from cached public
data, then VALIDATED against what actually happened.

Inputs (all already cached in repo):
  predictions  round-2 backtest calls (reconstruction-grade universe,
               disclosed) — FTSE_Taiwan50_Jun2026_backtest.md
  flows        Taiwan50_flow_simulation ($70B AUM lower bound)
  crowding     data/event_data_cache.json short ledger, dates < Jun 5
  T-multiples  data/event_flow_study.json, events effective < Jun 1
               (i.e. the May SAIR prints only — honest as-of gating)
Output: docs/case_studies/PITCH_PACK_TW50_Jun2026.md
"""
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from agents.pitch_pack import (build_pitch_pack, crowding_table,   # noqa
                               expected_t_multiples,
                               render_pitch_markdown,
                               render_validation_markdown, risk_flags,
                               validate_pack)

AS_OF, ANN, EFF = "2026-06-01", "2026-06-05", "2026-06-18"

# effective dates by label prefix (event_flow_study cache lacks eff)
EFF_BY_PREFIX = {"MSCI-TW": "2026-05-29", "MSCI-KR": "2026-05-29",
                 "TW50": "2026-06-18", "A50": "2026-06-19"}

# Round-2 model calls as-of late May (reconstruction-grade universe —
# disclosed in the pack notes). change: ADD/DELETE; NaN = watch only.
PREDICTIONS = pd.DataFrame([
    ("3443", "Global Unichip", "ADD", "HIGH", 78),
    ("3665", "BizLink", "ADD", "HIGH", 34),
    ("8046", "Nan Ya PCB", "ADD", "HIGH", 22),
    ("4958", "Zhen Ding", "ADD", "HIGH", 17),
    ("6919", "Compermed", "DELETE", "LOW", 8),
    ("2207", "Hotai", "DELETE", "LOW", 6),
    ("1101", "Taiwan Cement", "DELETE", "LOW", 4),
    ("1326", "FCFC", "DELETE", "LOW", 3),
    ("2615", "Wan Hai", "DELETE", "LOW", 2),
], columns=["ticker", "name", "change", "confidence", "margin_pct"])

# From the flow simulation (Taiwan50_flow_simulation.md, $70B AUM)
FLOWS = pd.DataFrame([
    ("3443", "Buy", 340, 7.3, "MULTI-DAY"),
    ("3665", "Buy", 310, 7.4, "MULTI-DAY"),
    ("8046", "Buy", 300, 7.2, "MULTI-DAY"),
    ("4958", "Buy", 330, 7.3, "MULTI-DAY"),
    ("6919", "Sell", 120, 7.8, "MULTI-DAY"),
    ("2207", "Sell", 350, 7.4, "MULTI-DAY"),
    ("2330", "Sell", 440, 0.08, "MOC"),
], columns=["ticker", "side", "flow_usd_m", "adv_days", "bucket"])

CANDIDATES = {
    "3443": "GUC (add candidate)", "3665": "BizLink (add candidate)",
    "8046": "NanYaPCB (add candidate)", "4958": "ZhenDing (add cand.)",
    "6919": "Compermed (del candidate)", "2207": "Hotai (del cand.)",
    "1101": "TaiwanCement (del candidate)", "1326": "FCFC (del cand.)",
    "2615": "WanHai (del candidate)",
    "2002": "China Steel (boundary watch)",
    "1301": "Formosa Plastics (boundary watch)",
}

NAMES_RISK = pd.DataFrame([
    {"ticker": "3443", "side": "Buy", "adv_days": 7.3, "band_pct": 10.0,
     "borrow_constrained": False},
    {"ticker": "6919", "side": "Sell", "adv_days": 7.8, "band_pct": 10.0,
     "borrow_constrained": True},
    {"ticker": "2207", "side": "Sell", "adv_days": 7.4, "band_pct": 10.0,
     "borrow_constrained": False},
    {"ticker": "2330", "side": "Sell", "adv_days": 0.08,
     "band_pct": 10.0, "borrow_constrained": False},
])

NOTES = (
    "Universe is reconstruction-grade (public caps/floats, +-30%) — a "
    "desk build replaces it with vendor cap files. Rank-boundary "
    "deletion calls are structurally LOW-confidence (measured by Monte "
    "Carlo, see track record) and shipped as a WATCH ZONE, not a "
    "signal: the boundary names 2002/1301 sit in the zone our model "
    "cannot rank reliably — and the short ledger (section 4) shows the "
    "street positioned for 2002 regardless of any model. TSMC reweight "
    "trim (-$440M) is the second-largest flow of the event and costs "
    "nothing to execute (0.08 ADV-days, MOC).")


def main():
    event_cache = json.load(open("data/event_flow_study.json"))
    for label, ev in event_cache.items():
        if isinstance(ev, dict):
            for pref, eff in EFF_BY_PREFIX.items():
                if label.startswith(pref):
                    ev.setdefault("eff", eff)
    short_cache = json.load(open("data/event_data_cache.json"))

    t_stats = {
        "MSCI deletions (Sell)": expected_t_multiples(
            event_cache, "MSCI", "Sell", as_of=AS_OF),
        "FTSE deletions (Sell)": expected_t_multiples(
            event_cache, "FTSE", "Sell", as_of=AS_OF),
        "FTSE additions (Buy)": expected_t_multiples(
            event_cache, "FTSE", "Buy", as_of=AS_OF),
    }
    crowd = crowding_table(short_cache, CANDIDATES, ANN, AS_OF)
    flags = risk_flags(NAMES_RISK)

    pack = build_pitch_pack(
        "FTSE TWSE Taiwan 50 — June 2026 review", ANN, EFF, AS_OF,
        PREDICTIONS, FLOWS, crowd, t_stats, flags, NOTES)
    md = render_pitch_markdown(pack)

    # ---- validation vs the actual outcome (known today) ----
    outcomes = pd.DataFrame([
        ("3443", True), ("3665", True), ("8046", True), ("4958", True),
        ("6919", True), ("2207", True), ("2002", True), ("1301", True),
        ("1101", False), ("1326", False), ("2615", False),
    ], columns=["ticker", "actual_change"])
    realized = {"FTSE deletions (Sell)": 5.0,
                "FTSE additions (Buy)": 5.2}
    score = validate_pack(pack, outcomes, realized)
    md += "\n\n---\n\n" + render_validation_markdown(score)

    out = Path("docs/case_studies/PITCH_PACK_TW50_Jun2026.md")
    out.write_text(md, encoding="utf-8")
    print(f"pack -> {out}")
    print(json.dumps({k: v for k, v in score.items()}, indent=1,
                     default=str))


if __name__ == "__main__":
    main()
