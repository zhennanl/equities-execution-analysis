# The Full Trade Cycle of a Basket at a Program Trading Desk

*End-to-end walkthrough, agency lens (CLSA-style), Asia specifics
throughout. Each stage maps to the platform module that automates it —
and the two stages the platform deliberately does not model are flagged.
Session 6q.*

---

## Stage 0 — Inquiry / RFQ (the desk wins the trade)

The client (asset manager, transition manager, hedge fund, index tracker)
sends an **indicative basket** — often *blind/masked*: no names, just the
profile (number of lines, gross notional, side balance, %ADV distribution,
sector/country weights, tracking properties vs a hedgeable index). On this
profile the desk quotes one of two ways:

- **Agency**: "we work it for you" — commission in bps/cps, benchmark
  agreed (arrival / interval VWAP / close / implementation shortfall),
  strategy discussed. Desk earns commission, client keeps market risk.
- **Principal / risk bid**: the desk buys the whole basket at a guaranteed
  price (usually benchmark ± a risk premium in bps) and takes the market
  risk onto its own book, hedging with futures/ETFs and unwinding over
  days. Priced off the blind profile: hedgeability, liquidity tail
  (the worst 10% of names dominate the bid), side imbalance, event risk.

Several brokers compete on the RFQ; the client picks on price, trust, and
past performance (the QBR is stage 8 feeding stage 0).

*Platform: pre-trade cost machinery informs an agency quote; risk-bid
pricing is deliberately NOT modeled (a negotiation + risk-book workflow —
see INFEASIBLE_FEATURES.md). Know the mechanics, don't claim the tool.*

## Stage 1 — Award, order receipt & staging

On award the real file lands (names revealed). Now:
normalize and validate the file (ticker conventions, sides, notional→
shares, duplicates, both-sides flags) → load into the OMS as a program →
**compliance pre-flight**: restricted/watch lists, short locates & market
legality, ownership/disclosure headroom, board-lot rounding → confirm
instructions with the sales trader (benchmark, limits, participation caps,
completion deadline, discretion boundaries) → FX plan for restricted
currencies (TWD/KRW/INR funding, cutoffs).

*Platform: A8 normalizer, lot/short checks, pre-flight, FX_NOTES.*

## Stage 2 — Pre-trade analysis & schedule design

Per name: %ADV, expected cost (spread + impact), capacity days, limit-band
proximity, venue plan. Per basket: side/notional imbalance, cost estimate
vs the agreed benchmark, hardest-names list, auction capacity vs order
size, market-by-market wave plan across time zones (Tokyo/Taipei →
HK/China → India → EU/US), holiday/closure check, internal **crossing
check** against other client flows (compliant mechanism per market).
Output: the pre-open pack the sales trader sends the client before the
open.

*Platform: A1 pre-open pack, cost model, wave_plan, A9 calendar, A10
crossing detector, A11 exposure scheduler (urgency vs funding path).*

## Stage 3 — Execution (the dealer's day)

Work the schedule across sessions: opening auctions where liquidity
justifies, continuous session via algos/DMA within participation caps,
lunch-break handling (JP/CN/HK), closing auctions with their cutoffs
(TW 13:25, CN 14:57, JP 15:25, HK CAS, KR 15:20). Throughout: monitor the
attention queue (limit proximity → the queue-vs-retreat decision on a
locked name, run-rate vs expected volume, behind-schedule names, auction
cutoff countdowns); handle events (halts, VCM/VI triggers, news on working
names); decide residuals (roll to next session vs force completion);
send the client intraday updates (completion %, slippage vs benchmark,
notable events). Every check and decision lands in the audit pack as a
by-product.

*Platform: cockpit (attention queue, limit proximity, auction countdown),
A2 transition alerts, live run-rate re-forecast, audit packs.*

## Stage 4 — Booking, allocation & confirmation

Fills aggregate to average prices per name (market conventions differ:
gross vs net-of-fees pricing, local currency). Book to client accounts;
if several funds sit behind one order, **allocate** per the client's
scheme. Confirmations flow client-ward (FIX allocations / CTM matching)
with commission, exchange fees, and taxes itemized (HK stamp duty, TW
transaction tax on sells, etc.). FX executed for settlement currency
needs, respecting onshore cutoffs for restricted currencies.

