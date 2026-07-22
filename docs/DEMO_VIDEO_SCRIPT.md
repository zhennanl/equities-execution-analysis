# Demo Video Script — Execution Analytics Platform

**Script v1.1 · matches platform state of 2026-07-08 evening (181 tests,
3 pages; adds condition-adjusted ranking to Segment 7).** Target runtime
**≤ 30:00**; budgeted 28:50 with 70s slack.
Audience: practitioners who have operated electronic-trading platforms —
every claim is written to survive an expert viewer, and Appendix B maps each
claim to the test or document that verifies it.

**How to maintain this script (read before editing):**
- One numbered SEGMENT per app section. Each carries: `[time budget]`,
  `SOURCE` (the modules it demonstrates), `UPDATE WHEN` (the triggers that
  make its narration stale), SCREEN directions, and NARRATION.
- When functionality changes: find the segment via its SOURCE line, rewrite
  only that narration, re-check its rows in the Appendix B claims audit, and
  rebalance timings in the §0 budget table.
- Never ad-lib quantitative claims on camera. If it isn't in Appendix B,
  don't say it.
- Bump the script version and the "matches platform state" line with every
  edit; keep old versions in git history, not in this file.

---

## 0. Timing budget

| # | Segment | Budget | Cumulative |
|---|---|---|---|
| 1 | Cold open & honest positioning | 1:30 | 1:30 |
| 2 | Architecture in two minutes | 2:00 | 3:30 |
| 3 | P1: Order ticket & compliance | 1:30 | 5:00 |
| 4 | P1: Desk verdict & pre-trade report | 1:30 | 6:30 |
| 5 | P1: Pipeline stages (regime → pre-trade → venue) | 2:00 | 8:30 |
| 6 | P1: Algo simulation, comparison & algo wheel | 2:30 | 11:00 |
| 7 | P1: Cost model, A/B-with-controls & condition-adjusted ranking | 1:50 | 12:50 |
| 8 | P1: Post-trade TCA (IS attribution, markouts, order detail) | 2:30 | 15:20 |
| 9 | P1: Live session (interventions, alerts, volume re-forecast) | 2:30 | 17:50 |
| 10 | P2: Event feed & a real MSCI event | 1:30 | 19:20 |
| 11 | P2: Event study with inference | 1:30 | 20:50 |
| 12 | P2: Execution-cost insights (crowding, expected move, liquidity shift) | 2:00 | 22:50 |
| 13 | P2: Strategy frontier, trader pack & best-ex record | 2:00 | 24:50 |
| 14 | P2: Basket mode & the event library | 1:00 | 25:50 |
| 15 | P3: Program Trading Desk | 2:00 | 27:50 |
| 16 | Close: boundaries & roadmap | 1:00 | 28:50 |

---

## SEGMENT 1 — Cold open & honest positioning  [1:30]
SOURCE: README.md intro; docs/INFEASIBLE_FEATURES.md
UPDATE WHEN: module count changes; data provider changes.

SCREEN: Title card, then the app's sidebar with the three modules visible.

NARRATION:
"This is a three-module execution-analytics platform: an execution-algorithm
simulator covering the full order lifecycle, an index-rebalancing analysis
built around a market-model event study, and an Asia program-trading desk.
Before anything else, the honesty statement, because you'll be checking for
it: everything runs on free Yahoo Finance data — five-minute bars intraday,
daily bars for sixty days. There is no order book, no quotes, no venue feed.
Every microstructure quantity you'll see — spreads, VPIN, Kyle's lambda — is
a disclosed bar-based approximation, and every simulated fill prints against
a historical tape our own trading could not have moved, so market impact is
a model, cross-checked three ways, and clearly labelled wherever it appears.
The claim of this platform is not data fidelity. It's that the methodology
is institutional, the boundaries are explicit, and the whole thing is pinned
by a 181-test regression suite."

## SEGMENT 2 — Architecture in two minutes  [2:00]
SOURCE: docs/ARCHITECTURE_DIAGRAMS.md D1; agents/orchestrator.py; agents/context.py
UPDATE WHEN: an agent is added/removed; orchestration behavior changes.

SCREEN: D1 mermaid diagram, then a brief flash of the orchestration trace
expander in the app ("what ran, what was skipped, and why").

