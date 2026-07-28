# The AI-Augmented Index-Review Framework — Current State, the CLSA Gap-Close, and the Target Workflow

*Session 8f, 2026-07-28. Expands the closing sections of
INDEX_REVIEW_ENGINE_SUMMARY.md into the full argument: (1) what the
AI-augmented framework IS today, precisely; (2) which of its measured
limits institutional access closes, resource by resource; (3) the
concrete AI-integrated workflow those resources enable on the desk,
described as an operating day and an event cycle.*

---

## Part 1 — The current AI-augmented framework, comprehensively

### 1.1 The architecture: a deterministic core with AI at the edges

The framework is NOT "an LLM predicting index changes." It is a
deterministic rules engine — a faithful replication of MSCI GIMI /
FTSE methodology — wrapped in AI where AI is strong and excluded from
where it is dangerous. The separation is the design:

**The deterministic core (every number traces here):**

1. **Screening engine** (`agents/review_engine.py::screen_market`) —
   GMSR at 85% cumulative free-float coverage; SAIR 1.15x / QIR 1.8x
   add hurdles; 0.5x delete floor; country-segment migration at
   85%+2%; min-float 0.15 and real-ATVR liquidity screens; A-share
   20% inclusion factor on member ranking (weight, not eligibility);
   count-anchored universes pinned to published constituent counts;
   churn buffers (no re-add of just-deleted names, no re-delete of
   just-added); corporate-action rule (announced takeover → deletion).
2. **Integrity gates** — universe validator; membership-ledger
   reconciliation replaying official change lists into a state
   machine (STALE_MEMBER / STALE_NONMEMBER are BLOCKING violations —
   the Feng Tay gate); NO-CALL for any market without a validated
   universe.
3. **Probability layer** — Laplace-shrunk per-call probabilities from
   the graded record (HIGH adds ~85%, verified deletes ~80%,
   unverified x0.75 discount), never gut feel.
4. **Flows** — float cap x stacked passive-ownership rate (5-9%),
   ranges not points; ADV-day buckets driving MOC / WORK+MOC /
   MULTI-DAY execution classes.
5. **Crowding** — daily TWSE margin+SBL archive; pre-event build %;
   drawdown-from-peak EXITING tag; CONSENSUS/UNPRICED/STREET-ONLY
   overlay vs our own calls.
6. **Event-history priors** — measured T-day multiples (MSCI deletes
   median 16x, max 38x; FTSE ~5x), −4.3% front-run, ~50% reversal,
   T+2 SBL settlement signature — from 21+ real 2026 events; absent
   classes stated, not guessed.
7. **Risk flags** — SIZE / LIMIT / BORROW / REVERSAL per name, plus
   market-access rules from the versioned Reg-Watch registry.
8. **Self-grading** — validate_pack appends outcomes to the same
   document; pre-registration by git timestamp; misses always ship.

**Where AI actually sits today (three distinct roles):**

- **AI-as-analyst (the big one).** The entire 34%→69% May-replication
  arc — hypothesize a miss mechanism, build the test, run it at
  point-in-time quality, grade against the official list, keep or
  revert — was executed by AI in hours per iteration. Eight
  iterations, 113 tickers, 8 markets, every lever documented. A human
  analyst doing this manually is looking at weeks per pass. This is
  the honest headline of "AI-augmented": not that a model predicts,
  but that the build-test-grade loop runs at machine speed while
  every artifact stays human-auditable.
- **AI-as-extractor.** Reg-Watch's multilingual keyword triage over
  708 raw notices → 109 clustered stories, with an LLM hook reserved
  for body-level summarization/extraction (circulars in 4 languages,
  the Toyota-Industries corporate-action class). The hook is a slot,
  human-gated, and never the ranker.
- **AI-as-renderer.** Pack generation: per-name rationale in trading
  language, reading guides, client-shaped narrative — generated from
  engine output, with the numbers untouched.

