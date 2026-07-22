# Session Summary — 2026-07-08

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
