"""
Transaction Cost Model — regression-based TCA.

The analytical core a GSET execution consultant lives in: instead of *assuming*
the square-root-law prefactor (eta = 0.3 elsewhere in this platform), this module
*estimates* the cost model from a panel of executions by ordinary least squares,
with the inference machinery a bank desk actually needs:

  * OLS with an explicit, auditable linear-algebra implementation (no statsmodels
    dependency — every number can be reproduced by hand from the formulas here).
  * Heteroskedasticity-robust (White HC1) and heteroskedasticity-AND-
    autocorrelation-robust (Newey-West HAC, Bartlett kernel) standard errors —
    the correct choice for execution-cost residuals, which fan out with order
    size and are serially correlated in time order. Naive-OLS SEs are reported
    alongside so the difference is explicit.
  * Residual diagnostics: Durbin-Watson (autocorrelation), Breusch-Pagan
    (heteroskedasticity, an LM test), Jarque-Bera (normality).
  * A cost-curve feature builder (sqrt(size %ADV) as the primary regressor,
    matching the market-impact literature) and an expected-cost predictor — the
    fitted model becomes a *conditional benchmark* every order can be scored on.
  * ab_test_with_controls(): an A/B test run as a regression with a strategy
    dummy PLUS condition controls, so the incremental cost of algo A vs. B is
    measured NET of confounders (size, volatility, spread) — strictly stronger
    than a raw paired mean difference when the two algos never ran on identical
    orders (the real-client case).

HONESTY BOUNDARY: on this platform the "realized" cost fed in is *simulated*, so
the residual variance is structural rather than true client noise. The identical
code fits a panel of REAL client fills the moment one is supplied; the simulated
panel demonstrates the method and recovers the square-root coefficient.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Sequence

import numpy as np
import pandas as pd
from scipy import stats as _stats


# ══════════════════════════════════════════════════════════════════════════
# OLS with robust / HAC standard errors
# ══════════════════════════════════════════════════════════════════════════

@dataclass
class OLSResult:
    names: list                      # regressor names (incl. 'const')
    coef: np.ndarray                 # point estimates
    se: np.ndarray                   # standard errors under the chosen cov
    se_classical: np.ndarray         # naive homoskedastic SEs (for contrast)
    tstat: np.ndarray
    pvalue: np.ndarray
    r2: float
    adj_r2: float
    fstat: float                     # overall F (all slopes = 0)
    f_pvalue: float
    n: int
    k: int                           # number of parameters (incl. const)
    cov_type: str                    # "classical" | "HC1" | "HAC"
    resid: np.ndarray = field(repr=False, default=None)
    fitted: np.ndarray = field(repr=False, default=None)
    _XtX_inv: np.ndarray = field(repr=False, default=None)
    _X: np.ndarray = field(repr=False, default=None)

    def summary_frame(self) -> pd.DataFrame:
        ci = 1.96 * self.se
        return pd.DataFrame({
            "coef": np.round(self.coef, 4),
            "std err": np.round(self.se, 4),
            "t": np.round(self.tstat, 3),
            "P>|t|": np.round(self.pvalue, 4),
            "CI low": np.round(self.coef - ci, 4),
            "CI high": np.round(self.coef + ci, 4),
        }, index=self.names)

    def predict(self, X_new: np.ndarray) -> np.ndarray:
        X_new = np.asarray(X_new, dtype=float)
        if X_new.ndim == 1:
            X_new = X_new.reshape(1, -1)
        return X_new @ self.coef


def add_const(X: np.ndarray) -> np.ndarray:
    """Prepend an intercept column of ones."""
    X = np.asarray(X, dtype=float)
    if X.ndim == 1:
        X = X.reshape(-1, 1)
    return np.column_stack([np.ones(len(X)), X])


def _hac_lag(n: int) -> int:
    """Newey-West (1994) automatic Bartlett bandwidth."""
    return int(np.floor(4 * (n / 100.0) ** (2.0 / 9.0)))


def fit_ols(X: np.ndarray, y: np.ndarray, names: Optional[Sequence[str]] = None,
            cov: str = "HC1", hac_lags: Optional[int] = None,
            add_intercept: bool = True) -> OLSResult:
    """Fit y = X beta + e by OLS.

    cov: "classical" (homoskedastic), "HC1" (White heteroskedasticity-robust),
         or "HAC" (Newey-West, robust to heteroskedasticity + autocorrelation).
    """
    y = np.asarray(y, dtype=float).ravel()
    X = np.asarray(X, dtype=float)
    if X.ndim == 1:
        X = X.reshape(-1, 1)
    if add_intercept:
        X = add_const(X)
        names = (["const"] + list(names)) if names is not None else None
    n, k = X.shape
    if names is None:
        names = ["const"] + [f"x{i}" for i in range(1, k)]
    names = list(names)

    XtX = X.T @ X
    XtX_inv = np.linalg.pinv(XtX)
    beta = XtX_inv @ (X.T @ y)
    fitted = X @ beta
    resid = y - fitted

    ss_res = float(resid @ resid)
    ss_tot = float(((y - y.mean()) ** 2).sum())
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0
    dof_resid = max(n - k, 1)
    adj_r2 = 1.0 - (1.0 - r2) * (n - 1) / dof_resid if n > k else r2

    # classical (homoskedastic) covariance
    sigma2 = ss_res / dof_resid
    cov_classical = sigma2 * XtX_inv
    se_classical = np.sqrt(np.clip(np.diag(cov_classical), 0, None))

    if cov == "classical":
        V = cov_classical
    elif cov == "HC1":
        meat = X.T @ (X * (resid ** 2)[:, None])          # X' diag(e^2) X
        V = XtX_inv @ meat @ XtX_inv * (n / dof_resid)     # HC1 small-sample scale
    elif cov == "HAC":
        L = _hac_lag(n) if hac_lags is None else int(hac_lags)
        u = X * resid[:, None]                              # (n,k) score contributions
        S = u.T @ u                                         # lag-0
        for l in range(1, L + 1):
            w = 1.0 - l / (L + 1.0)                         # Bartlett weight
            Gamma = u[l:].T @ u[:-l]
            S = S + w * (Gamma + Gamma.T)
        V = XtX_inv @ S @ XtX_inv * (n / dof_resid)
    else:
        raise ValueError(f"unknown cov type: {cov}")

    se = np.sqrt(np.clip(np.diag(V), 0, None))
    with np.errstate(divide="ignore", invalid="ignore"):
        tstat = np.where(se > 0, beta / se, 0.0)
    pvalue = 2 * _stats.t.sf(np.abs(tstat), df=dof_resid)

    # overall F-test (all slopes zero), classical form
    if k > 1 and ss_tot > 0 and ss_res > 0:
        fstat = ((ss_tot - ss_res) / (k - 1)) / (ss_res / dof_resid)
        f_pvalue = float(_stats.f.sf(fstat, k - 1, dof_resid))
    else:
        fstat, f_pvalue = float("nan"), float("nan")

    return OLSResult(
        names=names, coef=beta, se=se, se_classical=se_classical,
        tstat=tstat, pvalue=pvalue, r2=r2, adj_r2=adj_r2,
        fstat=float(fstat), f_pvalue=float(f_pvalue), n=n, k=k,
        cov_type=cov, resid=resid, fitted=fitted, _XtX_inv=XtX_inv, _X=X,
    )


# ══════════════════════════════════════════════════════════════════════════
# Residual diagnostics
# ══════════════════════════════════════════════════════════════════════════

def durbin_watson(resid: np.ndarray) -> float:
    """~2 = no first-order autocorrelation; <2 positive, >2 negative."""
    e = np.asarray(resid, dtype=float)
    d = np.diff(e)
    denom = float((e ** 2).sum())
    return float((d @ d) / denom) if denom > 0 else float("nan")


def breusch_pagan(resid: np.ndarray, X: np.ndarray, add_intercept: bool = True) -> dict:
    """LM test for heteroskedasticity: regress e^2 on the regressors.
    LM = n * R^2_aux ~ chi2(df = #regressors excl. const). Low p => heteroskedastic."""
    e = np.asarray(resid, dtype=float)
    aux = fit_ols(X, e ** 2, cov="classical", add_intercept=add_intercept)
    lm = aux.n * aux.r2
    df = aux.k - 1
    p = float(_stats.chi2.sf(lm, df)) if df > 0 else float("nan")
    return {"lm_stat": float(lm), "df": df, "p_value": p,
            "heteroskedastic": bool(p < 0.05)}


def jarque_bera(resid: np.ndarray) -> dict:
    """Normality of residuals via skewness/kurtosis. Low p => non-normal."""
    e = np.asarray(resid, dtype=float)
    n = len(e)
    s = _stats.skew(e)
    k = _stats.kurtosis(e, fisher=True)      # excess kurtosis
    jb = n / 6.0 * (s ** 2 + (k ** 2) / 4.0)
    p = float(_stats.chi2.sf(jb, 2))
    return {"jb_stat": float(jb), "skew": float(s), "excess_kurtosis": float(k),
            "p_value": p, "normal": bool(p > 0.05)}


def diagnostics(res: OLSResult) -> dict:
    """Bundle the standard residual diagnostics for a fitted model."""
    X_noconst = res._X[:, 1:]                 # drop the intercept column
    return {
        "durbin_watson": durbin_watson(res.resid),
        "breusch_pagan": breusch_pagan(res.resid, X_noconst),
        "jarque_bera": jarque_bera(res.resid),
    }


# ══════════════════════════════════════════════════════════════════════════
# Cost-model feature engineering + fit
# ══════════════════════════════════════════════════════════════════════════

# Default regressors for the execution cost curve. sqrt(size %ADV) is the
# primary term (square-root market-impact law); the rest are the standard
# conditioning variables a desk controls for.
DEFAULT_FEATURES = ("sqrt_size_pct_adv", "vol_ann", "participation", "spread_bps", "duration_frac")


def build_cost_design(panel: pd.DataFrame,
                      features: Sequence[str] = DEFAULT_FEATURES,
                      cost_col: str = "cost_bps") -> tuple[np.ndarray, np.ndarray, list]:
    """Build (X, y, names) for the cost regression from a panel DataFrame.

    Derives sqrt_size_pct_adv from size_pct_adv if not already present. Missing
    optional features are simply skipped (so a sparse panel still fits)."""
    df = panel.copy()
    if "sqrt_size_pct_adv" in features and "sqrt_size_pct_adv" not in df.columns:
        if "size_pct_adv" in df.columns:
            df["sqrt_size_pct_adv"] = np.sqrt(np.clip(df["size_pct_adv"].astype(float), 0, None))
    use = [f for f in features if f in df.columns]
    X = df[use].astype(float).to_numpy()
    y = df[cost_col].astype(float).to_numpy()
    return X, y, list(use)


def fit_cost_model(panel: pd.DataFrame,
                   features: Sequence[str] = DEFAULT_FEATURES,
                   cost_col: str = "cost_bps", cov: str = "HC1") -> OLSResult:
    """Fit the execution cost curve on a panel. Returns an OLSResult whose
    .predict() gives the expected cost (bps) for a new order's features — a
    conditional TCA benchmark."""
    X, y, names = build_cost_design(panel, features, cost_col)
    return fit_ols(X, y, names=names, cov=cov)


# ══════════════════════════════════════════════════════════════════════════
# A/B testing with controls (the GSET signature deliverable)
# ══════════════════════════════════════════════════════════════════════════

@dataclass
class ABResult:
    baseline: str
    table: pd.DataFrame              # per-strategy incremental cost vs baseline
    r2: float
    n: int
    cov_type: str
    naive_diff: dict                 # raw (uncontrolled) mean-cost difference per strategy
    note: str = ""


def ab_test_with_controls(panel: pd.DataFrame, strategy_col: str = "algo",
                          cost_col: str = "cost_bps",
                          controls: Sequence[str] = ("sqrt_size_pct_adv", "vol_ann",
                                                     "participation", "spread_bps"),
                          baseline: Optional[str] = None,
                          cov: str = "HC1") -> ABResult:
    """Regression-based A/B test: cost ~ strategy dummies + controls.

    The coefficient on each strategy dummy is that strategy's incremental cost
    (bps) vs. the baseline, HOLDING conditions fixed — the apples-to-apples
    number a raw mean difference cannot give when strategies ran on different
    orders. Lower (more negative) = cheaper than baseline. Also returns the naive
    uncontrolled mean difference so the confounding adjustment is visible.
    """
    df = panel.copy()
    if "sqrt_size_pct_adv" in controls and "sqrt_size_pct_adv" not in df.columns \
            and "size_pct_adv" in df.columns:
        df["sqrt_size_pct_adv"] = np.sqrt(np.clip(df["size_pct_adv"].astype(float), 0, None))

    strategies = list(pd.unique(df[strategy_col]))
    if baseline is None:
        # baseline = cheapest by raw mean (a sensible reference)
        baseline = df.groupby(strategy_col)[cost_col].mean().idxmin()
    others = [s for s in strategies if s != baseline]

    # design: controls + one dummy per non-baseline strategy
    ctrl = [c for c in controls if c in df.columns]
    Xparts, names = [], []
    for c in ctrl:
        Xparts.append(df[c].astype(float).to_numpy())
        names.append(c)
    for s in others:
        Xparts.append((df[strategy_col] == s).astype(float).to_numpy())
        names.append(f"algo[{s}]")
    X = np.column_stack(Xparts) if Xparts else np.zeros((len(df), 0))
    y = df[cost_col].astype(float).to_numpy()
    res = fit_ols(X, y, names=names, cov=cov)

    means = df.groupby(strategy_col)[cost_col].mean()
    rows, naive = [], {}
    sf = res.summary_frame()
    for s in others:
        nm = f"algo[{s}]"
        naive[s] = float(means[s] - means[baseline])
        rows.append({
            "strategy": s,
            "incremental cost vs baseline (bps)": round(float(sf.loc[nm, "coef"]), 3),
            "std err": round(float(sf.loc[nm, "std err"]), 3),
            "t": round(float(sf.loc[nm, "t"]), 2),
            "P>|t|": round(float(sf.loc[nm, "P>|t|"]), 4),
            "naive diff (uncontrolled)": round(naive[s], 3),
        })
    table = pd.DataFrame(rows).set_index("strategy") if rows else pd.DataFrame()
    note = (f"Baseline = {baseline}. Incremental cost is the strategy dummy's "
            f"coefficient, holding {', '.join(ctrl) or 'no'} controls fixed; "
            "compare it to the uncontrolled naive difference to see the "
            "confounding adjustment.")
    return ABResult(baseline=baseline, table=table, r2=res.r2, n=res.n,
                    cov_type=cov, naive_diff=naive, note=note)