**The invariants (stated once, enforced everywhere):** LLMs render,
retrieve, and extract; they never rank, score, or predict. Every
number traces to a deterministic engine and a named input. Misses
ship next to hits. No call without verified membership. NO-CALL beats
a fabricated list.

### 1.2 What it runs on (all free, all public)

yfinance caps/floats/volumes; exchange open data (TWSE TWT93U
short/margin, BFIAUU, TDCC ownership); MSCI public change-list PDFs
(parsed to ledgers); exchange notice feeds (4 live, 8 blocked by
anti-bot walls — disclosed); published constituent counts; historical
prices for point-in-time reconstruction.

### 1.3 What it has demonstrably achieved on that data

- **Adds 17/17 lifetime at PIT quality, zero false positives**, 8
  markets, 2 providers — the add side is signal.
- **Deletions 51/56 recall / 82% precision** — shipped as a
  probability-ranked watch zone with cutline residents labeled
  ~45-60%, never as flat calls.
- **69% of ALL 98 actual May-2026 Asia changes**, graded against the
  official list, 15+ days before it could have known them.
- A live Aug-2026 pack across 8 markets with an honest zero-call
  result, pre-registered for grading.
- Every remaining miss mechanism-classified: FIF discretion
  (structural), H-line share splits (fixable), CA events (rule now
  exists), holdings baselines (fixable).

### 1.4 The measured ceiling — why this is a public-data ceiling, not a method ceiling

Iteration was terminated at the methodologically correct point: the
last tunable knob (boundary buffer) swept flat, and every remaining
gain requires NEW DATA, not new rules. The six binding constraints
(from INDEX_REVIEW_ENGINE_SUMMARY.md): FIF discretion; dual-line
share splits; membership baselines; real-time data; anti-bot walls;
float/cap vintage. That list is the bridge to Part 2 — each entry
names the institutional resource that dissolves it.

---

## Part 2 — How institutional access at CLSA closes the gap, resource by resource

### 2.1 The gap-close map

