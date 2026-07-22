"""Trader-facing packaging of Page 2's analytics (design: docs/TRADER_WORKFLOW_DESIGN.md).

Everything here is a pure function over objects the page already computes
(EventStudyResult, ExecutionInsights, RebalanceStrategyAnalysis) — no
Streamlit imports, no network except run_basket's injectable study runner.
Analytics live in rebalancing_event_study / agent14; this module only
re-shapes them for a trader mid-event: verdict first, shares and bps, RAG
flags, triggers, exports.
"""

from __future__ import annotations

import datetime as _dt
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

import numpy as np
import pandas as pd

# Auction-capacity traffic light (fraction of estimated closing-auction volume).
# RED threshold == agent14.AUCTION_STRESS_WARN so the two never disagree.
AUCTION_GREEN_MAX = 0.15
AUCTION_RED_MIN = 0.25

DEFAULT_LIBRARY_PATH = Path(__file__).resolve().parent.parent / "data" / "event_library.json"
LIBRARY_MIN_N = 3          # medians used for playbook thresholds from this n


# ──────────────────────────────────────────────────────────────────────────
# F1 — verdict / auction RAG
# ──────────────────────────────────────────────────────────────────────────

def auction_rag(order_shares: float, t_day_volume: float,
                auction_normal_share: float = 0.10) -> tuple[str, float]:
    """('GREEN'|'AMBER'|'RED', order as fraction of estimated auction volume).

    Estimated auction volume = auction_normal_share x the day's volume — the
    same convention Agent 14 uses, so the banner and the stress note agree.
    """
    est_auction = max(auction_normal_share * max(t_day_volume, 0.0), 1.0)
    frac = order_shares / est_auction
    if frac > AUCTION_RED_MIN:
        return "RED", frac
    if frac > AUCTION_GREEN_MAX:
        return "AMBER", frac
    return "GREEN", frac


def plain_reversal_read(reversal) -> str:
    """One line of desk English for the reversal classification."""
    if not getattr(reversal, "available", False):
        return "Reversal read unavailable for this event."
    frac = reversal.reversal_fraction_5d
    cls = reversal.classification or ""
    if "Transient" in cls:
        return (f"Crowd pressure, not news: ~{frac:.0%} of the pre-event move "
                f"came back within 5 days. Patience after T is paid.")
    if "Partial" in cls:
        return (f"Partly crowd pressure: ~{frac:.0%} reversed within 5 days. "
                f"Some edge in waiting, less than a full-reversal event.")
    if "Momentum" in cls:
        return "The move kept going after T — waiting hurt on this event."
    if "Permanent" in cls:
        return "Little reversal — the re-rating stuck; waiting doesn't help."
    return "Pre-event move too small to classify."


def recommended_bucket_split(strategy) -> dict[str, float]:
    """Shares by bucket {'pre': ..., 'auction': ..., 'post': ...} from a
    StrategyOutcome's schedule DataFrame."""
    out = {"pre": 0.0, "auction": 0.0, "post": 0.0}
    sched = strategy.schedule
    if sched is None or len(sched) == 0:
        return out
    for _, row in sched.iterrows():
        if str(row.get("Venue", "")) == "Closing auction":
            out["auction"] += float(row["Shares"])
        elif int(row["Rel day"]) < 0:
            out["pre"] += float(row["Shares"])
        else:
            out["post"] += float(row["Shares"])
    return out


@dataclass
class Verdict:
    side: str
    order_shares: float
    order_pct_adv: float
    strategy_name: str
    cost_vs_decision_bps: float
    tracking_diff_bps: float
    auction_flag: str            # GREEN / AMBER / RED
    auction_frac: float          # order / est. auction volume
    objective: str
    headline: str                # the one line a trader reads


