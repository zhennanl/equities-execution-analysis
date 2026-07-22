# Desk Deployment Plan — From Prototype to Production at a PT Desk

*How to deploy the platform's automations (A1–A11 + cockpit + monitors)
once seated at a desk like CLSA's, with institutional data access. A plan,
not code. Session 6n.*

---

## 0. Guiding principles (say these before the plan)

1. **Shadow first, always.** Every automation runs read-only alongside the
   existing workflow until its outputs have been compared against reality
   for a defined period. Nothing touches order flow in phase one — most of
   these tools never touch order flow at all.
2. **Don't build shadow IT.** A junior dealer doesn't stand up servers. The
   plan works inside sanctioned tools (approved Python environment, Excel,
   the EMS's own automation hooks) and partners with the desk-tech/strats
   team for anything that needs entitlements or infrastructure. The
   prototype's value is that the logic is already written and tested — the
   ask to tech is integration, not invention.
3. **The gates come along.** Every learned model keeps its DM/pinball gate
   against a transparent baseline; every rule table keeps its version hash;
   every artifact stays audit-stamped. These were design choices in the
   prototype precisely so they'd survive a compliance review.
4. **Sequence by risk, not by value.** Read-only utilities first, alerting
   second, anything client-facing last (and through the sales trader,
   never around them).

## 1. Data upgrade map — what institutional access replaces

| Prototype source | Institutional replacement | Used by |
|---|---|---|
| yfinance 5-min bars | Internal kdb+ tick store / Refinitiv Elektron / B-PIPE real-time | cockpit, monitors, cost model (the kdb adapter is already written) |
| Static rule tables (bands, lots, cutoffs) | Exchange parameter files + notices; vendor reference data (lot files per stock, tick tables, tier bands) | limit proximity, lot checks, auction countdown |
| Static 2026 holiday list | Trading-calendar vendor (e.g. Copp Clark) / custodian calendars | settlement, closure warnings, roll plans |
| Prev-close reference for notional conversion | OMS security master + real-time snapshot | file normalizer, pre-open pack |
| Simulated fills / run library | **FIX drop copy from the OMS/EMS** — real parent/child orders, fills, timestamps | TCA, markouts, QBR, learning loops (the single biggest upgrade: every gated model starts training on real data) |
| Client basket CSVs | OMS program-trading module intake + FIX allocations | file normalizer becomes a validation layer on the OMS intake |
| Public short-interest proxies | Official regime feeds (JPX/TWSE/KRX/SFC files, automated) + **PB securities-lending book** (internal, entitlement-gated) | positioning, rebalance-interest monitor |
| Rulebook approximations (GMSR etc.) | MSCI/FTSE index product subscriptions: official review calendars, consultation notices, provisional lists | reconstitution predictor becomes a reconciler: model vs official |
| Synthetic event library | Desk's own history: every past index event with real fills and real close prints | strategy frontier, crowding, learned monitor weights |
| Demo street confirms | Custodian/clearing feeds (SWIFT MT5xx / CTM) | recon break classifier on real breaks |
| No FX leg | Treasury/FX desk rates + cutoff schedule; NDF quotes for TWD/KRW/INR | pre-open pack funding section, exposure scheduler |
| News keyword counts | Bloomberg/Refinitiv news APIs + index-provider notice scrapers; compliance-gated chat only with explicit approval | AI monitor `news` feature |

## 2. Phased rollout

**Weeks 1–2 — map, don't build.** Learn the desk's actual systems: which
OMS/EMS, where the tick store lives, what the recon workflow is, who owns
reference data, what the approved analytics environment is. Deliverable: a
one-page systems map and the entitlement request list. (Also: do the day
job well — credibility is the real currency for everything below.)

**Days 30 — read-only utilities in shadow (lowest risk, fastest value).**
- Client file normalizer run on real incoming files *after* the desk has
  processed them; compare outputs, log discrepancies. Target: catch one
  real issue the manual process missed.
- Pre-open basket pack generated in shadow for one sales trader who opts
  in; iterate on what they actually read.
- Holiday-aware settlement vs the ops team's dates — reconcile daily.

**Days 60 — monitoring goes live-read.**
- Cockpit (limit proximity, auction countdown, attention queue) fed from
  the real-time feed, on the dealer's own screen only. Tune weights
  against a month of real sessions; measure alert precision (what % of
  ALERTs the dealer judged worth seeing — target >70% before anyone else
  sees it).
- Recon break classifier on real custodian feeds in shadow; measure
  auto-clear accuracy vs the ops team's resolution (target: zero false
  auto-clears; then propose tolerance thresholds to ops).

