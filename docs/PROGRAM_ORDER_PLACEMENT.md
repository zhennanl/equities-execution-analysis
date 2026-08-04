# How a Client Places a Program Trade Order — Process Walkthrough + AI Enhancement Map

*Session 9i (2026-08-03). Generalizes Step-1 of
INDEX_REBALANCE_TRADE_LIFECYCLE.md from the rebalance case to ALL
program orders (rebalance, transition, cash-flow, restructure).
Companion to STEP1_AGENTIC_DESIGN.md (which details the rebalance
agent build). Sell-side PT desk perspective.*

---

## 1. The three ways a program order exists

| Mode | What the client buys | Economics | Information game |
|---|---|---|---|
| **Agency** | Execution skill + analytics; desk works the basket as agent | Commission (cents/bps) | Names disclosed to the working desk; size is the secret |
| **Principal / risk bid** | Certainty: desk buys the whole basket at a guaranteed price (e.g. close ± X bps) and wears the risk | Risk spread in bps, won via competitive RFQ | Client sends a BLIND PROFILE first; names revealed only to the winner after award |
| **DSA (direct strategy access)** | The desk's algos at lower rates; client drives | Reduced commission | Machine-to-machine; the desk sees flow but makes no decisions |

Index-rebalance wrinkle: the NAMES are public (everyone knows the
adds/deletes) — what stays confidential is the client's size and
constraints, so the game shifts from secrecy to auction quality and
discretion judgment.

## 2. The process, step by step

**S0 — Panel & relationship (weeks before).** The client's broker
panel already exists; pre-event marketing, TCA history, and past
grade credibility determine who gets the call. Nothing transactional
happens here, but this is where the order is actually won.

**S1 — Pre-trade inquiry / blind profile.** For risk bids the client
sends a CHARACTERISTICS sheet, not names: line count, total notional,
side mix (% buy/sell), country/sector breakdown, liquidity
distribution (% of basket > 1 ADV-day), tracking properties vs an
index, sometimes a crossing-potential hint. Sent to 3-5 brokers,
often via an EMS/portal with a response deadline measured in minutes.

**S2 — Quote.** Desks price the blind profile: expected impact cost
per liquidity bucket + factor/short-leg risk charge + inventory/
netting offsets − competitive shading. Agency inquiries instead get a
commission quote + proposed execution approach. Response time is
itself a selection criterion.

**S3 — Award & terms.** Winner notified; terms fixed: benchmark
(close / arrival / VWAP), commission or risk spread, the DISCRETION
ENVELOPE (MOC-only vs work-X%-ahead vs multi-day for illiquids),
constraints (cash neutrality, completion deadlines, restricted
names, per-market instructions), settlement/FX split (broker FX vs
custodian), multi-fund allocation scheme.

**S4 — Transmission.** Descending institutional-ness: FIX
NewOrderList OMS→OMS; Excel/CSV via secure portal or email;
Bloomberg IB chat + attachment; voice for sensitive size. Multi-
market Asia programs arrive as ONE list with follow-the-sun handoff
expectations.

**S5 — Ingestion & normalization.** The file becomes a canonical
basket: identifier resolution (SEDOL/ISIN/local code/RIC — mixed in
one file is normal), side/qty/limit conventions, board-lot rounding,
currency and market tagging, multi-fund allocation splits, duplicate
and reversal checks against yesterday's basket.