def build_verdict(es, ana, objective: str,
                  auction_normal_share: float = 0.10) -> Verdict:
    """The one-line, top-of-page verdict. `ana` is a RebalanceStrategyAnalysis
    (any parameterization — the page uses a default pass right after the study)."""
    if objective == "Index Tracker":
        best = min(ana.strategies, key=lambda s: (s.abs_tracking_bps, s.cost_vs_decision_bps))
    else:
        best = min(ana.strategies, key=lambda s: (s.cost_vs_decision_bps, s.abs_tracking_bps))
    i_T = int(np.where(np.asarray(es.rel_days) == 0)[0][0])
    t_vol = float(np.clip(np.asarray(es.ab_vol, dtype=float), 0, None)[i_T] * es.est_avg_volume)
    flag, frac = auction_rag(ana.order_shares * best.auction_pct / 100.0, t_vol,
                             auction_normal_share)
    icon = {"GREEN": "🟢", "AMBER": "🟡", "RED": "🔴"}[flag]
    headline = (f"{ana.side.upper()} {ana.order_shares:,.0f} sh "
                f"({ana.order_pct_adv:.1f}% ADV) — {best.name} · "
                f"cost {best.cost_vs_decision_bps:+.0f} bps vs decision · "
                f"tracking {best.tracking_diff_bps:+.0f} bps vs print · "
                f"auction {frac:.0%} of est. close volume {icon}")
    return Verdict(side=ana.side, order_shares=ana.order_shares,
                   order_pct_adv=ana.order_pct_adv, strategy_name=best.name,
                   cost_vs_decision_bps=best.cost_vs_decision_bps,
                   tracking_diff_bps=best.tracking_diff_bps,
                   auction_flag=flag, auction_frac=frac,
                   objective=objective, headline=headline)


# ──────────────────────────────────────────────────────────────────────────
# F2 — trade card + schedule CSV
# ──────────────────────────────────────────────────────────────────────────

def trade_card_text(es, insights, ana, verdict: Verdict) -> str:
    """Plain-text one-pager a trader can print or paste into chat."""
    best = next(s for s in ana.strategies if s.name == verdict.strategy_name)
    split = recommended_bucket_split(best)
    risk_lines = list(best.notes) or ["No auction-stress flag at this size."]
    rev_line = plain_reversal_read(insights.reversal) if insights else "n/a"
    conc = ""
    if insights and insights.concentration.available:
        c = insights.concentration
        conc = (f"T-day close concentration: {c.concentration_multiple_window:.1f}x normal "
                f"({c.t_last_window_pct:.1f}% vs {c.baseline_last_window_pct:.1f}%).")
    L = [
        "=" * 68,
        f"REBALANCE TRADE CARD — {es.ticker}   ({es.index_name})",
        f"Effective date T: {pd.Timestamp(es.T).date()}   Generated: {_dt.date.today()}",
        "=" * 68,
        f"SIDE / ORDER : {verdict.side.upper()} {verdict.order_shares:,.0f} sh "
        f"= {verdict.order_pct_adv:.1f}% ADV (ADV {es.est_avg_volume:,.0f} sh)",
        f"OBJECTIVE    : {verdict.objective}",
        f"STRATEGY     : {verdict.strategy_name}",
        f"BUCKETS      : pre {split['pre']:,.0f} | auction {split['auction']:,.0f} "
        f"| post {split['post']:,.0f}",
        f"AUCTION FLAG : {verdict.auction_flag} — order = {verdict.auction_frac:.0%} "
        f"of est. closing-auction volume",
        f"EXPECTED     : cost {verdict.cost_vs_decision_bps:+.0f} bps vs decision "
        f"({ana.decision_price:,.2f}); tracking {verdict.tracking_diff_bps:+.0f} bps "
        f"vs print ({ana.effective_close:,.2f})",
        "-" * 68,
        f"READ         : {rev_line}",
    ]
    if conc:
        L.append(f"               {conc}")
    for r in risk_lines:
        L.append(f"RISK         : {r}")
    L.append("-" * 68)
    L.append("Single-name model on free daily data; basket crowding on the day can")
    L.append("push realized costs above every number here. Evidence: app Page 2.")
    L.append("=" * 68)
    return "\n".join(L)


