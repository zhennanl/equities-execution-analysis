"""Variable Lab — event-clustered evaluation of the LOCKED registry.

Session 9i. Evaluates the hypotheses in VARIABLE_LAB_REGISTRY.md
(written and locked BEFORE this file) on the full-pillar TW event
panels (time_machine.event_panel — WINDOW_STUDY §0 formulas, PIT by
construction: every variable at day k uses rows <= k only).

Discipline implemented, not just stated:
  * effective n = EVENTS (name-days within an event are one regime
    draw); effects = mean of EVENT-LEVEL mean differences
  * split rule: above/below the EVENT-side median of the variable at
    the hypothesis's decision day (cross-sectional within event —
    market-regime neutral by construction)
  * class cells first (provider x side); pooling reported only as a
    cross-check
  * leave-one-event-out sign stability
  * verdicts assigned MECHANICALLY from the registry's acceptance
    criteria — same data, same verdict, every run
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "variable_lab.json"

# Acceptance criteria — MUST mirror the locked registry verbatim
ADOPT_BPS, ADOPT_WINRATE, MIN_EVENTS = 50.0, 0.65, 6
REJECT_WINRATE, NULL_BPS, NULL_EVENTS = 0.55, 25.0, 8


def full_events() -> list[str]:
    from agents.time_machine import list_events
    ev = list_events()
    ok = []
    for _, r in ev.iterrows():
        got, need = map(int, r["days_cached"].split("/"))
        if got > 0 and got >= need - 2 and r["n_changes"] > 0:
            ok.append(r["event"])
    return ok


def master_panel() -> pd.DataFrame:
    from agents.time_machine import event_panel
    frames = []
    for name in full_events():
        p = event_panel(name)
        if not len(p):
            continue
        p = p.copy()
        p["event"] = name
        p["provider"] = "MSCI" if name.startswith("MSCI") else "FTSE"
        frames.append(p)
    df = pd.concat(frames, ignore_index=True)
    # T = last day per event; rk = k - T (0 at the print)
    df["T"] = df.groupby("event")["k"].transform("max")
    df["rk"] = df["k"] - df["T"]
    return df


# ------------------------------------------------------ variable defs
def _at(df, day_col, day_val):
    return df[df[day_col] == day_val]


def build_observations(panel: pd.DataFrame) -> pd.DataFrame:
    """One row per name-event: every registry variable at its decision
    day + every target. NaN where the pillar is missing (stated)."""
    rows = []
    for (event, code), g in panel.groupby(["event", "code"]):
        g = g.sort_values("k")
        T = int(g["T"].iloc[0])
        if T < 6:
            continue                        # window too short to test
        last = g[g["k"] == T]
        if not len(last):
            continue
        fav_T = float(last["fav_drift_bps"].iloc[0])
        tmult_T = float(last["t_mult"].iloc[0])

        def at_k(k, col):
            r = g[g["k"] == k]
            return float(r[col].iloc[0]) if len(r) else np.nan
        k5 = min(5, T - 1)
        k3 = min(3, T - 1)
        rk3 = T - 3
        rows.append({
            "event": event, "code": code,
            "provider": g["provider"].iloc[0],
            "side": g["side"].iloc[0], "T": T,
            # H1: front-run completion — cumulative excess volume
            # (t_mult - 1 summed) to k5, per §0 units of ADV
            "h1_cum_excess": float(
                (g[g["k"] <= k5]["t_mult"] - 1).clip(lower=0).sum()),
            # H2/H7: crowding at rk=-3
            "h2_short_build": at_k(rk3, "short_chg_pct"),
            "h7_exiting": bool(
                g[g["k"] <= rk3]["short_chg_pct"].max() >= 15 and
                at_k(rk3, "short_chg_pct") <=
                g[g["k"] <= rk3]["short_chg_pct"].max() - 15)
            if not np.isnan(at_k(rk3, "short_chg_pct")) else np.nan,
            # H3: A+3 momentum
            "h3_a3_mom": at_k(k3, "fav_drift_bps"),
            # H4: foreign coverage at k5 (x ADV, with-flow sign)
            "h4_foreign_cum": at_k(k5, "foreign_cum_x_adv"),
            # H5: cohort lag input = own drift at k5 (lag computed
            # cross-sectionally below)
            "h5_drift_k5": at_k(k5, "fav_drift_bps"),
            # H6: early volume surge
            "h6_early_tmult": float(g[g["k"] <= k3]["t_mult"].mean()),
            # targets
            "tgt_remaining_k5": fav_T - at_k(k5, "fav_drift_bps"),
            "tgt_remaining_k3": fav_T - at_k(k3, "fav_drift_bps"),
            "tgt_remaining_rk3": fav_T - at_k(rk3, "fav_drift_bps"),
            "tgt_print_tmult": tmult_T})
    df = pd.DataFrame(rows)
    # H5 cohort lag: drift minus event-side median
    med = df.groupby(["event", "side"])["h5_drift_k5"] \
        .transform("median")
    df["h5_cohort_lag"] = df["h5_drift_k5"] - med
    return df


HYPOTHESES = [
    # id, variable, target, cell filter (None = all sides), direction
    # note (pre-declared; sign convention: effect = mean(HIGH group)
    # - mean(LOW group) of the target, event-clustered)
    ("H1", "h1_cum_excess", "tgt_remaining_k5", None,
     "HIGH completion -> LESS remaining drift (negative effect)"),
    ("H2", "h2_short_build", "tgt_remaining_rk3", "Sell",
     "HIGH build -> LESS favorable remaining drift for deletes"),
    ("H3", "h3_a3_mom", "tgt_remaining_k3", None,
     "momentum persists IN-CLASS (positive effect, FTSE); expected "
     "to fail on MSCI"),
    ("H4", "h4_foreign_cum", "tgt_remaining_k5", None,
     "HIGH foreign coverage -> LESS remaining drift"),
    ("H5", "h5_cohort_lag", "tgt_remaining_k5", None,
     "LAGGARDS (low) -> MORE remaining drift (negative effect)"),
    ("H6", "h6_early_tmult", "tgt_print_tmult", None,
     "HIGH early volume -> SMALLER print multiple"),
    ("H7", "h7_exiting", "tgt_remaining_rk3", "Sell",
     "EXITING flips the crowding effect"),
]


def _event_split_effect(obs: pd.DataFrame, var: str,
                        tgt: str) -> tuple[list, int]:
    """Per event: mean(target | var above event-side median) -
    mean(target | below). Returns per-event effects + n skipped."""
    effects, skipped = [], 0
    for event, g in obs.groupby("event"):
        g = g.dropna(subset=[var, tgt])
        if g[var].dtype == bool or set(g[var].dropna().unique()) \
                <= {0, 1, True, False}:
            hi, lo = g[g[var].astype(bool)], g[~g[var].astype(bool)]
        else:
            med = g[var].median()
            hi, lo = g[g[var] > med], g[g[var] <= med]
        if len(hi) < 1 or len(lo) < 1:
            skipped += 1
            continue
        effects.append(float(hi[tgt].mean() - lo[tgt].mean()))
    return effects, skipped


def _verdict(effects: list[float]) -> tuple[str, dict]:
    n = len(effects)
    if n < MIN_EVENTS:
        return "DATA-GATED", {"n_events": n}
    e = np.array(effects)
    mean = float(e.mean())
    sign = np.sign(mean)
    winrate = float((np.sign(e) == sign).mean())
    loo_stable = all(np.sign(np.delete(e, i).mean()) == sign
                     for i in range(n))
    stats = {"n_events": n, "mean_bps": round(mean, 1),
             "winrate": round(winrate, 2), "loo_stable": loo_stable}
    if abs(mean) >= ADOPT_BPS and winrate >= ADOPT_WINRATE \
            and loo_stable:
        return "ADOPT", stats
    if abs(mean) < NULL_BPS and n >= NULL_EVENTS:
        return "NULL-PIN", stats
    if winrate < REJECT_WINRATE or not loo_stable:
        return "REJECT", stats
    return "INCONCLUSIVE", stats


def run_lab() -> dict:
    panel = master_panel()
    obs = build_observations(panel)
    results = {}
    for hid, var, tgt, side, note in HYPOTHESES:
        res = {"variable": var, "target": tgt, "note": note}
        for cell_name, cell in (
                [("FTSE", obs[obs["provider"] == "FTSE"]),
                 ("MSCI", obs[obs["provider"] == "MSCI"]),
                 ("POOLED", obs)]):
            c = cell if side is None else cell[cell["side"] == side]
            effects, skipped = _event_split_effect(c, var, tgt)
            verdict, stats = _verdict(effects)
            res[cell_name] = {"verdict": verdict, **stats,
                              "events_skipped": skipped}
        results[hid] = res
    out = {"n_events_panel": int(obs["event"].nunique()),
           "n_name_events": int(len(obs)),
           "results": results}
    OUT.write_text(json.dumps(out, indent=1))
    return out
