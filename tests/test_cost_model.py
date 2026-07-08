"""Regression-based transaction cost model (agents/cost_model.py) + the cost
panel assembler (agents/cost_panel.py).

Covers the JD's statistical battery: OLS coefficient recovery, heteroskedasticity-
robust (HC1) and autocorrelation-robust (Newey-West HAC) standard errors,
residual diagnostics (Durbin-Watson / Breusch-Pagan / Jarque-Bera), and — the
headline value — that an A/B test run as a regression WITH controls debiases a
confounder that a naive mean difference gets wrong."""
import numpy as np
import pandas as pd
import pytest

from agents.cost_model import (
    fit_ols, add_const, durbin_watson, breusch_pagan, jarque_bera, diagnostics,
    fit_cost_model, ab_test_with_controls, build_cost_design,
)


# ── OLS core ───────────────────────────────────────────────────────────────

def test_ols_recovers_known_coefficients():
    rng = np.random.RandomState(0)
    n = 500
    x1 = rng.uniform(0, 1, n)
    x2 = rng.uniform(0, 5, n)
    y = 2.0 + 3.0 * x1 - 1.5 * x2 + rng.randn(n) * 0.5
    res = fit_ols(np.column_stack([x1, x2]), y, names=["x1", "x2"], cov="HC1")
    assert res.coef == pytest.approx([2.0, 3.0, -1.5], abs=0.15)
    assert res.r2 > 0.9
    assert res.f_pvalue < 1e-6
    # strong true effects => tiny p-values
    assert (res.pvalue[1:] < 1e-6).all()


def test_predict_matches_manual_dot_product():
    res = fit_ols(np.array([[1.0], [2.0], [3.0], [4.0]]), np.array([2.0, 4.0, 6.0, 8.0]),
                  names=["x"], cov="classical")
    # y = 2x exactly => const ~0, slope ~2
    assert res.predict(add_const(np.array([[10.0]])))[0] == pytest.approx(20.0, abs=1e-6)


def test_hc1_inflates_se_under_heteroskedasticity():
    rng = np.random.RandomState(1)
    n = 2000
    x = rng.uniform(1, 10, n)
    # residual variance grows sharply with x (high-variance obs at high leverage)
    y = 1.0 + 2.0 * x + rng.randn(n) * (x ** 1.5)
    classical = fit_ols(x, y, names=["x"], cov="classical")
    robust = fit_ols(x, y, names=["x"], cov="HC1")
    i = robust.names.index("x")
    # OLS understates the slope SE here; the White-robust SE corrects it upward
    assert robust.se[i] > classical.se_classical[i]


def test_hac_handles_autocorrelation():
    rng = np.random.RandomState(2)
    n = 800
    x = np.linspace(0.0, 1.0, n)                  # trending regressor
    e = np.zeros(n)
    for t in range(1, n):
        e[t] = 0.8 * e[t - 1] + rng.randn()       # AR(1) residuals
    y = 1.0 + 2.0 * x + e
    hac = fit_ols(x, y, names=["x"], cov="HAC")
    classical = fit_ols(x, y, names=["x"], cov="classical")
    i = hac.names.index("x")
    # with a trending regressor and autocorrelated errors, OLS badly understates
    # the SE; Newey-West corrects it upward materially
    assert hac.se[i] > 1.3 * classical.se_classical[i]


# ── Diagnostics ────────────────────────────────────────────────────────────

def test_durbin_watson_iid_vs_autocorrelated():
    rng = np.random.RandomState(3)
    iid = rng.randn(1000)
    assert durbin_watson(iid) == pytest.approx(2.0, abs=0.2)
    ar = np.zeros(1000)
    for t in range(1, 1000):
        ar[t] = 0.8 * ar[t - 1] + rng.randn()
    assert durbin_watson(ar) < 1.0        # strong positive autocorrelation


def test_breusch_pagan_flags_heteroskedasticity():
    rng = np.random.RandomState(4)
    n = 600
    x = rng.uniform(1, 10, n)
    het = fit_ols(x, 1 + 2 * x + rng.randn(n) * x, names=["x"], cov="classical")
    hom = fit_ols(x, 1 + 2 * x + rng.randn(n) * 0.5, names=["x"], cov="classical")
    assert diagnostics(het)["breusch_pagan"]["heteroskedastic"] is True
    assert diagnostics(hom)["breusch_pagan"]["heteroskedastic"] is False