def schedules_csv(ana) -> str:
    """Every strategy's day-by-day schedule, one CSV for EMS staging."""
    frames = []
    for s in ana.strategies:
        if s.schedule is None or len(s.schedule) == 0:
            continue
        df = s.schedule.copy()
        df.insert(0, "Strategy", s.name)
        frames.append(df)
    if not frames:
        return "Strategy\n"
    return pd.concat(frames, ignore_index=True).to_csv(index=False)


# ──────────────────────────────────────────────────────────────────────────
# F3 — conditional playbook
# ──────────────────────────────────────────────────────────────────────────

def build_playbook(es, insights, ana, verdict: Verdict,
                   library_stats_row: Optional[dict] = None,
                   crowding_tier: Optional[str] = None) -> list[str]:
    """Trigger-based checklist. Thresholds are PROPOSALS anchored on this
    event (and the event library's medians when n >= LIBRARY_MIN_N) — the
    trader confirms or overrides them."""
    lib = library_stats_row or {}
    n = int(lib.get("n", 0))
    med_runup = lib.get("median_abs_runup_pct")
    med_rev = lib.get("median_reversal_fraction")
    src = f"library median, n={n}" if n >= LIBRARY_MIN_N else "this event"

    runup_now = None
    if insights and insights.reversal.available:
        runup_now = abs(insights.reversal.pre_event_runup_pct or 0.0)
    runup_ref = (abs(med_runup) if (n >= LIBRARY_MIN_N and med_runup is not None)
                 else (runup_now or 3.0))
    runup_trigger = round(1.5 * runup_ref, 1)

    rev_ref = (med_rev if (n >= LIBRARY_MIN_N and med_rev is not None)
               else (insights.reversal.reversal_fraction_5d
                     if insights and insights.reversal.available
                     and insights.reversal.reversal_fraction_5d is not None else 0.5))

    steps = [
        f"[T-5 → T-2] Confirm order size: flow-to-trade if weight/AUM known "
        f"(current: {verdict.order_shares:,.0f} sh = {verdict.order_pct_adv:.1f}% ADV). "
        f"Recheck auction flag — currently {verdict.auction_flag} "
        f"({verdict.auction_frac:.0%} of est. close volume).",
        f"[T-2] IF auction flag is RED (> {AUCTION_RED_MIN:.0%} of est. close volume) "
        f"THEN pre-position the excess over {AUCTION_GREEN_MAX:.0%} across T-2/T-1 "
        f"continuous — do not carry a RED flag into the close.",
        f"[T-1, after close] IF abnormal move A→T-1 exceeds {runup_trigger:.1f}% "
        f"({src}: 1.5x the typical run-up) THEN the crowd is early — shift ~20% of "
        f"any remaining pre-position bucket to post-effective.",
        f"[T-day] Execute the auction bucket MOC. No limit on the tracker bucket if "
        f"the mandate is Index Tracker (the print IS the benchmark); cost-minimizers "
        f"cap the auction slice at {AUCTION_RED_MIN:.0%} of estimated auction volume.",
        f"[T+1 → T+{ana.params.get('post_days', 10)}] IF the reversal is tracking the "
        f"{rev_ref:.0%} reference ({src}) THEN work the post bucket passively into "
        f"strength; IF price makes new adverse extremes vs T (no reversal) THEN "
        f"complete within 2 days — do not fight a momentum event.",
        "[T+5] Record the outcome: rerun the study so this event enters the library "
        "and tightens the next playbook's thresholds.",
    ]
    if crowding_tier == "HIGH":
        steps.append("[Any time] Crowding score is HIGH — expect the announcement pop "
                     "to be largely spent and the post-effective reversal to run larger: "
                     "bias remaining discretion toward the post bucket; do not add to "
                     "the pre-position.")
    return steps


def playbook_text(es, steps: list[str]) -> str:
    head = [f"CONDITIONAL PLAYBOOK — {es.ticker} — T = {pd.Timestamp(es.T).date()}",
            "Thresholds are proposals; confirm or override before the event.", "-" * 68]
    return "\n".join(head + [f"{i+1}. {s}" for i, s in enumerate(steps)])


# ──────────────────────────────────────────────────────────────────────────
# F5 — event library
# ──────────────────────────────────────────────────────────────────────────

