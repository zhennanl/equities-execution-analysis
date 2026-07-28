"""PT Dealer cockpit — the minute-to-minute automation a program-trading
stock dealer needs across Asia (built against the CLSA PT Dealer JD).

JD bullet -> feature:
    "monitor intraday liquidity, volatility, market conditions"
        -> attention_queue: one ranked list of which basket names need the
           dealer's eyes NOW, with reasons — not twelve screens.
    "circuit breakers / market-specific regulations"
        -> limit_proximity: distance-to-price-limit per name with
           WATCH/ALERT levels (the Taiwan limit-lock queue-vs-retreat
           decision, surfaced BEFORE the lock).
    "coordinate cross-market execution across time zones"
        -> auction_countdown: every market's close-auction mechanism and
           minutes-to-cutoff in one table (complements wave_plan, which
           orders markets; this one says what you must SUBMIT and when).
    "accurate trade records for audit readiness"
        -> build_audit_pack / save_audit_pack: timestamped JSON of the
           basket, every compliance check run, and the dealer's state at
           the time — written as a by-product, not reconstructed later.

All rule tables are static approximations of public exchange rules,
deliberately conservative and clearly noted — a desk deployment replaces
them with the exchange's parameter feeds (lot files, band tiers, holiday
calendars). Session times are exchange-local without DST handling for
non-Asia markets (disclosed).
"""
from __future__ import annotations

import datetime as _dt
import json
from pathlib import Path

import numpy as np
import pandas as pd

from agents.program_trading import (MARKET_REG, market_status, lot_check,
                                    short_check)

DEFAULT_AUDIT_PATH = (Path(__file__).resolve().parent.parent / "data"
                      / "audit_packs.json")


def rules_version() -> str:
    """Content hash of every static rule table this module (and
    program_trading) applies — stamped into audit packs and alert logs so
    an auditor can see WHICH rule version produced every check. In
    production the exchange-parameter service would supply this."""
    import hashlib
    payload = json.dumps({"bands": LIMIT_BANDS, "cutoffs": AUCTION_CUTOFFS,
                          "reg": {k: {kk: str(vv) for kk, vv in v.items()}
                                  for k, v in MARKET_REG.items()}},
                         sort_keys=True, default=str)
    try:                       # pin the live registry state when present
        from agents.reg_watch import REGISTRY_PATH, load_registry, \
            registry_version
        if REGISTRY_PATH.exists():
            payload += registry_version(load_registry(REGISTRY_PATH))
    except Exception:
        pass
    return hashlib.sha256(payload.encode()).hexdigest()[:12]

# ── daily price-limit bands (static; per-stock tiers approximated) ─────────
# band = symmetric daily band vs previous close, as a fraction; None = no
# static daily band (dynamic per-stock mechanisms instead — noted).
LIMIT_BANDS: dict[str, dict] = {
    "Taiwan (TWSE)":    dict(band=0.10, note="±10% vs prev close; lock or retreat."),
    "China-A Shanghai": dict(band=0.10, note="±10% main board; ±5% ST; ±20% STAR."),
    "China-A Shenzhen": dict(band=0.10, note="±10% main board; ±20% ChiNext."),
    "Korea (KRX)":      dict(band=0.30, note="±30%; per-stock VI inside the band."),
    "Thailand (SET)":   dict(band=0.30, note="±30% ceiling/floor."),
    "Vietnam (HOSE)":   dict(band=0.07, note="±7% HOSE band."),
    "Malaysia (KLSE)":  dict(band=0.30, note="±30% static limit."),
    "Indonesia (IDX)":  dict(band=0.20, note="ARA/ARB asymmetric by price tier — 20% used as conservative proxy."),
    "Japan (TSE)":      dict(band=0.18, note="Price-tier bands (~15-22% typical mid-price tiers) — 18% proxy; renewal possible."),
    "India (NSE)":      dict(band=0.10, note="2-20% by band category — 10% proxy; F&O names have no static band."),
    "Hong Kong (HKEX)": dict(band=None, note="No static daily band; VCM ±10% vs 5-min-ago triggers cooling-off."),
    "Singapore (SGX)":  dict(band=None, note="No static band; per-stock CB ±10% vs 5-min reference."),
    "US":               dict(band=None, note="No static band; LULD dynamic bands + MWCB."),
    "Australia (ASX)":  dict(band=None, note="No static band; anomalous-order thresholds."),
    "UK (LSE)":         dict(band=None, note="No static band; order-book circuit breakers."),
}