NARRATION:
"The design is a pipeline of specialist agents over a shared context — each
one a pure function with typed inputs and outputs, unit-tested in isolation.
Three properties matter for a production mindset. First, graceful
degradation: if earnings data is missing for a name, that agent records
'skipped' with a reason and everything downstream that doesn't need it still
runs — a partial pipeline is a first-class, inspectable state, not an error
page. Second, the division of labor: all money-relevant arithmetic is
deterministic and auditable; the agentic layer does orchestration, routing,
and packaging — there is no LLM anywhere in the cost path. Third, the critic
pattern: an independent agent reviews the recommendation and raises findings
— it never silently overrides. In a money-adjacent workflow, an unexplained
automated override is worse than the disagreement it hides."

## SEGMENT 3 — P1: Order ticket & compliance  [1:30]
SOURCE: agents/order_ticket.py; compliance checks in views/page1_simulator.py (I-9)
UPDATE WHEN: ticket fields change; compliance rules change.

SCREEN: Fill the inputs — a liquid Asia name (e.g. 2330, Taiwan), 5% ADV,
Medium urgency. Open the order-ticket expander: side, limit, window,
participation cap, locate. Show the FIX-tag panel briefly. Trigger one
compliance block (e.g. Sell without locate) and show the refusal, then fix it.

NARRATION:
"Orders enter through an institutional ticket — side, limit, execution
window, participation cap, auction gating, short-locate — rendered with its
FIX tags. Pre-trade compliance runs before anything else: restricted list,
fat-finger versus ADV, and a hard locate requirement on sells; a block is a
block with a reason, not a warning. One engine property worth knowing: these
constraints bind the *fill kernel itself* — the same constraint code runs in
the static simulation and the live session, which we verify with exact
parity tests, including the execution window."

## SEGMENT 4 — P1: Desk verdict & pre-trade report  [1:30]
SOURCE: agents/desk_pack.py (P-A, P-C)
UPDATE WHEN: verdict/RAG logic or run-library stats change.

SCREEN: Run the pipeline. Point at the verdict banner, then open the
pre-trade report expander and the download button. Point at the run-library
caption under the banner.

NARRATION:
"The first render after the pipeline is the desk verdict — one line: side,
size, urgency, recommended algo and alternative, the expected-cost band, and
a capacity traffic light — green if the order completes inside a day at this
urgency's participation, red beyond three days. Below it, the full pre-trade
report as a text download: the artifact a desk attaches to a parent order.
And note this caption: every run records its predicted cost against the
realized simulation into a run library, so the platform reports its own
predicted-versus-realized bias and mean absolute error. The expected-cost
benchmark is accountable to its own history — that's the learning loop."

## SEGMENT 5 — P1: Pipeline stages  [2:00]
SOURCE: agents/agent2 (regime), agent6 pre-trade, agent7, agent9, agent13
UPDATE WHEN: estimators added to the spread blend; venue model changes.

SCREEN: Scroll Stage 1: regime badges, pre-trade estimate (expected-cost
table, capacity, spread note), earnings flag, microstructure metrics. Then
Stage 2 venue routing table.

NARRATION:
"Stage one is condition assessment. The regime agent classifies volatility,
volume shape, and trend — trend by a formal Lo-MacKinlay variance-ratio test,
not a moving-average heuristic. The pre-trade estimate gives expected-cost
bands per algorithm from empirical percentiles across simulated days, a
capacity table, and a spread estimate that deserves a sentence: it's the
median of three independent daily-bar estimators — Corwin-Schultz,
Abdi-Ranaldo, and the 2024 EDGE estimator — and when they disagree by more
than two-to-one, the page flags the disagreement explicitly and tells you to
treat the level as order-of-magnitude only, instead of letting a blended
number hide it. Impact is cross-checked
against the Almgren 2005 power-law calibration, and Kyle's lambda and a
BVC-based VPIN give the toxicity read. Stage two allocates the order across
a stylized venue set — the objective function is real, the venue mechanics
are simulated, and the page says exactly that."

## SEGMENT 6 — P1: Algo simulation, comparison & wheel  [2:30]
SOURCE: agents/agent3, agent4, agent10, agents/algo_wheel.py (I-7)
UPDATE WHEN: algo set changes; wheel statistics change.

SCREEN: The 8-algo results table and cost chart; the cross-day comparison
and AC frontier; then the Algo Wheel league table and rank chart with the CD
line.

