"""Pre-announcement orchestrator — the six analytics categories,
one agent, one pack.

Session 9i. Consolidates the pre-announcement workflow
(PRE_ANNOUNCEMENT_ANALYTICS_TW.md) into a single build:

  cat1  screening        engine screen + calls/shortlist (existing)
  cat2  crowding watch   NEW: dated short-balance deltas + alerts,
                         as-of aware (backtestable)
  cat3  positioning      class-conditional advisory lines from the
        advisory         decade cost tables
  cat4  capacity cards   T-day cards (existing) + NEW must-start-by
                         date per name
  cat5  marketing pack   one rendered artifact, grades attached
  cat6  priors snapshot  NEW: all microstructure priors, dated

Same honesty contract as everything else: every number carries its
basis; staleness is stated, never hidden; a graded mode exists so
the whole pack can be backtested against an official key.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


# ------------------------------------------------------- cat2: watch
def crowding_watch(short_cache: dict, codes: list[str],
                   asof: str | None = None,
                   lookback: int = 30) -> pd.DataFrame:
    """Dated crowding surveillance. For each code: balance now (or
    as-of), %-build over the window, 5-obs delta, band, EXITING tag,
    ALERT flag (|5-obs delta| >= 10% — positioning moving NOW).
    as-of aware so the May backtest sees only pre-announcement data."""
    from agents.event_data import short_balance_series
    rows = []
    for code in codes:
        s = short_balance_series(short_cache, code)
        if s.empty:
            rows.append({"code": code, "read": "no data",
                         "alert": False, "asof": asof or "latest"})
            continue
        if asof:                       # series is date-INDEXED
            s = s[s.index <= pd.Timestamp(asof)]
        if len(s) < 3:
            rows.append({"code": code, "read": "insufficient obs",
                         "alert": False, "asof": asof or "latest"})
            continue
        w = s.iloc[-min(len(s), lookback):]
        b, now = w["total_short"].iloc[0], w["total_short"].iloc[-1]
        pct = 100 * (now - b) / b if b else np.nan
        d5 = (100 * (now - w["total_short"].iloc[-min(len(w), 5)])
              / w["total_short"].iloc[-min(len(w), 5)]
              if w["total_short"].iloc[-min(len(w), 5)] else np.nan)
        peak = w["total_short"].max()
        off = 100 * (peak - now) / peak if peak else 0
        band = ("HIGH" if pct >= 25 else "MED" if pct >= 5
                else "LOW")
        tag = (f"; EXITING (-{off:.0f}% off peak)"
               if off >= 15 and peak > b * 1.1 else "")
        rows.append({
            "code": code, "band": band,
            "build_pct": round(pct, 0), "delta5_pct": round(d5, 0),
            "n_obs": len(w),
            "read": f"{band} ({pct:+.0f}%/{len(w)}obs){tag}",
            "alert": bool(abs(d5) >= 10),
            "asof": asof or w.index[-1].strftime("%Y%m%d")})
    return pd.DataFrame(rows)


# ---------------------------------------------------- cat4: schedule
def must_start_by(eff: str, adv_days_hi: float,
                  participation_cap: float = 0.25) -> str:
    """Last viable start date: eff minus ceil(adv_days_hi / cap)
    business days (Step-2 planner arithmetic)."""
    need = int(np.ceil(adv_days_hi / participation_cap))
    return (pd.Timestamp(eff) - pd.tseries.offsets.BDay(need - 1)
            ).strftime("%Y-%m-%d")


# ---------------------------------------------------- cat6: snapshot
def priors_snapshot(asof: str) -> dict:
    from agents.pitch_pack import expected_t_multiples
    from agents.tday_cards import (auction_share_prior, gap_prior,
                                   limit_prior)
    ev = json.loads(
        (ROOT / "data" / "event_flow_study.json").read_text())
    out = {"asof": asof,
           "print_mult_sell": expected_t_multiples(ev, "MSCI",
                                                   "Sell"),
           "print_mult_buy": expected_t_multiples(ev, "MSCI", "Buy"),
           "auction_share": auction_share_prior(),
           "gap_band": gap_prior(), "limits": limit_prior()}
    return out


# ------------------------------------------------------- cat3: lines
def advisory_lines(cc: dict | None) -> list[str]:
    L = ["TW adds are MOMENTUM events (6/7 recent adds +30..+107% "
         "into announcement) — the tape front-runs the arithmetic; "
         "advisory only for an agency desk."]
    # session 9i: window-intraday priors (24 events at 5m)
    wi = ROOT / "data" / "window_intraday.json"
    if wi.exists():
        L.append(
            "Window intraday priors (24 events, 5m): MSCI-delete "
            "window-day volumes run 1.4x baseline early -> 2.9x "
            "late (the obligation trades THROUGH the window; FTSE "
            "~1.0x until the print); delete-name closing auctions "
            "grow ~3.6 share points into T (H9b, 86% of events) — "
            "late-window MOC participation gets less lonely daily, "
            "but the print remains the event. PM-drift "
            "concentration toward T: NULL (H10) — no afternoon "
            "execution bias warranted.")
    if cc:
        s = cc.get("MSCI_Sell")
        if s:
            L.append(f"Deletes (TW MSCI class): spreading cost "
                     f"{s['vwap_w_med']:+.0f} bps vs close median "
                     f"(n={s['n']}) — MOC-family default; crowded "
                     "names flip to WORK-AHEAD per the matrix.")
        b = cc.get("FTSE_Buy")
        if b:
            L.append(f"Adds: no measured MSCI TW Buy prints; "
                     f"FTSE-class cross-reference: window-VWAP "
                     f"{b['vwap_w_med']:+.0f} bps (n={b['n']}); "
                     "MSCI-add WAIT rule remains a demoted "
                     "hypothesis (Aug-2026 arbitrates).")
    return L


# ---------------------------------------------------------- the pack
def build_pack(candidates: pd.DataFrame, universe: pd.DataFrame,
               event: dict, short_cache: dict | None = None,
               crowd_asof: str | None = None,
               live: bool = True) -> dict:
    """candidates: side/ticker/p/reasoning rows (firm calls carry
    their L8 p; shortlist rows their decade-anchored p).
    live=True (default): the freshness guarantee runs — the short
    cache is auto-refreshed to the most recent published day before
    any read, and the freshness report is attached to the pack.
    PIT/as-of runs pass live=False (a backtest must not fetch the
    present) — crowd_asof implies live=False automatically."""
    from agents.tday_cards import build_cards, class_costs
    freshness = None
    if live and not crowd_asof:
        from agents.data_freshness import CACHE, ensure_fresh_shorts
        freshness = ensure_fresh_shorts()
        if short_cache is not None:
            import json as _json
            short_cache = {"short": _json.loads(
                CACHE.read_text()).get("short", {})}
    codes = [t.split(".")[0] for t in candidates["ticker"]
             if not t.startswith("BELOW")]
    watch = (crowding_watch(short_cache, codes, asof=crowd_asof)
             if short_cache else pd.DataFrame())
    cmap = ({r["code"]: r["read"] for _, r in watch.iterrows()
             if r.get("read") not in ("no data", "insufficient obs")}
            if len(watch) else {})
    cards = build_cards(candidates, universe, crowding_map=cmap)
    for c in cards:
        if c.get("adv_days"):
            c["must_start_by"] = must_start_by(event["eff"],
                                               c["adv_days"][1])
    cc = class_costs()
    return {"event": event, "candidates": candidates,
            "crowding_watch": watch, "cards": cards,
            "advisory": advisory_lines(cc),
            "priors": priors_snapshot(crowd_asof or "latest"),
            "freshness": freshness}


def grade_pack(pack: dict, official_adds: set,
               official_dels: set) -> dict:
    from agents.review_funnel import validate_against_key
    cand = pack["candidates"]
    df = cand[~cand["ticker"].str.startswith("BELOW")].copy()
    df["call"] = df["side"]
    names = set(df["ticker"])
    g = validate_against_key(df, official_adds, official_dels,
                             names | official_adds | official_dels)
    # Brier-style score on candidate probabilities (graded record,
    # not vibes): outcome 1 if the name converted, else 0
    briers = []
    for _, r in df.iterrows():
        truth = (r["ticker"] in official_adds if r["side"] == "ADD"
                 else r["ticker"] in official_dels)
        briers.append((r["p"] - (1.0 if truth else 0.0)) ** 2)
    g["brier"] = round(float(np.mean(briers)), 3) if briers else None
    g["n_scored"] = len(briers)
    return g


def render_pack_md(pack: dict, title: str, grade: dict | None = None
                   ) -> str:
    ev = pack["event"]
    banner = []
    if pack.get("freshness"):
        from agents.data_freshness import freshness_line
        banner = ["> " + freshness_line(pack["freshness"]), ""]
    L = banner + [f"# Pre-Announcement Pack — {title}",
         f"*ann {ev['ann']} / effective {ev['eff']} "
         f"({ev['review']}). Six-category build, "
         "agents/pre_announcement.py; every number carries its "
         "basis; crowding as-of and prior staleness stated.*\n",
         "## 1. Screening — candidates\n",
         pack["candidates"].to_markdown(index=False), "",
         "## 2. Crowding watch (dated, alert = |5-obs delta| >= "
         "10%)\n"]
    w = pack["crowding_watch"]
    L.append(w.to_markdown(index=False) if len(w)
             else "no short cache supplied")
    L += ["", "## 3. Positioning advisory\n"]
    L += [f"- {a}" for a in pack["advisory"]]
    L += ["", "## 4. Capacity cards (must-start-by at 25% "
          "participation)\n"]
    for c in pack["cards"]:
        if "note" in c:
            L.append(f"- {c['side']} {c['ticker']} "
                     f"p={c['p_convert']}: {c['note']}")
        else:
            L.append(
                f"- **{c['side']} {c['ticker']}** p={c['p_convert']}"
                f" | flow ${c['flow_if_converts_usd_m'][0]}-"
                f"{c['flow_if_converts_usd_m'][1]}M | "
                f"{c['adv_days'][0]}-{c['adv_days'][1]} ADV-days "
                f"({c['bucket']}) | must start by "
                f"**{c.get('must_start_by', '—')}** | crowding "
                f"{c['crowding']}")
    p = pack["priors"]
    pm = p["print_mult_sell"]
    L += ["", "## 6. Microstructure priors snapshot "
          f"(as-of {p['asof']})\n",
          f"- Print multiple (Sell): median {pm.get('median')}x / "
          f"max {pm.get('max')}x (n={pm.get('n')}); Buy: "
          + ("NO MEASURED PRIOR" if not p["print_mult_buy"].get(
              "available") else str(p["print_mult_buy"]["median"])),
          f"- Event-day auction share: {p['auction_share']}",
          f"- Gap band: {p['gap_band']} (direction not predicted — "
          "null pinned)",
          f"- Limits: {p['limits']}"]
    if grade:
        L += ["", "## GRADE vs the official key\n",
              f"- dels hit {grade['dels_hit']} | missed visible "
              f"{grade['dels_missed_visible']} | false "
              f"{grade['false_dels']}",
              f"- adds hit {grade['adds_hit']} | missed "
              f"{grade['adds_missed_visible']} | false "
              f"{grade['false_adds']}",
              f"- Brier score {grade['brier']} over "
              f"{grade['n_scored']} scored candidates (lower is "
              "better; 0.25 = coin-flip at p=0.5)"]
    return "\n".join(L)
