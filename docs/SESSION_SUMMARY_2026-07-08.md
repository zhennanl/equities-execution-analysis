# Session Summary — 2026-07-08

## Session 9i continued-43 (2026-08-05) — PIT TIME-TRAVEL: any-date index reconstruction (TW)
- agents/pit_constituents.py: members_asof(date) = EWT anchor
  reverse-rolled through reviews by EFFECTIVE date (changes bind at
  eff close; resolved-state line names the last review) + interval
  logic for delisted names; ladder_asof(date) = full member list
  RANKED BY CAP as-of (vintage caps) + PIT GMSR walk + candidates
  (dels = buffer band w/ class labels incl. hard-floor breach;
  adds = dual hurdle + 0.15 float floor); stale-price guard (>45d)
  keeps delisted names out of later frames (the Inotera-at-2019
  trap, caught in validation)
- VINTAGE HARVEST EXTENDED to all current members: 110 -> 150
  names x (shares+prices) 2015-2026 — never-changed members now
  priced at any historical date; **May-01 frame resolves the
  pre-May index EXACTLY: 83 members = the factsheet number**
- Validation: May-01 dels candidates led by the 7 official
  deletions; Nov-01 holds all 7; 2019 frame renders (92 members,
  GMSR $2.06B); flagged 4551 excluded
- UI: "Test with historical data (PIT)" toggle inside the
  constituent viewer (TW) — date picker -> resolved-state banner ->
  full ranked list -> "Next step — the candidates" two-column
  (delete/add) w/ breadth note; st.cache_data 1h; sandbox
  screenshot verified. +1 pinned test; suite 442 green

## Session 9i continued-42 (2026-08-05) — CONSTITUENT VIEWER (market selector + cached list)
- UI (page6 Tab 1): "Current MSCI constituents by market" expander
  — selectbox over 10 APAC markets -> full Standard member list
  (ticker, company name, confidence tier CONFIRMED/LIKELY) from the
  apac_members.json cache; per-market source line (fund + as-of +
  composite cross-check); IMI-variant markets show the composite
  subset as Standard w/ note
- REFRESH POLICY implemented event-driven, per user spec: the
  members sentinel (daily 12-fund diff) now REWRITES the canonical
  cache whenever provider changes reach the tracking funds (review
  implementations + mid-quarter corporate events both trigger);
  cache-refresh failures surface as sentinel ALERTs; nothing
  refreshes on a timer for its own sake
- Verified live in sandbox: Taiwan 79 members / 77 confirmed by 2+
  funds, names rendered (1101 Taiwan Cement ... 2330 TSMC);
  +1 pinned test (data contract: names coverage >90%, TW anchors,
  IMI restriction); suite 441 green

## Session 9i continued-41 (2026-08-05) — UI PROPOSAL: the lifecycle site
- docs/UI_PROPOSAL_LIFECYCLE_SITE.md. Thesis: THE TIMELINE IS THE
  INTERFACE — traders think in where-are-we-in-the-event; site
  spine = event timeline w/ 4 station cards; three questions rule
  every screen (where are we / what changed / what do I do)
- Persistent Event Context Bar (event selector LIVE vs REPLAY,
  phase strip w/ today marker, sentinel light, unconfusable mode
  badge); Home = timeline + station cards (one headline number +
  alert count each) + deltas-only brief strip
- ONE workspace grammar all 4 steps: LEFT names table / CENTER one
  picture / RIGHT action rail (advice drafts, alerts, provenance,
  sign buttons) — learn step 1, know all 4. Honesty affordances
  everywhere: provenance popovers, SIMULATED badges, ~estimates
  muted, grades inline
- REPLAY = same workspaces + time travel: date scrubber renders
  everything AS-OF (PIT enforced structurally), reveal-outcome
  toggle (default OFF), session library doubles as public track
  record. Prerequisite: data/sessions/<tag>/ snapshot convention +
  sessions.json registry
- All tiles map to existing JSON producers (assembly not new
  analytics); build order: context bar+home -> Step-2 workspace
  first (live proving window) -> re-hang 1/3/4 -> replay may26 ->
  polish. Streamlit-feasible v1; artifact-driven design ports

## Session 9i continued-40 (2026-08-05) — STEP34 BUILD ORDER EXECUTED (items 1-6)
- post_event.py: PLAYBOOK strategy (scenario-conditional splits w/
  NEW T+1-close leg; vintage-cache fallback when stock_day ends at
  T) + ARCHETYPES panel (EM_TRACKER MOC-obliged / IMI_TRACKER /
  ACTIVE_FLEX / HF_PROVIDER sign-flipped) + archetype_grading
  (advised vs best-hindsight, regret) + render_tca_letters (drafts,
  SIMULATED basis stated) — build_pack wires Step-2 scenarios in
  (closes the 2->3->4 loop)
- **MAY-26 REGRADE: OVERCROWDED names' playbook split beat all-MOC
  by ~590bps (2324 -597 / 2474 -590) via the 60% T+1 defer leg —
  Step-2's crowding calls converted to execution value; 1402 the
  honest heterogeneity case (OVERCROWDED but no reversal, +140)**
- agents/cockpit_agent.py: pre-open card assembler from existing
  artifacts (8 cards may26 rehearsal) + desk-note DRAFT
- scripts/t1_orchestrator.py: data-arrival gate (refuses partial
  grading; names what's missing) -> unattended pack + TCA drafts;
  may26 run [GRADED 7/7]; aug26 slot filled by announcement agent
- scripts/auction_capture.py: TWSE MIS 5-sec snapshot capture;
  REHEARSAL PASSED live (2330/1101 parsed) — plumbing validated
  before the Aug-31 first live capture
- Pinned: OVERCROWDED playbook <-400bps anchor, archetype math +
  HF sign-flip unit test, cockpit/TCA artifacts; legacy pack test
  updated for grown strategy set (intentional). Suite 440 green

## Session 9i continued-39 (2026-08-05) — STEPS 3-4 SIMULATION + AGENTIC DESIGN DOC
- docs/STEP34_SIMULATION_AGENTIC_DESIGN.md. Simulation w/o client
  fills: synthetic orders on the REAL tape (24 events, discrete
  auction bars) under three honesty rules — participation ceilings
  (~15%/bar), impact adders from MEASURED playbook tolls (not
  theory), rankings-not-absolutes on identical tape. Exact-vs-
  modeled table stated. SYNTHETIC CLIENT PANEL replaces client
  records: archetypes (EM tracker MOC-obliged / IMI tracker /
  benchmarked active / liquidity-provider HF) — grade what we
  WOULD HAVE TOLD each client type. Validation anchors: simulation
  must reproduce measured findings (gap-against-obligated, reversal
  cells, May-26 OVERCROWDED fade dominance) — tape wins by
  definition
- Agentic: Step 3 = calendar-armed cockpit pipeline (pre-open
  card assembler, 13:00/13:25 updaters, limit-move re-router,
  5-sec auction capture from Aug-31) + Step 4 = data-arrival-gated
  unattended post-event pack (leaderboard incl. NEW playbook-guided
  strategy, archetype advice grading, scenario self-grade,
  crowding resolution, T+5 reversal tracker) -> TCA letter drafts;
  lessons may PROPOSE rules, adoption only via lab registry.
  Efficiency ledger: manual residue = sign-off, self-grade review,
  lab adoption. Build order 1-6 declared (playbook-guided strategy
  first — closes the 2->3->4 loop)

## Session 9i continued-38 (2026-08-05) — L0 SENTINEL SYSTEM COMPLETE
- agents/sentinels.py: six watchers, fetch+diff+one-line contract
  (never judge, never trade): shorts (wraps freshness guarantee),
  members (12 funds/10 markets daily diff — mid-quarter exits =
  corporate-event ALERTS, the Inotera class automated), ladder
  (pool entries/exits re-priced daily), calendar (T-countdowns +
  per-card must-start-by, finalization-protocol alarm at T-1),
  fx (TWD vs pinned 32.5, >2% drift alert), artifacts (mtime DAG:
  published artifact older than its inputs = regenerate-before-
  quoting alert). Statuses OK/CHANGED/ALERT/DEGRADED; state diff in
  sentinel_state.json; report sentinel_report.json; slow watchers
  TTL 4h; CLI per-sentinel; Windows schtasks line documented
- FIRST LIVE RUN all green: shorts OK (tolerance), members 10
  markets baseline, ladder pool stable 17, calendar T-6/T-26, FX
  32.52 (+0.1%), artifacts 4/4 current
- UI: sentinel strip atop lifecycle Tab 1 (auto-expands on
  ALERT/DEGRADED); docs/SENTINELS_GUIDE.md — trader guide (what
  each watcher is, why care, typical alerts, the analyst reads six
  lines and thinks only about the red ones; scheduling)
- +1 pinned test (offline-safe: calendar/artifacts logic, report
  schema, SYNTHETIC staleness fires the alert); suite 439 green;
  sandbox screenshot verified

## Session 9i continued-37 (2026-08-05) — STEPS 1-2 REVIEW -> LAYERED AGENTIC WORKFLOW DOC
- docs/STEP12_AGENTIC_WORKFLOW_REVIEW.md: state inventory (Step 1
  deep/validated, Step 2 modeled/1-event-graded), efficiency
  critique (analyst-run, pull-not-push, TW-deep/9-shallow), and the
  4-layer agent design: L0 data sentinels (scheduled fetch+diff;
  membership diffs become corporate-event ALERTS) -> L1 signal
  agents (ladder refresh, Step-2 daily tracker w/ scenario
  MIGRATIONS as the signal, announcement-day agent for Aug-12) ->
  L2 synthesis (morning brief deltas-only, client-note drafter
  keyed to client TYPE per composite math, meeting prep) -> L3
  surface (Desk Brief tiles pull, alerts push, provenance Q&A,
  what-if toll tool). HUMAN GATE preserved: agents never ship
  calls/notes; conviction gate between L2 and clients; agent output
  graded like analyst output
- Public-data ceiling stated (everything automatable free; limits:
  official floats/FIF, price-cutoff date, 5-sec auction history,
  non-TW SBL, client flow unseen) vs CLSA institutional upgrade
  ranked: internal flow history #1 (proxies->ground truth,
  capacity-aware advice, compliance wall stated), licensed floats
  #2 (kills last data-blocked step), tick backfill, borrow desk,
  ecosystem. DESIGN POINT: same architecture both worlds — better
  data makes it sharper, not different
- Priority: sentinels+scheduling, Step-2 live tracker for the
  Aug-12->Sep-1 proving window, announcement-day agent REHEARSED
  pre-Aug-12

## Session 9i continued-36 (2026-08-05) — STEP-2 LIQUIDITY-SUPPLY MODEL (interview lessons 1+2 built)
- User: predict effective-date liquidity supply from PIT window
  data. agents/liquidity_forecast.py: crowding_ratio = accumulated
  pre-positioning / expected passive flow (class prior x baseline
  ADV); legs = flow completion (volume, primary) + SBL borrow build
  (TWT93U cache) + foreign-holding delta w/ direction-consistency
  flag (FinMind) + retail margin shorts; scenario map
  UNDERSUPPLIED/BUILDING/WELL-SUPPLIED/OVERCROWDED w/ client advice
  strings — thresholds 0.3/0.7/1.2 DECLARED BEFORE the demo ran
- **MAY-26 PIT DEMO (frame frozen T-1=May-28): the two OVERCROWDED
  calls — 2474 (completion 1.70) and 2324 (2.04, and the only
  wrong-direction foreign flag: foreigners BUYING a delete) — were
  exactly the two monster reversals (+26.3% / +28.2% T+3). The one
  UNDERSUPPLIED call (2610) printed the smallest delete multiple
  (9.9x vs 18-42x). 2324 cross-checks post-event's +2,820bps.**
  data/liquidity_forecast_may26.json; docs/STEP2_LIQUIDITY_MODEL.md
  (framing, observables, scenario advice, honesty box: n=8, prior
  is weakest input 10-42x realized, SBL coverage partial; ML
  calibration path = decade replay ~150 name-events, registry v4)
- Aug-2026 live use: run daily from Aug-12 on the actual list —
  the client note writes itself from the advice column
- +1 pinned test (OVERCROWDED->reversal linkage, PIT frame check,
  calm-scenario reversals <12%); suite 438 green

## Session 9i continued-35 (2026-08-05) — MATERIALITY AUDIT CLOSED: foreign-room screen + ladder shadow
- Book-step audit correction: dual float-cap hurdle (§3.1.2.3) was
  ALREADY in predict_msci (min_ffcap_frac_of_add "blocked add") —
  only the workbench view had ignored it. Truly missing: foreign
  room (§3.1.2.6) + true ladder mechanism (§3.1.4-3.1.5)
- reconstitution.py: min_foreign_room=0.15 — new adds blocked when
  universe carries foreign_room_frac < 15% (column optional; zero
  impact on graded paths — May add MPI had ample room). Unit-tested
  both directions
- agents/ladder_engine.py — SHADOW ENGINE (book mechanism): 77
  confirmed members x current caps (vintage cache + FinMind live
  top-up w/ resumable cache incl. FOL room per name) -> full-member
  ladder -> inclusive delete pool <1.15x GMSR ->
  data/ladder_aug26_tw.json: **first full-breadth Aug-26 TW pool:
  17 names, bottom 6919 0.76x / 2834 0.84x / 2609 0.84x / 1101
  0.87x / 3529 0.88x / 5871 0.91x / 3533 0.99x** (vs the 16-name
  frame that could see only 1101). GMSR CAVEAT stated in-file:
  members+tail walk w/ default floats -> GMSR $6.5B ABOVE boundary
  frame's $4.8B — errs INCLUSIVE (safe for pool, wrong for calls,
  hence shadow); union-universe reconciliation queued
- Aug-12 grades BOTH engines (legacy locked call + shadow pool);
  suite 437 green

## Session 9i continued-34 (2026-08-05) — APAC CONSTITUENT PIPELINE (all 10 review markets)
- TW method generalized: scripts/apac_members_harvest.py ->
  data/apac_members.json — single-country iShares anchor +
  composite subset cross-check (EEM for EM / EFA for DM) per market
- RESULTS (live harvest): **Japan 168/168, Australia 47/47,
  HK 25/25, India 165/165, Malaysia 21/21 — PERFECT agreement;
  Korea 77 confirmed (1 anchor-only); Taiwan 77 (known); China 571
  confirmed of ~576 (5 diffs = CA churn at breadth)**
- TRAPS hit+solved: wrong product ids serve OTHER funds w/ 200
  status (name-header validation mandatory; found EWM/EPHE/INDA ids
  by probe: 239669/239675/239659); gzip responses; EEM Location
  string is "Korea (South)"; **EIDO/EPHE track IMI variants -> their
  lists are SUPERSETS; composite subset IS the Standard membership
  (Indonesia 11, Philippines 10)**
- docs/CONSTITUENT_PIPELINE_FRAMEWORK.md: full recipe (anchor ->
  composite -> tiers -> count reconcile -> reverse-roll -> delete
  pool), source table w/ verified ids+counts, traps, per-market
  third-fund candidates, validation standard (last-2-reviews 7/7
  requirement), vintage-cap source queue (J-Quants/KRX/NSE)
- Pre-announcement answer: iShares CSVs update daily (~1-2d lag);
  membership only moves at effective dates + corporate events ->
  full member list per market IS obtainable before any
  announcement; delete pool = bottom ladder per framework §5
- +1 pinned test (range-based, review-proof); suite 436 green

## Session 9i continued-33c (2026-08-05) — THIRD FUND UNANIMOUS + COUNT-ANCHOR FIX
- Yuanta 006203 (INDEPENDENT manager, full-replication, quarterly
  disclosure via MoneyDJ, Jun-30): 77 names, all mapped via FinMind
  name registry — **EXACTLY the EEM∩EWT set. Three funds, two
  managers, unanimous on 77.** EWT-only 1602/2418 = EWT artifacts
- **FACTSHEET MYSTERY SOLVED: 83(pre-May) − 7 dels + 1 add = 77.**
  The "sampling gap" never existed — our count anchor was the
  PRE-May factsheet. Funds hold the full index
- FIX CASCADED: Aug-26 live paths re-anchored 83→77 (funnel_demo
  prediction run, universe_workbench); GMSR robust ($4.78B
  unchanged — 6-member shift barely moves the 85% line), zero-call
  posture unchanged; May-26 PIT paths KEEP 83 (correct pre-May).
  tw_membership_sources.json now carries all three funds +
  3-way consistency string; suite 435 green

## Session 9i continued-33b (2026-08-05) — MULTI-FUND MEMBERSHIP CROSS-CHECK
- User: why does EWT differ from MSCI, use multiple funds? Reasons
  documented: sampling license, FOL walls (unbuyable names),
  snapshot timing/corporate events, line representation, 25/50
  weights making bottom names likeliest omissions
- SECOND SOURCE via building blocks: EEM (MSCI EM Standard) Taiwan
  subset = MSCI TW Standard membership. Result: **EEM 77 names,
  STRICT SUBSET of EWT's 79** (EWT-only: 1602, 2418); zero
  EEM-only names -> data/tw_membership_sources.json w/ confidence
  tiers (CONFIRMED both / LIKELY one / FLAGGED interval-only e.g.
  4551 — kept in delete pool by design). Caveats stated: both
  BlackRock (partially independent); 83-count factsheet gap
  unresolved (sampling vs count-date vs securities-vs-companies);
  truly independent third source = Yuanta 006203 local ETF (queued)

## Session 9i continued-33 (2026-08-05) — THE BREADTH FIX, PROVEN (delete pool 7/7 + 7/7)
- User: does the shortlist cover the May-26 key, and how to find the
  deletion pool w/o a licensed list? scripts/delete_pool_validation
  .py: pool = EWT anchor reverse-rolled (4551-class flags excluded)
  + vintage caps + generous 1.15x-GMSR band
- **MAY-26: deleted names are EXACTLY the bottom 7 of the
  reconstructed ladder (ranks 0-6), perfect separation — all 7
  below 1.0x GMSR, every survivor >= 1.05x. The 16-name frame's 3
  false calls (1101/1326/2207) VANISH in the 110-name frame (better
  GMSR).** Adds: 1/1 (MPI ranked, 12 float-gap false positives
  honestly displayed)
- **NOV-25 (the historical 0/7 breadth failure): 7/7 deletions
  present, occupying 7 of the bottom 8 slots.** THE binding TW
  constraint (PREDICTION_ENGINE_REVIEW §5, TAIWAN_MARKET_ANALYSIS
  §6) is STRUCTURALLY SOLVED by EWT-anchor + FinMind vintage caps
  — and next-tier names visible in the Nov-25 ladder (2610/2474/
  1102 survived Nov-25, deleted May-26) show hazard conversion
  live in the data
- Pinned test (both events 7/7, May-26 exact bottom-7); suite 435
  green. NEXT: fold the EWT-ladder universe into the live Aug-26
  engine run + full 46-review PIT backtest on this frame

## Session 9i continued-32 (2026-08-05) — MAY-26 PIT WORKBENCH + THE CONSTITUENT ANSWER
- User: pretend it's one day before the May-26 announcement, build
  the workbench view PIT, incl. ALL constituents + tentative adds
  w/ explicit derivation. CONSTITUENT ANSWER (the data question):
  full current membership = iShares EWT holdings CSV (free, daily,
  public; MSCI TW 25/50 — membership ~= Standard; 79 equity codes
  cached data/ewt_members.json) REVERSE-ROLLED through official
  reviews to any vintage; delisted names via change intervals.
  Fixed the bug this exposed: never-changed members outside the
  16-name boundary set (6505 etc.) were misclassified non-members
  under interval-only logic
- scripts/pit_workbench_may26.py -> universe_workbench_tw_may26pit
  .json: 110 names at Apr-30 caps (vintage cache), 46 members
  reconstructed, PIT GMSR $4.64B / SAIR bar $5.34B / floor $2.32B,
  6-step derivation strings, per-name foreign_12m_pp + cap_12m_chg
  (the EDA features) + ff_estimated flags + prior_status
