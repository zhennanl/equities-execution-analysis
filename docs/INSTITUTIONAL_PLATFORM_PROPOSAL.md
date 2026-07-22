# From Prototype to Institutional Platform — Feasibility & Value Proposal

*2026-07-08. Evaluates porting this agent-based design into an institutional
execution business (GSET/CLSA-style). Organizing principle: **mirror the desk's
existing workflow and add leverage inside it — never add a new screen that
competes with the OMS/EMS.** Companion docs: `GSET_ROLE_AUTOMATION_ANALYSIS.md`
(role mapping), `TRADER_WORKFLOW_DESIGN.md` (trader UX), `INTERVIEW_PREP.md`
(design philosophy).*

---

## 1. Where each agent already sits in the institutional workflow

The prototype's agents are not an invented pipeline — they are the desk's
actual division of labor, encoded. That is the core feasibility argument:
adoption asks nobody to change *what* they do, only how fast the analytical
layer underneath them runs.

| Desk function (who does it today) | Daily reality | Prototype module | Institutional gap to close |
|---|---|---|---|
| Index research analyst — tracks review calendars, forecasts adds/deletes | Manual spreadsheets, provider notices, email distribution | Agent 12 (calendar + announcements), candidate-radar spec | Official constituent/weights files (licensed), not scraped pages |
| Pre-trade consultant — sizes flow, estimates cost, proposes strategy | Ad-hoc per client request; hours per name | Event study + insights + expected-move calculator | Licensed tick/EOD data; client-mandate metadata from CRM |
| Program/PT desk — executes the basket on the day | EMS blotter, exceptions only, seconds per decision | Basket mode + verdict banner + trade cards + playbooks | FIX staging into the EMS; real-time fills feedback |
| Index/rebalance strategist — decides auction vs pre/post split | Experience + desk memory, rarely written down | Agent 14 frontier (S1–S4) + conditional playbooks | Calibration on the desk's own fills, not public proxies |
| TCA team — post-trade attribution, client reviews | Vendor TCA + internal spreadsheets, quarterly packs | Agent 6 TCA + cost-model regression + A/B-with-controls | Order/fill warehouse integration |
| Best-ex / compliance committee — evidences strategy choice | Manual narrative assembly after the fact | Verdict + playbook + thresholds are already a written record | Immutable storage, retention, entitlements |
| Critic / risk oversight | Senior trader eyeballing the blotter | Agent 8 pattern: flag, never silently override | Real-time alerting hooks |

## 2. Feasibility assessment, dimension by dimension

**Methodology — carries over as-is (LOW risk).** Every number is deterministic,
literature-anchored Python with pinned regression tests (142 passing). Nothing
in the math assumes retail data; the estimators upgrade transparently when fed
better inputs. The event-study → insights → strategy-frontier chain is exactly
the pre-trade analysis a consultant produces manually today.

**Data — the real cost line (MEDIUM risk, well-trodden).** Replace yfinance
with the feeds the desk already licenses: official index provider constituent
and weights files (kills the biggest prototype limitation — user-supplied
weights/AUM become computed), tick history from the internal kdb+/OneTick
store, real-time auction imbalance feeds (NOII, HKEX CAS, ASX/TSE equivalents)
for the live-day mode the prototype only specifies. No *new* procurement is
likely needed for phase 1 — EOD + constituent files are already on the desk.

**Technology — straightforward port (LOW/MEDIUM risk).** The agents are pure
functions with typed dataclass I/O and an orchestrator that degrades
gracefully — they containerize into services without redesign. Streamlit UI
becomes three thin surfaces instead of one app: (a) an analyst workbench,
(b) cards/blotters pushed INTO existing surfaces (EMS panel, desk chat,
morning-pack email), (c) an API the TCA warehouse and client portal call.
Schedule CSVs become FIX NewOrderSingle/List staging. The event library
(JSON) becomes a proper database table with versioning.

**Governance — manageable by design (MEDIUM risk, differentiator if done
right).** Three properties the prototype already has map directly onto model
-risk expectations: deterministic reproducible outputs (auditable), thresholds
that always display their source and n (challengeable), and the critic pattern
— the system flags, a human decides, nothing silently overrides. Two things to
add: model inventory/validation docs per agent, and information-barrier review
of the crowding analytics (see §4, "compliance framing").

**Organization/adoption — the decisive dimension.** The design principle that
makes this feasible: every output lands where the user already looks. Traders
get a ranked exception blotter and one-line verdicts, not a new dashboard;
sales get client-ready cards; compliance gets an audit trail generated as a
by-product. Nobody's workflow is replaced; each step is pre-computed.

## 3. The efficiency proposals (ranked, with the metric each moves)

**P1 — The overnight event-pack factory.** Chain what exists: review calendar →
candidate radar → batch event studies → basket blotter → per-name trade cards
and playbooks, run as a scheduled job the night before and pushed to desk chat
by 7am. *Metric: pre-trade prep per review cycle drops from ~3–4 analyst-hours
× top-20 names to minutes × the full ~200-name program; coverage of the
long-tail names goes from zero to complete.*

