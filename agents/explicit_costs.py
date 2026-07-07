"""
Explicit execution costs — commissions, exchange/regulatory fees, and
stamp/transaction taxes per market.

Institutional TCA always reports explicit costs SEPARATELY from implicit
costs (impact/slippage/opportunity): they're deterministic, known pre-trade,
and in some markets they dominate — UK stamp duty alone is 50 bps on buys,
an order of magnitude above typical large-cap impact for small orders.

Values are STYLIZED 2026-ERA APPROXIMATIONS of the headline rates (documented
order-of-magnitude, not a fee engine): institutional program/DMA commission
is standardized at 1.5 bps across markets for comparability; stamp/
transaction taxes use the published statutory rates. Side matters — several
Asian markets tax SELLS only (Taiwan 30 bps, Korea, China-A, Vietnam), the
UK taxes BUYS — so the table carries both and the app (currently buy-only)
reports the buy-side total plus an "exit cost" note for round-trip awareness.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ExplicitCosts:
    commission_bps: float      # institutional program/DMA commission
    fees_bps: float            # exchange + clearing + regulatory (per side approx)
    stamp_buy_bps: float       # stamp/transaction tax charged on BUYS
    sell_tax_bps: float        # transaction/stamp tax charged on SELLS
    note: str = ""

    def total_bps(self, side: str = "Buy") -> float:
        tax = self.stamp_buy_bps if side == "Buy" else self.sell_tax_bps
        return round(self.commission_bps + self.fees_bps + tax, 2)

    def breakdown(self, side: str = "Buy") -> list[str]:
        out = [f"Commission {self.commission_bps:g} bps",
               f"Exchange/clearing/regulatory fees {self.fees_bps:g} bps"]
        if side == "Buy" and self.stamp_buy_bps:
            out.append(f"Stamp/transaction tax on buys {self.stamp_buy_bps:g} bps")
        if side == "Sell" and self.sell_tax_bps:
            out.append(f"Transaction tax on sells {self.sell_tax_bps:g} bps")
        return out


_C = ExplicitCosts

EXPLICIT_COSTS: dict[str, ExplicitCosts] = {
    "US":               _C(1.5, 0.1, 0.0, 0.1,  "SEC/TAF-type fees apply to sells."),
    "UK (LSE)":         _C(1.5, 0.1, 50.0, 0.0, "0.5% stamp duty reserve tax on buys — often the "
                                                "dominant cost of UK executions."),
    "Hong Kong (HKEX)": _C(1.5, 0.6, 10.0, 10.0, "0.1% stamp duty each side + trading fee/levy."),
    "Japan (TSE)":      _C(1.5, 0.2, 0.0, 0.0,  "No stamp/transaction tax."),
    "Taiwan (TWSE)":    _C(1.5, 0.4, 0.0, 30.0, "0.3% securities transaction tax on sells."),
    "Korea (KRX)":      _C(1.5, 0.3, 0.0, 15.0, "Securities transaction tax on sells (KOSPI headline "
                                                "~0.15% era-dependent; stylized)."),
    "China-A Shanghai": _C(1.5, 0.4, 0.0, 5.0,  "0.05% stamp on sells (post-2023 cut) + transfer fee."),
    "China-A Shenzhen": _C(1.5, 0.4, 0.0, 5.0,  "0.05% stamp on sells (post-2023 cut) + transfer fee."),
    "India (NSE)":      _C(1.5, 0.4, 10.0, 10.0, "0.1% STT on delivery trades, both sides."),
    "Australia (ASX)":  _C(1.5, 0.2, 0.0, 0.0,  "No stamp on on-market transfers."),
    "Singapore (SGX)":  _C(1.5, 0.4, 0.0, 0.0,  "Clearing + access fees; no stamp on scripless."),
    "Thailand (SET)":   _C(1.5, 0.6, 0.0, 0.0,  "Exchange + regulator levies."),
    "Indonesia (IDX)":  _C(1.5, 0.4, 0.0, 10.0, "0.1% sales tax on sells."),
    "Malaysia (KLSE)":  _C(1.5, 0.4, 10.0, 10.0, "Stamp 0.1% (RM1,000 cap — cap not modeled) + clearing."),
    "Vietnam (HOSE)":   _C(1.5, 0.5, 0.0, 10.0, "0.1% personal income/transaction tax on sells."),
}

DEFAULT_COSTS = _C(1.5, 0.3, 0.0, 0.0, "Default estimate (market not in table).")


def get_explicit_costs(market: str) -> ExplicitCosts:
    return EXPLICIT_COSTS.get(market, DEFAULT_COSTS)


def explicit_cost_note(market: str, side: str = "Buy") -> str:
    c = get_explicit_costs(market)
    total = c.total_bps(side)
    parts = "; ".join(c.breakdown(side))
    exit_hint = ""
    if side == "Buy" and c.sell_tax_bps:
        exit_hint = (f" Round-trip awareness: exiting this position later incurs a further "
                     f"~{c.sell_tax_bps:g} bps sell-side tax in this market.")
    return (f"Explicit costs (~{total:g} bps, {side.lower()} side): {parts}. "
            f"{c.note} These are deterministic and additive to the modeled implicit costs "
            f"(impact/slippage/opportunity) — reported separately per TCA convention."
            + exit_hint)
