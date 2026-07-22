"""AI-based rebalance-interest monitor — daily tracking of accumulating
interest in index-event candidates AHEAD of the effective date.

Interview design (docs/AI_REBALANCE_MONITOR_DESIGN.md has the full desk
architecture); this module is the free-data implementation of the core:

    candidates   <- rulebook screener (agents/reconstitution.py)
    features     <- per name-day, from bars anyone has: abnormal volume,
                    abnormal turnover trend, price drift vs own vol, range
                    expansion; plus OPTIONAL feeds the desk would wire in
                    (short-balance delta from the official regimes,
                    news/chat mention counts from an NLP layer).
    score        <- transparent weighted composite 0-100 with reasons
                    (the dealer can challenge every number)...
    AI layer     <- ...weights LEARNED from the event library (ridge on
                    past events: features at T-k -> realized event-day
                    volume multiple), walk-forward, and SHIPPED ONLY if
                    they beat the static composite under a DM gate —
                    the platform-wide house rule. A thin library ships
                    static weights and says so.
    surface      <- daily ranked monitor + TRANSITION alerts (same
                    fire-once pattern as the dealer cockpit) + audit trail.

The "AI" is deliberately two-stage: a learned model where history
supports it, a transparent fallback where it doesn't, and the gate
decides — never vibes.
"""
from __future__ import annotations

import datetime as _dt
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from agents.flow_forecast import dm_test, DM_ALPHA

BASE = 20                      # baseline window (days)
# static composite weights (transparent starting point; sum to 1)
STATIC_W = {"vol": 0.40, "drift": 0.25, "range": 0.15, "short": 0.10,
            "news": 0.10}
ALERT_HI, ALERT_MID = 60.0, 35.0


# ── features (per name, from daily bars) ───────────────────────────────────

def interest_features(daily: pd.DataFrame, short_delta: float = None,
                      news_count: float = None) -> dict:
    """Latest-day features from a daily OHLCV frame (>= BASE+5 rows).
    Each feature is scaled to roughly [0, 1] with disclosed caps."""
    d = daily.dropna(subset=["Close", "Volume"])
    if len(d) < BASE + 5:
        return {"available": False,
                "reason": f"need >= {BASE + 5} daily rows, have {len(d)}"}
    v = d["Volume"].to_numpy(dtype=float)
    c = d["Close"].to_numpy(dtype=float)
    hi = d["High"].to_numpy(dtype=float)
    lo = d["Low"].to_numpy(dtype=float)
    vol_ratio = v[-5:].mean() / max(np.median(v[-BASE - 5:-5]), 1.0)
    f_vol = min(max(vol_ratio - 1.0, 0.0) / 2.0, 1.0)      # 3x -> 1.0
    rets = np.diff(np.log(c))
    sig = rets[-BASE - 5:-5].std() or 1e-9
    drift = rets[-10:].sum() / (sig * np.sqrt(10))          # 10d drift, in sigmas
    f_drift = min(abs(drift) / 3.0, 1.0)                    # 3 sigma -> 1.0
    rng = (hi - lo) / c
    f_range = min(max(rng[-5:].mean() / max(rng[-BASE - 5:-5].mean(), 1e-9)
                      - 1.0, 0.0), 1.0)
    f_short = min(abs(short_delta), 1.0) if short_delta is not None else 0.0
    f_news = min((news_count or 0.0) / 10.0, 1.0)           # 10 mentions -> 1.0
    return {"available": True, "vol": round(f_vol, 3),
            "drift": round(f_drift, 3), "drift_sign": float(np.sign(drift)),
            "range": round(f_range, 3), "short": round(f_short, 3),
            "news": round(f_news, 3), "vol_ratio_raw": round(vol_ratio, 2)}


