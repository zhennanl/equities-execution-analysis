# Agency vs Principal — When Clients Choose Which

*The client's decision framework for routing a program agency vs risk.
Companion to PT_BASKET_TRADE_CYCLE.md (cycle + principal appendix).
Session 6s.*

---

## The one-line economics

The client compares a **known cost** against an **uncertain one**:

> risk premium P (paid, certain)  vs  E[agency cost] + λ·σ(agency outcome)

where λ is how much the client hates variance. Principal wins when
certainty is worth more than its price; agency wins when the client can
carry the outcome variance more cheaply than the desk can. Everything
below is that comparison in specific situations.

## When clients go PRINCIPAL (pay for certainty)

1. **A benchmark print with legal or accounting force.** Transition
   management (pension fund changes manager: assets must move at a
   defensible single print), fund mergers and in-specie transfers priced
   at a NAV point, index transitions where the mandate measures at the
   effective close. The strike IS the deliverable — working the order
   leaves tracking risk the fiduciary cannot hold.
2. **Hard deadlines.** Redemption to fund by Friday, quarter-end NAV,
   deal completion. No time to average — transfer the risk.
3. **Event-gap risk the client refuses to carry.** Elections, central
   bank nights, an earnings date inside the working horizon: pay the
   premium, sleep. Volatile regimes push clients toward risk (even
   though premiums widen too — certainty demand rises faster).
4. **The toxic tail.** A basket whose worst names would take a week to
   work leaks footprint every day it's alive. One print, one leak — and
   the desk, not the client, wrestles the illiquidity. (This is the
   adverse-selection engine: risk desks know clients bring them the ugly
   baskets, and price accordingly.)
5. **Operational simplicity.** One price, one ticket, no intraday
   babysitting, trivial TCA — attractive to clients without execution
   infrastructure.
6. **Netting luck.** When a desk holding opposite inventory bids inside
   fair value, the client happily takes a premium below true cost —
   principal can be genuinely cheap when someone's book wants your risk.

## When clients go AGENCY (keep the variance, save the premium)

1. **Cost minimization with time flexibility.** No hard print, no
   deadline: expected agency cost = spread + impact + commission, with
   no risk charge, no winner's-curse buffer, no dealer margin. Over many
   programs the client keeps the premium.
2. **Liquid, balanced, high-tracking baskets.** The variance being
   insured is small — paying any premium for it is poor value. (Note
   the asymmetry: these baskets also get the TIGHTEST risk bids; it's
   the mid-quality basket where the choice is genuinely close.)
3. **Repeat/programmatic flow.** Daily index trackers, recurring
   rebalances: commissions compound cheaper than premiums, and the flow
   is exactly what agency desks price keenly to win.
4. **Confidentiality preference.** A risk RFQ broadcasts the blind
   profile to every losing bidder; agency shows the names to ONE broker
   with no inventory incentive. Clients burned by post-auction market
   moves route sensitive flow agency.
5. **Conflict aversion / mandate rules.** Some fiduciary mandates
   restrict principal dealing outright; others require best-execution
   evidence that a single risk print can't demonstrate. And an agency
   broker has no unwind competing with the client's own order — the
   agency-only pitch (CLSA's).
6. **Transparency and control.** Fill-by-fill visibility, benchmark
   choice (IS/VWAP/close), participation limits, the right to pause —
   none of which exist after a risk transfer.
7. **Asia-specific frictions.** Pan-Asia baskets with China-A short
   legs (unhedgeable under T+1/no-short), Taiwan/Korea funding or
   locked-limit names get carved out of risk bids or priced brutally —
   the risk route often isn't really available at size, so agency is
   the working default for the region's harder paper.

## The middle ground (what desks actually quote)

- **Guaranteed VWAP/close (principal-lite):** desk guarantees the
  benchmark print for a smaller premium — certainty about the benchmark,
  not about a level.
- **Partial risk:** agency on the liquid core, risk bid only on the
  illiquid tail — the client insures exactly the variance that scares it.
- **Agency incentive:** commission scales with performance vs benchmark —
  aligns without inventory.
- **Capital on residuals:** work agency all day, desk takes the unfilled
  tail at the close — certainty about completion, cheapest premium.

## The empirical pattern (what you'd see on a desk)

Certainty is bought around **benchmark-critical dates**: index effective
closes, month/quarter-end, transition strike dates — risk-bid volumes
cluster there. Cost-sensitive, flexible, repeat flow trades agency the
rest of the year. And the same client uses both: agency for the routine
rebalance, a risk bid for the merger — the routing decision is per-trade,
not per-relationship.

## Interview one-liner

"Principal is insurance: clients buy it when the outcome variance sits
somewhere it legally or emotionally can't — a transition strike, a hard
deadline, a toxic tail — and self-insure through agency when flow is
liquid, repeat, and flexible. My platform quantifies the agency side of
that comparison (expected cost and its distribution), which is exactly
what a client needs to judge whether a risk premium quoted elsewhere is
rich — an agency desk that can price the other side's bid is a better
advisor for it."
