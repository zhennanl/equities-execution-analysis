# HANDOFF — Load this file to continue with full context
## Next mission: brainstorm + build something INTERACTIVE AND PRESENTABLE for the PT traders at CLSA

*Written 2026-07-29 (session 9h close). Bill is interviewing for a CLSA
Program Trading Stock Dealer role; this project is his interview-prep
platform and demo asset. This file is the complete context capsule for
a new chat.*

---

## 1. Project identity & standing rules (NON-NEGOTIABLE)

- **Repo**: `C:\Users\Bill\Downloads\execution_analytics` (Python /
  Streamlit, free public data only). Sandbox path:
  `/sessions/<session>/mnt/execution_analytics`. Run scripts with
  `PYTHONPATH=.`; sandbox bash calls cap at ~40s and reap background
  jobs — long fetches are built RESUMABLE and run in timed chunks.
- **Autopilot mode is standing** — proceed without asking.
- **Bill handles ALL git commits personally.** Claude never commits.
- **Honesty culture**: NO-CALL over fabrication; never tune on known
  answers; misses always ship; in-sample tunes labeled; estimates vs
  exact values always distinguished; one-event findings carry caveats
  (this discipline paid off — see the decade revision below).
- **Session log**: `docs/SESSION_SUMMARY_2026-07-08.md` — prepend a
  new `## Session 9i` block per work chunk (newest first; ordering
  slips have happened — check placement).
- **Test suite**: pytest, currently **416 green**. Keep it green;
  new features get tests (findings get PINNED as tests — e.g. the
  violence-curve null, the decade CN-adds sign).
- Bill's style: concise, direct, no fluff. Explain economics slowly
  when asked "why"; he pushes until the logic clicks.

## 2. What the platform is (the 4-step lifecycle)

Streamlit app; the flagship is `views/page6_lifecycle.py` — 5 tabs
mirroring the index-rebalance trade lifecycle from
`docs/INDEX_REBALANCE_TRADE_LIFECYCLE.md`:
1. **Step 1 — Pre-event marketing**: event-driven prediction engine
   (`agents/review_engine.py`, 8 logic layers documented in
   `docs/PREDICTION_LOGIC_LAYERS.md` L0-L9), crowding reads, flow
   estimates, gradable predictions w/ methodology expanders.
   PIT-graded: May-2026 TW 17/17 adds; Asia: CN 8/8, JP 3/3, HK 1/1.
2. **Step 2 — Window management**: `agents/event_window.py` planner
   (liquidity/risk sheet, ADV-days, auction footprint %, borrow via
   TWT93U bal/(bal+quota), start schedule, discretion matrix w/
   rationale) + **Time Machine** (`agents/time_machine.py`): pick any
   of 38+ keyed events 2016-2026, any day in its window, STRUCTURAL
   PIT gate (future rows never loaded), as-of Step-2 decision state.
3. **Step 3 — T-day execution**: cockpit (morning check, lunch
   checkpoint, close sequence), auction countdown, indicative read
   rule (THIN/RICH), run-sheet. `docs/STEP3_TDAY_DESIGN.md`.
4. **Step 4 — Execution insights**: `agents/execution_insights.py`
   TCA vs estimate, discretion counterfactual grading, reversal
   grades, prior updates, client debrief renderer.
Docs: `docs/AI_INTEGRATED_WORKFLOW.md` (framework + CLSA gap-close +
ideal workflow per step).

## 3. Data assets (all free, all cached in `data/`)

- **Answer keys**: MSCI STPublicLists 2015-2025, 44/44 quarters
  parsed (`data/msci_archive/`, 176 files incl. PR txts w/ ann+eff
  dates); FTSE TW50 via TIP `/news/{id}` enumeration: 41 events /
  100 changes 2016-2026 (`data/ftse_tw50_changes.json`).