def record_event(es, insights, path: Path = DEFAULT_LIBRARY_PATH,
                 action: str = "", t_day_volume_multiple: float = None) -> dict:
    """Append (or update, keyed by ticker+T) one row per completed study."""
    rev = insights.reversal if insights else None
    dr = insights.drift if insights else None
    eta = insights.eta_calib if insights else None
    row = {
        "ticker": es.ticker, "index_name": es.index_name,
        "action": action,
        "T": str(pd.Timestamp(es.T).date()),
        "recorded_at": _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds"),
        "pre_event_runup_pct": getattr(rev, "pre_event_runup_pct", None),
        "reversal_fraction_5d": getattr(rev, "reversal_fraction_5d", None),
        "classification": getattr(rev, "classification", ""),
        "pct_move_after_announcement": getattr(dr, "pct_of_pre_event_move_after_announcement", None),
        "implied_eta": getattr(eta, "implied_eta", None),
        "t_day_volume_multiple": (round(float(t_day_volume_multiple), 2)
                                  if t_day_volume_multiple is not None else None),
        "sigma_daily": es.est_sigma_daily, "adv_shares": es.est_avg_volume,
    }
    rows = load_library(path)
    rows = [r for r in rows if not (r.get("ticker") == row["ticker"] and r.get("T") == row["T"])]
    rows.append(row)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(rows, indent=1), encoding="utf-8")
    return row


def load_library(path: Path = DEFAULT_LIBRARY_PATH) -> list[dict]:
    if not Path(path).exists():
        return []
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception:
        return []


def library_stats(path: Path = DEFAULT_LIBRARY_PATH, action: str = None) -> dict:
    """Medians across recorded events (None-safe). {'n': 0} when empty.
    action='Add'|'Delete' filters to one side (adds and deletes behave
    asymmetrically — Chen-Noronha-Singal 2004)."""
    rows = load_library(path)
    if action:
        rows = [r for r in rows if r.get("action") == action]
    out = {"n": len(rows)}
    if not rows:
        return out
    def med(key, absolute=False):
        vals = [r.get(key) for r in rows if isinstance(r.get(key), (int, float))]
        if absolute:
            vals = [abs(v) for v in vals]
        return round(float(np.median(vals)), 3) if vals else None
    out["median_abs_runup_pct"] = med("pre_event_runup_pct", absolute=True)
    out["median_reversal_fraction"] = med("reversal_fraction_5d")
    out["median_pct_after_announcement"] = med("pct_move_after_announcement")
    out["median_implied_eta"] = med("implied_eta")
    out["median_t_day_volume_multiple"] = med("t_day_volume_multiple")
    return out


def library_context_line(insights, stats: dict) -> str:
    """'This event vs library' caption for the insights section."""
    n = stats.get("n", 0)
    if n < LIBRARY_MIN_N:
        return (f"Event library: {n} event(s) recorded — medians appear once "
                f"{LIBRARY_MIN_N}+ events are stored (each completed study adds one).")
    bits = [f"Event library (n={n}):"]
    if insights and insights.reversal.available and stats.get("median_reversal_fraction") is not None:
        bits.append(f"reversal fraction {insights.reversal.reversal_fraction_5d:.2f} "
                    f"vs median {stats['median_reversal_fraction']:.2f};")
    if stats.get("median_abs_runup_pct") is not None:
        bits.append(f"median |run-up| {stats['median_abs_runup_pct']:.1f}%;")
    if stats.get("median_implied_eta") is not None:
        bits.append(f"median implied eta {stats['median_implied_eta']:.2f}.")
    return " ".join(bits)


# ──────────────────────────────────────────────────────────────────────────
# F4 — basket mode
# ──────────────────────────────────────────────────────────────────────────

_SEVERITY = {"RED": 0, "AMBER": 1, "GREEN": 2}


