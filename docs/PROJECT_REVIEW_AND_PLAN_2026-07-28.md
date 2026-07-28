# Project Review & Plan — 2026-07-28

*Reviewed against the two stated goals, with the CLSA PT Stock Dealer JD
as the end-user definition. Inventory at review: 47 agent modules,
6 app views (tour / simulator / rebalancing / program desk / QBR),
7 graded real-data case studies, ~50 docs, 347 tests green, live
fetchers for TWSE/TPEx/KRX flows + short balances + block tape + TDCC.*

---

## Part 1 — Where the project stands against each goal

### Goal 1: demonstrate PT + AI understanding via meaningful analysis under the public-data constraint

**Largely achieved in substance; under-packaged.** The evidence chain is
real and unusual for a candidate project: a prediction engine graded on
five actual reviews (adds 11/11, coverage deletions 14/14, rank
deletions honestly ~50–60% with self-labeling confidence); a flow
simulation that reproduced the Madhavan asymmetry from first principles;
an event study on 21 real 2026 names that FALSIFIED our own execution
rule twice; investor-type attribution that measured the arb→tracker
handoff 8/8; and an event-data layer that closed its own attribution
limitation (SBL decomposition) and caught a known model miss ex ante
(China Steel STREET-ONLY). The honest-methods culture (pre-registration,
kept false positives, in-sample labels) is itself a differentiator.

**Gaps:**
1. **No single narrative.** The chain lives in 7 case studies + addenda.
   An interviewer or desk user cannot consume it. There is no flagship
   document that walks predict → size flow → read positioning →
   choose strategy → verify, with the evidence inline.
2. **The capstone is scheduled but not packaged.** Aug 12 QIR
   pre-registration is the one thing that converts backtests into a
   live falsifiable demonstration — it needs a committed bundle, not an
   intention.
3. **"AI" is demonstrated as statistics + rules + small ML gates**
   (flow-forecast L1–L6, monitor scoring, regime detection). The
   LLM-assistant layer the desk would actually feel (instruction
   parsing, exception narration, EOD drafting) exists as deterministic
   automations — the AI framing needs to be argued explicitly, not
   assumed visible.
4. **Heuristics debt:** CROWDING_PATH_ADJ v1, refined_rule frozen but
   unvalidated, buffer calibrated on one pair. All disclosed — but the
   plan should show WHEN each gets its data (Aug/Sep cycles).

### Goal 2: institutionally useful to a PT desk end user

**Feature-rich; organized around modules, not around the user's day.**
The JD maps well: execution strategy (agents 3/6/14, frontier),
liquidity/vol monitoring (agents 2/9/11, run-rate re-forecast),
impact/slippage (cost model, IS attribution, markouts), cross-market
(timeline, holiday/settlement, FX notes), regulations (lot sizes,
limit bands, short-sell rules, circuit breakers, rules versioning),
audit records (best-ex store, audit packs), post-trade
(recon classifier, settlement calendar). QBR covers the client cycle.

**Gaps, in end-user order of pain:**
1. **No run-of-day entry point.** A dealer's day is pre-open → auctions
   → continuous session → closes → post-close, across staggered Asia
   time zones. Our pages are organized by capability. The first thing a
   desk user should see is "what does my day look like NOW".
2. **No golden-path demo.** No single client basket carried end-to-end
   through intake → normalize → compliance → risk/blind profile →
   quote sketch → strategy → simulated fills → TCA → client email →
   audit pack → recon. Every stage exists; the THREAD does not.
3. **Outputs are app-bound.** Desks live in Excel, email, and chat.
   Several artifacts export; many don't. Every client-facing or
   audit-facing artifact needs one-click text/xlsx export.
4. **Capacity/calendar awareness is implicit.** We know month-end MOC
   concentration, expiry clusters, index effective days (this week's
   conversation) — but there is no capacity view that warns "Aug 31 is
   MSCI implementation + month-end; your auction footprint is X% of
   expected MOC".
5. **Client-interaction surface is thin relative to execution surface.**
   QBR exists; per-trade client communication (pre-trade summary the
   sales trader forwards, intraday exception notes, post-trade recap
   email) is partially built (EOD draft) but not presented as a client
   thread.

---

## Part 2 — The plan

Sequenced to the real calendar: **Aug 12** MSCI QIR announcement,
**Aug 21** Vietnam eligible list, **Aug 31/Sep 1** MSCI implementation
(+ month-end), **~Sep 4** FTSE announcements, **Sep 21** FTSE effective
+ Vietnam reclassification. Interview likely lands inside this window —
every workstream ends in an artifact usable in the room.

### W1 — Package the evidence (Jul 28–30) → Goal 1

1. **Flagship memo** `docs/INDEX_EVENT_PLAYBOOK.md` (+ docx/pdf):
   the full loop in ~10 pages, evidence inline, one diagram, every
   claim linked to its case study and its test. This becomes THE
   interview artifact.