- **TW official**: TWSE MI_INDEX all-stock daily (2021+ verified,
  cache `tw_history/quotes.json` 190 days), STOCK_DAY per-name
  monthly to 2016 (`tw_history/stock_day.json`, 207 code-months),
  TWT93U borrow, TWT38U foreign, 5-second auction archive
  (May-29/Jun-18 studies), MI_5MINS.
- **Multi-market**: baostock CN daily (deep), yfinance JP/HK daily
  (deep; intraday walls 60d), SFC HK shorts ALL 724 weeks to 2012,
  JPX ~1mo retention (our archive started Jul-2026).
- **NEW (9h)**: alias bridge MSCI-English-names -> local codes
  (`data/decade_bridge.json`, 611/933 matched via HKEX Connect
  lists + JPX + HKEX masters in `data/masters/`); decade windows
  `data/decade_windows.json` (776); `data/tw_limits.json` (23 days
  full-tape OHLC + locked-book flags).

## 4. Findings hierarchy (what we can SHOW a desk, all measured)

1. **Prediction grades**: TW May-2026 17/17 adds PIT; decade TW
   backtest to honest plateau (review-cadence rule: SAIR-only
   migration sweep; deletion-as-hazard ~2/3 conversion).
2. **TWAP/VWAP/MOC decade costs (TW, 109 name-events)**: FTSE adds —
   window-VWAP beat close −164bps median (60% win), halved all-in
   cost vs MOC (+398 -> +196 vs arrival); FTSE deletes — MOC won
   (+57 to spread); VWAP dominated TWAP everywhere. Daily VWAP is
   EXACT (value/vol); TWAP=(O+H+L+C)/4 labeled estimator.
   `docs/TWAP_VWAP_MOC_STUDY.md`.
3. **THE DECADE REVISION (9h)**: the May-2026 "class inversion"
   (MSCI adds pop-decay/WAIT, deletes press/WORK) does NOT
   generalize — 367 print-validated name-events 2015-2025 show CN
   adds grind up TW-style (LINEAR −234, working beats print),
   deletes ~flat. May-2026 rule demoted to hypothesis; Aug-2026
   arbitrates. Plus: only ~25% of CN name-events print materially
   (10-20% IF vs retail tape); **JP edge FLIPPED after 2022**
   (Greenwood-Sammon disappearance arriving in Asia); HK unstable;
   2019-21 was the golden era. `docs/WINDOW_STUDY_DECADE_CNJPHK.md`.
4. **Auction microstructure (TW)**: May-29 print = 24.9% of market
   value in one print; TW50 adds 44-71% auction shares; book
   retention 14% withdrawal vs 24% baseline (indicative MORE honest
   on event days); violence-curve v1 NULL (share does not predict
   gap, R2~0, pinned); unconditional gap prior |125|±85bps.
5. **Limit moves (9h)**: baseline 3.0%/2.0%/2.2% touch-up/locked/
   touch-down; ~95% of locked closes have empty books; print days
   1.7-2.2x. **Case A: 6919 deletion locked LIMIT-UP into its own
   deletion print** (sell filled 100% at cap; early selling −1,800
   bps worse). **Case B: 2344 add locked LIMIT-DOWN into its own
   add print** (buy filled at floor, −14% vs T-2). Lesson: the
   print price is set by the CROWD'S EXIT, not the flow's
   direction; print-day locks FAVOR the obligated side.
   `docs/case_studies/TW_LIMIT_MOVES_2026.md`.
6. **Reserve/churn stats**: TW50 reserve conversion 18%/27%; adds
   deleted within 4 reviews 28.6%.
7. **Literature map** (`docs/LITERATURE_INDEX_REBALANCE.md`):
   Greenwood-Sammon, Chinco-Sammon 3.15x, Arnott delay=23bp/yr,
   DFA +4/−5.7 reversal, Sammon-Shim 47-70bp drag, Gabaix-Koijen —
   our positioning: we work where the effect lives, with name-level
   PIT grading the literature lacks.

## 5. This chat's conceptual threads (Bill worked through these)

