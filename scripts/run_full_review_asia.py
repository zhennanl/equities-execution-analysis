#!/usr/bin/env python3
"""Aug-2026 MSCI QIR — FULL 8-LAYER ENGINE, ALL COVERED ASIA MARKETS
(session 8e). Universes = the PIT-May-graded boundary sets with
membership rolled FORWARD by the official May changes; caps from the
PIT cache (April vintage — REFRESH AT AUG-11 FINALIZATION, disclosed).
Count-anchored tails + A-share inclusion factor + CA rule, exactly the
configuration that scored 69% on the May replication.
Output: docs/case_studies/AUG2026_QIR_ASIA_PACK.md
"""
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from agents.reconstitution import parse_msci_public_list      # noqa
from agents.review_engine import (crowding_reads,              # noqa
                                  render_review_markdown,
                                  run_full_review)
from scripts.pit_may2026_asia import ACTUAL, FX, UNIVERSES     # noqa
from scripts.run_qir_aug2026 import TW_ALIASES                 # noqa

COUNT = {"Taiwan": 77, "Japan": 189, "China": 578, "India": 156,
         "Korea": 87, "HongKong": 29, "Malaysia": 26,
         "Indonesia": 14}          # post-May counts (pre-May +- May)
RANGE = {"Japan": (20e9, 900), "China": (15e9, 1100),
         "India": (12e9, 700), "Korea": (10e9, 500),
         "Taiwan": (10e9, 500), "HongKong": (12e9, 400),
         "Malaysia": (6e9, 300), "Indonesia": (6e9, 300)}


def post_may_universe(mkt):
    cache = json.loads(
        Path("data/pit_may26_asia_cache.json").read_text())
    act = ACTUAL[mkt]
    rows = []
    for t, mem_pre in UNIVERSES[mkt]:
        c = cache.get(t, {})
        if "cap_pit" not in c:
            continue
        # roll membership FORWARD: May deletions out, May adds in
        mem = mem_pre
        if t in act["dels"]:
            mem = 0
        if t in act["adds"]:
            mem = 1
        capfx = 1.0 if t == "YMM" else FX[mkt]
        cap = c["cap_pit"] / capfx
        ff = min(c.get("ff", 0.7), 1.0)
        if mkt == "China" and mem == 1 and (t.endswith(".SS") or
                                            t.endswith(".SZ")):
            ff *= 0.2                     # inclusion factor (members)
        adv = (c.get("adv_loc") / capfx if c.get("adv_loc")
               else cap * 0.004)
        atvr = min((adv * 250 / (cap * ff)) if cap * ff else 1.0, 5.0)
        rows.append(dict(ticker=t, full_mktcap_usd=cap,
                         free_float_frac=ff, adv_usd=adv, atvr=atvr,
                         member=mem))
    return pd.DataFrame(rows)


def merge_short_caches(*caches):
    """Union the normalized {short: {date: {code: [..]}}} caches
    (e.g., TWSE listed + TPEx OTC for Taiwan)."""
    out = {"short": {}}
    for c in caches:
        if not c:
            continue
        for date, day in c.get("short", {}).items():
            out["short"].setdefault(date, {}).update(day)
    return out


def market_short_caches():
    """Per-market crowding caches — LIVE sources only, honest gaps
    elsewhere (see event_data.CROWDING_SOURCES). China gets the SFC HK
    file: its H-lines carry HK codes; A-lines stay uncovered."""
    tw_native = json.loads(
        Path("data/event_data_cache.json").read_text())
    asia = {}
    p = Path("data/crowding_asia_cache.json")
    if p.exists():
        asia = json.loads(p.read_text())
    hk = asia.get("HongKong")
    return {"Taiwan": merge_short_caches(tw_native,
                                         asia.get("TaiwanOTC")),
            "Japan": asia.get("Japan"),
            "HongKong": hk,
            "China": hk}