def test_jarque_bera_flags_nonnormal():
    rng = np.random.RandomState(5)
    normal = rng.randn(2000)
    heavy = rng.standard_t(3, size=2000)      # heavy tails
    assert jarque_bera(normal)["normal"] is True
    assert jarque_bera(heavy)["normal"] is False


# ── Cost model + A/B with controls ─────────────────────────────────────────

def test_cost_model_recovers_sqrt_law_coefficient():
    rng = np.random.RandomState(6)
    n = 400
    size = rng.uniform(0.5, 25, n)
    vol = rng.uniform(0.1, 0.4, n)
    part = rng.uniform(1, 20, n)
    spread = rng.uniform(1, 10, n)
    # true cost curve: 30 * sqrt(size) + 100 * vol + noise
    cost = 30 * np.sqrt(size) + 100 * vol + rng.randn(n) * 3
    panel = pd.DataFrame({"size_pct_adv": size, "vol_ann": vol,
                          "participation": part, "spread_bps": spread,
                          "duration_frac": 1.0, "cost_bps": cost})
    res = fit_cost_model(panel, cov="HC1")
    sqrt_i = res.names.index("sqrt_size_pct_adv")
    vol_i = res.names.index("vol_ann")
    assert res.coef[sqrt_i] == pytest.approx(30.0, rel=0.15)
    assert res.coef[vol_i] == pytest.approx(100.0, rel=0.25)


def test_ab_with_controls_debiases_a_confounder():
    # Truth: strategy B has NO real cost effect, but it was run mostly on
    # SMALL (easy) orders => a naive mean diff makes B look cheaper. Controlling
    # for size must recover ~0 incremental cost.
    rng = np.random.RandomState(7)
    nA, nB = 300, 300
    sizeA = rng.uniform(10, 25, nA)      # A on big orders
    sizeB = rng.uniform(1, 6, nB)        # B on small orders (confounder)
    costA = 10 + 5 * sizeA + rng.randn(nA) * 2
    costB = 10 + 5 * sizeB + rng.randn(nB) * 2      # SAME cost law, no B effect
    panel = pd.DataFrame({
        "algo": ["A"] * nA + ["B"] * nB,
        "size_pct_adv": np.concatenate([sizeA, sizeB]),
        "vol_ann": 0.2, "participation": 5.0, "spread_bps": 3.0,
        "cost_bps": np.concatenate([costA, costB]),
    })
    ab = ab_test_with_controls(panel, baseline="A",
                               controls=("size_pct_adv",))
    controlled = ab.table.loc["B", "incremental cost vs baseline (bps)"]
    naive = ab.naive_diff["B"]
    assert naive < -20          # B looks much cheaper uncontrolled
    assert abs(controlled) < 8  # controlling for size, the effect ~ 0 (truth)
    assert abs(controlled - naive) > 20   # the adjustment is large & material


# ── Offline integration on the recorded fixture ────────────────────────────

def test_build_panel_and_fit_on_fixture():
    import json
    from pathlib import Path
    from agents.agent1_market_data import MarketData
    from agents.cost_panel import build_cost_panel
    FIX = Path(__file__).resolve().parent / "fixtures"
    if not (FIX / "AAPL_meta.json").exists():
        pytest.skip("fixture missing")
    meta = json.load(open(FIX / "AAPL_meta.json"))
    md = MarketData(ticker=meta["ticker"], market=meta["market"],
                    intraday=pd.read_parquet(FIX / "AAPL_intraday.parquet"),
                    daily=pd.read_parquet(FIX / "AAPL_daily.parquet"),
                    adv_shares=float(meta["adv_shares"]), adv_usd=float(meta["adv_usd"]),
                    current_price=float(meta["current_price"]),
                    realized_vol_ann=float(meta["realized_vol_ann"]),
                    vol_profile=pd.DataFrame(), vol_note="")
    panel = build_cost_panel(md, sizes_pct_adv=(1, 2, 5, 10, 15, 20))
    assert len(panel) > 50
    assert set(["cost_bps", "sqrt_size_pct_adv", "vol_ann", "algo"]).issubset(panel.columns)
    res = fit_cost_model(panel, cov="HC1")
    # impact must rise with size (square-root term positive)
    assert res.coef[res.names.index("sqrt_size_pct_adv")] > 0
    ab = ab_test_with_controls(panel, baseline="TWAP")
    assert len(ab.table) == panel["algo"].nunique() - 1
