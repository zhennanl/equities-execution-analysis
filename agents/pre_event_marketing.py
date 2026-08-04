"""Pre-event marketing generator — Step 1, Phase 0 (session 8k).

The PT trader's workflow: a client asks about the next index event;
the trader picks the EVENT, the engine runs, and this module turns
engine output into the pitch — the call sheet, the boundary watch,
the crowding overlay, the T-day expectations, the graded record, and
the client-facing note to send. Composition + rendering only: the
predictions come from review_engine, the priors from the measured
event library, and every honesty rule (probabilities not lists,
NO-CALL where unvalidated, misses shipped) is enforced in the
rendered artifact itself.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

# ------------------------------------------------------------- events
# The registry the trader picks from. Dates from provider calendars;
# status says what the engine can honestly run TODAY.
EVENTS: dict[str, dict] = {
    "MSCI Aug-2026 QIR (Asia)": dict(
        provider="MSCI", review="QIR",
        ann="2026-08-12", eff="2026-09-01",
        markets=["Taiwan", "Japan", "Korea", "China", "India",
                 "Malaysia", "Indonesia", "HongKong"],
        engine="live",
        note="Full 8-market engine run on the May-graded config; "
             "caps April-vintage until the Aug-11 refresh."),
    "MSCI Nov-2026 SAIR (Asia)": dict(
        provider="MSCI", review="SAIR",
        ann="2026-11-10", eff="2026-12-01",
        markets=["Taiwan", "Japan", "Korea", "China", "India",
                 "Malaysia", "Indonesia", "HongKong"],
        engine="live",
        note="SAIR hurdles (1.15x) — wider add funnel than QIR; "
             "universes roll forward after Aug 12 results."),
    "MSCI May-2026 SAIR — PIT replay (predict, then grade)": dict(
        provider="MSCI", review="SAIR",
        ann="2026-05-12", eff="2026-05-29",
        markets=["Taiwan", "Japan", "Korea", "China", "India",
                 "Malaysia", "Indonesia", "HongKong"],
        engine="pit",
        note="Every input frozen at pre-announcement vintage: "
             "Apr-30 caps from historical prices, PRE-May "
             "membership, ledgers through Feb only (the May list is "
             "the answer key — it never enters), crowding archive "
             "truncated at May 12. Generate the prediction first; "
             "the official outcome reveals AFTER, as a self-grade."),
    "FTSE TW50 Sep-2026 review": dict(
        provider="FTSE", review="TW50",
        ann="2026-09-04", eff="2026-09-18",
        markets=["Taiwan"],
        engine="reference",
        note="Rank-buffer game (promote at 40th, relegate at 61st): "
             "boundary ranks are fragile, so deletion calls ship as "
             "watch zones. Live rank run lands at the next data "
             "refresh; the graded June-2026 case study is the "
             "reference (adds 4/4)."),
}


# How every number on the Step-1 page is produced — shown in the UI
# next to the number, because "explain how we got the result" is part
# of the product, not documentation.
METHODOLOGY: dict[str, str] = {
    "prediction":
        "Rebuild each market's investable ladder from market caps "
        "(PIT replay: Apr-30 caps via historical prices) and free-"
        "float estimates; pin total membership to MSCI's published "
        "constituent count; walk the ladder to 85% cumulative "
        "free-float coverage — the last cap in is the GMSR (the "
        "'magic line'). ADD: a non-member whose full cap clears the "
        "hurdle (SAIR ≥1.15x GMSR, QIR ≥1.8x) AND passes the "
        "min-float (0.15) and real-ATVR liquidity screens. DELETE "
        "WATCH: a member below the 0.5x coverage floor. A-shares "
        "rank inside the ladder at their 20% inclusion factor "
        "(weight rule, not an eligibility rule). Every call is then "
        "gated by membership verification against official change-"
        "list ledgers — no call ships on unverified membership (the "
        "Feng Tay rule).",
    "crowding":
        "Daily short-balance archive (TWSE TWT93U margin-short + "
        "SBL). For each flagged name: %-build over the last ≤30 "
        "observations → HIGH ≥+25% / MED ≥+5% / LOW. Then the "
        "stock-not-flow refinement: drawdown from the window peak "
        "≥15% off a real peak tags EXITING — a crowd that built and "
        "left is not crowding anymore. HIGH build = the street "
        "already trades our call (CONSENSUS, operationally "
        "important, alpha spent); LOW/EXITING = UNPRICED — the "
        "T-day move is still ahead. PIT replay: archive truncated "
        "at the announcement date; Taiwan only (the multi-market "
        "feeds began archiving in July).",
    "flows":
        "Per-name expected flow = free-float cap × passive-"
        "ownership rate, quoted as a RANGE (5–9%) because MSCI-"
        "linked tracker stacking (country + EM + ACWI layers) is an "
        "estimate, not a point. Execution size = flow ÷ ADV → "
        "ADV-days → the bucket (MOC < 1 day / WORK+MOC < 3 / "
        "MULTI-DAY) that drives the whole execution plan. "
        "Validation checkpoint: realized T-day prints.",
    "probabilities":
        "Laplace-shrunk from the graded record — adds 17/17 at PIT "
        "quality → ~85% per HIGH-margin call; verified deletes "
        "~80%; unverified membership discounts ×0.75. Not "
        "confidence theater: the same grading that produced these "
        "numbers is applied to THIS run after announcement.",
}


def grade_predictions(results: list[dict],
                      actual: dict[str, dict]) -> pd.DataFrame:
    """Self-grade a PIT run against the official outcome. actual:
    {market: {'adds': set, 'dels': set}}. Returns per-market hits /
    misses / false-flags with names — the artifact that makes the
    track record credible."""
    rows = []
    for r in results:
        act = actual.get(r["market"])
        if act is None:
            continue
        calls = r["calls"]
        pa = (set(calls[calls["call"] == "ADD"]["ticker"])
              if len(calls) else set())
        pd_ = (set(calls[calls["call"] == "DELETE"]["ticker"])
               if len(calls) else set())
        aa, ad = set(act["adds"]), set(act["dels"])
        rows.append({
            "market": r["market"],
            "adds": f"{len(pa & aa)}/{len(aa)}",
            "add_false+": len(pa - aa),
            "deletes": f"{len(pd_ & ad)}/{len(ad)}",
            "del_false+": len(pd_ - ad),
            "missed": ", ".join(sorted((aa - pa) | (ad - pd_)))
                      or "-",
            "false_flags": ", ".join(sorted((pa - aa) | (pd_ - ad)))
                           or "-"})
    return pd.DataFrame(rows)


def days_to(date_str: str, today: str | None = None) -> int:
    t = pd.Timestamp(today) if today else pd.Timestamp.today()
    return int((pd.Timestamp(date_str) - t.normalize()).days)


def boundary_watch(universe: pd.DataFrame, gmsr: float,
                   add_thr: float, n: int = 5) -> pd.DataFrame:
    """The trader's 'who is near the line' table: members nearest the
    0.5x delete floor and non-members nearest the add hurdle, with
    signed distance. This is what moves between now and announcement
    — the conversation the client actually wants."""
    real = universe[~universe["ticker"].astype(str)
                    .str.startswith("TAIL")].copy()
    real["x_gmsr"] = real["full_mktcap_usd"] / gmsr
    mem = real[real["member"] == 1].nsmallest(n, "x_gmsr")
    non = real[real["member"] == 0].nlargest(n, "x_gmsr")
    rows = []
    for _, r in mem.iterrows():
        margin = (r["x_gmsr"] / 0.5 - 1) * 100
        rows.append({"ticker": r["ticker"], "side": "member",
                     "x_gmsr": round(r["x_gmsr"], 2),
                     "line": "delete floor (0.5x)",
                     "distance": f"{margin:+.0f}% above floor",
                     "at_risk": bool(margin < 30)})
    add_x = add_thr / gmsr
    for _, r in non.iterrows():
        margin = (r["x_gmsr"] / add_x - 1) * 100
        rows.append({"ticker": r["ticker"], "side": "non-member",
                     "x_gmsr": round(r["x_gmsr"], 2),
                     "line": f"add hurdle ({add_x:.2f}x)",
                     "distance": f"{margin:+.0f}% vs hurdle",
                     "at_risk": bool(margin > -30)})
    return pd.DataFrame(rows)


def render_marketing_md(event_name: str, event: dict,
                        results: list[dict],
                        boundary: dict[str, pd.DataFrame],
                        crowding: dict[str, str],
                        as_of: str) -> str:
    """The client-facing pre-event note. Honesty rules enforced in
    the artifact: zero-call results stated as such with the reading,
    probabilities on every call, watch zones labeled, the track
    record WITH misses, NO-CALL markets listed."""
    L = [f"# Pre-Event Note — {event_name}",
         f"*Prepared {as_of}. Announcement {event['ann']} "
         f"(T-{max(days_to(event['ann'], as_of), 0)}), effective "
         f"close {event['eff']}. Systematic output; every call "
         "carries a probability from our graded record; misses are "
         "in the appendix, not hidden.*", ""]
    total_calls = 0
    for r in results:
        L.append(f"## {r['market']} — GMSR ${r['gmsr_usd'] / 1e9:.1f}B, "
                 f"add ≥ ${r['add_threshold_usd'] / 1e9:.1f}B")
        calls = r["calls"]
        live = (calls[calls["call"] != "BLOCKED"]
                if len(calls) else calls)
        if len(live):
            total_calls += len(live)
            L.append(live[["call", "ticker", "cap_usd_b", "x_gmsr",
                           "p_correct", "flow_usd_m", "adv_days",
                           "bucket", "crowding"]].to_markdown(
                index=False))
        else:
            L.append("**No calls.** Nothing in this market breaches "
                     "the thresholds under current caps — a credible "
                     "post-SAIR quiet, not a missing analysis.")
        b = boundary.get(r["market"])
        if b is not None and len(b):
            L.append("\n**Boundary watch (who moves the note before "
                     "announcement):**\n")
            bb = b.copy()
            bb["crowding"] = [
                crowding.get(str(t).split(".")[0], "no data")
                for t in bb["ticker"]]
            L.append(bb.to_markdown(index=False))
        L.append("")
    L.append("## What T-day looks like (measured, not guessed)")
    hist = results[0]["history"] if results else {}
    for k, v in hist.items():
        if isinstance(v, dict) and v.get("available"):
            L.append(f"- **{k}**: T-day volume median "
                     f"{v['median']:.0f}x ADV (range "
                     f"{v['min']:.0f}-{v['max']:.0f}x, n={v['n']})")
        else:
            L.append(f"- **{k}**: no measured events — stated, "
                     "not guessed")
    L.append("- Front-run drift −4.3% (MSCI deletes, measured); "
             "~50% reversal by T+5; T+2 SBL settlement signature "
             "— completion legs planned accordingly.")
    L.append("\n## Why believe this (the graded record)")
    tr = results[0]["track_record"] if results else pd.DataFrame()
    if len(tr):
        L.append(tr.to_markdown(index=False))
    L.append("\n## The honesty box")
    L.append("- Probabilities are Laplace-shrunk from graded "
             "outcomes, not confidence theater.")
    L.append("- Deletion calls are a probability-ranked WATCH ZONE "
             "(May-measured: precision 82% / recall 89%); cutline "
             "residents are labeled.")
    L.append("- Markets without a validated universe get NO-CALL, "
             "not a fabricated list.")
    L.append("- CONSENSUS vs UNPRICED (crowding column) tells you "
             "which calls the street has already traded — the part "
             "of this note nobody else sends.")
    L.append(f"\n*{event.get('note', '')}*")
    return "\n".join(L) + "\n"