def run_basket(basket: pd.DataFrame, rebal_date, event_window: int,
               index_name: str, study_fn: Callable = None,
               auction_normal_share: float = 0.10,
               log: Callable = None) -> pd.DataFrame:
    """Run the event study across a program CSV and rank exceptions.

    basket columns: ticker, market, side [, shares]. Missing shares → 5% ADV.
    study_fn is injectable for offline tests; defaults to run_event_study.
    Failures degrade per name (error goes in the row; the rest still run).
    """
    if study_fn is None:
        from agents.rebalancing_event_study import run_event_study as study_fn
    from agents.rebalancing_event_study import compute_reversal

    rows = []
    for _, r in basket.iterrows():
        tkr = str(r["ticker"]).strip()
        mkt = str(r["market"]).strip()
        side = str(r.get("side", "Buy")).strip().capitalize() or "Buy"
        try:
            es = study_fn(ticker_base=tkr, market=mkt, rebal_date=rebal_date,
                          event_window=event_window, index_name=index_name)
            shares = float(r["shares"]) if "shares" in basket.columns and pd.notna(r.get("shares")) \
                     else 0.05 * es.est_avg_volume
            rel = np.asarray(es.rel_days)
            i_T = int(np.where(rel == 0)[0][0])
            t_vol = float(np.clip(np.asarray(es.ab_vol, float), 0, None)[i_T] * es.est_avg_volume)
            flag, frac = auction_rag(shares, t_vol, auction_normal_share)
            rev = compute_reversal(es.car, rel)
            car_T = float(es.car[i_T]) * 100
            rows.append({
                "Ticker": es.ticker, "Side": side, "Shares": round(shares, 0),
                "% ADV": round(shares / es.est_avg_volume * 100, 1) if es.est_avg_volume else None,
                "Auction flag": flag, "% est. auction vol": round(frac * 100, 0),
                "Abn. move into T (%)": round(car_T, 1),
                "Reversal class": (rev.classification.split(" --")[0]
                                   if rev.available else "n/a"),
                "Error": "",
            })
        except Exception as e:
            rows.append({"Ticker": tkr, "Side": side, "Shares": None, "% ADV": None,
                         "Auction flag": "n/a", "% est. auction vol": None,
                         "Abn. move into T (%)": None, "Reversal class": "n/a",
                         "Error": f"{type(e).__name__}: {e}"})
        if log:
            log(f"{tkr}: done")
    df = pd.DataFrame(rows)
    df["_sev"] = df["Auction flag"].map(_SEVERITY).fillna(-1)   # errors first
    df = df.sort_values(["_sev", "% est. auction vol"],
                        ascending=[True, False]).drop(columns="_sev")
    return df.reset_index(drop=True)


# ──────────────────────────────────────────────────────────────────────────
# P1 analytics (docs/REBALANCE_RESEARCH_AUTOMATION.md streams D and E)
# ──────────────────────────────────────────────────────────────────────────

CROWDING_LOW_MAX = 33.0
CROWDING_HIGH_MIN = 66.0
_CROWD_COLORS = {"LOW": "#22c55e", "MODERATE": "#f97316", "HIGH": "#ef4444"}
MULTIPLIER_LOW, MULTIPLIER_HIGH = 3.0, 8.0   # Gabaix-Koijen flow multiplier range


@dataclass
class CrowdingScore:
    available: bool
    reason: str = ""
    score: float = None          # 0 (empty trade) … 100 (very crowded)
    tier: str = ""               # LOW / MODERATE / HIGH
    color: str = "#6b7280"
    detail: str = ""             # which proxies fed the score, with values
    insight: str = ""            # what the tier means for strategy choice


