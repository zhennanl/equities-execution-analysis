# Sentinels — the Desk's Automated Watchers (a trader's guide)

*Session 9i (2026-08-05). Code: agents/sentinels.py. One command,
daily: `py -m agents.sentinels`. The report lands on the lifecycle
page as a one-line-per-watcher strip.*

## Why this exists

Before sentinels, keeping our analytics honest meant a person
checking six data sources every morning: are shorts current, did
any fund's holdings move, did a pool name drift, what deadlines are
near, has FX drifted, are the site's numbers older than their
inputs. Sentinels do the CHECKING; the analyst does only the
THINKING. You read six lines — usually all green — and spend your
time on the two that aren't.

## The contract (what a sentinel is and is not)

Each sentinel fetches ONE data family, diffs it against yesterday,
and emits one line. It never judges, never trades, never rewrites a
call — judgment stays with the analyst and the graded engine.

**Statuses:**
- 🟢 **OK** — nothing changed; nothing to do.
- 🟡 **CHANGED** — normal evolution, recorded (e.g. a review
  implemented adds into the funds on schedule). Read the line,
  move on.
- 🔴 **ALERT** — a human should look TODAY. Every alert names the
  thing and the reason.
- ⚫ **DEGRADED** — the data itself is broken or stale. Until it
  clears, distrust downstream numbers built on it (they will also
  be flagged by the artifacts sentinel).

## The six watchers

| Sentinel | Watches | Why a trader cares | Typical alert |
|---|---|---|---|
| **shorts** | TWSE short/SBL files vs the expected latest business day | crowding reads run on this; stale shorts = stale crowding | "no data published for expected day" |
| **members** | holdings of 12 index funds across 10 markets, diffed daily | a name leaving funds MID-QUARTER is an M&A/suspension exit the review lists never announce (the Inotera class) — this used to take archaeology | "2408 left tracking funds mid-quarter — check M&A" |
| **ladder** | current caps of the TW member-ladder bottom vs the delete-pool cutoff | pool entries/exits are the deletion-risk watchlist moving | "pool entries ['2609']" |
| **calendar** | days to announcement/effective + every card's must-start-by date | the window has hard deadlines; missing must-start-by turns a plan into a chase | "must-start-by within 2 days"; "ANNOUNCEMENT IMMINENT" |
| **fx** | TWD/USD vs the pinned 32.5 | all USD caps use pinned FX; >2% drift bends every threshold comparison | "caps translation drifting — re-pin FX" |
| **artifacts** | file times: every published artifact vs the data it was built from | the site must never quote numbers older than their inputs | "funnel_tw.json predates ewt_members.json — regenerate" |

## How the diffing works (one paragraph, no magic)

Each run stores what it saw in `data/sentinel_state.json`. The next
run fetches fresh, compares, and reports only the DIFFERENCE. Slow
watchers (members, ladder) cache for 4 hours so repeated runs cost
nothing; fast ones (calendar, artifacts) always recompute. The
combined report is `data/sentinel_report.json`; the worst
individual status becomes the headline.

## What this does to the analyst's day

Before: ~30-45 min of source-checking before any real work, done
imperfectly under time pressure — and the costly failures were
exactly the un-checked days (the stale-artifact class, the silent
corporate event). After: one command (or the 08:00 scheduled run),
six lines, and attention goes only to 🔴/⚫ items — each of which
arrives pre-diagnosed with the affected names. Quality goes UP
precisely because the boring part is no longer done by a tired
human: sentinels never skip a morning.

## Scheduling

Windows Task Scheduler (daily 08:00):
```
schtasks /create /tn "pt_sentinels" /tr "py -m agents.sentinels" /sc daily /st 08:00
```
Manual anytime: `py -m agents.sentinels` (all) or
`py -m agents.sentinels members` (one, ignores cache for that run).

## What sits ABOVE sentinels (so the layering is clear)

Sentinels are Layer 0 of the agent design
(STEP12_AGENTIC_WORKFLOW_REVIEW.md): they watch and diff. Layer 1
recomputes analytics when a sentinel reports change (ladder
refresh, Step-2 tracker, the Aug-12 announcement agent). Layer 2
drafts words (morning brief, client notes). Layer 3 is this site
and the alert routing. Nothing above Layer 0 fires unless a
sentinel saw something — which is exactly why the system is cheap
to run and hard to fool.