NARRATION:
"Eight algorithms are simulated against the same day — VWAP, TWAP, POV, an
Almgren-Chriss implementation-shortfall trajectory, the auctions, a
liquidity-seeker, and a low-footprint stealth profile. Schedules are
look-ahead-bias-free: volume curves come from prior days only. Costs follow
Perold: slippage versus arrival, modeled square-root impact, and opportunity
cost on unfilled shares — a POV that fills forty percent cheaply is not
cheap. Then the wheel: every strategy on the same historical days is a fully
blocked design — stronger pairing than a live randomized wheel can achieve —
so we rank by Friedman test and mark separability with a Nemenyi critical
difference. Watch the honest small-sample behavior: with few days, most
algos are 'not separable from best,' and the league table says exactly that
instead of overclaiming an ordering. The output also warns about
multiplicity if you re-run across many configurations."

## SEGMENT 7 — P1: Cost model, A/B-with-controls & condition-adjusted ranking  [1:50]
SOURCE: agents/cost_model.py, cost_panel.py; agents/algo_wheel.condition_adjusted_ranking
UPDATE WHEN: regression spec or diagnostics change; ranking view changes.

SCREEN: Coefficient table with robust SEs, diagnostics row, predicted-vs-
realized plot, A/B-with-controls result; then the Condition-Adjusted Ranking
table — pause on a Δ-rank row.

NARRATION:
"Rather than assuming the square-root prefactor, this section estimates the
cost curve: OLS on a panel across order sizes, all eight algos, and every
available day — cost on root-size, volatility, participation, spread, and
duration — with White and Newey-West standard errors and the standard
residual diagnostics on screen. The same machinery gives A/B testing with
controls: a strategy dummy net of size, volatility, and spread. On a
balanced simulated grid the naive and controlled estimates coincide — on
real, unbalanced client flow they diverge, and the controlled coefficient is
the defensible one. That's the exact regression a desk would fit on its own
fills; the panel is simulated here, the spec is not. And the same machinery
answers the question every algo wheel raises: raw rank versus
condition-adjusted rank, side by side. Raw league tables measure the flow an
algo was given as much as the engine behind it — the broker handed the
biggest, hardest orders ranks last raw even with the best engine. The
adjusted column holds size, volatility, participation, and spread fixed,
names which algos move, and tests separability. We show both ranks, always —
an adjusted number alone invites the suspicion that the controls were chosen
to flatter it."

## SEGMENT 8 — P1: Post-trade TCA  [2:30]
SOURCE: agent6 post-trade incl. build_is_attribution (I-5); microstructure_analytics.compute_markout_curve; order detail (I-8)
UPDATE WHEN: IS attribution conventions change; markout horizons change.

SCREEN: Benchmark table, reversion, permanent/temporary decomposition; then
the IS attribution waterfall — pause on the reconciliation tooltip; the
parent/child order detail; the markout curve.

NARRATION:
"Post-trade starts with the standard benchmark set and the Almgren
permanent-temporary split, both flagged as directional — there's no control
group on a single day. The centerpiece is the Perold attribution: delay from
decision to first fill, trading cost share-weighted from first fill to
average price, opportunity on unfilled shares, and explicit costs from the
per-market schedule — reconciling to the share-weighted shortfall within a
tenth of a basis point *by construction*, asserted in tests across all eight
algos on both sides. One convention an expert will ask about: the modeled
impact appears as a memo item, not a component — because simulated fills
don't embed our own impact, blending a model into a reconciled decomposition
would be dishonest bookkeeping. Below it, the EMS-style order detail —
child slices and completion — and the markout curve: share-weighted
post-fill drift at five to sixty minutes against the bar-close mid proxy.
Rising markouts say the order was behind the market; falling say we paid
temporary impact a slower schedule could have recaptured."

## SEGMENT 9 — P1: Live session  [2:30]
SOURCE: agent11 (+ live_volume_forecast, B4); agent3.simulate_with_interventions
UPDATE WHEN: alert rules change; re-forecast logic changes.

SCREEN: Scrub the playback to mid-day; show fills vs plan and running
benchmarks; the alert blotter; the volume re-forecast metrics; apply an
intervention (switch algo/urgency) and show the re-plan; show the live
re-recommendation flag.

NARRATION:
"The live session replays the day bar by bar — it's backtest-style replay,
not a feed, and it says so. The blotter alerts on completion pace,
participation breaches, limit state, toxicity, and benchmark slippage —
alerts inform, nothing auto-acts. The most-watched number on any live
blotter is here: volume run-rate versus the historical curve, the projected
full-day volume it implies, and whether the remaining order still fits at
this urgency's participation — with a projected completion time, and a hard
'does not fit — act' when it doesn't. Interventions re-plan only the
residual, forward from the checkpoint — nothing behind the checkpoint is
ever re-simulated — and the ticket's cap, limit, and window keep binding
every leg; single-leg parity with the static pipeline is asserted to the
sixth decimal in tests."