WATCH_FRAC = 0.60      # >=60% of the band used -> WATCH
ALERT_FRAC = 0.80      # >=80% -> ALERT (decide queue-vs-retreat NOW)

# ── close-auction mechanics: (cutoff_local, auction_local, mechanism) ─────
# cutoff = last realistic moment to enter/amend close-auction orders.
AUCTION_CUTOFFS: dict[str, dict] = {
    "Taiwan (TWSE)":    dict(cutoff="13:25", auction="13:30",
                             note="Close call auction 13:25-13:30; orders rest from 13:25."),
    "Japan (TSE)":      dict(cutoff="15:25", auction="15:30",
                             note="Closing auction at 15:30 (post Nov-2024 close reform)."),
    "Hong Kong (HKEX)": dict(cutoff="16:08", auction="16:10",
                             note="CAS 16:00-16:10: reference-price then no-cancel phases; random close 16:08-16:10."),
    "Korea (KRX)":      dict(cutoff="15:20", auction="15:30",
                             note="15:20-15:30 closing call; no continuous trades in the window."),
    "China-A Shanghai": dict(cutoff="14:57", auction="15:00",
                             note="14:57-15:00 closing call; no cancels in the window."),
    "China-A Shenzhen": dict(cutoff="14:57", auction="15:00",
                             note="14:57-15:00 closing call; no cancels."),
    "Singapore (SGX)":  dict(cutoff="17:00", auction="17:06",
                             note="Pre-close 17:00-17:04/05 + non-cancel; random end to 17:06."),
    "India (NSE)":      dict(cutoff="15:30", auction="15:40",
                             note="Post-close session 15:40-16:00 at close price; main close 15:30."),
    "Australia (ASX)":  dict(cutoff="16:00", auction="16:10",
                             note="CSPA ~16:00-16:10, random end (DST approx.)."),
    "US":               dict(cutoff="15:50", auction="16:00",
                             note="NYSE MOC/LOC 15:50 (imbalance rules after); Nasdaq 15:55/15:58 tiers."),
    "Thailand (SET)":   dict(cutoff="16:30", auction="16:40",
                             note="Random close call after 16:30 continuous end (approx.)."),
    "Indonesia (IDX)":  dict(cutoff="15:50", auction="16:15",
                             note="Pre-closing then post-trading; times shift with sessions (approx.)."),
    "Malaysia (KLSE)":  dict(cutoff="16:45", auction="17:00",
                             note="Pre-close phase into 17:00 close (approx.)."),
    "Vietnam (HOSE)":   dict(cutoff="14:30", auction="14:45",
                             note="ATC call 14:30-14:45; no cancels in ATC."),
    "UK (LSE)":         dict(cutoff="16:30", auction="16:35",
                             note="Closing auction 16:30-16:35, random end (DST approx.)."),
}


# ── registry-aware rule lookup (Reg-Watch single source of truth) ─────────

def _rule(category: str, market: str, static_table: dict):
    """Prefer the Reg-Watch registry (versioned, human-approved) when it
    exists; fall back to this module's static tables otherwise. Lazy
    import breaks the reg_watch->pt_dealer seed-time cycle."""
    try:
        from agents.reg_watch import REGISTRY_PATH, current_value, \
            load_registry
        if REGISTRY_PATH.exists():
            v = current_value(load_registry(REGISTRY_PATH), category,
                              market)
            if v is not None:
                return v
    except Exception:
        pass                     # registry unavailable -> static tables
    return static_table.get(market)


# ── limit proximity ────────────────────────────────────────────────────────

def limit_proximity(market: str, prev_close: float, last_price: float) -> dict:
    """How much of today's daily band has this name used, and toward which
    side? Levels: none / WATCH (>=60%) / ALERT (>=80%) / LOCKED (>=99.5%)."""
    lb = _rule("limit_band", market, LIMIT_BANDS) \
        or dict(band=None, note="Unknown market.")
    if not lb["band"] or prev_close <= 0:
        return dict(level="n/a", used_frac=np.nan, side="", band_pct=None,
                    note=lb["note"])
    move = (last_price - prev_close) / prev_close
    used = abs(move) / lb["band"]
    side = "upper" if move > 0 else "lower"
    if used >= 0.995:
        level = "LOCKED"
    elif used >= ALERT_FRAC:
        level = "ALERT"
    elif used >= WATCH_FRAC:
        level = "WATCH"
    else:
        level = "none"
    return dict(level=level, used_frac=round(float(used), 3), side=side,
                band_pct=round(lb["band"] * 100, 1),
                note=lb["note"] + (f" {used:.0%} of the {side} band used."
                                   if level != "none" else ""))


