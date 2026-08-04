# Step-1 Agentic Workflow Design — Order Placement / Pre-Event Marketing
## Jefferies-referenced architecture; demo on public data; institutional path documented

*Session 9i (2026-08-03). Scope = Step 1 of
INDEX_REBALANCE_TRADE_LIFECYCLE.md: Phase 0 winning the trade
(pre-event marketing), Phase 1 terms (the discretion-envelope
negotiation), Phase 2 the order arrives (file intake), Phase 3
acknowledgment (normalize → pre-flight → pre-trade pack → confirm).
Reference: the AWS/Jefferies trade-assistant pattern (agent harness +
tool-per-source + schema-RAG + entitlements + "LLM never computes").*

---

## 1. The design idea in one paragraph

Step 1 is where an agent adds the most leverage per dollar, because
its work products are DOCUMENTS AND DECISIONS, not fills: prediction
packs, envelope term sheets, normalized baskets, pre-flight reports,
acknowledgment notes. Every one of those is "deterministic engine
computes → LLM assembles, explains, and formats → human gates the
send." The Jefferies architecture maps almost one-to-one — with one
substitution: where Jefferies grounds the LLM in a SCHEMA knowledge
base so it writes correct SQL, we ground ours in a METHODOLOGY
knowledge base (the prediction logic layers, metric definitions,
graded history) so it explains calls correctly and never invents a
rule.

## 2. Architecture — Jefferies component → demo → institutional

| Jefferies component | Our demo (public data) | Institutional (CLSA) |
|---|---|---|
| Embedded UI widget in GFM | Chat panel embedded in the Streamlit lifecycle page (Tab 1) | Widget in the desk's blotter/monitor + Bloomberg IB integration |
| Strands agent on Bedrock | Single orchestrator loop on the Anthropic API (tool-use), with a canned-replay mode for offline demos | Agent harness on a model gateway (Bedrock-style), multi-model, firm security layer |
| MCP tool per data source | Python tool registry wrapping EXISTING engines (below) | Same tools re-pointed at licensed feeds + internal stores; genuine MCP servers |
| Bedrock KB: schema RAG | **Methodology KB**: PREDICTION_LOGIC_LAYERS.md, WINDOW_STUDY §0 metric defs, decade cost tables, graded history — embedded for retrieval | Same + internal research, client agreements, compliance manuals |
| Row-level entitlements | Single-user demo: none needed; note in UI | SSO + per-trader client-row entitlements injected in executors |
| Guardrails + PII filter | Invariants enforced in code: numbers only from engine JSON; NO-CALL preserved verbatim; misses always shown | Firm guardrails, PII/name masking on cross-client queries |
| Conversation audit log | Append-only JSONL of every turn + artifact hash | Compliance-grade logging/retention platform |
| In-memory grid | Cached JSON/pandas (already how the platform runs) | kdb/in-memory grid for intraday |

Existing engines that become the tool belt (no rebuild needed):
`review_engine.run_full_review` (predictions), `event_data` crowding
readers, flow estimators, `pre_event_marketing` (packs + grading),
`event_window.liquidity_risk_sheet` (pre-trade pack numbers),
`time_machine` (PIT replay), Reg-Watch registry (pre-flight rules),
`pt_ops.client_file_normalizer` (intake), the answer-key/grades
archives.

## 3. The five agentic workflows (concrete, in build order)

### W1 — Pitch-pack generator (Phase 0, on-demand)
**Trigger:** trader types "Aug QIR Taiwan pack for a TE-constrained
tracker" (or clicks a button).
**Agent plan:** call `run_full_review` for the event → pull crowding
reads per name → pull flow estimates → retrieve the client-type
framing from the methodology KB (MOC-only client vs envelope client
get different emphasis) → attach the PRIOR GRADE summary (17/17 May;
misses listed) → render the marketing note with per-call rationale
citations (logic layer L0-L9 references).
**Efficiency win:** the analyst-day of assembling a pack becomes ~1
minute, and every number carries its methodology citation.
**Human gate:** trader edits/approves before anything leaves.

### W2 — Boundary-watch briefer (Phase 0, scheduled)
**Trigger:** scheduled daily during review season (our Aug-11
protocol, agentified).
**Agent plan:** refresh caps → diff today's calls vs yesterday →
flag names that crossed a buffer, new entrants, crowding regime
changes → draft a 5-line "what changed and why" morning note; alert
only when the diff is non-empty.
**Efficiency win:** the desk never gets surprised by a migration;
the agent watches the boundary so nobody re-runs screens manually.

### W3 — Envelope advisor (Phase 1, on-demand)
**Trigger:** "client asks what discretion to give us on the TW
basket — what do we propose?"
**Agent plan:** classify the basket's event class (provider ×
market × side mix) → pull the decade counterfactual tables (TWAP/
VWAP/MOC study; window studies) → compute the expected value of an
envelope FOR THIS CLASS (e.g. FTSE adds: window-VWAP beat close
−164 bps median, 60% win rate; FTSE deletes: MOC won) → draft a
term-sheet paragraph: proposed envelope %, expected TD gain, the TE
cost in quadrature bps, and the honest caveat set.
**Efficiency win:** the terms conversation is armed with measured
evidence instead of instinct — this is the §3b pricing assistant's
Step-1 face, and it's the artifact that converts MOC-only clients.