| # | Public-data limit (measured) | CLSA resource | What changes | Residual |
|---|---|---|---|---|
| 1 | FIF discretion (Indonesia May deletions; floats 0.20-0.29 invisible to third-party data) | Index-provider data license: official FIFs, NOS, inclusion/capping factors per security, pro-forma files, consultation notices | The engine ranks on MSCI's OWN current float factors instead of estimates; FIF-cut candidates become visible as "low official FIF + deteriorating float trend" watch names | Genuine pre-announcement discretion stays unknowable — but the blind spot shrinks from "can't see the input" to "can't see the decision," and nobody on the street can |
| 2 | Dual-line share splits (0177/2799 H-line misses; yfinance assigns whole-company cap to one line) | Vendor security master (Bloomberg/Refinitiv) + HKEX direct feed: exact per-line shares outstanding | The two remaining fixable China misses close; dual-listed universes (H/A, local/ADR) modeled correctly by construction | None — this class disappears |
| 3 | Membership baselines (the AI-quartet error: ledgers replay deltas but can't establish base state) | Daily official constituent files from the vendor license | The entire ledger-reconstruction apparatus (holdings ingestion, alias maps, STALE detection) collapses into a one-line join against ground truth; the Feng Tay gate becomes a trivial lookup | None — and the reconciliation code is repurposed as a vendor-file sanity check |
| 4 | Real-time data (crowding/auction reads EOD or delayed) | Real-time market data incl. the TWSE 13:25-13:30 indicative auction broadcast, live order-book depth, real-time SBL rates and availability, KRX/HKEX equivalents | A NEW capability class, not just a gap-close: live auction-imbalance reads on event day, intraday crowding drift, borrow-rate spikes as positioning signals | — |
| 5 | Anti-bot walls (8 of 12 notice feeds, iShares CSVs) | Desk network + Bloomberg regulatory news + exchange memberships and e-mail circulars + compliance feeds | Reg-Watch coverage goes 4/12 → 12/12+ with zero code change (the pipeline is source-agnostic: anything landing as {source, date, title, url} joins clustering/scoring) | None |
| 6 | Float/cap vintage (third-party estimates vs as-of files; the Rainbow-Robotics false-positive source) | Vendor as-of files with MSCI's own price-cutoff conventions | Add-side margins computed on the same numbers MSCI uses; the residual false-positive class shrinks to genuine cutoff-date price moves | Small — price moves between cutoff and announcement remain irreducible |

### 2.2 Resources that are net-NEW signal, not gap-closes

Three things a desk has that no public rebuild can approximate:

- **The desk's own flow.** Client indications, GC quote requests, PT
  basket compositions arriving pre-event — the strongest crowding
  signal that exists, subject to strict information-barrier and
  client-confidentiality rules. Used correctly (aggregated,
  anonymized, compliance-approved), it upgrades the crowding layer
  from "TWSE short ledger, Taiwan only" to "actual demand curve,
  every market we trade."
- **Execution history.** CLSA's own T-day fills across past
  rebalances: realized impact per ADV-day bucket, auction fill
  quality, limit-lock frequency. This calibrates the flows and
  risk-flag layers against ground truth instead of measured-but-
  external event studies.
- **The vendor/provider relationship.** Index-provider client
  coverage, consultation participation, and methodology Q&A — the
  channel through which ambiguous rule interpretations (segment
  migration edge cases, FIF review timing) get resolved before the
  engine encodes them wrong.

### 2.3 What institutional access does NOT change

The invariants survive contact with better data: LLMs still never
rank; probabilities still come from the graded record; misses still
ship; pre-registration still applies (now against internal
timestamped records rather than public git). And two constraints are
permanent: MSCI's pre-announcement discretion, and the compliance
wall between client-flow information and any signal that leaves the
agency context. The framework was designed input-upgradable precisely
so that the METHODS — screening, reconciliation, grading, the
watch-zone product shape — carry over unchanged while every input
gets replaced by its official version.

---

## Part 3 — The ideal AI-integrated workflow on the desk

Two loops: a **daily loop** (always on) and an **event loop** (keyed
to the review calendar — MSCI announcements mid-Feb/May/Aug/Nov
effective month-end; FTSE March/Sep majors). The dealer's day
touches the outputs, never the pipeline.

### 3.1 The daily loop (runs unattended, overnight)

    vendor constituent + FIF files land
      → engine regenerates the full pack per market
        (screen → reconcile → probabilities → flows → crowding
         → history → flags → rationale)
      → DIFF against yesterday's pack
      → flash brief ONLY if something changed
         (new boundary entrant, crowding regime shift, notice-feed
          FLASH story, CA detection on a member)
      → silence otherwise — alert fatigue is a design goal

In parallel: Reg-Watch ingests all notice sources (now 12/12),
clusters stories, scores deterministically, LLM-extracts corporate
actions from circular bodies in four languages with human sign-off
before any CA flag enters the engine. Crowding fetchers archive
short/SBL/borrow-rate data across every covered market, not just
Taiwan.

**The dealer's touchpoint: a five-minute read at the open.** The
brief says what changed, why (scoring reasons printed), and what it
means for execution (impact notes in trading language). Drill-down
links reach the raw engine output. Human time per day: minutes.
Human time per review cycle under the manual alternative: days.

### 3.2 The event loop (per review, T = effective date)

**T−60 to T−30 — positioning phase.** The pack is live and
regenerating nightly on official inputs. Add calls carry graded
probabilities; the deletion watch zone is ranked with cutline
residents labeled. Crowding overlay marks each call CONSENSUS /
UNPRICED / STREET-ONLY — the differentiated claim clients pay for.
Sales gets a client-conditioned rendering: same engine output,
filtered to each client's holdings overlap and TE budget, narrative
LLM-rendered, numbers untouched.

**Announcement day (T−12 approx).** The official list lands; the
engine auto-grades within minutes — hits, misses, false flags
appended to the pre-registered pack. The desk's answer to "what
surprised?" is ready before the client calls. Surprise names
immediately enter the flows/crowding layers as fresh events.

**T−12 to T−1 — inclusion window.** Daily crowding trajectories on
every confirmed name (build %, EXITING tags, drift composition
short-led vs long-seller-led). Expected-flow ranges refresh on live
caps. Risk flags finalize the execution plan per name: MOC-able /
WORK+MOC / MULTI-DAY; LIMIT flags on static-band markets (TW ±10%,
KR ±30%, CN-A ±10/20%...) drive T+1 contingency planning; BORROW
flags drive locate pre-arrangement.

**T-day.** The new capability class: live indicative-auction reads
(TWSE 13:25-13:30 broadcast and equivalents) against the engine's
expected-flow number per name — imbalance vs expectation in real
time, limit-lock probability updating live, the GC book's risk
visible before the print. This is where real-time institutional data
creates something the public rebuild could only describe.

**T+1 to T+5 — grading and learning.** Realized prints vs predicted
flows; reversal fraction vs prior; T-multiples appended to the event
library; probability calibration updated (the Laplace priors get new
counts); execution quality vs the plan feeds the impact model. Every
layer's predicted-vs-realized delta updates automatically — the
desk's numbers compound each cycle without anyone scheduling the
work.

### 3.3 The client-facing surface

- **RAG over the graded corpus:** a client asks "what's your hit rate
  on Korea deletes?" — the answer comes with citations to graded
  packs, in seconds, because every claim already lives in a
  self-graded document.
- **Scenario turnaround:** "what if we execute 60% MOC and work the
  rest?" — parameterized engine run, drafted reply, minutes not
  hours.
- **The honesty product:** the same NO-CALL / watch-zone / misses-
  included discipline, which on a desk becomes a commercial edge —
  clients allocate GC risk budget to the broker whose probabilities
  are calibrated, and calibration is only provable with a shipped
  track record.

### 3.4 Division of labor, stated plainly

| AI owns | The dealer owns |
|---|---|
| Regeneration, diffing, monitoring, extraction, rendering, grading, calibration bookkeeping | Every call that ships; GC pricing; client conversations; registry changes (human-gated); CA sign-off; the judgment on cutline residents |

The endpoint of the design is NOT fewer humans — it is that the
dealer's hours migrate from pipeline-tending to the three things
that price risk: judgment at the boundary, client trust, and the
event-day read. The framework as built is the proof-of-concept that
this migration works: one person, public data, and an AI loop
produced a graded 69%-of-Asia replication in a session. The same
loop pointed at official inputs is the desk tool.

---
---

# STEP 2 — The Announcement→T Window: Framework, Gap-Close, Target Workflow

*Session 8h. Parts 1-3 above cover the prediction engine (lifecycle
Phase 0 — winning the trade). This section does the same three-part
walk for lifecycle Step 2 (docs/INDEX_REBALANCE_TRADE_LIFECYCLE.md):
the 13-trading-day window between announcement and effective day,
where execution quality is actually determined. Scope note, agreed
with the analyst: workstreams 2.2 (liquidity & risk per name) and
2.3 (execution planning & discretion) are the AI-implementable core
and are BUILT; 2.5's market-surveillance half already runs
(Reg-Watch + multi-market crowding fetchers); 2.1/2.6 are desk ops
and client relationship work; 2.4's aggregate netting needs
multi-client order data that only exists on a desk.*

## Part 4 — The current AI-augmented Step-2 framework, comprehensively

### 4.1 What is built (`agents/event_window.py` + feeders)

**2.2 — the per-name liquidity & risk sheet** (`liquidity_risk_sheet`).
One deterministic table per basket, every column traceable to a
measured input:

- **ADV-days** from order size vs average volume — the master sizing
  number.
- **Expected T-day volume** from the measured event library (MSCI
  deletes median 16x / max 38x, FTSE ~5x — 21+ graded 2026 events,
  never guessed), and the order's **auction footprint %** against the
  measured ~30% close share of T-day volume — the single-client
  primitive of workstream 2.4's capacity check (a 120% footprint
  reads "you ARE the auction; the plan must change").
