"""Statistics & microstructure additions (2026-07-08 review):
algo wheel (Friedman+Nemenyi), event-study inference (Brown-Warner),
Roll (1984) spread, post-fill markout curve, post-event liquidity shift."""
import numpy as np
import pandas as pd
import pytest

from agents.algo_wheel import run_algo_wheel
from agents.rebalancing_event_study import event_inference, compute_liquidity_shift
from agents.microstructure_analytics import roll_spread, compute_markout_curve


# ── Algo wheel ─────────────────────────────────────────────────────────────

def _wheel_df(n_days=20, seed=7):
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range("2026-01-05", periods=n_days)
    return pd.DataFrame({
        "CHEAP": rng.normal(5, 1, n_days),       # dominates
        "MID":   rng.normal(9, 1, n_days),
        "DEAR":  rng.normal(13, 1, n_days),
    }, index=idx)


def test_wheel_detects_clear_ordering():
    w = run_algo_wheel(_wheel_df())
    assert w.available
    assert w.friedman_p < 0.001
    assert w.best_algo == "CHEAP"
    league = w.league.set_index("Algo")
    assert league.loc["CHEAP", "Avg rank"] < league.loc["MID", "Avg rank"] \
           < league.loc["DEAR", "Avg rank"]
    assert "YES" in league.loc["DEAR", "Separable from best?"]
    assert league.loc["CHEAP", "Separable from best?"].startswith("—")


def test_wheel_nemenyi_cd_formula():
    from scipy.stats import studentized_range
    w = run_algo_wheel(_wheel_df(n_days=20))
    k, n = 3, 20
    cd = studentized_range.ppf(0.95, k, np.inf) / np.sqrt(2) * np.sqrt(k * (k + 1) / (6 * n))
    assert w.critical_difference == pytest.approx(cd, abs=1e-3)


def test_wheel_indistinguishable_arms_flagged():
    rng = np.random.default_rng(3)
    df = pd.DataFrame(rng.normal(8, 2, size=(12, 4)),
                      columns=list("ABCD"),
                      index=pd.bdate_range("2026-01-05", periods=12))
    w = run_algo_wheel(df)
    assert w.available
    if w.friedman_p >= 0.05:
        assert "NOT" in w.notes[0]


def test_wheel_guards():
    df = _wheel_df(n_days=3)
    assert not run_algo_wheel(df).available            # too few days
    assert not run_algo_wheel(_wheel_df()[["CHEAP", "MID"]]).available  # too few algos


# ── Event-study inference (Brown-Warner single-firm) ──────────────────────

def test_event_inference_flat_market_anchor():
    L = 60
    rng = np.random.default_rng(0)
    resid = rng.normal(0, 0.01, L)
    rm_est = np.zeros(L)             # flat market: forecast-error term needs ssrm>0
    rm_est[0] = 1e-6                 # tiny variation to keep ssrm positive
    AR = np.array([0.02, -0.01, 0.0])
    rm_ev = np.zeros(3)
    ar_t, car_sigma = event_inference(AR, resid, rm_est, rm_ev)
    s = np.sqrt(np.sum(resid**2) / (L - 2))
    expect_sd = s * np.sqrt(1 + 1/L)         # (Rm_t - Rm_bar)^2/ssrm ~ 0 here... but rm_bar tiny
    assert ar_t[0] == pytest.approx(AR[0] / expect_sd, rel=0.05)
    # CAR sigma grows like sqrt of cumulative variance
    assert car_sigma[2] == pytest.approx(expect_sd * np.sqrt(3), rel=0.05)
    assert car_sigma[2] > car_sigma[1] > car_sigma[0]


def test_event_inference_too_short_returns_none():
    assert event_inference(np.array([0.01]), np.zeros(5), np.zeros(5), np.zeros(1)) == (None, None)


# ── Roll (1984) spread ─────────────────────────────────────────────────────

def test_roll_recovers_pure_bounce_spread():
    # Roll's model: p_t = mid + (s/2) q_t with q_t iid ±1 -> cov(dp_t, dp_{t-1})
    # = -s^2/4 -> implied spread = s. (A deterministic alternation is NOT iid
    # and doubles the estimate — hence the random sequence here.)
    rng = np.random.default_rng(42)
    n, sconst = 5000, 1.0
    q = rng.choice([1.0, -1.0], size=n)
    px = 100 + (sconst / 2) * q
    r = roll_spread(pd.DataFrame({"Close": px}))
    assert r["spread_bps"] == pytest.approx(sconst / 100 * 10_000, rel=0.10)


def test_roll_undefined_on_pure_trend():
    daily = pd.DataFrame({"Close": np.linspace(100, 120, 100)})
    r = roll_spread(daily)
    assert r["spread_bps"] is None and "non-negative" in r["note"]


# ── Markout curve ──────────────────────────────────────────────────────────

def _mk_day_and_schedule(drift_per_bar=0.1):
    idx = pd.date_range("2026-06-04 09:30", periods=30, freq="5min")
    closes = 100 + drift_per_bar * np.arange(30)
    day = pd.DataFrame({"Close": closes}, index=idx)
    sched = pd.DataFrame({
        "time": [idx[5]], "shares_traded": [1000.0],
        "price": [closes[5]], "cumulative": [1000.0]})
    return day, sched


def test_markout_positive_when_price_trends_against_buy():
    day, sched = _mk_day_and_schedule(drift_per_bar=0.1)
    mo = compute_markout_curve(sched, day, "Buy", horizons=(1, 2, 3))
    assert mo["available"]
    c = mo["curve"].set_index("horizon_min")["markout_bps"]
    # buy fill at bar5 close; +h bars later price is h*0.1 higher
    assert c.loc[5] == pytest.approx(0.1 / closes_at(day, 5) * 1e4, rel=0.01)
    assert c.loc[15] > c.loc[5] > 0
    assert "against the order" in mo["note"] or "persistent" in mo["note"]


