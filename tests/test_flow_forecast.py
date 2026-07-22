"""Flow-prediction framework (Layers 1-6) — all offline, synthetic anchors."""
import numpy as np
import pandas as pd
import pytest

from agents.flow_forecast import (dm_test, daily_volume_forecast, blended_day_total,
                                  close_share_series, close_share_ar1,
                                  imbalance_diagnostics, ml_volume_gate, event_uplift)
from tests.conftest import make_market_data


def _ar1_log_volumes(n=120, phi=0.7, mu=13.0, sd=0.25, seed=3):
    rng = np.random.default_rng(seed)
    x = np.zeros(n); x[0] = mu
    for t in range(1, n):
        x[t] = mu + phi * (x[t-1] - mu) + rng.normal(0, sd)
    idx = pd.bdate_range("2026-01-05", periods=n)
    return pd.Series(np.exp(x), index=idx)


# ── DM test ────────────────────────────────────────────────────────────────

def test_dm_detects_clearly_better_forecaster():
    rng = np.random.default_rng(0)
    e_good = rng.normal(0, 1.0, 200)
    e_bad = rng.normal(0, 2.0, 200)
    dm = dm_test(e_good, e_bad)
    assert dm["stat"] < 0 and dm["p_one_sided"] < 0.01
    # symmetric: bad vs good flips sign
    assert dm_test(e_bad, e_good)["stat"] > 0


def test_dm_indifferent_on_equal_forecasters():
    rng = np.random.default_rng(1)
    e1, e2 = rng.normal(0, 1, 300), rng.normal(0, 1, 300)
    assert dm_test(e1, e2)["p_one_sided"] > 0.05


# ── Layer 1 ────────────────────────────────────────────────────────────────

def test_daily_forecast_ships_model_on_persistent_series():
    f = daily_volume_forecast(_ar1_log_volumes(phi=0.85))
    assert f.available and f.n_eval > 30
    assert f.mae_model < f.mae_median            # persistence is learnable
    assert f.chosen_model == "AR+calendar"
    assert f.forecast_next > 0
    assert "shipping the model" in f.note


def test_daily_forecast_ships_median_on_white_noise():
    rng = np.random.default_rng(7)
    idx = pd.bdate_range("2026-01-05", periods=120)
    v = pd.Series(np.exp(13 + rng.normal(0, 0.3, 120)), index=idx)  # iid: nothing to learn
    f = daily_volume_forecast(v)
    assert f.available
    assert f.chosen_model == "median20"          # gate holds: can't beat naive -> ship naive
    assert "median" in f.note


def test_daily_forecast_guard():
    assert not daily_volume_forecast(_ar1_log_volumes(n=10)).available


# ── Layer 2 ────────────────────────────────────────────────────────────────

def test_blend_trusts_prior_early_and_tape_late():
    early = blended_day_total(1_000_000, realized_so_far=50_000, cum_curve=0.05)
    late = blended_day_total(1_000_000, realized_so_far=1_800_000, cum_curve=0.90)
    assert early["weight_on_tape"] < 0.2
    assert late["weight_on_tape"] > 0.85
    # late blend ~ grossup (2.0M); early blend ~ prior (1.0M)
    assert abs(early["blended_total"] - 1_000_000) < 150_000
    assert abs(late["blended_total"] - 2_000_000) < 150_000


# ── Layer 3 ────────────────────────────────────────────────────────────────

def test_close_share_ar1_recovers_dynamics_and_forecast_formula():
    rng = np.random.default_rng(5)
    mu, phi, n = 0.08, 0.7, 300
    x = np.zeros(n); x[0] = mu
    for t in range(1, n):
        x[t] = mu + phi * (x[t-1] - mu) + rng.normal(0, 0.01)
    s = pd.Series(x, index=pd.bdate_range("2025-01-01", periods=n))
    f = close_share_ar1(s)
    assert f.available
    assert f.mu == pytest.approx(mu, abs=0.01)
    assert f.phi == pytest.approx(phi, abs=0.1)
    assert f.forecast_next == pytest.approx(f.mu + f.phi * (f.latest - f.mu), abs=1e-4)  # fields round to 4dp
    assert f.half_life_days == pytest.approx(np.log(0.5)/np.log(f.phi), abs=0.05)


def test_close_share_series_from_intraday():
    md = make_market_data()
    s = close_share_series(md.intraday)
    assert len(s) >= 3
    assert ((s > 0) & (s < 1)).all()


