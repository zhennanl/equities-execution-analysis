"""Pre-mandate pitch pack — the analytics that win the broker-selection
phase of an index-rebalance trade (lifecycle Step 1 / Phase 0).

The commercial context (AI_ON_THE_PT_DESK.md, bullet-1 factors):
"analytics and color" is the tie-breaker among qualified brokers, and
the cheapest factor to be exceptional at. This module composes the
project's engines into ONE client-facing artifact:

    1. Event overview          calendar + what trades
    2. Predicted changes       reconstitution engine + confidence tags
    3. Expected flows          AUM x weight deltas, ADV-day buckets
    4. Crowding read           short-ledger positioning, per candidate
    5. Execution framework     measured T-multiples + per-bucket strategy
    6. Risk flags              limit-band / borrow / capacity names
    7. Track record            the GRADED scoreboard, misses included

Design rules:
- POINT-IN-TIME discipline: `as_of` gates every data input; a pack for
  June 1 uses nothing dated after June 1 (the validation loop depends
  on this being real).
- The track record ships its failures. A pitch that only shows wins is
  marketing; one that shows graded misses with mechanisms is evidence.
- `validate_pack` closes the loop: after the event, the pack's own
  claims are scored and the scorecard is appended. Clients keep brokers
  who grade themselves.
"""
from __future__ import annotations

import datetime as _dt

import numpy as np
import pandas as pd


# ------------------------------------------------- measured event history

def expected_t_multiples(event_cache: dict, provider: str, side: str,
                         as_of: str | None = None) -> dict:
    """Median / range of measured T-day volume multiples for events of
    this provider+side, using only events EFFECTIVE before `as_of`.
    Source: data/event_flow_study.json (real 2026 measurements)."""
    vals = []
    for label, ev in event_cache.items():
        if label.startswith("_") or not isinstance(ev, dict):
            continue
        if not ev.get("available", False):
            continue
        if ev.get("provider") != provider or ev.get("side") != side:
            continue
        eff = ev.get("eff")
        if as_of and eff and str(eff) > as_of:
            continue
        if as_of and not eff:
            continue          # unknown effective date -> excluded when
                              # point-in-time discipline is requested
        m = ev.get("t_day_volume_multiple")
        if m is not None and np.isfinite(m):
            vals.append(float(m))
    if not vals:
        return {"available": False, "n": 0}
    return {"available": True, "n": len(vals),
            "median": round(float(np.median(vals)), 1),
            "min": round(min(vals), 1), "max": round(max(vals), 1)}


# ---------------------------------------------------------- crowding read

def crowding_table(short_cache: dict, candidates: dict[str, str],
                   ann_date: str, as_of: str) -> pd.DataFrame:
    """Per-candidate positioning read from the short ledger, using only
    dates strictly before min(ann_date, as_of). candidates:
    ticker -> label (e.g. '2002 China Steel (delete candidate)')."""
    from agents.event_data import crowding_score, short_balance_series
    cutoff = min(ann_date, as_of)
    trimmed = {"short": {d: v for d, v in
                         short_cache.get("short", {}).items()
                         if d.replace("-", "") <
                         cutoff.replace("-", "")}}
    rows = []
    for tkr, label in candidates.items():
        cs = crowding_score(short_balance_series(trimmed, tkr), cutoff)
        rows.append({
            "ticker": tkr, "label": label,
            "pre_ann_build_pct": cs.get("pre_ann_build_pct", np.nan),
            "crowding": cs.get("crowding", "n/a"),
            "read": _crowding_read(cs.get("crowding"))})
    return pd.DataFrame(rows)


def _crowding_read(band):
    return {"HIGH": "street heavily positioned — pressure part-spent; "
                    "expect bigger post-event reversal",
            "MED": "moderate positioning",
            "LOW": "unpriced — full event pressure still ahead"
            }.get(band, "insufficient data")


# ------------------------------------------------------------- risk flags

