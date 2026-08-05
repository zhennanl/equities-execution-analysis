"""Screening funnel — universe -> conditions -> final candidates.

Session 9i. Decomposes one review screen into the stage-by-stage
funnel a trader can SEE: how ~500 names boil down to a handful of
calls, with every elimination tied to its rule (the same L0-L4
logic as the engine — this file only OBSERVES, it never re-decides).

Stages:
  S0 acquisition     engine Step 1 — how the named universe is built
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
    n_real_mem = int(real["is_member"].sum())
    stages = [
        {"stage": "S0 acquisition", "n": n_real,
         "rule": "engine Step 1 — named universe from public data: "
                 "cap = price x shares (yfinance, FX to USD), "
                 "free-float estimated from holder filings, ADV 60d; "
                 "membership rolled forward from official review "
                 "results (never assumed)",
         "detail": f"{n_real} named boundary stocks ({n_real_mem} "
                   f"members near the deletion floor, "
                   f"{n_real - n_real_mem} candidates near the add "
                   "bar); market body below the boundary is modeled, "
                   "not fetched — see next stage"},
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


# GIMI May-2026 book citations per funnel stage (user request:
# selection method shown with the rule's source, not just our label)
STAGE_METHOD = {
    "S0 acquisition":
        "OURS. The book reviews the full equity universe (GIMI "
        "§3.1.1); changes only occur at the size boundary, so we "
        "curate the names nearest it from our own cap ranking and "
        "model the rest as a count-anchored tail. Caps = price x "
        "shares (yfinance, FX to USD) as of the frame date.",
    "S0 universe":
        "OURS + MSCI factsheet. Total member count pinned to the "
        "published constituent count so the coverage walk (GIMI "
        "§2.3.5) lands where the real index size puts it.",
    "S1 eligible":
        "GIMI §2.2 / §3.1.2: investability screens — free float "
        ">= 0.15 and ATVR liquidity floor. Existing constituents "
        "get 2/3-of-threshold retention grace (§3.1.2.4, §3.1.6.2).",
    "S2 thresholds":
        "GIMI §2.3.2 (p.24): walk the cap ladder to 85% free-float "
        "coverage -> GMSR reference; Range = 0.5x to 1.15x. QIR add "
        "bar 1.8x, SAIR 1.15x; deletion floor 0.5x.",
    "S3 candidates":
        "GIMI §3.1.4-3.1.5: non-members above the add bar become "
        "ADD candidates; members below the floor DELETE candidates; "
        "the +-15% band is the watch zone (hazard class, ~2/3 "
        "convert - our decade measurement, not the book's).",
    "S4 churn-buffered":
        "GIMI §3.1.5.1 (p.44): buffer zones control migration and "
        "index turnover — the prior review's changes are excluded "
        "from opposite-side candidacy.",
    "S5 verified":
        "OURS (Feng Tay gate): no call ships on unverified "
        "membership. The book assumes MSCI knows its own index; a "
        "predictor must prove it does.",
    "FINAL calls":
        "OURS: Laplace-shrunk probabilities from the graded record "
        "(L8) — the book has no probabilities; this layer is why a "
        "call says p=0.6 instead of pretending certainty.",
}


def name_journeys(screen: dict, calls: pd.DataFrame, review: str,
                  official: dict | None = None) -> list[dict]:
    """Per-name, stage-by-stage journey for every REAL stock in the
    universe — the shortlist AT each funnel step, with the rule that
    decided it. `official` = {"adds": set, "dels": set} grades the
    validation run's rows."""
    from agents.reconstitution import MSCIRules, _screens
    u = screen["assembled"]
    real = u[~u["ticker"].astype(str).str.startswith("TAIL")].copy()
    rules = MSCIRules(review=review)
    real["eligible"] = _screens(real, rules.min_float,
                                rules.min_atvr)
    gmsr, add_thr = screen["gmsr"], screen["add_thr"]
    floor = 0.5 * gmsr
    grab = lambda k: (set(screen[k]["ticker"])
                      if len(screen.get(k, [])) else set())
    adds, dels, watch = grab("adds"), grab("deletes"), grab("watch")
    buffered = set(screen.get("excluded_readds", [])) \
        | set(screen.get("excluded_redels", []))
    callmap = ({r["ticker"]: r for _, r in calls.iterrows()}
               if len(calls) else {})
    rows = []
    for _, r in real.sort_values("full_mktcap_usd",
                                 ascending=False).iterrows():
        t = str(r["ticker"])
        mem = bool(r.get("member", r.get("is_member", 0)))
        cap = float(r["full_mktcap_usd"])
        thr = floor if mem else add_thr
        if not r["eligible"]:
            s3 = "OUT at S1 — fails float/liquidity screen"
        elif t in buffered:
            s3 = "OUT at S4 — churn buffer (changed last review)"
        elif t in adds:
            s3 = "ADD candidate (above the add bar)"
        elif t in dels:
            s3 = ("DELETE candidate — below the effective deletion "
                  "bar (SAIR migration sweep sits ABOVE the hard "
                  "0.5x floor; GIMI §3.1.5.1)" if review == "SAIR"
                  else "DELETE candidate (below the 0.5x floor)")
        elif t in watch:
            s3 = "WATCH — within ±15% of its threshold"
        else:
            s3 = ("SAFE — comfortably above the floor" if mem else
                  "NOT CLOSE — below the add bar")
        c = callmap.get(t)
        final = (f"{c['call']} (p={c['p_correct']})"
                 if c is not None else "no call")
        row = {"ticker": t,
               "role": "member" if mem else "non-member",
               "cap_usd_b": round(cap / 1e9, 2),
               "threshold": ("hard 0.5x floor" if mem else "add bar")
               + f" ${thr/1e9:.1f}B",
               "x_threshold": round(cap / thr, 2),
               "status": s3, "final": final}
        if official:
            if t in official["dels"]:
                row["official"] = "DELETED" + (
                    " — HIT" if c is not None
                    and c["call"] == "DELETE" else " — MISSED")
            elif t in official["adds"]:
                row["official"] = "ADDED" + (
                    " — HIT" if c is not None
                    and c["call"] == "ADD" else " — MISSED")
            elif c is not None and c["call"] != "BLOCKED":
                row["official"] = ("RETAINED — false call "
                                   "(cutline resident)")
            else:
                row["official"] = "unchanged — correct"
        rows.append(row)
    return rows


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
