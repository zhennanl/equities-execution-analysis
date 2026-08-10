# Individual Review Study — Design + Implementation Roadmap (c-103)

*The redesign of the Explorer's drill-down: from "show the
changes" to "RECONSTRUCT the decision" — for any past review,
rebuild MSCI's arithmetic with the data and the RULES of that
day, explain per name why it moved, and let an agent explain
the reviews the arithmetic cannot (tranche events, ad-hoc
policy changes).*

## What the module answers, per review

1. WHY did each add/delete happen — in MSCI's own terms
   (PIT full cap vs that review's frontiers; which gate bound)?
2. Under which RULEBOOK — what edition was in force, what had
   changed since the prior review?
3. When the arithmetic CANNOT explain it (May-18 China's
   mass inclusion, reclassifications) — what was the event?

## Architecture: four layers + UI

### L1 — PIT input layer (prices, shares, floats at THAT
### review's data dates)

- Data dates from `review_dates(year, month)` (universe /
  liquidity / 10-day price window — GIMI §3.1.9, global).
- TW: FULLY buildable now — vintage cache has px + shares +
  foreign daily 2015+; PIT membership registry exists; caps at
  any candidate price day are one lookup.
- FLOATS are the honest weak point: our v2 floats are
  CURRENT-vintage. PIT floats need historical insider filings
  (TW: MOPS archives exist — a harvester away) or stay labeled
  "current-float approximation, era caveat". Rule: the
  reconstruction ALWAYS prints its float vintage.
- Other markets: prices PIT via Yahoo history (moved names
  only — cheap); shares/floats labeled EST until per-market
  sources are wired (the market_profiles activation path).

### L2 — Rules-in-force layer (the methodology timeline)

- Harvest every GIMI edition 2015->now (the meth_docs URL
  pattern; Dec-2022 + May-2026 already archived) into
  data/gimi_editions/.
- EDITION-MINE each one: the §2.3.2.1 worked example discloses
  that review's GMSR AND its chosen Price Cutoff Date ex post
  (the Q60 discovery) -> data/gimi_editions_index.json:
  {review: {edition, gmsr_dm, gmsr_em, price_date_disclosed,
  notable_rule_changes[]}}.
- Rule-change tracking: editions carry revision notes; MSCI
  also announces methodology consultations/changes in press
  releases (QIRPR archive already local). The registry stores
  DELTAS between consecutive editions (headline level: buffer
  changes, FIF rounding, China A inclusion framework steps,
  coverage-target adjustments).
- This layer retires the 1.042-style proxy for HISTORICAL
  work: past reconstructions use the ACTUAL GMSR + ACTUAL
  price date. (Forecasting the NEXT review still needs the
  proxy — only history gets the answer key.)

### L3 — Reconstruction engine

- Per review: PIT universe -> corrected walk (rank FULL,
  accumulate FLOAT) at the DISCLOSED price date -> corridor
  from the ACTUAL GMSR -> frontiers -> per-name verdict table:
  full cap, float cap, margin vs the binding frontier, gates
  (float floor / half-bar / ATVR-at-liquidity-date / room),
  verdict = the reason string ("below 2/3 buffer by 12%" /
  "cleared 1.5x bar, all gates" / "NOT EXPLAINED").
- GRADE: reconstruction vs the actual change list — explained
  / miss-input (our data wrong) / miss-rule (we misread the
  rule) / NOT-EXPLAINED (candidate for L4). This is the
  44-review PIT backtest, upgraded with answer keys.

### L4 — Anomaly explainer (the LLM agent leg)

- TRIGGER (mechanical, declared): review-market cells where
  changes > 3x that market's trailing-8-review average, or
  adds/dels wildly asymmetric, or L3 leaves > 30% of moves
  NOT-EXPLAINED. (May-18 China trips all three.)
- AGENT JOB per triggered cell: read the local QIRPR press
  release first (archived), then web-search contemporaneous
  MSCI announcements/news -> produce a CONTEXT CARD: {review,
  market, event_type (inclusion-tranche / reclassification /
  FIF-methodology / corporate-event wave), summary, sources[],
  confidence}. Cached in data/review_context_cards.json —
  agent runs ONCE per cell, humans can edit cards.
- Known cards to seed from the registry already: CN May-18/
  Nov-19 inclusion tranches (v3 flags), Feb-26 Hon Precision
  (large-IPO QIR archetype), Aug-25 TW cadence lesson.
- Honesty rule: cards are LABELED agent-researched with
  sources; a card is context, never a grade.

### UI (the redesigned section)

Header: edition in force + GMSR (DM/EM) + disclosed price
date + rule-changes-since-last-review chips + ANOMALY CARD if
any. Body: the per-name verdict table (L3), sortable by margin
— the "why" column is the product. Footer: reconstruction
grade for that review + links (official PDF, press release,
edition PDF). Quiet reviews get the header only ("nothing
crossed the frontiers — and the reconstruction agrees/"
"disagrees").

## Scope (user-corrected, c-106)

**Feb-2018 -> May-2026** — after the 2015-17 edition hole.
Reconstruction runs only where the CONTEMPORANEOUS rulebook is
in hand; applying later methodology to earlier reviews is the
error class this module exists to avoid. Edition coverage for
the scope is now COMPLETE (46 editions incl. the mixed-naming
2019-20 stragglers; every SAIR 2018-26 has its own GMSR +
disclosed price date; pre-2023 QIRs used prevailing SAIR
values per the discovered regime). Extensions, both optional:
2008-2014 (books EXIST, 40 archived-probe hits — could extend
the scope backward with rulebooks in hand) and 2015-2017
(Wayback-recoverable; API blocked from the sandbox — browser-
side attempt registered). 2006-07 changes remain
Explorer-history only.

## Implementation roadmap (value order; TW first, then APAC)

| Phase | Deliverable | Effort | Depends on |
|---|---|---|---|
| 0 ✓ | Section renamed; design doc (this file) | done | — |
| 1 | GIMI edition harvest + edition-mining -> gimi_editions_index.json (actual GMSR + price date per review; rule-change deltas) | ~1 session | archive pattern exists |
| 2 | TW reconstruction engine (L3) on the vintage cache: 34 reviews, per-name verdict tables + grades; floats labeled current-vintage | 1-2 sessions | Phase 1 |
| 3 | Anomaly trigger + agent context cards (~10-15 cells expected APAC-wide); seed the known ones | ~1 session | changes_db (done) |
| 4 | UI: the redesigned study section rendering L2+L3+L4 | ~1 session | 1-3 |
| 5 | PIT float upgrade: MOPS insider-history harvester (TW) -> true PIT floats; tighten the reconstruction grades | 1-2 sessions | independent |
| 6 | APAC extension: Yahoo PIT prices for moved names, per-market reconstruction sketches (floats EST, labeled); full engines follow the census activation path (KR -> IN -> JP) | rolling | ladder runs |

Sequencing note: Phases 1-2 are the highest-value pre-Aug-11
work (the edition index also grades our price-date sweep and
retires the 1.042 proxy for history); Phase 3's agent leg can
run any time after; Phase 5 is the only new harvester.

## What this module becomes when finished

The 44-review PIT backtest with answer keys: every historical
review reconstructed under its own rules, every miss decomposed
into input-vs-rule-vs-event, anomalies explained with sources —
the strongest possible calibration evidence for the Aug-2026
call and every call after it.