def interest_score(features: dict, weights: dict = None) -> dict:
    w = weights or STATIC_W
    score = 100.0 * sum(w[k] * features.get(k, 0.0) for k in w)
    reasons = [f"{k}={features.get(k, 0.0):.2f} (w={w[k]:.2f})"
               for k in w if features.get(k, 0.0) >= 0.25]
    tier = ("HOT" if score >= ALERT_HI else
            "WARM" if score >= ALERT_MID else "quiet")
    return {"score": round(min(score, 100.0), 1), "tier": tier,
            "reasons": "; ".join(reasons) or "no elevated feature"}


# ── AI layer: learn weights from the event library, gated ─────────────────

@dataclass
class LearnedWeights:
    available: bool
    reason: str = ""
    weights: dict = field(default_factory=lambda: dict(STATIC_W))
    source: str = "static"              # "static" | "learned"
    mae_learned: float = 0.0
    mae_static: float = 0.0
    dm_p: float = 0.5
    n_events: int = 0
    note: str = ""


def learn_weights(event_panel: pd.DataFrame,
                  ridge_lambda: float = 1.0) -> LearnedWeights:
    """Learn feature weights from past events: rows = one event each, with
    feature columns (vol/drift/range/short/news measured at T-k) and label
    `event_vol_multiple` (realized event-day volume multiple). Chronological
    70/30 split; learned ridge must beat the static composite\'s scaled
    prediction on test MAE with DM p < 0.10 — else ship static (house rule)."""
    feats = list(STATIC_W)
    need = feats + ["event_vol_multiple"]
    if event_panel is None or not all(c in event_panel.columns for c in need):
        return LearnedWeights(False, reason="panel missing feature/label columns")
    p = event_panel.dropna(subset=need)
    if len(p) < 12:
        return LearnedWeights(False, reason=f"only {len(p)} labeled events — "
                              "need >= 12; shipping static weights",
                              note="Library too thin to learn from (disclosed).")
    k = max(8, int(len(p) * 0.7))
    tr, te = p.iloc[:k], p.iloc[k:]
    if len(te) < 4:
        return LearnedWeights(False, reason="test slice < 4 events")
    X = tr[feats].to_numpy(dtype=float)
    y = tr["event_vol_multiple"].to_numpy(dtype=float)
    Xc = np.column_stack([np.ones(len(X)), X])
    beta = np.linalg.solve(Xc.T @ Xc + ridge_lambda * np.eye(Xc.shape[1]),
                           Xc.T @ y)
    Xt = np.column_stack([np.ones(len(te)), te[feats].to_numpy(dtype=float)])
    pred_l = Xt @ beta
    # static comparator with the SAME calibration freedom (intercept +
    # slope on the static composite) — otherwise the gate is rigged in the
    # learned model's favor on pure noise
    s_tr = X @ np.array([STATIC_W[f] for f in feats])
    A = np.column_stack([np.ones(len(s_tr)), s_tr])
    ab = np.linalg.lstsq(A, y, rcond=None)[0]
    s_te = te[feats].to_numpy(dtype=float) @ np.array(
        [STATIC_W[f] for f in feats])
    pred_s = ab[0] + ab[1] * s_te
    yt = te["event_vol_multiple"].to_numpy(dtype=float)
    err_l, err_s = np.abs(yt - pred_l), np.abs(yt - pred_s)
    dm = dm_test(err_l, err_s)
    use = err_l.mean() < err_s.mean() and dm["p_one_sided"] < DM_ALPHA
    if use:
        raw = np.clip(beta[1:], 0.0, None)
        w = ({f: float(r / raw.sum()) for f, r in zip(feats, raw)}
             if raw.sum() > 0 else dict(STATIC_W))
        src, note = "learned", (f"Learned weights beat static (MAE "
                                f"{err_l.mean():.2f} vs {err_s.mean():.2f}, "
                                f"DM p={dm['p_one_sided']}) on "
                                f"{len(p)} events.")
    else:
        w, src = dict(STATIC_W), "static"
        note = (f"Learned model did NOT beat the static composite (MAE "
                f"{err_l.mean():.2f} vs {err_s.mean():.2f}, DM "
                f"p={dm['p_one_sided']}) — shipping static (house rule).")
    return LearnedWeights(True, weights=w, source=src,
                          mae_learned=round(float(err_l.mean()), 3),
                          mae_static=round(float(err_s.mean()), 3),
                          dm_p=dm["p_one_sided"], n_events=int(len(p)),
                          note=note)


