"""
Institutional order ticket + pre-trade compliance checks.

Models the parameters an institutional algo order actually carries (the FIX
strategy-parameter set a buy-side EMS sends a broker algo), and the pre-trade
checks an OMS runs *before* anything is routed:

  * OrderTicket   — order type / limit price, execution time window, max
                    participation cap, must-complete flag, auction
                    participation flag. Rendered as its FIX tag set for
                    authenticity (`to_fix_fields`).
  * constrain_fills — the one shared fill-constraint kernel: applies the
                    participation cap and limit-price gating to any planned
                    per-bar schedule with carry-forward, so Agent 3 (schedule
                    DataFrames) and Agent 4 (fast numpy path) enforce
                    *identical* semantics. Residual unfilled shares flow into
                    the existing Perold opportunity-cost accounting.
  * check_order   — pre-trade compliance: restricted list, fat-finger size
                    limits, limit-price sanity. Returns findings with
                    BLOCK/WARN severity; the UI refuses to route a BLOCKed
                    order unless a supervisor override is acknowledged
                    (mirroring a real OMS override workflow).

Side is fixed to Buy for now — adding Sell flips slippage/impact signs across
the entire analytics stack and is tracked in INSTITUTIONAL_GAP_REGISTER.md.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

# ── Compliance rule parameters ────────────────────────────────────────────
FAT_FINGER_BLOCK_PCT_ADV = 25.0   # order > 25% ADV: blocked pending override
FAT_FINGER_WARN_PCT_ADV  = 10.0   # order > 10% ADV: warning
LIMIT_THROUGH_WARN_PCT   = 5.0    # limit > 5% through last close: warning

RESTRICTED_LIST_PATH = Path(__file__).resolve().parent.parent / "data" / "restricted_list.txt"


# ══════════════════════════════════════════════════════════════════════════
# Order ticket
# ══════════════════════════════════════════════════════════════════════════

@dataclass
class OrderTicket:
    """Institutional algo-order parameters. All-defaults == the app's
    original unconstrained behavior (backward compatible)."""
    side: str = "Buy"                                # fixed for now
    order_type: str = "Market"                       # "Market" | "Limit"
    limit_price: Optional[float] = None              # required if Limit
    start_time: Optional[dt.time] = None             # None = session open
    end_time: Optional[dt.time] = None               # None = session close
    max_participation_pct: Optional[float] = None    # e.g. 15.0 (% of bar volume)
    must_complete: bool = False                      # completion is a hard client constraint
    allow_auction: bool = True                       # gate MOC/MOO participation
    # ── venue / routing preferences (consumed by Agent 13, not by the fill
    #    constraints — routing allocates fills, it doesn't change them) ────
    sor_policy: str = "Cost-optimized"               # see agent13 ROUTING_POLICIES
    allow_dark: bool = True                          # eligible for dark/midpoint venues
    excluded_venues: list = field(default_factory=list)

    # ── derived helpers ───────────────────────────────────────────────────
    @property
    def effective_limit(self) -> Optional[float]:
        return self.limit_price if self.order_type == "Limit" else None

    @property
    def cap_frac(self) -> Optional[float]:
        return self.max_participation_pct / 100.0 if self.max_participation_pct else None

    def is_default(self) -> bool:
        """True when no constraint is active — callers can skip the
        constraint path entirely and reproduce legacy behavior."""
        return (self.effective_limit is None and self.start_time is None
                and self.end_time is None and self.cap_frac is None
                and self.allow_auction and not self.must_complete)

    def window_indices(self, bar_times) -> tuple[int, int]:
        """Map start/end times onto [s, e] inclusive bar positions of a
        simulated day. bar_times: DatetimeIndex of the day's bars."""
        n = len(bar_times)
        s, e = 0, n - 1
        times = [t.time() for t in bar_times]
        if self.start_time is not None:
            s = next((i for i, t in enumerate(times) if t >= self.start_time), n - 1)
        if self.end_time is not None:
            e = next((i for i in range(n - 1, -1, -1) if times[i] <= self.end_time), 0)
        if e <= s:                      # degenerate window — fall back to full day
            return 0, n - 1
        return s, e

    def constraint_summary(self) -> list[str]:
        out = []
        if self.effective_limit is not None:
            out.append(f"Limit {self.effective_limit:g} (no fills through limit)")
        if self.start_time or self.end_time:
            out.append(f"Window {self.start_time or 'open'} → {self.end_time or 'close'}")
        if self.max_participation_pct:
            out.append(f"Max participation {self.max_participation_pct:g}% of bar volume")
        if not self.allow_auction:
            out.append("Auction participation disabled (MOC/MOO excluded)")
        if self.must_complete:
            out.append("Must-complete order (unfilled residual is a violation, "
                       "not just an opportunity cost)")
        return out

    def routing_summary(self) -> list[str]:
        out = [f"SOR policy: {self.sor_policy}"]
        if not self.allow_dark:
            out.append("Dark/midpoint venues disallowed")
        if self.excluded_venues:
            out.append("Excluded venues: " + ", ".join(self.excluded_venues))
        return out

    def to_fix_fields(self, ticker: str, order_shares: float) -> list[dict]:
        """The ticket as (a subset of) its FIX 4.4 tag representation —
        what an EMS would actually put on the wire to a broker algo."""
        rows = [
            {"Tag": 55,  "Field": "Symbol",          "Value": ticker},
            {"Tag": 54,  "Field": "Side",            "Value": "1 (Buy)"},
            {"Tag": 38,  "Field": "OrderQty",        "Value": f"{order_shares:,.0f}"},
            {"Tag": 40,  "Field": "OrdType",         "Value": "2 (Limit)" if self.order_type == "Limit" else "1 (Market)"},
            {"Tag": 59,  "Field": "TimeInForce",     "Value": "0 (Day)"},
            {"Tag": 21,  "Field": "HandlInst",       "Value": "3 (Automated, no intervention)"},
        ]
        if self.effective_limit is not None:
            rows.append({"Tag": 44, "Field": "Price", "Value": f"{self.effective_limit:g}"})
        if self.start_time is not None:
            rows.append({"Tag": 168, "Field": "EffectiveTime", "Value": str(self.start_time)})
        if self.end_time is not None:
            rows.append({"Tag": 126, "Field": "ExpireTime", "Value": str(self.end_time)})
        if self.max_participation_pct:
            rows.append({"Tag": 849, "Field": "ParticipationRate",
                         "Value": f"{self.max_participation_pct:g}%"})
        rows.append({"Tag": 847, "Field": "TargetStrategy",
                     "Value": "(set by Agent 5 recommendation / user selection)"})
        rows.append({"Tag": 100, "Field": "ExDestination",
                     "Value": f"SOR ({self.sor_policy}"
                              + ("" if self.allow_dark else ", lit-only")
                              + (", excl: " + ",".join(self.excluded_venues)
                                 if self.excluded_venues else "") + ")"})
        if not self.allow_auction:
            rows.append({"Tag": 6062, "Field": "CustomTag: AuctionParticipation",
                         "Value": "N"})
        return rows


