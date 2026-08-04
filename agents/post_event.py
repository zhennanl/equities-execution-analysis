"""Post-event pack — Step-4 analytics WITHOUT our own executions.

Session 9i. What a desk can honestly offer the morning after an
effective day, from tape + its own prior artifacts:

  1. BENCHMARK STRIP per name — official close, exact day VWAP
     (value/volume from official files), continuous-session VWAP
     (5m), TWAP estimate, last continuous price, the auction gap.
     Any client can drop their own fills against this strip and
     self-grade: the desk provides the ruler.
  2. STRATEGY LEADERBOARD for THIS event — what each canonical
     execution (MOC / T-day VWAP / window-linear) would have cost,
     per name: which playbook won this time.
  3. SELF-GRADING vs our OWN priors — realized print multiple vs
     the class prior, realized auction share vs prior, |gap| inside
     the quoted band or not: the estimate-accuracy ledger (the
     client-scorecard dimension applied to ourselves; our forecasts
     are our executions).
  4. REVERSAL TRACKER — T+1..T+5 favorable-signed path per name
     (completion-leg grading; feeds the playbook's cell-dependent
     reversal priors).
  5. CROWDING RESOLUTION — short-balance path through the print
     where cached: did the crowd exit as the mechanism claims.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def _stock_day(code):
    sd = json.loads((ROOT / "data" / "tw_history" /
                     "stock_day.json").read_text(encoding="utf-8"))
    rows = [r for m in sorted(sd.get(code, {}))
            for r in sd[code][m]]
    return sorted(rows)


def benchmark_strip(code: str, t_day: str) -> dict | None:
    from scripts.tday_execution_studies import _ib_day, _load_ib
    ib = _load_ib()
    days = _stock_day(code)
    d = next((r for r in days if r[0] == t_day), None)
    if d is None:
        return None
    off_close, day_vwap = d[6], (d[2] / d[1] if d[1] else None)
    twap_est = (d[3] + d[4] + d[5] + d[6]) / 4
    r = _ib_day(ib, code, t_day)
    cont_vwap = last_cont = auc_share = None
    if r:
        cont, auc, last_cont = r
        cv = sum(x[3] for x in cont)
        cont_vwap = (sum(x[2] * x[3] for x in cont) / cv
                     if cv else None)
        auc_share = auc / (auc + cv) if auc + cv else None
    return {"code": code, "t_day": t_day,
            "official_close": off_close,
            "day_vwap_exact": round(day_vwap, 2) if day_vwap else None,
            "cont_vwap_5m": round(cont_vwap, 2) if cont_vwap else None,
            "twap_est": round(twap_est, 2),
            "last_cont": last_cont,
            "gap_bps": round((off_close / last_cont - 1) * 1e4, 1)
            if last_cont else None,
            "auction_share": round(auc_share, 3) if auc_share
            else None,
            "t_volume": d[1]}


def strategy_leaderboard(code: str, side: str, ann: str,
                         t_day: str) -> dict | None:
    """Cost vs the close for MOC / T-day VWAP / window-linear,
    favorable-signed (negative beats the close). Daily official data
    (exact VWAPs)."""
    days = _stock_day(code)
    win = [r for r in days if ann < r[0] <= t_day]
    t = next((r for r in win if r[0] == t_day), None)
    if not t or len(win) < 3:
        return None
    sgn = 1.0 if side == "Buy" else -1.0
    ct = t[6]
    vwap_t = t[2] / t[1] if t[1] else None
    lin = np.mean([r[2] / r[1] for r in win if r[1]])
    out = {"MOC": 0.0,
           "VWAP_T": round(sgn * (vwap_t / ct - 1) * 1e4, 1)
           if vwap_t else None,
           "LINEAR_W": round(sgn * (lin / ct - 1) * 1e4, 1)}
    out["winner"] = min((k for k, v in out.items()
                         if v is not None), key=lambda k: out[k])
    return out


def self_grade(strip: dict, side: str, provider: str,
               baseline_vol: float | None) -> dict:
    """Realized vs OUR quoted priors — the estimate ledger."""
    from agents.tday_cards import auction_share_prior, gap_prior
    g = gap_prior()
    ap = auction_share_prior(provider=provider, side=side)
    grades = {}
    if g and strip.get("gap_bps") is not None:
        lo, hi = 0, g["mean"] + g["std"]
        grades["gap_in_band"] = bool(abs(strip["gap_bps"]) <= hi)
        grades["gap_band_quoted"] = f"|gap| <= {hi:.0f} bps"
    if ap and strip.get("auction_share") is not None:
        grades["share_prior_med"] = ap["med"] / 100
        grades["share_realized"] = strip["auction_share"]
        grades["share_surprise"] = round(
            strip["auction_share"] - ap["med"] / 100, 3)
    if baseline_vol and strip.get("t_volume"):
        grades["t_mult_realized"] = round(
            strip["t_volume"] / baseline_vol, 1)
    return grades


def reversal_path(code: str, side: str, t_day: str,
                  n_days: int = 5) -> list | None:
    """T+1..T+n favorable-signed closes vs the official close
    (positive = price came BACK = completion-leg friendly).
    Post-T closes from IB bars (windows extend to eff+7); official
    daily as fallback."""
    from scripts.tday_execution_studies import _ib_day, _load_ib
    days = _stock_day(code)
    ct = next((r[6] for r in days if r[0] == t_day), None)
    if ct is None:
        return None
    sgn = 1.0 if side == "Buy" else -1.0
    ib = _load_ib()
    post = sorted({r[0][:10] for r in ib.get(code, {}).get("5m", [])
                   if r[0][:10] > t_day})[:n_days]
    out = []
    for d in post:
        r = _ib_day(ib, code, d)
        if r:
            close = r[2] if not r[1] else (
                # day close = auction-inclusive: last price is the
                # official close bar close when the print bar exists
                [b for b in ib[code]["5m"]
                 if b[0].startswith(d)][-1][2])
            out.append(round(-sgn * (close / ct - 1) * 1e4, 1))
    if not out:                        # official-daily fallback
        idx = next((i for i, r in enumerate(days)
                    if r[0] == t_day), None)
        if idx is not None:
            out = [round(-sgn * (days[idx + j][6] / ct - 1) * 1e4, 1)
                   for j in range(1, n_days + 1)
                   if idx + j < len(days)]
    return out or None


def crowding_resolution(code: str, t_day: str) -> str:
    """Short-balance path T-5 -> T+3 where cached — did the crowd
    exit through the print?"""
    cache = json.loads((ROOT / "data" / "event_data_cache.json")
                       .read_text())["short"]
    key = t_day.replace("-", "")
    dates = sorted(cache)
    around = [d for d in dates if abs(int(d) - int(key)) <= 700]
    series = [(d, cache[d].get(code.split(".")[0])
               or cache[d].get(code))
              for d in around]
    series = [(d, v[0] + v[1]) for d, v in series if v]
    if len(series) < 4:
        return "no cached short path for this window"
    pre = [v for d, v in series if d < key]
    post = [v for d, v in series if d >= key]
    if not pre or not post:
        return "one-sided short path only"
    chg = (post[-1] - pre[-1]) / pre[-1] * 100 if pre[-1] else 0
    return (f"shorts {pre[-1]:,.0f} at T-1 -> {post[-1]:,.0f} "
            f"({chg:+.0f}% through/after the print)")


def build_pack(event: str, provider: str, ann: str, t_day: str,
               names: dict[str, str]) -> dict:
    from scripts.tday_execution_studies import _ib_day, _load_ib
    ib = _load_ib()
    rows = []
    for code, side in names.items():
        strip = benchmark_strip(code, t_day)
        if strip is None:
            rows.append({"code": code, "side": side,
                         "note": "no official day data (TPEx or "
                                 "missing) — excluded, stated"})
            continue
        # baseline vol for t_mult: pre-ann median from official days
        days = _stock_day(code)
        pre = [r[1] for r in days if r[0] <= ann][-10:]
        base = float(np.median(pre)) if pre else None
        rows.append({
            "code": code, "side": side, **strip,
            "strategies": strategy_leaderboard(code, side, ann,
                                               t_day),
            "grades": self_grade(strip, side, provider, base),
            "reversal_T1_T5": reversal_path(code, side, t_day),
            "crowding": crowding_resolution(code, t_day)})
    return {"event": event, "provider": provider, "ann": ann,
            "t_day": t_day, "names": rows}


def render_pack(pack: dict) -> str:
    L = [f"# Post-Event Pack — {pack['event']} (T = {pack['t_day']})",
         "*Step-4 without own executions: the benchmark strip any "
         "client can self-grade against, the strategy leaderboard "
         "for THIS event, our estimate ledger (realized vs the "
         "priors we quoted), the reversal path for completion "
         "legs, and the crowding resolution. Every number from "
         "official/verified tape.*\n"]
    for r in pack["names"]:
        if "note" in r:
            L.append(f"## {r['side']} {r['code']} — {r['note']}\n")
            continue
        L.append(f"## {r['side']} {r['code']}\n")
        L.append(f"- **Benchmark strip**: close {r['official_close']}"
                 f" | day VWAP {r['day_vwap_exact']} | cont VWAP "
                 f"{r['cont_vwap_5m']} | TWAP~ {r['twap_est']} | "
                 f"last cont {r['last_cont']} | gap "
                 f"{r['gap_bps']:+.0f} bps | auction share "
                 f"{r['auction_share']}")
        s = r.get("strategies")
        if s:
            L.append(f"- **Strategy leaderboard** (fav bps vs "
                     f"close): MOC 0 | VWAP_T {s['VWAP_T']} | "
                     f"LINEAR {s['LINEAR_W']} -> winner "
                     f"**{s['winner']}**")
        g = r.get("grades", {})
        if g:
            gi = g.get("gap_in_band")
            L.append(f"- **Estimate ledger**: gap in quoted band: "
                     f"{'YES' if gi else 'NO'} "
                     f"({g.get('gap_band_quoted', '')}); share "
                     f"realized {g.get('share_realized')} vs prior "
                     f"med {g.get('share_prior_med')} (surprise "
                     f"{g.get('share_surprise')}); realized "
                     f"T-mult {g.get('t_mult_realized')}x")
        if r.get("reversal_T1_T5"):
            L.append(f"- **Reversal path T+1..T+5** (positive = "
                     f"came back): {r['reversal_T1_T5']}")
        L.append(f"- **Crowding resolution**: {r['crowding']}\n")
    return "\n".join(L)
