"""Flow-prediction framework (Layers 1-6; design in the 2026-07-09 session,
statistical conventions per docs/QUANT_REVIEW_ADDITIONS.md).

Targets are kept distinct because they are different problems:
  L1  daily total volume        — log-volume AR(1) + day-of-week + event flags,
                                  gated against naive baselines by Diebold-Mariano
  L2  intraday distribution     — L1 total x historical curve, with a
                                  precision-weighted live update (Kalman-lite)
  L3  close-auction share       — AR(1) with half-life (MOC capacity)
  L4  event-day uplift          — realized event-day volume multiples from the
                                  event library correcting mechanical estimates
  L5  signed flow               — DIAGNOSTIC ONLY: BVC imbalance persistence;
                                  direction prediction is alpha territory and
                                  deliberately out of scope
  L6  ML upgrade                — ridge (numpy; sklearn GBM if installed) over
                                  pooled features, shipped ONLY if it beats L1
                                  out-of-sample by a DM test

House rules throughout: walk-forward evaluation only; every model is gated
against a naive baseline; a model that cannot beat the 20-day median ships
the 20-day median.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import numpy as np
import pandas as pd
from scipy import stats as _stats

BASELINE_WINDOW = 20          # the median every model must beat
MIN_OBS_DAILY = 30            # minimum history for the L1 AR fit
DM_ALPHA = 0.10               # gate significance (one-sided, forecasting convention)


# ── Shared: Diebold-Mariano test ───────────────────────────────────────────

def dm_test(err_a: np.ndarray, err_b: np.ndarray, h: int = 1) -> dict:
    """DM test on two forecast-error series (same targets). Loss = squared
    error. Negative stat => A more accurate. HAC (Bartlett) variance with
    h-1 lags. Returns {stat, p_one_sided (A better), n}."""
    d = np.asarray(err_a, float) ** 2 - np.asarray(err_b, float) ** 2
    d = d[np.isfinite(d)]
    n = len(d)
    if n < 8:
        return {"stat": None, "p_one_sided": None, "n": n}
    dbar = d.mean()
    gamma0 = np.var(d, ddof=1)
    var = gamma0
    for k in range(1, max(h, 1)):
        w = 1 - k / max(h, 1)
        cov = np.cov(d[k:], d[:-k], ddof=1)[0, 1]
        var += 2 * w * cov
    if var <= 0:
        return {"stat": None, "p_one_sided": None, "n": n}
    stat = dbar / np.sqrt(var / n)
    p = float(_stats.norm.cdf(stat))            # P(A better): mass below 0
    return {"stat": round(float(stat), 3), "p_one_sided": round(p, 4), "n": n}


# ── Layer 1: daily volume ──────────────────────────────────────────────────

@dataclass
class DailyVolumeForecast:
    available: bool
    reason: str = ""
    forecast_next: float = None            # shares, next session
    chosen_model: str = ""                 # "AR+calendar" | "median20" (gate outcome)
    phi: float = None                      # AR(1) coefficient on log volume
    mae_model: float = None                # walk-forward MAE (log space)
    mae_median: float = None
    mae_yesterday: float = None
    dm_vs_median: dict = field(default_factory=dict)
    n_eval: int = 0
    note: str = ""


def daily_volume_forecast(volumes: pd.Series,
                          event_next: bool = False,
                          event_flags: Optional[pd.Series] = None) -> DailyVolumeForecast:
    """volumes: daily volume indexed by date. Fits demeaned log-volume AR(1)
    with day-of-week + optional event dummies; walk-forward one-step
    evaluation over the back half of the sample; DM-gates vs the 20-day
    median. event_next flags tomorrow as an event day."""
    v = volumes.dropna().astype(float)
    v = v[v > 0]
    if len(v) < MIN_OBS_DAILY:
        return DailyVolumeForecast(False, f"Need >= {MIN_OBS_DAILY} daily observations (have {len(v)}).")
    ly = np.log(v.values)
    dows = pd.DatetimeIndex(v.index).dayofweek
    ev = (event_flags.reindex(v.index).fillna(False).astype(float).values
          if event_flags is not None else np.zeros(len(v)))

    def design(i0, i1):
        # rows i0..i1 predict from t-1: [const, ly_{t-1}, dow dummies(4), ev_t]
        rows = []
        for t in range(i0, i1):
            d = [1.0, ly[t - 1]]
            d += [1.0 if dows[t] == k else 0.0 for k in range(4)]   # Mon..Thu vs Fri
            d.append(ev[t])
            rows.append(d)
        return np.array(rows)

    def fit_predict(train_end, t):
        X = design(1, train_end)
        y = ly[1:train_end]
        beta, *_ = np.linalg.lstsq(X, y, rcond=None)
        x = np.array([1.0, ly[t - 1]] + [1.0 if dows[t] == k else 0.0 for k in range(4)] + [ev[t]])
        return float(x @ beta), beta

    # walk-forward over the back half
    start = max(MIN_OBS_DAILY // 2, len(ly) // 2)
    e_model, e_med, e_yest = [], [], []
    for t in range(start, len(ly)):
        pred, _ = fit_predict(t, t)
        e_model.append(pred - ly[t])
        med = np.log(np.median(v.values[max(0, t - BASELINE_WINDOW):t]))
        e_med.append(med - ly[t])
        e_yest.append(ly[t - 1] - ly[t])
    e_model, e_med, e_yest = map(np.array, (e_model, e_med, e_yest))
    mae_m, mae_md, mae_y = (float(np.mean(np.abs(e))) for e in (e_model, e_med, e_yest))
    dm = dm_test(e_model, e_med)

    use_model = (mae_m < mae_md and dm["p_one_sided"] is not None
                 and dm["p_one_sided"] < DM_ALPHA)
    # next-session forecast
    _, beta = fit_predict(len(ly), len(ly) - 1)     # fit on all data
    next_dow = (dows[-1] + 1) % 5                    # naive next business day
    x = np.array([1.0, ly[-1]] + [1.0 if next_dow == k else 0.0 for k in range(4)]
                 + [1.0 if event_next else 0.0])
    f_model = float(np.exp(x @ beta))
    f_median = float(np.median(v.values[-BASELINE_WINDOW:]))
    chosen = "AR+calendar" if use_model else "median20"
    note = (f"Walk-forward MAE (log): model {mae_m:.3f} vs median20 {mae_md:.3f} vs "
            f"yesterday {mae_y:.3f}; DM p={dm['p_one_sided']} — "
            + ("model beats the baseline; shipping the model."
               if use_model else
               "model does NOT clear the DM gate; shipping the 20-day median "
               "(the house rule: a model that can't beat naive ships naive)."))
    return DailyVolumeForecast(True, "", round(f_model if use_model else f_median, 0),
                               chosen, None, round(mae_m, 4), round(mae_md, 4),
                               round(mae_y, 4), dm, len(e_model), note)


# ── Layer 2: intraday blend (Kalman-lite) ──────────────────────────────────

def blended_day_total(prior_total: float, realized_so_far: float, cum_curve: float,
                      prior_cv: float = 0.35) -> dict:
    """Precision-weighted blend of (a) the pre-open forecast and (b) the
    curve-grossed-up realized volume. Gross-up variance shrinks as the day
    elapses (~ (1-w)/w with w = cumulative curve weight), so the estimate
    trusts the prior early and the tape late — a one-line Kalman filter with
    a disclosed heuristic variance model."""
    if cum_curve <= 0:
        return {"blended_total": prior_total, "weight_on_tape": 0.0}
    grossup = realized_so_far / cum_curve
    var_prior = (prior_cv * prior_total) ** 2
    var_gross = var_prior * (1 - cum_curve) / max(cum_curve, 1e-6)
    w_tape = var_prior / (var_prior + var_gross)     # -> 1 as day completes
    blended = w_tape * grossup + (1 - w_tape) * prior_total
    return {"blended_total": round(float(blended), 0),
            "weight_on_tape": round(float(w_tape), 3),
            "grossup_total": round(float(grossup), 0)}


# ── Layer 3: close-auction share AR(1) ─────────────────────────────────────

@dataclass
class CloseShareForecast:
    available: bool
    reason: str = ""
    mu: float = None
    phi: float = None
    half_life_days: float = None
    latest: float = None
    forecast_next: float = None
    note: str = ""


def close_share_series(intraday: pd.DataFrame) -> pd.Series:
    """Per-day share of volume in the final bar (bar-based close proxy)."""
    df = intraday.copy()
    df["_d"] = df.index.normalize()
    out = {}
    for d, day in df.groupby("_d"):
        tot = float(day["Volume"].sum())
        if tot > 0 and len(day) >= 10:
            out[d] = float(day["Volume"].iloc[-1]) / tot
    return pd.Series(out).sort_index()


def close_share_ar1(shares: pd.Series) -> CloseShareForecast:
    s = shares.dropna().astype(float)
    if len(s) < 5:
        return CloseShareForecast(False, f"Need >= 5 daily close-share observations (have {len(s)}).")
    x = s.values
    mu = float(x.mean())
    xc, xl = x[1:] - mu, x[:-1] - mu
    denom = float(np.sum(xl ** 2))
    phi = float(np.sum(xc * xl) / denom) if denom > 0 else 0.0
    phi = float(np.clip(phi, -0.95, 0.95))
    hl = float(np.log(0.5) / np.log(abs(phi))) if 0 < abs(phi) < 1 else None
    latest = float(x[-1])
    fc = mu + phi * (latest - mu)
    note = (f"Close share mean {mu:.1%}, AR(1) φ={phi:.2f}"
            + (f", shock half-life ≈ {hl:.1f} days" if hl else "")
            + f". Latest {latest:.1%} → next-day forecast {fc:.1%} — size MOC "
              "orders against the forecast, not the long-run mean or yesterday.")
    return CloseShareForecast(True, "", round(mu, 4), round(phi, 3),
                              round(hl, 2) if hl else None,
                              round(latest, 4), round(fc, 4), note)


# ── Layer 5: signed-flow DIAGNOSTICS (deliberately not predictive) ─────────

def imbalance_diagnostics(day: pd.DataFrame) -> dict:
    """BVC-signed order-flow imbalance persistence for the given day's bars.
    DIAGNOSTIC ONLY — a regime/toxicity input, not a direction forecast:
    predicting signed flow is short-horizon alpha and out of this platform's
    honest scope (stated in the output)."""
    from agents.agent9_microstructure import _bulk_volume_classify
    if len(day) < 20:
        return {"available": False, "reason": "Need >= 20 bars."}
    bvc = _bulk_volume_classify(day)
    imb = (bvc["buy_vol"] - bvc["sell_vol"]) / (bvc["buy_vol"] + bvc["sell_vol"]).replace(0, np.nan)
    imb = imb.dropna()
    if len(imb) < 15:
        return {"available": False, "reason": "Too few classified bars."}
    ac1 = float(imb.autocorr(lag=1)) if imb.std() > 0 else 0.0
    m = min(10, len(imb) // 3)
    n = len(imb)
    acfs = [imb.autocorr(lag=k) for k in range(1, m + 1)]
    q = n * (n + 2) * sum((a ** 2) / (n - k) for k, a in enumerate(acfs, 1) if np.isfinite(a))
    p = float(1 - _stats.chi2.cdf(q, m))
    persistent = p < 0.05 and ac1 > 0
    return {"available": True, "mean_imbalance": round(float(imb.mean()), 3),
            "ac1": round(ac1, 3), "ljung_box_p": round(p, 4),
            "persistent": bool(persistent),
            "note": ("Imbalance is serially persistent today — one-sided flow regime; "
                     "treat as a toxicity/momentum input to urgency, NOT a direction "
                     "forecast (signed-flow prediction is alpha territory, out of scope)."
                     if persistent else
                     "No significant imbalance persistence — flow looks two-sided.")}


# ── Layer 6: ML gate (ridge; sklearn GBM if present) ──────────────────────

def ml_volume_gate(volumes: pd.Series, extra_features: Optional[pd.DataFrame] = None,
                   ridge_lambda: float = 1.0) -> dict:
    """Feature model for next-day log volume: lags 1/2/5, 5-day mean, dow,
    plus optional extra features. Ridge via numpy (GBM via sklearn if
    installed). Walk-forward MAE + DM against the L1-style AR fit; the
    verdict field says whether ML earns its complexity. Returns a dict with
    use_ml, engine, maes, dm."""
    v = volumes.dropna().astype(float); v = v[v > 0]
    if len(v) < MIN_OBS_DAILY + 10:
        return {"available": False, "reason": "Insufficient history for the ML gate."}
    ly = pd.Series(np.log(v.values), index=v.index)
    F = pd.DataFrame(index=ly.index)
    F["l1"], F["l2"], F["l5"] = ly.shift(1), ly.shift(2), ly.shift(5)
    F["m5"] = ly.shift(1).rolling(5).mean()
    for k in range(4):
        F[f"dow{k}"] = (pd.DatetimeIndex(ly.index).dayofweek == k).astype(float)
    if extra_features is not None:
        F = F.join(extra_features.reindex(F.index))
    F = F.dropna()
    y = ly.reindex(F.index).values
    X = F.values
    try:
        from sklearn.ensemble import GradientBoostingRegressor
        engine = "sklearn-GBM"
        def fit_pred(Xtr, ytr, xte):
            m = GradientBoostingRegressor(n_estimators=100, max_depth=2, random_state=0)
            m.fit(Xtr, ytr)
            return float(m.predict(xte.reshape(1, -1))[0])
    except ImportError:
        engine = "numpy-ridge"
        def fit_pred(Xtr, ytr, xte):
            mu, sd = Xtr.mean(0), Xtr.std(0) + 1e-9
            Xs = (Xtr - mu) / sd
            A = Xs.T @ Xs + ridge_lambda * np.eye(Xs.shape[1])
            b = np.linalg.solve(A, Xs.T @ (ytr - ytr.mean()))
            return float(((xte - mu) / sd) @ b + ytr.mean())
    start = len(y) // 2
    e_ml, e_ar = [], []
    for t in range(start, len(y)):
        e_ml.append(fit_pred(X[:t], y[:t], X[t]) - y[t])
        # AR(1)-only comparator on the same split
        xl, yc = X[:t, 0], y[:t]
        phi = np.polyfit(xl, yc, 1)
        e_ar.append(float(np.polyval(phi, X[t, 0])) - y[t])
    e_ml, e_ar = np.array(e_ml), np.array(e_ar)
    mae_ml, mae_ar = float(np.mean(np.abs(e_ml))), float(np.mean(np.abs(e_ar)))
    dm = dm_test(e_ml, e_ar)
    use = mae_ml < mae_ar and dm["p_one_sided"] is not None and dm["p_one_sided"] < DM_ALPHA
    return {"available": True, "engine": engine, "use_ml": bool(use),
            "mae_ml": round(mae_ml, 4), "mae_ar": round(mae_ar, 4), "dm": dm,
            "note": (f"{engine} beats the AR comparator (DM p={dm['p_one_sided']}) — ML earns "
                     "its complexity on this name." if use else
                     f"{engine} does not clear the DM gate vs plain AR — ship the simple "
                     "model (house rule).")}


# ── Layer 4: event-day uplift from the event library ──────────────────────

def event_uplift(library_stats_row: dict) -> dict:
    """Median realized event-day volume multiple from recorded events —
    the empirical correction applied to L1's forecast on known event days
    (rebalance effective dates). n and source always displayed."""
    n = int(library_stats_row.get("n", 0))
    m = library_stats_row.get("median_t_day_volume_multiple")
    if not m or n < 3:
        return {"available": False,
                "reason": f"Needs >= 3 recorded events with volume multiples (n={n}).",
                "multiple": 1.4, "source": "literature placeholder (event closes run well above normal)"}
    return {"available": True, "multiple": float(m), "n": n,
            "source": f"event library median (n={n})"}


# --------------------------------------------------------------------------
# L6b — distributional & pooled upgrades (same house rule: gated or shipped
# as the naive baseline). Quantile heads make the point forecast
# decision-grade (P10 = "will the liquidity be there", P90 = "can the tape
# absorb an accelerated schedule"); pooling borrows strength across symbols
# when single-name history is short.
# --------------------------------------------------------------------------

@dataclass
class QuantileVolumeForecast:
    available: bool
    reason: str = ""
    taus: tuple = (0.1, 0.5, 0.9)
    forecast_shares: tuple = ()          # aligned with taus, monotone-enforced
    pinball_model: float = 0.0           # walk-forward mean pinball (avg over taus)
    pinball_baseline: float = 0.0        # rolling 20d empirical quantiles
    dm_vs_baseline: dict = None
    chosen_model: str = ""               # "quantile_reg" | "empirical20"
    n_eval: int = 0
    note: str = ""


def _pinball_loss(y: float, q: float, tau: float) -> float:
    return tau * (y - q) if y >= q else (1.0 - tau) * (q - y)


def _quantile_fit_predict(X: np.ndarray, y: np.ndarray, x_new: np.ndarray,
                          tau: float) -> float:
    """Exact linear quantile regression via the standard LP formulation:
    min tau*u + (1-tau)*v  s.t.  y - Xb = u - v, u,v >= 0 (Koenker-Bassett).
    Tiny problem sizes here (n<=~120, k=3) — scipy HiGHS solves in ms."""
    from scipy.optimize import linprog
    n, k = X.shape
    c = np.concatenate([np.zeros(k), np.full(n, tau), np.full(n, 1.0 - tau)])
    A_eq = np.hstack([X, np.eye(n), -np.eye(n)])
    bounds = [(None, None)] * k + [(0.0, None)] * (2 * n)
    res = linprog(c, A_eq=A_eq, b_eq=y, bounds=bounds, method="highs")
    if not res.success:                              # pragma: no cover
        b = np.linalg.lstsq(X, y, rcond=None)[0]     # degenerate fallback
        return float(x_new @ b)
    return float(x_new @ res.x[:k])


def _qvf_design(x: np.ndarray):
    """Shared design: const, lag-1 log volume, 5-day mean log volume."""
    lag1 = x[4:-1]
    m5 = np.array([x[i - 5:i].mean() for i in range(5, len(x))])
    y = x[5:]
    X = np.column_stack([np.ones_like(y), lag1, m5])
    return X, y


def quantile_volume_forecast(volumes: pd.Series,
                             taus: tuple = (0.1, 0.5, 0.9)
                             ) -> QuantileVolumeForecast:
    """Distributional next-day volume: linear quantile regression per tau,
    walk-forward pinball-gated against rolling 20-day EMPIRICAL quantiles.
    If the regression can't beat the empirical quantiles (DM one-sided
    p < DM_ALPHA on the pinball-loss differential), ship the empirical
    quantiles — same discipline as L1."""
    v = pd.Series(volumes).dropna()
    v = v[v > 0]
    if len(v) < MIN_OBS_DAILY + 10:
        return QuantileVolumeForecast(False, reason=f"need >= {MIN_OBS_DAILY + 10} "
                                      f"positive-volume days, have {len(v)}")
    x = np.log(v.to_numpy(dtype=float))
    X, y = _qvf_design(x)
    n = len(y)
    start = max(15, int(n * 0.6))
    if n - start < 10:
        start = n - 10
    loss_m, loss_b = [], []
    for t in range(start, n):
        row_m, row_b = 0.0, 0.0
        hist = x[max(0, 5 + t - BASELINE_WINDOW):5 + t]   # last <=20 realized logs
        for tau in taus:
            q_hat = _quantile_fit_predict(X[:t], y[:t], X[t], tau)
            q_emp = float(np.quantile(hist, tau))
            row_m += _pinball_loss(y[t], q_hat, tau)
            row_b += _pinball_loss(y[t], q_emp, tau)
        loss_m.append(row_m / len(taus))
        loss_b.append(row_b / len(taus))
    loss_m, loss_b = np.array(loss_m), np.array(loss_b)
    # DM on the loss differential directly (losses, not errors — pass through
    # a helper identical to dm_test but on pre-computed losses).
    d = loss_m - loss_b
    dbar = float(d.mean()); nn = len(d)
    gamma0 = float(np.mean((d - dbar) ** 2))
    var_dbar = gamma0 / nn if gamma0 > 0 else 0.0
    if var_dbar <= 0:
        dm = {"stat": 0.0, "p_one_sided": 0.5, "n": nn}
    else:
        stat = dbar / np.sqrt(var_dbar)
        from math import erf
        dm = {"stat": round(stat, 3),
              "p_one_sided": round(0.5 * (1 + erf(stat / np.sqrt(2))), 4), "n": nn}
    use_model = (loss_m.mean() < loss_b.mean()) and (dm["p_one_sided"] < DM_ALPHA)
    chosen = "quantile_reg" if use_model else "empirical20"
    # final forecasts from the chosen approach, monotone-enforced, back to shares
    x_new = np.array([1.0, x[-1], x[-5:].mean()])
    hist_tail = x[-BASELINE_WINDOW:]
    qs = []
    for tau in taus:
        if use_model:
            qs.append(_quantile_fit_predict(X, y, x_new, tau))
        else:
            qs.append(float(np.quantile(hist_tail, tau)))
    qs = np.sort(np.array(qs))                    # non-crossing by construction
    fc = tuple(round(float(np.exp(q)), 0) for q in qs)
    note = (f"L6b quantile head [{chosen}]: P10/P50/P90 = "
            f"{fc[0]:,.0f} / {fc[1]:,.0f} / {fc[2]:,.0f} sh; walk-forward pinball "
            f"{loss_m.mean():.4f} (reg) vs {loss_b.mean():.4f} (empirical20), "
            f"DM one-sided p={dm['p_one_sided']}. "
            + ("Regression beats the empirical quantiles and ships."
               if use_model else
               "Regression does NOT beat rolling empirical quantiles — "
               "shipping empirical20 (house rule)."))
    return QuantileVolumeForecast(True, taus=taus, forecast_shares=fc,
                                  pinball_model=round(float(loss_m.mean()), 4),
                                  pinball_baseline=round(float(loss_b.mean()), 4),
                                  dm_vs_baseline=dm, chosen_model=chosen,
                                  n_eval=len(d), note=note)


@dataclass
class PooledVolumeModel:
    available: bool
    reason: str = ""
    n_symbols: int = 0
    n_train: int = 0
    n_test: int = 0
    mae_pooled: float = 0.0              # log-space MAE, pooled cross-sectional ridge
    mae_per_name: float = 0.0            # per-symbol AR(1) fit on own history only
    dm_p: float = 0.5
    chosen_model: str = ""               # "pooled_ridge" | "per_name_ar1"
    next_forecast_shares: dict = None    # symbol -> next-day share forecast
    note: str = ""


def _pooled_design(x: np.ndarray):
    """Per-symbol demeaned log volume (symbol fixed effect), features:
    lag1, lag2, mean5, day-of-week dummies handled by caller."""
    lag1, lag2 = x[4:-1], x[3:-2]
    m5 = np.array([x[i - 5:i].mean() for i in range(5, len(x))])
    y = x[5:]
    return np.column_stack([lag1, lag2, m5]), y


def pooled_volume_model(volumes_by_symbol: dict, ridge_lambda: float = 1.0,
                        train_frac: float = 0.7) -> PooledVolumeModel:
    """Pooled cross-sectional volume model: demean each symbol's log volume
    (fixed effect), stack lag/calendar features across symbols, fit one ridge.
    Gate: pooled test MAE must beat a per-symbol AR(1) trained on each name's
    own history alone. This is the standard 'borrow strength across the
    cross-section' upgrade — most valuable exactly when per-name history is
    short. Walk-forward within a static chronological split (disclosed)."""
    panel = {}
    for sym, ser in volumes_by_symbol.items():
        v = pd.Series(ser).dropna()
        v = v[v > 0]
        if len(v) >= 25:
            panel[sym] = v
    if len(panel) < 2:
        return PooledVolumeModel(False, reason="need >= 2 symbols with >= 25 "
                                 "positive-volume days each")
    Xtr, ytr = [], []
    tests = {}          # sym -> (X_test, y_test, mu, dows_test)
    means, dow_all_tr = {}, []
    for sym, v in panel.items():
        x = np.log(v.to_numpy(dtype=float))
        mu = float(x.mean()); means[sym] = mu
        Xs, ys = _pooled_design(x - mu)
        dows = pd.DatetimeIndex(v.index[5:]).dayofweek if isinstance(
            v.index, pd.DatetimeIndex) else np.zeros(len(ys), dtype=int)
        D = np.zeros((len(ys), 4))
        for j in range(4):
            D[:, j] = (np.asarray(dows) == j + 1).astype(float)
        Xs = np.hstack([Xs, D])
        k = max(10, int(len(ys) * train_frac))
        Xtr.append(Xs[:k]); ytr.append(ys[:k])
        tests[sym] = (Xs[k:], ys[k:], mu, x)
    Xtr = np.vstack(Xtr); ytr = np.concatenate(ytr)
    XtX = Xtr.T @ Xtr + ridge_lambda * np.eye(Xtr.shape[1])
    beta = np.linalg.solve(XtX, Xtr.T @ ytr)
    err_pool, err_ar = [], []
    next_fc = {}
    for sym, (Xte, yte, mu, x) in tests.items():
        xc = x - mu
        Xs_all, ys_all = _pooled_design(xc)
        k = max(10, int(len(ys_all) * train_frac))
        # per-name AR(1) on own training slice only
        a, b = xc[4:4 + k], ys_all[:k]      # lag1 -> y over train
        denom = float(np.dot(a - a.mean(), a - a.mean()))
        phi = float(np.dot(a - a.mean(), b - b.mean()) / denom) if denom > 0 else 0.0
        phi = float(np.clip(phi, -0.95, 0.95))
        if len(yte):
            pred_pool = Xte @ beta
            pred_ar = phi * Xte[:, 0]        # lag1 column, demeaned space
            err_pool.extend(np.abs(yte - pred_pool))
            err_ar.extend(np.abs(yte - pred_ar))
        # next-day forecast from the pooled model
        lag1, lag2, m5 = xc[-1], xc[-2], xc[-5:].mean()
        D = np.zeros(4)
        x_new = np.concatenate([[lag1, lag2, m5], D])
        next_fc[sym] = round(float(np.exp(mu + x_new @ beta)), 0)
    err_pool, err_ar = np.array(err_pool), np.array(err_ar)
    if len(err_pool) < 8:
        return PooledVolumeModel(False, reason="test slice too short to gate")
    dm = dm_test(err_pool, err_ar)
    use_pool = (err_pool.mean() < err_ar.mean()) and (dm["p_one_sided"] < DM_ALPHA)
    chosen = "pooled_ridge" if use_pool else "per_name_ar1"
    note = (f"L6b pooled [{chosen}]: {len(panel)} symbols, pooled test MAE "
            f"{err_pool.mean():.4f} vs per-name AR(1) {err_ar.mean():.4f} "
            f"(log space), DM p={dm['p_one_sided']}. "
            + ("Pooling borrows strength across the cross-section and ships."
               if use_pool else
               "Pooling does NOT beat per-name AR(1) here — shipping per-name "
               "(house rule). Pooling pays off mainly on short histories."))
    return PooledVolumeModel(True, n_symbols=len(panel), n_train=len(ytr),
                             n_test=len(err_pool),
                             mae_pooled=round(float(err_pool.mean()), 4),
                             mae_per_name=round(float(err_ar.mean()), 4),
                             dm_p=dm["p_one_sided"], chosen_model=chosen,
                             next_forecast_shares=next_fc, note=note)