def crowding_score(es, insights, announcement_date=None,
                   short_interest_change_pct=None) -> CrowdingScore:
    """Anticipatory-arbitrage crowding proxies (0–100). Components, each
    optional and each disclosed in `detail`:
      1. share of the pre-event move that happened BEFORE the announcement
         (predictable changes get front-run before A — Greenwood-Sammon);
      2. pre-announcement abnormal volume ((mean-1)x100, capped);
      3. |short-interest change| into the event x2 (user-supplied; exchange
         short-interest reporting lags ~2 weeks).
    A proxy score, NOT a positioning feed — n components always shown."""
    comps, details = [], []

    dr = getattr(insights, "drift", None) if insights is not None else None
    if dr is not None and getattr(dr, "available", False)             and dr.pct_of_pre_event_move_after_announcement is not None:
        pre_share = float(np.clip(100.0 - dr.pct_of_pre_event_move_after_announcement,
                                  0.0, 100.0))
        comps.append(pre_share)
        details.append(f"{pre_share:.0f}% of the pre-event move came BEFORE the announcement")

    if announcement_date is not None:
        try:
            ev_dates = pd.DatetimeIndex(es.event_dates)
            pre_mask = ev_dates < pd.Timestamp(announcement_date)
            if int(pre_mask.sum()) >= 2:
                pre_vol = float(np.mean(np.asarray(es.ab_vol, dtype=float)[pre_mask]))
                comps.append(float(np.clip((pre_vol - 1.0) * 100.0, 0.0, 100.0)))
                details.append(f"pre-announcement volume ran {pre_vol:.2f}x normal")
        except Exception:
            pass

    if short_interest_change_pct is not None:
        comps.append(float(np.clip(abs(short_interest_change_pct) * 2.0, 0.0, 100.0)))
        details.append(f"short interest {short_interest_change_pct:+.0f}% into the event "
                       f"(reported, ~2-week lag)")

    if not comps:
        return CrowdingScore(available=False,
                             reason="Needs an announcement date (drift + volume proxies) "
                                    "and/or a short-interest change input.")

    score = float(np.mean(comps))
    tier = ("LOW" if score < CROWDING_LOW_MAX
            else "HIGH" if score > CROWDING_HIGH_MIN else "MODERATE")
    insight = {
        "HIGH": ("Anticipatory positioning looks heavy: expect the announcement pop to be "
                 "largely spent, weaker drift into T, and a LARGER post-effective reversal "
                 "— favors post-effective completion (S3) and patience (the Dec-2024 "
                 "Apollo add is the cautionary example)."),
        "MODERATE": ("Some anticipatory positioning: split the difference — partial "
                     "pre-position, and keep a post-effective bucket for the reversal."),
        "LOW": ("Little sign of anticipatory positioning: the classic pre-position "
                "playbook (S2/S4) still has room, and the close will carry the flow."),
    }[tier]
    return CrowdingScore(available=True, score=round(score, 0), tier=tier,
                         color=_CROWD_COLORS[tier],
                         detail=("Components (" + str(len(comps)) + "): "
                                 + "; ".join(details) + ". Proxy-based score, "
                                 "not a positioning feed."),
                         insight=insight)


@dataclass
class ExpectedMove:
    available: bool
    reason: str = ""
    sqrt_low_bps: float = None
    sqrt_high_bps: float = None      # None until the library has a median eta
    mult_low_bps: float = None       # None without float market cap
    mult_high_bps: float = None
    detail: str = ""


