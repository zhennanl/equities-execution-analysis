# What Wins an Agency Rebalance Quote & the PT Desk's Full Book

*Reference note (companion to INDEX_REBALANCE_TRADE_LIFECYCLE.md
Step 1 / Phase 0, and the commercial context for AI_ON_THE_PT_DESK.md
and PITCH_PACK_DESIGN.md).*

---

## Part 1 — What wins an agency rebalance quote

When several brokers pitch the same agency trade, commission is rarely
the decider — it's table stakes among qualified desks (everyone quotes
within a basis point). What actually ranks, in order:

1. **Measurable execution quality.** The benchmark is public and
   identical across brokers, so clients literally maintain league
   tables: your realized slippage vs the close, auction fill rates,
   completion rates on past events. This is the one factor that
   compounds — and why every basis point on every event matters beyond
   that event.
2. **Local market capability.** Can you handle *every* market and name
   in the basket — the Taiwan ID process, India FPI mechanics, Connect
   quotas, foreign-room-constrained names, odd lots, the weird ones?
   One "sorry, we can't do that line" loses the whole basket, because
   clients hate splitting.
3. **Crossing and natural liquidity.** The probability that CLSA holds
   offsetting flow (other clients' rebalance orders, block flow) that
   can cross against yours at mid — less impact, and clients know
   which desks have the franchise density to offer it.
4. **Analytics and color.** Differentiated pre-event content — flow
   estimates, crowding reads, per-name risk flags — plus honest,
   detailed post-trade TCA. This is the *tie-breaker among equals* and
   the cheapest factor to be exceptional at. It's also exactly what
   our project produces (see PITCH_PACK_DESIGN.md).
5. **Operational cleanliness.** No fails, clean allocations across the
   client's 40 funds, painless recon. Ops errors are how brokers get
   *removed* from panels — asymmetric: it can't win you the trade but
   absolutely loses it.
6. **Trust and conflicts.** Information handling record (did your last
   rebalance leak?), and the structural pitch: agency-only means no
   principal book positioned against the client's order. That's CLSA's
   cleanest differentiator against bank desks.
7. **Relationship infrastructure.** Panel status, research/corporate-
   access votes, service consistency — the ambient stuff that decides
   marginal allocations.

## Part 2 — The rest of the PT desk's book, ranked by importance

Index rebalance is the flagship, but a rough ordering of everything
else (revenue-weighted, for an Asia agency desk — mix varies by
franchise):

1. **Systematic/quant model turnover** — the bread and butter. Quant
   funds rebalance monthly, weekly, some daily; recurring baskets,
   algo-heavy, lower touch but relentless volume. Annually this often
   *exceeds* index-event revenue precisely because it never stops.
2. **Transitions** — a pension fires manager A and hires manager B;
   the legacy portfolio must become the target portfolio. Episodic but
   enormous (single events can be billions), multi-week, high-touch,
   and won on exactly the same capabilities as rebalances plus
   confidentiality.
3. **Cash-flow rebalances** — fund inflows deployed, redemptions
   raised, month-end realignment to target weights. The month-end
   rhythm; steady, moderate-margin.
4. **Asset-allocation restructures** — "shift 3% from EM to DM,"
   de-grossing in risk-off, sector tilts, hedge-fund pair baskets.
   Discretionary timing (they fill the mid-month dead zone),
   judgment-heavy.
5. **ETF-linked flow** — authorized participants' creation/redemption
   baskets and ETF market-maker hedging. Growing fast in Asia with
   local ETF complexes; tight margins, but it's the same in-kind
   baskets our 0050 paired-block proxy watches.
6. **Derivative-linked baskets** — cash-vs-futures switches (EFPs),
   expiry-related programs, dividend-season trades, delta-one hedge
   flow executed for clients. Technical, calendar-clustered around
   expiries.
7. **Event-driven misc** — corporate-action-driven baskets (tenders,
   spin-offs, share-class conversions), dual-listing migrations, and
   one-off client special situations.

**The connective observation:** items 1–5 are all *benchmark-
constrained basket flow with a knowable calendar* — the same
analytical machinery (pre-trade cost, capacity, crossing, auction
discipline, TCA loop) serves the whole ranking. Index rebalance is the
purest, most public, most competitive instance of it — which is why
demonstrating mastery there implies capability across the book.
