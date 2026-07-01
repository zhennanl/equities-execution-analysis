"""
Agent 8: Critic / Verification Agent

Independent second pass over Agent 5's recommendation -- the negotiation/
verification pattern from the multi-agent design write-up in
PROJECT_CONTEXT.md. Agent 5 picks a primary algo from a fixed rule table;
this agent doesn't re-derive that pick, it separately checks the pick
against cross-cutting concerns that Agent 5's rules don't cover, using
context Agent 5 never sees (Agent 7's earnings flag) plus a redundant
defense-in-depth re-check of a concern Agent 4/5 are already supposed to
enforce (fill-qualification), on the theory that a second, independently
written check is cheap insurance against the first one regressing.

Deliberately does NOT silently override memo.primary_algo -- it raises
findings for a human (or, in a fuller build, a downstream policy layer) to
act on. An automated system quietly overriding an execution decision based
on a secondary check with no visibility would be worse than the problem
it's solving.
"""

from dataclasses import dataclass, field
from typing import List
from agents.agent3_algo_simulation import FILL_QUALIFY_THRESH


@dataclass
class CriticFinding:
    severity: str   # "override" (material -- should give the analyst pause) | "note" (informational)
    message: str


@dataclass
class CriticReview:
    approved: bool                       # False if any "override"-severity finding exists
    findings: List[CriticFinding] = field(default_factory=list)


def review_recommendation(ctx, log=None) -> CriticReview:
    def _log(msg):
        if log:
            log(msg)

    findings: List[CriticFinding] = []
    approved = True

    memo, comp = ctx.memo, ctx.comp
    if memo is None or comp is None:
        return CriticReview(True, [CriticFinding(
            "note", "Critic review skipped — recommendation or comparison data unavailable."
        )])

    # -- Check 1: fill-qualification re-check (defense in depth) -------------
    # Agent 4/5 already gate best_algo/secondary selection on FILL_QUALIFY_THRESH
    # (see agent4_performance_comparison.py); this independently re-verifies
    # the *actual* primary that was selected still clears the bar, since
    # regime/urgency rules in Agent 5 (e.g. High urgency -> IS unconditionally)
    # can override the fill-qualified default and should be flagged if the
    # override lands on a thinly-filled algo.
    primary = memo.primary_algo
    if primary in comp.summary.index and "Avg Fill" in comp.summary.columns:
        avg_fill = float(comp.summary.loc[primary, "Avg Fill"])
        if avg_fill < FILL_QUALIFY_THRESH:
            approved = False
            findings.append(CriticFinding(
                "override",
                f"{primary} averages only {avg_fill:.0%} historical fill (below the "
                f"{FILL_QUALIFY_THRESH:.0%} qualification bar) but was still selected as primary — "
                f"likely a regime/urgency rule override. Confirm this is intentional, or fall back "
                f"to {memo.secondary_algo}."
            ))

    # -- Check 2: earnings-date risk vs. chosen urgency -----------------------
    # Agent 5 has no visibility into scheduled corporate events at all —
    # this is context only Agent 7 provides.
    earnings = ctx.earnings
    if earnings is not None and earnings.available and earnings.is_near_term and ctx.urgency != "High":
        approved = False
        findings.append(CriticFinding(
            "override",
            f"Earnings in ~{earnings.trading_days_until} trading day(s) "
            f"({earnings.next_earnings_date.date()}) but urgency is {ctx.urgency}, not High. "
            f"{earnings.risk_note}"
        ))

    # -- Check 3: degraded spread estimate compounding with large size -------
    pretrade = ctx.pretrade
    if pretrade is not None and pretrade.spread_reliability not in ("Normal", "N/A") and ctx.order_pct_adv >= 15:
        findings.append(CriticFinding(
            "note",
            f"Spread-cost estimate reliability is degraded for a {ctx.order_pct_adv}% ADV order — "
            f"size and spread-cost uncertainty compound here; treat the pre-trade cost range as "
            f"wider than shown."
        ))

    # -- Check 4: elevated order-flow toxicity (Agent 9's VPIN) --------------
    # Note-only, not an override: VPIN is a debated metric in the academic
    # literature (see agent9's module docstring) and this platform's reading
    # is a time-bar approximation of it, not a canonical tick-data VPIN --
    # too much uncertainty on both the methodology and the underlying number
    # to auto-flip an approval, but worth surfacing since it's context Agent
    # 5's rule table has no way to see.
    micro = ctx.microstructure
    if micro is not None and micro.vpin.available and micro.vpin.label in ("Elevated", "High"):
        findings.append(CriticFinding(
            "note",
            f"Order-flow toxicity (VPIN) reads {micro.vpin.label} ({micro.vpin.vpin_score:.2f}) — "
            f"{micro.vpin.note} Consider whether {primary}'s participation pattern still makes sense "
            f"if flow stays this one-sided."
        ))

    # -- Check 5: Kyle's lambda suggests the sqrt-law impact model may be off -
    # Agent 3/4's cost simulation uses a fixed eta=0.3 square-root impact
    # model for every ticker; Agent 9 independently estimates a ticker-
    # specific price-impact coefficient from the data itself. If that
    # estimate is both statistically significant and points to materially
    # higher sensitivity than the fixed model assumes for a sizeable order,
    # that's worth flagging rather than silently trusting the fixed constant.
    if (micro is not None and micro.kyle_lambda.available and abs(micro.kyle_lambda.t_stat) >= 2
            and micro.kyle_lambda.lambda_bps_per_pct_adv > 0 and ctx.order_pct_adv >= 10):
        findings.append(CriticFinding(
            "note",
            f"Kyle's lambda (Agent 9) is statistically significant and positive "
            f"({micro.kyle_lambda.lambda_bps_per_pct_adv:+.1f} bps per 1% of ADV net flow, "
            f"t={micro.kyle_lambda.t_stat:.1f}) — this name's data-estimated price sensitivity "
            f"may run ahead of the fixed eta=0.3 square-root model's assumption at this order size; "
            f"cross-check against the Almgren et al. (2005) calibrated estimate in Pre-Trade Analytics."
        ))

    if not findings:
        findings.append(CriticFinding("note", "No material issues found. Recommendation approved as-is."))

    _log(f"Critic review: approved={approved}, {len(findings)} finding(s)")
    return CriticReview(approved=approved, findings=findings)
