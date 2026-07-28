# Index Review Prediction Framework — Summary by Category

*Compiled 2026-07-28 (session 8e). The complete framework after the
May-2026 all-Asia replication (34%→69% across six iterations) and the
Aug-2026 live pack. One section per category; every claim traces to a
graded case study in docs/case_studies/.*

---

## 1. Predictions (the rules engine)

**What:** replicate provider methodology on public data.
MSCI: GIMI coverage cutoffs (GMSR at 85% cumulative FF coverage;
SAIR add ≥1.15x, QIR ≥1.8x; delete <0.5x; country-segment migration
rule at 85%+2% buffer; min-float & real-ATVR screens; A-share 20%
inclusion factor on member ranking only). FTSE: rank buffers + reserve
lists (TW50 40/61). Plus the churn buffers (no re-add/re-delete of
just-changed names) and the corporate-action rule (announced takeover
→ deletion).
**Inputs:** count-anchored universes (published constituent counts),
caps/floats/volumes (yfinance), official change-list ledgers (MSCI
PDFs, parsed), alias maps.
**Safeguards:** universe validator; membership ledger reconciliation
(STALE_MEMBER/STALE_NONMEMBER blocking — the Feng Tay gate); NO-CALL
for unvalidated markets; PIT replication harness for every past
review.
**Graded:** adds 17/17, zero false positives, 8 markets, true PIT
data. Deletions 51/56 recall / 82% precision — shipped as a
probability-ranked watch zone, never as calls. 69% of ALL 98 actual
May Asia changes.

## 2. Expected flows

**What:** per-name dollar flow = float cap x passive-ownership rate
(5-9%, MSCI-linked stacking across country/EM/ACWI layers), ranges
not points; ADV-day buckets (MOC / WORK+MOC / MULTI-DAY); full-event
simulation incl. the reweight leg (27% of turnover; TSMC −$440M trim
validated against the real −7.27M-share print); self-financing checks.
**Status:** heuristic v1, validation checkpoint = Sep-1 realized
prints.

## 3. Crowding color (positioning overlay)

**What:** daily short-ledger archive (TWSE margin+SBL); pre-event
build % → HIGH/MED/LOW; stock-not-flow refinement (drawdown-from-peak
→ EXITING tag); CONSENSUS/UNPRICED/STREET-ONLY overlay vs our own
calls; drift composition (short-led vs long-seller-led — the
MSCI/FTSE asymmetry, measured).
**Graded:** post-event unwind 9/9; arb→tracker handoff 8/8; the
STREET-ONLY cell caught our China Steel miss ex ante.
**Coverage (multi-market since session 8g):** Taiwan LIVE daily
(TWSE TWT93U + TPEx for .TWO); Japan LIVE daily (JPX disclosed
short positions ≥0.5%, summed per stock — a floor, deltas valid);
Hong Kong LIVE weekly (SFC aggregated short positions CSV) — which
also covers MSCI China H-lines; Korea/Malaysia PROTOCOL (login/403
from sandbox — desk feeds on-site); India/Indonesia STRUCTURAL (no
public per-stock short-balance product). One normalized cache schema
(`merge_into_short_cache`), one read function (`crowding_reads`,
labels actual observation count), registry
`event_data.CROWDING_SOURCES`. Expected flows (layer 2) were already
market-agnostic — computed from cap × float × passive-ownership for
every market's rows.

## 4. Measured event history

**What:** the empirical priors packs quote — T-day volume multiples by
provider x side (MSCI deletes median 16x, max 38x; FTSE ~5x),
front-run drift (−4.3% MSCI), reversal fractions (~50%), auction
shares, T+2 settlement signature. Absent classes stated ("no measured
MSCI-Buy events — stated, not guessed").
**Source:** 21+ real 2026 events, cached and re-usable.

## 5. Risk flags

**What:** deterministic per-name flags — SIZE (ADV-days → multi-day
plan), LIMIT (±band lock risk on event day), BORROW (constrained
lending → squeeze/fail risk), REVERSAL (completion-leg planning),
plus market-access flags (foreign room, investor IDs) from the rules
registry (Reg-Watch, versioned, human-gated).

## 6. Graded track record (the differentiator)

**What:** every pack ships the scoreboard WITH misses: the false-flag
register (Hotai/TaiwanCem/Lotte — cutline residents), the two recorded
failed iterations, the Feng Tay and AI-quartet corrections, null
results (buffer sweep), and Laplace-shrunk per-call probabilities.
Self-grading loop: validate_pack appends outcomes to the same
document; pre-registration by git timestamp.

---

## Where public data limits the analysis (measured, not guessed)

1. **FIF discretion** — MSCI's internal float-factor decisions
   (Indonesia May deletions; floats 0.20-0.29, above any defensible
   screen). Structural blind spot.
2. **Dual-line share splits** — H-tranche vs whole-company caps
   (0177/2799 misses). Fixable: HKEX per-line shares, fetcher queued.
3. **Membership baselines** — change-list ledgers replay deltas but
   can't establish base state (the AI-quartet error). Fixable: fund
   holdings files (8 downloads).
4. **Real-time data** — crowding/auction reads are EOD/delayed;
   indicative-auction logic is live-only by nature.
5. **Anti-bot walls** — 8 of 12 notice feeds, iShares CSVs blocked
   from sandbox (not from a desk browser/network).
6. **Float/cap vintage** — third-party estimates vs vendor as-of
   files; the residual add-side false-positive source (Rainbow).

## On the desk: the same analysis with CLSA's data + AI leverage

*Expanded in full — framework description, resource-by-resource
gap-close map, and the target daily/event workflow — in
docs/AI_INTEGRATED_WORKFLOW.md (session 8f).*

**What desk data closes instantly:** vendor index files (official
constituents, FIFs, capping factors — kills categories 1-3 and 6
above); real-time feeds (closes category 4); Bloomberg/exchange
subscriptions (category 5). The engine's METHODS carry over unchanged
— they were built to be input-upgradable.

**Where AI multiplies efficiency (ranked):**
1. **Automated review cycle**: the entire pack (screen → reconcile →
   flows → crowding → history → flags → rationale) regenerates
   nightly, unattended; the dealer reads a flash brief, not a
   pipeline. Human time per review cycle: days → minutes.
2. **LLM notice/CA extraction**: Reg-Watch triage + corporate-action
   detection from circulars in 4 languages (the Toyota Industries
   class), human-gated.
3. **Client-conditioned rendering**: one engine output → per-client
   packs (their holdings overlap, their TE budget), LLM renders
   narrative, numbers stay deterministic.
4. **RAG over the graded corpus**: instant, cited answers to client
   questions from the case-study library.
5. **Learning loops**: predicted-vs-realized on every layer (flows
   heuristic, T-multiple priors, probability calibration) updates
   automatically each cycle — the desk's numbers compound.
6. **Scenario turnaround**: client "what-if" emails → parameterized
   frontier runs → drafted replies in minutes.
Invariants: LLMs render/retrieve/extract, never rank or predict;
every number traces to a deterministic engine; misses always ship.

## Current live state (Aug-2026 QIR, ann Aug 12)

Eight covered markets, ZERO calls under the May-graded config —
credible post-SAIR quiet, scoped to April-vintage boundary sets (see
AUG2026_QIR_ASIA_PACK.md reading guide). Aug-11 finalization: refresh
caps, scan new boundary entrants, resolve TW AI-quartet membership
(EWT file), commit before announcement, grade after Sep 1.