# ── Layer 5 ────────────────────────────────────────────────────────────────

def test_imbalance_diagnostics_flags_one_sided_day():
    idx = pd.date_range("2026-06-04 09:30", periods=78, freq="5min")
    up = np.cumsum(np.abs(np.random.default_rng(2).normal(0.05, 0.02, 78)))
    day = pd.DataFrame({"Open": 100+up, "High": 100.2+up, "Low": 99.9+up,
                        "Close": 100.1+up, "Volume": 10_000}, index=idx)
    d = imbalance_diagnostics(day)
    assert d["available"]
    assert d["mean_imbalance"] > 0.3          # persistent buying classified by BVC
    assert "NOT a direction forecast" in d["note"] or "two-sided" in d["note"]


# ── Layer 6 ────────────────────────────────────────────────────────────────

def test_ml_gate_returns_verdict_and_respects_house_rule():
    out = ml_volume_gate(_ar1_log_volumes(n=140, phi=0.8))
    assert out["available"]
    assert out["engine"] in ("numpy-ridge", "sklearn-GBM")
    assert isinstance(out["use_ml"], bool)
    # on a pure AR series, features add ~nothing: the gate should be honest
    if not out["use_ml"]:
        assert "ship the simple model" in out["note"]


# ── Layer 4 ────────────────────────────────────────────────────────────────

def test_event_uplift_uses_library_median_or_placeholder():
    lib = {"n": 5, "median_t_day_volume_multiple": 1.8}
    u = event_uplift(lib)
    assert u["available"] and u["multiple"] == 1.8 and "n=5" in u["source"]
    u2 = event_uplift({"n": 1})
    assert not u2["available"] and u2["multiple"] == 1.4    # disclosed placeholder


# ---------------------------------------------------------------- L6b

from agents.flow_forecast import quantile_volume_forecast, pooled_volume_model


def _ar_log_volumes(n=120, phi=0.85, seed=7, sigma=0.3, mu=13.0):
    rng = np.random.default_rng(seed)
    x = np.zeros(n)
    for i in range(1, n):
        x[i] = phi * x[i - 1] + rng.normal(0, sigma)
    idx = pd.bdate_range("2026-01-02", periods=n)
    return pd.Series(np.exp(mu + x), index=idx)


def test_quantile_forecast_monotone_and_positive():
    q = quantile_volume_forecast(_ar_log_volumes())
    assert q.available
    p10, p50, p90 = q.forecast_shares
    assert 0 < p10 <= p50 <= p90


def test_quantile_gate_ships_empirical_on_white_noise():
    # iid lognormal: the regression has nothing to condition on, so the
    # rolling empirical quantiles must ship (house rule / anti-overfit gate).
    rng = np.random.default_rng(11)
    idx = pd.bdate_range("2026-01-02", periods=100)
    v = pd.Series(np.exp(13.0 + rng.normal(0, 0.3, 100)), index=idx)
    q = quantile_volume_forecast(v)
    assert q.available
    assert q.chosen_model == "empirical20"


def _dow_panel(n_sym=8, n=45, seed=3):
    """Symbols sharing a strong day-of-week effect + mild AR(1); per-name
    history too short for a name-alone model to learn the calendar."""
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range("2026-02-02", periods=n)
    dow_eff = np.array([0.0, 0.35, -0.30, 0.25, -0.35])   # Mon..Fri, in logs
    out = {}
    for s in range(n_sym):
        mu = 12.0 + rng.normal(0, 0.5)
        x = np.zeros(n)
        for i in range(1, n):
            x[i] = 0.3 * x[i - 1] + rng.normal(0, 0.12)
        logv = mu + x + dow_eff[idx.dayofweek]
        out[f"SYM{s}"] = pd.Series(np.exp(logv), index=idx)
    return out


def test_pooled_model_beats_per_name_ar_on_shared_calendar():
    m = pooled_volume_model(_dow_panel())
    assert m.available
    assert m.mae_pooled < m.mae_per_name          # pooling captures shared DOW
    assert set(m.next_forecast_shares) == {f"SYM{i}" for i in range(8)}
    assert all(v > 0 for v in m.next_forecast_shares.values())


def test_pooled_model_needs_two_symbols():
    m = pooled_volume_model({"ONLY": _ar_log_volumes(60)})
    assert not m.available
