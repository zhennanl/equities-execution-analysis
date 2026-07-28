"""Step-4 execution insights — post-trade analytics for index
rebalance events (session 8i).

Assumes Step-3 dynamics are simulable/measurable (replay simulator +
auction derivation); extracts the insights that win next quarter's
mandate (lifecycle 4.2/4.4/4.5):

    tca_vs_estimate           realized slippage vs the PRE-TRADE
                              estimate, line by line — the
                              reconciliation most brokers don't send
    discretion_counterfactual each discretion choice graded against
                              the realized path: what did the
                              alternative cost?
    reversal_grade            did crowded names bounce as the
                              crowding read implied?
    update_priors             the event joins the library; before ->
                              after shift of every prior the next
                              pack will quote
    render_debrief            the client debrief: what we said vs
                              what happened, one document

Conventions: slippage in bps, SIGNED SO POSITIVE = COST to the
client (buy filled above benchmark, sell filled below). Every grade
is deterministic; misses ship."""
from __future__ import annotations

import numpy as np
import pandas as pd

NEUTRAL_BPS = 5.0          # |gain| below this = NEUTRAL, not a win
WITHIN_FRAC = 0.5          # realized within 50% of estimate = WITHIN
REVERSAL_CONFIRM_BPS = 50.0  # bounce needed to confirm a crowded read


def _cost_bps(side: str, px: float, bench: float) -> float:
    """Positive = worse than benchmark for the client."""
    raw = (px / bench - 1) * 1e4
    return raw if side == "Buy" else -raw


def tca_vs_estimate(lines: pd.DataFrame) -> pd.DataFrame:
    """4.2 — per line: realized slippage vs the close benchmark AND
    vs the pre-trade estimate. Columns in: ticker, side, qty_shares,
    avg_px, close_px, est_cost_bps. The differentiator column is
    vs_estimate_bps: we promised a number; here is the delta."""
    rows = []
    for _, r in lines.iterrows():
        real = _cost_bps(r["side"], r["avg_px"], r["close_px"])
        delta = real - r["est_cost_bps"]
        est = abs(r["est_cost_bps"])
        verdict = ("WITHIN estimate"
                   if abs(delta) <= max(est * WITHIN_FRAC, NEUTRAL_BPS)
                   else "BETTER than estimate" if delta < 0
                   else "WORSE than estimate")
        rows.append({"ticker": r["ticker"], "side": r["side"],
                     "qty_shares": r["qty_shares"],
                     "realized_bps": round(real, 1),
                     "est_bps": round(r["est_cost_bps"], 1),
                     "vs_estimate_bps": round(delta, 1),
                     "verdict": verdict})
    df = pd.DataFrame(rows)
    if len(df):
        w = df["qty_shares"] / df["qty_shares"].sum()
        df.attrs["portfolio_realized_bps"] = round(
            float((df["realized_bps"] * w).sum()), 1)
        df.attrs["portfolio_vs_estimate_bps"] = round(
            float((df["vs_estimate_bps"] * w).sum()), 1)
    return df


def discretion_counterfactual(decisions: pd.DataFrame) -> pd.DataFrame:
    """4.4/4.5 — grade each Step-2 discretion choice against the
    realized path. Columns in: ticker, side, decision (WORK AHEAD /
    WAIT-MOC / PRE-POSITION / MOC ONLY), worked_frac (0..1 actually
    worked away from close), pre_close_drift_bps (price move from
    decision window into the close, SIGNED: positive = price rose).

    The counterfactual is mechanical: working a Sell ahead of a fall
    (drift < 0) captured |drift| x worked_frac bps vs MOC; working
    ahead of a rise gave it up. Mirror for buys. Verdict: CORRECT /
    INCORRECT / NEUTRAL (<5 bps either way); MOC ONLY lines grade
    the ENVELOPE-GRANT question instead (what discretion would have
    been worth)."""
    rows = []
    for _, r in decisions.iterrows():
        drift = r["pre_close_drift_bps"]
        # Gain (client-positive bps) of the worked fraction vs pure
        # MOC, with worked fills approximated at the decision-window
        # price (replay-simulator bars refine this). Sell worked
        # ahead of a FALL (drift<0): early sells printed higher ->
        # gain > 0. Buy pre-positioned ahead of a RISE (drift>0):
        # early buys printed lower -> gain > 0.
        gain = r["worked_frac"] * (drift if r["side"] == "Buy"
                                   else -drift)
        if (r["decision"] == "MOC ONLY"
                or str(r["decision"]).startswith("WAIT")):
            # nothing was worked — grade the ROAD NOT TAKEN at a
            # standard 30% fraction: was staying at the close right?
            hypo = (-drift if r["side"] == "Sell" else drift) * 0.3
            verdict = ("WORKING WOULD HAVE HELPED"
                       if hypo > NEUTRAL_BPS else
                       "staying MOC was right"
                       if hypo < -NEUTRAL_BPS else "NEUTRAL")
            rows.append({"ticker": r["ticker"], "side": r["side"],
                         "decision": r["decision"],
                         "cf_gain_bps": round(hypo, 1),
                         "verdict": verdict})
            continue
        verdict = ("CORRECT" if gain > NEUTRAL_BPS else
                   "INCORRECT" if gain < -NEUTRAL_BPS else "NEUTRAL")
        rows.append({"ticker": r["ticker"], "side": r["side"],
                     "decision": r["decision"],
                     "cf_gain_bps": round(gain, 1),
                     "verdict": verdict})
    return pd.DataFrame(rows)


