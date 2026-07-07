"""
Agent 13 — Venue Selection & Smart Order Routing (statistical simulation).

Simulates the venue-allocation layer that sits between an execution algo's
parent-order schedule and the market: each 5-minute slice of the schedule is
split across the venues available in that market by a routing policy that
minimizes expected marginal cost per share — the actual objective of a real
smart order router, minus the microsecond mechanics.

WHAT IS HONESTLY SIMULATABLE at 5-min bar granularity with free data:
  * A stylized venue set per market with parameters calibrated to public
    sources (exchange fee schedules, Rule 605/606-style aggregates, MiFID
    market-share statistics): fee/rebate, addressable share of bar volume,
    fill probability, spread capture (how much of the half-spread crossing
    costs at that venue; 0 = midpoint), and adverse-selection markout.
  * Deterministic EXPECTED-fill routing (dark fills at their fill
    probability's expectation, residual re-routed to lit in the same bar —
    the ping-dark-then-sweep-lit behavior of real SORs), so results are
    exactly reproducible and unit-testable.
  * Genuine market-structure differences: the US/UK/Japan/Australia books are
    fragmented (primary + ECN/MTF/PTS + dark pools); Taiwan, Korea, China-A,
    India and most of SE Asia are single-venue markets where routing is
    correctly a near-no-op — and China-A has no off-exchange dark mechanism
    at all.
  * Venue-level TCA as a direct by-product: fills, fees, spread cost, price
    improvement, markouts by venue.

WHAT IS NOT SIMULATABLE (tracked in INSTITUTIONAL_GAP_REGISTER.md):
queue position/priority, latency and co-location effects, real-time
fill-probability estimation, actual dark-liquidity discovery, anti-gaming
logic, and internalization against franchise flow. Those need tick/L2 data
and venue connectivity. Every number this module produces is a parametric
model output, labelled as such in the UI.

Venue parameters are STYLIZED CONSTANTS — right order of magnitude, not a
fee-schedule feed. Fees are in bps of notional (negative = net rebate).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import numpy as np
import pandas as pd

# ── Default half-spread when no Corwin-Schultz estimate is available ──────
DEFAULT_HALF_SPREAD_BPS = 2.5

# Corwin-Schultz at daily frequency is known to overshoot spreads for liquid
# names; uncapped it makes lit crossing look absurdly expensive vs midpoint.
# Routing inputs are capped here, with a disclosed note on the result.
ROUTING_SPREAD_CAP_BPS = 15.0

ROUTING_POLICIES = ("Cost-optimized", "Lit-only", "Dark-preferred", "Primary-only")


@dataclass
class VenueProfile:
    name: str
    kind: str                  # "primary" | "lit" | "dark"
    fee_bps: float             # explicit cost in bps of notional (neg = rebate)
    volume_share: float        # fraction of a bar's volume addressable here
    fill_prob: float           # probability an allocated share executes
    spread_capture: float      # fraction of half-spread paid crossing (0 = midpoint)
    adverse_selection_bps: float  # expected post-fill markout penalty

    def expected_cost_bps(self, half_spread_bps: float) -> float:
        """Expected all-in marginal cost per share routed here (bps)."""
        return (self.spread_capture * half_spread_bps
                + self.fee_bps
                + self.adverse_selection_bps)


# ── Stylized venue sets per market ─────────────────────────────────────────
# Fragmented markets get a realistic primary/lit-alternative/dark structure;
# single-venue markets correctly offer no routing choice (the institutional
# reality in TW/KR/CN-A/IN and most of SE Asia).

def _fragmented(primary: str, ecn_a: str, ecn_b: Optional[str], dark: str) -> list[VenueProfile]:
    vs = [
        VenueProfile(primary, "primary", fee_bps=0.30, volume_share=0.40,
                     fill_prob=1.00, spread_capture=1.0, adverse_selection_bps=0.0),
        VenueProfile(ecn_a, "lit", fee_bps=0.25, volume_share=0.20,
                     fill_prob=1.00, spread_capture=1.0, adverse_selection_bps=0.1),
    ]
    if ecn_b:
        vs.append(VenueProfile(ecn_b, "lit", fee_bps=-0.10, volume_share=0.10,
                               fill_prob=1.00, spread_capture=1.0, adverse_selection_bps=0.4))
    vs.append(VenueProfile(dark, "dark", fee_bps=0.10, volume_share=0.15,
                           fill_prob=0.55, spread_capture=0.0, adverse_selection_bps=0.3))
    return vs


def _single(primary: str) -> list[VenueProfile]:
    return [VenueProfile(primary, "primary", fee_bps=0.30, volume_share=1.00,
                         fill_prob=1.00, spread_capture=1.0, adverse_selection_bps=0.0)]


MARKET_VENUES: dict[str, list[VenueProfile]] = {
    "US":               _fragmented("NYSE/Nasdaq (primary)", "ECN A (maker-taker)",
                                    "ECN B (inverted)", "Dark pool (midpoint ATS)"),
    "UK (LSE)":         _fragmented("LSE (primary)", "Cboe CXE / Turquoise (MTF)",
                                    None, "Dark MTF (midpoint, LIS)"),
    "Japan (TSE)":      _fragmented("TSE (primary)", "PTS (Japannext/Cboe)",
                                    None, "ToSTNeT / dark crossing"),
    "Australia (ASX)":  _fragmented("ASX (primary)", "Cboe Australia",
                                    None, "ASX Centre Point (midpoint)"),
    "Hong Kong (HKEX)": [
        VenueProfile("HKEX (primary)", "primary", 0.30, 0.90, 1.00, 1.0, 0.0),
        VenueProfile("Broker dark pools (ALP)", "dark", 0.10, 0.10, 0.45, 0.0, 0.3),
    ],
    # Single-venue markets — routing is correctly a near-no-op here.
    "Taiwan (TWSE)":    _single("TWSE (primary)"),
    "Korea (KRX)":      _single("KRX (primary)"),
    "Singapore (SGX)":  _single("SGX (primary)"),
    "China-A Shanghai": _single("SSE (primary — no off-exchange/dark mechanism)"),
    "China-A Shenzhen": _single("SZSE (primary — no off-exchange/dark mechanism)"),
    "India (NSE)":      _single("NSE (primary)"),
    "Thailand (SET)":   _single("SET (primary)"),
    "Indonesia (IDX)":  _single("IDX (primary)"),
    "Malaysia (KLSE)":  _single("Bursa (primary)"),
    "Vietnam (HOSE)":   _single("HOSE (primary)"),
}


@dataclass
class RoutingResult:
    policy: str
    market: str
    half_spread_bps: float
    fills_by_venue: pd.DataFrame     # index = bar time, columns = venue names (shares)
    venue_summary: pd.DataFrame      # per-venue shares/%, cost components, net cost
    blended_cost_bps: float          # share-weighted routing cost of the whole order
    routed_shares: float
    notes: list = field(default_factory=list)


def venues_for(market: str, allow_dark: bool = True,
               excluded: Optional[list[str]] = None) -> list[VenueProfile]:
    vs = MARKET_VENUES.get(market, _single(f"{market} (primary)"))
    excluded = set(excluded or [])
    out = [v for v in vs if v.name not in excluded]
    if not allow_dark:
        out = [v for v in out if v.kind != "dark"]
    # never route into an empty set — primary is always eligible
    return out or [vs[0]]


def route_order(schedule: pd.DataFrame, bar_volumes: np.ndarray, market: str,
                policy: str = "Cost-optimized", half_spread_bps: float = DEFAULT_HALF_SPREAD_BPS,
                allow_dark: bool = True, excluded: Optional[list[str]] = None) -> RoutingResult:
    """Split each bar's scheduled shares across eligible venues.

    schedule    : Agent 3 schedule DataFrame (time / shares_traded / price)
    bar_volumes : market volume per bar, aligned with schedule rows
    policy      : one of ROUTING_POLICIES
    Deterministic: dark venues fill at expected value (fill_prob × allocation)
    and the residual re-routes to lit venues in the SAME bar — the
    ping-dark-then-sweep behavior of a real SOR, in expectation.
    """
    capped = half_spread_bps > ROUTING_SPREAD_CAP_BPS
    if capped:
        half_spread_bps = ROUTING_SPREAD_CAP_BPS
    vs = venues_for(market, allow_dark=allow_dark and policy != "Lit-only", excluded=excluded)
    if policy == "Primary-only":
        vs = [v for v in vs if v.kind == "primary"] or vs
    notes = []
    if capped:
        notes.append(f"Half-spread input exceeded {ROUTING_SPREAD_CAP_BPS:g} bps and was capped "
                     "for routing realism — Corwin-Schultz overshoots at daily frequency for "
                     "liquid names; see the Pre-Trade spread reliability note.")
    if len(MARKET_VENUES.get(market, [])) <= 1:
        notes.append(f"{market} is a single-venue market — no routing choice exists; "
                     "100% executes on the primary exchange.")

    lit = sorted([v for v in vs if v.kind != "dark"],
                 key=lambda v: v.expected_cost_bps(half_spread_bps))
    dark = [v for v in vs if v.kind == "dark"]

    n = len(schedule)
    shares = schedule["shares_traded"].to_numpy(dtype=float)
    vols = np.asarray(bar_volumes, dtype=float)[:n]
    fills = {v.name: np.zeros(n) for v in vs}

    for i in range(n):
        want = shares[i]
        if want <= 0:
            continue
        bar_vol = max(vols[i], 0.0)

        # 1) dark first (midpoint saves the half-spread) unless policy says otherwise
        if dark and policy in ("Cost-optimized", "Dark-preferred"):
            for v in dark:
                cap = v.volume_share * bar_vol
                alloc = min(want, cap if policy == "Cost-optimized" else want)
                filled = alloc * v.fill_prob          # expected fill
                fills[v.name][i] += filled
                want -= filled
                if want <= 1e-9:
                    break

        # 2) residual sweeps lit venues in marginal-cost order, capped by
        #    each venue's addressable share of the bar
        for j, v in enumerate(lit):
            if want <= 1e-9:
                break
            is_last = j == len(lit) - 1
            cap = want if is_last else v.volume_share * bar_vol
            take = min(want, cap)
            fills[v.name][i] += take
            want -= take

    fills_df = pd.DataFrame(fills, index=schedule["time"].values)

    rows = []
    total = float(fills_df.values.sum())
    weighted_cost = 0.0
    for v in vs:
        sh = float(fills_df[v.name].sum())
        if total > 0 and sh <= 0:
            continue
        cost = v.expected_cost_bps(half_spread_bps)
        spread_cost = v.spread_capture * half_spread_bps
        improvement = (1 - v.spread_capture) * half_spread_bps
        weighted_cost += (sh / total) * cost if total > 0 else 0.0
        rows.append({
            "Venue": v.name, "Type": v.kind,
            "Shares": round(sh, 0), "% of order": round(100 * sh / total, 1) if total else 0.0,
            "Spread cost (bps)": round(spread_cost, 2),
            "Fees (bps)": round(v.fee_bps, 2),
            "Adverse selection (bps)": round(v.adverse_selection_bps, 2),
            "Price improvement (bps)": round(improvement, 2),
            "Net cost (bps)": round(cost, 2),
        })
    summary = pd.DataFrame(rows)

    return RoutingResult(policy=policy, market=market, half_spread_bps=half_spread_bps,
                         fills_by_venue=fills_df, venue_summary=summary,
                         blended_cost_bps=round(weighted_cost, 2),
                         routed_shares=round(total, 0), notes=notes)


def bar_volumes_for(schedule: pd.DataFrame, intraday: pd.DataFrame) -> np.ndarray:
    """Market volume per bar aligned to a schedule's timestamps."""
    vols = intraday["Volume"].reindex(pd.DatetimeIndex(schedule["time"]))
    return vols.fillna(0.0).to_numpy(dtype=float)


def compare_policies(schedule: pd.DataFrame, bar_volumes: np.ndarray, market: str,
                     half_spread_bps: float = DEFAULT_HALF_SPREAD_BPS,
                     allow_dark: bool = True,
                     excluded: Optional[list[str]] = None) -> pd.DataFrame:
    """Blended routing cost of the same schedule under each policy — the
    'why the router does what it does' view."""
    rows = []
    for pol in ROUTING_POLICIES:
        r = route_order(schedule, bar_volumes, market, policy=pol,
                        half_spread_bps=half_spread_bps,
                        allow_dark=allow_dark, excluded=excluded)
        dark_pct = 0.0
        if len(r.venue_summary):
            dk = r.venue_summary[r.venue_summary["Type"] == "dark"]["% of order"].sum()
            dark_pct = float(dk)
        rows.append({"Policy": pol, "Blended routing cost (bps)": r.blended_cost_bps,
                     "% dark": round(dark_pct, 1)})
    return pd.DataFrame(rows)