**S6 — Compliance & feasibility pre-flight.** Restricted list,
foreign-ownership room (TW/KR/IN/VN), market access for new names
(TW foreign-investor ID, China Connect eligibility, India FPI),
short-sell locates and uptick regimes on the sell side, odd lots,
limit-band risk names, settlement calendar conflicts (holidays,
T+1/T+2 mismatches across the basket's markets).

**S7 — Pre-trade pack.** The desk's risk sheet: ADV-day buckets,
expected cost vs benchmark per bucket, auction footprint for
close-benchmarked lines, borrow status, netting/crossing potential
vs other desk flow, hedge plan for principal risk, and the exception
list (anything that cannot be executed as instructed).

**S8 — Acknowledgment loop.** Confirmation back to the client: line
count, gross/net notional, benchmark, per-bucket strategy,
exceptions with proposed resolutions. Client signs off or amends;
amendments loop back through S5-S7. Instruction + confirmation open
the audit trail.

**S9 — Order live.** Handoff to the window/execution phase (Step 2).

## 3. AI enhancement, step by step

| Step | AI role | Type | Efficiency win |
|---|---|---|---|
| S0 | Grade-backed marketing packs; client fingerprint briefs ("their basket shapes, sizes, cadences, past realized-vs-estimate") | LLM render over engine JSON + ML retrieval | Sales prep from hours to minutes; institutional memory survives staff turnover |
| S1 | **Blind-profile parser**: normalize any inquiry format into canonical characteristics; flag inconsistencies (breakdowns that don't sum, notional/line-count mismatch) | LLM parse + deterministic validator | Minutes-deadline RFQs answered with machine speed |
| S2 | **Quote support**: cost model per bucket + event-class priors + similarity retrieval ("nearest 5 past programs and their realized costs") + netting scan vs current desk flow; drafts the quote sheet; TRADER SETS THE PRICE | Deterministic model + embedding retrieval + LLM draft | The quote is evidence-based and fast; shading stays human |
| S3 | **Envelope advisor**: expected TD gain vs TE cost for the proposed envelope, by event class (the decade tables); drafts term-sheet language | Deterministic tables + LLM draft | Converts terms negotiation from instinct to measured evidence |
| S4/S5 | **Universal intake**: LLM proposes column mapping for any file/chat format → deterministic validator reconciles rows/notional/sides before acceptance; identifier resolution with confidence scores, ambiguity → human | LLM-assist, code-decides | The 30-60min error-prone normalize loop → minutes; fewer fat-finger incidents |
| S5 | **Anomaly vs fingerprint**: basket compared to this client's historical shape (size, turnover, sector skew); deviations flagged ("3x usual notional; new market: India") | ML | Catches client-side file errors BEFORE execution — the highest-value catch in the whole chain |
| S6 | **Pre-flight orchestrator**: run all checks, EXPLAIN failures in plain language with the rule citation, propose resolutions (odd-lot handling, substitute settlement) | Rules engine + LLM explain | Exceptions become a triaged, explained list, not a manual hunt |
| S7 | **Pack assembler**: liquidity sheet, cost estimate, footprint, borrow — engine-computed; LLM writes the narrative and the exception prose | Engines + LLM render | Client-ready in minutes with methodology attached |
| S8 | **Acknowledgment drafter** + amendment differ ("v2 changes 12 lines: +3 adds, qty changes on 9; re-flight only those") | LLM + deterministic diff | Amendment cycles stop re-running the full loop |
| All | **Q&A copilot** over methodology, terms, and order state, with citations | RAG | Every trader answers client questions at specialist depth |

**The invariant everywhere:** the LLM parses, retrieves, explains,
and drafts; deterministic code computes, validates, and decides
whether data is fit to proceed; a human gates every quote, every
price, and every client send. No autonomous order acceptance.

## 4. Where the money is (ranked honestly)

1. **S5 anomaly-vs-fingerprint + validator** — prevents the
   expensive disasters (wrong-side files, doubled baskets, stale
   versions). One caught error pays for the system.
2. **S1-S2 speed** — risk-bid RFQs are won partly on response time;
   machine-speed parsing with evidence-based pricing support is a
   competitive edge, not a convenience.
3. **S3 envelope advisor** — grows the higher-margin envelope
   business by arming the terms conversation.
4. **S6-S8 automation** — pure cost-and-error reduction, the
   Jefferies-style efficiency case.

## 5. Demo vs institutional

Demo (public data, this repo): synthetic client files exercise
S4-S8 end-to-end (normalizer, pre-flight vs public restricted list +
rules registry, pack from the existing liquidity/cost engines,
acknowledgment draft); S1-S3 run on constructed blind profiles with
the decade tables as the pricing evidence; the client fingerprint is
simulated from our event library. Institutionally: FIX/portal/chat
listeners, real CRM and agreement stores, firm compliance engine,
desk-fill-calibrated cost models, entitlements + audit platform —
per the upgrade table in STEP1_AGENTIC_DESIGN.md §5.