def reversal_grade(names: pd.DataFrame) -> pd.DataFrame:
    """4.4 — did the crowding read's implication hold? Columns in:
    ticker, crowding_band (HIGH/MED/LOW), t_move_bps (event-day move,
    signed), post_reversal_bps (T+1..T+5 move, signed). A HIGH-crowd
    delete implies an enlarged covering bounce: reversal opposite in
    sign to the T-day move and >= REVERSAL_CONFIRM_BPS. LOW implies a
    modest bounce. Output: per-name AGREE/DISAGREE + the hit rate the
    next pack quotes."""
    rows = []
    for _, r in names.iterrows():
        bounced = (np.sign(r["post_reversal_bps"])
                   == -np.sign(r["t_move_bps"])
                   and abs(r["post_reversal_bps"])
                   >= REVERSAL_CONFIRM_BPS)
        if r["crowding_band"] == "HIGH":
            ok = bounced
            expect = "enlarged covering bounce"
        elif r["crowding_band"] == "LOW":
            ok = not bounced
            expect = "modest reversal"
        else:
            ok = True
            expect = ("no strong implication (MED)"
                      if r["crowding_band"] == "MED"
                      else "no read — ungraded")
        rows.append({"ticker": r["ticker"],
                     "crowding_band": r["crowding_band"],
                     "t_move_bps": r["t_move_bps"],
                     "post_reversal_bps": r["post_reversal_bps"],
                     "expected": expect,
                     "grade": "AGREE" if ok else "DISAGREE"})
    df = pd.DataFrame(rows)
    if len(df):
        # only HIGH/LOW carry a falsifiable implication — MED and
        # no-data names never count toward the quoted hit rate
        strong = df[df["crowding_band"].isin(["HIGH", "LOW"])]
        df.attrs["hit_rate"] = (
            f"{(strong['grade'] == 'AGREE').sum()}/{len(strong)}"
            if len(strong) else "n/a")
    return df


def update_priors(event_cache: dict,
                  realized: list[dict]) -> pd.DataFrame:
    """4.5 — the event joins the library. realized: [{provider,
    side, t_mult, auction_share, reversal_frac}]. Returns the
    before/after table of every prior the next pack quotes (the
    caller persists the cache)."""
    rows = []
    evs = event_cache.setdefault("events", [])
    for key, field in (("t_mult", "t_mult"),
                       ("auction_share", "auction_share"),
                       ("reversal_frac", "reversal_frac")):
        old = [e[field] for e in evs if field in e
               and e[field] is not None]
        new_vals = [r[field] for r in realized
                    if r.get(field) is not None]
        merged = old + new_vals
        rows.append({
            "prior": key,
            "before_median": (round(float(np.median(old)), 2)
                              if old else np.nan),
            "n_before": len(old),
            "after_median": (round(float(np.median(merged)), 2)
                             if merged else np.nan),
            "n_after": len(merged)})
    for r in realized:
        evs.append(dict(r))
    return pd.DataFrame(rows)


def render_debrief(tca: pd.DataFrame, cf: pd.DataFrame,
                   rev: pd.DataFrame, priors: pd.DataFrame,
                   title: str, as_of: str, notes: str = "") -> str:
    """The client debrief: what we said vs what happened, misses
    included — the artifact next quarter's RFP asks for."""
    L = [f"# {title}",
         f"*Generated {as_of} by agents/execution_insights.py — "
         "lifecycle Step 4. Signed bps, positive = cost. Misses "
         "ship.*", ""]
    L.append("## 4.2 TCA vs the pre-trade estimate (what we "
             "promised vs what printed)\n")
    L.append(tca.to_markdown(index=False))
    L.append(f"\nPortfolio: realized "
             f"{tca.attrs.get('portfolio_realized_bps', 'n/a')} bps "
             f"vs estimate delta "
             f"{tca.attrs.get('portfolio_vs_estimate_bps', 'n/a')} "
             "bps (qty-weighted).")
    L.append("\n## 4.4a Discretion choices, graded against the "
             "realized path\n")
    L.append(cf.to_markdown(index=False))
    L.append("\n## 4.4b Reversal vs the crowding read\n")
    L.append(rev.to_markdown(index=False))
    L.append(f"\nCrowding-implication hit rate: "
             f"{rev.attrs.get('hit_rate', 'n/a')}.")
    L.append("\n## 4.5 Priors updated (what the next pack quotes)\n")
    L.append(priors.to_markdown(index=False))
    if notes:
        L.append(f"\n## Notes\n\n{notes}")
    return "\n".join(L) + "\n"