- **Limit-band risk** from the per-market band table (LOCK RISK for
  ±10% markets like TW/CN-A, WATCH for ±30% KR/MY/TH, dash for
  band-free HK/SG) — the static-band taxonomy from the T+1-deferral
  analysis, wired per name.
- **Borrow status** from the live TWT93U file: balance /(balance +
  remaining quota) = fraction of implied SBL capacity in use, TIGHT
  at >=80%. Taiwan only — the one public per-stock quota file; other
  markets print "no quota data" rather than a guess.
- **Halt proxy** and the **bucket map** (MOC / WORK+MOC / MULTI-DAY)
  that drives everything downstream.

**2.3a — the start schedule** (`start_schedule`). For every MULTI-DAY
name: working days = ceil(ADV-days / participation cap), start date =
effective date minus that many business days, and a LATE START
escalation flag when the computed start is already behind today —
the "when do we begin" decision, mechanized, with the escalation
built in rather than discovered on T-3.

**2.3b — the discretion decision** (`discretion_decision`). The
pre-position-vs-wait call, decided BY the crowding read through an
explicit rule matrix: crowded delete → WORK AHEAD (pressure
part-spent, covering bounce enlarged); uncrowded delete → WAIT for
the print; crowded add → NO pre-positioning (jump already priced);
uncrowded add → PRE-POSITION within the envelope; an EXITING tag
(drawdown-from-peak — stock, not flow) flips crowded logic to
uncrowded; no envelope → MOC ONLY, whatever the color. Every
decision emits its best-ex rationale citing the actual crowding
read — **the audit evidence is a by-product of deciding, not
paperwork written after**.