2. **README restructure into the two-goal frame:** research narrative
   (Goal 1) and desk product (Goal 2) as the two top-level entry
   points; case-study index table with one-line verdicts.
3. **10-minute guided demo path** (extend Page 0 tour): scripted
   click-path that hits the golden thread; matching one-page quick
   start (md + docx) for a desk user.

### W2 — Build the desk's day (Jul 31–Aug 6) → Goal 2

4. **Run-of-day view** (new Page: "Today"): time-zone-staggered Asia
   session ribbon (already in pt_dealer timeline) + attention queue +
   auction countdowns + capacity/calendar flags (month-end, expiry,
   index events from agent 12) — the screen a dealer would leave open.
   Reuses existing engines; this is composition, not new machinery.
5. **Golden basket thread:** one canned client basket (CSV in
   `examples/`) carried through all 10 stages with state persisted
   between pages; "next step" buttons; every stage exports (xlsx or
   email text). Ends with audit pack + recon exceptions.
6. **Capacity view:** expected MOC share per name vs auction-size
   history (volume data we already pull), flagged against the calendar
   (Aug 31 warning as the live example).
7. **Client thread artifacts:** pre-trade one-pager (exists as desk
   pack — re-skin as client-facing), intraday exception note template
   fed by alerts, post-trade recap email fed by TCA + venue/impact
   attribution. Three exports, one basket.

### W3 — The QIR capstone (Aug 7–11, hard deadline) → Goal 1

8. **Pre-registration bundle** committed before Aug 12: predictions
   with confidence tags for 2–3 markets (TW, KR, JP screener),
   crowding overlay from the live forward archive (running since
   Jul 22), expected flows, per-name strategy picks (crowding-adjusted
   frontier), and the frozen refined_rule's calls. One doc + one JSON,
   git-timestamped. Includes pre-declared grading criteria.
9. **Daily forward fetch discipline** through Sep 21 (short balances,
   block tape, TDCC weekly, institutional flows) — builds the first
   REAL pre-announcement archive so Phase-0 tests stop being
   reconstructions.

### W4 — Live grading loop (Aug 12 → Sep 21) → both goals

10. Grade the Aug 12 bundle when announcements land; publish the
    scorecard unedited (wins AND misses — the honesty culture is the
    product). Repeat pattern for FTSE Sep + Vietnam.
11. **Aug 31 implementation-day observation pack:** capture T-day
    volumes/auction shares for graded names; validate refined_rule
    out-of-sample (its first frozen test); update completion clocks
    daily through Sep 4.
12. **Vietnam Sep-21 view** (the sales-trader-track artifact): flow
    sizing from EM-tracker AUM, HOSE band/foreign-room constraints,
    execution plan under the constraints our platform already models —
    the "bring a view" doc for interviews.

### W5 — Institutional hardening + the AI argument (parallel, Aug)

13. **`docs/AI_ON_THE_PT_DESK.md`:** JD bullet → workflow → what we
    automated → estimated minutes saved per day/cycle → what needs
    desk data. Explicitly separates: deterministic automation, ML,
    LLM-assist (and where each is trustworthy enough for a regulated
    desk — human-in-the-loop points marked). This is the Goal-2 thesis
    document.
14. **Auditability pass:** every recommendation surface stamps
    rules_version + inputs hash into the best-ex/audit stores
    (partially done; make it universal).
15. **Error/exception playbook page:** wrong-basket, fat-finger,
    halted-name mid-basket, failed-settle — each mapped to the
    existing automation that catches it + the manual procedure. Desks
    trust tools that plan for failure.
16. **Excel-first exports everywhere** (xlsxwriter already in stack):
    any table a client or ops team would touch gets a download button.

### Deliberately NOT in the plan

Live order routing, FIX connectivity, real client data, intraday tick
streaming: out of scope by constraint and honestly labeled as such in
DESK_DEPLOYMENT_PLAN.md (which already specifies the institutional
versions). No new prediction markets until the current ones are graded
live — depth over breadth through September.

### Acceptance criteria

- A PT dealer with zero context reaches a useful screen in <5 minutes
  via the quick start, and can export something they'd actually send.
- The full research loop is readable in one sitting (flagship memo).
- The Aug 12 bundle exists BEFORE Aug 12 (git timestamp is the proof).
- Every JD bullet maps to a demonstrated feature + an AI-efficiency
  claim with a number attached.
- Suite stays green; every new artifact has a test or a scripted check.

### Effort estimate

W1 ≈ 2 sessions, W2 ≈ 3–4, W3 ≈ 1–2, W4 ≈ ongoing small sessions,
W5 ≈ 2–3. Front-load W1+W3 (interview-critical, calendar-locked);
W2 is the biggest build; W4 is calendar-driven; W5 fills gaps between.
