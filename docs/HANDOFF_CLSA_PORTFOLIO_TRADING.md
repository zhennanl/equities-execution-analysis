# CONTEXT CAPSULE — CLSA Portfolio Trading Interview

*Chat context filtered and re-angled for an interview with CLSA's (CITIC
CLSA) portfolio trading team. Companion to HANDOFF_2026-07-15.md (full
platform state); this file is what matters for THIS interview. 2026-07.*

---

## 1. The role reframe (read this first)

The platform was built while prepping for a GSET Execution Solutions role —
single-stock electronic execution advisory. **Portfolio trading is a
different lens on the same machinery:** the unit of work is a BASKET, and
the risk axes change:

| Single-stock electronic | Portfolio trading |
|---|---|
| One order vs arrival/VWAP | Basket vs benchmark print (often the close) |
| Impact vs timing risk | Cost vs **tracking error** frontier |
| Algo choice / wheel | Wave scheduling, auction participation, residual management |
| Venue/SOR | Cross-market session alignment, FX, settlement cycles |
| Order-level TCA | Basket-level TCA + side-imbalance / exposure drift |

CLSA is an **agency** franchise (Asia's largest independent brokerage,
CITIC-owned, HK HQ, 21 locations) — pitch everything as *client advisory
and evidence*, not prop. Their own materials emphasize pre-/intra-/
post-trade tools and STP for portfolio trading — exactly the platform's
shape (pre-trade desk pack → live monitoring → post-trade TCA → QBR).

## 2. Lead assets (in this order)

1. **The Invesco / TWSE ETF-tracking project (real production experience —
   lead with this).** Traded index-tracking baskets against benchmark
   closes; handled Taiwan ±10% price limits (limit-lock vs retreat),
   +2% T+1 completion rules, tracking thresholds; the Millennium loss
   post-mortem story. This IS portfolio trading, done for real. Review:
   `docs/ORIGINAL_TWSE_PROJECT_REVIEW.md`.