# ── auction countdown ──────────────────────────────────────────────────────

def auction_countdown(markets, now_utc: _dt.datetime = None) -> pd.DataFrame:
    """Minutes to each market's close-auction CUTOFF (the moment that
    matters for MOC-style orders), plus the mechanism reminder."""
    now_utc = now_utc or _dt.datetime.now(_dt.timezone.utc).replace(tzinfo=None)
    rows = []
    for m in sorted(set(markets)):
        ac = _rule("auction_cutoff", m, AUCTION_CUTOFFS)
        reg = MARKET_REG.get(m, {})
        if not ac:
            continue
        off = float(reg.get("utc", 0))
        local = now_utc + _dt.timedelta(hours=off)
        cut_h, cut_m = map(int, ac["cutoff"].split(":"))
        cutoff_local = local.replace(hour=cut_h, minute=cut_m, second=0,
                                     microsecond=0)
        mins = (cutoff_local - local).total_seconds() / 60.0
        status = ("PASSED" if mins < 0 else
                  "🔴 <15m" if mins < 15 else
                  "🟡 <60m" if mins < 60 else "ok")
        rows.append({"Market": m, "Cutoff (local)": ac["cutoff"],
                     "Auction (local)": ac["auction"],
                     "Mins to cutoff": round(mins, 1), "Status": status,
                     "Mechanism": ac["note"]})
    return (pd.DataFrame(rows).sort_values("Mins to cutoff")
            .reset_index(drop=True))


# ── attention queue ────────────────────────────────────────────────────────

W_LIMIT, W_AUCTION, W_BEHIND, W_LIQ = 40.0, 25.0, 20.0, 15.0


def attention_queue(basket: pd.DataFrame,
                    now_utc: _dt.datetime = None) -> pd.DataFrame:
    """Rank basket names by 'needs the dealer's eyes now'.

    Expects columns: ticker, market, side, prev_close, last_price,
    filled_frac (0-1), elapsed_frac (0-1 of the name's schedule),
    runrate_ratio (realized volume / expected-by-now; <1 = tape running dry).
    Score (0-100): limit proximity (40) + auction cutoff urgency (25) +
    behind schedule (20) + liquidity shortfall (15). Reasons are explicit —
    a triage list the dealer can challenge, not a black box."""
    now_utc = now_utc or _dt.datetime.now(_dt.timezone.utc).replace(tzinfo=None)
    cutoffs = {r["Market"]: r["Mins to cutoff"]
               for _, r in auction_countdown(basket["market"].unique(),
                                             now_utc).iterrows()}
    rows = []
    for _, r in basket.iterrows():
        score, reasons = 0.0, []
        lp = limit_proximity(r["market"], r["prev_close"], r["last_price"])
        if lp["level"] in ("ALERT", "LOCKED"):
            score += W_LIMIT
            reasons.append(f"limit {lp['level']}: {lp['used_frac']:.0%} of "
                           f"±{lp['band_pct']}% band ({lp['side']})")
        elif lp["level"] == "WATCH":
            score += W_LIMIT * 0.5
            reasons.append(f"limit WATCH: {lp['used_frac']:.0%} of band")
        mins = cutoffs.get(r["market"], np.inf)
        remaining = 1.0 - float(r["filled_frac"])
        if 0 <= mins < 15 and remaining > 0.05:
            score += W_AUCTION
            reasons.append(f"close cutoff in {mins:.0f}m with "
                           f"{remaining:.0%} unfilled")
        elif 0 <= mins < 60 and remaining > 0.25:
            score += W_AUCTION * 0.5
            reasons.append(f"cutoff in {mins:.0f}m, {remaining:.0%} unfilled")
        behind = float(r["elapsed_frac"]) - float(r["filled_frac"])
        if behind > 0.15:
            score += W_BEHIND
            reasons.append(f"{behind:.0%} behind schedule")
        elif behind > 0.05:
            score += W_BEHIND * 0.5
            reasons.append(f"{behind:.0%} behind")
        rr = float(r.get("runrate_ratio", 1.0))
        if rr < 0.6:
            score += W_LIQ
            reasons.append(f"tape running at {rr:.0%} of expected volume")
        elif rr < 0.8:
            score += W_LIQ * 0.5
            reasons.append(f"tape at {rr:.0%} of expected")
        sc = short_check(r["market"], r["side"],
                         bool(r.get("locate_confirmed", False)))
        if sc["level"] == "BLOCK":
            score = 100.0
            reasons.insert(0, "SHORT BLOCKED in this market")
        rows.append({"ticker": r["ticker"], "market": r["market"],
                     "side": r["side"], "score": round(min(score, 100.0), 1),
                     "filled": f"{float(r['filled_frac']):.0%}",
                     "reasons": "; ".join(reasons) or "—"})
    return (pd.DataFrame(rows).sort_values("score", ascending=False)
            .reset_index(drop=True))