# ── monitor + transition alerts ────────────────────────────────────────────

def monitor_report(panel: dict, lw: LearnedWeights = None,
                   extras: dict = None) -> pd.DataFrame:
    """panel: {ticker: daily OHLCV df}; extras: {ticker: {short_delta,
    news_count}}. One ranked row per name with score, tier, reasons."""
    lw = lw or LearnedWeights(True, note="static weights")
    rows = []
    for t, d in panel.items():
        ex = (extras or {}).get(t, {})
        f = interest_features(d, ex.get("short_delta"), ex.get("news_count"))
        if not f.get("available"):
            rows.append({"ticker": t, "score": None, "tier": "n/a",
                         "reasons": f.get("reason", "")})
            continue
        sc = interest_score(f, lw.weights)
        rows.append({"ticker": t, "score": sc["score"], "tier": sc["tier"],
                     "vol_ratio": f["vol_ratio_raw"],
                     "drift_dir": "+" if f["drift_sign"] > 0 else "-",
                     "reasons": sc["reasons"]})
    df = pd.DataFrame(rows)
    return df.sort_values("score", ascending=False,
                          na_position="last").reset_index(drop=True)


def monitor_alerts(report: pd.DataFrame, prev_tiers: dict = None):
    """Fire-once transition alerts (cockpit pattern): quiet->WARM->HOT
    escalations only. Returns (alerts, new_tiers)."""
    prev_tiers = prev_tiers or {}
    order = {"n/a": 0, "quiet": 0, "WARM": 1, "HOT": 2}
    alerts, tiers = [], {}
    for _, r in report.iterrows():
        t, tier = r["ticker"], r["tier"]
        if order.get(tier, 0) > order.get(prev_tiers.get(t, "quiet"), 0):
            alerts.append({"ticker": t, "tier": tier,
                           "ts_utc": _dt.datetime.now(_dt.timezone.utc)
                           .isoformat(timespec="seconds"),
                           "message": f"interest escalated to {tier}: "
                                      f"{r['reasons']}"})
        tiers[t] = tier if tier in ("WARM", "HOT") else "quiet"
    return alerts, tiers


# ── demo data ──────────────────────────────────────────────────────────────

def demo_monitor_panel(seed: int = 8):
    """Three candidates: one HOT (volume + drift building into the event),
    one WARM (volume only), one quiet control."""
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range("2026-05-01", periods=40)

    def name(vol_mult_tail, drift_tail):
        c = 100 * np.exp(np.cumsum(rng.normal(0, 0.01, 40)))
        c[-10:] *= np.exp(np.linspace(0, drift_tail, 10))
        v = np.full(40, 1e6) * rng.uniform(0.9, 1.1, 40)
        v[-5:] *= vol_mult_tail
        return pd.DataFrame({"Open": c, "High": c * 1.01, "Low": c * 0.99,
                             "Close": c, "Volume": v}, index=idx)
    return {"HOT.T": name(3.5, 0.10), "WARM.HK": name(2.6, 0.03),
            "QUIET.SI": name(1.0, 0.0)}


def demo_event_panel(n: int = 30, signal: float = 3.0, seed: int = 4):
    """Synthetic past-event library: features -> label with tunable
    signal-to-noise (signal=0 -> weights unlearnable, gate must ship
    static)."""
    rng = np.random.default_rng(seed)
    f = pd.DataFrame({k: rng.uniform(0, 1, n) for k in STATIC_W})
    # true drivers deliberately ORTHOGONAL to the static weights (news/range
    # carry 20%/15% statically but 100% here) — the regime where learning
    # the weights genuinely pays and the gate should open
    label = (1.5 + signal * (0.7 * f["news"] + 0.3 * f["range"])
             + rng.normal(0, 0.3, n))
    f["event_vol_multiple"] = label.clip(lower=1.0)
    return f
