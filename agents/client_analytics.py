"""
Client-facing analytics — the automatable half of the two most senior
responsibilities:

  * benchmark_scorecard()  (R2) — grades a realized execution against its
    benchmarks, the model-expected cost, and the client's own history, with a
    continuous-improvement delta (realized vs typical). This is the "client
    performance benchmark + continuous improvement" framing, computed.
  * client_report()        (R1) — renders a client-ready markdown one-pager
    (headline, benchmark table, liquidity/microstructure read, flags,
    recommendation) so the consultant walks into the client conversation with
    the analysis already prepared, not the plumbing.

Everything is a pure function of values passed in — trivially testable and
decoupled from the simulation objects.
"""
from __future__ import annotations

from typing import Optional, Sequence

import numpy as np
import pandas as pd


def _verdict(slip_bps: float, tol: float = 1.0) -> str:
    if slip_bps < -tol:
        return "outperformed"
    if slip_bps > tol:
        return "underperformed"
    return "in line"


def _grade(percentile: float) -> str:
    # lower percentile within own history = cheaper than usual = better
    return "A" if percentile <= 25 else "B" if percentile <= 50 else "C" if percentile <= 75 else "D"


def benchmark_scorecard(realized_cost_bps: float,
                        benchmark_slippages: dict,
                        model_expected_bps: Optional[float] = None,
                        hist_total_costs: Optional[Sequence[float]] = None) -> dict:
    """Grade a realized execution.

    benchmark_slippages: {benchmark_name: slippage_bps} (positive = worse).
    model_expected_bps:  the cost model's conditional expectation for this order.
    hist_total_costs:    the algo's own historical total-cost distribution.
    """
    rows = [{"benchmark": name, "slippage_bps": round(float(bps), 2),
             "verdict": _verdict(float(bps))}
            for name, bps in benchmark_slippages.items()]
    table = pd.DataFrame(rows)

    model_delta = None
    if model_expected_bps is not None:
        model_delta = round(float(realized_cost_bps) - float(model_expected_bps), 2)

    percentile = improvement_bps = grade = None
    if hist_total_costs is not None and len(hist_total_costs) > 0:
        h = np.asarray(hist_total_costs, dtype=float)
        percentile = round(float((h <= realized_cost_bps).mean() * 100), 1)
        improvement_bps = round(float(np.median(h) - realized_cost_bps), 2)
        grade = _grade(percentile)

    # headline verdict
    if grade is not None:
        headline = (f"Grade {grade}: this execution ranked in the "
                    f"{percentile:.0f}th percentile of the algo's own history "
                    f"({'cheaper' if percentile <= 50 else 'costlier'} than usual, "
                    f"{improvement_bps:+.1f} bps vs the typical fill).")
    elif model_delta is not None:
        headline = (f"Realized cost was {model_delta:+.1f} bps vs the model-expected "
                    f"cost for an order this size/condition "
                    f"({'better' if model_delta < 0 else 'worse'} than modelled).")
    else:
        beat = sum(1 for r in rows if r["verdict"] == "outperformed")
        headline = f"Outperformed {beat} of {len(rows)} benchmarks."

    return {"table": table, "model_expected_bps": model_expected_bps,
            "model_delta_bps": model_delta, "percentile": percentile,
            "improvement_bps": improvement_bps, "grade": grade, "headline": headline}


def client_report(context: dict) -> str:
    """Render a client-ready markdown one-pager from a context dict. Only the
    sections whose keys are present are emitted, so partial context still yields
    a clean report.

    Recognised keys: ticker, market, side, order_pct_adv, algo, urgency,
    realized_cost_bps, arrival_slip_bps, benchmarks(dict), spreads(dict of
    name->bps), amihud_impact_bps_per_1m, price_limit(dict), auction(dict),
    scorecard(dict from benchmark_scorecard), recommendation(str),
    flags(list[str]).
    """
    g = context.get
    lines: list[str] = []
    tick = g("ticker", "—")
    mkt = g("market", "")
    lines.append(f"# Execution Quality Review — {tick}" + (f" ({mkt})" if mkt else ""))

    meta = []
    if g("side"): meta.append(f"**Side:** {g('side')}")
    if g("order_pct_adv") is not None: meta.append(f"**Size:** {g('order_pct_adv'):g}% ADV")
    if g("algo"): meta.append(f"**Algo:** {g('algo')}")
    if g("urgency"): meta.append(f"**Urgency:** {g('urgency')}")
    if meta:
        lines.append(" · ".join(meta))

    sc = g("scorecard")
    if sc and sc.get("headline"):
        lines.append("\n## Headline\n" + sc["headline"])

    bm = g("benchmarks")
    if bm:
        lines.append("\n## Benchmark performance (slippage, bps; negative = better)\n")
        lines.append("| Benchmark | Slippage (bps) | Verdict |")
        lines.append("|---|---:|---|")
        for name, bps in bm.items():
            lines.append(f"| {name} | {float(bps):+.2f} | {_verdict(float(bps))} |")

    liq = []
    sp = g("spreads")
    if sp:
        liq.append("Effective spread estimates (bps): "
                   + ", ".join(f"{k} {float(v):.1f}" for k, v in sp.items() if v is not None) + ".")
    if g("amihud_impact_bps_per_1m") is not None:
        liq.append(f"Amihud price impact ≈ {g('amihud_impact_bps_per_1m'):.2f} bps per $1M traded.")
    au = g("auction")
    if au and au.get("close_share_pct") is not None:
        liq.append(f"Closing-auction concentration ≈ {au['close_share_pct']:.0f}% of daily volume"
                   + (" (high — consider sourcing size in the close)." if au.get("concentrated") else "."))
    if liq:
        lines.append("\n## Liquidity & microstructure\n" + " ".join(liq))

    flags = list(g("flags", []) or [])
    pl = g("price_limit")
    if pl and pl.get("severity") in ("BLOCK", "WARN"):
        flags.append(f"[{pl['severity']}] {pl['message']}")
    if flags:
        lines.append("\n## Flags\n" + "\n".join(f"- {f}" for f in flags))

    if g("recommendation"):
        lines.append("\n## Recommendation\n" + g("recommendation"))

    lines.append("\n---\n*Generated from the execution-analytics platform. Costs are "
                 "simulated on free market data; methodology transfers to real client "
                 "fills unchanged.*")
    return "\n".join(lines)