def risk_flags(names: pd.DataFrame) -> pd.DataFrame:
    """Deterministic per-name flags. Expects columns: ticker, side,
    adv_days, band_pct (daily limit band %, NaN = none),
    borrow_constrained (bool)."""
    rows = []
    for _, r in names.iterrows():
        flags = []
        if r.get("adv_days", 0) >= 5:
            flags.append(f"SIZE: {r['adv_days']:.1f} ADV-days — "
                         "multi-day plan required")
        band = r.get("band_pct")
        if band is not None and not (isinstance(band, float) and
                                     np.isnan(band)) and band <= 10:
            flags.append(f"LIMIT: ±{band:.0f}% band — lock risk on "
                         "event day")
        if r.get("borrow_constrained"):
            flags.append("BORROW: constrained lending — short-side "
                         "hedging impaired, squeeze risk")
        if r.get("side") == "Sell" and r.get("adv_days", 0) >= 3:
            flags.append("REVERSAL: large delete — plan the "
                         "completion leg for the covering bounce")
        rows.append({"ticker": r["ticker"], "flags": flags,
                     "n_flags": len(flags)})
    return pd.DataFrame(rows)


# ------------------------------------------------- the graded track record

def track_record() -> pd.DataFrame:
    """The scoreboard, with misses. Every row traces to a graded case
    study in docs/case_studies/."""
    return pd.DataFrame([
        {"claim": "Addition predictions",
         "record": "11/11 across 5 real reviews, 2 providers, 3 markets",
         "caveat": "1 false positive (Korea) — diagnosed input data "
                   "quality, kept in report",
         "source": "DUAL_PROVIDER_backtests_Korea_ChinaA50.md"},
        {"claim": "Coverage-rule deletion predictions",
         "record": "14/14 (TW May 7/7, TW Feb 4/4, KR May 3/3)",
         "caveat": "buffer calibrated on one review pair; Aug 12 is the "
                   "frozen live test",
         "source": "MSCI_Taiwan_May2026_backtest.md"},
        {"claim": "Rank-boundary deletion predictions",
         "record": "~50-60%, every call self-labeled LOW confidence",
         "caveat": "structurally noise-fragile (measured by Monte "
                   "Carlo); shipped as watch zone, not signal",
         "source": "FTSE_Taiwan50_Jun2026_backtest.md"},
        {"claim": "T-day volume multiples",
         "record": "measured per provider x side on 21 real 2026 names "
                   "(MSCI deletes median 16x; FTSE ~5x)",
         "caveat": "one cycle of events; ranges shown, not points",
         "source": "EVENT_FLOW_STUDY_2026Q2.md"},
        {"claim": "Execution strategy rules",
         "record": "own rule falsified twice by realized grading, "
                   "refined in-sample 355->0 bps regret",
         "caveat": "refined rule FROZEN, unvalidated until Aug/Sep "
                   "cycle — stated before the event, not after",
         "source": "EVENT_FLOW_STUDY_2026Q2.md"},
        {"claim": "Positioning reads",
         "record": "arb->tracker handoff measured 8/8; within-foreign "
                   "split via SBL ledger; STREET-ONLY overlay caught "
                   "our own China Steel miss ex ante",
         "caveat": "Taiwan/Korea data depth; other markets thinner",
         "source": "EVENT_DATA_USEFULNESS_2026Q2.md"},
    ])


# ------------------------------------------------------------ composition

def build_pitch_pack(event_name: str, ann_date: str, eff_date: str,
                     as_of: str, predictions: pd.DataFrame,
                     flows: pd.DataFrame, crowding: pd.DataFrame,
                     t_mult_stats: dict[str, dict],
                     flags: pd.DataFrame, notes: str = "") -> dict:
    """Assemble the pack. predictions: ticker, name, change, confidence,
    margin_pct. flows: ticker, side, flow_usd_m, adv_days, bucket."""
    return {"event": event_name, "ann_date": ann_date,
            "eff_date": eff_date, "as_of": as_of,
            "predictions": predictions, "flows": flows,
            "crowding": crowding, "t_mult_stats": t_mult_stats,
            "flags": flags, "track_record": track_record(),
            "notes": notes}