## SEGMENT 10 — P2: Event feed & a real MSCI event  [1:30]
SOURCE: agents/agent12_index_calendar.py
UPDATE WHEN: providers/parsers change; the running example changes.

SCREEN: Page 2. Open the Agent-12 expander; refresh; show real events; pick
the running example (VEDL deletion, eff 2026-06-25); show prefilled inputs;
point out the index-proxy dropdown needing a manual pick for MSCI.

NARRATION:
"The rebalancing module starts from real events: parsed MSCI announcements,
FTSE Russell releases, S&P DJI newswire, plus each provider's review
calendar. Selecting an event prefills ticker, market, dates, and side — the
running example throughout is a real MSCI Standard deletion of Vedanta,
India, announced June nineteenth, effective June twenty-fifth. One honest
note: for MSCI events you choose the benchmark proxy yourself — this is a
market-model event study, so the proxy needs to explain systematic moves,
not replicate the MSCI index."

## SEGMENT 11 — P2: Event study with inference  [1:30]
SOURCE: rebalancing_event_study.run_event_study + event_inference
UPDATE WHEN: estimation window, inference method, or chart bands change.

SCREEN: Run the study. Verdict banner appears first — hold one beat. Key-day
summary with the CAR-t column; CAR chart with the shaded band; volume and
price tabs briefly.

NARRATION:
"The study fits alpha and beta on trading days minus-seventy to minus-eleven
and computes abnormal returns over the window, so idiosyncratic and
beta-driven moves are stripped out. The point-estimate era is over, though —
so every CAR carries inference: the shaded band is plus-minus one-point-
ninety-six sigma under the null, Brown-Warner single-firm with the
forecast-error correction, and the summary shows a t-statistic per key day.
On Vedanta: minus six percent abnormal into the effective date and a sharp
snap-back after — and the caption tells you the band is anti-conservative on
event days themselves because of event-induced variance. Guidance, not a
hard test. That's the difference between quoting a number and quoting a
number you can defend."

## SEGMENT 12 — P2: Execution-cost insights  [2:00]
SOURCE: rebalancing_event_study insights + trader_view.crowding_score / expected_move + compute_liquidity_shift
UPDATE WHEN: insight panels or their rules change.

SCREEN: Concentration, reversal classification, drift decomposition, flow-
to-trade, eta calibration; then crowding score badge, expected-move bands,
and the liquidity/beta shift panel.

NARRATION:
"The insights layer turns measurement into decision inputs. Reversal
classification: Vedanta gave back roughly seventy percent of its pre-event
move inside five days — transient pressure, not a re-rating. Drift
decomposition: about three-quarters of the move came after the announcement.
The crowding score aggregates disclosed proxies — pre-announcement share of
the move, pre-announcement volume, optionally short-interest change — and
maps the tier to strategy advice: high crowding means the pop is spent and
the reversal runs larger. The expected-move panel calibrates the flow two
independent ways: a square-root-law band, and a Gabaix-Koijen flow
multiplier of three to eight on flow over float cap. The reading rule is
printed with the numbers: realized move far above the bands means crowding
on top of mechanical flow. And after the event, the liquidity shift panel
re-fits beta and re-estimates spread and Amihud on post-event days — because
inclusion changes comovement, and your hedge ratio should notice."

## SEGMENT 13 — P2: Strategy frontier, trader pack & best-ex  [2:00]
SOURCE: agent14_rebalance_strategist; trader_view (cards, playbook, bestex)
UPDATE WHEN: strategies, card fields, or record schema change.

SCREEN: Agent 14 controls (side prefilled Sell); frontier scatter — pause on
S1 at zero tracking; the trade card; playbook expander; best-ex download.

NARRATION:
"Four literature-anchored strategies are scored on this event's actual path:
full market-on-close, pre-positioning after the announcement, post-effective
completion, and the announcement-anchored spread. The frontier is the client
conversation: cost versus the decision price against tracking versus the
print. One convention experts will test: S1 shows exactly zero tracking even
with impact on — deliberately, because a hundred-percent MOC fill *is* the
closing print; your auction impact moves the print itself. Its impact shows
up where it belongs, in cost versus decision — a thousand basis points on
this deletion. The trader pack renders the decision desk-ready: a plain-text
card, all schedules as CSV for staging, and a conditional playbook — dated
if-then triggers with thresholds that display their source, this event or
the library median. And every run persists a best-execution record at
decision time: decision, evidence, thresholds — the quarterly best-ex
narrative as a by-product, not a reconstruction."