**The feeders** (all pre-existing layers, now consumed by Step 2):
multi-market crowding archive (TWSE+TPEx daily, JPX daily, SFC HK
weekly incl. China H-lines); measured T-multiples; the frontier
(`recommend_execution`) for per-bucket strategy under the client's
tracking tolerance, on crowding-adjusted paths; Reg-Watch in watch
mode for provider/exchange amendments (workstream 2.5's
surveillance half).

### 4.2 What the live demo established

On real boundary names with live reads
(EVENT_WINDOW_PLAN_DEMO_AUG2026.md): the matrix visibly keys to
data — 1101 (HIGH +53% short build, Sell) works ahead while the
EXITING Taiwan names wait; 9995.HK (HIGH +45%, Buy) is denied
pre-positioning; the envelope-less line stays MOC-only. And a
cross-validation for free: the borrow read came back TIGHT (97-98%
of implied SBL capacity) on exactly the names the crowding layer
flagged — two independent public files agreeing on where the crowd
is.

### 4.3 The honest limits of the Step-2 build

1. **Borrow visibility** — quota data public in Taiwan only; JP/HK
   lines say "no quota data"; real SBL rates/availability are a
   vendor/desk feed everywhere.
2. **Halt/suspension risk** — a proxy flag, not a feed; corporate-
   action radar (Reg-Watch LLM hook) is the systematic answer and is
   human-gated by design.
3. **Aggregate capacity & netting (2.4)** — per-name footprint is
   single-client; the desk's REAL constraint is its combined
   footprint across all clients, unknowable outside.
4. **Frontier calibration** — impact parameters are stylized (eta,
   pressure paths); real fills would calibrate them.
5. **Demo quantities** — order sizes are hypothetical; every other
   column is live. The tool's shape is real; the desk fills in the
   orders.

