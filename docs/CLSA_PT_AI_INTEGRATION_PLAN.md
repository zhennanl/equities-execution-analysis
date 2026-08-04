# AI Integration Plan — CLSA Program Trading Desk
## Modeled on the Jefferies/AWS trade-assistant pattern, grounded in what this project has already proven

*Session 9i (2026-08-03). Sources: AWS/Jefferies engineering post
(Jul-2026) + peer-deployment scan + execution-AI landscape (links in
§7). Purpose: a proposal-grade plan Bill can present — what to build,
in what order, with governance that survives a trading-floor
compliance review.*

---

## 1. What Jefferies actually built — the anatomy, distilled

The [AWS post](https://aws.amazon.com/blogs/machine-learning/building-trade-assistant-how-jefferies-optimized-front-office-trading-operations-with-ai/)
describes an equities front-office "trade assistant":

| Layer | Jefferies choice | The portable principle |
|---|---|---|
| Entry point | Widget EMBEDDED in the existing desk BI (Global Flow Monitor) | Meet traders inside the tool they already stare at — never a new destination app |
| Orchestration | Strands agent SDK + Claude on Amazon Bedrock | An agent harness plans, calls tools, reflects; model-agnostic platform |
| Data access | One MCP tool PER data source (in-memory grid, SQL stores, FIX message files) | Each source wrapped as a tool → extensible, testable, swappable |
| Schema grounding | Bedrock Knowledge Base RAG over table schemas / column defs / query patterns | The LLM writes SQL from RETRIEVED schema context, not memory — kills schema hallucination |
| Serving | NL → SQL → in-memory execution | Latency matters: pre-loaded grids, not cold warehouse queries |
| Trust & control | Guardrails, PII filtering, ROW-LEVEL entitlements injected into SQL, full conversation audit logs | Entitlements enforced in the executor, not the prompt |
| Hallucination stance | **LLM never renders charts** — it generates queries; deterministic viz engines draw | Separate language understanding from number production |
| Languages | Python for LLM/experimentation, Java for high-throughput processing | Two-speed stack is fine; don't force one |

Reported impact: traders self-serve analyses that previously took an
IT dashboard queue days; IT freed from repetitive dashboard builds;
data access democratized with audit intact.

**The most important sentence in the post is the hallucination one.**
Their "LLM understands, deterministic engines compute" split is
exactly this project's standing invariant (LLMs never rank or decide;
engines produce numbers; everything traces). Jefferies independently
converged on it in production — that's the strongest external
validation of our architecture we've seen.

## 2. Landscape — who else is doing what