## SEGMENT 14 — P2: Basket mode & the event library  [1:00]
SOURCE: trader_view.run_basket; event library functions
UPDATE WHEN: blotter columns change; library stats change.

SCREEN: Upload a small program CSV; show the severity-ranked blotter; then
the library context line in the insights section.

NARRATION:
"Rebalance trading is portfolio trading, so basket mode takes the whole
program as a CSV and returns an exception blotter, worst first — failed
names, then auction-capacity red flags by size. And everything accumulates:
each completed study writes one row to the event library, and once it holds
three events the playbook thresholds and the eta band switch from
single-event anecdotes to library medians — with n displayed, always."

## SEGMENT 15 — P3: Program Trading Desk  [2:00]
SOURCE: agents/program_trading.py; views/page3_program.py
UPDATE WHEN: market reg table changes; blotter/wave/recon logic changes.

SCREEN: Session board (point at Tokyo lunch or an open/closed contrast);
regulation reference; upload the sample program; blotter flags (a China-A
sell BLOCK, a Taiwan odd-lot note); wave plan; recon report download.

NARRATION:
"The program desk view covers the cross-market mechanics. A session board
with local phases and minutes to close — lunch breaks included. A regulation
reference per market: board lots, short-sale regimes — China-A effectively
unavailable, Korea's post-resumption rules, Hong Kong's designated list —
circuit-breaker structures, and settlement cycles. The program blotter
pre-trades a CSV of names: capacity flags, board-lot rounding with the
odd-lot residual quantified, short-sale blocks and locate warnings, explicit
costs, and settlement dates. The wave plan orders the program's markets by
closing time — Taipei and Tokyo before the China reopen, everything before
India's close, residuals into Europe and the U.S. And the reconciliation
report ties ordered against lot-executable quantities per name — simulated,
labelled as such, but the record-keeping discipline is the point. One
disclosure on this page, stated on screen: session times and regulatory
notes are stylized — no holiday calendars, DST approximated — verify against
the exchange notice."

## SEGMENT 16 — Close: boundaries & roadmap  [1:00]
SOURCE: docs/HANDOFF_2026-07-08_v3.md §5; INFEASIBLE_FEATURES.md
UPDATE WHEN: roadmap changes.

SCREEN: D4 learning-loops diagram, then the docs folder briefly.

NARRATION:
"What this is not: it has no ticks, no real venues, no client fills, and it
never pretends otherwise — the infeasible-features register documents every
boundary and what access would close it. What it is: institutional
methodology, three learning loops — an event library, a run library, and
best-execution records — and a test suite that pins every number you saw
today. Next on the roadmap: multi-day parent orders, a pre-announcement
candidate radar, and venue-level markouts. Everything you saw is documented,
versioned, and reproducible — which is the property that matters most when
the person watching runs a real desk."

---

## Appendix A — Demo preparation checklist

1. **Pre-warm data (yfinance rate limits are real):** run Page 1 once on the
   demo ticker ~10 min before recording (5-min cache covers a retake window;
   re-run on a retake). Run the VEDL study once so Page 2 renders instantly.
2. **Seed the libraries:** ensure `data/event_library.json` holds ≥3 events
   so library medians (not "this event") appear in the playbook — record 2–3
   past events beforehand. Ensure the run library has a few scored runs.
3. **Program CSV for Segments 14–15** (save as `demo_program.csv`):
   `ticker,market,side,shares` — e.g. `2330,Taiwan (TWSE),Buy,5000000` ·
   `VEDL,India (NSE),Sell,1359725` · `600519,China-A Shanghai,Sell,50050`
   (shows the BLOCK + odd-lot) · `7203,Japan (TSE),Buy,400000`.
4. **Segment 3 compliance demo:** Sell + locate unchecked triggers the block.
5. **Timing discipline:** segments 6, 8, 9, 13 carry the conceptual weight —
   protect their time; trim 5 and 15 first if running long.
6. **Don't** live-refresh Agent 12 on camera more than once; don't run
   basket mode with >5 names on camera (one fetch per name).

## Appendix B — Claims audit (every number said on camera → its source)