# ══════════════════════════════════════════════════════════════════════════
# Shared fill-constraint kernel (used by Agent 3 and Agent 4)
# ══════════════════════════════════════════════════════════════════════════

def constrain_fills(planned: np.ndarray, prices: np.ndarray, volumes: np.ndarray,
                    cap_frac: Optional[float] = None,
                    limit_price: Optional[float] = None,
                    exempt: frozenset = frozenset()) -> np.ndarray:
    """Apply participation cap + limit-price gating to a planned per-bar
    schedule, carrying blocked shares forward to later eligible bars.

    planned/prices/volumes are aligned arrays over the (already windowed)
    simulation bars. `exempt` holds bar indices exempt from the participation
    cap (auction prints — MOC's closing bar, MOO's opening bar — where the
    continuous-trading cap doesn't apply). The limit gate applies everywhere,
    auctions included. Shares that never become fillable remain unfilled and
    flow into the caller's opportunity-cost accounting.
    """
    n = len(planned)
    out = np.zeros(n)
    carry = 0.0
    for i in range(n):
        want = planned[i] + carry
        if want <= 0:
            continue
        allowed = want
        if limit_price is not None and prices[i] > limit_price:   # Buy side
            allowed = 0.0
        elif cap_frac is not None and i not in exempt:
            allowed = min(allowed, cap_frac * max(volumes[i], 0.0))
        traded = min(want, allowed)
        out[i] = traded
        carry = want - traded
    return out