def closes_at(day, i):
    return float(day["Close"].iloc[i])


def test_markout_sell_mirror():
    day, sched = _mk_day_and_schedule(drift_per_bar=0.1)
    buy = compute_markout_curve(sched, day, "Buy", horizons=(1, 2))
    sell = compute_markout_curve(sched, day, "Sell", horizons=(1, 2))
    b = buy["curve"]["markout_bps"].values
    s = sell["curve"]["markout_bps"].values
    assert np.allclose(b, -s)


def test_markout_unavailable_when_fills_at_close():
    day, sched = _mk_day_and_schedule()
    sched["time"] = [day.index[-1]]                    # fill on the last bar
    sched["price"] = [float(day["Close"].iloc[-1])]
    mo = compute_markout_curve(sched, day, "Buy", horizons=(6,))
    assert not mo["available"]


# ── Post-event liquidity shift ─────────────────────────────────────────────

def test_liquidity_shift_detects_beta_change():
    rng = np.random.default_rng(1)
    n_pre, n_post = 60, 15
    idx = pd.bdate_range("2026-01-05", periods=n_pre + 1 + n_post)
    m = rng.normal(0, 0.01, len(idx))
    stock_r = np.concatenate([
        0.5 * m[:n_pre] + rng.normal(0, 0.002, n_pre),          # beta 0.5 pre
        [0.0],
        1.5 * m[n_pre + 1:] + rng.normal(0, 0.002, n_post),     # beta 1.5 post
    ])
    stock = 100 * np.cumprod(1 + stock_r)
    index = 1000 * np.cumprod(1 + m)
    combined = pd.DataFrame({"stock": stock, "index": index}, index=idx)
    raw = pd.DataFrame({"Open": stock, "High": stock * 1.01, "Low": stock * 0.99,
                        "Close": stock, "Volume": np.full(len(idx), 1e6)}, index=idx)
    ls = compute_liquidity_shift(raw, combined, est_start=0, est_end=n_pre,
                                 T_idx=n_pre, alpha=0.0, beta=0.5)
    assert ls.available and ls.n_post_days == n_post
    assert ls.beta_post > 1.0 > ls.beta_pre
    assert ls.edge_pre_bps is None or ls.edge_pre_bps >= 0


def test_liquidity_shift_needs_post_days():
    idx = pd.bdate_range("2026-01-05", periods=65)
    combined = pd.DataFrame({"stock": np.full(65, 100.0), "index": np.full(65, 1000.0)}, index=idx)
    raw = pd.DataFrame({"Open": 100.0, "High": 101.0, "Low": 99.0, "Close": 100.0,
                        "Volume": 1e6}, index=idx)
    ls = compute_liquidity_shift(raw, combined, 0, 60, 62, 0.0, 1.0)
    assert not ls.available


# ── Condition-adjusted ranking (wheel defense — Execution Solutions angle) ──

from agents.algo_wheel import condition_adjusted_ranking


def _confounded_panel(n=120, seed=11):
    """Algo GOOD has the better engine (-3 bps at equal conditions) but
    receives systematically LARGER orders; BAD gets small easy flow; MID in
    between. Raw means make GOOD look worst — adjustment must correct it."""
    rng = np.random.default_rng(seed)
    rows = []
    for algo, edge, size_mu in (("GOOD", -3.0, 15.0), ("MID", 0.0, 8.0), ("BAD", 3.0, 3.0)):
        for _ in range(n // 3):
            size = max(0.5, rng.normal(size_mu, 1.0))
            vol = max(0.05, rng.normal(0.25, 0.03))
            cost = 4.0 * np.sqrt(size) + 20.0 * vol + edge + rng.normal(0, 0.5)
            rows.append({"algo": algo, "size_pct_adv": size, "vol_ann": vol,
                         "participation": size, "spread_bps": 5.0,
                         "duration_frac": 1.0, "cost_bps": cost})
    return pd.DataFrame(rows)


def test_adjusted_ranking_corrects_confounded_raw_rank():
    out = condition_adjusted_ranking(_confounded_panel())
    assert out["available"]
    t = out["table"].set_index("Algo")
    # Raw means punish GOOD (hardest flow): raw rank worst
    assert t.loc["GOOD", "Raw rank"] == 3
    # Net of conditions, GOOD is best and separable
    assert t.loc["GOOD", "Adjusted rank"] == 1
    assert t.loc["GOOD", "Adjusted vs baseline (bps)"] < 0
    assert "GOOD" in out["movers"]
    assert t.loc["GOOD", "Separable from baseline?"] in ("YES", "— (baseline)")


def test_adjusted_ranking_matches_raw_on_balanced_grid():
    # identical condition distribution per algo -> ranks coincide
    rng = np.random.default_rng(5)
    rows = []
    for algo, edge in (("A", 0.0), ("B", 2.0), ("C", 4.0)):
        for size in (2.0, 5.0, 10.0) * 12:
            cost = 4.0 * np.sqrt(size) + edge + rng.normal(0, 0.3)
            rows.append({"algo": algo, "size_pct_adv": size, "vol_ann": 0.25,
                         "participation": size, "spread_bps": 5.0,
                         "duration_frac": 1.0, "cost_bps": cost})
    out = condition_adjusted_ranking(pd.DataFrame(rows))
    t = out["table"]
    assert (t["Raw rank"] == t["Adjusted rank"]).all()
    assert out["movers"] == []


def test_adjusted_ranking_guard():
    small = _confounded_panel().head(10)
    assert not condition_adjusted_ranking(small)["available"]
