"""Counterfactual impact propagator — the answer to the counterfactual-tape
problem for strategy-switch simulations (motivated by a GSET interviewer
question; see docs/COUNTERFACTUAL_IMPACT_MODEL.md).

The problem: replaying a DIFFERENT strategy over historical bars prices each
fill against a tape that never felt that strategy's impact. The Level-1 fix
(already platform-wide) adds modeled impact as a labeled cost overlay — but
the PATH never moves, so an aggressive morning never makes the afternoon more
expensive. This module is Level 2: perturb the simulated price path with the
accumulated footprint of the simulation's own fills,

    perturb(t) [bps] = sum over own fills i<=t of
        perm_i + temp_i * 0.5^((t - bar_i) / half_life_bars)

where each fill's instantaneous impact eta*sigma_d*sqrt(q_i/ADV) splits into
a permanent fraction (information: never decays) and a temporary fraction
(liquidity concession: decays with a half-life), signed adverse to the order's
side. Strictly causal: a fill perturbs bars at and after itself, never before.

Modeling conventions (each a disclosed choice, not a hidden assumption):
  * Schedule-invariant perturbation: fills' SIZES/TIMES come from the raw-tape
    simulation; only their PRICES are adjusted. (A fully price-reactive
    re-simulation is the next fidelity level; for volume/time-driven schedules
    the approximation is exact by construction.)
  * A fill's own instantaneous impact is NOT re-charged here — that is the
    existing Level-1 overlay. The propagator adds only the CROSS effect of
    earlier fills on later fills, so the two compose without double counting.
  * On a synthetic replay (this platform) the tape contains no own impact. On
    a REAL account's history the tape already embeds the original strategy's
    footprint — a naive overlay then double-counts where old and new
    strategies overlap. That de-impacting caveat is documented, not modeled.

Because every parameter is an assumption, the deliverable is a SENSITIVITY
BAND across a kernel grid, with a robustness verdict — never a point estimate.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import numpy as np
import pandas as pd

from agents.agent1_market_data import MarketData, MARKET_INFO
from agents.agent3_algo_simulation import simulate_with_interventions, IMPACT_ETA
from agents.order_ticket import side_sign

# Literature-anchored default grid (Almgren-2005-era eta magnitudes; decay
# half-lives spanning the 5-30 minute reversion evidence at 5-min bars).
DEFAULT_ETA_GRID = (0.3, 0.45, 0.6)
DEFAULT_HALF_LIFE_GRID = (2.0, 6.0)          # bars (= 10 and 30 minutes)
DEFAULT_PERM_FRAC = 0.4                       # ~Almgren permanent/total split


@dataclass
class ImpactKernel:
    eta: float = IMPACT_ETA
    perm_frac: float = DEFAULT_PERM_FRAC      # share of instantaneous impact that persists
    half_life_bars: float = 6.0               # temporary component's decay half-life

    def label(self) -> str:
        return f"η={self.eta:.2f}, perm={self.perm_frac:.0%}, t½={self.half_life_bars:g} bars"


def propagate_impact(fill_bars: np.ndarray, fill_shares: np.ndarray, n_bars: int,
                     sigma_daily: float, adv_shares: float, side: str,
                     kernel: ImpactKernel) -> np.ndarray:
    """Per-bar cumulative price perturbation (bps, signed: positive = price
    pushed UP) from the given fills. Causal: fill at bar i affects bars >= i;
    its effect on bar i itself is excluded (own-slice impact is the Level-1
    overlay's job) — implemented by applying each fill's footprint from i+1.
    """
    perturb = np.zeros(n_bars, dtype=float)
    if adv_shares <= 0 or sigma_daily <= 0:
        return perturb
    sgn = side_sign(side)
    lam = np.log(0.5) / kernel.half_life_bars if kernel.half_life_bars > 0 else -np.inf
    for i, q in zip(fill_bars, fill_shares):
        if q <= 0:
            continue
        inst = kernel.eta * sigma_daily * np.sqrt(q / adv_shares) * 10_000
        perm = kernel.perm_frac * inst
        temp = (1.0 - kernel.perm_frac) * inst
        t = np.arange(i + 1, n_bars)
        if len(t) == 0:
            continue
        perturb[i + 1:] += sgn * (perm + temp * np.exp(lam * (t - i)))
    return perturb


def apply_kernel_to_schedule(schedule: pd.DataFrame, n_bars: int, bar_index: dict,
                             sigma_daily: float, adv_shares: float, side: str,
                             kernel: ImpactKernel) -> dict:
    """Reprice a schedule's fills on the perturbed path. Returns
    {perturbed_avg_px, raw_avg_px, extra_cost_bps, perturb_at_fill (Series)}.
    extra_cost_bps is the side-signed additional cost vs the raw-tape fills —
    the feedback term the raw simulation cannot see."""
    fills = schedule[schedule["shares_traded"] > 0]
    if len(fills) == 0:
        return {"perturbed_avg_px": None, "raw_avg_px": None,
                "extra_cost_bps": 0.0, "n_fills": 0}
    bars = np.array([bar_index[t] for t in fills["time"]], dtype=int)
    qty = fills["shares_traded"].to_numpy(dtype=float)
    px = fills["price"].to_numpy(dtype=float)

    perturb = propagate_impact(bars, qty, n_bars, sigma_daily, adv_shares, side, kernel)
    px_adj = px * (1.0 + perturb[bars] / 10_000)

    raw_avg = float(np.average(px, weights=qty))
    adj_avg = float(np.average(px_adj, weights=qty))
    sgn = side_sign(side)
    extra = sgn * (adj_avg - raw_avg) / raw_avg * 10_000
    return {"perturbed_avg_px": round(adj_avg, 4), "raw_avg_px": round(raw_avg, 4),
            "extra_cost_bps": round(float(extra), 2), "n_fills": int(len(fills))}


@dataclass
class CounterfactualBands:
    available: bool
    reason: str = ""
    table: pd.DataFrame = None        # one row per kernel: costs + delta
    delta_min_bps: float = None       # (new - base) total-cost delta across grid
    delta_max_bps: float = None
    robust: Optional[bool] = None     # conclusion sign identical across the grid
    note: str = ""
    caveats: list = field(default_factory=list)


def counterfactual_with_bands(market_data: MarketData, order_shares: float,
                              base_algo: str, base_urgency: str,
                              interventions: list, side: str = "Buy",
                              ticket=None,
                              eta_grid=DEFAULT_ETA_GRID,
                              half_life_grid=DEFAULT_HALF_LIFE_GRID,
                              perm_frac: float = DEFAULT_PERM_FRAC) -> CounterfactualBands:
    """Compare BASE strategy vs BASE+INTERVENTIONS with the propagator applied
    to both, across a kernel-assumption grid. The deliverable is the DELTA
    band: if its sign survives the whole grid, the strategy-switch conclusion
    is robust to the impact model; if it flips, the simulation is telling you
    it cannot decide and a live experiment must."""
    base = simulate_with_interventions(market_data, order_shares, base_algo,
                                       base_urgency, interventions=[], side=side, ticket=ticket)
    newr = simulate_with_interventions(market_data, order_shares, base_algo,
                                       base_urgency, interventions=interventions,
                                       side=side, ticket=ticket)
    day = base["day"]
    n = len(day)
    bar_index = {t: i for i, t in enumerate(day.index)}
    sigma_d = float(market_data.realized_vol_ann) / np.sqrt(252)
    adv = float(market_data.adv_shares)
    arrival = float(base["arrival_price"])
    sgn = side_sign(side)

    rows = []
    for eta in eta_grid:
        for hl in half_life_grid:
            k = ImpactKernel(eta=eta, perm_frac=perm_frac, half_life_bars=hl)
            b = apply_kernel_to_schedule(base["schedule"], n, bar_index, sigma_d, adv, side, k)
            v = apply_kernel_to_schedule(newr["schedule"], n, bar_index, sigma_d, adv, side, k)
            if b["perturbed_avg_px"] is None or v["perturbed_avg_px"] is None:
                continue
            b_cost = sgn * (b["perturbed_avg_px"] - arrival) / arrival * 10_000
            v_cost = sgn * (v["perturbed_avg_px"] - arrival) / arrival * 10_000
            rows.append({"Kernel": k.label(),
                         "Base cost (bps)": round(b_cost, 1),
                         "Switch cost (bps)": round(v_cost, 1),
                         "Δ switch − base (bps)": round(v_cost - b_cost, 1),
                         "Path feedback, base (bps)": b["extra_cost_bps"],
                         "Path feedback, switch (bps)": v["extra_cost_bps"]})
    if not rows:
        return CounterfactualBands(False, "No fills in one of the scenarios.")
    table = pd.DataFrame(rows)
    deltas = table["Δ switch − base (bps)"]
    robust = bool((deltas > 0).all() or (deltas < 0).all())
    note = ("Conclusion ROBUST to the impact model: the switch is "
            + ("more expensive" if deltas.min() > 0 else "cheaper")
            + f" under every kernel tested (Δ {deltas.min():+.1f} to {deltas.max():+.1f} bps)."
            if robust else
            f"Conclusion NOT robust: the delta changes sign across kernels "
            f"({deltas.min():+.1f} to {deltas.max():+.1f} bps) — the simulation cannot "
            "decide this switch; it needs a live A/B.")
    caveats = [
        "Slippage vs arrival on the perturbed path; the raw-tape totals elsewhere on "
        "this page are unchanged and remain the reconciled record.",
        "Schedule-invariant perturbation: fill sizes/times from the raw tape, prices "
        "adjusted by prior own-fill footprint (exact for volume/time-driven schedules; "
        "approximate for price-reactive tactics).",
        "Own-slice instantaneous impact is the existing overlay; the propagator adds "
        "only the cross-slice feedback — the two compose without double counting.",
        "On a REAL account's history the tape already embeds the original strategy's "
        "impact — this synthetic replay does not; de-impacting is required there.",
        f"Kernel grid: η ∈ {tuple(eta_grid)}, half-life ∈ {tuple(half_life_grid)} bars, "
        f"permanent fraction {perm_frac:.0%} — literature-anchored priors pending "
        "calibration from the event library (see COUNTERFACTUAL_IMPACT_MODEL.md).",
    ]
    return CounterfactualBands(True, "", table,
                               round(float(deltas.min()), 1), round(float(deltas.max()), 1),
                               robust, note, caveats)
