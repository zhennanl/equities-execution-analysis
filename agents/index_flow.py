"""Index-event flow simulation + optimal execution strategy — the module
the two backtests pointed at (session 6z).

The screener predicts WHO changes; this module answers the desk's next
two questions:

1. HOW MUCH trades — and not just in the adds/deletes. When names enter,
   every CONTINUING member's weight is diluted and trackers trim it; when
   names leave, everyone is topped up. These weight-adjustment flows are
   individually small but collectively they are the other half of the
   event — and an index rebalance is SELF-FINANCING by construction
   (total buys ≈ total sells), which this module verifies as an
   arithmetic identity rather than assumes.

2. HOW to execute each flow — by feeding the flow sizes into the existing
   S1-S4 strategy frontier (agent14) on a calibrated pressure-reversal
   path: flows too small to matter go 100% to the close (the tracker's
   zero-tracking default); flows large in ADV-days get the full
   cost-vs-tracking frontier and a tracking-tolerance-constrained
   argmin. The optimal strategy is per-NAME, because the same event
   produces a 0.02-ADV-day TSMC trim and a 3-ADV-day add in the same
   basket.

Everything runs on data we have: FF caps (weights), ADV (days-to-trade),
the event library's observed T-day volume multiple (path calibration),
and a passive-AUM input that is the desk's estimate, never a claim.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from types import SimpleNamespace

import numpy as np
import pandas as pd

# ADV-day thresholds for execution buckets
BUCKET_MOC = 0.20        # below: 100% close auction, no footprint concern
BUCKET_WORK = 1.00       # below: work intraday + MOC remainder
DEFAULT_PRESSURE_BPS = 500   # calibrated path: pressure into T (50% reverses)
DEFAULT_T_VOL_MULT = 5.0


def simulate_index_flow(universe: pd.DataFrame, members_before: set,
                        adds: set, deletes: set,
                        passive_aum_usd: float) -> dict:
    """Per-name passive flow for a review: deletes sell out, adds buy in,
    continuing members trim/top-up to their NEW weights.

    universe: ticker, full_mktcap_usd, free_float_frac, adv_usd.
    Returns {"flows": df, "checks": {...}} — flows has w_before, w_after,
    flow_usd (signed, + = buy), adv_days, bucket."""
    u = universe.set_index("ticker")
    u["ff_cap"] = u["full_mktcap_usd"] * u["free_float_frac"]
    before = set(members_before)
    after = (before - set(deletes)) | set(adds)
    tot_b = float(u.loc[sorted(before), "ff_cap"].sum())
    tot_a = float(u.loc[sorted(after), "ff_cap"].sum())
    rows = []
    for t in sorted(before | after):
        wb = float(u.loc[t, "ff_cap"] / tot_b) if t in before else 0.0
        wa = float(u.loc[t, "ff_cap"] / tot_a) if t in after else 0.0
        flow = (wa - wb) * passive_aum_usd
        adv = float(u.loc[t, "adv_usd"])
        days = abs(flow) / adv if adv > 0 else np.inf
        kind = ("ADD" if t in adds else "DELETE" if t in deletes
                else "reweight")
        rows.append({"ticker": t, "kind": kind,
                     "w_before_pct": round(wb * 100, 3),
                     "w_after_pct": round(wa * 100, 3),
                     "flow_usd": round(flow, 0),
                     "side": "Buy" if flow > 0 else "Sell",
                     "adv_days": round(days, 2),
                     "bucket": ("MOC" if days < BUCKET_MOC else
                                "WORK+MOC" if days < BUCKET_WORK else
                                "MULTI-DAY")})
    f = pd.DataFrame(rows).sort_values("flow_usd", key=abs,
                                       ascending=False).reset_index(drop=True)
    buys = float(f.loc[f.flow_usd > 0, "flow_usd"].sum())
    sells = float(-f.loc[f.flow_usd < 0, "flow_usd"].sum())
    checks = {
        "gross_turnover_usd": round(buys + sells, 0),
        "buys_usd": round(buys, 0), "sells_usd": round(sells, 0),
        "self_financing_gap_pct": round(abs(buys - sells)
                                        / max(buys + sells, 1) * 100, 2),
        "turnover_pct_of_aum": round((buys + sells) / passive_aum_usd * 100, 2),
        "n_add": int((f.kind == "ADD").sum()),
        "n_delete": int((f.kind == "DELETE").sum()),
        "n_reweight": int((f.kind == "reweight").sum()),
        "reweight_share_of_turnover": round(
            float(f.loc[f.kind == "reweight", "flow_usd"].abs().sum())
            / max(buys + sells, 1), 3),
    }
    return {"flows": f, "checks": checks}


# ── calibrated event path for the strategy frontier ────────────────────────

def _event_path(pressure_bps: float = DEFAULT_PRESSURE_BPS,
                t_vol_mult: float = DEFAULT_T_VOL_MULT,
                adv_shares: float = 1_000_000.0,
                sigma_daily: float = 0.02,
                reversal_frac: float = 0.5):
    """Pressure-into-T, partial-reversal path (the canonical index-event
    shape from the literature and our event studies), calibrated by the
    magnitude arguments — the same SimpleNamespace contract agent14
    consumes. Price base 100. reversal_frac: share of the pressure that
    unwinds post-T (0.5 canonical; crowding-adjusted upstream)."""
    rel = np.arange(-10, 11)
    p = pressure_bps / 1e4
    closes = np.concatenate([
        np.full(5, 100.0),                                   # -10..-6
        100 * (1 + np.linspace(0, p, 6)),                    # -5..0 pressure
        100 * (1 + p - np.linspace(0, p * reversal_frac, 10)),  # +1..+10
    ])
    ab = np.ones(len(rel)); ab[rel == 0] = t_vol_mult
    return SimpleNamespace(rel_days=rel, norm_price=closes * 100.0,
                           price_at_T=1.0, ab_vol=ab,
                           est_avg_volume=adv_shares,
                           est_sigma_daily=sigma_daily,
                           car=np.zeros(len(rel)),
                           event_dates=pd.bdate_range("2026-06-04",
                                                      periods=len(rel)))


def recommend_execution(flows: pd.DataFrame,
                        tracking_tolerance_bps: float = 50.0,
                        eta: float = 0.3,
                        pressure_bps: float = DEFAULT_PRESSURE_BPS,
                        t_vol_mult: float = DEFAULT_T_VOL_MULT,
                        crowding: dict[str, str] | None = None) -> dict:
    """Per-name execution recommendation.

    MOC bucket        -> 100% close auction (S1): zero tracking, footprint
                         immaterial at <0.2 ADV-days.
    WORK+MOC bucket   -> intraday working + MOC remainder (S2-lite).
    MULTI-DAY bucket  -> run the FULL S1-S4 frontier (agent14) on the
                         calibrated path at the name's size and pick the
                         cheapest strategy whose |tracking| is within the
                         client's tolerance — the frontier decides, per
                         name, not a blanket rule.

    crowding: optional {ticker: HIGH/MED/LOW} from the short-ledger
    crowding gauge (agents.event_data). A crowded name has spent part of
    its pressure before T and carries a larger covering bounce, so its
    frontier runs on a crowding-adjusted path (v1 heuristic multipliers,
    documented in event_data.CROWDING_PATH_ADJ)."""
    from agents.agent14_rebalance_strategist import analyze_strategies
    recs, frontiers = [], {}
    for _, r in flows.iterrows():
        if r["bucket"] == "MOC":
            recs.append({"ticker": r["ticker"], "bucket": r["bucket"],
                         "strategy": "S1 100% MOC",
                         "why": f"{r['adv_days']:.2f} ADV-days — footprint "
                                "immaterial, take the benchmark print"})
            continue
        if r["bucket"] == "WORK+MOC":
            recs.append({"ticker": r["ticker"], "bucket": r["bucket"],
                         "strategy": "work 30-50% intraday + MOC remainder",
                         "why": f"{r['adv_days']:.2f} ADV-days — split the "
                                "footprint between tape and auction"})
            continue
        # MULTI-DAY: full frontier at this name's size
        adv_sh = 1_000_000.0
        band = (crowding or {}).get(r["ticker"])
        if band:
            from agents.event_data import crowding_adjusted_params
            p_adj, rev = crowding_adjusted_params(pressure_bps, band)
        else:
            p_adj, rev = pressure_bps, 0.5
        es = _event_path(p_adj, t_vol_mult, adv_shares=adv_sh,
                         reversal_frac=rev)
        order_sh = r["adv_days"] * adv_sh
        ana = analyze_strategies(es, side=r["side"], order_shares=order_sh,
                                 eta=eta)
        fr = ana.frontier.copy()
        frontiers[r["ticker"]] = fr
        ok = fr[fr["|Tracking diff| (bps)"].abs() <= tracking_tolerance_bps]
        pick = (ok if len(ok) else fr).sort_values("Cost vs decision (bps)").iloc[0]
        recs.append({"ticker": r["ticker"], "bucket": r["bucket"],
                     "strategy": str(pick["Strategy"]),
                     "why": f"{r['adv_days']:.2f} ADV-days — frontier pick: "
                            f"cost {pick['Cost vs decision (bps)']:.0f} bps, tracking "
                            f"{pick['|Tracking diff| (bps)']:.0f} bps "
                            f"(tol {tracking_tolerance_bps:.0f})"
                            + ("" if len(ok) else
                               " [NO strategy met tolerance — cheapest shown; "
                               "escalate to client]")})
    return {"recommendations": pd.DataFrame(recs), "frontiers": frontiers,
            "note": f"Frontier path calibrated at {pressure_bps:.0f} bps "
                    f"pressure / {t_vol_mult:.0f}x T-day volume (override "
                    "from the event library when it has history). Impact "
                    f"eta={eta}. Tracking tolerance is the CLIENT's number."}