*Platform: explicit-costs model knows the fee/tax schedules; booking/
allocation itself is OMS territory — not modeled, disclosed.*

## Stage 5 — EOD reporting

Same evening: per-market completion, average prices vs the agreed
benchmark, residual roll plan for tomorrow's opens, notable events
(limit locks, blocks, halts), settlement dates per market. Drafted
automatically, edited by the dealer, sent by the sales trader.

*Platform: A3 EOD summary draft (numbers-locked).*

## Stage 6 — Settlement (T+1/T+2 by market)

Settlement instructions to custodians (SWIFT MT54x), each market on its
own cycle: China T+1 stock (with pre-matching), India T+1 (T+0 optional
top-500), US T+1, most of Asia T+2 — holiday clusters shift chains (a
CNY-week TWSE trade settles almost two weeks after trade date).
Restricted-currency funding must land on time (FINI pre-funding
considerations in TW, IRC in KR). Fails management: partials, buy-in
regimes per market.

*Platform: A9 holiday-aware settlement + closure warnings.*

## Stage 7 — Reconciliation & discrepancy resolution

Our blotter vs street confirms vs custodian records: quantity, average
price, fees, FX. Breaks classified (qty / price / missing-either-side /
fee-FX) with suggested actions; trivial ones auto-clear within tolerance,
humans keep the ambiguous tail; correspondence to counterparties in
standard formats. Unresolved breaks age into fails.

*Platform: A4/classify_breaks + program_recon; B7 drafter at the desk.*

## Stage 8 — Post-trade review (and back to Stage 0)

TCA vs the agreed benchmark filed per program; outliers attributed;
quarterly the client review aggregates it all — difficulty-adjusted,
CI-gated — into the deck that defends the desk's ranking on the client's
broker wheel. That ranking decides how much flow arrives at Stage 0 next
quarter. The cycle is a loop, and the QBR is the flywheel.

*Platform: TCA/IS attribution, markouts, Page-4 QBR.*

---

## One picture

```
RFQ/quote → award & staging → pre-trade pack → EXECUTE (the day)
   ↑            (normalize,      (cost, waves,     (cockpit, alerts,
   │             pre-flight)      crossing)         residuals, audit)
   │                                                     ↓
QBR/wheel ← recon & breaks ← settlement ← EOD report ← booking/allocation
(stage 8)     (stage 7)       (stage 6)    (stage 5)      (stage 4)
```

## The two honest boundaries

1. **Risk-bid pricing (Stage 0 principal path)** — a risk-book and
   negotiation workflow; the platform informs the agency quote only.
2. **Booking/allocation (Stage 4)** — OMS/middle-office territory; the
   platform consumes its outputs (fills, confirms) rather than replacing it.

Interview one-liner: "I can walk a basket from a blind RFQ profile to the
quarterly review that wins the next RFQ — and my project automates six of
the nine stages: staging, pre-trade, execution monitoring, EOD, settlement
awareness, and recon, with the audit trail written as a by-product at
every step."


---

## Appendix — How a principal (risk) program trade works

*CLSA runs agency-only, so a dealer there never books one — but clients
compare the agency quote against risk bids from bulge brackets on every
large RFQ, so understanding the other side of the auction is part of the
job. It is also CLSA's pitch: an agency-only desk has no risk book to
favor and no unwind flow to hide.*

### 1. The auction

The client sends the **blind profile** to several brokers simultaneously:
line count, gross notional, side balance, currency/country weights,
%ADV distribution (especially the tail), tracking error and beta vs a
hedgeable index, sometimes sector weights. Names are NOT disclosed —
the client is about to hand over its footprint and does not want losers
of the auction front-running it. Brokers return a single number: the
**risk premium**, in bps of gross notional, to take the entire basket at
a agreed **strike benchmark** (usually today's close, sometimes arrival
mid). Best bid wins; the winner learns the names only after winning.

