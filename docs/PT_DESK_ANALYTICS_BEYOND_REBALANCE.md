# PT Desk Analytics Beyond Index Rebalance — Per Flow Type, With AI Leverage

*Session 9h (2026-07-29). Structure: the user's revenue-weighted
flow taxonomy; per category — the analytics worth building, the AI
role, and which existing components port directly. The invariants
carry over unchanged: deterministic engines produce numbers; AI
parses, patterns, optimizes, and renders; everything gets graded.*

## 1. Systematic/quant turnover (the bread and butter)

**Analytics:** client flow FINGERPRINTING — each quant client has a
signature (rebalance calendar, urgency profile, basket shape,
participation tolerance) learnable from their own execution
history; pre-positioning liquidity forecasts for recurring baskets
(the desk knows Tuesday's basket is coming — inventory and locates
staged); per-client cost curves by participation rate,
regime-conditioned; CROSS-CLIENT NETTING FORECASTS (predict when
client A's monthly basket offsets client B's — schedule the cross);
capacity analytics (impact decay per client as their AUM grows).
**AI:** pattern-mining execution histories is the canonical ML-on-
own-data problem — rich, labeled, recurring; anomaly detection when
a basket deviates from fingerprint (strategy change = client
conversation); schedule optimization under the client's constraint
set; LLM renders the recurring recaps. **Ports:** the whole
TCA/wheel layer, netting detector, cost model. **Insight quality:
HIGHEST — recurring flow means training data compounds.**

## 2. Transitions

**Analytics:** legacy→target overlap and in-kind maximization
(combinatorial matching — every share transferred in kind is cost
avoided); interim-exposure risk schedule (minimize the days of
unintended factor bets); liquidity-tiered tranche plans; stamp/tax-
aware sequencing (HK stamp, TW tax quirks); INFORMATION-LEAKAGE
measurement (did the market move against the transition after day
1? — measurable, rarely measured); pre-trade cost bands graded
against realized (T-Charter discipline). **AI:** the matching
problem is pure optimization; LLM extracts constraints from IMA
documents (restricted lists, ESG screens) — hours of legal reading
to minutes; leakage detection = event-study machinery pointed at
our own footprint; Monte Carlo scenario bands from the event
library. **Ports:** window planner, bounded-fill simulator, blind-
profile machinery, the PIT discipline itself (a transition IS a
private index event).

## 3. Cash-flow rebalances

**Analytics:** the month-end map (we measured the rhythm) —
per-market month-end flow calendars with expiry collisions flagged;
client inflow/outflow FORECASTING from their own history + fund-
flow data; optimal equitization (futures first vs cash basket —
basis vs impact trade-off, per size); drift-band trigger modeling
(predict WHICH clients rebalance after a 3% equity move — the
de-facto index event nobody announces). **AI:** flow forecasting;
auto-generated month-end playbooks conditioned on the calendar;
the drift-trigger model is a genuine predictive product ("post-5%
rally, expect $X of allocation-rebalance supply this month-end").
**Ports:** calendar machinery, flow heuristics, exposure scheduler.

## 4. Asset-allocation restructures

**Analytics:** SIMILARITY RETRIEVAL — "this basket resembles the
March de-grossing wave; realized costs were X" (embedding baskets
by composition/liquidity/factor shape against the desk's history);
liquidity-window advisory for discretionary timing (the mid-month
dead zone is cheap FOR A REASON — quantify it); de-grossing stress
maps (if this client's unwind is crowded with other HF unwinds,
who else holds this? — positioning data again); pair-basket hedge
ratios and cash-neutral sequencing. **AI:** basket embeddings +
nearest-neighbor cost retrieval is the killer app here — turns the
desk's history into a queryable cost oracle; LLM turns the
retrieval into the client note. **Ports:** crowding layer, impact
models, factor exposure analytics.

## 5. ETF-linked flow

**Analytics:** creation/redemption NOWCASTING from premium/discount
+ secondary volume (predict tonight's AP baskets before they
arrive); the 0050 paired-block proxy generalized per ETF complex;
in-kind vs cash-create cost comparison for issuers (a pitchable
study); MM inventory/hedge analytics; local-complex rebalance
calendars (TW high-div ETFs — we identified these as market-moving
events in their own right). **AI:** the premium/discount → flow
nowcast is a clean supervised problem with daily labels; anomaly
alerts when a complex's arb band widens (inventory opportunity).
**Ports:** auction studies (ETF rebalances print like mini index
events), event calendar, block-trade parser.

## 6. Derivative-linked baskets

**Analytics:** EFP/basis fair-value monitors (carry vs traded
basis, flag rich/cheap switches); expiry-week flow forecasts from
open-interest structure; **DIVIDEND-POINT FORECASTING per index**
— the sleeper product: ML on announcement history + payout policy
beats vendor consensus often enough to matter for futures fair
value; roll-cost calendars per index. **AI:** dividend forecasting
is a genuine ML edge product; expiry-pin analytics from OI. 
**Ports:** calendar machinery, TAIFEX/SGX data layer (planned),
the run-sheet discipline for expiry days.

## 7. Event-driven misc

**Analytics:** the corporate-action radar generalized — tender
feasibility and odd-lot arbitrage screens, spin-off INDEX-TREATMENT
prediction (when does the provider add spinco? our rules engine
domain exactly), share-class conversion flow maps, dual-listing
migration liquidity tracking (where does the volume actually move,
week by week — measurable from our data layers). **AI:** LLM
circular parsing (BUILT — Reg-Watch), precedent retrieval over the
case library ("last five Taiwan tenders: terms, timelines, fill
rates"). **Ports:** Reg-Watch, CA rule, event-print detector.

## The cross-cutting answer on AI

Three AI modes recur, in descending reliability:
1. **Parse & retrieve** (LLM): circulars, IMAs, precedents —
   deployed today, human-gated. Highest confidence.
2. **Pattern & predict** (ML on own flow + public archives):
   fingerprints, nowcasts, dividend points, drift triggers — the
   desk's proprietary data is the moat; every model graded like
   the rebalance engine.
3. **Optimize** (deterministic solvers, AI-assisted): matching,
   scheduling, netting — solvers do the work, AI frames inputs.
LLMs still never rank or decide; every output traces; misses ship.
The rebalance engine was the proof-of-concept for the pattern —
these seven are the rollout, ordered by data-richness: 1, 5, 6
first (recurring, labeled), 2, 3 next, 4, 7 opportunistic.
