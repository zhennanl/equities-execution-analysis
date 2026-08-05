# Steps 1–2 Comprehensive Review → a Layered Agentic Workflow for the PT Desk

*Session 9i (2026-08-05). Scope: everything built for Step 1 (win
the trade) and Step 2 (manage the window), reviewed for EFFICIENCY —
then the agent architecture that turns analyst-run scripts into a
desk system, staged as public-data-now vs institutional-later.*

## 1. Where Steps 1–2 actually stand

**Step 1 (prediction/marketing) — deep and validated:** rules
engine (L0–L9) graded 22/22 adds PIT; constituent pipeline solved
for 10 markets (3-fund triangulation, TW unanimous 77); vintage
caches unlock decade PIT backtests (TW 110 names, 2015+); ladder
shadow engine running the book's true mechanism (May-26 exact
bottom-7, Nov-25 7/7 — breadth constraint dead); PIT workbench +
funnel + name journeys + provenance on the site; probabilistic
shortlist with BLIND_SHARE honesty; freshness guarantee.

**Step 2 (window management) — model complete, one event graded:**
liquidity-supply forecast (crowding ratio, 4 observable legs,
declared scenario thresholds) whose May-26 PIT demo called both
monster reversals (2474/2324 OVERCROWDED → +26/+28%); crowding
watch, must-start-by, window-intraday priors, adopted lab variables
(H2/H5/H9).

## 2. The efficiency critique (honest)

Everything above is ANALYST-RUN: scripts regenerate artifacts by
hand; monitoring is pull-not-push (staleness is discovered, not
announced); depth is TW-first while nine markets run shallow; fetch
logic is duplicated across scripts; client notes are drafted
manually from packs; nothing fires on the calendar by itself. A PT
desk cannot babysit scripts at 08:30 — the system must come to the
trader.

## 3. The layered agent architecture

**Layer 0 — Data sentinels (scheduled, dumb, reliable).** Daily
agents that only fetch and diff: shorts/caps/FX (freshness daemon —
exists, generalize beyond shorts), fund holdings across 12 ETFs
(membership diffs = corporate-event detector — the 4551 class
becomes an ALERT, not an archaeology find), review-calendar
countdowns. Output: state files + a one-line delta each. No
judgment.

**Layer 1 — Signal agents (event-driven compute).** Fire when a
sentinel reports change: ladder refresh → pool entries/exits;
Step-2 daily tracker → per-name completion + scenario MIGRATIONS
(the signal is the transition, not the level); hazard-velocity
updates; and the announcement-day agent — Aug-12 08:00: parse the
official list, regenerate funnel/cards/packs, grade every locked
call including the zero, publish the scorecard. Everything this
layer emits carries provenance (which sentinel, which formula,
which prior).

**Layer 2 — Synthesis agents (words, not numbers).** The morning
brief writer (deltas only — "2474 moved BUILDING→OVERCROWDED
yesterday; advice flipped" — never a full-state dump); the
client-note drafter, keyed to client TYPE because the same event
means different flows (EM-Standard tracker vs IMI tracker vs
25/50-capped fund — the composite mathematics we documented); the
meeting-prep pack (client's names × current scenarios × talking
points). Drafts only — nothing sends itself.

**Layer 3 — Interaction surface.** The Desk Brief page as the pull
surface (live tiles, one per lifecycle step); alert routing as the
push surface (scenario migrations, pool changes, freshness
DEGRADED); Q&A over artifacts ("why is 1101 in the pool?" →
answered from the ladder row + provenance chain + GIMI citation);
what-if tools (client size in → toll estimate out, from the
playbook's measured cells).

**The human gate, preserved by design:** agents NEVER ship a call
or send a client note. The conviction-gate checklist (interview
lesson 4) sits between Layer 2 output and anything client-facing;
every agent output lands in the graded record exactly like analyst
output. Automation raises throughput; the honesty culture is not
delegated.

**Mapping to our stack:** sentinels = scheduled tasks over existing
scripts; signal agents = the scripts we already have, wrapped with
delta detection; synthesis = templated generation from the JSON
artifacts (packs/cards/advice columns already exist as inputs);
surface = page7 tiles + a notification hook. Nothing requires new
science — it is plumbing around validated pieces.

## 4. The public-data ceiling (all of this is achievable free)

Daily-automated: 10-market constituent monitoring, TW full ladder +
pool, Step-2 tracker on any announced list, freshness everywhere.
One-time builds: 46-review PIT backtest (data in hand), scenario
calibration (~150 name-events), KR/IN alias bridges, APAC ladder
rollout. Hard limits that remain AT the ceiling: MSCI official
floats/FIF (cutline discretion — the 1101/1326/2207 class), the
unannounced price-cutoff date, historical 5-second auction paths
(capture-forward only, from Aug-31), SBL depth outside TW, and —
fundamentally — we observe the market's positioning, never actual
client flow.

## 5. The institutional upgrade (CLSA desk access)

What changes, in order of impact:

1. **Internal flow history (the big one).** Actual index-rebalance
   client orders, participation and fills across past events turn
   our crowding PROXIES into measured ground truth: calibrate
   completion thresholds against realized supplied liquidity, build
   toll curves BY SIZE from TCA records, and make advice
   capacity-aware ("at your size, split 60/40 pre-close/close")
   instead of directional. Compliance wall stated: aggregated,
   anonymized modeling; information barriers respected; nothing
   here fronts client flow.
2. **Licensed MSCI feeds.** Official floats/FIF + constituent
   files kill the last data-blocked step (#12), resolve cutline
   discretion, and make the decade backtest exact rather than
   ff±10%-banded.
3. **Tick/venue data + vendor history.** The 5-second auction-path
   archive we can only capture-forward becomes purchasable
   backfill; the cockpit trains on years, not seasons.
4. **Real borrow desk data.** SBL rates/utilization replace the
   TWT93U balance proxy — the deletes' positioning leg sharpens
   from "balance rose" to "borrow is 90% utilized at 8%, the
   short is crowded in the RATE, not just the quantity."
5. **Sell-side ecosystem data.** Peer flow estimates, futures
   basis, EM-fund creation/redemption baskets — corroborating legs
   for the crowding read.

The workflow architecture (section 3) is IDENTICAL in both worlds —
that is the design point. Institutional access swaps proxy inputs
for measured ones and tightens thresholds; it does not change a
single interface. Which is also the interview line: *the system is
built so that better data makes it sharper, not different.*

## 6. Priority order

Public, now: (1) generalize the freshness daemon to all sentinels +
scheduling; (2) Step-2 daily tracker with scenario-migration
alerts wired to the site (Aug-12→Sep-1 is the live proving window);
(3) announcement-day agent rehearsed before Aug-12; (4) synthesis
drafts from existing artifacts; (5) decade calibration when the
backtest lands. Institutional, later: recalibrate thresholds on
flow history first (highest ratio of value to integration effort),
then licensed floats.
