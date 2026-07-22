"""Pre-trade desk pack + run library for Page 1 (assessment P-A and P-C).

P-A — the institutional pre-trade report: every parent order at a desk carries
a one-page pre-trade summary (side/size, expected cost band, capacity, risk
flags, recommendation + independent review). This module renders that from
objects the pipeline already computes — verdict first, exportable as text.

P-C — the run library: every pipeline run records (conditions, chosen algo,
predicted cost band, realized cost) so the platform accumulates its own
predicted-vs-realized history — the expected-cost-benchmark loop a
quantitative execution consultant runs on client flow. Same design as
Page 2's event library: JSON, keyed update-not-duplicate, medians honest
about n.
"""

from __future__ import annotations

import datetime as _dt
import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

DEFAULT_RUN_LIBRARY_PATH = Path(__file__).resolve().parent.parent / "data" / "run_library.json"

# Capacity traffic light (days to complete at the chosen urgency's participation)
CAPACITY_GREEN_MAX_DAYS = 1.0
CAPACITY_RED_MIN_DAYS = 3.0


@dataclass
class DeskVerdict:
    headline: str
    flag: str                    # GREEN / AMBER / RED (capacity-led)
    days_to_complete: float
    expected_bps: float = None
    low_bps: float = None
    high_bps: float = None
    n_critic_findings: int = 0
    earnings_flag: str = ""


def _cost_row(pretrade, algo: str):
    try:
        rng = pretrade.expected_cost_range
        row = rng.loc[algo]
        return (float(row["Expected (bps)"]), float(row["Low (bps)"]), float(row["High (bps)"]))
    except Exception:
        return (None, None, None)


def build_desk_verdict(memo, critic, pretrade, sim, order_shares: float,
                       adv_shares: float, urgency: str, earnings=None) -> DeskVerdict:
    exp, lo, hi = _cost_row(pretrade, memo.primary_algo)
    days = float(getattr(pretrade, "days_at_chosen_urgency", 0.0) or 0.0)
    flag = ("GREEN" if days <= CAPACITY_GREEN_MAX_DAYS
            else "RED" if days > CAPACITY_RED_MIN_DAYS else "AMBER")
    nfind = len(getattr(critic, "findings", []) or [])
    e_flag = ""
    if earnings is not None and getattr(earnings, "warning", None):
        e_flag = str(earnings.warning)
    side = getattr(sim, "side", "Buy").upper()
    pct = order_shares / adv_shares * 100 if adv_shares else 0.0
    icon = {"GREEN": "🟢", "AMBER": "🟡", "RED": "🔴"}[flag]
    cost_txt = (f"expected {exp:+.1f} bps (band {lo:+.1f}…{hi:+.1f})"
                if exp is not None else "expected cost band unavailable")
    headline = (f"{side} {order_shares:,.0f} sh ({pct:.1f}% ADV, {urgency} urgency) — "
                f"{memo.primary_algo} (alt: {memo.secondary_algo}) · {cost_txt} · "
                f"capacity {days:.1f} day(s) {icon}"
                + (f" · ⚠️ {nfind} critic finding(s)" if nfind else "")
                + (" · 📅 earnings risk" if e_flag else ""))
    return DeskVerdict(headline=headline, flag=flag, days_to_complete=round(days, 2),
                       expected_bps=exp, low_bps=lo, high_bps=hi,
                       n_critic_findings=nfind, earnings_flag=e_flag)