def expected_move(flow, es, float_mcap_usd: float = None,
                  lib: Optional[dict] = None) -> ExpectedMove:
    """Pre-event expected-move band from the flow estimate.
    Two independent calibrations, both shown when computable:
      * sqrt-law: eta x sigma x sqrt(flow/ADV), eta from the baseline (0.3)
        up to the event library's median implied eta (n >= LIBRARY_MIN_N);
      * flow multiplier: M x (flow notional / float market cap), M in the
        Gabaix-Koijen 3–8 range (needs float market cap, user-supplied).
    Reading: realized move above the bands = crowding on top of the flow;
    well below = absorbed / capacity remains."""
    from agents.agent3_algo_simulation import IMPACT_ETA
    if flow is None:
        return ExpectedMove(available=False,
                            reason="Enter index weight change % and tracked AUM first — "
                                   "the flow estimate is the calculator's input.")
    adv, sigma = float(es.est_avg_volume), float(es.est_sigma_daily)
    if adv <= 0 or sigma <= 0 or not flow.shares or flow.shares <= 0:
        return ExpectedMove(available=False, reason="Missing ADV, volatility, or flow shares.")

    part = float(flow.shares) / adv
    lib = lib or {}
    eta_lo = float(IMPACT_ETA)
    eta_hi = (lib.get("median_implied_eta")
              if int(lib.get("n", 0)) >= LIBRARY_MIN_N else None)
    lo = eta_lo * sigma * float(np.sqrt(part)) * 1e4
    hi = eta_hi * sigma * float(np.sqrt(part)) * 1e4 if eta_hi else None

    bits = ["Sqrt-law band: " + (f"{lo:,.0f}–{hi:,.0f} bps" if hi else f"{lo:,.0f} bps")
            + f" (eta {eta_lo:.2f}" + (f" → library median {eta_hi:.2f}, n={lib.get('n')})"
                                       if eta_hi else "; library median appears at n≥3)")]
    m_lo = m_hi = None
    if float_mcap_usd and float_mcap_usd > 0:
        fshare = float(flow.notional_usd) / float(float_mcap_usd)
        m_lo = MULTIPLIER_LOW * fshare * 1e4
        m_hi = MULTIPLIER_HIGH * fshare * 1e4
        bits.append(f"Flow-multiplier band (M=3–8 on flow {fshare:.2%} of float cap): "
                    f"{m_lo:,.0f}–{m_hi:,.0f} bps")
    bits.append("Read: realized move above the bands = crowding on top of the flow; "
                "well below = absorbed / capacity remains.")
    return ExpectedMove(available=True,
                        sqrt_low_bps=round(lo, 0),
                        sqrt_high_bps=round(hi, 0) if hi else None,
                        mult_low_bps=round(m_lo, 0) if m_lo else None,
                        mult_high_bps=round(m_hi, 0) if m_hi else None,
                        detail=" · ".join(bits))


# ──────────────────────────────────────────────────────────────────────────
# Best-execution record store (INSTITUTIONAL_PLATFORM_PROPOSAL.md P2) —
# the decision documented AT decision time, as a by-product of the workflow.
# ──────────────────────────────────────────────────────────────────────────

DEFAULT_BESTEX_PATH = Path(__file__).resolve().parent.parent / "data" / "bestex_records.json"


def build_bestex_record(es, verdict: Verdict, ana, objective: str,
                        playbook_steps: list[str],
                        library_n: int = 0) -> dict:
    """Assemble the best-ex evidence record: what was recommended, on what
    numbers, under which thresholds — everything a best-ex committee asks for
    quarterly, captured when the decision was made rather than reconstructed."""
    return {
        "ticker": es.ticker, "index_name": es.index_name,
        "effective_date": str(pd.Timestamp(es.T).date()),
        "recorded_at": _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds"),
        "objective": objective,
        "decision": {
            "side": verdict.side, "order_shares": verdict.order_shares,
            "order_pct_adv": verdict.order_pct_adv,
            "strategy": verdict.strategy_name,
            "expected_cost_vs_decision_bps": verdict.cost_vs_decision_bps,
            "expected_tracking_bps": verdict.tracking_diff_bps,
            "auction_flag": verdict.auction_flag,
            "auction_frac_of_est_volume": round(verdict.auction_frac, 4),
        },
        "evidence": {
            "frontier": ana.frontier.to_dict(orient="records"),
            "params": ana.params,
            "decision_price": ana.decision_price,
            "effective_close": ana.effective_close,
            "event_library_n": int(library_n),
        },
        "playbook": list(playbook_steps),
        "model_notes": list(ana.caveats),
    }


def record_bestex(record: dict, path: Path = DEFAULT_BESTEX_PATH) -> dict:
    """Persist keyed on (ticker, effective_date, objective) — update, not
    duplicate, across Streamlit reruns."""
    key = ("ticker", "effective_date", "objective")
    rows = []
    if Path(path).exists():
        try:
            rows = json.loads(Path(path).read_text(encoding="utf-8"))
        except Exception:
            rows = []
    rows = [r for r in rows if tuple(r.get(k) for k in key) != tuple(record[k] for k in key)]
    rows.append(record)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(rows, indent=1), encoding="utf-8")
    return record


def bestex_record_json(record: dict) -> str:
    return json.dumps(record, indent=2)