| Claim in narration | Segment | Verified by |
|---|---|---|
| 181 offline tests | 1 | `pytest -m "not live"` (updated post-HANDOFF-v3; script v1.1) |
| Constraints bind live == static, exact parity | 3, 9 | tests/test_live_binding.py |
| Capacity RAG ≤1 day green / >3 red | 4 | agents/desk_pack.py constants |
| Predicted-vs-realized bias/MAE from run library | 4 | tests/test_desk_pack.py |
| Variance-ratio trend test (Lo-MacKinlay) | 5 | agents/agent2; tests/test_estimators.py |
| Spread = median of CS/AR/EDGE; >2x disagreement disclosed | 5 | agent6 blend (MICROSTRUCTURE_RESEARCH_IMPROVEMENTS.md update note) |
| Almgren-2005 cross-check; Kyle λ; VPIN via BVC | 5 | agents/agent9 |
| Look-ahead-bias-free volume curves | 6 | agent3 `_historical_volume_weights` docstring |
| Perold opportunity cost on unfilled shares | 6, 8 | agent3 `_build_result`; tests/test_agent3.py |
| Blocked design; Friedman + Nemenyi CD; multiplicity note | 6 | agents/algo_wheel.py; tests/test_quant_additions.py (CD formula) |
| HC1/Newey-West SEs; DW/BP/JB diagnostics; A/B-with-controls debias | 7 | agents/cost_model.py; tests/test_cost_model.py |
| Raw vs adjusted rank; confounded flow corrected (raw last → adjusted first); balanced grid ⇒ identical ranks | 7 | algo_wheel.condition_adjusted_ranking; tests/test_quant_additions.py |
| IS attribution reconciles ±0.1bp, all algos × both sides | 8 | tests/test_is_attribution.py |
| Modeled impact = memo item, not IS component | 8 | ISAttribution docstring |
| Markouts at 5–60 min vs bar-close mid; sell mirror | 8 | compute_markout_curve; tests/test_quant_additions.py |
| Interventions re-plan residual only; window binds legs | 9 | agent3.simulate_with_interventions; test_live_binding window tests |
| Volume run-rate / projected completion | 9 | agent11.live_volume_forecast; tests/test_desk_pack.py |
| VEDL: −6% abnormal into T; ~70% reversal in 5d; ~75% post-announcement | 11, 12 | SESSION_SUMMARY_2026-07-08 session 5a (real-data run) |
| Estimation window T−70..T−11; Brown-Warner + forecast-error correction; band anti-conservative | 11 | rebalancing_event_study.event_inference docstring; tests/test_quant_additions.py |
| Crowding tiers → strategy advice; proxies disclosed | 12 | trader_view.crowding_score; tests/test_trader_view.py |
| GK multiplier 3–8; sqrt-law band | 12 | trader_view.expected_move; REBALANCE_RESEARCH_AUTOMATION.md (E) |
| Beta/EDGE/Amihud pre-vs-post shift | 12 | compute_liquidity_shift; tests/test_quant_additions.py |
| S1 tracking ≡ 0 with η>0; ~1,000bp cost on the VEDL deletion | 13 | tests/test_agent14.py; session 5a frontier |
| Playbook thresholds display source + n; library medians at n≥3 | 13, 14 | trader_view.build_playbook; tests/test_trader_view.py |
| Best-ex record at decision time, keyed dedupe | 13 | trader_view.record_bestex; tests/test_trader_view.py |
| Blotter severity order: errors → RED by size | 14 | trader_view.run_basket; tests/test_trader_view.py |
| Session phases (e.g. Tokyo lunch), lot/short/settlement rules | 15 | agents/program_trading.py; tests/test_program_trading.py |
| China-A short BLOCK; Korea Mar-2025 resumption; US/India T+1 | 15 | MARKET_REG table (stylized-disclosure caption on page) |
| Wave order Taipei/Tokyo → China → India → EU/US | 15 | wave_plan; test_wave_plan_orders_by_utc_close |
| Roadmap items | 16 | HANDOFF_2026-07-08_v3.md §5 |

**Literature numbers allowed on camera** (cite the papers, not the platform):
Petajisto 2011 drag 21–28bps (S&P) / 38–77bps (R2000); Greenwood-Sammon 2025
addition effect <1% in the 2010s, A→E gaps ~4.8/5.8 days; Gabaix-Koijen
multiplier ~5 (3–8). Sources in docs/INDEX_REBALANCE_RESEARCH.md.