- THE HONEST FINDING (now a UI warning box): 13 non-members cleared
  0.85x the full-cap bar PIT; only 1 was added (6223 MPI, ranked
  clearly). The other 12 are mostly ex-members deleted years ago
  for float/liquidity reasons that persist -> full-cap proximity
  alone ~8% precision; binding discriminators are floats/FIF (our
  stated #1 gap). Raw ladder alone would mislead — this is WHY the
  engine layers screens/churn/probabilities
- UI: workbench expander got a Frame selector (Aug-26 live /
  May-26 PIT validation); PIT view shows derivation, graded
  tentative adds, full universe table; sandbox screenshot verified
- +1 pinned test (EWT anchor logic: giants members, May-26 dels
  members at Apr-30, MPI non-member + ADDED-hit, >=40 members);
  suite 434 green

## Session 9i continued-31 (2026-08-05) — FIRST VINTAGE EDA + REVIEW LINK LIST
- scripts/vintage_eda.py on the fresh cache (EXPLORATION ONLY — any
  finding must pass registry v4 before the engine may use it):
  **GLIDE PATH: deleted names lose median 22% of cap over the 250
  trading days before announcement (70 windows) vs survivors -3%
  (120 windows) — deletion is a yearlong glide, not an event.**
  **SMART MONEY: foreign ownership +5.5pp into adds, -4.1pp into
  deletes over the same window (54/70 windows) — anticipation IS
  visible in the daily shareholding tape, and it accelerates ~T-120.**
  Charts: docs/img/eda_glidepath.png, eda_foreign.png
- Both series are PIT-available DAILY (FinMind Shareholding) ->
  prime candidate features for the cutline-retention classifier;
  H15 (foreign-flow direction) + glide-slope feature registered as
  v4 candidates, thresholds NOT set here
- docs/MSCI_REVIEW_LINKS_2015_2026.md: all 46 reviews Feb15-May26,
  official STPublicList links (app2.msci.com pattern verified vs our
  archive) + TW change counts + Aug-26 pending line; local mirror
  noted (data/msci_archive — platform never depends on live links)

## Session 9i continued-30 (2026-08-05) — PIT VINTAGE UNLOCK (the decade backtest data, HARVESTED)
- User: what data do we need for PIT-graded 2015+ backtests, then
  get it. docs/PIT_BACKTEST_DATA_PLAN.md: 9-item inventory, each
  PROBED LIVE before listing
- THE FIND: FinMind free API TaiwanStockShareholding =
  NumberOfSharesIssued DAILY from 2015 + foreign holding % + FOL,
  covering TWSE + TPEx + DELISTED names; TaiwanStockPrice covers
  delisted prices -> survivorship solved. TDCC dispersion (best
  float source) paywalled -> v1 float policy: current ff held w/
  REPORTED ±10% sensitivity band; FLOAT-SENSITIVE reviews excluded
  from headline accuracy
- scripts/tw_vintage_harvest.py (probe/fetch/sanity; resumable,
  atomic, paced, FINMIND_TOKEN optional): **HARVEST COMPLETE IN
  SANDBOX — 110 names x (shares + prices) 2015-2026, 58MB cache**
  (109 = full review key + boundary set; +3474 Inotera as the
  corporate-event-exit anchor, absent from the review key because
  M&A exits happen MID-QUARTER — live proof of the interview's
  corporate-events blind channel)
- Sanity: 100/109 series reach 2015-H1 (rest listed later); TSMC
  mid-2015 shares 25,930,380,458 matches known value; pinned test
  added (anchor + survivorship). Suite 433 green
- NEXT: scripts/pit_backtest_2015.py — rebuild vintages, replay all
  46 reviews w/ frozen May-26 rules (no per-review tuning), grade
  vs key -> becomes the training set for cutline-retention
  classifier + proximity calibration + regime priors (v4)

## Session 9i continued-29 (2026-08-05) — STEP-1 WORKBENCH: every number behind the universe
- User: visualize step 1 w/ clear numbers (ff, caps, decision).
  scripts/universe_workbench.py -> data/universe_workbench_tw.json:
  per-name TWD cap (Apr-30, price x shares) -> FX 32.5 -> current
  price ratio -> USD cap, free-float est, float-adj cap, ADV,
  x-threshold, decision bucket; thresholds GMSR $4.78B / add bar
  $8.61B / floor $2.39B (Aug-2026 QIR config, post-May membership)
- UI: "Step 1 workbench" expander (page6 Tab 1, above the funnel) —
  3 threshold metric cards, log-scale boundary ladder chart (members
  blue vs non-members red, dashed floor/GMSR/add-bar lines), full
  numbers table, decision-logic caption incl. the ff nuance (float
  shapes GMSR via coverage walk; hurdles use FULL cap)
- Fix during build: Streamlit rendered paired $ as LaTeX — amounts
  moved out of markdown into metric cards; chart x-range pinned
- +1 pinned test (threshold ratios 1.8x/0.5x exact, ff in (0,1],
  float-adj arithmetic, bucket logic consistent; proportional
  rounding tolerances); suite 432 green; sandbox screenshot verified

## Session 9i continued-28 (2026-08-04) — NAME JOURNEYS: the shortlist AT every stage
- User: show the shortlist per funnel step w/ selection method.
  agents/review_funnel.py: name_journeys() — every real name's
  stage-by-stage row (role, cap, x-threshold, status, final call,
  official outcome for the graded run) + STAGE_METHOD dict citing
  the GIMI May-2026 book per stage (§2.3.2 GMSR range, §3.1 QIR
  recipe, §3.1.5.1 buffers, §3.1.2.4/3.1.6.2 retention grace)
- May-26 validation journeys: 6223.TWO ADDED—HIT at 2.92x add bar;
  7 deletes HIT; 1101/1326/2207 RETAINED—false calls labeled
  "cutline resident"; giants (2330 at 771x floor) shown SAFE so the
  reader sees why they never enter the shortlist
- HONESTY FIX during build: delete candidates sit 1.5-4.2x ABOVE
  the hard 0.5x floor in the May run because the SAIR migration
  sweep (GIMI §3.1.5.1) is the effective bar — status text + UI
  caption now say so instead of implying a floor breach
- funnel_tw.json/TW_FUNNEL.md carry journeys + methods; UI renders
  journeys table + GIMI-citation popover; pinned test extended
  (journey outcomes + 3 false-call count + citation present);
  431 green; verified live in sandbox screenshot
- GIMI locating answer of record: the book has no "shortlist" —
  closest is §3.1.5.1 buffer zones; our shortlist = buffers +
  proximity probabilities + churn/hazard/blind-band layers (ours)

## Session 9i continued-27 (2026-08-04) — FUNNEL STARTS AT STEP 1 + SIDEBAR TRIM
- Funnel now OPENS with "S0 acquisition" (engine Step 1 — how the
  universe is built): 16 named TW boundary stocks (caps = price x
  shares via yfinance FX->USD, floats estimated, ADV 60d, membership
  rolled forward from official results) + count-anchored 500-name
  modeled tail (83 members, MSCI factsheet). review_funnel.py stage
  prepended; funnel_tw.json + TW_FUNNEL.md regenerated — May-26
  validation grade UNCHANGED (7/7 dels + 1/1 add, 3 cutline false
  dels); UI expander caption explains the acquisition sources
- app.py: TEMPORARY sidebar trim per user — only "Rebalance Trade
  Lifecycle" visible; SHOW_ALL_MODULES=True restores everything
  (Desk Brief hidden too, per instruction; nothing deleted)
- Pinned funnel test updated for the new leading stage; suite 431 green
- PROVENANCE EXPANDER added to Tab 1 (user: "is this from MSCI or
  calculated by us?"): per-input table — boundary list OURS (curated
  near GMSR), caps OURS (price x shares, refresh timestamp from
  aug26_cap_refresh.json mtime shown live), floats OURS (estimated,
  MSCI's licensed — stated miss source), count anchor MSCI factsheet,
  shorts TWSE auto-refreshed; stale-caps warning at >=3 days.
  Answer of record: caps are NOT auto-refreshed every run (shorts
  are); ratio file refreshed 2026-08-04; Aug-11 protocol refreshes
  same-morning. Verified live in sandbox (streamlit + headless
  chromium w/ stubbed libXdamage): screenshots confirm trimmed
  sidebar, provenance table, funnel starting at S0 acquisition

**Mode:** Autopilot (Opus 4.8). **Backlog item completed:** **B1 — Formal test
suite + CI.** This was the correct first pick: no `tests/` directory existed,
and B1 is explicitly the protection layer for every later backlog task.

## Starting state

- Working tree was **clean and committed** at HEAD `77c880f "Updated Agents"`
  (baseline `7f2d4aa` present) — contrary to the handoff's warning of ~24
  uncommitted files, the user had committed since writing it. Git-diff recovery
  therefore works; no unrecoverable state.
- Repo lives at `Downloads/execution_analytics` (mounted via a picked folder).

## What changed (all NEW files except two doc edits)

New (untracked) — no existing code touched:
- `tests/conftest.py` — offline, deterministic synthetic-data builders
  (intraday multi-day, daily GBM for Yang-Zhang, single-day scheduler inputs,
  synthetic `MarketData`) + path setup.
- `tests/test_explicit_costs.py` — 7 tests (UK buy 51.6, TW sell 31.9, side
  logic, default fallback).
- `tests/test_order_ticket.py` — 19 tests: `constrain_fills` kernel (the
  **25%-fill anchor**: 20% ADV / 5% cap / 78×10k → 39,000 filled), carry-forward,
  limit gate, exempt auction bars, `windowed_curve`, ticket helpers, all
  pre-trade compliance findings.
- `tests/test_agent3.py` — typical-price wick convention (**TWAP slippage
  10.0 bps**, MOC/MOO 0.0), **limit-below-market → 0% fill, opp cost 385.0 bps**,
  Almgren-Chriss trajectory, **default-ticket == legacy invariant (P-4)**,
  flat-day zero slippage, cap reduces completion, auction-disabled exclusion.
- `tests/test_estimators.py` — Yang-Zhang recovers ~0.20 GBM, CS recovers an
  injected 100 bps spread, floors/insufficient-data paths, AR order-of-magnitude.
- `tests/test_agent13.py` — Cost-optimized uses dark & beats Lit-only (0% dark),
  venue cost formula, single-venue = 100% primary, spread cap + note, full route.
- `tests/test_agent14.py` — **pressure-then-reversal anchor: S1/S2/S3 =
  1000.0 / 750.0 / 725.0 bps, S1 tracking 0.0**, cost ordering, **buy/sell
  mirror** (Sell on reflected path 2·P0−P == Buy on original), positive-adverse
  impact both sides.
- `tests/test_agent11.py` — live alert engine thresholds (pace, participation
  breach, limit-through, VPIN High/Elevated, benchmark slippage HIGH/MEDIUM,
  reconsider, clean state).
- `tests/test_integration.py` — offline integration over a **recorded AAPL
  fixture** (full 8-algo sim + estimators + routing on real data shapes) and one
  `@pytest.mark.live` smoke test (skipped by default).
- `tests/fixtures/AAPL_{intraday,daily}.parquet` + `AAPL_meta.json` — recorded
  once via `fetch_market_data("AAPL","US")` (352 intraday bars / 5 days, 60
  daily bars; ADV 54.3M, YZ vol 26.3%).
- `pytest.ini` (markers, `live` marker documented), `requirements-dev.txt`
  (`-r requirements.txt` + pytest + pyarrow), `.github/workflows/tests.yml`
  (runs `pytest -m "not live"` on push/PR/manual).

Edited (tracked) — docs only, no code:
- `README.md` — CI badge, a **Testing** section, and repo-structure block now
  lists agents 12/13/14, `order_ticket.py`, `explicit_costs.py`, `tests/`,
  `docs/`, `requirements-dev.txt`, `pytest.ini`.
- `docs/INSTITUTIONAL_GAP_REGISTER.md` — "Last updated" → 2026-07-08; new
  "covered today" row for the test suite + CI.

## Verification (all green — §5 checklist)

1. `python3 -m py_compile app.py agents/*.py` → OK.
2. `pytest -m "not live"` → **64 passed, 1 deselected** (0.5s, fully offline).
3. AppTest smoke (P-3 recipe): **both pages render, Page 1 pipeline runs,
   `at.exception` empty on both.** (The pyarrow serialization traceback in
   stderr is the known-benign Arrow noise P-3 tells us to ignore — not an app
   error.)

Numbers that shifted: **none.** No estimator, fill convention, or η was
touched — this session only added tests that pin the *existing* numbers.

## Autopilot decisions made without the user

- Picked B1 first (backlog order + it protects later work).
- Where a documented §6 anchor is an exact hand-computable kernel result
  (25% fill, 385 bps, 10 bps wick, 51.6/31.9, 1000/750/725) I asserted the
  literal value. Where an anchor is statistical (YZ/CS/AR) I asserted a
  generous recovery band with a fixed RNG seed, to keep CI non-flaky.
- Split dev deps into `requirements-dev.txt` rather than polluting runtime
  `requirements.txt`.
- Did **not** commit or push (autopilot rule 4). Did not touch
  `PROJECT_CONTEXT.md` / `INTERVIEW_PREP.md`.
- **Note (autopilot rule 4):** `.github/workflows/tests.yml` is a *new* GitHub
  workflow. It was explicitly requested by B1, is CI-only (no scheduled cron,
  no provider fetching), and is independent of the demo-only
  `refresh-index-changes.yml`. Flagging it here per the "note new workflows
  prominently" rule.

## Operating-protocol notes for the next session

- **P-2 extension (git stat cache on this mount).** After editing a *tracked*
  file with the Edit tool, git did not detect the change — the mounted
  filesystem serves git a frozen mtime, so `git status`/`git diff` reported
  README.md as clean even though the working blob differed from the index
  (confirmed via `git hash-object` ≠ `git ls-files -s`). Fix that worked:
  `touch <file> && git update-index -q --really-refresh`. **Before ending a
  session, run `touch` on every tracked file you edited, then re-check
  `git status`,** or the user won't see (and won't commit) your doc edits.
- **Stale `.git/index.lock`.** A `git status` left a 0-byte `.git/index.lock`
  that could not be unlinked from the sandbox ("Operation not permitted");
  cleared it via the Cowork file-delete permission tool. If git ever reports a
  lock, this is why — it blocks the user's commits until removed.
- P-8 budget: **2 live yfinance fetches used** this session (fixture record +
  the AppTest smoke's internal AAPL fetch). Stay at 1–2 next time.
- Sandbox setup: `pip install --break-system-packages pytest pandas plotly
  yfinance streamlit`; **pyarrow in `~/.local` was broken** (missing
  `pyarrow.vendored`) and shadowed the working copy — fix with
  `pip install --break-system-packages --force-reinstall --no-deps pyarrow`
  before pandas will import.

## Recommended next step

**B2 — Sell-side migration** (the flagship gap, test-first). The suite now
makes this safe: the buy/sell **mirror property test already exists for Agent 14**
(`test_agent14.py::test_buy_sell_mirror_property`) and is the exact mechanical
check B2 Step 3 prescribes — replicate that pattern for Agents 3/4/6/10/11 as
each is migrated. Alternatively **B3 — live-session ticket binding** (1 session,
smaller blast radius) if a lower-risk item is preferred; the live-alert tests
in `test_agent11.py` already cover the alert side of it.
```

---

# B2 — Sell-side migration (started 2026-07-08, same session)

User selected B2 as the next item. Test-first; engine migrated to side-aware
with the mirror property enforced; **UI kept functionally buy-only** until the
full migration (engine + UI selector + short-locate) is verified — so the app's
behavior is unchanged for users at every boundary (handoff B2 constraint).

## Step 1 — inventory of sign-bearing sites (slippage/opportunity/tracking take
`sign = +1 buy / −1 sell`; market impact stays positive-adverse; limit gate is
side-aware).

- **order_ticket.py** — `constrain_fills` limit gate (buy blocks price>limit;
  sell must block price<limit). New `side_sign()` helper lives here.
- **agent3_algo_simulation.py** — `_build_result` slippage + Perold opp cost;
  `_attach_running_metrics` running slip vs arrival & vs interval-VWAP;
  `simulate_algos` + `simulate_with_interventions` pass `side` and side to
  `constrain_fills`. Price-reactive tilt: `_sim_liquidity_seeking` z-score
  (favorable = dip for buy / rise for sell) must be side-aware to mirror;
  TWAP/VWAP/STEALTH schedules are price-direction-independent already.
- **agent4_performance_comparison.py** — `_sim_day_all` slip + opp; thread
  `side`; side-aware limit gate if it applies ticket constraints.
- **agent6_pretrade_posttrade.py** — `compute_benchmark_comparison` slip vs
  each benchmark; `compute_impact_decomposition` I/J/K (J == algo.slippage_bps,
  already signed once Agent 3 is migrated); pre-trade `explicit_cost_note`/
  `total_bps` hardcode "Buy" → use ticket side.
- **agent10_hypothesis_test.py** — reads Agent 4's signed daily_slips/costs
  directly; "lower cost is better" holds for both sides once upstream is signed
  → no in-module sign logic needed.
- **agent11_live_snapshot.py** — `_benchmarks_to_date` slip vs benchmarks;
  `live_tca` builds an AlgoResult via `_build_result` → pass side;
  `build_live_alerts` receives already-signed slip → no change.
- **app.py** — UI language ("paying"/"buy"/"underperform"), FIX Tag 54, side
  selector, short-locate. Deferred to Step 4; UI stays buy-only until then.

Mirror-property test (the mechanical sign-site catch): a **Sell on price path P
produces identical costs to a Buy on path (2·P0 − P)** with mirrored limit.
Enforced on TWAP/VWAP (exact) and, after the LIQ tilt is made side-aware, on the
price-reactive algos too.

*Continuity: this file is the source of truth for the next session — start here.*

## B2 progress this session — engine migrated + verified (Steps 1-3 done, Step 4 partial)

Completed:
- **Step 2 — central convention:** `side_sign(side)` (+1 buy / −1 sell) in
  `order_ticket.py`; `constrain_fills` limit gate made side-aware (buy blocks
  price>limit, sell blocks price<limit); FIX Tag 54 reflects side.
- **Step 3 — engine migration (all sign sites):**
  - Agent 3 `_build_result` (slippage, Perold opp), `_attach_running_metrics`
    (running slip vs arrival / vs interval VWAP), the LIQ favorability z-score
    (side-aware), and threading of `side` through `simulate_algos` /
    `simulate_with_interventions` + `constrain_fills`; `SimulationResult.side`.
  - Agent 4 fast path `_sim_day_all` (`_cost` slip+opp, `_constrain`, LIQ z).
  - Agent 6 pre-trade explicit-cost side; post-trade `compute_benchmark_comparison`,
    `compute_impact_reversion`, `compute_impact_decomposition` (signed), wired
    from `sim.side`.
  - Agent 11 `_benchmarks_to_date` + `live_tca` threaded with `side`.
  - Agent 10 needs no change — it consumes Agent 4's already-signed series and
    "lower cost is better" holds for both sides.
- **Step 4 (partial) — short-locate compliance:** `locate_confirmed` flag on the
  ticket (default True); a Sell without a confirmed locate is a pre-trade BLOCK.
- **Tests:** `tests/test_sell_side.py` — the Buy/Sell **mirror property** (Sell
  on P ≡ Buy on 2·P0−P) over all 8 algos + the Agent-4 fast path, impact
  positive-adverse both sides, sell limit gate, and opposite-sign slippage on a
  shared path. Sell-kernel + locate tests added to `test_order_ticket.py`.
  **Full offline suite: 84 passed, 1 deselected.** Buy numbers unchanged
  (default-ticket == legacy invariant still green). Both pages still render.

Deferred to the next session (Step 4 remainder) — the app stays functionally
**buy-only** until this lands, per the handoff's "keep buy-only when incomplete"
rule (the engine is complete and correct, so this is not half-shipping the
analytics — only the UI exposure is pending):
- Wire a Buy/Sell selector + a short-locate checkbox into `app.py`, pass `side`
  into the `OrderTicket` and into `simulate_with_interventions` / `live_tca`
  (both already accept a `side=` kwarg, default Buy), and refresh buy-centric UI
  wording ("paying", "buy"). **P-1 applies doubly to `app.py`.**

## IMPORTANT operating note — mount write consistency (extends P-1/P-2)

This session hit repeated filesystem-consistency problems on the mounted repo:
1. The **Edit tool truncated `order_ticket.py`** once it pushed the file past
   ~300 lines (the known P-1 incident) — restored from a `/tmp` backup and
   re-applied via the bash-python anchor-assert patch method.
2. The **Write/Edit host tools intermittently desynced** from what the bash
   sandbox (and therefore pytest) reads — a `Write` reported success but bash
   still saw the old/corrupted bytes; a bash `>>` append interleaved with
   existing content and corrupted a test file.
**Resolution / rule for next session:** treat **bash `cat > file` (heredoc) and
`python3 … Path.write_text` as the authoritative write path** on this mount, and
re-run `py_compile` + `pytest` via bash immediately after every write. After
editing any *tracked* file, `touch` it and `git update-index --really-refresh`
so git detects the change (see the P-2 extension note above). Back up every
file before patching (`cp … /tmp/backup_*`). All agent-module edits this session
were made via bash-python and are consistent with the passing suite.

## Follow-on same session — Streamlit deploy fix + B2 Step 4 + B3

**Deploy bug (Streamlit Cloud `ImportError` at the `agent11` import).** Root
cause: a partial/stale commit shipped `agent11.py` (with its new
`from agents.order_ticket import side_sign`) without the updated
`order_ticket.py` that defines `side_sign` — a direct consequence of the mount
git-index staleness noted above. Four files (`agent3/4/6/11`) import `side_sign`
from `order_ticket`, so **they must be committed as one atomic set**. The full
working tree was re-verified import-clean in a cold Python process (all 11
modules OK). FIX: commit *all* modified engine files + `order_ticket.py`
together (git now detects the whole set).

**B2 Step 4 (shipped).** `app.py` order ticket now has a **Buy/Sell selector**
(FIX Tag 54) and a **short-locate checkbox** (disabled for Buy); `side` and
`locate_confirmed` flow into `OrderTicket`, and `side` is threaded into
`simulate_with_interventions` and `live_tca`. Validated end-to-end with an
AppTest **Sell** pipeline + live-session run (no exception; both pages render).

**B3 (shipped).** Order-ticket **participation cap + side-aware limit gate now
bind the live trading session** via the same `constrain_fills` kernel (auction
prints exempt from the continuous cap); `simulate_with_interventions` takes a
`ticket=` arg and `app.py` passes it. The two "live-session enforcement is the
next build" captions were replaced. New `tests/test_live_binding.py` proves a
single-leg live session reproduces the Agent-3 static result under a cap ticket,
that the cap reduces completion, that a sell limit gate binds, and that a
default ticket is a no-op. **Full offline suite: 88 passed, 1 deselected.**

Remaining B2/B3 refinement (small): execution-**window** binding inside the live
playback (cap+limit already bind); a few buy-centric caption wordings.

### ACTION REQUIRED (user) — fixes the Streamlit deploy
Commit the **complete** set together, then push, so Cloud gets a consistent tree:
```
git add -A
git commit -m "B2 sell-side (engine+UI) + B3 live-session binding + B1 tests/CI"
git push
```
The earlier broken deploy was a partial commit missing `order_ticket.py`; a full
`git add -A` avoids that. If Cloud still errors after a clean redeploy, open
"Manage app" → logs for the full (un-redacted) traceback and share it.

## Follow-on same session — Statistical modelling for the GSET role (Cost Model / TCA Regression)

User asked to map the GSET Quantitative Execution Consultant responsibilities,
rank them, and build the most role-relevant statistical-modelling automation.

- **Analysis doc:** `docs/GSET_ROLE_AUTOMATION_ANALYSIS.md` ranks the 7
  responsibilities (top cluster: R3 apply-TCM, R7 statistical-tools, R6 A/B) and
  justifies building a regression cost model, with an efficiency/value writeup
  for the desk.
- **`agents/cost_model.py`** — OLS with an explicit, auditable implementation:
  White **HC1** and Newey-West **HAC** robust SEs, classical SE for contrast,
  t/p-values, F-test, R²/adj-R²; **Durbin-Watson / Breusch-Pagan / Jarque-Bera**
  diagnostics; a sqrt-law cost-curve feature builder + `predict()`; and
  **`ab_test_with_controls`** — an A/B test as a regression with a strategy dummy
  + condition controls (the incremental cost net of confounders, the
  apples-to-apples number a raw paired mean cannot give). numpy/scipy only.
- **`agents/cost_panel.py`** — assembles the regression panel from the fast
  Agent-4 sim across order-size grid × 8 algos × every available day (this is the
  "backtest & calibrate the cost model" workflow, R5).
- **App:** a Page-1 **"Cost Model — TCA Regression"** section (button-gated,
  session-persisted): coefficient table with robust SEs, R²/F/diagnostics,
  predicted-vs-realized plot, and the A/B-with-controls readout. Validated
  end-to-end via AppTest (pipeline run + Fit Cost Model click → no exception,
  tables render).
- **Tests:** `tests/test_cost_model.py` (10) — OLS recovers known betas; HC1
  inflates SEs under heteroskedasticity; HAC handles autocorrelation (trending
  regressor + AR(1) errors); DW/BP/JB behave; the cost model recovers the
  synthetic sqrt-law coefficient; **A/B-with-controls debiases a size confounder**
  (naive says strategy B is cheaper, controlled recovers ~0 — the headline
  value); offline panel-build+fit on the AAPL fixture. **Full suite: 98 passed.**
- Docs synced: gap register (new "covered today" row), README (feature paragraph
  + Testing mention).

Numbers that shifted: none in the existing engine — the cost model is additive.
P-8: 4 live fetches used this session total (fixture, two AppTest smokes, the
Sell + Cost-Model AppTest). All engine/module edits made via bash-python /
`cat >` (authoritative on this mount); Write/Edit host tools remained unreliable.

## Follow-on same session — Research-grounded microstructure + all-7-responsibilities coverage

User asked to research market microstructure (Asia-focused where possible) and
implement features covering all 7 GSET responsibility bullets.

- **Research memo:** `docs/MICROSTRUCTURE_RESEARCH_IMPROVEMENTS.md` — literature
  scan (EDGE spread estimator Ardia-Guidotti-Kroencke JFE 2024; the "double"
  square-root impact law on Tokyo Stock Exchange data, Bouchaud et al. 2025;
  closing-auction growth/concentration in Asia; Asian price-limit bands; Amihud
  2002 illiquidity; intraday U-shape seasonality) mapped to concrete builds.
- **`agents/microstructure_analytics.py`** — EDGE effective-spread estimator
  (faithful reimplementation of the authors' MIT reference, attributed), Amihud
  illiquidity, intraday seasonality (open/midday/close, lunch-break-robust), and
  time-series tools (ACF + Ljung-Box).
- **`agents/asian_markets.py`** — per-market price-limit bands (China/Korea/
  Taiwan/Vietnam/Thailand/Indonesia) with a pre-trade flag (a buy/sell limit
  beyond the band can never fill → BLOCK), and closing-auction concentration.
- **`agents/client_analytics.py`** — benchmark scorecard (realized vs benchmarks
  vs model-expected vs own-history percentile + grade + improvement delta) and a
  client-ready markdown one-pager generator.
- **App:** a Page-1 "Microstructure & Client Analytics" section — EDGE/CS/AR
  spread cross-check, Amihud, seasonality, closing-auction concentration, the
  price-limit flag, the benchmark scorecard, and a downloadable client one-pager.
  Validated end-to-end via AppTest (pipeline run → section renders, no exception).
- **Tests:** `tests/test_research_analytics.py` (18) — EDGE recovers an injected
  spread; Amihud ranks illiquidity; seasonality detects the U-shape; ACF recovers
  AR(1); Ljung-Box separates autocorrelated from iid; China/Taiwan price-limit
  BLOCKs; closing-auction concentration; scorecard grading; client-report
  rendering. **Full offline suite: 116 passed, 1 deselected.**
- **Docs:** research memo; gap-register row; README paragraph; and a
  **seven-responsibility coverage map** appended to
  `docs/GSET_ROLE_AUTOMATION_ANALYSIS.md` (every R1–R7 bullet now maps to tested
  features).

Numbers that shifted: none in the existing engine — all additions are new modules
+ one additive app section. Research grounded in cited academic/industry sources
(memo has the Sources list). P-8: 5 live fetches total across the whole session.


---

# Session 5 (post-handoff-v2) — Page-2 MSCI walkthrough, 4 bug fixes, user manual

**Goal:** walk the Index Rebalancing page end-to-end with a real MSCI event, fix
bugs found on the way, produce a user manual (delivered to the user's outputs
folder as `Index_Rebalancing_User_Manual.docx`).

**Walkthrough:** Agent 12 live MSCI feed → picked the real "Delete · VEDANTA
(VEDL, India NSE) · ann 2026-06-19 · eff 2026-06-25" event → event study
(NIFTY 50 proxy, ±10d) → insights → Agent 14 (Sell 5% ADV). Textbook deletion:
CAR −6.06% at T, 72% reversal fraction (Transient), 74% of the move
post-announcement; tracker → MOC/S1, cost-minimizer → STEALTH/S4.
yfinance fetches used: 5 (2 daily pairs + 1 intraday) — P-8 noted.

**Bugs found & fixed (all verified, suite 116 → 126 passed):**
1. `rebalancing_event_study.py` — first event-window day's AR was `-alpha`
   (pct_change().fillna(0) artifact), shifting the ENTIRE CAR curve. Returns
   now computed with one extra leading trading day (AR[0]=0 only when no
   earlier data exists). Vedanta T−10 CAR: bogus +0.70% → real +2.90%.
2. `agent14_rebalance_strategist.py` — S1's tracking difference was nonzero
   with eta>0 (auction fill compared to an unimpacted close), so Index-Tracker
   mandates were mis-recommended S3. Auction fills now carry ZERO tracking by
   construction (the print includes your own impact); impact still in cost.
   Caveat added; pinned by new test with eta=0.3.
3. `app.py` Agent-14 sliders — StreamlitAPIException (min<max) whenever the
   event window has no post-event days (default date=today, fresh
   announcements) or no pre-event days. Guards added; fixed-value captions;
   S3 skipped cleanly (engine already handled it — new test pins that too).
4. `app.py` Key-Day Summary — Styler format key "Ab. Volume (×)" vs actual
   column "Ab. Volume (x)": column silently rendered unformatted. Aligned.

**Also repaired:**
- Corrupted `.git/index` ("unknown index entry format 0x76000000") — rebuilt
  in place via `git read-tree HEAD` (sandbox couldn't rm the file). git now
  works; commits were fully blocked before this.
- `tests/test_sell_side.py` — HEAD (46a0289) contains a stray corrupted final
  line (`loc[bench, col] == ...`, the P-B append incident) that breaks import
  of the committed file. Working tree carries the fix — COMMIT IT.

**New files:** `tests/test_rebalancing_event_study.py` (8 offline tests pinning
reversal/drift/flow/eta arithmetic + recommendation rules — the module had no
coverage), extended `tests/test_agent14.py` (7 tests). Suite: **126 passed,
1 deselected**; AppTest smoke of both pages clean.

**Modified tracked:** `app.py`, `agents/rebalancing_event_study.py`,
`agents/agent14_rebalance_strategist.py`, `tests/test_agent14.py`,
`tests/test_sell_side.py` (pre-existing fix), this file.
**Untracked new:** `tests/test_rebalancing_event_study.py`.


---

# Session 5b — Trader workflow layer (Page 2)

**Goal:** make Page 2 usable by a trader mid-rebalance (verdict-first) and
pre-event (playbooks, basket, priors). Design doc: `docs/TRADER_WORKFLOW_DESIGN.md`
(F1–F5 built, F6–F8 specified). User walkthrough: `docs/Trader_Features_Guide.docx`.

**Built (all offline-tested, suite 126 → 136 passed):**
- F1 Verdict banner — first render after a study: side/size/strategy/cost/
  tracking + auction RAG (GREEN <15% / AMBER / RED >25% of est. auction volume,
  RED == agent14 AUCTION_STRESS_WARN). Side defaults from the Agent-12 action
  (Delete→Sell via p2_side14 pre-seed); size from flow-to-trade else 5% ADV.
- F2 Trade card + exports — plain-text desk card (st.code) + download buttons:
  card .txt, all-strategy schedules .csv (EMS staging), playbook .txt.
- F3 Conditional playbook — dated IF/THEN triggers with computed thresholds
  (1.5x typical run-up, RAG gates, reversal reference); thresholds labelled
  with source ("this event" vs "library median, n=…").
- F4 Basket mode — CSV (ticker,market,side[,shares]) → per-name event studies
  → severity-ranked exception blotter (errors first, then RED by size), CSV
  download. study_fn injectable → fully offline tests.
- F5 Event library — every study auto-records to `data/event_library.json`
  (keyed ticker+T, update-not-duplicate); medians feed playbook thresholds
  once n≥3; context caption under the crowding caveat. Seeded with the real
  VEDL event. NOTE: derived data — consider .gitignore.

**Files:** new `agents/trader_view.py` (372 lines, no Streamlit imports),
`tests/test_trader_view.py` (10 tests), `docs/TRADER_WORKFLOW_DESIGN.md`,
`docs/Trader_Features_Guide.docx`; app.py 6 anchor patches (imports, side
hint, basket expander, banner, library caption, trader pack) → 2060 lines.
AppTest smoke: both pages clean, basket expander renders. No new network use
(trader pack for the guide regenerated from the session's cached VEDL pickle).


---

# Session 5c — Research survey + P1 analytics (crowding score, expected move)

**Research memo:** `docs/REBALANCE_RESEARCH_AUTOMATION.md` — ten research
streams (index effect measurement, indexer costs, change prediction,
crowding/anticipatory arb, flows/elasticity, auction microstructure,
add/delete asymmetry, post-inclusion shifts, staggered implementation,
provider methodology) each mapped to automatable features with free-data
feasibility + prioritized table. Gap-register candidates named (real-time
NOII, official MSCI FIFs, intraday short flow).

**Built (P1 from the memo; suite 136 → 142 passed):**
- Crowding Score (trader_view.crowding_score) — 0–100 from up to 3 disclosed
  proxies: pre-announcement share of the move (from drift decomposition),
  pre-announcement abnormal volume, optional user-supplied short-interest
  change (~2wk lag). Tiers LOW/MODERATE/HIGH with strategy-mapped insight
  (HIGH → S3/patience; appends a playbook step). VEDL: LOW 13/100.
- Expected Move (trader_view.expected_move) — pre-event band two ways:
  sqrt-law (eta baseline 0.3 → library median once n≥3) and Gabaix-Koijen
  flow-multiplier band (M=3–8 on flow/float-cap; float cap is a new optional
  input). VEDL illustrative: 12 bps sqrt / 38–100 bps multiplier vs realized
  −6.7% ⇒ pressure-driven, consistent with the 72% reversal.
- Library side-split: record_event(action=...), library_stats(action=
  "Add"|"Delete") (Chen-Noronha-Singal asymmetry); action auto-captured from
  the loaded Agent-12 event.
- UI: two optional inputs (float mcap $B, short-interest change %) on a second
  row of the Execution-Cost expander; Crowding/Expected-Move panels render
  under the library context line; playbook consumes the crowding tier.

**Manual:** regenerated as v1.1 (`docs/Index_Rebalancing_User_Manual.docx`) —
new §3.7 with the real VEDL numbers, updated §3.3 inputs table, §3.5 row,
troubleshooting entries, Appendix B (Gabaix-Koijen added). 6 new tests in
tests/test_trader_view.py (16 total there). AppTest smoke clean. No new
network use this session-segment (VEDL numbers from the cached pickle).


---

# Session 5d — Institutional feasibility proposal

`docs/INSTITUTIONAL_PLATFORM_PROPOSAL.md` — evaluates porting the agent design
to an institutional (GSET/CLSA-style) platform. Structure: agent→desk-function
mapping (adoption argument: the pipeline mirrors the existing division of
labor), five-dimension feasibility (methodology LOW risk / data MEDIUM = the
real cost line / tech LOW-MEDIUM / governance MEDIUM / adoption decisive),
seven ranked efficiency proposals each with a metric (P1 overnight event-pack
factory; P2 best-ex documentation as by-product; P3 calibration on desk fills;
P4 strategy A/B with controls; P5 sales client-tier scalability; P6 guard-railed
LLM narration; P7 live-day escalation), interviewer-proof risk answers
(vendor-TCA overlap, compliance framing of crowding analytics, LLM risk, model
risk, adoption), and a 3-phase roadmap. Doc only — no code changes.


---

# Session 5e — Page-1 institutional assessment + I-5/I-8 shipped

`docs/SIMULATOR_INSTITUTIONAL_ASSESSMENT.md` — stage-by-stage quality
comparison vs the institutional order lifecycle; verdict: math at parity,
gaps are data fidelity (disclosed), workflow packaging, and feedback loops.
Ranked designs: P-A pre-trade desk card, P-B algo wheel (I-7), P-C run
library, P-D live volume re-forecast (B4), P-E multi-day (I-10), P-F polish.

**Shipped:**
- I-5 full IS attribution — `ISAttribution` + `build_is_attribution` in
  agent6; Perold delay/trading/opportunity/explicit reconciling to the
  share-weighted shortfall ±0.1bp by construction; waterfall + metrics UI in
  the Post-Trade section; modeled sqrt-law impact shown as MEMO (fills don't
  embed it); PostTradeTCA gains trailing defaulted field (P-E convention).
  NOTE: attribution is share-weighted CANONICAL IS — intentionally differs
  from the headline total (unweighted slippage + modeled impact) on partial
  fills; documented in the dataclass docstring and UI note.
- I-8 parent/child order detail — EMS-style expander: child slices bar chart
  + cumulative % overlay + schedule table for the executed algo.
- `tests/test_is_attribution.py` (5 tests: reconciliation across all 8 algos
  x both sides, full-fill identity vs slippage, partial-fill scaling POV@60%
  ADV Low urgency, sell-side mirror, TCA carriage). Suite 142 → 147 passed.
  AppTest smoke clean. agent6 backup in ~/backups/.


---

# Session 5f — Architecture diagrams (maintainable, text-based)

`docs/ARCHITECTURE_DIAGRAMS.md` — four Mermaid diagrams as the single source
of truth (render on GitHub/VS Code/mermaid.live; edit-commit to update, no
image regeneration): D1 Page-1 order lifecycle (ticket→compliance→stages→
sim→TCA incl. new I-5/I-8→live, critic flag pattern), D2 Page-2 flow
(Agent 12→event study→verdict/insights/library→Agent 14→trader pack + basket),
D3 trader event timeline T−10→T+5 with library feedback, D4 learning loops
(shipped event library vs proposed Page-1 run library). Each diagram carries
a node→module map so design changes map to one-line edits.


---

# Session 5g — Quant review (statistics + microstructure lenses), 5 additions

`docs/QUANT_REVIEW_ADDITIONS.md` — critical review of both tools from the two
lenses with practitioner gaps; 5 additions shipped (suite 147 → 160 passed):
1. Event-study inference — `event_inference()` (Brown-Warner single-firm,
   forecast-error corrected): AR t-stats + CAR sigma; ±1.96σ band on the CAR
   chart; "CAR t" column in the key-day summary (+ styler key). BMP
   anti-conservatism disclosed. IMPORTANT fix caught at runtime: inference
   originally inserted AFTER the summary that consumes car_sigma → NameError;
   relocated before the summary block (offline tests could not see this —
   verified via monkeypatched end-to-end run).
2. Algo wheel (I-7/B6) — `agents/algo_wheel.py`: Friedman + Nemenyi CD league
   table on comp.daily_costs (blocked design); Page-1 section before Cost
   Model; small-n honesty notes.
3. Markout curve — `compute_markout_curve` in microstructure_analytics:
   share-weighted post-fill drift at 5–60 min, bar-close mid proxy disclosed;
   Post-Trade TCA UI; alignment by schedule 'time' column (sparse schedules).
4. Roll (1984) spread — 4th cross-check row; eps guard so pure trends report
   "undefined (diagnostic)" rather than 0.0.
5. Post-event liquidity/beta shift — `compute_liquidity_shift` (stream H):
   pre/post beta + EDGE + Amihud; Page-2 insights panel; needs >= 8 post days.
EventStudyResult gained trailing fields (ar_tstat, car_sigma,
liquidity_shift) per P-E. New tests: tests/test_quant_additions.py (13).
Roll test lesson pinned in-file: deterministic alternation is NOT Roll's iid
model (doubles the estimate) — test uses random ±1 bounce.


---

# Session 5h — Autopilot block: P-A, P-C, B4/P-D shipped (Page 1 workflow layer)

Closed the three top items from the simulator assessment (suite 160 → 166):
- **P-A desk pack** — `agents/desk_pack.py`: `build_desk_verdict` (capacity
  RAG: GREEN ≤1 day / RED >3 days at chosen urgency; critic-findings and
  earnings flags in the headline) + `pretrade_card_text` (the institutional
  pre-trade report: order, recommendation, expected-cost band + method,
  explicit, spread, capacity, regime, critic findings). UI: verdict banner +
  report download rendered FIRST after the pipeline, before the live session.
- **P-C run library** — `record_run`/`run_stats` (data/run_library.json,
  keyed update-not-duplicate so Streamlit reruns don't inflate n): predicted
  (pre-trade Expected bps for the executed algo) vs realized (total cost);
  bias/MAE caption under the verdict; recording wired at the end of
  Post-Trade after the markout block.
- **B4 / P-D live volume re-forecast** — `agent11.live_volume_forecast`:
  historical-curve gross-up of realized volume-so-far → run-rate multiple,
  projected day volume (× ADV), POV-at-urgency completion projection with
  "does NOT fit — act" inverse delta; metrics row in Live Agent Readouts.
Tests: `tests/test_desk_pack.py` (6; pipeline fixture goes through
`run_pipeline` — the same entry point the app uses, after signature
mismatches showed hand-wiring agents in tests is fragile). Registers
updated: I-5/I-7/I-8 marked shipped in the gap register; P-A/B/C/D marked
shipped in the assessment. data/run_library.json is derived data (same
.gitignore decision as event_library).

**Also in 5h:** buy-centric caption sweep (backlog small-polish item) — the
three remaining hardcoded "buy order / paid more" captions (live benchmark
chart, comparison header, post-trade benchmark table) are now side-aware via
`getattr(sim, 'side', 'Buy')`. Full suite 166 passed; AppTest both pages clean.

**Remaining open backlog after this block:** EDGE→agent6 spread-blend fold-in
(shifts displayed pre-trade numbers — do with a documented note), ticket
execution-WINDOW binding per leg in the live session (engine change, has a
recipe in HANDOFF v2 §7), multi-day parent orders (B7/I-10), app.py page-module
refactor (B8 — file is now ~2,340 lines; the P-A edit hazard grows with it).


---

# Session 5i — Autopilot block 2: window binding, EDGE blend, best-ex store

Suite 166 → 169 passed; AppTest both pages clean.
- **Live execution-WINDOW binding (backlog item, engine):** in
  `simulate_with_interventions`, every leg's bars are now intersected with
  `ticket.window_indices` (seg_mask also drives the historical-curve slice).
  If the window ends before the close, an "MOC" leg prints at the last
  in-window bar (static path instead excludes MOC — documented in-code).
  Tests: single-leg windowed TWAP live == static EXACTLY; multi-leg with
  intervention never fills outside the window. Live-session caption updated
  (cap + limit + window). Backup: ~/backups/agent3_pre_window.py.
- **EDGE → pre-trade blend (documented number shift):** blended half-spread
  = MEDIAN of CS/AR/EDGE (was CS×AR mean). Feeds Agent 13 routing. Note added
  to MICROSTRUCTURE_RESEARCH_IMPROVEMENTS.md; Roll deliberately NOT in the
  blend (undefined on trending samples → would flicker in/out of a median).
- **Best-ex record store (proposal P2 demo):** `build_bestex_record` /
  `record_bestex` in trader_view — decision, verdict numbers, frontier
  snapshot, params, playbook thresholds, library n persisted to
  `data/bestex_records.json` (keyed ticker+T+objective) at decision time;
  download button + caption in the Trader Pack. Third derived-data JSON
  (same .gitignore decision as event/run libraries).


---

# Session 5j — Program-trader JD mapped and implemented (Page 3)

**JD → platform mapping:** basket execution & client flows → program
pre-trade blotter (was Page-2-only); intraday cross-market monitoring →
market session board; impact/slippage optimization → already core;
cross-jurisdiction/time-zone coordination → execution wave plan;
market-specific regulation (short-selling, lot sizes, circuit breakers) →
per-market regulation reference + hard checks; audit records → best-ex/run
stores (existing) + program blotter/recon exports; settlement/recon support →
T+n settlement dates + simulated reconciliation report.

**Built — new Page 3 "🧺 Program Trading Desk" + `agents/program_trading.py`
(suite 169 → 178 passed, 9 new tests):**
- MARKET_REG: per-market desk reference for all 15 markets — UTC offset,
  lunch break, T+n settlement, board lot, short-sale regime note, circuit-
  breaker/band note. STYLIZED with explicit disclosures (no holiday
  calendars; DST approximated US/UK/AU; HK lots vary per stock; Korea note
  reflects the Mar-2025 resumption).
- Market session board: phase per market (Pre-open/Open/Lunch/Closed), local
  time, minutes to close; open-first earliest-close-first ordering; verified
  at 03:00 UTC (Tokyo Lunch, Shanghai Open, India Pre-open, US Closed).
- Compliance checks: `lot_check` (round-down + odd-lot note), `short_check`
  (BLOCK China-A/Vietnam; WARN without locate; regime note always),
  `settlement_date` (weekend-aware T+n).
- Program pre-trade blotter: CSV → per-name %ADV, capacity days/RAG, lot
  rounding, short flags, explicit costs, settlement date; errors first, then
  RED by size; injectable fetch_fn (offline tests); CSV download.
- Execution wave plan: program's markets ordered by UTC close — the
  cross-timezone coordination artifact.
- `program_recon`: simulated EOD tie-out report (ordered vs lot-executable vs
  odd-lot residual per name + escalation rule) — the ops-support analog,
  honestly labelled simulated.
App note: Page-3 branch appended at end of app.py (now ~2,440 lines — the
page-module refactor (B8) is now overdue and should be the next block's
first item before further UI growth).


---

# Session 5k — B8 refactor + caveat sweep

**B8 — app.py split into view modules (the P-A hazard fix, permanent):**
- `app.py` 2,441 → 65 lines: page config + sidebar + dispatch ONLY.
- `views/common.py` — all shared imports + `_cached_fetch`/`_badge`/`_VC/_TC/_AC`.
- `views/page1_simulator.py` (1,600) / `page2_rebalancing.py` (671) /
  `page3_program.py` (83) — bodies extracted VERBATIM (indentation preserved
  under `def render():`), so no logic diffs to review.
- Package deliberately named `views/` NOT `pages/` — Streamlit auto-builds
  nav from a `pages/` dir, which would fight the radio nav.
- Verified: py_compile, pyflakes name-check on every module (star-import
  noise filtered), full suite 178 passed, AppTest across all three pages
  including page switching. Backup: ~/backups/app_pre_refactor.py.
- **Latent bug EXPOSED AND FIXED by the pyflakes pass:** the cost-model →
  client-scorecard bridge used `np.` but app.py never imported numpy; the
  surrounding try/except swallowed the NameError, silently disabling the
  fitted-model expected value in the scorecard on EVERY run. numpy now
  imported in views/common.py (with an explanatory comment).
- Editing note for future sessions: view modules are 80–1,600 lines — the
  P-A "no host-Edit on >250-line files" rule still applies to
  page1_simulator.py, but blast radius is now per-page.

**Caveat sweep:**
- Suite warning eliminated: `agent2._classify_trend_legacy_autocorr` emitted
  a numpy divide RuntimeWarning and propagated NaN on zero-variance windows —
  now errstate-guarded and mapped to 0.0 (10-obs floor and rounding kept).
  Under `-W error` this had FAILED agent2 entirely (skipping memo/posttrade)
  — worth knowing for any future strict-warnings CI.
- `datetime.utcnow()` (deprecated) → timezone-aware now with naive-UTC
  semantics preserved (program_trading defaults, page3 board).
- `.gitignore`: the three derived JSONs (event_library, run_library,
  bestex_records) are now ignored — regenerated by app use; decision
  reversible if the user prefers committing seeded libraries.
- ARCHITECTURE_DIAGRAMS node→module maps updated for the views/ layout.


---

# Session 5l — Final caveat sweep + HANDOFF v3

- README repaired: the repo-structure block had been TRUNCATED MID-LINE since
  the original failed-anchor incident (file ended at "live-execu"); fully
  rebuilt with the current tree (views/, 10 new modules), intro updated to
  three modules, Testing section counts refreshed (178). Gap register's stale
  "64 tests" fixed.
- Two cosmetic f-string-without-placeholder warnings fixed (page1).
- Algo wheel output now carries an explicit multiplicity caution (BH screen
  when re-running across configs) — the quant-review leftover.
- `docs/HANDOFF_2026-07-08_v3.md` written — supersedes v2 for state (three
  pages, 178 tests, anchors list, derived-data policy, docs map, prioritized
  backlog led by B7 multi-day, per-view P-A protocol, pyflakes lesson).
  v2's operating protocols P-A…P-G remain the incident reference.


---

# Session 5m — Original TWSE project materials reviewed

`docs/ORIGINAL_TWSE_PROJECT_REVIEW.md` — digest of the uploaded internship
artifacts: pipeline reconstruction (2x4 limit taxonomy via process_data;
7-day path/transition machinery; 1-min full-universe intraday pickles ~5k
name-days across MSCI May/Aug-24 + FTSE Jun-24; threshold detector 9-11AM),
ranked improvement list each mapped to the current platform (inference,
OOS-validated hazard model, rebalance attribution control, magnitude-aware
paths, sample accumulation, execution realism, engineering), and a summary
of the July-2024 AI presentation (46 slides, dot-com comparison, 4-layer
opportunity map, 4 takeaways). Notable connective tissue: the internship's
tight/normal/trending/extremely-trending buckets are Agent 2's regime
labels. Reading coverage stated in-file (Rebalancing.docx is image-only —
unreviewable; Sentiment Scrapper partially read).


---

# Session 5n — Demo video script (expert audience, maintainable)

`docs/DEMO_VIDEO_SCRIPT.md` v1.0 — 16 segments, 28:30 budgeted of a 30:00
cap, each segment carrying [time budget] / SOURCE modules / UPDATE WHEN
triggers / SCREEN directions / NARRATION. Maintenance contract at the top:
edit by segment via SOURCE line, re-check Appendix B, rebalance the §0
timing table, bump the version line. Appendix A = demo prep (cache
pre-warming, library seeding ≥3 events, sample program CSV incl. the
Moutai odd-lot+BLOCK demo, rate-limit discipline). Appendix B = claims
audit: every on-camera number mapped to its test or doc, plus the
literature numbers allowed on camera. Narration written to expert
standards (memo-item impact convention, S1 zero-tracking rationale,
Brown-Warner anti-conservatism, blocked-design wheel honesty, stylized
program-desk disclosure). One self-audit correction applied before ship:
Segment 5 initially overstated the spread blend's disagreement handling
(it medians + flags; it does not refuse). Code-level spot-checks of the
claims table pass programmatically.


---

# Session 5o — Execution Solutions angle (interviewer-role mapping + feature)

`docs/EXECUTION_SOLUTIONS_ANGLE.md` — maps the interviewer's APAC ES role to
the platform; demo path + anticipated pushbacks. **Built:**
`condition_adjusted_ranking` in agents/algo_wheel.py (raw vs condition-
adjusted algo ranks; adjustment = cost-model strategy dummies holding
size/vol/participation/spread fixed; Δ-rank movers + 5% separability),
rendered in the Cost Model section as "the wheel-defense view". Tests: the
confounded-flow case (better engine + harder flow: raw rank last → adjusted
rank first), balanced-grid equivalence (ranks coincide, movers empty),
small-panel guard. Suite 178 → 181 passed. Demo script NOT yet updated with
this feature — add to Segment 7 + Appendix B on next script edit (script
stays v1.0/178-tests until then).


---

# Session 5p — Demo script v1.1 + statistics-first prep roadmap v2

- `docs/DEMO_VIDEO_SCRIPT.md` bumped to **v1.1** per its maintenance
  contract: Segment 7 extended to 1:50 with the condition-adjusted ranking
  (narration includes the both-ranks-always honesty line), timing table
  re-cumulated (28:50/30:00), Appendix B gains the ranking row, 178→181
  test claims updated. (First patch attempt failed on a wrapped-line anchor
  — assert-before-write held; corrected anchor applied.)
- `docs/GSET_Prep_Roadmap.docx` + `.pdf` (v2, statistics-first, replaces the
  uploaded Round-1 version; saved to docs/): §3 ten-question statistics bank
  with 60–90s answer sketches (paired design→test, power worked example
  n≈1,760 pairs for 2bps at σ_d=30, robust-vs-clustered SEs, Friedman/
  Nemenyi + BH + no-peeking, non-normality toolkit, monthly-TCA mix
  decomposition, A/B design, Brown-Warner single-firm, VR/Ljung-Box,
  three selection-bias stories); §4 CV-specific probes incl. the Invesco
  +2% self-critique delivered without defensiveness; §5 demo-live mapping
  table (method → platform location → one-line script); §6 7-day stats
  sprint; §7 day-before checklist with stats-flavored questions to ask her.
  Round-1 context retained condensed (§1–2). NOTE: the interrupted
  interviewer-Q&A task is absorbed into roadmap v2 §3–4.


---

# Session 5q — Study quiz tools (JD-mapped, single-source)

31 scenario questions with standard answers + practical-application notes,
mapped to the US-flow Quant Execution Consultant JD (8 categories:
benchmarks/TCA 5, microstructure/impact 5, US market structure 6,
backtesting 3, A/B testing 3, statistics 4, kdb+/q 2, client/compliance 3).
Single source of truth `docs/quiz_src/questions.py` + `build_quiz.py`
regenerates BOTH artifacts: `docs/QUANT_CONSULTANT_QUIZ.md` (study doc) and
`docs/QUANT_CONSULTANT_QUIZ.html` (interactive: category filters,
answer-aloud-then-reveal, got-it/review-again self-scoring, in-memory only —
resets on reload by design). US-specifics written with care (NYSE 3:50 /
Nasdaq 3:55/3:58 cutoffs, LULD tiers, T+1, Reg NMS 610/611 with the 2024
amendments phrased as verify-current-status). Questions deliberately
complement roadmap v2 §3 (scenario/factual mix vs. spoken answer sketches).


---

# Session 5r — Technical question bank (stats / programming / math)

Second bank added to the study-tool system: `docs/TECH_QUESTION_BANK.md` +
`.html` — 44 questions across 12 categories (inference 7, regression 6, time
series 5; Python 6, SQL 3, kdb+/q 2, algorithms 3; probability 5, linear
algebra 3, optimization 2, stochastic 2). Fundamentals with exact answers
(Bayes base-rate 27% worked example, Welford, merge_asof≡aj, HH=6/HT=4 with
retained-progress logic, AR(1) half-life, OU half-life, Lagrangian
marginal-cost equalization → why volume-following schedules are near-optimal)
each with a desk practical-application note. Build system generalized:
`quiz_src/build_bank.py` + shared `quiz_template.html` now regenerate BOTH
banks from their question modules (original build_quiz.py superseded; both
artifacts regenerated through the new path to prove it). One self-editing
artifact caught and cleaned in the HH/HT answer before ship.


---

# Session 5s — Tech question bank extended: 44 → 96, three-tier structure

Bank restructured with tiers (T1 Fundamental 39 / T2 Role-critical 39 /
T3 Good-to-know 18) applied per concept; builder + shared template upgraded
(tier legend + per-question tags in md; toggleable tier filter chips + card
badges in html); both banks regenerated through the generic path. 52 new
questions across all areas: inference fundamentals (SD-vs-SE, LLN-vs-CLT,
independence-vs-uncorrelated with the X,X² counterexample, paired-power via
the covariance term, MLE, causation escapes, missing-data mechanisms, delta
method), regression (R²-vs-adjusted, dummy trap, residual-plot reading,
interactions, temporal OOS validation, IV, quantile), time series (white
noise, RW-with-drift, EWMA≡IGARCH, cointegration, Diebold-Mariano),
probability/stochastic canon (birthday 23, Monty Hall 2/3, memorylessness,
coupon collector 14.7, gambler's ruin k/N + k(N−k), E[max 2 dice]=161/36,
Markov/stationary, hitting time, GBM vol drag, Itô), Python (container
complexities, mutable defaults, is-vs-==, index alignment, NaN semantics ×3,
generators, GIL), SQL (WHERE/HAVING + NULL 3VL + NOT-IN trap, UNION ALL +
ROW_NUMBER pattern, B-tree/composite order), algorithms (sort stability,
binary-search-on-monotone-predicate, sliding window O(n), reservoir
sampling), linalg/optimization (mult chain cost, det=0 decoded, QR-vs-X'X
conditioning, FOC/SOC + convex shortcut, step size/κ, KKT with binding-cap
pricing). Numeric answers spot-checked programmatically (dice EV, coupon,
AR half-life, Bayes 27%).

---

# Session 5t — Behavioral bank (third bank; framework + model answers)

`docs/BEHAVIORAL_QUESTION_BANK.md` + `.html` — 17 questions, tiers relabeled
per-bank (certain/likely/occasional; builder gained INTRO + TIER_LABELS
support, other two banks regression-rebuilt through the changed path).
INTRO = the STAR-R framework (STAR + Reflection, with per-step time budget
and the constraint-in-Task / choice-in-Action / number-in-Result rules) +
three delivery rules + the six-story matrix mapping Bill's real experiences
(Invesco limit-up, threshold self-critique, AI presentation win, agentic
platform, trader proposals, extension+handover) to every behavioral
dimension. Model answers written in first person from the CV/project record,
each with a coaching note; the flagship Q3 is a fully-annotated [S][T][A][R][Rf]
worked example; mistake/weakness answers use REAL flaws (in-sample thresholds
shipped under pressure; over-building before validating) with process fixes.


---

# Session 5u — Interviewer-specific bank (fourth bank)

`docs/INTERVIEWER_PREP_BANK.md` + `.html` — 20 tiered Q&A (T1 highly-likely
8 / T2 8 / T3 4) built from the interviewer's profile read (Zhejiang econ →
GS HK 2012–14 → Tokyo 2014–17 through the tick-size program → senior APAC
ES): China/HK depth by origin, Japan by lived experience. INTRO = profile
read + FIVE client-conversation vignettes (wheel review, China access
advisory, Japan close deep-dive, customization request, market-event color
call), each ending with the interview probe it generates. Market Q&A:
Connect/A-share transfer-breakage, HK CAS funnel + VCM + stamp history,
A-share curve shape, China short honesty; Japan Nov-2024 close reform WITH
measurement design, special-quote mechanics ('don't chase the walking
quote'), 2014–15 tick program → US 2024 reform bridge, PTS/ToSTNeT; APAC
curve design, TCA-in-Asia differences (incl. the price-limit CENSORING
point), Korea short-sale process answer, pan-Asia wave sequencing. Advisory:
wheel-demotion three-layer investigation (mix → conditional → localize),
raw-wheel diplomacy, deep-dive deck contents. Client-situation behaviorals:
error-in-sent-analysis (speed+ownership+systemic fix, tied to the Invesco
in-sample story), harmful customization ('their execution, our advice, in
that order'), sales pressure ('credibility is the product'), cold-client
build, intraday angry call ('give them the decision with its price').

---

# Session 5v — AI-at-GS research + fifth prep bank

Researched (WebSearch, July 2026): GS AI Assistant firmwide June 2025 on the
model-agnostic GS AI Platform (GPT/Gemini/Claude/open-source; ~10k pilot from
Jan 2025; Argenti); Devin/Cognition pilot July 2025 (first major bank,
~12k-engineer org, hundreds of instances, legacy/refactor tasks, 3-4x vs
prior tools, 'hybrid workforce' supervision framing); GSET public materials
(data-driven SOR venue analytics, Sonar, Atlas modularity).
`docs/AI_AT_GS_PREP.md` + `.html` — INTRO: 4-pillar landscape brief with the
governance through-line (internal/governed/supervised/model-flexible) + the
60-second positioning script tying Bill's platform stance (no LLM in the
cost path; 181 tests; critic-flags-not-overrides) to the firm's own posture.
14 tiered Q&A: what's-actually-agentic, AI-in-ES use-cases ranked by
value-to-risk, LLM risk controls ('narrate, never compute'), ML-vs-stats
(testify vs predict split), the GS-landscape homework answer, volume-model
validation, LLM TCA commentary yes-with-architecture, RL honest take
(supervised+bandits engineering), critic-no-override defense, Devin
implications ('the tests are the supervision'), RAG/fine-tune/prompt rule,
LLM eval discipline, AI limits, replacement curveball.

---

# Session 5w — Questions-for-her prep sheet

`docs/QUESTIONS_FOR_HER.md` — 8 curated questions in two tiers + bold-closer
option + do-not-ask list + delivery rules (2-3 chosen live, follow-up-once
discipline, craft→impact→closer sequencing, note answers for the thank-you).
Tier 1: client-data-disagrees craft question, analysis→product 'what made it
persuasive internally' impact question, first-90-days closer. Tier 2:
Tokyo-arc reflection (rapport-gated), customization-vs-product boundary,
wheel-verdict sample-size pressure (the stats-culture probe), AI
stuck-vs-disappointed + recovered-hours. Each with why-it-works +
listen-for notes.

---

# Session 5x — Stats-review handoff for a new chat

`docs/HANDOFF_STATS_REVIEW.md` — self-contained context transfer: candidate
+ seat + round-2 statistics feedback + interviewer read; the tested
knowledge map (A–F: design/inference with the 1,760 worked example and
3-layer multiplicity, regression-as-TCM chain with OVB-as-wheel-defense,
time series, Brown-Warner + the censoring signature move, non-parametrics,
probability screeners); the used-DAILY table (7 workflows → their embedded
statistics); ready evidence (Invesco self-critique + platform demo list);
known gaps to probe (spoken derivations, clustered-vs-HAC specificity,
sequential testing recognition); file pointers; and a 6-step session plan
(cold audit → drill loop → scenario wrappers → spoken derivations → two
set-pieces → mock close).

---

# Session 5y — Mobile continuation capsule

docs/CONTEXT_CAPSULE_MOBILE.md — one-page paste-ready context transfer for
continuing prep on Claude mobile (identity, interview state, platform asset
summary with the demo-able stats stack, rehearsed set-pieces, materials
pointer, and a fill-in intent line). Companion guidance delivered in chat:
Cowork web/mobile sync (July 2026 rollout) as path A; claude.ai Project with
uploaded docs as path B; paste-capsule as path C.

---

# Session 6a (2026-07-09) — Counterfactual impact propagator (interviewer question → feature)

Sherry's round-1 question ("re-run history with a more aggressive strategy —
the tape doesn't reflect its impact") implemented as
`agents/impact_propagator.py`: permanent/temporary kernel (η·σ_d·√(q/ADV)
split 40% permanent / decaying temporary with half-life), strictly causal
path perturbation (own-slice impact stays the Level-1 overlay — composition
without double counting), schedule-invariant repricing (disclosed), and
`counterfactual_with_bands()` sweeping η×half-life grid → delta band +
robustness verdict ("needs a live A/B" when the sign flips). UI: expander in
the Live Session once interventions exist; raw reconciled numbers untouched.
Tests: 5 (exact decay arithmetic, causality, sell mirror, end-to-end bands,
η-monotonicity). Suite 181 → 186. Statistical roadmap in
docs/COUNTERFACTUAL_IMPACT_MODEL.md (NLS kernel calibration from event
library reversion/markouts, Bayesian shrinkage → credible intervals,
bootstrap uncertainty propagation, sim-to-real slope/intercept validation,
regime-conditional kernels, de-impacting real-account history).
NOTE: tests/test_sell_side.py corrupted trailing line RESURFACED (line 129,
same P-B artifact — likely restored by a commit/checkout of the broken HEAD
copy); removed again. If the repo was committed since HANDOFF v3, verify the
committed copy is the FIXED one this time.


---

# Session 6b — Flow-prediction framework, all six layers (suite 186 → 197)

`agents/flow_forecast.py` (~330 lines) + `tests/test_flow_forecast.py` (11):
- L1 daily volume: demeaned log-volume AR(1) + day-of-week + event dummies,
  walk-forward one-step eval over the back half, Diebold-Mariano-GATED vs the
  20-day median — a model that can't beat naive SHIPS naive (pinned by the
  white-noise test: chosen_model == median20). dm_test implemented (squared
  loss, Bartlett HAC).
- L2 intraday: blended_day_total — precision-weighted Kalman-lite combining
  the pre-open forecast with the curve-grossed-up tape (weight-on-tape → 1 as
  the day completes; disclosed heuristic variance model).
- L3 close-share AR(1): mu/phi/half-life + next-day forecast from the
  last-bar volume share series (close_share_series); recovery pinned on
  synthetic AR (φ 0.7 → 0.715).
- L4 event uplift: record_event now stores t_day_volume_multiple (ab_vol at
  T, wired in page2), library_stats exposes its median; event_uplift returns
  library median (n≥3) else a DISCLOSED 1.4x placeholder.
- L5 signed-flow DIAGNOSTICS ONLY: BVC (reused from agent9) imbalance mean,
  lag-1 autocorr, Ljung-Box; output states direction prediction is alpha
  territory and out of scope.
- L6 ML gate: lag/rolling/dow features, numpy-ridge (sklearn GBM auto-used
  if installed — it is NOT in this sandbox), walk-forward MAE + DM vs plain
  AR comparator; use_ml verdict honest by construction.
UI: "Flow forecast (Layers 1–6)" expander in Pre-Trade Analytics after the
expected-cost table — L1 metrics + DM gate, L3/L4/L5/L6 caption lines, house
-rule caveat. AppTest clean; pyflakes clean (pre-existing widget-var noise
only). Test-tolerance lesson: dataclass fields round to 4dp — identity
assertions must match the rounding.


---

# Session 6c — GSET algo research → two documented traits adopted (197 → 199)

Public-source research (The TRADE GSET guide; GS pages; Sonar Dark X launch
release): suite = VWAP/TWAP/IS/Scaling (benchmark), Participate
(participation, 'ignoring outsized prints'), Sonar/Sonar Dark X ('liquidity
scoring framework' + 'Liquidity Shield' balancing quality vs capture via
venue segments/min quantities/spread allowances)/Stealth (seeking),
SmallCap/SpreadTrader/Port X/Navigator/1CLICK (specialists/meta) + SOR/
Sigma X/Atlas. Adopted the two DOCUMENTED behavioral traits:
- `_sim_pov`: outsized-print filter — bar participation base capped at
  POV_OUTSIZE_CAP(3.0)× trailing-median volume (POV_MED_BARS=12, causal).
- `_sim_liquidity_seeking`: Liquidity-Shield-style progress relaxation —
  mult = clip(1 + K·z + LIQ_SHIELD_K(0.8)·behind), behind = elapsed − filled
  fraction; selective early, capture-oriented when lagging; side-symmetric.
Stealth's seeded jitter + cap already embodied the anti-gaming trait (no
change). IS/MOC/MOO deliberately untouched (pinned anchors; no public basis
for adaptivity). New tests: block-print cap + shield-relaxation monotonicity
(tests/test_agent3.py). All prior anchors + mirror suite intact.
`docs/GSET_ALGO_IMPLEMENTATION_NOTES.md`: per-algo public summary, our
analog mapping, adopted-trait table with guards, honest-boundary paragraph.
Backup: ~/backups/agent3_pre_gset_traits.py.

## Session 6d (2026-07-15) — L6b learning upgrade + SOR "Shield" policy

- `agents/flow_forecast.py` +2 layers (L6b): `quantile_volume_forecast`
  (exact Koenker-Bassett LP via scipy HiGHS; walk-forward pinball-gated vs
  rolling 20-day empirical quantiles; monotone-enforced P10/P50/P90) and
  `pooled_volume_model` (per-symbol demeaned pooled ridge with DOW dummies,
  gated vs per-name AR(1) via DM). Same house rule: can't beat naive → ship
  naive.
- `agents/agent13_venue_router.py`: new policy "Shield (dark-patient)"
  (SHIELD_PATIENT_FRAC=0.5): early-phase dark residual carries forward
  cross-bar instead of same-bar lit sweep; conservation preserved (final
  sweep guaranteed); policy note appended; compare_policies picks it up
  automatically. Backup: ~/backups/agent13_venue_router.py.
- UI: Page 1 flow expander gains an L6b caption (quantile head note).
- Design narrative: "SOR & dark pool incorporation" section appended to
  docs/GSET_ALGO_IMPLEMENTATION_NOTES.md incl. honest fill-level boundaries.
- Tests: +5 flow (quantile monotonicity, white-noise gate ships empirical20,
  pooled beats per-name AR on shared-DOW panel, 2-symbol guard) and
  +2 agent13 (Shield conservation + higher dark share; cost <= Cost-optimized
  at wide spread). Suite: **205 passed, 1 live deselected.** AppTest clean.
- Reminder: verify committed tests/test_sell_side.py is the fixed copy.


## Session 6e (2026-07-15) — Quarterly Client Review (QBR) module

- New `agents/quarterly_review.py`: six-section QBR framework (flow profile
  / headline distributions / decomposition / difficulty-adjusted ranking /
  outlier attribution / trend & actions) built from the run library.
  Adjusted ranking reuses cost_model.ab_test_with_controls with the control
  set the run library supports (sqrt size, urgency, market FEs — disclosed).
  Rule-generated recommendations each carry supporting numbers; no verdict
  on cells with n < MIN_CELL=5; raw league table never stands alone.
  `synthesize_demo_quarter` plants known structure (LIQ +8 edge, IS −1,
  >10% ADV pain, urgency premium) and is CLEARLY LABELED synthetic.
- New `views/page4_quarterly_review.py` (plotly): mix bars, box-by-algo,
  market×algo heatmap (small-n cells blanked), predicted-vs-realized
  scatter with 45° line, outlier Pareto with cumulative share, monthly
  trend, adjusted-ranking table with rank-mover warning.
- `app.py`: 4th module "📋 Quarterly Client Review" registered
  (backup ~/backups/app_pre_qbr.py).
- Tests: `tests/test_quarterly_review.py` (6) — planted structure recovered
  (LIQ separable at 5%, IS baseline), size/urgency effects, quarter filter
  + prior-quarter QoQ, MIN_ORDERS gate, empty-library gate.
  Suite: **211 passed, 1 live deselected.** AppTest incl. Page-4 demo render.


## Session 6f (2026-07-15) — kdb+/q market-data source

- `agents/agent1_market_data.py` refactored (backup ~/backups/): derivation
  (ADV, Yang-Zhang, vol profile) extracted into `assemble_market_data` —
  any source delivering two normalized OHLCV frames gets the identical
  MarketData contract. yfinance path behavior unchanged.
- New `agents/kdb_source.py`: KdbSchema mapping, server-side `xbar` bar
  aggregation queries, connect_kdb (qpython→PyKX→actionable error),
  KdbHandle normalization (keyed tables, byte syms, minute-typed bars),
  fetch_market_data_kdb with injectable query_fn (testable w/o server).
- `views/common.py`: `_cached_fetch_kdb` + `kdb_source_expander` (host/port/
  auth/schema mapping UI, connect test) + `fetch_any` dispatch (loud
  fallback — broken kdb config never silently becomes Yahoo data).
  `views/page1_simulator.py`: expander rendered above Inputs; fetch routed
  through `fetch_any`.
- `docs/KDB_INTEGRATION.md`: architecture, q queries, driver notes, honest
  production boundaries (no .u.sub, no sym-enum edge cases, no pagination,
  identifier trust domain, timezone convention).
- Tests: `tests/test_kdb_source.py` (8) — query builders incl. custom
  schema, MarketData contract from q-shaped stub frames, date+bar timestamp
  assembly, int-minute bars, empty-result error, driverless connect error,
  and run_pipeline end-to-end on kdb-sourced data.
  Suite: **219 passed, 1 live deselected.** AppTest clean.


## Session 6g (2026-07-15) — tick-file ingester (free historical tick data)

- New `agents/tick_ingest.py`: LOBSTER (exec types 4/5, /10000 price),
  Binance trades+aggTrades (zip, headerless, ms/us epoch auto-detect),
  generic CSV mapping, IEX HIST via optional IEXTools; all -> normalized
  trades frame (canonical kdb trade shape) -> `trades_to_bars` (q-xbar
  identical semantics) -> `market_data_from_trades` (assemble_market_data;
  thin single-day context disclosed) -> optional `to_kdb_csv` + q 3-liner.
- `views/common.py`: source expander now 3-way (Yahoo / kdb+ / tick file);
  `_tick_file_form` with uploader + per-format inputs; `fetch_any` returns
  the pinned tick MarketData (loud pin, explicit unload).
- Docs: tick-file section appended to KDB_INTEGRATION.md.
- Tests: `tests/test_tick_ingest.py` (10) — parser correctness incl. epoch
  unit detection, xbar semantics vs hand-computed bars, contract assembly,
  external-daily supplement, multi-sym guard, q csv roundtrip (date/time
  literal formats). Suite next run expected ~229.


## Session 6h (2026-07-22) — PT Dealer cockpit (CLSA PT Dealer JD)

- New `agents/pt_dealer.py`: LIMIT_BANDS (static daily-band table w/ tier
  proxies + n/a-with-mechanism for HK/SG/US/AU/UK), `limit_proximity`
  (WATCH>=60% / ALERT>=80% / LOCKED>=99.5% of band, side-aware),
  AUCTION_CUTOFFS (per-market close-auction mechanism + cutoff),
  `auction_countdown` (minutes-to-cutoff, urgency status), `attention_queue`
  (ranked triage, weights 40/25/20/15, short-BLOCK pins 100, explicit
  reasons), `build_audit_pack`/`save_audit_pack` (timestamped compliance
  record as by-product), `demo_basket` (exercises every rule).
- Page 3: "PT Dealer Cockpit" section — editable basket (data_editor),
  cutoff table, attention queue, audit-pack download. Backup ~/backups/.
- `.gitignore`: data/audit_packs.json.
- Docs: `CLSA_PT_DEALER_REFINEMENTS.md` (JD bullet -> feature map, rule
  tables summary, 7-step desk-automation roadmap, honest boundaries) +
  `HANDOFF_CLSA_PORTFOLIO_TRADING.md` (interview capsule, prior block).
- Tests: `tests/test_pt_dealer.py` (11) — band math incl. LOCKED/downside,
  n/a markets, cutoff minutes math + PASSED + sorting, triage ordering,
  short-block pin, audit roundtrip. Suite: **240 passed, 1 live deselected.**
  AppTest incl. Page-3 cockpit render.


## Session 6i (2026-07-22) — desk automations implemented (interview answer)

- New `agents/pt_automation.py`: A1 preopen_pack (lot-normalized shares,
  pre-flight, %ADV/capacity RAG, explicit costs, settlement, side/notional
  imbalance, cutoffs, formatted text); A2 alert_scan (TRANSITION-based:
  limit escalation, cutoff T-15 w/ residual, run-rate collapse; no re-page
  on refresh) + acknowledge -> data/alert_log.json (ack IS the audit
  record); A3 eod_client_summary (per-market fills, residual roll plan,
  notable events, settlement, optional slippage); A4 classify_breaks
  (AUTO_CLEAR within tol; QTY/PRICE/MISSING classes + suggested actions);
  A5 event_radar (Agent 12 offline cadence + event-library volume
  multiples; key fix: 'effective (approx)').
- `agents/pt_dealer.py`: rules_version() sha over all rule tables, stamped
  into audit packs/alerts/packs (A6). Backup ~/backups/pt_dealer_pre_6i.py.
- Page 3 "Desk Automations" section: five expanders + A6/A7 note.
- `.gitignore`: data/alert_log.json.
- Doc: CLSA_PT_DEALER_REFINEMENTS.md roadmap marked implemented.
- Tests: tests/test_pt_automation.py (10) — imbalance math, capacity RAG,
  fire-once + escalation re-fire, cutoff alert + ack roundtrip w/ version,
  EOD contents, all 5 break classes, radar window/quiet, version
  stability/sensitivity. Suite expected ~250.


## Session 6j (2026-07-22) — rulebook reconstitution predictor

- Gap identified: Agent 12 had calendar + announced-change scraping, but no
  rulebook-based membership PREDICTION. New `agents/reconstitution.py`:
  predict_msci (GMSR at 85% cumulative FF coverage — verified vs GIMI book;
  0.5-1.15x range; QIR add multiple 1.8x configurable w/ verify note;
  float/ATVR screens; +/-15% watch band), predict_ftse (90/111 rank buffer
  + reserve pairing holds index size), expected_flow (weight x AUM-input /
  ADV), demo_universe with planted add/delete/screen-fail stories.
- Page 2: "Reconstitution screener" expander (methodology radio incl.
  SAIR-vs-QIR contrast, thresholds line, adds/deletes/watch tables, flow
  table, honest not-modeled caption). Backup ~/backups/page2_rebalancing.py.
- INDEX_REBALANCE_RESEARCH.md §8 with methodology sources.
- Tests: tests/test_reconstitution.py (9) — GMSR crossing math, buffer
  keeps incumbent while gating newcomer, QIR stricter than SAIR, screen
  deletions/blocks, watchlist, scaled 90/111 with pairing, reserve top-up,
  flow arithmetic, demo-story recovery.
  Suite: **259 passed, 1 live deselected.** AppTest incl. Page-2 render.


## Session 6k (2026-07-22) — positioning check for rebalance names

- New `agents/positioning.py`: `positioning_footprint` (excess abnormal
  volume A->T-1 in ADV-days x disclosed 50% participation assumption;
  CAR-drift confirmation; HEAVY needs both volume >=3 ADV-days AND drift
  >=2% — volume without drift downgrades to MODERATE with 'two-sided'
  note); PUBLIC_POSITIONING_SOURCES per-market table incl. broker-only
  honesty row; `short_interest_snapshot` (yfinance FINRA fields,
  injectable info_fn, degrades with pointer to official sources for
  non-US).
- Page 2: 'Positioning check' expander after crowding/expected-move —
  footprint badge + caveats + source table; announcement date narrows the
  window when set.
- docs/POSITIONING_DATA_SOURCES.md: three-layer answer (inference /
  official disclosures / broker-only) + interview framing + sources.
- Tests: tests/test_positioning.py (8) — footprint math, drift-gated
  verdicts, window narrowing, degradations, source-table coverage,
  injected snapshot building signal. Suite: **267 passed, 1 live
  deselected.** AppTest incl. Page-2 render.


## Session 6l (2026-07-22) — AI rebalance-interest monitor

- New `agents/rebalance_monitor.py`: interest_features (abnormal vol /
  sigma-scaled drift / range expansion + injectable short-delta & news
  count, capped 0-1 scales), interest_score (transparent composite w/
  per-feature reasons, HOT>=60/WARM>=35), learn_weights (ridge on event
  library, chronological split, static comparator given SAME calibration
  freedom — intercept+slope — so the gate is fair; ships learned only if
  MAE better AND DM p<0.10; thin library ships static w/ disclosure),
  monitor_report (ranked), monitor_alerts (fire-once tier transitions),
  demo panels (orthogonal-driver library where learning genuinely pays).
- Gate verified both ways: signal->learned (recovers news 0.46, p=0.003),
  noise->static.
- Page 2: 'AI rebalance-interest monitor' expander (weight-source line,
  ranked table, transition alerts via session state).
- docs/AI_REBALANCE_MONITOR_DESIGN.md: full CLSA-desk architecture (data
  layers, NLP extension, governance/information barriers, 30-second
  interview version).
- Tests: tests/test_rebalance_monitor.py (8). Suite: **275 passed,
  1 live deselected.** AppTest incl. Page-2 render.


## Session 6m (2026-07-22) — desk automations round 2 (pt_ops)

- New `agents/pt_ops.py`: A8 normalize_client_file (BBG suffix map w/
  HK 4-pad + KR 6-pad, side codes, notional->shares w/ price, dup
  aggregation, BOTH-SIDES flag, loud issues); A9 HOLIDAYS_2026 static
  table (approx, disclosed) + settlement_date_holiday_aware (reports
  holidays skipped) + closure_warnings + FX_NOTES (TWD/KRW/INR
  restricted); A10 crossing_report (min-of-sides crossable, both-sides
  spread saving, CROSSING_RULES mechanism per market, same-client
  exclusion); A11 exposure_schedule REDESIGNED mid-build: terminal net is
  structural — scheduler holds PATH deviation around the structural
  pro-rata line within +/-band while front-loading urgency, and reports
  the unthrottled counterfactual (initial version tried to fix the
  structural net by scheduling — wrong frame, caught in review).
- Page 3 "Desk Automations — round 2": four expanders wired to the
  cockpit basket / demo data.
- CLSA_PT_DEALER_REFINEMENTS.md §5 added.
- Tests: tests/test_pt_ops.py (12) — conventions, dup/unknown flags,
  notional conversion + BOTH-SIDES, CNY-cluster settlement (Feb-12 ->
  Feb-24), Golden-Week warning, FX restricted flags, crossable math +
  mechanisms, same-client exclusion, band-capped path deviation,
  completion. Suite: **287 passed, 1 live deselected.** AppTest Page-3.


## Session 6n (2026-07-22) — desk deployment plan (no code)

- docs/DESK_DEPLOYMENT_PLAN.md: how to take A1-A11 + cockpit + monitors
  to production with institutional access. Principles (shadow-first, no
  shadow IT, gates travel along, sequence by risk); data upgrade map
  (FIX drop copy = biggest upgrade; kdb adapter already written; official
  regime feeds; index product subscriptions turn the reconstitution
  predictor into a reconciler); phased 2w/30/60/90/6m rollout with
  measurable exit criteria per phase; governance checklist (compliance,
  model governance w/ auto-revert-to-baseline policy, audit retention,
  IT); success metrics; honest risks (entitlements slower than code,
  desk may already have tools, chat NLP last, trust is the budget).
- No code changes; suite remains 287 passed, 1 live deselected.


## Session 6o (2026-07-22) — implementation detail + JD re-review (docs only)

- DESK_DEPLOYMENT_PLAN.md §6: per-automation implementation detail
  (A1-A11 + cockpit): data interfaces (FIX drop-copy tags 35=D/8, 151,
  14; SWIFT MT535/545/547 via ops extracts; exchange parameter files;
  MSCI/FTSE product files), integration patterns (numbers-locked LLM
  templating for client-facing text; flag-only crossing; validation gates
  per item; S/M/L effort with entitlements called out as the long pole).
  A7 rule-table service identified as the multiplier to build early;
  reconstitution predictor becomes a reconciler vs provisional lists.
- DESK_DEPLOYMENT_PLAN.md §7: JD re-review found 8 NEW AI automations not
  in the project (B-series): B1 NL order-instruction copilot (confirm-back
  control), B2 regulatory-change monitor (LLM over exchange circulars ->
  diffs vs rule service, best LLM fit on the JD), B3 news guard on live
  baskets, B4 ownership/disclosure threshold monitor (real gap: we check
  short legality but not accumulation vs 5%-style + foreign-room caps),
  B5 pre-submission fat-finger anomaly guard, B6 follow-the-sun handover
  generator, B7 ops correspondence drafter (numbers-locked), B8
  client-flow pattern model (most sensitive, last, gated). Sequencing +
  one-line interview version included.
- Docs only; suite remains 287 passed, 1 live deselected.


## Session 6p (2026-07-22) — market-structure fingerprint & drift tracker

- New `agents/market_structure.py`: structure_fingerprint (close-bar
  share, U-shape, lunch dip, Roll spread reuse, 5-min variance ratio,
  lag-1 autocorr, overnight variance share, Amihud), describe_fingerprint
  (numbers -> dealer words), record_fingerprint/structure_drift (snapshot
  library data/structure_library.json + thresholded what-changed
  briefing), MARKET_STRUCTURE_NOTES (2026 qualitative per-market state,
  web-verified: Nextrade ~10% stall under 15% cap, China program-trading
  rules Jul-2025, India T+0 top-500, HKEX RMB counter staging).
- Page 1 expander: metrics row + words + drift-vs-last-snapshot +
  snapshot button + per-market 2026 note. .gitignore: structure library.
- docs/MICROSTRUCTURE_STUDY_GUIDE.md: study method (measure don't
  memorize; reconcile fingerprint vs rulebook), measurement framework
  table, sources.
- Note: conftest make_market_data has flat intraday closes — vr/autocorr
  correctly degrade to None on it; tests use a richer local synthetic.
- Tests: tests/test_market_structure.py (6). Suite: **293 passed, 1 live
  deselected.** AppTest clean.


## Session 6q (2026-07-22) — PT basket trade cycle walkthrough (doc)

- Checked chat + docs first: no existing end-to-end cycle doc (only
  per-stage automations; RFQ/risk-bid stage explicitly out-of-scope in
  gap register). New docs/PT_BASKET_TRADE_CYCLE.md: 9 stages (RFQ w/
  blind-profile agency-vs-risk-bid mechanics -> award/staging ->
  pre-trade -> execution day -> booking/allocation -> EOD -> settlement
  -> recon -> QBR loop back to RFQ), each mapped to platform modules;
  two honest boundaries (risk-bid pricing, OMS booking/allocation);
  ASCII cycle diagram; interview one-liner ("automates six of nine
  stages"). Docs only; suite unchanged (293 passed, 1 live deselected).


## Session 6r (2026-07-22) — principal PT appendix (doc)

- PT_BASKET_TRADE_CYCLE.md appendix: how a principal/risk basket works —
  blind-profile auction (names only after winning), bid anatomy
  (hedgeable-vs-idiosyncratic split, unwind cost from the same sqrt-law,
  Asia frictions incl. unhedgeable China shorts, winner's curse/toxicity,
  book netting; stylized premium formula), strike mechanics + immediate
  futures hedge, unwind economics (P&L identity), controls (pre-hedging
  restrictions, info barriers, balance sheet — why agency-only CLSA
  doesn't and how that's the pitch), and what carries over to an agency
  dealer. Docs only; suite unchanged (293 passed).


## Session 6s (2026-07-22) — agency vs principal decision doc

- New docs/AGENCY_VS_PRINCIPAL_DECISION.md: client routing framework —
  the one-line economics (premium P vs E[agency cost] + lambda*sigma),
  6 principal triggers (benchmark prints w/ legal force, deadlines,
  event-gap risk, toxic tail/adverse-selection engine, simplicity,
  netting luck), 7 agency triggers (cost+flexibility, liquid balanced
  baskets w/ tight-bid asymmetry noted, repeat flow, confidentiality
  vs RFQ profile leakage, mandate/conflict rules, transparency/control,
  Asia frictions incl. unhedgeable CN-A shorts), middle-ground products
  (guaranteed VWAP, partial risk on tail, agency incentive, capital on
  residuals), empirical clustering around benchmark-critical dates,
  interview one-liner. Docs only; suite unchanged (293 passed).


## Session 6t (2026-07-22) — application-strength sprint (all 6 suggestions)

- `agents/basket_risk.py` (the quant gap): risk_decomposition (signed-
  notional basket returns vs hedge index -> beta, ann. TE, hedgeable R2
  split, hedge notional, leave-one-out TE contributors), blind_profile
  (masked RFQ artifact — tested to contain NO tickers), agency_quote_sketch
  (framework, 'commission is commercial'), aggregate_basket_costs
  (weighted bps + contribution Pareto), demo_panel with planted
  tracker/idio/negative-beta structure (recovered in tests).
- `views/page0_tour.py`: Guided Demo landing page — one basket through
  the 9-stage cycle using live demo pieces (RFQ profile+quote, messy-file
  normalization, pre-open pack, attention queue, EOD draft, CNY
  settlement push, QBR adjusted ranking w/ rank movers), house-rules
  closer. Registered FIRST in app.py (5 pages).
- `scripts/run_case_study.py`: real-event runner (SMCI/TSLA S&P examples
  documented) -> event study + library record + optional case-study doc;
  offline parser smoke test; network runs are local-only by design.
- README refreshed: 3-modules paragraph -> 5-page overview + data sources
  + house rules (deploy link + CI badge already existed — user had
  already deployed; DEPLOYMENT.md now documents redeploy checklist, cloud
  rate-limit reality, Page-0-works-offline guarantee).
- Tests: test_basket_risk.py (8) + case-study parser smoke (1).
  Suite: **302 passed, 1 live deselected.** AppTest: all 5 pages render
  clean.


## Session 6u (2026-07-22) — MSCI Japan Aug-2026 screener example

- Research (web-verified): MSCI Aug-2026 QIR announces Aug 12 / effective
  Sep 1 — ahead of FTSE Sep semi-annual (eff Sep 21) -> MSCI selected.
  Largest Asia MSCI tracker: EWJ $21.2B (> EWT 10.7 > INDA 6.9 > MCHI 6.0).
- Example run of predict_msci on approximate MSCI-Japan universe:
  RUN-1 LESSON: top-35-only universe inflated the GMSR proxy to $55B and
  false-flagged solid members — GMSR needs the FULL universe; fixed by
  modeling a 350-name mid/small tail -> GMSR proxy $5.7B (matches
  published interim zone), Kioxia predicted add at 2.81x GMSR (clears
  even the 1.8x QIR hurdle), fallen incumbents correctly retained above
  the 0.5x floor, flow $56M/0.3 ADV-days on the EWJ lower bound.
- docs/case_studies/MSCI_Japan_Aug2026_screener.md (with disclosures:
  approx caps, unverified membership assumptions esp. Kioxia, modeled
  tail) + scripts/run_msci_japan_screener.py (live yfinance version,
  local). Suite unchanged (302 passed).


## Session 6v (2026-07-22) — Taiwan May-2026 SAIR backtest + engine upgrade

- Truth set researched (MSCI PR + press; disambiguated Feb QIR HongJing
  story from May SAIR): Taiwan May-2026 = add MPI Corp (6223); delete
  AsiaCement/Catcher/ChinaAirlines/Compal/FarEasternNC/THSR/Teco (all
  migrated Standard->SmallCap); Winbond/NanyaTech watched-not-added.
- Backtest on pre-announcement approximate universe (37 members + 3
  candidates/controls + 300-name tail): ADDS 1/1 (MPI at 1.74x GMSR),
  controls clean; DELETIONS 0/7 — all seven at $4.6-6.5B, far above the
  $2.7B global floor. Diagnosis: SAIR deletions are COUNTRY size-segment
  migrations — the engine's documented omission, now measured.
- Fix implemented: MSCIRules.country_coverage/country_buffer — members
  below country FF-coverage cutoff flagged as segment-migration
  deletions (default off; backup ~/backups/reconstitution_pre_6v.py).
  Re-run: 7/7 deletions, zero named false flags. Circularity caveat
  documented (validates mechanism, not noisy-data ranking).
- Tests: +2 (migration rule isolated via non-member tail so global floor
  is silent; defaults-off behavior preserved). Suite: **304 passed,
  1 live deselected.**
- docs/case_studies/MSCI_Taiwan_May2026_backtest.md — full scorecard,
  caveats, desk workflow, interview one-liner.


## Session 6w (2026-07-22) — backtest caveat fixed (measured, not argued)

- `robustness_check` added to agents/reconstitution.py: Monte-Carlo cap/
  float perturbation -> distribution of add/delete precision & recall.
  May backtest: deletion RECALL robust (mean 0.94, p10 0.86 even at ±30%
  cap error); zero-false-flag PRECISION partly reconstruction luck
  (0.66 mean at ±30%) — claim refined accordingly.
- Out-of-sample: same untuned parameters on Feb-2026 QIR -> adds 1/1
  (HongJing), deletions 4/4; 7 of 9 'false flags' were the names MSCI
  deleted in MAY — the rule was early, not wrong. Buffer calibration
  table: 2% buffer = 4/4 Feb + 7/7 early + zero false flags; buffer
  demonstrated as the precision-vs-early-warning knob.
- Fixes 3 (real as-of caps via local script) and 4 (pre-register the
  Aug-12 prediction in a timestamped git commit, grade after) documented
  as protocol in the case study.
- Tests: +1 (robustness_check structure + clear-cut stability).
  Suite: **305 passed, 1 live deselected.**


## Session 6x (2026-07-22) — FTSE Taiwan 50 June-2026 backtest

- Index selection verified: FTSE TWSE Taiwan 50 is the largest non-Japan
  Asia FTSE index by tracking AUM (0050 alone NT$2.11T ~ US$70B). Truth
  set: June-2026 review adds BizLink/GUC/NanYaPCB/ZhenDing, deletes
  Compermed/ChinaSteel/FormosaPlastics/Hotai; published reserve list
  Compeq/Innolux/Kinsus/WinWay/WTMicro.
- robustness_check generalized (predict_fn injectable) for FTSE engine.
- Round 1 failed usefully: thin/mis-marked universe -> 5 false adds;
  diagnosis incl. MPI being TPEx-listed = INELIGIBLE (listing-venue
  screen = new documented omission). Round 2 (corrected membership):
  adds 4/4 zero false+, pairing holds size 50 exactly, watchlist scored
  Compeq on the PUBLISHED reserve list (fully non-circular hit);
  deletes 2/4 — cap-estimate failures in the crowded $6-10B rank zone.
- Monte Carlo: add recall 0.96/precision 0.89 at sigma=10%; delete
  recall ~0.5 — COMPARATIVE FINDING: rank-buffer deletion boundaries are
  structurally noise-fragile vs MSCI coverage cutoffs (0.94 at 30%) —
  ship the add list as signal, the delete list as a watch zone.
- docs/case_studies/FTSE_Taiwan50_Jun2026_backtest.md incl. 3-backtest
  scoreboard (adds 9/9 across providers). Suite: **305 passed, 1 live
  deselected** (robustness generalization covered by existing tests).


## Session 6y (2026-07-22) — FTSE failure fixed generically

- New `agents/universe_builder.py`: UniverseSpec + validate_universe
  pre-flight (membership count vs index size, LISTING_ELIGIBILITY
  suffix screens for 10 markets, duplicates, float/cap sanity, boundary
  DENSITY check for rank ladders); explicit issues, never silent.
  Meta-test replays the actual round-1 Taiwan universe and catches all
  three original errors (49-count, TPEx MPI, thin delete boundary).
- FTSERules.allowed_suffixes: ineligible candidates excluded inside
  predict_ftse (second layer for MPI-type errors, all markets).
- Boundary-confidence tags in predict_ftse: margin_pct + HIGH/LOW-watch
  per predicted add/delete (10% threshold). June rerun: 4/4 actual adds
  HIGH (17-78% margins), all deletion calls LOW — the Monte-Carlo
  fragility finding now surfaces per-name in the product.
- Tests: tests/test_universe_builder.py (6, incl. the meta-test) after
  2 test-design fixes (empty-frame access; boundary that produced no
  adds). Suite: **311 passed, 1 live deselected.**
- Case-study addendum in FTSE_Taiwan50_Jun2026_backtest.md.


## Session 6z (2026-07-22) — index-event flow simulation + optimal strategy

- New `agents/index_flow.py`: simulate_index_flow (before/after weights
  for ALL names — adds, deletes, AND continuing-member reweights;
  self-financing verified as arithmetic identity; ADV-day bucketing
  MOC/WORK+MOC/MULTI-DAY) + recommend_execution (tracking-tolerance-
  constrained argmin over the agent14 S1-S4 frontier on a calibrated
  pressure-reversal path; per-name, not blanket).
- Taiwan 50 June-2026 run ($70B AUM lower bound): turnover $2.95B (4.2%
  of AUM), self-financing gap 0.00%, reweights = 27% of turnover incl.
  TSMC -$440M (2nd-largest flow of the event, 0.08 ADV-days -> MOC).
  Optimal: adds -> S3 post-effective (S2 infeasible at 91% participation,
  S4 breaches tracking tol); deletes -> S1 100% MOC at -258 bps (riding
  the pressure); MADHAVAN ASYMMETRY emerged from the frontier unprompted
  (tested). Feasibility flag: participation column caught infeasible S2.
- Framework-improvement synthesis (from the two backtests) in the case
  study: done list (country rule, validator, eligibility, confidence
  tags, robustness) + 6-item roadmap (as-of pipeline, review-type
  awareness, multi-cycle buffer calibration, reserve-list output,
  confidence-weighted flows, Aug-12 pre-registration).
- Tests: tests/test_index_flow.py (6) — self-financing, delete/add flow
  identities, dilution/top-up directions, bucketing, buy-sell asymmetry.
  Suite: **317 passed, 1 live deselected.**
- docs/case_studies/Taiwan50_flow_simulation.md.


## Session 7a (2026-07-22) — dual-provider backtests: MSCI Korea + FTSE China A50

- Catalog survey: MSCI Asia (country Standard/IMI/SmallCap + regional
  composites, GIMI coverage mechanism) vs FTSE Asia (GEIS slices + the
  tradable co-brands: TW50, China A50/China 50, STI, KLCI, SET, Vietnam;
  rank-buffer mechanism). Engine mapping documented.
- Engine upgrade first: MSCIRules.min_ffcap_frac_of_add (GIMI's ~50%-of-
  cutoff FREE-FLOAT requirement) — big-cap/low-float names blocked with
  explicit 'blocked add' watch entries (+1 test).
- MSCI Korea May SAIR (truth: 0 adds; 3 deletes Hanjin KAL/HD Hyundai
  Marine/SK Biopharm; Rainbow Robotics tipped-not-added): deletions
  **3/3 zero false flags with the Taiwan-calibrated 2% buffer untouched**
  — coverage deletion logic now 14/14 across three events/two markets.
  Rainbow = kept false positive (passed full-cap AND FF rule at assumed
  0.20 float): diagnosis = candidate FIF/ATVR data quality binds add
  precision; not tuned away (curve-fitting refusal documented).
- FTSE China A50 June quarterly (official LSEG truth set: 5 in AI-hw /
  5 out consumer-banks): adds **5/5 zero false+ all HIGH confidence
  (30-63% margins)** on FF-cap rank basis; deletions 3/5 with all calls
  self-labeled LOW — Taiwan-50 rank-fragility finding replicated
  out-of-market.
- Five-backtest scoreboard: 11/11 actual adds captured, coverage deletes
  14/14, rank deletes ~50-60% self-labeled. Suite: **319 passed, 1 live
  deselected.** docs/case_studies/DUAL_PROVIDER_backtests_Korea_ChinaA50.md.


## Session 7b (2026-07-22) — scorecard improvements + exhaustive coverage map

- Improvements from the 5-review scorecard: NOW shipped — (1)
  FTSERules.assumed_cap_sigma + `p_survives_noise` per predicted add/
  delete (normal approx: margin/sigma -> survival probability; the
  Monte-Carlo fragility finding as a per-name number; delete page now
  probabilistic); (2) `reserve_list` output in predict_ftse (top-5
  eligible non-members below add boundary — we emit what FTSE
  publishes). Roadmap confirmed: float/ATVR data quality binds add
  precision (Rainbow); calibration harness; calendar-driven review-type.
  Tests +2. Suite: **320 passed, 1 live deselected.**
- Coverage map (verified): MSCI 23 DM + 24 EM + ~31 FM/related +
  standalone ~ 80 markets; FTSE 4 tiers (~25 DM / 10 AE / ~13 SE / ~24
  frontier, ~70+ GEIS markets) + tradable co-brands.
- KEY FIND: FTSE promotes VIETNAM frontier->Secondary Emerging effective
  Sep 21 2026 (list Aug 21) — largest scheduled Asia index event of
  H2-2026, one-off reclassification flow into a band/foreign-room
  constrained market the platform already models. Flagged as the event
  to bring a view on for a July-2026 PT interview.


## Session 7c (2026-07-22) — REAL event-flow study + execution grading

- NETWORK LIVE in sandbox -> real study, not framework-only. New
  `agents/event_flow_study.py`: summarize_event (T-mult, pre-positioning
  excess ADV-days, CAR drift, T-return, reversal frac), aggregate_study,
  grade_strategies (realized S1-S4 on actual paths, eta=0, regret vs
  ex-ante rule), close_auction_share, refined_rule + regrade. Chunked
  cached fetcher scripts/fetch_event_flow.py -> data/event_flow_study.json
  (gitignored) — 21/21 real event-names across MSCI TW/KR May SAIR + FTSE
  TW50/A50 June reviews + real 5-min close-bar shares for 3 TW names.
- FINDINGS (real): MSCI Standard deletions = the crowded prints (median
  T-mult 16x, THSR 38x; ~5 ADV-days pre-realized; -4.3% drift into T ->
  close near trough, names bounced after); FTSE deletions milder (5.5x);
  additions tiny prints (1.4x). Execution grading: 6z flat rule WRONG
  twice — MSCI dels should NOT dump the trough close (S3 best 6/8;
  deletion-reversal asymmetry rediscovered), momentum-tape adds should
  front-load (S4 best 6/7; GigaDevice S3 regret 2,773 bps; regime-
  conditional, disclosed).
- refined_rule(side, provider, drift): median regret 355 -> 0 bps
  IN-SAMPLE (MSCI sells 382->0/75% hit; FTSE buys 754->0/57%);
  frozen-rule validation scheduled for the Aug/Sep 2026 cycle.
- Tests: tests/test_event_flow_study.py (5, offline synthetic paths).
  Suite: **325 passed, 1 live deselected.**
- docs/case_studies/EVENT_FLOW_STUDY_2026Q2.md (metrics table, grading,
  the 5 trading guides, honest boundaries incl. one-quarter momentum
  regime and eta=0 semantics).


## Session 7d (2026-07-22) — positioning trajectories A->T (real data)

- New in event_flow_study: positioning_trajectory (daily excess-volume
  build A->T, build_frac curve, t_day_share, half_build_rel, FRONT/
  STEADY/BACK shape) + aggregate_trajectories (median build curve on
  normalized A->T clock). Fetcher extended with 'traj' mode (argv fix);
  20/20 real trajectories cached.
- FINDINGS: MSCI deletions = volume BACK-LOADED (78% of excess volume ON
  T; SKBio 99%, Compermed 100%) while price FRONT-LOADED (-4.3% drift) —
  arb moves price early on thin volume, trackers print at T into the
  trough, bounce follows: the S3-beats-S1 result now has its mechanism
  measured from two angles. A50 additions FRONT-LOADED everything
  (half-done 9-11 days early, T-day share 0-23%) — no print to wait for.
  TW50 intermediate. Drift-without-volume divergence flagged as the
  ex-ante tell; shape classifier promoted to standing live diagnostic
  for the next review window.
- Tests +2 (planted front/back shapes, aggregation). Suite: **327
  passed, 1 live deselected.** EVENT_FLOW_STUDY_2026Q2.md addendum.


## Session 7e (2026-07-22) — WHO limitation solved: TWSE investor-type data

- New `agents/investor_flow.py`: TWSE T86 daily per-stock institutional
  flow fetcher/parser (foreign / investment-trust / dealer nets),
  attribute_window, handoff_metrics (T-day tracker-vs-foreign opposition
  + arb pre-positioning flags). scripts/fetch_investor_flow.py cached 22
  trading days across May+June windows (1 call/day, all stocks;
  gitignored cache). Tests (4, canned payloads).
- FINDINGS: FTSE TW50 Jun-18 handoff confirmed **8/8 names** — trusts
  (0050 complex) traded index direction on T, foreigners the other side
  every time (ZhenDing +19.7M vs -18.1M; ChinaSteel -286M vs +320M);
  foreigners pre-SHORT deletions then cover into the tracker print.
  TSMC reweight trim VALIDATED: 6z simulation said -$440M; real data:
  trusts -7.27M sh (~$580M) on exactly Jun 18 — right order/day/
  direction/investor type. MSCI May-29: foreign category nets out
  internally (trackers sell vs arbs cover) -> within-category limit
  stated; fix = daily SBL overlay (same pattern, next layer). Compal
  anomaly flagged (foreign buying absorbed the deletion).
- Suite: **331 passed, 1 live deselected.** EVENT_FLOW_STUDY addendum 7e.


## Session 7f (2026-07-22) — investor-flow attribution: multi-market

- investor_flow.py -> registry (INVESTOR_FLOW_COVERAGE, 10 markets w/
  honest status) + 2 new fetchers: TPEx institutional daily (parse_tpex)
  and Korea per-stock foreign/institution via Naver mirror of KRX data
  (parse_naver_frgn; desk-feed disclosure). Tests +2 (canned payloads).
- Korea MSCI deletions (full window): 2/3 show POSITIVE foreign nets on
  the deletion print — within-foreign netting signature REPLICATES
  cross-market (property of MSCI events, not Taiwan data); SKBiopharm
  the clean tracker-sell (both categories selling the 99% back-loaded
  print).
- MPI (TPEx) finally attributed: MSCI-add effective day trust +26,014 vs
  foreign -26,033 — near share-for-share handoff, same signature as all
  8 TW50 names; Jun-1 trust -243k post-inclusion flagged.
- Caches: data/investor_flow_kr_tpex.json (gitignored). Timeout lessons:
  chunked one-name-per-call fetches; Naver needs 4 pages to reach the
  May window. Suite: **333 passed, 1 live deselected.**

## Session 7g (2026-07-22)
- Ideation: public data for event positioning beyond investor-type flows, mapped by phase (pre-announcement / A→T / T / T+) → docs/EVENT_POSITIONING_DATA_BY_PHASE.md
- Priority queue set: (1) SBL/short-balance daily fetcher (one dataset, three phases; resolves within-foreign netting), (2) TWSE indicative-auction feed into cockpit, (3) ETF units + premium/discount, (4) TDCC weekly shareholding distribution, (5) block-trade tape
- No code this session — ideation only, per question phrasing

## Session 7h (2026-07-22)
- Implemented the event-data priority queue: agents/event_data.py (TWT93U margin+SBL short balances, BFIAUU block tape, TDCC weekly distribution, indicative-auction parser, EVENT_DATA_COVERAGE registry) + 7 canned-payload tests
- scripts/fetch_event_data.py: 44 trading days (Apr 27-Jun 30) x 18 names cached to data/event_data_cache.json (gitignored) + TDCC latest week
- Graded on MSCI May SAIR + FTSE TW50 June: pre-ann short build = crowding gauge not truth signal (TaiwanCem false-flag control also +52%; MSCI deletes flat -> front-run was long-seller-driven); A->T SBL splits within-foreign flow (THSR: shorts ~15-20% of foreign selling) -> 7e limitation CLOSED; post-T unwind 9/9 deletes (-12% to -84%) incl. THSR T+2 settlement signature; 0050 paired blocks NT$50B = free ETF-creation proxy
- docs/case_studies/EVENT_DATA_USEFULNESS_2026Q2.md; suite 340 passed, 1 live deselected

## Session 7i (2026-07-22)
- Converted 7h findings into machinery: crowding_overlay (STREET-ONLY cell catches the round-2 ChinaSteel miss ex ante, +85% build), drift_composition (MSCI deletes LONG_SELLER_LED 0.00-0.19 arb-short frac), completion_clock (T+2 settlement guard; ChinaSteel still UNWINDING 0.64 vs Formosa done), crowding-adjusted frontier (Buy pick flips S3->S2 under HIGH; Sell S1 edge collapses -259->-64 bps), etf_creation_proxy, forward-archive mode for Aug-12 QIR
- Hook: index_flow.recommend_execution(crowding=...) + _event_path(reversal_frac=...); all picks frontier-derived, no hand overrides
- 8 new tests; addendum in EVENT_DATA_USEFULNESS_2026Q2.md

## Session 7j (2026-07-28)
- Project review vs two goals + detailed plan: docs/PROJECT_REVIEW_AND_PLAN_2026-07-28.md (W1 packaging, W2 run-of-day + golden basket, W3 Aug-12 pre-registration bundle, W4 live grading loop, W5 AI-on-the-desk memo + hardening); no code this session

## Session 7k (2026-07-28)
- Completed AI_ON_THE_PT_DESK.md: all 8 JD bullets — workflow, tools-we-can-create tables (built vs NEW), realistic institutional-benefit verdicts + ranked summary table; W5.13 deliverable done

## Session 7l (2026-07-28)
- Built Reg-Watch (JD bullet 5): agents/reg_watch.py — versioned rules registry (single source of truth; pt_dealer limit/auction/pre-flight now read from it, registry hash folded into rules_version/audit packs), multilingual keyword triage (zh/ja/ko/en) + LLM hook slot, human-gated propose/approve/reject with log, daily digest; views/page5_regwatch.py + app registration; scripts/fetch_reg_notices.py
- Live feeds: TWSE(479)/JPX(90)/NSE(139) notices; TPEx/HKEX/KRX/SGX/SET honest PROTOCOL; first digest caught NSE Closing Auction Session introduction + JPX limit broadenings
- 11 new tests incl. end-to-end approved-change-propagates-to-pt_dealer; suite 358 passed; docs/REG_WATCH_DESIGN.md

## Session 7m (2026-07-28)
- Reg-Watch v2 per user design review: proactive pipeline fetch->seen-diff->cluster_stories (708 notices->109 stories; dept-prefix normalization merges 6 NSE CAS circulars)->score_story (category x scope + drumbeat + basket-relevance +3, mock x0.6; explainable reasons)->flash_brief only when FLASH/NOTABLE arrives; watch mode with seen-ID baseline (758); IMPACT_NOTES per category in trading language; page renders stories w/ drill-down + basket box
- 4th live feed: SGX circulars API (Referer header); TPEx/HKEX/KRX/SET/Bursa/IDX/HOSE remain PROTOCOL (anti-bot, not availability); 6 new tests; suite 364

## Session 7n (2026-07-28)
- Started docs/INDEX_REBALANCE_TRADE_LIFECYCLE.md (living reference w/ mermaid flowcharts + project mapping per step): Step 1 order placement (broker selection -> terms -> transmission -> acknowledgment), Step 2 announcement->T window (basket prep/access, per-name liquidity risk, strategy+discretion via crowding, cross-client netting+capacity, window monitoring/amendments, client cadence, T-1 checklist)

## Session 7o (2026-07-28)
- Built pre-mandate pitch pack (lifecycle Step-1/Phase-0 analytics): agents/pitch_pack.py — expected_t_multiples (point-in-time gated), crowding_table (as_of-trimmed), risk_flags, track_record-with-misses, build/render + validate_pack self-grading loop; 6 tests
- Real example: scripts/build_pitch_pack_tw50.py -> PITCH_PACK_TW50_Jun2026.md (as-of Jun 1, validated: 6/8 changes called, 4/4 HIGH correct, misses named; crowding table showed ChinaSteel +74.5% HIGH pre-ann); PITCH_PACK_DESIGN.md w/ 6 ranked institutional AI enhancements (LLM renders, never ranks)
- Suite green

## Session 7p (2026-07-28)
- Exported reference note docs/BROKER_SELECTION_AND_PT_TRADE_TYPES.md (broker-selection factors ranked + PT desk full trade-type book ranked)

## Session 7q (2026-07-28)
- Aug-2026 QIR pre-run (scripts/run_qir_aug2026.py, chunked yfinance cache): live boundary universes TW(28)/KR(13)/JP(19) + modeled tails; QIR 1.8x hurdle -> TW adds 3443/3665/8046/4958 (2.4-3.5x GMSR), del 9910; KR no adds (Rainbow below hurdle again), del cand 011170; JP cands 285A(data-flag)/3659/4755; explicit NO-CALL for 8 markets without validated universes
- Positioning overlay: BizLink +116%/GUC +67% short build (consensus) vs NanYaPCB -26%/ZhenDing -37% (unpriced for MSCI leg); KEEP list extended (9910/3231/2379/6669); pre-registration draft docs/case_studies/QIR_AUG2026_PRERUN.md with declared grading criteria; finalize+commit before Aug 12

## Session 7r (2026-07-28)
- Completed INDEX_REBALANCE_TRADE_LIFECYCLE.md: Step 3 T-day (pre-open sweep, exception monitoring, lunch re-forecast checkpoint, close-sequence cascade w/ indicative-auction read as the days one real-time decision, post-close flash) + Step 4 post-trade (recap, TCA w/ predicted-vs-realized, settlement, completion leg via SBL clock, learning loop) — both w/ flowcharts + project mappings; closing note: the 4-step compounding loop is the agency business model

## Session 7s (2026-07-28)
- Explained NO-CALL rationale (validator standard: membership/boundary/eligibility/caps; iShares country-ETF holdings CSVs = fastest coverage route, ~1 session/market, China 2-3)
- Reference file docs/LARGEST_MSCI_FTSE_INDICES.md (provider-ranked approx caps + flow-weighted desk reading; figures labeled approximate w/ factsheet sources)

## Session 7t (2026-07-28)
- Revised LARGEST_MSCI_FTSE_INDICES.md to Asia-only + Asia-containing composites w/ AUM-stacking note + composite prediction mechanics (MSCI country-level inheritance vs FTSE regional size-banding)
- 8-market Aug QIR: market-level skew screen from 6m country-ETF returns (Indonesia -28%/China -15% deletion-skewed; TH/SG add-skewed; falsifiable, LOW-tagged, added to prerun doc) + scripts/ingest_holdings.py (iShares CSV -> validated membership + deletion watch zone; manual 10-min download converts NO-CALLs)

## Session 7u (2026-07-28)
- Compiled docs/RECENT_ASIA_REVIEW_RESULTS.md: MSCI May SAIR (TW 1 add/7 dels incl. measured 16-38x T-multiples + handoff; KR 0/3) + FTSE June (TW50 4/4 AI cohort + A50 5/5) with our grading per review and the cross-review picture (provider asymmetry, add-reliable/rank-delete-fragile, June cohort = Aug MSCI story)

## Session 7v (2026-07-28)
- User challenge caught v1 incompleteness: parsed MSCI May26 official PDF in full -> complete per-market scan ALL Asia (China 22/24, Japan 3/14, India 5/4, MY 0/6, ID 0/6, HK 0/1, PH 0/1, AU 1/0, SG/TH explicitly NONE); FTSE June: STI no changes (reserve refresh), KLCI 1 change per LSEG (preview-article 3-name list flagged as speculation), FTSE SET honestly UNVERIFIED
- RECENT_ASIA_REVIEW_RESULTS.md v2: Asia totals 32 adds/66 dels (deletion skew = prior support for Aug screen); coverage priority China+Japan; None-rows-matter lesson; raw PDF text cached

## Session 7w (2026-07-28)
- May-list cross-check caught stale membership in our OWN Aug draft: 9910 Feng Tay was deleted in Feb QIR -> DELETE call invalidated, universe+cache corrected, rerun (TW: 4 adds, no deletes); membership cross-check now mandatory finalization step
- Addendum 7w: per-name rationale + probability estimates (HIGH adds ~85%/call Laplace-shrunk from 11/12; Lotte Chem ~75%; JP candidates -> conditional WATCH pending membership verification); portfolio expectation ~4.1/5

## Session 7y (2026-07-28)
- Built agents/review_engine.py: unified 8-layer pipeline (screen -> ledger reconciliation w/ Feng Tay BLOCK gate -> rationale+Laplace probabilities w/ unverified 0.75 discount (empty alias map != verified) -> stacked-AUM flow ranges (5-9% passive-ownership heuristic) + ADV buckets -> crowding from short archive -> measured T-multiples (absent classes stated) -> risk flags -> track record) + render; 6 tests
- Live run scripts/run_full_review_aug2026.py -> AUG2026_QIR_FULL_PACK.md: TW 4 adds verified w/ crowding split (exp 3.35/4), KR 1 delete unverified 0.6, JP 3 adds unverified-discounted 0.64 each; 8 NO-CALLs; suite 380 passed

## Session 7z (2026-07-28)
- TRUE PIT replication of May-2026 TW SAIR (Apr-30 caps via historical prices, official-list grading): deletions 7/7 at PIT (4 false flags from thinner ladder); adds 0/1 — MPI ticker-mapping error (6187 vs 6223) AND the big catch: 3443/3665/8046/4958 false-flagged -> they were ALREADY MSCI members -> Aug pack Taiwan ADD calls WITHDRAWN (STALE_NONMEMBER class; correction in AUG2026_QIR_FULL_PACK); membership BASELINE (fund holdings) now mandatory pre-registration input; PIT harness repeatable (scripts/pit_may2026_taiwan.py)

## Session 8a (2026-07-28)
- Crowding refined stock-vs-flow: review_engine live read now measures drawdown-from-peak and tags EXITING (>=15% off a real peak) — early-exit signature; test added; suite green

## Session 8b (2026-07-28)
- ALL-ASIA PIT May-2026 replication (scripts/pit_may2026_asia.py, 113 tickers/8 markets, Apr-30 caps, official-list grading), iterated 3x: (1) generic tails 34%, (2) tail scaling — MY/ID regressed, reverted+disclosed, (3) real ATVR (activated dormant liquidity screen) + China expansion + Taiwan w/ corrected MPI ticker -> MAJORITY: 54/98 = 55% of ALL actual Asia changes, adds 17/17 zero false+, dels 37/56, 2 delete false-flags kept (incl. Lotte Chem = our live Aug candidate, boundary-consistent)
- Remaining 19 misses mechanism-classified: coverage-boundary depth (~11, fix = holdings baselines), FIF cuts (~4, structural limit), corporate-action (Toyota Industries, Reg-Watch radar job), CN universe (3); PIT_MAY2026_ALL_ASIA.md

## Session 8c (2026-07-28)
- Iterations 4-5 on all-Asia PIT: count-anchored universes (public constituent counts) 55->65%; A-share 20% inclusion factor on member ranking only (first attempt broke adds 8->4, corrected+recorded) -> FINAL 67/98 = 68% of ALL Asia changes, 92% of covered; adds 17/17 zero fp; dels 50/56, 11 boundary false-flags (delete precision 82%/recall 89%); remaining 6 misses fully classified (FIF 3, dual-line 2, CA 1); upgrades flow into Aug live engine

## Session 8d (2026-07-28)
- Iterations 6-8: CA rule (Toyota tender, public pre-review) -> 68/73 = 69% of ALL 98; CN composition tail no-change; buffer sweep 1-4% FLAT (null result, no tune exists, kept 2%); FIF trio confirmed structural w/ numbers (floats 0.204/0.254/0.294 above any defensible screen; AMMN misses 0.20 line by 0.0035 — line not moved); CN pair reclassified FIXABLE (yfinance assigns whole-company cap to H-line; HKEX per-line shares = queued fetcher); iteration terminated at the correct point — remaining gains are data, not rules

## Session 8e (2026-07-28)
- Flowed PIT-graded methods into review_engine (member_count anchoring, a_share_tail_mix, recent_deletions/recent_additions churn buffers — the buffers caught 18 spurious re-add/re-delete flags incl. Nestle MY re-add and CN May-adds re-delete); scripts/run_full_review_asia.py -> AUG2026_QIR_ASIA_PACK.md: 8 markets, ZERO calls under May-graded config w/ reading guide (post-SAIR QIR quiet + April-vintage scope caveat + Lotte downgraded to WATCH superseding prior pack); suite 381

## Session 8f (2026-07-28)
- docs/AI_INTEGRATED_WORKFLOW.md: (1) comprehensive framework description — deterministic 8-layer core + AI's three actual roles (analyst/iteration loop, extractor human-gated, renderer) + invariants + graded state + why the 69% ceiling is a DATA ceiling not method ceiling; (2) CLSA gap-close map — six measured limits x institutional resource x residual (vendor FIF/constituent files kill limits 1-3+6; real-time feeds = NEW capability class; desk flow/execution history/provider relationship = net-new signal, compliance-scoped); (3) target workflow — daily loop (nightly regenerate -> diff -> flash-brief-only-on-change; dealer touchpoint 5 min) + event loop T-60 -> T+5 (positioning/announcement auto-grade/inclusion-window crowding/T-day live auction reads vs expected flow/learning loop) + client surface (RAG over graded corpus, scenario turnaround, calibration-as-product) + division-of-labor table; linked from INDEX_REVIEW_ENGINE_SUMMARY.md

## Session 8g (2026-07-28)
- MULTI-MARKET CROWDING: probed 10+ regional endpoints honestly — LIVE: SFC HK weekly aggregated short positions CSV (per-stock shares, covers HK + MSCI China H-lines), JPX daily Short_Positions.xls (disclosed >=0.5% summed per stock — floor not census, deltas valid), TPEx margin/balance JSON (fills the .TWO gap, e.g. 6223); PROTOCOL: KRX (login-gated), Bursa (403), SSE/SZSE (TLS-blocked); STRUCTURAL: India (no per-stock short product), Indonesia (shorting restricted)
- event_data.py: parse_sfc_short_csv (zero-pad join to 0177.HK-style codes)/fetch_hk_short_positions, parse_jpx_short_xls/fetch_jpx_short_positions (xlrd), parse_tpex_margin/fetch_tpex_short_balance, merge_into_short_cache (one normalized TWT93U schema for every market), CROWDING_SOURCES registry; scripts/fetch_crowding_asia.py (incremental, 45s-chunk-safe; archives: HK 8 wks x 1232 names, JP 6 days x 627, TPEx 4 days x 812)
- review_engine: crowding read refactored into reusable crowding_reads() — window label now actual obs count (no fake "30d" on weekly data); flows layer confirmed already market-agnostic (cap x float x passive-ownership per row, all markets)
- run_full_review_asia.py: per-market caches (TW=TWSE+TPEx merged, JP, HK, CN=SFC H-lines) + crowding-demo appendix on boundary names -> pack regenerated: live reads incl. TaiwanCement HIGH +53% (cutline resident being shorted), Galaxy 0027 HIGH +84%, 9995.HK HIGH +45%, JP/TW EXITING tags; honest no-data lines for KR/MY/IN/ID
- +6 tests (SFC zero-pad, TPEx col-14, merge/series roundtrip, registry completeness, weekly-cadence label); suite 387

## Session 8h (2026-07-28)
- LIFECYCLE STEP 2 implementation — agreed with user that 2.2+2.3 are the AI-implementable workstreams (2.1/2.6 desk-ops, 2.4 needs multi-client order data, 2.5's surveillance half already runs); gap analysis: pieces existed (T-multiples, bands, buckets, frontier) but NO assembled per-name sheet, NO computed borrow status, NO start-date calc, NO explicit discretion function
- agents/event_window.py: liquidity_risk_sheet (2.2: ADV-days, measured T-multiple, auction-footprint % vs ~30% close share, LOCK/WATCH band risk, borrow, halt proxy, bucket); sbl_utilization (TWT93U col-12 semantics = REMAINING quota -> honest proxy bal/(bal+quota); first cut bal/quota gave 6597% — caught and fixed); start_schedule (2.3a: eff - ceil(ADV-days/cap) bdays, LATE START escalation flag); discretion_decision (2.3b rule matrix: crowded delete WORK AHEAD/uncrowded WAIT/crowded add NO pre-position/uncrowded add PRE-POSITION in envelope/EXITING flips to uncrowded logic/no envelope = MOC ONLY — every decision emits best-ex rationale citing the crowding read)
- parse_twt93u extended w/ sbl_quota; asian_markets Malaysia band corrected None->30% static; scripts/run_event_window_demo.py -> EVENT_WINDOW_PLAN_DEMO_AUG2026.md (live crowding + live TWT93U borrow: 1101/2207/2002 TIGHT 97-98% of implied SBL capacity, consistent w/ their crowding reads; demo quantities labeled hypothetical)
- lifecycle doc Step-2 mapping table updated; +5 tests (sheet flags/footprint, capacity proxy, start dates + LATE, full discretion matrix, render e2e w/ evidence count); suite 392
- AI_INTEGRATED_WORKFLOW.md extended w/ Step-2 counterpart (Parts 4-6): current framework (2.2 sheet/2.3a schedule/2.3b discretion matrix + feeders + demo cross-validation borrow-vs-crowding + 5 honest limits), 6-row CLSA gap-close map (SBL feeds, CA amendment files, OMS aggregate book for 2.4, execution history calibrates frontier, real-time crowding, actual client mandates), and the target window workflow (announcement-day auto-generation w/ dealer as reviewer, daily DIFF-not-report loop w/ discretion-flip alerts, continuous netting pass, T-1 checklist as verification run; dealer approves every discretion decision — rationale pre-written, judgment theirs)

## Session 8i (2026-07-28)
- STEP-3 T-DAY DESIGN (docs/STEP3_TDAY_DESIGN.md) after live data probes: KEY FINDING — TW close-auction volume DERIVABLE free (daily vol − Σ intraday 5m bars; verified 2330.TW Jul-24: 24.8% auction share) + HK CAS print = last 5m bar (verified 0027.HK); yfinance 5m depth 60 days COVERS June TW50/May-MSCI event days; TWSE OpenAPI free/keyless probed (MI_5MINS = 5-second market-wide order-flow accumulation); upgrade paths researched: J-Quants minute/tick = ¥5,500/mo add-on (free tier 12-wk delayed), EODHD Asian 5m/1m to Oct-2020 varies
- AI-leverage principle: T-day AI adds ZERO new judgment — compresses reaction time on pre-made decisions (3.1 machine overnight sweep, 3.2 dollar-at-risk exception engine + mechanized lunch checkpoint, 3.3 countdown + indicative-vs-expected framed recommendation, 3.4 auto flash); simulation suite designed w/ build order: auction-share study (data verified) -> T-day replay simulator (counterfactual: what would each discretion choice have cost on May names) -> violence curve + lunch backtest -> run-sheet + indicative archiver (proprietary asset from free feed, start Aug 11) -> limit-lock model
- AI_INTEGRATED_WORKFLOW.md Parts 7-9 (Step 3): current framework (zero-new-judgment principle, verified auction layer, exception machinery, designed-vs-built honesty w/ PROTOCOL cockpit line), 6-row gap-close (real-time feeds, full auction/imbalance feeds + tick warehouse for violence curve, OMS fill state, desk execution history for priors, push amendments, live cash/FX), cascade workflow hour-by-hour (dealer takes exactly two reserved decisions: lunch resize + close sizing within envelope)
- STEP-4 EXECUTION INSIGHTS (agents/execution_insights.py): tca_vs_estimate (signed cost bps, realized vs pre-trade estimate reconciliation, WITHIN/BETTER/WORSE, qty-weighted portfolio delta), discretion_counterfactual (worked choices graded vs realized drift; WAIT/MOC-ONLY graded as road-not-taken at 30%), reversal_grade (HIGH/LOW falsifiable implications only — NO-DATA excluded from hit rate, bug caught: no-data names were auto-AGREEing), update_priors (event joins library, before/after medians), render_debrief
- Demo on REAL May TW deletions (scripts/run_execution_insights_may2026.py -> EXECUTION_INSIGHTS_DEMO_MAY2026.md): pre-announcement crowding reads (archive truncated to May 12) -> all WAIT; counterfactual honestly mixed — 3/7 WAIT right (2324 avoided -682bps), 4/7 working would have helped (+29..+213bps); reversal implications 5/5 on graded names; fills/estimates labeled hypothetical; +5 tests, suite 397

## Session 8j (2026-07-28)
- UI: NEW PAGE views/page6_lifecycle.py "Rebalance Trade Lifecycle" — 4 tabs = the 4 lifecycle steps, all interactive, logic stays in agents/: Tab1 Win-the-trade (track_record table + CROWDING_SOURCES grid + live positioning read on typed tickers), Tab2 Window planner (editable basket w/ envelope column -> live 2.2 sheet + 2.3 schedule + discretion expanders w/ rationale; live crowding + live TWT93U borrow, graceful degradation), Tab3 T-day cascade (AUCTION_CUTOFFS run-sheet + interactive indicative-vs-expected calculator + live auction-share derivation on any ticker), Tab4 Post-trade (editable fills/decisions/reversal tables prefilled w/ real May paths -> TCA/counterfactual/reversal grades + priors + downloadable client debrief)
- agents/event_window.indicative_read added (THIN <0.6x -> retreat-or-flag / IN LINE / RICH >1.3x -> size up; deterministic, dealer decides); registered in app.py sidebar+dispatch; +2 tests (indicative rule matrix, page import smoke); suite 399

## Session 8k (2026-07-28)
- STEP-1 TAB REDESIGN (trader-centric, user-driven): trader picks the EVENT -> engine runs -> pre-event marketing pack generates. agents/pre_event_marketing.py: EVENTS registry (Aug QIR live / Nov SAIR live / FTSE TW50 Sep = honest reference mode — no fabricated rank list, June graded case cited), days_to countdown, boundary_watch (members nearest 0.5x floor + non-members nearest add hurdle w/ signed distance + at_risk flag — "who moves the note before announcement"), render_marketing_md (client-facing note w/ honesty rules ENFORCED IN THE ARTIFACT: zero-call stated w/ reading, probabilities per call, watch-zone labels, NO-CALL registry, misses, CONSENSUS-vs-UNPRICED line)
- page6 tab1 rewritten: event selector + T-minus metrics -> market multiselect -> live engine run (run_full_review per market from cached universes, cached in session_state) -> call-sheet expanders w/ boundary watch + crowding, measured T-day metrics row, track record, downloadable client note; zero-call banner frames the pitch ("nothing breaches + who's near the line" beats a fabricated list); headless smoke: TW+HK run clean (1101 HIGH read joined to boundary table)
- .gitignore: crowding cache + reg digest/seen-ids added (pre-push housekeeping); +4 tests (registry sanity, days_to, boundary distances/at-risk, note honesty content); suite 403

## Session 8l (2026-07-28)
- TABS 2-4 REDESIGN: the trade FLOWS through the lifecycle via session_state — Step-1 pack seeds Step-2 basket (_seed_basket_from_pack: live calls + at-risk boundary names -> draft basket, sides inferred member->Sell/nonmember->Buy, market from ticker suffix; verified headless: KR at-risk trio + 0004.HK seed correctly, TW-only returns None gracefully); Step-2 plan stored -> Step-3 watch list + Step-4 fills/decisions seeds
- Tab2 "the order is live": client-terms panel framed as THEIR mandate; EXCEPTION ROW first (MULTI-DAY count, LATE starts, footprint>30%, borrow TIGHT w/ action captions); discretion expanders labeled "approve before anything trades"; client strategy memo download (render_window_plan)
- Tab3 cockpit restructured to the day's arc: 3.1 morning check (watch list from stored plan: LOCK/TIGHT/>30% names + late-start escalation banner + run-sheet FILTERED to basket markets), 3.2 lunch checkpoint (run-rate vs plan via indicative_read logic, "resize NOW not at cutoff"), 3.3 close read + auction-share derivation moved into expander
- Tab4: seed-from-plan button (tickers/sides/decisions/worked_frac prefilled, trader overwrites realized numbers); headline grade row FIRST (realized bps, vs-estimate w/ kept-our-word/beat-it/explain-it caption, discretion hit ratio, crowding hit rate); debrief framed as "next quarter's pitch"; suite 403 green

## Session 8m (2026-07-29)
- PIT MAY-2026 REPLAY ON THE STEP-1 PAGE (user request: predict May from pre-announcement data, w/ crowding + flows + explained methodology, as the Step-1 output feeding Step 2 next): EVENTS entry engine="pit" — inputs frozen at vintage: Apr-30 caps (pit_universe: PRE-May membership; 2324.TW member=1 pre/0 post, tested), ledgers FEB-ONLY (the May list is the answer key — leak prevented), crowding = TW archive truncated at 20260512
- KEY FIX: live screen_market only implements the 0.5x delete floor -> first PIT run graded dels 1/56; the graded 69% config's deletions come from predict_msci's country-segment MIGRATION rule + CA rule -> added scripts/run_full_review_asia.pit_screen (exact harness config: seed-11 count-anchored tails, PIT_RANGE, China composition tail, CA_DELETIONS) + `screen` override param on run_full_review; UI PIT run now reproduces the graded scoreboard: adds 17/17 (0 fp), dels 50/56, 67/98 — every call carrying probability/flow-range/bucket/PIT crowding (TW dels read LOW/MED pre-announcement = UNPRICED); Toyota Industries miss explained in-UI (cap unfetchable post-delisting, CA radar's job)
- agents/pre_event_marketing: METHODOLOGY dict (prediction/crowding/flows/probabilities — "how every number is produced" expanders on the page, Feng-Tay + EXITING + 5-9% stacking language) + grade_predictions (hits/misses/false-flags per market w/ names); tab1: PIT banner (predict FIRST) + "Reveal official outcome" self-grade expander w/ named-miss captions
- +4 tests (PIT membership no-future-leak, TW 7/7 migration dels + MPI-only add, grading math, methodology completeness) + registry test extended to "pit"; suite 407

## Session 8n (2026-07-29)
- STEP-2 DAILY WINDOW REPLAY (scripts/run_window_replay_may2026.py -> WINDOW_REPLAY_MAY2026.md): basket = Step-1 PIT calls sized by the engine's own flow midpoints (USD-denominated, ratios exact); analysis re-run each of 12 trading days May 13->28 on data through that day only; DAILY DIFF product = decision-flip log: 2 flips — 2633 WAIT->WORK AHEAD May 20 (crowding crossed MED +6%/17obs), 1102 WAIT->WORK AHEAD ON T-1 ITSELF (May 28, +6%/23obs — street building the night before); T-1 full plan: all names LOCK-RISK (TW ±10%), footprints 51-475% of event-adjusted auction (total street flow, hence 16x T-day volume), checklist state + cutoff discipline
- CLOSING_AUCTIONS_ASIA.md: all-market close-mechanics reference — taxonomy (call auction / VWAP window / India transitioning), per-market table (windows, no-cancel, transparency, random ends), execution implications (rationing + band-lock capacity binds first; transparency ranking makes indicative read a TAIWAN tool; no-cancel = real deadline; HK CAS bands cap violence). KEY FIND (web-verified): SEBI replaces India's 30-min VWAP close with a 20-min CAS for F&O stocks FROM AUG 3, 2026 — our Sep-1 MSCI effective day executes into a four-week-old mechanism, no measured priors apply (Reg-Watch FLASH class; Aug-pack India risk flag)
- Answered the client-question "why not 100% MOC if passives must trade at close": self-benchmarking = zero TE by construction BUT (1) minimal TE != minimal cost — the index absorbs the impact so the cost hides in the benchmark itself; (2) auction capacity/band-locks can make the print unattainable (forced T+1 residual = actual TE risk); (3) India has no print to hide in (VWAP close); (4) TE-budget funds deliberately trade around the close to recapture measured front-run/reversal; suite 407

## Session 8o (2026-07-29)
- AUCTION DATA FOR MAY-29 MSCI EFFECTIVE DAY (user question: findable? insights?): per-name yfinance 5m intraday rolled out of 60-day retention ~ONE DAY before the study (recorded as the lesson that makes the Aug-11 archiver standing) — but TWO doors open: (a) TWSE MI_5MINS is HISTORICAL (any date, market-wide 5-second accumulated order/trade stats) — May-29 closing auction measured: 3.22M lots between 13:29:55->13:30:00 = 16.7% of day volume / 24.9% of day VALUE vs 4.8% baseline median = >5x market-wide uplift on ~8 names' flow, value>volume skew = auction concentrated in the large event names, close bid/ask imbalance 1.33; (b) June TW50 print still in per-name window
- June study found the print day EMPIRICALLY: Jun 19 (third Friday) = Dragon Boat holiday -> implementation close was JUN 18 — 3443 auction share 61.7% vs 10.2% baseline (2.2x T-mult), 3665 71.3% vs 7.7%, 8046 43.7%, 4958 54.1%; and the intended CONTROL 2330 printed 55.3% vs 30.1% — TSMC is the REWEIGHT leg on a TW50 rebalance (27%-of-turnover reweight flow made visible in public data); auction gaps -16..-192bps = per-name violence-curve points
- scripts/auction_study_2026.py (market/names/report modes, cache data/auction_study_2026.json) -> docs/case_studies/AUCTION_STUDY_2026.md incl. 5-point insights framework (measured footprint denominators, violence-curve calibration, crowding validation big-auction-small-gap test, completion inference, compounding archive)

## Session 8p (2026-07-29)
- MAY-29 PER-NAME DATA SOURCE HUNT (user: double-check yfinance, explore alternatives): yfinance CONFIRMED dead across all sub-daily intervals (1m=30d wall, 5m/15m/30m=60d wall; 60m survives 730d but its 13:00 bar merges the last half-hour with the auction — cannot isolate); FinMind probed — TaiwanStockPriceTick/TaiwanStockKBar EXIST but are sponsor-tier even registered (HTTP 400 "update your user level"); full v4 dataset enum extracted (132 sets)
- NEW FREE DOOR FOUND: TWSE MI_5MINS_INDEX (historical, 5-second TAIEX) -> the closing auction's PRICE move at market level: MSCI effective day 13:29:55->13:30 = **-40.9 bps in one print** vs ~11 bps abs baseline median (sell-skewed as 66-del SAIR + reweight sells imply) — added "gaps" mode to auction_study_2026.py, doc regenerated w/ market-level violence table
- Source landscape recorded: per-name May-29 minute data requires either Fugle marketdata API (free registration key — best path, official TW broker API w/ historical candles) or FinMind sponsor tier or EODHD paid; desk tick warehouse supersedes all; the Aug-11 indicative/intraday archiver remains the permanent fix

## Session 8q (2026-07-29)
- ALL-MARKET MAY-29 PER-NAME HUNT (user: not just Taiwan — all review stocks): Eastmoney push2his probed — CN+HK coverage but flat ~31-trading-day intraday wall (earliest Jun 15, all klt) -> May 29 out; Tencent ifzq.gtimg.cn DNS-blocked from sandbox; **BAOSTOCK = THE FIND**: free, YEARS of A-share 5-min history — May 29 full 48-bar days delivered, 15:00 bar = the 14:57-15:00 closing call directly
- CN per-name auction study run (13 A-line May-review names + control, 10 days each, "cn" mode chunked): TEXTBOOK VIOLENCE CURVE — adds' auction gaps median +194bps / deletes' −146bps (print pays the imbalance in the side's direction), auction shares 4.4-37.3% event vs 1.2-3.9% baseline, T-mults 0.8-2.1x; control 600000 shows 10.9% event-day share = the reweight-flow effect (TSMC lesson repeating in CN); H-lines honestly out (no free HK intraday reaches May 29)
- Final May-29 per-market data map: TW market-wide SOLVED (official 5s: 25% of value, −41bps index gap) / per-name = Fugle-key or paid; CN-A per-name SOLVED (baostock); HK = account/paid only; JP = J-Quants ¥5,500 add-on; KR = account-gated; IN = no print existed (VWAP close era); MY/ID = none found; suite 407

## Session 8r (2026-07-29)
- TW MAY-29 AUCTION DEEP DIVE (scripts/tw_auction_deep_dive.py -> TW_AUCTION_DEEP_DIVE_MAY29.md, full 5s MI_5MINS series, event vs 3 baselines): three NEW playbook rules from real event data —
  (1) LUNCH-CHECKPOINT CORRECTION TERM: event day printed only 0.94x baseline value by noon yet closed 1.23x (market-wide) — auction concentration makes the morning tape look deceptively normal; the lunch read must compare vs `mult x (1 − auction share)` or every event day false-alarms 'thin' (raw-run-rate rule would have proposed a WRONG resize on May 29)
  (2) ORDER RETENTION: data-semantics discovery recorded honestly — accumulated order volume FALLS 13:25->13:30 (counter nets cancels/purges; first 'arrival' interpretation was wrong, corrected in-doc); the decline IS the signal: baselines withdraw ~24% of the resting book before the match, event day only ~14% — MOC obligation is committed flow, so the REBALANCE-day indicative is MORE trustworthy than normal (strengthens the 3.3 close-read rule)
  (3) IMBALANCE DELTAS NOT LEVELS: gross bid/ask ratio bid-heavy every day (retail clutter) — but the event day's ratio DROPS into the close while baselines hold: direction of the walk carried the −41bps sell-side signal
- volume-curve table (12:00/13:00/13:24 % of final: event 58.9/68.9/75.1 vs baseline ~76/88/95); all three rules parameterize the replay simulator + Sep-1 run-sheet; suite 407

## Session 8s (2026-07-29)
- CAPSTONE: full lifecycle Steps 1-4 as ONE CHAIN on May-2026 TW (scripts/run_lifecycle_e2e_may2026_tw.py -> LIFECYCLE_E2E_MAY2026_TW.md; [PIT]/[REALIZED] labels throughout): S1 prediction 1/1 adds + 7/7 dels graded; S2 daily loop 12 days -> T-1 plan; S3 realized (24.9%-of-value print, −41bps, 14% withdrawal, med t_mult 13.3x); S4 discretion 5/7 + reversal 5/5 + priors updated
- HEADLINE FINDING: the daily loop's 2 flips (2633 May-20, 1102 T-1) both graded CORRECT work-aheads -> discretion 5/7 vs 3/7 static all-WAIT — first MEASURED evidence the daily diff adds money, not comfort; remaining 2 misses = drift-direction (crowding said UNPRICED correctly; drift leg needs its own signal = replay simulator's assignment)
- Review sections in-doc: 5 honest weaknesses; APAC-per-market institutional-fix table (methods transfer unchanged — CN-A baostock study already proved the transfer); RETROSPECTIVE FRAMEWORK w/ probed depths: MI_5MINS serves 2012+ (VERIFIED: 2012/2018/2023 all OK) -> decade of TW market-wide auction studies; TWT93U 2015+ VERIFIED -> ~20 review cycles of crowding rebuildable; JPX 2013+/SFC 2012+ (regime starts); baostock 2026 verified/2016+2019 empty then throttled (depth TBD); outcomes public 10+y; T-multiple library expandable to HUNDREDS of events on daily data (15-20y); prediction replication full-fidelity ~2-3y / degraded-graded ~5y (share-drift + no historical ff); per-name intraday NOT retrospective — forward archive standing; suite 407

## Session 8t (2026-07-29)
- TWSE HISTORICAL BACKFILL LAYER (scripts/backfill_tw_history.py — the yfinance replacement for TW, official + years deep): probed TWT38U foreign per-stock net flows 2015+ OK, MI_INDEX ALLBUT0999 all-stock daily quotes (1191 names/call) 2023+ OK; incremental per-type caches (quotes/shorts/foreign) in data/tw_history/, chunk-safe; backfilled Feb-2026 window (quotes 32d, shorts 22d, foreign 6d — CNY Feb 12-22 closure explains the gaps)
- FEB-2026 QIR RETRO DEMO (REPRO_FEB2026_TW.md, zero yfinance): implementation print EMPIRICALLY identified as FEB 26 (Feb 27 = holiday, absent from tape — third date caught by data: Jun 18, May 29 CN, Feb 26); all 4 TW deletes printed 21-26x T-multiples from official quotes; pre-announcement crowding readable 5+ months back (9910 Feng Tay HIGH +33% — the street saw it; 1476/8464 LOW = unpriced); ALIAS VERIFICATION BY EVENT PRINT: "HONPRECISION"->2354 candidate REJECTED by its own 0.9x non-print (reusable technique); foreign-net hypothesis CONTRADICTED and recorded — 2105 +41.9M shares foreign BUYING into the deletion print (the column reveals who takes the OTHER side, not a sell signature)
- Unlocks: retrospective Step-1 crowding/flow + Step-2/3 analytics on official data for ~40 past reviews (2015+); suite 407

## Session 8u (2026-07-29)
- NEW LIVING REFERENCE docs/TAIWAN_MARKET_ANALYSIS.md (user request: single home for all TW-specific project info, sections added as work lands): Section 1 = the 2015-lookback background STORY (probe table per pillar w/ binding-layer logic; regulatory backstory — mid-2010s short-sale/SBL liberalization means pre-2015 positioning is UNRECORDED in consumable form, not merely unfetched; verified-at-not-proven-first qualification; partial-stack depths 2005+/2012+; what 2015 buys = ~40 cycles, priors from n=8 to n=hundreds); stub sections 2-5 (data infra, mechanics, case-study index, planned retro sweep) w/ pointers

## Session 8v (2026-07-29)
- BACKTEST FIRST SLICE (user: iterate 2015->now until 100%/plateau; honest scope: keys + universe breadth gate depth — this slice = 4 MSCI TW events 2025-26; BACKTEST_TW_2025_2026.md): answer keys RECONSTRUCTED via event-print detector, iterated on KNOWN keys — it1 recall 4/4+7/7 w/ 6 false+; it2 (t>=12) REJECTED OUT-OF-SAMPLE (3 true May dels at 8.4-11.9x — recorded as the in-sample-tune lesson); it3 (value>=NT$4B: Standard names print big + limit-lock SUSPECT tag + ETF exclusion) -> Feb exactly the 4 trues, May 7/7 preserved; reconstructed 2025 keys: quiet reviews (Aug {2395}, Nov {8033 del, 7769 fast-entry, 2316 suspect})
- Prediction it4 = REVIEW-CADENCE RULE (documented MSCI cadence, not a knob): migration sweep = SAIR-only, QIR = 0.5x floor + screens -> Aug-25 QIR 10 false dels -> 0 (Feb-26 cross-check: real QIR dels all sub-floor, Feng Tay 0.38x); HAZARD FINDING reframes deletion output: Nov-25 SAIR 9 flags = EARLY not wrong — 6/9 deleted at the NEXT SAIR, 3/9 = the persistent cutline trio (1101/1326/2207, same names every graded run flags) -> deletion calls formally hazard-ranked w/ measured ~2/3-per-SAIR conversion; plateau declared honestly (remaining misses = universe breadth 2395/8033, fast-entry class 7769, key depth)
- docs/PREDICTION_LOGIC_LAYERS.md (user request: all layers displayed): L0 count-anchored universe -> L1 screens/inclusion-factor scope -> L2 GMSR ladder -> L3 thresholds -> L4 review-cadence (NEW) -> L5 churn buffers -> L6 CA/fast-entry radar -> L7 Feng-Tay verification gate -> L8 Laplace probabilities -> L9 deletion-as-hazard (NEW) — each with rule/input/ORIGIN-mistake/failure-mode; closing frame: "the engine is its own error history, compiled"; TAIWAN doc section 5 updated; suite 407

## Session 8w (2026-07-29)
- ANSWER-KEY ARCHAEOLOGY — MSCI SOLVED TO 2015 (and beyond): Wayback CDX index used as a FILENAME-DISCOVERY tool against MSCI's still-live archives — (1) app2.msci.com/eqb/pressreleases/archive/MSCI_{season}{YY}_QIRPR.pdf serves 2005-2025 (my SAIRPR guess was the error; May/Nov are QIRPR-named too, May18 the lone exception); (2) THE MOTHERLODE: msci.com/eqb/gimi/stdindex/MSCI_{season}{YY}_STPublicList.pdf = FULL Standard-index per-country change lists, CDX-visible back to 2003
- Downloaded ALL 44 STPublicLists + ALL 44 QIRPRs 2015-2025 (100% hit rate, data/msci_archive/, scripts/fetch_msci_archive.py fetch/lists/extract/check modes); **44/44 parse clean with the EXISTING ledger parser** — 123 TW changes keyed (56 adds/67 dels; 2015's 17-del year visible), spot-check sane (Nov-16: Micro-Star add/Simplo del); every other country's sections came free — the ~40-cycle backtest now has official keys for ALL MSCI markets
- FTSE path identified not collected: wayback snapshots of research.ftserussell.com Taiwan Constituents.jsp -> membership by snapshot diffs (multi-session job); TAIWAN doc section 5 updated — remaining 2015 gates are universe breadth + share-drift caps, NOT keys
- FTSE evaluation deepened (same session, user follow-up): probed TIP /news (NUXT SSR payload = CSS only, API hidden in JS bundle -> client-side wall), primary constituents.jsp URL has ZERO wayback snapshots (crawlers archive shells not data), CDX domain queries intermittently time out; verdict = NOT sandbox-automatable; ranked paths in TAIWAN doc: (1) Claude-in-Chrome browser session on TIP/ftserussell news archives (<1hr, official text), (2) TWSE monthly publications (manual, complete), (3) factsheet diffs INSUFFICIENT (top-10 only), (4) print-detection REJECTED (FTSE 2-5x in noise); priority note: FTSE validates the rank game but MSCI's 44 keyed events carry the retro program
- TAIWAN doc §4b added: MSCI-vs-FTSE importance note (MSCI >> TW50 > GEIS w/ the measured evidence: 16x/38x vs 2-5x prints, 25%-of-market May print, −41bps; TW50's three claims: 0050 scale, TSMC 30%-cap reweight leg, MSCI-preview effect; routing principle); docs/TASK_FTSE_LIST_COLLECTION.md created — self-contained handoff brief for a NEW chat (goal schema data/ftse_tw50_changes.json ~46 quarters, ranked browser-first method TIP->TWSE news->ftserussell + print cross-validation, repo honesty conventions binding, definition-of-done checklist, suggested opening prompt)

## Session 8x (2026-07-29)
- FTSE TW50 KEYS SOLVED IN-SESSION (user connected Claude-in-Chrome): browser rendered TIP's client-side news archive (year filter + 全部 -> ALL ~300 titles one page; TWSE press-release search ruled out first — ETF marketing only); KEY DISCOVERY: detail pages /news/{id} are numeric AND SSR -> sandbox took over: scripts/fetch_tip_news.py (threaded enumerate 1-460, index titles/dates, keep 41 TWSE-FTSE review pages) + scripts/build_ftse_tw50_keys.py (parse 納入/剔除/候補/生效)
- Parser iterated on data checks: (1) preamble-enumeration trap (first regex captured "、" — select occurrence w/ content; empty-quarters 2020-23 implausibility was the tell), (2) spaced "臺灣 50 指數" variant (2020-03) -> 41/41 parse
- RESULT: data/ftse_tw50_changes.json — 41 events, **100 TW50 adds+dels 2016-11->2026-06** w/ reserve lists + sources; 7 pre-TIP quarters NOT FOUND stated (2015-2016Q3, TWSE-era manual path); VALIDATED: 2026-06 quartet exact vs measured prints, official text confirms Jun-18 holiday-shifted eff (the data-identified date), deletion side revealed (2002/2207 cutline residents were FTSE June deletions!), shipping-boom 2021-06 cohort + 2023-09 reversal + Feng Tay 2019-2024 arc + 6919 one-review churn all read true; FTSE_TW50_KEYS.md; TAIWAN doc §5 FTSE marked SOLVED; suite 407
- 2015 FTSE follow-up (user: why 2016+, can we get 2015?): answer = TIP founded Jan-2016, archive starts at its birth; FOUR recovery routes probed and killed same session: TWSE press archive doesn't carry the class, old ftse.com Constituents.jsp 302-dead from Feb-2015 (wayback snapshots bracket every 2015 quarter but capture the tombstone), Yuanta 0050 SPA api/Composition = 1 useless wrapped snapshot, TWSE monthly-journal page = JS shell; viable browser-led paths recorded (證交資料月刊 PDFs, 2015 press coverage); impact framed: MSCI 2015 keys exist (TW's 17-del year), FTSE-2015 only completes the rank series

## Session 8y (2026-07-29)
- APAC DATA-AVAILABILITY RANKING vs Taiwan (docs/APAC_DATA_AVAILABILITY.md; user goal: find Taiwan-like markets): 6-pillar scoring (daily quotes/shorts/auction archive/flow attribution/intraday history/access friction), every LIVE-DEAD claim probe-referenced; new probes: NSE bhavcopy 2015 zip SERVES (official daily archives decade+), HKEX CCASS per-participant daily holdings page REACHABLE (custody-level attribution — HK's TDCC-equivalent, unique study: which brokers' books absorbed the flow)
- RANKING: TW 10 (only market w/ all pillars keyless+decade-deep; weak only on per-name intraday) > CN-A 8 (BEATS TW on per-name intraday via baostock-years; crowding pillar thin) > JP 7.5 (daily disclosed shorts 2013+; J-Quants cheap) > HK 7 (weekly SFC + CCASS X-ray) > AU 6 (ASIC daily shorts open CSV, years) > IN 6 (bhavcopy+delivery deep; positioning pillar structurally absent; CAS arrives Aug-3) > KR 5.5-gated (Asia's best flow attribution behind one free registration -> Taiwan-tier = highest-ROI action) > TH 4 (NVDR daily = hidden gem) > SG 3.5 > MY 3 > ID 2.5 > VN 2; program order TW->CN-A->JP->HK, KR on key, IN post-CAS

## Session 8z (2026-07-29)
- SIMULATABLE PITCH FACTORS BUILT (user: implement factors 2/5/6/7/8/9-class analytics on historical data; trust/relationship factors excluded as unsimulatable):
- FACTOR 6 — scripts/reserve_churn_stats.py on the decade of official TW50 keys (41 reviews, 190 reserve-slots, 35 fully-windowed adds/dels): **reserve-list conversion 18% within 1 review / 27% within 2; new adds DELETED again within 4 reviews 28.6%** (the 6919 class — flow-reversal risk finally priced); deletions sticky (8.6% re-added within 4); TW50_RESERVE_CHURN_STATS.md + data/tw50_stats.json
- INSTITUTIONAL-ACCESS CODA added to APAC_DATA_AVAILABILITY.md + mirrored as TAIWAN doc §4c (user: can CLSA access replicate the TW pillars elsewhere?): shorts pillar SOLVED+UPGRADED everywhere via securities-finance data (daily borrow qty/utilization/FEES — the crowding price signal free data never had); auction pillar SOLVED+UPGRADED via tick history (per-name, decades); foreign-flow pillar STRUCTURAL — vendor products can't sell what markets don't record (exists only under ID regimes KR/TW, NVDR TH, Connect CN, CCASS HK; JP/SG/AU weekly aggregates at best); ownership brackets partial (CCASS genuine, fund-holdings proxy elsewhere); verdict: full five-layer replication in KR/HK/CN, near-complete JP (flow pillar degraded, stated), everywhere else positioning runs on borrow fees instead of flow attribution
- FACTOR 5 — agents/violence_curve.py on the 17 measured per-name auction points: **v1 IS A NULL RESULT, stated and test-pinned (R2~0.00)** — auction share does NOT predict gap magnitude; what survives: unconditional prior |gap| ~ 125±85bps + the CROWDING-VIOLENCE link (all four CONSENSUS TW adds printed AT/BELOW last price despite 44-71% shares — pre-positioned supply sells into the print — vs CN +194/+239bps at 5-19% shares; SUPPORTED not proven, CN crowding unmeasured at vintage; Sep-1 = designed OOS test); VIOLENCE_CURVE_V1.md; +2 tests (fit/band math, real-points null pinned); suite 409

## Session 9a (2026-07-29)
- STEP-2 WINDOW STUDY ON THE KEYED DECADE (user: PIT-strict day-by-day factor analysis + execution-quality comparison + lessons): backfill_tw_history THREADED (8 workers); 6 TW50 events backfilled (2021-06/2021-09/2023-09/2024-03/2025-12/2026-03) x 3 official sources -> quotes 190/shorts 166/foreign 147 dates; scripts/window_study.py: 38 event-names, 372 name-days, every factor uses data <= its own day
- DAY TRACKS (median, rk to print): ADDS drift builds to +329bps by T, volume QUIET until T (1.96x), short build ACCELERATES into T (+3.6->+9.7% = arbs shorting into the run), foreign −0.66xADV ON the print (pre-positioned supply selling — violence-null confirmed independently); DELETES fall to −136 mid-window then RECOVER into T (covering bounce pre-print), T t_mult 5.5x (= the FTSE ~5x prior, reconfirmed), foreign +2.84xADV buying the deletion print (the contrarian bid, = Feb-2026 2105 finding)
- COUNTERFACTUALS vs T-close (median bps, closes-based, impact-free upper bounds stated): ADDS all-day-1 **−630**, 30/70 split −86, late5 −71 (early wins); DELETES ALL working strategies LOSE (+43..+88) -> MOC default right for dels, expensive for adds — THE SIDE ASYMMETRY is the headline
- **A+3 CONDITIONING (PIT-legal day-3 signal): early-hot adds linear −274 vs early-cold +282; dels −35/−55 vs +187/+154 — window momentum persists; one conditional rule dominates every unconditional strategy**; supplies the missing drift leg the May-2026 discretion grading identified (L3); lessons L1-L5 incl. honest caveats (close-fills, n=38, FTSE-class not MSCI, no borrow costs) + playbook wiring (A+3 checkpoint joins the daily loop); WINDOW_STUDY_2021_2026.md; suite 409

## Session 9b (2026-07-29)
- INTERPRETABILITY + VISUALIZATION for the window study (user request): §0 METRIC DEFINITIONS added to the doc via the script (exact formula/inputs/units/edge-handling per metric: P0 pre-close uncontaminated because ann lands post-close, V0 = median ≤5-session baseline vol, drift/fav_drift sign convention, short_chg = %Δ total short interest since A-day, foreign in xADV units, counterfactual cost sign convention w/ MOC≡0 + impact-free-upper-bound statement, early_hot flagged as IN-SAMPLE split)
- Visualization both ways: (a) matplotlib PNGs (drift/t_mult/short/foreign tracks, adds-vs-dels, vline at print) -> docs/figs/, embedded in the case study; (b) INTERACTIVE plotly in page6 Step-2 tab (_window_study_charts expander): metric selector + single-event overlay (individual name trajectories at 45% opacity over the median tracks), PIT caption w/ headline numbers; +1 test (panel/tracks pipeline); suite 410

## Session 9i continued-26 (2026-08-04) — JP STEP-1 UPGRADE (no new source needed)
- USER ASK (JP historical data w/o IBKR): **KEY INSIGHT — the prediction engine runs on DAILIES and we already hold them** (decade harvest: 182 JP name-windows, yfinance daily 2015-2025, 29 seasons); IB's ¥3,000 gates INTRADAY only (deferred stands); J-Quants free tier documented as the official upgrade path (signup)
- scripts/jp_step1_upgrade.py: **166/181 JP aliases PRINT-VERIFIED (92%)**, 6 print-weak, 9 no-material-print (survivorship stated: delisted names absent from yfinance); **FIRST JP-MEASURED CLASS PRIORS: Sell median 10.0x/max 24.5x (n=113), Buy 7.7x/21.3x (n=53)** — lighter than TW's 16x, consistent w/ JP's bigger tapes
- HONESTY GAP CLOSED: the Asia pack previously showed TW's TW-measured 16x under EVERY market's history line — Japan section now shows JP-measured priors (runner wires jp_event_priors.json for the Japan result); pack regenerated
- +1 test (verification rate ≥85%, prior bounds, survivorship note, pack wiring); suite 431 green (the yfinance live-skip test passed this run)

## Session 9i continued-25 (2026-08-04) — DESK BRIEF PAGE (the front door, Step 1 built)
- Anticipation-study alignment confirmed w/ user: CN starts 2018-05-31 (inclusion day); **pre-run refinement locked: May18/May19/Nov19 = INCLUSION-TRANCHE flagged** (adds pre-announced up to a year — announcement wasn't the info event; H11b reported w/ and w/o, w/o = primary; H11a dels unaffected — 14 delete event-clusters ≥ the 6 minimum); training-set sizing rationale delivered (events are the unit; ~35 clusters right-sized; extend SIDEWAYS (CN QIRs/KR/IN) not backward)
- **views/page7_desk_brief.py — "⭐ Index Rebalance Desk Brief", FIRST in the sidebar**: 30-second orientation for time-poor CLSA traders — hero chips (22/22 adds PIT · 24 events @5m · 429 tests · public+own-IB data), LIVE Aug-2026 banner w/ T-countdowns, 4-step lifecycle strip (Step 1 BUILT, 2-4 pointed to the deep tool), Step-1 live section: freshness check on visit, the validated-zero narrative + shortlist table (p / flow-if-converts / crowding-now / must-start-by, BELOW-FLOOR honesty caption), funnel + T-day-cards expanders REUSED from page6, methodology-in-one-breath + why-trust cards; cached-JSON rendering only (instant load)
- app.py wired (new radio entry + dispatch); +page7 import/wiring asserts in the page test; suite 429+1skip

## Session 9i continued-24 (2026-08-04) — ANTICIPATION STUDY STAGED (registry v3 + APAC harvest)
- **REGISTRY V3 LOCKED** (before any evaluation): does the tape front-run the ANNOUNCEMENT? **Confounder stated up front: add-side drift is mechanical (price causes the cap-crossing) — clean tests are abnormal VOLUME (H11a DELETES = the decisive cell: ~45% are coverage-arithmetic w/ no mechanical tape cause; H11b adds guarded) + close-hour share shift (H12)**; within-name baseline design (ann−10..−1 vs ann−30..−11); limitation stated: measures anticipation EXISTENCE not incremental power (no historical PIT universes for cross-name controls); Aug-11 announcement = standing OOS
- HARVEST STAGED: data/apac_harvest_manifest.json — **407 windows (CN 390: SAIRs 2018+ via Connect codes SEHKNTL/SEHKSZSE; HK 17 + 36 CN H-lines via SEHK), window eff−45d→eff+7d** (pre-ann baseline + reversal week); ib_harvest gains fetch_apac (per-market end-times, resumable/atomic, ~45min) + sanity_apac (bar-sums vs decade_windows official dailies — per-market unit/auction calibration awaits, incl. the adjusted-fractional-volume caveat)
- Bill to run: fetch_apac → sanity_apac → paste outputs; analysis script (H11/H12 evaluation w/ the verdict machinery) builds once data lands

## Session 9i continued-23 (2026-08-04) — APAC EXPANSION PROBES (Bill-guided)
- probe_apac built (one liquid benchmark per market, IB exchange codes); Bill ran rounds: **HK/CN-A(NB)/SG/AU/IN/KR ALL serve 5m bars to 2015+ (probed 2023/2021/2018/2015 print days — no floor found!)**; Taiwan is the newcomer exception; **Korea unlocked (KRX code — my "KSE" was a wrong address; fee-waived Korea Equities Bundle covers KRX+NXT)**; Japan DEFERRED by user (JPY 3,000/mo TSE L1 — line commented w/ re-add note); subscription advice given (skip TSE-L2/OSE/Japannext; DON'T buy SSE/SZSE L1 — Connect route already works)
- **TW FLOOR FINAL**: probe_tw_deep (TRADES/ADJUSTED_LAST/MIDPOINT/BID_ASK @2018) — all pre-coverage; no data type reaches deeper; **ib_async hang fixed structurally: RequestTimeout=30 set at connect** (ADJUSTED_LAST farm-silence hung the default-infinite wait)
- Expansion caveats logged in HF doc: probe 06:00-UTC clipping (artifact), ADJUSTED fractional volumes on old bars (per-market calibration required), KR volume thin pre-2018, SGX Hari-Raya calendar trap #7, IN zero-vol observations; next: HK/CN-A harvests on the EXISTING bridges → then KR (182 changes) + IN (195) bridges
- Suite unchanged 429+1skip

## Session 9i continued-22 (2026-08-04) — INTEGRATION AUDIT + WIRING (user challenge: standalone or integrated?)
- HONEST AUDIT: Step-1 additions were INTEGRATED from the start (shortlist/decade-consistency/hazard-velocity inside review_engine; card priors inside tday_cards); **Steps 2-4 additions were STANDALONE modules — four gaps found and closed**:
- (1) **A+3 demotion now IN CODE**: time_machine.asof_step2 gate relabeled "descriptive: A+3 [H3 REJECTED — context only]" w/ lab citation (was doc-only demotion);
- (2) **playbook → Tab-3 cockpit**: _playbook_expander (side×tape×volume selector → cell metrics PM/gap/P(fav)/T+1, DATA-THIN warning honored);
- (3) **post_event ↔ execution_insights relationship DECLARED in code** (post_event = NO-FILLS path/market anatomy; execution_insights = WITH-FILLS grading; they merge into one debrief) + _post_event_expander in Tab-4 (strip table w/ winner, gap-in-band incl. the 1402 miss, T+3 reversal);
- (4) **window-intraday priors → pre_announcement advisory** (vol-through-window 1.4→2.9x, H9b +3.6 share pts, H10 no-PM-bias line); packs regenerated
- Suite 429+1skip

## Session 9i continued-21 (2026-08-04) — STEP-4 POST-EVENT PACK (NO OWN FILLS NEEDED)
- **agents/post_event.py — the morning-after product without executions**: (1) BENCHMARK STRIP per name (official close, EXACT day VWAP value/vol, cont VWAP 5m, TWAP est, last cont, gap, share) — the ruler clients self-grade their fills against; (2) STRATEGY LEADERBOARD for THIS event (MOC/VWAP_T/LINEAR fav-bps + winner per name); (3) ESTIMATE LEDGER = our forecasts graded as our executions (gap-in-quoted-band?, realized share vs class prior + surprise, realized t-mult); (4) REVERSAL TRACKER T+1..T+5 from IB post-T bars (official fallback); (5) CROWDING RESOLUTION (short path through the print)
- **May-26 demo pack (docs/case_studies/POST_EVENT_PACK_MAY2026.md)**: strips complete 7/7; winners split (LINEAR x3 / MOC x3 / VWAP_T x1 — event-level heterogeneity real); **1402 gap +281 OUTSIDE the quoted band → estimate miss SHIPPED** (in-band 6/7); realized t-mults 8.3-42.8x vs 16x prior; **reversal paths: the deletes snapped back HARD post-print (2324 +2,820bps by T+3, 2474 +2,630, 1402 +740) while 1102's clean 91% print barely reversed (−59→+118)** — Harris-Gurel at name level, completion-leg sizing now per-name-conditioned
- +1 test (strips complete, winner enum, 1402 miss pinned, >1,000bps snap-back real); suite 429+1skip

## Session 9i continued-20 (2026-08-04) — T-DAY SITUATIONS PLAYBOOK
- **scripts/tday_playbook.py: "you are here → history says"** — 96 T-day observations (24 events, 5m+auction bars) conditioned on MIDDAY OBSERVABLES (side × AM tape WITH/AGAINST-flow × AM volume HEAVY≥1.5x-own-baseline/NORMAL) with post-noon outcomes (PM drift, auction gap fav-signed, p_gap_fav, realized share, **T+1 reversal from the eff+ bars**); 7/8 cells OK (thin-cell honesty: <8 days or <4 events = DATA-THIN, no recommendation)
- **THE SYSTEMATIC FINDING (pinned): the closing print typically lands AGAINST the obligated side — p_gap_fav 0.08-0.38 across all OK cells, median toll 15-55bps** = the measured cost of demanding immediacy at the bell (Dimensional's reconstitution result reproduced at 5m scale); the limit-lock favors-obligated cases (6919/2344) are TAILS not the rule — prior narrative corrected
- Cell highlights: Sell/AGAINST/NORMAL = the most punitive tape (gap −55, p 0.08, T+1 CONTINUES −108 — quiet strength in a delete is the worst sell tape; no comeback); Sell/WITH/HEAVY = the fairest print (p 0.38); **Buy/AGAINST/NORMAL = the strongest completion-leg signal (T+1 reversal +255 — soft-add prints overshoot and snap back; buy residuals patiently on T+1)**; T+1 behavior is CELL-DEPENDENT → completion plans conditioned on the same midday observables, not a blanket reversal prior
- Honesty note recorded: first-draft reactions (written pre-numbers) disagreed with the measured table in two cells → rewritten DATA-GROUNDED with numbers cited per cell
- +1 test (scale, thin-cell honesty, p_gap_fav<0.5 in every OK cell pinned, doc structure); suite 428+1skip

## Session 9i continued-19 (2026-08-04) — WINDOW-PERIOD ENGINE UPGRADE (REGISTRY V2)
- COVERAGE AUDIT (ann→eff, post-2023-05 floor): **96/99 name-windows FULLY covered at 5m** — the 8 flags decomposed into CNY closures (calendar trap x6: Feb windows span Chinese New Year; audit made holiday-aware) + the 3 known TPEx-floor names
- REGISTRY V2 LOCKED FIRST (appended to VARIABLE_LAB_REGISTRY before evaluation): H9 window-day auction share rises toward T for deletes (≥0.05 share, wr≥65%, LOO); H10 PM-drift concentration grows toward T (≥50bps); H6 re-registered w/ t_mult-unit threshold (the v1 criteria gap)
- **scripts/window_intraday_study.py: 1,083 name-days × 24 events × 96 name-windows** — per-day DIRECT auction share, PM vol share, AM/PM fav split, day-vol-x-baseline
- **VERDICTS: H9 ADOPT (effect +0.169 share, winrate 1.00, LOO-stable) — but the honest DECOMPOSITION shows the locked late-bucket includes T and the print dominates: excluding T the pre-T migration is +0.036 share at 0.86 winrate → BELOW the locked threshold → registered as H9b for v3 (criteria never move post-hoc)**; H10 NULL-PINNED (−6bps, wr 0.54 — PM drift does NOT concentrate toward T)
- Descriptive gold: **MSCI delete window-day volumes run 1.4x baseline early → 2.9x late (FTSE ~1.0x throughout)** — the MSCI obligation visibly trades THROUGH the window (coheres w/ H1 rejection + May-26 working-wins)
- +1 test (panel scale, H9 ADOPT wr≥0.9, H10 NULL, decomposition doc enforced); suite 427+1skip

## Session 9i continued-18 (2026-08-04) — STEP-1 UPGRADE + FRESH AUG PREDICTION + EXPLAINER
- HONEST SCOPE STATED: intraday data upgrades EXECUTION more than PREDICTION (Step-1 = caps/floats = daily questions); the real Step-1 gains delivered: **(a) ~44 bridge aliases PRINT-VERIFIED from IB auction bars (shares 0.5-0.93 on their event days; Feb-25 verified at T=Feb-27 — "data not calendar" x5: Feb-28 is ALWAYS a TW holiday, walk-back added to studies base_table; Nov-24 3653/2344 shares 0.14-0.17 tagged PRINT-WEAK not rejected — high-ADV tape swallows flow, the CN-materiality mechanism)**; msci_tw_events.json now carries print_verified shares per season; (b) cards' auction prior upgraded n=4 → **class-conditional DIRECT priors (MSCI/Sell med 60% n=20; per-side lookup)**; (c) fresh-caps rerun
- DATA WISHLIST (for better prediction, documented): historical shares outstanding (TWSE monthly archives → 2018+ decade PIT grading), provider FIF/float vintages (institutional — kills Indonesia/JP-float miss classes), listing calendars (L6 fast-entry), holdings baselines; IB adds nothing further for PREDICTION (prices only)
- **FRESH AUG-2026 PREDICTION (caps repriced to Aug-4, 125/125; crowding as-of Aug-3 via freshness layer)**: TW 0 calls (visible margin), 10-candidate shortlist regenerated (1101 p≈0.149 leading delete, BELOW-FLOOR 0.27-0.30 declared), 2 crowd alerts (1326 building, 2633 covering), cards re-rendered w/ direct priors + "None-None" render fix
- **EXPLAINER for PT traders (docs/EXPLAINER_INDEX_REVIEW_FOR_TRADERS.md)**: Part 1 selection mechanics in plain language (85%-coverage ladder = the height line; GMSR = the magic line; two doors 1.8x/0.5x w/ buffers; float haircut; May/Nov housecleaning rhythm 79%; hazard batching 2/3); Part 2 term-by-term (crowding = 30-session short-balance build w/ HIGH/MED/LOW + EXITING and WHY it matters — the crowd's exit sets the print, 6919 exhibit + live 1101 read; T-multiple 16x/38x; auction share delete-vs-add asymmetry 60-72% vs ~10-50%; gap band |123|±82 direction-not-predicted; ADV-days; footprint >100% meaning; shortlist probability construction incl. BELOW-FLOOR honesty); Part 3 one-breath versions
- Suite 426+1skip

## Session 9i continued-17 (2026-08-04) — IB HARVEST LANDED + STUDIES ON DIRECT AUCTION DATA
- BILL'S HARVEST (his machine, guided): TWSE sub + restart fixed entitlements; **floor bracketed empirically: Mar-17-23 fails / May-31-23 works → IB_FLOOR=2023-05-01 (earliest 5m event = May-2023 MSCI SAIR)**; TPEx sub added but its historical feed is shallow (2023-08/2024-05/2024-11 windows below TPEx floor — 3-window documented gap; TPEx earns forward); **96/99 + 20 bridge-era windows landed: 65 codes, 202,934 5m bars incl. discrete 13:30 auction bars**
- SANITY VERDICT: **unit switch located (≤2024-03 LOTS, ≥2024-05-31 SHARES — boundary-checked on the May-24 bridge window 0.953; IB_UNIT_CUTOFF=2024-05-01 ×1000)**; auction inclusion confirmed at scale (post-switch ratios 0.95-1.00); anomalies catalogued (6446 1.20/2801 1.08 = probable after-hours-session inclusion; Feb-26 cohort 0.80-0.90 = block-trade share on that print day — internally-consistent shares unaffected); **1102 direct auction share 0.914 = the derived 0.914 EXACTLY (derivation method validated by direct observation; 13:25 call-window bar = 0 ✓)**
- WIRED: tday_execution_studies.base_table rebuilt on _ib_event_set (bridge events included), source priority IB-direct > TV-5m > TV-60m-derived; 86 name-days joined
- **RERUN RESULTS: (1) violence NULL holds a THIRD time (n=86 direct, R²=0.033)** — triple-confirmed (17/85/86), unconditional band stays the quote; **(2) THIN/RICH honest expansion: n 25→80, ρ 0.61→0.306, p=0.006 — still significant; small sample had overstated it** (test re-pinned with the expansion note); **(3) decomposition refined at true 5m boundaries — the TV-hourly "AM leg" secretly spanned 09:00→13:00 (hourly bar semantics); corrected attribution relocates the FTSE-delete recovery INTO THE PRINT (auction leg −79bps) rather than the morning**; MSCI legs ~0 = continuous flat + random gap direction, consistent throughout
- Suite 426+1skip; commit Bill's

## Session 9i continued-16 (2026-08-04) — TW ALIAS BRIDGE (THE PRE-2025 MSCI UNLOCK)
- IB debugging thread (Bill's machine): TWS-restart fixed the entitlement binding (probe 8454 -> 55 bars incl. its 13:30 auction bar); **2018 probe returned "no permissions" = IB's pre-COVERAGE error in disguise — IB's TWSE floor sits near their 2023 launch, bracket empirically** (probe 2330 20230616 / 20220617); fetch handles pre-floor windows by skip-not-fail
- Windows already cover the FULL ann->eff period + ~2wks pre-announcement runway (eff−33d -> eff+7d); ib_harvest floor extended TV's 2022-06 -> **FTSE 2018-03 (125 windows)** (IB not bound by TV depth)
- **TW ALIAS BRIDGE BUILT (scripts/tw_alias_bridge.py): 135/136 MSCI TW names mapped 2015-2026** — TWSE ISIN English registry (isin.twse.com.tw e_C_public, big5, disk-cached — server throttles + ~40s slow) + decade-bridge token matcher + NEW containment pass (ISIN master uses ABBREVIATED names: ACCTON/GUC/FPCC; unique-containment w/ len≥4 guard) + 2 seed batches (acronym/TPEx/delisted, tagged UNVERIFIED-SEED); **HONPRECISION deliberately unmatched** (prior 2354 print-rejection on record — investigate, don't guess); eff fallback = month's last bday (MSCI rule) for 2 PR-parse gaps
- **data/msci_tw_events.json: 34 MSCI TW events with codes back to Feb-2015**; wired into ib_harvest (pre-Aug-2025 seasons; dupes excluded) → **231 windows spanning 2015-02-27 -> 2026-06-18**
- HOW-FAR-BACK ANSWERS: MSCI keys floor 2015 (archive; extendable ~2003 for price-only studies via more PDF fetches); FTSE keys floor 2016-11 (TIP collection; harvest floor 2018-03 = earliest w/ codes+eff; 2017-06 rule-derivable); IB 5m floor = empirical ~2023-ish (bracket via probe); pre-IB-floor events analyzable at DAILY resolution via STOCK_DAY (2016+) using the same bridge — the TWAP/MOC study can now extend to MSCI 2016+ (queued)
- +1 test (135 mapped, HONPRECISION-only unmatched, 34 events, eff/ann complete, 2015-02-27 floor, ≥200 windows); suite 426+1skip

## Session 9i continued-15 (2026-08-04) — IB HARVESTER BUILT (Bill has an IB account)
- Residency check (sourced): Fugle ALSO needs an E.Sun brokerage account (demo token otherwise); TW brokerage for HK residents = permitted category but IN-PERSON only (UI number online 4h post-entry; online opening ROC-tax-residents only) — a Taipei-trip errand, not remote
- **Bill has INTERACTIVE BROKERS → scripts/ib_harvest.py** (runs on HIS machine vs TWS/Gateway, sandbox can't reach his session): IB 5m depth limits LIFTED for bars ≥1min (TWS API docs), pacing 60/10min honored (6s sleep); 3-step flow: `verify` (one-name entitlement test incl. DELAYED fallback before any bulk) → `fetch` (87 event windows 2022-06→2026, resumable, atomic, ~30min) → `sanity` (bar-sum vs official daily DECIDES auction-inclusion + the lots-vs-shares factor empirically — nothing assumed); output ib_bars.json in tv_bars row shape for study consumption; setup instructions in-file (API port, TWSE market-data subscription in Client Portal, ib_async)
- HF_DATA_SOLUTIONS_TW.md updated w/ Bill-specific findings section; 87 windows enumerated; syntax+windows verified in-sandbox; suite 425+1skip
- NEXT once Bill runs it: if sanity≈1.0 → IB supersedes TV everywhere → rerun the three studies at 5m auction-inclusive across 2022-2026

## Session 9i continued-14 (2026-08-04) — CLIENT-SCORECARD EXPLAINER + THE THREE STUDIES
- Buy-side measurement explainer (chat): benchmark ladder (vs-close primary, degenerate for pure MOC → weight shifts to) 5 differentiating dimensions: estimate accuracy (estimate-vs-realized ledgers; sandbagging kills trust), discretion value-added (counterfactual — sophisticated clients compute it), completeness/exceptions (locks, residuals, MOC-integrity binary), footprint/reversion (T+1/T+5 attribution via Virtu/BestX-class TCA), consistency (variance = the broker-wheel criterion); machinery: quarterly reviews, peer universes, debrief quality scored; our studies = the client's ruler pre-applied to ourselves
- **ALL THREE STUDIES BUILT+RUN (scripts/tday_execution_studies.py, 85 name-days): (1) VIOLENCE V2 — THE NULL SURVIVES AT n=85** (R²=0.023 all; FTSE 0.01, MSCI 0.095): auction share does not predict gap magnitude even at 5x v1's data — the unconditional band |gap| stays the honest quote, now with real sample; **(2) DECOMPOSITION** (fav bps medians): FTSE adds AM −93 (the fade), FTSE dels AM −74 AND auction leg −79 (recovery at the print itself), MSCI legs ~flat w/ abs gap 51 and signed median ~0 (direction random = crowd-exit rule); **(3) THIN/RICH PROXY — FIRST SIGNIFICANT REAL-TIME-READ RESULT: Spearman ρ=0.614, p=0.001, n=25** — late continuous run-rate (13:00-13:25 at 5m) predicts relative print size; graduates to the real indicative walk when the Aug-31 archive lands
- +1 test (v2 null at n≥80 pinned, THIN/RICH ρ>0.4 p<0.01 pinned, decomposition fields); suite 425+1skip

## Session 9i continued-13 (2026-08-04) — TV HARVEST + DERIVED AUCTION SHARES AT SCALE
- HARVEST COMPLETE (scripts/tv_harvest.py, atomic writes, resumable): **61 codes hourly (full 2022-06→2026 depth, 5000 bars each) + 30 codes 5m (2026-03→now)** = 21MB cached (data/tv_bars.json); harvest set = all FTSE change names 2022-09→2026-06 + MSCI TW registry + Aug shortlist; TWSE→TPEX fallback per code
- **DERIVATION AT SCALE (docs/case_studies/AUCTION_SHARES_DERIVED.md): 85 per-name event-day auction shares, ZERO sanity failures** (continuous<official held on every row) — dataset 17 hand points → 85
- **NEW FINDING — the auction-dominance ASYMMETRY: deletes' prints dominate their tape (FTSE Sell median 72.5% max 88%, MSCI Sell 59.6% max 91.4%=1102) while adds' prints DROWN in it (MSCI Buy median 7.2%, FTSE Buy 51%)** — adds are momentum names w/ huge retail tape (index flow = minority of even the print), deletes are faded names where the index flow IS the day; execution: delete MOC = you ARE the auction (footprint critical), add MOC = minority participant (2344's crowd-overwhelm coheres)
- +1 test (85 rows OK, zero flags, asymmetry medians + 1102-class max pinned); suite 424+1skip
- NEXT (queued, user to confirm priorities): violence-curve v2 re-test at n=85 (v1 null was n=17), execution decomposition (cost = AM drift + PM drift + auction gap per class at 5m/hourly), THIN/RICH 5m calibration for the 2026 prints

## Session 9i continued-12 (2026-08-04) — HF DATA: ALL SOLUTIONS ASSESSED (docs/HF_DATA_SOLUTIONS_TW.md)
- Exhaustive probe round 2 (all live-tested): **TradingView via tvdatafeed anonymous = the free unlock — 5m bars to 2026-03 (covers the May-29 MSCI print at 5-minute resolution) + 1h bars to 2022-06 (~16 event T-days), MORE complete than Yahoo (first hour present; Yahoo 09:00 bar vol=0 verified undercount)**; ToS-grey stated (research yes, production no); Twelve Data lists TWSE but plan-gates intraday; Fugle 401-without-key (free signup); Shioaji 1m-to-~2020 doc-verified (BILL ACTION recommended: SinoPac account = clean deep legal solution w/ auction); FinMind sponsor = cheapest paid; TWSE E-Shop/IB/LSEG-BMLL documented
- **THE DERIVED METHOD (found during verification): official STOCK_DAY daily vol − TV continuous vol = per-name AUCTION PRINT** — exhibit 1102 May-29: 205.2M official − 17.6M continuous → **auction = 91.4% of its deletion day**; converts the auction-share dataset from 17 hand points to potentially hundreds (violence curve re-opens w/ real n; MSCI-class per-name auction shares previously unmeasured); caveats stated (per-day sanity check, block-trade term via BFIAUU, TV grey/cache-aggressively)
- Recommended plan in doc: TV harvest now → Shioaji signup (Bill) → Aug-11 archiver still needed (nothing captures the indicative WALK) → LSEG/BMLL at CLSA

## Session 9i continued-11 (2026-08-04) — HF DATA HUNT + T-DAY HOURLY SHAPE
- USER ASK (find historical per-name HF data for TW MSCI T-days) — probe verdict, all live-tested: **yfinance 60m WORKS to ~730d back (the unlock — covers 8 event T-days: 4 MSCI + 4 FTSE 2025-26)**; 5m/15m/30m/90m walled 60d; FinMind minute not in free enum + tick returns "update your level"; Stooq bot-walled; TWSE per-name tick = paid Data E-Shop; auction-resolution history stays FORWARD-ONLY (archiver Aug-11)
- HARVEST: scripts/tday_hourly_shape.py — 57 name-T-days across 8 events (atomic cache writes); **VERIFIED CAVEAT (3443 exhibit): Yahoo intraday EXCLUDES the closing auction — hourly sum = 22.5% of official daily on its print day, 09:00 bar vol=0** → volume metrics relabeled CONTINUOUS-session; price metrics valid; the continuous→close leg = the separately measured gap band
- **FINDING (docs/case_studies/TDAY_HOURLY_SHAPE.md): FTSE T-day continuous sessions are the CROWD-UNWIND session — BOTH sides move AGAINST the index flow (adds fall −198bps AM median, deletes rise −120 fav; 2344/6919 locks = the extremes); MSCI T-day continuous ~FLAT (adds +62, dels +8) — the action is entirely in the 16x print**; execution reading: FTSE T-day worked fraction can harvest the unwind intraday, MSCI T-day = the close is the event
- Step-3 brainstorm delivered in chat (measured inventory → Aug-31 application incl. 1101 THIN/RICH numbers ~$220M/$480M; unmined list: crowding→print-character H2b, reversal-capture conditioner, 5s volume curve, indicative commit rule forward-only; NOVEL cascade hypothesis: TW's 13:30 print as information for same-day HK/CN closes — unpublished in our lit map)
- +1 test (harvest ≥7 events, FTSE against-flow medians pinned, MSCI flat, caveat text enforced in doc); suite 423+1skip

## Session 9i continued-10 (2026-08-04) — VARIABLE LAB (THE FULL FRAMEWORK)
- **REGISTRY LOCKED FIRST** (docs/VARIABLE_LAB_REGISTRY.md): 8 pre-declared hypotheses (variable x decision moment x target x direction) + FIXED acceptance criteria (ADOPT ≥50bps & 65% event-winrate & LOO-stable & n≥6; NULL-PIN <25bps n≥8; class cells before pooling; effective n = EVENTS)
- PANEL EXPANSION: 8 more windows backfilled via ensure_window (MSCI 2025-08/11, 2026-05; FTSE 2024-06/09/12, 2025-03/06/09, 2026-06) → **16 full five-pillar TW events**; quotes.json CORRUPTED mid-write by a timeout (11MB truncation) → salvaged all 227 dates via last-complete-block trim; **atomic write (tmp+rename) added to backfill saves** — the incident class closed
- **agents/variable_lab.py**: master_panel (16 events via time_machine, PIT), build_observations (per name-event: H1-H7 variables at decision days + targets), event-clustered split effects (above/below EVENT-side median — regime-neutral), mechanical verdicts, LOO stability; run 1 = 83 name-events
- **RUN-1 VERDICTS (docs/VARIABLE_LAB_LEADERBOARD.md)**: **ADOPT H2 crowding-build (deletes) +149bps wr 0.67 — but direction OPPOSITE the pre-declaration** (crowded deletes PRESS into the print, don't recover — coheres w/ CN/HK press + May-26 TW; 6919 squeeze = tail case, H7 gated); **ADOPT H5 cohort dispersion +210bps FTSE-only** (LEADERS persist — opposite the laggard-convergence declaration; pooled flips → strictly-FTSE); **REJECT H3 A+3 momentum (−73bps, wr 0.38 on 13 events) — REVERSES the 6-event impression; the A+3 gate is demoted to descriptive context** ("6 events looked fine; 13 killed it — effective n is events"); REJECT H1 front-run completion + H4 foreign coverage (sign-unstable; foreign flow = confirmatory not predictive); H6 CRITERIA-GAP (bps thresholds vs t_mult units — cannot move post-hoc; registry v2 item; observed pattern reported unverdicted); H7/H8 DATA-GATED; ALL MSCI cells DATA-GATED (3 events < 6)
- Aug-2026 = standing OOS grade for every verdict; +1 test (verdict mechanics synthetic + run-1 verdicts PINNED incl. the A+3 reversal); suite 422+1skip

## Session 9i continued-9 (2026-08-04) — STEP-2 DATA VERIFIED + MSCI TW WINDOWS EXTENDED
- User Q (can we get historical stock data for past review windows? Yahoo doesn't support this?): **LIVE-VERIFIED half-true — Yahoo DAILY is deep (28 rows for the Nov-25 window ✓), Yahoo INTRADAY hard-walled at 60d (5m for Nov-25 fails: "must be within the last 60 days")**; TW alternatives already integrated & superior: STOCK_DAY/MI_INDEX daily 2016+, TWT93U/TWT38U 2015+, 5s market archive 2012+; irreducible gap = per-name intraday history (FinMind sponsor-tier; forward indicative archiver standing from Aug-11)
- Step-2 code inventory confirmed: event_window planner, time_machine (38+ events PIT), window_study (6 FTSE windows), window_study_decade (776 CN/JP/HK), May-26 replay
- **BUILD: MSCI TW 2025 events added to time_machine.MSCI_TW registry** (Aug-25: +6919,2059/−9904,9945; Nov-25: +3665,2360,2368,2449,1504/−2353,2409,2377,6415,2347,6409,3702; 5274 TPEx excluded stated) — data already in stock_day from the ex-post fetch (327 code-months, 0 new jobs)
- **TWAP/VWAP/MOC study rerun: 125 name-events, 0 skipped — FIRST MEASURED MSCI TW BUY CLASS (n=7): window-VWAP −280bps median vs close, 57% win** = TW MSCI adds GRIND UP (consistent w/ decade revision, not CN/HK pop-decay); MSCI Sell doubled to n=20 (+48 median cost to spread — MOC-favoring confirmed)
- tday_cards upgraded: Buy playbook now cites the IN-CLASS measured prior ("TW MSCI adds (measured, 2025 events): −280bps n=7") replacing the FTSE cross-class fallback (fallback retained, labeled); cards+preann packs regenerated; Time Machine gains 2 events
- Tests updated (MSCI event count 2→4); suite 421+1skip

## Session 9i continued-8 (2026-08-04) — DATA-FRESHNESS GUARANTEE (STRUCTURAL)
- User escalation (staleness = big issue) → **agents/data_freshness.py: live analytics can never run on silently stale data**. ensure_fresh_shorts: expected-latest-trading-day check (tolerance 1 bday — TWT93U publishes post-close), fetches EVERY missing bday, holiday/not-published days → no-data ledger (no refetch loops), **FULL-DAY storage (all codes — kills the code-set-gap class that gave 1504/1402 only 8 obs)**, TTL 4h against UI-rerun hammering, injectable fetch_fn for tests
- Failure honesty: network failure → status DEGRADED + rendered WARNING, never a crash, never silent; freshness_line banner REQUIRED on every live artifact (pack header + UI caption/warning)
- Wiring: build_pack(live=True default) auto-refreshes + re-reads cache before crowding_watch; **PIT/as-of runs EXEMPT by design (crowd_asof implies no fetch — a backtest must not see the present)**; UI Tab-1 runs the TTL-guarded check on every visit + notes when pre-generated artifacts predate a refresh
- Verified live: Aug pack header now renders "DATA FRESHNESS [OK]: latest 20260803 vs expected 20260804 (1 bday, tolerance)"
- +1 test (stale→REFRESHED w/ all missing bdays, holiday ledger, full-day storage assert, TTL short-circuit, DEGRADED-not-crash w/ WARNING line); suite 421+1skip

## Session 9i continued-7 (2026-08-04) — CROWDING CACHE REFRESHED TO CURRENT
- User challenge (why as-of Jul-22?): no structural reason — cache was last pulled Jul-22; TWT93U publishes daily. Fetched Jul-23→Aug-3 (8 sessions, 11 watch codes) into event_data_cache; pack regenerated as-of 20260803
- **THE PICTURE MOVED with 8 fresh sessions**: 1101 still HIGH but build MODERATED (+32% vs +53%, 5-obs flat −3% — pause, no longer alerting); **1326 now building fast (+40%/5obs — NEW alert)**; 2633 covering (−12%/5obs); alerts 5→2; 1504/1402 now have data (n_obs=8 — they were outside the older fetch code-set, stated)
- Lesson encoded: crowding is a DAILY read — the Aug-11 protocol's final refresh remains mandatory; suite 420+1skip

## Session 9i continued-6 (2026-08-04) — PRE-ANNOUNCEMENT ORCHESTRATOR
- Six-category walkthrough saved: docs/PRE_ANNOUNCEMENT_ANALYTICS_TW.md (screening w/ uncertainty, crowding surveillance, pre-positioning economics, capacity cards, marketing, priors refresh + the institutional own-flow complement)
- **agents/pre_announcement.py — one agent, six categories**: NEW crowding_watch (dated short-balance deltas, AS-OF aware for backtests, ALERT = |5-obs delta|≥10%, EXITING tags), NEW priors_snapshot (all microstructure priors dated), NEW must_start_by (eff − ceil(adv_days/25%) bdays per card), advisory_lines from decade class costs; build_pack composes existing screen/shortlist/cards; grade_pack adds **Brier scoring on candidate probabilities** (graded record for the probability layer itself)
- **MAY-2026 BACKTEST (PIT: April universe, SAIR config, crowding as-of 05-11)**: 7/7 dels + 1/1 add, 0 missed visible, false dels = the 3 residents, **Brier 0.212 (n=11, < 0.25 coin-flip; honestly penalized by residents at p=0.6)** — docs/case_studies/PREANN_PACK_MAY2026_TW.md
- **AUG-2026 LIVE PACK** (docs/case_studies/PREANN_PACK_AUG2026_TW.md): 10 candidates, **5 crowding ALERTS at as-of 07-22 (staleness stated): 1101 HIGH +53% AND still building (+11%/5obs — street pre-positioning its deletion), 2633 building fast off low base (+62%/5obs), 2207/1326 EXITING**; must-start-by dates per card; priors snapshot dated
- +1 test (as-of PIT filter on synthetic cache, alert rule, must_start_by, May grade+Brier pinned, Aug fields); suite 420+1skip

## Session 9i continued-5 (2026-08-04) — T-DAY FORECAST CARDS
- CARD GENERATOR (user: build w/ full metric transparency): agents/tday_cards.py — per-shortlist-name effective-day forecast chaining ONLY measured priors; **METHOD table rendered atop every artifact: metric -> rule -> source -> basis(n)** — no number without a "how"
- Metrics per card: p_convert (shortlist basis quoted), flow-if-converts = cap x ff x 5-9% float (UNCONDITIONAL, labeled) + p-weighted variant (capacity-planning-only warning), ADV-days->bucket, print multiple (measured MSCI Sell 16x med/38x max n=8; **Buy = NO MEASURED PRIOR stated, FTSE 5x labeled cross-class ref**), expected T volume, EVENT-DAY auction-share prior (43.7-71.3% med 57.9 n=4 — fixed from an 11% median polluted by non-event days), auction footprint w/ >100%-is-meaningful doc (obligated flow can't clear one print at prior sizes), gap band |123|±82 n=17 w/ sign-NOT-predicted rule (null pinned; crowd's-exit exhibits), limit context (3.0%/2.0% baseline, ~5.5% print days, obligated-side-favored), live crowding read, playbook = discretion matrix @illustrative 20% envelope + decade class cost cite + demoted-hypothesis flag on adds
- LIVE READS in the Aug-26 TW cards: **1101 crowding HIGH (+53%/30obs) -> WORK-AHEAD playbook**, flow-if-converts $225-406M = 9.8-17.6 ADV-days MULTI-DAY, footprint 148% of expected print; BELOW-FLOOR rows carry note only (no fabricated numbers)
- Outputs: docs/case_studies/TDAY_CARDS_AUG2026_TW.md + data/tday_cards_aug26.json + UI expander in Tab-1 (cards w/ METHOD popover); py3.10 f-string gotcha fixed in view
- +1 test (flow arithmetic exact vs PASSIVE_OWN_RATE, 16x prior, WORK-AHEAD on crowded delete, NO-MEASURED honesty on Buy, blind-row note, METHOD completeness in render); suite 419+1skip

## Session 9i continued-4 (2026-08-04) — NO-CHANGE SHORTLIST LAYER
- USER RULE ADOPTED: a zero-call prediction must still ship a ranked SHORTLIST (probabilities + reasoning) so Steps 2-4 have names to analyze — "for a no-change there isn't much we can analyze" fixed structurally
- p_any base rates added to decade stats (per market x review type: TW QIR P(any add)=45.5% / P(any del)=50%; TW SAIR 91%/86%)
- review_engine.shortlist_candidates: p = P(any, decade) x visible-share x proximity-softmax(|log x_thr|, temp 0.25); **BLIND_SHARE explicit per market (TW 0.6, basis: 13/21 of 2025-26 changes below the 16-name floor) with the blind mass carried on a named BELOW-FLOOR row** — never overstating visible candidates; recent-deletion CAUTION appended w/ decade re-add rate (TW 0%); negligible rows (p<0.005) dropped; auto-attached to run_full_review when 0 live calls; rendered in pack
- AUG-26 TW SHORTLIST now in the pack: adds 2324 (p=0.062, +78% needed, re-add caution), 1504, 2633, 1402 + BELOW-FLOOR p=0.273; dels 1101 (p=0.149, 2.19x floor), 2207, 2002, 1326 + BELOW-FLOOR p=0.30 — Steps 2-4 run on these names now
- +1 test (shortlist present, p bounds per side ≤ P(any), blind rows x2, caution text); suite 418+1skip

## Session 9i continued-3 (2026-08-04) — CHANGE LIST COMPLETED
- MSCI_APAC_CHANGES doc regenerated per user: EVERY review shown per market (46 reviews = 44 archive quarters + held Feb/May-2026 lists), no-change quarters explicitly listed ("a quiet review is a data point too" — 248 no-change rows), all 13 APAC markets through May-2026; TW header: 34/46 reviews with changes; _rows_2026() appends the local 2026 lists without touching ledgers()/decade stats (n=44 pinned test unchanged); suite 417+1skip

## Session 9i continued-2 (2026-08-04) — SCREENING FUNNEL
- FUNNEL BUILT (user request: visualize universe -> conditions -> candidates): agents/review_funnel.py — funnel_stages consumes the ENGINE'S OWN artifacts (screen dict + calls) so the viz can never drift from the engine; stages S0 universe (real+count-anchored tail) -> S1 eligibility (float/ATVR) -> S2 GMSR ladder+thresholds -> S3 threshold candidates (+watch band) -> S4 churn buffers -> S5 Feng-Tay verification -> FINAL calls w/ probabilities; validate_against_key grades final calls vs official keys w/ UNGRADABLE-below-floor bucket
- screen_market + pit_screen now return "assembled" universe (funnel decomposition); watch added to pit_screen return
- **VALIDATION (May-26 SAIR, April-PIT universe, graded config w/ migration sweep + CA rule): funnel reproduces the graded run EXACTLY — 7/7 dels + 1/1 add (6223.TWO MPI), 3 false dels = the cutline residents 1101/1326/2207** (the hazard class); config gotcha caught en route: plain screen_market (floor-only) missed all 7 — May dels were MIGRATION deletions, pit_screen is the graded config
- PREDICTION funnel (Aug-26 QIR, refreshed caps, churn buffers = May-26 actuals): 516 -> 0 visible candidates, FINAL row carries the blind-band declaration
- Decade scope stated in doc + UI: official OUTCOMES for all 44 reviews = MSCI_APAC_CHANGES doc; funnel REPLAY beyond May-26 gated on share/float vintages (not fudged)
- UI: page6 Tab-1 expander "🔻 Screening funnel" — plotly funnel + stage table + grade line (validation) / blind-band caption (prediction), radio toggles the two runs; data/funnel_tw.json via scripts/funnel_demo.py
- +1 test (stage monotonicity, 7/7+1/1 grade, residents as the only false dels, Aug-26 visible=0); suite 417+1skip

## Session 9i continued (2026-08-04) — TW EX-POST REVIEW + OFFICIAL RE-GRADE
- FULL CHANGE LIST EXPORTED: docs/MSCI_APAC_CHANGES_2015_2026.md (all 13 APAC markets, 44 quarters, official names); TW per-review table + TW Aug-QIR base rate: 7/11 years had changes (median ~2), 4/11 quiet
- **OFFICIAL RE-GRADE of the 2025 backtest (keys solved after it ran)**: Nov-25 truth = 6 adds/7 dels — detector found 2/13 (NT$4B floor tuned on giants; real changes were $1.5-4B mid-caps Acer/AUO/MSI/Silergy/Synnex/Voltronic/WPG — detector limits stated); engine's 9 flags overlapped actual Nov-25 dels ZERO times (all truth below the 15-name floor — BREADTH confirmed as THE binding TW constraint); **hazard rule SURVIVES truth: 6/9 flags officially deleted May-26**, 3 survivors = the usual residents; **first observed quick reversal: TECO 1504 added Nov-25 deleted May-26** (L5 counterexample, n=1, two-review gap — buffer spans one review so wouldn't have blocked)
- **DRIVER CLASSIFICATION (scripts/tw_expost_msci.py, 29 changes 2025-26, curated code map, ret_3m unadjusted)**: ADDS 6/7 = MOMENTUM (+30..+107% into announcement — TW adds announce themselves on the tape; 6919 −81.5% flagged as capital-action contamination, not asserted); DELETES: **9/20 STALE (flat — coverage-arithmetic, momentum CANNOT predict, validates ladder-first design)**, 6/20 DRIFT, 5/20 DECLINE (fast converters)
- ENGINE IMPROVEMENTS APPLIED: hazard-velocity tag in build_calls (DECLINE/DRIFT/STALE from optional ret_3m col); momentum-riser screen adopted as candidate-DISCOVERY tool for the breadth gap (flag +30%/3m mid-caps for share-count acquisition); TAIWAN_MARKET_ANALYSIS §6 written (re-grade, drivers, boundary)
- **AUG-2026 TW BOUNDARY ANSWER (§6c)**: at refreshed caps no member near 0.5x floor (nearest 1101 at 1.09x) and no visible non-member near 1.8x (best 2324 at 1.01x, needs +80%) → posture = "no changes VISIBLE, blind band $1.5-8B declared, decade says ~2 changes typically live there" — not "no changes expected"
- Housekeeping: live yfinance integration test now SKIPs on NaN feed (Yahoo throttle ≠ code failure); suite 416+1skip

## Session 9i (2026-08-04) — ENGINE REVIEW + DECADE PRIORS + AUG APAC RERUN
- CLSA thread (chat, fact-checked): 2013 CITIC acquisition EXCLUDED Taiwan (CACIB retained; became CLST via 2016 MBO; CLST now merging into SinoPac NT$1.628B) — CITIC CLSA holds NO TW license; TW execution = HK desk via local partner under FINI; corrected earlier overstated claim. Who-runs-analytics: agency shops have no dedicated index analyst — the PT dealer is the role (the interview angle)
- AWS/Jefferies STUDY + CLSA PLAN: docs/CLSA_PT_AI_INTEGRATION_PLAN.md (Jefferies anatomy table incl. their LLM-never-renders-numbers rule = our invariant independently validated in production; peer scan MS/GS/JPM = all HORIZONTAL, the PT vertical is open; §3b cash-vs-PT narrowing: basket ontology, calendar-proactivity, client-grade artifacts, 6 PT behaviors; 4 phases; risks table)
- STEP-1 DESIGNS: docs/STEP1_AGENTIC_DESIGN.md (methodology-KB substitutes Jefferies' schema-RAG; 5 workflows W1-W5: pitch-pack generator, boundary briefer, envelope advisor, intake+acknowledge w/ LLM-proposes-code-decides validator, methodology Q&A; components; institutional table; build order) + docs/PROGRAM_ORDER_PLACEMENT.md (S0-S9 process: 3 modes agency/principal/DSA; AI map per step; money ranked: fingerprint-anomaly catch #1) + docs/AUG2026_QIR_LIFECYCLE_WALKTHROUGH.md (live-event day-by-day: ann Aug-11/12, T=Aug-31; crucial days ranked)
- DSA explainer (chat, sourced): US 44% electronic/37% algo; EU small funds >50% low-touch; Asia climbing from 75%-HT (2011); mega-passives self-serve; conversion play = per-event high-touch
- **ENGINE REVIEW (user request): docs/PREDICTION_ENGINE_REVIEW_2026.md** — L0-L9 recap; why-2015 = TWT93U/TWT38U regime start; HONEST scope: keys solved 44Q but PIT-graded 2025-26 ONLY (input-vintage gate: shares/floats current-dated, degrades ~2-3y); record: 22/22 adds PIT, dels ~90% same-review, QIR false-dels 10→0; TYPE-1 all state/cadence errors now structurally gated (L4/L5/L7/L9 table); TYPE-2 all data-boundary (floor/fast-entry/dual-line/float-vintage/FIF-discretion table w/ fix paths); improvement plan 6 items priority-ordered
- **IMPROVEMENT EXECUTED — DECADE PRIORS (items 2+partial 5)**: scripts/msci_key_stats.py on all 44 quarters x 13 APAC markets → data/msci_decade_stats.json: **L4 cadence VALIDATED DECADE-WIDE (SAIR deletion share 62-90%, TW 79/JP 78/SG 90 — ~3x QIR intensity)**; churn base rates measured (add→del-within-4: TW 4.3%, HK 16.7%, PH 25%; del→re-add: India 9.5% = the reversal-prone market); wave quarters per market
- ENGINE WIRED: review_engine.decade_consistency (market x review expected-count quartiles → OK/ELEVATED/OUTSIDE — a review flag never a suppressor) + load_decade_stats; run_full_review emits r["decade"]; render shows per-market decade-prior line
- **AUG-2026 APAC PACK RERUN (8 markets)**: 0 calls everywhere, all decade verdicts OK — the quiet-QIR pack is now DECADE-VALIDATED not merely asserted; caps remain April-vintage w/ MANDATORY Aug-11 refresh standing (protocol unchanged: refresh caps, boundary scan, TW AI-quartet via EWT, Bill commits before Aug-12)
- +1 test (44Q stats, SAIR-share>50% four majors, consistency verdicts incl. OUTSIDE); suite 417
- **USER CHALLENGE (zero-call pack can't be right) — CONFIRMED AND FIXED**: base rates measured — only 1/44 reviews was APAC-quiet (median review = 43 changes); China quiet just 4/44 and EVERY Aug QIR since inclusion had changes (Aug-25: 14 adds/17 dels); per-market zero-review counts tabled (TW 12/44 → TW-quiet plausible, CN-quiet not)
- TWO ERRORS DIAGNOSED: (1) consistency check was ONE-SIDED (over-calling only) → two-sided verdicts OK/ELEVATED/OUTSIDE_HIGH/OUTSIDE_LOW (flag when calling < half q25 with median>=3); (2) April-vintage caps → scripts/refresh_aug_caps.py repriced all 125 universe names Apr-30→now via batched yfinance (resumable; dispersion p10 0.75/p90 1.18), wired into post_may_universe ONLY (PIT replay path stays April-frozen deliberately)
- RERUN RESULT: **Korea DELETE surfaced — 011170.KS at 0.40x GMSR** (sub-floor = correct QIR class, unverified Feng-Tay 0.6); **China now reads OUTSIDE_LOW on adds** — 0 called vs decade QIR median ~12 = the 125-name universe cannot see the mid-cap risers/IPOs that supply China QIR adds; pack notes rewritten: China add side = NO-CALL-below-the-floor (breadth gap, improvement item 4), NOT "no changes expected"; the check now EXPOSES the blind spot instead of asserting quiet; Aug-11 final refresh still mandatory; test updated (OUTSIDE_HIGH + China OUTSIDE_LOW pinned); suite 417

## Session 9h continued-2 (2026-07-29) — TW LIMIT-MOVE STUDY
- FTSE-keys-for-CN/JP/HK explainer (chat): TIP was a Taiwan-specific lucky structure (TWSE/FTSE JV w/ enumerable /news/{id} SSR archive); ftse.com Constituents.jsp dead since Feb-2015 (probed); each market = separate archaeology (HSIL PDF archive > China A50 scattered sources > TOPIX/Nikkei different providers); value order queued: Hang Seng, A50, TOPIX/Nikkei
- LIMIT STUDY (user request): scripts/limit_moves_tw.py — EXACT band math (tick table, up=floor/down=ceil to tick; float fix round-2dp; both case locks verify to tick), official MI_INDEX daily w/ signed-change->prev-close + last-ask column as LOCKED-BOOK detector; 23 days cached (19 July baseline + 4 print days)
- INCIDENCE: baseline ~2.96% touch limit-up / 2.01% locked at close / 2.17% touch-down daily; violent clustering (Jul-17: 9.3% touched down, 79 locked); ~95% of locked-up closes have ZERO ask = truly frozen books; print days run 1.7-2.2x baseline on up-side (4.95-6.39% touched; n=4, prior not law)
- **CASE A — 6919 deletion locked LIMIT-UP into its own deletion print (Jun-18)**: ann 96.0 -> pressured to 88.2 -> recovered -> T at 109.0 = exact cap, 53.9M shares (~13x), zero asks; passive SELL on the right side of the lock (fills 100% at cap, best price of window); working early = −1,700-1,900bps vs print; squeeze-INTO-deletion = FTSE-delete recovery pattern at its extreme
- **CASE B — 2344 add locked LIMIT-DOWN into its own add print (Mar-20)**: ann 106.5 -> +20% momentum to 128 -> T crashed to 110.0 = exact floor on 338M (window max); crowd unwind dumped MORE than trackers needed; passive BUY filled 100% at floor, −14% vs T-2; pre-positioning alongside crowd = worst trade of window
- LESSONS (docs/case_studies/TW_LIMIT_MOVES_2026.md): print price is set by the CROWD'S EXIT not the index flow's direction (crowding-violence link, two locked exhibits); print-day locks FAVOR the obligated flow (band caps price in passive side's favor; fill risk sits on crowd's side); mid-window locks remain the dangerous kind (planner LOCK RISK) — run-sheet should distinguish; extreme validation of discretion matrix (crowded-delete WORK-AHEAD = out before squeeze; crowded-add NO-prepositioning = 2344 is the cost)
- +1 test (limit math exact incl. case locks, day_stats synthetic); suite 416

## Session 9h continued (2026-07-29) — DECADE EXPANSION CN/JP/HK
- AUDIT ANSWER (user: did we run Steps 1-2 on CN/JP/HK for ALL changes 2015-now? ): NO — Step 1 live+May-2026-graded only, Step 2 May-2026 only. Feasibility stated: Step-1 decade PIT infeasible JP/HK on free data (no historical universe snapshots; CN partial-possible via baostock, queued); FTSE keys for these markets never collected (MSCI-only study); JP/CN historical crowding absent, HK SFC-reconstructable but out of this pass
- **ALIAS BRIDGE BUILT (the long-queued blocker)**: scripts/window_study_decade.py — MSCI English names -> local codes via exchange English masters (HKEX SSE/SZSE Connect-eligible lists w/ EQTY filter, JPX data_e.xls, HKEX ListOfSecurities), fuzzy token match + abbreviation alias table (CN->CHINA, AGRI->AGRICULTURAL...), accept ≥0.95 or ≥0.65 w/ margin; 611/933 unique names matched (65% — misses ledgered; masters are CURRENT snapshots -> delete-side survivorship in COVERAGE stated); every match VALIDATED BY ITS OWN EVENT PRINT (t_mult≥2, the HONPRECISION technique at scale)
- DATA: all 44 STPublicLists parse (CN 1,008 / JP 213 / HK 49 name-changes); ann+eff dates regex'd from PR txts; 776 windows fetched resumable (baostock CN 512, yfinance JP/HK 264; chunked 40s foreground runs — sandbox reaps background jobs, save-every-8 fix); SSE master layout gotcha (code col 1 not 0, EQTY filter)
- **RESULTS (docs/WINDOW_STUDY_DECADE_CNJPHK.md, 367 print-validated name-events): the May-2026 CLASS INVERSION does NOT generalize** — decade CN adds grind up TW-style (drift +391, day-1 −325, LINEAR −234 = working beats print), deletes show no press-to-print (CN 22-25 LINEAR −8, n=46); the pop-decay is late-regime-or-event-specific; MSCI-add WAIT rule DEMOTED to hypothesis pending Aug-2026 (revision note added to the 9d case study — the one-event caveat did its job)
- Structural finding 2: **CN materiality — only 25% of CN name-events print materially** (excluded median t_mult ~1.1: 10-20% IF flow vs retail-heavy tape; exclusions relabeled NO-MATERIAL-PRINT, not suspect-alias); JP/HK validated prints 8-13x (TW-like)
- Structural finding 3: **the edge is dying newest-era-inward, JP first** — JP 15-21 working crushed print (LINEAR −118/−337 adds, −235/−257 dels), JP 22-25 FLIPPED (+230/+116) = Greenwood-Sammon disappearance arriving in Asia measured in counterfactual space; CN adds still alive 22-25 (−306); HK unstable (n~15/cell, no reliable playbook); 2019-21 the golden era everywhere (IF step-ups + pre-saturation arbs)
- Discretion-matrix encoding: CN adds work-early valid; JP post-2022 MOC-first; HK unconditional-band only
- +1 test (44 events parse, alias matcher unit, panel≥300 validated across 3 mkts, CN-adds-LINEAR<0 revision PINNED); suite 415

## Session 9h (2026-07-29)
- CONCEPT THREAD closed: TE-vs-MOC arithmetic walked slowly (only the traded 3% slice can deviate; one-day deviation ≈ 4-5bp one-off; QUADRATURE: √(40²+8²)=40.8bp — the monitored TE number barely moves; TD gain is a MEAN shift 3-8bp/yr recurring — noise adds in quadrature, means add linearly); TD explicitly in fund selection; TE-for-TD relaxation = pragmatic replication / sampled mandates (EM norm, DM growing); caveat: arithmetic breaks at high event turnover — why strict trackers stay MOC
- PT-DESK ANALYTICS BEYOND REBALANCE (user taxonomy, 7 flows): docs/PT_DESK_ANALYTICS_BEYOND_REBALANCE.md — per-flow analytics + AI leverage + which components port (fingerprinting/netting for quant turnover; IMA-LLM+matching+leakage for transitions; drift-trigger model for cash-flow; basket-embedding cost oracle for AA restructures; creation/redemption nowcast for ETF; dividend-point forecasting for delta-one; Reg-Watch generalized for CA); three AI modes ranked (parse&retrieve > pattern&predict > optimize); rollout order 1,5,6 -> 2,3 -> 4,7
- Monthly-rebalance explainer (chat): three streams (quant signal refresh = cost-vs-freshness optimum; drift correction to policy mix at month-end NAV/benchmark strike; cash-flow plumbing) -> month-end = the unconditional index event
- Step-3 auction-simulator insights enumerated (chat): blind-MOC slippage prior, indicative-convergence commit-time rule, THIN/RICH backtest, fade haircut, imbalance-delta retreat rules, intra-hour split families (class-conditional), limit-lock contingency pricing, completion leg; limits restated (violence null caps self-impact claims; no queue dynamics in single-price call)
- **TWAP/VWAP/MOC COST STUDY (user request: computable from 2015? YES w/ precision statement)**: scripts/twap_vwap_moc_study.py — daily VWAP is EXACT (value/volume from STOCK_DAY, verified to 2016), TWAP = (O+H+L+C)/4 LABELED ESTIMATOR; 5 strategies x 2 benchmarks (vs close = tracking view MOC≡0; vs arrival = ann-day close incl. drift); **109 name-events / 31 events (29 FTSE 2018-2026 + 2 MSCI-2026 TW)**; resumable threaded STOCK_DAY cache (data/tw_history/stock_day.json, 207 code-months)
- FINDINGS (docs/TWAP_VWAP_MOC_STUDY.md, computed not asserted): FTSE adds — window-VWAP beat the close −164bps median (60% win, n=48) and roughly HALVED all-in cost (MOC-vs-arrival +398 vs +196); FTSE dels — MOC won (+57 median cost to spread, deletes recover into print); MSCI TW dels 2026 (n=11) mildly MOC-favoring +32 — closer to FTSE pattern than CN/HK press-to-print, small-n flagged; VWAP dominated TWAP everywhere (partly estimator error, stated); the side/class ASYMMETRY is the sellable product = the deviation-envelope evidence for the TD-for-TE trade
- Gotcha logged: FTSE 2018-06 stated effective 06-18 = Dragon Boat holiday -> T = last session <= stated eff ("data not calendar" x4); pre-2026 MSCI still blocked on name<->code alias bridge (stated in doc)
- +2 tests (cost math: exact-VWAP identity, MOC≡0 invariant, sign flips, summarize shape; events+cache pipeline); suite 414

## Session 9g (2026-07-29)
- User-supplied additions commented + added to §4b: Wang-Yao-Yelekenova SSRN-2023 (hedge funds front-run ETF rebalancing, +0.86%/mo t=3.86 — the 13F-cadence academic mirror of our daily crowding layer; direct support for the discretion matrix premise); ETFGI Feb-2025 (ETF AUM surpassed hedge funds — the regime datapoint: obligated capital now exceeds the discretionary capital that arbitrages it); Petajisto + Arnott already mapped
- EASTSPRING CITATION LIST traced (user request): §4b added to LITERATURE doc, three strands — A) trade-around-the-crowd: **Arnott et al FAJ-2023** (deletions beat additions ~22%/yr; delaying reconstitution trades 3-12mo adds ~23bp/yr — the flexible-implementation client's strongest published case), **DFA-2024 global** (adds/dels +4% into reconstitution, −5.7% reversal after, 15 indices incl. international — immediacy at the print is what costs), **Sammon-Shim JFE** (pure mechanical rebalancing = implicit market timing, 47-70bp/yr drag; composition-aware alternatives save ~50bp); B) flow-demand machinery: **Gabaix-Koijen inelastic markets ($1 flow -> ~$5 market value — the macro version of our auction physics)**, Ben-David et al ETF volatility, Brown-Davies-Ringgenberg ETF-arb non-fundamental demand (academic twin of our creation/redemption proxy), Dannhauser-Pontiff, Agarwal-Fos-Jiang holdings-inference; C) Petajisto already covered

## Session 9f (2026-07-29)
- LITERATURE MAP (user request; history checked — only the L&G hit-rate benchmark was cited before, no review existed): docs/LITERATURE_INDEX_REBALANCE.md — classics (Shleifer'86 demand curves +3%; Harris-Gurel'86 price-pressure/reversal; Lynch-Mendenhall'97 window anatomy; Chen-Noronha-Singal'04 asymmetry; Petajisto'11 +8.8%/−15.1% & 21-28bp/yr index premium; Madhavan'03 Russell), the modern turn (**Greenwood-Sammon JF-2025 "Disappearing Index Effect": S&P adds +7.4%→+0.3%** despite passive growth — predictability+front-running; Bennett-Stulz-Wang; NY-Fed sr484), mechanism/volume (**Chinco-Sammon: reconstitution volume 3.15x ETF-explainable; true passive share ~33.5% vs 16%**; Greenwood'05 Nikkei; Hau'11 MSCI; Kaul-Mehrotra-Morck'00), institutional (FTSE-Russell four-decades, NBIM $2B txn costs, Callan/T-Rowe front-running consensus)
- §5 positions our work: we operate where the effect LIVES (Asia vs the dead US trade — consistent w/ G-S mechanism), Harris-Gurel reversal = our completion leg (~50% measured), the literature's asymmetry is EVENT-CLASS-CONDITIONAL in our windows, Chinco-Sammon excess volume = our measured auction concentration, front-running = our crowding layer quantified; our additions: name-level PIT grading, non-US window microstructure on official data, PIT-conditioned execution counterfactuals

## Session 9e (2026-07-29)
- LIFECYCLE DOC Step-3 refined w/ new §3.0 "What the desk actually DOES on T-day — the honest answer" (user Qs: is it just MOC when auction liquidity suffices? how do desks differentiate?): yes-mostly-MOC stated as the starting fact w/ measured concentration (25%-of-market print, 44-71% add shares); the five not-just-MOC jobs (mechanical certainty at scale, exception minority = skill majority, the one real-time decision w/ the 14%-vs-24% book-commitment edge, netting/GC risk transfer, immediate proof); differentiation stack ranked w/ the NEW event-class-conditional discretion point (FTSE-class adds reward early −630 vs MSCI-class punish +1100 — same envelope spent oppositely by class); "the MOC order is the commodity; everything wrapped around it is the product"

## Session 9d (2026-07-29)
- CN/JP/HK EXPANSION (user: replicate the Taiwan framework Steps 1-2, autopilot; Step 1 already covers these markets via the Asia engine — the new build = Step-2 window analytics): scripts/window_study_cnjphk.py on the May-2026 MSCI cohorts (CN 13 A-lines via baostock daily + H-lines under HK; JP 17 names; HK 0004 + 5 H-lines via yfinance), formulas identical to WINDOW_STUDY §0, PIT baselines pre-announcement
- DATA DISCOVERY: **SFC page lists ALL 724 weekly short files back to 2012** -> HK crowding pillar is HISTORICAL (vintage May-2026 weeks fetched, per-name short_chg series at announcement time reconstructed); JPX site retains ~1 month -> JP May-vintage crowding honestly ABSENT (archive starts w/ our July collection); CN-A crowding absent (margin walled, northbound queued)
- **THE HEADLINE: MSCI-class INVERTS the Taiwan playbook** — adds: announcement-day overshoot then decay (buy-day-1 cost +1103 CN / +1453 HK vs TW's −630 gain; WAIT wins); deletes: press to the print, no recovery (sell-early gains −614/−1097; working wins — TW said MOC); **A+3 momentum gate FAILS OOS on MSCI adds (hot +448 vs cold +336 = mean-reversion after the pop)** -> execution playbooks must be EVENT-CLASS-CONDITIONAL (provider x tracked-AUM ahead of the A+3 gate in the matrix); JP milder (adds LINEAR −402, dels ~flat) = within-class variation
- Caveats stated (one MSCI event/one regime, close-fill upper bounds); confirmation path = Aug-2026 + archived future events + alias-bridged history; WINDOW_STUDY_CNJPHK_MAY2026.md w/ per-market limitations table + synthesis; +1 test (3-market pipeline, OOS flag, vintage base week); suite 412

## Session 9c (2026-07-29)
- STEP-2 TIME MACHINE (user: replace summary viz with go-back-to-any-review-any-day PIT replay in the website): agents/time_machine.py — list_events (all 38+ keyed events: TW50 quarters 2016-2026 + MSCI-2026 TW, per-event cache-status badge), ensure_window (on-demand THREADED backfill of quotes/shorts/foreign for any window ~30-90s), event_panel (WINDOW_STUDY §0 formulas per name/day), **asof_panel = the STRUCTURAL PIT gate (rows <= asof only — the future is never loaded, not merely hidden)**, asof_step2 (per-name as-of decision state: latest factors + A+3 momentum gate + short-build band -> discretion_decision w/ rationale)
- page6 5th tab "🕰️ Time Machine": event picker w/ cached badge -> fetch button if missing -> as-of date slider -> decision-state table + rationale expander + per-name metric evolution chart THAT ENDS AT THE AS-OF DAY ("what you cannot know yet" caption); summary-viz expander REMOVED per user; verified live on 2026-03 (day-5 state: 7769 HIGH+138% denied pre-positioning, A+3 gates splitting the book, 3665's deletion drift visible pre-re-add); +1 test (PIT gate: future absent, len(asof)<len(panel), decision cols) — first run caught event-count assert 38 vs 40, corrected; suite 411