**P2 — Best-execution documentation as a by-product.** Every verdict, playbook
threshold, and the data behind them is already a structured record. Persist it
immutably per order and the quarterly best-ex pack assembles itself: "strategy
chosen, evidence at decision time, triggers agreed, outcome vs expectation."
*Metric: best-ex narrative assembly (today hours per client per quarter) → 
generated; 100% of rebalance orders documented at decision time, not
reconstructed after.*

**P3 — Calibration on the desk's own prints.** Swap the event library's public
proxies for the desk's fill history: per-market η, reversal fractions, auction
capacity curves, add/delete asymmetry — versioned like any model, refreshed
every event, with the same "n and source always displayed" rule. This is the
moat: no vendor TCA has the desk's own rebalance fills. *Metric: pre-trade
estimate error vs realized (predicted-vs-realized shortfall tracking error)
measured and shrinking quarter over quarter.*

**P4 — A/B the strategies, not just the algos.** The cost-model machinery
(regression with condition controls) already built for algo A/B extends
directly to S1–S4 across the event library: "does pre-positioning beat the
close, net of size, volatility, and crowding tier?" — GSET's signature
deliverable, applied to the rebalance business. *Metric: strategy defaults
per market/client-mandate become evidence-based and re-fitted per cycle.*

**P5 — Client-tier scalability for sales.** Auto-generated pre-trade cards
(per client mandate: tracker vs cost-minimizer) let sales-traders service the
long tail of passive clients that today get generic coverage. *Metric: pre-
trade pitches per salesperson per review cycle; response latency on client
"what would you do with my flow" queries: same-day → minutes.*

**P6 — LLM synthesis layer, guard-railed.** Keep every P&L-relevant number
deterministic; add an LLM layer that (a) drafts the client-facing narrative
from the structured outputs, (b) answers free-form follow-ups ("why not more
in the auction for this name?") by citing the computed evidence, (c)
reconciles multiple critic findings into one prioritized note. The LLM never
generates a number — it narrates numbers that exist. *Metric: consultant time
per client note; consistency of narratives across the team.*

**P7 — Live-day escalation loop.** With real imbalance feeds: volume-run-rate
vs expected, revised auction capacity, and RAG re-flagging during T-day —
alerts INTO desk chat with the Agent-8 rule (flag, don't override). *Metric:
time-to-detect a stressed auction; avoided worst-decile prints.*

## 4. Risks and the honest answers (interviewer-proof)

- **"We already have vendor TCA."** Vendors measure after the fact. This
  decides before, documents at decision time, and calibrates on our own flow.
  It complements the vendor number (and can ingest it as a benchmark).
- **Compliance framing of "crowding"/anticipatory analytics.** Everything here
  is agency-side: optimizing execution of a client's own mandated flow and
  characterizing market conditions from public data. No client-flow signals
  cross information barriers; internal-calibration data is aggregated and
  entitlement-controlled. This framing is designed in, not bolted on.
- **"LLM risk in a trading workflow."** The LLM is confined to narration over
  deterministic outputs (P6); the cost path stays assert-able Python. This is
  the same division the prototype already enforces.
- **Model risk.** Deterministic, versioned, source-labelled thresholds; pinned
  regression tests; critic-flags-human-decides. The model-validation write-up
  is largely already written in the repo's research docs.
- **Adoption risk.** Mitigated by the no-new-screens rule and by phasing
  (below): value lands first where zero integration is needed (morning pack in
  chat/email), integration follows demand.

## 5. Phased roadmap

- **Phase 1 (0–3 months) — analyst tool on licensed EOD data.** Port agents
  to internal data APIs; constituent/weights files replace user inputs;
  overnight event-pack job (P1) delivered via chat/email; event library on the
  internal DB. No EMS integration yet — zero adoption friction, immediate
  hours saved.
- **Phase 2 (3–9 months) — desk workflow integration.** FIX staging of
  schedules; blotter panel in the EMS; best-ex record store (P2); calibration
  switched to desk fills (P3); strategy A/B with controls (P4); client cards
  for sales (P5).
- **Phase 3 (9–18 months) — live-day + client-facing.** Real-time imbalance
  ingestion and the escalation loop (P7); LLM narration layer with guardrails
  (P6); client portal exposure of pre/post-trade packs.

## 6. The one-paragraph pitch

The prototype proves the workflow end-to-end on free data: calendar → event
study → crowding and flow calibration → strategy frontier → trade card,
playbook, and exception blotter — deterministic, tested, and honest about its
boundaries. Institutionally, the same agents slot one-for-one into the desk's
existing division of labor; the port replaces data feeds and delivery
surfaces, not methodology. The value is leverage and evidence: full-program
pre-trade coverage by 7am, strategy choices documented for best-ex at decision
time, and a cost model that learns from every event the desk trades — while
every number stays reproducible and every automated judgment arrives as a flag
for a human, never a silent override.
