#!/usr/bin/env python3
"""Aug-2026 MSCI QIR — FULL-ENGINE run on real caches (session 7y).
All eight layers via agents/review_engine.py. Output:
docs/case_studies/AUG2026_QIR_FULL_PACK.md
"""
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from agents.reconstitution import parse_msci_public_list      # noqa
from agents.review_engine import (render_review_markdown,      # noqa
                                  run_full_review)
from scripts.run_qir_aug2026 import FX, TW_ALIASES, UNIVERSES  # noqa

AS_OF = "2026-07-28"


def load_universe(market):
    cache = json.loads(Path("data/qir_universe_cache.json").read_text(encoding="utf-8"))
    fx = FX[market]
    rows = []
    for t, m in UNIVERSES[market]:
        c = cache.get(t, {})
        if "cap_usd" not in c:
            continue
        cap = c["cap_usd"] / fx
        rows.append(dict(ticker=t, full_mktcap_usd=cap,
                         free_float_frac=min(c["ff"], 1.0),
                         adv_usd=cap * 0.004, atvr=1.0,
                         member=c["member"]))
    return pd.DataFrame(rows)


def main():
    ledgers = [parse_msci_public_list(
        Path(f"data/msci_{p}_public_list.txt").read_text(encoding="utf-8"))
        for p in ("feb26", "may26")]
    short_cache = json.loads(
        Path("data/event_data_cache.json").read_text(encoding="utf-8"))
    event_cache = json.loads(
        Path("data/event_flow_study.json").read_text(encoding="utf-8"))

    tw_risk = pd.DataFrame([
        {"ticker": "3443.TW", "side": "Buy", "adv_days": 5.0,
         "band_pct": 10.0, "borrow_constrained": False},
        {"ticker": "3665.TW", "side": "Buy", "adv_days": 5.0,
         "band_pct": 10.0, "borrow_constrained": False},
        {"ticker": "8046.TW", "side": "Buy", "adv_days": 5.0,
         "band_pct": 10.0, "borrow_constrained": False},
        {"ticker": "4958.TW", "side": "Buy", "adv_days": 5.0,
         "band_pct": 10.0, "borrow_constrained": False},
    ])

    results = [
        run_full_review("Taiwan", load_universe("Taiwan"), TW_ALIASES,
                        ledgers, "TAIWAN", short_cache=short_cache,
                        event_cache=event_cache, names_risk=tw_risk),
        run_full_review("Korea", load_universe("Korea"), {},
                        ledgers, "KOREA", event_cache=event_cache),
        run_full_review("Japan", load_universe("Japan"), {},
                        ledgers, "JAPAN", event_cache=event_cache),
    ]

    notes = (
        "Flow estimates: passive-ownership-rate heuristic "
        "(5-9% of float cap, MSCI-linked trackers, EM stacking) — v1, "
        "validated against Sep-1 realized prints. ADV proxied at 0.4% "
        "of cap (overstates ADV-days for liquid AI names — direction "
        "disclosed). Korea/Japan alias maps pending -> their deletes "
        "carry UNVERIFIED probability; Japan candidates remain "
        "conditional WATCH per addendum 7w (Kioxia cap flag + "
        "membership unverified). Finalize + git-commit before Aug 11; "
        "grade after Sep 1 with the pre-declared criteria in "
        "QIR_AUG2026_PRERUN.md.")

    md = render_review_markdown(
        results, "MSCI Aug-2026 QIR (ann Aug 12, eff Sep 1)", AS_OF,
        ["China", "Hong Kong", "Singapore", "India", "Thailand",
         "Malaysia", "Indonesia", "Philippines"], notes=notes)
    out = Path("docs/case_studies/AUG2026_QIR_FULL_PACK.md")
    out.write_text(md, encoding="utf-8")
    print(f"pack -> {out}")
    for r in results:
        print(f"{r['market']}: {len(r['calls'])} calls "
              f"(expected hits {r['expected_hits']}), "
              f"{len(r['violations'])} ledger violations")


if __name__ == "__main__":
    main()