**Days 90 — client-adjacent, through the sales traders.**
- EOD client summary drafts to the sales trader for one pilot client;
  measure edit distance (how much they rewrite) as the quality metric.
- Crossing detector output to the desk head + compliance for the
  mechanism-by-market review; goes live only with their sign-off and only
  as a *flag*, never an automatic cross.
- Index-event radar + reconstitution reconciler (model vs official
  provisional lists) as a weekly desk note.

**Months 4–6 — the learning loops close.**
- Event library accumulates real events → strategy frontier and crowding
  calibrate on desk data; learned monitor weights face their gate against
  real outcomes for the first time.
- QBR module on real fills for the pilot client's quarterly review, run
  side-by-side with the existing deck once before replacing anything.
- Rule-table service proposal to desk tech: versioned reference-data
  store, fed by exchange notices, with the version hash in every audit
  artifact (the prototype's `rules_version` pattern as the spec).

## 3. Governance checklist (before anything leaves shadow)

- **Compliance:** crossing mechanisms per market signed off; information
  barriers documented (aggregated flow only, no client-attributable data
  in any model input; chat/NLP only with explicit approval and never
  client-identifying); best-execution policy alignment for any tool that
  informs routing.
- **Model governance:** every learned component registered with its gate
  report (baseline, test window, DM p-value), version-stamped, re-fit on
  a stated cadence (quarterly, aligned to QBR). A model that stops beating
  its baseline reverts to the baseline automatically — the house rule
  becomes policy.
- **Audit:** the audit-pack/alert-acknowledgment pattern extends to every
  automation; retention per local record-keeping rules (varies by
  jurisdiction — ops/compliance own the schedule).
- **IT/security:** everything runs in the sanctioned environment;
  entitlements requested through the standard process; no personal
  machines, no external data egress.

## 4. Success metrics (report at 90 days)

- Dealer time: minutes saved per pre-open pack vs manual (self-timed).
- File normalizer: real issues caught that manual processing missed.
- Alert precision: % of fired alerts judged useful; zero missed
  limit-locks on monitored names.
- Recon: % of breaks auto-classified correctly; ops sign-off on tolerance.
- EOD drafts: edit distance trending down; sales-trader adoption count.
- Settlement: zero holiday-date errors in the reconciled period.

## 5. Risks and honest expectations

- **Entitlements take longer than code.** PB lending-book access may
  never be granted to a junior dealer — the plan works without it (public
  regime feeds cover the short side).
- **The desk may already have versions of some tools.** Then the
  contribution is the gap analysis and the gates/audit patterns, not the
  tool — find out in weeks 1–2, not after building.
- **Chat NLP is the last thing, not the first.** Highest compliance
  sensitivity, lowest marginal value over news feeds.
- **A junior dealer's automation budget is trust.** Every shadow-period
  discrepancy honestly reported buys the next phase; one overclaimed
  result ends the program. Same culture as the prototype: when in doubt
  between impressive and honest, choose honest.


---

## 6. Implementation detail — automation by automation

Format per item: data interface → integration pattern → validation → effort
(S = days, M = 1–2 wks, L = 1–2 mos elapsed, mostly waiting on entitlements).

### A1 Pre-open basket pack
- **Data:** OMS program intake (staged orders via API or FIX 35=D drop
  copy pre-release); security master for prev close/ADV/lot; calendar
  service; FX desk indicative rates.
- **Integration:** scheduled job (T-1 18:00 + pre-open 08:00 HKT) in the
  approved Python env; output = PDF/HTML to the sales trader's inbox + a
  row in the audit store. The prototype's `preopen_pack` is the template —
  swap its inputs for OMS fields (LastPx→prev close, OrderQty, Side 54=1/2).
- **Validation:** 2 weeks side-by-side vs the manual morning process;
  count caught-vs-missed issues. **Effort: S–M.**

### A2 Intraday alerting
- **Data:** real-time bars from the tick store (the kdb adapter's
  `xbar` query pattern, 1-min); order state from EMS drop copy (fills:
  35=8 ExecType=F; working qty from 151=LeavesQty); rule tables from the
  reference service.
- **Integration:** a polling loop (30–60s) per active program computing
  the transition-state dict exactly as `alert_scan` does; delivery to the
  desk chat (sanctioned messaging API) with an ACK button writing to the
  audit log. Never auto-acts — alert only.
- **Validation:** precision ≥70% judged by the dealer over 20 sessions;
  zero missed limit-locks (recall check vs end-of-day scan). **Effort: M**
  (the chat-delivery entitlement is usually the long pole).

### A3 EOD client summary
- **Data:** fills from drop copy aggregated per program (avg px vs agreed
  benchmark from the TCA store); residuals = OrderQty − CumQty (14=);
  alert log for notable events; calendar for roll/settle dates.
- **Integration:** T+10min after each market close, draft into the sales
  trader's drafts folder — never sent directly. An LLM pass may smooth the
  prose; every NUMBER comes from the deterministic layer, the LLM only
  rewords (numbers-locked templating: the model fills connective text
  around immutable figures).
- **Validation:** edit distance per draft, trending down; pilot with one
  sales trader. **Effort: S–M.**

### A4 Recon break classifier
- **Data:** our side = clearing extract from the OMS; street side =
  custodian confirms (SWIFT MT535/545/547 parsed by ops systems — consume
  ops' normalized extract rather than raw SWIFT if it exists).
- **Integration:** end-of-day batch joining on (account, ISIN, market,
  settle date); tolerance parameters owned by ops, versioned like rule
  tables. AUTO_CLEAR writes a recon note; everything else goes to the ops
  queue pre-classified with the suggested action.
- **Validation:** one month shadow: zero false auto-clears (hard gate),
  classification agreement ≥90% with ops resolution. **Effort: M.**

### A5/A12 Index-event radar + reconstitution reconciler
- **Data:** MSCI/FTSE product files (official calendars, consultation and
  provisional lists); the universe snapshot (cap/float/ADV) from the
  security master; desk client-basket holdings (aggregated, entitlement-
  checked).
- **Integration:** weekly job: run `predict_msci`/`predict_ftse` on the
  real universe → diff vs official provisional lists when published →
  desk note listing (a) agreement, (b) model-only names (our early
  warning), (c) official-only names (model gap — feeds parameter tuning).
- **Validation:** hit-rate tracked per review cycle; the diff IS the
  validation. **Effort: M** after index-product access.

### A6/QBR quarterly client review
- **Data:** the TCA store (real fills, benchmarks, difficulty controls
  now including realized spread/vol per order — the controls the run
  library lacked).
- **Integration:** the Page-4 aggregation logic pointed at the fills
  database; output into the desk's existing deck template (pptx export).
  One side-by-side quarter with the incumbent process before switching.
- **Effort: M.**

### A7 Rule-table service (the multiplier — do early)
- **Data:** exchange parameter files (lot/tick/band files most Asian
  exchanges publish daily), Copp-Clark-style calendars, exchange notices.
- **Integration:** a small versioned store (even a git-backed YAML repo
  works day one): every consumer (cockpit, checks, packs) reads from it;
  every artifact stamps the version hash — the prototype's
  `rules_version()` as the spec. Tech team owns the feed handlers; the
  dealer owns rule review sign-off.
- **Validation:** daily diff report; any rule change requires a human
  approve before the new version activates. **Effort: M–L** (org, not code).

### A8 Client file normalizer
- **Data/Integration:** becomes a VALIDATION layer on the OMS intake
  rather than a parser: OMS ingests, the normalizer re-derives and diffs,
  issues go back to the sales trader before release. Add SEDOL/ISIN/RIC
  resolution via the security master (the prototype only handles
  Bloomberg-style codes).
- **Validation:** shadow on every incoming file; catch-count is the KPI.
  **Effort: S.**

### A9 Calendar/FX — folds into A7's service. **Effort: S** once A7 exists.

### A10 Crossing detector
- **Data:** live client programs from the OMS (aggregated per client,
  info-barrier checked — the detector needs side+qty, never the client's
  full book).
- **Integration:** flag-only surface to the desk head; execution of any
  cross stays 100% manual through the market's mechanism (ToSTNeT / HK
  direct business / block platforms). Compliance sign-off precedes first
  use; every flag logged whether acted or not.
- **Effort: S** code, **L** approval — correctly so.

### A11 Exposure scheduler
- **Data:** basket with per-name participation caps from the cost model;
  FX cutoffs from A7.
- **Integration:** decision-support panel in the dealer's screen (what-if
  waves), NOT an auto-scheduler; band and front-load are dealer inputs.
  Later: propose as a constraint overlay in the EMS's program scheduler if
  the desk's stack allows custom strategies. **Effort: S–M.**