2. **Index Rebalancing module (Page 2).** The PT desk's biggest recurring
   event. S1–S4 strategy frontier (100% MOC tracker vs pre-position vs
   post-event completion vs announcement-anchored) quantified per event
   from data — the Madhavan cost-vs-tracking-error frontier is the client
   deliverable. Crowding score, expected move, close-auction share vs
   capacity, best-ex record store. Literature anchors ready:
   Petajisto (21–28bp hidden indexer cost), Madhavan (Russell recon),
   Greenwood-Sammon (disappearing index effect — effect shrank, FLOW
   didn't). `docs/INDEX_REBALANCE_RESEARCH.md`.
3. **Program Trading Desk module (Page 3).** Built explicitly from a
   program-trading JD: APAC sessions/regulations, settlement/recon,
   program blotter, basket mode. Market mechanics bank: Taiwan
   limit-lock/retreat, China A T+1 + SPSA + front-loaded volume curve,
   HK CAS/VCM + stamp duty, Japan special quotes + 15:30 close (Nov-2024
   reform), Korea VI/sidecar/Nextrade. US close mechanics (NYSE 3:50 /
   Nasdaq 3:55/3:58 cutoffs), LULD/MWCB, leveraged-ETF rebalance math
   A·(L²−L)·r.
4. **Quarterly Client Review module (Page 4).** Agency PT desks live on
   client reviews. Six exhibits: flow profile → cost distributions →
   decomposition (no verdict below n=5) → difficulty-adjusted ranking
   (regression controls; raw-vs-adjusted rank movers) → outlier Pareto
   (the meeting is about 5 orders, not 500) → trend + recommendations that
   only fire on non-overlapping CIs.
5. **Supporting depth (mention, don't lead):** algo simulator + Perold IS
   attribution reconciling ±0.1bp; markouts/reversion; counterfactual
   impact propagator with sensitivity bands; flow forecast L1–L6b (all
   DM/pinball-gated vs naive — "a model that can't beat the 20-day median
   ships the 20-day median"); kdb+/q + tick-file ingestion (LOBSTER/
   Binance/IEX) behind a source-agnostic MarketData contract.

## 3. Portfolio-trading questions to expect (and platform answers)

- **"Walk me through pre-trade on a 300-name two-sided basket."** Notional
  and %ADV by name; side imbalance and net exposure; cost model per name →
  aggregate; hardest names (high %ADV, wide spread, limit-risk markets)
  drive the schedule; benchmark choice (close vs arrival) sets the
  tracking-vs-cost frontier; auction capacity per market. Platform: basket
  mode + desk pack + Page-3 blotter.
- **"Index rebalance: client wants the close print but hates the cost."**
  S1–S4 frontier per event; quantify crowding (close-volume multiple);
  partial MOC + T+1 completion captures reversal at tracking-error cost —
  show the number, let the client choose; document in best-ex record.
- **"How do you measure PT performance fairly?"** Basket-level slippage vs
  agreed benchmark; difficulty-adjust before ranking (size, spread,
  urgency, market mix — the QBR regression); distributions + outlier
  attribution, not means; n and CIs everywhere.
- **"Taiwan name locks limit-up mid-program?"** Real experience: lock vs
  retreat behavior, queue position value, +2% T+1 completion rule,
  residual management and client comms — the Invesco war story.
- **"Cross-market basket (Japan+HK+Taiwan+India) — what breaks?"** Session
  misalignment, holidays, FX cutoffs, settlement cycles (T+1 vs T+2),
  China A ID markets/SPSA, omnibus vs ID accounts, recon. Page 3 exists
  because of exactly this question.
- **"Futures overlay for interim exposure?"** Honest gap: platform tracks
  it in the gap register (no futures data on free feeds); explain the
  practice (transition-management standard) and where it would slot in.
- **Stats under pressure:** hypothesis tests on strategy deltas (power:
  ~1,760 paired orders for 2bp at σ=30bp — so pool, block, or wait);
  event-study inference with single-firm correction; DM gates; why
  raw algo league tables mislead (OVB) and the regression fix.

## 4. What NOT to lead with

- GSET-specific branding (Sonar Dark X, Sherry-specific prep, GS algo
  names) — the *traits* (outsized-print filtering, dark-patient routing)
  are fine as generic industry practice.
- Single-stock SOR minutiae — secondary for PT; bring it only if asked
  about execution of residuals.
- Don't oversell: simulated fills on historical bars, modeled impact,
  free data. Same honesty culture: "when in doubt between impressive and
  honest, choose honest" — agency brokers audit claims.

## 5. Questions to ask them

- How is the PT desk's pre-trade advisory evolving — do clients consume
  it as reports, API, or embedded in the EMS? (maps to the platform's
  desk-pack/STP angle)
- Around big index events, how does the desk balance its own clients'
  crowding against each other — is there an internal netting/crossing
  conversation? (Sigma-X-style pools exist at CLSA per public materials)
- How much of basket performance review is standardized vs bespoke per
  client — and who owns the difficulty adjustment when clients compare
  brokers? (QBR angle)
- With China A access mechanics (Connect, SPSA, T+1) still evolving, what
  does the desk see as the binding constraint on A-share program flow?

## 6. Assets to bring / demo

- Demo: Page 2 event walkthrough (frontier + crowding + best-ex record) →
  Page 3 basket blotter → Page 4 QBR demo quarter. ~10 min.
- Docs to re-read the night before: ORIGINAL_TWSE_PROJECT_REVIEW.md,
  INDEX_REBALANCE_RESEARCH.md, program-trading sections of
  SESSION_SUMMARY (sessions on Page 3), QBR section (6e), APAC mechanics
  in the question banks (tech bank market-structure tier).
- The interviewer-agnostic stat drills in HANDOFF_STATS_REVIEW.md still
  apply verbatim.

## 7. One-paragraph self-intro (PT-angled)

"I ran index-tracking basket execution in production — Taiwan limit
mechanics, T+1 completion rules, benchmark-close tracking — and then built
an execution analytics platform around exactly that workflow: per-event
rebalance strategy frontiers, an APAC program-trading blotter with
settlement and regulation checks, basket pre-trade cost packs, and a
quarterly client review module that difficulty-adjusts performance before
ranking anything. Everything is statistically gated — models that can't
beat a naive baseline ship the baseline — because agency advisory only
works if the numbers survive audit."