def windowed_curve(hist_curve: Optional[np.ndarray], s: int, e: int) -> Optional[np.ndarray]:
    """Slice a full-day volume curve to [s, e] and renormalize to sum 1."""
    if hist_curve is None:
        return None
    seg = np.asarray(hist_curve[s:e + 1], dtype=float)
    tot = seg.sum()
    return seg / tot if tot > 0 else None


def excluded_algos(ticket: "OrderTicket", s: int, e: int, n_bars: int) -> dict[str, str]:
    """Algos the ticket makes ineligible, with reasons (shown in the UI and
    respected by Agent 5, which can only pick from what was simulated)."""
    out: dict[str, str] = {}
    if not ticket.allow_auction:
        out["MOC"] = "Auction participation disabled on the order ticket"
        out["MOO"] = "Auction participation disabled on the order ticket"
    if s > 0:
        out.setdefault("MOO", "Execution window starts after the opening auction")
    if e < n_bars - 1:
        out.setdefault("MOC", "Execution window ends before the closing auction")
    return out


# ══════════════════════════════════════════════════════════════════════════
# Pre-trade compliance
# ══════════════════════════════════════════════════════════════════════════

@dataclass
class ComplianceFinding:
    severity: str        # "BLOCK" | "WARN"
    rule: str
    message: str


def load_restricted_list(path: Path = RESTRICTED_LIST_PATH) -> set[str]:
    """Restricted/watch list — one symbol per line, '#' comments. A demo
    stand-in for the OMS-enforced firm restricted list."""
    if not path.exists():
        return set()
    out = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.split("#", 1)[0].strip().upper()
        if line:
            out.add(line)
    return out


def check_order(ticket: OrderTicket, ticker_base: str, order_pct_adv: float,
                last_price: Optional[float] = None) -> list[ComplianceFinding]:
    """Pre-trade checks an OMS would run before routing. Returns findings;
    empty list = clean pass. BLOCK findings require an override to proceed."""
    findings: list[ComplianceFinding] = []

    restricted = load_restricted_list()
    if ticker_base.strip().upper() in restricted:
        findings.append(ComplianceFinding(
            "BLOCK", "Restricted list",
            f"{ticker_base.upper()} is on the firm restricted/watch list — "
            "orders require compliance sign-off."))

    if order_pct_adv > FAT_FINGER_BLOCK_PCT_ADV:
        findings.append(ComplianceFinding(
            "BLOCK", "Fat-finger / size limit",
            f"Order is {order_pct_adv:g}% of ADV (> {FAT_FINGER_BLOCK_PCT_ADV:g}% "
            "hard limit) — confirm size is intended."))
    elif order_pct_adv > FAT_FINGER_WARN_PCT_ADV:
        findings.append(ComplianceFinding(
            "WARN", "Size advisory",
            f"Order is {order_pct_adv:g}% of ADV (> {FAT_FINGER_WARN_PCT_ADV:g}%) — "
            "expect meaningful market impact; consider a multi-day schedule."))

    if ticket.effective_limit is not None and last_price:
        through = (ticket.effective_limit - last_price) / last_price * 100
        if through > LIMIT_THROUGH_WARN_PCT:
            findings.append(ComplianceFinding(
                "WARN", "Limit-price sanity",
                f"Buy limit is {through:.1f}% ABOVE the last price "
                f"({ticket.effective_limit:g} vs {last_price:g}) — behaves like a "
                "market order; check for a mis-keyed limit."))

    if ticket.order_type == "Limit" and ticket.limit_price is None:
        findings.append(ComplianceFinding(
            "BLOCK", "Order validity",
            "Order type is Limit but no limit price was provided."))

    if (ticket.start_time and ticket.end_time
            and ticket.end_time <= ticket.start_time):
        findings.append(ComplianceFinding(
            "BLOCK", "Order validity",
            "Execution window end time is not after its start time."))

    if ticket.must_complete and ticket.effective_limit is not None:
        findings.append(ComplianceFinding(
            "WARN", "Constraint conflict",
            "Must-complete + limit price can conflict: if the market trades "
            "away from the limit, completion is impossible by construction."))

    return findings