## Part 5 — How institutional access closes the Step-2 gaps

| # | Step-2 gap | CLSA resource | What changes |
|---|---|---|---|
| 1 | Borrow: one public quota file (TW) | Prime/SBL desk feeds: real-time rates, availability, recall risk per name, every market | Borrow column goes from proxy-in-one-market to hard numbers everywhere; BORROW TIGHT becomes a rate threshold, and locate pre-arrangement (2.1) triggers straight off the sheet |
| 2 | Halt/CA amendments as proxy | Bloomberg/exchange corporate-action feeds + index-provider amendment notices (subscriber files) | The 2.5 revision loop becomes machine-diffable: provider amendment in → basket re-versioned → sheet regenerated → client notified, same hour |
| 3 | Aggregate capacity unknowable | The desk's own OMS: every client's rebalance orders in one book | The 2.4 layer computes CLSA's combined per-name auction footprint and crossing candidates (offsetting flows) mechanically — the single-client footprint column already built is the same math run over the aggregate book |
| 4 | Stylized impact parameters | CLSA execution history: realized T-day fills, auction fill quality, limit-lock frequency per market | The frontier's eta/pressure/reversal parameters become fitted values with confidence intervals; the discretion matrix thresholds get calibrated against realized outcomes |
| 5 | Crowding EOD/delayed, 3 markets live | Real-time market data + KRX/vendor short feeds + the desk's own flow color (compliance-scoped) | Crowding trajectories update intraday across every covered market; the EXITING tag becomes observable day-by-day instead of inferred from EOD prints |
| 6 | Client tolerance/envelope assumed | The actual mandate: tracking budget, envelope, cash-neutrality, restricted list — per client | The frontier stops using a default 50 bps tolerance and runs each client's real constraint; one engine, per-client plans |

## Part 6 — The ideal AI-integrated Step-2 workflow (announcement → T)

**Announcement day (T-13).** The moment the official list lands, the
Step-2 chain fires automatically off Step 1's acknowledged baskets:
per-client liquidity & risk sheets, start schedules, and draft
discretion decisions generate within minutes. The dealer's first
Step-2 act is REVIEW, not assembly: sign off the discretion drafts
(they carry their rationale already), eyeball the LATE START and
capacity flags, approve the client strategy memos the renderer
drafted from the sheet.

**Daily loop through the window (T-12 → T-2).** Overnight, the
machine re-runs everything against fresh data: crowding
trajectories (all markets, intraday-capable), borrow rates, provider
amendments (Reg-Watch diff — a suspended name comes out, an FIF
change re-weights, the basket re-versions and the whole validation
chain re-runs on the revised file). The morning brief is a DIFF, not
a report: which names changed bucket, which discretion decisions
should flip (the crowding read crossed a threshold — 2207's crowd
started EXITING, recommendation moves WORK→WAIT, rationale updated),
which start dates arrive today, which client needs a note. Silence
on unchanged names. MULTI-DAY working legs report progress vs plan
automatically; the daily client notes draft themselves from the
run records, dealer edits and sends.

**The netting pass (continuous).** Every new client order joins the
aggregate book; the 2.4 layer recomputes combined footprints and
surfaces crossing candidates with per-market mechanics attached (TW
block session / HK direct business / JP ToSTNeT) — the dealer
decides, the machine documents.

**T-2/T-1 — convergence.** Final index files diff against every
client basket mechanically; discrepancies list themselves. The T-1
checklist generates as a verification run over live state — staged
auction orders vs final quantities, FX legs, cutoff run-sheet in
HKT, contingency notes for every LOCK RISK and BORROW TIGHT name —
and the T-1 client confirmations draft from it. The dealer's T-1
evening is spent on the exceptions the checklist surfaced, not on
building the checklist.

