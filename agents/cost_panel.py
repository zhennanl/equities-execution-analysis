"""
Cost-panel assembler — turns the execution simulator into a regression dataset.

Runs the fast Agent-4 per-day simulation across a grid of order sizes x all 8
algos x every available trading day, and records, for each execution, the
realized cost together with the conditioning variables a transaction cost model
regresses on (size %ADV, volatility, participation, spread, duration, side).

This is the "backtest & calibrate the cost model" workflow (GSET responsibility
#5) feeding the regression TCA (responsibilities #3/#6/#7): one call produces the
panel that `cost_model.fit_cost_model()` / `ab_test_with_controls()` consume.

Cost is *simulated* here (free data, no real fills); the panel schema and the
downstream regression are identical to what a real client-fill panel would use.
"""
from __future__ import annotations

from typing import Sequence

import numpy as np
import pandas as pd

_METRIC_IDX = {"slippage": 0, "impact": 1, "opportunity": 2, "total": 3}


def build_cost_panel(market_data, sizes_pct_adv: Sequence[float] = (1, 2, 5, 10, 15, 20),
                     urgency: str = "Medium", side: str = "Buy",
                     cost_metric: str = "total") -> pd.DataFrame:
    """Assemble a cost-regression panel from a MarketData object.

    Columns: date, algo, side, size_pct_adv, vol_ann, participation, spread_bps,
    duration_frac, fill_frac, cost_bps. One row per (day, size, algo).
    """
    from agents.agent4_performance_comparison import _sim_day_all
    from agents.agent3_algo_simulation import _historical_volume_weights
    from agents.agent1_market_data import MARKET_INFO
    from agents.order_ticket import OrderTicket

    bars_expected = MARKET_INFO[market_data.market]["bars"]
    intraday = market_data.intraday
    adv = float(market_data.adv_shares)
    metric_idx = _METRIC_IDX[cost_metric]
    ticket = OrderTicket(side=side)          # side-aware; no binding constraints

    dates = sorted(intraday.index.normalize().unique())
    rows = []
    for d in dates:
        day = intraday[intraday.index.normalize() == d]
        if len(day) < int(bars_expected * 0.8):
            continue
        n = len(day)

        # day-level annualized vol from 5-min log returns (gives cross-day variation)
        rets = np.log(day["Close"].astype(float)).diff().dropna()
        day_vol = float(rets.std() * np.sqrt(bars_expected * 252)) if len(rets) > 1 else float("nan")
        if not np.isfinite(day_vol) or day_vol <= 0:
            day_vol = float(market_data.realized_vol_ann)

        # day-level spread proxy (bps): mean intrabar range / close
        spread_bps = float(((day["High"] - day["Low"]) / day["Close"]).mean() * 10_000)
        day_volume = float(day["Volume"].sum())
        hist_curve, _ = _historical_volume_weights(intraday, d, n)

        for size in sizes_pct_adv:
            order_shares = adv * float(size) / 100.0
            res = _sim_day_all(day, order_shares, urgency, adv, day_vol,
                               hist_curve=hist_curve, ticket=ticket)
            if res is None:
                continue
            participation = order_shares / day_volume * 100 if day_volume > 0 else 0.0
            for algo, tup in res.items():
                cost = float(tup[metric_idx])
                duration = 0.15 if algo in ("MOC", "MOO") else 1.0
                rows.append({
                    "date": str(pd.Timestamp(d).date()), "algo": algo, "side": side,
                    "size_pct_adv": float(size), "vol_ann": day_vol,
                    "participation": float(participation), "spread_bps": spread_bps,
                    "duration_frac": duration, "fill_frac": float(tup[4]),
                    "cost_bps": cost,
                })
    panel = pd.DataFrame(rows)
    if len(panel):
        panel["sqrt_size_pct_adv"] = np.sqrt(np.clip(panel["size_pct_adv"], 0, None))
    return panel