- **TE-vs-TD economics**: TE = constraint (quadrature — event
  deviations consume ~1bp of a 40-100bp budget), TD = objective
  (mean shifts add linearly, 3-8bp/yr from avoiding the crowd);
  asset owners DO relax TE for TD (sampled/pragmatic mandates, EM
  norm); the side/class cost asymmetry is the evidence a manager
  shows an owner to justify a deviation envelope.
- **MOC-is-the-commodity framing**: most passive flow is MOC; the
  desk's product is everything wrapped around it (guarantee
  pricing, failure detection via indicative, envelope minority,
  live color, dislocation clients, the research loop).
- **PT-desk flow taxonomy beyond rebalance** (Bill's 7-type revenue
  ranking) + per-flow analytics/AI:
  `docs/PT_DESK_ANALYTICS_BEYOND_REBALANCE.md` — fingerprinting,
  transitions, drift-trigger model, basket-embedding cost oracle,
  ETF nowcasting, dividend-point forecasting, CA radar. Three AI
  modes: parse&retrieve > pattern&predict > optimize; LLMs never
  rank or decide.
- **Monthly rebalance = the unconditional index event** (quant
  signal refresh + drift correction + cash-flow plumbing, all
  benchmarked to month-end closes).
- **FTSE keys for CN/JP/HK = separate archaeology** (TIP was a
  Taiwan-lucky structure); queued value order: Hang Seng (HSIL PDF
  archive), China A50, TOPIX/Nikkei.

## 6. Pending / standing items

- **Aug-11 finalization protocol** (STANDING, time-critical):
  refresh caps, scan boundary entrants, resolve TW AI-quartet via
  EWT, verify, Bill commits before Aug-12; grade after Sep-1;
  indicative-auction archiver standing from Aug-11. Aug-2026 also
  ARBITRATES the demoted May-2026 inversion hypothesis.
- Queued builds: bounded-fill replay simulator (indicative
  convergence commit-time rule, THIN/RICH backtest, fade haircut —
  data already cached), Hang Seng key archaeology, CN Step-1
  decade PIT via baostock, northbound/CCASS fetchers, futures-roll
  analytics, Step-1 note reordering per factor ranking.
- Suite must stay green (416). Bill commits.

## 7. THE NEW MISSION (this new chat)

Brainstorm, then build, something **interactive and presentable to
CLSA PT traders** — a demo that lands in a trading-floor
conversation. Constraints and assets to reason from:
- Audience: PT dealers/desk heads — skeptical, time-poor, respect
  measured numbers and PIT discipline, allergic to black boxes.
  Every number in the platform traces to public data + a documented
  rule; misses are shipped (this is the differentiator — lead with
  graded predictions and the revision story, not polish).
- Existing interactive surface: the Streamlit 5-tab lifecycle page
  incl. Time Machine replay (any event, any day, no future
  peeking) — likely the demo backbone. Gaps: it's a local app
  (deployment story needed), no guided "tour" mode, no
  single-screen wow artifact.
- Strong demo-able moments already built: 17/17 PIT grade reveal;
  Time Machine day-slider on a real event; the 6919/2344 limit-lock
  case studies; TWAP/VWAP/MOC decade tables; the JP-edge-death
  chart; May-29 auction anatomy (24.9% print).
- Ideas floated but NOT committed (fresh brainstorm welcome):
  guided demo script/video, one-page HTML interactive artifacts,
  live Aug-2026 event as the centerpiece (the event finalizes
  Aug-11 and prints Aug-31 — a LIVE prediction with skin in the
  game is the strongest possible pitch), pitch-deck wrapper,
  desk-drop one-pager per event.
- Bill will drive scope; ask clarifying questions via the question
  tool BEFORE building; then autopilot.

*Verify environment on load: `PYTHONPATH=. python -m pytest -q`
(expect 416 passed), then read the session summary's newest 9h
blocks for anything this capsule compressed.*