### W4 — Intake-and-acknowledge agent (Phases 2-3)
**Trigger:** a basket file arrives (CSV/Excel drop in the demo; FIX
NewOrderList / portal / chat attachment institutionally).
**Agent plan:** parse ANY reasonable format into the canonical
basket (LLM-assisted column mapping with a deterministic validator —
the LLM proposes the mapping, code verifies row counts/notional
reconcile before anything proceeds) → run compliance pre-flight
(restricted list, foreign-room flags, odd lots, limit-band risk
names, market-access flags for new adds: TW foreign-investor ID,
Connect eligibility) → build the pre-trade pack (liquidity buckets,
ADV-days, footprint, cost estimate w/ event-class priors) → draft
the acknowledgment note (line count, notional, benchmark, per-bucket
strategy, EXCEPTIONS list) → audit-log everything.
**Efficiency win:** the ingest-normalize-preflight-acknowledge loop
(30-60 min of careful manual work, error-prone under time pressure)
becomes minutes with a machine-checked exceptions list. This is the
§3b inbound basket profiler.
**Hard rule:** the deterministic validator, not the LLM, decides the
file parsed correctly; ambiguity → human, never a guess.

### W5 — Methodology Q&A copilot (all phases, conversational)
**Trigger:** any question in the chat panel: "why is 1101 a delete
call?", "how did we grade in May?", "what does the crowding HIGH tag
mean?", "what happened last time a client gave us 30% discretion on
an MSCI delete?"
**Agent plan:** retrieve from the methodology KB + query engine
output JSON + grades archive → answer with citations to the specific
logic layer / study section; numbers quoted only from engine output.
**Efficiency win:** every trader can field client methodology
questions at sales-trader depth; the Jefferies "3x query volume"
effect applied to our documented-rules corpus.

## 4. Components to implement (demo scope)

1. **Orchestrator** (`agents/step1_agent.py`): Anthropic tool-use
   loop; system prompt = invariants + tool briefs; max ~8 tool calls
   per turn; canned-replay mode (recorded tool results) so the demo
   runs offline and deterministically.
2. **Tool registry** (`agents/agent_tools.py`): thin JSON-in/JSON-out
   wrappers over the existing engines listed in §2 — each tool
   returns numbers + provenance (which cache, which rule version).
3. **Methodology KB**: chunk + embed the docs (logic layers, metric
   defs, study findings, graded history); local vector store (e.g.
   simple cosine over sentence embeddings — no infra dependency);
   retrieval returns doc + section anchors for citation.
4. **Artifact renderer**: templates for the four Step-1 documents
   (pitch pack, envelope term sheet, pre-flight report,
   acknowledgment note) filled from engine JSON; LLM writes only the
   connective prose fields.
5. **Audit log**: append-only JSONL per session (turn, tools called,
   artifact hashes, human approve/reject).
6. **UI embedding**: chat panel inside lifecycle Tab 1 + a file-drop
   zone for W4; artifacts render as downloadable markdown.
7. **Scheduler** (W2): reuse the existing session cadence — in the
   demo, a "simulate next morning" button; institutionally, cron.

## 5. What changes with institutional access (document now, build later)

| Area | Demo reality | With CLSA access |
|---|---|---|
| Index notices | Scraped/archived public PDFs (MSCI/TIP) | Licensed provider feeds (MSCI/FTSE subscriptions) — W2 alerts become minutes-after-publication, pro-forma files replace our parsing |
| Crowding | Public shorts/foreign flows (TWT93U, SFC, exchange files) | + Internal flow, axe books, PB data where permissioned — crowding layer gains intraday resolution |
| Client context | Client-TYPE archetypes (tracker/envelope/HF) | CRM + agreement store: real mandates, TE budgets, past envelopes — W1/W3 personalize to the actual client, with entitlements |
| Intake | CSV/Excel drop | FIX NewOrderList listener + portal + IB chat parser; OMS write-back of the acknowledged basket |
| Pre-flight | Public restricted-list + rules registry | Firm compliance engine integration (restricted, MNPI walls, position limits, foreign-room realtime) |
| Cost model | Event-class priors from public studies | Calibrated on the desk's own fills (the data moat); per-client realized-vs-estimate curves |
| Serving | Cached JSON, single user | In-memory grid, SSO, entitlements, HA |
| Governance | Code-enforced invariants + JSONL log | Firm guardrails, model gateway, compliance retention, model-risk sign-off of every deterministic engine |

## 6. Invariants (unchanged from the platform, enforced in the agent)

Numbers come only from engine JSON — the LLM never computes or
adjusts one. NO-CALL ships as NO-CALL. Misses appear in every grade
summary. Every artifact carries methodology citations + rule
version. Every client-bound artifact passes a human gate. Every turn
is logged. If a tool fails, the agent says so — no silent fallback.

## 7. Demo build order (proposed)

1. Tool registry + orchestrator with canned replay (2 sessions)
2. W1 pitch-pack generator end-to-end in the UI (the wow moment)
3. W5 methodology Q&A (small KB first: logic layers + grades)
4. W4 intake agent on a synthetic client CSV (file-drop demo)
5. W2 scheduled briefer ("simulate next morning" button)
6. W3 envelope advisor (reads the decade tables)
Steps 2-3 alone are a compelling CLSA demo; 4-6 complete Step 1.