# ── audit pack ─────────────────────────────────────────────────────────────

def build_audit_pack(basket: pd.DataFrame, program_id: str,
                     now_utc: _dt.datetime = None, notes: str = "") -> dict:
    """Timestamped, audit-ready record of the basket and every compliance
    check as of NOW — written as a by-product of working the program, not
    reconstructed for the auditor later."""
    now_utc = now_utc or _dt.datetime.now(_dt.timezone.utc)
    checks = []
    for _, r in basket.iterrows():
        lc = lot_check(r["market"], float(r.get("shares", 0)))
        sc = short_check(r["market"], r["side"],
                         bool(r.get("locate_confirmed", False)))
        lp = limit_proximity(r["market"], r["prev_close"], r["last_price"])
        checks.append({"ticker": r["ticker"], "market": r["market"],
                       "side": r["side"],
                       "lot": {"ok": lc["ok"], "note": lc["note"]},
                       "short": {"level": sc["level"], "note": sc["note"]},
                       "limit": {"level": lp["level"],
                                 "used_frac": None if pd.isna(lp["used_frac"])
                                 else lp["used_frac"]}})
    q = attention_queue(basket, now_utc.replace(tzinfo=None))
    return {"program_id": program_id,
            "recorded_at_utc": now_utc.isoformat(timespec="seconds"),
            "n_names": int(len(basket)),
            "markets": sorted(basket["market"].unique().tolist()),
            "checks": checks,
            "attention_top3": q.head(3).to_dict(orient="records"),
            "notes": notes,
            "rules_version": rules_version(),
            "disclaimer": "Static rule tables (approximations of public "
                          "exchange rules); production replaces with "
                          "exchange parameter feeds."}


def save_audit_pack(pack: dict, path: Path = DEFAULT_AUDIT_PATH) -> dict:
    path = Path(path)
    packs = []
    if path.exists():
        try:
            packs = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            packs = []
    packs.append(pack)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(packs, indent=1), encoding="utf-8")
    return pack


# ── demo basket ────────────────────────────────────────────────────────────

def demo_basket(seed: int = 3) -> pd.DataFrame:
    """A small cross-market basket exercising every cockpit rule: a Taiwan
    name near limit-up, a China-A short (blocked), an HK name behind
    schedule, a dry Japan tape, and two quiet names."""
    return pd.DataFrame([
        dict(ticker="2330.TW", market="Taiwan (TWSE)", side="Buy",
             shares=250_000, prev_close=100.0, last_price=108.9,
             filled_frac=0.55, elapsed_frac=0.60, runrate_ratio=1.1),
        dict(ticker="600519.SS", market="China-A Shanghai", side="Sell",
             shares=40_000, prev_close=1500.0, last_price=1493.0,
             filled_frac=0.10, elapsed_frac=0.30, runrate_ratio=0.9),
        dict(ticker="0700.HK", market="Hong Kong (HKEX)", side="Buy",
             shares=300_000, prev_close=350.0, last_price=352.0,
             filled_frac=0.35, elapsed_frac=0.70, runrate_ratio=0.9),
        dict(ticker="7203.T", market="Japan (TSE)", side="Sell",
             shares=500_000, prev_close=2500.0, last_price=2492.0,
             filled_frac=0.62, elapsed_frac=0.65, runrate_ratio=0.5,
             locate_confirmed=True),
        dict(ticker="005930.KS", market="Korea (KRX)", side="Buy",
             shares=150_000, prev_close=80_000.0, last_price=80_400.0,
             filled_frac=0.50, elapsed_frac=0.50, runrate_ratio=1.0),
        dict(ticker="D05.SI", market="Singapore (SGX)", side="Buy",
             shares=80_000, prev_close=40.0, last_price=40.1,
             filled_frac=0.45, elapsed_frac=0.48, runrate_ratio=1.0),
    ])