def crowding_demo(results, caches):
    """Live multi-market demonstration: crowding reads on the 4
    members nearest the delete floor + 4 nonmembers nearest the add
    hurdle per market — proves the layer runs wherever a LIVE source
    exists, and says 'no data' where it doesn't."""
    lines = ["", "## Appendix — multi-market crowding coverage "
                 "(live reads, boundary names)", ""]
    from agents.event_data import CROWDING_SOURCES
    for r in results:
        mkt = r["market"]
        src = CROWDING_SOURCES.get(mkt, {})
        lines.append(f"**{mkt}** — {src.get('status', '?')} "
                     f"({src.get('cadence', '-')}): "
                     f"{src.get('source', '')}")
        cache = caches.get(mkt)
        u = r["universe_df"]
        real = u[~u["ticker"].str.startswith("TAIL")]
        mem = real[real["member"] == 1].nsmallest(
            4, "full_mktcap_usd")["ticker"].tolist()
        non = real[real["member"] == 0].nlargest(
            4, "full_mktcap_usd")["ticker"].tolist()
        reads = crowding_reads(cache, mem + non)
        if reads:
            for t in mem + non:
                b = t.split(".")[0]
                if b in reads:
                    side = "member" if t in mem else "non-member"
                    lines.append(f"- {t} ({side}, boundary): "
                                 f"{reads[b]}")
        else:
            lines.append("- no data from sandbox (see status above)")
        lines.append("")
    return "\n".join(lines)


def main():
    ledgers = [parse_msci_public_list(
        Path(f"data/msci_{p}_public_list.txt").read_text())
        for p in ("feb26", "may26")]
    caches = market_short_caches()
    event_cache = json.loads(
        Path("data/event_flow_study.json").read_text())
    LEDGER_COUNTRY = {"Taiwan": "TAIWAN", "Japan": "JAPAN",
                      "Korea": "KOREA", "China": "CHINA",
                      "India": "INDIA", "Malaysia": "MALAYSIA",
                      "Indonesia": "INDONESIA",
                      "HongKong": "HONG KONG"}
    results, universes = [], {}
    for mkt in ("Taiwan", "Japan", "Korea", "China", "India",
                "Malaysia", "Indonesia", "HongKong"):
        u = post_may_universe(mkt)
        universes[mkt] = u
        hi, n = RANGE[mkt]
        r = run_full_review(
            mkt, u, TW_ALIASES if mkt == "Taiwan" else {},
            ledgers, LEDGER_COUNTRY[mkt],
            short_cache=caches.get(mkt),
            event_cache=event_cache,
            member_count=COUNT[mkt],
            a_share_tail_mix=(mkt == "China"),
            tail_hi=hi, tail_n=n,
            recent_deletions=set(ACTUAL[mkt]["dels"]),
            recent_additions=set(ACTUAL[mkt]["adds"]))
        r["universe_df"] = u
        results.append(r)

    notes = (
        "Configuration = the May-replication-graded setup (69% of all "
        "98 actual May changes at PIT; adds 17/17 zero false "
        "positives). Caps are APRIL vintage from the PIT cache — "
        "MANDATORY refresh at Aug-11 finalization along with the "
        "membership cross-check. Deletion calls are a probability-"
        "ranked watch zone (May-measured: delete precision 82% / "
        "recall 89%; cutline residents ~45-60%). Crowding now "
        "MULTI-MARKET (session 8g): Taiwan TWSE+TPEx daily, Japan JPX "
        "daily disclosed shorts, HK + China-H via SFC weekly CSV; "
        "KR/MY PROTOCOL (login/403 from sandbox), IN/ID structural — "
        "see appendix. KR/JP/other alias maps pending -> unverified "
        "discounts apply. FIF-cut deletions (Indonesia-class) and "
        "H-line share splits are DISCLOSED blind spots pending HKEX "
        "per-line shares + holdings baselines. SG/TH/PH remain "
        "NO-CALL (no validated universe).")
    md = render_review_markdown(
        results, "MSCI Aug-2026 QIR — ALL COVERED ASIA (ann Aug 12, "
        "eff Sep 1)", "2026-07-28",
        ["Singapore", "Thailand", "Philippines"], notes=notes)
    md += crowding_demo(results, caches)
    out = Path("docs/case_studies/AUG2026_QIR_ASIA_PACK.md")
    out.write_text(md, encoding="utf-8")
    print(f"pack -> {out}")
    for r in results:
        live = r["calls"][r["calls"]["call"] != "BLOCKED"] \
            if len(r["calls"]) else r["calls"]
        print(f"{r['market']:10s} calls {len(live)} "
              f"(exp {r['expected_hits']}) "
              f"violations {len(r['violations'])}")


if __name__ == "__main__":
    main()