### 2. What the premium prices (the bid anatomy)

The desk decomposes the blind profile into:

- **Hedgeable (systematic) risk** — the basket's beta/tracking vs index
  futures or liquid ETFs. Cheap to carry: hedge it at strike, pay only
  futures spread + basis risk. A high-tracking basket (an index-fund
  transition) bids TIGHT.
- **Idiosyncratic residual** — what no hedge covers; carried unhedged
  through the unwind. Priced off residual vol x expected unwind horizon
  (the sqrt-of-days term). This is why tracking properties dominate the
  bid.
- **Unwind cost** — the impact cost of trading OUT of every line, from
  the same sqrt-law machinery an agency desk uses for cost estimates;
  the %ADV tail drives it (the worst 10% of lines can be half the bid).
- **Asia frictions** — limit bands (a locked name cannot be unwound),
  China T+1/no-short (a short-side China line may be UNHEDGEABLE —
  bid wide or carve it out), restricted currencies (TWD/KRW funding),
  stamp/transaction taxes paid on the unwind leg too.
- **Adverse selection (winner's curse)** — the client knows the names;
  the desk knows a distribution. Clients systematically send their most
  toxic baskets to risk (that is WHY they pay the premium), and the
  winning bid is by construction the most optimistic one. Desks defend
  with profile analytics, client-level history (whose baskets bled?),
  and by capping size per client.
- **Book netting** — if the incoming basket offsets inventory already on
  the risk book (yesterday's unwind residuals, another client's
  opposite flow), the marginal risk is lower and the desk can bid
  tighter than standalone math suggests. Big risk books win auctions for
  structural reasons.

Stylized: premium ≈ unwind impact cost + λ·(residual vol √unwind-days)
+ frictions + winner's-curse buffer − netting benefit, with λ the risk
charge the desk's management sets.

### 3. The strike (risk transfer moment)

At the agreed print (say today's HK/TW/JP closes), ownership transfers:
the client sells the basket to the desk at close ± premium, one ticket,
done — the client's execution risk ends HERE. The desk simultaneously
slams on the systematic hedge (sell index futures against a bought
basket) as close to the strike as possible; every minute of delay is
naked market risk.

### 4. The unwind (where the P&L is made or lost)

The desk now quietly trades out of the inventory over hours-to-days —
this is an agency-style execution problem turned inward: schedule vs
impact, participation caps, limit-band management, but with the desk's
own capital on the line and the hedge decaying as the basket shrinks
(futures rolled down as lines complete, else the book becomes a
short-futures position). Residual names that lock limit-up/down or lose
liquidity stretch the horizon and burn premium.

**P&L = premium collected − unwind slippage − hedge costs/basis −
idiosyncratic moves while carried.** A desk that consistently wins
auctions and loses on unwind is mispricing the tail or the toxicity —
which is why risk desks keep exactly the per-client, difficulty-adjusted
performance history our QBR builds for agency flow.

### 5. Controls and conflicts (why this is a different business)

- **Pre-hedging rules**: hedging before the strike on the basis of the
  client's inquiry is heavily restricted (and in exam-question form:
  front-running). Regimes differ; compliance owns the line.
- **Information barriers**: the risk book must not see agency client
  flow; the losing bidders must never learn the names; the winner's
  unwind must not be visible to its own agency desk's clients.
- **Balance sheet & capital**: inventory consumes risk limits and
  regulatory capital — the real reason principal PT lives at
  balance-sheet banks. An agency-only broker (CLSA) structurally cannot
  and strategically does not: its pitch is the ABSENCE of an unwind flow
  that competes with the client's order — no risk book, no conflict.

### 6. What carries over to an agency dealer

The math is the same machinery pointed the other way: the unwind-cost
term is our pre-trade cost model; tracking decomposition is our basket
analytics; the toxicity history is our QBR; limit/liquidity tails are our
attention queue. Understanding the risk bid makes the agency dealer
better at the two moments it matters: advising a client whether a risk
premium quoted elsewhere is rich or fair, and explaining why the agency
route's expected cost + zero conflict can beat a guaranteed-price
headline.