def render_pitch_markdown(pack: dict) -> str:
    p = pack
    L = [f"# Pre-Event Analytics Pack — {p['event']}",
         f"*Prepared {p['as_of']} · announcement {p['ann_date']} · "
         f"effective {p['eff_date']}*",
         "", "*Every number below is generated from public data with a "
         "stated method; the track record section includes our misses. "
         "Point-in-time: nothing in this pack uses data after "
         f"{p['as_of']}.*", ""]

    L += ["## 1. Predicted changes",
          p["predictions"].to_markdown(index=False), ""]
    L += ["## 2. Expected flows",
          p["flows"].to_markdown(index=False), ""]

    L.append("## 3. What event days actually look like (measured)")
    for k, s in p["t_mult_stats"].items():
        if s.get("available"):
            L.append(f"- **{k}**: T-day volume median {s['median']}x "
                     f"normal (range {s['min']}-{s['max']}x, "
                     f"n={s['n']} measured 2026 events)")
        else:
            L.append(f"- **{k}**: no measured events yet (stated, not "
                     "guessed)")
    L.append("")

    L += ["## 4. Street positioning (short-ledger read, "
          f"pre-{p['ann_date']} data only)",
          p["crowding"].to_markdown(index=False), ""]

    L.append("## 5. Per-name risk flags")
    for _, r in p["flags"].iterrows():
        if r["flags"]:
            L.append(f"- **{r['ticker']}**: " + "; ".join(r["flags"]))
    L.append("")

    L += ["## 6. Our graded track record (misses included)",
          p["track_record"].to_markdown(index=False), ""]
    if p["notes"]:
        L += ["## Notes", p["notes"], ""]
    return "\n".join(L)


# ------------------------------------------------------- validation loop

def validate_pack(pack: dict, outcomes: pd.DataFrame,
                  realized_t_mult: dict[str, float] | None = None) -> dict:
    """Score the pack's claims after the event. outcomes: ticker,
    actual_change (bool). Returns per-claim scorecard — appended to the
    pack doc, wins and misses alike."""
    pred = pack["predictions"].merge(outcomes, on="ticker", how="left")
    pred["hit"] = (pred["change"].notna() &
                   pred["actual_change"].fillna(False))
    n_pred = int(pred["change"].notna().sum())
    n_hit = int(pred["hit"].sum())
    n_actual = int(outcomes["actual_change"].sum())
    hi = pred[pred["confidence"] == "HIGH"]
    scorecard = {
        "predictions": f"{n_hit}/{n_actual} actual changes called "
                       f"({n_pred} calls made)",
        "high_conf_precision": (f"{int(hi['hit'].sum())}/{len(hi)} "
                                "HIGH-confidence calls correct"
                                if len(hi) else "no HIGH calls"),
        "misses": pred[~pred["hit"] &
                       pred["change"].notna()]["ticker"].tolist(),
        "not_predicted": outcomes[outcomes["actual_change"] &
                                  ~outcomes["ticker"].isin(
                                      pred["ticker"])]["ticker"].tolist(),
    }
    if realized_t_mult:
        checks = []
        for key, realized in realized_t_mult.items():
            s = pack["t_mult_stats"].get(key, {})
            if s.get("available"):
                ok = s["min"] * 0.5 <= realized <= s["max"] * 1.5
                checks.append(f"{key}: forecast "
                              f"{s['min']}-{s['max']}x, realized "
                              f"{realized}x -> "
                              f"{'IN RANGE' if ok else 'OUT OF RANGE'}")
        scorecard["t_multiple_checks"] = checks
    return scorecard


def render_validation_markdown(scorecard: dict) -> str:
    L = ["## Post-event validation (the pack graded against reality)",
         f"- Predictions: {scorecard['predictions']}",
         f"- HIGH-confidence precision: "
         f"{scorecard['high_conf_precision']}"]
    if scorecard["misses"]:
        L.append(f"- Missed calls: {', '.join(scorecard['misses'])}")
    if scorecard["not_predicted"]:
        L.append(f"- Changes we did not predict: "
                 f"{', '.join(scorecard['not_predicted'])}")
    for c in scorecard.get("t_multiple_checks", []):
        L.append(f"- {c}")
    L.append("\n*This section is generated by the same code that built "
             "the pack — the desk grades itself before the client "
             "does.*")
    return "\n".join(L)