**Division of labor, Step-2 specific:** AI regenerates, diffs,
drafts, schedules, and documents; the dealer approves every
discretion decision before it trades (the rationale is pre-written,
the judgment is theirs), owns every client conversation, and
handles the escalations the machine can only flag (LATE START,
capacity breach, tolerance-infeasible names). The window's
economics: six workstreams that consume a team's fortnight collapse
into a review-and-exceptions cadence — and every decision arrives
with its best-ex evidence already attached, which is precisely the
artifact regulators, clients, and next quarter's RFP all ask for.

---
---

# STEP 3 — T-Day: Framework, Gap-Close, Target Workflow

*Session 8i. Companion to docs/STEP3_TDAY_DESIGN.md. Step 3 is the
one lifecycle step that is intrinsically real-time, so the honest
split matters most here: what runs today on public data, what is
designed-and-gradable, and what is PROTOCOL until desk feeds exist.*

## Part 7 — The current AI-augmented Step-3 framework, comprehensively

### 7.1 The organizing principle

T-day is the disciplined execution of decisions already made — so
**T-day AI adds ZERO new judgment**. Its entire job is compressing
reaction time on pre-made decisions and holding vigilance constant
while the Asia cascade runs the same close sequence market after
market. Every trigger is deterministic; the LLM only drafts language
over computed numbers. This is the strictest application of the
framework-wide invariant, because T-day is where a wrong automated
"decision" costs the most.

### 7.2 What runs today (public data, verified)

- **The auction measurement layer** — the session-8i discovery:
  Taiwan's closing-auction volume is DERIVABLE free (daily volume −
  Σ intraday 5-min bars; verified 2330.TW = 24.8% auction share),
  and HK's CAS print is the last bar. With 60 days of 5-min depth
  covering the June TW50 and May-MSCI effective days, per-name
  EVENT-day auction shares are measurable now — the input every
  T-day sizing decision rests on.
- **The indicative-auction parser** (`parse_auction_snapshot`) for
  TWSE's 13:25-13:30 broadcast — live-only by nature; our own
  archive starts Aug 11 (a proprietary dataset from a free feed).
- **TWSE OpenAPI** (free, keyless, probed): MI_5MINS 5-second
  market-wide order-flow accumulation — auction-period context.
- **The exception machinery** — limit_proximity (WATCH/ALERT/LOCKED
  against the band table), attention_queue ranking by dollar-at-
  risk, flow_forecast's DM-gated run-rate re-forecast (the lunch
  checkpoint's engine), auction_countdown off the rules registry.
- **The measured event library** — 21+ graded 2026 events: T-day
  volume multiples (MSCI-Sell median 16x/max 38x), −4.3% front-run,
  ~50% reversal — the priors every T-day expectation quotes.
- **The strategy frontier** (agent14) — S1-S4 outcomes on calibrated
  event paths, crowding-adjusted; T-day executes its picks.

### 7.3 What is designed and gradable (STEP3_TDAY_DESIGN.md)