def pretrade_card_text(ticker: str, market: str, memo, critic, pretrade, regime,
                       sim, order_shares: float, adv_shares: float, urgency: str,
                       verdict: DeskVerdict, benchmark_target: str = "Arrival",
                       earnings=None) -> str:
    side = getattr(sim, "side", "Buy").upper()
    pct = order_shares / adv_shares * 100 if adv_shares else 0.0
    L = [
        "=" * 68,
        f"PRE-TRADE REPORT — {ticker} ({market})   generated {_dt.date.today()}",
        "=" * 68,
        f"ORDER        : {side} {order_shares:,.0f} sh = {pct:.1f}% ADV · urgency {urgency} "
        f"· benchmark {benchmark_target}",
        f"RECOMMENDED  : {memo.primary_algo} (alternative: {memo.secondary_algo})",
        f"EXPECTED COST: " + (f"{verdict.expected_bps:+.1f} bps "
                              f"(low {verdict.low_bps:+.1f} / high {verdict.high_bps:+.1f}) — "
                              f"{pretrade.cost_range_method}"
                              if verdict.expected_bps is not None else "band unavailable"),
        f"EXPLICIT     : ~{pretrade.explicit_cost_bps:.1f} bps ({market} schedule)"
        if getattr(pretrade, "explicit_cost_bps", None) is not None else "EXPLICIT     : n/a",
        f"SPREAD       : ~{pretrade.spread_bps:.1f} bps blended estimate "
        f"({pretrade.spread_reliability})" if pretrade.spread_bps is not None
        else "SPREAD       : unavailable",
        f"CAPACITY     : {verdict.days_to_complete:.1f} day(s) at the {urgency}-urgency "
        f"participation — flag {verdict.flag}",
        f"REGIME       : vol {regime.vol_label} · volume {regime.volume_label} · "
        f"trend {regime.trend_label}",
    ]
    if verdict.earnings_flag:
        L.append(f"EVENT RISK   : {verdict.earnings_flag}")
    fins = list(getattr(critic, "findings", []) or [])
    if fins:
        L.append("-" * 68)
        L.append(f"CRITIC ({len(fins)} finding(s) — review before routing):")
        for f in fins:
            L.append(f"  • {getattr(f, 'message', str(f))}")
    L += ["-" * 68,
          "Simulated pre-trade estimate on historical bars — impact is modeled",
          "(sqrt-law + Almgren-2005 cross-check); see Post-Trade TCA for realized.",
          "=" * 68]
    return "\n".join(L)


# ── Run library (P-C) ──────────────────────────────────────────────────────

def record_run(*, ticker: str, market: str, side: str, order_pct_adv: float,
               urgency: str, algo: str, predicted_bps, realized_bps,
               sim_day: str, path: Path = DEFAULT_RUN_LIBRARY_PATH) -> dict:
    """One row per pipeline run; keyed update on (ticker, sim_day, algo,
    order_pct_adv, urgency, side) so Streamlit reruns don't duplicate."""
    row = {
        "ticker": ticker, "market": market, "side": side,
        "order_pct_adv": round(float(order_pct_adv), 3), "urgency": urgency,
        "algo": algo, "sim_day": sim_day,
        "predicted_bps": None if predicted_bps is None else round(float(predicted_bps), 2),
        "realized_bps": None if realized_bps is None else round(float(realized_bps), 2),
        "recorded_at": _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds"),
    }
    key = ("ticker", "sim_day", "algo", "order_pct_adv", "urgency", "side")
    rows = load_runs(path)
    rows = [r for r in rows if tuple(r.get(k) for k in key) != tuple(row[k] for k in key)]
    rows.append(row)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(rows, indent=1), encoding="utf-8")
    return row


def load_runs(path: Path = DEFAULT_RUN_LIBRARY_PATH) -> list[dict]:
    if not Path(path).exists():
        return []
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception:
        return []


def run_stats(path: Path = DEFAULT_RUN_LIBRARY_PATH) -> dict:
    """Predicted-vs-realized tracking across recorded runs: n, mean error
    (bias, + = model under-predicts cost), MAE, and n by algo."""
    rows = load_runs(path)
    out = {"n": len(rows)}
    pairs = [(r["realized_bps"] - r["predicted_bps"])
             for r in rows
             if isinstance(r.get("realized_bps"), (int, float))
             and isinstance(r.get("predicted_bps"), (int, float))]
    out["n_scored"] = len(pairs)
    if pairs:
        out["bias_bps"] = round(float(np.mean(pairs)), 2)
        out["mae_bps"] = round(float(np.mean(np.abs(pairs))), 2)
    by_algo = {}
    for r in rows:
        by_algo[r.get("algo", "?")] = by_algo.get(r.get("algo", "?"), 0) + 1
    out["by_algo"] = by_algo
    return out
