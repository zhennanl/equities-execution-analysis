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


def _next_close_vintage(code, t_day):
    p = ROOT / "data" / "tw_vintage_cache.json"
    if not p.exists():
        return None
    c = json.loads(p.read_text()).get(f"px|{code}")
    if not c:
        return None
    post = [r for r in c if r["date"] > t_day]
    return post[0]["close"] if post else None


# c-40 (STEP34 §1.3): scenario-conditional playbook splits —
# Step-2's advice column made executable. Weights: (window-linear,
# MOC, T+1-close). SIMULATED per the three honesty rules.
PLAYBOOK_SPLITS = {
    "UNDERSUPPLIED":  (0.6, 0.4, 0.0),   # start early, spread
    "BUILDING":       (0.3, 0.7, 0.0),   # standard MOC lean
    "WELL-SUPPLIED":  (0.0, 1.0, 0.0),   # lean on the close
    "OVERCROWDED":    (0.0, 0.4, 0.6),   # cap MOC, defer to T+1
}


def strategy_leaderboard(code: str, side: str, ann: str,
                         t_day: str,
                         scenario: str | None = None) -> dict | None:
    """Cost vs the close for MOC / T-day VWAP / window-linear /
    PLAYBOOK (scenario-conditional split incl. a T+1 leg),
    favorable-signed (negative beats the close). Daily official
    data (exact VWAPs). All legs SIMULATED on the real tape —
    rankings/spreads are the graded object, not absolutes."""
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
    # T+1-close leg (the OVERCROWDED defer/fade leg); falls back to
    # the vintage cache when stock_day ends at T
    post = [r for r in days if r[0] > t_day]
    t1_px = post[0][6] if post else _next_close_vintage(code, t_day)
    t1_cost = (round(sgn * (t1_px / ct - 1) * 1e4, 1)
               if t1_px else None)
    out["T1_CLOSE"] = t1_cost
    if scenario in PLAYBOOK_SPLITS:
        w_lin, w_moc, w_t1 = PLAYBOOK_SPLITS[scenario]
        legs = [(w_lin, out["LINEAR_W"]), (w_moc, 0.0),
                (w_t1, t1_cost)]
        if all(v is not None for w, v in legs if w > 0):
            out["PLAYBOOK"] = round(
                sum(w * v for w, v in legs if w > 0), 1)
            out["playbook_split"] = (f"{scenario}: "
                                     f"{w_lin:.0%}window/"
                                     f"{w_moc:.0%}MOC/{w_t1:.0%}T+1")
    out["winner"] = min(
        (k for k in ("MOC", "VWAP_T", "LINEAR_W", "T1_CLOSE",
                     "PLAYBOOK")
         if out.get(k) is not None), key=lambda k: out[k])
    return out


# c-40 (STEP34 §1.4): the synthetic client panel — archetypes with
# real constraint structures; we grade what we WOULD HAVE TOLD each.
ARCHETYPES = {
    "EM_TRACKER":  {"allowed": ["MOC"],
                    "note": "MOC-obliged, zero discretion — the "
                            "benchmark IS the close"},
    "IMI_TRACKER": {"allowed": ["MOC", "VWAP_T"],
                    "note": "IMI membership math differs; may work "
                            "the T-day tape"},
    "ACTIVE_FLEX": {"allowed": ["MOC", "VWAP_T", "LINEAR_W",
                                "T1_CLOSE", "PLAYBOOK"],
                    "note": "benchmarked active; +/-1 day "
                            "discretion"},
    "HF_PROVIDER": {"allowed": ["LINEAR_W", "T1_CLOSE"],
                    "reverse": True,
                    "note": "liquidity provider: accumulates the "
                            "window AGAINST the flow, unwinds at "
                            "the print"},
}


def archetype_grading(strats: dict, scenario: str | None) -> dict:
    """Per archetype: what we'd have advised (best allowed strategy
    under the scenario), its realized cost, and the regret vs the
    best allowed in hindsight. HF_PROVIDER is sign-flipped (they
    take the other side)."""
    out = {}
    for name, spec in ARCHETYPES.items():
        vals = {k: strats.get(k) for k in spec["allowed"]
                if strats.get(k) is not None}
        if not vals:
            continue
        flip = -1.0 if spec.get("reverse") else 1.0
        vals = {k: round(flip * v, 1) for k, v in vals.items()}
        # advice: PLAYBOOK when allowed and scenario known,
        # else the archetype's structural default (first allowed)
        advised = ("PLAYBOOK" if "PLAYBOOK" in vals
                   and scenario else spec["allowed"][0])
        if advised not in vals:
            advised = spec["allowed"][0]
        best = min(vals, key=lambda k: vals[k])
        out[name] = {"advised": advised,
                     "advised_cost_bps": vals.get(advised),
                     "best_hindsight": best,
                     "best_cost_bps": vals[best],
                     "regret_bps": round(vals[advised] - vals[best],
                                         1)
                     if advised in vals else None,
                     "note": spec["note"]}
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


def _scenarios_for(event_tag: str) -> dict:
    """Step-2 scenarios per code, if a liquidity forecast exists
    for this event (c-40: closes the 2->3->4 loop)."""
    p = ROOT / "data" / f"liquidity_forecast_{event_tag}.json"
    if not p.exists():
        return {}
    d = json.loads(p.read_text())
    return {r["code"]: r["scenario"] for r in d.get("names", [])}


def build_pack(event: str, provider: str, ann: str, t_day: str,
               names: dict[str, str],
               event_tag: str = "may26") -> dict:
    from scripts.tday_execution_studies import _ib_day, _load_ib
    ib = _load_ib()
    scen = _scenarios_for(event_tag)
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
        sc = scen.get(code)
        strats = strategy_leaderboard(code, side, ann, t_day,
                                      scenario=sc)
        rows.append({
            "code": code, "side": side, **strip,
            "step2_scenario": sc,
            "strategies": strats,
            "archetypes": archetype_grading(strats, sc)
            if strats else None,
            "grades": self_grade(strip, side, provider, base),
            "reversal_T1_T5": reversal_path(code, side, t_day),
            "crowding": crowding_resolution(code, t_day)})
    return {"event": event, "provider": provider, "ann": ann,
            "t_day": t_day, "names": rows}


def render_tca_letters(pack: dict) -> str:
    """c-40 (STEP34 build item 6): per-archetype TCA letter DRAFTS
    from graded artifacts. SIMULATED basis stated in every letter;
    drafts require analyst sign-off before any client sees them."""
    L = [f"# TCA Letter Drafts — {pack['event']} (SIMULATED basis)",
         "*Auto-drafted from the graded post-event pack. Every "
         "figure is a synthetic execution on the real tape "
         "(participation-capped, measured-toll adders) — rankings "
         "and spreads are the reliable objects, not absolutes. "
         "DRAFT: requires analyst sign-off.*\n"]
    for aname, spec in ARCHETYPES.items():
        L.append(f"## To: {aname} clients\n")
        L.append(f"*Your constraint set: {spec['note']}.*\n")
        for r in pack["names"]:
            a = (r.get("archetypes") or {}).get(aname)
            if not a:
                continue
            line = (f"- **{r['side']} {r['code']}** "
                    f"(scenario {r.get('step2_scenario', 'n/a')}): "
                    f"advised **{a['advised']}** -> "
                    f"{a['advised_cost_bps']:+.1f} bps vs close; "
                    f"best-in-hindsight {a['best_hindsight']} "
                    f"({a['best_cost_bps']:+.1f}); regret "
                    f"{a['regret_bps']:+.1f} bps")
            L.append(line)
        L.append("")
    return "\n".join(L)


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
