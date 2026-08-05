# Steps 3–4 Without Client Fills — Simulation Methodology + Agentic Workflow

*Session 9i (2026-08-05). Question: how do we simulate execution
(Step 3) and performance review (Step 4) honestly with NO buy-side
trade records — and how do we automate both so the analyst touches
only judgment? Builds on: post_event.py (no-fills Step 4, May-26
demo), tday_cards, the situations playbook, the measured execution
studies, STEP12_AGENTIC_WORKFLOW_REVIEW.md (the layer model).*

## Part 1 — The simulation methodology (synthetic orders, real tape)

### 1.1 The core substitution

We lack fills; we hold the TAPE — direct 5-minute bars with the
discrete 13:30 auction print separated, for 24 events. So the
substitution is: define a synthetic order, execute it against the
ACTUAL bars under conservative rules, and label everything
SIMULATED. What is exact and what is modeled must never blur:

| Exact (measured tape) | Modeled (stated assumptions) |
|---|---|
| every bar's price/volume, the auction print, close-vs-VWAP gaps, T+1..5 reversal path | our order's market impact (we didn't move the real tape) |
| relative ranking of strategies on the same tape | queue position / fill probability inside a bar |
| timing cost of being early vs late | opportunity cost of unfilled residuals |

### 1.2 The three honesty rules for synthetic execution

1. **Participation ceilings** — the synthetic order may take at
   most ~15% of any bar's actual volume (and a bounded share of the
   auction print); this keeps the no-impact assumption second-order
   rather than heroic.
2. **Impact adders from measured tolls** — where the strategy
   demands liquidity at the close, add the playbook's MEASURED toll
   for that cell (15–55bps by side/crowding), not a theoretical
   impact curve. Our own measurements price our own simulation.
3. **Same tape, all strategies** — strategies compete only against
   each other on identical bars; we grade RANKINGS and SPREADS
   (strategy A beat B by x bps), which survive the no-impact
   approximation far better than absolute costs do.

### 1.3 The strategy set (the benchmark strip, formalized)

All-MOC (the passive-obligation baseline) · TWAP across the final
day · volume-weighted participation · front-loaded (ann-window
accumulation, unwind at print) · playbook-guided (the advice column
made executable: scenario-conditional split across pre-close /
print / T+1). Each produces a simulated arrival-vs-benchmark strip
per name per event — post_event.strategy_leaderboard already
computes the first four; the playbook-guided strategy closes the
loop from Step 2's advice to graded outcome.

### 1.4 The synthetic client panel (substituting for client records)

Real desks review performance PER CLIENT TYPE; we simulate the
archetypes instead: the EM-tracker (MOC-obliged, zero discretion),
the IMI-tracker (different membership event set — the composite
math), the benchmarked active (may deviate ±1 day), the
liquidity-provider HF (the interview's archetype — accumulates the
window, supplies the print). Each archetype = constraints + an
objective; run all archetypes through every event and grade the
ADVICE per archetype, not just the strategy. This is the honest
replacement for client records: we cannot know what clients did,
but we can grade what we WOULD HAVE TOLD each kind of client.

### 1.5 Validation anchors (why the simulation is trustworthy)

The synthetic results must reproduce the independently measured
findings before being trusted for advice: the print landing AGAINST
the obligated side (p_gap_fav 0.08–0.38), the T+1 reversal cells
(+255bps Buy/AGAINST/NORMAL class), the May-26 OVERCROWDED names'
fade profitability (2324/2474: +26/+28% reversals — the fade leg of
the playbook-guided strategy should dominate exactly there, and
does). Every new event re-anchors: simulate → grade vs measured
tape → any contradiction between simulation and measurement is a
BUG in the simulation, by definition — the tape wins.

## Part 2 — The agentic workflow (who does what, when)

### Step 3 (T-day) — the cockpit pipeline

- **L0 sentinels:** the calendar sentinel arms T-day mode at T-1;
  the live-capture archiver records the 5-second indicative auction
  path 13:25–13:30 (first live run Aug-31 — capture-forward asset);
  a limit-move detector watches the shortlist names' bands.
- **L1 signal agents:** the PRE-OPEN agent assembles per-name
  cockpit cards (Step-2 final scenario, expected print multiple,
  playbook cell, archetype advice) before the desk sits down; the
  13:00 and 13:25 UPDATERS re-read crowding-day state (and, once
  the capture archive exists, the live indicative-imbalance read);
  the limit-move agent re-routes affected names to their playbook
  branch and flags the cards.
- **L2 synthesis:** the T-day desk note (pre-open draft: today's
  names, scenarios, advice per archetype) and the same-day recap
  (post-close: print vs expectation, one line per name) — drafts,
  never sent unreviewed.
- **Human gate:** the trader signs advice; the agents assemble it.

### Step 4 (post-trade) — the self-grading pipeline

- **L0:** a data-arrival sentinel (T-day bars landed? official
  closes? foreign-flow files?) gates everything downstream — no
  grading on partial data, ever.
- **L1:** the POST-EVENT agent runs the full pack unattended:
  benchmark strip + strategy leaderboard (§1.3), archetype advice
  grading (§1.4), Step-2 scenario self-grade (did OVERCROWDED
  reverse?), crowding resolution (did the measured inventory
  actually supply the print?), and the reversal tracker daily
  through T+5. Estimate-vs-exact ledger updated; every miss ships.
- **L2:** the client-facing TCA letter per archetype ("all-MOC vs
  the advised split: −x bps, SIMULATED basis stated") and the
  lessons-learned draft — which may PROPOSE new playbook rules but
  cannot adopt them: adoption goes through the variable-lab
  registry like every other rule (lock, thresholds, LOO).
- **Human gate:** the analyst reviews the self-grade, signs the
  letters, and decides what enters the lab. Nothing else is manual.

### The efficiency ledger (before → after)

| Task | Before | After |
|---|---|---|
| T-day morning prep | ~1h assembling cards/notes | read the pre-open draft, sign |
| Intraday monitoring | watching names by hand | 13:00/13:25 agent updates + limit alerts |
| Post-event pack | half a day of scripts by hand | unattended at T+1 data arrival |
| TCA/client letters | written from scratch | drafts from graded artifacts |
| What stays manual | — | advice sign-off, self-grade review, lab adoption — the judgment |

### The institutional upgrade (one line each, per prior doc)

Real client fills replace the synthetic panel (§1.4) and calibrate
the impact adders (§1.2); real-time feeds make the 13:25 updater a
true live cockpit; venue/TCA history turns toll adders into size-
conditional curves. The workflow shape does not change — proxies
swap for measurements, same as Steps 1–2.

## Build order

1. Playbook-guided strategy into strategy_leaderboard (closes the
   Step-2→3→4 loop; data held)  2. Archetype panel + advice grading
   in post_event  3. Pre-open cockpit agent (assembles existing
   artifacts — plumbing)  4. Live-capture archiver rehearsal before
   Aug-29, first live run Aug-31  5. Data-arrival sentinel + T+1
   unattended pack  6. TCA letter templates from graded output.