- **Morgan Stanley**: GPT-4 advisor assistant (98% adoption), then
  [AskResearchGPT](https://www.cnbc.com/2024/10/23/morgan-stanley-rolls-out-openai-powered-chatbot-for-wall-street-division.html)
  for institutional securities — NL over 100k+ research docs; ~3x
  the query volume of the pre-LLM tool. Lesson: retrieval-over-
  proprietary-corpus is the fastest adoption win.
- **Goldman Sachs**: [GS AI Assistant](https://www.cnbc.com/2025/01/21/goldman-sachs-launches-ai-assistant.html)
  rolled from 10k to ~46k staff — multi-model behind an internal
  security layer. Lesson: platform + entitlements first, use cases
  second.
- **JPMorgan**: LLM Suite at 200k+ employees, 400+ use cases;
  IndexGPT for thematic idea retrieval. Lesson: a shared horizontal
  layer with desk-level verticals on top.
- **Execution-specific**: [Bloomberg pre-trade TCA](https://www.bloomberg.com/professional/insights/trading/pre-trade-transaction-cost-analysis-turning-trading-analytics-into-better-execution-decisions/)
  pushes pre/in/post-trade continuity; EMS vendors ship NL pre-trade
  scenario copilots ([TS Imagine](https://tsimagine.com/insights/best-execution-ems-2026-compliance-alpha/));
  [KX/NVIDIA blueprints](https://www.businesswire.com/news/home/20260311726438/en/)
  for research assistants + signal agents over tick stores;
  algo/RFQ-selection models are the industry's "Level 2" frontier
  ([FX Algo News](https://fxalgonews.com/investigating-the-evolving-ai-tca-and-algo-trading-landscape/)).
- Consensus across all of it (and [Traders Magazine](https://www.tradersmagazine.com/featured_articles/agentic-ai-moves-closer-to-the-trading-desk-but-humans-remain-in-control/)):
  **humans stay in control; agents assist decisions, never execute
  autonomously.** No one credible is wiring an LLM to order entry.

Gap in the landscape worth saying out loud in a proposal: everyone
built HORIZONTAL assistants (query your data, search your docs).
Nobody has published a **workflow-vertical agent for a PT desk's
actual revenue events** — index rebalances, transitions, month-end.
That vertical is exactly what this project already prototyped. The
pitch is: CLSA skips the me-too horizontal race and leads on the
vertical where an Asia agency desk actually differentiates.

## 3. Design principles (Jefferies lessons + this project's invariants)

1. **Embed, don't build a destination.** The assistant lives in the
   desk's existing blotter/monitor UI (CLSA equivalent of GFM) and
   in chat where the desk already talks.
2. **Deterministic core, linguistic shell.** Engines compute every
   number (predictions, footprints, cost tables); the LLM parses
   intent, retrieves, orchestrates, and drafts prose. LLM output
   never becomes a number a client sees.
3. **Tool-per-source (MCP).** OMS/EMS blotter, FIX logs, TCA store,
   client flow history, index-event engine, market data — each a
   separate tool; the agent composes them.
4. **Entitlements in the executor, audit on every turn.** Row-level
   client filters injected below the agent; full conversation logs;
   PII/name masking for cross-client questions (a PT desk's walls
   are BETWEEN clients).
5. **Everything gradable.** Every prediction and estimate ships with
   its later grade — the desk's credibility artifact (this is our
   platform's differentiator; no peer post mentions grading).
6. **In-memory for the intraday path; batch for the archive.**
7. **Expect usage to drift; instrument from day one** (Jefferies'
   observability lesson).

## 3b. Narrowing it: cash-equities assistant → PROGRAM TRADING assistant

Jefferies built for a general equities desk — single-stock flow,
reactive intraday questions. A PT desk is structurally different on
every axis the assistant design touches:

| Axis | Cash desk (Jefferies) | PT desk (CLSA) |
|---|---|---|
| Unit of work | The stock | **The basket/program** — 50-500 lines with one instruction, one benchmark, one client conversation |
| Time structure | Reactive, intraday | **Campaign-shaped and calendar-known**: rebalances/transitions/month-end are scheduled weeks ahead; the desk works T-10 → T → T+1 |
| Benchmark | Arrival/VWAP mix | **Close-dominated** (MOC obligation), auction physics, tracking-vs-arrival trade |
| Risk view | Name inventory | **Portfolio residuals**: side imbalance, factor/sector skew, futures hedge, completion risk on unfilled lines |
| Client artifact | Color, IOIs | **Contractual documents**: pre-trade cost estimate in bps (often a principal bid), post-trade TCA report — these WIN or LOSE the next order |
| Cross-flow | Rare | **Netting/crossing across client baskets** is core desk P&L |
| Asia specificity | one close | **A cascade of closes** (TW 13:30, JP 15:30, HK 16:08/10, IN 15:30…) with per-market cutoffs, limit bands, lot rules |

Same plumbing (agent + tools + schema-RAG + entitlements), but three
things change: the **semantic layer** (a basket ontology —
program_id → waves → child orders — so NL questions aggregate
correctly by default), the **proactivity model** (a calendar-anchored
agent that knows "today is T-3 for MSCI Aug" and opens with the
checklist, versus a purely reactive Q&A box), and the **outputs**
(client-grade artifacts, not charts).

The six PT-specific agent behaviors, in build order:

1. **Inbound basket profiler.** A client file lands; the agent
   diagnoses it before anyone trades: overlap vs known event lists
   (is this the MSCI cohort? a transition? month-end?), liquidity
   tiering in ADV-days, borrow flags on sells, limit-band and lot
   quirks per market, footprint vs expected auction size, similarity
   to past programs and their realized costs. Output: a one-screen
   profile in the seconds between file arrival and the client call.
2. **Campaign calendar copilot.** Event-anchored, not query-anchored:
   T-n checklists (locates by T-5, FX by T-2, files reconciled T-1,
   auctions staged), cutoff cascade countdowns across Asian markets
   on T-day, and the "what changed overnight" brief each morning of
   a window (short builds, index notices, boundary names).
3. **Basket Q&A** (the Jefferies clone, re-keyed): "which lines in
   wave 3 are behind POV target", "residual factor skew if I stop
   now", "adds where our footprint exceeds 25% of expected auction",
   "how did client A's last four rebalance baskets realize vs our
   estimates".
4. **Pricing assistant.** Drafts the pre-trade estimate / principal
   bid support: engine cost model + event-class priors (the decade
   tables) + crowding read + risk charge — trader adjusts, artifact
   goes out with methodology attached. Never auto-sent.
5. **Netting scout.** Continuously matches inbound/working baskets
   across clients for crossable flow within compliance rules;
   proposes the cross, sized and priced, to the trader.
6. **Debrief writer.** T+30min post-close: TCA vs estimate,
   auction anatomy per market, discretion counterfactual grades,
   client-ready draft (human gate). Feeds the grading archive that
   becomes next quarter's marketing.

Example query set for the demo script — the PT tell is that none of
these are single-stock questions: "profile this file", "what's my
worst borrow on the sells", "if TW indicative volume runs thin at
13:28 what's my playbook", "cross-check: has this client's basket
shape changed vs their fingerprint", "draft the debrief for the
Aug-31 print".

## 4. The phased plan

### Phase 0 — Foundations (weeks 0-6)
Data inventory and tool wrapping: blotter/positions (in-memory),
executions + FIX logs, TCA history, client flow history, index-event
data layer (the public archives this project already maintains:
answer keys, crowding, auction stats). Schema knowledge base built
from day one (table defs + curated query patterns — the Jefferies
RAG trick). Entitlement map: which trader sees which client rows.
Deliverable: 5-6 MCP tools + governance memo.

### Phase 1 — Basket Q&A assistant (weeks 6-14) — the Jefferies
### pattern re-keyed to the basket ontology (§3b behaviors 1+3)
NL over desk data grouped by program/wave/child by default, embedded
in the desk monitor, plus the inbound basket profiler: "profile this
file", "which lines in wave 3 are behind POV target", "slippage vs
estimate on yesterday's baskets by client".
NL → schema-RAG → SQL → in-memory execution → deterministic charts.
This is the proven, de-risked pattern — it exists in production at a
peer and its value is measured in dashboard-queue hours eliminated.
Success metric: queries/trader/day, dashboard tickets avoided.

### Phase 2 — The PT vertical: event-lifecycle agents (weeks 10-24)
### (§3b behaviors 2, 4, 5, 6: calendar copilot, pricing assistant,
### netting scout, debrief writer)
This is where CLSA leads instead of follows — agents for the desk's
revenue events, prototyped end-to-end in this project:
- **Step-1 agent**: index-review prediction pack on demand
  (engine-computed calls + crowding + flow estimates), rendered as
  client-ready marketing notes with methodology and PRIOR GRADES
  attached (TW 17/17 PIT May-2026; graded misses shipped).
- **Step-2 agent**: window planner — liquidity/risk sheet, ADV-days,
  auction footprint, borrow, start schedule, discretion matrix with
  written rationale; daily window replay with PIT discipline.
- **Step-3 agent**: T-day cockpit — run-sheet, cutoff countdowns,
  indicative-auction reads (THIN/RICH), limit-lock contingencies
  (baseline: ~2-3% of the TW tape touches a band daily, ~2x on
  print days; print-day locks favor the obligated side).
- **Step-4 agent**: same-night TCA debrief vs pre-trade estimate +
  discretion counterfactual grading + client debrief draft
  (human-approved before send).
Extension beyond rebalance per the flow taxonomy: month-end
playbooks, transition planning (in-kind matching + IMA constraint
extraction), ETF creation/redemption nowcasts.

### Phase 3 — Pattern & predict (months 6-12)
ML on the desk's own flow (the data moat): client basket
fingerprinting and anomaly alerts, cross-client netting forecasts,
drift-trigger month-end supply forecasts, dividend-point forecasts.
Every model graded like the rebalance engine; misses ship.

### Explicitly out of scope (the line that builds trust)
No autonomous order entry, no LLM-generated numbers in client
artifacts, no cross-client information leakage paths, no ungated
client sends. The agent proposes; the trader disposes.

## 5. Why CLSA can move fast: the prototype already exists

Everything in Phase 2 has a working, tested public-data prototype in
this repo (416 green tests): the 8-layer prediction engine with a
decade of graded backtests, the window planner and Time Machine
(structural PIT replay of 38+ events), the auction studies (24.9%
single-print concentration, book-retention edge, limit-lock cases),
the TWAP/VWAP/MOC decade cost tables, and the decade CN/JP/HK window
study. Swap the public-data adapters for desk feeds (institutional
data closes the gaps documented in APAC_DATA_AVAILABILITY.md) and
Phase 2 is an integration project, not a research project. The
honesty machinery — grades, shipped misses, pinned null results — is
precisely the compliance-friendly posture a bank needs.

## 6. Risks & mitigations

| Risk | Mitigation |
|---|---|
| NL→SQL errors on desk data | Schema-RAG + curated query patterns + read-only executor + result-count sanity checks; start with a bounded schema |
| Cross-client leakage | Row-level entitlements injected in executor (Jefferies pattern); client-masked aggregates for desk-wide views |
| Hallucinated numbers | LLM never computes; engines only; client artifacts assembled from engine JSON |
| Adoption failure | Embed in existing UI; seed with the 5 questions each trader already asks daily; measure queries/trader/day |
| Model/vendor lock-in | Agent harness + model-agnostic gateway (Bedrock-style); tools are the stable interface |
| Compliance discomfort | Full audit logs, human gate on all external artifacts, grading culture as evidence of epistemic hygiene |

## 7. Sources

- [AWS: Building trade assistant — Jefferies (Jul-2026)](https://aws.amazon.com/blogs/machine-learning/building-trade-assistant-how-jefferies-optimized-front-office-trading-operations-with-ai/)
- [CNBC: Morgan Stanley AskResearchGPT](https://www.cnbc.com/2024/10/23/morgan-stanley-rolls-out-openai-powered-chatbot-for-wall-street-division.html)
- [CNBC: Goldman Sachs GS AI Assistant](https://www.cnbc.com/2025/01/21/goldman-sachs-launches-ai-assistant.html)
- [ValueAdd: JPMorgan LLM Suite / bank AI spend overview](https://valueaddvc.com/blog/ai-in-financial-services-2026-what-jpmorgan-goldman-and-blackrock-are-actually-doing)
- [Traders Magazine: Agentic AI moves closer to the trading desk, humans in control](https://www.tradersmagazine.com/featured_articles/agentic-ai-moves-closer-to-the-trading-desk-but-humans-remain-in-control/)
- [Bloomberg Professional: pre-trade TCA](https://www.bloomberg.com/professional/insights/trading/pre-trade-transaction-cost-analysis-turning-trading-analytics-into-better-execution-decisions/)
- [TS Imagine: EMS best-execution 2026](https://tsimagine.com/insights/best-execution-ems-2026-compliance-alpha/)
- [KX + NVIDIA agentic blueprints (GTC 2026)](https://www.businesswire.com/news/home/20260311726438/en/)
- [FX Algo News: AI, TCA and algo trading landscape](https://fxalgonews.com/investigating-the-evolving-ai-tca-and-algo-trading-landscape/)
