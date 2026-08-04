"""Unified index-review engine (session 7y) — the complete pipeline,
one call: predictions -> factual reconciliation -> rationale &
probabilities -> stacked-AUM flows -> crowding -> measured event
history -> risk flags -> graded track record -> client-ready markdown.

Composes engines built and graded across sessions 6v-7x:

    layer 1  screen           reconstitution.predict_msci (QIR/SAIR)
    layer 2  reconcile        reconstitution.parse_msci_public_list /
                              reconcile_membership — the Feng Tay gate:
                              a call touching a STALE name is BLOCKED,
                              not silently fixed
    layer 3  rationale        reconstitution.explain_call + Laplace-
                              shrunk probabilities from the graded record
    layer 4  flows            stacked-AUM heuristic (passive ownership
                              rate x free-float cap) + ADV-day buckets
    layer 5  crowding         event_data.crowding_score on the short
                              ledger archive
    layer 6  history          pitch_pack.expected_t_multiples (measured
                              2026 events; absent classes say so)
    layer 7  risk flags       pitch_pack.risk_flags
    layer 8  track record     pitch_pack.track_record (misses included)

Design rules unchanged: point-in-time inputs, NO-CALL where the
universe is unvalidated, deterministic scoring, every number checkable.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

# Laplace-shrunk per-call probabilities from the graded record
# (5 reviews, 26 committed calls — see QIR_AUG2026_PRERUN addendum 7w)
PROB = {"ADD_HIGH": 0.85, "ADD_MED": 0.80, "DELETE_VERIFIED": 0.80,
        "DELETE_UNVERIFIED": 0.60}

# Passive ownership rate of MSCI-linked trackers as % of FREE-FLOAT cap
# for EM Asia names — v1 heuristic (range disclosed), to be validated
# against the Sep-1 realized prints. Literature + our May measurements
# put MSCI-linked passive holdings at mid-to-high single digits of float.
PASSIVE_OWN_RATE = (0.05, 0.09)

# ------------------------------------------------------------------
# Decade priors (session 9i): measured on all 44 MSCI quarters
# 2015-2025 from official STPublicLists (scripts/msci_key_stats.py).
# Used as (a) per-market cadence context in packs and (b) an
# EXPECTED-COUNT consistency check: a pack whose call counts sit far
# outside the decade distribution for that review type gets flagged
# for review — a check against over/under-calling, never a tuner.
_DECADE_PATH = "data/msci_decade_stats.json"
_LEDGER_NAME = {"Taiwan": "TAIWAN", "China": "CHINA",
                "Japan": "JAPAN", "HongKong": "HONG KONG",
                "Korea": "KOREA", "India": "INDIA",
                "Malaysia": "MALAYSIA", "Indonesia": "INDONESIA",
                "Thailand": "THAILAND", "Philippines": "PHILIPPINES",
                "Singapore": "SINGAPORE", "Australia": "AUSTRALIA"}


def load_decade_stats():
    import json
    from pathlib import Path
    p = Path(__file__).resolve().parents[1] / _DECADE_PATH
    return json.loads(p.read_text()) if p.exists() else None


def decade_consistency(market: str, review: str,
                       n_adds: int, n_dels: int) -> dict | None:
    """Score a pack's call counts against the decade distribution for
    this market x review type. Verdicts: OK (<= q75), ELEVATED
    (q75-q90), OUTSIDE (> q90) — OUTSIDE is a review flag, not an
    auto-suppression."""
    stats = load_decade_stats()
    led = _LEDGER_NAME.get(market)
    if not stats or not led or led not in stats["cadence"]:
        return None
    c = stats["cadence"][led]
    qs = c["counts"].get(review)
    if not qs:
        return None

    def verdict(n, q):
        # two-sided (session 9i fix): a zero-call pack in a market
        # whose decade MEDIAN is well above zero is as suspect as an
        # over-calling one. q = [q25, q50, q75, q90].
        if n > q[3]:
            return "OUTSIDE_HIGH"
        if n > q[2]:
            return "ELEVATED"
        if q[1] >= 3 and n < max(1, q[0] // 2):
            return "OUTSIDE_LOW"     # calling far below decade norm
        return "OK"
    ch = stats.get("churn", {}).get(led, {})
    return {"review": review,
            "del_q75_q90": (qs["del_q"][2], qs["del_q"][3]),
            "add_q75_q90": (qs["add_q"][2], qs["add_q"][3]),
            "del_verdict": verdict(n_dels, qs["del_q"]),
            "add_verdict": verdict(n_adds, qs["add_q"]),
            "sair_del_share": c["sair_del_share"],
            "add_deleted_within_4": ch.get("add_deleted_within_4"),
            "del_readded_within_4": ch.get("del_readded_within_4"),
            "basis": f"{qs['n_reviews']} {review}s 2015-2025"}


# Share of a market's review changes that historically originate
# BELOW the named-universe floor (measured on the official re-grades:
# TW Nov-25 13/13 below floor vs May-26 8/8 visible -> ~0.6 for the
# current 16-name breadth). Explicit, stated, revisable as breadth
# grows — the shortlist allocates this probability mass to a declared
# BELOW-FLOOR row instead of overstating visible candidates.
BLIND_SHARE = {"Taiwan": (0.6, "13/21 of 2025-26 TW changes sat "
                                "below the 16-name floor (Nov-25 "
                                "re-grade vs May-26 grade)")}


def shortlist_candidates(screen: dict, universe: pd.DataFrame,
                         review: str, market: str, k: int = 4,
                         recent_deletions: set | None = None
                         ) -> pd.DataFrame | None:
    """Session 9i (user rule): a no-change prediction still ships a
    ranked SHORTLIST — nearest candidates each side with an assigned
    probability and reasoning — so Steps 2-4 have names to analyze.

    Probability construction (every factor measured, none tuned):
      P(any change this review)  = decade base rate, market x type
      x visible share            = 1 - BLIND_SHARE (breadth-honest)
      x proximity weight         = softmax of cap/threshold among
                                   the k nearest visible candidates
    The BELOW-FLOOR row carries the blind mass explicitly."""
    import numpy as np
    stats = load_decade_stats()
    led = _LEDGER_NAME.get(market)
    if not stats or not led:
        return None
    qs = stats["cadence"].get(led, {}).get("counts", {}).get(review)
    if not qs:
        return None
    blind, blind_basis = BLIND_SHARE.get(market, (0.5, "default 0.5 "
                                                  "(unmeasured)"))
    u = screen["assembled"]
    real = u[~u["ticker"].astype(str).str.startswith("TAIL")]
    gmsr, add_thr = screen["gmsr"], screen["add_thr"]
    rows = []
    for side, pool, thr, p_any in (
            ("ADD", real[real["member"] == 0], add_thr,
             qs["p_any_add"]),
            ("DELETE", real[real["member"] == 1], 0.5 * gmsr,
             qs["p_any_del"])):
        if not len(pool):
            continue
        pool = pool.copy()
        pool["x_thr"] = pool["full_mktcap_usd"] / thr
        near = (pool.nlargest(k, "x_thr") if side == "ADD"
                else pool.nsmallest(k, "x_thr"))
        # proximity softmax: distance of log(x_thr) from 0
        d = -abs(np.log(near["x_thr"].clip(lower=1e-6)))
        w = np.exp(d / 0.25)
        w = w / w.sum()
        readd = stats.get("churn", {}).get(led, {}) \
            .get("del_readded_within_4")
        for (_, r), wi in zip(near.iterrows(), w):
            gap = ((1 / r["x_thr"] - 1) if side == "ADD"
                   else (r["x_thr"] - 1))
            caution = ""
            if side == "ADD" and recent_deletions \
                    and r["ticker"] in recent_deletions \
                    and readd is not None:
                caution = (f"; CAUTION recent deletion — decade "
                           f"re-add-within-4 rate here is "
                           f"{readd:.0%}")
            rows.append({
                "side": side, "ticker": r["ticker"],
                "cap_usd_b": round(r["full_mktcap_usd"] / 1e9, 1),
                "x_threshold": round(r["x_thr"], 2),
                "p": round(p_any * (1 - blind) * wi, 3),
                "reasoning": (
                    f"{'non-member' if side == 'ADD' else 'member'} "
                    f"{r['x_thr']:.2f}x the "
                    f"{'add bar' if side == 'ADD' else 'del floor'} "
                    f"(needs {gap:+.0%}); P(any {side.lower()} at a "
                    f"{led} {review}) = {p_any:.0%} decade-measured, "
                    f"x visible share {1 - blind:.0%}, x proximity "
                    f"weight {wi:.0%}" + caution)})
        rows.append({
            "side": side, "ticker": "BELOW-FLOOR (unobservable)",
            "cap_usd_b": None, "x_threshold": None,
            "p": round(p_any * blind, 3),
            "reasoning": f"blind-band mass: {blind_basis}"})
    df = pd.DataFrame(rows)
    # drop negligible visible rows (p < 0.005) — a 0.000-probability
    # line is noise, not honesty; blind-band rows always stay
    return df[(df["p"] >= 0.005)
              | df["ticker"].str.startswith("BELOW-FLOOR")
              ].reset_index(drop=True)


def screen_market(universe: pd.DataFrame, review: str = "QIR",
                  tail_seed: int = 11, tail_n: int = 400,
                  tail_hi: float = 8e9,
                  member_count: int | None = None,
                  a_share_tail_mix: bool = False) -> dict:
    """Layer 1: rules engine on real boundary names + modeled tail.

    PIT-May-validated upgrades (case study PIT_MAY2026_ALL_ASIA):
    - member_count: COUNT-ANCHORED universe — total members pinned to
      the provider's published constituent count (public factsheet
      input), placing the coverage boundary where the index's real
      size puts it. Took the May replication 55%->65%.
    - a_share_tail_mix: China only — tail floats alternate 0.7 (H) and
      0.14 (A x 20% inclusion factor, documented MSCI methodology).
    Universe columns: ticker, full_mktcap_usd, free_float_frac,
    adv_usd, atvr, member. (A-share members' ff should arrive already
    factor-adjusted; candidates' ff raw — factor sets weight, not
    eligibility.)"""
    from agents.reconstitution import MSCIRules, predict_msci
    rng = np.random.default_rng(tail_seed)
    caps = np.sort(np.exp(rng.uniform(np.log(0.3e9), np.log(tail_hi),
                                      tail_n)))[::-1]
    if member_count is not None:
        n_tail_mem = max(member_count - int(universe["member"].sum()),
                         0)
        mem_flag = lambda i, c: int(i < n_tail_mem)
    else:
        mem_flag = lambda i, c: int(c > 2.5e9)
    tf = (lambda i: 0.14 if (a_share_tail_mix and i % 2 == 0)
          else 0.7)
    tail = pd.DataFrame([dict(ticker=f"TAIL{i:03d}",
                              full_mktcap_usd=float(c),
                              free_float_frac=tf(i),
                              adv_usd=float(c) * 0.004, atvr=1.0,
                              member=mem_flag(i, c))
                         for i, c in enumerate(caps)])
    u = pd.concat([universe, tail], ignore_index=True)
    members = set(u.loc[u["member"] == 1, "ticker"])
    r = predict_msci(u.drop(columns="member"), members,
                     MSCIRules(review=review))
    named = lambda d: (d[~d["ticker"].str.startswith("TAIL")]
                       if len(d) else d)
    return {"gmsr": r["gmsr_usd"], "add_thr": r["add_threshold_usd"],
            "adds": named(r["adds"]), "deletes": named(r["deletes"]),
            "watch": named(r["watchlist"]),
            "assembled": u}       # session 9i: funnel decomposition


def reconcile_layer(universe: pd.DataFrame, aliases: dict,
                    ledgers: list[dict], country: str) -> list[dict]:
    """Layer 2: the Feng Tay gate."""
    from agents.reconstitution import reconcile_membership
    members = {aliases[t]: bool(m) for t, m in
               zip(universe["ticker"], universe["member"])
               if t in aliases}
    return reconcile_membership(members, ledgers, country)


def build_calls(screen: dict, universe: pd.DataFrame,
                violations: list[dict], aliases: dict,
                crowding_map: dict[str, str] | None = None,
                membership_verified: bool = False) -> pd.DataFrame:
    """Layers 3+4: per-name call rows with rationale, probability, and
    stacked-AUM flow estimate. Calls touching a ledger violation are
    BLOCKED (kind -> 'BLOCKED', probability 0, reason attached)."""
    from agents.reconstitution import explain_call
    bad_names = {v["name"].upper(): v for v in violations}
    ffm = dict(zip(universe["ticker"], universe["free_float_frac"]))
    rows = []
    for kind, df in (("ADD", screen["adds"]),
                     ("DELETE", screen["deletes"])):
        for _, r in df.iterrows():
            t = r["ticker"]
            cap = r["full_mktcap_usd"]
            ratio = cap / screen["gmsr"]
            alias = aliases.get(t, t).upper()
            blocked = alias in bad_names
            crowd = (crowding_map or {}).get(t.split(".")[0])
            exp = explain_call(kind, t, cap, screen["gmsr"],
                               screen["add_thr"] if kind == "ADD"
                               else 0.5 * screen["gmsr"],
                               float_frac=ffm.get(t),
                               membership_verified=membership_verified
                               and not blocked,
                               crowding=crowd)
            if blocked:
                p = 0.0
                exp["membership_verified"] = ("BLOCKED: " +
                                              bad_names[alias]["fix"])
            elif kind == "ADD":
                p = (PROB["ADD_HIGH"] if ratio >= 2.5
                     else PROB["ADD_MED"])
                if not membership_verified:
                    p = round(p * 0.75, 2)     # unverified discount
            else:
                p = (PROB["DELETE_VERIFIED"] if membership_verified
                     else PROB["DELETE_UNVERIFIED"])
                # session 9i (TW ex-post drivers): where ret_3m is
                # supplied, deletion hazard is velocity-tagged —
                # DECLINE names convert fastest; STALE names are the
                # coverage-arithmetic class (no price signal exists;
                # ~45% of 2025-26 TW deletions were STALE, so the
                # ladder, not momentum, remains the primary signal)
                if "ret_3m" in universe.columns:
                    r3s = universe.set_index("ticker")["ret_3m"]
                    r3 = r3s.get(t)
                    if r3 is not None and not pd.isna(r3):
                        tag = ("DECLINE" if r3 < -15 else
                               "DRIFT" if r3 < -3 else "STALE")
                        exp["mechanism"] += (
                            f"; hazard velocity {tag} "
                            f"(ret_3m {r3:+.0f}%)")
            kind_out = "BLOCKED" if blocked else kind
            ff = ffm.get(t, 0.7)
            lo = cap * ff * PASSIVE_OWN_RATE[0]
            hi = cap * ff * PASSIVE_OWN_RATE[1]
            adv = float(universe.loc[universe["ticker"] == t,
                                     "adv_usd"].iloc[0])
            adv_days = (lo + hi) / 2 / adv if adv else np.nan
            rows.append({
                "call": kind_out, "ticker": t,
                "cap_usd_b": round(cap / 1e9, 1),
                "x_gmsr": round(ratio, 2),
                "p_correct": p,
                "flow_usd_m": f"{lo/1e6:.0f}-{hi/1e6:.0f}",
                "adv_days": round(adv_days, 1),
                "bucket": ("MOC" if adv_days < 1 else
                           "WORK+MOC" if adv_days < 3 else "MULTI-DAY"),
                "crowding": crowd or "no data",
                "rationale": exp["mechanism"],
                "verified": exp["membership_verified"]})
    return pd.DataFrame(rows)


def crowding_reads(short_cache: dict | None,
                   tickers: list[str]) -> dict[str, str]:
    """Layer-5 crowding read for any market whose cache uses the
    normalized {short: {date: {code: [bal, x]}}} schema (TWSE native;
    JPX/SFC/TPEx via event_data.merge_into_short_cache). Positioning
    NOW over the last <=30 observations, PLUS the stock-vs-flow
    refinement — crowding that was built and then EXITED early is not
    crowding anymore: drawdown-from-peak >=15% off a real peak tags
    EXITING. Window label reports actual observation count (daily for
    TW/JP, weekly for HK — units cancel in %-change)."""
    if not short_cache:
        return {}
    from agents.event_data import short_balance_series
    out = {}
    for t in tickers:
        base = t.split(".")[0]
        s = short_balance_series(short_cache, base)
        if s.empty or len(s) < 3:
            continue
        w = s.iloc[-min(len(s), 30):]
        b = w["total_short"].iloc[0]
        now = w["total_short"].iloc[-1]
        peak = w["total_short"].max()
        pct = 100 * (now - b) / b if b else np.nan
        band = ("HIGH" if pct >= 25 else
                "MED" if pct >= 5 else "LOW")
        off_peak = 100 * (peak - now) / peak if peak else 0
        tag = (f"; EXITING (-{off_peak:.0f}% off peak)"
               if off_peak >= 15 and peak > b * 1.1 else "")
        out[base] = f"{band} ({pct:+.0f}%/{len(w)}obs){tag}"
    return out


def run_full_review(market: str, universe: pd.DataFrame, aliases: dict,
                    ledgers: list[dict], ledger_country: str,
                    short_cache: dict | None = None,
                    event_cache: dict | None = None,
                    review: str = "QIR",
                    names_risk: pd.DataFrame | None = None,
                    member_count: int | None = None,
                    a_share_tail_mix: bool = False,
                    tail_hi: float = 8e9, tail_n: int = 400,
                    recent_deletions: set | None = None,
                    recent_additions: set | None = None,
                    screen: dict | None = None) -> dict:
    """The complete pipeline for one market. recent_deletions: names
    deleted at the immediately preceding review are EXCLUDED from add
    candidacy (churn-buffer behavior: an FF/coverage-deleted name does
    not re-enter next review on unchanged fundamentals — full-cap add
    screens alone would spuriously re-flag them)."""
    from agents.pitch_pack import (expected_t_multiples, risk_flags,
                                   track_record)
    # screen override (session 8m): a caller may supply a precomputed
    # screen — e.g. the PIT harness's predict_msci screen with the
    # country-segment MIGRATION deletion rule and CA rule, the exact
    # configuration the May replication graded at 69%. screen_market's
    # 0.5x-floor-only deletes are the live-QIR default.
    if screen is None:
        screen = screen_market(universe, review=review,
                               member_count=member_count,
                               a_share_tail_mix=a_share_tail_mix,
                               tail_hi=tail_hi, tail_n=tail_n)
    if recent_deletions and len(screen["adds"]):
        excl = screen["adds"]["ticker"].isin(recent_deletions)
        if excl.any():
            screen = {**screen,
                      "excluded_readds": sorted(
                          screen["adds"].loc[excl, "ticker"]),
                      "adds": screen["adds"][~excl]}
    # symmetric churn buffer: names ADDED at the immediately preceding
    # review are excluded from deletion candidacy — the provider
    # admitted them knowing their (factor-adjusted) FF profile; they
    # do not migrate out one review later on unchanged fundamentals.
    if recent_additions and len(screen["deletes"]):
        excl = screen["deletes"]["ticker"].isin(recent_additions)
        if excl.any():
            screen = {**screen,
                      "excluded_redels": sorted(
                          screen["deletes"].loc[excl, "ticker"]),
                      "deletes": screen["deletes"][~excl]}
    violations = reconcile_layer(universe, aliases, ledgers,
                                 ledger_country)
    tickers = (list(screen["adds"]["ticker"] if len(screen["adds"])
                    else []) + list(screen["deletes"]["ticker"]
                                    if len(screen["deletes"]) else []))
    crowding_map = crowding_reads(short_cache, tickers)
    # verification requires ACTUAL ledger coverage: an empty alias map
    # means nothing was checked — that is NOT verified (Feng Tay rule)
    calls = build_calls(screen, universe, violations, aliases,
                        crowding_map,
                        membership_verified=bool(aliases)
                        and not violations)
    history = {}
    if event_cache:
        for side in ("Sell", "Buy"):
            history[f"MSCI {side}"] = expected_t_multiples(
                event_cache, "MSCI", side)
    flags = (risk_flags(names_risk) if names_risk is not None
             else pd.DataFrame())
    live = calls[calls["call"] != "BLOCKED"] if len(calls) \
        else pd.DataFrame(columns=["call"])
    n_a = int((live["call"] == "ADD").sum()) if len(live) else 0
    n_d = int(live["call"].isin(["DELETE", "DELETE_WATCH"]).sum()) \
        if len(live) else 0
    short = (shortlist_candidates(screen, universe, review, market,
                                  recent_deletions=recent_deletions)
             if (n_a + n_d) == 0 and "assembled" in screen else None)
    return {"market": market, "review": review,
            "gmsr_usd": screen["gmsr"],
            "add_threshold_usd": screen["add_thr"],
            "calls": calls, "violations": violations,
            "history": history, "flags": flags,
            "shortlist": short,
            "decade": decade_consistency(market, review, n_a, n_d),
            "track_record": track_record(),
            "expected_hits": round(float(
                calls.loc[calls["call"] != "BLOCKED",
                          "p_correct"].sum()), 2) if len(calls) else 0}


def render_review_markdown(results: list[dict], event_name: str,
                           as_of: str, no_call_markets: list[str],
                           notes: str = "") -> str:
    L = [f"# {event_name} — Full-Engine Pre-Registration Pack",
         f"*Generated {as_of} by agents/review_engine.py — all eight "
         "layers, one pipeline. Point-in-time; NO-CALL where "
         "unvalidated; blocked calls shown, not hidden.*", ""]
    for r in results:
        L.append(f"## {r['market']} ({r['review']}: GMSR "
                 f"${r['gmsr_usd']/1e9:.1f}B, add ≥ "
                 f"${r['add_threshold_usd']/1e9:.1f}B)")
        if r["violations"]:
            L.append("**Ledger violations (gate fired):** " +
                     "; ".join(f"{v['name']}: {v['type']}"
                               for v in r["violations"]))
        if len(r["calls"]):
            L.append(r["calls"].to_markdown(index=False))
            L.append(f"\nExpected correct calls: "
                     f"**{r['expected_hits']}** of "
                     f"{len(r['calls'][r['calls']['call'] != 'BLOCKED'])}")
        else:
            L.append("No calls.")
        if r.get("shortlist") is not None and len(r["shortlist"]):
            L.append("\n**No-change review — the SHORTLIST (nearest "
                     "candidates, decade-anchored probabilities; "
                     "Steps 2-4 run on these names):**\n")
            L.append(r["shortlist"].to_markdown(index=False))
        if r.get("decade"):
            d = r["decade"]
            L.append(f"\n**Decade prior ({d['basis']}):** "
                     f"{d['review']} deletions q75/q90 = "
                     f"{d['del_q75_q90'][0]}/{d['del_q75_q90'][1]} "
                     f"(this pack: {d['del_verdict']}), adds "
                     f"{d['add_q75_q90'][0]}/{d['add_q75_q90'][1]} "
                     f"({d['add_verdict']}); "
                     f"{(d['sair_del_share'] or 0)*100:.0f}% of this "
                     "market's decade deletions occurred at SAIRs; "
                     "churn: add→del4 "
                     f"{d['add_deleted_within_4']}, del→re-add4 "
                     f"{d['del_readded_within_4']}")
        if r["history"]:
            L.append("\n**Measured T-day behavior (2026 events):** " +
                     "; ".join(
                         f"{k}: median {v['median']}x (n={v['n']})"
                         if v.get("available") else f"{k}: no measured "
                         "events — stated, not guessed"
                         for k, v in r["history"].items()))
        if len(r["flags"]):
            for _, f in r["flags"].iterrows():
                if f["flags"]:
                    L.append(f"- RISK {f['ticker']}: " +
                             "; ".join(f["flags"]))
        L.append("")
    L += ["## NO-CALL markets", ", ".join(no_call_markets) +
          " — no validated universe; explicit refusal, not omission.", "",
          "## Graded track record (misses included)",
          results[0]["track_record"].to_markdown(index=False), ""]
    if notes:
        L += ["## Notes", notes]
    return "\n".join(L)