The simulation suite, in build order: auction-share measurement
study (data verified); the T-day REPLAY SIMULATOR — execute the full
Step-2 plan bar-by-bar against realized event days, producing the
counterfactual table ("what would each discretion choice have cost
on the May names") that turns the discretion matrix from argued to
measured; the auction violence curve (close return vs volume
multiple, ~20 points, banded prior); the lunch re-forecast backtest
(validate or honestly kill the half-day rule); the limit-lock
scenario model (P(close unreachable) x T+1 residual cost); the
cascade run-sheet generator.

### 7.4 The honest PROTOCOL line

The live cockpit is PROTOCOL until desk feeds exist: our monitors
run on delayed/EOD public data, and no free source carries per-stock
real-time state for the full cascade. The design defense: every
consumer is REPLAY-DRIVEN — thresholds, countdowns, and the
indicative-vs-expected logic are all built and testable on archived
data, so live feeds are a transport swap, not a redesign.

## Part 8 — How institutional access closes the Step-3 gaps

| # | Step-3 gap | CLSA resource | What changes |
|---|---|---|---|
| 1 | No real-time per-stock state | Direct exchange feeds / vendor consolidated feed, all covered markets | The exception engine's inputs go live; limit_proximity, run-rate, halt detection tick in real time — the cockpit stops being PROTOCOL |
| 2 | Indicative auction: TW only, self-archived | Full auction/imbalance feeds where they exist (TW indicative, HK CAS reference + imbalance, JP/KR auction states) + the desk's historical tick warehouse | The violence curve trains on hundreds of auctions, per market, instead of ~20 events; indicative-vs-final becomes a fitted model with market fixed effects |
| 3 | Fill state invisible (we simulate it) | OMS/EMS: live fills, working-order state, algo child-order telemetry | Run-rate vs plan becomes exact; the lunch checkpoint compares actual participation, not estimates; post-close verification is instantaneous |
| 4 | T-multiple/auction-share priors from 21 public events | Desk execution history across years of rebalances | Priors become per-market, per-side, per-liquidity-tier distributions with real sample sizes; resize triggers get calibrated thresholds |
| 5 | Halt/amendment detection via public notices | Exchange operational feeds + index-provider intraday notices + internal ops alerts | The overnight sweep and intraday amendment watch run on push, not poll — minutes of latency become seconds |
| 6 | Cash/FX state assumed | Real-time positions, FX desk rates, custodian links | The cash-neutrality constraint and FX legs are monitored facts, not plan-time assumptions |

## Part 9 — The ideal AI-integrated T-day workflow (the cascade, hour by hour)

**Pre-open, per market.** The machine has already swept: overnight
notices diffed, corporate actions extracted (human-gated), any
touched name re-versioned through the full validation chain; staged
orders reconciled against the final file; the run-sheet (all cutoffs
in HKT, contingency references attached to every LOCK RISK / BORROW
TIGHT name) is on the desk. The dealer reads exceptions over coffee
— the basket is already correct.

**Continuous session.** The exception engine watches everything and
surfaces almost nothing: run-rate vs plan bands per working leg,
limit proximity with tightened thresholds on flagged names, halts,
cash drift — ranked by dollar-at-risk, silent otherwise. THE LUNCH
CHECKPOINT fires automatically: realized half-day volume → posterior
T-multiple → if the tape disagrees with the plan's assumption, a
resize proposal with its arithmetic shown lands on the dealer's
screen by 12:30, not at 13:20. Approve or override; either way the
decision and its evidence are logged as they happen.

**The close cascade.** Market by market, the same drill: countdown
to cutoff; MOC orders confirmed in; then the auction read — live
imbalance/indicative vs the expected multiple, the violence curve
translating any deficit into expected print deviation, and the ONE
real-time decision (final envelope sizing / queue-or-retreat on
locked names) presented as a framed recommendation with the
pre-agreed playbook attached. The dealer takes the decision; the
machine executes the mechanics and starts the clock on the next
market. TW 13:30 → CN 15:00 → HK 16:08 → JP/KR closed hours earlier
— by mid-afternoon HKT the cascade is history and every print is
already reconciled.

**Post-close, per market, immediately.** Fills vs official close
verified line-by-line the moment both exist; the client flash
drafts itself with completion, tracking, and residual plan; every
exception is in the intraday note before the next market closes.
Step 4's TCA inputs are complete BEFORE the day ends — post-trade
starts with nothing to assemble.

**Division of labor, T-day specific:** the machine watches, counts
down, reconciles, drafts, and frames; the dealer makes exactly the
decisions that were reserved for T-day — the lunch resize and the
close-auction sizing within each envelope — plus anything the
exception engine escalates. One dealer runs a cascade that used to
need a row of screens and a team's full attention, and every
decision of the day lands in the audit pack with its evidence
attached at the moment it was made.