### Cockpit / monitors — as §2's 60-day phase; the kdb adapter and the
transition-alert pattern port directly.

---

## 7. JD re-review — NEW AI automations not yet in the project (B-series)

Re-reading the JD bullet by bullet with desk-level access in mind, eight
genuinely new items the project does NOT cover — each one is an AI
application in the strict sense (LLM/NLP/ML), each with a human-in-the-loop
by design:

**B1 — Natural-language order-instruction copilot.** *("coordination with
sales traders")* Sales-trader messages — "client adds 50k 2330, cap at 15%
POV, done by Taipei close" — parsed by an LLM into a STRUCTURED amendment
(ticker, qty, constraint, deadline) that is echoed back for one-click
confirm before touching the OMS. Never auto-executes; the confirm-back IS
the control. Value: the highest-frequency manual translation on the desk,
and every misheard instruction is an error avoided. Data: desk chat
(sanctioned, compliance-approved), OMS API. The hard part is entitlement,
not the model.

**B2 — Regulatory-change monitor.** *("stay updated on market-specific
regulations")* An LLM pipeline that reads exchange circulars and regulator
notices (TWSE/HKEX/JPX/KRX/SGX publish these daily), classifies relevance
(short-selling rules, lot/tick changes, band changes, session changes),
DIFFS the finding against the A7 rule-table service, and drafts the
versioned rule update with the citation attached. Human approves every
change; the LLM's job is reading hundreds of notices so the dealer reads
five. This is the single best LLM fit on the whole JD — pure reading
comprehension at volume, verifiable output, human sign-off.

**B3 — News guard on live baskets.** *("monitor market conditions")* Every
name in a working program subscribed to the news feed; an LLM classifies
each story (halt-risk / vol-risk / benign / stale) and only
halt-or-vol-risk on a NAME WE ARE WORKING pages the dealer — connecting
news to the blotter is what generic news alerts don't do. Extends the
existing fire-once alert pattern with a `news` alert kind.

**B4 — Ownership & disclosure threshold monitor.** *("regulatory adherence
across jurisdictions")* Tracks cumulative client buying against
substantial-shareholder disclosure thresholds (5% HK/JP-style), foreign
ownership rooms (Vietnam/Thailand caps, India FPI limits, TW/KR sectoral
caps), and exchange position limits — warning BEFORE a fill crosses a
disclosure line, not after. Deterministic rules + the A7 service for
thresholds; AI part = LLM-read of the (frequently changing) cap notices,
same pattern as B2. The project checks short-sale legality but not
ownership accumulation — a real gap this review found.

**B5 — Pre-submission anomaly guard ("fat-finger AI").** *("high attention
to detail, fast-paced")* Before any wave releases: score each order
against the name's history and the desk's order distribution — price-limit
distance, qty vs ADV vs the client's typical size, side vs the program's
pattern, duplicated wave suspicion. Isolation-forest-style outlier score;
anything anomalous requires an explicit dealer override (logged). The
attention queue watches the market; this watches US.

**B6 — Follow-the-sun handover generator.** *("cross-market coordination
across time zones")* At Asia close, auto-draft the handover: residuals per
program with roll plans, open breaks, unacknowledged alerts, tomorrow's
closures/cutoffs, positions near disclosure thresholds — assembled from
the audit/alert/blotter stores (all deterministic), LLM used only to
compress into the desk's handover format. The London/NY desk starts with a
brief instead of a scroll-back.

**B7 — Ops correspondence drafter.** *("resolving operational
discrepancies")* For each classified break (A4), draft the custodian/
counterparty email in the standard format with the trade references,
amounts, and the discrepancy class pre-filled; ops reviews and sends.
Numbers-locked templating like A3 — the LLM never invents a figure.

**B8 — Client-flow pattern model.** *("client-driven flows")* The most
sensitive and the last: learn per-client flow patterns (which clients tend
to send rebalance baskets after which announcements; typical size/timing)
to pre-position DESK RESOURCES (coverage, pre-open prep) — never market
positions. Internal aggregated data only, information-barrier review
before any build, and the same gate discipline: it ships only if it beats
"the client does what they did last quarter."

**Sequencing:** B2 and B6 first (read-only, pure LLM-over-documents, zero
order-flow risk, immediately visible value); B5 and B4 next (deterministic
cores with AI reading layers); B3 after the alert plumbing exists; B1 when
chat entitlement is granted; B7 with ops' blessing; B8 last, if ever.

**One-line interview version:** "Beyond porting my eleven implemented
automations, the JD has four AI-shaped gaps my project doesn't cover —
reading regulations at volume (B2), guarding the blotter against ourselves
(B5), ownership-threshold accumulation (B4), and the time-zone handover
(B6) — and the common design is the same as my platform: deterministic
core, AI reading layer, human sign-off, audit by-product."
