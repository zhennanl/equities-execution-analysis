# UI Proposal — The Lifecycle Site (4 live steps + historical replay)

*Session 9i (2026-08-05). A proposal, not an implementation. Goal:
a PT trader who has never seen the site is productive in under two
minutes, because the site's shape IS the shape of the trade they
already run in their head.*

## 1. The design thesis: the timeline is the interface

Traders don't think in "modules" — they think in WHERE ARE WE IN
THE EVENT. So the site's spine is a single horizontal EVENT
TIMELINE (announcement → window → T-day → post-trade), with a
"today" marker, and the four steps as stations on it. Everything
else hangs off that spine. Three questions drive every screen, in
order: **Where are we? What changed since I last looked? What
should I do about it?** If a widget doesn't answer one of those,
it doesn't belong on the first screen.

## 2. Information architecture

### 2.1 The Event Context Bar (persistent, top of every screen)

- **Event selector**: `MSCI Aug-2026 QIR — LIVE` ▾ (dropdown also
  lists historical sessions, each tagged REPLAY — see §3)
- **Phase strip**: the timeline with today's marker (during the
  window it reads e.g. `T-6 to announcement · T-26 to effective`)
- **Sentinel light**: the 🟢/🟡/🔴/⚫ overall from the L0 report —
  one glance answers "can I trust the numbers right now"
- **Mode badge**: LIVE (blue) vs REPLAY (amber, with the as-of
  date) — the two must be visually unconfusable

### 2.2 Home = the Timeline view

Four STATION CARDS in a row (the four steps), each with: status
icon, ONE headline number, and an alert count. Examples:
`1 · WIN — 0 visible calls + 17-name pool · 2 alerts` /
`2 · WINDOW — 3 names OVERCROWDED · 1 migration today` /
`3 · T-DAY — arms in 26 days` / `4 · PROVE — May-26 graded 7/7`.
Click a station → its workspace. The Home also carries the
morning-brief strip (deltas only, from Layer 2) and nothing else.
A trader's default loop is: glance Home (10 seconds), open the one
station that's hot.

### 2.3 Step workspaces — ONE layout, learned once

Every workspace uses the same three-zone grammar:

| Zone | Content | Constant across steps |
|---|---|---|
| LEFT — the names | the ranked table for this step (ladder / scenario tiles / cockpit cards / scorecard rows); click selects a name | same table component, same columns-first ordering |
| CENTER — the picture | the step's primary visual, driven by the selected name | one chart, never a gallery |
| RIGHT — the action rail | advice drafts, alerts for this step, provenance panel, "export/sign" buttons | identical rail anatomy |

Per step: **1 WIN** — left: boundary ladder (members vs floor,
non-members vs bar); center: funnel with name journeys; rail:
shortlist cards + GIMI citations + provenance. **2 WINDOW** — left:
per-name scenario tiles (color = scenario, arrow = yesterday's
migration); center: completion trajectory chart for the selected
name (the crowding build, day by day); rail: must-start-by
countdowns + advice drafts. **3 T-DAY** — left: cockpit cards;
center: intraday curve, and during 13:25–13:30 the LIVE 5-second
indicative-imbalance path; rail: playbook cell + limit-move alerts
+ the signed-advice checklist. **4 PROVE** — left: scorecard rows
(estimate vs realized, hit/miss); center: strategy leaderboard +
reversal path; rail: TCA letter drafts awaiting sign-off + the
lessons-proposed list (lab-gated).

### 2.4 Honesty affordances (non-negotiable, everywhere)

Every number carries its provenance one click away (the existing
provenance panel becomes a per-widget popover); SIMULATED badges on
all synthetic-execution figures; estimates render with a `~` and
muted color vs exact values; every graded artifact shows its grade
inline (the site never hides a miss). These are not decorations —
they are why a trader can trust the site enough to use it fast.

## 3. REPLAY mode — the historical/backtest ability

The critical design decision: **replay is not a separate tool — it
is the SAME four workspaces with time travel.** Pick `May-2026
(REPLAY)` from the event selector and:

- a **date scrubber** appears in the context bar (Apr-30 → T+5);
  every widget renders AS-OF the scrubbed date, PIT — scrub to
  May-20 and Step 2 shows the crowding build as it stood that day
- a **"reveal outcome" toggle** (default OFF) overlays what
  actually happened: the official changes, the realized prints,
  the graded scorecard. OFF = train yourself / demo the honest
  forecast; ON = review the grade
- a **session library** panel lists all replayable events with
  their headline grades (May-26: 7/7+1/1, scenarios 2/2 on
  reversals...) — this doubles as the public track record page

Why this design wins: zero extra learning (the trader already
knows the workspaces), it is the perfect interview/marketing demo
("here is May-26 as we saw it on May-20 — now reveal"), and it
enforces PIT discipline structurally, because every widget must be
renderable from dated artifacts to work in replay at all.

**Enabling convention (the one build prerequisite):** artifacts get
versioned into `data/sessions/<event_tag>/` snapshots (the files
already exist for may26; the convention formalizes it), plus a tiny
`sessions.json` registry (tag, dates, grade headline). Live mode
reads current files; replay reads the session folder.

## 4. Why traders learn it in two minutes

One spine (the timeline they already think in); one workspace
grammar (learn Step 1, know all four); one color language (the
sentinel palette everywhere); alerts always in the same corner;
LIVE vs REPLAY unconfusable; and empty states that explain
themselves ("No cockpit yet — arms automatically at T-1"). No
manual, no tour: the first screen IS the mental model.

## 5. Mapping to what exists (assembly, not new analytics)

Every tile has a producer already: ladder (ladder_aug26_tw.json),
funnel+journeys (funnel_tw.json), workbench (universe_workbench_*),
scenario tiles (liquidity_forecast_*.json), cockpit
(cockpit_*.json), leaderboard/TCA (post_event_*.json + letters),
sentinel light (sentinel_report.json), brief strip (Layer-2
drafts). Gaps to build: the sessions registry + snapshot convention
(§3), the date scrubber's as-of filtering (artifacts carry dates —
mostly filtering, not recomputation), and the per-widget provenance
popover (content exists, placement is new).

## 6. Build order (each phase ships usable)

1. **Context bar + Home timeline** (replaces the Desk Brief page as
   the front door; station cards read existing JSONs)
2. **Workspace grammar on Step 2** first (the live window Aug-12 →
   Sep-1 is the proving ground; scenario tiles + trajectory chart)
3. **Steps 1/3/4 re-hung** onto the same grammar (content exists —
   this is rearrangement)
4. **Replay mode** for may26 (sessions registry + scrubber +
   reveal toggle)
5. **Polish**: provenance popovers everywhere, empty states,
   keyboard-free onboarding pass

Streamlit reality check: all of this fits Streamlit (context bar =
top container + selectbox; stations = columns of buttons; scrubber
= slider over dated artifacts; mode badge = colored banner). No
framework change needed for v1; if the site ever outgrows
Streamlit, the artifact-driven design ports as-is because every
widget is a pure function of JSON files.
