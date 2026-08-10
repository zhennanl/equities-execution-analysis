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


def cap_refresh():
    """Session 9i: Apr-30 -> current price ratios per ticker
    (scripts/refresh_aug_caps.py). Empty dict = no refresh file."""
    p = Path("data/aug26_cap_refresh.json")
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def post_may_universe(mkt):
    cache = json.loads(
        Path("data/pit_may26_asia_cache.json").read_text(encoding="utf-8"))
    ratios = cap_refresh()
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
        # session 9i: current-price refresh (PIT replay path below
        # deliberately does NOT get this — it must stay April-frozen)
        cap = c["cap_pit"] / capfx * ratios.get(t, 1.0)
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


# PRE-May constituent counts (published factsheets, knowable at the
# time) — the PIT replay's count anchors.
PRE_COUNT = {"Taiwan": 83, "Japan": 200, "China": 580, "India": 155,
             "Korea": 90, "HongKong": 30, "Malaysia": 32,
             "Indonesia": 20}


def pit_universe(mkt):
    """POINT-IN-TIME vintage for the May-2026 replay: Apr-30 caps
    (historical prices) and PRE-May membership. No information from
    after the announcement enters this frame."""
    cache = json.loads(
        Path("data/pit_may26_asia_cache.json").read_text(encoding="utf-8"))
    rows = []
    for t, mem in UNIVERSES[mkt]:
        c = cache.get(t, {})
        if "cap_pit" not in c:
            continue
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


# PIT harness tail ranges (lo, hi, n) — copied from the graded
# report() configuration.
PIT_RANGE = {"Japan": (0.5e9, 20e9, 900), "China": (0.3e9, 15e9, 1100),
             "India": (0.3e9, 12e9, 700), "Korea": (0.3e9, 10e9, 500),
             "Taiwan": (0.3e9, 10e9, 500),
             "HongKong": (0.5e9, 12e9, 400),
             "Malaysia": (0.2e9, 6e9, 300),
             "Indonesia": (0.2e9, 6e9, 300)}


def pit_screen(mkt, u, buffer=0.02, review="SAIR"):
    """The EXACT graded May-replication screen (69% of all 98):
    count-anchored synthetic tails + predict_msci with the country-
    segment MIGRATION deletion rule + the corporate-action rule.
    Returns a screen dict consumable by review_engine.build_calls."""
    import numpy as np
    from agents.reconstitution import MSCIRules, predict_msci
    from scripts.pit_may2026_asia import CA_DELETIONS
    lo, hi, n = PIT_RANGE.get(mkt, (0.3e9, 8e9, 400))
    rng = np.random.default_rng(11)
    caps = np.sort(np.exp(rng.uniform(np.log(lo), np.log(hi),
                                      n)))[::-1]
    n_tail_mem = max(PRE_COUNT.get(mkt, 60) - int(u["member"].sum()),
                     0)

    def tail_ff(i):
        return 0.14 if (mkt == "China" and i % 2 == 0) else 0.7
    tail = pd.DataFrame([dict(ticker=f"TAIL{i:03d}",
                              full_mktcap_usd=float(c),
                              free_float_frac=tail_ff(i),
                              adv_usd=float(c) * 0.004, atvr=1.0,
                              member=int(i < n_tail_mem))
                         for i, c in enumerate(caps)])
    full = pd.concat([u, tail], ignore_index=True)
    members = set(full.loc[full["member"] == 1, "ticker"])
    # Backtest iteration-4 rule (session 8u): the deep country-
    # coverage MIGRATION sweep is SAIR business; QIRs execute only
    # extreme breaches (0.5x floor + screens). Applying migration at
    # QIR vintages over-flagged 10 deletions at Aug-2025 that MSCI
    # did not make. Documented MSCI cadence, not a tuned knob.
    r = predict_msci(full.drop(columns="member"), members,
                     MSCIRules(review=review,
                               country_coverage=(0.85 if review ==
                                                 "SAIR" else None),
                               country_buffer=buffer))

    def named(d):
        return (d[~d["ticker"].astype(str).str.startswith("TAIL")]
                if len(d) else d)
    adds, dels = named(r["adds"]), named(r["deletes"])
    # corporate-action rule: announced takeover pre-review -> delete
    for t, why in CA_DELETIONS.get(mkt, {}).items():
        if t in set(u["ticker"]) and (not len(dels)
                                      or t not in set(dels["ticker"])):
            cap = float(u.loc[u["ticker"] == t,
                              "full_mktcap_usd"].iloc[0])
            dels = pd.concat([dels, pd.DataFrame(
                [{"ticker": t, "full_mktcap_usd": cap,
                  "reason": f"corporate action: {why}"}])],
                ignore_index=True)
    return {"adds": adds, "deletes": dels, "gmsr": r["gmsr_usd"],
            "add_thr": r["add_threshold_usd"],
            "watch": named(r["watchlist"]),
            "assembled": full}     # session 9i: funnel decomposition


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
        Path("data/event_data_cache.json").read_text(encoding="utf-8"))
    asia = {}
    p = Path("data/crowding_asia_cache.json")
    if p.exists():
        asia = json.loads(p.read_text(encoding="utf-8"))
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
        Path(f"data/msci_{p}_public_list.txt").read_text(encoding="utf-8"))
        for p in ("feb26", "may26")]
    caches = market_short_caches()
    event_cache = json.loads(
        Path("data/event_flow_study.json").read_text(encoding="utf-8"))
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
        # session 9i: JAPAN uses its OWN measured T-multiple priors
        # (jp_event_priors.json, 166 print-verified name-events) —
        # previously every market's history line showed TW's cache
        # (an honesty gap, closed)
        if mkt == "Japan":
            jp = Path("data/jp_event_priors.json")
            if jp.exists():
                pri = json.loads(jp.read_text(encoding="utf-8"))["priors"]
                r["history"] = {
                    f"MSCI {side} (JP-measured)": {
                        "available": True, "median": p["median"],
                        "max": p["max"], "n": p["n"]}
                    for side, p in pri.items()}
        r["universe_df"] = u
        results.append(r)

    notes = (
        "SESSION 9i ITERATION: caps REPRICED TO CURRENT (Apr-30 -> "
        "now ratios, 125/125 names, scripts/refresh_aug_caps.py; "
        "dispersion p10 0.75 / p90 1.18) — this surfaced the Korea "
        "sub-floor delete. DISCLOSED LIMIT the decade check now "
        "exposes: China reads OUTSIDE_LOW on adds (0 called vs "
        "decade QIR median ~12) because the 125-name cached universe "
        "cannot SEE the mid-cap risers and new listings that "
        "historically supply China QIR adds — a UNIVERSE-BREADTH "
        "gap (improvement plan item 4), not a quiet market. Treat "
        "the China add side as NO-CALL-below-the-floor, not as "
        "'no changes expected'. "
        "Configuration otherwise = the May-replication-graded setup "
        "(69% of all 98 actual May changes at PIT; adds 17/17 zero "
        "false positives). Original caps were APRIL vintage — "
        "final refresh still MANDATORY at Aug-11 along with the "
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
